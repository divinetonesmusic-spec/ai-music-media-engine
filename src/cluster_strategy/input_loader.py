"""Cluster Strategy — input contract (contract §2).

Loads ONE Opportunity Report sidecar (``reports/<run_id>/<opportunity_id>.json`` —
spec §23 names it the contract), decodes it with the shared codec, and proves it
was owner-advanced in that run's ``review.md``. Every failure is a hard failure —
Cluster Strategy never runs on an un-advanced, wrong-version, or evidence-thin
opportunity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from market_intelligence.gate import GateError, parse_review
from market_intelligence.io_utils import LoadError, read_json, read_yaml_front_matter
from market_intelligence.schema.codec import CodecError, decode
from market_intelligence.schema.enums import EvidenceType
from market_intelligence.schema.models import Opportunity

from .schema.models import OpportunitySnapshot, OwnerAuthorization

_EXPECTED_SCHEMA_VERSION = "1.0.0"  # D-CS-11 — pin; hard-fail on any other value


class ClusterStrategyInputError(Exception):
    """The Opportunity Report cannot enter Cluster Strategy (wrong version, not
    advanced, no OBSERVED evidence, malformed, or missing)."""


@dataclass
class LoadedInput:
    opportunity: Opportunity
    snapshot: OpportunitySnapshot
    owner_authorization: OwnerAuthorization
    sidecar_path: Path
    review_md_path: Path


def _snapshot(opp: Opportunity, sidecar_ref: str) -> OpportunitySnapshot:
    pc = opp.hypotheses.potential_cluster if opp.hypotheses else None
    return OpportunitySnapshot(
        opportunity_id=opp.opportunity_id,
        opportunity_run_id=opp.run_id,
        opportunity_report_ref=sidecar_ref,
        schema_version=opp.schema_version,
        title=opp.title,
        need=opp.need,
        audience_description=opp.audience.description,
        audience_attributes=opp.audience.attributes,
        market=opp.market,
        language=opp.language,
        platform=opp.platform.value,
        consumption_context=opp.consumption_context,
        durability=opp.durability,
        urgency=opp.urgency,
        overall_confidence=opp.evaluation.overall_confidence,
        status=opp.status,  # the opportunity's ACTUAL lifecycle state — carried unchanged (I2)
        target_state=opp.recommendation.target_state,  # the MI recommendation — context only
        potential_cluster_value=pc.value if pc else None,
        potential_cluster_canonical=pc.canonical if pc else None,
        potential_cluster_basis=pc.basis if pc else None,
    )


def load_input(
    sidecar_path: Union[str, Path],
    *,
    review_md_path: Optional[Union[str, Path]] = None,
    project_root: Union[str, Path],
) -> LoadedInput:
    sidecar_path = Path(sidecar_path)
    root = Path(project_root)

    if not sidecar_path.is_file():
        raise ClusterStrategyInputError(f"Opportunity Report sidecar not found: {sidecar_path}")
    try:
        raw = read_json(sidecar_path)
    except LoadError as e:
        raise ClusterStrategyInputError(str(e)) from e
    if not isinstance(raw, dict):
        raise ClusterStrategyInputError(f"{sidecar_path}: not a JSON object")

    version = raw.get("schema_version")
    if version != _EXPECTED_SCHEMA_VERSION:
        raise ClusterStrategyInputError(
            f"{sidecar_path}: Opportunity Report schema_version is {version!r}; "
            f"Cluster Strategy V1 pins to {_EXPECTED_SCHEMA_VERSION!r} (D-CS-11)"
        )

    try:
        opp = decode(Opportunity, raw)
    except CodecError as e:
        raise ClusterStrategyInputError(f"{sidecar_path}: {e}") from e

    if not any(e.type is EvidenceType.OBSERVED for e in opp.evidence):
        raise ClusterStrategyInputError(
            f"{opp.opportunity_id}: no OBSERVED evidence item — Cluster Strategy "
            "requires >= 1 (contract §2.1, mirrors ranking §11.1)"
        )

    review_path = (
        Path(review_md_path) if review_md_path is not None
        else sidecar_path.parent / "review.md"
    )
    if not review_path.is_file():
        raise ClusterStrategyInputError(
            f"{opp.opportunity_id}: run review not found at {review_path} — "
            "cannot confirm the owner advanced this opportunity (contract §2.2)"
        )
    try:
        review = parse_review(review_path)
        review_fm, _ = read_yaml_front_matter(review_path)
    except (GateError, LoadError) as e:
        raise ClusterStrategyInputError(str(e)) from e
    if review.advanced_opportunity_id != opp.opportunity_id:
        raise ClusterStrategyInputError(
            f"{opp.opportunity_id}: not marked `advance` in {review_path} "
            f"(advanced_opportunity_id = {review.advanced_opportunity_id!r}). "
            "Cluster Strategy runs only on an owner-advanced opportunity (autonomy L1)."
        )

    try:
        sidecar_ref = str(sidecar_path.resolve().relative_to(root.resolve()))
    except ValueError:
        sidecar_ref = str(sidecar_path)

    return LoadedInput(
        opportunity=opp,
        snapshot=_snapshot(opp, sidecar_ref),
        owner_authorization=OwnerAuthorization(
            review_md_ref=str(review_path),
            advanced_opportunity_id=opp.opportunity_id,
            reviewer=(str(review_fm.get("reviewer")).strip() or None)
            if review_fm.get("reviewer") else None,
            review_date=str(review_fm["review_date"]) if review_fm.get("review_date") else None,
        ),
        sidecar_path=sidecar_path,
        review_md_path=review_path,
    )
