"""Dataclass models for the ``PageBlueprint`` entity (contract §4).

Pure data holders — no behaviour, no validation (that lives in
``page_blueprint.schema.validate``). Shared value types (``Provenance``,
``NewAssetRecommendation``, ``RedFlag``) and shared enums come from
``market_intelligence``; the asset-decision types (``PageStrategy``,
``PlaylistStrategy``, ``ArtistStrategy``) come from ``cluster_strategy`` —
Page Blueprint carries them **verbatim**, it never re-decides an asset (D-PB-3).

Field order: required fields (no default) first, then optional/defaulted
fields, matching the pipeline's existing dataclass convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cluster_strategy.schema.models import PageStrategy
from market_intelligence.schema.enums import Confidence, Language, Market
from market_intelligence.schema.models import Provenance, RedFlag

from .enums import EXECUTION_NOTE, PageBlueprintTargetNextStage

# Fixed disclaimer text required verbatim on every PageBlueprint (contract §4, §B).
# Mirrors cluster_strategy.schema.models.CONTENT_BOUNDARY_NOTE — the same boundary,
# restated from Page Blueprint's side of it.
CONTENT_BOUNDARY_NOTE = (
    "Content pillars here are a broad thematic outline for this page only — not "
    "formats, hooks, structures, CTA copy, linguistic/visual production rules, or "
    "a content calendar. Those are Content Strategy's job (stage 5, C7/I11)."
)

#: Fixed disclaimer confirming the asset decision was NOT re-made here (D-PB-3).
ASSET_INHERITANCE_NOTE = (
    "The page/playlist/artist decision is carried verbatim from Cluster Strategy "
    "(stage 3) — Page Blueprint designs the page, it does not re-decide whether a "
    "new asset is warranted (I5) or which asset anchors it."
)


# --- §4.1 Identity & Provenance --------------------------------------------

@dataclass
class ClusterStrategySnapshot:
    """Frozen copy of the input ClusterStrategy's decision-relevant fields
    (contract §4.1). Everything here is carried, unchanged, from stage 3."""

    cluster_strategy_id: str
    cluster_strategy_ref: str  # path to the ClusterStrategy sidecar this run consumed
    opportunity_id: str
    opportunity_run_id: str
    schema_version: str  # MUST be "1.0.0" (mirrors D-CS-11's pin)
    cluster_id: Optional[str]  # a canonical id, or None for a proposed cluster
    cluster_name: Optional[str]
    subcluster_or_angle: Optional[str]
    central_concept: str
    positioning_statement: str
    editorial_promise: str
    market: Market
    language: Language
    consumption_context: str
    music_relationship: str  # the role music plays — from ClusterContentDirection
    first_content_direction: str
    editorial_angles: List[str]
    overall_confidence: Confidence  # ClusterStrategy's — this stage's ceiling (mirrors C6)


# --- §4.2 Page Identity (Claude-authored synthesis) ------------------------

@dataclass
class PageIdentity:
    concept_name: str
    # one sentence — may refine ClusterStrategy's, must not contradict it
    positioning_statement: str
    bio: str  # a short bio-length text (a page profile bio, not a caption)


# --- §4.3 Visual Identity — the Musical DNA §9 consumption point -----------

@dataclass
class VisualIdentity:
    """Visual identity + tone of voice, derived from the cluster's house-sound
    expression (business-dna §9.9) and the cluster's positioning (contract §5).
    Never derived from anything else in §9 (D-PB-4) — no instrumentation/BPM/
    frequency detail belongs here, that is Audio Engine's job (stage 8)."""

    visual_language: str  # palette / mood / imagery descriptors
    tone_of_voice: str  # copy register / voice
    # the exact §9.9 cluster-expression phrase this was grounded in
    musical_dna_expression_used: str


# --- §4.4 Asset Link — carried verbatim, never re-decided (D-PB-3) ---------

@dataclass
class PageAssetLink:
    page_strategy: PageStrategy  # carried verbatim from ClusterStrategy.asset_strategy
    primary_playlist_id: str  # carried from ClusterStrategy.asset_strategy.playlist_strategy
    primary_artist_id: str  # carried from ClusterStrategy.asset_strategy.artist_strategy
    asset_inheritance_note: str = ASSET_INHERITANCE_NOTE


# --- §4.5 Content Framing (deliberately shallow — see §5, D-PB-2) ---------

@dataclass
class PageContentFraming:
    content_pillars: List[str]  # 3–5 broad thematic pillars for THIS page only
    platforms: List[str]  # platform(s) this page should run on
    posting_cadence: str  # a qualitative recommendation, e.g. "3–4x per week" — never a schedule
    content_boundary_note: str = CONTENT_BOUNDARY_NOTE


# --- §4.6 Evaluation & Confidence (no 0–100, no multi-dim rubric — D-PB-6) -

@dataclass
class PageBlueprintEvaluation:
    overall_confidence: Confidence  # <= ClusterStrategy's; not raised by the synthesis itself
    justification: str
    red_flags: List[RedFlag] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)  # NEEDS_INPUT / UNKNOWN items


# --- §4.7 Recommendation (I3 pattern) --------------------------------------

@dataclass
class PageBlueprintRecommendation:
    target_next_stage: PageBlueprintTargetNextStage
    recommended_next_step: str
    justification: str
    execution_note: str = EXECUTION_NOTE


# --- §4.1 Provenance --------------------------------------------------------

@dataclass
class PageBlueprintProvenance:
    run_id: str  # this Page Blueprint run's id
    schema_version: str
    model: str
    prompt_version: str
    generated_at: str
    replay: bool  # true under recorded replay — the input ClusterStrategy may itself be a fixture
    signal_ids: List[str]  # carried union from the Opportunity Report (via ClusterStrategy)
    sources: List[Provenance]  # carried distinct Provenance records
    knowledge_snapshot: Dict[str, Any]  # business-dna §9 version marker


# --- the entity -------------------------------------------------------------

@dataclass
class PageBlueprint:
    """One Page Blueprint per Cluster-Strategy-recommended opportunity (contract
    §4). Requires ``ClusterStrategy.recommendation.target_next_stage ==
    PAGE_BLUEPRINT`` on the input (contract §2)."""

    page_blueprint_id: str  # "pb_<opportunity_id>" (idempotent — one per opportunity)
    schema_version: str
    cluster_strategy: ClusterStrategySnapshot
    identity: PageIdentity
    visual_identity: VisualIdentity
    asset_link: PageAssetLink
    content_framing: PageContentFraming
    evaluation: PageBlueprintEvaluation
    recommendation: PageBlueprintRecommendation
    provenance: PageBlueprintProvenance
