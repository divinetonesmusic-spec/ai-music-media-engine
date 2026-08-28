"""Config loading — RunConfig, ranking.yaml, dedup.yaml (spec §20)."""

from __future__ import annotations

import datetime as dt

import pytest

from market_intelligence.config.loader import (
    ConfigError,
    load_dedup_config,
    load_ranking_config,
    load_run_config,
)
from market_intelligence.schema.models import RunConfig
from market_intelligence.schema.validate import validate_run_config


def test_run_example_loads_and_validates_against_the_real_repo(project_root):
    cfg = load_run_config("config/run.example.yaml", project_root=project_root)
    assert isinstance(cfg, RunConfig)
    assert validate_run_config(cfg, project_root=project_root) == []


def test_run_example_uses_only_sources_that_need_no_capture_file(project_root):
    cfg = load_run_config("config/run.example.yaml", project_root=project_root)
    assert [s.value for s in cfg.signal_sources] == ["web_search", "youtube"]


def test_loader_fills_run_date_and_run_id_when_absent(project_root, tmp_path):
    (tmp_path / "c.yaml").write_text(
        'schema_version: "1.0.0"\nmodel: "claude-sonnet-5"\nprompt_version: "p"\n',
        encoding="utf-8",
    )
    cfg = load_run_config(
        tmp_path / "c.yaml", project_root=project_root, today=dt.date(2026, 8, 28)
    )
    assert cfg.run_date == "2026-08-28"
    assert cfg.run_id == "run_2026-08-28_01"


def test_loader_respects_explicit_run_id(project_root, tmp_path):
    (tmp_path / "c.yaml").write_text(
        'schema_version: "1.0.0"\nrun_id: my_run\nmodel: m\nprompt_version: p\n',
        encoding="utf-8",
    )
    cfg = load_run_config(tmp_path / "c.yaml", project_root=project_root)
    assert cfg.run_id == "my_run"


def test_loader_raises_on_missing_file(project_root):
    with pytest.raises(ConfigError):
        load_run_config("config/nope.yaml", project_root=project_root)


def test_loader_raises_on_unknown_field(project_root, tmp_path):
    (tmp_path / "c.yaml").write_text(
        'schema_version: "1.0.0"\nmodel: m\nprompt_version: p\nmystery: 1\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_run_config(tmp_path / "c.yaml", project_root=project_root)


def test_loader_raises_on_non_mapping_yaml(project_root, tmp_path):
    (tmp_path / "c.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_run_config(tmp_path / "c.yaml", project_root=project_root)


def test_ranking_config_loads_with_the_nine_comparator_stages(project_root):
    rk = load_ranking_config(project_root=project_root)
    assert rk["schema_version"] == "1.0.0"
    keys = [k["key"] for k in rk["comparator_keys"]]
    assert keys == [
        "overall_confidence",
        "count_dimensions_high_or_very_high",
        "count_axes_high_or_very_high",
        "urgency",
        "durability",
        "non_compliance_red_flags",
        "asset_fit_rating",
        "opportunity_id",
    ]
    assert rk["hard_exclusion"]["zero_observed_evidence"] is True
    assert rk["value_engine_weighting"] == "NEEDS_INPUT"


def test_dedup_config_loads_with_the_seven_key_parts(project_root):
    dd = load_dedup_config(project_root=project_root)
    assert dd["schema_version"] == "1.0.0"
    assert dd["dedup_key_parts"] == [
        "normalized_source",
        "canonical_url",
        "market",
        "language",
        "platform",
        "signal_type",
        "normalized_subject",
    ]
    assert dd["duplicate_requires_same_observed_at"] is True
    assert set(dd["stopwords"]) == {"en", "pt", "es"}


def test_ranking_and_dedup_loaders_raise_on_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        load_ranking_config(project_root=tmp_path)
    with pytest.raises(ConfigError):
        load_dedup_config(project_root=tmp_path)
