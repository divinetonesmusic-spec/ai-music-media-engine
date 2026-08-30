"""``python -m market_intelligence <command>`` — the V1 command line.

Commands:
  preflight <config>   load + validate config and the knowledge base (spec §5)
  collect   <config>   run Signal Collection (spec §18 stage 1) — NOT Normalization
  normalize <config>   run Signal Collection + Normalization (stages 1–2) — NOT Analysis
  run       <config>   run the full Market Intelligence V1 pipeline (spec §5)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .collect.base import SignalCollectionError
from .collect.runner import manifest_path, run_collection
from .config.loader import ConfigError, load_dedup_config, load_run_config
from .normalize.runner import normalized_path, run_normalization
from .orchestrator import OrchestratorError, run_pipeline
from .preflight import PreflightError, PreflightResult, preflight
from .schema.validate import blocking, validate_run_config


def _preflight_summary(result: PreflightResult) -> str:
    kb = result.knowledge
    g_first, g_last = kb.guardrails[0].guardrail_id, kb.guardrails[-1].guardrail_id
    return "\n".join([
        f"run_id:         {result.config.run_id}",
        f"run_date:       {result.config.run_date}",
        f"model:          {result.config.model}",
        f"signal_sources: {[s.value for s in result.config.signal_sources]}",
        f"guardrails:     {len(kb.guardrails)} ({g_first}..{g_last})",
        f"clusters:       {len(kb.clusters)} canonical",
        f"inventory:      {len(kb.artists)} artists, {len(kb.playlists)} playlists, "
        f"{len(kb.pages)} pages ({len(kb.inventory.own_page_ids)} own), {len(kb.catalog)} catalog",
        f"registry:       {len(kb.registry)} opportunities",
        f"config errors:  {len(result.config_errors)}",
    ])


def _run_preflight(config: str, root: Path, *, strict: bool) -> int:
    try:
        result = preflight(config, project_root=root, strict=strict)
    except PreflightError as e:
        print(f"PREFLIGHT FAILED\n{e}")
        return 1
    print(_preflight_summary(result))
    if not result.ok:
        print("\nconfig errors:")
        for e in result.config_errors:
            print(f"  - [{e.code}] {e.path}: {e.message}")
        return 1
    print("\nPREFLIGHT OK")
    return 0


def _run_collect(config: str, root: Path) -> int:
    try:
        cfg = load_run_config(config, project_root=root)
    except ConfigError as e:
        print(f"COLLECT FAILED (config could not be loaded)\n{e}")
        return 1
    errs = blocking(
        validate_run_config(cfg, project_root=root, require_knowledge_paths=False)
    )
    if errs:
        print("COLLECT FAILED (config failed validation)")
        for e in errs:
            print(f"  - [{e.code}] {e.path}: {e.message}")
        return 1

    try:
        result = run_collection(cfg, project_root=root)
    except SignalCollectionError as e:
        print(f"COLLECT FAILED (every configured signal source failed)\n{e}")
        return 1

    man = manifest_path(cfg, root)
    try:
        man_display = man.relative_to(root)
    except ValueError:  # pragma: no cover
        man_display = man
    print(f"run_id:         {cfg.run_id}")
    print(f"replay:         {result.replay}")
    print(f"signals:        {len(result.signals)}")
    print(f"sources_used:   {result.sources_used or '(none)'}")
    if result.sources_failed:
        print("sources_failed:")
        for f in result.sources_failed:
            print(f"  - {f['source']}: {f['reason']}")
    else:
        print("sources_failed: (none)")
    print(f"manifest:       {man_display}")
    if len(result.signals) < cfg.min_opportunities_target:
        print(
            f"\nnote: {len(result.signals)} signals collected "
            f"(below the C10 target of {cfg.min_opportunities_target})"
        )
    print("\nCOLLECT OK  (Signal Collection only — Normalization not run)")
    return 0


def _run_normalize(config: str, root: Path) -> int:
    try:
        cfg = load_run_config(config, project_root=root)
    except ConfigError as e:
        print(f"NORMALIZE FAILED (config could not be loaded)\n{e}")
        return 1
    errs = blocking(
        validate_run_config(cfg, project_root=root, require_knowledge_paths=False)
    )
    if errs:
        print("NORMALIZE FAILED (config failed validation)")
        for e in errs:
            print(f"  - [{e.code}] {e.path}: {e.message}")
        return 1

    try:
        collection = run_collection(cfg, project_root=root)
    except SignalCollectionError as e:
        print(f"NORMALIZE FAILED (every configured signal source failed)\n{e}")
        return 1

    try:
        dedup_config = load_dedup_config(project_root=root, path=cfg.paths.dedup_config_path)
    except ConfigError as e:
        print(f"NORMALIZE FAILED (dedup config)\n{e}")
        return 1

    result = run_normalization(
        collection.signals, config=cfg, project_root=root, dedup_config=dedup_config
    )
    det = result.deterministic
    out = normalized_path(cfg, root)
    try:
        out_display = out.relative_to(root)
    except ValueError:  # pragma: no cover
        out_display = out
    print(f"run_id:           {cfg.run_id}")
    print(f"replay:           {result.llm.replay} (llm: {result.llm.llm_mode})")
    print(f"collected:        {len(collection.signals)}")
    print(f"invalid dropped:  {len(det.invalid_signals)}")
    print(f"dedup dropped:    {len(det.discarded_signal_ids)}")
    print(f"llm changes:      {sum(1 for c in result.llm.changes if c.applied)} applied")
    print(f"normalized:       {len(result.signals)}")
    print(f"manifest:         {out_display}")
    print("\nNORMALIZE OK  (Signal Collection + Normalization — Analysis not run)")
    return 0


def _run_pipeline(config: str, root: Path) -> int:
    try:
        result = run_pipeline(config, project_root=root)
    except OrchestratorError as e:
        print(f"RUN FAILED\n{e}")
        return 1

    cfg_run_id = result.run_id
    print(f"run_id:          {cfg_run_id}")
    print(f"replay:          {result.replay}")
    print(f"signals:         collected {len(result.collection.signals)} / "
          f"normalized {len(result.normalization.signals)}")
    print(f"sources_used:    {result.collection.sources_used or '(none)'}")
    for f in result.collection.sources_failed:
        print(f"  source failed: {f['source']}: {f['reason']}")
    print(f"opportunities:   framed {len(result.framing.opportunities)}")

    if result.dry_run:
        print("\nRUN OK  (dry_run — stopped after Framing, spec §20.1)")
        return 0

    ranking = result.ranking
    reporting = result.reporting
    print(f"                 presented {len(ranking.presented)} · "
          f"parked {len(ranking.parked)} · excluded {len(ranking.excluded)}")
    for rank_id in ranking.presented:
        opp = reporting.opportunities.get(rank_id)
        if opp is not None:
            print(f"  #{opp.rank} {opp.title}  [{opp.recommendation.target_state.value}] "
                  f"({rank_id})")
    reg = result.registry
    print(f"registry:        +{len(reg.added)} new / ~{len(reg.updated)} updated "
          f"→ {reg.path.name} ({reg.total} total)")
    try:
        digest_display = reporting.digest_path.relative_to(root)
    except (ValueError, AttributeError):  # pragma: no cover
        digest_display = reporting.digest_path
    print(f"digest:          {digest_display}")
    if len(ranking.presented) < 5:
        print("\nnote: fewer than 5 opportunities presented (below the C10 target — §12.5)")
    print("\nRUN OK")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="market_intelligence")
    sub = parser.add_subparsers(dest="command", required=True)

    pf = sub.add_parser("preflight", help="load + validate config and knowledge (spec §5)")
    pf.add_argument("config", help="path to a RunConfig YAML (e.g. config/run.example.yaml)")
    pf.add_argument("--project-root", default=".", help="repo root (default: cwd)")
    pf.add_argument(
        "--no-strict", action="store_true", help="report config errors instead of failing"
    )

    co = sub.add_parser(
        "collect", help="run Signal Collection — stage 1 only, no Normalization (spec §18)"
    )
    co.add_argument("config", help="path to a RunConfig YAML")
    co.add_argument("--project-root", default=".", help="repo root (default: cwd)")

    no = sub.add_parser(
        "normalize",
        help="run Signal Collection + Normalization — stages 1–2 only (spec §18)",
    )
    no.add_argument("config", help="path to a RunConfig YAML")
    no.add_argument("--project-root", default=".", help="repo root (default: cwd)")

    rn = sub.add_parser(
        "run", help="run the full Market Intelligence V1 pipeline (spec §5)"
    )
    rn.add_argument("config", help="path to a RunConfig YAML")
    rn.add_argument("--project-root", default=".", help="repo root (default: cwd)")

    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()

    if args.command == "preflight":
        return _run_preflight(args.config, root, strict=not args.no_strict)
    if args.command == "collect":
        return _run_collect(args.config, root)
    if args.command == "normalize":
        return _run_normalize(args.config, root)
    if args.command == "run":
        return _run_pipeline(args.config, root)
    return 2  # pragma: no cover - argparse requires a subcommand
