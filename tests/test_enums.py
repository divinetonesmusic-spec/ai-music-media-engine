"""Controlled vocabularies — exact membership pinned to docs/TECHNICAL-SPEC-V1.md.

Every set here is a spec citation. If the spec changes, these tests change first.
"""

from market_intelligence.schema import enums as E

# --- §6.1 / §6.5 signal sources & capture methods -------------------------------

def test_source_type_is_exactly_the_four_v1_sources():
    # spec §6.1, §6.5, C2
    assert {s.value for s in E.SourceType} == {
        "web_search",
        "youtube",
        "tiktok_creative_center",
        "internal_data",
    }
    assert {s.value for s in E.SourceType} == set(E.V1_SIGNAL_SOURCES)


def test_capture_method_values():
    # spec §16.1
    assert {c.value for c in E.CaptureMethod} == {
        "claude_web_search",
        "youtube_data_api",
        "analyst_capture",
        "internal_data",
    }


# --- §7.1a market / language taxonomy -----------------------------------------

def test_market_values():
    # spec §7.1a — the only valid market values on an Opportunity
    assert {m.value for m in E.Market} == {
        "Brasil",
        "Mercados hispanohablantes",
        "English-speaking markets",
    }


def test_language_values():
    assert {lang.value for lang in E.Language} == {"pt", "es", "en"}


def test_language_to_market_mapping_is_bijective_and_matches_spec():
    # spec §7.1a table
    assert E.LANGUAGE_TO_MARKET == {
        E.Language.PT: E.Market.BRASIL,
        E.Language.ES: E.Market.MERCADOS_HISPANOHABLANTES,
        E.Language.EN: E.Market.ENGLISH_SPEAKING,
    }
    assert set(E.LANGUAGE_TO_MARKET.values()) == set(E.Market)


# --- §6.1 platform enum ------------------------------------------------------

def test_signal_platform_includes_web_and_unknown():
    # spec §6.1 Signal.platform
    assert {p.value for p in E.Platform} == {
        "tiktok", "youtube", "spotify", "instagram", "facebook", "web", "other", "UNKNOWN",
    }


def test_opportunity_platforms_exclude_web_and_unknown():
    # spec §7.1 Opportunity.platform enum
    assert {p.value for p in E.OPPORTUNITY_PLATFORMS} == {
        "tiktok", "youtube", "spotify", "instagram", "facebook", "other",
    }


# --- §6.2 signal_type -------------------------------------------------------

def test_signal_type_starter_set():
    # spec §6.2 (TECHNICAL DEFAULT starter set, derived from CLAUDE.md §7)
    assert {s.value for s in E.SignalType} == {
        "search_trend", "social_trend", "hashtag", "emerging_theme", "content_format",
        "competitor_activity", "audience_behavior", "emotional_need",
        "regional_opportunity", "language_opportunity", "platform_opportunity", "other",
    }


# --- §7.3 evidence typing --------------------------------------------------

def test_evidence_type_values():
    assert {e.value for e in E.EvidenceType} == {"OBSERVED", "INFERRED", "HYPOTHESIS"}


# --- §7.1 timing --------------------------------------------------------

def test_durability_values():
    # spec §7.1, I9
    assert {d.value for d in E.Durability} == {
        "EPHEMERAL", "EMERGING", "STRUCTURAL", "EVERGREEN",
    }


def test_urgency_and_confidence_are_low_medium_high():
    assert {u.value for u in E.Urgency} == {"LOW", "MEDIUM", "HIGH"}
    assert {c.value for c in E.Confidence} == {"LOW", "MEDIUM", "HIGH"}


# --- §8 evaluation --------------------------------------------------------

def test_rating_scale_has_very_high():
    # spec §8.2 DimensionRating.rating / AxisRating.rating
    assert [r.value for r in E.Rating] == ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]


def test_the_ten_evaluation_dimensions_in_spec_order():
    # spec §8.1 (C9)
    assert E.DIMENSION_KEYS == [
        "signal_strength",
        "audience_potential",
        "growth_momentum",
        "durability_opportunity_window",
        "music_fit",
        "content_potential",
        "competitive_position",
        "differentiation_potential",
        "asset_fit",
        "business_outcome_potential",
    ]
    assert [d.value for d in E.DimensionKey] == E.DIMENSION_KEYS


def test_the_five_business_outcome_axes_in_spec_order():
    # spec §9.1 (C5)
    assert E.AXIS_KEYS == [
        "playlist_growth_potential",
        "music_trend_ugc_potential",
        "streaming_royalty_potential",
        "page_growth_potential",
        "youtube_media_potential",
    ]
    assert [a.value for a in E.AxisKey] == E.AXIS_KEYS


def test_red_flag_kind_values():
    # spec §8.2 RedFlag.kind
    assert {k.value for k in E.RedFlagKind} == {
        "compliance", "feasibility", "evidence_gap", "asset_gap", "market", "other",
    }


def test_severity_values():
    assert {s.value for s in E.Severity} == {"LOW", "MEDIUM", "HIGH"}


# --- §5 / §7.1 lifecycle ------------------------------------------------

def test_lifecycle_states_full_and_v1_operational_subset():
    # spec §5, §7.1, CLAUDE.md §9
    assert {s.value for s in E.LifecycleState} == {
        "EXPLORE", "TEST", "LAUNCH", "SCALE", "KILL", "PARK",
    }
    assert {s.value for s in E.V1_OPERATIONAL_STATES} == {"EXPLORE", "TEST", "PARK"}
    assert E.V1_OPERATIONAL_STATES.issubset(set(E.LifecycleState))


# --- §10 asset matching -----------------------------------------------

def test_asset_type_values():
    assert {a.value for a in E.AssetType} == {"playlist", "page", "artist", "catalog"}


def test_fit_level_and_fit_basis():
    # spec §10.3 AssetCandidate
    assert {f.value for f in E.FitLevel} == {"NONE", "LOW", "MEDIUM", "HIGH"}
    assert {f.value for f in E.FitBasis} == {"OBSERVED", "INFERRED", "UNKNOWN"}


def test_asset_role_values():
    assert {r.value for r in E.AssetRole} == {"candidate", "reference", "hero"}


def test_new_asset_type_values():
    # spec §10.3 NewAssetRecommendation.asset_type
    assert {a.value for a in E.NewAssetType} == {"page", "playlist", "other"}


# --- §13 / guardrails.yaml -------------------------------------------

def test_guardrail_type_and_action_values():
    # knowledge/rules/guardrails.yaml meta block
    assert {t.value for t in E.GuardrailType} == {"prohibition", "permissive", "principle"}
    assert {a.value for a in E.GuardrailAction} == {
        "reject_and_revise",
        "exclude_opportunity",
        "flag",
        "flag_for_validation",
        "require_uncertainty_statement",
        "none",
    }


# --- §15 sentinels ---------------------------------------------------

def test_sentinels():
    # spec §15
    assert E.UNKNOWN == "UNKNOWN"
    assert E.NEEDS_INPUT == "NEEDS_INPUT"
    assert E.NEW_ASSET == "NEW_ASSET"


def test_potential_cluster_basis_values():
    # spec §7.2 hypotheses.potential_cluster.basis
    assert {b.value for b in E.ClusterBasis} == {"existing", "proposed_new"}
