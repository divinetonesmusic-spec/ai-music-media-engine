"""Shared plumbing for the Claude-in-the-loop pipeline stages (spec §19, §22).

Framing, Asset Matching and Evaluation each make one structured-output call per
item. This module gives them a common injectable client, a recorded-replay client
(``<fixture_path>/llm/<stage>/<key>.json``), and the live↔recorded selector — so
each stage only writes its prompt, its JSON schema and its result mapping.

Nothing here decides *what is true*; it only moves a validated JSON object between
the model and deterministic code. API keys are read from the environment and
never stored, logged or written to a fixture.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable, Optional, Union

from .io_utils import LoadError, read_json
from .schema.models import RunConfig

_DEFAULT_MAX_TOKENS = 8000
_KEY_IN_TEXT = re.compile(r"(sk-ant-[A-Za-z0-9_-]+)")

# Per-stage output budget + effort (spec §19). ``max_tokens`` is a hard output
# cap the model cannot see, so too small a value truncates the JSON mid-emit — a
# live Framing run over 37 normalized signals hit ``stop_reason=max_tokens`` at
# 8000. Framing emits the largest structured output (a list of up to
# ``max_candidates`` opportunities, each ~1k tokens of JSON, over every signal),
# so it gets the most room and runs at effort ``"medium"`` — a thinking
# step-down from the default ``"high"`` that keeps the analysis intact while
# freeing budget for the JSON. Matching and Evaluation are per-opportunity and
# small; they are absent here and fall through to the default budget / effort.
# 32000 = ~15 opportunities * ~1.2k JSON tokens + medium-effort thinking headroom.
_STAGE_OUTPUT: "dict[str, dict]" = {
    "framing": {"max_tokens": 32000, "effort": "medium"},
}

# Timeout / retry policy (spec §14). The anthropic SDK defaults to a 600s read
# timeout retried twice — a stalled analysis call would hang ~30 min. Bounded
# here to 600s (sized for Framing at its 32k-token budget; Matching / Evaluation
# finish far sooner and only inherit the ceiling) with one retry (keeps
# transient-429/5xx recovery without tripling the wait on a real timeout).
_CONNECT_TIMEOUT = 10.0
_READ_TIMEOUT = 600.0
_MAX_RETRIES = 1


class StageError(Exception):
    """A stage's model call could not run (missing SDK / credentials / API error)."""


class ResponseRejected(Exception):
    """A model response is malformed or violates the stage's contract."""


class MissingFixtureError(StageError):
    """Recorded replay is on but no fixture exists for this key — never fall back to the network."""


def redact(text: str) -> str:
    return _KEY_IN_TEXT.sub("sk-ant-REDACTED", str(text))


class StageClient:
    """Protocol: run one structured-output call and return the parsed JSON object."""

    def complete(self, *, stage: str, key: str, prompt: str, schema: dict, model: str) -> dict:
        raise NotImplementedError  # pragma: no cover - interface


class RecordedStageClient(StageClient):
    """Replays ``<fixture_root>/<stage>/<key>.json`` — offline, deterministic (spec §22)."""

    def __init__(self, fixture_root: Path):
        self._root = Path(fixture_root)

    def complete(self, *, stage, key, prompt, schema, model) -> dict:
        path = self._root / stage / f"{key}.json"
        if not path.is_file():
            raise MissingFixtureError(
                f"recorded replay: no fixture at {path} (spec §22)"
            )
        try:
            return read_json(path)
        except LoadError as e:
            raise ResponseRejected(str(e)) from e


