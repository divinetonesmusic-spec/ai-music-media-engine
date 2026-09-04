"""Page Blueprint report renderer (contract §4, I4 pattern).

Markdown + YAML front matter + a JSON sidecar (``codec.encode``). Carried facts,
Claude's synthesis, and the recommendation are visually separated. Missing
information renders ``UNKNOWN`` / ``NEEDS_INPUT``, never omitted or guessed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Union

import yaml

from market_intelligence.io_utils import write_json, write_text
from market_intelligence.schema.codec import encode

from .schema.models import PageBlueprint


def _fm(mapping: dict) -> str:
    body = yaml.safe_dump(mapping, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{body}---\n"


def _front_matter(pb: PageBlueprint) -> dict:
    return {
        "page_blueprint_id": pb.page_blueprint_id,
        "schema_version": pb.schema_version,
        "opportunity_id": pb.cluster_strategy.opportunity_id,
        "cluster_strategy_id": pb.cluster_strategy.cluster_strategy_id,
        "cluster_id": pb.cluster_strategy.cluster_id,
        "generated_at": pb.provenance.generated_at,
        "replay": pb.provenance.replay,
        "model": pb.provenance.model,
        "prompt_version": pb.provenance.prompt_version,
        "market": pb.cluster_strategy.market.value,
        "language": pb.cluster_strategy.language.value,
        "overall_confidence": pb.evaluation.overall_confidence.value,
        "target_next_stage": pb.recommendation.target_next_stage.value,
    }


def _identity(pb: PageBlueprint) -> str:
    cs = pb.cluster_strategy
    cluster_line = (
        f"{cs.cluster_id} — {cs.cluster_name or ''}"
        if cs.cluster_id else "PROPOSED (not yet formalized)"
    )
    return (
        f"- **page_blueprint_id:** `{pb.page_blueprint_id}`\n"
        f"- **cluster strategy:** `{cs.cluster_strategy_id}` "
        f"([sidecar]({cs.cluster_strategy_ref}))\n"
        f"- **opportunity:** `{cs.opportunity_id}`\n"
        f"- **cluster:** {cluster_line}\n"
        f"- **schema_version:** {pb.schema_version}\n"
        f"- **generated_at:** {pb.provenance.generated_at}"
        + ("  _(replay — the source ClusterStrategy or this run is a fixture; not "
           "current-trend evidence, §22)_" if pb.provenance.replay else "")
    )


def _page_identity_section(pb: PageBlueprint) -> str:
    ident = pb.identity
    return (
        f"- **concept name:** {ident.concept_name}\n"
        f"- **positioning statement:** {ident.positioning_statement}\n"
        f"- **bio:** {ident.bio}\n"
        f"- **market / language:** {pb.cluster_strategy.market.value} / "
        f"{pb.cluster_strategy.language.value}"
    )


def _visual_identity_section(pb: PageBlueprint) -> str:
    v = pb.visual_identity
    return (
        f"- **visual language:** {v.visual_language}\n"
        f"- **tone of voice:** {v.tone_of_voice}\n"
        f"- **grounded in (business-dna §9.9):** {v.musical_dna_expression_used}"
    )


def _asset_section(pb: PageBlueprint) -> str:
    a = pb.asset_link
    ps = a.page_strategy
    lines = [
        f"- **primary page:** `{ps.primary_page_id}` (fit basis: {ps.page_fit_basis})",
        f"- **page note (from Cluster Strategy, I5):** {ps.note}",
        f"- **primary playlist:** `{a.primary_playlist_id}`",
        f"- **primary artist:** `{a.primary_artist_id}`",
    ]
    if ps.new_page_recommendation:
        n = ps.new_page_recommendation
        lines.append(
            f"- **new asset recommended (carried, not decided here):** {n.asset_type.value} — "
            f"{n.rationale}"
        )
    lines.append(f"- _{a.asset_inheritance_note}_")
    return "\n".join(lines)


def _content_framing_section(pb: PageBlueprint) -> str:
    cf = pb.content_framing
    pillars = "\n".join(f"  - {p}" for p in cf.content_pillars)
    return (
        f"- **content pillars:**\n{pillars}\n"
        f"- **platforms:** {', '.join(cf.platforms)}\n"
        f"- **posting cadence (recommendation, not a schedule):** {cf.posting_cadence}\n"
        f"- _{cf.content_boundary_note}_"
    )


def _evaluation_section(pb: PageBlueprint) -> str:
    ev = pb.evaluation
    lines = [
        f"- **overall_confidence:** {ev.overall_confidence.value}",
        f"- **justification:** {ev.justification}",
    ]
    if ev.blocked_by:
        lines.append("- **blocked_by (NEEDS_INPUT / UNKNOWN):**")
        lines += [f"  - {b}" for b in ev.blocked_by]
    if ev.red_flags:
        lines.append("- **red flags:**")
        lines += [
            f"  - `{rf.severity.value}` ({rf.kind.value}): {rf.description}"
            for rf in ev.red_flags
        ]
    else:
        lines.append("- **red flags:** none")
    return "\n".join(lines)


def _recommendation_section(pb: PageBlueprint) -> str:
    r = pb.recommendation
    return (
        f"- **target_next_stage (recommendation):** `{r.target_next_stage.value}`\n"
        f"- **recommended_next_step:** {r.recommended_next_step}\n"
        f"- **justification:** {r.justification}\n"
        f"- _{r.execution_note}_"
    )


def render_markdown(pb: PageBlueprint) -> str:
    sections = [
        _fm(_front_matter(pb)),
        f"# Page Blueprint — {pb.page_blueprint_id}\n",
        "## 1. Identity & Provenance\n",
        _identity(pb) + "\n",
        "## 2. Page Identity\n",
        _page_identity_section(pb) + "\n",
        "## 3. Visual Identity & Tone of Voice (Musical DNA §9)\n",
        _visual_identity_section(pb) + "\n",
        "## 4. Asset Link (carried from Cluster Strategy — never re-decided)\n",
        _asset_section(pb) + "\n",
        "## 5. Content Framing (page-level pillars only — not a content system)\n",
        _content_framing_section(pb) + "\n",
        "## 6. Evaluation & Confidence\n",
        _evaluation_section(pb) + "\n",
        "## 7. Recommendation\n",
        _recommendation_section(pb) + "\n",
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_report(
    pb: PageBlueprint, *, reports_dir: Union[str, Path],
) -> Tuple[Path, Path]:
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    stem = pb.cluster_strategy.opportunity_id
    report_path = reports_dir / f"{stem}.md"
    sidecar_path = reports_dir / f"{stem}.json"
    write_text(report_path, render_markdown(pb))
    write_json(sidecar_path, encode(pb))
    return report_path, sidecar_path
