"""Asset Matching — spec §10, §18 component 4, §19. No network."""

from __future__ import annotations

from tests.conftest import FIXTURES, PROJECT_ROOT, load_fixture

from market_intelligence.framing import FramedOpportunity, frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.matching import (
    MatchingResult,
    _candidates,
    _cluster_ctx,
    _coerce_candidate,
    match_assets,
)
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import (
    UNKNOWN,
    AssetRole,
    Confidence,
    Durability,
    EvidenceType,
    FitBasis,
    Language,
    Market,
    Platform,
    Urgency,
)
from market_intelligence.schema.models import (
    Audience,
    EvidenceItem,
    Hypotheses,
    PotentialCluster,
    RunConfig,
    RunPaths,
    Signal,
)

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


# --- canonical cluster id ↔ inventory name (LOW-1) -------------------

_MARKET = {Language.PT: Market.BRASIL, Language.ES: Market.MERCADOS_HISPANOHABLANTES}


def _opp(cluster_value, *, canonical=True, language=Language.PT, title="t", need="n"):
    lang = language
    return FramedOpportunity(
        opportunity_id="opp_test", schema_version="1.0.0", run_id="r",
        created_at="2026-08-28T00:00:00Z", title=title, need=need, audience=Audience("a"),
        market=_MARKET[lang], language=lang, platform=Platform.TIKTOK,
        consumption_context="c", durability=Durability.EMERGING, urgency=Urgency.MEDIUM,
        evidence=[EvidenceItem(type=EvidenceType.OBSERVED, statement="s",
                               confidence=Confidence.MEDIUM, signal_ids=["sig_x"])],
        signal_ids=["sig_x"],
        hypotheses=Hypotheses(potential_cluster=PotentialCluster(
            value=cluster_value, canonical=canonical,
            basis="existing" if canonical else "proposed_new",
        )),
    )


def test_cluster_ctx_resolves_canonical_names_to_ids_deterministically():
    cx = _cluster_ctx(_opp("sono"), _knowledge())
    assert cx.resolve("Abundância / Prosperidade") == "abundancia-prosperidade"
    assert cx.resolve("Limpeza Energética") == "limpeza-energetica"
    assert cx.resolve("Sonho Lúcido") == "sonho-lucido"
    assert cx.resolve("Frequência Divina / Espiritualidade") == "frequencia-divina-espiritualidade"
    # non-canonical / unclassified values do not resolve
    assert cx.resolve("NEEDS_INPUT") is None
    assert cx.resolve("UNKNOWN") is None
    assert cx.resolve("Sono Restaurador") is None       # a subcluster, not a canonical cluster
    assert cx.resolve("Um Tema Inventado") is None


def test_multiple_canonical_clusters_match_the_inventory_by_id_not_only_sono():
    kn = _knowledge()
    # (opportunity canonical cluster id, an inventory asset stored under the matching NAME,
    #  the opportunity's language chosen so LOCALE does NOT match — isolating the cluster path)
    cases = [
        ("abundancia-prosperidade", "pl_2vZzaPRyZrrWqpt8zZ5wDs", Language.ES),  # inv: pt/Brasil
        ("limpeza-energetica",      "pl_4oV5F1W2E6azZePnmqBanN", Language.PT),  # inv: es
        ("sonho-lucido",            "pl_0fzUPuhRHjqMyfOgNx0d4S", Language.PT),  # inv: es
        ("glandula-pineal-frequencias", "pl_2wQ3zDAXPdF9cLtR9OppyZ", Language.ES),  # inv: pt/Brasil
    ]
    for cluster_id, asset_id, lang in cases:
        cands = {c.asset_id: c for c in _candidates(_opp(cluster_id, language=lang), kn)}
        assert asset_id in cands, f"{cluster_id}: {asset_id} should be a candidate via cluster id"
        assert cands[asset_id].consolidated_basis is True, (
            f"{cluster_id}: {asset_id} should carry a consolidated (cluster) basis"
        )
        assert cands[asset_id].facts["canonical_cluster_id"] == cluster_id


