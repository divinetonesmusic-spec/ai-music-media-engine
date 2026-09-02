"""Cluster Strategy run configuration (contract §14). Mirrors the pipeline's
``RunConfig`` pattern — reuses ``market_intelligence.schema.models.RunPaths`` for
the knowledge-file locations so both stages read the same tree."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from market_intelligence.io_utils import LoadError, read_yaml
from market_intelligence.schema.codec import CodecError, decode
from market_intelligence.schema.models import RunPaths


class ClusterStrategyConfigError(Exception):
    """The config file is missing, malformed, or does not match the schema."""


@dataclass
class CSReplayConfig:
    enabled: bool = False
    fixture_path: Optional[str] = None
    llm: Optional[str] = None  # "recorded" | "live"


@dataclass
class ClusterStrategyConfig:
    run_id: str  # this Cluster Strategy run's id
    model: str
    prompt_version: str
    run_date: str
    schema_version: str = "1.0.0"
    reports_subdir: str = "reports/cluster-strategy"
    # D-CS-7 — appending `cluster_strategy_ref` to the human-owned
    # opportunity-registry.yaml is OPT-IN. A normal or offline run never mutates
    # `knowledge/` unless a config or the owner explicitly sets this to true.
    write_registry_link: bool = False
    paths: RunPaths = field(default_factory=RunPaths)
    replay: CSReplayConfig = field(default_factory=CSReplayConfig)


def load_config(
    config_path: Union[str, Path], *, project_root: Union[str, Path],
    today: Optional[_dt.date] = None,
) -> ClusterStrategyConfig:
    root = Path(project_root)
    path = Path(config_path)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise ClusterStrategyConfigError(f"cluster-strategy config not found: {path}")
    try:
        raw = read_yaml(path)
    except LoadError as e:
        raise ClusterStrategyConfigError(str(e)) from e
    if not isinstance(raw, dict):
        raise ClusterStrategyConfigError(f"config must be a YAML mapping: {path}")
    raw.setdefault("run_date", (today or _dt.date.today()).isoformat())
    raw.setdefault("run_id", f"cs_run_{raw['run_date']}_01")
    try:
        return decode(ClusterStrategyConfig, raw)
    except CodecError as e:
        raise ClusterStrategyConfigError(f"invalid config {path}: {e}") from e
