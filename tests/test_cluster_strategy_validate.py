"""Cluster Strategy V1 — deterministic validators (contract §13, §B).

Rejects: a non-canonical cluster_id; any 0–100 score in any prose (C6);
overall_confidence above the opportunity's (contract §11); an invented asset id;
a page-blueprint / content-strategy field name (scope leakage, §B); a
new_cluster_proposal missing its boundary map; tampered fixed disclaimer text.
"""

from __future__ import annotations

import copy

import pytest
from tests.conftest import PROJECT_ROOT
from tests.test_cluster_strategy_models import _minimal_map_to_existing

from cluster_strategy.schema import validate as V
from cluster_strategy.schema.models import ClusterStrategy
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.models import RunPaths
from market_intelligence.schema.validate import blocking

_KB = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)
_CANON = frozenset(c.id for c in _KB.clusters)


def _raw(mutate=None) -> dict:
    r = encode(_minimal_map_to_existing())
    if mutate:
        r = mutate(copy.deepcopy(r))
    return r


def _errs(raw: dict):
    cs = decode(ClusterStrategy, raw)
    return blocking(V.validate_cluster_strategy(
        cs, canonical_cluster_ids=_CANON, inventory=_KB.inventory))


def _all(raw: dict):
    cs = decode(ClusterStrategy, raw)
    return V.validate_cluster_strategy(
        cs, canonical_cluster_ids=_CANON, inventory=_KB.inventory)


def test_the_minimal_valid_strategy_passes():
    assert _errs(_raw()) == []


def test_non_canonical_cluster_id_is_an_error():
    errs = _errs(_raw(lambda r: {**r, "cluster_decision": {
        **r["cluster_decision"], "cluster_id": "not-a-real-cluster"}}))
    assert any("cluster_id" in e.code for e in errs)


def test_a_0_to_100_score_in_any_prose_is_an_error():
    def inject(r):
        r["strategic_definition"]["positioning_statement"] = "we score this 82/100 for fit"
        return r
    errs = _errs(_raw(inject))
    assert any("numeric_score" in e.code for e in errs)


def test_overall_confidence_above_the_opportunitys_is_an_error():
    # opportunity.overall_confidence == LOW; strategy claims HIGH
    def raise_conf(r):
        r["evaluation"]["overall_confidence"] = "HIGH"
        return r
    errs = _errs(_raw(raise_conf))
    assert any("overall_confidence" in e.code for e in errs)


def test_an_invented_playlist_id_is_an_error():
    def invent(r):
        r["asset_strategy"]["playlist_strategy"]["primary_playlist_id"] = "pl_totally_made_up"
        return r
    errs = _errs(_raw(invent))
    assert any("asset" in e.code and "playlist" in e.message.lower() for e in errs)


def test_map_to_existing_without_the_strategy_sections_is_an_error():
    def strip(r):
        r.pop("strategic_definition", None)
        r.pop("asset_strategy", None)
        return r
    errs = _errs(_raw(strip))
    assert any("strategy_sections" in e.code for e in errs)


def test_propose_new_cluster_requires_a_boundary_map():
    def to_proposal(r):
        r["cluster_decision"] = {
            "decision": "PROPOSE_NEW_CLUSTER",
            "justification": "fits no canonical cluster",
            "framing_hypothesis_comparison": "overrode limpeza-energetica",
            "new_cluster_proposal": {
                "proposed_id": "night-overthinking-reset",
                "proposed_name": "Night Overthinking Reset",
                "concept": "music for spiralling nighttime thoughts",
                "boundary_vs_adjacent": {},   # <-- empty
                "why_not_subcluster": "distinct trigger",
                "supporting_evidence": ["sig_x"],
                "governance_note": ("Formalizing a canonical cluster is an owner "
                    "decision (P6, DEFERRED). This is a proposal only; the pipeline "
                    "does not modify cluster-taxonomy.md."),
            },
        }
        return r
    errs = _errs(_raw(to_proposal))
    assert any("boundary" in e.code for e in errs)


def test_the_four_dimension_keys_must_be_exact():
    def drop_dim(r):
        r["evaluation"]["dimensions"].pop("strategic_coherence")
        return r
    errs = _errs(_raw(drop_dim))
    assert any("dimension" in e.code for e in errs)


def test_tampered_fixed_disclaimer_is_an_error():
    def tamper(r):
        r["content_direction"]["content_boundary_note"] = "we also define the pillars here"
        return r
    errs = _errs(_raw(tamper))
    assert any("boundary_note" in e.code or "disclaimer" in e.code for e in errs)


def test_too_many_editorial_angles_is_a_non_blocking_warning():
    def flood(r):
        r["content_direction"]["editorial_angles"] = [f"angle {i}" for i in range(9)]
        return r
    raw = _raw(flood)
    all_errs = _all(raw)
    warned = [e for e in all_errs if e.code == "cluster_strategy.too_many_editorial_angles"]
    assert warned and warned[0].severity == "WARNING"
    assert _errs(raw) == []  # WARNING does not block the run


def test_scope_leakage_field_name_is_rejected_by_the_codec_and_the_scanner():
    # the model has no such field -> decode already refuses it; the scanner is a
    # regression guard if the models are ever wrongly extended.
    raw = _raw()
    raw["asset_strategy"]["page_strategy"]["visual_identity"] = {"palette": "blue"}
    from market_intelligence.schema.codec import CodecError
    with pytest.raises(CodecError):
        decode(ClusterStrategy, raw)
    assert V.scan_for_scope_leakage(raw)  # the scanner also flags it
