"""The Claude sub-step of Cluster Strategy (contract §3, §4.2/§4.3/§4.5–§4.7).

Claude decides: the cluster decision (map / propose / defer / reject) + the
strategic definition + the content direction + the 4 qualitative dimensions +
the recommendation. Deterministic code (orchestrator) owns everything that must
be well-formed, traceable, asset-honest and in-scope.

One structured-output-free call per opportunity (prompt-guided JSON). A malformed
response is a ``ResponseRejected`` — a hard failure the owner re-runs, never a
silent business state.
"""

from __future__ import annotations

import json
from typing import Optional, Sequence

from market_intelligence.schema.enums import Confidence, Rating, RedFlagKind, Severity
from market_intelligence.schema.models import Guardrail, Opportunity

from .llm import ResponseRejected, StageClient, call_stage, stage_key
from .schema.enums import CLUSTER_DIMENSION_KEYS, ClusterDecisionKind, TargetNextStage
from .schema.models import OpportunitySnapshot

STAGE = "cluster_strategy"

_RATINGS = {r.value for r in Rating}
_CONFS = {c.value for c in Confidence}
_SEVERITIES = {s.value for s in Severity}
_RF_KINDS = {k.value for k in RedFlagKind} | {"taxonomy"}
_DECISIONS = {d.value for d in ClusterDecisionKind}
_NEXT_STAGES = {s.value for s in TargetNextStage}


# --- strict response shape check (deviation -> ResponseRejected) ------------

def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise ResponseRejected(f"{STAGE}: {msg}")


def _rating_node(node: object, path: str) -> None:
    _need(isinstance(node, dict), f"{path} is not an object")
    _need(node.get("rating") in _RATINGS, f"{path}.rating invalid: {node.get('rating')!r}")
    _need(node.get("confidence") in _CONFS, f"{path}.confidence invalid")
    _need(bool(str(node.get("justification", "")).strip()), f"{path}.justification empty")


def reject_malformed_strategy(raw: object) -> dict:
    _need(isinstance(raw, dict), "response is not a JSON object")
    assert isinstance(raw, dict)

    cd = raw.get("cluster_decision")
    _need(isinstance(cd, dict), "cluster_decision missing/not an object")
    _need(cd.get("decision") in _DECISIONS,
          f"cluster_decision.decision invalid: {cd.get('decision')!r}")
    _need(bool(str(cd.get("justification", "")).strip()), "cluster_decision.justification empty")
    _need(bool(str(cd.get("framing_hypothesis_comparison", "")).strip()),
          "cluster_decision.framing_hypothesis_comparison empty")
    decision = cd["decision"]

    if decision == "MAP_TO_EXISTING":
        _need(bool(str(cd.get("cluster_id", "")).strip()),
              "MAP_TO_EXISTING requires cluster_id")
    if decision == "PROPOSE_NEW_CLUSTER":
        p = cd.get("new_cluster_proposal")
        _need(isinstance(p, dict), "PROPOSE_NEW_CLUSTER requires new_cluster_proposal")
        assert isinstance(p, dict)
        for k in ("proposed_id", "proposed_name", "concept", "why_not_subcluster"):
            _need(bool(str(p.get(k, "")).strip()), f"new_cluster_proposal.{k} empty")
        _need(isinstance(p.get("boundary_vs_adjacent"), dict) and p["boundary_vs_adjacent"],
              "new_cluster_proposal.boundary_vs_adjacent must be a non-empty map")
        _need(isinstance(p.get("supporting_evidence"), list) and p["supporting_evidence"],
              "new_cluster_proposal.supporting_evidence must be a non-empty list")
    if decision == "DEFER":
        _need(bool(str(cd.get("deferral_reason", "")).strip()), "DEFER requires deferral_reason")
    if decision == "REJECT":
        _need(bool(str(cd.get("rejection_reason", "")).strip()), "REJECT requires rejection_reason")

    if decision in ("MAP_TO_EXISTING", "PROPOSE_NEW_CLUSTER"):
        sd = raw.get("strategic_definition")
        _need(isinstance(sd, dict), f"{decision} requires strategic_definition")
        assert isinstance(sd, dict)
        for k in ("central_concept", "audience_description", "intent", "emotional_state",
                  "editorial_promise", "positioning_statement", "localization_notes",
                  "durability_read", "strategic_coherence_note"):
            _need(bool(str(sd.get(k, "")).strip()), f"strategic_definition.{k} empty")
        cdir = raw.get("content_direction")
        _need(isinstance(cdir, dict), f"{decision} requires content_direction")
        assert isinstance(cdir, dict)
        for k in ("first_content_direction", "music_relationship"):
            _need(bool(str(cdir.get(k, "")).strip()), f"content_direction.{k} empty")
        _need(isinstance(cdir.get("editorial_angles", []), list),
              "content_direction.editorial_angles must be a list")

    dims = raw.get("dimensions")
    _need(isinstance(dims, dict), "dimensions missing/not an object")
    assert isinstance(dims, dict)
    _need(set(dims) == set(CLUSTER_DIMENSION_KEYS),
          f"dimensions must be exactly {CLUSTER_DIMENSION_KEYS}; got {sorted(dims)}")
    for k, node in dims.items():
        _rating_node(node, f"dimensions.{k}")
        bb = node.get("blocked_by")
        _need(bb is None or (isinstance(bb, list) and all(isinstance(x, str) for x in bb)),
              f"dimensions.{k}.blocked_by must be a list of strings or absent")

    _need(raw.get("overall_confidence") in _CONFS,
          f"overall_confidence invalid: {raw.get('overall_confidence')!r}")

    rfs = raw.get("red_flags", [])
    _need(isinstance(rfs, list), "red_flags must be a list")
    for i, rf in enumerate(rfs):
        _need(isinstance(rf, dict), f"red_flags[{i}] not an object")
        _need(bool(str(rf.get("description", "")).strip()), f"red_flags[{i}].description empty")
        _need(rf.get("severity") in _SEVERITIES, f"red_flags[{i}].severity invalid")
        _need(rf.get("kind") in _RF_KINDS, f"red_flags[{i}].kind invalid: {rf.get('kind')!r}")

    oq = raw.get("open_questions", [])
    _need(isinstance(oq, list) and all(isinstance(x, str) for x in oq),
          "open_questions must be a list of strings")

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


