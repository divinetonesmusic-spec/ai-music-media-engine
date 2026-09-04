"""The Claude sub-step of Page Blueprint (contract §4.2–§4.7).

Claude decides: the page identity (name/positioning/bio), the visual identity +
tone of voice (grounded in business-dna §9), the page-level content pillars,
platforms, posting cadence, confidence + red flags, and the recommendation.
Deterministic code (orchestrator) owns everything that must be well-formed,
traceable, asset-honest and in-scope — including the asset decision itself,
which Claude never sees as a decision to make (it is carried, D-PB-3).

One structured-output-free call per opportunity (prompt-guided JSON, same
reasoning as Cluster Strategy/Evaluation). A malformed response is a
``ResponseRejected`` — a hard failure the owner re-runs, never a silent
business state.
"""

from __future__ import annotations

import json
from typing import Optional, Sequence

from market_intelligence.schema.enums import Confidence, RedFlagKind, Severity
from market_intelligence.schema.models import Guardrail

from .llm import ResponseRejected, StageClient, StageError, call_stage, stage_key  # noqa: F401
from .schema.enums import PageBlueprintTargetNextStage
from .schema.models import ClusterStrategySnapshot

STAGE = "page_blueprint"

_CONFS = {c.value for c in Confidence}
_SEVERITIES = {s.value for s in Severity}
_RF_KINDS = {k.value for k in RedFlagKind}
_NEXT_STAGES = {s.value for s in PageBlueprintTargetNextStage}


# --- strict response shape check (deviation -> ResponseRejected) ------------

def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise ResponseRejected(f"{STAGE}: {msg}")


def reject_malformed_blueprint(raw: object) -> dict:
    _need(isinstance(raw, dict), "response is not a JSON object")
    assert isinstance(raw, dict)

    ident = raw.get("identity")
    _need(isinstance(ident, dict), "identity missing/not an object")
    assert isinstance(ident, dict)
    for k in ("concept_name", "positioning_statement", "bio"):
        _need(bool(str(ident.get(k, "")).strip()), f"identity.{k} empty")

    vis = raw.get("visual_identity")
    _need(isinstance(vis, dict), "visual_identity missing/not an object")
    assert isinstance(vis, dict)
    for k in ("visual_language", "tone_of_voice", "musical_dna_expression_used"):
        _need(bool(str(vis.get(k, "")).strip()), f"visual_identity.{k} empty")

    cf = raw.get("content_framing")
    _need(isinstance(cf, dict), "content_framing missing/not an object")
    assert isinstance(cf, dict)
    pillars = cf.get("content_pillars")
    _need(isinstance(pillars, list) and bool(pillars)
          and all(isinstance(p, str) and p.strip() for p in pillars),
          "content_framing.content_pillars must be a non-empty list of non-empty strings")
    platforms = cf.get("platforms")
    _need(isinstance(platforms, list) and bool(platforms)
          and all(isinstance(p, str) and p.strip() for p in platforms),
          "content_framing.platforms must be a non-empty list of non-empty strings")
    _need(bool(str(cf.get("posting_cadence", "")).strip()), "content_framing.posting_cadence empty")

    ev = raw.get("evaluation")
    _need(isinstance(ev, dict), "evaluation missing/not an object")
    assert isinstance(ev, dict)
    _need(ev.get("overall_confidence") in _CONFS,
          f"evaluation.overall_confidence invalid: {ev.get('overall_confidence')!r}")
    _need(bool(str(ev.get("justification", "")).strip()), "evaluation.justification empty")
    bb = ev.get("blocked_by", [])
    _need(isinstance(bb, list) and all(isinstance(x, str) for x in bb),
          "evaluation.blocked_by must be a list of strings")

    rfs = raw.get("red_flags", [])
    _need(isinstance(rfs, list), "red_flags must be a list")
    for i, rf in enumerate(rfs):
        _need(isinstance(rf, dict), f"red_flags[{i}] not an object")
        _need(bool(str(rf.get("description", "")).strip()), f"red_flags[{i}].description empty")
        _need(rf.get("severity") in _SEVERITIES, f"red_flags[{i}].severity invalid")
        _need(rf.get("kind") in _RF_KINDS, f"red_flags[{i}].kind invalid: {rf.get('kind')!r}")

    rec = raw.get("recommendation")
    _need(isinstance(rec, dict), "recommendation missing/not an object")
    assert isinstance(rec, dict)
    _need(rec.get("target_next_stage") in _NEXT_STAGES,
          f"recommendation.target_next_stage invalid: {rec.get('target_next_stage')!r}")
    for k in ("recommended_next_step", "justification"):
        _need(bool(str(rec.get(k, "")).strip()), f"recommendation.{k} empty")

    from market_intelligence.schema.validate import scan_json_for_numeric_score
    hits = scan_json_for_numeric_score(raw)
    _need(not hits, f"a 0–100 score is forbidden (C6): {hits[0] if hits else ''}")

    return raw


# --- prompt ------------------------------------------------------------

