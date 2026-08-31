"""Ranking / Prioritization — spec §11, §18 component 6. Deterministic golden tests."""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from market_intelligence.config.loader import load_ranking_config
from market_intelligence.evaluation import EvaluationBundle
from market_intelligence.framing import FramedOpportunity
from market_intelligence.guardrails import ComplianceResult
from market_intelligence.ranking import EXCLUDED, TECHNICAL_FAILURE, rank_opportunities
from market_intelligence.schema.enums import (
    AXIS_KEYS,
    DIMENSION_KEYS,
    Confidence,
    Durability,
    EvidenceType,
    Language,
    LifecycleState,
    Market,
    Platform,
    Rating,
    RedFlagKind,
    Severity,
    Urgency,
)
from market_intelligence.schema.models import (
    EXECUTION_NOTE,
    Audience,
    AxisRating,
    BusinessOutcomeProfile,
    DimensionRating,
    Evaluation,
    EvidenceItem,
    Recommendation,
    RedFlag,
)

RANKING = load_ranking_config(project_root=PROJECT_ROOT)


def _opp(oid, *, urgency=Urgency.MEDIUM, durability=Durability.STRUCTURAL, observed=True):
    evidence = []
    if observed:
        evidence.append(EvidenceItem(
            type=EvidenceType.OBSERVED, statement="seen", confidence=Confidence.MEDIUM,
            signal_ids=["sig_x"],
        ))
    else:
        evidence.append(EvidenceItem(
            type=EvidenceType.HYPOTHESIS, statement="maybe", confidence=Confidence.LOW,
            rationale="hunch",
        ))
    return FramedOpportunity(
        opportunity_id=oid, schema_version="1.0.0", run_id="run_rank",
        created_at="2026-08-28T00:00:00Z", title=oid, need="need", audience=Audience("aud"),
        market=Market.BRASIL, language=Language.PT, platform=Platform.TIKTOK,
        consumption_context="ctx", durability=durability, urgency=urgency, evidence=evidence,
        signal_ids=["sig_x"],
    )


def _bundle(oid, *, overall=Confidence.MEDIUM, dims_high=3, axes_high=2,
            asset_fit=Rating.MEDIUM, red_flags=None, excluded=False):
    dims = {}
    for i, k in enumerate(DIMENSION_KEYS):
        rating = Rating.HIGH if i < dims_high else Rating.LOW
        if k == "asset_fit":
            rating = asset_fit
        dims[k] = DimensionRating(rating=rating, confidence=Confidence.MEDIUM, justification="j")
    axes = {
        k: AxisRating(rating=Rating.HIGH if i < axes_high else Rating.LOW,
                      confidence=Confidence.MEDIUM, justification="j")
        for i, k in enumerate(AXIS_KEYS)
    }
    evaluation = Evaluation(
        schema_version="1.0.0", dimensions=dims, red_flags=red_flags or [],
        overall_confidence=overall, summary="s",
    )
    rec = Recommendation(
        schema_version="1.0.0", target_state=LifecycleState.TEST,
        suggested_next_step="do", justification="because", confidence=overall,
        execution_note=EXECUTION_NOTE,
    )
    return EvaluationBundle(
        opportunity_id=oid, evaluation=evaluation,
        business_outcome_profile=BusinessOutcomeProfile(schema_version="1.0.0", axes=axes),
        recommendation=rec, compliance=ComplianceResult(), excluded=excluded,
    )


def _tech_fail_bundle(oid, reason="evaluation API call failed: 400 grammar too large"):
    return EvaluationBundle(
        opportunity_id=oid, evaluation=None, business_outcome_profile=None,
        recommendation=None, compliance=ComplianceResult(),
        technical_failure=True, technical_failure_reason=reason,
    )


def _rank(pairs, max_presented=10):
    opps = [p[0] for p in pairs]
    bundles = {p[0].opportunity_id: p[1] for p in pairs}
    return rank_opportunities(
        opps, bundles, ranking_config=RANKING, max_presented=max_presented
    )


def test_higher_overall_confidence_ranks_first():
    a = (_opp("opp_a"), _bundle("opp_a", overall=Confidence.LOW))
    b = (_opp("opp_b"), _bundle("opp_b", overall=Confidence.HIGH))
    result = _rank([a, b])
    assert result.presented == ["opp_b", "opp_a"]
    assert result.by_id("opp_b").rank == 1


def test_more_high_dimensions_breaks_a_confidence_tie():
    a = (_opp("opp_a"), _bundle("opp_a", dims_high=2))
    b = (_opp("opp_b"), _bundle("opp_b", dims_high=7))
    assert _rank([a, b]).presented == ["opp_b", "opp_a"]


def test_urgency_then_durability_are_consulted_in_order():
    # equal confidence + dims + axes; a has HIGH urgency, b has LOW
    a = (_opp("opp_a", urgency=Urgency.HIGH), _bundle("opp_a"))
    b = (_opp("opp_b", urgency=Urgency.LOW, durability=Durability.EVERGREEN), _bundle("opp_b"))
    assert _rank([a, b]).presented == ["opp_a", "opp_b"]


