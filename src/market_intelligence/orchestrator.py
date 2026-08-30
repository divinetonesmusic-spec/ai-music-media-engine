"""Orchestrator — spec §5, §18 (Orchestrator row), §14.

Deterministic sequential driver. Calls each component in order and passes their
typed outputs on. Components never call each other (§18). Hard failures
(missing knowledge, all signal sources down) propagate; per-source degradation
and per-opportunity exclusions are collected and surfaced in the digest.

    preflight
      → 1. Signal Collection
      → 2. Signal Normalization
      → 3. Analysis / Framing            (dry_run stops here)
      → 4. Asset Matching
      → 5. Evaluation
      → 6. Ranking / Prioritization
      → 7. Report Generation (+ digest + review)
      → Registry update
"""

from __future__ import annotations

import datetime as _dt
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

from .collect.base import CollectionResult, SignalCollectionError
from .collect.runner import run_collection
from .config.loader import ConfigError, load_dedup_config, load_ranking_config
from .evaluation import EvaluationResult, evaluate_opportunities
from .framing import FramingResult, frame_signals
from .io_utils import write_text
from .llm_stage import StageClient, StageError
from .matching import MatchingResult, match_assets
from .normalize.llm import NormalizationClient
from .normalize.runner import NormalizationRunResult, run_normalization
from .preflight import PreflightError, preflight
from .ranking import RankingResult, rank_opportunities
from .registry import RegistryUpdateResult, update_registry
from .reporting import ReportingResult, generate_reports
from .schema.models import RunConfig


class OrchestratorError(Exception):
    """The run could not start or a stage hard-failed (spec §14)."""


@dataclass
class RunResult:
    run_id: str
    reports_dir: Path
    collection: CollectionResult
    normalization: NormalizationRunResult
    framing: FramingResult
    matching: Optional[MatchingResult] = None
    evaluation: Optional[EvaluationResult] = None
    ranking: Optional[RankingResult] = None
    reporting: Optional[ReportingResult] = None
    registry: Optional[RegistryUpdateResult] = None
    dry_run: bool = False
    timings: Dict[str, float] = field(default_factory=dict)
    replay: bool = False

    @property
    def presented_ids(self):
        return list(self.reporting.opportunities) if self.reporting else []


def _musical_dna_needs_input(business_dna_body: str) -> bool:
    idx = business_dna_body.find("Music DNA")
    if idx == -1:
        return True
    window = business_dna_body[idx: idx + 800]
    return "NEEDS INPUT" in window or "NEEDS_INPUT" in window


def _write_run_log(result: RunResult, root: Path, cfg, generated_at: str) -> None:
    """``data/<run_id>/run.log`` — every warning / degradation / exclusion (spec §14, §6.6)."""
    lines: List[str] = [f"# run.log — {cfg.run_id} — {generated_at}", ""]

    det = result.normalization.deterministic
    lines.append(f"[normalization] {len(det.invalid_signals)} invalid signal(s) dropped:")
    for iv in det.invalid_signals:
        codes = ", ".join(e["code"] for e in iv.errors)
        lines.append(f"  - {iv.signal_id}: {codes}")
    lines.append(f"[normalization] {len(det.discarded_signal_ids)} signal(s) removed by dedup: "
                 f"{', '.join(det.discarded_signal_ids) or '(none)'}")
    for c in result.normalization.llm.changes:
        if c.rejection_reason:
            reason = c.rejection_reason
            if "no normalization fixture" in reason or "fixture at" in reason:
                reason = "SN-2 fixture absent (replay) — conservative values kept"
            lines.append(f"[normalization] {c.signal_id}: {reason}")

    lines.append("")
    lines.append(f"[framing] {len(result.framing.dropped)} candidate(s) not turned into "
                 f"opportunities (spec §7.1):")
    for d in result.framing.dropped:
        lines.append(f"  - {d.title!r}: {d.reason}")

    if result.matching:
        lines.append("")
        lines.append(f"[asset_matching] {len(result.matching.warnings)} warning(s):")
        for w in result.matching.warnings:
            lines.append(f"  - {w.opportunity_id}: [{w.error.code}] {w.error.message}")

    if result.evaluation:
        excl = [b for b in result.evaluation.bundles.values() if b.excluded]
        lines.append("")
        lines.append(f"[evaluation] {len(excl)} opportunity(ies) excluded:")
        for b in excl:
            lines.append(f"  - {b.opportunity_id}: {b.exclusion_reason}")

    if result.ranking:
        lines.append("")
        lines.append(f"[ranking] {len(result.ranking.excluded)} hard-excluded:")
        for r in result.ranking.ordered:
            if r.bucket == "excluded":
                lines.append(f"  - {r.opportunity_id}: {r.exclusion_reason}")

    if result.reporting and result.reporting.excluded_at_report:
        lines.append("")
        lines.append(f"[reporting] {len(result.reporting.excluded_at_report)} opportunity(ies) "
                     f"failed validation and were excluded:")
        for oid, reason in result.reporting.excluded_at_report.items():
            lines.append(f"  - {oid}: {reason}")

    write_text(root / cfg.paths.data_dir / cfg.run_id / "run.log", "\n".join(lines))


