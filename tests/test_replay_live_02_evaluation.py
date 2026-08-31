"""Real Evaluation responses captured live (2026-08-31) over the live_02
opportunities, into ``tests/fixtures/replay/live_02/llm/evaluation/``.

Evaluation sends NO structured-output schema (owner decision 2026-08-31 — the
schema compiles to an over-limit grammar). These fixtures are the real
prompt-guided JSON the model returned; the deterministic parser + strict
validator + ``_build_bundle`` reproduce the evaluations offline.

All 3 picked opportunities were captured. The first isolated run got 2/3 clean +
1 model JSON-syntax slip (``stop_reason=end_turn`` — not truncation, not the
grammar 400); a re-run with ``call_stage``'s retry-once enabled got the 3rd on
the first attempt (no retry needed — the slip was a one-off).
"""

from __future__ import annotations

import json
import re

import pytest
from tests.conftest import PROJECT_ROOT

from market_intelligence.evaluation import evaluate_opportunities
from market_intelligence.framing import frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.matching import match_assets
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.enums import AXIS_KEYS, DIMENSION_KEYS, Confidence, LifecycleState
from market_intelligence.schema.models import RunConfig, RunPaths, Signal
from market_intelligence.schema.validate import (
    blocking,
    validate_business_outcome_profile,
    validate_evaluation,
)

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "replay" / "live_02"
EVAL_DIR = FIXTURE / "llm" / "evaluation"
_SECRET = re.compile(r"sk-ant-|x-api-key|authorization|bearer |api[_-]?key|/Users/|/home/", re.I)
_V1_STATES = {LifecycleState.EXPLORE, LifecycleState.TEST, LifecycleState.PARK}

_CAPTURED = sorted(p.name for p in EVAL_DIR.glob("evaluation__*.json")) if EVAL_DIR.is_dir() else []
_CAPTURED_IDS = [n[len("evaluation__"):-len(".json")] for n in _CAPTURED]


def _replay_cfg() -> RunConfig:
    return decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_live_02_replay", "run_date": "2026-08-30",
        "model": "claude-sonnet-5", "prompt_version": "p", "signal_sources": ["web_search"],
        "max_candidates": 15,
        "replay": {"enabled": True, "fixture_path": str(FIXTURE)},
    })


def _bundles():
    kn = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)
    sigs = [decode(Signal, d) for d in json.loads((FIXTURE / "signals.json").read_text())]
    picked = sorted(
        frame_signals(sigs, knowledge=kn, config=_replay_cfg(),
                      project_root=PROJECT_ROOT, now="2026-08-30T00:00:00Z").opportunities,
        key=lambda o: o.opportunity_id,
    )[:3]
    matches = match_assets(
        picked, knowledge=kn, config=_replay_cfg(), project_root=PROJECT_ROOT
    ).matches
    return picked, evaluate_opportunities(
        picked, matches, knowledge=kn, config=_replay_cfg(),
        project_root=PROJECT_ROOT, musical_dna_needs_input=True,
    ).bundles


def test_all_three_picked_opportunities_have_a_captured_evaluation_fixture():
    picked, _ = _bundles()
    assert set(_CAPTURED_IDS) == {o.opportunity_id for o in picked}
    assert len(_CAPTURED) == 3


def test_no_captured_evaluation_fixture_contains_a_secret_or_local_path():
    for p in EVAL_DIR.glob("*.json"):
        assert not _SECRET.search(p.read_text(encoding="utf-8")), p.name


def test_no_captured_evaluation_fixture_carries_a_0_to_100_score():
    for p in EVAL_DIR.glob("*.json"):
        assert not re.search(r"\b\d{1,3}\s*/\s*100\b", p.read_text()), p.name


@pytest.mark.parametrize("oid", _CAPTURED_IDS)
def test_captured_evaluation_replays_clean_and_schema_valid(oid):
    _picked, bundles = _bundles()
    b = bundles[oid]
    assert b.technical_failure is False, b.technical_failure_reason
    assert b.evaluation is not None and b.recommendation is not None
    assert set(b.evaluation.dimensions) == set(DIMENSION_KEYS)          # C9
    assert set(b.business_outcome_profile.axes) == set(AXIS_KEYS)       # C5
    assert blocking(validate_evaluation(b.evaluation, musical_dna_needs_input=True)) == []
    assert blocking(validate_business_outcome_profile(b.business_outcome_profile)) == []
    assert b.recommendation.target_state in _V1_STATES                  # I2
    # rating ≠ confidence; music_fit confidence capped while musical DNA NEEDS_INPUT
    assert b.evaluation.dimensions["music_fit"].confidence in (Confidence.LOW, Confidence.MEDIUM)
    # overall_confidence is not raised by high dimension ratings
    highs = [d for d in b.evaluation.dimensions.values() if d.rating.value in ("HIGH", "VERY_HIGH")]
    if b.evaluation.overall_confidence is Confidence.HIGH:
        assert highs, "overall_confidence HIGH with no HIGH dimensions is suspicious"


def test_captured_evaluation_replay_is_deterministic():
    for oid in _CAPTURED_IDS:
        a = encode(_bundles()[1][oid].evaluation)
        c = encode(_bundles()[1][oid].evaluation)
        assert a == c, oid


def test_the_captured_evaluations_span_the_v1_target_states_sensibly():
    # the 3 real live evaluations: single-thin-signal → EXPLORE, a testable one →
    # TEST. No PARK forced by a technical failure. All grounded in LOW overall
    # confidence (the evidence base is thin — the model preserved that).
    _picked, bundles = _bundles()
    states = {bundles[oid].recommendation.target_state.value for oid in _CAPTURED_IDS}
    assert states <= {"EXPLORE", "TEST", "PARK"}
    assert all(bundles[oid].evaluation.overall_confidence.value == "LOW"
               for oid in _CAPTURED_IDS)
    assert all(not bundles[oid].technical_failure for oid in _CAPTURED_IDS)
