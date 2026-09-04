"""Page Blueprint V1 — deterministic validators (contract §6, §B).

Rejects: any 0-100 score in any prose (C6); a page-content-strategy field name
(scope leakage, §B); overall_confidence above the Cluster Strategy's own
ceiling; overall_confidence HIGH while Musical DNA (§9) is NEEDS_INPUT
(D-PB-4); an invented asset id (I1); a reference/competitor page used as the
designed page; tampered fixed disclaimer text; too many content pillars.
"""

from __future__ import annotations

import copy

import pytest
from tests.conftest import PROJECT_ROOT

from cluster_strategy.schema.models import PageStrategy
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.enums import Confidence, Language, Market
from market_intelligence.schema.models import Provenance, RunPaths
from market_intelligence.schema.validate import blocking
from page_blueprint.schema import validate as V
from page_blueprint.schema.enums import SCHEMA_VERSION, PageBlueprintTargetNextStage
from page_blueprint.schema.models import (
    ClusterStrategySnapshot,
    PageAssetLink,
    PageBlueprint,
    PageBlueprintEvaluation,
    PageBlueprintProvenance,
    PageBlueprintRecommendation,
    PageContentFraming,
    PageIdentity,
    VisualIdentity,
)

_KB = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)
_PLAYLIST_ID = "pl_4oV5F1W2E6azZePnmqBanN"
_ARTIST_ID = "art_7bnKOg3GDWAbLFtNhyn8Gw"


def _minimal_page_blueprint() -> PageBlueprint:
    snapshot = ClusterStrategySnapshot(
        cluster_strategy_id="cs_opp_test",
        cluster_strategy_ref="reports/cluster-strategy/opp_test.json",
        opportunity_id="opp_test",
        opportunity_run_id="run_test",
        schema_version="1.0.0",
        cluster_id="limpeza-energetica",
        cluster_name="Limpeza Energética",
        subcluster_or_angle="new-home ritual",
        central_concept="Music for a home-cleansing ritual",
        positioning_statement="For es movers who want a calm ritual",
        editorial_promise="a calming ritual companion",
        market=Market("Mercados hispanohablantes"),
        language=Language("es"),
        consumption_context="at home, around a move",
        music_relationship="atmospheric backdrop",
        first_content_direction="short-form ritual content",
        editorial_angles=["the moving-in ritual"],
        overall_confidence=Confidence.LOW,
    )
    return PageBlueprint(
        page_blueprint_id="pb_opp_test",
        schema_version=SCHEMA_VERSION,
        cluster_strategy=snapshot,
        identity=PageIdentity(
            concept_name="Ritual Nuevo Hogar",
            positioning_statement="the soundtrack for your new-home ritual",
            bio="a short bio",
        ),
        visual_identity=VisualIdentity(
            visual_language="soft cream and gold tones",
            tone_of_voice="warm, intimate, ritual",
            musical_dna_expression_used=(
                "Limpeza energética: light · crystalline · spacious"
            ),
        ),
        asset_link=PageAssetLink(
            page_strategy=PageStrategy(
                primary_page_id="UNKNOWN", page_fit_basis="UNKNOWN",
                note="a new page is recommended upstream", new_page_recommendation=None,
            ),
            primary_playlist_id=_PLAYLIST_ID,
            primary_artist_id=_ARTIST_ID,
        ),
        content_framing=PageContentFraming(
            content_pillars=["the moving-in ritual"], platforms=["tiktok"],
            posting_cadence="3-4x per week",
        ),
        evaluation=PageBlueprintEvaluation(overall_confidence=Confidence.LOW, justification="j"),
        recommendation=PageBlueprintRecommendation(
            target_next_stage=PageBlueprintTargetNextStage.CONTENT_STRATEGY,
            recommended_next_step="proceed to Content Strategy",
            justification="the concept and asset are defined",
        ),
        provenance=PageBlueprintProvenance(
            run_id="pb_run_test", schema_version=SCHEMA_VERSION, model="claude-sonnet-5",
            prompt_version="pb-v1-test", generated_at="2026-09-04T00:00:00Z", replay=True,
            signal_ids=[], sources=[Provenance(
                source="x", source_type="web_search", observed_at="UNKNOWN",
                collected_at="2026-09-04T00:00:00Z", query_or_reference="x",
                capture_method="claude_web_search",
            )],
            knowledge_snapshot={},
        ),
    )


def _raw(mutate=None) -> dict:
    r = encode(_minimal_page_blueprint())
    if mutate:
        r = mutate(copy.deepcopy(r))
    return r


def _errs(raw: dict, *, needs_input: bool = False, ceiling: Confidence = Confidence.LOW):
    pb = decode(PageBlueprint, raw)
    return blocking(V.validate_page_blueprint(
        pb, cluster_strategy_overall_confidence=ceiling,
        inventory=_KB.inventory, musical_dna_needs_input=needs_input,
    ))


