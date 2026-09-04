"""Controlled vocabularies for Page Blueprint V1 (canonical pipeline stage 4).

Only two enums are introduced here; everything else (``Rating``, ``Confidence``,
``Severity``, ``RedFlagKind``, ``Market``, ``Language``) is reused verbatim from
``market_intelligence.schema.enums`` so stage 4 speaks the same vocabulary as
stages 1–3. Asset decisions (``NewAssetRecommendation``) and the page/playlist/
artist strategy types are reused verbatim from ``cluster_strategy.schema.models``
— Page Blueprint never re-decides them (D-PB-3).

No 0–100 score anywhere (C6).
"""

from __future__ import annotations

from enum import Enum

SCHEMA_VERSION = "1.0.0"

#: Verbatim from ``market_intelligence.schema.models.EXECUTION_NOTE`` (spec §12.4) /
#: ``cluster_strategy.schema.enums.EXECUTION_NOTE`` — re-stated so the constant is
#: available without importing the whole upstream module.
EXECUTION_NOTE = "V1 does not execute this action; it requires human approval."


class PageBlueprintTargetNextStage(str, Enum):
    """The recommended next pipeline action (contract §7). Still a recommendation
    — human-approved (I3, autonomy L1). Content Strategy (stage 5) stays DEFERRED
    under P4 regardless of this value; it never triggers execution."""

    CONTENT_STRATEGY = "CONTENT_STRATEGY"
    BACK_TO_CLUSTER_STRATEGY = "BACK_TO_CLUSTER_STRATEGY"
    HOLD = "HOLD"
