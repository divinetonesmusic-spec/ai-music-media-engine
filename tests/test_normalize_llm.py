"""Claude-assisted Signal Normalization (spec §18 component 2, §19, §22). No network."""

from __future__ import annotations

import types

import anthropic
import pytest
from tests.conftest import FIXTURES, load_fixture

from market_intelligence.normalize import llm as norm_llm
from market_intelligence.normalize.deterministic import NormalizationResult
from market_intelligence.normalize.llm import (
    AnthropicNormalization,
    MissingFixtureError,
    NormalizationClient,
    NormalizationError,
    ResponseRejected,
    normalize_with_llm,
    validate_llm_response,
)
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.enums import SignalType
from market_intelligence.schema.models import RunConfig, Signal
from market_intelligence.schema.validate import validate_signal

_REPLAY_FIXTURE = FIXTURES / "normalize" / "llm_replay"


def _sigs():
    return [decode(Signal, d) for d in load_fixture("normalize/llm/ambiguous_signals.json")]


def _sig(sid):
    return next(s for s in _sigs() if s.signal_id == sid)


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_norm_llm",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p",
        "signal_sources": ["web_search"],
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _replay_cfg(**over) -> RunConfig:
    return _cfg(replay={"enabled": True, "fixture_path": str(_REPLAY_FIXTURE)}, **over)


def _resp(sid, suggestions, rationale="ok", confidence=None):
    out = {"signal_id": sid, "suggestions": suggestions, "rationale": rationale}
    if confidence is not None:
        out["confidence"] = confidence
    return out


def _run(signals, client, cfg=None):
    return normalize_with_llm(signals, config=cfg or _cfg(), project_root=".", client=client)


class StubClient(NormalizationClient):
    def __init__(self, responses: dict):
        self.responses = responses
        self.calls: list[str] = []

    def classify(self, signal_id, *, context, ambiguous_fields, model):
        self.calls.append(signal_id)
        if signal_id not in self.responses:
            raise MissingFixtureError(f"stub has no response for {signal_id}")
        return self.responses[signal_id]


class ForbiddenClient(NormalizationClient):
    def classify(self, *a, **k):
        raise AssertionError("the model / network must not be contacted here")


# --- ambiguity detection --------------------------------------

def test_only_underspecified_fields_are_offered_to_the_model():
    stub = StubClient({s.signal_id: _resp(s.signal_id, {}) for s in _sigs()})
    changes = {c.signal_id: c for c in _run(_sigs(), stub).changes}
    assert set(changes["sig_norm_llm_0001"].preserved_fields) == {"market"}
    assert set(changes["sig_norm_llm_0002"].preserved_fields) == {"market", "language"}
    assert set(changes["sig_norm_llm_0003"].preserved_fields) == {"signal_type"}
    assert set(changes["sig_norm_llm_0004"].preserved_fields) == {"durability_hint"}


def test_signal_with_no_ambiguous_field_is_passed_through_without_a_model_call():
    sig = _sig("sig_norm_llm_0004")
    fully_specified = decode(Signal, {**encode(sig), "durability_hint": "STRUCTURAL"})
    r = _run([fully_specified], ForbiddenClient())
    assert r.signals[0] is fully_specified
    assert r.changes[0].applied is False
    assert r.changes[0].rationale == "no ambiguous fields"


# --- applying suggestions ------------------------------------

def test_an_ambiguous_field_is_normalized():
    stub = StubClient({"sig_norm_llm_0001": _resp(
        "sig_norm_llm_0001", {"market": "Mercados hispanohablantes"}, confidence="MEDIUM"
    )})
    r = _run([_sig("sig_norm_llm_0001")], stub)
    out, ch = r.signals[0], r.changes[0]
    assert out.market == "Mercados hispanohablantes"
    assert validate_signal(out) == []
    assert ch.applied is True and ch.llm_confidence == "MEDIUM"
    assert [(s.field, s.from_value, s.to_value, s.applied) for s in ch.suggestions] == [
        ("market", "UNKNOWN", "Mercados hispanohablantes", True)
    ]


def test_a_field_already_set_by_the_collector_is_preserved():
    # 0001's language is 'es' (not ambiguous); a suggestion for it must be rejected
    stub = StubClient({"sig_norm_llm_0001": _resp("sig_norm_llm_0001", {"language": "en"})})
    r = _run([_sig("sig_norm_llm_0001")], stub)
    assert r.signals[0].language == "es"
    assert r.changes[0].applied is False
    assert "non-ambiguous" in r.changes[0].rejection_reason


