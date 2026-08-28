"""Controlled vocabularies for Market Intelligence V1.

Every enum and constant here is a direct transcription of a value set in
``docs/TECHNICAL-SPEC-V1.md`` (which in turn cites ``knowledge/DECISIONS-NEEDED.md``).
No value is invented. Section references are on each definition.

All enums subclass ``(str, Enum)`` so members compare equal to their raw string
and serialise transparently to YAML / JSON.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List

# --- §15 sentinels ------------------------------------------------------------
# Two distinct sentinels; neither is ever replaced by a guess (spec §15).
UNKNOWN = "UNKNOWN"            # information absent from the sources available to the run
NEEDS_INPUT = "NEEDS_INPUT"    # knowable, but pending an owner decision
NEW_ASSET = "NEW_ASSET"        # AssetMatch.best_page marker for a recommended new asset (§10.3)


class SourceType(str, Enum):
    """The four V1 signal sources (spec §6.1, §6.5; decision C2)."""

    WEB_SEARCH = "web_search"
    YOUTUBE = "youtube"
    TIKTOK_CREATIVE_CENTER = "tiktok_creative_center"
    INTERNAL_DATA = "internal_data"


class CaptureMethod(str, Enum):
    """How a signal was captured (spec §16.1 Provenance.capture_method)."""

    CLAUDE_WEB_SEARCH = "claude_web_search"
    YOUTUBE_DATA_API = "youtube_data_api"
    ANALYST_CAPTURE = "analyst_capture"
    INTERNAL_DATA = "internal_data"


class Market(str, Enum):
    """V1 market taxonomy — the only valid market values on an Opportunity (spec §7.1a)."""

    BRASIL = "Brasil"
    MERCADOS_HISPANOHABLANTES = "Mercados hispanohablantes"
    ENGLISH_SPEAKING = "English-speaking markets"


class Language(str, Enum):
    """Priority language markets (spec §7.1a; business-dna §8)."""

    PT = "pt"
    ES = "es"
    EN = "en"


class Platform(str, Enum):
    """Signal.platform enum (spec §6.1). Superset of OPPORTUNITY_PLATFORMS."""

    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WEB = "web"
    OTHER = "other"
    UNKNOWN = "UNKNOWN"  # spec §6.1 writes this token uppercase, matching the §15 sentinel


class SignalType(str, Enum):
    """Signal.signal_type starter set (spec §6.2, TECHNICAL DEFAULT; CLAUDE.md §7).

    Extendable without a schema change.
    """

    SEARCH_TREND = "search_trend"
    SOCIAL_TREND = "social_trend"
    HASHTAG = "hashtag"
    EMERGING_THEME = "emerging_theme"
    CONTENT_FORMAT = "content_format"
    COMPETITOR_ACTIVITY = "competitor_activity"
    AUDIENCE_BEHAVIOR = "audience_behavior"
    EMOTIONAL_NEED = "emotional_need"
    REGIONAL_OPPORTUNITY = "regional_opportunity"
    LANGUAGE_OPPORTUNITY = "language_opportunity"
    PLATFORM_OPPORTUNITY = "platform_opportunity"
    OTHER = "other"


class EvidenceType(str, Enum):
    """Evidence typing — distinct categories that must never be collapsed (spec §7.3, I4)."""

    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"


class Durability(str, Enum):
    """Opportunity durability label (spec §7.1; I9)."""

    EPHEMERAL = "EPHEMERAL"
    EMERGING = "EMERGING"
    STRUCTURAL = "STRUCTURAL"
    EVERGREEN = "EVERGREEN"


class Urgency(str, Enum):
    """Opportunity urgency — separate axis from durability (spec §7.1; I9)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Confidence(str, Enum):
    """Confidence level, kept separate from any rating (spec §8; C6)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Rating(str, Enum):
    """Qualitative rating for an evaluation dimension or an outcome axis (spec §8.2).

    Declared low-to-high; there is NO numeric mapping (C6 — no composite score).
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class DimensionKey(str, Enum):
    """The 10 evaluation dimensions (spec §8.1; C9). Order is significant."""

    SIGNAL_STRENGTH = "signal_strength"
    AUDIENCE_POTENTIAL = "audience_potential"
    GROWTH_MOMENTUM = "growth_momentum"
    DURABILITY_OPPORTUNITY_WINDOW = "durability_opportunity_window"
    MUSIC_FIT = "music_fit"
    CONTENT_POTENTIAL = "content_potential"
    COMPETITIVE_POSITION = "competitive_position"
    DIFFERENTIATION_POTENTIAL = "differentiation_potential"
    ASSET_FIT = "asset_fit"
    BUSINESS_OUTCOME_POTENTIAL = "business_outcome_potential"


class AxisKey(str, Enum):
    """The 5 Business Outcome Profile axes (spec §9.1; C5). Kept separate, never aggregated."""

    PLAYLIST_GROWTH_POTENTIAL = "playlist_growth_potential"
    MUSIC_TREND_UGC_POTENTIAL = "music_trend_ugc_potential"
    STREAMING_ROYALTY_POTENTIAL = "streaming_royalty_potential"
    PAGE_GROWTH_POTENTIAL = "page_growth_potential"
    YOUTUBE_MEDIA_POTENTIAL = "youtube_media_potential"


