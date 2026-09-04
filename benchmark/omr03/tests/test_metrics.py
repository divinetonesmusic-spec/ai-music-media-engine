"""Pure-logic tests for omr03.metrics — no network, no provider, no fixtures."""

from __future__ import annotations

from omr03.metrics import (
    FieldObservation,
    abstention_appropriateness,
    degradation_severity,
    field_accuracy,
    indeterminate_rate,
    joint_accuracy,
    sensitivity_table,
    verdict,
)


def _obs(**over) -> FieldObservation:
    base = dict(
        case_id="c1", field="market", ground_truth_status="DETERMINABLE",
        ground_truth_value="Brasil", acceptable_alternatives=[],
        claude_suggested="Brasil", groq_suggested="Brasil",
        claude_technical_error=None, groq_technical_error=None,
    )
    base.update(over)
    return FieldObservation(**base)


def test_matches_ground_truth_exact_value():
    o = _obs(claude_suggested="Brasil")
    assert o.matches_ground_truth(o.claude_suggested)


def test_matches_ground_truth_accepts_registered_alternative():
    o = _obs(
        acceptable_alternatives=["Mercados hispanohablantes"],
        groq_suggested="Mercados hispanohablantes",
    )
    assert o.matches_ground_truth(o.groq_suggested)


def test_indeterminate_case_correct_answer_is_abstention():
    o = _obs(ground_truth_status="INDETERMINATE", ground_truth_value=None, groq_suggested=None)
    assert o.is_indeterminate()
    assert o.matches_ground_truth(None)
    assert not o.matches_ground_truth("Brasil")


def test_verdict_concordance_correct():
    o = _obs(claude_suggested="Brasil", groq_suggested="Brasil")
    assert verdict(o) == "CONCORDANCE_CORRECT"


def test_verdict_degradation_when_claude_right_groq_wrong():
    o = _obs(claude_suggested="Brasil", groq_suggested="English-speaking markets")
    assert verdict(o) == "DEGRADATION"


def test_verdict_advantage_when_groq_right_claude_wrong():
    o = _obs(claude_suggested="English-speaking markets", groq_suggested="Brasil")
    assert verdict(o) == "ADVANTAGE"


def test_verdict_both_wrong():
    o = _obs(claude_suggested="pt", groq_suggested="en", ground_truth_value="Brasil")
    assert verdict(o) == "BOTH_WRONG"


def test_verdict_inconclusive_on_technical_error():
    o = _obs(groq_technical_error="StageError: HTTP 503")
    assert verdict(o) == "INCONCLUSIVE"


def test_degradation_severity_active_vs_passive():
    common = dict(field="language", ground_truth_value="es", claude_suggested="es")
    active = _obs(groq_suggested="pt", **common)
    passive = _obs(groq_suggested=None, **common)
    assert degradation_severity(active) == "HIGH_ACTIVE"
    assert degradation_severity(passive) == "HIGH_PASSIVE"


def test_degradation_severity_none_when_not_a_degradation():
    o = _obs(claude_suggested="Brasil", groq_suggested="Brasil")
    assert degradation_severity(o) is None


def test_degradation_severity_by_field():
    common = dict(ground_truth_value="a", claude_suggested="a", groq_suggested="b")
    st = _obs(field="signal_type", **common)
    dh = _obs(field="durability_hint", **common)
    assert degradation_severity(st) == "MEDIUM_ACTIVE"
    assert degradation_severity(dh) == "LOW_ACTIVE"


def test_field_accuracy_excludes_indeterminate_from_denominator():
    obs = [
        _obs(case_id="c1", field="durability_hint", ground_truth_status="INDETERMINATE",
             ground_truth_value=None, claude_suggested=None, groq_suggested=None),
        _obs(case_id="c2", field="durability_hint", ground_truth_status="DETERMINABLE",
             ground_truth_value="EMERGING", claude_suggested="EMERGING",
             groq_suggested="STRUCTURAL"),
    ]
    acc = field_accuracy(obs, "groq")
    assert acc["durability_hint"]["n_evaluable"] == 1
    assert acc["durability_hint"]["n_correct"] == 0
    assert acc["durability_hint"]["accuracy"] == 0.0


