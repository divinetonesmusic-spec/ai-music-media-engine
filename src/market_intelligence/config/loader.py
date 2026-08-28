"""Load and normalise run configuration (docs/TECHNICAL-SPEC-V1.md §20).

``load_run_config`` fills the two loader-supplied defaults (``run_id``,
``run_date`` — spec §20.1) and decodes into a ``RunConfig``. It does NOT run
``validate_run_config`` — the orchestrator does that so it can report every
config error at once.

``load_ranking_config`` / ``load_dedup_config`` read the data-driven comparator
and dedup-key definitions (§11.1, §6.6). They return plain dicts; the components
that consume them (Ranking, Signal Normalization) own their typed interpretation.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Optional

from ..io_utils import LoadError, read_yaml
from ..schema.codec import CodecError, decode
from ..schema.models import RunConfig, RunPaths

_DEFAULT_RANKING_PATH = "config/ranking.yaml"
_DEFAULT_DEDUP_PATH = "config/dedup.yaml"


class ConfigError(Exception):
    """A configuration file is missing, malformed, or does not match its schema."""


def _resolve(path, project_root: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(project_root) / p


def _default_run_id(run_date: str, project_root: Path, reports_dir: str = "reports") -> str:
    base = f"run_{run_date}_"
    reports = Path(project_root) / reports_dir
    existing = {p.name for p in reports.glob(f"{base}*")} if reports.is_dir() else set()
    n = 1
    while f"{base}{n:02d}" in existing:
        n += 1
    return f"{base}{n:02d}"


def load_run_config(
    config_path,
    *,
    project_root: Path,
    today: Optional[_dt.date] = None,
) -> RunConfig:
    path = _resolve(config_path, project_root)
    if not path.exists():
        raise ConfigError(f"run config not found: {path}")

    try:
        raw = read_yaml(path)
    except LoadError as e:
        raise ConfigError(str(e)) from e
    if not isinstance(raw, dict):
        raise ConfigError(f"run config must be a YAML mapping: {path}")

    raw.setdefault("run_date", (today or _dt.date.today()).isoformat())
    reports_dir = (raw.get("paths") or {}).get("reports_dir", RunPaths().reports_dir)
    raw.setdefault("run_id", _default_run_id(raw["run_date"], project_root, reports_dir))

    try:
        return decode(RunConfig, raw)
    except CodecError as e:
        raise ConfigError(f"invalid run config {path}: {e}") from e


def _load_config_dict(path, project_root: Path, *, label: str, required_keys) -> dict:
    resolved = _resolve(path, project_root)
    if not resolved.exists():
        raise ConfigError(f"{label} config not found: {resolved}")
    try:
        data = read_yaml(resolved)
    except LoadError as e:
        raise ConfigError(str(e)) from e
    if not isinstance(data, dict):
        raise ConfigError(f"{label} config must be a YAML mapping: {resolved}")
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ConfigError(f"{label} config {resolved} is missing keys: {missing}")
    if data.get("schema_version") != "1.0.0":
        raise ConfigError(f"{label} config {resolved} has unexpected schema_version")
    return data


def load_ranking_config(*, project_root: Path, path=_DEFAULT_RANKING_PATH) -> dict:
    return _load_config_dict(
        path, project_root, label="ranking",
        required_keys=("schema_version", "hard_exclusion", "comparator_keys"),
    )


def load_dedup_config(*, project_root: Path, path=_DEFAULT_DEDUP_PATH) -> dict:
    return _load_config_dict(
        path, project_root, label="dedup",
        required_keys=("schema_version", "dedup_key_parts", "on_duplicate"),
    )
