"""Deterministic validators for ``PageBlueprint`` (contract §6).

Semantic rules only — structural checks (field presence/type/enum, unknown-key
rejection) are the shared codec's job. Reuses the pipeline's ``ValidationError`` /
``ERROR`` / ``WARNING`` / ``InventoryIndex`` and its 0–100-score scanner (C6).
"""

from __future__ import annotations

from typing import Iterable, List

from market_intelligence.schema.codec import encode
from market_intelligence.schema.enums import Confidence
from market_intelligence.schema.validate import (
    ERROR,
    WARNING,
    InventoryIndex,
    ValidationError,
    scan_json_for_numeric_score,
)

from .models import (
    ASSET_INHERITANCE_NOTE,
    CONTENT_BOUNDARY_NOTE,
    PageBlueprint,
)

_CONF_RANK = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
_MAX_CONTENT_PILLARS = 5  # more than this reads as a full content system (Content Strategy's job)

# Content Strategy (stage 5) structural names. The models carry none of them, so
# `decode` already rejects a rogue field; this scanner is a regression guard if
# the models are ever wrongly extended (mirrors cluster_strategy's own guard).
_SCOPE_LEAK_KEYS = frozenset({
    "formats", "hook_library", "hooks", "structures", "cta_copy", "captions",
    "batch_size", "templates", "template", "variations", "content_object",
    "linguistic_rules", "visual_rules", "schedule", "publishing_calendar",
})

# UNKNOWN / NEW_ASSET sentinels (spec §15, cluster_strategy.schema.enums) — page
# Blueprint reuses the string values directly rather than re-importing the enum,
# to avoid a needless coupling for two literals.
_UNKNOWN = "UNKNOWN"
_NEW_ASSET = "NEW_ASSET"


def _e(code: str, path: str, message: str, severity: str = ERROR) -> ValidationError:
    return ValidationError(code=code, path=path, message=message, severity=severity)


def scan_for_scope_leakage(raw: dict, path: str = "$") -> List[str]:
    """Reason strings for any Content-Strategy structural key found anywhere in
    an encoded PageBlueprint (contract §B)."""
    out: List[str] = []
    if isinstance(raw, dict):
        for k, v in raw.items():
            if k in _SCOPE_LEAK_KEYS:
                out.append(f"{path}.{k}: '{k}' belongs to Content Strategy (stage 5)")
            out.extend(scan_for_scope_leakage(v, f"{path}.{k}"))
    elif isinstance(raw, list):
        for i, v in enumerate(raw):
            out.extend(scan_for_scope_leakage(v, f"{path}[{i}]"))
    return out


def _check_asset(errs: List[ValidationError], field: str, asset_id: str,
                  id_set: Iterable[str], label: str, *, allow_new: bool = False) -> None:
    ok = {_UNKNOWN} | ({_NEW_ASSET} if allow_new else set())
    if asset_id in ok:
        return
    if asset_id not in set(id_set):
        errs.append(_e("page_blueprint.asset.not_in_inventory", f"$.asset_link.{field}",
                       f"{label} id {asset_id!r} is not in the inventory — never invent (I1)"))


