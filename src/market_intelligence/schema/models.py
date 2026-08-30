"""Dataclass models for every structured entity in Market Intelligence V1.

Each model maps 1:1 to a schema table in ``docs/TECHNICAL-SPEC-V1.md``; the section
reference is on the class. Models are pure data holders — no behaviour, no
validation. Structural checks (field presence/type/enum) are the codec's job
(``codec.py``); the semantic rules of spec §13 live in ``validate.py``.

Field order: required fields (no default) first, then optional/defaulted fields,
because Python 3.9 dataclasses have no ``kw_only``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .enums import (
    AssetRole,
    AssetType,
    CaptureMethod,
    Confidence,
    Durability,
    EvidenceType,
    FitBasis,
    FitLevel,
    GuardrailAction,
    GuardrailType,
    Language,
    LifecycleState,
    Market,
    NewAssetType,
    Platform,
    Rating,
    RedFlagKind,
    Severity,
    SignalType,
    SourceType,
    Urgency,
)

# Constant text required verbatim on every Recommendation (spec §12.4).
EXECUTION_NOTE = "V1 does not execute this action; it requires human approval."


# --- §16.1 Provenance / §6.1 Signal -----------------------------------------

@dataclass
class Provenance:
    """Per-Signal provenance — the full trace of why a signal exists (spec §16.1)."""

    source: str
    source_type: SourceType
    observed_at: str  # ISO date, or the literal "UNKNOWN"
    collected_at: str  # ISO datetime
    query_or_reference: str
    capture_method: CaptureMethod
    url: Optional[str] = None
    source_version: Optional[str] = None


@dataclass
class Signal:
    """A normalised, atomic observation from one source. Inherently OBSERVED (spec §6.1)."""

    signal_id: str
    schema_version: str
    run_id: str
    source: str
    source_type: SourceType
    observed_at: str
    collected_at: str
    market: str  # a Market value or "UNKNOWN" (§6.1)
    language: str  # "pt" | "es" | "en" | "UNKNOWN" (§6.1)
    platform: Platform
    signal_type: SignalType
    evidence: str
    raw_ref: str
    context: str
    confidence: Confidence
    provenance: Provenance
    url: Optional[str] = None
    raw_excerpt: Optional[str] = None
    durability_hint: Optional[Durability] = None
    metrics: Optional[Dict[str, Any]] = None  # map<string, number|string>; missing -> UNKNOWN


# --- §7 Opportunity ---------------------------------------------------------

@dataclass
class Audience:
    """Opportunity.audience (spec §7.1)."""

    description: str
    attributes: Optional[Dict[str, Any]] = None


@dataclass
class EvidenceItem:
    """One typed evidence claim on an Opportunity (spec §7.3, I4)."""

    type: EvidenceType
    statement: str
    confidence: Confidence
    signal_ids: Optional[List[str]] = None  # required when type == OBSERVED (§13)
    derived_from: Optional[List[str]] = None  # required when type == INFERRED (§13)
    rationale: Optional[str] = None  # required when type in {INFERRED, HYPOTHESIS} (§13)
    test_idea: Optional[str] = None


@dataclass
class PotentialCluster:
    """hypotheses.potential_cluster (spec §7.2)."""

    value: str
    canonical: bool
    basis: str  # ClusterBasis value: "existing" | "proposed_new"


@dataclass
class Hypotheses:
    """Derived / hypothetical fields — every one is a HYPOTHESIS, non-binding (spec §7.2, C7)."""

    potential_cluster: Optional[PotentialCluster] = None
    potential_positioning: Optional[str] = None
    potential_page: Optional[str] = None  # an existing page_id, or "NEW_ASSET"
    first_content_direction: Optional[str] = None
    format: Optional[str] = None
    hook: Optional[str] = None


# --- §8 Evaluation --------------------------------------------------------

@dataclass
class DimensionRating:
    """One of the 10 evaluation dimensions (spec §8.2)."""

    rating: Rating
    confidence: Confidence
    justification: str
    blocked_by: Optional[List[str]] = None


@dataclass
class RedFlag:
    """A blocking / impeding factor (spec §8.2, C6)."""

    description: str
    severity: Severity
    kind: RedFlagKind


@dataclass
class Evaluation:
    """Qualitative multidimensional profile — NO composite 0–100 score (spec §8.2, C6)."""

    schema_version: str
    dimensions: Dict[str, DimensionRating]  # exactly the 10 keys of §8.1
    red_flags: List[RedFlag]
    overall_confidence: Confidence
    summary: str


# --- §9 Business Outcome Profile ----------------------------------------

@dataclass
class AxisRating:
    """One of the 5 value-engine axes (spec §9.1, C5)."""

    rating: Rating
    confidence: Confidence
    justification: str


@dataclass
class BusinessOutcomeProfile:
    """The 5 axes, kept separate — never aggregated into one value (spec §9.1, C5)."""

    schema_version: str
    axes: Dict[str, AxisRating]  # exactly the 5 keys of §9.1


# --- §10 Asset Matching ------------------------------------------------

@dataclass
class AssetCandidate:
    """A candidate inventory asset with a fit judgement (spec §10.3)."""

    asset_type: AssetType
    asset_id: str
    name: str
    fit: FitLevel
    fit_basis: FitBasis
    fit_rationale: str
    role: Optional[AssetRole] = None


@dataclass
class I5Conditions:
    """The four I5 conditions for recommending a new asset (spec §10.3)."""

    no_adequate_fit: bool
    relevant_potential: bool
    differentiation_potential: bool
    sufficient_window: bool


@dataclass
class NewAssetRecommendation:
    """Recommendation only — never executed in V1 (spec §10.3, I5)."""

    asset_type: NewAssetType
    rationale: str
    i5_conditions_met: I5Conditions


@dataclass
class AssetMatch:
    """Connects an opportunity to EXISTING inventory assets — no asset invented (spec §10.3)."""

    schema_version: str
    matching_playlists: List[AssetCandidate]
    matching_pages: List[AssetCandidate]
    matching_artists: List[AssetCandidate]
    best_playlist: str  # playlist_id or "UNKNOWN"
    best_page: str  # page_id, "UNKNOWN", or "NEW_ASSET"
    best_artist: str  # artist_id or "UNKNOWN"
    matching_catalog: Optional[List[AssetCandidate]] = None
    new_asset_recommendation: Optional[NewAssetRecommendation] = None
    unmatched_reason: Optional[str] = None  # required when any best_* is "UNKNOWN" (§13)


# --- §12.4 Recommendation --------------------------------------------

@dataclass
class Recommendation:
    """target_state + suggested_next_step + justification (spec §12.4, I3, C6)."""

    schema_version: str
    target_state: LifecycleState
    suggested_next_step: str
    justification: str
    confidence: Confidence
    execution_note: str = EXECUTION_NOTE


# --- §7.1 registry fields / §16.2 provenance -------------------------

@dataclass
class StateChange:
    """One entry in Opportunity.state_history (spec §7.1)."""

    to: str  # a LifecycleState value
    at: str  # ISO datetime
    by: str  # "system" or a human id
    from_: Optional[str] = field(default=None, metadata={"codec_key": "from"})
    note: Optional[str] = None


@dataclass
class OpportunityProvenance:
    """Aggregate provenance for an Opportunity (spec §16.2)."""

    run_id: str
    schema_version: str
    model: str
    prompt_version: str
    generated_at: str
    signal_ids: List[str]
    sources: List[Provenance]
    replay: bool


@dataclass
class Opportunity:
    """The unit of analysis (spec §7.1, C1). OPPORTUNITY != CLUSTER."""

    opportunity_id: str
    schema_version: str
    run_id: str
    created_at: str
    title: str
    # C1 mandatory minimum structure — all six required, non-empty:
    need: str
    audience: Audience
    market: Market
    language: Language
    platform: Platform  # validated against OPPORTUNITY_PLATFORMS (§13)
    consumption_context: str
    # timing (I9):
    durability: Durability
    urgency: Urgency
    # evidence / analysis outputs:
    evidence: List[EvidenceItem]
    asset_fit: AssetMatch
    evaluation: Evaluation
    business_outcome_profile: BusinessOutcomeProfile
    recommendation: Recommendation
    provenance: OpportunityProvenance
    # registry fields (I2):
    status: LifecycleState
    state_history: List[StateChange]
    # derived / hypothetical (C7 — non-binding):
    hypotheses: Optional[Hypotheses] = None
    rank: Optional[int] = None
    report_ref: Optional[str] = None


# --- §12.2 Opportunity Report front matter ---------------------------

@dataclass
class OpportunityReportFrontMatter:
    """Front matter of a rendered Opportunity Report (spec §12.2)."""

    opportunity_id: str
    run_id: str
    schema_version: str
    created_at: str
    rank: int
    title: str
    market: Market
    language: Language
    platforms: List[Platform]
    durability: Durability
    urgency: Urgency
    potential_cluster: Optional[str]  # canonical id, "<name> (proposed_new)", or None
    overall_confidence: Confidence
    target_state: LifecycleState


# --- §20 Configuration ----------------------------------------------

@dataclass
class RunScope:
    """RunConfig.scope — the research brief (spec §20.1)."""

    clusters: List[str] = field(default_factory=list)  # subset of the 11 canonical ids
    markets: List[Market] = field(default_factory=list)  # [] == all three
    languages: List[Language] = field(
        default_factory=lambda: [Language.PT, Language.ES, Language.EN]
    )
    discovery_platforms: List[Platform] = field(
        default_factory=lambda: [Platform.TIKTOK, Platform.YOUTUBE]
    )
    notes: Optional[str] = None
    # TECHNICAL DEFAULT — explicit search queries for the deterministic collectors
    # (e.g. YouTube Data API). Spec §6.5 requires a `query`; §20.1 has no field for it.
    queries: List[str] = field(default_factory=list)
    # TECHNICAL DEFAULT — optional YouTube `regionCode` (ISO 3166-1 alpha-2). Only an
    # API hint; it does NOT set a Signal's `market` (§7.1a — no country taxonomy in V1).
    youtube_region_code: Optional[str] = None


@dataclass
class ReplayConfig:
    """RunConfig.replay (spec §20.1, §22)."""

    enabled: bool = False
    fixture_path: Optional[str] = None  # required when enabled (§13)
    llm: Optional[str] = None  # "recorded" | "live" (§22)


@dataclass
class RunPaths:
    """RunConfig.paths — repo-relative locations (spec §17, §20.1). Defaults = §17 layout."""

    knowledge_dir: str = "knowledge"
    inventories_dir: str = "knowledge/inventories"
    business_dna_path: str = "knowledge/business-dna/business-dna.md"
    content_methodology_path: str = "knowledge/business-dna/content-methodology.md"
    guardrails_path: str = "knowledge/rules/guardrails.yaml"
    taxonomy_path: str = "knowledge/clusters/cluster-taxonomy.md"
    registry_path: str = "knowledge/market/opportunity-registry.yaml"
    ranking_config_path: str = "config/ranking.yaml"
    dedup_config_path: str = "config/dedup.yaml"
    reports_dir: str = "reports"
    data_dir: str = "data"


@dataclass
class RunConfig:
    """A single pipeline invocation's configuration (spec §20.1)."""

    run_id: str  # ^[A-Za-z0-9_\-]+$ (§13)
    run_date: str  # ISO date
    model: str  # a Claude model id
    prompt_version: str
    schema_version: str = "1.0.0"
    scope: RunScope = field(default_factory=RunScope)
    signal_sources: List[SourceType] = field(
        default_factory=lambda: list(SourceType)
    )
    max_opportunities_presented: int = 10  # I12
    min_opportunities_target: int = 5  # C10 lower target (advisory)
    max_candidates: Optional[int] = None
    internal_data_path: Optional[str] = None
    tiktok_capture_path: Optional[str] = None
    extraction_model: Optional[str] = None
    paths: RunPaths = field(default_factory=RunPaths)
    dry_run: bool = False
    replay: ReplayConfig = field(default_factory=ReplayConfig)


# --- knowledge/rules/guardrails.yaml (spec §13) ----------------------

@dataclass
class Guardrail:
    """One machine-readable compliance guardrail G01..G10 (guardrails.yaml, spec §13)."""

    guardrail_id: str
    name: str
    type: GuardrailType
    description: str
    severity: Severity
    action_on_violation: GuardrailAction
    applies_to: Optional[List[str]] = None  # absent for permissive/principle entries
    escalation: Optional[GuardrailAction] = None
    note: Optional[str] = None
