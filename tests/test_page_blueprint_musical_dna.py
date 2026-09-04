"""Page Blueprint V1 — business-dna §9 access (contract §5, D-PB-4).

Page Blueprint reads business-dna.md directly (no hand-written mapping table):
``extract_section_9`` pulls the raw §9 markdown verbatim, and
``extract_cluster_expression_hint`` best-effort matches a cluster name to its
§9.9 house-sound expression line. ``musical_dna_needs_input`` is the pipeline's
own single-source-of-truth detector, re-exported unchanged.
"""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.orchestrator import _musical_dna_needs_input
from market_intelligence.schema.models import RunPaths
from page_blueprint.musical_dna import (
    extract_cluster_expression_hint,
    extract_section_9,
    musical_dna_needs_input,
)

_KB = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def test_musical_dna_needs_input_is_the_same_single_source_of_truth():
    assert musical_dna_needs_input is _musical_dna_needs_input
    assert musical_dna_needs_input(_KB.business_dna_body) is False  # §9 is owner-approved


def test_extract_section_9_returns_the_real_owner_approved_section():
    section_9 = extract_section_9(_KB.business_dna_body)
    assert section_9.startswith("## 9. Music DNA")
    assert "OWNER-APPROVED" in section_9
    assert "House-sound principle" in section_9
    # stops before the next top-level section
    assert "## 10. Artist Architecture" not in section_9


def test_extract_section_9_is_fail_safe_when_the_heading_is_absent():
    out = extract_section_9("# Some other document\n\nno music dna heading here")
    assert "NEEDS_INPUT" in out


def test_extract_cluster_expression_hint_matches_limpeza_energetica():
    section_9 = extract_section_9(_KB.business_dna_body)
    hint = extract_cluster_expression_hint(section_9, "Limpeza Energética")
    assert hint is not None
    assert "crystalline" in hint  # matched line is the §9.9 bullet (wraps in the source)


def test_extract_cluster_expression_hint_returns_none_for_no_match():
    section_9 = extract_section_9(_KB.business_dna_body)
    assert extract_cluster_expression_hint(section_9, "Not A Real Cluster Name") is None


def test_extract_cluster_expression_hint_returns_none_without_a_cluster_name():
    section_9 = extract_section_9(_KB.business_dna_body)
    assert extract_cluster_expression_hint(section_9, None) is None
