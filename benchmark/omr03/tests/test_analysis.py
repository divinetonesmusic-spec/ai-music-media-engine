"""analysis.py tests — operates on an in-memory fake results dict, no real
results file, no network."""

from __future__ import annotations

from omr03.analysis import build_observations, standalone_accuracy_vs_ground_truth


def _fake_results(*, market_suggestion="Mercados hispanohablantes"):
    return {
        "results": [
            {
                "case_id": "sig_norm_llm_0001",
                "ambiguous_fields": ["market"],
                "claude": {
                    "suggestions": None,
                    "technical_error": "billing", "rejected_reason": None,
                },
                "groq": {
                    "suggestions": {"market": market_suggestion} if market_suggestion else None,
                    "technical_error": None, "rejected_reason": None,
                },
            },
        ],
    }


def test_build_observations_reads_ground_truth_from_disk():
    obs = build_observations(_fake_results())
    assert len(obs) == 1
    o = obs[0]
    assert o.case_id == "sig_norm_llm_0001"
    assert o.field == "market"
    assert o.ground_truth_value == "Mercados hispanohablantes"
    assert o.claude_technical_error == "billing"
    assert o.groq_suggested == "Mercados hispanohablantes"


def test_standalone_accuracy_counts_groq_correct_even_when_claude_failed():
    obs = build_observations(_fake_results())
    acc = standalone_accuracy_vs_ground_truth(obs, "groq")
    assert acc["market"]["n_evaluable"] == 1
    assert acc["market"]["n_correct"] == 1
    assert acc["market"]["accuracy"] == 1.0

    acc_claude = standalone_accuracy_vs_ground_truth(obs, "claude")
    assert acc_claude["market"]["n_evaluable"] == 0
    assert acc_claude["market"]["n_failed_technical_or_rejected"] == 1
    assert acc_claude["market"]["accuracy"] is None


def test_standalone_accuracy_flags_a_wrong_groq_suggestion():
    obs = build_observations(_fake_results(market_suggestion="Brasil"))
    acc = standalone_accuracy_vs_ground_truth(obs, "groq")
    assert acc["market"]["n_correct"] == 0
    assert acc["market"]["accuracy"] == 0.0
