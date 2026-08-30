"""Compliance check against guardrails.yaml (spec §13, §14, C4). Deterministic, no network."""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from market_intelligence.guardrails import (
    SCOPE_EVIDENCE,
    SCOPE_HYPOTHESES_HOOK,
    SCOPE_HYPOTHESES_POSITIONING,
    SCOPE_REPORT_PROSE,
    check_texts,
    scan_text,
)
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.enums import RedFlagKind, Severity
from market_intelligence.schema.models import RunPaths

GUARDRAILS = load_knowledge(RunPaths(), project_root=PROJECT_ROOT).guardrails


def test_editorial_cluster_labels_and_wellness_themes_do_not_trip_the_scanner():
    for text in [
        "Posicionamento no cluster Cura / Bem-estar como experiência subjetiva de relaxamento.",
        "Conteúdo de Ansiedade / Relaxamento: acalmar a mente antes de dormir.",
        "A playlist ajuda a criar um ambiente tranquilo para o sono.",
        "Trata-se de um público com tendência à ansiedade noturna.",   # PT idiom, not a claim
        "Se trata de insomnio en estudiantes universitarios.",          # ES idiom, not a claim
        "Faixas para aliviar o estresse e a ansiedade antes de dormir.",
    ]:
        assert scan_text(text, scope=SCOPE_REPORT_PROSE, guardrails=GUARDRAILS) == []


def test_a_cure_claim_about_a_disease_is_a_g01_violation():
    hits = scan_text(
        "Esta faixa cura a depressão em poucos dias.",
        scope=SCOPE_HYPOTHESES_POSITIONING, guardrails=GUARDRAILS,
    )
    assert [h.guardrail_id for h in hits] == ["G01"]
    assert hits[0].severity is Severity.HIGH


def test_treatment_framing_is_a_g03_violation():
    hits = scan_text(
        "Use this as a medical treatment for your condition instead of medication.",
        scope=SCOPE_REPORT_PROSE, guardrails=GUARDRAILS,
    )
    ids = {h.guardrail_id for h in hits}
    assert "G03" in ids


def test_treating_a_named_disease_is_a_g03_violation():
    hits = scan_text(
        "This track treats hypertension over time.",
        scope=SCOPE_REPORT_PROSE, guardrails=GUARDRAILS,
    )
    assert any(h.guardrail_id == "G03" for h in hits)


def test_invented_science_is_a_g04_violation():
    hits = scan_text(
        "It is clinically proven to lower cortisol.",
        scope=SCOPE_EVIDENCE, guardrails=GUARDRAILS,
    )
    assert any(h.guardrail_id == "G04" for h in hits)


def test_scope_gating_only_checks_guardrails_that_apply_to_that_scope():
    # G04 applies to `evidence`, not to `hypotheses.hook`
    text = "clinically proven to work"
    assert any(h.guardrail_id == "G04"
               for h in scan_text(text, scope=SCOPE_EVIDENCE, guardrails=GUARDRAILS))
    assert not any(h.guardrail_id == "G04"
                   for h in scan_text(text, scope=SCOPE_HYPOTHESES_HOOK, guardrails=GUARDRAILS))


def test_violation_in_a_hypothesis_field_strips_it_and_proceeds():
    result = check_texts(
        {SCOPE_HYPOTHESES_POSITIONING: ["This cures your disease permanently."]},
        guardrails=GUARDRAILS,
    )
    assert result.exclude_opportunity is False
    assert SCOPE_HYPOTHESES_POSITIONING in result.strip_scopes
    assert result.red_flags and result.red_flags[0].kind is RedFlagKind.COMPLIANCE


def test_violation_in_core_content_excludes_the_opportunity():
    result = check_texts(
        {SCOPE_EVIDENCE: ["Research proves this track reverses the disease."]},
        guardrails=GUARDRAILS,
    )
    assert result.exclude_opportunity is True
    assert result.red_flags


def test_clean_texts_produce_no_findings():
    result = check_texts(
        {
            SCOPE_HYPOTHESES_POSITIONING: ["A calm bedtime ritual with frequency tracks."],
            SCOPE_EVIDENCE: ["Search interest for sleep-frequency music rose in Brazil."],
            SCOPE_REPORT_PROSE: ["The opportunity targets an evening wind-down routine."],
        },
        guardrails=GUARDRAILS,
    )
    assert result.clean is True
    assert result.red_flags == []
