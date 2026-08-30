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
