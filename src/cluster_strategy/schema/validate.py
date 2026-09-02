"""Deterministic validators for ``ClusterStrategy`` (contract §13).

Semantic rules only — structural checks (field presence/type/enum, unknown-key
rejection) are the shared codec's job. Reuses the pipeline's ``ValidationError`` /
``ERROR`` / ``WARNING`` / ``InventoryIndex`` and its 0–100-score scanner (C6).
"""

from __future__ import annotations

from typing import FrozenSet, Iterable, List

from market_intelligence.schema.codec import encode
from market_intelligence.schema.enums import Confidence
from market_intelligence.schema.validate import (
    ERROR,
    WARNING,
    InventoryIndex,
    ValidationError,
    scan_json_for_numeric_score,
)

from .enums import (
    CLUSTER_DIMENSION_KEYS,
    NEW_ASSET,
    UNKNOWN,
    ClusterDecisionKind,
    TargetNextStage,
)
from .models import (
    AFFINITY_NOTE,
    CONTENT_BOUNDARY_NOTE,
    NEW_CLUSTER_GOVERNANCE_NOTE,
    ClusterStrategy,
)

_CONF_RANK = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}

# Page Blueprint (stage 4) / Content Strategy (stage 5) structural names. The
# models carry none of them, so `decode` already rejects a rogue field; this
# scanner is a regression guard if the models are ever wrongly extended (§B).
_SCOPE_LEAK_KEYS = frozenset({
    "visual_identity", "tone_of_voice", "bio", "pillars", "content_pillars",
    "formats", "hook_library", "hooks", "structures", "cta_copy", "captions",
    "posting_frequency", "cadence", "schedule", "batch_size", "templates",
    "template", "variations", "content_object", "linguistic_rules", "visual_rules",
})

_MAX_EDITORIAL_ANGLES = 6  # more than this reads as a content-pillar list (soft — WARNING)


def scan_for_scope_leakage(raw: dict, path: str = "$") -> List[str]:
    """Reason strings for any Page-Blueprint / Content-Strategy structural key
    found anywhere in an encoded ClusterStrategy (contract §B)."""
    out: List[str] = []
    if isinstance(raw, dict):
        for k, v in raw.items():
            if k in _SCOPE_LEAK_KEYS:
                out.append(f"{path}.{k}: '{k}' belongs to Page Blueprint / Content Strategy")
            out.extend(scan_for_scope_leakage(v, f"{path}.{k}"))
    elif isinstance(raw, list):
        for i, v in enumerate(raw):
            out.extend(scan_for_scope_leakage(v, f"{path}[{i}]"))
    return out


def _e(code: str, path: str, message: str, severity: str = ERROR) -> ValidationError:
    return ValidationError(code=code, path=path, message=message, severity=severity)


