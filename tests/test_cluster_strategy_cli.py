"""Cluster Strategy V1 — CLI (contract §14)."""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from cluster_strategy import cli

_SIDECAR = str(PROJECT_ROOT / "reports" / "run_2026-08-31_01" / "opp_2026-08-31_1bca4af972.json")


def _config_yaml(tmp_path, *, registry_link="false") -> str:
    p = tmp_path / "cs.yaml"
    p.write_text(
        "run_id: cs_run_test_01\n"
        "run_date: '2026-09-01'\n"
        "model: claude-sonnet-5\n"
        "prompt_version: cs-v1-test\n"
        f"reports_subdir: {tmp_path / 'out'}\n"
        f"write_registry_link: {registry_link}\n"
        "replay:\n"
        "  enabled: true\n"
        "  fixture_path: tests/fixtures/cluster_strategy\n"
        "  llm: recorded\n",
        encoding="utf-8",
    )
    return str(p)


def test_cli_runs_the_stage_and_prints_a_summary(tmp_path, capsys):
    rc = cli.main([_SIDECAR, "--config", _config_yaml(tmp_path),
                   "--project-root", str(PROJECT_ROOT)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "cluster decision: MAP_TO_EXISTING  -> limpeza-energetica" in out
    assert "next stage:       PAGE_BLUEPRINT" in out
    assert "opportunity lifecycle unchanged: EXPLORE" in out
    assert "CLUSTER STRATEGY OK" in out
    assert (tmp_path / "out" / "opp_2026-08-31_1bca4af972.md").is_file()


def test_cli_reports_a_bad_config(tmp_path, capsys):
    rc = cli.main([_SIDECAR, "--config", str(tmp_path / "nope.yaml"),
                   "--project-root", str(PROJECT_ROOT)])
    assert rc == 1
    assert "CONFIG ERROR" in capsys.readouterr().out


def test_cli_reports_a_run_failure_nonzero(tmp_path, capsys):
    # point at an opportunity report that was NOT advanced
    other = str(PROJECT_ROOT / "reports" / "run_2026-08-31_01" / "opp_2026-08-31_3c6c875d54.json")
    rc = cli.main([other, "--config", _config_yaml(tmp_path), "--project-root", str(PROJECT_ROOT)])
    assert rc == 1
    assert "CLUSTER STRATEGY FAILED" in capsys.readouterr().out
