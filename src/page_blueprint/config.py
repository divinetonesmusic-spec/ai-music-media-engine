"""Page Blueprint run configuration (contract §8). Mirrors Cluster Strategy's
``ClusterStrategyConfig`` pattern — reuses ``market_intelligence.schema.models.RunPaths``
for the knowledge-file locations so all three stages read the same tree."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from market_intelligence.io_utils import LoadError, read_yaml
from market_intelligence.schema.codec import CodecError, decode
from market_intelligence.schema.models import RunPaths


class PageBlueprintConfigError(Exception):
    """The config file is missing, malformed, or does not match the schema."""


@dataclass
class PBReplayConfig:
    enabled: bool = False
    fixture_path: Optional[str] = None  # "recorded" | "live"
    llm: Optional[str] = None


@dataclass
class PageBlueprintConfig:
    run_id: str  # this Page Blueprint run's id
    model: str
    prompt_version: str
    run_date: str
    schema_version: str = "1.0.0"
    reports_subdir: str = "reports/page-blueprint"
    paths: RunPaths = field(default_factory=RunPaths)
    replay: PBReplayConfig = field(default_factory=PBReplayConfig)


def load_config(
    config_path: Union[str, Path], *, project_root: Union[str, Path],
    today: Optional[_dt.date] = None,
) -> PageBlueprintConfig:
    root = Path(project_root)
    path = Path(config_path)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise PageBlueprintConfigError(f"page-blueprint config not found: {path}")
    try:
        raw = read_yaml(path)
    except LoadError as e:
        raise PageBlueprintConfigError(str(e)) from e
    if not isinstance(raw, dict):
        raise PageBlueprintConfigError(f"config must be a YAML mapping: {path}")
    raw.setdefault("run_date", (today or _dt.date.today()).isoformat())
    raw.setdefault("run_id", f"pb_run_{raw['run_date']}_01")
    try:
        return decode(PageBlueprintConfig, raw)
    except CodecError as e:
        raise PageBlueprintConfigError(f"invalid config {path}: {e}") from e
