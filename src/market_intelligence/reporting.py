"""Report Generation — spec §12, §16, §18 component 7, §19.

Deterministic. Assembles a full ``Opportunity`` from the framed opportunity + its
``AssetMatch`` + its ``EvaluationBundle`` + its rank, runs the §13 opportunity
validator, then renders:

* ``reports/<run_id>/<opportunity_id>.md``  — 9 sections + YAML front matter (§12.2/§12.3)
* ``reports/<run_id>/<opportunity_id>.json`` — the structured record (sidecar)
* ``reports/<run_id>/digest.md``             — the run digest (§12.5)
* ``reports/<run_id>/review.md``             — the owner review-gate template (§21.1)

Observed facts, inferences and hypotheses are visually separated (§12.3); missing
information is rendered ``UNKNOWN`` / ``NEEDS_INPUT``, never omitted or guessed.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import yaml

from .evaluation import EvaluationBundle
from .framing import FramedOpportunity
from .guardrails import (
    SCOPE_HYPOTHESES_DIRECTION,
    SCOPE_HYPOTHESES_HOOK,
    SCOPE_HYPOTHESES_POSITIONING,
)
from .io_utils import write_json, write_text
from .knowledge_loader import KnowledgeBundle
from .ranking import RankingResult
from .schema.codec import encode
from .schema.enums import EvidenceType
from .schema.models import (
    Hypotheses,
    Opportunity,
    OpportunityProvenance,
    Provenance,
    RunConfig,
    Signal,
    StateChange,
)
from .schema.validate import InventoryIndex, blocking, validate_opportunity

SCHEMA_VERSION = "1.0.0"
_STRIP_FIELD = {
    SCOPE_HYPOTHESES_POSITIONING: "potential_positioning",
    SCOPE_HYPOTHESES_DIRECTION: "first_content_direction",
    SCOPE_HYPOTHESES_HOOK: "hook",
}


@dataclass
class ReportingResult:
    opportunities: Dict[str, Opportunity]        # assembled, validated, presented set
    report_paths: Dict[str, Path] = field(default_factory=dict)
    sidecar_paths: Dict[str, Path] = field(default_factory=dict)
    digest_path: Optional[Path] = None
    review_path: Optional[Path] = None
    opportunities_json_path: Optional[Path] = None
    excluded_at_report: Dict[str, str] = field(default_factory=dict)
    needs_input_notes: List[str] = field(default_factory=list)


def _partial_record(oid, bucket, framed, bundles, asset_matches, reason):
    """A compact structured record for a parked / excluded opportunity (§17)."""
    fo = framed.get(oid)
    bundle = bundles.get(oid)
    am = asset_matches.get(oid)
    rec: dict = {"opportunity_id": oid, "bucket": bucket}
    if fo is not None:
        rec.update({
            "title": fo.title, "need": fo.need, "market": fo.market.value,
            "language": fo.language.value, "platform": fo.platform.value,
            "durability": fo.durability.value, "urgency": fo.urgency.value,
            "signal_ids": list(fo.signal_ids),
        })
    if bundle is not None and not bundle.excluded:
        rec["overall_confidence"] = bundle.evaluation.overall_confidence.value
        rec["target_state"] = bundle.recommendation.target_state.value
    if am is not None:
        rec["best_assets"] = {
            "playlist": am.best_playlist, "page": am.best_page, "artist": am.best_artist,
        }
    if reason:
        rec["exclusion_reason"] = reason
    return rec


# --- assembly -------------------------------------------------

def _strip_hypotheses(h: Optional[Hypotheses], scopes: set) -> Optional[Hypotheses]:
    if h is None:
        return None
    kwargs = dict(
        potential_cluster=h.potential_cluster,
        potential_positioning=h.potential_positioning,
        potential_page=h.potential_page,
        first_content_direction=h.first_content_direction,
        format=h.format,
        hook=h.hook,
    )
    for scope in scopes:
        fname = _STRIP_FIELD.get(scope)
        if fname:
            kwargs[fname] = None
    if not any(kwargs.values()):
        return None
    return Hypotheses(**kwargs)


def _distinct_sources(signal_ids: Sequence[str], by_id: Dict[str, Signal]) -> List[Provenance]:
    seen = set()
    out: List[Provenance] = []
    for sid in signal_ids:
        sig = by_id.get(sid)
        if sig is None:
            continue
        p = sig.provenance
        key = (p.source, p.query_or_reference, p.url, p.observed_at)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def assemble_opportunity(
    framed: FramedOpportunity,
    asset_match,
    bundle: EvaluationBundle,
    *,
    rank: Optional[int],
    status,
    report_ref: Optional[str],
    signals_by_id: Dict[str, Signal],
    run_config: RunConfig,
    generated_at: str,
    replay: bool,
) -> Opportunity:
    hypotheses = _strip_hypotheses(framed.hypotheses, bundle.stripped_hypothesis_scopes)
    provenance = OpportunityProvenance(
        run_id=run_config.run_id,
        schema_version=SCHEMA_VERSION,
        model=run_config.model,
        prompt_version=run_config.prompt_version,
        generated_at=generated_at,
        signal_ids=list(framed.signal_ids),
        sources=_distinct_sources(framed.signal_ids, signals_by_id),
        replay=replay,
    )
    state_history = [StateChange(
        to=status.value, at=generated_at, by="system",
        from_=None, note=f"created by run {run_config.run_id}",
    )]
    return Opportunity(
        opportunity_id=framed.opportunity_id,
        schema_version=SCHEMA_VERSION,
        run_id=run_config.run_id,
        created_at=framed.created_at,
        title=framed.title,
        need=framed.need,
        audience=framed.audience,
        market=framed.market,
        language=framed.language,
        platform=framed.platform,
        consumption_context=framed.consumption_context,
        durability=framed.durability,
        urgency=framed.urgency,
        evidence=framed.evidence,
        asset_fit=asset_match,
        evaluation=bundle.evaluation,
        business_outcome_profile=bundle.business_outcome_profile,
        recommendation=bundle.recommendation,
        provenance=provenance,
        status=status,
        state_history=state_history,
        hypotheses=hypotheses,
        rank=rank,
        report_ref=report_ref,
    )


# --- markdown rendering --------------------------------------

def _fm(mapping: dict) -> str:
    body = yaml.safe_dump(mapping, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{body}---\n"


def _potential_cluster_label(h: Optional[Hypotheses]) -> Optional[str]:
    if not h or not h.potential_cluster:
        return None
    pc = h.potential_cluster
    return pc.value if pc.canonical else f"{pc.value} (proposed_new)"


def _evidence_block(opp: Opportunity, by_id: Dict[str, Signal]) -> str:
    lines: List[str] = []
    groups = {
        EvidenceType.OBSERVED: "Observed facts",
        EvidenceType.INFERRED: "Inferences",
        EvidenceType.HYPOTHESIS: "Hypotheses",
    }
    for etype, heading in groups.items():
        items = [e for e in opp.evidence if e.type is etype]
        if not items:
            continue
        lines.append(f"### {heading}")
        for e in items:
            lines.append(
                f"- **[{e.type.value}]** {e.statement} "
                f"_(confidence: {e.confidence.value})_"
            )
            if e.type is EvidenceType.OBSERVED:
                for sid in e.signal_ids or []:
                    sig = by_id.get(sid)
                    if sig is None:
                        lines.append(f"  - signal `{sid}` — UNKNOWN (not resolvable)")
                        continue
                    url = sig.url or "UNKNOWN"
                    lines.append(
                        f"  - signal `{sid}` — {sig.source} · observed_at: {sig.observed_at} "
                        f"· url: {url}"
                    )
            if e.type is EvidenceType.INFERRED and e.derived_from:
                lines.append(f"  - derived from: {', '.join(f'`{d}`' for d in e.derived_from)}")
            if e.rationale:
                lines.append(f"  - rationale: {e.rationale}")
            if e.test_idea:
                lines.append(f"  - test idea: {e.test_idea}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _evaluation_block(opp: Opportunity) -> str:
    ev = opp.evaluation
    lines = ["| dimension | rating | confidence | justification |",
             "|---|---|---|---|"]
    for key, dim in ev.dimensions.items():
        blocked = f" _(blocked_by: {', '.join(dim.blocked_by)})_" if dim.blocked_by else ""
        lines.append(
            f"| {key} | {dim.rating.value} | {dim.confidence.value} | "
            f"{dim.justification}{blocked} |"
        )
    lines.append("")
    if ev.red_flags:
        lines.append("**Red flags**")
        for rf in ev.red_flags:
            lines.append(f"- _{rf.kind.value} / {rf.severity.value}_ — {rf.description}")
        lines.append("")
    lines.append(f"**Overall confidence:** {ev.overall_confidence.value}")
    lines.append("")
    lines.append(f"**Summary:** {ev.summary}")
    return "\n".join(lines)


def _bop_block(opp: Opportunity) -> str:
    lines = ["| axis | rating | confidence | justification |", "|---|---|---|---|"]
    for key, ax in opp.business_outcome_profile.axes.items():
        lines.append(f"| {key} | {ax.rating.value} | {ax.confidence.value} | {ax.justification} |")
    return "\n".join(lines)


def _asset_block(opp: Opportunity) -> str:
    am = opp.asset_fit
    lines = []

    def _cands(title, cands):
        if not cands:
            lines.append(f"**{title}:** (none)")
            return
        lines.append(f"**{title}:**")
        for c in cands:
            role = f" · role: {c.role.value}" if c.role else ""
            lines.append(
                f"- `{c.asset_id}` {c.name} — fit: {c.fit.value} "
                f"(basis: {c.fit_basis.value}){role} — {c.fit_rationale}"
            )

    _cands("Matching playlists", am.matching_playlists)
    _cands("Matching pages", am.matching_pages)
    _cands("Matching artists", am.matching_artists)
    lines.append("")
    lines.append(f"**best_playlist:** {am.best_playlist}")
    lines.append(f"**best_page:** {am.best_page}")
    lines.append(f"**best_artist:** {am.best_artist}")
    if am.unmatched_reason:
        lines.append(f"**unmatched_reason:** {am.unmatched_reason}")
    if am.new_asset_recommendation:
        r = am.new_asset_recommendation
        c = r.i5_conditions_met
        lines.append("")
        lines.append(f"**New asset recommendation** (recommendation only — never executed): "
                     f"{r.asset_type.value}")
        lines.append(f"- rationale: {r.rationale}")
        lines.append(
            f"- I5 conditions — no_adequate_fit: {c.no_adequate_fit}; "
            f"relevant_potential: {c.relevant_potential}; "
            f"differentiation_potential: {c.differentiation_potential}; "
            f"sufficient_window: {c.sufficient_window}"
        )
    return "\n".join(lines)


def _hypotheses_block(opp: Opportunity) -> str:
    h = opp.hypotheses
    if h is None:
        return "_No hypotheses were recorded for this opportunity._"
    lines = ["_Every item below is a HYPOTHESIS — non-binding, not a decision (C7)._", ""]
    pc = _potential_cluster_label(h)
    lines.append(f"- **potential_cluster:** {pc or 'UNKNOWN'}")
    lines.append(f"- **potential_positioning:** {h.potential_positioning or 'UNKNOWN'}")
    lines.append(f"- **potential_page:** {h.potential_page or 'UNKNOWN'}")
    lines.append(f"- **first_content_direction:** {h.first_content_direction or 'UNKNOWN'}")
    lines.append(f"- **format:** {h.format or 'UNKNOWN'}")
    lines.append(f"- **hook:** {h.hook or 'UNKNOWN'}")
    return "\n".join(lines)


def _recommendation_block(opp: Opportunity) -> str:
    r = opp.recommendation
    return "\n".join([
        f"- **target_state:** {r.target_state.value}",
        f"- **suggested_next_step:** {r.suggested_next_step}",
        f"- **justification:** {r.justification}",
        f"- **confidence:** {r.confidence.value}",
        f"- **execution_note:** {r.execution_note}",
    ])


def _provenance_block(opp: Opportunity) -> str:
    p = opp.provenance
    lines = [
        f"- **run_id:** {p.run_id}",
        f"- **model:** {p.model}",
        f"- **prompt_version:** {p.prompt_version}",
        f"- **generated_at:** {p.generated_at}",
        f"- **replay:** {p.replay}"
        + ("  _(replay run — not valid as current-trend evidence, §22)_" if p.replay else ""),
        f"- **signal_ids:** {', '.join(f'`{s}`' for s in p.signal_ids) or 'UNKNOWN'}",
        "- **sources:**",
    ]
    for s in p.sources:
        lines.append(
            f"  - {s.source} ({s.source_type.value}) · {s.capture_method.value} · "
            f"query/ref: {s.query_or_reference} · observed_at: {s.observed_at}"
        )
    if not p.sources:
        lines.append("  - UNKNOWN")
    return "\n".join(lines)


def render_report(opp: Opportunity, *, signals_by_id: Dict[str, Signal]) -> str:
    fm = {
        "opportunity_id": opp.opportunity_id,
        "run_id": opp.run_id,
        "schema_version": SCHEMA_VERSION,
        "created_at": opp.created_at,
        "rank": opp.rank,
        "title": opp.title,
        "market": opp.market.value,
        "language": opp.language.value,
        "platforms": [opp.platform.value],
        "durability": opp.durability.value,
        "urgency": opp.urgency.value,
        "potential_cluster": _potential_cluster_label(opp.hypotheses),
        "overall_confidence": opp.evaluation.overall_confidence.value,
        "target_state": opp.recommendation.target_state.value,
    }
    audience = opp.audience.description
    if opp.audience.attributes:
        audience += f" — attributes: {opp.audience.attributes}"
    sections = [
        _fm(fm),
        f"# {opp.title}\n",
        "## 1. Identity\n"
        f"- **opportunity_id:** `{opp.opportunity_id}`\n"
        f"- **created_at:** {opp.created_at}\n"
        f"- **run_id:** {opp.run_id}\n"
        f"- **schema_version:** {SCHEMA_VERSION}\n",
        "## 2. Market Context\n"
        f"- **market:** {opp.market.value}\n"
        f"- **language:** {opp.language.value}\n"
        f"- **platform(s):** {opp.platform.value}\n"
        f"- **need / desire / behaviour:** {opp.need}\n"
        f"- **audience:** {audience}\n"
        f"- **consumption context:** {opp.consumption_context}\n"
        f"- **durability:** {opp.durability.value} · **urgency:** {opp.urgency.value}\n",
        "## 3. Evidence\n\n" + _evidence_block(opp, signals_by_id) + "\n",
        "## 4. Evaluation\n\n" + _evaluation_block(opp) + "\n",
        "## 5. Business Outcome Profile\n\n" + _bop_block(opp) + "\n",
        "## 6. Asset Fit\n\n" + _asset_block(opp) + "\n",
        "## 7. Hypotheses\n\n" + _hypotheses_block(opp) + "\n",
        "## 8. Recommendation\n\n" + _recommendation_block(opp) + "\n",
        "## 9. Provenance\n\n" + _provenance_block(opp) + "\n",
    ]
    return "\n".join(sections).rstrip() + "\n"


# --- digest + review ----------------------------------------

def _config_snapshot(cfg: RunConfig) -> dict:
    """The reproducibility set from RunConfig (spec §12.5, §16.4)."""
    return {
        "run_id": cfg.run_id,
        "run_date": cfg.run_date,
        "model": cfg.model,
        "extraction_model": cfg.extraction_model,
        "prompt_version": cfg.prompt_version,
        "schema_version": cfg.schema_version,
        "signal_sources": [s.value for s in cfg.signal_sources],
        "scope": {
            "clusters": list(cfg.scope.clusters),
            "markets": [m.value for m in cfg.scope.markets],
            "languages": [lang.value for lang in cfg.scope.languages],
            "discovery_platforms": [p.value for p in cfg.scope.discovery_platforms],
            "queries": list(cfg.scope.queries),
            "notes": cfg.scope.notes,
        },
        "max_opportunities_presented": cfg.max_opportunities_presented,
        "max_candidates": cfg.max_candidates,
        "min_opportunities_target": cfg.min_opportunities_target,
        "dry_run": cfg.dry_run,
        "replay": {
            "enabled": cfg.replay.enabled,
            "llm": cfg.replay.llm,
            "fixture_path": cfg.replay.fixture_path,
        },
    }


def _digest(
    run_config: RunConfig,
    ranking: RankingResult,
    opportunities: Dict[str, Opportunity],
    framed: Dict[str, FramedOpportunity],
    *,
    collection_summary: dict,
    counts: dict,
    excluded_reasons: Dict[str, str],
    needs_input_notes: Sequence[str],
    generated_at: str,
    replay: bool,
) -> str:
    counts = dict(counts)
    timings = counts.pop("timings_seconds", None)
    fm = {
        "run_id": run_config.run_id,
        "run_date": run_config.run_date,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "replay": replay,
        "model": run_config.model,
        "prompt_version": run_config.prompt_version,
        "config_snapshot": _config_snapshot(run_config),
        "sources_used": collection_summary.get("sources_used", []),
        "sources_failed": collection_summary.get("sources_failed", []),
        "counts": counts,
        "timings_seconds": timings or {},
    }
    lines = [_fm(fm), f"# Run digest — {run_config.run_id}\n"]

    presented_ids = [oid for oid in ranking.presented if oid in opportunities]

    lines.append("## Presented opportunities\n")
    if presented_ids:
        lines.append("| rank | opportunity_id | title | market/language | target_state "
                     "| overall_confidence | top dimensions | key red flags | report |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for oid in presented_ids:
            opp = opportunities.get(oid)
            if opp is None:
                continue
            top_dims = ", ".join(
                k for k, d in opp.evaluation.dimensions.items()
                if d.rating.value in ("HIGH", "VERY_HIGH")
            ) or "—"
            flags = "; ".join(
                f"{rf.kind.value}/{rf.severity.value}" for rf in opp.evaluation.red_flags
            ) or "—"
            lines.append(
                f"| {opp.rank} | `{oid}` | {opp.title} | "
                f"{opp.market.value} / {opp.language.value} | "
                f"{opp.recommendation.target_state.value} | "
                f"{opp.evaluation.overall_confidence.value} | {top_dims} | {flags} | "
                f"[{oid}.md](./{oid}.md) |"
            )
    else:
        lines.append("_No opportunities were presented this run._")
    lines.append("")

    if counts["presented"] < run_config.min_opportunities_target:
        lines.append(
            f"> **Below C10 target:** {counts['presented']} presented "
            f"(target is {run_config.min_opportunities_target}–"
            f"{run_config.max_opportunities_presented}). (spec §12.5, §14)\n"
        )

    lines.append("## Parked opportunities\n")
    if ranking.parked:
        for oid in ranking.parked:
            fo = framed.get(oid)
            lines.append(f"- `{oid}` — {fo.title if fo else 'UNKNOWN'} (status: PARK)")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## Excluded opportunities\n")
    # every hard-exclusion (ranking) plus every opportunity dropped at report time (§14)
    all_excluded = dict(excluded_reasons)
    for oid in ranking.excluded:
        all_excluded.setdefault(oid, "hard-excluded")
    if all_excluded:
        for oid in sorted(all_excluded):
            fo = framed.get(oid)
            lines.append(
                f"- `{oid}` — {fo.title if fo else 'UNKNOWN'} — reason: {all_excluded[oid]}"
            )
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("## NEEDS_INPUT encountered\n")
    if needs_input_notes:
        for note in sorted(set(needs_input_notes)):
            lines.append(f"- {note}")
    else:
        lines.append("_None recorded this run._")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _review(run_config: RunConfig, ranking: RankingResult,
            opportunities: Dict[str, Opportunity]) -> str:
    presented_ids = [oid for oid in ranking.presented if oid in opportunities]
    fm = {
        "run_id": run_config.run_id,
        "review_date": run_config.run_date,
        "reviewer": "",
        "opportunities_presented": len(presented_ids),
        "opportunities_relevant_count": None,
        "relevant_ratio": None,
        "advanced_opportunity_id": None,
    }
    lines = [_fm(fm), f"# Run Review — {run_config.run_id}\n"]
    lines.append("> Owner fills this after reading the digest (spec §21.1). "
                 "`owner_decision`: `relevant` · `not_relevant` · `advance` "
                 "(`advance` implies `relevant`).\n")
    lines.append("| rank | opportunity_id | title | owner_decision | note |")
    lines.append("|------|----------------|-------|----------------|------|")
    for oid in presented_ids:
        opp = opportunities[oid]
        lines.append(f"| {opp.rank} | {oid} | {opp.title} |  |  |")
    lines.append("")
    lines.append("## Notes\n")
    lines.append("<free text: patterns, source quality, NEEDS_INPUT that blocked judgement, etc.>")
    return "\n".join(lines).rstrip() + "\n"


# --- entry point -------------------------------------------

def _collect_needs_input(opp: Opportunity) -> List[str]:
    notes: List[str] = []
    for key, dim in opp.evaluation.dimensions.items():
        for b in dim.blocked_by or []:
            if "NEEDS_INPUT" in b or "UNKNOWN" in b:
                notes.append(f"{key}: {b}")
    return notes


def generate_reports(
    ranking: RankingResult,
    framed: Dict[str, FramedOpportunity],
    asset_matches: Dict[str, object],
    bundles: Dict[str, EvaluationBundle],
    *,
    signals: Sequence[Signal],
    knowledge: KnowledgeBundle,
    run_config: RunConfig,
    project_root: Union[str, Path],
    collection_summary: Optional[dict] = None,
    counts_extra: Optional[dict] = None,
    generated_at: Optional[str] = None,
    replay: bool = False,
    musical_dna_needs_input: bool = True,
) -> ReportingResult:
    root = Path(project_root)
    reports_dir = root / run_config.paths.reports_dir / run_config.run_id
    generated_at = generated_at or _dt.datetime.now(_dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    signals_by_id = {s.signal_id: s for s in signals}
    inventory: InventoryIndex = knowledge.inventory
    known_signal_ids = set(signals_by_id)
    canonical_ids = set(knowledge.canonical_cluster_ids)

    result = ReportingResult(opportunities={})
    excluded_reasons: Dict[str, str] = {
        r.opportunity_id: (r.exclusion_reason or "hard-excluded")
        for r in ranking.ordered if r.bucket == "excluded"
    }

    for oid in ranking.presented:
        fo = framed.get(oid)
        bundle = bundles.get(oid)
        am = asset_matches.get(oid)
        ranked = ranking.by_id(oid)
        if not (fo and bundle and am and ranked):
            continue

        report_ref = f"{run_config.paths.reports_dir}/{run_config.run_id}/{oid}.md"
        opp = assemble_opportunity(
            fo, am, bundle, rank=ranked.rank, status=ranked.status,
            report_ref=report_ref, signals_by_id=signals_by_id,
            run_config=run_config, generated_at=generated_at, replay=replay,
        )
        errs = blocking(validate_opportunity(
            opp, known_signal_ids=known_signal_ids, canonical_cluster_ids=canonical_ids,
            inventory=inventory, musical_dna_needs_input=musical_dna_needs_input,
        ))
        if errs:
            # §14 — a report that fails validation moves the opportunity to `excluded`.
            reason = "; ".join(f"[{e.code}] {e.message}" for e in errs[:3])
            result.excluded_at_report[oid] = reason
            excluded_reasons[oid] = reason
            continue

        result.opportunities[oid] = opp
        result.needs_input_notes.extend(_collect_needs_input(opp))

        md = render_report(opp, signals_by_id=signals_by_id)
        result.report_paths[oid] = write_text(reports_dir / f"{oid}.md", md)
        result.sidecar_paths[oid] = write_json(reports_dir / f"{oid}.json", encode(opp))

    # digest counts
    presented_final = [oid for oid in ranking.presented if oid in result.opportunities]
    counts = {
        "signals": len(signals),
        "opportunities_total": len(framed),
        "presented": len(presented_final),
        "parked": len(ranking.parked),
        "excluded": len(ranking.excluded) + len(result.excluded_at_report),
    }
    if counts_extra:
        counts.update(counts_extra)

    # data/<run_id>/opportunities.json — full structured records before rendering (§17).
    data_dir = root / run_config.paths.data_dir / run_config.run_id
    result.opportunities_json_path = write_json(data_dir / "opportunities.json", {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_config.run_id,
        "generated_at": generated_at,
        "presented": [encode(result.opportunities[oid]) for oid in presented_final],
        "parked": [
            _partial_record(oid, "parked", framed, bundles, asset_matches, None)
            for oid in ranking.parked
        ],
        "excluded": [
            _partial_record(oid, "excluded", framed, bundles, asset_matches,
                            excluded_reasons.get(oid))
            for oid in sorted(set(ranking.excluded) | set(result.excluded_at_report))
        ],
    })

    digest = _digest(
        run_config, ranking, result.opportunities, framed,
        collection_summary=collection_summary or {},
        counts=counts, excluded_reasons=excluded_reasons,
        needs_input_notes=result.needs_input_notes,
        generated_at=generated_at, replay=replay,
    )
    result.digest_path = write_text(reports_dir / "digest.md", digest)
    result.review_path = write_text(
        reports_dir / "review.md", _review(run_config, ranking, result.opportunities)
    )
    return result
