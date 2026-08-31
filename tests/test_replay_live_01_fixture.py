"""The 37 real Signals from the 2026-08-30 first live dry run, preserved as an
offline replay fixture (``tests/fixtures/replay/live_01/``).

No network in any test. The fixture is repo-relative and machine-independent.
"""

from __future__ import annotations

import datetime as dt
import json
import re

import pytest
from tests.conftest import PROJECT_ROOT

from market_intelligence.collect.base import collect_signals
from market_intelligence.collect.web_search import WebSearchClient, WebSearchCollector
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.enums import SourceType
from market_intelligence.schema.models import RunConfig, Signal
from market_intelligence.schema.validate import validate_signals

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "replay" / "live_01"
FIXED = dt.datetime(2026, 8, 30, 23, 40, 7, tzinfo=dt.timezone.utc)
_SECRET = re.compile(r"sk-ant-|x-api-key|authorization:|bearer |ANTHROPIC_API_KEY|/Users/", re.I)


class _ExplodingClient(WebSearchClient):
    def research(self, **kw):
        raise AssertionError("replay must not touch the network")


def _cfg() -> RunConfig:
    return decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_live_01_replay", "run_date": "2026-08-30",
        "model": "claude-sonnet-5", "prompt_version": "p", "signal_sources": ["web_search"],
        "replay": {"enabled": True, "fixture_path": str(FIXTURE)},
    })


def _replay(tmp_path):
    return collect_signals(
        _cfg(),
        project_root=tmp_path,
        collectors={SourceType.WEB_SEARCH: WebSearchCollector(client=_ExplodingClient())},
        now=lambda: FIXED,
    )


def _raw_root(tmp_path):
    return tmp_path / "data" / "run_live_01_replay" / "signals" / "raw"


# --- the fixture exists in the canonical replay layout ---------------------


def test_fixture_layout():
    assert (FIXTURE / "llm" / "web_search" / "research.json").is_file()
    assert (FIXTURE / "signals.json").is_file()
    raw = sorted((FIXTURE / "signals" / "raw").glob("*.json"))
    assert len(raw) == 37
    assert raw[0].name == "sig_run_live_01_dry_0001.json"


def test_fixture_carries_no_secrets_or_local_paths():
    for path in FIXTURE.rglob("*.json"):
        blob = path.read_text(encoding="utf-8")
        assert not _SECRET.search(blob), f"secret-like token in {path.name}"


# --- replay reconstructs the 37 Signals, offline, deterministically -------


def test_replay_reconstructs_all_37_signals(tmp_path):
    result = _replay(tmp_path)
    assert result.replay is True
    assert len(result.signals) == 37
    assert result.sources_used == ["web_search"]
    assert validate_signals(result.signals, raw_root=_raw_root(tmp_path)) == []


def test_replay_never_touches_the_network(tmp_path):
    # _ExplodingClient.research raises if called; reaching this assert means it didn't.
    assert len(_replay(tmp_path).signals) == 37


def test_replay_is_deterministic(tmp_path):
    a = [encode(s) for s in _replay(tmp_path).signals]
    b = [encode(s) for s in _replay(tmp_path / "second").signals]
    assert a == b


def test_reconstructed_signals_preserve_provenance_and_observed_at(tmp_path):
    findings = json.loads(
        (FIXTURE / "llm" / "web_search" / "research.json").read_text()
    )["findings"]
    # findings can share a result_url, so match on the (query, url, evidence) triple
    finding_triples = {(f["query"], f["result_url"], f["evidence"]) for f in findings}

    for sig in _replay(tmp_path).signals:
        assert (
            sig.provenance.query_or_reference, sig.provenance.url, sig.evidence
        ) in finding_triples
        assert sig.provenance.source_type is SourceType.WEB_SEARCH
        assert sig.provenance.capture_method.value == "claude_web_search"
        # observed_at is derived deterministically from the finding's page_age
        assert sig.observed_at == sig.provenance.observed_at


# --- the 37 normalized Signals are preserved verbatim --------------------


def _normalized_signals() -> list:
    return [decode(Signal, d) for d in json.loads((FIXTURE / "signals.json").read_text())]


def test_signals_json_holds_the_original_37_normalized_signals():
    sigs = _normalized_signals()
    assert len(sigs) == 37
    ids = [s.signal_id for s in sigs]
    assert ids == [f"sig_run_live_01_dry_{n:04d}" for n in range(1, 38)]
    assert all(s.run_id == "run_live_01_dry" for s in sigs)


def test_preserved_signals_are_valid_with_provenance_and_dates_intact():
    sigs = _normalized_signals()
    assert validate_signals(sigs, raw_root=FIXTURE / "signals" / "raw") == []
    for s in sigs:
        assert s.provenance.url == s.url
        assert s.observed_at == s.provenance.observed_at
        assert s.provenance.capture_method.value == "claude_web_search"
        assert s.raw_ref == f"data/run_live_01_dry/signals/raw/{s.signal_id}.json"


def test_normalization_disambiguation_is_captured():
    # SN-2 filled one market on the live run; signals.json keeps that post-norm state
    sigs = {s.signal_id: s for s in _normalized_signals()}
    assert sigs["sig_run_live_01_dry_0002"].market == "English-speaking markets"


@pytest.mark.parametrize(
    "market", ["Brasil", "Mercados hispanohablantes", "English-speaking markets"]
)
def test_all_three_v1_markets_are_represented(market):
    assert any(s.market == market for s in _normalized_signals())
