"""external_llm_gateway.omniroute_client — decision OMR-01 (knowledge/DECISIONS-NEEDED.md).

Isolated adapter test. No real network, no real OmniRoute — the HTTP transport is
always mocked via ``httpx.MockTransport``. Mirrors the style of
``tests/test_llm_stage.py`` for the sibling ``StageClient`` implementations.
"""

from __future__ import annotations

import json

import httpx
import pytest

from external_llm_gateway.config import OmniRouteConfig
from external_llm_gateway.omniroute_client import OmniRouteStageClient
from market_intelligence.llm_stage import ResponseRejected, StageClient, StageError


def _cfg(**over) -> OmniRouteConfig:
    kwargs = {"model": "groq/openai/gpt-oss-120b"}
    kwargs.update(over)
    return OmniRouteConfig(**kwargs)


def _chat_response(content: str, *, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        json={
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
        },
    )


def _error_response(status: int, message: str) -> httpx.Response:
    return httpx.Response(status, json={"error": {"message": message}})


def _client_with_handler(handler, **cfg_over) -> OmniRouteStageClient:
    transport = httpx.MockTransport(handler)
    return OmniRouteStageClient(_cfg(**cfg_over), transport=transport)


# --- contract conformance -------------------------------------------------

def test_omniroute_client_implements_stage_client():
    assert isinstance(_client_with_handler(lambda r: _chat_response("{}")), StageClient)


# --- valid response ---------------------------------------------------

def test_valid_response_returns_the_parsed_json_object():
    def handler(request):
        return _chat_response(json.dumps({"ok": True, "n": 1}))

    client = _client_with_handler(handler)
    out = client.complete(stage="framing", key="k1", prompt="p", schema={}, model="")
    assert out == {"ok": True, "n": 1}


def test_valid_response_tolerates_a_markdown_code_fence():
    def handler(request):
        return _chat_response("```json\n" + json.dumps({"a": 1}) + "\n```")

    client = _client_with_handler(handler)
    out = client.complete(stage="framing", key="k1", prompt="p", schema={}, model="")
    assert out == {"a": 1}


# --- request construction ---------------------------------------------

def test_payload_is_sent_correctly():
    captured = {}

    def handler(request):
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return _chat_response(json.dumps({"ok": True}))

    client = _client_with_handler(handler, model="groq/openai/gpt-oss-120b")
    client.complete(stage="matching", key="k2", prompt="the prompt text", schema={}, model="")

    assert captured["method"] == "POST"
    assert captured["url"] == "http://localhost:20128/v1/chat/completions"
    assert captured["body"] == {
        "model": "groq/openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "the prompt text"}],
        "stream": False,
    }


def test_model_and_endpoint_are_configurable():
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["model"] = json.loads(request.content)["model"]
        return _chat_response(json.dumps({"ok": True}))

    client = _client_with_handler(
        handler, base_url="https://example.internal/v1", model="cerebras/gpt-oss-120b"
    )
    client.complete(stage="evaluation", key="k3", prompt="p", schema={}, model="")

    assert captured["url"] == "https://example.internal/v1/chat/completions"
    assert captured["model"] == "cerebras/gpt-oss-120b"


def test_a_model_passed_to_complete_overrides_the_config_default():
    captured = {}

    def handler(request):
        captured["model"] = json.loads(request.content)["model"]
        return _chat_response(json.dumps({"ok": True}))

    client = _client_with_handler(handler, model="groq/openai/gpt-oss-120b")
    client.complete(stage="framing", key="k4", prompt="p", schema={}, model="cerebras/gpt-oss-120b")
    assert captured["model"] == "cerebras/gpt-oss-120b"


# --- invalid response content -------------------------------------------

def test_non_json_message_content_is_a_response_rejected():
    def handler(request):
        return _chat_response("this is not JSON at all")

    client = _client_with_handler(handler)
    with pytest.raises(ResponseRejected):
        client.complete(stage="framing", key="k5", prompt="p", schema={}, model="")


def test_a_response_with_no_choices_is_a_response_rejected():
    def handler(request):
        return httpx.Response(200, json={"id": "x", "choices": []})

    client = _client_with_handler(handler)
    with pytest.raises(ResponseRejected):
        client.complete(stage="framing", key="k6", prompt="p", schema={}, model="")


def test_a_non_json_http_body_is_a_response_rejected():
    def handler(request):
        return httpx.Response(200, text="not json at the transport level either")

    client = _client_with_handler(handler)
    with pytest.raises(ResponseRejected):
        client.complete(stage="framing", key="k7", prompt="p", schema={}, model="")


# --- HTTP error taxonomy (spec: distinguish at least these four) -------