class AnthropicStageClient(StageClient):
    """Live implementation — one ``messages.create`` with ``output_config`` per call."""

    def __init__(self, *, client=None, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _build_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover - installed in dev
            raise StageError("this stage needs the 'anthropic' package") from e
        if not (
            self._api_key
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        ):
            raise StageError(
                "no Anthropic credentials (set ANTHROPIC_API_KEY) — spec §20.2"
            )
        return anthropic.Anthropic(
            api_key=self._api_key,
            timeout=anthropic.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT),
            max_retries=_MAX_RETRIES,
        )

    def complete(self, *, stage, key, prompt, schema, model) -> dict:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise StageError("this stage needs the 'anthropic' package") from e
        client = self._build_client()

        budget = _STAGE_OUTPUT.get(stage, {})
        output_config: dict = {"format": {"type": "json_schema", "schema": schema}}
        # `effort` is a direct key of output_config, sibling of `format` (not
        # nested in it) — Anthropic effort docs, verified 2026-08-30.
        if budget.get("effort"):
            output_config["effort"] = budget["effort"]

        try:
            msg = client.messages.create(
                model=model,
                max_tokens=budget.get("max_tokens", _DEFAULT_MAX_TOKENS),
                messages=[{"role": "user", "content": prompt}],
                output_config=output_config,
            )
        except anthropic.APITimeoutError as e:
            raise StageError(
                f"{stage}: the model call did not return within ~{_READ_TIMEOUT:.0f}s"
            ) from e
        except anthropic.APIError as e:
            raise StageError(redact(f"{stage} API call failed: {e}")) from e
        return _response_to_json_object(msg, stage=stage)


def _response_to_json_object(msg, *, stage: str) -> dict:
    """A structured-output response -> a JSON object, or ``ResponseRejected`` that
    says exactly what came back (``stop_reason``, block types) instead of a bare
    ``json.loads`` on a truncated / empty string. Never fabricates JSON.

    Per the Anthropic docs the JSON arrives in a ``text`` block; with thinking on
    (Sonnet 5 default) ``thinking`` blocks precede it, and a ``stop_reason`` of
    ``max_tokens`` or ``refusal`` can leave the response unusable.
    """
    blocks = getattr(msg, "content", None) or []
    text = "".join(
        b.text for b in blocks
        if getattr(b, "type", None) == "text" and getattr(b, "text", None)
    ).strip()
    stop = getattr(msg, "stop_reason", None)

    if not text:
        kinds = sorted({str(getattr(b, "type", "?")) for b in blocks})
        if stop == "refusal":
            cat = getattr(getattr(msg, "stop_details", None), "category", None)
            raise ResponseRejected(
                f"{stage}: the model refused (stop_reason=refusal"
                + (f", category={cat}" if cat else "")
                + ") — no structured output"
            )
        raise ResponseRejected(
            f"{stage}: response carried no JSON text block "
            f"(stop_reason={stop!r}, blocks={kinds})"
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        hint = (
            " — the response was truncated at the max_tokens cap; raise this stage's budget"
            if stop == "max_tokens" else ""
        )
        raise ResponseRejected(
            f"{stage}: model returned non-JSON: {e} (stop_reason={stop!r}){hint}"
        ) from e
    if not isinstance(payload, dict):
        raise ResponseRejected(
            f"{stage}: structured response is a {type(payload).__name__}, not a JSON object"
        )
    return payload


def select_stage_client(
    config: RunConfig,
    project_root: Union[str, Path],
    *,
    client: Optional[StageClient] = None,
) -> "tuple[StageClient, str]":
    """Return (client, llm_mode). Recorded replay unless ``replay.llm == 'live'``."""
    if config.replay.enabled and (config.replay.llm or "recorded") != "live":
        fp = config.replay.fixture_path
        if not fp:
            raise StageError("replay is enabled but replay.fixture_path is not set")
        base = Path(fp)
        base = base if base.is_absolute() else Path(project_root) / base
        return RecordedStageClient(base / "llm"), "recorded"
    return (client or AnthropicStageClient()), "live"


def stage_key(*parts: str) -> str:
    """A filesystem-safe fixture key from the parts that identify one call."""
    raw = "__".join(str(p) for p in parts if p)
    return re.sub(r"[^A-Za-z0-9._-]+", "_", raw) or "default"


def obj_schema(properties: dict, required: list) -> dict:
    """A closed JSON-schema object (structured outputs require additionalProperties:false)."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def enum_str(values) -> dict:
    return {"type": "string", "enum": sorted({str(v) for v in values})}


def call_stage(
    client: StageClient,
    *,
    stage: str,
    key: str,
    prompt: str,
    schema: dict,
    model: str,
    validate: Callable[[dict], object],
):
    """Run one call and hand the parsed response to ``validate`` (which may raise)."""
    raw = client.complete(stage=stage, key=key, prompt=prompt, schema=schema, model=model)
    return validate(raw)
