"""Controlled vocabularies for Cluster Strategy V1.

Only three enums are introduced here; everything else (Rating, Confidence,
Severity, RedFlagKind, Market, Language, LifecycleState, Durability, Urgency,
NewAssetType, FitBasis) is reused verbatim from ``market_intelligence.schema.enums``
so stage 3 speaks exactly the same vocabulary as stages 1–2.

No 0–100 score anywhere (C6). ``TargetNextStage`` is a *pipeline action*, not an
opportunity lifecycle state — it deliberately excludes LAUNCH / SCALE / KILL (I2).
"""

from __future__ import annotations

from enum import Enum
from typing import List

SCHEMA_VERSION = "1.0.0"

#: Verbatim from ``market_intelligence.schema.models.EXECUTION_NOTE`` (spec §12.4) —
#: re-stated here so the constant is available without importing the whole module.
EXECUTION_NOTE = "V1 does not execute this action; it requires human approval."


class ClusterDecisionKind(str, Enum):
    """The classification of one run of the Cluster Strategy stage (contract §3).

    This is NOT a lifecycle state and NOT persisted as a mutable status — a
    re-run overwrites the report (idempotent, D-CS-4).
    """

    MAP_TO_EXISTING = "MAP_TO_EXISTING"          # one of the 11 canonical clusters
    PROPOSE_NEW_CLUSTER = "PROPOSE_NEW_CLUSTER"  # hypothesis + hand-off to the owner (P6 deferred)
    DEFER = "DEFER"                              # needs P6 / more evidence / an ambiguity
    REJECT = "REJECT"                            # untenable cluster (HIGH compliance / none)


class TargetNextStage(str, Enum):
    """The recommended next pipeline action (contract §10). Still a recommendation
    — human-approved (I3, autonomy L1). NOT an opportunity lifecycle state."""

    PAGE_BLUEPRINT = "PAGE_BLUEPRINT"
    FORMALIZE_CLUSTER = "FORMALIZE_CLUSTER"
    BACK_TO_MARKET_INTELLIGENCE = "BACK_TO_MARKET_INTELLIGENCE"
    HOLD = "HOLD"


class ClusterDimensionKey(str, Enum):
    """The 4 qualitative Cluster Strategy dimensions (contract §11, D-CS-4).
    Order is significant. Each carries a rating + a SEPARATE confidence — no score."""

    CLUSTER_FIT = "cluster_fit"
    DIFFERENTIATION_WITHIN_CLUSTER = "differentiation_within_cluster"
    ASSET_READINESS = "asset_readiness"
    STRATEGIC_COHERENCE = "strategic_coherence"


#: contract §11 — the 4 dimension keys, in canonical order.
CLUSTER_DIMENSION_KEYS: List[str] = [d.value for d in ClusterDimensionKey]

#: contract §4.4 / §5 — asset id sentinels reused from the pipeline (spec §10.3, §15).
UNKNOWN = "UNKNOWN"
NEW_ASSET = "NEW_ASSET"