def test_unknown_stays_unknown_when_the_model_cannot_decide():
    stub = StubClient({"sig_norm_llm_0002": _resp("sig_norm_llm_0002", {"language": "es"})})
    r = _run([_sig("sig_norm_llm_0002")], stub)
    assert r.signals[0].language == "es"
    assert r.signals[0].market == "UNKNOWN"
    assert "market" in r.changes[0].preserved_fields


def test_empty_suggestions_leave_the_signal_unchanged():
    stub = StubClient({"sig_norm_llm_0004": _resp("sig_norm_llm_0004", {})})
    r = _run([_sig("sig_norm_llm_0004")], stub)
    assert r.signals[0].durability_hint is None
    assert r.changes[0].applied is False
    assert r.changes[0].preserved_fields == ["durability_hint"]


def test_technical_default_signal_type_may_be_refined():
    resp = _resp("sig_norm_llm_0003", {"signal_type": "search_trend"})
    r = _run([_sig("sig_norm_llm_0003")], StubClient({"sig_norm_llm_0003": resp}))
    assert r.signals[0].signal_type is SignalType.SEARCH_TREND


# --- immutability -------------------------------------------

def test_evidence_provenance_metrics_ids_are_never_touched():
    sig = _sig("sig_norm_llm_0003")
    before = encode(sig)
    resp = _resp("sig_norm_llm_0003", {"signal_type": "content_format"})
    out = _run([sig], StubClient({"sig_norm_llm_0003": resp})).signals[0]
    assert encode(sig) == before  # original untouched
    assert out.signal_id == sig.signal_id
    assert out.evidence == sig.evidence
    assert encode(out.provenance) == encode(sig.provenance)
    assert (out.source, out.observed_at, out.collected_at, out.raw_ref, out.metrics) == (
        sig.source, sig.observed_at, sig.collected_at, sig.raw_ref, sig.metrics
    )


# --- rejecting bad model output --------------------------

def test_invalid_taxonomy_value_is_rejected():
    resp = load_fixture("normalize/llm/response_invalid_market.json")
    with pytest.raises(ResponseRejected):
        validate_llm_response(resp, signal_id="sig_norm_llm_0001", ambiguous_fields=["market"])
    r = _run([_sig("sig_norm_llm_0001")], StubClient({"sig_norm_llm_0001": resp}))
    assert r.signals[0].market == "UNKNOWN"
    assert r.changes[0].applied is False


def test_response_with_a_forbidden_field_is_rejected():
    resp = load_fixture("normalize/llm/response_forbidden_field.json")
    with pytest.raises(ResponseRejected):
        validate_llm_response(resp, signal_id="sig_norm_llm_0001", ambiguous_fields=["market"])
    out = _run([_sig("sig_norm_llm_0001")], StubClient({"sig_norm_llm_0001": resp})).signals[0]
    assert out.market == "UNKNOWN"
    assert "FABRICATED" not in out.evidence
    assert out.url is None


def test_forbidden_suggestion_key_is_rejected():
    with pytest.raises(ResponseRejected):
        validate_llm_response(
            _resp("sig_norm_llm_0001", {"url": "http://x"}),
            signal_id="sig_norm_llm_0001", ambiguous_fields=["market"],
        )


def test_signal_id_mismatch_is_rejected():
    with pytest.raises(ResponseRejected):
        validate_llm_response(
            _resp("someone_else", {}),
            signal_id="sig_norm_llm_0001", ambiguous_fields=["market"],
        )


def test_the_model_cannot_add_a_new_signal():
    stub = StubClient({
        "sig_norm_llm_0001": _resp("sig_norm_llm_0001", {}),
        "sig_ghost": _resp("sig_ghost", {"market": "Brasil"}),
    })
    r = _run([_sig("sig_norm_llm_0001")], stub)
    assert [s.signal_id for s in r.signals] == ["sig_norm_llm_0001"]
    assert stub.calls == ["sig_norm_llm_0001"]


# --- replay -----------------------------------------------

def test_replay_recorded_works_offline():
    r = _run(_sigs(), ForbiddenClient(), cfg=_replay_cfg())
    assert r.replay is True and r.llm_mode == "recorded"
    by_id = {s.signal_id: s for s in r.signals}
    assert by_id["sig_norm_llm_0001"].market == "Mercados hispanohablantes"
    assert by_id["sig_norm_llm_0002"].language == "es"
    assert by_id["sig_norm_llm_0002"].market == "UNKNOWN"  # partial fixture
    assert by_id["sig_norm_llm_0003"].signal_type is SignalType.SEARCH_TREND
    assert by_id["sig_norm_llm_0004"].durability_hint is None  # empty-suggestions fixture
    assert all(validate_signal(s) == [] for s in r.signals)


