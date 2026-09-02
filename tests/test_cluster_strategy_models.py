"""Cluster Strategy V1 — schema layer: enums, models, codec round-trip.

Cluster Strategy is canonical pipeline stage 3 (C8). This proposal's contract:
docs/CLUSTER-STRATEGY-V1.md (approved 2026-09-01). No 0–100 score (C6); no
LAUNCH/SCALE/KILL (I2); the opportunity lifecycle is carried, not transitioned.
"""

from __future__ import annotations

from cluster_strategy.schema import models as M
from cluster_strategy.schema.enums import (
    CLUSTER_DIMENSION_KEYS,
    SCHEMA_VERSION,
    ClusterDecisionKind,
    ClusterDimensionKey,
    TargetNextStage,
)
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.enums import (
    Confidence,
    Durability,
    LifecycleState,
    Market,
    Rating,
)


def test_the_four_cluster_dimension_keys_are_fixed_and_ordered():
    assert CLUSTER_DIMENSION_KEYS == [
        "cluster_fit",
        "differentiation_within_cluster",
        "asset_readiness",
        "strategic_coherence",
    ]
    assert [k.value for k in ClusterDimensionKey] == CLUSTER_DIMENSION_KEYS


def test_no_launch_scale_kill_in_the_next_stage_vocabulary():
    # target_next_stage is a pipeline action, NOT an opportunity lifecycle state.
    values = {s.value for s in TargetNextStage}
    assert values == {
        "PAGE_BLUEPRINT",
        "FORMALIZE_CLUSTER",
        "BACK_TO_MARKET_INTELLIGENCE",
        "HOLD",
    }
    assert "LAUNCH" not in values and "SCALE" not in values and "KILL" not in values


def _minimal_map_to_existing() -> M.ClusterStrategy:
    dim = lambda: M.ClusterDimensionRating(  # noqa: E731
        rating=Rating.MEDIUM, confidence=Confidence.LOW, justification="x"
    )
    return M.ClusterStrategy(
        cluster_strategy_id="cs_opp_2026-08-31_1bca4af972",
        schema_version=SCHEMA_VERSION,
        opportunity=M.OpportunitySnapshot(
            opportunity_id="opp_2026-08-31_1bca4af972",
            opportunity_run_id="run_2026-08-31_01",
            opportunity_report_ref="reports/run_2026-08-31_01/opp_2026-08-31_1bca4af972.json",
            schema_version="1.0.0",
            title="Energetic cleansing music for new-home rituals (ES market)",
            need="Música para limpiar energéticamente una casa nueva",
            audience_description="Hispanohablantes que se mudan a una casa nueva",
            market=Market.MERCADOS_HISPANOHABLANTES,
            language="es",
            platform="tiktok",
            consumption_context="Ritual de limpieza al mudarse",
            durability=Durability.EMERGING,
            urgency="MEDIUM",
            overall_confidence=Confidence.LOW,
            status=LifecycleState.EXPLORE,
            target_state=LifecycleState.TEST,
            potential_cluster_value="limpeza-energetica",
            potential_cluster_canonical=True,
            potential_cluster_basis="existing",
        ),
        owner_authorization=M.OwnerAuthorization(
            review_md_ref="reports/run_2026-08-31_01/review.md",
            advanced_opportunity_id="opp_2026-08-31_1bca4af972",
            reviewer="Nicolas",
        ),
        cluster_decision=M.ClusterDecision(
            decision=ClusterDecisionKind.MAP_TO_EXISTING,
            justification="fits limpeza-energetica per the taxonomy boundary",
            framing_hypothesis_comparison="confirmed",
            cluster_id="limpeza-energetica",
            cluster_name="Limpeza Energética",
            subcluster_or_angle="new-home / moving-in ritual",
            is_new_subcluster=True,
        ),
        strategic_definition=M.ClusterStrategicDefinition(
            central_concept="Music for the ritual of settling a new home",
            audience_description="es-speaking people around a house move",
            intent="soundtrack a moving-in ritual",
            emotional_state="a felt sense of welcome and calm",
            consumption_context="at home, around a move",
            editorial_promise="a calming ritual to welcome your new home",
            positioning_statement="For es movers who want a calm ritual, ...",
            market=Market.MERCADOS_HISPANOHABLANTES,
            language="es",
            localization_notes="es-native concept",
            durability_read="EMERGING — a recurring life event",
            strategic_coherence_note="core canonical cluster; serves the funnel",
        ),
        asset_strategy=M.ClusterAssetStrategy(
            playlist_strategy=M.PlaylistStrategy(
                primary_playlist_id="pl_4oV5F1W2E6azZePnmqBanN",
                playlist_fit_basis="OBSERVED",
                reuse_rationale="existing es Limpeza Energética playlist",
            ),
            page_strategy=M.PageStrategy(
                primary_page_id="UNKNOWN",
                page_fit_basis="UNKNOWN",
                note="a new es page is warranted; its design is Page Blueprint's",
            ),
            artist_strategy=M.ArtistStrategy(
                best_artist_id="art_7bnKOg3GDWAbLFtNhyn8Gw",
                anchor_hero_artist_ids=["art_7bnKOg3GDWAbLFtNhyn8Gw"],
            ),
            catalog_affinity_summary="cleansing-themed releases relate",
            market_language_fit=M.MarketLanguageFit(
                rating=Rating.HIGH, confidence=Confidence.MEDIUM,
                justification="es playlist + es-market hero anchor",
            ),
            asset_gaps=["no own page targets es Limpeza Energética"],
        ),
        content_direction=M.ClusterContentDirection(
            first_content_direction="short vertical video of a moving-in ritual",
            music_relationship="ambient bed to a slow ritual gesture",
            editorial_angles=["the first night", "room-by-room"],
        ),
        evaluation=M.ClusterEvaluation(
            dimensions={k: dim() for k in CLUSTER_DIMENSION_KEYS},
            overall_confidence=Confidence.LOW,
            red_flags=[],
            open_questions=["platform: tiktok vs youtube"],
        ),
        recommendation=M.ClusterRecommendation(
            target_next_stage=TargetNextStage.PAGE_BLUEPRINT,
            recommended_next_step="Proceed to Page Blueprint anchored on the es playlist",
            opportunity_lifecycle_state=LifecycleState.EXPLORE,  # == opportunity.status, carried
            justification="cluster confirmed; assets ready except the page",
        ),
        provenance=M.ClusterStrategyProvenance(
            run_id="cs_run_2026-09-01_01",
            schema_version=SCHEMA_VERSION,
            model="claude-sonnet-5",
            prompt_version="cs-v1",
            generated_at="2026-09-01T18:00:00Z",
            replay=True,
            signal_ids=["sig_run_2026-08-31_01_0014"],
            sources=[],
            knowledge_snapshot={"taxonomy_canonical_count": 11},
        ),
    )


