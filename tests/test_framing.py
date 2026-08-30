"""Analysis / Framing — spec §7, §18 component 3, §19. No network."""

from __future__ import annotations

import pytest
from tests.conftest import FIXTURES, PROJECT_ROOT, load_fixture

from market_intelligence.framing import (
    FramedOpportunity,
    FramingResult,
    frame_signals,
)
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import (
    Durability,
    EvidenceType,
    Language,
    Market,
    Urgency,
)
from market_intelligence.schema.ids import opportunity_id_base
from market_intelligence.schema.models import RunConfig, RunPaths, Signal

_FIXTURE_ROOT = FIXTURES / "pipeline"


def _knowledge():
    return load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def _signals():
    return [decode(Signal, d) for d in load_fixture("pipeline/signals.json")]


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_pipe",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["web_search", "tiktok_creative_center", "internal_data"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(_FIXTURE_ROOT)},
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _frame(**over):
    return frame_signals(
        _signals(), knowledge=_knowledge(), config=_cfg(**over), project_root=PROJECT_ROOT
    )


# --- happy path ------------------------------------------------

def test_frames_signals_into_opportunities():
    result = _frame()
    assert isinstance(result, FramingResult)
    assert len(result.opportunities) == 1
    opp = result.opportunities[0]
    assert isinstance(opp, FramedOpportunity)
    assert opp.market is Market.BRASIL
    assert opp.language is Language.PT
    assert opp.durability is Durability.EMERGING
    assert opp.urgency is Urgency.MEDIUM
    assert opp.need and opp.consumption_context and opp.audience.description


def test_opportunity_id_is_the_deterministic_c1_hash():
    opp = _frame().opportunities[0]
    expected = "opp_2026-08-28_" + opportunity_id_base(
        opp.need, opp.audience.description, opp.market.value, opp.language.value, opp.platform.value
    )
    assert opp.opportunity_id == expected


def test_evidence_is_typed_and_observed_items_resolve_to_real_signals():
    opp = _frame().opportunities[0]
    types = {e.type for e in opp.evidence}
    assert EvidenceType.OBSERVED in types
    known = {s.signal_id for s in _signals()}
    for item in opp.evidence:
        if item.type is EvidenceType.OBSERVED:
            assert item.signal_ids and set(item.signal_ids) <= known
    assert set(opp.signal_ids) <= known


def test_potential_cluster_hypothesis_is_validated_against_the_taxonomy():
    opp = _frame().opportunities[0]
    pc = opp.hypotheses.potential_cluster
    assert pc.value == "sono" and pc.canonical is True and pc.basis == "existing"


# --- deterministic guards ------------------------------------

def test_market_language_mismatch_candidate_is_dropped_not_emitted():
    result = _frame()
    assert all(o.title != "Oportunidade sem mercado claro" for o in result.opportunities)
    reasons = " ".join(d.reason for d in result.dropped)
    assert "7.1a" in reasons or "inconsistent" in reasons


def test_non_canonical_cluster_becomes_a_proposed_new_hypothesis(tmp_path):
    # rewrite the framing fixture so the cluster value is not canonical
    fx = tmp_path / "pipeline"
    (fx / "llm" / "framing").mkdir(parents=True)
    (fx / "signals.json").write_text(
        (FIXTURES / "pipeline" / "signals.json").read_text(), encoding="utf-8"
    )
    resp = load_fixture("pipeline/llm/framing/framing__de1e16a6b378.json")
    resp["opportunities"][0]["hypotheses"]["potential_cluster"] = {
        "value": "sono-do-atleta", "canonical": True, "basis": "existing"
    }
    import json

    (fx / "llm" / "framing" / "framing__de1e16a6b378.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_pipe", "run_date": "2026-08-28",
        "model": "claude-sonnet-5", "prompt_version": "p1",
        "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(fx)},
    })
    opp = frame_signals(
        _signals(), knowledge=_knowledge(), config=cfg, project_root=PROJECT_ROOT
    ).opportunities[0]
    pc = opp.hypotheses.potential_cluster
    assert pc.canonical is False and pc.basis == "proposed_new"


def test_inferred_evidence_without_a_basis_is_dropped_not_the_whole_opportunity(tmp_path):
    fx = tmp_path / "pipeline"
    (fx / "llm" / "framing").mkdir(parents=True)
    (fx / "signals.json").write_text(
        (FIXTURES / "pipeline" / "signals.json").read_text(), encoding="utf-8"
    )
    resp = load_fixture("pipeline/llm/framing/framing__de1e16a6b378.json")
    # strip derived_from from the INFERRED item (leave rationale) + keep the OBSERVED ones
    for ev in resp["opportunities"][0]["evidence"]:
        if ev["type"] == "INFERRED":
            ev.pop("derived_from", None)
    import json

    (fx / "llm" / "framing" / "framing__de1e16a6b378.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_pipe", "run_date": "2026-08-28",
        "model": "claude-sonnet-5", "prompt_version": "p1", "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(fx)},
    })
    result = frame_signals(
        _signals(), knowledge=_knowledge(), config=cfg, project_root=PROJECT_ROOT
    )
    assert len(result.opportunities) == 1  # opportunity survives on its OBSERVED evidence
    opp = result.opportunities[0]
    assert not any(e.type is EvidenceType.INFERRED for e in opp.evidence)
    assert any(e.type is EvidenceType.OBSERVED for e in opp.evidence)


