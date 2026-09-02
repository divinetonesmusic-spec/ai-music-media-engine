"""Cluster Strategy — deterministic sequential driver (contract §14).

input_loader -> deterministic cluster pre-normalisation -> Claude strategy call
-> deterministic asset consolidation -> deterministic guardrail check
-> assemble -> validate -> render (+ optional registry link).

A hard failure (bad input, malformed model response, validation error) raises
``ClusterStrategyError`` — the owner re-runs. There is no silent "business state".
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from market_intelligence.guardrails import SCOPE_HYPOTHESES_DIRECTION, ComplianceResult
from market_intelligence.knowledge_loader import KnowledgeError, load_knowledge
from market_intelligence.schema.enums import (
    Confidence,
    Language,
    Market,
    Rating,
    RedFlagKind,
    Severity,
)
from market_intelligence.schema.models import RedFlag
from market_intelligence.schema.validate import blocking

from .asset_strategy import consolidate
from .guardrails import check_cluster_strategy_prose
from .input_loader import ClusterStrategyInputError, LoadedInput, load_input
from .llm import ResponseRejected, StageClient, StageError, select_client
from .mapping import _ID_TO_NAME, CANONICAL_IDS, load_taxonomy_markdown, normalize_cluster_value
from .registry_link import append_cluster_strategy_ref
from .reporting import write_report
from .schema.enums import SCHEMA_VERSION, ClusterDecisionKind, TargetNextStage
from .schema.models import (
    ClusterContentDirection,
    ClusterDecision,
    ClusterDimensionRating,
    ClusterEvaluation,
    ClusterRecommendation,
    ClusterStrategicDefinition,
    ClusterStrategy,
    ClusterStrategyProvenance,
    NewClusterProposal,
)
from .strategy import run_strategy

_CONF_RANK = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
_RANK_CONF = {v: k for k, v in _CONF_RANK.items()}


class ClusterStrategyError(Exception):
    """The Cluster Strategy run could not complete (spec §14 style — hard fail)."""


# The drafted content direction is a non-core HYPOTHESIS. When a HIGH-severity
# guardrail flags its scope, MI semantics say "strip the offending text and
# proceed" (not exclude). `first_content_direction` is a required string, so the
# strip replaces it with this note rather than blanking it (cf. MI setting the
# optional `Hypotheses.first_content_direction` to None).
_STRIPPED_DIRECTION_NOTE = (
    "[removed — a HIGH-severity compliance guardrail flagged the drafted content "
    "direction; Content Strategy (stage 5) must supply a compliant one]"
)


@dataclass
class ClusterStrategyRunResult:
    cluster_strategy: ClusterStrategy
    report_path: Path
    sidecar_path: Path
    registry_updated: bool = False
    llm_mode: str = "recorded"
    validation_warnings: List[str] = field(default_factory=list)


def _clamp_confidence(model_conf: str, ceiling: Confidence) -> Confidence:
    mc = Confidence(model_conf)
    return _RANK_CONF[min(_CONF_RANK[mc], _CONF_RANK[ceiling])]


_CARRIED_PREFIX = re.compile(r"^\[carried from the opportunity report\]\s*", re.IGNORECASE)
_GUARDRAIL_PREFIX = re.compile(r"^g\d\d\b[^:]*:\s*", re.IGNORECASE)


def _rf_key(description: str) -> str:
    """Dedup key for a red flag: an exact restatement collapses, a genuinely
    different flag does not. Only the wrappers the pipeline itself adds are
    stripped — the ``[carried ...]`` prefix and a leading ``GNN (scope):`` tag —
    then whitespace is collapsed and the text lower-cased. No fuzzy / substring
    matching (which risked dropping a distinct flag)."""
    s = _CARRIED_PREFIX.sub("", description.strip())
    s = _GUARDRAIL_PREFIX.sub("", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _red_flags(raw: dict, loaded: LoadedInput, compliance_flags: List[RedFlag]) -> List[RedFlag]:
    out: List[RedFlag] = []
    seen: set = set()

    def _add(rf: RedFlag) -> None:
        key = _rf_key(rf.description)
        if key in seen:
            return
        seen.add(key)
        out.append(rf)

    for rf in raw.get("red_flags", []):
        kind = rf["kind"]
        _add(RedFlag(
            description=rf["description"],
            severity=Severity(rf["severity"]),
            kind=RedFlagKind(kind) if kind in {k.value for k in RedFlagKind} else RedFlagKind.OTHER,
        ))
    # carry the opportunity's compliance flags that Claude did not restate
    for rf in loaded.opportunity.evaluation.red_flags:
        if rf.kind is RedFlagKind.COMPLIANCE:
            _add(RedFlag(description=f"[carried from the Opportunity Report] {rf.description}",
                         severity=rf.severity, kind=RedFlagKind.COMPLIANCE))
    for rf in compliance_flags:
        _add(rf)
    return out


def _new_cluster_proposal(raw_p: Optional[dict]) -> Optional[NewClusterProposal]:
    if not raw_p:
        return None
    return NewClusterProposal(
        proposed_id=raw_p["proposed_id"],
        proposed_name=raw_p["proposed_name"],
        concept=raw_p["concept"],
        boundary_vs_adjacent=dict(raw_p.get("boundary_vs_adjacent") or {}),
        why_not_subcluster=raw_p["why_not_subcluster"],
        supporting_evidence=list(raw_p.get("supporting_evidence") or []),
    )


def _assemble(
    raw: dict,
    loaded: LoadedInput,
    kb,
    *,
    config,
    generated_at: str,
    replay: bool,
    knowledge_snapshot: dict,
    compliance: ComplianceResult,
    forced_reject_reason: Optional[str],
) -> ClusterStrategy:
    snap = loaded.snapshot
    cd_raw = raw["cluster_decision"]
    decision = ClusterDecisionKind(cd_raw["decision"])
    if forced_reject_reason:
        decision = ClusterDecisionKind.REJECT

    _map = decision is ClusterDecisionKind.MAP_TO_EXISTING
    cluster_id = cd_raw.get("cluster_id") if _map else None
    cluster_decision = ClusterDecision(
        decision=decision,
        justification=cd_raw["justification"],
        framing_hypothesis_comparison=cd_raw["framing_hypothesis_comparison"],
        cluster_id=cluster_id,
        cluster_name=_ID_TO_NAME.get(cluster_id) if cluster_id else None,
        subcluster_or_angle=cd_raw.get("subcluster_or_angle") or None,
        is_new_subcluster=cd_raw.get("is_new_subcluster"),
        new_cluster_proposal=(
            _new_cluster_proposal(cd_raw.get("new_cluster_proposal"))
            if decision is ClusterDecisionKind.PROPOSE_NEW_CLUSTER else None
        ),
        deferral_reason=(cd_raw.get("deferral_reason")
                         if decision is ClusterDecisionKind.DEFER else None),
        rejection_reason=(
            forced_reject_reason or cd_raw.get("rejection_reason")
            if decision is ClusterDecisionKind.REJECT else None
        ),
    )

    has_strategy = decision in (
        ClusterDecisionKind.MAP_TO_EXISTING, ClusterDecisionKind.PROPOSE_NEW_CLUSTER
    )
    strategic_definition = asset_strategy = content_direction = None
    if has_strategy:
        sd = raw["strategic_definition"]
        strategic_definition = ClusterStrategicDefinition(
            central_concept=sd["central_concept"],
            audience_description=sd["audience_description"],
            intent=sd["intent"],
            emotional_state=sd["emotional_state"],
            consumption_context=snap.consumption_context,
            editorial_promise=sd["editorial_promise"],
            positioning_statement=sd["positioning_statement"],
            market=snap.market if isinstance(snap.market, Market) else Market(snap.market),
            language=(snap.language if isinstance(snap.language, Language)
                      else Language(snap.language)),
            localization_notes=sd["localization_notes"],
            durability_read=sd["durability_read"],
            strategic_coherence_note=sd["strategic_coherence_note"],
            audience_attributes=snap.audience_attributes,
        )
        asset_strategy = consolidate(loaded.opportunity, kb)
        cdir = raw["content_direction"]
        # MI guardrail semantics: a HIGH-severity hit in a NON-core scope strips
        # that scope's text and the run proceeds. `first_content_direction` and
        # `editorial_angles` both map to SCOPE_HYPOTHESES_DIRECTION, so a strip of
        # that scope blanks both.
        strip_direction = SCOPE_HYPOTHESES_DIRECTION in compliance.strip_scopes
        content_direction = ClusterContentDirection(
            first_content_direction=(
                _STRIPPED_DIRECTION_NOTE if strip_direction
                else cdir["first_content_direction"]
            ),
            music_relationship=cdir["music_relationship"],
            editorial_angles=[] if strip_direction else list(cdir.get("editorial_angles") or []),
        )

    open_questions = list(raw.get("open_questions") or [])
    # MI guardrail semantics: `require_uncertainty_statement` -> the scope needs an
    # explicit UNKNOWN / uncertainty note. Surface it where the owner / stage 4 see it.
    for scope in sorted(compliance.needs_uncertainty_note):
        open_questions.append(
            f"Compliance (G10): the {scope} text needs an explicit uncertainty / "
            "UNKNOWN statement before it is relied on."
        )

    evaluation = ClusterEvaluation(
        dimensions={
            k: ClusterDimensionRating(
                rating=Rating(v["rating"]),
                confidence=Confidence(v["confidence"]),
                justification=v["justification"],
                blocked_by=list(v["blocked_by"]) if v.get("blocked_by") else None,
            )
            for k, v in raw["dimensions"].items()
        },
        overall_confidence=_clamp_confidence(raw["overall_confidence"], snap.overall_confidence),
        red_flags=_red_flags(raw, loaded, compliance.red_flags),
        open_questions=open_questions,
    )

    next_stage = TargetNextStage(raw["recommendation"]["target_next_stage"])
    if forced_reject_reason:
        next_stage = TargetNextStage.HOLD
    recommendation = ClusterRecommendation(
        target_next_stage=next_stage,
        recommended_next_step=raw["recommendation"]["recommended_next_step"],
        opportunity_lifecycle_state=snap.status,  # the opportunity's real state, carried (I2)
        justification=(
            f"{raw['recommendation']['justification']} "
            f"(overridden to REJECT: {forced_reject_reason})" if forced_reject_reason
            else raw["recommendation"]["justification"]
        ),
    )

    return ClusterStrategy(
        cluster_strategy_id=f"cs_{snap.opportunity_id}",
        schema_version=SCHEMA_VERSION,
        opportunity=snap,
        owner_authorization=loaded.owner_authorization,
        cluster_decision=cluster_decision,
        strategic_definition=strategic_definition,
        asset_strategy=asset_strategy,
        content_direction=content_direction,
        evaluation=evaluation,
        recommendation=recommendation,
        provenance=ClusterStrategyProvenance(
            run_id=config.run_id,
            schema_version=SCHEMA_VERSION,
            model=config.model,
            prompt_version=config.prompt_version,
            generated_at=generated_at,
            replay=replay,
            signal_ids=list(loaded.opportunity.provenance.signal_ids),
            sources=list(loaded.opportunity.provenance.sources),
            knowledge_snapshot=knowledge_snapshot,
        ),
    )


def _prose_for_compliance(raw: dict) -> Dict[str, object]:
    prose: Dict[str, object] = {}
    sd = raw.get("strategic_definition") or {}
    for k in ("central_concept", "intent", "emotional_state", "editorial_promise",
              "positioning_statement", "localization_notes", "strategic_coherence_note",
              "durability_read"):
        if sd.get(k):
            prose[k] = sd[k]
    cdir = raw.get("content_direction") or {}
    if cdir.get("first_content_direction"):
        prose["first_content_direction"] = cdir["first_content_direction"]
    if cdir.get("editorial_angles"):
        prose["editorial_angles"] = cdir["editorial_angles"]
    if cdir.get("music_relationship"):
        prose["music_relationship"] = cdir["music_relationship"]
    cd = raw.get("cluster_decision") or {}
    prose["cluster_decision_justification"] = cd.get("justification", "")
    prose["framing_hypothesis_comparison"] = cd.get("framing_hypothesis_comparison", "")
    p = cd.get("new_cluster_proposal") or {}
    if p.get("concept"):
        prose["new_cluster_concept"] = p["concept"]
    if p.get("why_not_subcluster"):
        prose["new_cluster_why_not_subcluster"] = p["why_not_subcluster"]
    prose["recommendation_justification"] = (
        (raw.get("recommendation") or {}).get("justification", ""))
    return prose


def run_cluster_strategy(
    sidecar_path: Union[str, Path],
    *,
    config,
    project_root: Union[str, Path],
    review_md_path: Optional[Union[str, Path]] = None,
    client: Optional[StageClient] = None,
    now: Optional[str] = None,
) -> ClusterStrategyRunResult:
    root = Path(project_root)
    generated_at = now or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        loaded = load_input(sidecar_path, review_md_path=review_md_path, project_root=root)
    except ClusterStrategyInputError as e:
        raise ClusterStrategyError(str(e)) from e

    try:
        kb = load_knowledge(config.paths, project_root=root)
    except KnowledgeError as e:
        raise ClusterStrategyError(f"knowledge base failed to load: {e}") from e

    taxonomy_md = load_taxonomy_markdown(root)
    hint = normalize_cluster_value(loaded.snapshot.potential_cluster_value, CANONICAL_IDS)

    stage_client, mode = select_client(
        replay_enabled=config.replay.enabled,
        replay_llm=config.replay.llm,
        replay_fixture_path=config.replay.fixture_path,
        project_root=root,
        client=client,
    )
    try:
        raw = run_strategy(
            loaded.snapshot, loaded.opportunity,
            taxonomy_markdown=taxonomy_md, guardrails=kb.guardrails,
            cluster_hint=hint, client=stage_client, model=config.model,
        )
    except (ResponseRejected, StageError) as e:
        raise ClusterStrategyError(f"the strategy model call failed: {e}") from e

    # deterministic guardrail check (MI semantics, contract §9):
    #   * exclude_opportunity (HIGH hit in core content)  -> forced REJECT
    #   * strip_scopes        (HIGH hit in a hypothesis)  -> blank that scope, proceed
    #   * needs_uncertainty_note                          -> add an open question
    compliance = check_cluster_strategy_prose(_prose_for_compliance(raw), guardrails=kb.guardrails)
    forced_reject = (
        "a HIGH-severity compliance guardrail is violated by the cluster's core "
        "editorial content and cannot be reframed without abandoning the concept"
        if compliance.exclude_opportunity else None
    )

    knowledge_snapshot = {
        "taxonomy_canonical_count": len(kb.clusters),
        "guardrails_count": len(kb.guardrails),
        "inventory": {
            "artists": len(kb.artists), "playlists": len(kb.playlists),
            "pages": len(kb.pages), "catalog": len(kb.catalog),
        },
        "opportunity_report_replay": bool(loaded.opportunity.provenance.replay),
    }
    replay = bool(config.replay.enabled) or bool(loaded.opportunity.provenance.replay)

    cs = _assemble(
        raw, loaded, kb, config=config, generated_at=generated_at, replay=replay,
        knowledge_snapshot=knowledge_snapshot, compliance=compliance,
        forced_reject_reason=forced_reject,
    )

    from .schema.validate import validate_cluster_strategy
    errs = validate_cluster_strategy(
        cs, canonical_cluster_ids=CANONICAL_IDS, inventory=kb.inventory
    )
    blockers = blocking(errs)
    if blockers:
        detail = "; ".join(f"[{e.code}] {e.message}" for e in blockers[:5])
        raise ClusterStrategyError(f"the assembled Cluster Strategy is invalid: {detail}")

    report_path, sidecar = write_report(cs, config=config, project_root=root)

    registry_updated = False
    if config.write_registry_link:
        registry_updated = append_cluster_strategy_ref(
            cs, config=config, project_root=root, generated_at=generated_at,
        )

    return ClusterStrategyRunResult(
        cluster_strategy=cs,
        report_path=report_path,
        sidecar_path=sidecar,
        registry_updated=registry_updated,
        llm_mode=mode,
        validation_warnings=[f"[{e.code}] {e.message}" for e in errs if e.severity != "ERROR"],
    )
