"""Cluster Strategy V1 — compliance (contract §9).

Same mechanism as the pipeline: load guardrails.yaml (G01–G10), run
`check_texts` over the stage's prose, carry the opportunity's compliance flags
forward. The claims-vs-topics calibration is preserved — a topic mention is not a
violation; a claim about it is.
"""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from cluster_strategy.guardrails import check_cluster_strategy_prose
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.enums import RedFlagKind, Severity
from market_intelligence.schema.models import RunPaths

_GUARDRAILS = load_knowledge(RunPaths(), project_root=PROJECT_ROOT).guardrails


def _flags(prose: dict):
    return check_cluster_strategy_prose(prose, guardrails=_GUARDRAILS).red_flags


def test_a_topic_or_a_subjective_experience_is_not_a_violation():
    clean = {
        "central_concept": "Music for the ritual of settling a new home.",
        "emotional_state": "a felt sense of welcome and calm; people find it grounding.",
        "editorial_promise": "a calming ritual to welcome your new home.",
        "positioning_statement": "For es movers who want a calm ritual...",
        "first_content_direction": "a short video of a moving-in ritual with 432 Hz music.",
        "music_relationship": "ambient bed to a slow ritual gesture.",
        "localization_notes": "the moving-house ritual is culturally salient across es markets.",
    }
    assert _flags(clean) == []


def test_an_efficacy_claim_about_health_is_a_compliance_violation():
    prose = {
        "editorial_promise": "this music removes negative energy and cures your anxiety disorder.",
    }
    flags = _flags(prose)
    assert any(f.kind is RedFlagKind.COMPLIANCE and f.severity is Severity.HIGH for f in flags)


def test_invented_science_is_a_compliance_violation():
    prose = {"positioning_statement": "clinically proven to lower cortisol in listeners."}
    flags = _flags(prose)
    assert any(f.kind is RedFlagKind.COMPLIANCE for f in flags)


def test_the_permitted_wellness_themes_do_not_false_positive():
    prose = {
        "central_concept": "faixas para aliviar o estresse e a ansiedade antes de dormir.",
        "emotional_state": "trata-se de um público com tendência à ansiedade noturna.",
    }
    assert _flags(prose) == []
