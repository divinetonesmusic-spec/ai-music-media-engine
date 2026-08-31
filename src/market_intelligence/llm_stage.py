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
import logging
import os
import re
from pathlib import Path
from typing import Callable, Optional, Union

from .io_utils import LoadError, read_json
from .schema.models import RunConfig

_LOG = logging.getLogger(__name__)
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
#
# Matching: the first live run hit stop_reason=max_tokens on all 3 calls — adaptive
# thinking at the default effort consumed the whole 8000-token budget before any
# JSON (prompt = one opportunity + ~47 inventory candidates, since §10.2a makes
# every artist a candidate). It is bounded per-candidate fit judgement, so it runs
# at effort "low" (like the Web Search structuring call) with more room: 16000 =
# ~47 candidates * ~90 JSON tokens + low-effort thinking headroom.
#
# Evaluation: ``structured: False`` — no ``output_config.format``. Its JSON Schema
# compiles to a grammar over Anthropic's size limit even after the 5d9781f flatten
# (10 dims + 5 axes = 15 nested rating objects, ~30 enum productions inlined 15×;
# confirmed live 2026-08-31, HTTP 400 "The compiled grammar is too large").
# Evaluation asks for prompt-guided JSON, parses it with the lenient parser, and
# validates the shape deterministically (``_reject_malformed_evaluation``) — an
# invalid response is a technical_failure, never a business state. Owner decision
# 2026-08-31 (spec §19 fallback C). 24000 = ~2k JSON + default-``high``-effort
# thinking headroom (effort left at the default to preserve judgement quality).
_STAGE_OUTPUT: "dict[str, dict]" = {
    "framing": {"max_tokens": 32000, "effort": "medium"},
    "matching": {"max_tokens": 16000, "effort": "low"},
    "evaluation": {"max_tokens": 24000, "structured": False},
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
        structured = budget.get("structured", True)
        output_config: dict = {}
        if structured:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        # `effort` is a direct key of output_config, sibling of `format` (not
        # nested in it) — Anthropic effort docs, verified 2026-08-30.
        if budget.get("effort"):
            output_config["effort"] = budget["effort"]

        create_kwargs: dict = {
            "model": model,
            "max_tokens": budget.get("max_tokens", _DEFAULT_MAX_TOKENS),
            "messages": [{"role": "user", "content": prompt}],
        }
        if output_config:
            create_kwargs["output_config"] = output_config

        try:
            msg = client.messages.create(**create_kwargs)
        except anthropic.APITimeoutError as e:
            raise StageError(
                f"{stage}: the model call did not return within ~{_READ_TIMEOUT:.0f}s"
            ) from e
        except anthropic.APIError as e:
            raise StageError(redact(f"{stage} API call failed: {e}")) from e
        return _response_to_json_object(msg, stage=stage, lenient=not structured)


def _unwrap_json_object(text: str) -> str:
    """Best-effort: pull a single JSON object out of prompt-guided (non-schema)
    output. Strips a ``` / ```json fence, and when the text is not already a bare
    JSON value, extracts the first balanced ``{ … }`` span (string-aware). Never
    fabricates — if there is no object, the original text is returned and
    ``json.loads`` reports the real error.
    """
    t = text.strip()
    if t.startswith("```"):
        t = t[3:]
        if t[:4].lower() == "json":
            t = t[4:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
        t = t.strip()
    if t[:1] in "{[":
        return t
    start = t.find("{")
    if start == -1:
        return t
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        c = t[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return t[start:i + 1]
    return t[start:]


def _response_to_json_object(msg, *, stage: str, lenient: bool = False) -> dict:
    """A model response -> a JSON object, or ``ResponseRejected`` that says exactly
    what came back (``stop_reason``, block types, refusal category) instead of a
    bare ``json.loads`` on a truncated / empty string. Never fabricates JSON.

    Per the Anthropic docs the JSON arrives in ``text`` block(s); with thinking on
    (Sonnet 5 default) ``thinking`` blocks precede it, the model may split the JSON
    across several ``text`` blocks, and a ``stop_reason`` of ``max_tokens`` or
    ``refusal`` can leave the response unusable.

    ``lenient=True`` (Evaluation — prompt-guided JSON, no schema): also tolerate a
    ``` fence or a prose preamble around the object. It never makes an invalid
    response valid — a top-level array or genuinely non-JSON text is still
    rejected.
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
                + ") — no usable output"
            )
        raise ResponseRejected(
            f"{stage}: response carried no JSON text block "
            f"(stop_reason={stop!r}, blocks={kinds})"
        )

    candidate = _unwrap_json_object(text) if lenient else text
    try:
        payload = json.loads(candidate)
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
            f"{stage}: response is a {type(payload).__name__}, not a JSON object"
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


# A ``ResponseRejected`` whose cause an identical retry cannot fix (spec §14 — the
# retry is for a transient malformed emit, not for truncation / refusal).
_UNRECOVERABLE = ("truncated at the max_tokens cap", "stop_reason=max_tokens",
                  "refus", "stop_reason=refusal")


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
    """Run one structured-output call and hand the parsed response to ``validate``.

    Spec §14 — a schema-invalid model response is **retried once**. Constrained
    decoding makes a genuinely malformed emit rare, so the retry is narrow: only a
    live client, only a ``ResponseRejected`` (a 200 with unusable content), and not
    when the message says the response was truncated or refused (an identical retry
    would fail the same way). A ``StageError`` (missing SDK / credentials / HTTP
    error / timeout) and a ``MissingFixtureError`` are never retried here — the
    SDK already retries transient HTTP, and a missing fixture is deterministic.
    """
    attempts = 2 if isinstance(client, AnthropicStageClient) else 1
    for attempt in range(attempts):
        try:
            raw = client.complete(
                stage=stage, key=key, prompt=prompt, schema=schema, model=model
            )
            return validate(raw)
        except ResponseRejected as e:
            last = attempt == attempts - 1
            if last or any(m in str(e).lower() for m in _UNRECOVERABLE):
                raise
            _LOG.info("%s: response rejected (%s) — retrying once", stage, e)
    raise AssertionError("unreachable")  # pragma: no cover
