"""Preflight — the deterministic head of the V1 run lifecycle (spec §5):

    load & validate config
      -> Knowledge Loader (business DNA, guardrails, taxonomy, 4 inventories, registry)
         [hard-fail if any required file is missing]

Everything from Signal Collection onward is out of scope here. ``preflight`` is
what the orchestrator will call before stage 1; it is also runnable on its own
(``python -m market_intelligence preflight <config>``) as a Foundation sanity check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

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
    config_path,
    *,
    project_root: Path,
    strict: bool = True,
) -> PreflightResult:
    """Load + validate the run config, then load the knowledge bundle.

    ``strict`` (default): any blocking config error raises ``PreflightError``.
    ``strict=False``: the errors are returned on the result for the caller to
    render, and the knowledge bundle is still loaded.
    """
    root = Path(project_root)

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


def _summary(result: PreflightResult) -> str:
    kb = result.knowledge
    g_first, g_last = kb.guardrails[0].guardrail_id, kb.guardrails[-1].guardrail_id
    lines = [
        f"run_id:        {result.config.run_id}",
        f"run_date:      {result.config.run_date}",
        f"model:         {result.config.model}",
        f"signal_sources: {[s.value for s in result.config.signal_sources]}",
        f"guardrails:    {len(kb.guardrails)} ({g_first}..{g_last})",
        f"clusters:      {len(kb.clusters)} canonical",
        f"inventory:     {len(kb.artists)} artists, {len(kb.playlists)} playlists, "
        f"{len(kb.pages)} pages ({len(kb.inventory.own_page_ids)} own), {len(kb.catalog)} catalog",
        f"registry:      {len(kb.registry)} opportunities",
        f"config errors: {len(result.config_errors)}",
    ]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="market_intelligence")
    sub = parser.add_subparsers(dest="command", required=True)
    pf = sub.add_parser("preflight", help="load + validate config and knowledge (spec §5)")
    pf.add_argument("config", help="path to a RunConfig YAML (e.g. config/run.example.yaml)")
    pf.add_argument("--project-root", default=".", help="repo root (default: cwd)")
    pf.add_argument(
        "--no-strict", action="store_true", help="report config errors instead of failing"
    )
    args = parser.parse_args(argv)

    try:
        result = preflight(
            args.config,
            project_root=Path(args.project_root).resolve(),
            strict=not args.no_strict,
        )
    except PreflightError as e:
        print(f"PREFLIGHT FAILED\n{e}")
        return 1

    print(_summary(result))
    if not result.ok:
        print("\nconfig errors:")
        for e in result.config_errors:
            print(f"  - [{e.code}] {e.path}: {e.message}")
        return 1
    print("\nPREFLIGHT OK")
    return 0