def validate_cluster_strategy(
    cs: ClusterStrategy,
    *,
    canonical_cluster_ids: Iterable[str],
    inventory: InventoryIndex,
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    canon: FrozenSet[str] = frozenset(canonical_cluster_ids)
    raw = encode(cs)
    dec = cs.cluster_decision

    # --- schema version pins (D-CS-11) ---
    if cs.schema_version != "1.0.0":
        errs.append(_e("cluster_strategy.schema_version", "$.schema_version",
                       f"schema_version must be '1.0.0', got {cs.schema_version!r}"))
    if cs.opportunity.schema_version != "1.0.0":
        errs.append(_e("cluster_strategy.opportunity_schema_version",
                       "$.opportunity.schema_version",
                       "the source Opportunity Report must be schema_version '1.0.0'"))

    # --- no 0–100 score anywhere (C6) ---
    for reason in scan_json_for_numeric_score(raw):
        errs.append(_e("cluster_strategy.numeric_score_detected", "$", reason))

    # --- scope-leakage regression guard (§B) ---
    for reason in scan_for_scope_leakage(raw):
        errs.append(_e("cluster_strategy.scope_leakage", "$", reason))

    # --- fixed disclaimer tamper checks (§B) ---
    if cs.content_direction and cs.content_direction.content_boundary_note != CONTENT_BOUNDARY_NOTE:
        errs.append(_e("cluster_strategy.content_boundary_note_tampered",
                       "$.content_direction.content_boundary_note",
                       "the fixed content-boundary disclaimer was altered"))
    if cs.asset_strategy and cs.asset_strategy.artist_strategy.affinity_note != AFFINITY_NOTE:
        errs.append(_e("cluster_strategy.affinity_note_tampered",
                       "$.asset_strategy.artist_strategy.affinity_note",
                       "the fixed catalog-affinity disclaimer was altered"))
    if (dec.new_cluster_proposal
            and dec.new_cluster_proposal.governance_note != NEW_CLUSTER_GOVERNANCE_NOTE):
        errs.append(_e("cluster_strategy.governance_note_tampered",
                       "$.cluster_decision.new_cluster_proposal.governance_note",
                       "the fixed P6 governance disclaimer was altered"))
    if "does not execute" not in cs.recommendation.execution_note:
        errs.append(_e("cluster_strategy.execution_note_tampered",
                       "$.recommendation.execution_note",
                       "the fixed execution note (autonomy L1) was altered"))

    # --- the 4 dimension keys, exact (D-CS-4) ---
    keys = list(cs.evaluation.dimensions)
    if set(keys) != set(CLUSTER_DIMENSION_KEYS):
        errs.append(_e("cluster_strategy.dimension_keys", "$.evaluation.dimensions",
                       f"must be exactly {CLUSTER_DIMENSION_KEYS}, got {sorted(keys)}"))
    for k, d in cs.evaluation.dimensions.items():
        if not d.justification.strip():
            errs.append(_e("cluster_strategy.dimension_justification",
                           f"$.evaluation.dimensions.{k}", "justification is empty"))

    # --- editorial_angles must stay a short hypothesis list, not a pillar set (§8, soft) ---
    if (cs.content_direction is not None
            and len(cs.content_direction.editorial_angles) > _MAX_EDITORIAL_ANGLES):
        errs.append(_e("cluster_strategy.too_many_editorial_angles",
                       "$.content_direction.editorial_angles",
                       f"{len(cs.content_direction.editorial_angles)} editorial angles — more "
                       f"than {_MAX_EDITORIAL_ANGLES} reads as a content-pillar list, which is "
                       "Content Strategy's job (contract §8)", severity=WARNING))

    # --- overall_confidence <= the opportunity's, and not raised by sub-ratings (C6, §11) ---
    if _CONF_RANK[cs.evaluation.overall_confidence] > _CONF_RANK[cs.opportunity.overall_confidence]:
        errs.append(_e(
            "cluster_strategy.overall_confidence_exceeds_opportunity",
            "$.evaluation.overall_confidence",
            f"Cluster Strategy overall_confidence ({cs.evaluation.overall_confidence.value}) "
            f"exceeds the opportunity's ({cs.opportunity.overall_confidence.value}) — a "
            "cluster strategy cannot be more confident than the opportunity it rests on (C6)",
        ))

    # --- decision-specific completeness (contract §3, §4.2) ---
    has_strategy = (cs.strategic_definition is not None
                    and cs.asset_strategy is not None
                    and cs.content_direction is not None)

    if dec.decision is ClusterDecisionKind.MAP_TO_EXISTING:
        if not dec.cluster_id or dec.cluster_id not in canon:
            errs.append(_e("cluster_strategy.cluster_id_not_canonical",
                           "$.cluster_decision.cluster_id",
                           f"MAP_TO_EXISTING requires a canonical cluster_id; got "
                           f"{dec.cluster_id!r}"))
        if not has_strategy:
            errs.append(_e("cluster_strategy.strategy_sections_missing", "$",
                           "MAP_TO_EXISTING requires strategic_definition + asset_strategy "
                           "+ content_direction"))

    elif dec.decision is ClusterDecisionKind.PROPOSE_NEW_CLUSTER:
        p = dec.new_cluster_proposal
        if p is None:
            errs.append(_e("cluster_strategy.new_cluster_proposal_missing",
                           "$.cluster_decision.new_cluster_proposal",
                           "PROPOSE_NEW_CLUSTER requires a new_cluster_proposal"))
        else:
            if not p.boundary_vs_adjacent:
                errs.append(_e("cluster_strategy.new_cluster_boundary_missing",
                               "$.cluster_decision.new_cluster_proposal.boundary_vs_adjacent",
                               "a new-cluster proposal MUST state its boundary against "
                               "every adjacent canonical cluster (contract §3.2, §3.3)"))
            bad = sorted(k for k in p.boundary_vs_adjacent if k not in canon)
            if bad:
                errs.append(_e("cluster_strategy.new_cluster_boundary_key",
                               "$.cluster_decision.new_cluster_proposal.boundary_vs_adjacent",
                               f"boundary keys must be canonical cluster ids; unknown: {bad}"))
            if not p.why_not_subcluster.strip():
                errs.append(_e("cluster_strategy.new_cluster_why_not_subcluster",
                               "$.cluster_decision.new_cluster_proposal.why_not_subcluster",
                               "empty — a proposal must argue it is not a subcluster"))
            if not p.supporting_evidence:
                errs.append(_e("cluster_strategy.new_cluster_evidence",
                               "$.cluster_decision.new_cluster_proposal.supporting_evidence",
                               "empty — a proposal needs >= 1 OBSERVED/INFERRED evidence ref"))
        if dec.cluster_id:
            errs.append(_e("cluster_strategy.proposal_has_cluster_id",
                           "$.cluster_decision.cluster_id",
                           "PROPOSE_NEW_CLUSTER must not set a canonical cluster_id"))
        if not has_strategy:
            errs.append(_e("cluster_strategy.strategy_sections_missing", "$",
                           "PROPOSE_NEW_CLUSTER requires strategic_definition + asset_strategy "
                           "+ content_direction"))

    elif dec.decision is ClusterDecisionKind.DEFER:
        if not (dec.deferral_reason or "").strip():
            errs.append(_e("cluster_strategy.deferral_reason_missing",
                           "$.cluster_decision.deferral_reason", "DEFER requires a reason"))

    elif dec.decision is ClusterDecisionKind.REJECT:
        if not (dec.rejection_reason or "").strip():
            errs.append(_e("cluster_strategy.rejection_reason_missing",
                           "$.cluster_decision.rejection_reason", "REJECT requires a reason"))
        if cs.recommendation.target_next_stage not in (
            TargetNextStage.HOLD, TargetNextStage.BACK_TO_MARKET_INTELLIGENCE
        ):
            errs.append(_e("cluster_strategy.reject_next_stage",
                           "$.recommendation.target_next_stage",
                           "a REJECT recommends HOLD or BACK_TO_MARKET_INTELLIGENCE"))

    # --- opportunity lifecycle carried, not transitioned (I2, §10) ---
    # The recommendation must carry the opportunity's ACTUAL registry status
    # (`status`) unchanged — never the Market Intelligence recommendation
    # (`target_state`), which may propose advancing to a different state.
    if cs.recommendation.opportunity_lifecycle_state != cs.opportunity.status:
        errs.append(_e("cluster_strategy.lifecycle_transitioned",
                       "$.recommendation.opportunity_lifecycle_state",
                       f"Cluster Strategy must carry the opportunity's lifecycle state "
                       f"({cs.opportunity.status.value}) unchanged; got "
                       f"{cs.recommendation.opportunity_lifecycle_state.value} (autonomy L1, I2)"))

    # --- asset honesty (I1, spec §10.4) ---
    if cs.asset_strategy is not None:
        a = cs.asset_strategy
        _check_asset(errs, "playlist_strategy.primary_playlist_id",
                     a.playlist_strategy.primary_playlist_id,
                     inventory.playlist_ids, "playlist", allow_new=True)
        for pid in a.playlist_strategy.secondary_playlist_ids:
            _check_asset(errs, "playlist_strategy.secondary_playlist_ids", pid,
                         inventory.playlist_ids, "playlist")
        _check_asset(errs, "page_strategy.primary_page_id",
                     a.page_strategy.primary_page_id, inventory.own_page_ids,
                     "own page", allow_new=True)
        if a.page_strategy.primary_page_id in inventory.reference_page_ids:
            errs.append(_e("cluster_strategy.asset.reference_page",
                           "$.asset_strategy.page_strategy.primary_page_id",
                           "a reference_competitor page can never be a recommended page (§10.3)"))
        for aid in ([a.artist_strategy.best_artist_id]
                    + a.artist_strategy.anchor_hero_artist_ids
                    + a.artist_strategy.catalog_affinity_artist_ids
                    + a.artist_strategy.candidate_artist_ids):
            _check_asset(errs, "artist_strategy", aid, inventory.artist_ids, "artist")

    return errs


def _check_asset(errs, field, asset_id, id_set, label, *, allow_new: bool = False):
    ok = {UNKNOWN} | ({NEW_ASSET} if allow_new else set())
    if asset_id in ok:
        return
    if asset_id not in id_set:
        errs.append(_e("cluster_strategy.asset.not_in_inventory",
                       f"$.asset_strategy.{field}",
                       f"{label} id {asset_id!r} is not in the inventory — never invent (I1)"))
