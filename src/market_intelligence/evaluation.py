"""Evaluation — spec §8, §9, §12.4, §18 component 5, §19.

Claude rates the 10 evaluation dimensions (§8.1), builds the 5-axis Business
Outcome Profile (§9.1), lists red flags and produces the ``Recommendation``.
Deterministic code checks completeness, bans any 0–100 score (C6), caps
``music_fit`` confidence while musical DNA is ``NEEDS_INPUT`` (§8.3), constrains
``target_state`` to ``EXPLORE`` / ``TEST`` / ``PARK`` and attaches the fixed
``execution_note`` (§12.4), and runs the ``guardrails.yaml`` compliance check
(§13) over every piece of generated free text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from .framing import FramedOpportunity
from .guardrails import (
    SCOPE_BOP_JUSTIFICATION,
    SCOPE_EVAL_JUSTIFICATION,
    SCOPE_EVAL_SUMMARY,
    SCOPE_EVIDENCE,
    SCOPE_HYPOTHESES_DIRECTION,
    SCOPE_HYPOTHESES_HOOK,
    SCOPE_HYPOTHESES_POSITIONING,
    SCOPE_RECOMMENDATION,
    SCOPE_REPORT_PROSE,
    ComplianceResult,
    check_texts,
)
from .knowledge_loader import KnowledgeBundle
from .llm_stage import (
    ResponseRejected,
    StageClient,
    StageError,
    call_stage,
    enum_str,
    obj_schema,
    select_stage_client,
    stage_key,
)
from .schema.enums import (
    AXIS_KEYS,
    DIMENSION_KEYS,
    Confidence,
    LifecycleState,
    Rating,
    RedFlagKind,
    Severity,
)
from .schema.models import (
    EXECUTION_NOTE,
    AssetMatch,
    AxisRating,
    BusinessOutcomeProfile,
    DimensionRating,
    Evaluation,
    Recommendation,
    RedFlag,
    RunConfig,
)
from .schema.validate import (
    blocking,
    validate_business_outcome_profile,
    validate_evaluation,
)

SCHEMA_VERSION = "1.0.0"
STAGE = "evaluation"

_CONF_ORDER = [Confidence.LOW, Confidence.MEDIUM, Confidence.HIGH]
_V1_TARGET_STATES = {LifecycleState.EXPLORE, LifecycleState.TEST, LifecycleState.PARK}


@dataclass
class EvaluationBundle:
    opportunity_id: str
    evaluation: Evaluation
    business_outcome_profile: BusinessOutcomeProfile
    recommendation: Recommendation
    compliance: ComplianceResult
    excluded: bool = False
    exclusion_reason: Optional[str] = None
    stripped_hypothesis_scopes: set = field(default_factory=set)


@dataclass
class EvaluationResult:
    bundles: Dict[str, EvaluationBundle]
    llm_mode: str = "recorded"


# --- response schema -------------------------------------------

def _rated(extra_required=()) -> dict:
    props = {
        "rating": enum_str([r.value for r in Rating]),
        "confidence": enum_str([c.value for c in Confidence]),
        "justification": {"type": "string"},
        "blocked_by": {"type": "array", "items": {"type": "string"}},
    }
    return obj_schema(props, ["rating", "confidence", "justification", *extra_required])


def _response_schema() -> dict:
    return obj_schema(
        {
            "dimensions": obj_schema({k: _rated() for k in DIMENSION_KEYS}, list(DIMENSION_KEYS)),
            "business_outcome_profile": obj_schema(
                {k: _rated() for k in AXIS_KEYS}, list(AXIS_KEYS)
            ),
            "red_flags": {
                "type": "array",
                "items": obj_schema(
                    {
                        "description": {"type": "string"},
                        "severity": enum_str([s.value for s in Severity]),
                        "kind": enum_str([k.value for k in RedFlagKind]),
                    },
                    ["description", "severity", "kind"],
                ),
            },
            "overall_confidence": enum_str([c.value for c in Confidence]),
            "summary": {"type": "string"},
            "recommendation": obj_schema(
                {
                    "target_state": enum_str([s.value for s in LifecycleState]),
                    "suggested_next_step": {"type": "string"},
                    "justification": {"type": "string"},
                    "confidence": enum_str([c.value for c in Confidence]),
                },
                ["target_state", "suggested_next_step", "justification", "confidence"],
            ),
        },
        ["dimensions", "business_outcome_profile", "red_flags", "overall_confidence",
         "summary", "recommendation"],
    )


# --- prompt ---------------------------------------------------

def _prompt(opp: FramedOpportunity, am: AssetMatch, knowledge: KnowledgeBundle) -> str:
    evidence = [
        {"type": e.type.value, "statement": e.statement, "confidence": e.confidence.value,
         "signal_ids": e.signal_ids, "rationale": e.rationale}
        for e in opp.evidence
    ]
    asset = {
        "best_playlist": am.best_playlist,
        "best_page": am.best_page,
        "best_artist": am.best_artist,
        "matching_counts": {
            "playlists": len(am.matching_playlists),
            "pages": len(am.matching_pages),
            "artists": len(am.matching_artists),
        },
        "new_asset_recommended": am.new_asset_recommendation is not None,
        "unmatched_reason": am.unmatched_reason,
    }
    opp_json = json.dumps(
        {
            "title": opp.title, "need": opp.need, "audience": opp.audience.description,
            "market": opp.market.value, "language": opp.language.value,
            "platform": opp.platform.value, "consumption_context": opp.consumption_context,
            "durability": opp.durability.value, "urgency": opp.urgency.value,
        },
        ensure_ascii=False, indent=1,
    )
    guardrail_lines = "\n".join(
        f"  {g.guardrail_id} ({g.type.value}, severity {g.severity.value}): {g.description}"
        for g in knowledge.guardrails
    )
    return (
        "You are the Evaluation step. Assess ONE opportunity. Output a qualitative "
        "profile — there is NO 0-100 score anywhere.\n\n"
        f"Rate ALL 10 dimensions ({', '.join(DIMENSION_KEYS)}) and ALL 5 Business Outcome "
        f"axes ({', '.join(AXIS_KEYS)}). Each: rating LOW/MEDIUM/HIGH/VERY_HIGH, a SEPARATE "
        "confidence LOW/MEDIUM/HIGH, and a justification citing specific evidence.\n\n"
        "Rules:\n"
        "- A dimension you cannot rate from the evidence MUST be rating:LOW, confidence:LOW "
        "with blocked_by naming the missing input. Never guess.\n"
        "- music_fit: the business's musical DNA detail is NEEDS_INPUT, so music_fit "
        "confidence MUST be LOW or MEDIUM. A catalog-affinity mismatch is NOT a blocker.\n"
        "- overall_confidence MUST NOT be raised by high dimension ratings — it reflects how "
        "much you actually know.\n"
        "- red_flags: compliance / feasibility / evidence_gap / asset_gap / market / other.\n"
        "- recommendation.target_state: EXPLORE, TEST or PARK only. suggested_next_step is a "
        "concrete action — still a recommendation, never executed in V1.\n\n"
        "COMPLIANCE SELF-CHECK (decision C4). Review every piece of text you write — "
        "evidence, justifications, summary, recommendation, and the opportunity's "
        "hypotheses — against these guardrails:\n"
        f"{guardrail_lines}\n"
        "For each guardrail your text would violate, add a red_flag with kind:'compliance', "
        "the guardrail's severity, and a description naming the guardrail id and what is "
        "wrong. Then FIX your own text so it no longer violates it (state the uncertainty "
        "instead of inventing; drop the claim; reframe as subjective experience). Do not "
        "leave a violating sentence in place.\n\n"
        f"OPPORTUNITY:\n{opp_json}\n\n"
        f"EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False, indent=1)}\n\n"
        f"ASSET FIT:\n{json.dumps(asset, ensure_ascii=False, indent=1)}\n\n"
        "Return the JSON object matching the schema exactly."
    )


# --- deterministic assembly --------------------------------

def _clean(v) -> str:
    return (v or "").strip() if isinstance(v, str) else ""


def _rating(v, default=Rating.LOW) -> Rating:
    try:
        return Rating(v)
    except ValueError:
        return default


def _confidence(v, default=Confidence.LOW) -> Confidence:
    try:
        return Confidence(v)
    except ValueError:
        return default


def _dimension(raw) -> DimensionRating:
    raw = raw if isinstance(raw, dict) else {}
    justification = _clean(raw.get("justification"))
    blocked = [b for b in (raw.get("blocked_by") or []) if isinstance(b, str)]
    if not justification:
        justification = "Not rateable from the available evidence."
        blocked = blocked or ["insufficient evidence"]
    return DimensionRating(
        rating=_rating(raw.get("rating")),
        confidence=_confidence(raw.get("confidence")),
        justification=justification,
        blocked_by=blocked or None,
    )


def _axis(raw) -> AxisRating:
    raw = raw if isinstance(raw, dict) else {}
    justification = _clean(raw.get("justification")) or "Not rateable from the available evidence."
    return AxisRating(
        rating=_rating(raw.get("rating")),
        confidence=_confidence(raw.get("confidence")),
        justification=justification,
    )


def _lowest_confidence(dims: Dict[str, DimensionRating]) -> Confidence:
    return min((d.confidence for d in dims.values()), key=_CONF_ORDER.index, default=Confidence.LOW)


def _red_flags(raw) -> List[RedFlag]:
    out: List[RedFlag] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        desc = _clean(item.get("description"))
        if not desc:
            continue
        try:
            severity = Severity(item.get("severity", "LOW"))
            kind = RedFlagKind(item.get("kind", "other"))
        except ValueError:
            severity, kind = Severity.LOW, RedFlagKind.OTHER
        out.append(RedFlag(description=desc, severity=severity, kind=kind))
    return out


def _constrain_target_state(raw) -> LifecycleState:
    try:
        state = LifecycleState(raw)
    except ValueError:
        return LifecycleState.EXPLORE
    if state in _V1_TARGET_STATES:
        return state
    if state is LifecycleState.KILL:
        return LifecycleState.PARK
    return LifecycleState.TEST  # LAUNCH / SCALE → TEST (§5)


def _texts_for_compliance(opp: FramedOpportunity, ev: Evaluation, bop: BusinessOutcomeProfile,
                          rec: Recommendation) -> Dict[str, Sequence[str]]:
    dim_justifications = [d.justification for d in ev.dimensions.values()]
    axis_justifications = [a.justification for a in bop.axes.values()]
    evidence_text = [e.statement for e in opp.evidence] + \
                    [e.rationale for e in opp.evidence if e.rationale]
    rec_text = [rec.suggested_next_step, rec.justification]

    texts: Dict[str, List[str]] = {
        SCOPE_EVIDENCE: evidence_text,
        SCOPE_EVAL_JUSTIFICATION: dim_justifications,
        SCOPE_EVAL_SUMMARY: [ev.summary],
        SCOPE_BOP_JUSTIFICATION: axis_justifications,
        SCOPE_RECOMMENDATION: rec_text,
        # everything that will be rendered verbatim as report prose (§12.3) is also
        # checked against the report_prose scope — that is where G01 / G03 apply.
        SCOPE_REPORT_PROSE: (
            [ev.summary, *dim_justifications, *axis_justifications, *rec_text, *evidence_text]
        ),
    }
    # Hypothesis fields are checked under their own scopes only — a violation there is
    # STRIPPED, not excluded (§14). They are not folded into the report_prose bucket.
    if opp.hypotheses:
        if opp.hypotheses.potential_positioning:
            texts[SCOPE_HYPOTHESES_POSITIONING] = [opp.hypotheses.potential_positioning]
        if opp.hypotheses.first_content_direction:
            texts[SCOPE_HYPOTHESES_DIRECTION] = [opp.hypotheses.first_content_direction]
        if opp.hypotheses.hook:
            texts[SCOPE_HYPOTHESES_HOOK] = [opp.hypotheses.hook]
    return texts


def _build_bundle(
    opp: FramedOpportunity, am: AssetMatch, raw: dict, *, config: RunConfig,
    musical_dna_needs_input: bool, guardrails,
) -> EvaluationBundle:
    raw = raw if isinstance(raw, dict) else {}
    dim_raw = raw.get("dimensions") or {}
    dimensions = {k: _dimension(dim_raw.get(k)) for k in DIMENSION_KEYS}

    if musical_dna_needs_input and dimensions["music_fit"].confidence is Confidence.HIGH:
        dimensions["music_fit"].confidence = Confidence.MEDIUM
        blocked = list(dimensions["music_fit"].blocked_by or [])
        if "musical DNA (NEEDS_INPUT)" not in blocked:
            blocked.append("musical DNA (NEEDS_INPUT)")
        dimensions["music_fit"].blocked_by = blocked

    bop_raw = raw.get("business_outcome_profile") or {}
    axes = {k: _axis(bop_raw.get(k)) for k in AXIS_KEYS}
    bop = BusinessOutcomeProfile(schema_version=SCHEMA_VERSION, axes=axes)

    overall = _confidence(raw.get("overall_confidence"), _lowest_confidence(dimensions))

    evaluation = Evaluation(
        schema_version=SCHEMA_VERSION,
        dimensions=dimensions,
        red_flags=_red_flags(raw.get("red_flags")),
        overall_confidence=overall,
        summary=_clean(raw.get("summary")) or "No synthesis was produced for this opportunity.",
    )

    rec_raw = raw.get("recommendation") or {}
    target_state = _constrain_target_state(rec_raw.get("target_state"))
    recommendation = Recommendation(
        schema_version=SCHEMA_VERSION,
        target_state=target_state,
        suggested_next_step=_clean(rec_raw.get("suggested_next_step"))
        or "Review this opportunity before deciding on a test.",
        justification=_clean(rec_raw.get("justification"))
        or "Recommendation grounded in the evaluation profile and red flags.",
        confidence=_confidence(rec_raw.get("confidence"), overall),
        execution_note=EXECUTION_NOTE,
    )

    # --- compliance check over every generated free text (§13) ---
    compliance = check_texts(
        _texts_for_compliance(opp, evaluation, bop, recommendation), guardrails=guardrails
    )
    for rf in compliance.red_flags:
        if rf.description not in {x.description for x in evaluation.red_flags}:
            evaluation.red_flags.append(rf)

    bundle = EvaluationBundle(
        opportunity_id=opp.opportunity_id,
        evaluation=evaluation,
        business_outcome_profile=bop,
        recommendation=recommendation,
        compliance=compliance,
        stripped_hypothesis_scopes=set(compliance.strip_scopes),
    )

    # --- deterministic validation (§13) ---
    errs = blocking(validate_evaluation(
        evaluation, musical_dna_needs_input=musical_dna_needs_input
    )) + blocking(validate_business_outcome_profile(bop))
    if errs:
        bundle.excluded = True
        bundle.exclusion_reason = "; ".join(f"[{e.code}] {e.message}" for e in errs[:3])
    elif compliance.exclude_opportunity:
        bundle.excluded = True
        bundle.exclusion_reason = (
            "compliance: a HIGH-severity guardrail violation in core content "
            "(spec §13, §14)"
        )
    return bundle


# --- entry point --------------------------------------------

def evaluate_opportunities(
    opportunities: Sequence[FramedOpportunity],
    asset_matches: Dict[str, AssetMatch],
    *,
    knowledge: KnowledgeBundle,
    config: RunConfig,
    project_root: Union[str, Path],
    client: Optional[StageClient] = None,
    musical_dna_needs_input: bool = True,
) -> EvaluationResult:
    active, mode = select_stage_client(config, project_root, client=client)
    bundles: Dict[str, EvaluationBundle] = {}

    for opp in opportunities:
        am = asset_matches.get(opp.opportunity_id)
        if am is None:
            continue
        try:
            raw = call_stage(
                active,
                stage=STAGE,
                key=stage_key(STAGE, opp.opportunity_id),
                prompt=_prompt(opp, am, knowledge),
                schema=_response_schema(),
                model=config.model,
                validate=lambda r: r,
            )
        except (StageError, ResponseRejected) as e:
            # §14 — an opportunity Claude could not evaluate is excluded, run continues.
            bundles[opp.opportunity_id] = _excluded_bundle(
                opp.opportunity_id, f"Evaluation could not run: {e}"
            )
            continue
        bundles[opp.opportunity_id] = _build_bundle(
            opp, am, raw, config=config,
            musical_dna_needs_input=musical_dna_needs_input,
            guardrails=knowledge.guardrails,
        )

    return EvaluationResult(bundles=bundles, llm_mode=mode)


def _excluded_bundle(opportunity_id: str, reason: str) -> EvaluationBundle:
    """A minimal, schema-shaped bundle marked excluded (no model output available)."""
    dims = {
        k: DimensionRating(rating=Rating.LOW, confidence=Confidence.LOW,
                           justification="Not evaluated.", blocked_by=["evaluation failed"])
        for k in DIMENSION_KEYS
    }
    axes = {
        k: AxisRating(rating=Rating.LOW, confidence=Confidence.LOW, justification="Not evaluated.")
        for k in AXIS_KEYS
    }
    evaluation = Evaluation(
        schema_version=SCHEMA_VERSION, dimensions=dims, red_flags=[],
        overall_confidence=Confidence.LOW, summary="This opportunity was not evaluated.",
    )
    rec = Recommendation(
        schema_version=SCHEMA_VERSION, target_state=LifecycleState.PARK,
        suggested_next_step="Re-run the evaluation for this opportunity.",
        justification=reason, confidence=Confidence.LOW, execution_note=EXECUTION_NOTE,
    )
    return EvaluationBundle(
        opportunity_id=opportunity_id, evaluation=evaluation,
        business_outcome_profile=BusinessOutcomeProfile(schema_version=SCHEMA_VERSION, axes=axes),
        recommendation=rec, compliance=ComplianceResult(),
        excluded=True, exclusion_reason=reason,
    )