def run_pipeline(
    config: Union[str, Path, RunConfig],
    *,
    project_root: Union[str, Path],
    now: Optional[_dt.datetime] = None,
    stage_client: Optional[StageClient] = None,
    normalization_client: Optional[NormalizationClient] = None,
) -> RunResult:
    root = Path(project_root)
    moment = now or _dt.datetime.now(_dt.timezone.utc)
    generated_at = moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    timings: Dict[str, float] = {}

    def _timed(name, fn):
        start = time.perf_counter()
        out = fn()
        timings[name] = round(time.perf_counter() - start, 4)
        return out

    # --- preflight -------------------------------------------------
    try:
        pf = preflight(config, project_root=root, strict=True)
    except PreflightError as e:
        raise OrchestratorError(f"preflight failed: {e}") from e
    cfg = pf.config
    knowledge = pf.knowledge
    replay = bool(cfg.replay.enabled)

    try:
        dedup_config = load_dedup_config(
            project_root=root, path=cfg.paths.dedup_config_path
        )
        ranking_config = load_ranking_config(
            project_root=root, path=cfg.paths.ranking_config_path
        )
    except ConfigError as e:
        raise OrchestratorError(f"configuration error: {e}") from e

    # --- 1. Signal Collection ------------------------------------
    try:
        collection = _timed("collection", lambda: run_collection(
            cfg, project_root=root, now=lambda: moment
        ))
    except SignalCollectionError as e:
        raise OrchestratorError(f"Signal Collection failed — every source failed: {e}") from e

    # --- 2. Signal Normalization --------------------------------
    normalization = _timed("normalization", lambda: run_normalization(
        collection.signals, config=cfg, project_root=root,
        dedup_config=dedup_config, client=normalization_client,
    ))
    signals = normalization.signals

    # --- 3. Analysis / Framing ---------------------------------
    try:
        framing = _timed("framing", lambda: frame_signals(
            signals, knowledge=knowledge, config=cfg, project_root=root,
            client=stage_client, now=f"{cfg.run_date}T00:00:00Z",
        ))
    except StageError as e:
        raise OrchestratorError(f"Analysis / Framing could not run: {e}") from e

    collection_summary = {
        "sources_used": collection.sources_used,
        "sources_failed": collection.sources_failed,
    }

    result = RunResult(
        run_id=cfg.run_id,
        reports_dir=root / cfg.paths.reports_dir / cfg.run_id,
        collection=collection,
        normalization=normalization,
        framing=framing,
        dry_run=bool(cfg.dry_run),
        timings=timings,
        replay=replay,
    )
    if cfg.dry_run:
        _write_run_log(result, root, cfg, generated_at)
        return result  # TECHNICAL DEFAULT — dry_run stops after Framing (§20.1)

    framed_by_id = {o.opportunity_id: o for o in framing.opportunities}

    # --- 4. Asset Matching ------------------------------------
    matching = _timed("matching", lambda: match_assets(
        framing.opportunities, knowledge=knowledge, config=cfg,
        project_root=root, client=stage_client,
    ))
    result.matching = matching

    # --- 5. Evaluation ---------------------------------------
    musical_dna_ni = _musical_dna_needs_input(knowledge.business_dna_body)
    evaluation = _timed("evaluation", lambda: evaluate_opportunities(
        framing.opportunities, matching.matches, knowledge=knowledge, config=cfg,
        project_root=root, client=stage_client, musical_dna_needs_input=musical_dna_ni,
    ))
    result.evaluation = evaluation

    # --- 6. Ranking -----------------------------------------
    ranking = _timed("ranking", lambda: rank_opportunities(
        framing.opportunities, evaluation.bundles,
        ranking_config=ranking_config, max_presented=cfg.max_opportunities_presented,
    ))
    result.ranking = ranking

    # --- 7. Report Generation ------------------------------
    reporting = _timed("reporting", lambda: generate_reports(
        ranking, framed_by_id, matching.matches, evaluation.bundles,
        signals=signals, knowledge=knowledge, run_config=cfg, project_root=root,
        collection_summary=collection_summary,
        counts_extra={
            "timings_seconds": timings,
            "framing_candidates_dropped": len(framing.dropped),
            "asset_match_warnings": len(matching.warnings),
        },
        generated_at=generated_at, replay=replay,
        musical_dna_needs_input=musical_dna_ni,
    ))
    result.reporting = reporting

    # --- Registry update ----------------------------------
    registry = _timed("registry", lambda: update_registry(
        reporting.opportunities, ranking, framed_by_id,
        run_config=cfg, project_root=root, generated_at=generated_at, replay=replay,
    ))
    result.registry = registry

    _write_run_log(result, root, cfg, generated_at)
    return result
