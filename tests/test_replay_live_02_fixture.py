"""The real Framing response from the 2026-08-31 successful live dry run,
captured over its 23 preserved Signals into ``tests/fixtures/replay/live_02/``.

One live Framing call produced this fixture (no Web Search / Normalization were
re-run). Every test here is fully offline.
"""

from __future__ import annotations

import datetime as dt
import json
import re

import pytest
from tests.conftest import PROJECT_ROOT

from market_intelligence.collect.base import collect_signals
from market_intelligence.collect.web_search import WebSearchClient, WebSearchCollector
from market_intelligence.framing import FramedOpportunity, frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.enums import EvidenceType, SourceType
from market_intelligence.schema.ids import opportunity_id_base
from market_intelligence.schema.models import RunConfig, RunPaths, Signal
from market_intelligence.schema.validate import validate_signals

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "replay" / "live_02"
FIXED = dt.datetime(2026, 8, 31, 0, 13, 17, tzinfo=dt.timezone.utc)
_SECRET = re.compile(r"sk-ant-|x-api-key|authorization:|bearer |api[_-]?key|/Users/|/home/", re.I)
_EXPECTED_OPPORTUNITIES = 13


class _ExplodingClient(WebSearchClient):
    def research(self, **kw):
        raise AssertionError("replay must not touch the network")


def _knowledge():
    return load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def _normalized_signals() -> list:
    return [decode(Signal, d) for d in json.loads((FIXTURE / "signals.json").read_text())]


def _replay_cfg() -> RunConfig:
    return decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_live_02_replay", "run_date": "2026-08-30",
        "model": "claude-sonnet-5", "prompt_version": "p", "signal_sources": ["web_search"],
        "max_candidates": 15,
        "replay": {"enabled": True, "fixture_path": str(FIXTURE)},
    })


def _frame(signals):
    return frame_signals(
        signals, knowledge=_knowledge(), config=_replay_cfg(),
        project_root=PROJECT_ROOT, now="2026-08-30T00:00:00Z",
    )


# --- layout / secrets ----------------------------------------------------


def test_fixture_layout():
    assert (FIXTURE / "signals.json").is_file()
    assert (FIXTURE / "llm" / "web_search" / "research.json").is_file()
    framing = list((FIXTURE / "llm" / "framing").glob("framing__*.json"))
    assert len(framing) == 1
    assert len(list((FIXTURE / "signals" / "raw").glob("*.json"))) == 23


def test_fixture_carries_no_secrets_or_local_paths():
    for path in FIXTURE.rglob("*.json"):
        assert not _SECRET.search(path.read_text(encoding="utf-8")), path.name


# --- the 23 Signals are preserved ------------------------------------


def test_signals_json_holds_the_23_normalized_signals():
    sigs = _normalized_signals()
    assert len(sigs) == 23
    assert [s.signal_id for s in sigs] == [
        f"sig_run_live_01_dry_{n:04d}" for n in range(1, 24)
    ]
    assert validate_signals(sigs, raw_root=FIXTURE / "signals" / "raw") == []
    for s in sigs:
        assert s.provenance.url == s.url
        assert s.observed_at == s.provenance.observed_at
        assert s.provenance.source_type is SourceType.WEB_SEARCH


def test_web_search_replay_reconstructs_23_signals(tmp_path):
    result = collect_signals(
        _replay_cfg(), project_root=tmp_path,
        collectors={SourceType.WEB_SEARCH: WebSearchCollector(client=_ExplodingClient())},
        now=lambda: FIXED,
    )
    assert result.replay is True
    assert len(result.signals) == 23
    raw_root = tmp_path / "data" / "run_live_02_replay" / "signals" / "raw"
    assert validate_signals(result.signals, raw_root=raw_root) == []


# --- Framing replays the real recorded response --------------------


def test_framing_replay_reproduces_the_opportunities():
    result = _frame(_normalized_signals())
    assert len(result.opportunities) == _EXPECTED_OPPORTUNITIES
    assert result.dropped == []
    assert result.llm_mode == "recorded"
    assert all(isinstance(o, FramedOpportunity) for o in result.opportunities)


def test_framing_replay_never_touches_the_network():
    # frame_signals with replay.enabled + no client must use RecordedStageClient
    assert len(_frame(_normalized_signals()).opportunities) == _EXPECTED_OPPORTUNITIES


def test_framing_replay_is_deterministic():
    a = [encode(o) for o in _frame(_normalized_signals()).opportunities]
    b = [encode(o) for o in _frame(_normalized_signals()).opportunities]
    assert a == b


def test_reproduced_opportunities_are_schema_valid():
    known = {s.signal_id for s in _normalized_signals()}
    for opp in _frame(_normalized_signals()).opportunities:
        # the six C1 mandatory fields
        assert opp.need and opp.audience.description and opp.consumption_context
        assert opp.market and opp.language and opp.platform
        # opportunity_id is the deterministic C1 hash (§7.1)
        assert opp.opportunity_id == "opp_2026-08-30_" + opportunity_id_base(
            opp.need, opp.audience.description,
            opp.market.value, opp.language.value, opp.platform.value,
        )
        # at least one OBSERVED evidence item, resolving to a signal in this run
        observed = [e for e in opp.evidence if e.type is EvidenceType.OBSERVED]
        assert observed
        assert any(set(e.signal_ids or []) & known for e in observed)
        assert set(opp.signal_ids) <= known


@pytest.mark.parametrize(
    "market", ["Brasil", "Mercados hispanohablantes", "English-speaking markets"]
)
def test_all_three_v1_markets_are_represented(market):
    opps = _frame(_normalized_signals()).opportunities
    assert any(o.market.value == market for o in opps)
