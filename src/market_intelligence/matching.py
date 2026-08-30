"""Asset Matching — spec §10, §18 component 4, §19.

Connects each framed opportunity to **existing** inventory assets. No asset is
ever invented (I1): a ``new_asset_recommendation`` is a recommendation only.

Split of work (§19):

* deterministic — candidate generation from the real inventory (§10.2 step 1;
  the 10 hero artists are always artist candidates, §10.2a); **asset-existence
  verification**; ``fit_basis`` gating (OBSERVED only when a consolidated
  inventory classification actually backs it); blocking any write-back.
* Claude — the fit judgement + rationale per candidate, the ``best_*`` selection,
  and the four I5 conditions for a new asset.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from .framing import FramedOpportunity
from .knowledge_loader import KnowledgeBundle
from .llm_stage import (
    ResponseRejected,
    StageClient,
    StageError,
    call_stage,
    enum_str,
    obj_schema,
    select_stage_client,
    stage_key,
)
from .schema.enums import (
    NEW_ASSET,
    UNKNOWN,
    AssetRole,
    AssetType,
    FitBasis,
    FitLevel,
    NewAssetType,
)
from .schema.models import (
    AssetCandidate,
    AssetMatch,
    I5Conditions,
    NewAssetRecommendation,
    RunConfig,
)
from .schema.validate import InventoryIndex, ValidationError, validate_asset_match

SCHEMA_VERSION = "1.0.0"
STAGE = "matching"

_HERO = "hero"
_REFERENCE = "reference"
_CANDIDATE = "candidate"

_WORD_RE = re.compile(r"[0-9a-zà-ú]+", re.IGNORECASE)
_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "para", "com", "em",
    "the", "of", "for", "and", "to", "in", "on", "un", "una", "el", "la", "los", "las",
    "y", "con", "por", "musica", "música", "music", "hz",
}


@dataclass
class AssetMatchWarning:
    opportunity_id: str
    error: ValidationError


@dataclass
class MatchingResult:
    matches: Dict[str, AssetMatch]
    warnings: List[AssetMatchWarning] = field(default_factory=list)
    llm_mode: str = "recorded"


# --- inventory helpers -------------------------------------------

def _tokens(text: str) -> set:
    found = (t.lower() for t in _WORD_RE.findall(text or ""))
    return {t for t in found if len(t) > 2 and t not in _STOPWORDS}


def _classified(value) -> bool:
    return isinstance(value, str) and value not in ("", "UNKNOWN", "NEEDS_INPUT")


def _cluster_terms(opp: FramedOpportunity) -> set:
    terms = set()
    if opp.hypotheses and opp.hypotheses.potential_cluster:
        terms.add(opp.hypotheses.potential_cluster.value)
    return terms


def _hero_artist_ids(knowledge: KnowledgeBundle) -> List[str]:
    return [a["artist_id"] for a in knowledge.artists if a.get("hero_artist") is True]


@dataclass
class _Cand:
    asset_type: str
    asset_id: str
    name: str
    consolidated_basis: bool   # a real inventory classification backs a fit judgement
    role: str
    facts: dict


def _playlist_candidates(opp: FramedOpportunity, knowledge: KnowledgeBundle) -> List[_Cand]:
    want_cluster = _cluster_terms(opp)
    opp_tokens = _tokens(opp.title) | _tokens(opp.need)
    out: List[_Cand] = []
    for p in knowledge.playlists:
        cluster = p.get("cluster")
        market = p.get("market")
        language = p.get("language")
        cluster_match = _classified(cluster) and cluster.strip().lower() in {
            c.strip().lower() for c in want_cluster
        }
        locale_match = (
            _classified(market) and market == opp.market.value
            and _classified(language) and language == opp.language.value
        )
        lexical = bool(opp_tokens & _tokens(p.get("name", "")))
        if not (cluster_match or locale_match or lexical):
            continue
        out.append(_Cand(
            asset_type="playlist",
            asset_id=p["playlist_id"],
            name=p.get("name", ""),
            consolidated_basis=cluster_match or locale_match,
            role=_CANDIDATE,
            facts={"cluster": cluster, "market": market, "language": language,
                   "purpose": p.get("purpose")},
        ))
    return out


def _page_candidates(opp: FramedOpportunity, knowledge: KnowledgeBundle) -> List[_Cand]:
    want_cluster = {c.strip().lower() for c in _cluster_terms(opp)}
    opp_tokens = _tokens(opp.title) | _tokens(opp.need)
    out: List[_Cand] = []
    for p in knowledge.pages:
        own = p.get("ownership") == "own"
        cluster = p.get("cluster")
        market = p.get("market")
        language = p.get("language")
        cluster_match = own and _classified(cluster) and cluster.strip().lower() in want_cluster
        locale_match = (
            own and _classified(market) and market == opp.market.value
            and _classified(language) and language == opp.language.value
        )
        lexical = bool(opp_tokens & _tokens(p.get("name", "")))
        if not (own and (cluster_match or locale_match or lexical)):
            continue
        out.append(_Cand(
            asset_type="page",
            asset_id=p["page_id"],
            name=p.get("name", ""),
            consolidated_basis=cluster_match or locale_match,
            role=_CANDIDATE,
            facts={"cluster": cluster, "market": market, "language": language,
                   "purpose": p.get("purpose")},
        ))
    return out


def _artist_candidates(opp: FramedOpportunity, knowledge: KnowledgeBundle) -> List[_Cand]:
    hero_ids = set(_hero_artist_ids(knowledge))
    want_cluster = {c.strip().lower() for c in _cluster_terms(opp)}
    opp_tokens = _tokens(opp.title) | _tokens(opp.need)
    out: List[_Cand] = []
    for a in knowledge.artists:
        aid = a["artist_id"]
        is_hero = aid in hero_ids
        primary = a.get("primary_cluster")
        secondary = a.get("secondary_clusters")
        sec_terms = {s.strip().lower() for s in secondary} if isinstance(secondary, list) else set()
        cluster_related = (
            (_classified(primary) and primary.strip().lower() in want_cluster)
            or bool(sec_terms & want_cluster)
        )
        lexical = bool(opp_tokens & _tokens(a.get("name", "")))
        # §10.2a — hero artists are ALWAYS candidates; others need a relation/lexical hint.
        if not (is_hero or cluster_related or lexical):
            continue
        out.append(_Cand(
            asset_type="artist",
            asset_id=aid,
            name=a.get("name", ""),
            # a consolidated basis exists when the artist is hero (strategic role) or
            # has a consolidated primary/secondary cluster (§10.2 step 2).
            consolidated_basis=is_hero or _classified(primary) or bool(sec_terms),
            role=_HERO if is_hero else _CANDIDATE,
            facts={"primary_cluster": primary, "secondary_clusters": secondary,
                   "hero_artist": is_hero},
        ))
    return out


def _candidates(opp: FramedOpportunity, knowledge: KnowledgeBundle) -> List[_Cand]:
    cands = (
        _playlist_candidates(opp, knowledge)
        + _page_candidates(opp, knowledge)
        + _artist_candidates(opp, knowledge)
    )
    cands.sort(key=lambda c: (c.asset_type, c.asset_id))
    return cands


# --- response schema + prompt ----------------------------------

def _response_schema(candidate_ids: Sequence[str]) -> dict:
    return obj_schema(
        {
            "candidates": {
                "type": "array",
                "items": obj_schema(
                    {
                        "asset_id": enum_str(list(candidate_ids)) if candidate_ids
                        else {"type": "string"},
                        "asset_type": enum_str(["playlist", "page", "artist", "catalog"]),
                        "fit": enum_str(["NONE", "LOW", "MEDIUM", "HIGH"]),
                        "fit_basis": enum_str(["OBSERVED", "INFERRED", "UNKNOWN"]),
                        "fit_rationale": {"type": "string"},
                        "role": enum_str(["candidate", "reference", "hero"]),
                    },
                    ["asset_id", "asset_type", "fit", "fit_basis", "fit_rationale"],
                ),
            },
            "best_playlist": {"type": "string"},
            "best_page": {"type": "string"},
            "best_artist": {"type": "string"},
            "unmatched_reason": {"type": "string"},
            "new_asset_recommendation": obj_schema(
                {
                    "asset_type": enum_str(["page", "playlist", "other"]),
                    "rationale": {"type": "string"},
                    "i5_conditions_met": obj_schema(
                        {
                            "no_adequate_fit": {"type": "boolean"},
                            "relevant_potential": {"type": "boolean"},
                            "differentiation_potential": {"type": "boolean"},
                            "sufficient_window": {"type": "boolean"},
                        },
                        ["no_adequate_fit", "relevant_potential",
                         "differentiation_potential", "sufficient_window"],
                    ),
                },
                ["asset_type", "rationale", "i5_conditions_met"],
            ),
        },
        ["candidates", "best_playlist", "best_page", "best_artist"],
    )


def _prompt(opp: FramedOpportunity, cands: Sequence[_Cand]) -> str:
    pc = opp.hypotheses.potential_cluster.value if (
        opp.hypotheses and opp.hypotheses.potential_cluster
    ) else None
    payload = {
        "opportunity": {
            "title": opp.title,
            "need": opp.need,
            "audience": opp.audience.description,
            "market": opp.market.value,
            "language": opp.language.value,
            "platform": opp.platform.value,
            "consumption_context": opp.consumption_context,
            "potential_cluster": pc,
        },
        "candidates": [
            {"asset_id": c.asset_id, "asset_type": c.asset_type, "name": c.name,
             "role_hint": c.role, "inventory_facts": c.facts,
             "has_consolidated_classification": c.consolidated_basis}
            for c in cands
        ],
    }
    return (
        "You are the Asset Matching step. Judge how well each EXISTING inventory asset "
        "below fits the opportunity, and pick the best playlist / page / artist.\n\n"
        "Rules:\n"
        "- Only judge assets in the candidates list. NEVER invent an asset id.\n"
        "- fit_basis: OBSERVED only when has_consolidated_classification is true AND the "
        "classification actually aligns; INFERRED when you rely on the name text, a "
        "NEEDS_INPUT field or a hypothesis; UNKNOWN when there is no basis at all.\n"
        "- An artist's catalog affinity is NOT an eligibility filter. Any artist can serve "
        "any opportunity. hero artists are strong candidates regardless of catalog affinity "
        "(role: hero).\n"
        "- reference_competitor pages are context only (role: reference) and can NEVER be a "
        "best_page.\n"
        "- best_playlist / best_artist: a candidate id or 'UNKNOWN'. best_page: a candidate "
        "id, 'UNKNOWN', or 'NEW_ASSET'. Set unmatched_reason whenever a best_* is UNKNOWN.\n"
        "- Recommend a new asset ONLY if all four I5 conditions hold: no adequate existing "
        "fit; relevant potential; plausible differentiation; sufficient window. It is a "
        "recommendation only — never executed.\n\n"
        f"INPUT:\n{json.dumps(payload, ensure_ascii=False, indent=1)}\n\n"
        "Return the JSON object matching the schema exactly."
    )


# --- deterministic assembly ----------------------------------

def _clean(v) -> str:
    return (v or "").strip() if isinstance(v, str) else ""


def _coerce_candidate(
    raw: dict, by_id: Dict[str, _Cand], inv: InventoryIndex
) -> Optional[AssetCandidate]:
    asset_id = _clean(raw.get("asset_id"))
    cand = by_id.get(asset_id)
    if cand is None:
        return None  # Claude may only judge assets we generated (existence-checked)
    try:
        fit = raw.get("fit", "NONE")
        fit_level = FitLevel(fit)
        basis = FitBasis(raw.get("fit_basis", "UNKNOWN"))
    except ValueError:
        return None

    # fit_basis gating (§10.2 step 2): OBSERVED requires a real consolidated classification.
    if basis is FitBasis.OBSERVED and not cand.consolidated_basis:
        basis = FitBasis.INFERRED
    # INFERRED cannot carry a HIGH fit (spec §10.3 — LOW/MEDIUM confidence only).
    if basis is FitBasis.INFERRED and fit_level is FitLevel.HIGH:
        fit_level = FitLevel.MEDIUM

    role_raw = _clean(raw.get("role")) or cand.role
    if cand.asset_id in inv.reference_page_ids:
        role_raw = _REFERENCE
    elif cand.role == _HERO:
        role_raw = _HERO
    try:
        role = AssetRole(role_raw)
    except ValueError:
        role = AssetRole.CANDIDATE

    return AssetCandidate(
        asset_type=AssetType(cand.asset_type),
        asset_id=cand.asset_id,
        name=cand.name,
        fit=fit_level,
        fit_basis=basis,
        fit_rationale=_clean(raw.get("fit_rationale")) or "(no rationale provided)",
        role=role,
    )


def _select(value: str, valid_ids: set, *, allow_new: bool = False) -> str:
    v = _clean(value)
    if v in valid_ids:
        return v
    if allow_new and v == NEW_ASSET:
        return NEW_ASSET
    return UNKNOWN


def _new_asset_reco(raw) -> Optional[NewAssetRecommendation]:
    if not isinstance(raw, dict):
        return None
    conds = raw.get("i5_conditions_met") or {}
    try:
        return NewAssetRecommendation(
            asset_type=NewAssetType(raw.get("asset_type", "other")),
            rationale=_clean(raw.get("rationale")) or "(no rationale provided)",
            i5_conditions_met=I5Conditions(
                no_adequate_fit=bool(conds.get("no_adequate_fit")),
                relevant_potential=bool(conds.get("relevant_potential")),
                differentiation_potential=bool(conds.get("differentiation_potential")),
                sufficient_window=bool(conds.get("sufficient_window")),
            ),
        )
    except ValueError:
        return None


def _build_match(
    raw: dict, cands: Sequence[_Cand], knowledge: KnowledgeBundle
) -> AssetMatch:
    inv = knowledge.inventory
    by_id = {c.asset_id: c for c in cands}

    coerced: List[AssetCandidate] = []
    for item in raw.get("candidates") or []:
        if isinstance(item, dict):
            ac = _coerce_candidate(item, by_id, inv)
            if ac is not None:
                coerced.append(ac)

    playlists = [c for c in coerced if c.asset_type.value == "playlist"]
    pages = [c for c in coerced if c.asset_type.value == "page"]
    artists = [c for c in coerced if c.asset_type.value == "artist"]

    # best_* must be one of the assets we generated as candidates (existence-checked,
    # §10.4) — Claude cannot reach outside the candidate set — or a sentinel.
    cand_ids = {c.asset_type: {x.asset_id for x in cands if x.asset_type == c.asset_type}
                for c in cands}
    best_playlist = _select(raw.get("best_playlist", UNKNOWN), cand_ids.get("playlist", set()))
    best_artist = _select(raw.get("best_artist", UNKNOWN), cand_ids.get("artist", set()))
    best_page = _select(
        raw.get("best_page", UNKNOWN),
        cand_ids.get("page", set()) & inv.own_page_ids,
        allow_new=True,
    )

    reco = None
    if best_page == NEW_ASSET:
        reco = _new_asset_reco(raw.get("new_asset_recommendation"))
        if reco is None or not all([
            reco.i5_conditions_met.no_adequate_fit,
            reco.i5_conditions_met.relevant_potential,
            reco.i5_conditions_met.differentiation_potential,
            reco.i5_conditions_met.sufficient_window,
        ]):
            best_page = UNKNOWN
            reco = None
    else:
        maybe = _new_asset_reco(raw.get("new_asset_recommendation"))
        if maybe and all([
            maybe.i5_conditions_met.no_adequate_fit,
            maybe.i5_conditions_met.relevant_potential,
            maybe.i5_conditions_met.differentiation_potential,
            maybe.i5_conditions_met.sufficient_window,
        ]):
            reco = maybe  # kept as a note; best_page stays as selected

    unmatched = _clean(raw.get("unmatched_reason")) or None
    if UNKNOWN in (best_playlist, best_page, best_artist) and not unmatched:
        unmatched = "No inventory asset had an adequate, consolidated fit for this opportunity."

    return AssetMatch(
        schema_version=SCHEMA_VERSION,
        matching_playlists=playlists,
        matching_pages=pages,
        matching_artists=artists,
        best_playlist=best_playlist,
        best_page=best_page,
        best_artist=best_artist,
        matching_catalog=None,  # TECHNICAL DEFAULT — catalog matching is coarse in V1 (§10.3)
        new_asset_recommendation=reco,
        unmatched_reason=unmatched,
    )


# --- entry point ----------------------------------------------

def match_assets(
    opportunities: Sequence[FramedOpportunity],
    *,
    knowledge: KnowledgeBundle,
    config: RunConfig,
    project_root: Union[str, Path],
    client: Optional[StageClient] = None,
) -> MatchingResult:
    active, mode = select_stage_client(config, project_root, client=client)
    matches: Dict[str, AssetMatch] = {}
    warnings: List[AssetMatchWarning] = []

    for opp in opportunities:
        cands = _candidates(opp, knowledge)
        try:
            raw = call_stage(
                active,
                stage=STAGE,
                key=stage_key(STAGE, opp.opportunity_id),
                prompt=_prompt(opp, cands),
                schema=_response_schema([c.asset_id for c in cands]),
                model=config.model,
                validate=lambda r: r,
            )
            match = _build_match(raw if isinstance(raw, dict) else {}, cands, knowledge)
        except (StageError, ResponseRejected) as e:
            # Degrade this opportunity to "no adequate match" rather than failing the
            # run — asset fit is UNKNOWN and the reason is recorded (§14).
            match = _unmatched(f"asset matching could not run for this opportunity: {e}")
        for err in validate_asset_match(match, inventory=knowledge.inventory):
            warnings.append(AssetMatchWarning(opp.opportunity_id, err))
        matches[opp.opportunity_id] = match

    return MatchingResult(matches=matches, warnings=warnings, llm_mode=mode)


def _unmatched(reason: str) -> AssetMatch:
    return AssetMatch(
        schema_version=SCHEMA_VERSION,
        matching_playlists=[], matching_pages=[], matching_artists=[],
        best_playlist=UNKNOWN, best_page=UNKNOWN, best_artist=UNKNOWN,
        matching_catalog=None, new_asset_recommendation=None, unmatched_reason=reason,
    )
