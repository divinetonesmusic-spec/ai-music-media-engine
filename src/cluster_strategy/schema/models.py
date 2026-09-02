"""Dataclass models for the ``ClusterStrategy`` entity (contract §4).

Pure data holders — no behaviour, no validation. Structural checks are the shared
codec's job (``market_intelligence.schema.codec``); the contract's semantic rules
live in ``cluster_strategy.schema.validate``.

Shared value types (``Provenance``, ``NewAssetRecommendation``, ``RedFlag``) and
shared enums are imported from ``market_intelligence`` so stage 3 serialises with
the same codec and the same vocabulary as stages 1–2.

Field order: required fields (no default) first, then optional/defaulted fields
(dataclass rule, no ``kw_only`` for parity with the pipeline models).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from market_intelligence.schema.enums import (
    Confidence,
    Durability,
    Language,
    LifecycleState,
    Market,
    Rating,
    Urgency,
)
from market_intelligence.schema.models import NewAssetRecommendation, Provenance, RedFlag

from .enums import EXECUTION_NOTE, ClusterDecisionKind, TargetNextStage

# Fixed disclaimer text required verbatim on every ClusterStrategy (contract §4).
CONTENT_BOUNDARY_NOTE = (
    "Content pillars, formats, hooks, structures, CTAs, cadence and visual "
    "language are defined by Content Strategy (stage 5) and Page Blueprint "
    "(stage 4). This section is a non-binding starting direction only (C7, I11)."
)
AFFINITY_NOTE = (
    "Catalog affinity is context, not a placement restriction. Any artist may "
    "serve this cluster (spec §10.2a). Hero status is independent of catalog "
    "affinity — never conclude an artist 'does not fit' from an affinity mismatch."
)
NEW_CLUSTER_GOVERNANCE_NOTE = (
    "Formalizing a canonical cluster is an owner decision (P6, DEFERRED). This is "
    "a proposal only; the pipeline does not modify cluster-taxonomy.md."
)


# --- §4.1 Identity ---------------------------------------------------------

@dataclass
class OpportunitySnapshot:
    """Frozen copy of the input opportunity's decision-relevant fields (contract §4.1).
    Everything here is OBSERVED — carried from the Opportunity Report, unchanged."""

    opportunity_id: str
    opportunity_run_id: str
    opportunity_report_ref: str
    schema_version: str  # MUST be "1.0.0" (D-CS-11)
    title: str
    need: str
    audience_description: str
    market: Market
    language: Language
    platform: str  # an OPPORTUNITY_PLATFORMS value (already §13-enforced upstream)
    consumption_context: str
    durability: Durability
    urgency: Urgency
    overall_confidence: Confidence
    status: LifecycleState  # the opportunity's ACTUAL registry lifecycle state (I2)
    target_state: LifecycleState  # the Market Intelligence RECOMMENDATION (context only)
    audience_attributes: Optional[Dict[str, Any]] = None
    potential_cluster_value: Optional[str] = None
    potential_cluster_canonical: Optional[bool] = None
    potential_cluster_basis: Optional[str] = None  # "existing" | "proposed_new"


@dataclass
class OwnerAuthorization:
    """Proof the opportunity was advanced by the owner (contract §2.2, autonomy L1)."""

    review_md_ref: str
    advanced_opportunity_id: str
    reviewer: Optional[str] = None
    review_date: Optional[str] = None


# --- §4.2 Cluster Decision -----------------------------------------------

@dataclass
class NewClusterProposal:
    """A proposed canonical cluster — HYPOTHESIS + hand-off to the owner (contract §3.2).
    The pipeline never writes cluster-taxonomy.md (P6 deferred)."""

    proposed_id: str
    proposed_name: str
    concept: str
    boundary_vs_adjacent: Dict[str, str]  # canonical_cluster_id -> distinguishing sentence
    why_not_subcluster: str
    supporting_evidence: List[str]  # evidence-item refs / signal_ids from the opportunity
    governance_note: str = NEW_CLUSTER_GOVERNANCE_NOTE


@dataclass
class ClusterDecision:
    """The decision this stage reached about the cluster (contract §3, §4.2).
    ``decision`` is a RECOMMENDATION the owner approves before stage 4."""

    decision: ClusterDecisionKind
    justification: str
    framing_hypothesis_comparison: str  # confirmed / overrode the opp's potential_cluster, why
    cluster_id: Optional[str] = None  # required when MAP_TO_EXISTING (a canonical id)
    cluster_name: Optional[str] = None
    subcluster_or_angle: Optional[str] = None
    is_new_subcluster: Optional[bool] = None
    new_cluster_proposal: Optional[NewClusterProposal] = None  # required when PROPOSE_NEW_CLUSTER
    deferral_reason: Optional[str] = None  # required when DEFER
    rejection_reason: Optional[str] = None  # required when REJECT


# --- §4.3 Strategic Definition -----------------------------------------

@dataclass
class ClusterStrategicDefinition:
    """The cluster's strategy at cluster level (contract §4.3). Present only for
    MAP_TO_EXISTING / PROPOSE_NEW_CLUSTER (a DEFER/REJECT has no strategy to define)."""

    central_concept: str
    audience_description: str  # refined from the opportunity's audience + evidence
    intent: str
    emotional_state: str  # subjective experience only (G02) — never an outcome
    consumption_context: str  # carried
    editorial_promise: str  # guardrail-checked
    positioning_statement: str  # RECOMMENDATION
    market: Market  # carried
    language: Language  # carried
    localization_notes: str
    durability_read: str
    strategic_coherence_note: str
    audience_attributes: Optional[Dict[str, Any]] = None


# --- §4.4 Asset Strategy (NEVER invent — I1) --------------------------

@dataclass
class PlaylistStrategy:
    primary_playlist_id: str  # playlist_id | "UNKNOWN" | "NEW_ASSET"
    playlist_fit_basis: str  # "OBSERVED" | "INFERRED" | "UNKNOWN" (carried from AssetMatch)
    reuse_rationale: str
    secondary_playlist_ids: List[str] = field(default_factory=list)
    new_playlist_recommendation: Optional[NewAssetRecommendation] = None  # carried, never executed


@dataclass
class PageStrategy:
    primary_page_id: str  # own page_id | "UNKNOWN" | "NEW_ASSET"
    page_fit_basis: str
    note: str  # "a new page is/isn't warranted + why" — the page's DESIGN is Page Blueprint's
    new_page_recommendation: Optional[NewAssetRecommendation] = None  # carried verbatim


@dataclass
class ArtistStrategy:
    best_artist_id: str  # artist_id | "UNKNOWN"
    anchor_hero_artist_ids: List[str] = field(default_factory=list)
    catalog_affinity_artist_ids: List[str] = field(default_factory=list)
    candidate_artist_ids: List[str] = field(default_factory=list)
    affinity_note: str = AFFINITY_NOTE


@dataclass
class MarketLanguageFit:
    """Rating + SEPARATE confidence + justification. No score (C6). Confidence
    structurally capped <= MEDIUM while musical DNA / the classification backlog
    are NEEDS_INPUT (contract §5, §11)."""

    rating: Rating
    confidence: Confidence
    justification: str


@dataclass
class ClusterAssetStrategy:
    playlist_strategy: PlaylistStrategy
    page_strategy: PageStrategy
    artist_strategy: ArtistStrategy
    catalog_affinity_summary: str
    market_language_fit: MarketLanguageFit
    asset_gaps: List[str] = field(default_factory=list)


# --- §4.5 Content Direction (deliberately shallow) -------------------

@dataclass
class ClusterContentDirection:
    """The MINIMUM about content stage 4/5 need to start — nothing more (contract §8)."""

    first_content_direction: str  # HYPOTHESIS — carried/refined from the opportunity
    music_relationship: str  # the ROLE music plays; sonic spec is NEEDS_INPUT
    editorial_angles: List[str] = field(default_factory=list)  # HYPOTHESIS — tactical, non-binding
    content_boundary_note: str = CONTENT_BOUNDARY_NOTE


# --- §4.6 Evaluation & Confidence (no 0–100) --------------------------

@dataclass
class ClusterDimensionRating:
    rating: Rating  # LOW | MEDIUM | HIGH | VERY_HIGH
    confidence: Confidence  # LOW | MEDIUM | HIGH — separate from rating (C6)
    justification: str
    blocked_by: Optional[List[str]] = None  # NEEDS_INPUT / UNKNOWN items limiting this rating


@dataclass
class ClusterEvaluation:
    dimensions: Dict[str, ClusterDimensionRating]  # exactly the 4 CLUSTER_DIMENSION_KEYS
    overall_confidence: Confidence  # <= Opportunity.overall_confidence; not raised by sub-ratings
    red_flags: List[RedFlag]  # carried compliance flags + any in this stage's own prose
    open_questions: List[str] = field(default_factory=list)


# --- §4.7 Recommendation (I3 pattern) --------------------------------

@dataclass
class ClusterRecommendation:
    target_next_stage: TargetNextStage  # RECOMMENDATION — the next pipeline action
    recommended_next_step: str
    opportunity_lifecycle_state: LifecycleState  # carried from the Opportunity, UNCHANGED
    justification: str
    execution_note: str = EXECUTION_NOTE


# --- §4.1 Provenance ------------------------------------------------

@dataclass
class ClusterStrategyProvenance:
    run_id: str  # this Cluster Strategy run's id
    schema_version: str
    model: str
    prompt_version: str
    generated_at: str
    replay: bool  # true under recorded replay — the input opp may itself be a replay fixture (§22)
    signal_ids: List[str]  # carried union from the Opportunity Report
    sources: List[Provenance]  # carried distinct Provenance records
    knowledge_snapshot: Dict[str, Any]  # taxonomy / guardrails / inventory version markers


# --- the entity ----------------------------------------------------

@dataclass
class ClusterStrategy:
    """One Cluster Strategy per owner-advanced opportunity (contract §4).

    ``strategic_definition`` / ``asset_strategy`` / ``content_direction`` are
    present for MAP_TO_EXISTING and PROPOSE_NEW_CLUSTER, and omitted for
    DEFER / REJECT (the validator enforces this)."""

    cluster_strategy_id: str  # "cs_<opportunity_id>" (idempotent — one per opportunity)
    schema_version: str
    opportunity: OpportunitySnapshot
    owner_authorization: OwnerAuthorization
    cluster_decision: ClusterDecision
    evaluation: ClusterEvaluation
    recommendation: ClusterRecommendation
    provenance: ClusterStrategyProvenance
    strategic_definition: Optional[ClusterStrategicDefinition] = None
    asset_strategy: Optional[ClusterAssetStrategy] = None
    content_direction: Optional[ClusterContentDirection] = None
