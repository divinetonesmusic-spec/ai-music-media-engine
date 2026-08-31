"""Evaluation — spec §8, §9, §12.4, §18 component 5, §19. No network."""

from __future__ import annotations

import json

from tests.conftest import FIXTURES, PROJECT_ROOT, load_fixture

from market_intelligence.evaluation import EvaluationResult, evaluate_opportunities
from market_intelligence.framing import frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.matching import match_assets
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import (
    AXIS_KEYS,
    DIMENSION_KEYS,
    Confidence,
    LifecycleState,
    RedFlagKind,
)
from market_intelligence.schema.models import EXECUTION_NOTE, RunConfig, RunPaths, Signal
from market_intelligence.schema.validate import blocking, validate_evaluation

_FIXTURE_ROOT = FIXTURES / "pipeline"
_OPP_ID = "opp_2026-08-28_e1a48ddf1c"


def _knowledge():
    return load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_pipe",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(_FIXTURE_ROOT)},
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _pipeline_to_matches(cfg=None):
    cfg = cfg or _cfg()
    kn = _knowledge()
    signals = [decode(Signal, d) for d in load_fixture("pipeline/signals.json")]
    framed = frame_signals(
        signals, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).opportunities
    matches = match_assets(
        framed, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).matches
    return framed, matches, kn, cfg


def _evaluate(**over) -> EvaluationResult:
    framed, matches, kn, cfg = _pipeline_to_matches(_cfg(**over))
    return evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    )


def test_produces_a_bundle_per_opportunity_with_all_dims_and_axes():
    bundle = _evaluate().bundles[_OPP_ID]
    assert set(bundle.evaluation.dimensions) == set(DIMENSION_KEYS)
    assert set(bundle.business_outcome_profile.axes) == set(AXIS_KEYS)
    assert not bundle.excluded


def test_evaluation_is_schema_valid_and_carries_no_numeric_score():
    bundle = _evaluate().bundles[_OPP_ID]
    assert blocking(validate_evaluation(bundle.evaluation)) == []


def test_music_fit_confidence_is_capped_while_musical_dna_is_needs_input(tmp_path):
    fx = _clone_fixtures(tmp_path)
    resp = load_fixture("pipeline/llm/evaluation/evaluation__" + _OPP_ID + ".json")
    resp["dimensions"]["music_fit"]["confidence"] = "HIGH"
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    framed, matches, kn, cfg = _pipeline_to_matches(cfg)
    bundle = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles[_OPP_ID]
    assert bundle.evaluation.dimensions["music_fit"].confidence in (
        Confidence.LOW, Confidence.MEDIUM
    )


def test_target_state_is_constrained_to_v1_states(tmp_path):
    fx = _clone_fixtures(tmp_path)
    resp = load_fixture("pipeline/llm/evaluation/evaluation__" + _OPP_ID + ".json")
    resp["recommendation"]["target_state"] = "LAUNCH"
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    framed, matches, kn, cfg = _pipeline_to_matches(cfg)
    bundle = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles[_OPP_ID]
    assert bundle.recommendation.target_state is LifecycleState.TEST
    assert bundle.recommendation.execution_note == EXECUTION_NOTE


def test_overall_confidence_is_not_raised_by_high_dimension_ratings():
    bundle = _evaluate().bundles[_OPP_ID]
    # fixture sets it to MEDIUM and several dims are HIGH — it must stay MEDIUM
    assert bundle.evaluation.overall_confidence is Confidence.MEDIUM


def test_required_blocked_by_array_from_the_model_keeps_its_semantics():
    # `blocked_by` is a required array in the live schema now (7th-bug fix). An
    # empty list means "no blocker" and maps to None; a non-empty list is kept.
    dims = _evaluate().bundles[_OPP_ID].evaluation.dimensions
    assert dims["signal_strength"].blocked_by is None                  # fixture: []
    assert dims["growth_momentum"].blocked_by == [
        "historical performance data (UNKNOWN)"
    ]


def test_an_empty_justification_is_a_malformed_response_now(tmp_path):
    # Structured outputs are gone from Evaluation (owner decision 2026-08-31); the
    # prompt requires every string non-empty, so an empty justification is a
    # malformed response → technical_failure, not silent coercion.
    def blank_one(resp):
        resp["dimensions"]["signal_strength"]["justification"] = ""
        return resp
    b = _eval_with_raw_fixture(tmp_path, blank_one)
    assert b.technical_failure is True and b.excluded is False
    assert "justification" in b.technical_failure_reason


