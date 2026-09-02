"""Cluster Strategy V1 — input contract (contract §2).

The stage runs ONLY on an owner-advanced Opportunity Report whose sidecar is
schema_version 1.0.0 and carries >= 1 OBSERVED evidence item.
"""

from __future__ import annotations

import json

import pytest
from tests.conftest import PROJECT_ROOT

from cluster_strategy.input_loader import ClusterStrategyInputError, load_input

_RUN = "run_2026-08-31_01"
_OID = "opp_2026-08-31_1bca4af972"  # Run 1's owner-advanced opportunity
_SIDECAR = PROJECT_ROOT / "reports" / _RUN / f"{_OID}.json"
_REVIEW = PROJECT_ROOT / "reports" / _RUN / "review.md"


def test_loads_a_real_advanced_opportunity_report(tmp_path):
    loaded = load_input(_SIDECAR, review_md_path=_REVIEW, project_root=PROJECT_ROOT)
    assert loaded.opportunity.opportunity_id == _OID
    assert loaded.snapshot.opportunity_id == _OID
    assert loaded.snapshot.schema_version == "1.0.0"
    assert loaded.snapshot.market.value == "Mercados hispanohablantes"
    assert loaded.snapshot.potential_cluster_value == "limpeza-energetica"
    assert loaded.snapshot.potential_cluster_canonical is True
    assert loaded.owner_authorization.advanced_opportunity_id == _OID
    assert loaded.owner_authorization.reviewer == "Nicolas"
    # the OBSERVED / typed evidence is carried through unchanged
    assert any(e.type.value == "OBSERVED" for e in loaded.opportunity.evidence)


def test_review_md_defaults_to_the_sidecar_directory(tmp_path):
    loaded = load_input(_SIDECAR, project_root=PROJECT_ROOT)  # no review_md_path
    assert loaded.owner_authorization.advanced_opportunity_id == _OID


def _write_sidecar(tmp_path, mutate) -> "tuple":
    raw = json.loads(_SIDECAR.read_text())
    raw = mutate(raw)
    sc = tmp_path / f"{_OID}.json"
    sc.write_text(json.dumps(raw), encoding="utf-8")
    review = tmp_path / "review.md"
    review.write_text(_REVIEW.read_text(), encoding="utf-8")
    return sc, review


def test_schema_version_mismatch_is_a_hard_failure(tmp_path):
    sc, review = _write_sidecar(tmp_path, lambda r: {**r, "schema_version": "2.0.0"})
    with pytest.raises(ClusterStrategyInputError) as ei:
        load_input(sc, review_md_path=review, project_root=PROJECT_ROOT)
    assert "schema_version" in str(ei.value)


def test_zero_observed_evidence_is_refused(tmp_path):
    def strip_observed(r):
        r["evidence"] = [
            {"type": "HYPOTHESIS", "statement": "x", "confidence": "LOW", "rationale": "y"}
        ]
        return r
    sc, review = _write_sidecar(tmp_path, strip_observed)
    with pytest.raises(ClusterStrategyInputError) as ei:
        load_input(sc, review_md_path=review, project_root=PROJECT_ROOT)
    assert "OBSERVED" in str(ei.value)


def test_opportunity_not_advanced_in_review_md_is_refused(tmp_path):
    def other_advance(_r):
        return _r
    sc, review = _write_sidecar(tmp_path, other_advance)
    review.write_text(
        review.read_text().replace(
            f"advanced_opportunity_id: {_OID}", "advanced_opportunity_id: null"
        ).replace("| advance |", "| relevant |"),
        encoding="utf-8",
    )
    with pytest.raises(ClusterStrategyInputError) as ei:
        load_input(sc, review_md_path=review, project_root=PROJECT_ROOT)
    assert "advance" in str(ei.value).lower()


def test_a_row_marked_advance_is_accepted_even_without_the_front_matter_field(tmp_path):
    sc, review = _write_sidecar(tmp_path, lambda r: r)
    review.write_text(
        review.read_text().replace(
            f"advanced_opportunity_id: {_OID}", "advanced_opportunity_id: null"
        ),
        encoding="utf-8",
    )
    # the decision-table row for _OID still says `advance`
    loaded = load_input(sc, review_md_path=review, project_root=PROJECT_ROOT)
    assert loaded.owner_authorization.advanced_opportunity_id == _OID


def test_missing_sidecar_is_a_hard_failure(tmp_path):
    with pytest.raises(ClusterStrategyInputError):
        load_input(tmp_path / "nope.json", project_root=PROJECT_ROOT)
