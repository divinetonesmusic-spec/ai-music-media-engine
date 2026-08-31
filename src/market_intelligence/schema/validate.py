"""Deterministic validators for the V1 rule set (docs/TECHNICAL-SPEC-V1.md §13).

Each validator takes a decoded model instance (plus whatever external context it
needs — known signal ids, the canonical cluster ids, an inventory index) and
returns a ``list[ValidationError]``. An empty list means valid.

Severity:
  * ``ERROR``   — blocks the entity from the presented set (spec §13 intro).
  * ``WARNING`` — logged; the entity continues (e.g. a dropped asset reference, §14).

These validators enforce *semantic* rules. Structural rules (field presence,
field type, enum membership) are enforced earlier by ``codec.decode``.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

from . import models as M
from .codec import encode
from .enums import (
    AXIS_KEYS,
    DIMENSION_KEYS,
    LANGUAGE_TO_MARKET,
    OPPORTUNITY_PLATFORMS,
    CaptureMethod,
    Confidence,
    EvidenceType,
    Language,
    Market,
    SourceType,
)
from .ids import opportunity_id_base

ERROR = "ERROR"
WARNING = "WARNING"

_SIGNAL_MARKETS = {m.value for m in Market} | {"UNKNOWN"}
_SIGNAL_LANGUAGES = {lang.value for lang in Language} | {"UNKNOWN"}
_OPP_ID_BASE_RE = re.compile(r"^opp_(\d{4}-\d{2}-\d{2})_([0-9a-f]{10})(?:-\d+)?$")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_\-]+$")

# spec §6.5 — capture_method that each source_type must use.
_CAPTURE_FOR_SOURCE = {
    SourceType.WEB_SEARCH: CaptureMethod.CLAUDE_WEB_SEARCH,
    SourceType.YOUTUBE: CaptureMethod.YOUTUBE_DATA_API,
    SourceType.TIKTOK_CREATIVE_CENTER: CaptureMethod.ANALYST_CAPTURE,
    SourceType.INTERNAL_DATA: CaptureMethod.INTERNAL_DATA,
}

# spec §13 / §14 — knowledge paths that MUST already exist for a run to start.
# The registry may legitimately be absent (first run); data/ and reports/ are
# created at runtime.
_REQUIRED_EXISTING_PATHS = (
    "knowledge_dir",
    "inventories_dir",
    "business_dna_path",
    "content_methodology_path",
    "guardrails_path",
    "taxonomy_path",
    "ranking_config_path",
    "dedup_config_path",
)

# "no score" scanner (spec §13, C6). Conservative: only fires on an explicit
# X/100 construction or the word "score" adjacent to a 1–3 digit number.
_SCORE_PATTERNS = (
    re.compile(r"\b\d{1,3}\s*/\s*100\b"),
    re.compile(r"\b\d{1,3}\s*(?:out of|de)\s*100\b", re.IGNORECASE),
    re.compile(r"\bscores?\b[^.\n]{0,15}?\b\d{1,3}\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}\b[^.\n]{0,10}?\bscores?\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ValidationError:
    code: str
    path: str
    message: str
    severity: str = ERROR


@dataclass(frozen=True)
class InventoryIndex:
    """The id sets Asset Matching validation needs (built by the Knowledge Loader)."""

    artist_ids: frozenset
    playlist_ids: frozenset
    page_ids: frozenset
    catalog_ids: frozenset
    own_page_ids: frozenset
    reference_page_ids: frozenset


def blocking(errors: Iterable[ValidationError]) -> List[ValidationError]:
    """The subset that blocks presentation (severity == ERROR)."""
    return [e for e in errors if e.severity == ERROR]


# --- helpers ---------------------------------------------------------------

def _blank(value: Optional[str]) -> bool:
    return value is None or not str(value).strip()


def _iter_strings(obj: Any, path: str = "") -> Iterator[Tuple[str, str]]:
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _iter_strings(v, f"{path}[{i}]")


def _scan_for_numeric_score(entity: Any, base_path: str) -> List[ValidationError]:
    out: List[ValidationError] = []
    for path, text in _iter_strings(encode(entity), base_path):
        if any(p.search(text) for p in _SCORE_PATTERNS):
            out.append(
                ValidationError(
                    code="evaluation.numeric_score_detected",
                    path=path,
                    message=f"text reads as a 0–100 score, which V1 forbids (C6): {text!r}",
                )
            )
    return out


def scan_json_for_numeric_score(raw: Any, base_path: str = "$") -> List[str]:
    """Reason strings for any 0–100 score in a raw parsed-JSON structure (C6).

    Same patterns as ``_scan_for_numeric_score`` but over a plain dict/list (no
    dataclass ``encode``) — used to reject a malformed Evaluation response before
    it is assembled (spec §19, owner decision 2026-08-31).
    """
    return [
        f"{path} reads as a 0–100 score (C6): {text!r}"
        for path, text in _iter_strings(raw, base_path)
        if any(p.search(text) for p in _SCORE_PATTERNS)
    ]


def _parse_date(value: str) -> Optional[_dt.date]:
    try:
        return _dt.date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


# --- §6 Signal ----------------------------------------------------------

def validate_signal(
    sig: M.Signal, *, raw_root: Optional[Path] = None
) -> List[ValidationError]:
    """Validate one Signal against spec §6.1 / §6.3.

    ``raw_root``: the run's ``.../signals/raw`` directory. When given, also checks
    that ``raw_ref`` resolves to an existing capture file (§6.3).
    """
    errs: List[ValidationError] = []
    sid = sig.signal_id

    if raw_root is not None and not (Path(raw_root) / f"{sid}.json").is_file():
        errs.append(ValidationError(
            "signal.raw_ref_missing_file", f"{sid}.raw_ref",
            f"raw_ref {sig.raw_ref!r} does not resolve to a file under {raw_root} (spec §6.3)",
        ))

    if sig.market not in _SIGNAL_MARKETS:
        errs.append(ValidationError(
            "signal.market_not_in_taxonomy", f"{sid}.market",
            f"{sig.market!r} is not a V1 market or UNKNOWN (spec §6.3)",
        ))
    if sig.language not in _SIGNAL_LANGUAGES:
        errs.append(ValidationError(
            "signal.language_not_in_taxonomy", f"{sid}.language",
            f"{sig.language!r} is not pt/es/en/UNKNOWN (spec §6.3)",
        ))

    expected_raw_ref = f"data/{sig.run_id}/signals/raw/{sid}.json"
    if sig.raw_ref != expected_raw_ref:
        errs.append(ValidationError(
            "signal.raw_ref_shape", f"{sid}.raw_ref",
            f"raw_ref must be {expected_raw_ref!r} (spec §6.1), got {sig.raw_ref!r}",
        ))

    obs = _parse_date(sig.observed_at) if sig.observed_at != "UNKNOWN" else None
    col = _parse_date(sig.collected_at)
    if obs and col and obs > col:
        errs.append(ValidationError(
            "signal.observed_at_in_future", f"{sid}.observed_at",
            f"observed_at {sig.observed_at} is after collected_at {sig.collected_at} (spec §6.3)",
        ))

    expected_capture = _CAPTURE_FOR_SOURCE.get(sig.source_type)
    if expected_capture and sig.provenance.capture_method != expected_capture:
        errs.append(ValidationError(
            "signal.capture_method_mismatch", f"{sid}.provenance.capture_method",
            f"source_type {sig.source_type.value!r} requires capture_method "
            f"{expected_capture.value!r} (spec §6.5), got "
            f"{sig.provenance.capture_method.value!r}",
        ))

    p = sig.provenance
    mirror_mismatch = (
        sig.source != p.source
        or sig.source_type != p.source_type
        or sig.observed_at != p.observed_at
        or sig.collected_at != p.collected_at
        or (sig.url is not None and sig.url != p.url)
    )
    if mirror_mismatch:
        errs.append(ValidationError(
            "signal.provenance_mirror_mismatch", f"{sid}.provenance",
            "top-level source / source_type / observed_at / collected_at / url must mirror "
            "provenance (spec §6.1)",
        ))

    return errs


def validate_signals(
    signals: Sequence[M.Signal], *, raw_root: Optional[Path] = None
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    seen: Set[str] = set()
    for sig in signals:
        if sig.signal_id in seen:
            errs.append(ValidationError(
                "signal.duplicate_id", sig.signal_id,
                f"signal_id {sig.signal_id!r} is not unique within the run (spec §6.3)",
            ))
        seen.add(sig.signal_id)
        errs.extend(validate_signal(sig, raw_root=raw_root))
    return errs


# --- §7 / §8 / §9 / §10 Opportunity --------------------------------------

def validate_opportunity(
    opp: M.Opportunity,
    *,
    known_signal_ids: Iterable[str],
    canonical_cluster_ids: Iterable[str],
    inventory: InventoryIndex,
    musical_dna_needs_input: bool = True,
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    known = set(known_signal_ids)
    clusters = set(canonical_cluster_ids)

    # C1 mandatory minimum structure — present (codec) and non-empty (here).
    if _blank(opp.need):
        errs.append(ValidationError("opportunity.c1_field_empty", "need", "need is empty (C1)"))
    if _blank(opp.consumption_context):
        errs.append(ValidationError(
            "opportunity.c1_field_empty", "consumption_context",
            "consumption_context is empty (C1)",
        ))
    if opp.audience is None or _blank(opp.audience.description):
        errs.append(ValidationError(
            "opportunity.c1_field_empty", "audience.description",
            "audience.description is empty (C1)",
        ))

    # §7.1a — language and market must be consistent.
    if LANGUAGE_TO_MARKET.get(opp.language) != opp.market:
        errs.append(ValidationError(
            "opportunity.market_language_mismatch", "market/language",
            f"language {opp.language.value!r} implies market "
            f"{LANGUAGE_TO_MARKET[opp.language].value!r}, got {opp.market.value!r} (spec §7.1a)",
        ))

    # §7.1 — platform is the Opportunity subset (no 'web' / 'UNKNOWN').
    if opp.platform not in OPPORTUNITY_PLATFORMS:
        errs.append(ValidationError(
            "opportunity.platform_not_allowed", "platform",
            f"{opp.platform.value!r} is not an Opportunity platform (spec §7.1)",
        ))

    # §7.1 / §13 — opportunity_id is the deterministic hash of the C1 tuple.
    m = _OPP_ID_BASE_RE.match(opp.opportunity_id)
    if not m:
        errs.append(ValidationError(
            "opportunity.id_malformed", "opportunity_id",
            f"{opp.opportunity_id!r} is not a well-formed opportunity id (spec §7.1)",
        ))
    else:
        expected_hash = opportunity_id_base(
            opp.need, opp.audience.description if opp.audience else "",
            opp.market.value, opp.language.value, opp.platform.value,
        )
        if m.group(2) != expected_hash:
            errs.append(ValidationError(
                "opportunity.id_hash_mismatch", "opportunity_id",
                f"opportunity_id hash {m.group(2)!r} does not match the C1 tuple "
                f"(expected {expected_hash!r}) (spec §7.1)",
            ))

    # Evidence (§7.3, §13).
    if not opp.evidence:
        errs.append(ValidationError(
            "opportunity.no_evidence", "evidence", "an opportunity needs >= 1 evidence item (§13)",
        ))
    if opp.evidence and not any(e.type is EvidenceType.OBSERVED for e in opp.evidence):
        errs.append(ValidationError(
            "opportunity.no_observed_evidence", "evidence",
            ">= 1 OBSERVED evidence item is required to be eligible for the presented set (§13)",
        ))
    errs.extend(_validate_evidence(opp.evidence, known))

    # Hypotheses — potential_cluster (§7.2, §13).
    if opp.hypotheses and opp.hypotheses.potential_cluster:
        errs.extend(_validate_potential_cluster(opp.hypotheses.potential_cluster, clusters))

    # Delegated sub-entities.
    errs.extend(validate_evaluation(
        opp.evaluation, musical_dna_needs_input=musical_dna_needs_input,
    ))
    errs.extend(validate_business_outcome_profile(opp.business_outcome_profile))
    errs.extend(validate_asset_match(opp.asset_fit, inventory=inventory))

    # C6 — no 0–100 score in the recommendation prose either.
    errs.extend(_scan_for_numeric_score(opp.recommendation, "recommendation"))

    # §16.3(d) — OpportunityProvenance.signal_ids must cover the union of every
    # signal cited by OBSERVED evidence and referenced by INFERRED derived_from.
    cited = {
        s for e in opp.evidence for s in (e.signal_ids or [])
    } | {
        r for e in opp.evidence if e.type is EvidenceType.INFERRED
        for r in (e.derived_from or []) if r in known
    }
    missing_prov = sorted(cited - set(opp.provenance.signal_ids))
    if missing_prov:
        errs.append(ValidationError(
            "provenance.signal_ids_incomplete", "provenance.signal_ids",
            f"provenance.signal_ids does not cover every cited signal (missing {missing_prov}) "
            f"(spec §16.3)",
        ))

    return errs


def _validate_evidence(
    items: Sequence[M.EvidenceItem], known_signal_ids: Set[str]
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    count = len(items)
    for i, item in enumerate(items):
        at = f"evidence[{i}]"
        if item.type is EvidenceType.OBSERVED:
            if not item.signal_ids:
                errs.append(ValidationError(
                    "evidence.observed_without_signal_ids", at,
                    "OBSERVED evidence must list signal_ids (spec §7.3)",
                ))
            for s in item.signal_ids or []:
                if s not in known_signal_ids:
                    errs.append(ValidationError(
                        "evidence.signal_id_unresolved", f"{at}.signal_ids",
                        f"signal_id {s!r} does not resolve to a signal in this run (§13)",
                    ))
        elif item.type is EvidenceType.INFERRED:
            if not item.derived_from:
                errs.append(ValidationError(
                    "evidence.inferred_without_basis", at,
                    "INFERRED evidence must list derived_from (spec §7.3)",
                ))
            if _blank(item.rationale):
                errs.append(ValidationError(
                    "evidence.inferred_without_rationale", at,
                    "INFERRED evidence must carry a rationale (spec §7.3)",
                ))
            for ref in item.derived_from or []:
                if not _evidence_ref_resolves(ref, known_signal_ids, count):
                    errs.append(ValidationError(
                        "evidence.derived_from_unresolved", f"{at}.derived_from",
                        f"{ref!r} is neither a known signal_id nor an evidence index",
                        severity=WARNING,
                    ))
        elif item.type is EvidenceType.HYPOTHESIS:
            if _blank(item.rationale):
                errs.append(ValidationError(
                    "evidence.hypothesis_without_rationale", at,
                    "HYPOTHESIS evidence must carry a rationale (spec §7.3)",
                ))
    return errs


def _evidence_ref_resolves(ref: str, known_signal_ids: Set[str], count: int) -> bool:
    if ref in known_signal_ids:
        return True
    m = re.match(r"^(?:#|evidence\[)?(\d+)\]?$", ref.strip())
    return bool(m) and int(m.group(1)) < count


def _validate_potential_cluster(
    pc: M.PotentialCluster, canonical_cluster_ids: Set[str]
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    if pc.basis not in ("existing", "proposed_new"):
        errs.append(ValidationError(
            "hypotheses.cluster_basis_invalid", "hypotheses.potential_cluster.basis",
            f"basis must be 'existing' or 'proposed_new', got {pc.basis!r} (spec §7.2)",
        ))
    if pc.canonical:
        if pc.value not in canonical_cluster_ids:
            errs.append(ValidationError(
                "hypotheses.cluster_not_canonical", "hypotheses.potential_cluster.value",
                f"{pc.value!r} is marked canonical but is not in cluster-taxonomy.md (§13)",
            ))
        if pc.basis != "existing":
            errs.append(ValidationError(
                "hypotheses.cluster_basis_inconsistent", "hypotheses.potential_cluster",
                "canonical: true requires basis: 'existing' (spec §7.2)",
            ))
    else:
        if pc.basis != "proposed_new":
            errs.append(ValidationError(
                "hypotheses.cluster_basis_inconsistent", "hypotheses.potential_cluster",
                "a non-canonical cluster must have basis: 'proposed_new' (spec §7.2, P6)",
            ))
    return errs


# --- §8 Evaluation ----------------------------------------------------

def validate_evaluation(
    ev: M.Evaluation, *, musical_dna_needs_input: bool = True
) -> List[ValidationError]:
    errs: List[ValidationError] = []

    if set(ev.dimensions) != set(DIMENSION_KEYS):
        missing = sorted(set(DIMENSION_KEYS) - set(ev.dimensions))
        extra = sorted(set(ev.dimensions) - set(DIMENSION_KEYS))
        errs.append(ValidationError(
            "evaluation.dimension_set_mismatch", "evaluation.dimensions",
            f"expected exactly the 10 dimensions (§8.1); missing={missing} extra={extra}",
        ))

    for key, dim in ev.dimensions.items():
        if _blank(dim.justification):
            errs.append(ValidationError(
                "evaluation.justification_empty", f"evaluation.dimensions.{key}.justification",
                "each dimension needs a non-empty justification (§13)",
            ))

    if musical_dna_needs_input and "music_fit" in ev.dimensions:
        if ev.dimensions["music_fit"].confidence is Confidence.HIGH:
            errs.append(ValidationError(
                "evaluation.music_fit_confidence_cap", "evaluation.dimensions.music_fit.confidence",
                "music_fit confidence is capped at LOW/MEDIUM while musical DNA detail is "
                "NEEDS_INPUT (spec §8.3, business-dna §9)",
            ))

    if _blank(ev.summary):
        errs.append(ValidationError(
            "evaluation.summary_empty", "evaluation.summary", "summary is empty (§8.2)",
        ))

    errs.extend(_scan_for_numeric_score(ev, "evaluation"))
    return errs


# --- §9 Business Outcome Profile ------------------------------------

def validate_business_outcome_profile(
    bop: M.BusinessOutcomeProfile,
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    if set(bop.axes) != set(AXIS_KEYS):
        missing = sorted(set(AXIS_KEYS) - set(bop.axes))
        extra = sorted(set(bop.axes) - set(AXIS_KEYS))
        errs.append(ValidationError(
            "bop.axis_set_mismatch", "business_outcome_profile.axes",
            f"expected exactly the 5 axes (§9.1); missing={missing} extra={extra}",
        ))
    for key, axis in bop.axes.items():
        if _blank(axis.justification):
            errs.append(ValidationError(
                "bop.justification_empty", f"business_outcome_profile.axes.{key}.justification",
                "each axis needs a non-empty justification (§13)",
            ))
    errs.extend(_scan_for_numeric_score(bop, "business_outcome_profile"))
    return errs


# --- §10 Asset Matching --------------------------------------------

def validate_asset_match(
    am: M.AssetMatch, *, inventory: InventoryIndex
) -> List[ValidationError]:
    errs: List[ValidationError] = []

    def check_candidates(cands, id_set, label):
        for c in cands or []:
            if c.asset_id not in id_set:
                errs.append(ValidationError(
                    "asset_fit.candidate_id_unknown", f"asset_fit.matching_{label}",
                    f"{c.asset_id!r} is not in the {label} inventory — reference must be dropped "
                    f"and the field set to UNKNOWN (spec §10.4, §14)",
                    severity=WARNING,
                ))

    check_candidates(am.matching_playlists, inventory.playlist_ids, "playlists")
    check_candidates(am.matching_pages, inventory.page_ids, "pages")
    check_candidates(am.matching_artists, inventory.artist_ids, "artists")
    check_candidates(am.matching_catalog, inventory.catalog_ids, "catalog")

    for page in am.matching_pages or []:
        if page.asset_id in inventory.reference_page_ids and page.role != M.AssetRole.REFERENCE:
            errs.append(ValidationError(
                "asset_fit.reference_page_role", "asset_fit.matching_pages",
                f"reference_competitor page {page.asset_id!r} may only appear with role "
                f"'reference' (spec §10.3)",
                severity=WARNING,
            ))

    checks = (
        ("best_playlist", am.best_playlist, inventory.playlist_ids, ("UNKNOWN",)),
        ("best_artist", am.best_artist, inventory.artist_ids, ("UNKNOWN",)),
        ("best_page", am.best_page, inventory.page_ids, ("UNKNOWN", "NEW_ASSET")),
    )
    for field_name, value, id_set, sentinels in checks:
        if value not in sentinels and value not in id_set:
            errs.append(ValidationError(
                "asset_fit.best_id_unknown", f"asset_fit.{field_name}",
                f"{value!r} is neither a valid inventory id nor one of {sentinels} "
                f"(spec §10.3, §10.4)",
            ))

    if am.best_page in inventory.reference_page_ids:
        errs.append(ValidationError(
            "asset_fit.reference_page_not_recommendable", "asset_fit.best_page",
            f"reference_competitor page {am.best_page!r} can never be a recommended page "
            f"(spec §10.3)",
        ))

    any_unknown_best = "UNKNOWN" in (am.best_playlist, am.best_page, am.best_artist)
    if any_unknown_best and _blank(am.unmatched_reason):
        errs.append(ValidationError(
            "asset_fit.unmatched_reason_missing", "asset_fit.unmatched_reason",
            "unmatched_reason is required whenever a best_* is UNKNOWN (spec §10.3)",
        ))

    if am.best_page == "NEW_ASSET" and am.new_asset_recommendation is None:
        errs.append(ValidationError(
            "asset_fit.new_asset_without_recommendation", "asset_fit.best_page",
            "best_page = NEW_ASSET requires a new_asset_recommendation (spec §10.3, I5)",
        ))

    rec = am.new_asset_recommendation
    if rec is not None:
        c = rec.i5_conditions_met
        if not (c.no_adequate_fit and c.relevant_potential
                and c.differentiation_potential and c.sufficient_window):
            errs.append(ValidationError(
                "asset_fit.i5_conditions_incomplete", "asset_fit.new_asset_recommendation",
                "all four I5 conditions SHOULD hold, or the recommendation is downgraded to a "
                "note (spec §10.3)",
                severity=WARNING,
            ))

    return errs


# --- §20 / §13 Config ---------------------------------------------

def validate_run_config(
    cfg: M.RunConfig, *, project_root: Path, require_knowledge_paths: bool = True
) -> List[ValidationError]:
    """Validate a ``RunConfig`` (spec §13, §20).

    ``require_knowledge_paths`` (default): also check that the knowledge / config
    files a full run needs actually exist. Signal Collection on its own does not
    read ``knowledge/`` or ``config/{ranking,dedup}.yaml``, so the ``collect``
    entry point passes ``False``.
    """
    errs: List[ValidationError] = []

    if not _RUN_ID_RE.match(cfg.run_id):
        errs.append(ValidationError(
            "config.run_id_pattern", "run_id",
            r"run_id must match ^[A-Za-z0-9_\-]+$ (spec §13)",
        ))

    if cfg.max_opportunities_presented < 1:
        errs.append(ValidationError(
            "config.max_presented_too_low", "max_opportunities_presented",
            "max_opportunities_presented must be >= 1 (spec §13)",
        ))

    if cfg.replay.enabled and _blank(cfg.replay.fixture_path):
        errs.append(ValidationError(
            "config.replay_fixture_path_missing", "replay.fixture_path",
            "replay.fixture_path is required when replay.enabled (spec §20.1)",
        ))

    # Source capture-file paths are not needed in replay mode — the collectors read
    # recorded fixtures instead (§22). TECHNICAL DEFAULT: skip these checks then.
    if not cfg.replay.enabled:
        if SourceType.INTERNAL_DATA in cfg.signal_sources and _blank(cfg.internal_data_path):
            errs.append(ValidationError(
                "config.internal_data_path_missing", "internal_data_path",
                "internal_data_path is required when 'internal_data' is a signal source "
                "(spec §20.1)",
            ))
        if (
            SourceType.TIKTOK_CREATIVE_CENTER in cfg.signal_sources
            and _blank(cfg.tiktok_capture_path)
        ):
            errs.append(ValidationError(
                "config.tiktok_capture_path_missing", "tiktok_capture_path",
                "tiktok_capture_path is required when 'tiktok_creative_center' is a signal "
                "source (spec §20.1, §6.5)",
            ))

    if require_knowledge_paths:
        for attr in _REQUIRED_EXISTING_PATHS:
            rel = getattr(cfg.paths, attr)
            if not (project_root / rel).exists():
                errs.append(ValidationError(
                    "config.path_missing", f"paths.{attr}",
                    f"required path {rel!r} does not exist under the project root "
                    f"(spec §13, §14)",
                ))

    return errs


# --- §13 knowledge-file structural checks ------------------------

def validate_guardrails(guardrails: Sequence[M.Guardrail]) -> List[ValidationError]:
    errs: List[ValidationError] = []
    from .enums import GUARDRAIL_COUNT

    if len(guardrails) != GUARDRAIL_COUNT:
        errs.append(ValidationError(
            "guardrails.count", "guardrails",
            f"expected exactly {GUARDRAIL_COUNT} guardrails (C4 / spec §13), got {len(guardrails)}",
        ))

    expected_ids = [f"G{i:02d}" for i in range(1, len(guardrails) + 1)]
    actual_ids = [g.guardrail_id for g in guardrails]
    if actual_ids != expected_ids:
        errs.append(ValidationError(
            "guardrails.id_sequence", "guardrails[].guardrail_id",
            f"guardrail ids must be a contiguous G01.. sequence; got {actual_ids}",
        ))

    for g in guardrails:
        if _blank(g.description):
            errs.append(ValidationError(
                "guardrails.description_empty", f"{g.guardrail_id}.description",
                "guardrail description is empty",
            ))
    return errs


def validate_canonical_clusters(cluster_ids: Sequence[str]) -> List[ValidationError]:
    errs: List[ValidationError] = []
    from .enums import CANONICAL_CLUSTER_COUNT

    if len(cluster_ids) != CANONICAL_CLUSTER_COUNT:
        errs.append(ValidationError(
            "taxonomy.count", "cluster-taxonomy.md",
            f"expected exactly {CANONICAL_CLUSTER_COUNT} canonical clusters (spec §7.2), "
            f"got {len(cluster_ids)}",
        ))
    if len(set(cluster_ids)) != len(cluster_ids):
        errs.append(ValidationError(
            "taxonomy.duplicate_id", "cluster-taxonomy.md", "canonical cluster ids must be unique",
        ))
    return errs


# --- §13 presented-set contract -------------------------------

def validate_presented_count(
    *, presented: int, cap: int, target: Optional[int] = None
) -> List[ValidationError]:
    errs: List[ValidationError] = []
    if presented > cap:
        errs.append(ValidationError(
            "report.presented_over_cap", "presented",
            f"presented set size {presented} exceeds max_opportunities_presented {cap} "
            f"(spec §13, I12)",
        ))
    if target is not None and presented < target:
        errs.append(ValidationError(
            "report.presented_below_target", "presented",
            f"presented set size {presented} is below the C10 target of {target} — "
            f"digest must flag this (spec §12.5, §14)",
            severity=WARNING,
        ))
    return errs
