"""Preflight — the deterministic head of the V1 run lifecycle (spec §5):

    load & validate config
      -> Knowledge Loader (business DNA, guardrails, taxonomy, 4 inventories, registry)
         [hard-fail if any required file is missing]

Everything from Signal Collection onward is out of scope here. ``preflight`` is
what the orchestrator will call before stage 1; it is also runnable on its own
(``python -m market_intelligence preflight <config>``, wired in ``cli.py``) as a
Foundation sanity check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Union

from .config.loader import ConfigError, load_run_config
from .knowledge_loader import KnowledgeBundle, KnowledgeError, load_knowledge
from .schema.models import RunConfig
from .schema.validate import ValidationError, blocking, validate_run_config


class PreflightError(Exception):
    """Preflight could not produce a usable (config, knowledge) pair."""


@dataclass
class PreflightResult:
    config: RunConfig
    knowledge: KnowledgeBundle
    config_errors: List[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not blocking(self.config_errors)


def preflight(
    config_path: Union[str, Path, RunConfig],
    *,
    project_root: Path,
    strict: bool = True,
) -> PreflightResult:
    """Load + validate the run config, then load the knowledge bundle.

    ``config_path`` may be a path to a RunConfig YAML or an already-resolved
    ``RunConfig`` (used by the orchestrator / programmatic callers).

    ``strict`` (default): any blocking config error raises ``PreflightError``.
    ``strict=False``: the errors are returned on the result for the caller to
    render, and the knowledge bundle is still loaded.
    """
    root = Path(project_root)

    if isinstance(config_path, RunConfig):
        config = config_path
    else:
        try:
            config = load_run_config(config_path, project_root=root)
        except ConfigError as e:
            raise PreflightError(f"run config could not be loaded: {e}") from e

    config_errors = validate_run_config(config, project_root=root)
    if strict and blocking(config_errors):
        raise PreflightError(
            "run config failed validation:\n"
            + "\n".join(f"  - [{e.code}] {e.path}: {e.message}" for e in blocking(config_errors))
        )

    try:
        knowledge = load_knowledge(config.paths, project_root=root)
    except KnowledgeError as e:
        raise PreflightError(f"knowledge base could not be loaded: {e}") from e

    return PreflightResult(config=config, knowledge=knowledge, config_errors=config_errors)
