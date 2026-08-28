"""Preflight — the deterministic head of the run lifecycle (spec §5):
``load & validate config -> Knowledge Loader``. No signal collection."""

from __future__ import annotations

import pytest

from market_intelligence.preflight import PreflightError, preflight


def test_preflight_succeeds_against_the_real_repo(project_root):
    result = preflight("config/run.example.yaml", project_root=project_root)
    assert result.ok
    assert result.config.run_id.startswith("run_")
    assert [g.guardrail_id for g in result.knowledge.guardrails][0] == "G01"
    assert len(result.knowledge.clusters) == 11
    assert result.config_errors == []


def test_preflight_reports_config_errors_without_raising(project_root, tmp_path):
    (tmp_path / "bad.yaml").write_text(
        'schema_version: "1.0.0"\nrun_id: "has spaces"\nmodel: m\nprompt_version: p\n'
        'signal_sources: ["web_search"]\n',
        encoding="utf-8",
    )
    result = preflight(tmp_path / "bad.yaml", project_root=project_root, strict=False)
    assert not result.ok
    assert any(e.code == "config.run_id_pattern" for e in result.config_errors)


def test_preflight_strict_raises_on_config_error(project_root, tmp_path):
    (tmp_path / "bad.yaml").write_text(
        'schema_version: "1.0.0"\nrun_id: "has spaces"\nmodel: m\nprompt_version: p\n'
        'signal_sources: ["web_search"]\n',
        encoding="utf-8",
    )
    with pytest.raises(PreflightError):
        preflight(tmp_path / "bad.yaml", project_root=project_root, strict=True)


def test_preflight_fails_when_the_environment_is_incomplete(tmp_path):
    # a bare project root: no knowledge/ tree, no config/ files
    (tmp_path / "config").mkdir()
    (tmp_path / "config/run.example.yaml").write_text(
        'schema_version: "1.0.0"\nmodel: m\nprompt_version: p\nsignal_sources: ["web_search"]\n',
        encoding="utf-8",
    )
    with pytest.raises(PreflightError):
        preflight("config/run.example.yaml", project_root=tmp_path)