class RedFlagKind(str, Enum):
    """RedFlag.kind (spec §8.2, TECHNICAL DEFAULT set)."""

    COMPLIANCE = "compliance"
    FEASIBILITY = "feasibility"
    EVIDENCE_GAP = "evidence_gap"
    ASSET_GAP = "asset_gap"
    MARKET = "market"
    OTHER = "other"


class Severity(str, Enum):
    """Severity scale shared by RedFlag and the guardrails (spec §8.2; guardrails.yaml)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LifecycleState(str, Enum):
    """Conceptual opportunity lifecycle (spec §5; CLAUDE.md §9).

    V1 execution is constrained to V1_OPERATIONAL_STATES; the model still permits
    LAUNCH / SCALE / KILL so reports stay forward-compatible.
    """

    EXPLORE = "EXPLORE"
    TEST = "TEST"
    LAUNCH = "LAUNCH"
    SCALE = "SCALE"
    KILL = "KILL"
    PARK = "PARK"


class AssetType(str, Enum):
    """AssetCandidate.asset_type (spec §10.3)."""

    PLAYLIST = "playlist"
    PAGE = "page"
    ARTIST = "artist"
    CATALOG = "catalog"


class FitLevel(str, Enum):
    """AssetCandidate.fit (spec §10.3)."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FitBasis(str, Enum):
    """AssetCandidate.fit_basis (spec §10.2 step 2, §10.3).

    OBSERVED  -> supported by a consolidated inventory classification
    INFERRED  -> relies on name/title text, a NEEDS_INPUT field, or a hypothesis
    UNKNOWN   -> no adequate basis to judge fit
    """

    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"


class AssetRole(str, Enum):
    """AssetCandidate.role (spec §10.3)."""

    CANDIDATE = "candidate"
    REFERENCE = "reference"  # reference_competitor pages — context only, never recommended
    HERO = "hero"            # artist flagged hero_artist: true


class NewAssetType(str, Enum):
    """NewAssetRecommendation.asset_type (spec §10.3)."""

    PAGE = "page"
    PLAYLIST = "playlist"
    OTHER = "other"


class ClusterBasis(str, Enum):
    """hypotheses.potential_cluster.basis (spec §7.2)."""

    EXISTING = "existing"
    PROPOSED_NEW = "proposed_new"


class GuardrailType(str, Enum):
    """guardrails.yaml meta.guardrail_types."""

    PROHIBITION = "prohibition"
    PERMISSIVE = "permissive"
    PRINCIPLE = "principle"


class GuardrailAction(str, Enum):
    """guardrails.yaml meta.action_values (spec §13)."""

    REJECT_AND_REVISE = "reject_and_revise"
    EXCLUDE_OPPORTUNITY = "exclude_opportunity"
    FLAG = "flag"
    FLAG_FOR_VALIDATION = "flag_for_validation"
    REQUIRE_UNCERTAINTY_STATEMENT = "require_uncertainty_statement"
    NONE = "none"


# --- derived constants -------------------------------------------------------

#: The four collectors that may run (spec §6.1, §20.1 signal_sources; C2).
V1_SIGNAL_SOURCES: List[str] = [s.value for s in SourceType]

#: spec §7.1a — language <-> market are consistent by this table; a mismatch is a
#: validation failure (§13).
LANGUAGE_TO_MARKET: Dict[Language, Market] = {
    Language.PT: Market.BRASIL,
    Language.ES: Market.MERCADOS_HISPANOHABLANTES,
    Language.EN: Market.ENGLISH_SPEAKING,
}
MARKET_TO_LANGUAGE: Dict[Market, Language] = {
    market: lang for lang, market in LANGUAGE_TO_MARKET.items()
}

#: spec §7.1 Opportunity.platform — the Signal superset minus ``web`` and ``unknown``.
OPPORTUNITY_PLATFORMS = frozenset(
    {
        Platform.TIKTOK,
        Platform.YOUTUBE,
        Platform.SPOTIFY,
        Platform.INSTAGRAM,
        Platform.FACEBOOK,
        Platform.OTHER,
    }
)

#: spec §5, §7.1 — the lifecycle states V1 actually emits / stores.
V1_OPERATIONAL_STATES = frozenset(
    {LifecycleState.EXPLORE, LifecycleState.TEST, LifecycleState.PARK}
)

#: spec §8.1 (C9) — the 10 dimension keys, in canonical order.
DIMENSION_KEYS: List[str] = [d.value for d in DimensionKey]

#: spec §9.1 (C5) — the 5 outcome axes, in canonical order.
AXIS_KEYS: List[str] = [a.value for a in AxisKey]

#: knowledge/clusters/cluster-taxonomy.md — count only; the ids are loaded at runtime
#: by the Knowledge Loader (spec §18) and validated against this number.
CANONICAL_CLUSTER_COUNT = 11

#: knowledge/rules/guardrails.yaml — count only; ids G01..G10 checked by the loader.
GUARDRAIL_COUNT = 10
