"""Analysis / Framing — spec §18 component 3, §7, §19.

Claude frames the normalized ``Signal`` list into candidate ``Opportunity``
objects: the need / audience / consumption context, the ``durability`` /
``urgency`` labels, typed evidence (``OBSERVED`` / ``INFERRED`` / ``HYPOTHESIS``)
and the non-binding ``hypotheses``. Deterministic code owns everything that must
be well-formed and stable: the six C1 mandatory fields, the ``opportunity_id``
hash (§7.1), the §7.1a market/language rule, the canonical-cluster check, and
dropping evidence that does not resolve to a real signal in this run.

Output: a ``FramedOpportunity`` per surviving candidate — the input to Asset
Matching and Evaluation. It is **not** a full ``Opportunity`` yet (no
``asset_fit`` / ``evaluation`` / ``business_outcome_profile`` /
``recommendation`` — those are later stages, assembled at report time).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Union

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
    LANGUAGE_TO_MARKET,
    Confidence,
    Durability,
    EvidenceType,
    Language,
    Market,
    Platform,
    Urgency,
)
from .schema.ids import opportunity_id_base
from .schema.models import (
    Audience,
    EvidenceItem,
    Hypotheses,
    PotentialCluster,
    RunConfig,
    Signal,
)

SCHEMA_VERSION = "1.0.0"
STAGE = "framing"

_OPPORTUNITY_PLATFORMS = [
    Platform.TIKTOK, Platform.YOUTUBE, Platform.SPOTIFY,
    Platform.INSTAGRAM, Platform.FACEBOOK, Platform.OTHER,
]


@dataclass
class FramedOpportunity:
    opportunity_id: str
    schema_version: str
    run_id: str
    created_at: str
    title: str
    need: str
    audience: Audience
    market: Market
    language: Language
    platform: Platform
    consumption_context: str
    durability: Durability
    urgency: Urgency
    evidence: List[EvidenceItem]
    signal_ids: List[str]              # every signal feeding this opportunity
    hypotheses: Optional[Hypotheses] = None


@dataclass
class DroppedCandidate:
    title: str
    reason: str


@dataclass
class FramingResult:
    opportunities: List[FramedOpportunity]
    dropped: List[DroppedCandidate] = field(default_factory=list)
    llm_mode: str = "recorded"

    @property
    def opportunity_ids(self) -> List[str]:
        return [o.opportunity_id for o in self.opportunities]


class FramingError(StageError):
    """Framing could not run at all (e.g. no model client and no fixture)."""


# --- response schema ------------------------------------------------

def _evidence_schema() -> dict:
    return {
        "type": "array",
        "items": obj_schema(
            {
                "type": enum_str([e.value for e in EvidenceType]),
                "statement": {"type": "string"},
                "confidence": enum_str([c.value for c in Confidence]),
                "signal_ids": {"type": "array", "items": {"type": "string"}},
                "derived_from": {"type": "array", "items": {"type": "string"}},
                "rationale": {"type": "string"},
                "test_idea": {"type": "string"},
            },
            ["type", "statement", "confidence"],
        ),
    }


def _hypotheses_schema() -> dict:
    return obj_schema(
        {
            "potential_cluster": obj_schema(
                {
                    "value": {"type": "string"},
                    "canonical": {"type": "boolean"},
                    "basis": enum_str(["existing", "proposed_new"]),
                },
                ["value", "canonical", "basis"],
            ),
            "potential_positioning": {"type": "string"},
            "potential_page": {"type": "string"},
            "first_content_direction": {"type": "string"},
            "format": {"type": "string"},
            "hook": {"type": "string"},
        },
        [],
    )


def _response_schema() -> dict:
    return obj_schema(
        {
            "opportunities": {
                "type": "array",
                "items": obj_schema(
                    {
                        "title": {"type": "string"},
                        "need": {"type": "string"},
                        "audience": obj_schema(
                            {"description": {"type": "string"},
                             "attributes": {"type": "object"}},
                            ["description"],
                        ),
                        "market": enum_str([m.value for m in Market]),
                        "language": enum_str([lang.value for lang in Language]),
                        "platform": enum_str([p.value for p in _OPPORTUNITY_PLATFORMS]),
                        "consumption_context": {"type": "string"},
                        "durability": enum_str([d.value for d in Durability]),
                        "urgency": enum_str([u.value for u in Urgency]),
                        "evidence": _evidence_schema(),
                        "hypotheses": _hypotheses_schema(),
                    },
                    [
                        "title", "need", "audience", "market", "language", "platform",
                        "consumption_context", "durability", "urgency", "evidence",
                    ],
                ),
            }
        },
        ["opportunities"],
    )


# --- prompt -------------------------------------------------------

def _volume_hint(config: RunConfig) -> str:
    if config.max_candidates:
        return (
            f"Produce at most {config.max_candidates} candidate opportunities "
            "(a cost bound); merge near-duplicates."
        )
    # spec §11 — no hard cap on internal candidates; only the presented set is capped.
    return (
        "Produce as many distinct candidate opportunities as the evidence genuinely "
        "supports — do not pad, do not force; merge near-duplicates."
    )


def _prompt(signals: Sequence[Signal], knowledge: KnowledgeBundle, config: RunConfig) -> str:
    cluster_ids = sorted(knowledge.canonical_cluster_ids)
    sig_lines = [
        {
            "signal_id": s.signal_id,
            "market": s.market,
            "language": s.language,
            "platform": s.platform.value,
            "signal_type": s.signal_type.value,
            "evidence": s.evidence,
            "context": s.context,
            "observed_at": s.observed_at,
            "durability_hint": s.durability_hint.value if s.durability_hint else None,
            "confidence": s.confidence.value,
        }
        for s in signals
    ]
    return (
        "You are the Analysis / Framing step of a market-intelligence pipeline for an "
        "AI-assisted instrumental wellness-music business.\n\n"
        "Turn the SIGNALS below into candidate OPPORTUNITIES. An opportunity is a need, "
        "desire or behaviour of an audience with demand/growth signals that can become a "
        "content cluster in ONE market + language + platform. OPPORTUNITY != CLUSTER.\n\n"
        "Rules:\n"
        "- Each opportunity MUST have all six: need, audience.description, market, language, "
        "platform, consumption_context. Market and language MUST be consistent: "
        "pt<->Brasil, es<->Mercados hispanohablantes, en<->English-speaking markets.\n"
        "- Do NOT create an opportunity from a signal whose market is UNKNOWN or outside "
        "the three markets — skip it.\n"
        "- evidence: type each item OBSERVED (cite signal_ids), INFERRED (cite derived_from "
        "+ rationale) or HYPOTHESIS (rationale + test_idea). Every OBSERVED item MUST cite "
        "real signal_ids from the list. NEVER invent a fact, date, url or metric.\n"
        "- durability: EPHEMERAL / EMERGING / STRUCTURAL / EVERGREEN. urgency: LOW / MEDIUM / "
        "HIGH. These are judgement calls grounded in the evidence.\n"
        f"- hypotheses.potential_cluster.value: one of {cluster_ids} with canonical:true, "
        "basis:'existing'; OR a new theme with canonical:false, basis:'proposed_new' "
        "(a hypothesis only — never a decision).\n"
        "- No medical claims: no cure / treatment / diagnosis / disease-prevention language.\n"
        f"- {_volume_hint(config)}\n\n"
        f"scope notes: {config.scope.notes or '(none)'}\n"
        f"SIGNALS:\n{json.dumps(sig_lines, ensure_ascii=False, indent=1)}\n\n"
        'Return {"opportunities": [ ... ]} matching the schema exactly.'
    )


# --- deterministic assembly ------------------------------------

def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def _coerce_evidence(raw: list, known_signal_ids: set) -> List[EvidenceItem]:
    out: List[EvidenceItem] = []
    for item in raw or []:
        try:
            etype = EvidenceType(item["type"])
        except (KeyError, ValueError):
            continue
        statement = _clean(item.get("statement"))
        if not statement:
            continue
        try:
            confidence = Confidence(item.get("confidence", "LOW"))
        except ValueError:
            confidence = Confidence.LOW
        signal_ids = [s for s in (item.get("signal_ids") or []) if s in known_signal_ids]
        if etype is EvidenceType.OBSERVED and not signal_ids:
            # OBSERVED with no resolvable signal — drop the claim (§14).
            continue
        derived = [d for d in (item.get("derived_from") or []) if isinstance(d, str) and d]
        rationale = _clean(item.get("rationale")) or None
        if etype in (EvidenceType.INFERRED, EvidenceType.HYPOTHESIS) and not rationale:
            continue
        if etype is EvidenceType.INFERRED and not derived:
            # INFERRED must cite its basis (spec §7.3, §13) — drop the item, not the
            # whole opportunity (§14). The opportunity's OBSERVED evidence is untouched.
            continue
        out.append(EvidenceItem(
            type=etype,
            statement=statement,
            confidence=confidence,
            signal_ids=signal_ids or None,
            derived_from=derived or None,
            rationale=rationale,
            test_idea=_clean(item.get("test_idea")) or None,
        ))
    return out


def _coerce_hypotheses(raw: Optional[dict], canonical_ids: set) -> Optional[Hypotheses]:
    if not raw:
        return None
    pc = None
    pc_raw = raw.get("potential_cluster")
    if isinstance(pc_raw, dict) and _clean(pc_raw.get("value")):
        value = _clean(pc_raw["value"])
        canonical = bool(pc_raw.get("canonical"))
        basis = pc_raw.get("basis") or ("existing" if canonical else "proposed_new")
        # Deterministic guard: canonical must actually be in the taxonomy.
        if canonical and value not in canonical_ids:
            canonical, basis = False, "proposed_new"
        if not canonical:
            basis = "proposed_new"
        elif basis != "existing":
            basis = "existing"
        pc = PotentialCluster(value=value, canonical=canonical, basis=basis)
    h = Hypotheses(
        potential_cluster=pc,
        potential_positioning=_clean(raw.get("potential_positioning")) or None,
        potential_page=_clean(raw.get("potential_page")) or None,
        first_content_direction=_clean(raw.get("first_content_direction")) or None,
        format=_clean(raw.get("format")) or None,
        hook=_clean(raw.get("hook")) or None,
    )
    if not any(
        [pc, h.potential_positioning, h.potential_page, h.first_content_direction,
         h.format, h.hook]
    ):
        return None
    return h


def _assign_id(run_date: str, need: str, audience_desc: str, market: str,
               language: str, platform: str, taken: set) -> str:
    base = f"opp_{run_date}_{opportunity_id_base(need, audience_desc, market, language, platform)}"
    candidate = base
    n = 2
    while candidate in taken:
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def _build_one(
    raw: dict, *, config: RunConfig, created_at: str, known_signal_ids: set,
    canonical_ids: set, taken_ids: set,
) -> Union[FramedOpportunity, DroppedCandidate]:
    title = _clean(raw.get("title")) or "(untitled opportunity)"

    need = _clean(raw.get("need"))
    audience_raw = raw.get("audience") or {}
    audience_desc = _clean(audience_raw.get("description"))
    consumption = _clean(raw.get("consumption_context"))
    if not (need and audience_desc and consumption):
        return DroppedCandidate(title, "missing a C1 mandatory field (need/audience/context)")

    try:
        market = Market(raw["market"])
        language = Language(raw["language"])
        platform = Platform(raw["platform"])
        durability = Durability(raw["durability"])
        urgency = Urgency(raw["urgency"])
    except (KeyError, ValueError) as e:
        return DroppedCandidate(title, f"invalid or missing enum: {e}")

    if platform not in _OPPORTUNITY_PLATFORMS:
        return DroppedCandidate(title, f"platform {platform.value!r} not allowed for opportunities")
    if LANGUAGE_TO_MARKET.get(language) != market:
        return DroppedCandidate(
            title, f"market {market.value!r} inconsistent with language {language.value!r} (§7.1a)"
        )

    evidence = _coerce_evidence(raw.get("evidence"), known_signal_ids)
    if not evidence:
        return DroppedCandidate(title, "no usable evidence item after resolving signal_ids")

    observed_signal_ids = {
        sid for item in evidence for sid in (item.signal_ids or []) if sid in known_signal_ids
    }
    if not observed_signal_ids:
        return DroppedCandidate(title, "no OBSERVED evidence resolving to a signal in this run")
    # §16.2 — every signal that fed this opportunity, directly or via an inference.
    opp_signal_ids = sorted(observed_signal_ids | {
        ref for item in evidence for ref in (item.derived_from or []) if ref in known_signal_ids
    })

    hypotheses = _coerce_hypotheses(raw.get("hypotheses"), canonical_ids)

    opp_id = _assign_id(
        config.run_date, need, audience_desc, market.value, language.value, platform.value,
        taken_ids,
    )
    taken_ids.add(opp_id)

    attributes = audience_raw.get("attributes")
    return FramedOpportunity(
        opportunity_id=opp_id,
        schema_version=SCHEMA_VERSION,
        run_id=config.run_id,
        created_at=created_at,
        title=title,
        need=need,
        audience=Audience(description=audience_desc,
                          attributes=attributes if isinstance(attributes, dict) else None),
        market=market,
        language=language,
        platform=platform,
        consumption_context=consumption,
        durability=durability,
        urgency=urgency,
        evidence=evidence,
        signal_ids=opp_signal_ids,
        hypotheses=hypotheses,
    )


# --- entry point -------------------------------------------------

def frame_signals(
    signals: Sequence[Signal],
    *,
    knowledge: KnowledgeBundle,
    config: RunConfig,
    project_root: Union[str, Path],
    client: Optional[StageClient] = None,
    now: Optional[str] = None,
) -> FramingResult:
    signals = list(signals)
    created_at = now or f"{config.run_date}T00:00:00Z"
    active, mode = select_stage_client(config, project_root, client=client)

    known_signal_ids = {s.signal_id for s in signals}
    canonical_ids = set(knowledge.canonical_cluster_ids)

    if not signals:
        return FramingResult(opportunities=[], dropped=[], llm_mode=mode)

    # Key the framing call by the signal set, not the run_id — a re-run over the
    # same signals replays the same recorded fixture (idempotency, §5, §22).
    digest = hashlib.sha1(
        "|".join(sorted(known_signal_ids)).encode("utf-8")
    ).hexdigest()[:12]
    key = stage_key(STAGE, digest)
    try:
        raw = call_stage(
            active,
            stage=STAGE,
            key=key,
            prompt=_prompt(signals, knowledge, config),
            schema=_response_schema(),
            model=config.model,
            validate=lambda r: r,
        )
    except ResponseRejected as e:
        # A malformed / non-JSON framing response is a clean hard failure, not a
        # traceback (spec §14). FramingError is a StageError, caught by the orchestrator.
        raise FramingError(f"framing response was rejected: {e}") from e

    candidates = raw.get("opportunities") if isinstance(raw, dict) else None
    if not isinstance(candidates, list):
        raise FramingError("framing response has no 'opportunities' list")

    opportunities: List[FramedOpportunity] = []
    dropped: List[DroppedCandidate] = []
    taken_ids: set = set()
    for cand in candidates:
        if not isinstance(cand, dict):
            dropped.append(DroppedCandidate("(non-object)", "candidate is not an object"))
            continue
        built = _build_one(
            cand, config=config, created_at=created_at,
            known_signal_ids=known_signal_ids, canonical_ids=canonical_ids,
            taken_ids=taken_ids,
        )
        if isinstance(built, FramedOpportunity):
            opportunities.append(built)
        else:
            dropped.append(built)

    if config.max_candidates and len(opportunities) > config.max_candidates:
        for extra in opportunities[config.max_candidates:]:
            dropped.append(DroppedCandidate(extra.title, "over max_candidates soft cap"))
        opportunities = opportunities[: config.max_candidates]

    opportunities.sort(key=lambda o: o.opportunity_id)
    return FramingResult(opportunities=opportunities, dropped=dropped, llm_mode=mode)