def test_http_400_is_a_stage_error_naming_invalid_model():
    def handler(request):
        return _error_response(400, "Model 'x' is not available in the active live catalog.")

    client = _client_with_handler(handler)
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k8", prompt="p", schema={}, model="")
    assert "400" in str(ei.value)


def test_http_402_is_a_stage_error_naming_billing():
    def handler(request):
        return _error_response(402, "Payment required to access this resource.")

    client = _client_with_handler(handler)
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k9", prompt="p", schema={}, model="")
    assert "402" in str(ei.value)
    assert "billing" in str(ei.value).lower()


def test_http_503_is_a_stage_error_naming_unavailable():
    def handler(request):
        return _error_response(503, "This model is currently experiencing high demand.")

    client = _client_with_handler(handler)
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k10", prompt="p", schema={}, model="")
    assert "503" in str(ei.value)
    assert "unavailable" in str(ei.value).lower()


def test_http_504_is_a_stage_error_naming_gateway_timeout():
    def handler(request):
        return _error_response(
            504, "Request exceeded OmniRoute's local rate-limit execution expiration."
        )

    client = _client_with_handler(handler)
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k11", prompt="p", schema={}, model="")
    assert "504" in str(ei.value)
    assert "timeout" in str(ei.value).lower()


def test_an_unmapped_http_error_is_still_a_stage_error():
    def handler(request):
        return _error_response(500, "internal error")

    client = _client_with_handler(handler)
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k12", prompt="p", schema={}, model="")
    assert "500" in str(ei.value)


# --- transport-level failures (never a raw httpx exception) -----------

def test_a_read_timeout_becomes_a_stage_error_not_a_raw_httpx_exception():
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    client = _client_with_handler(handler)
    with pytest.raises(StageError):
        client.complete(stage="framing", key="k13", prompt="p", schema={}, model="")


def test_a_connect_error_becomes_a_stage_error_not_a_raw_httpx_exception():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = _client_with_handler(handler)
    with pytest.raises(StageError):
        client.complete(stage="framing", key="k14", prompt="p", schema={}, model="")


# --- credentials --------------------------------------------------------

def test_no_credential_configured_sends_no_authorization_header(monkeypatch):
    monkeypatch.delenv("OMNIROUTE_API_KEY", raising=False)
    captured = {}

    def handler(request):
        captured["headers"] = dict(request.headers)
        return _chat_response(json.dumps({"ok": True}))

    client = _client_with_handler(handler)
    client.complete(stage="framing", key="k15", prompt="p", schema={}, model="")
    assert "authorization" not in captured["headers"]


def test_credential_from_env_is_sent_as_a_bearer_token(monkeypatch):
    monkeypatch.setenv("OMNIROUTE_API_KEY", "sk-omr-super-secret-value")
    captured = {}

    def handler(request):
        captured["headers"] = dict(request.headers)
        return _chat_response(json.dumps({"ok": True}))

    client = _client_with_handler(handler)
    client.complete(stage="framing", key="k16", prompt="p", schema={}, model="")
    assert captured["headers"]["authorization"] == "Bearer sk-omr-super-secret-value"


def test_the_secret_never_appears_in_a_raised_error_message(monkeypatch):
    monkeypatch.setenv("OMNIROUTE_API_KEY", "sk-omr-super-secret-value")

    def handler(request):
        return _error_response(400, "bad request")

    client = _client_with_handler(handler)
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k17", prompt="p", schema={}, model="")
    assert "sk-omr-super-secret-value" not in str(ei.value)


def test_a_custom_api_key_env_var_name_is_honoured(monkeypatch):
    monkeypatch.delenv("OMNIROUTE_API_KEY", raising=False)
    monkeypatch.setenv("MY_OTHER_OMNIROUTE_KEY", "sk-other-secret")
    captured = {}

    def handler(request):
        captured["headers"] = dict(request.headers)
        return _chat_response(json.dumps({"ok": True}))

    client = _client_with_handler(handler, api_key_env_var="MY_OTHER_OMNIROUTE_KEY")
    client.complete(stage="framing", key="k18", prompt="p", schema={}, model="")
    assert captured["headers"]["authorization"] == "Bearer sk-other-secret"


# --- no fallback ----------------------------------------------------------

def test_a_failure_triggers_exactly_one_request_never_a_fallback_attempt():
    calls = []

    def handler(request):
        calls.append(request)
        return _error_response(402, "payment required")

    client = _client_with_handler(handler)
    with pytest.raises(StageError):
        client.complete(stage="framing", key="k19", prompt="p", schema={}, model="")
    assert len(calls) == 1
