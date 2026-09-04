"""Page Blueprint compliance (contract §6).

Thin wrapper over ``market_intelligence.guardrails``: the pipeline's deterministic
G01/G03/G04 disease-claim scanner, run over this stage's prose, mapped to the
guardrail ``applies_to`` scope families. The subtler claims-vs-topics judgement
is done by Claude in the blueprint prompt (calibration inherited from the
Evaluation / Cluster Strategy stages).
"""

from __future__ import annotations

from typing import Dict, Sequence

from market_intelligence.guardrails import (
    SCOPE_HYPOTHESES_DIRECTION,
    SCOPE_REPORT_PROSE,
    ComplianceResult,
    check_texts,
)
from market_intelligence.schema.models import Guardrail

# Page Blueprint prose field -> guardrail applies_to scope family.
#   *_REPORT_PROSE         -> G01, G03, G04, G05, G06, G09, G10 (broadest)
#   *_HYPOTHESES_DIRECTION -> G01, G03, G06, G07 — content_pillars are still a
#                             non-binding starting direction, same family as
#                             Cluster Strategy's editorial_angles.
_FIELD_SCOPE: Dict[str, str] = {
    "concept_name": SCOPE_REPORT_PROSE,
    "positioning_statement": SCOPE_REPORT_PROSE,
    "bio": SCOPE_REPORT_PROSE,
    "visual_language": SCOPE_REPORT_PROSE,
    "tone_of_voice": SCOPE_REPORT_PROSE,
    "posting_cadence": SCOPE_REPORT_PROSE,
    "recommendation_justification": SCOPE_REPORT_PROSE,
    "content_pillars": SCOPE_HYPOTHESES_DIRECTION,
}


def check_page_blueprint_prose(
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
