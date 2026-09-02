"""Cluster Strategy V1 — registry link (D-CS-7, contract §14).

Appends `cluster_strategy_ref` + one state_history note to the opportunity's
registry entry, append-only, without touching `status` (the lifecycle is carried,
not transitioned — I2). Idempotent.
"""

from __future__ import annotations

import yaml
from tests.conftest import PROJECT_ROOT

from cluster_strategy.config import ClusterStrategyConfig, CSReplayConfig
from cluster_strategy.orchestrator import run_cluster_strategy
from market_intelligence.schema.models import RunPaths

_OID = "opp_2026-08-31_1bca4af972"
_SIDECAR = PROJECT_ROOT / "reports" / "run_2026-08-31_01" / f"{_OID}.json"
_REAL_REGISTRY = PROJECT_ROOT / "knowledge" / "market" / "opportunity-registry.yaml"


def _config(tmp_path, registry_path):
    paths = RunPaths()
    paths.registry_path = str(registry_path)
    return ClusterStrategyConfig(
        run_id="cs_run_2026-09-01_01",
        model="claude-sonnet-5",
        prompt_version="cs-v1-test",
        run_date="2026-09-01",
        reports_subdir=str(tmp_path / "out"),
        write_registry_link=True,
        paths=paths,
        replay=CSReplayConfig(enabled=True, fixture_path="tests/fixtures/cluster_strategy",
                              llm="recorded"),
    )


def test_appends_a_cluster_strategy_ref_without_changing_status(tmp_path):
    reg = tmp_path / "opportunity-registry.yaml"
    reg.write_text(_REAL_REGISTRY.read_text(), encoding="utf-8")
    before = yaml.safe_load(reg.read_text())
    entry_before = next(e for e in before["opportunities"] if e["opportunity_id"] == _OID)
    status_before = entry_before["status"]
    hist_before = len(entry_before.get("state_history", []))

    result = run_cluster_strategy(
        _SIDECAR, config=_config(tmp_path, reg), project_root=PROJECT_ROOT,
        now="2026-09-01T18:00:00Z",
    )
    assert result.registry_updated is True

    after = yaml.safe_load(reg.read_text())
    entry = next(e for e in after["opportunities"] if e["opportunity_id"] == _OID)
    assert entry["cluster_strategy_ref"] == "reports/cluster-strategy/" + _OID + ".md"
    assert entry["status"] == status_before                       # lifecycle NOT transitioned
    assert len(entry["state_history"]) == hist_before + 1
    note = entry["state_history"][-1]
    assert note["by"] == "system" and note["to"] == status_before
    assert "cluster strategy" in note["note"] and "MAP_TO_EXISTING" in note["note"]
    # every other entry is byte-untouched (append-only, localized git diff)
    assert [e["opportunity_id"] for e in after["opportunities"]] == \
           [e["opportunity_id"] for e in before["opportunities"]]


def test_a_second_run_is_idempotent(tmp_path):
    reg = tmp_path / "opportunity-registry.yaml"
    reg.write_text(_REAL_REGISTRY.read_text(), encoding="utf-8")
    cfg = _config(tmp_path, reg)
    run_cluster_strategy(_SIDECAR, config=cfg, project_root=PROJECT_ROOT,
                         now="2026-09-01T18:00:00Z")
    after_one = reg.read_text()
    r2 = run_cluster_strategy(_SIDECAR, config=cfg, project_root=PROJECT_ROOT,
                              now="2026-09-01T19:00:00Z")
    assert r2.registry_updated is False
    assert reg.read_text() == after_one  # no second state_history entry, no rewrite


def test_no_registry_file_is_a_noop_not_an_error(tmp_path):
    result = run_cluster_strategy(
        _SIDECAR, config=_config(tmp_path, tmp_path / "does_not_exist.yaml"),
        project_root=PROJECT_ROOT, now="2026-09-01T18:00:00Z",
    )
    assert result.registry_updated is False
    assert not (tmp_path / "does_not_exist.yaml").exists()


def test_writing_the_registry_link_is_opt_in_off_by_default(tmp_path):
    # A config that does not mention write_registry_link must NOT mutate the
    # human-owned opportunity-registry.yaml (D-CS-7 opt-in; reviewer HIGH).
    from cluster_strategy.config import ClusterStrategyConfig
    assert ClusterStrategyConfig.__dataclass_fields__["write_registry_link"].default is False

    reg = tmp_path / "opportunity-registry.yaml"
    reg.write_text(_REAL_REGISTRY.read_text(), encoding="utf-8")
    before = reg.read_text()
    paths = RunPaths()
    paths.registry_path = str(reg)
    cfg = ClusterStrategyConfig(
        run_id="cs_run_2026-09-01_01", model="claude-sonnet-5",
        prompt_version="cs-v1-test", run_date="2026-09-01",
        reports_subdir=str(tmp_path / "out"), paths=paths,
        replay=CSReplayConfig(enabled=True, fixture_path="tests/fixtures/cluster_strategy",
                              llm="recorded"),
    )
    result = run_cluster_strategy(_SIDECAR, config=cfg, project_root=PROJECT_ROOT,
                                  now="2026-09-01T18:00:00Z")
    assert result.registry_updated is False
    assert reg.read_text() == before  # byte-identical — nothing written
