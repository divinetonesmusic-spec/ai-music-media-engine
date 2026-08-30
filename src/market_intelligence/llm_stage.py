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

_MAX_TOKENS = 8000
_KEY_IN_TEXT = re.compile(r"(sk-ant-[A-Za-z0-9_-]+)")

# Timeout / retry policy (spec §14). The anthropic SDK defaults to a 600s read
# timeout retried twice — a stalled analysis call would hang ~30 min. These are
# no-tool, thinking-on calls that normally finish in well under a minute; 300s is
# a generous ceiling, one retry keeps transient-429/5xx recovery.
_CONNECT_TIMEOUT = 10.0
_READ_TIMEOUT = 300.0
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
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
        except anthropic.APITimeoutError as e:
            raise StageError(
                f"{stage}: the model call did not return within ~{_READ_TIMEOUT:.0f}s"
            ) from e
        except anthropic.APIError as e:
            raise StageError(redact(f"{stage} API call failed: {e}")) from e
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ResponseRejected(f"{stage}: model returned non-JSON: {e}") from e


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