def _all(raw: dict, *, needs_input: bool = False, ceiling: Confidence = Confidence.LOW):
    pb = decode(PageBlueprint, raw)
    return V.validate_page_blueprint(
        pb, cluster_strategy_overall_confidence=ceiling,
        inventory=_KB.inventory, musical_dna_needs_input=needs_input,
    )


def test_the_minimal_valid_blueprint_passes():
    assert _errs(_raw()) == []


def test_a_0_to_100_score_in_any_prose_is_an_error():
    def inject(r):
        r["identity"]["bio"] = "we score this page 82/100 for fit"
        return r
    errs = _errs(_raw(inject))
    assert any("numeric_score" in e.code for e in errs)


def test_scope_leakage_field_name_is_rejected_by_the_codec_and_the_scanner():
    raw = _raw()
    raw["content_framing"]["hooks"] = ["hook 1", "hook 2"]
    from market_intelligence.schema.codec import CodecError
    with pytest.raises(CodecError):
        decode(PageBlueprint, raw)
    assert V.scan_for_scope_leakage(raw)  # the scanner is a regression guard


def test_overall_confidence_above_the_cluster_strategys_is_an_error():
    def raise_conf(r):
        r["evaluation"] = {**r["evaluation"], "overall_confidence": "HIGH"}
        return r
    errs = _errs(_raw(raise_conf))
    assert any("overall_confidence" in e.code for e in errs)


def test_high_confidence_while_musical_dna_needs_input_is_an_error():
    def raise_conf(r):
        r["evaluation"] = {**r["evaluation"], "overall_confidence": "HIGH"}
        return r
    errs = _errs(_raw(raise_conf), needs_input=True, ceiling=Confidence.HIGH)
    assert any("musical_dna_cap" in e.code for e in errs)


def test_medium_confidence_while_musical_dna_needs_input_is_allowed():
    def medium(r):
        r["evaluation"] = {**r["evaluation"], "overall_confidence": "MEDIUM"}
        return r
    errs = _errs(_raw(medium), needs_input=True, ceiling=Confidence.MEDIUM)
    assert errs == []


def test_missing_musical_dna_expression_used_is_an_error():
    def blank(r):
        r["visual_identity"] = {**r["visual_identity"], "musical_dna_expression_used": "  "}
        return r
    errs = _errs(_raw(blank))
    assert any("musical_dna_expression_missing" in e.code for e in errs)


def test_an_invented_artist_id_is_an_error():
    def invent(r):
        r["asset_link"] = {**r["asset_link"], "primary_artist_id": "art_totally_made_up"}
        return r
    errs = _errs(_raw(invent))
    assert any("asset" in e.code and "artist" in e.message.lower() for e in errs)


def test_a_reference_competitor_page_can_never_be_the_designed_page():
    ref_page = next(iter(_KB.inventory.reference_page_ids), None)
    if ref_page is None:
        pytest.skip("no reference page in the current inventory")

    def use_reference(r):
        r["asset_link"]["page_strategy"] = {
            **r["asset_link"]["page_strategy"], "primary_page_id": ref_page,
        }
        return r
    errs = _errs(_raw(use_reference))
    assert any("reference_page" in e.code for e in errs)


def test_unknown_sentinel_is_always_accepted_for_the_page():
    assert _errs(_raw()) == []  # primary_page_id == "UNKNOWN" in the minimal fixture


def test_tampered_content_boundary_note_is_an_error():
    def tamper(r):
        r["content_framing"]["content_boundary_note"] = "we also define hooks here"
        return r
    errs = _errs(_raw(tamper))
    assert any("content_boundary_note_tampered" in e.code for e in errs)


def test_tampered_asset_inheritance_note_is_an_error():
    def tamper(r):
        r["asset_link"]["asset_inheritance_note"] = "actually we re-decided the asset"
        return r
    errs = _errs(_raw(tamper))
    assert any("asset_inheritance_note_tampered" in e.code for e in errs)


def test_zero_content_pillars_is_an_error():
    def empty(r):
        r["content_framing"] = {**r["content_framing"], "content_pillars": []}
        return r
    errs = _errs(_raw(empty))
    assert any("no_content_pillars" in e.code for e in errs)


def test_too_many_content_pillars_is_a_non_blocking_warning():
    def flood(r):
        r["content_framing"]["content_pillars"] = [f"pillar {i}" for i in range(7)]
        return r
    raw = _raw(flood)
    all_errs = _all(raw)
    warned = [e for e in all_errs if e.code == "page_blueprint.too_many_content_pillars"]
    assert warned and warned[0].severity == "WARNING"
    assert _errs(raw) == []  # WARNING does not block the run