def test_evergreen_and_structural_rank_equally_then_id_breaks_the_tie():
    a = (_opp("opp_a", durability=Durability.EVERGREEN), _bundle("opp_a"))
    b = (_opp("opp_b", durability=Durability.STRUCTURAL), _bundle("opp_b"))
    assert _rank([a, b]).presented == ["opp_a", "opp_b"]  # lexical tie-break


def test_zero_observed_evidence_is_hard_excluded():
    a = (_opp("opp_a", observed=False), _bundle("opp_a"))
    b = (_opp("opp_b"), _bundle("opp_b"))
    result = _rank([a, b])
    assert result.presented == ["opp_b"]
    assert "opp_a" in result.excluded
    assert result.by_id("opp_a").bucket == EXCLUDED
    assert result.by_id("opp_a").status is LifecycleState.PARK


def test_high_severity_compliance_red_flag_is_hard_excluded():
    flag = RedFlag(description="G01", severity=Severity.HIGH, kind=RedFlagKind.COMPLIANCE)
    a = (_opp("opp_a"), _bundle("opp_a", red_flags=[flag]))
    b = (_opp("opp_b"), _bundle("opp_b"))
    result = _rank([a, b])
    assert result.presented == ["opp_b"]
    assert "opp_a" in result.excluded


def test_evaluation_stage_exclusion_is_carried_through():
    a = (_opp("opp_a"), _bundle("opp_a", excluded=True))
    b = (_opp("opp_b"), _bundle("opp_b"))
    result = _rank([a, b])
    assert result.excluded == ["opp_a"]
    assert result.by_id("opp_a").exclusion_reason


# --- technical failure is NOT a ranking / business decision (spec §14) -----


def test_a_technical_failure_is_not_hard_excluded_and_carries_no_status():
    a = (_opp("opp_a"), _tech_fail_bundle("opp_a"))
    b = (_opp("opp_b"), _bundle("opp_b"))
    result = _rank([a, b])

    assert result.presented == ["opp_b"]
    assert result.excluded == []                       # NOT a business exclusion
    assert result.technical_failures == ["opp_a"]
    r = result.by_id("opp_a")
    assert r.bucket == TECHNICAL_FAILURE
    assert r.status is None                            # no PARK, no EXPLORE
    assert r.technical_failure_reason


def test_a_technical_failure_is_not_converted_to_compliance_or_zero_evidence_exclusion():
    # opp_a technically failed AND has only hypothesis evidence (zero OBSERVED) —
    # it must still be technical_failure, never a zero-evidence hard exclusion.
    a = (_opp("opp_a", observed=False), _tech_fail_bundle("opp_a"))
    result = _rank([a])
    assert result.technical_failures == ["opp_a"]
    assert result.excluded == []
    assert result.by_id("opp_a").bucket == TECHNICAL_FAILURE


def test_evaluated_opportunities_still_rank_while_another_fails_technically():
    good = (_opp("opp_good"), _bundle("opp_good", overall=Confidence.HIGH))
    bad = (_opp("opp_bad"), _tech_fail_bundle("opp_bad"))
    result = _rank([bad, good])

    assert result.presented == ["opp_good"]            # the evaluated one flows through
    assert result.by_id("opp_good").status is LifecycleState.EXPLORE
    assert result.technical_failures == ["opp_bad"]
    assert "opp_bad" not in result.presented + result.parked + result.excluded


def test_non_compliance_red_flags_penalise_but_do_not_exclude():
    noisy = [RedFlag(description="x", severity=Severity.HIGH, kind=RedFlagKind.EVIDENCE_GAP)]
    a = (_opp("opp_a"), _bundle("opp_a", red_flags=noisy))
    b = (_opp("opp_b"), _bundle("opp_b"))
    result = _rank([a, b])
    assert result.presented == ["opp_b", "opp_a"]
    assert result.excluded == []


def test_presented_cap_moves_the_rest_to_parked():
    pairs = [(_opp(f"opp_{i:02d}"), _bundle(f"opp_{i:02d}")) for i in range(12)]
    result = _rank(pairs, max_presented=10)
    assert len(result.presented) == 10
    assert len(result.parked) == 2
    assert all(result.by_id(pid).status is LifecycleState.PARK for pid in result.parked)


def test_ranking_is_a_pure_function_stable_across_input_order():
    pairs = [
        (_opp("opp_a", urgency=Urgency.LOW), _bundle("opp_a", overall=Confidence.MEDIUM)),
        (_opp("opp_b", urgency=Urgency.HIGH), _bundle("opp_b", overall=Confidence.HIGH)),
        (_opp("opp_c"), _bundle("opp_c", overall=Confidence.LOW)),
    ]
    a = _rank(pairs).presented
    b = _rank(list(reversed(pairs))).presented
    assert a == b
