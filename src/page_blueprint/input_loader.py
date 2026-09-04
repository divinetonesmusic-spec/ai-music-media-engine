"""Page Blueprint — input contract (contract §2).

Loads ONE ClusterStrategy sidecar (``reports/cluster-strategy/<opportunity_id>.json``
— already documented as Page Blueprint's future input contract, docs/CLUSTER-STRATEGY-V1.md),
decodes it with the shared codec, and requires
``recommendation.target_next_stage == PAGE_BLUEPRINT`` — the structural proof that
Cluster Strategy itself recommended proceeding here (mirrors the owner-advanced
gate Cluster Strategy applies to the Opportunity Report, one level down the
pipeline). Every failure is a hard failure — Page Blueprint never runs on a
DEFER/REJECT/not-yet-ready ClusterStrategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from cluster_strategy.schema.enums import ClusterDecisionKind, TargetNextStage
from cluster_strategy.schema.models import ClusterStrategy
from market_intelligence.io_utils import LoadError, read_json
from market_intelligence.schema.codec import CodecError, decode

from .schema.models import ClusterStrategySnapshot

_EXPECTED_SCHEMA_VERSION = "1.0.0"  # mirrors D-CS-11's pin, one stage further down


class PageBlueprintInputError(Exception):
    """The ClusterStrategy cannot enter Page Blueprint (wrong version, not
    recommended for this stage, malformed, or missing)."""


@dataclass
class LoadedInput:
    cluster_strategy: ClusterStrategy
    snapshot: ClusterStrategySnapshot
    sidecar_path: Path


def _snapshot(cs: ClusterStrategy, sidecar_ref: str) -> ClusterStrategySnapshot:
    sd = cs.strategic_definition
    cdir = cs.content_direction
    assert sd is not None and cdir is not None  # guaranteed by the gate check below
    d = cs.cluster_decision
    return ClusterStrategySnapshot(
        cluster_strategy_id=cs.cluster_strategy_id,
        cluster_strategy_ref=sidecar_ref,
        opportunity_id=cs.opportunity.opportunity_id,
        opportunity_run_id=cs.opportunity.opportunity_run_id,
        schema_version=cs.schema_version,
        cluster_id=d.cluster_id,
        cluster_name=d.cluster_name,
        subcluster_or_angle=d.subcluster_or_angle,
        central_concept=sd.central_concept,
        positioning_statement=sd.positioning_statement,
        editorial_promise=sd.editorial_promise,
        market=sd.market,
        language=sd.language,
        consumption_context=sd.consumption_context,
        music_relationship=cdir.music_relationship,
        first_content_direction=cdir.first_content_direction,
        editorial_angles=list(cdir.editorial_angles),
        overall_confidence=cs.evaluation.overall_confidence,
    )


def load_input(
    sidecar_path: Union[str, Path], *, project_root: Union[str, Path],
) -> LoadedInput:
    sidecar_path = Path(sidecar_path)
    root = Path(project_root)

    if not sidecar_path.is_file():
        raise PageBlueprintInputError(f"ClusterStrategy sidecar not found: {sidecar_path}")
    try:
        raw = read_json(sidecar_path)
    except LoadError as e:
        raise PageBlueprintInputError(str(e)) from e
    if not isinstance(raw, dict):
        raise PageBlueprintInputError(f"{sidecar_path}: not a JSON object")

    version = raw.get("schema_version")
    if version != _EXPECTED_SCHEMA_VERSION:
        raise PageBlueprintInputError(
            f"{sidecar_path}: ClusterStrategy schema_version is {version!r}; "
            f"Page Blueprint V1 pins to {_EXPECTED_SCHEMA_VERSION!r}"
        )

    try:
        cs = decode(ClusterStrategy, raw)
    except CodecError as e:
        raise PageBlueprintInputError(f"{sidecar_path}: {e}") from e

    if cs.cluster_decision.decision not in (
        ClusterDecisionKind.MAP_TO_EXISTING, ClusterDecisionKind.PROPOSE_NEW_CLUSTER
    ):
        raise PageBlueprintInputError(
            f"{cs.opportunity.opportunity_id}: cluster_decision is "
            f"{cs.cluster_decision.decision.value} — Page Blueprint requires "
            "MAP_TO_EXISTING or PROPOSE_NEW_CLUSTER (a DEFER/REJECT has no strategy to build on)"
        )
    if cs.strategic_definition is None or cs.asset_strategy is None or cs.content_direction is None:
        raise PageBlueprintInputError(
            f"{cs.opportunity.opportunity_id}: strategic_definition / asset_strategy / "
            "content_direction must all be present for this decision — malformed ClusterStrategy"
        )
    if cs.recommendation.target_next_stage != TargetNextStage.PAGE_BLUEPRINT:
        raise PageBlueprintInputError(
            f"{cs.opportunity.opportunity_id}: Cluster Strategy recommended "
            f"'{cs.recommendation.target_next_stage.value}', not 'PAGE_BLUEPRINT' — Page "
            "Blueprint runs only on a ClusterStrategy that recommends it (autonomy L1: the "
            "owner picks which ClusterStrategy sidecar to run this on, mirroring D-CS-3)"
        )

    try:
        sidecar_ref = str(sidecar_path.resolve().relative_to(root.resolve()))
    except ValueError:
        sidecar_ref = str(sidecar_path)

    return LoadedInput(
        cluster_strategy=cs,
        snapshot=_snapshot(cs, sidecar_ref),
        sidecar_path=sidecar_path,
    )
