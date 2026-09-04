"""harness.py tests — NO network, NO real OmniRoute, NO real Anthropic call.

Mirrors the fake-client injection style already used by
tests/test_llm_stage.py and tests/test_external_llm_gateway_omniroute_client.py
in the main project suite.
"""

from __future__ import annotations

import json

import httpx

from market_intelligence.normalize.llm import NormalizationClient, NormalizationError
from market_intelligence.normalize.llm import ResponseRejected as NormResponseRejected
from omr03 import harness


def test_dataset_loads_exactly_the_four_inherited_cases():
    cases = harness.load_dataset()
    ids = sorted(c["signal"]["signal_id"] for c in cases)
    assert ids == [
        "sig_norm_llm_0001", "sig_norm_llm_0002", "sig_norm_llm_0003", "sig_norm_llm_0004",
    ]


def test_every_case_has_a_ground_truth_file():
    for case in harness.load_dataset():
        gt = harness.load_ground_truth(case["signal"]["signal_id"])
        assert set(gt["fields"]) == set(case["case_metadata"]["ambiguous_fields"])


def test_signal_from_case_decodes_a_real_signal():
    case = harness.load_dataset()[0]
    sig = harness.signal_from_case(case)
    assert sig.signal_id == case["signal"]["signal_id"]


# --- call_claude -----------------------------------------------------------

class _FakeNormClient(NormalizationClient):
    def __init__(self, response=None, raise_exc=None):
        self._response = response
        self._raise = raise_exc

    def classify(self, signal_id, *, context, ambiguous_fields, model):
        if self._raise:
            raise self._raise
        return self._response


def _case_and_signal(case_id="sig_norm_llm_0001"):
    case = next(c for c in harness.load_dataset() if c["signal"]["signal_id"] == case_id)
    return case, harness.signal_from_case(case)


def test_call_claude_success_returns_suggestions():
    _, sig = _case_and_signal()
    fake = _FakeNormClient(response={
        "signal_id": sig.signal_id,
        "suggestions": {"market": "Mercados hispanohablantes"},
        "rationale": "x", "confidence": "MEDIUM",
    })
    out = harness.call_claude(sig, ["market"], client=fake)
    assert out.suggestions == {"market": "Mercados hispanohablantes"}
    assert out.technical_error is None and out.rejected_reason is None


def test_call_claude_technical_error_never_raises():
    _, sig = _case_and_signal()
    fake = _FakeNormClient(raise_exc=NormalizationError("no credentials"))
    out = harness.call_claude(sig, ["market"], client=fake)
    assert out.technical_error == "no credentials"
    assert out.suggestions is None


def test_call_claude_response_rejected_from_client():
    _, sig = _case_and_signal()
    fake = _FakeNormClient(raise_exc=NormResponseRejected("bad json"))
    out = harness.call_claude(sig, ["market"], client=fake)
    assert out.rejected_reason == "bad json"


def test_call_claude_response_rejected_from_deterministic_validator():
    _, sig = _case_and_signal()
    # a forbidden top-level key -> validate_llm_response rejects it, even though
    # the client itself returned successfully (no exception).
    fake = _FakeNormClient(response={
        "signal_id": sig.signal_id, "suggestions": {"market": "Brasil"},
        "rationale": "x", "evidence": "FABRICATED",
    })
    out = harness.call_claude(sig, ["market"], client=fake)
    assert out.rejected_reason is not None
    assert out.suggestions is None
    assert out.raw_response_safe is not None  # raw is kept even on rejection


# --- call_groq ---------------------------------------------------------------

def _omr_client(handler) -> "harness.OmniRouteStageClient":
    from external_llm_gateway.config import OmniRouteConfig
    from external_llm_gateway.omniroute_client import OmniRouteStageClient

    return OmniRouteStageClient(
        OmniRouteConfig(model="groq/openai/gpt-oss-120b"),
        transport=httpx.MockTransport(handler),
    )


def _chat_response(content: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def test_call_groq_success_returns_suggestions():
    _, sig = _case_and_signal()

    def handler(request):
        return _chat_response(json.dumps({
            "signal_id": sig.signal_id,
            "suggestions": {"market": "Mercados hispanohablantes"},
            "rationale": "x", "confidence": "MEDIUM",
        }))

    out = harness.call_groq(sig, ["market"], client=_omr_client(handler))
    assert out.suggestions == {"market": "Mercados hispanohablantes"}


def test_call_groq_http_error_becomes_technical_error_not_raw_exception():
    _, sig = _case_and_signal()

    def handler(request):
        return httpx.Response(402, json={"error": {"message": "payment required"}})

    out = harness.call_groq(sig, ["market"], client=_omr_client(handler))
    assert out.technical_error is not None
    assert "402" in out.technical_error
    assert out.suggestions is None


def test_call_groq_non_json_content_is_rejected_not_a_crash():
    _, sig = _case_and_signal()

    def handler(request):
        return _chat_response("not json at all")

    out = harness.call_groq(sig, ["market"], client=_omr_client(handler))
    assert out.rejected_reason is not None


def test_call_groq_invalid_taxonomy_value_is_rejected_by_shared_validator():
    _, sig = _case_and_signal()

    def handler(request):
        return _chat_response(json.dumps({
            "signal_id": sig.signal_id, "suggestions": {"market": "Germany"}, "rationale": "x",
        }))

    out = harness.call_groq(sig, ["market"], client=_omr_client(handler))
    assert out.rejected_reason is not None
    assert "market" in out.rejected_reason.lower() or "Germany" in out.rejected_reason


def test_call_groq_prompt_includes_the_json_schema_instruction():
    _, sig = _case_and_signal()
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return _chat_response(
            json.dumps({"signal_id": sig.signal_id, "suggestions": {}, "rationale": "x"})
        )

    harness.call_groq(sig, ["market"], client=_omr_client(handler))
    assert "JSON Schema" in captured["body"]["messages"][0]["content"]


# --- run_all -----------------------------------------------------------------

def test_run_all_calls_both_providers_for_every_case_exactly_once():
    calls = {"claude": 0, "groq": 0}

    class CountingClaude(NormalizationClient):
        def classify(self, signal_id, *, context, ambiguous_fields, model):
            calls["claude"] += 1
            return {"signal_id": signal_id, "suggestions": {}, "rationale": "x"}

    def handler(request):
        calls["groq"] += 1
        # doesn't matter which signal_id the harness sent this call for: echo
        # back whatever validate_llm_response will actually check against by
        # re-reading it from the request body's embedded signal JSON.
        body_text = json.loads(request.content)["messages"][0]["content"]
        sid = body_text.split('"signal_id": "')[1].split('"')[0]
        return _chat_response(json.dumps({"signal_id": sid, "suggestions": {}, "rationale": "x"}))

    run = harness.run_all(claude_client=CountingClaude(), groq_client=_omr_client(handler))
    assert calls["claude"] == 4
    assert calls["groq"] == 4
    assert len(run["results"]) == 4
    assert run["claude_model"] == harness.CLAUDE_MODEL
    assert run["groq_model"] == harness.GROQ_MODEL