def _frame_with_mutated_response(tmp_path, mutate) -> FramingResult:
    """Run framing against a copy of the recorded fixture, `mutate(resp)` applied."""
    import json

    fx = tmp_path / "pipeline"
    (fx / "llm" / "framing").mkdir(parents=True, exist_ok=True)
    (fx / "signals.json").write_text(
        (FIXTURES / "pipeline" / "signals.json").read_text(), encoding="utf-8"
    )
    resp = load_fixture("pipeline/llm/framing/framing__de1e16a6b378.json")
    mutate(resp)
    (fx / "llm" / "framing" / "framing__de1e16a6b378.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_pipe", "run_date": "2026-08-28",
        "model": "claude-sonnet-5", "prompt_version": "p1", "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(fx)},
    })
    return frame_signals(
        _signals(), knowledge=_knowledge(), config=cfg, project_root=PROJECT_ROOT
    )


def _set_attributes(value):
    def mutate(resp):
        resp["opportunities"][0]["audience"]["attributes"] = value
    return mutate


def test_recorded_fixture_folds_the_attribute_pair_list_into_the_internal_map():
    # the recorded fixture carries attributes as the wire pair-list form
    opp = _frame().opportunities[0]
    assert opp.audience.attributes == {
        "life_stage": "trabalhadores urbanos",
        "habit": "ouvem musica ao deitar",
    }


def test_arbitrary_attribute_keys_round_trip_model_to_internal(tmp_path):
    pairs = [
        {"key": "commute_mode", "value": "metro"},
        {"key": "device", "value": "phone with earbuds"},
        {"key": "time_of_day", "value": "late night"},
    ]
    opp = _frame_with_mutated_response(tmp_path, _set_attributes(pairs)).opportunities[0]
    assert opp.audience.attributes == {
        "commute_mode": "metro",
        "device": "phone with earbuds",
        "time_of_day": "late night",
    }


def test_empty_or_absent_attributes_become_none(tmp_path):
    assert _frame_with_mutated_response(
        tmp_path, _set_attributes([])
    ).opportunities[0].audience.attributes is None

    def drop(resp):
        resp["opportunities"][0]["audience"].pop("attributes", None)

    assert _frame_with_mutated_response(tmp_path, drop).opportunities[0].audience.attributes is None


def test_malformed_attribute_entries_are_dropped_never_invented(tmp_path):
    pairs = [
        {"key": "valid_key", "value": "kept"},
        {"key": "", "value": "no key"},
        {"key": "no_value"},
        {"value": "no key field"},
        {"key": "blank_value", "value": "  "},
        "not-an-object",
    ]
    opp = _frame_with_mutated_response(tmp_path, _set_attributes(pairs)).opportunities[0]
    assert opp.audience.attributes == {"valid_key": "kept"}


def test_a_rejected_framing_response_is_a_clean_framing_error(tmp_path):
    fx = tmp_path / "pipeline"
    (fx / "llm" / "framing").mkdir(parents=True)
    (fx / "signals.json").write_text(
        (FIXTURES / "pipeline" / "signals.json").read_text(), encoding="utf-8"
    )
    (fx / "llm" / "framing" / "framing__de1e16a6b378.json").write_text(
        "{ this is not json", encoding="utf-8"
    )
    cfg = decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_pipe", "run_date": "2026-08-28",
        "model": "claude-sonnet-5", "prompt_version": "p1", "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(fx)},
    })
    from market_intelligence.framing import FramingError

    with pytest.raises(FramingError):
        frame_signals(_signals(), knowledge=_knowledge(), config=cfg, project_root=PROJECT_ROOT)


def test_missing_fixture_raises_not_network(tmp_path):
    cfg = decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_absent", "run_date": "2026-08-28",
        "model": "claude-sonnet-5", "prompt_version": "p1", "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(tmp_path)},
    })
    from market_intelligence.llm_stage import MissingFixtureError

    with pytest.raises(MissingFixtureError):
        frame_signals(_signals(), knowledge=_knowledge(), config=cfg, project_root=PROJECT_ROOT)


def test_empty_signal_list_produces_no_opportunities():
    result = frame_signals([], knowledge=_knowledge(), config=_cfg(), project_root=PROJECT_ROOT)
    assert result.opportunities == []


def test_ids_are_stable_across_runs():
    a = _frame().opportunities[0].opportunity_id
    b = _frame().opportunities[0].opportunity_id
    assert a == b
