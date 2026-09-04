"""OMR-03 — turns a harness results file + the ground truth files into
``FieldObservation`` records and a full metrics summary (metrics.py). Pure
transformation over already-persisted data — no network, no provider calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from omr03.metrics import (
    FieldObservation,
    abstention_appropriateness,
    field_accuracy,
    indeterminate_rate,
    joint_accuracy,
    sensitivity_table,
    verdict,
)

HERE = Path(__file__).resolve().parent
GROUND_TRUTH_DIR = HERE / "ground_truth"


def _suggested_value(outcome: dict, field_name: str):
    """None on abstention (field omitted / no suggestions at all) OR on any
    failure (technical error / rejected response) — a failed call produced no
    semantic answer to compare, which is NOT the same as a valid abstention,
    but is represented the same way in FieldObservation.*_suggested because
    the *_technical_error / verdict() logic is what distinguishes them.
    """
    suggestions = outcome.get("suggestions")
    if not suggestions:
        return None
    return suggestions.get(field_name)


def build_observations(results: dict) -> List[FieldObservation]:
    observations: List[FieldObservation] = []
    for case_result in results["results"]:
        case_id = case_result["case_id"]
        gt = json.loads((GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        for field_name, gt_entry in gt["fields"].items():
            claude_out, groq_out = case_result["claude"], case_result["groq"]
            observations.append(FieldObservation(
                case_id=case_id,
                field=field_name,
                ground_truth_status=gt_entry["status"],
                ground_truth_value=gt_entry["ground_truth_value"],
                acceptable_alternatives=gt_entry.get("acceptable_alternatives", []),
                claude_suggested=_suggested_value(claude_out, field_name),
                groq_suggested=_suggested_value(groq_out, field_name),
                claude_technical_error=(
                    claude_out.get("technical_error") or claude_out.get("rejected_reason")
                ),
                groq_technical_error=(
                    groq_out.get("technical_error") or groq_out.get("rejected_reason")
                ),
            ))
    return observations


def standalone_accuracy_vs_ground_truth(
    observations: List[FieldObservation], provider: str
) -> dict:
    """Accuracy of ONE provider against ground truth, independent of whether the
    OTHER provider succeeded. Unlike field_accuracy()+verdict(), this does not
    require both providers to have valid data for a case to count — it exists
    specifically for the situation this execution hit: one provider (Claude)
    was unreachable, so the paired Claude-vs-Groq comparison is INCONCLUSIVE
    for every case, but Groq's OWN accuracy against the independently-built
    ground truth is still real, reportable information.
    """
    err_attr = "claude_technical_error" if provider == "claude" else "groq_technical_error"
    suggested_attr = "claude_suggested" if provider == "claude" else "groq_suggested"
    by_field: dict = {}
    for f in sorted({o.field for o in observations}):
        field_obs = [o for o in observations if o.field == f]
        evaluable = [o for o in field_obs if not o.is_indeterminate() and not getattr(o, err_attr)]
        correct = [o for o in evaluable if o.matches_ground_truth(getattr(o, suggested_attr))]
        failed = [o for o in field_obs if getattr(o, err_attr)]
        indeterminate = [o for o in field_obs if o.is_indeterminate()]
        by_field[f] = {
            "n_total_instances": len(field_obs),
            "n_failed_technical_or_rejected": len(failed),
            "n_indeterminate_excluded": len(indeterminate),
            "n_evaluable": len(evaluable),
            "n_correct": len(correct),
            "accuracy": (len(correct) / len(evaluable)) if evaluable else None,
        }
    return by_field


def summarize(results: dict) -> dict:
    obs = build_observations(results)
    return {
        "n_field_observations": len(obs),
        "claude_standalone_accuracy": standalone_accuracy_vs_ground_truth(obs, "claude"),
        "groq_standalone_accuracy": standalone_accuracy_vs_ground_truth(obs, "groq"),
        "paired_field_accuracy_claude": field_accuracy(obs, "claude"),
        "paired_field_accuracy_groq": field_accuracy(obs, "groq"),
        "joint_accuracy_claude": joint_accuracy(obs, "claude"),
        "joint_accuracy_groq": joint_accuracy(obs, "groq"),
        "indeterminate_rate": indeterminate_rate(obs),
        "abstention_appropriateness_claude": abstention_appropriateness(obs, "claude"),
        "abstention_appropriateness_groq": abstention_appropriateness(obs, "groq"),
        "verdicts": [
            {"case_id": o.case_id, "field": o.field, "verdict": verdict(o)}
            for o in obs
        ],
        "sensitivity_table": sensitivity_table(obs),
    }
