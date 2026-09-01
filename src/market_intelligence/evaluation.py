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
    MissingFixtureError,
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
    scan_json_for_numeric_score,
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
    # ``evaluation`` / ``business_outcome_profile`` / ``recommendation`` are ``None``
    # only for a ``technical_failure`` — the model call itself could not complete, so
    # no profile and (crucially) no business ``Recommendation`` exists.
    evaluation: Optional[Evaluation]
    business_outcome_profile: Optional[BusinessOutcomeProfile]
    recommendation: Optional[Recommendation]
    compliance: ComplianceResult
    # ``excluded`` is a BUSINESS decision from a completed evaluation — a HIGH-severity
    # guardrail violation in core content, or a §13 validation failure.
    excluded: bool = False
    exclusion_reason: Optional[str] = None
    # ``technical_failure`` is an INFRASTRUCTURE failure of the Evaluation call
    # (API error, timeout, unparseable / over-limit response). It is NOT a business
    # state: no PARK, no exclusion, never written to the opportunity registry.
    technical_failure: bool = False
    technical_failure_reason: Optional[str] = None
    stripped_hypothesis_scopes: set = field(default_factory=set)


@dataclass
class EvaluationResult:
    bundles: Dict[str, EvaluationBundle]
    llm_mode: str = "recorded"


# --- response schema -------------------------------------------
#
# Every field is REQUIRED. Anthropic compiles this schema into a constrained-
# decoding grammar; an optional field roughly doubles the grammar's state space,
# so 15 optional `blocked_by` fields (10 dims + 5 axes) blew the compiled grammar
# past the API limit ("The compiled grammar is too large", HTTP 400) on the first
# full live run. `blocked_by` is now a required array — `[]` means "rateable, no
# blocker", which the deterministic assembly already maps back to ``None`` — and
# the axes drop `blocked_by` entirely (``_axis`` never read it). No dimension,
# axis, rating/confidence, red_flag or recommendation semantic changes.

def _rated_dimension() -> dict:
    return obj_schema(
        {
            "rating": enum_str([r.value for r in Rating]),
            "confidence": enum_str([c.value for c in Confidence]),
            "justification": {"type": "string"},
            "blocked_by": {"type": "array", "items": {"type": "string"}},
        },
        ["rating", "confidence", "justification", "blocked_by"],
    )


def _rated_axis() -> dict:
    return obj_schema(
        {
            "rating": enum_str([r.value for r in Rating]),
            "confidence": enum_str([c.value for c in Confidence]),
            "justification": {"type": "string"},
        },
        ["rating", "confidence", "justification"],
    )


