"""Asset Matching — spec §10, §18 component 4, §19. No network."""

from __future__ import annotations

from tests.conftest import FIXTURES, PROJECT_ROOT, load_fixture

from market_intelligence.framing import frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.matching import MatchingResult, match_assets
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import UNKNOWN, AssetRole, FitBasis
from market_intelligence.schema.models import RunConfig, RunPaths, Signal

_FIXTURE_ROOT = FIXTURES / "pipeline"
_OPP_ID = "opp_2026-08-28_e1a48ddf1c"


def _knowledge():
    return load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_pipe",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(_FIXTURE_ROOT)},
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _framed():
    signals = [decode(Signal, d) for d in load_fixture("pipeline/signals.json")]
    return frame_signals(
        signals, knowledge=_knowledge(), config=_cfg(), project_root=PROJECT_ROOT
    ).opportunities


def _match(**over) -> MatchingResult:
    return match_assets(
        _framed(), knowledge=_knowledge(), config=_cfg(**over), project_root=PROJECT_ROOT
    )


def test_produces_an_asset_match_per_opportunity():
    result = _match()
    assert isinstance(result, MatchingResult)
    assert set(result.matches) == {_OPP_ID}


def test_best_assets_are_real_inventory_ids():
    am = _match().matches[_OPP_ID]
    kn = _knowledge()
    assert am.best_playlist in kn.inventory.playlist_ids
    assert am.best_page in kn.inventory.own_page_ids
    assert am.best_artist in kn.inventory.artist_ids
    assert am.best_playlist == "pl_4jmuWvaWI6BvsjhxmJBUao"


def test_hero_artist_is_a_candidate_and_carries_the_hero_role():
    am = _match().matches[_OPP_ID]
    heroes = [c for c in am.matching_artists if c.role is AssetRole.HERO]
    assert any(c.asset_id == "art_1rGWl45kQm6h9PQEOOWGfZ" for c in heroes)


def test_observed_fit_basis_requires_a_consolidated_classification():
    # page_tiktok_frequenciasdivinas: own page but cluster != Sono → INFERRED, not OBSERVED
    am = _match().matches[_OPP_ID]
    fd = next(c for c in am.matching_pages if c.asset_id == "page_tiktok_frequenciasdivinas")
    assert fd.fit_basis is FitBasis.INFERRED


def test_model_cannot_introduce_an_asset_outside_the_candidate_set(tmp_path):
    fx = tmp_path / "pipeline"
    (fx / "llm" / "matching").mkdir(parents=True)
    (fx / "signals.json").write_text(
        (FIXTURES / "pipeline" / "signals.json").read_text(), encoding="utf-8"
    )
    (fx / "llm" / "framing").mkdir(parents=True)
    (fx / "llm" / "framing" / "framing__de1e16a6b378.json").write_text(
        (FIXTURES / "pipeline" / "llm" / "framing" / "framing__de1e16a6b378.json").read_text(),
        encoding="utf-8",
    )
    import json

    resp = {
        "candidates": [
            {"asset_id": "pl_DOES_NOT_EXIST", "asset_type": "playlist", "fit": "HIGH",
             "fit_basis": "OBSERVED", "fit_rationale": "invented", "role": "candidate"},
        ],
        "best_playlist": "pl_DOES_NOT_EXIST",
        "best_page": "UNKNOWN",
        "best_artist": "UNKNOWN",
    }
    (fx / "llm" / "matching" / f"matching__{_OPP_ID}.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    am = match_assets(
        _framed(), knowledge=_knowledge(), config=cfg, project_root=PROJECT_ROOT
    ).matches[_OPP_ID]
    assert all(c.asset_id != "pl_DOES_NOT_EXIST" for c in am.matching_playlists)
    assert am.best_playlist == UNKNOWN
    assert am.unmatched_reason


def test_new_asset_recommendation_requires_all_four_i5_conditions(tmp_path):
    fx = tmp_path / "pipeline"
    (fx / "llm" / "matching").mkdir(parents=True)
    (fx / "signals.json").write_text(
        (FIXTURES / "pipeline" / "signals.json").read_text(), encoding="utf-8"
    )
    (fx / "llm" / "framing").mkdir(parents=True)
    (fx / "llm" / "framing" / "framing__de1e16a6b378.json").write_text(
        (FIXTURES / "pipeline" / "llm" / "framing" / "framing__de1e16a6b378.json").read_text(),
        encoding="utf-8",
    )
    import json

    resp = {
        "candidates": [],
        "best_playlist": "UNKNOWN",
        "best_page": "NEW_ASSET",
        "best_artist": "UNKNOWN",
        "unmatched_reason": "nothing fits",
        "new_asset_recommendation": {
            "asset_type": "page",
            "rationale": "gap",
            "i5_conditions_met": {
                "no_adequate_fit": True, "relevant_potential": True,
                "differentiation_potential": False, "sufficient_window": True
            }
        }
    }
    (fx / "llm" / "matching" / f"matching__{_OPP_ID}.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    am = match_assets(
        _framed(), knowledge=_knowledge(), config=cfg, project_root=PROJECT_ROOT
    ).matches[_OPP_ID]
    # one I5 condition is False → the new-asset recommendation is downgraded, best_page → UNKNOWN
    assert am.best_page == UNKNOWN
    assert am.new_asset_recommendation is None


def test_matching_never_writes_to_the_inventory(tmp_path):
    before = {p: (PROJECT_ROOT / "knowledge" / "inventories" / f"{p}.yaml").read_bytes()
              for p in ("artists", "playlists", "pages", "catalog")}
    _match()
    after = {p: (PROJECT_ROOT / "knowledge" / "inventories" / f"{p}.yaml").read_bytes()
             for p in ("artists", "playlists", "pages", "catalog")}
    assert before == after
