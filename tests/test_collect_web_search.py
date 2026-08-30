"""Web Search collector (spec §6.5, §6.7, §14, §16, §22). No network in any test."""

from __future__ import annotations

import datetime as dt
import json
import shutil

import pytest
from tests.conftest import FIXTURES, load_fixture

from market_intelligence.collect.base import (
    DEFAULT_COLLECTORS,
    SignalCollectionError,
    collect_signals,
)
from market_intelligence.collect.web_search import (
    WebSearchClient,
    WebSearchCollector,
    WebSearchResearch,
    _page_age_to_iso,
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