def test_a_properly_formed_unrateable_dimension_flows_through(tmp_path):
    # the model's correct way to say "cannot rate": LOW/LOW + a real justification
    # + a non-empty blocked_by — this must NOT be a technical failure.
    def unrateable(resp):
        resp["dimensions"]["signal_strength"] = {
            "rating": "LOW", "confidence": "LOW",
            "justification": "Not rateable from the available evidence.",
            "blocked_by": ["historical search-volume data (UNKNOWN)"],
        }
        return resp
    b = _eval_with_raw_fixture(tmp_path, unrateable)
    assert b.technical_failure is False
    dim = b.evaluation.dimensions["signal_strength"]
    assert dim.blocked_by == ["historical search-volume data (UNKNOWN)"]


def test_evaluation_api_failure_is_a_technical_failure_not_a_business_exclusion(tmp_path):
    # a corrupt recorded fixture -> ResponseRejected -> the Evaluation call could not
    # complete. That is infrastructure, not a business decision.
    fx = _clone_fixtures(tmp_path)
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        "{ this is not valid json", encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    framed, matches, kn, cfg = _pipeline_to_matches(cfg)
    bundle = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles[_OPP_ID]

    assert bundle.technical_failure is True
    assert bundle.technical_failure_reason
    assert bundle.excluded is False                 # NOT a business exclusion
    assert bundle.recommendation is None            # no PARK, no recommendation at all
    assert bundle.evaluation is None


def test_a_missing_replay_fixture_stays_a_business_exclusion(tmp_path):
    # spec §22 — a missing recorded fixture is a documented offline-testing degrade,
    # distinct from an operational failure.
    fx = _clone_fixtures(tmp_path)
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").unlink()
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    framed, matches, kn, cfg = _pipeline_to_matches(cfg)
    bundle = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles[_OPP_ID]

    assert bundle.technical_failure is False
    assert bundle.excluded is True


def test_compliance_violation_in_core_content_excludes_the_opportunity(tmp_path):
    fx = _clone_fixtures(tmp_path)
    resp = load_fixture("pipeline/llm/evaluation/evaluation__" + _OPP_ID + ".json")
    resp["summary"] = "This routine is clinically proven to cure insomnia within a week."
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    framed, matches, kn, cfg = _pipeline_to_matches(cfg)
    bundle = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles[_OPP_ID]
    assert bundle.excluded is True
    assert any(rf.kind is RedFlagKind.COMPLIANCE for rf in bundle.evaluation.red_flags)


def _clone_fixtures(tmp_path):
    fx = tmp_path / "pipeline"
    for sub in ("framing", "matching", "evaluation"):
        (fx / "llm" / sub).mkdir(parents=True, exist_ok=True)
    (fx / "signals.json").write_text(
        (FIXTURES / "pipeline" / "signals.json").read_text(), encoding="utf-8"
    )
    for sub in ("framing", "matching", "evaluation"):
        src = FIXTURES / "pipeline" / "llm" / sub
        for f in src.glob("*.json"):
            (fx / "llm" / sub / f.name).write_text(f.read_text(), encoding="utf-8")
    return fx


# --- structured outputs removed from Evaluation (owner decision 2026-08-31) --
#
# The Evaluation JSON Schema compiles to a grammar over Anthropic's size limit
# (confirmed live). Evaluation now asks for prompt-guided JSON; the deterministic
# layer must reject any malformed response → technical_failure (never PARK, never
# registered), distinct from the §13 business validation that still runs on a
# well-formed response.


def _eval_with_raw_fixture(tmp_path, mutate):
    """Load the good evaluation fixture, apply ``mutate`` to the parsed dict, write
    it back, and run Evaluation over it (recorded replay)."""
    fx = _clone_fixtures(tmp_path)
    resp = load_fixture("pipeline/llm/evaluation/evaluation__" + _OPP_ID + ".json")
    resp = mutate(resp)
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    framed, matches, kn, cfg = _pipeline_to_matches(cfg)
    return evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles[_OPP_ID]


