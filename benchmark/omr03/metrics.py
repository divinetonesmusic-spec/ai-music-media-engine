"""OMR-03 Normalization Benchmark — pure, network-free metrics.

Deliberately isolated from `harness.py` (which does I/O — live model calls). Every
function here is a pure function over plain data structures, so it can be unit
tested without mocking any network or provider. Nothing here is imported by, or
imports, `market_intelligence` production code paths — it only consumes plain
dicts/dataclasses built by the harness from data already validated elsewhere
(`market_intelligence.normalize.llm.validate_llm_response`).

Field severity (spec: OMR-03 Threshold Policy V1, knowledge/DECISIONS-NEEDED.md,
commit ca95573): market/language = HIGH, signal_type = MEDIUM, durability_hint = LOW.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

SEVERITY = {
    "market": "HIGH",
    "language": "HIGH",
    "signal_type": "MEDIUM",
    "durability_hint": "LOW",
}

# The pre-registered per-field accuracy thresholds (OMR-03 Threshold Policy V1).
# Reproduced here as data ONLY for reporting/comparison — this module never
# changes them, and nothing here can be mistaken for altering the policy.
PREREGISTERED_THRESHOLDS = {
    "language": 0.97,
    "market": 0.95,
    "signal_type": 0.90,
    # durability_hint's threshold applies only to cases with an establishable
    # ground truth (excludes INDETERMINATE cases from the denominator).
    "durability_hint": 0.80,
}


@dataclass
class FieldObservation:
    """One (case, field) evaluation point — the atomic unit of comparison."""

    case_id: str
    field: str
    # "DETERMINABLE" | "DETERMINABLE_WITH_ACCEPTABLE_ALTERNATIVE" | "INDETERMINATE"
    ground_truth_status: str
    ground_truth_value: Optional[str]
    acceptable_alternatives: List[str] = field(default_factory=list)
    claude_suggested: Optional[str] = None  # None = field omitted/abstained
    groq_suggested: Optional[str] = None
    claude_technical_error: Optional[str] = None
    groq_technical_error: Optional[str] = None

    def is_indeterminate(self) -> bool:
        return self.ground_truth_status == "INDETERMINATE"

    def matches_ground_truth(self, value: Optional[str]) -> bool:
        if self.is_indeterminate():
            return value is None  # correct = abstaining
        if value is None:
            return False
        return value == self.ground_truth_value or value in self.acceptable_alternatives


def verdict(obs: FieldObservation) -> str:
    """One of: CONCORDANCE_CORRECT, DEGRADATION, ADVANTAGE, BOTH_WRONG, INCONCLUSIVE.

    INCONCLUSIVE covers both "no ground truth" (not used in this dataset — every
    case has at least an INDETERMINATE label) and "a provider hit a technical
    error before producing a semantic answer" (an error is not a wrong answer).
    """
    if obs.claude_technical_error or obs.groq_technical_error:
        return "INCONCLUSIVE"
    claude_ok = obs.matches_ground_truth(obs.claude_suggested)
    groq_ok = obs.matches_ground_truth(obs.groq_suggested)
    if claude_ok and groq_ok:
        return "CONCORDANCE_CORRECT"
    if claude_ok and not groq_ok:
        return "DEGRADATION"
    if not claude_ok and groq_ok:
        return "ADVANTAGE"
    return "BOTH_WRONG"


def degradation_severity(obs: FieldObservation) -> Optional[str]:
    """HIGH/MEDIUM/LOW severity of a DEGRADATION case, further split by whether
    the candidate actively overwrote a correct value (worse) or merely failed to
    resolve it (no worse than not using the candidate at all).
    """
    if verdict(obs) != "DEGRADATION":
        return None
    base = SEVERITY.get(obs.field, "MEDIUM")
    active = obs.groq_suggested is not None  # candidate proposed a wrong value,
    # vs. simply staying silent where Claude correctly resolved the field.
    return f"{base}_ACTIVE" if active else f"{base}_PASSIVE"


def field_accuracy(observations: Sequence[FieldObservation], provider: str) -> dict:
    """Per-field accuracy for one provider ("claude" or "groq"), EXCLUDING
    indeterminate cases from the denominator (OMR-03 policy item 6) and
    EXCLUDING cases where that provider hit a technical error (an error is not
    a wrong semantic answer — it is counted separately, see technical_error_rate).
    """
    by_field: Dict[str, dict] = {}
    for f in sorted({o.field for o in observations}):
        evaluable = [
            o for o in observations
            if o.field == f
            and not o.is_indeterminate()
            and not (o.claude_technical_error if provider == "claude" else o.groq_technical_error)
        ]
        suggested_attr = "claude_suggested" if provider == "claude" else "groq_suggested"
        correct = [o for o in evaluable if o.matches_ground_truth(getattr(o, suggested_attr))]
        n = len(evaluable)
        by_field[f] = {
            "n_evaluable": n,
            "n_correct": len(correct),
            "accuracy": (len(correct) / n) if n else None,
            "threshold": PREREGISTERED_THRESHOLDS.get(f),
            "max_tolerable_errors_at_threshold": (
                _max_errors_within_threshold(n, PREREGISTERED_THRESHOLDS[f])
                if n and f in PREREGISTERED_THRESHOLDS else None
            ),
        }
    return by_field


def _max_errors_within_threshold(n: int, threshold: float) -> int:
    """The largest k such that (n - k) / n >= threshold — i.e. how many wrong
    answers are still compatible with meeting the pre-registered threshold at
    this sample size. Never negative.
    """
    k = 0
    while n and (n - (k + 1)) / n >= threshold:
        k += 1
    return k


def joint_accuracy(observations: Sequence[FieldObservation], provider: str) -> dict:
    """Per-case: are ALL of that case's evaluable (non-indeterminate,
    non-technical-error) fields correct simultaneously? Diagnostic only — never
    a gate (OMR-03 policy item 4).
    """
    by_case: Dict[str, List[FieldObservation]] = {}
    for o in observations:
        by_case.setdefault(o.case_id, []).append(o)
    total, all_correct = 0, 0
    per_case: Dict[str, Optional[bool]] = {}
    for case_id, obs_list in by_case.items():
        evaluable = [
            o for o in obs_list
            if not o.is_indeterminate()
            and not (o.claude_technical_error if provider == "claude" else o.groq_technical_error)
        ]
        if not evaluable:
            per_case[case_id] = None
            continue
        suggested_attr = "claude_suggested" if provider == "claude" else "groq_suggested"
        ok = all(o.matches_ground_truth(getattr(o, suggested_attr)) for o in evaluable)
        per_case[case_id] = ok
        total += 1
        all_correct += 1 if ok else 0
    predicted = 1.0
    field_acc = field_accuracy(observations, provider)
    for stats in field_acc.values():
        if stats["accuracy"] is not None:
            predicted *= stats["accuracy"]
    observed = (all_correct / total) if total else None
    return {
        "per_case": per_case,
        "n_cases_evaluable": total,
        "n_cases_all_correct": all_correct,
        "observed_joint_accuracy": observed,
        "naive_independent_prediction": predicted if field_acc else None,
        "note": "diagnostic only, not a gate (OMR-03 item 4); large gap between "
        "observed and naive_independent_prediction suggests correlated failures",
    }


def indeterminate_rate(observations: Sequence[FieldObservation]) -> dict:
    by_field: Dict[str, dict] = {}
    for f in sorted({o.field for o in observations}):
        field_obs = [o for o in observations if o.field == f]
        n_indet = sum(1 for o in field_obs if o.is_indeterminate())
        by_field[f] = {"n_total": len(field_obs), "n_indeterminate": n_indet}
    return by_field


def abstention_appropriateness(observations: Sequence[FieldObservation], provider: str) -> dict:
    """For INDETERMINATE cases only: did the provider correctly abstain (omit
    the field) rather than force a guess? Separate from accuracy (OMR-03 §2 /
    durability_hint special rule).
    """
    indet = [o for o in observations if o.is_indeterminate()]
    suggested_attr = "claude_suggested" if provider == "claude" else "groq_suggested"
    err_attr = "claude_technical_error" if provider == "claude" else "groq_technical_error"
    evaluable = [o for o in indet if not getattr(o, err_attr)]
    abstained = [o for o in evaluable if getattr(o, suggested_attr) is None]
    n = len(evaluable)
    return {
        "n_indeterminate_evaluable": n,
        "n_appropriately_abstained": len(abstained),
        "rate": (len(abstained) / n) if n else None,
    }


def sensitivity_table(
    observations: Sequence[FieldObservation], multipliers: Sequence[float] = (1, 2, 3, 5)
) -> List[dict]:
    """OMR-03 explicitly forbids inventing a single degradation/improvement
    compensation multiplier. This produces the required sensitivity analysis
    instead: for each candidate multiplier, whether HIGH-severity degradation
    count would be considered 'compensated' by ADVANTAGE count of the same
    severity class. Purely descriptive — picks nothing.
    """
    verdicts = [verdict(o) for o in observations]
    degradations = [
        o for o, v in zip(observations, verdicts, strict=True)
        if v == "DEGRADATION" and SEVERITY.get(o.field) == "HIGH"
    ]
    advantages = [
        o for o, v in zip(observations, verdicts, strict=True)
        if v == "ADVANTAGE" and SEVERITY.get(o.field) == "HIGH"
    ]
    n_deg, n_adv = len(degradations), len(advantages)
    rows = []
    for m in multipliers:
        required_advantages = n_deg * m
        rows.append({
            "multiplier": m,
            "high_severity_degradations_observed": n_deg,
            "high_severity_advantages_observed": n_adv,
            "advantages_required_to_compensate": required_advantages,
            "would_be_compensated": n_adv >= required_advantages if n_deg else True,
        })
    return rows
