"""Web Search collector (spec §6.5, §6.7, §14, §16, §22). No network in any test."""

from __future__ import annotations

import datetime as dt
import json
import shutil
import types

import anthropic
import pytest
from tests.conftest import FIXTURES, load_fixture

from market_intelligence.collect import web_search as ws
from market_intelligence.collect.base import (
    DEFAULT_COLLECTORS,
    CollectorError,
    SignalCollectionError,
    collect_signals,
)
from market_intelligence.collect.web_search import (
    WEB_SEARCH_TOOL_TYPE,
    AnthropicWebSearch,
    WebSearchClient,
    WebSearchCollector,
    WebSearchResearch,
    _page_age_to_iso,
    _parse_search_response,
)
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import CaptureMethod, SourceType
from market_intelligence.schema.models import RunConfig, Signal
from market_intelligence.schema.validate import validate_signals

FIXED = dt.datetime(2026, 8, 28, 14, 3, 11, tzinfo=dt.timezone.utc)


class FakeWebSearchClient(WebSearchClient):
    def __init__(self, research: WebSearchResearch):
        self.research_obj = research
        self.calls = 0

    def research(self, *, brief, model, max_uses) -> WebSearchResearch:
        self.calls += 1
        self.brief = brief
        return self.research_obj


class ExplodingClient(WebSearchClient):
    def research(self, *, brief, model, max_uses):
        raise AssertionError("the network / client must not be touched in this test")


def _research() -> WebSearchResearch:
    return decode(WebSearchResearch, load_fixture("web_search_research.json"))


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_2026-08-28_01",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p",
        "signal_sources": ["web_search"],
        "paths": {"data_dir": "data"},
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _run(tmp_path, client, cfg=None):
    cfg = cfg or _cfg()
    return collect_signals(
        cfg,
        project_root=tmp_path,
        collectors={SourceType.WEB_SEARCH: WebSearchCollector(client=client)},
        now=lambda: FIXED,
    )


def _raw_root(tmp_path, run_id="run_2026-08-28_01"):
    return tmp_path / "data" / run_id / "signals" / "raw"


# --- 1. finding -> valid Signal --------------------------------------

def test_findings_become_valid_signals(tmp_path):
    result = _run(tmp_path, FakeWebSearchClient(_research()))
    assert [o.ok for o in result.outcomes] == [True]
    assert len(result.signals) == 2  # 3 of 5 fixture findings are dropped
    assert validate_signals(result.signals, raw_root=_raw_root(tmp_path)) == []
    assert all(isinstance(s, Signal) for s in result.signals)


# --- 2. provenance -------------------------------------------------

def test_provenance_recorded_per_spec_6_5(tmp_path):
    s0 = _run(tmp_path, FakeWebSearchClient(_research())).signals[0]
    p = s0.provenance
    assert p.query_or_reference == "frecuencias 528 hz para dormir tendencia 2026"  # exact query
    assert p.source == "Why 528 Hz sleep tracks are trending in 2026"  # result title
    assert s0.source == p.source  # mirror (§6.1)
    assert p.url == "https://example-news.test/sleep-frequencies-2026"
    assert s0.url == p.url
    assert p.observed_at == "2026-03-03"  # normalised from "March 3, 2026"
    assert s0.observed_at == p.observed_at
    assert p.collected_at == "2026-08-28T14:03:11Z"


# --- 3 & 4. source_type / capture_method ------------------------

def test_source_type_and_capture_method(tmp_path):
    s0 = _run(tmp_path, FakeWebSearchClient(_research())).signals[0]
    assert s0.source_type is SourceType.WEB_SEARCH
    assert s0.provenance.source_type is SourceType.WEB_SEARCH
    assert s0.provenance.capture_method is CaptureMethod.CLAUDE_WEB_SEARCH


# --- 5. raw capture ---------------------------------------------

def test_raw_capture_written_in_spec_6_7_shape(tmp_path):
    _run(tmp_path, FakeWebSearchClient(_research()))
    files = sorted(_raw_root(tmp_path).glob("*.json"))
    assert [f.name for f in files] == [
        "sig_run_2026-08-28_01_0001.json",
        "sig_run_2026-08-28_01_0002.json",
    ]
    cap = json.loads(files[0].read_text())
    assert cap["source_type"] == "web_search"
    assert cap["capture_method"] == "claude_web_search"
    assert cap["query_or_reference"] == "frecuencias 528 hz para dormir tendencia 2026"
    assert cap["url"] == "https://example-news.test/sleep-frequencies-2026"
    assert cap["captured_at"] == "2026-08-28T14:03:11Z"
    assert cap["raw_content"]["evidence"].startswith("A March 2026 news article")


