"""Signal Collection entry point (spec §5 lifecycle step 1, §18 component 1).

``run_collection`` closes stage 1 end to end: load config → ``collect_signals``
(all four collectors, degrade per source, hard-fail only if every source fails,
§14) → write a run manifest. It does **not** run Signal Normalization (dedup,
Claude classification) or anything downstream.

The manifest ``data/<run_id>/signals/collected.json`` is a run artifact, not a
new business entity: it carries the collected ``Signal`` list (an existing §6
entity) plus the run's source outcomes. The raw captures under
``data/<run_id>/signals/raw/`` remain the source of truth for replay. Given a
fixed clock (or ``replay`` mode) the manifest is byte-reproducible.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Callable, Optional, Union

from ..config.loader import ConfigError, load_run_config
from ..schema.codec import encode
from ..schema.models import RunConfig
from ..schema.validate import blocking, validate_run_config
from .base import CollectionResult, collect_signals

MANIFEST_SCHEMA_VERSION = "1.0.0"

ConfigLike = Union[RunConfig, str, Path]


def run_collection(
    config: ConfigLike,
    *,
    project_root: Union[str, Path],
    now: Optional[Callable[[], _dt.datetime]] = None,
) -> CollectionResult:
    """Run Signal Collection and persist ``data/<run_id>/signals/collected.json``.

    ``config`` may be a resolved ``RunConfig`` (trusted) or a path to a config
    YAML (loaded and validated here; a blocking config error raises ``ConfigError``).
    Propagates ``SignalCollectionError`` when every configured source fails (§14).
    """
    root = Path(project_root)
    cfg = config if isinstance(config, RunConfig) else _load_and_validate(config, root)

    result = collect_signals(cfg, project_root=root, now=now)
    _write_manifest(result, cfg, root)
    return result


def manifest_path(cfg: RunConfig, project_root: Union[str, Path]) -> Path:
    return Path(project_root) / cfg.paths.data_dir / cfg.run_id / "signals" / "collected.json"


def build_manifest(result: CollectionResult, cfg: RunConfig) -> dict:
    signals = sorted(result.signals, key=lambda s: s.signal_id)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": cfg.run_id,
        "replay": result.replay,
        "signal_count": len(signals),
        "sources_used": result.sources_used,
        "sources_failed": result.sources_failed,
        "signal_ids": [s.signal_id for s in signals],
        "signals": [encode(s) for s in signals],
    }


def _load_and_validate(config_path: Union[str, Path], root: Path) -> RunConfig:
    cfg = load_run_config(config_path, project_root=root)
    errs = blocking(
        validate_run_config(cfg, project_root=root, require_knowledge_paths=False)
    )
    if errs:
        raise ConfigError(
            "run config failed validation:\n"
            + "\n".join(f"  - [{e.code}] {e.path}: {e.message}" for e in errs)
        )
    return cfg


def _write_manifest(result: CollectionResult, cfg: RunConfig, root: Path) -> Path:
    path = manifest_path(cfg, root)
    path.parent.mkdir(parents=True, exist_ok=True)  # runtime structure only
    text = json.dumps(build_manifest(result, cfg), indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")
    return path