# --- prompt ---------------------------------------------------------------

def _asset_summary(opp: Opportunity) -> dict:
    am = opp.asset_fit
    return {
        "best_playlist": am.best_playlist,
        "best_page": am.best_page,
        "best_artist": am.best_artist,
        "matching_counts": {
            "playlists": len(am.matching_playlists),
            "pages": len(am.matching_pages),
            "artists": len(am.matching_artists),
        },
        "new_asset_recommendation": (
            am.new_asset_recommendation.asset_type.value
            if am.new_asset_recommendation else None
        ),
        "unmatched_reason": am.unmatched_reason,
        "compliance_red_flags": [
            {"severity": rf.severity.value, "description": rf.description}
            for rf in opp.evaluation.red_flags if rf.kind is RedFlagKind.COMPLIANCE
        ],
    }


def build_prompt(
    snapshot: OpportunitySnapshot,
    opp: Opportunity,
    *,
    taxonomy_markdown: str,
    guardrails: Sequence[Guardrail],
    cluster_hint: Optional[str],
) -> str:
    evidence = [
        {"type": e.type.value, "statement": e.statement, "confidence": e.confidence.value,
         "signal_ids": e.signal_ids or [], "rationale": e.rationale}
        for e in opp.evidence
    ]
    opp_json = json.dumps({
        "title": snapshot.title, "need": snapshot.need,
        "audience": snapshot.audience_description,
        "audience_attributes": snapshot.audience_attributes,
        "market": snapshot.market.value, "language": snapshot.language.value,
        "platform": snapshot.platform, "consumption_context": snapshot.consumption_context,
        "durability": snapshot.durability.value, "urgency": snapshot.urgency.value,
        "overall_confidence": snapshot.overall_confidence.value,
        # the opportunity's ACTUAL lifecycle state — carry it, never transition it
        "lifecycle_status": snapshot.status.value,
        # a Market Intelligence RECOMMENDATION only ("advance to X"); NOT the current state
        "mi_recommended_target_state": snapshot.target_state.value,
        "potential_cluster_hypothesis": {
            "value": snapshot.potential_cluster_value,
            "canonical": snapshot.potential_cluster_canonical,
            "basis": snapshot.potential_cluster_basis,
        },
    }, ensure_ascii=False, indent=1)
    guardrail_lines = "\n".join(
        f"  {g.guardrail_id} ({g.type.value}, severity {g.severity.value}): {g.description}"
        for g in guardrails
    )
    hint = (
        f"Deterministic pre-normalisation resolved the cluster hypothesis to the canonical "
        f"id '{cluster_hint}'. Confirm or override it against the taxonomy boundaries."
        if cluster_hint else
        "Deterministic pre-normalisation did NOT match the cluster hypothesis to any of the "
        "11 canonical ids. Re-test it against every canonical cluster; only if it genuinely "
        "fits none AND is not a subcluster/angle of one, produce a new-cluster proposal."
    )
    return (
        "You are the CLUSTER STRATEGY step (canonical pipeline stage 3). You receive ONE "
        "owner-advanced Opportunity Report and produce the cluster decision + a strategic "
        "cluster definition. Autonomy Level 1 — you recommend, the owner decides.\n\n"
        "HARD RULES:\n"
        "- NO 0–100 score anywhere. Ratings are LOW/MEDIUM/HIGH/VERY_HIGH with a SEPARATE "
        "LOW/MEDIUM/HIGH confidence.\n"
        "- Do NOT transition the opportunity's lifecycle (EXPLORE/TEST/PARK) — that is the "
        "owner's. The opportunity is currently in `lifecycle_status`; "
        "`mi_recommended_target_state` is only what Market Intelligence recommended, NOT its "
        "current state. `target_next_stage` is a pipeline action, not a lifecycle state.\n"
        "- Do NOT design a page (name, bio, visual identity, tone of voice, cadence) — that "
        "is Page Blueprint (stage 4). Do NOT produce a content system (pillars, formats, "
        "hooks, structures, CTAs, visual language, schedules) — that is Content Strategy "
        "(stage 5). Give ONE non-binding first content direction and a few candidate angles "
        "only.\n"
        "- Do NOT invent an artist / playlist / page. The asset strategy is consolidated "
        "deterministically from the Opportunity Report — you only reason about the cluster.\n"
        "- A NEW canonical cluster is a PROPOSAL only (P6 deferred). Never claim to create one.\n\n"
        "COMPLIANCE — flag CLAIMS, not TOPICS. Naming a theme ('energetic cleansing', "
        "'432 Hz', 'sleep music') or an audience belief is fine. An efficacy claim about "
        "health ('removes negative energy' as fact, 'treats insomnia', 'cures anxiety'), "
        "presenting music as medical treatment, or 'scientifically proven' with no source is "
        "NOT. Write `emotional_state` and `editorial_promise` as subjective experience / "
        "intention / ritual (permitted, G02). Guardrails:\n"
        f"{guardrail_lines}\n\n"
        f"CLUSTER HINT: {hint}\n\n"
        "CANONICAL CLUSTER TAXONOMY (reason about each cluster's 'Fronteira conceitual'):\n"
        f"{taxonomy_markdown}\n\n"
        f"OPPORTUNITY:\n{opp_json}\n\n"
        f"EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False, indent=1)}\n\n"
        f"ASSET FIT (context only — you do not decide assets):\n"
        f"{json.dumps(_asset_summary(opp), ensure_ascii=False, indent=1)}\n\n"
        "OUTPUT — return ONE JSON object and nothing else. Exactly this shape:\n"
        "{\n"
        '  "cluster_decision": {"decision": "MAP_TO_EXISTING|PROPOSE_NEW_CLUSTER|DEFER|REJECT", '
        '"cluster_id": "<canonical id or null>", "subcluster_or_angle": "<text or null>", '
        '"is_new_subcluster": true|false|null, "framing_hypothesis_comparison": "<confirmed/'
        'overrode the hypothesis, why>", "justification": "<text citing the taxonomy boundary '
        '+ an evidence item>", "new_cluster_proposal": {"proposed_id": "", "proposed_name": "", '
        '"concept": "", "boundary_vs_adjacent": {"<canonical_id>": "<distinguishing sentence>"}, '
        '"why_not_subcluster": "", "supporting_evidence": ["<evidence ref>"]} , '
        '"deferral_reason": "<text or null>", "rejection_reason": "<text or null>"},\n'
        '  "strategic_definition": {  // null for DEFER/REJECT\n'
        '    "central_concept": "", "audience_description": "", "intent": "", '
        '"emotional_state": "", "editorial_promise": "", "positioning_statement": "", '
        '"localization_notes": "", "durability_read": "", "strategic_coherence_note": ""},\n'
        '  "content_direction": {  // null for DEFER/REJECT\n'
        '    "first_content_direction": "", "editorial_angles": ["", ""], '
        '"music_relationship": ""},\n'
        '  "dimensions": {  // ALL 4 keys, each {"rating": "...", "confidence": "...", '
        '"justification": "<cites evidence>", "blocked_by": ["<NEEDS_INPUT/UNKNOWN item>", ...]}\n'
        f'    {", ".join(CLUSTER_DIMENSION_KEYS)} }},\n'
        '  "overall_confidence": "LOW|MEDIUM|HIGH",  // MUST NOT exceed the opportunity\'s; '
        'not raised by high dimension ratings\n'
        '  "red_flags": [{"description": "", "severity": "LOW|MEDIUM|HIGH", '
        '"kind": "compliance|feasibility|evidence_gap|asset_gap|taxonomy|other"}],  // [] if none\n'
        '  "open_questions": ["<what the owner / a downstream stage must resolve>"],\n'
        '  "recommendation": {"target_next_stage": "PAGE_BLUEPRINT|FORMALIZE_CLUSTER|'
        'BACK_TO_MARKET_INTELLIGENCE|HOLD", "recommended_next_step": "<concrete, still a '
        'recommendation>", "justification": ""}\n'
        "}\n"
        "Every string is non-empty. Use the exact enum spellings. NO numeric score anywhere."
    )


def run_strategy(
    snapshot: OpportunitySnapshot,
    opp: Opportunity,
    *,
    taxonomy_markdown: str,
    guardrails: Sequence[Guardrail],
    cluster_hint: Optional[str],
    client: StageClient,
    model: str,
) -> dict:
    prompt = build_prompt(
        snapshot, opp, taxonomy_markdown=taxonomy_markdown,
        guardrails=guardrails, cluster_hint=cluster_hint,
    )
    return call_stage(
        client,
        stage=STAGE,
        key=stage_key(STAGE, snapshot.opportunity_id),
        prompt=prompt,
        schema={},  # prompt-guided — RecordedStageClient ignores it, live client sends none
        model=model,
        validate=reject_malformed_strategy,
    )