# --- 6. missing date -> UNKNOWN --------------------------------

def test_missing_page_age_yields_unknown_observed_at(tmp_path):
    s1 = _run(tmp_path, FakeWebSearchClient(_research())).signals[1]
    assert s1.observed_at == "UNKNOWN"
    assert s1.provenance.observed_at == "UNKNOWN"


def test_page_age_normalisation_never_guesses():
    assert _page_age_to_iso("2026-03-03") == "2026-03-03"
    assert _page_age_to_iso("March 3, 2026") == "2026-03-03"
    assert _page_age_to_iso("3 Mar 2026") == "2026-03-03"
    assert _page_age_to_iso("03/03/2026") == "2026-03-03"
    assert _page_age_to_iso("3 days ago") is None
    assert _page_age_to_iso("February 2026") is None  # no day -> not invented
    assert _page_age_to_iso(None) is None
    assert _page_age_to_iso("") is None


# --- 7. no URL -> no invention --------------------------------

def test_finding_without_a_backing_result_url_is_dropped(tmp_path):
    signals = _run(tmp_path, FakeWebSearchClient(_research())).signals
    contexts = [s.context for s in signals]
    assert not any("no source URL" in c for c in contexts)  # the null-url finding
    assert not any("not anchored" in c for c in contexts)  # the unbacked finding
    assert all(s.url for s in signals)  # every emitted signal has a real URL


# --- 8. unusable evidence -> not a Signal ---------------------

def test_finding_with_blank_evidence_is_dropped(tmp_path):
    signals = _run(tmp_path, FakeWebSearchClient(_research())).signals
    assert not any("no usable evidence" in s.context for s in signals)
    assert all(s.evidence.strip() for s in signals)


# --- 9. replay recorded, no network -------------------------

def test_replay_recorded_reconstructs_signals_without_a_client(tmp_path):
    fixture_dir = tmp_path / "fixtures" / "run1"
    (fixture_dir / "llm" / "web_search").mkdir(parents=True)
    shutil.copy(
        FIXTURES / "web_search_research.json",
        fixture_dir / "llm" / "web_search" / "research.json",
    )
    cfg = _cfg(
        run_id="run_2026-08-29_01",
        replay={"enabled": True, "fixture_path": str(fixture_dir)},
    )
    result = collect_signals(
        cfg,
        project_root=tmp_path,
        collectors={SourceType.WEB_SEARCH: WebSearchCollector(client=ExplodingClient())},
        now=lambda: FIXED,
    )
    assert result.replay is True
    assert len(result.signals) == 2
    assert validate_signals(
        result.signals, raw_root=_raw_root(tmp_path, "run_2026-08-29_01")
    ) == []


def test_replay_recorded_missing_fixtures_degrades(tmp_path):
    cfg = _cfg(replay={"enabled": True, "fixture_path": str(tmp_path / "nope")})
    with pytest.raises(SignalCollectionError):
        collect_signals(
            cfg,
            project_root=tmp_path,
            collectors={SourceType.WEB_SEARCH: WebSearchCollector(client=ExplodingClient())},
            now=lambda: FIXED,
        )


# --- 10. source failure degrades --------------------------

class RaisingClient(WebSearchClient):
    def research(self, *, brief, model, max_uses):
        raise RuntimeError("simulated API outage")


def test_source_failure_degrades_and_run_continues_with_another_source(tmp_path):
    (tmp_path / "inputs").mkdir()
    shutil.copy(FIXTURES / "internal_data_example.yaml", tmp_path / "inputs" / "internal.yaml")
    cfg = _cfg(
        signal_sources=["web_search", "internal_data"],
        internal_data_path="inputs/internal.yaml",
    )
    from market_intelligence.collect.internal_data import InternalDataCollector

    result = collect_signals(
        cfg,
        project_root=tmp_path,
        collectors={
            SourceType.WEB_SEARCH: WebSearchCollector(client=RaisingClient()),
            SourceType.INTERNAL_DATA: InternalDataCollector(),
        },
        now=lambda: FIXED,
    )
    assert result.sources_used == ["internal_data"]
    assert [f["source"] for f in result.sources_failed] == ["web_search"]
    assert "simulated API outage" in result.sources_failed[0]["reason"]
    assert len(result.signals) == 2  # from internal_data


def test_web_search_only_source_failing_raises(tmp_path):
    with pytest.raises(SignalCollectionError):
        _run(tmp_path, RaisingClient())


