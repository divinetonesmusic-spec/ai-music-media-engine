"""Deterministic asset consolidation (contract §5).

Reframes the opportunity's ``AssetMatch`` (spec §10) at cluster level. It makes
**no new asset judgement** — every id it emits already appears in the
opportunity's AssetMatch or a sentinel — and it can never introduce an asset the
inventory does not contain (I1, spec §10.4, §19). Hero artists are always
eligible regardless of catalog affinity (spec §10.2a).
"""

from __future__ import annotations

from typing import Dict, List

from market_intelligence.knowledge_loader import KnowledgeBundle
from market_intelligence.schema.enums import (
    AssetRole,
    Confidence,
    FitLevel,
    NewAssetType,
    Rating,
)
from market_intelligence.schema.models import AssetMatch, Opportunity

from .schema.enums import NEW_ASSET, UNKNOWN
from .schema.models import (
    ArtistStrategy,
    ClusterAssetStrategy,
    MarketLanguageFit,
    PageStrategy,
    PlaylistStrategy,
)

_GOOD_FIT = {FitLevel.MEDIUM, FitLevel.HIGH}


def _candidate_basis(am: AssetMatch, kind: str, asset_id: str) -> str:
    cands = {
        "playlist": am.matching_playlists,
        "page": am.matching_pages,
        "artist": am.matching_artists,
    }[kind]
    for c in cands:
        if c.asset_id == asset_id:
            return c.fit_basis.value
    return UNKNOWN


def _inv_by_id(rows: List[dict], key: str) -> Dict[str, dict]:
    return {r[key]: r for r in rows if isinstance(r, dict) and r.get(key)}


def _market_language_fit(
    opp: Opportunity, am: AssetMatch, kb: KnowledgeBundle
) -> MarketLanguageFit:
    """Deterministic: compare the opportunity's market/language against the
    consolidated market/language on the chosen assets. Confidence is capped at
    MEDIUM while musical-DNA detail and the classification backlog are
    NEEDS_INPUT (contract §11)."""
    opp_market, opp_lang = opp.market.value, opp.language.value
    playlists = _inv_by_id(kb.playlists, "playlist_id")
    artists = _inv_by_id(kb.artists, "artist_id")

    def matches(row: dict) -> bool:
        return row.get("market") == opp_market and row.get("language") == opp_lang

    pl_row = playlists.get(am.best_playlist)
    ar_row = artists.get(am.best_artist)
    pl_ok = pl_row is not None and matches(pl_row)
    ar_ok = ar_row is not None and matches(ar_row)

    if pl_ok and (ar_ok or ar_row is None):
        rating = Rating.HIGH
        why = (
            f"the chosen playlist ({am.best_playlist}) is classified "
            f"{opp_lang}/{opp_market} in this cluster"
            + (f"; the chosen artist ({am.best_artist}) matches the market" if ar_ok else "")
        )
    elif pl_ok or ar_ok:
        rating = Rating.MEDIUM
        why = "some chosen assets match the opportunity's market/language, others do not"
    else:
        rating = Rating.LOW
        why = (
            "no chosen asset is classified for the opportunity's "
            f"{opp_lang}/{opp_market} in this cluster"
        )
    return MarketLanguageFit(
        rating=rating,
        confidence=Confidence.MEDIUM,  # cap — musical DNA / classification backlog NEEDS_INPUT
        justification=(
            why + ". Confidence capped at MEDIUM while musical-DNA detail "
            "(business-dna §9) and the strategic-classification backlog are NEEDS_INPUT."
        ),
    )


def consolidate(opp: Opportunity, kb: KnowledgeBundle) -> ClusterAssetStrategy:
    am = opp.asset_fit
    hero_ids = {a["artist_id"] for a in kb.artists
                if isinstance(a, dict) and a.get("hero_artist") is True and a.get("artist_id")}

    # --- playlist ---
    primary_pl = am.best_playlist
    secondary_pl = [
        c.asset_id for c in am.matching_playlists
        if c.asset_id != primary_pl and c.fit in _GOOD_FIT
    ]
    new_pl = (
        am.new_asset_recommendation
        if am.new_asset_recommendation
        and am.new_asset_recommendation.asset_type is NewAssetType.PLAYLIST
        else None
    )
    playlist = PlaylistStrategy(
        primary_playlist_id=primary_pl,
        playlist_fit_basis=_candidate_basis(am, "playlist", primary_pl),
        reuse_rationale=(
            f"Reuse the existing playlist {primary_pl} (I5 default — asset reuse)."
            if primary_pl not in (UNKNOWN, NEW_ASSET)
            else "No existing playlist adequately fits; see the recommendation and asset gaps."
        ),
        secondary_playlist_ids=secondary_pl,
        new_playlist_recommendation=new_pl,
    )

    # --- page (design is Page Blueprint's — this only carries the recommendation) ---
    new_pg = (
        am.new_asset_recommendation
        if am.new_asset_recommendation
        and am.new_asset_recommendation.asset_type is NewAssetType.PAGE
        else None
    )
    page = PageStrategy(
        primary_page_id=am.best_page,
        page_fit_basis=_candidate_basis(am, "page", am.best_page),
        note=(
            "A new page is recommended (I5 conditions met upstream). Its name, bio, "
            "visual identity, tone of voice and cadence are Page Blueprint's (stage 4); "
            "Cluster Strategy only records that a new page is warranted and which "
            "playlist/artist should anchor it."
            if new_pg is not None
            else "An existing own page carries this cluster; its design is unchanged here."
            if am.best_page not in (UNKNOWN, NEW_ASSET)
            else "No own page fits and no new page is recommended; see asset gaps."
        ),
        new_page_recommendation=new_pg,
    )

    # --- artists (§10.2a — hero roster always eligible; affinity is context) ---
    cand_ids = [c.asset_id for c in am.matching_artists]
    anchor_heroes = [c.asset_id for c in am.matching_artists
                     if c.role is AssetRole.HERO and c.fit in _GOOD_FIT]
    if am.best_artist in hero_ids and am.best_artist not in anchor_heroes:
        anchor_heroes.insert(0, am.best_artist)
    affinity_artists = [
        c.asset_id for c in am.matching_artists
        if c.fit_basis.value == "OBSERVED" and c.role is not AssetRole.HERO
    ]
    artist = ArtistStrategy(
        best_artist_id=am.best_artist,
        anchor_hero_artist_ids=anchor_heroes,
        catalog_affinity_artist_ids=affinity_artists,
        candidate_artist_ids=cand_ids,
    )

    # --- catalog affinity (coarse in V1 — §10.3) ---
    catalog_summary = (
        f"{len(am.matching_artists)} candidate artist(s) and "
        f"{len(am.matching_playlists)} candidate playlist(s) relate to this cluster; "
        "release-level catalog matching is coarse in V1 (spec §10.3)."
    )

    # --- asset gaps ---
    gaps: List[str] = []
    if am.unmatched_reason:
        gaps.append(am.unmatched_reason)
    if am.best_page in (UNKNOWN, NEW_ASSET):
        gaps.append(
            f"No own page is classified for {opp.language.value}/{opp.market.value} "
            "in this cluster."
        )

    return ClusterAssetStrategy(
        playlist_strategy=playlist,
        page_strategy=page,
        artist_strategy=artist,
        catalog_affinity_summary=catalog_summary,
        market_language_fit=_market_language_fit(opp, am, kb),
        asset_gaps=gaps,
    )