def _response_schema() -> dict:
    return obj_schema(
        {
            "dimensions": obj_schema(
                {k: _rated_dimension() for k in DIMENSION_KEYS}, list(DIMENSION_KEYS)
            ),
            "business_outcome_profile": obj_schema(
                {k: _rated_axis() for k in AXIS_KEYS}, list(AXIS_KEYS)
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


# --- strict shape check on the raw (non-schema) response --------
#
# Evaluation no longer sends ``output_config.format`` (its JSON Schema compiles to
# an over-limit grammar — owner decision 2026-08-31, spec §19 fallback C). The
# structured-output validator used to guarantee the shape; this does it now. Any
# deviation raises ``ResponseRejected`` → the opportunity becomes a
# ``technical_failure`` (never PARK, never registered), which is distinct from the
# §13 business validation that ``_build_bundle`` still runs on a well-formed
# response. ``_build_bundle``'s coercion is deliberately kept as a second layer.

_RATINGS = {r.value for r in Rating}
_CONFIDENCES = {c.value for c in Confidence}
_SEVERITIES = {s.value for s in Severity}
_RF_KINDS = {k.value for k in RedFlagKind}
_LIFECYCLE = {s.value for s in LifecycleState}


def _nonempty_str(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _check_rating_node(node, path: str, *, need_blocked_by: bool) -> List[str]:
    if not isinstance(node, dict):
        return [f"{path} is missing or not an object"]
    out: List[str] = []
    if node.get("rating") not in _RATINGS:
        out.append(f"{path}.rating is not one of {sorted(_RATINGS)}: {node.get('rating')!r}")
    if node.get("confidence") not in _CONFIDENCES:
        out.append(
            f"{path}.confidence is not one of {sorted(_CONFIDENCES)}: {node.get('confidence')!r}"
        )
    if not _nonempty_str(node.get("justification")):
        out.append(f"{path}.justification is missing or empty")
    if need_blocked_by:
        bb = node.get("blocked_by")
        if not isinstance(bb, list) or not all(isinstance(x, str) for x in bb):
            out.append(f"{path}.blocked_by must be an array of strings")
    return out


def _reject_malformed_evaluation(raw: object) -> dict:
    """Return ``raw`` unchanged, or raise ``ResponseRejected`` naming every way the
    prompt-guided Evaluation JSON deviates from the structure ``_build_bundle``
    needs (spec §19, owner decision 2026-08-31)."""
    if not isinstance(raw, dict):
        raise ResponseRejected(
            f"evaluation: response is a {type(raw).__name__}, not a JSON object"
        )

    problems: List[str] = []

    dims = raw.get("dimensions")
    if not isinstance(dims, dict):
        problems.append("dimensions is missing or not an object")
    else:
        for k in sorted(set(DIMENSION_KEYS) - set(dims)):
            problems.append(f"dimensions is missing '{k}'")
        for k in sorted(set(dims) - set(DIMENSION_KEYS)):
            problems.append(f"dimensions has an unexpected key '{k}'")
        for k in DIMENSION_KEYS:
            if k in dims:
                problems += _check_rating_node(dims[k], f"dimensions.{k}", need_blocked_by=True)

    axes = raw.get("business_outcome_profile")
    if not isinstance(axes, dict):
        problems.append("business_outcome_profile is missing or not an object")
    else:
        for k in sorted(set(AXIS_KEYS) - set(axes)):
            problems.append(f"business_outcome_profile is missing '{k}'")
        for k in sorted(set(axes) - set(AXIS_KEYS)):
            problems.append(f"business_outcome_profile has an unexpected key '{k}'")
        for k in AXIS_KEYS:
            if k in axes:
                problems += _check_rating_node(
                    axes[k], f"business_outcome_profile.{k}", need_blocked_by=False
                )

    rf = raw.get("red_flags")
    if not isinstance(rf, list):
        problems.append("red_flags is missing or not an array")
    else:
        for i, item in enumerate(rf):
            if not isinstance(item, dict):
                problems.append(f"red_flags[{i}] is not an object")
                continue
            if not _nonempty_str(item.get("description")):
                problems.append(f"red_flags[{i}].description is missing or empty")
            if item.get("severity") not in _SEVERITIES:
                problems.append(f"red_flags[{i}].severity is invalid: {item.get('severity')!r}")
            if item.get("kind") not in _RF_KINDS:
                problems.append(f"red_flags[{i}].kind is invalid: {item.get('kind')!r}")

    if raw.get("overall_confidence") not in _CONFIDENCES:
        problems.append(f"overall_confidence is invalid: {raw.get('overall_confidence')!r}")
    if not _nonempty_str(raw.get("summary")):
        problems.append("summary is missing or empty")

    rec = raw.get("recommendation")
    if not isinstance(rec, dict):
        problems.append("recommendation is missing or not an object")
    else:
        if rec.get("target_state") not in _LIFECYCLE:
            problems.append(
                f"recommendation.target_state is invalid: {rec.get('target_state')!r}"
            )
        if not _nonempty_str(rec.get("suggested_next_step")):
            problems.append("recommendation.suggested_next_step is missing or empty")
        if not _nonempty_str(rec.get("justification")):
            problems.append("recommendation.justification is missing or empty")
        if rec.get("confidence") not in _CONFIDENCES:
            problems.append(f"recommendation.confidence is invalid: {rec.get('confidence')!r}")

    problems += scan_json_for_numeric_score(raw, "evaluation")

    if problems:
        raise ResponseRejected(
            "evaluation: the response does not match the required structure — "
            + "; ".join(problems[:8])
        )
    return raw


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
        "- Every dimension carries a blocked_by array: [] when you could rate it from the "
        "evidence, otherwise the specific missing inputs. A dimension you cannot rate MUST "
        "be rating:LOW, confidence:LOW with a non-empty blocked_by. Never guess.\n"
        "- music_fit: the business's musical DNA detail is NEEDS_INPUT, so music_fit "
        "confidence MUST be LOW or MEDIUM. A catalog-affinity mismatch is NOT a blocker.\n"
        "- overall_confidence MUST NOT be raised by high dimension ratings — it reflects how "
        "much you actually know.\n"
        "- red_flags: compliance / feasibility / evidence_gap / asset_gap / market / other.\n"
        "- recommendation.target_state: EXPLORE, TEST or PARK only. suggested_next_step is a "
        "concrete action — still a recommendation, never executed in V1.\n\n"
        "COMPLIANCE SELF-CHECK (decision C4). This check is about the CLAIMS your "
        "text makes — not the TOPICS it mentions. A sensitive subject discussed on "
        "its own is never a guardrail violation; a prohibited claim about it is.\n"
        "NOT a violation by itself — never add a compliance red_flag for these:\n"
        '  - naming a topic or theme: "sleep music", "music to relax", "meditation", '
        '"432 Hz", "angel numbers", "energetic cleansing"\n'
        '  - stating an audience need or behaviour: "listeners look for music to '
        'fall asleep faster", "people play focus music while studying"\n'
        "  - describing a subjective experience or an editorial framing: "
        '"helps set a calm mood", "many find it relaxing", "positioned in the '
        'Healing / Well-being cluster"\n'
        "IS a violation — flag the exact sentence, name the guardrail id, say why:\n"
        '  - a factual efficacy claim about health: "432 Hz treats insomnia", '
        '"this music cures anxiety", "reduces your depression" (G01, G03)\n'
        "  - presenting music / frequencies / meditation as a medical treatment or "
        "as a substitute for care (G03)\n"
        '  - a scientific or medical claim stated as proven with no cited source: '
        '"scientifically proven to lower cortisol", "studies show it heals" (G04)\n'
        '  - an invented or unsupported number, statistic or trend figure: '
        '"streams grew 300%", "the #1 wellness trend of the year" with no source '
        "(G05)\n"
        "  - copying a third party's identity, wording or assets (G06)\n"
        'Borderline: "432 Hz" as a subject is fine; "432 Hz treats insomnia" is '
        'not. "sleep music" is fine; "sleep music proven to cure your insomnia" is '
        "not. Apply the SAME standard regardless of which topic, market or language "
        "the sentence uses — do not flag one market's sleep opportunity while "
        "clearing another's.\n"
        "For every sentence in YOUR text (evidence, justifications, summary, "
        "recommendation, hypotheses) that actually makes one of the violating "
        "claims above, add a red_flag with kind:'compliance', the offending "
        "guardrail's severity, and a description that QUOTES the exact sentence, "
        "names the guardrail id, and explains why. Then FIX your own text — drop "
        "the claim, state the uncertainty, or reframe it as a subjective "
        "experience — so no violating sentence remains. A topic, an audience need "
        "or a subjective experience that makes no prohibited claim is NOT a "
        "compliance red_flag.\n"
        f"The guardrails in full:\n{guardrail_lines}\n\n"
        f"OPPORTUNITY:\n{opp_json}\n\n"
        f"EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False, indent=1)}\n\n"
        f"ASSET FIT:\n{json.dumps(asset, ensure_ascii=False, indent=1)}\n\n"
        "OUTPUT — return ONE JSON object and nothing else (no prose, no markdown "
        "fence). Exactly this shape:\n"
        "{\n"
        '  "dimensions": {  // ALL 10 keys, each: '
        '{"rating": "LOW|MEDIUM|HIGH|VERY_HIGH", "confidence": "LOW|MEDIUM|HIGH", '
        '"justification": "<text citing evidence>", "blocked_by": ["<missing input>", ...]}\n'
        f"    {', '.join(DIMENSION_KEYS)}\n"
        "  },\n"
        '  "business_outcome_profile": {  // ALL 5 keys, each: '
        '{"rating": ..., "confidence": ..., "justification": ...}  (no blocked_by)\n'
        f"    {', '.join(AXIS_KEYS)}\n"
        "  },\n"
        '  "red_flags": [ {"description": "<text>", "severity": "LOW|MEDIUM|HIGH", '
        '"kind": "compliance|feasibility|evidence_gap|asset_gap|market|other"} ],  // [] if none\n'
        '  "overall_confidence": "LOW|MEDIUM|HIGH",\n'
        '  "summary": "<2-4 sentences grounded in evidence>",\n'
        '  "recommendation": {"target_state": "EXPLORE|TEST|PARK", '
        '"suggested_next_step": "<concrete action>", "justification": "<text>", '
        '"confidence": "LOW|MEDIUM|HIGH"}\n'
        "}\n"
        "Every string is required and non-empty. Use the exact enum spellings above. "
        "There is NO numeric score anywhere — never write '85/100', 'score: 72' or similar."
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
                schema=_response_schema(),  # reference shape only — not sent (see llm_stage)
                model=config.model,
                validate=_reject_malformed_evaluation,
            )
        except MissingFixtureError as e:
            # Replay with no recorded fixture — a documented offline-testing degrade
            # (spec §22), not an operational failure. Treated as a business exclusion.
            bundles[opp.opportunity_id] = _excluded_bundle(
                opp.opportunity_id, f"Evaluation fixture missing (replay): {e}"
            )
            continue
        except (StageError, ResponseRejected) as e:
            # An infrastructure failure of the Evaluation call (API error, timeout,
            # over-limit / unparseable response). NOT a business decision — the
            # opportunity is recorded as a technical failure, never PARKed, never
            # registered, and the run continues (§14). If EVERY opportunity fails
            # this way the orchestrator raises a controlled Evaluation error.
            bundles[opp.opportunity_id] = _technical_failure_bundle(
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
    """A minimal, schema-shaped bundle marked BUSINESS-excluded (no model output)."""
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


def _technical_failure_bundle(opportunity_id: str, reason: str) -> EvaluationBundle:
    """The Evaluation call could not complete. No profile, no ``Recommendation``,
    no business state — just a diagnosable technical error the run surfaces."""
    return EvaluationBundle(
        opportunity_id=opportunity_id,
        evaluation=None,
        business_outcome_profile=None,
        recommendation=None,
        compliance=ComplianceResult(),
        excluded=False,
        technical_failure=True,
        technical_failure_reason=reason,
    )