# --- 11. DEFAULT_COLLECTORS integration ------------------

def test_registered_in_default_collectors():
    import market_intelligence.collect  # noqa: F401 - triggers registration

    assert SourceType.WEB_SEARCH in DEFAULT_COLLECTORS
    assert isinstance(DEFAULT_COLLECTORS[SourceType.WEB_SEARCH], WebSearchCollector)


def test_default_web_search_collector_without_credentials_degrades(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    with pytest.raises(SignalCollectionError):
        collect_signals(_cfg(), project_root=tmp_path, now=lambda: FIXED)


# --- 12. AnthropicWebSearch <-> current Anthropic API shape (H1) --------
#
# The other tests inject a WebSearchClient stub; these exercise the real
# SDK-facing code (_run_search / _parse_search_response) with a fake SDK.

class _Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _RecordingSDK:
    """Minimal stand-in for anthropic.Anthropic — captures each messages.create call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.messages_seen: list = []
        self.tools_seen: list = []
        self.kwargs_seen: list = []
        outer = self

        class _Messages:
            def create(self, **kw):
                outer.messages_seen.append(kw["messages"])
                outer.tools_seen.append(kw.get("tools"))
                outer.kwargs_seen.append(kw)
                resp = outer._responses.pop(0)
                if isinstance(resp, BaseException):
                    raise resp
                return resp

        self.messages = _Messages()


def test_run_search_sends_the_current_web_search_tool_definition():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[])])
    AnthropicWebSearch(client=sdk)._run_search(
        sdk, model="claude-sonnet-5", brief="b", max_uses=7
    )
    assert WEB_SEARCH_TOOL_TYPE == "web_search_20250305"      # current basic version
    assert sdk.tools_seen[0] == [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": 7}
    ]


def test_run_search_resumes_a_paused_turn_without_stacking_assistant_messages():
    # two consecutive pause_turns then completion — the old code appended and would
    # produce [user, assistant, assistant] (a 400). The fix replaces the list.
    sdk = _RecordingSDK([
        _Block(stop_reason="pause_turn", content=["blocks-1"]),
        _Block(stop_reason="pause_turn", content=["blocks-2"]),
        _Block(stop_reason="end_turn", content=["final"]),
    ])
    done = sdk._responses[-1]
    result = AnthropicWebSearch(client=sdk)._run_search(sdk, model="m", brief="b", max_uses=3)

    assert result is done
    assert [len(m) for m in sdk.messages_seen] == [1, 2, 2]   # never 3+, never stacked
    assert sdk.messages_seen[1][0]["role"] == "user"
    assert sdk.messages_seen[1][1] == {"role": "assistant", "content": ["blocks-1"]}
    assert sdk.messages_seen[2][1] == {"role": "assistant", "content": ["blocks-2"]}  # latest
    # the user message is re-sent unchanged; no "Continue" turn is injected
    assert sdk.messages_seen[2][0] == sdk.messages_seen[0][0]


def test_run_search_raises_after_too_many_pauses():
    sdk = _RecordingSDK([_Block(stop_reason="pause_turn", content=[f"b{i}"]) for i in range(12)])
    with pytest.raises(CollectorError):
        AnthropicWebSearch(client=sdk)._run_search(sdk, model="m", brief="b", max_uses=3)


def test_parse_search_response_reads_the_documented_block_shape():
    msg = _Block(content=[
        _Block(type="text", text="I'll search."),
        _Block(type="server_tool_use", name="web_search", input={"query": "musica sono brasil"}),
        _Block(type="web_search_tool_result", tool_use_id="srvtoolu_x", content=[
            _Block(type="web_search_result", url="https://example.com/a", title="A",
                   page_age="April 30, 2025", encrypted_content="EqgfC…"),  # present, not consumed
        ]),
        _Block(type="text", text="Based on the result, X is trending."),
    ])
    results, queries, analysis = _parse_search_response(msg)
    assert queries == ["musica sono brasil"]
    assert [(r.url, r.title, r.page_age) for r in results] == [
        ("https://example.com/a", "A", "April 30, 2025")
    ]
    assert "trending" in analysis


def test_parse_search_response_tolerates_a_tool_result_error_object():
    msg = _Block(content=[
        _Block(type="server_tool_use", name="web_search", input={"query": "q"}),
        _Block(type="web_search_tool_result", tool_use_id="x",
               content=_Block(type="web_search_tool_result_error",
                              error_code="max_uses_exceeded")),
    ])
    results, queries, _ = _parse_search_response(msg)
    assert results == [] and queries == ["q"]


# --- 13. structuring call: parsing the structured-output response (H2) ------
#
# The live dry run failed here:  "web_search structuring returned non-JSON:
# Expecting value: line 1 column 1 (char 0)"  == json.loads("").  The 2nd call
# uses output_config.format; per the Anthropic docs the JSON arrives in a `text`
# content block, but with adaptive thinking (Sonnet 5 default) a max_tokens cap
# or a refusal can leave the response with no usable text block. The old parser
# defaulted to "" and blindly json.loads()'d it. No network in any test.

_VALID_FINDING = {
    "query": "q", "result_url": "https://x.test/a", "result_title": "A",
    "result_page_age": None, "evidence": "e", "context": "c", "market": "Brasil",
    "language": "pt", "platform": "web", "signal_type": "search_trend",
    "confidence": "LOW", "durability_hint": None, "raw_excerpt": None,
}


def _text_block(s: str) -> "_Block":
    return _Block(type="text", text=s)


def _thinking_block() -> "_Block":
    return _Block(type="thinking", thinking="(summarised thinking is empty on Sonnet 5)")


def _structure(sdk) -> list:
    findings, _msg = AnthropicWebSearch(client=sdk)._structure(
        sdk, model="claude-sonnet-5", brief="b", analysis="a", results=[], queries=[]
    )
    return findings


def test_structure_parses_json_from_the_documented_text_block():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[
        _text_block(json.dumps({"findings": [_VALID_FINDING]})),
    ])])
    findings = _structure(sdk)
    assert len(findings) == 1
    assert findings[0].result_url == "https://x.test/a"


def test_structure_skips_thinking_blocks_before_the_text_block():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[
        _thinking_block(),
        _text_block('{"findings": []}'),
    ])])
    assert _structure(sdk) == []


def test_structure_concatenates_multiple_text_blocks():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[
        _text_block('{"findings":'),
        _text_block(' []}'),
    ])])
    assert _structure(sdk) == []


def test_structure_max_tokens_with_no_json_raises_a_clear_error_not_json_loads_empty():
    sdk = _RecordingSDK([_Block(stop_reason="max_tokens", content=[_thinking_block()])])
    with pytest.raises(CollectorError) as ei:
        _structure(sdk)
    m = str(ei.value)
    assert "max_tokens" in m
    assert "line 1 column 1" not in m       # not the opaque json.loads("") message
    assert "thinking" in m                  # names the block types actually returned


def test_structure_refusal_is_reported_and_leaks_nothing():
    sdk = _RecordingSDK([_Block(
        stop_reason="refusal",
        content=[],
        stop_details=_Block(type="refusal", category="frontier_llm", explanation="x"),
    )])
    with pytest.raises(CollectorError) as ei:
        _structure(sdk)
    assert "refus" in str(ei.value).lower()


def test_structure_empty_or_whitespace_text_is_rejected():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[_text_block("   ")])])
    with pytest.raises(CollectorError):
        _structure(sdk)


def test_structure_no_content_at_all_is_rejected():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[])])
    with pytest.raises(CollectorError):
        _structure(sdk)


def test_structure_non_json_text_is_rejected_with_a_redacted_preview():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[
        _text_block("Sorry, I can't help with that. sk-ant-api03-LEAKED_SECRET_VALUE"),
    ])])
    with pytest.raises(CollectorError) as ei:
        _structure(sdk)
    m = str(ei.value)
    assert "sk-ant-api03-LEAKED_SECRET_VALUE" not in m
    assert "not valid JSON" in m


def test_structure_json_that_is_not_an_object_is_rejected():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[_text_block("[1, 2, 3]")])])
    with pytest.raises(CollectorError):
        _structure(sdk)


def test_structure_requests_output_budget_for_thinking_plus_json():
    sdk = _RecordingSDK([_Block(stop_reason="end_turn", content=[_text_block('{"findings": []}')])])
    _structure(sdk)
    kw = sdk.kwargs_seen[0]
    assert kw["output_config"]["format"]["type"] == "json_schema"
    assert kw["max_tokens"] >= 16000     # 8000 truncated the real run mid-thinking


def test_research_records_the_structuring_response_for_diagnosability():
    search_msg = _Block(stop_reason="end_turn", content=[
        _Block(type="server_tool_use", name="web_search", input={"query": "q"}),
        _Block(type="web_search_tool_result", tool_use_id="x", content=[
            _Block(type="web_search_result", url="https://x.test/a", title="A", page_age=None),
        ]),
        _Block(type="text", text="analysis"),
    ])
    structuring_msg = _Block(stop_reason="end_turn", content=[_text_block('{"findings": []}')])
    sdk = _RecordingSDK([search_msg, structuring_msg])
    research = AnthropicWebSearch(client=sdk).research(
        brief="b", model="claude-sonnet-5", max_uses=3
    )
    assert "search" in research.provider_response
    assert "structuring" in research.provider_response


# --- 14. timeout / network resilience of the Anthropic calls (H3) ----------
#
# The 2nd live dry run was Ctrl+C'd while blocked in `socket.recv` waiting for
# the server-side web search. The anthropic SDK default is a 600 s read timeout
# retried twice (~30 min per call) and `_run_search` loops up to 6 times on
# `pause_turn`. These tests pin an explicit, bounded timeout + retry, a
# wall-clock budget for the pause loop, and a diagnostic error. No network.


class _CapturingAnthropic:
    """Stands in for `anthropic.Anthropic` and records the constructor kwargs."""

    last_kwargs: dict = {}

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs
        self.messages = None


def _timeout_exc() -> anthropic.APITimeoutError:
    req = types.SimpleNamespace(
        method="POST",
        url="https://api.anthropic.com/v1/messages",
        headers={"x-api-key": "sk-ant-api03-MUST-NOT-LEAK"},
    )
    return anthropic.APITimeoutError(request=req)


def test_build_client_sets_an_explicit_bounded_timeout_and_retry(monkeypatch):
    monkeypatch.setattr(anthropic, "Anthropic", _CapturingAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-placeholder")
    AnthropicWebSearch()._build_client()

    kw = _CapturingAnthropic.last_kwargs
    assert kw.get("max_retries") is not None and kw["max_retries"] <= 1   # SDK default is 2
    timeout = kw.get("timeout")
    assert timeout is not None
    read = float(getattr(timeout, "read", timeout))
    assert 60.0 <= read <= 480.0        # explicit and well under the 600 s default


def test_search_call_timeout_becomes_a_diagnostic_collector_error():
    sdk = _RecordingSDK([_timeout_exc()])
    with pytest.raises(CollectorError) as ei:
        AnthropicWebSearch(client=sdk)._run_search(sdk, model="m", brief="b", max_uses=5)
    msg = str(ei.value)
    assert "timed out" in msg.lower() or "did not return" in msg.lower()
    assert "search" in msg.lower()
    assert "sk-ant-api03-MUST-NOT-LEAK" not in msg


def test_structuring_call_timeout_becomes_a_diagnostic_collector_error():
    sdk = _RecordingSDK([_timeout_exc()])
    with pytest.raises(CollectorError) as ei:
        AnthropicWebSearch(client=sdk)._structure(
            sdk, model="m", brief="b", analysis="a", results=[], queries=[]
        )
    msg = str(ei.value)
    assert "timed out" in msg.lower() or "did not return" in msg.lower()
    assert "structur" in msg.lower()
    assert "sk-ant" not in msg


def test_search_phase_has_a_wall_clock_budget_across_pause_turn(monkeypatch):
    ticks = iter([0.0, 1.0, ws._SEARCH_PHASE_BUDGET_S + 1.0, ws._SEARCH_PHASE_BUDGET_S + 2.0])
    monkeypatch.setattr(ws, "_monotonic", lambda: next(ticks))
    sdk = _RecordingSDK([_Block(stop_reason="pause_turn", content=[f"b{i}"]) for i in range(6)])
    with pytest.raises(CollectorError) as ei:
        AnthropicWebSearch(client=sdk)._run_search(sdk, model="m", brief="b", max_uses=5)
    assert "budget" in str(ei.value).lower()
    assert len(sdk.messages_seen) <= 2       # stopped early — not all 6 iterations


def test_normal_research_flow_is_unaffected_by_the_timeout_hardening():
    search_msg = _Block(stop_reason="end_turn", content=[
        _Block(type="server_tool_use", name="web_search", input={"query": "q"}),
        _Block(type="web_search_tool_result", tool_use_id="x", content=[
            _Block(type="web_search_result", url="https://x.test/a", title="A", page_age=None),
        ]),
        _Block(type="text", text="analysis"),
    ])
    structuring_msg = _Block(stop_reason="end_turn", content=[
        _text_block(json.dumps({"findings": [_VALID_FINDING]})),
    ])
    sdk = _RecordingSDK([search_msg, structuring_msg])
    research = AnthropicWebSearch(client=sdk).research(
        brief="b", model="claude-sonnet-5", max_uses=5
    )
    assert len(research.findings) == 1
    assert research.results[0].url == "https://x.test/a"
