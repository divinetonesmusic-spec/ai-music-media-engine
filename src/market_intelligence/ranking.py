"""Ranking / Prioritization — spec §11, §18 component 6, §19.

Pure deterministic function. No numeric score (C6): an **ordinal comparator**
whose key order and exclusion rule come entirely from ``config/ranking.yaml``.
The top ``N = max_opportunities_presented`` eligible opportunities are
*presented*; the rest are *parked*; hard-excluded ones (HIGH-severity compliance
red flag, or zero OBSERVED evidence, or an Evaluation-stage exclusion) are
recorded but never presented (§11.1, §11.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .evaluation import EvaluationBundle
from .framing import FramedOpportunity
from .schema.enums import EvidenceType, LifecycleState, Rating, RedFlagKind

PRESENTED = "presented"
PARKED = "parked"
EXCLUDED = "excluded"
TECHNICAL_FAILURE = "technical_failure"

_SEVERITY_WEIGHTS_DEFAULT = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


@dataclass
class RankedOpportunity:
    opportunity_id: str
    bucket: str                       # presented | parked | excluded | technical_failure
    rank: Optional[int]               # 1..N for presented, else None
    # EXPLORE (presented) | PARK (parked / business-excluded) | None (technical_failure —
    # the Evaluation call did not complete, so no business state was decided).
    status: Optional[LifecycleState]
    exclusion_reason: Optional[str] = None
    technical_failure_reason: Optional[str] = None
    sort_key: Tuple = ()


@dataclass
class RankingResult:
    ordered: List[RankedOpportunity]
    presented: List[str] = field(default_factory=list)
    parked: List[str] = field(default_factory=list)
    excluded: List[str] = field(default_factory=list)
    technical_failures: List[str] = field(default_factory=list)

    def by_id(self, opportunity_id: str) -> Optional[RankedOpportunity]:
        return next((r for r in self.ordered if r.opportunity_id == opportunity_id), None)


# --- per-key value extraction --------------------------------

def _observed_count(bundle: EvaluationBundle, opp: FramedOpportunity) -> int:
    return sum(1 for e in opp.evidence if e.type is EvidenceType.OBSERVED and e.signal_ids)


def _high_compliance_flag(bundle: EvaluationBundle) -> bool:
    return any(
        rf.kind is RedFlagKind.COMPLIANCE and rf.severity.value == "HIGH"
        for rf in bundle.evaluation.red_flags
    )


def _count_ratings_high(items) -> int:
    return sum(1 for it in items if it.rating in (Rating.HIGH, Rating.VERY_HIGH))


def _ordinal_index(value: str, tiers: Sequence[Sequence[str]]) -> int:
    for i, tier in enumerate(tiers):
        if value in tier:
            return i
    return len(tiers)  # unknown value sorts last


def _severity_weighted(red_flags, weights: dict) -> int:
    return sum(
        weights.get(rf.severity.value, 1)
        for rf in red_flags
        if rf.kind is not RedFlagKind.COMPLIANCE
    )


def _key_value(key_cfg: dict, opp: FramedOpportunity, bundle: EvaluationBundle):
    """Return a comparable value for one comparator key — smaller sorts first (better)."""
    key = key_cfg["key"]
    kind = key_cfg.get("kind")

    if kind == "ordinal":
        tiers = key_cfg["tiers"]
        if key == "overall_confidence":
            return _ordinal_index(bundle.evaluation.overall_confidence.value, tiers)
        if key == "urgency":
            return _ordinal_index(opp.urgency.value, tiers)
        if key == "durability":
            return _ordinal_index(opp.durability.value, tiers)
        if key == "asset_fit_rating":
            rating = bundle.evaluation.dimensions["asset_fit"].rating.value
            return _ordinal_index(rating, tiers)
        raise KeyError(f"ranking.yaml: unknown ordinal key {key!r}")

    if kind == "count":
        if key == "count_dimensions_high_or_very_high":
            n = _count_ratings_high(bundle.evaluation.dimensions.values())
        elif key == "count_axes_high_or_very_high":
            n = _count_ratings_high(bundle.business_outcome_profile.axes.values())
        else:
            raise KeyError(f"ranking.yaml: unknown count key {key!r}")
        return -n if key_cfg.get("direction", "desc") == "desc" else n

    if kind == "severity_weighted_count":
        weights = key_cfg.get("severity_weights") or _SEVERITY_WEIGHTS_DEFAULT
        w = _severity_weighted(bundle.evaluation.red_flags, weights)
        return w if key_cfg.get("direction", "asc") == "asc" else -w

    if kind == "lexical":
        return opp.opportunity_id

    raise KeyError(f"ranking.yaml: unsupported comparator kind {kind!r} for key {key!r}")


# --- entry point -------------------------------------------

def rank_opportunities(
    opportunities: Sequence[FramedOpportunity],
    bundles: Dict[str, EvaluationBundle],
    *,
    ranking_config: dict,
    max_presented: int,
) -> RankingResult:
    hard = ranking_config.get("hard_exclusion") or {}
    exclude_on_compliance = bool(hard.get("high_severity_compliance_red_flag"))
    exclude_on_no_observed = bool(hard.get("zero_observed_evidence"))
    comparator_keys = ranking_config.get("comparator_keys") or []

    eligible: List[Tuple[Tuple, FramedOpportunity]] = []
    excluded: List[RankedOpportunity] = []
    technical: List[RankedOpportunity] = []

    for opp in opportunities:
        bundle = bundles.get(opp.opportunity_id)
        if bundle is None:
            excluded.append(RankedOpportunity(
                opp.opportunity_id, EXCLUDED, None, LifecycleState.PARK,
                "no evaluation was produced for this opportunity",
            ))
            continue
        if bundle.technical_failure:
            # An Evaluation infrastructure failure is NOT a ranking decision — it is
            # never a hard exclusion (not for compliance, not for zero evidence) and
            # carries no business status (§14). It cannot be presented or parked.
            technical.append(RankedOpportunity(
                opp.opportunity_id, TECHNICAL_FAILURE, None, None,
                technical_failure_reason=bundle.technical_failure_reason
                or "Evaluation could not run",
            ))
            continue
        if bundle.excluded:
            excluded.append(RankedOpportunity(
                opp.opportunity_id, EXCLUDED, None, LifecycleState.PARK,
                bundle.exclusion_reason or "excluded during Evaluation",
            ))
            continue

        reasons = []
        if exclude_on_compliance and _high_compliance_flag(bundle):
            reasons.append("HIGH-severity compliance red flag (spec §11.1)")
        if exclude_on_no_observed and _observed_count(bundle, opp) == 0:
            reasons.append("zero OBSERVED evidence (spec §11.1)")
        if reasons:
            excluded.append(RankedOpportunity(
                opp.opportunity_id, EXCLUDED, None, LifecycleState.PARK, "; ".join(reasons),
            ))
            continue

        sort_key = tuple(_key_value(k, opp, bundle) for k in comparator_keys)
        eligible.append((sort_key, opp))

    eligible.sort(key=lambda pair: pair[0])

    ordered: List[RankedOpportunity] = []
    presented: List[str] = []
    parked: List[str] = []
    for i, (sort_key, opp) in enumerate(eligible):
        if i < max_presented:
            ordered.append(RankedOpportunity(
                opp.opportunity_id, PRESENTED, i + 1, LifecycleState.EXPLORE,
                sort_key=sort_key,
            ))
            presented.append(opp.opportunity_id)
        else:
            ordered.append(RankedOpportunity(
                opp.opportunity_id, PARKED, None, LifecycleState.PARK, sort_key=sort_key,
            ))
            parked.append(opp.opportunity_id)

    ordered.extend(sorted(excluded, key=lambda r: r.opportunity_id))
    ordered.extend(sorted(technical, key=lambda r: r.opportunity_id))
    return RankingResult(
        ordered=ordered,
        presented=presented,
        parked=parked,
        excluded=[r.opportunity_id for r in excluded],
        technical_failures=[r.opportunity_id for r in technical],
    )