def test_cluster_strategy_round_trips_through_the_codec():
    cs = _minimal_map_to_existing()
    raw = encode(cs)
    assert decode(M.ClusterStrategy, raw) == cs
    # re-encode is byte-identical (no null keys, stable order)
    assert encode(decode(M.ClusterStrategy, raw)) == raw


def test_fixed_disclaimer_text_is_present_and_carries_the_execution_note():
    cs = _minimal_map_to_existing()
    assert "Content Strategy (stage 5)" in cs.content_direction.content_boundary_note
    assert "does not execute" in cs.recommendation.execution_note
    assert "not a placement restriction" in cs.asset_strategy.artist_strategy.affinity_note


def test_defer_and_reject_may_omit_the_strategy_sections():
    cs = _minimal_map_to_existing()
    deferred = M.ClusterStrategy(
        cluster_strategy_id=cs.cluster_strategy_id,
        schema_version=cs.schema_version,
        opportunity=cs.opportunity,
        owner_authorization=cs.owner_authorization,
        cluster_decision=M.ClusterDecision(
            decision=ClusterDecisionKind.DEFER,
            justification="proposed_new cluster; P6 governance not open",
            framing_hypothesis_comparison="overridden — theme fits no canonical cluster",
            deferral_reason="needs a formal cluster (P6, deferred)",
        ),
        strategic_definition=None,
        asset_strategy=None,
        content_direction=None,
        evaluation=cs.evaluation,
        recommendation=M.ClusterRecommendation(
            target_next_stage=TargetNextStage.FORMALIZE_CLUSTER,
            recommended_next_step="Owner to formalize the cluster in cluster-taxonomy.md",
            opportunity_lifecycle_state=LifecycleState.EXPLORE,  # == opportunity.status, carried
            justification="cannot finalize a strategy for an unformalized cluster",
        ),
        provenance=cs.provenance,
    )
    raw = encode(deferred)
    assert "strategic_definition" not in raw and "asset_strategy" not in raw
    assert decode(M.ClusterStrategy, raw) == deferred
