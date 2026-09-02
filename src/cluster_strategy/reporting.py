"""Cluster Strategy report renderer (contract §4, I4 pattern).

Markdown + YAML front matter + a JSON sidecar (``codec.encode``). Observed facts,
derived decisions, hypotheses and recommendations are visually separated. Missing
information renders ``UNKNOWN`` / ``NEEDS_INPUT``, never omitted or guessed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

import yaml

from market_intelligence.io_utils import write_json, write_text
from market_intelligence.schema.codec import encode

from .schema.models import ClusterStrategy


def _fm(mapping: dict) -> str:
    body = yaml.safe_dump(mapping, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{body}---\n"


def _front_matter(cs: ClusterStrategy) -> dict:
    d = cs.cluster_decision
    return {
        "cluster_strategy_id": cs.cluster_strategy_id,
        "schema_version": cs.schema_version,
        "opportunity_id": cs.opportunity.opportunity_id,
        "opportunity_run_id": cs.opportunity.opportunity_run_id,
        "generated_at": cs.provenance.generated_at,
        "replay": cs.provenance.replay,
        "model": cs.provenance.model,
        "prompt_version": cs.provenance.prompt_version,
        "cluster_decision": d.decision.value,
        "cluster_id": d.cluster_id,
        "subcluster_or_angle": d.subcluster_or_angle,
        "market": cs.opportunity.market.value,
        "language": cs.opportunity.language.value,
        "overall_confidence": cs.evaluation.overall_confidence.value,
        "opportunity_lifecycle_state": cs.recommendation.opportunity_lifecycle_state.value,
        "target_next_stage": cs.recommendation.target_next_stage.value,
    }


def _identity(cs: ClusterStrategy) -> str:
    oa = cs.owner_authorization
    return (
        f"- **cluster_strategy_id:** `{cs.cluster_strategy_id}`\n"
        f"- **opportunity:** `{cs.opportunity.opportunity_id}` "
        f"([report]({cs.opportunity.opportunity_report_ref}))\n"
        f"- **owner authorization:** advanced in `{oa.review_md_ref}`"
        + (f" by {oa.reviewer}" if oa.reviewer else "")
        + (f" on {oa.review_date}" if oa.review_date else "")
        + "\n"
        f"- **schema_version:** {cs.schema_version}\n"
        f"- **generated_at:** {cs.provenance.generated_at}"
        + ("  _(replay — the source opportunity or this run is a fixture; not "
           "current-trend evidence, §22)_" if cs.provenance.replay else "")
    )


def _cluster_decision(cs: ClusterStrategy) -> str:
    d = cs.cluster_decision
    lines = [
        f"- **decision (recommendation):** `{d.decision.value}`",
        f"- **cluster:** {(d.cluster_id + ' — ' + d.cluster_name) if d.cluster_id else 'UNKNOWN'}",
        f"- **subcluster / angle:** {d.subcluster_or_angle or 'UNKNOWN'}"
        + ("  _(new to the cluster)_" if d.is_new_subcluster else ""),
        f"- **framing hypothesis comparison:** {d.framing_hypothesis_comparison}",
        f"- **justification:** {d.justification}",
    ]
    if d.deferral_reason:
        lines.append(f"- **deferral reason:** {d.deferral_reason}")
    if d.rejection_reason:
        lines.append(f"- **rejection reason:** {d.rejection_reason}")
    if d.new_cluster_proposal:
        p = d.new_cluster_proposal
        lines += [
            "",
            "### Proposed new cluster (HYPOTHESIS — hand-off to the owner)",
            f"- **proposed id / name:** `{p.proposed_id}` — {p.proposed_name}",
            f"- **concept:** {p.concept}",
            f"- **why not a subcluster:** {p.why_not_subcluster}",
            "- **boundary vs adjacent canonical clusters:**",
        ]
        for cid, sentence in p.boundary_vs_adjacent.items():
            lines.append(f"  - `{cid}`: {sentence}")
        lines.append(
            f"- **supporting evidence:** {', '.join(f'`{e}`' for e in p.supporting_evidence)}"
        )
        lines.append(f"- _{p.governance_note}_")
    return "\n".join(lines)


def _strategic_definition(cs: ClusterStrategy) -> str:
    sd = cs.strategic_definition
    if sd is None:
        return "_Not defined — the cluster decision was DEFER or REJECT._"
    return "\n".join([
        "_Derived decisions (Cluster Strategy's own reasoning, grounded in the opportunity)._",
        "",
        f"- **central concept:** {sd.central_concept}",
        f"- **audience:** {sd.audience_description}"
        + (f"  _(attributes: {sd.audience_attributes})_" if sd.audience_attributes else ""),
        f"- **intent:** {sd.intent}",
        f"- **emotional state (subjective experience — G02):** {sd.emotional_state}",
        f"- **consumption context:** {sd.consumption_context}",
        f"- **editorial promise:** {sd.editorial_promise}",
        f"- **positioning statement (recommendation):** {sd.positioning_statement}",
        f"- **market / language:** {sd.market.value} / {sd.language.value}",
        f"- **localization notes:** {sd.localization_notes}",
        f"- **durability read:** {sd.durability_read}",
        f"- **strategic coherence:** {sd.strategic_coherence_note}",
    ])


def _asset_strategy(cs: ClusterStrategy) -> str:
    a = cs.asset_strategy
    if a is None:
        return "_Not defined — the cluster decision was DEFER or REJECT._"
    pl, pg, ar = a.playlist_strategy, a.page_strategy, a.artist_strategy
    lines = [
        "_Observed (from the inventory / the opportunity's AssetMatch) + derived framing. "
        "No asset is invented (I1)._",
        "",
        "**Playlist**",
        f"- primary: `{pl.primary_playlist_id}` (fit basis: {pl.playlist_fit_basis})",
        f"- secondary: {', '.join(f'`{p}`' for p in pl.secondary_playlist_ids) or 'none'}",
        f"- {pl.reuse_rationale}",
    ]
    if pl.new_playlist_recommendation:
        lines.append(
            f"- new-playlist recommendation (never executed): "
            f"{pl.new_playlist_recommendation.asset_type.value} — "
            f"{pl.new_playlist_recommendation.rationale}"
        )
    lines += [
        "",
        "**Page**",
        f"- primary: `{pg.primary_page_id}` (fit basis: {pg.page_fit_basis})",
        f"- {pg.note}",
    ]
    if pg.new_page_recommendation:
        c = pg.new_page_recommendation.i5_conditions_met
        lines.append(
            f"- new-page recommendation (never executed): "
            f"{pg.new_page_recommendation.asset_type.value} — "
            f"{pg.new_page_recommendation.rationale}"
        )
        lines.append(
            f"  - I5 conditions — no_adequate_fit: {c.no_adequate_fit}; "
            f"relevant_potential: {c.relevant_potential}; "
            f"differentiation_potential: {c.differentiation_potential}; "
            f"sufficient_window: {c.sufficient_window}"
        )
    lines += [
        "",
        "**Artists**",
        f"- best: `{ar.best_artist_id}`",
        "- anchor hero artists: "
        + (", ".join(f"`{a}`" for a in ar.anchor_hero_artist_ids) or "none"),
        f"- catalog-affinity artists: "
        f"{', '.join(f'`{a}`' for a in ar.catalog_affinity_artist_ids) or 'none'}",
        f"- candidates: {len(ar.candidate_artist_ids)} artist(s)",
        f"- _{ar.affinity_note}_",
        "",
        f"**Catalog affinity:** {a.catalog_affinity_summary}",
        "",
        f"**Market / language fit:** {a.market_language_fit.rating.value} "
        f"(confidence: {a.market_language_fit.confidence.value}) — "
        f"{a.market_language_fit.justification}",
        "",
        "**Asset gaps:** " + ("; ".join(a.asset_gaps) if a.asset_gaps else "none"),
    ]
    return "\n".join(lines)


def _content_direction(cs: ClusterStrategy) -> str:
    c = cs.content_direction
    if c is None:
        return "_Not defined — the cluster decision was DEFER or REJECT._"
    lines = [
        "_Every item below is a HYPOTHESIS — non-binding, not a decision (C7)._",
        "",
        f"- **first content direction:** {c.first_content_direction}",
        "- **candidate editorial angles:** "
        + ("; ".join(c.editorial_angles) if c.editorial_angles else "none"),
        f"- **music relationship:** {c.music_relationship}",
        "",
        f"_{c.content_boundary_note}_",
    ]
    return "\n".join(lines)


def _evaluation(cs: ClusterStrategy) -> str:
    ev = cs.evaluation
    lines = ["| dimension | rating | confidence | justification |", "|---|---|---|---|"]
    for k, d in ev.dimensions.items():
        blocked = f" _(blocked_by: {', '.join(d.blocked_by)})_" if d.blocked_by else ""
        lines.append(
            f"| {k} | {d.rating.value} | {d.confidence.value} | {d.justification}{blocked} |")
    lines.append("")
    lines.append(f"**Overall confidence:** {ev.overall_confidence.value}  "
                 f"_(capped at the opportunity's {cs.opportunity.overall_confidence.value}; "
                 "not raised by high dimension ratings — C6)_")
    lines.append("")
    if ev.red_flags:
        lines.append("**Red flags**")
        for rf in ev.red_flags:
            lines.append(f"- _{rf.kind.value} / {rf.severity.value}_ — {rf.description}")
        lines.append("")
    lines.append("**Open questions**")
    if ev.open_questions:
        for q in ev.open_questions:
            lines.append(f"- {q}")
    else:
        lines.append("- none")
    return "\n".join(lines)


def _recommendation(cs: ClusterStrategy) -> str:
    r = cs.recommendation
    return "\n".join([
        f"- **target next stage (recommendation):** `{r.target_next_stage.value}`",
        f"- **recommended next step:** {r.recommended_next_step}",
        f"- **opportunity lifecycle state (carried, unchanged):** "
        f"`{r.opportunity_lifecycle_state.value}`",
        f"- **justification:** {r.justification}",
        f"- **execution note:** {r.execution_note}",
    ])


def _provenance(cs: ClusterStrategy) -> str:
    p = cs.provenance
    lines = [
        f"- **cluster strategy run_id:** {p.run_id}",
        f"- **model:** {p.model}",
        f"- **prompt_version:** {p.prompt_version}",
        f"- **generated_at:** {p.generated_at}",
        f"- **replay:** {p.replay}",
        f"- **knowledge snapshot:** {p.knowledge_snapshot}",
        f"- **signal_ids (carried):** {', '.join(f'`{s}`' for s in p.signal_ids) or 'UNKNOWN'}",
        "- **sources (carried):**",
    ]
    for s in p.sources:
        lines.append(
            f"  - {s.source} ({s.source_type.value}) · {s.capture_method.value} · "
            f"observed_at: {s.observed_at}"
        )
    if not p.sources:
        lines.append("  - UNKNOWN")
    return "\n".join(lines)


def render(cs: ClusterStrategy) -> str:
    parts = [
        _fm(_front_matter(cs)),
        f"# Cluster Strategy — {cs.opportunity.title}\n",
        "## 1. Identity\n\n" + _identity(cs) + "\n",
        "## 2. Cluster Decision\n\n" + _cluster_decision(cs) + "\n",
        "## 3. Strategic Definition\n\n" + _strategic_definition(cs) + "\n",
        "## 4. Asset Strategy\n\n" + _asset_strategy(cs) + "\n",
        "## 5. Content Direction\n\n" + _content_direction(cs) + "\n",
        "## 6. Evaluation & Confidence\n\n" + _evaluation(cs) + "\n",
        "## 7. Recommendation\n\n" + _recommendation(cs) + "\n",
        "## 8. Provenance\n\n" + _provenance(cs) + "\n",
    ]
    return "\n".join(parts).rstrip() + "\n"


def write_report(
    cs: ClusterStrategy, *, config, project_root: Union[str, Path],
) -> Tuple[Path, Path]:
    out_dir = Path(project_root) / config.reports_subdir
    oid = cs.opportunity.opportunity_id
    md_path = write_text(out_dir / f"{oid}.md", render(cs))
    json_path = write_json(out_dir / f"{oid}.json", encode(cs))
    return md_path, json_path
