"""Page Blueprint V1 — input contract (contract §2).

The stage runs ONLY on a ClusterStrategy sidecar that is schema_version 1.0.0,
carries a MAP_TO_EXISTING/PROPOSE_NEW_CLUSTER decision with all three strategy
sections present, and was itself recommended for Page Blueprint
(`recommendation.target_next_stage == PAGE_BLUEPRINT`).
"""

from __future__ import annotations

import json

import pytest
from tests.conftest import PROJECT_ROOT

from page_blueprint.input_loader import PageBlueprintInputError, load_input

_OID = "opp_2026-08-31_1bca4af972"
_SIDECAR = PROJECT_ROOT / "reports" / "cluster-strategy" / f"{_OID}.json"


def test_loads_a_real_page_blueprint_recommended_cluster_strategy():
    loaded = load_input(_SIDECAR, project_root=PROJECT_ROOT)
    assert loaded.snapshot.opportunity_id == _OID
    assert loaded.snapshot.schema_version == "1.0.0"
    assert loaded.snapshot.cluster_id == "limpeza-energetica"
    assert loaded.snapshot.cluster_name == "Limpeza Energética"
    assert loaded.snapshot.market.value == "Mercados hispanohablantes"
    assert loaded.snapshot.overall_confidence.value == "LOW"
    assert loaded.cluster_strategy.asset_strategy is not None


def _write_sidecar(tmp_path, mutate) -> "object":
    raw = json.loads(_SIDECAR.read_text())
    raw = mutate(raw)
    sc = tmp_path / f"{_OID}.json"
    sc.write_text(json.dumps(raw), encoding="utf-8")
    return sc


def test_schema_version_mismatch_is_a_hard_failure(tmp_path):
    sc = _write_sidecar(tmp_path, lambda r: {**r, "schema_version": "2.0.0"})
    with pytest.raises(PageBlueprintInputError) as ei:
        load_input(sc, project_root=PROJECT_ROOT)
    assert "schema_version" in str(ei.value)


def test_wrong_target_next_stage_is_refused(tmp_path):
    def other_target(r):
        r["recommendation"] = {**r["recommendation"], "target_next_stage": "CONTENT_STRATEGY"}
        return r
    sc = _write_sidecar(tmp_path, other_target)
    with pytest.raises(PageBlueprintInputError) as ei:
        load_input(sc, project_root=PROJECT_ROOT)
    assert "PAGE_BLUEPRINT" in str(ei.value)


def test_defer_decision_is_refused(tmp_path):
    def defer(r):
        r["cluster_decision"] = {
            "decision": "DEFER",
            "justification": "not enough evidence yet",
            "framing_hypothesis_comparison": "insufficient signal to confirm or override",
        }
        r.pop("strategic_definition", None)
        r.pop("asset_strategy", None)
        r.pop("content_direction", None)
        return r
    sc = _write_sidecar(tmp_path, defer)
    with pytest.raises(PageBlueprintInputError) as ei:
        load_input(sc, project_root=PROJECT_ROOT)
    assert "DEFER" in str(ei.value) or "MAP_TO_EXISTING" in str(ei.value)


def test_reject_decision_is_refused(tmp_path):
    def reject(r):
        r["cluster_decision"] = {
            "decision": "REJECT",
            "justification": "does not fit any cluster and has no strategic merit",
            "framing_hypothesis_comparison": "overrides the pre-normalised hypothesis",
        }
        r.pop("strategic_definition", None)
        r.pop("asset_strategy", None)
        r.pop("content_direction", None)
        return r
    sc = _write_sidecar(tmp_path, reject)
    with pytest.raises(PageBlueprintInputError):
        load_input(sc, project_root=PROJECT_ROOT)


def test_missing_strategy_sections_is_a_hard_failure(tmp_path):
    def strip(r):
        r.pop("asset_strategy", None)
        return r
    sc = _write_sidecar(tmp_path, strip)
    with pytest.raises(PageBlueprintInputError) as ei:
        load_input(sc, project_root=PROJECT_ROOT)
    assert "asset_strategy" in str(ei.value) or "malformed" in str(ei.value).lower()


def test_missing_sidecar_is_a_hard_failure(tmp_path):
    with pytest.raises(PageBlueprintInputError):
        load_input(tmp_path / "nope.json", project_root=PROJECT_ROOT)


def test_not_a_json_object_is_a_hard_failure(tmp_path):
    sc = tmp_path / "bad.json"
    sc.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(PageBlueprintInputError):
        load_input(sc, project_root=PROJECT_ROOT)
