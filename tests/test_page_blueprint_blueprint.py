"""Page Blueprint V1 — the Claude sub-step (contract §4.2-§4.7).

``reject_malformed_blueprint`` is the strict shape gate a model response must
pass before anything else runs; a deviation is a ``ResponseRejected``, never a
silent best-effort repair. ``build_prompt`` carries the hard rules the model
must follow (no re-deciding the asset, no content system, the Musical DNA
gate) into the prompt text itself.
"""

from __future__ import annotations

import copy

import pytest

from market_intelligence.schema.enums import Confidence, Language, Market
from page_blueprint.blueprint import ResponseRejected, build_prompt, reject_malformed_blueprint
from page_blueprint.schema.models import ClusterStrategySnapshot

_VALID = {
    "identity": {
        "concept_name": "Ritual Nuevo Hogar",
        "positioning_statement": "the soundtrack for your new-home ritual",
        "bio": "a short bio",
    },
    "visual_identity": {
        "visual_language": "soft cream and gold tones",
        "tone_of_voice": "warm, intimate, ritual",
        "musical_dna_expression_used": "Limpeza energética: light · crystalline · spacious",
    },
    "content_framing": {
        "content_pillars": ["the moving-in ritual"],
        "platforms": ["tiktok"],
        "posting_cadence": "3-4x per week",
    },
    "evaluation": {
        "overall_confidence": "MEDIUM",
        "justification": "cluster fit is high, asset readiness is low",
        "blocked_by": [],
    },
    "red_flags": [],
    "recommendation": {
        "target_next_stage": "CONTENT_STRATEGY",
        "recommended_next_step": "proceed to Content Strategy",
        "justification": "the concept and asset are defined",
    },
}


def _mutate(**patches) -> dict:
    raw = copy.deepcopy(_VALID)
    for path, value in patches.items():
        section, field = path.split(".")
        raw[section][field] = value
    return raw


def test_a_well_formed_response_passes_through_unchanged():
    assert reject_malformed_blueprint(copy.deepcopy(_VALID)) == _VALID


def test_a_non_object_response_is_rejected():
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(["not", "an", "object"])


@pytest.mark.parametrize("section", ["identity", "visual_identity", "content_framing",
                                      "evaluation", "recommendation"])
def test_a_missing_required_section_is_rejected(section):
    raw = copy.deepcopy(_VALID)
    del raw[section]
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(raw)


def test_an_empty_identity_field_is_rejected():
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(_mutate(**{"identity.concept_name": "  "}))


def test_empty_content_pillars_is_rejected():
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(_mutate(**{"content_framing.content_pillars": []}))


def test_an_invalid_confidence_value_is_rejected():
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(_mutate(**{"evaluation.overall_confidence": "SUPER_HIGH"}))


def test_an_invalid_target_next_stage_is_rejected():
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(_mutate(**{"recommendation.target_next_stage": "PUBLISH"}))


def test_an_invalid_red_flag_kind_is_rejected():
    raw = copy.deepcopy(_VALID)
    raw["red_flags"] = [{"description": "x", "severity": "LOW", "kind": "not_a_real_kind"}]
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(raw)


def test_a_0_to_100_score_anywhere_is_rejected():
    with pytest.raises(ResponseRejected):
        reject_malformed_blueprint(_mutate(**{"identity.bio": "this page scores 91/100"}))


def _snapshot() -> ClusterStrategySnapshot:
    return ClusterStrategySnapshot(
        cluster_strategy_id="cs_opp_test", cluster_strategy_ref="ref.json",
        opportunity_id="opp_test", opportunity_run_id="run_test", schema_version="1.0.0",
        cluster_id="limpeza-energetica", cluster_name="Limpeza Energética",
        subcluster_or_angle="new-home ritual", central_concept="x",
        positioning_statement="x", editorial_promise="x",
        market=Market("Mercados hispanohablantes"), language=Language("es"),
        consumption_context="x", music_relationship="x", first_content_direction="x",
        editorial_angles=["a"], overall_confidence=Confidence.LOW,
    )


def test_prompt_forbids_redeciding_the_asset_and_a_content_system():
    prompt = build_prompt(
        _snapshot(), section_9_markdown="## 9. Music DNA\n...", cluster_expression_hint=None,
        guardrails=[], page_context={"primary_playlist_id": "pl_x"},
        musical_dna_needs_input=False,
    )
    assert "Do NOT decide the asset" in prompt
    assert "Do NOT produce a content system" in prompt
    assert "NO 0" in prompt


def test_prompt_forces_low_or_medium_confidence_when_musical_dna_needs_input():
    prompt = build_prompt(
        _snapshot(), section_9_markdown="NEEDS_INPUT", cluster_expression_hint=None,
        guardrails=[], page_context={}, musical_dna_needs_input=True,
    )
    assert "MUST be LOW or MEDIUM" in prompt


def test_prompt_carries_the_9_9_expression_hint_when_given():
    prompt = build_prompt(
        _snapshot(), section_9_markdown="## 9. Music DNA",
        cluster_expression_hint="light · crystalline",
        guardrails=[], page_context={}, musical_dna_needs_input=False,
    )
    assert "light · crystalline" in prompt
