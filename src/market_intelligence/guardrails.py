"""Compliance check against ``knowledge/rules/guardrails.yaml`` (spec §13, §14, C4).

Deterministic. The Knowledge Loader parses the 10 guardrails (G01–G10); this
module runs the check **per ``applies_to`` scope** over the free text the pipeline
generated, raises a ``compliance`` ``RedFlag`` per violation, and reports the
``action_on_violation`` the caller must apply.

Detection is a conservative pattern scan for the constructions the HIGH-severity
prohibitions forbid — explicit cure / treatment / diagnosis claims (G01, G03),
"clinically/scientifically proven" language (G04). It never fires on the editorial
cluster labels ("Cura / Bem-estar", "Ansiedade / Relaxamento") on their own —
only on a claim built around them. Claude's own compliance self-check (§19)
covers the subtler cases and reports them as red flags from the Evaluation stage.

`CLAUDE.md` prose is **not** parsed — only this data file (§13).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .schema.enums import GuardrailAction, RedFlagKind, Severity
from .schema.models import Guardrail, RedFlag

# Scopes the compliance check covers (spec §13). A guardrail applies to a piece of
# text when its `applies_to` names that text's scope.
SCOPE_HYPOTHESES_POSITIONING = "hypotheses.potential_positioning"
SCOPE_HYPOTHESES_DIRECTION = "hypotheses.first_content_direction"
SCOPE_HYPOTHESES_HOOK = "hypotheses.hook"
SCOPE_HYPOTHESES = "hypotheses"
SCOPE_EVIDENCE = "evidence"
SCOPE_EVAL_JUSTIFICATION = "evaluation.justification"
SCOPE_EVAL_SUMMARY = "evaluation.summary"
SCOPE_BOP_JUSTIFICATION = "business_outcome_profile.justification"
SCOPE_RECOMMENDATION = "recommendation"
SCOPE_REPORT_PROSE = "report_prose"

# "core required content" — a violation here excludes the opportunity (§14);
# a violation only in a hypothesis field is stripped and the report proceeds.
_CORE_SCOPES = frozenset({
    SCOPE_EVIDENCE, SCOPE_EVAL_JUSTIFICATION, SCOPE_EVAL_SUMMARY,
    SCOPE_BOP_JUSTIFICATION, SCOPE_RECOMMENDATION, SCOPE_REPORT_PROSE,
})

# Named clinical conditions — NOT the permitted editorial wellness themes. Anxiety,
# stress, insomnia, relaxation are in-scope subjective-experience topics (CLAUDE.md
# §14.2, cluster-taxonomy.md) and are deliberately excluded here.
_CONDITION = (
    r"(?:depress\w+|disease|doen[çc]as?|enfermedad\w*|disorder|transtorno\w*|trastorno\w*|"
    r"c[aâ]ncer|cancer|hypertension|hipertens[ãa]o|hipertensi[óo]n|diabetes|"
    r"adhd|tdah|migraine|enxaqueca|migra[ñn]a|illness|patolog\w*|"
    r"s[ií]ndrome (?:de|do|da)\s+\w+|syndrome)"
)

# guardrail_id -> compiled patterns whose match is a violation of that guardrail.
# "trata-se de" / "se trata de" (= "it concerns") is a common PT/ES idiom, NOT a
# treatment claim — the (?<!se )/(?<!-se ) guards keep it out.
_SCANNERS: Dict[str, List[re.Pattern]] = {
    "G01": [
        re.compile(rf"\b(?:cure|cures|curing|cura|curam|curar|curan?|sana|sanar|heals?|"
                   rf"healing)\b[^.\n]{{0,40}}\b{_CONDITION}\b", re.IGNORECASE),
        re.compile(rf"\b{_CONDITION}\b[^.\n]{{0,25}}\b(?:is|é|está|será|will be)?\s*"
                   rf"(?:cured|curada?|healed|eliminated|eliminada?)\b", re.IGNORECASE),
        re.compile(r"\b(?:prevents?|previne[m]?|previene[n]?|prevención de|prevention of)\b"
                   rf"[^.\n]{{0,30}}\b{_CONDITION}\b", re.IGNORECASE),
        re.compile(rf"\b(?:diagnos(?:e|es|is|ing)|diagn[oó]stic\w*|diagnóstic\w*)\b"
                   rf"[^.\n]{{0,30}}\b{_CONDITION}\b", re.IGNORECASE),
    ],
    "G03": [
        re.compile(r"\b(?:medical treatment|treatment for|tratamento médico|tratamento para|"
                   r"tratamiento médico|tratamiento para|terapia médica|medical therapy|"
                   r"clinical treatment|prescription|prescrição|receita médica)\b",
                   re.IGNORECASE),
        re.compile(rf"(?<!se )(?<!-se )\b(?:treats?|trata|tratam|tratar|tratan)\s+"
                   rf"(?:a |o |os |as |sua |seu |the |your )?{_CONDITION}\b",
                   re.IGNORECASE),
        re.compile(r"\b(?:substitui[r]?|replaces?|replace your|em vez de|instead of)\b"
                   r"[^.\n]{0,20}\b(?:medica\w*|rem[eé]dio|medicine|medication|doctor|médico|"
                   r"tratamento médico|medical treatment)\b", re.IGNORECASE),
    ],
    "G04": [
        re.compile(r"\b(?:clinically|scientifically|medically|cientificamente|"
                   r"clinicamente|científicamente|cl[ií]nicamente)\s+"
                   r"(?:proven|prode|tested|validated|comprovad\w*|provad\w*|demonstrad\w*|"
                   r"probad\w*|validad\w*)\b", re.IGNORECASE),
        re.compile(r"\b(?:studies (?:show|prove)|research proves|estudos (?:comprovam|provam)|"
                   r"estudios (?:demuestran|prueban)|la ciencia (?:demuestra|prueba))\b",
                   re.IGNORECASE),
    ],
}


@dataclass
class GuardrailFinding:
    guardrail_id: str
    scope: str
    severity: Severity
    action: GuardrailAction
    escalation: Optional[GuardrailAction]
    matched_text: str
    core: bool  # the text is core required content → exclusion, not a strip


@dataclass
class ComplianceResult:
    findings: List[GuardrailFinding] = field(default_factory=list)
    red_flags: List[RedFlag] = field(default_factory=list)
    exclude_opportunity: bool = False
    strip_scopes: set = field(default_factory=set)   # hypothesis scopes to blank out
    needs_uncertainty_note: set = field(default_factory=set)

    @property
    def clean(self) -> bool:
        return not self.findings


def _by_id(guardrails: Sequence[Guardrail]) -> Dict[str, Guardrail]:
    return {g.guardrail_id: g for g in guardrails}


def _applies(g: Guardrail, scope: str) -> bool:
    if not g.applies_to:
        return False
    if scope in g.applies_to:
        return True
    # a scope like "evaluation.justification" is covered by a broader "evaluation" entry
    root = scope.split(".", 1)[0]
    return root in g.applies_to


def scan_text(text: str, *, scope: str, guardrails: Sequence[Guardrail]) -> List[GuardrailFinding]:
    """Every guardrail violation the pattern scanners find in ``text`` for ``scope``."""
    if not text or not text.strip():
        return []
    out: List[GuardrailFinding] = []
    catalog = _by_id(guardrails)
    for gid, patterns in _SCANNERS.items():
        g = catalog.get(gid)
        if g is None or not _applies(g, scope):
            continue
        for pat in patterns:
            m = pat.search(text)
            if m:
                out.append(GuardrailFinding(
                    guardrail_id=gid,
                    scope=scope,
                    severity=g.severity,
                    action=g.action_on_violation,
                    escalation=g.escalation,
                    matched_text=m.group(0).strip(),
                    core=scope in _CORE_SCOPES,
                ))
                break  # one finding per guardrail per text is enough
    return out


def check_texts(
    texts: Dict[str, Sequence[str]], *, guardrails: Sequence[Guardrail]
) -> ComplianceResult:
    """Run the compliance check over ``{scope: [text, ...]}`` and decide the actions.

    Action handling (spec §13, §14):
      * ``reject_and_revise`` (no live revision in V1) → escalate: strip the
        offending hypothesis field, or exclude the opportunity when the text is
        core required content.
      * ``flag`` / ``flag_for_validation`` → a ``compliance`` red flag; proceed.
      * ``require_uncertainty_statement`` → red flag + the scope is flagged so the
        renderer adds an explicit uncertainty note.
      * ``none`` → nothing.
    """
    result = ComplianceResult()
    seen = set()
    for scope, chunk in texts.items():
        for text in chunk:
            for f in scan_text(text, scope=scope, guardrails=guardrails):
                key = (f.guardrail_id, f.scope, f.matched_text)
                if key in seen:
                    continue
                seen.add(key)
                result.findings.append(f)
                result.red_flags.append(RedFlag(
                    description=(
                        f"{f.guardrail_id} ({scope}): text reads as a compliance violation "
                        f"— {f.matched_text!r}"
                    ),
                    severity=f.severity,
                    kind=RedFlagKind.COMPLIANCE,
                ))
                if f.action in (
                    GuardrailAction.REJECT_AND_REVISE, GuardrailAction.EXCLUDE_OPPORTUNITY
                ):
                    # No live revision pass in V1 → apply the escalation directly (§14):
                    # core required content → exclude; a hypothesis field → strip it.
                    if f.core:
                        result.exclude_opportunity = True
                    else:
                        result.strip_scopes.add(f.scope)
                elif f.action is GuardrailAction.REQUIRE_UNCERTAINTY_STATEMENT:
                    result.needs_uncertainty_note.add(f.scope)
    return result