def test_replay_missing_fixture_degrades_without_touching_the_network():
    base = encode(_sig("sig_norm_llm_0001"))
    extra = decode(Signal, {
        **base,
        "signal_id": "sig_norm_llm_9999",
        "raw_ref": "data/run_norm_llm/signals/raw/sig_norm_llm_9999.json",
    })
    r = _run([extra], ForbiddenClient(), cfg=_replay_cfg())
    assert r.signals[0].market == "UNKNOWN"  # preserved, not inferred
    assert r.changes[0].applied is False
    assert "fixture" in r.changes[0].rejection_reason


def test_replay_never_constructs_the_anthropic_client():
    # ForbiddenClient.classify raises if called; in recorded replay it must not be called
    _run(_sigs(), ForbiddenClient(), cfg=_replay_cfg())


# --- determinism outside the LLM --------------------------

def test_pipeline_structure_is_stable_across_different_model_outputs():
    ra = _run([_sig("sig_norm_llm_0001")], StubClient({
        "sig_norm_llm_0001": _resp("sig_norm_llm_0001", {"market": "Brasil"}),
    }))
    rb = _run([_sig("sig_norm_llm_0001")], StubClient({
        "sig_norm_llm_0001": _resp("sig_norm_llm_0001", {"market": "English-speaking markets"}),
    }))
    assert [s.signal_id for s in ra.signals] == [s.signal_id for s in rb.signals]
    assert [c.signal_id for c in ra.changes] == [c.signal_id for c in rb.changes]
    assert ra.signals[0].market != rb.signals[0].market  # only the value differs


def test_accepts_a_normalization_result_and_reads_deduplicated_signals():
    nr = NormalizationResult(
        valid_signals=[], invalid_signals=[],
        deduplicated_signals=[_sig("sig_norm_llm_0001")],
        discarded_signal_ids=[], dedup_reasons=[],
    )
    stub = StubClient({"sig_norm_llm_0001": _resp("sig_norm_llm_0001", {})})
    r = normalize_with_llm(nr, config=_cfg(), project_root=".", client=stub)
    assert [s.signal_id for s in r.signals] == ["sig_norm_llm_0001"]


def test_no_credentials_degrades_every_signal_without_a_network_call(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    r = normalize_with_llm(_sigs(), config=_cfg(), project_root=".")  # real client, no creds
    assert [encode(s) for s in r.signals] == [encode(s) for s in _sigs()]
    assert all(c.applied is False for c in r.changes)
    assert all("credential" in (c.rejection_reason or "").lower() for c in r.changes)


# --- timeout / retry policy (spec §14) -----------------------------------


class _CapturingAnthropic:
    last_kwargs: dict = {}

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs
        self.messages = None


def test_anthropic_client_is_built_with_a_bounded_timeout_and_retry(monkeypatch):
    monkeypatch.setattr(anthropic, "Anthropic", _CapturingAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-placeholder")
    AnthropicNormalization()._build_client()

    kw = _CapturingAnthropic.last_kwargs
    assert kw.get("max_retries") is not None and kw["max_retries"] <= 1   # SDK default is 2
    read = float(getattr(kw.get("timeout"), "read", kw.get("timeout")))
    assert 30.0 <= read <= 480.0


def test_timeout_becomes_a_normalization_error_without_leaking_the_key():
    req = types.SimpleNamespace(
        method="POST", url="https://api.anthropic.com/v1/messages",
        headers={"x-api-key": "sk-ant-api03-MUST-NOT-LEAK"},
    )

    class _Messages:
        def create(self, **kw):
            raise anthropic.APITimeoutError(request=req)

    class _SDK:
        messages = _Messages()

    with pytest.raises(NormalizationError) as ei:
        AnthropicNormalization(client=_SDK()).classify(
            "sig_1", context={}, ambiguous_fields=["market"], model="m"
        )
    msg = str(ei.value)
    assert "did not return" in msg or "timed out" in msg.lower()
    assert "sk-ant-api03-MUST-NOT-LEAK" not in msg
    assert norm_llm._READ_TIMEOUT >= 60
