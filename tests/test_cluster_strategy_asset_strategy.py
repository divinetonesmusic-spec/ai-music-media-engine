"""Cluster Strategy V1 — deterministic asset consolidation (contract §5).

NEVER invent an artist / playlist / page (I1). The consolidation only reframes
what the opportunity's AssetMatch already established, cross-checked against the
inventory. Hero artists are always eligible (§10.2a). reference_competitor pages
never become a recommended page.
"""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from cluster_strategy.asset_strategy import consolidate
from cluster_strategy.input_loader import load_input
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.models import RunPaths

_SIDECAR = PROJECT_ROOT / "reports" / "run_2026-08-31_01" / "opp_2026-08-31_1bca4af972.json"
_KB = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def _loaded():
    return load_input(_SIDECAR, project_root=PROJECT_ROOT)


def test_consolidation_carries_the_opportunitys_best_assets_verbatim():
    opp = _loaded().opportunity
    cas = consolidate(opp, _KB)
    assert cas.playlist_strategy.primary_playlist_id == opp.asset_fit.best_playlist
    assert cas.page_strategy.primary_page_id == opp.asset_fit.best_page  # "UNKNOWN" here
    assert cas.artist_strategy.best_artist_id == opp.asset_fit.best_artist


def test_every_asset_id_in_the_output_exists_in_the_inventory_or_is_a_sentinel():
    cas = consolidate(_loaded().opportunity, _KB)
    inv = _KB.inventory
    sentinels = {"UNKNOWN", "NEW_ASSET"}

    def ok_playlist(pid):
        return pid in sentinels or pid in inv.playlist_ids

    def ok_page(pid):
        return pid in sentinels or pid in inv.own_page_ids

    def ok_artist(aid):
        return aid in sentinels or aid in inv.artist_ids

    assert ok_playlist(cas.playlist_strategy.primary_playlist_id)
    assert all(ok_playlist(p) for p in cas.playlist_strategy.secondary_playlist_ids)
    assert ok_page(cas.page_strategy.primary_page_id)
    assert ok_artist(cas.artist_strategy.best_artist_id)
    assert all(ok_artist(a) for a in cas.artist_strategy.anchor_hero_artist_ids)
    assert all(ok_artist(a) for a in cas.artist_strategy.catalog_affinity_artist_ids)
    assert all(ok_artist(a) for a in cas.artist_strategy.candidate_artist_ids)
    # never a reference_competitor page
    assert not (set(_KB.inventory.reference_page_ids) & {cas.page_strategy.primary_page_id})


def test_the_new_page_recommendation_is_carried_and_the_playlist_one_is_not():
    opp = _loaded().opportunity  # AssetMatch.new_asset_recommendation.asset_type == "page"
    cas = consolidate(opp, _KB)
    assert cas.page_strategy.new_page_recommendation is not None
    assert cas.page_strategy.new_page_recommendation.asset_type.value == "page"
    assert cas.playlist_strategy.new_playlist_recommendation is None
    # all four I5 conditions are preserved on the carried recommendation
    c = cas.page_strategy.new_page_recommendation.i5_conditions_met
    assert (c.no_adequate_fit and c.relevant_potential
            and c.differentiation_potential and c.sufficient_window)


def test_hero_artist_anchor_and_the_affinity_note():
    cas = consolidate(_loaded().opportunity, _KB)
    hero_ids = {a["artist_id"] for a in _KB.artists if a.get("hero_artist") is True}
    # the opportunity's best_artist (Sonia Amor Divino) is a hero
    assert cas.artist_strategy.best_artist_id in hero_ids
    assert cas.artist_strategy.best_artist_id in cas.artist_strategy.anchor_hero_artist_ids
    assert "not a placement restriction" in cas.artist_strategy.affinity_note


def test_market_language_fit_is_rating_plus_separate_confidence_and_no_score():
    cas = consolidate(_loaded().opportunity, _KB)
    mlf = cas.market_language_fit
    assert mlf.rating.value in ("LOW", "MEDIUM", "HIGH", "VERY_HIGH")
    assert mlf.confidence.value in ("LOW", "MEDIUM", "HIGH")
    # es opportunity + es playlist + es-market hero -> at least MEDIUM
    assert mlf.rating.value in ("MEDIUM", "HIGH", "VERY_HIGH")
    # confidence capped while musical DNA is NEEDS_INPUT
    assert mlf.confidence.value in ("LOW", "MEDIUM")
    assert "/100" not in mlf.justification and "out of 100" not in mlf.justification


def test_asset_gaps_carries_the_unmatched_reason():
    opp = _loaded().opportunity
    cas = consolidate(opp, _KB)
    assert opp.asset_fit.unmatched_reason
    assert any(opp.asset_fit.unmatched_reason in g for g in cas.asset_gaps)
