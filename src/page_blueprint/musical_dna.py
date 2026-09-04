"""Business DNA §9 (Musical DNA) access for Page Blueprint (contract §5, D-PB-4).

Page Blueprint is the stage that most needs §9 (`docs/MUSICAL-DNA-INPUT.md`):
visual identity and tone of voice are meant to derive from the house-sound
principle and the per-cluster sonic expression (§9.9). Nothing else in §9
(instrumentation, BPM, frequency use, sonority criteria) is consumed here —
that is Audio Engine's job (stage 8, deferred).

Deterministic, text-based — mirrors ``cluster_strategy.mapping.load_taxonomy_markdown``:
Claude reads the raw §9 markdown directly in the prompt; this module never
pre-parses business content into a hand-written mapping table.
"""

from __future__ import annotations

import re
from typing import Optional

from market_intelligence.orchestrator import _musical_dna_needs_input

__all__ = ["musical_dna_needs_input", "extract_section_9", "extract_cluster_expression_hint"]

#: Re-exported under a public name — the pipeline's own detector (spec: scans for
#: the "Music DNA" heading, then "NEEDS INPUT" within 800 chars). Kept as a single
#: source of truth rather than a second, independently-brittle copy.
musical_dna_needs_input = _musical_dna_needs_input

_SECTION_9_HEADING = re.compile(r"^##\s+9\.\s", re.MULTILINE)
_NEXT_H2_HEADING = re.compile(r"^##\s+\d", re.MULTILINE)
_EXPRESSION_LINE = re.compile(r"^-\s+\*\*([^*]+?)[:\*]", re.MULTILINE)


def extract_section_9(business_dna_body: str) -> str:
    """The full §9 (Music DNA) markdown section, verbatim — or a NEEDS_INPUT
    placeholder note if the section cannot be located (fail-safe, never invents
    content)."""
    m = _SECTION_9_HEADING.search(business_dna_body)
    if not m:
        return "NEEDS_INPUT — business-dna.md has no '## 9.' Music DNA section."
    start = m.start()
    rest = business_dna_body[m.end():]
    end_m = _NEXT_H2_HEADING.search(rest)
    end = m.end() + end_m.start() if end_m else len(business_dna_body)
    return business_dna_body[start:end].strip()


def extract_cluster_expression_hint(section_9: str, cluster_name: Optional[str]) -> Optional[str]:
    """Best-effort §9.9 cluster-expression line matching ``cluster_name`` (e.g.
    "Sono", "Abundância") — a convenience hint only. Returns ``None`` on no
    match; Claude still receives the full §9 text and can locate the right
    expression itself (mirrors Cluster Strategy's ``cluster_hint`` pattern:
    the hint narrows attention, it is never the sole source of truth)."""
    if not cluster_name:
        return None
    needle = cluster_name.strip().lower()
    for line in section_9.splitlines():
        m = _EXPRESSION_LINE.match(line.strip())
        if not m:
            continue
        label = m.group(1).strip().lower()
        if needle in label or label in needle:
            return line.strip().lstrip("- ").strip()
    return None
