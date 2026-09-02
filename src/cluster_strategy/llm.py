"""Claude-in-the-loop plumbing for Cluster Strategy (one call per opportunity).

Reuses the pipeline's injectable ``StageClient`` / ``RecordedStageClient`` /
``call_stage`` / ``stage_key`` (``<fixture_path>/llm/<stage>/<key>.json`` replay
convention, spec §22) and adds one live client that asks for prompt-guided JSON
(no ``output_config`` — the ClusterStrategy schema is large, same reason
Evaluation dropped structured outputs). Tests never touch the network.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional, Tuple, Union

from market_intelligence.llm_stage import (  # noqa: F401 — re-exported for stage code
    MissingFixtureError,
    RecordedStageClient,
    ResponseRejected,
    StageClient,
    StageError,
    call_stage,
    stage_key,
)

_KEY_IN_TEXT = re.compile(r"(sk-ant-[A-Za-z0-9_-]+)")
_MAX_TOKENS = 24000  # ~2k JSON + default-effort thinking headroom (mirrors Evaluation)


def _redact(text: str) -> str:
    return _KEY_IN_TEXT.sub("sk-ant-REDACTED", str(text))


def _extract_json_object(text: str) -> dict:
    """Pull one JSON object out of prompt-guided output — strip a ``` fence / prose
    preamble, take the first balanced ``{...}`` span. Never fabricates."""
    t = text.strip()
    if t.startswith("```"):
        t = t[3:]
        if t[:4].lower() == "json":
            t = t[4:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
        t = t.strip()
    if t[:1] != "{":
        start = t.find("{")
        if start == -1:
            raise ResponseRejected("cluster_strategy: response carried no JSON object")
        depth = in_str = esc = 0
        end = None
        for i in range(start, len(t)):
            c = t[i]
            if in_str:
                if esc:
                    esc = 0
                elif c == "\\":
                    esc = 1
                elif c == '"':
                    in_str = 0
            elif c == '"':
                in_str = 1
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        t = t[start:end] if end else t[start:]
    try:
        payload = json.loads(t)
    except json.JSONDecodeError as e:
        raise ResponseRejected(f"cluster_strategy: model returned non-JSON: {e}") from e
    if not isinstance(payload, dict):
        raise ResponseRejected(
            f"cluster_strategy: response is a {type(payload).__name__}, not a JSON object"
        )
    return payload


class AnthropicClusterStrategyClient(StageClient):
    """Live: one ``messages.create`` per opportunity, prompt-guided JSON (no schema)."""

    _READ_TIMEOUT = 600.0
    _CONNECT_TIMEOUT = 10.0

    def __init__(self, *, client=None, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _build(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise StageError("cluster_strategy needs the 'anthropic' package") from e
        if not (self._api_key or os.environ.get("ANTHROPIC_API_KEY")
                or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            raise StageError("no Anthropic credentials (set ANTHROPIC_API_KEY)")
        return anthropic.Anthropic(
            api_key=self._api_key,
            timeout=anthropic.Timeout(self._READ_TIMEOUT, connect=self._CONNECT_TIMEOUT),
            max_retries=1,
        )

    def complete(self, *, stage, key, prompt, schema, model) -> dict:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise StageError("cluster_strategy needs the 'anthropic' package") from e
        client = self._build()
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.APITimeoutError as e:
            raise StageError(
                f"cluster_strategy: the model call did not return within "
                f"~{self._READ_TIMEOUT:.0f}s"
            ) from e
        except anthropic.APIError as e:
            raise StageError(_redact(f"cluster_strategy API call failed: {e}")) from e
        blocks = getattr(msg, "content", None) or []
        text = "".join(
            b.text for b in blocks
            if getattr(b, "type", None) == "text" and getattr(b, "text", None)
        ).strip()
        if not text:
            stop = getattr(msg, "stop_reason", None)
            raise ResponseRejected(
                f"cluster_strategy: no text block (stop_reason={stop!r})"
            )
        return _extract_json_object(text)


def select_client(
    *,
    replay_enabled: bool,
    replay_llm: Optional[str],
    replay_fixture_path: Optional[str],
    project_root: Union[str, Path],
    client: Optional[StageClient] = None,
) -> Tuple[StageClient, str]:
    """(client, mode). Recorded replay unless ``replay_llm == 'live'``."""
    if client is not None:
        return client, "injected"
    if replay_enabled and (replay_llm or "recorded") != "live":
        if not replay_fixture_path:
            raise StageError("replay is enabled but replay.fixture_path is not set")
        base = Path(replay_fixture_path)
        base = base if base.is_absolute() else Path(project_root) / base
        return RecordedStageClient(base / "llm"), "recorded"
    return AnthropicClusterStrategyClient(), "live"
