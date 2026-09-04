"""Page Blueprint V1 — CLI (contract §8)."""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from page_blueprint import cli
from page_blueprint.config import PageBlueprintConfigError, load_config

_SIDECAR = str(PROJECT_ROOT / "reports" / "cluster-strategy" / "opp_2026-08-31_1bca4af972.json")
_NOT_RECOMMENDED = str(
    PROJECT_ROOT / "reports" / "run_2026-08-31_01" / "opp_2026-08-31_1bca4af972.json"
)  # an Opportunity Report, not a ClusterStrategy sidecar -> input gate rejects it


def _config_yaml(tmp_path) -> str:
    p = tmp_path / "pb.yaml"
    p.write_text(
        "run_id: pb_run_test_01\n"
        "run_date: '2026-09-04'\n"
        "model: claude-sonnet-5\n"
        "prompt_version: pb-v1-test\n"
        f"reports_subdir: {tmp_path / 'out'}\n"
        "replay:\n"
        "  enabled: true\n"
        "  fixture_path: tests/fixtures/page_blueprint\n"
        "  llm: recorded\n",
        encoding="utf-8",
    )
    return str(p)


def test_cli_runs_the_stage_and_prints_a_summary(tmp_path, capsys):
    rc = cli.main([_SIDECAR, "--config", _config_yaml(tmp_path),
                   "--project-root", str(PROJECT_ROOT)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "page concept:     Ritual Nuevo Hogar" in out
    assert "next stage:       CONTENT_STRATEGY" in out
    assert "PAGE BLUEPRINT OK" in out
    assert (tmp_path / "out" / "opp_2026-08-31_1bca4af972.md").is_file()


def test_cli_reports_a_bad_config(tmp_path, capsys):
    rc = cli.main([_SIDECAR, "--config", str(tmp_path / "nope.yaml"),
                   "--project-root", str(PROJECT_ROOT)])
    assert rc == 1
    assert "CONFIG ERROR" in capsys.readouterr().out


def test_cli_reports_a_run_failure_nonzero(tmp_path, capsys):
    rc = cli.main([_NOT_RECOMMENDED, "--config", _config_yaml(tmp_path),
                   "--project-root", str(PROJECT_ROOT)])
    assert rc == 1
    assert "PAGE BLUEPRINT FAILED" in capsys.readouterr().out


def test_load_config_defaults_run_id_and_run_date(tmp_path):
    p = tmp_path / "pb.yaml"
    p.write_text(
        "model: claude-sonnet-5\nprompt_version: pb-v1-test\n",
        encoding="utf-8",
    )
    cfg = load_config(p, project_root=PROJECT_ROOT)
    assert cfg.run_id.startswith("pb_run_")
    assert cfg.schema_version == "1.0.0"


def test_load_config_missing_file_is_an_error(tmp_path):
    import pytest
    with pytest.raises(PageBlueprintConfigError):
        load_config(tmp_path / "nope.yaml", project_root=PROJECT_ROOT)