def test_field_accuracy_excludes_technical_error_from_denominator():
    obs = [_obs(field="market", groq_technical_error="StageError")]
    acc = field_accuracy(obs, "groq")
    assert acc["market"]["n_evaluable"] == 0
    assert acc["market"]["accuracy"] is None
    # Claude had no error on this observation, so it IS evaluable for claude.
    acc_claude = field_accuracy(obs, "claude")
    assert acc_claude["market"]["n_evaluable"] == 1


def test_max_tolerable_errors_matches_preregistered_threshold_math():
    obs = [
        _obs(field="language", ground_truth_value="es", claude_suggested="es", groq_suggested="es")
        for _ in range(40)
    ]
    acc = field_accuracy(obs, "groq")
    # language threshold is 0.97; with n=40, 1 error -> 39/40 = 0.975 (>= 0.97, ok);
    # 2 errors -> 38/40 = 0.95 (< 0.97). So max tolerable errors = 1.
    assert acc["language"]["max_tolerable_errors_at_threshold"] == 1


def test_joint_accuracy_flags_gap_between_observed_and_naive_prediction():
    # Two cases, two different fields each with 50% accuracy independently,
    # but the SAME case fails both fields together (correlated failure) ->
    # observed joint accuracy (0%) should be far below the naive product (25%).
    obs = [
        _obs(case_id="hard", field="market", claude_suggested="Brasil", groq_suggested="wrong"),
        _obs(case_id="hard", field="language", claude_suggested="pt", groq_suggested="wrong",
             ground_truth_value="pt"),
        _obs(case_id="easy", field="market", claude_suggested="Brasil", groq_suggested="Brasil"),
        _obs(case_id="easy", field="language", claude_suggested="pt", groq_suggested="pt",
             ground_truth_value="pt"),
    ]
    j = joint_accuracy(obs, "groq")
    assert j["n_cases_evaluable"] == 2
    assert j["n_cases_all_correct"] == 1
    assert j["observed_joint_accuracy"] == 0.5


def test_indeterminate_rate_counts_per_field():
    obs = [
        _obs(case_id="c1", field="durability_hint", ground_truth_status="INDETERMINATE",
             ground_truth_value=None),
        _obs(case_id="c2", field="durability_hint", ground_truth_status="DETERMINABLE",
             ground_truth_value="EMERGING"),
    ]
    rate = indeterminate_rate(obs)
    assert rate["durability_hint"] == {"n_total": 2, "n_indeterminate": 1}


def test_abstention_appropriateness_rewards_omitting_on_indeterminate_case():
    obs = [_obs(field="durability_hint", ground_truth_status="INDETERMINATE",
                ground_truth_value=None, groq_suggested=None)]
    result = abstention_appropriateness(obs, "groq")
    assert result == {"n_indeterminate_evaluable": 1, "n_appropriately_abstained": 1, "rate": 1.0}


def test_abstention_appropriateness_penalizes_forced_guess():
    obs = [_obs(field="durability_hint", ground_truth_status="INDETERMINATE",
                ground_truth_value=None, groq_suggested="EMERGING")]
    result = abstention_appropriateness(obs, "groq")
    assert result["n_appropriately_abstained"] == 0
    assert result["rate"] == 0.0


def test_sensitivity_table_never_picks_a_single_multiplier():
    obs = [
        _obs(field="market", claude_suggested="Brasil", groq_suggested="wrong"),  # HIGH degradation
        _obs(case_id="c2", field="language", claude_suggested="wrong", groq_suggested="es",
             ground_truth_value="es"),  # HIGH advantage
    ]
    table = sensitivity_table(obs, multipliers=(1, 2, 3))
    assert [row["multiplier"] for row in table] == [1, 2, 3]
    assert table[0]["would_be_compensated"] is True   # 1 deg needs 1 adv, have 1
    assert table[1]["would_be_compensated"] is False  # needs 2 adv, have 1
