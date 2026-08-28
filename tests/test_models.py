"""Dataclass models — structural fidelity and dict round-trip (spec §6–§10, §12, §16, §20)."""

from __future__ import annotations

import pytest

from market_intelligence.schema import models as M
from market_intelligence.schema.codec import CodecError, decode, encode
from market_intelligence.schema.enums import (
    AXIS_KEYS,
    DIMENSION_KEYS,
    Confidence,
    EvidenceType,
    LifecycleState,
    Market,
)


def test_opportunity_fixture_round_trips_through_the_codec(valid_opportunity_dict):
    opp = decode(M.Opportunity, valid_opportunity_dict)
    assert isinstance(opp, M.Opportunity)
    assert encode(opp) == valid_opportunity_dict


def test_opportunity_decodes_nested_types(valid_opportunity_dict):
    opp = decode(M.Opportunity, valid_opportunity_dict)
    assert opp.market is Market.BRASIL
    assert opp.status is LifecycleState.EXPLORE
    assert isinstance(opp.audience, M.Audience)
    assert {k: type(v) for k, v in opp.evaluation.dimensions.items()} == {
        k: M.DimensionRating for k in DIMENSION_KEYS
    }
    assert set(opp.business_outcome_profile.axes) == set(AXIS_KEYS)
    assert opp.evidence[0].type is EvidenceType.OBSERVED
    assert opp.recommendation.execution_note == M.EXECUTION_NOTE


def test_state_change_from_is_serialised_as_the_reserved_word_key(valid_opportunity_dict):
    opp = decode(M.Opportunity, valid_opportunity_dict)
    sc = opp.state_history[0]
    assert sc.from_ is None  # no prior state on creation -> omitted from the wire form
    assert sc.to == "EXPLORE"
    assert "from" not in encode(sc)

    advanced = decode(
        M.StateChange,
        {"from": "EXPLORE", "to": "TEST", "at": "2026-09-01T09:00:00Z", "by": "Nicolas Alves"},
    )
    assert advanced.from_ == "EXPLORE"
    out = encode(advanced)
    assert out["from"] == "EXPLORE" and "from_" not in out


def test_signal_fixtures_round_trip(valid_signal_dicts):
    for raw in valid_signal_dicts:
        sig = decode(M.Signal, raw)
        assert isinstance(sig.provenance, M.Provenance)
        assert encode(sig) == raw


def test_unknown_field_in_fixture_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["surprise"] = 1
    with pytest.raises(CodecError):
        decode(M.Opportunity, valid_opportunity_dict)


def test_recommendation_execution_note_defaults_to_the_fixed_constant():
    rec = decode(
        M.Recommendation,
        {
            "schema_version": "1.0.0",
            "target_state": "EXPLORE",
            "suggested_next_step": "Keep watching the sleep hashtag for another 30 days.",
            "justification": "Signals are too early to justify a content test.",
            "confidence": "LOW",
        },
    )
    assert rec.execution_note == M.EXECUTION_NOTE
    assert rec.confidence is Confidence.LOW


def test_runconfig_defaults_match_spec_20_1():
    cfg = decode(
        M.RunConfig,
        {
            "run_id": "run_2026-08-28_01",
            "run_date": "2026-08-28",
            "model": "claude-sonnet-5",
            "prompt_version": "mi-v1-2026-08-28",
        },
    )
    assert cfg.max_opportunities_presented == 10  # I12
    assert cfg.min_opportunities_target == 5  # C10
    assert cfg.dry_run is False
    assert cfg.replay.enabled is False
    assert [s.value for s in cfg.signal_sources] == [
        "web_search",
        "youtube",
        "tiktok_creative_center",
        "internal_data",
    ]
    assert [lang.value for lang in cfg.scope.languages] == ["pt", "es", "en"]
    assert cfg.paths.guardrails_path == "knowledge/rules/guardrails.yaml"
    assert cfg.paths.taxonomy_path == "knowledge/clusters/cluster-taxonomy.md"