def build_prompt(
    snapshot: ClusterStrategySnapshot,
    *,
    section_9_markdown: str,
    cluster_expression_hint: Optional[str],
    guardrails: Sequence[Guardrail],
    page_context: dict,
    musical_dna_needs_input: bool,
) -> str:
    snap_json = json.dumps({
        "cluster_id": snapshot.cluster_id,
        "cluster_name": snapshot.cluster_name,
        "subcluster_or_angle": snapshot.subcluster_or_angle,
        "central_concept": snapshot.central_concept,
        "positioning_statement": snapshot.positioning_statement,
        "editorial_promise": snapshot.editorial_promise,
        "market": snapshot.market.value,
        "language": snapshot.language.value,
        "consumption_context": snapshot.consumption_context,
        "music_relationship": snapshot.music_relationship,
        "first_content_direction": snapshot.first_content_direction,
        "editorial_angles": snapshot.editorial_angles,
    }, ensure_ascii=False, indent=1)
    guardrail_lines = "\n".join(
        f"  {g.guardrail_id} ({g.type.value}, severity {g.severity.value}): {g.description}"
        for g in guardrails
    )
    hint_line = (
        f"§9.9 EXPRESSION HINT for this cluster: {cluster_expression_hint}\n\n"
        if cluster_expression_hint else
        "No pre-matched §9.9 expression line for this cluster name — find the closest fit "
        "yourself in the §9 text below, or state that none fits closely (blocked_by).\n\n"
    )
    dna_rule = (
        "Musical DNA (§9) is NEEDS_INPUT — ground visual_identity/tone_of_voice as best you "
        "can from the cluster's positioning alone, set musical_dna_expression_used to a short "
        "note that §9 is unavailable, and evaluation.overall_confidence MUST be LOW or MEDIUM."
        if musical_dna_needs_input else
        "Musical DNA (§9) is OWNER-APPROVED — visual_identity and tone_of_voice MUST be "
        "grounded in the house-sound principle and this cluster's §9.9 expression below. "
        "musical_dna_expression_used must quote or closely paraphrase that expression."
    )
    return (
        "You are the PAGE BLUEPRINT step (canonical pipeline stage 4). You receive ONE "
        "Cluster Strategy recommended for Page Blueprint and design the concrete page. "
        "Autonomy Level 1 — you recommend, the owner decides; nothing here creates a page.\n\n"
        "HARD RULES:\n"
        "- NO 0–100 score anywhere. overall_confidence is LOW/MEDIUM/HIGH only.\n"
        "- Do NOT decide the asset (which page/playlist/artist) — that was already decided by "
        "Cluster Strategy (I5) and is given to you below as PAGE CONTEXT, for reference only. "
        "Never propose a different asset or a new one.\n"
        "- Do NOT produce a content system (formats, hooks, structures, CTA copy, linguistic/"
        "visual production rules, a posting calendar) — that is Content Strategy (stage 5). "
        "content_pillars is a short list (<=5) of BROAD thematic pillars only, not specific "
        "content ideas.\n"
        f"- {dna_rule}\n\n"
        "COMPLIANCE — flag CLAIMS, not TOPICS (same standard as Evaluation/Cluster Strategy). "
        "Positioning/bio/tone-of-voice may describe experience, ritual, intention and "
        "atmosphere; they must never assert a health/medical claim, cure, or guaranteed "
        "outcome. Guardrails:\n"
        f"{guardrail_lines}\n\n"
        f"CLUSTER STRATEGY (context — do not re-decide the cluster):\n{snap_json}\n\n"
        f"PAGE CONTEXT (carried asset decision — reference only, never re-decide):\n"
        f"{json.dumps(page_context, ensure_ascii=False, indent=1)}\n\n"
        f"{hint_line}"
        f"BUSINESS DNA §9 — MUSICAL DNA (full section):\n{section_9_markdown}\n\n"
        "OUTPUT — return ONE JSON object and nothing else. Exactly this shape:\n"
        "{\n"
        '  "identity": {"concept_name": "", "positioning_statement": "", "bio": ""},\n'
        '  "visual_identity": {"visual_language": "", "tone_of_voice": "", '
        '"musical_dna_expression_used": ""},\n'
        '  "content_framing": {"content_pillars": ["<=5 short items"], '
        '"platforms": ["<one or more>"], "posting_cadence": "<qualitative, e.g. 3-4x/week>"},\n'
        '  "evaluation": {"overall_confidence": "LOW|MEDIUM|HIGH", "justification": "", '
        '"blocked_by": ["<NEEDS_INPUT/UNKNOWN item>", ...]},\n'
        '  "red_flags": [{"description": "", "severity": "LOW|MEDIUM|HIGH", '
        '"kind": "compliance|feasibility|evidence_gap|asset_gap|other"}],  // [] if none\n'
        '  "recommendation": {"target_next_stage": '
        '"CONTENT_STRATEGY|BACK_TO_CLUSTER_STRATEGY|HOLD", '
        '"recommended_next_step": "<concrete, still a recommendation>", "justification": ""}\n'
        "}\n"
        "Every string is non-empty. Use the exact enum spellings. NO numeric score anywhere."
    )


def run_blueprint(
    snapshot: ClusterStrategySnapshot,
    *,
    section_9_markdown: str,
    cluster_expression_hint: Optional[str],
    guardrails: Sequence[Guardrail],
    page_context: dict,
    musical_dna_needs_input: bool,
    client: StageClient,
    model: str,
) -> dict:
    prompt = build_prompt(
        snapshot,
        section_9_markdown=section_9_markdown,
        cluster_expression_hint=cluster_expression_hint,
        guardrails=guardrails,
        page_context=page_context,
        musical_dna_needs_input=musical_dna_needs_input,
    )
    return call_stage(
        client,
        stage=STAGE,
        key=stage_key(STAGE, snapshot.opportunity_id),
        prompt=prompt,
        schema={},  # prompt-guided — RecordedStageClient ignores it, live client sends none
        model=model,
        validate=reject_malformed_blueprint,
    )