def test_evaluation_still_replays_the_valid_fixture_with_10_dims_and_5_axes():
    b = _evaluate().bundles[_OPP_ID]
    assert b.technical_failure is False and b.excluded is False
    assert set(b.evaluation.dimensions) == set(DIMENSION_KEYS)
    assert set(b.business_outcome_profile.axes) == set(AXIS_KEYS)
    assert b.recommendation.target_state in (
        LifecycleState.EXPLORE, LifecycleState.TEST, LifecycleState.PARK
    )


def test_evaluation_rejects_a_response_missing_a_dimension(tmp_path):
    def drop_a_dim(resp):
        resp["dimensions"].pop("growth_momentum")
        return resp
    b = _eval_with_raw_fixture(tmp_path, drop_a_dim)
    assert b.technical_failure is True
    assert b.excluded is False and b.recommendation is None and b.evaluation is None
    assert "growth_momentum" in b.technical_failure_reason


def test_evaluation_rejects_a_missing_bop_axis(tmp_path):
    b = _eval_with_raw_fixture(
        tmp_path, lambda r: (r["business_outcome_profile"].pop("page_growth_potential"), r)[1]
    )
    assert b.technical_failure is True and b.excluded is False


def test_evaluation_rejects_an_invalid_rating_enum(tmp_path):
    def bad_enum(resp):
        resp["dimensions"]["signal_strength"]["rating"] = "SUPERB"
        return resp
    b = _eval_with_raw_fixture(tmp_path, bad_enum)
    assert b.technical_failure is True and b.excluded is False
    assert "rating" in b.technical_failure_reason.lower()


def test_evaluation_rejects_a_0_to_100_score_in_a_justification(tmp_path):
    def inject_score(resp):
        resp["dimensions"]["audience_potential"]["justification"] = (
            "Strong reach — I score this 85/100 for audience potential."
        )
        return resp
    b = _eval_with_raw_fixture(tmp_path, inject_score)
    # a 0–100 score is a malformed response, NOT a business exclusion
    assert b.technical_failure is True
    assert b.excluded is False and b.recommendation is None
    assert "score" in b.technical_failure_reason.lower()


def test_evaluation_rejects_an_invalid_recommendation(tmp_path):
    def bad_rec(resp):
        resp["recommendation"]["target_state"] = "MAYBE"
        resp["recommendation"].pop("suggested_next_step")
        return resp
    b = _eval_with_raw_fixture(tmp_path, bad_rec)
    assert b.technical_failure is True and b.excluded is False


def test_evaluation_rejects_malformed_red_flags(tmp_path):
    def bad_flags(resp):
        resp["red_flags"] = [{"description": "x", "severity": "CRITICAL", "kind": "other"}]
        return resp
    b = _eval_with_raw_fixture(tmp_path, bad_flags)
    assert b.technical_failure is True and b.excluded is False


def test_evaluation_rejects_a_top_level_array(tmp_path):
    fx = _clone_fixtures(tmp_path)
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        json.dumps(["not", "an", "object"]), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    framed, matches, kn, cfg = _pipeline_to_matches(cfg)
    b = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles[_OPP_ID]
    assert b.technical_failure is True and b.excluded is False


def test_a_malformed_evaluation_never_becomes_park_or_a_registry_entry(tmp_path):
    from market_intelligence.config.loader import load_ranking_config
    from market_intelligence.ranking import TECHNICAL_FAILURE, rank_opportunities

    b = _eval_with_raw_fixture(tmp_path, lambda r: (r["dimensions"].pop("music_fit"), r)[1])
    assert b.technical_failure is True
    ranking = rank_opportunities(
        _framed_only(), {b.opportunity_id: b},
        ranking_config=load_ranking_config(project_root=PROJECT_ROOT), max_presented=10,
    )
    r = ranking.by_id(b.opportunity_id)
    assert r.bucket == TECHNICAL_FAILURE and r.status is None
    assert b.opportunity_id in ranking.technical_failures
    assert b.opportunity_id not in ranking.presented + ranking.parked + ranking.excluded


def _framed_only():
    kn = _knowledge()
    signals = [decode(Signal, d) for d in load_fixture("pipeline/signals.json")]
    return frame_signals(
        signals, knowledge=kn, config=_cfg(), project_root=PROJECT_ROOT
    ).opportunities
