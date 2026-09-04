"""OmniRoute adapter — implements ``market_intelligence.llm_stage.StageClient``.

Decision OMR-01 (``knowledge/DECISIONS-NEEDED.md``): an isolated, optional adapter
that lets *some future, separately-decided* caller reach an external model through
a local OmniRoute OpenAI-compatible gateway (``/v1/chat/completions``), without
Claude/Anthropic being replaced and without any pipeline stage depending on this
module. Dependency direction is one-way — this module imports
``market_intelligence.llm_stage``; nothing in ``market_intelligence`` or
``cluster_strategy`` imports ``external_llm_gateway`` (see docs/EXTERNAL-LLM-GATEWAY.md).

The adapter never starts, stops or supervises an OmniRoute process — it only makes
an HTTP call, and only when :meth:`OmniRouteStageClient.complete` is actually
invoked. There is no automatic retry and no automatic fallback to another model,
provider or transport — a failure is always surfaced as one of the two errors the
``StageClient`` contract already defines:

- ``StageError`` — the call could not complete (HTTP error status, timeout,
  transport failure, no model configured). Mirrors how ``AnthropicStageClient``
  treats every ``anthropic.APIError`` / ``anthropic.APITimeoutError``.
- ``ResponseRejected`` — a 200 response arrived but its content is unusable
  (missing ``choices``, non-JSON message content). Mirrors
  ``llm_stage._response_to_json_object``.

No raw ``httpx`` exception, and no bare non-2xx ``httpx.Response``, is ever allowed
to propagate out of :meth:`complete`.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from market_intelligence.llm_stage import ResponseRejected, StageClient, StageError

from .config import OmniRouteConfig

# Defensive redaction: an upstream error body could in principle echo a token
# back. No secret is ever deliberately placed in a message here (the resolved
# API key is used only in the Authorization header, never in exception text),
# but this is cheap insurance — mirrors the intent of llm_stage.redact().
_BEARER_RE = re.compile(r"Bearer\s+\S+")


def _redact(text: str) -> str:
    return _BEARER_RE.sub("Bearer <redacted>", text)


# HTTP status -> a short, human-readable category named in every StageError
# message, so a caller (or a human reading a log) can tell at a glance whether
# the failure is about the model, billing, upstream capacity or a local
# OmniRoute timeout — the same taxonomy observed empirically against Groq,
# Cerebras and Gemini through OmniRoute during the OMR-01 connectivity tests.
_STATUS_CATEGORY = {
    400: "invalid request or model not available in the live catalog",
    401: "authentication rejected by OmniRoute",
    402: "billing / payment required by the upstream provider",
    403: "forbidden by OmniRoute or the upstream provider",
    404: "not found",
    429: "rate limited",
    503: "upstream provider unavailable (overloaded)",
    504: "gateway timeout (OmniRoute or the upstream provider did not respond in time)",
}


def _error_detail(response) -> str:
    """Best-effort human-readable text from an OmniRoute/OpenAI-style error body
    (``{"error": {"message": "..."}}``); falls back to the raw response text.
    """
    try:
        data = response.json()
    except ValueError:
        return response.text[:500]
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict) and isinstance(err.get("message"), str):
            return err["message"]
        if isinstance(err, str):
            return err
    return response.text[:500]


def _extract_message_content(data: object) -> str:
    """The assistant message text from an OpenAI-compatible chat-completion body,
    or ``ResponseRejected`` naming exactly what was missing/wrong.
    """
    if not isinstance(data, dict):
        raise ResponseRejected(
            f"omniroute: response body is a {type(data).__name__}, not a JSON object"
        )
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ResponseRejected("omniroute: response has no non-empty 'choices' array")
    first = choices[0]
    message = first.get("message") if isinstance(first, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ResponseRejected("omniroute: response choice has no usable message content")
    return content


def _extract_json_object(text: str) -> dict:
    """Strip an optional ``` / ```json fence, then parse a JSON object. Never
    fabricates — a genuinely non-JSON or non-object payload is ``ResponseRejected``.
    """
    t = text.strip()
    if t.startswith("```"):
        t = t[3:]
        if t[:4].lower() == "json":
            t = t[4:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
        t = t.strip()
    try:
        payload = json.loads(t)
    except json.JSONDecodeError as e:
        raise ResponseRejected(f"omniroute: response content is not valid JSON: {e}") from e
    if not isinstance(payload, dict):
        raise ResponseRejected(
            f"omniroute: response content is a {type(payload).__name__}, not a JSON object"
        )
    return payload


class OmniRouteStageClient(StageClient):
    """Live implementation — one ``POST /chat/completions`` per call.

    Not registered with ``market_intelligence.llm_stage.select_stage_client`` and
    not imported by any pipeline stage (OMR-01 non-goal). The only supported use
    in this milestone is explicit construction in an isolated test or script.
    """

    def __init__(self, config: OmniRouteConfig, *, transport: Optional[object] = None):
        self._config = config
        # Test seam: an ``httpx.BaseTransport`` (e.g. ``httpx.MockTransport``) so
        # tests never touch a real socket or need OmniRoute running.
        self._transport = transport

    def complete(self, *, stage: str, key: str, prompt: str, schema: dict, model: str) -> dict:
        import httpx  # lazy import — mirrors the project's "anthropic" lazy-import style

        resolved_model = model or self._config.model
        if not resolved_model:
            raise StageError(
                f"{stage}: omniroute: no model configured "
                "(pass complete(model=...) or set OmniRouteConfig.model)"
            )

        headers = {"Content-Type": "application/json"}
        api_key = self._config.resolve_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = {
            "model": resolved_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        url = f"{self._config.base_url.rstrip('/')}/chat/completions"
        timeout = httpx.Timeout(self._config.read_timeout, connect=self._config.connect_timeout)
        client_kwargs = {"timeout": timeout}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        try:
            with httpx.Client(**client_kwargs) as client:
                response = client.post(url, headers=headers, json=body)
        except httpx.TimeoutException as e:
            raise StageError(
                _redact(f"{stage}: omniroute: request timed out calling {url}: {e}")
            ) from e
        except httpx.TransportError as e:
            raise StageError(
                _redact(f"{stage}: omniroute: transport error calling {url}: {e}")
            ) from e

        if response.status_code >= 400:
            category = _STATUS_CATEGORY.get(response.status_code, "request failed")
            detail = _error_detail(response)
            raise StageError(
                _redact(
                    f"{stage}: omniroute: HTTP {response.status_code} ({category}) "
                    f"for model {resolved_model!r}: {detail}"
                )
            )

        try:
            data = response.json()
        except ValueError as e:
            raise ResponseRejected(f"omniroute: response body was not valid JSON: {e}") from e

        content = _extract_message_content(data)
        return _extract_json_object(content)