def validate_page_blueprint(
    pb: PageBlueprint,
    *,
    cluster_strategy_overall_confidence: Confidence,
    inventory: InventoryIndex,
    musical_dna_needs_input: bool = True,
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    raw = encode(pb)

    # --- schema version pins ---
    if pb.schema_version != "1.0.0":
        errs.append(_e("page_blueprint.schema_version", "$.schema_version",
                       f"schema_version must be '1.0.0', got {pb.schema_version!r}"))
    if pb.cluster_strategy.schema_version != "1.0.0":
        errs.append(_e("page_blueprint.cluster_strategy_schema_version",
                       "$.cluster_strategy.schema_version",
                       "the source ClusterStrategy must be schema_version '1.0.0'"))

    # --- no 0–100 score anywhere (C6) ---
    for reason in scan_json_for_numeric_score(raw):
        errs.append(_e("page_blueprint.numeric_score_detected", "$", reason))

    # --- scope-leakage regression guard (§B) ---
    for reason in scan_for_scope_leakage(raw):
        errs.append(_e("page_blueprint.scope_leakage", "$", reason))

    # --- fixed disclaimer tamper checks (§B) ---
    if pb.content_framing.content_boundary_note != CONTENT_BOUNDARY_NOTE:
        errs.append(_e("page_blueprint.content_boundary_note_tampered",
                       "$.content_framing.content_boundary_note",
                       "the fixed content-boundary disclaimer was altered"))
    if pb.asset_link.asset_inheritance_note != ASSET_INHERITANCE_NOTE:
        errs.append(_e("page_blueprint.asset_inheritance_note_tampered",
                       "$.asset_link.asset_inheritance_note",
                       "the fixed asset-inheritance disclaimer was altered"))
    if "does not execute" not in pb.recommendation.execution_note:
        errs.append(_e("page_blueprint.execution_note_tampered",
                       "$.recommendation.execution_note",
                       "the fixed execution note (autonomy L1) was altered"))

    # --- content pillars stay a broad outline, not a content system (D-PB-2, soft) ---
    n_pillars = len(pb.content_framing.content_pillars)
    if n_pillars > _MAX_CONTENT_PILLARS:
        errs.append(_e("page_blueprint.too_many_content_pillars",
                       "$.content_framing.content_pillars",
                       f"{n_pillars} content pillars — more than {_MAX_CONTENT_PILLARS} reads as "
                       "a content system, which is Content Strategy's job (contract §5)",
                       severity=WARNING))
    if n_pillars == 0:
        errs.append(_e("page_blueprint.no_content_pillars", "$.content_framing.content_pillars",
                       "at least one content pillar is required"))

    # --- overall_confidence <= the ClusterStrategy's, not raised by the synthesis (C6) ---
    pb_rank = _CONF_RANK[pb.evaluation.overall_confidence]
    cs_rank = _CONF_RANK[cluster_strategy_overall_confidence]
    if pb_rank > cs_rank:
        errs.append(_e(
            "page_blueprint.overall_confidence_exceeds_cluster_strategy",
            "$.evaluation.overall_confidence",
            f"Page Blueprint overall_confidence ({pb.evaluation.overall_confidence.value}) "
            f"exceeds the Cluster Strategy's ({cluster_strategy_overall_confidence.value}) — a "
            "page design cannot be more confident than the strategy it rests on (C6)",
        ))

    # --- Musical DNA §9 gate (mirrors evaluation._build_bundle's music_fit cap) ---
    if (musical_dna_needs_input
            and pb.evaluation.overall_confidence is Confidence.HIGH):
        errs.append(_e(
            "page_blueprint.confidence_exceeds_musical_dna_cap",
            "$.evaluation.overall_confidence",
            "overall_confidence is HIGH but business-dna §9 (Musical DNA) is NEEDS_INPUT — "
            "visual identity / tone of voice cannot be HIGH-confidence without it (D-PB-4)",
        ))
    if not pb.visual_identity.musical_dna_expression_used.strip():
        errs.append(_e("page_blueprint.musical_dna_expression_missing",
                       "$.visual_identity.musical_dna_expression_used",
                       "visual_identity must cite the §9.9 cluster-expression phrase it used "
                       "(D-PB-4) — never invent a visual identity untethered from §9"))

    # --- asset honesty (I1) — the ids are carried, but must still trace to the inventory ---
    a = pb.asset_link
    _check_asset(errs, "page_strategy.primary_page_id", a.page_strategy.primary_page_id,
                 inventory.own_page_ids, "own page", allow_new=True)
    if a.page_strategy.primary_page_id in inventory.reference_page_ids:
        errs.append(_e("page_blueprint.asset.reference_page",
                       "$.asset_link.page_strategy.primary_page_id",
                       "a reference_competitor page can never be a designed page (spec §10.3)"))
    _check_asset(errs, "primary_playlist_id", a.primary_playlist_id,
                 inventory.playlist_ids, "playlist", allow_new=True)
    _check_asset(errs, "primary_artist_id", a.primary_artist_id,
                 inventory.artist_ids, "artist")

    return errs
