"""Cluster Strategy compliance (contract §9).

Thin wrapper over ``market_intelligence.guardrails``: the pipeline's deterministic
G01/G03/G04 disease-claim scanner, run over this stage's prose, mapped to the
guardrail ``applies_to`` scope families. The subtler claims-vs-topics judgement
is done by Claude in the strategy prompt (calibration inherited from the
Evaluation stage, commit 39fe464). The opportunity's own ``compliance`` red flags
are carried forward by the orchestrator, not here.
"""

from __future__ import annotations

from typing import Dict, Sequence

from market_intelligence.guardrails import (
    SCOPE_EVAL_JUSTIFICATION,
    SCOPE_HYPOTHESES_DIRECTION,
    SCOPE_REPORT_PROSE,
    ComplianceResult,
    check_texts,
)
from market_intelligence.schema.models import Guardrail

# Cluster Strategy prose field -> guardrail applies_to scope family.
#   *_REPORT_PROSE       -> G01, G03, G04, G05, G06, G09, G10 (broadest)
#   *_HYPOTHESES_DIRECTION -> G01, G03, G06, G07
#   *_EVAL_JUSTIFICATION -> G04, G05, G09
_FIELD_SCOPE: Dict[str, str] = {
    "central_concept": SCOPE_REPORT_PROSE,
    "intent": SCOPE_REPORT_PROSE,
    "emotional_state": SCOPE_REPORT_PROSE,
    "editorial_promise": SCOPE_REPORT_PROSE,
    "positioning_statement": SCOPE_REPORT_PROSE,
    "localization_notes": SCOPE_REPORT_PROSE,
    "strategic_coherence_note": SCOPE_REPORT_PROSE,
    "durability_read": SCOPE_REPORT_PROSE,
    "cluster_decision_justification": SCOPE_REPORT_PROSE,
    "framing_hypothesis_comparison": SCOPE_REPORT_PROSE,
    "new_cluster_concept": SCOPE_REPORT_PROSE,
    "new_cluster_why_not_subcluster": SCOPE_REPORT_PROSE,
    "music_relationship": SCOPE_REPORT_PROSE,
    "first_content_direction": SCOPE_HYPOTHESES_DIRECTION,
    "editorial_angles": SCOPE_HYPOTHESES_DIRECTION,
    "market_language_fit_justification": SCOPE_EVAL_JUSTIFICATION,
    "dimension_justification": SCOPE_EVAL_JUSTIFICATION,
    "recommendation_justification": SCOPE_REPORT_PROSE,
}


def check_cluster_strategy_prose(
    prose: Dict[str, object], *, guardrails: Sequence[Guardrail]
) -> ComplianceResult:
    """``prose`` = ``{field_name: str | [str, ...]}``. Unknown keys default to
    ``report_prose`` (the broadest scope). Returns the pipeline's
    ``ComplianceResult`` (findings, red_flags, exclude_opportunity, strip_scopes)."""
    by_scope: Dict[str, list] = {}
    for field, value in prose.items():
        if value is None:
            continue
        scope = _FIELD_SCOPE.get(field, SCOPE_REPORT_PROSE)
        chunk = by_scope.setdefault(scope, [])
        if isinstance(value, str):
            if value.strip():
                chunk.append(value)
        elif isinstance(value, (list, tuple)):
            chunk.extend(str(v) for v in value if str(v).strip())
    return check_texts(by_scope, guardrails=guardrails)
