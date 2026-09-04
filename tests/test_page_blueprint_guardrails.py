"""Page Blueprint V1 — compliance (contract §6).

Same mechanism as the pipeline: load guardrails.yaml (G01-G10), run
`check_texts` over the stage's prose, scoped by field. A topic mention (a
ritual, an emotional state) is not a violation; a claim of cure/treatment/
guaranteed effect is.
"""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.enums import RedFlagKind, Severity
from market_intelligence.schema.models import RunPaths
from page_blueprint.guardrails import check_page_blueprint_prose

_GUARDRAILS = load_knowledge(RunPaths(), project_root=PROJECT_ROOT).guardrails


def _flags(prose: dict):
    return check_page_blueprint_prose(prose, guardrails=_GUARDRAILS).red_flags


def test_ritual_and_atmosphere_prose_is_not_a_violation():
    clean = {
        "concept_name": "Ritual Nuevo Hogar",
        "positioning_statement": "the soundtrack for your new-home ritual",
        "bio": "an intentional, atmospheric companion for the moving-in ritual",
        "visual_language": "soft cream and gold tones, gentle light",
        "tone_of_voice": "warm, intimate, ritual",
        "posting_cadence": "3-4x per week",
        "content_pillars": ["the moving-in ritual", "renewing your space"],
    }
    assert _flags(clean) == []


def test_an_efficacy_claim_about_health_is_a_compliance_violation():
    prose = {"bio": "this music removes negative energy and cures your anxiety disorder."}
    flags = _flags(prose)
    assert any(f.kind is RedFlagKind.COMPLIANCE and f.severity is Severity.HIGH for f in flags)


def test_invented_science_in_the_positioning_statement_is_a_violation():
    prose = {"positioning_statement": "clinically proven to lower cortisol in listeners."}
    assert any(f.kind is RedFlagKind.COMPLIANCE for f in _flags(prose))


def test_content_pillars_use_the_hypotheses_direction_scope():
    # a claim inside a content pillar is still caught (it's just a narrower scope)
    prose = {"content_pillars": ["this cures your anxiety disorder permanently"]}
    assert any(f.kind is RedFlagKind.COMPLIANCE for f in _flags(prose))


def test_none_values_are_skipped_without_error():
    assert _flags({"bio": None, "content_pillars": []}) == []


def test_an_unknown_field_defaults_to_the_broadest_scope():
    prose = {"some_future_field": "clinically proven to cure insomnia"}
    assert any(f.kind is RedFlagKind.COMPLIANCE for f in _flags(prose))
