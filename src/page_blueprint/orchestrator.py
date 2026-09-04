"""Page Blueprint — deterministic sequential driver (contract §8).

input_loader -> business-dna §9 extraction -> Claude blueprint call -> deterministic
confidence clamping (ceiling + Musical-DNA cap) -> deterministic guardrail check ->
assemble -> validate -> render.

A hard failure (bad input, malformed model response, validation error) raises
``PageBlueprintError`` — the owner re-runs. A HIGH-severity compliance violation in
core content is not a crash: it forces ``recommendation.target_next_stage = HOLD``
and the run still writes a report (mirrors Cluster Strategy's forced-REJECT
semantics, spec §14 "technical failure != business state").
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from market_intelligence.guardrails import SCOPE_HYPOTHESES_DIRECTION, ComplianceResult
from market_intelligence.knowledge_loader import KnowledgeError, load_knowledge
from market_intelligence.schema.enums import Confidence
from market_intelligence.schema.validate import WARNING, blocking

from . import musical_dna
from .blueprint import ResponseRejected, StageClient, StageError, run_blueprint
from .config import PageBlueprintConfig
from .guardrails import check_page_blueprint_prose
from .input_loader import LoadedInput, PageBlueprintInputError, load_input
from .llm import select_client
from .reporting import write_report
from .schema.enums import SCHEMA_VERSION, PageBlueprintTargetNextStage
from .schema.models import (
    PageAssetLink,
    PageBlueprint,
    PageBlueprintEvaluation,
    PageBlueprintProvenance,
    PageBlueprintRecommendation,
    PageContentFraming,
    PageIdentity,
    VisualIdentity,
)
from .schema.validate import validate_page_blueprint

_CONF_RANK = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
_RANK_CONF = {v: k for k, v in _CONF_RANK.items()}

_STRIPPED_PILLARS_NOTE = (
    "[removed — a HIGH-severity compliance guardrail flagged the drafted content "
    "pillars; Content Strategy (stage 5) must supply compliant ones]"
)
_FORCED_HOLD_REASON = (
    "a HIGH-severity compliance guardrail is violated by the page's core editorial "
    "content (positioning/bio/visual identity/tone of voice) and cannot be reframed "
    "without abandoning the concept"
)


class PageBlueprintError(Exception):
    """The Page Blueprint run could not complete (spec §14 style — hard fail)."""


@dataclass
class PageBlueprintRunResult:
    page_blueprint: PageBlueprint
    report_path: Path
    sidecar_path: Path
    llm_mode: str = "recorded"
    validation_warnings: List[str] = field(default_factory=list)


def _clamp_confidence(model_conf: str, ceiling: Confidence) -> Confidence:
    mc = Confidence(model_conf)
    return _RANK_CONF[min(_CONF_RANK[mc], _CONF_RANK[ceiling])]


def _page_context(loaded: LoadedInput) -> dict:
    a = loaded.cluster_strategy.asset_strategy
    assert a is not None  # guaranteed by the input gate
    return {
        "page_strategy": {
            "primary_page_id": a.page_strategy.primary_page_id,
            "page_fit_basis": a.page_strategy.page_fit_basis,
            "note": a.page_strategy.note,
            "new_page_recommended": a.page_strategy.new_page_recommendation is not None,
        },
        "primary_playlist_id": a.playlist_strategy.primary_playlist_id,
        "primary_artist_id": a.artist_strategy.best_artist_id,
    }


def _prose_for_compliance(raw: dict) -> Dict[str, object]:
    ident = raw.get("identity", {})
    vis = raw.get("visual_identity", {})
    cf = raw.get("content_framing", {})
    rec = raw.get("recommendation", {})
    return {
        "concept_name": ident.get("concept_name"),
        "positioning_statement": ident.get("positioning_statement"),
        "bio": ident.get("bio"),
        "visual_language": vis.get("visual_language"),
        "tone_of_voice": vis.get("tone_of_voice"),
        "posting_cadence": cf.get("posting_cadence"),
        "content_pillars": cf.get("content_pillars", []),
        "recommendation_justification": rec.get("justification"),
    }


def _assemble(
    raw: dict, loaded: LoadedInput, *, config: PageBlueprintConfig, generated_at: str,
    replay: bool, knowledge_snapshot: dict, compliance: ComplianceResult,
    musical_dna_needs_input: bool,
) -> PageBlueprint:
    ident = raw["identity"]
    vis = raw["visual_identity"]
    cf = raw["content_framing"]
    ev = raw["evaluation"]
    rec = raw["recommendation"]
    cs = loaded.cluster_strategy
    a = cs.asset_strategy
    assert a is not None

    pillars = list(cf["content_pillars"])
    if SCOPE_HYPOTHESES_DIRECTION in compliance.strip_scopes:
        pillars = [_STRIPPED_PILLARS_NOTE]

    confidence = _clamp_confidence(ev["overall_confidence"], loaded.snapshot.overall_confidence)
    blocked_by = list(ev.get("blocked_by") or [])
    if musical_dna_needs_input and confidence is Confidence.HIGH:
        confidence = Confidence.MEDIUM
        if "musical DNA (NEEDS_INPUT)" not in blocked_by:
            blocked_by.append("musical DNA (NEEDS_INPUT)")

    red_flags = list(compliance.red_flags)
    for rf_raw in raw.get("red_flags", []):
        from market_intelligence.schema.codec import decode as _decode
        from market_intelligence.schema.models import RedFlag as _RedFlag
        rf = _decode(_RedFlag, rf_raw)
        if rf.description not in {x.description for x in red_flags}:
            red_flags.append(rf)

    target_next_stage = PageBlueprintTargetNextStage(rec["target_next_stage"])
    recommended_next_step = rec["recommended_next_step"]
    rec_justification = rec["justification"]
    if compliance.exclude_opportunity:
        target_next_stage = PageBlueprintTargetNextStage.HOLD
        recommended_next_step = "Hold — resolve the compliance violation before Content Strategy."
        rec_justification = _FORCED_HOLD_REASON

    return PageBlueprint(
        page_blueprint_id=f"pb_{cs.opportunity.opportunity_id}",
        schema_version=SCHEMA_VERSION,
        cluster_strategy=loaded.snapshot,
        identity=PageIdentity(
            concept_name=ident["concept_name"],
            positioning_statement=ident["positioning_statement"],
            bio=ident["bio"],
        ),
        visual_identity=VisualIdentity(
            visual_language=vis["visual_language"],
            tone_of_voice=vis["tone_of_voice"],
            musical_dna_expression_used=vis["musical_dna_expression_used"],
        ),
        asset_link=PageAssetLink(
            page_strategy=a.page_strategy,
            primary_playlist_id=a.playlist_strategy.primary_playlist_id,
            primary_artist_id=a.artist_strategy.best_artist_id,
        ),
        content_framing=PageContentFraming(
            content_pillars=pillars,
            platforms=list(cf["platforms"]),
            posting_cadence=cf["posting_cadence"],
        ),
        evaluation=PageBlueprintEvaluation(
            overall_confidence=confidence,
            justification=ev["justification"],
            red_flags=red_flags,
            blocked_by=blocked_by,
        ),
        recommendation=PageBlueprintRecommendation(
            target_next_stage=target_next_stage,
            recommended_next_step=recommended_next_step,
            justification=rec_justification,
        ),
        provenance=PageBlueprintProvenance(
            run_id=config.run_id,
            schema_version=SCHEMA_VERSION,
            model=config.model,
            prompt_version=config.prompt_version,
            generated_at=generated_at,
            replay=replay,
            signal_ids=list(cs.provenance.signal_ids),
            sources=list(cs.provenance.sources),
            knowledge_snapshot=knowledge_snapshot,
        ),
    )


def run_page_blueprint(
    cluster_strategy_sidecar: Union[str, Path],
    *,
    config: PageBlueprintConfig,
    project_root: Union[str, Path],
    client: Optional[StageClient] = None,
    generated_at: Optional[str] = None,
) -> PageBlueprintRunResult:
    root = Path(project_root)
    try:
        loaded = load_input(cluster_strategy_sidecar, project_root=root)
    except PageBlueprintInputError as e:
        raise PageBlueprintError(str(e)) from e

    try:
        kb = load_knowledge(config.paths, project_root=root)
    except KnowledgeError as e:
        raise PageBlueprintError(f"knowledge could not be loaded: {e}") from e

    needs_input = musical_dna.musical_dna_needs_input(kb.business_dna_body)
    section_9 = musical_dna.extract_section_9(kb.business_dna_body)
    hint = musical_dna.extract_cluster_expression_hint(section_9, loaded.snapshot.cluster_name)

    stage_client, llm_mode = select_client(
        replay_enabled=config.replay.enabled,
        replay_llm=config.replay.llm,
        replay_fixture_path=config.replay.fixture_path,
        project_root=root,
        client=client,
    )
    try:
        raw = run_blueprint(
            loaded.snapshot,
            section_9_markdown=section_9,
            cluster_expression_hint=hint,
            guardrails=kb.guardrails,
            page_context=_page_context(loaded),
            musical_dna_needs_input=needs_input,
            client=stage_client,
            model=config.model,
        )
    except (ResponseRejected, StageError) as e:
        raise PageBlueprintError(f"the blueprint model call failed: {e}") from e

    compliance = check_page_blueprint_prose(_prose_for_compliance(raw), guardrails=kb.guardrails)

    knowledge_snapshot = {
        "guardrails_count": len(kb.guardrails),
        "musical_dna_needs_input": needs_input,
        "cluster_strategy_replay": bool(loaded.cluster_strategy.provenance.replay),
    }
    generated_at = generated_at or _dt.datetime.now(_dt.timezone.utc).isoformat()
    replay = bool(config.replay.enabled) or bool(loaded.cluster_strategy.provenance.replay)

    pb = _assemble(
        raw, loaded, config=config, generated_at=generated_at, replay=replay,
        knowledge_snapshot=knowledge_snapshot, compliance=compliance,
        musical_dna_needs_input=needs_input,
    )

    errs = validate_page_blueprint(
        pb, cluster_strategy_overall_confidence=loaded.snapshot.overall_confidence,
        inventory=kb.inventory, musical_dna_needs_input=needs_input,
    )
    hard = blocking(errs)
    if hard:
        reasons = "; ".join(f"[{e.code}] {e.message}" for e in hard)
        raise PageBlueprintError(f"Page Blueprint failed validation: {reasons}")
    warnings = [f"[{e.code}] {e.message}" for e in errs if e.severity == WARNING]

    report_path, sidecar_path = write_report(
        pb, reports_dir=root / config.reports_subdir,
    )

    return PageBlueprintRunResult(
        page_blueprint=pb, report_path=report_path, sidecar_path=sidecar_path,
        llm_mode=llm_mode, validation_warnings=warnings,
    )