def test_observed_fit_basis_survives_when_a_consolidated_cluster_classification_aligns():
    kn = _knowledge()
    cands = {c.asset_id: c for c in _candidates(
        _opp("abundancia-prosperidade", language=Language.ES), kn
    )}
    target = "pl_2vZzaPRyZrrWqpt8zZ5wDs"  # cluster "Abundância / Prosperidade"
    raw = {"asset_id": target, "asset_type": "playlist", "fit": "HIGH",
           "fit_basis": "OBSERVED", "fit_rationale": "cluster consolidado alinha",
           "role": "candidate"}
    ac = _coerce_candidate(raw, cands, kn.inventory)
    assert ac is not None
    # NOT downgraded — the consolidated cluster classification backs the OBSERVED claim
    assert ac.fit_basis is FitBasis.OBSERVED


def test_nonexistent_or_mismatched_cluster_cannot_produce_observed():
    kn = _knowledge()

    # (a) opportunity's canonical cluster (foco-estudo) matches NO inventory asset;
    #     an own page enters ONLY via the lexical hint, at a mismatched locale (ES opp
    #     vs pt/Brasil page) → no consolidated basis at all.
    cands = {c.asset_id: c for c in _candidates(
        _opp("foco-estudo", language=Language.ES,
             title="frequências de sono profundo", need="sono profundo"), kn
    )}
    page = cands["page_tiktok_mandalameditationss"]      # cluster "Sono", pt/Brasil
    assert page.consolidated_basis is False
    raw = {"asset_id": "page_tiktok_mandalameditationss", "asset_type": "page",
           "fit": "MEDIUM", "fit_basis": "OBSERVED", "fit_rationale": "x", "role": "candidate"}
    ac = _coerce_candidate(raw, cands, kn.inventory)
    assert ac.fit_basis is FitBasis.INFERRED             # OBSERVED downgraded — no real basis

    # (b) a non-canonical (proposed_new) cluster never yields a cluster match
    cx = _cluster_ctx(_opp("tema-proposto-novo", canonical=False), kn)
    assert cx.want_id is None
    assert cx.matches("Sono") is False
    assert cx.matches("Abundância / Prosperidade") is False


def test_non_hero_artist_needs_a_related_classification_for_an_observed_basis():
    kn = _knowledge()
    non_hero = next(
        a for a in kn.artists
        if a.get("hero_artist") is not True and a.get("name")
    )
    # opportunity cluster (foco-estudo) relates to no artist; the non-hero artist's
    # consolidated classification (if any) is unrelated → NO OBSERVED basis
    # (§10.2 step 2). A hero artist stays OBSERVED (§10.2a).
    opp = _opp("foco-estudo", language=Language.PT,
               title=non_hero["name"], need=non_hero["name"])
    cands = {c.asset_id: c for c in _candidates(opp, kn)}
    assert non_hero["artist_id"] in cands
    assert cands[non_hero["artist_id"]].consolidated_basis is False

    hero_id = next(a["artist_id"] for a in kn.artists if a.get("hero_artist") is True)
    assert cands[hero_id].consolidated_basis is True


def test_every_artist_is_an_asset_match_candidate_regardless_of_catalog_affinity():
    # §10.2a (DECIDED 2026-08-27): catalog affinity is NOT an eligibility filter.
    # An artist candidate MUST NOT be dropped for a cluster mismatch, even with no
    # lexical overlap. The fit judgement (OBSERVED/INFERRED, the fit rating) is where
    # a mismatch shows — never candidate eligibility.
    kn = _knowledge()
    # cluster relates to no artist (all are Sono / Anjos / Abundância / NEEDS_INPUT);
    # nonsense title/need share no tokens with any artist name.
    opp = _opp("foco-estudo", language=Language.PT,
               title="zzxq plughfrob widget", need="zzxq plughfrob widget")
    cand_ids = {c.asset_id for c in _candidates(opp, kn)}
    artist_ids = {a["artist_id"] for a in kn.artists}
    missing = artist_ids - cand_ids
    assert missing == set(), (
        f"{len(missing)} artist(s) dropped from the candidate set on a cluster/lexical "
        f"mismatch — §10.2a forbids this"
    )
    # a non-hero, cluster-mismatched artist is present but carries no OBSERVED basis
    non_hero_mismatch = next(
        a for a in kn.artists
        if a.get("hero_artist") is not True and a.get("primary_cluster") == "Sono"
    )
    by_id = {c.asset_id: c for c in _candidates(opp, kn)}
    assert by_id[non_hero_mismatch["artist_id"]].consolidated_basis is False
