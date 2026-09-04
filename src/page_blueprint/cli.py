"""``python -m page_blueprint <cluster-strategy-sidecar.json>`` — Page Blueprint V1.

Runs canonical pipeline stage 4 on ONE Cluster-Strategy-recommended sidecar and
writes ``reports/page-blueprint/<opportunity_id>.{md,json}``. Autonomy L1 —
recommends, never executes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .config import PageBlueprintConfigError, load_config
from .orchestrator import PageBlueprintError, run_page_blueprint

_DEFAULT_CONFIG = "config/page-blueprint.example.yaml"


def _summary(result) -> str:
    pb = result.page_blueprint
    ident = pb.identity
    lines = [
        f"opportunity:      {pb.cluster_strategy.opportunity_id}",
        f"cluster strategy: {pb.cluster_strategy.cluster_strategy_id}",
        f"page concept:     {ident.concept_name}",
        f"primary page:     {pb.asset_link.page_strategy.primary_page_id}",
        f"overall_confidence: {pb.evaluation.overall_confidence.value}  "
        f"(cluster strategy: {pb.cluster_strategy.overall_confidence.value})",
        f"next stage:       {pb.recommendation.target_next_stage.value}",
        f"red flags:        {len(pb.evaluation.red_flags)}  "
        f"| blocked_by: {len(pb.evaluation.blocked_by)}",
        f"llm mode:         {result.llm_mode}",
        f"report:           {result.report_path}",
        f"sidecar:          {result.sidecar_path}",
    ]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="page_blueprint")
    parser.add_argument(
        "cluster_strategy_sidecar",
        help="path to a ClusterStrategy sidecar (reports/cluster-strategy/<opportunity_id>.json)",
    )
    parser.add_argument("--config", default=_DEFAULT_CONFIG,
                        help=f"page-blueprint config YAML (default: {_DEFAULT_CONFIG})")
    parser.add_argument("--project-root", default=".", help="repo root (default: cwd)")
    args = parser.parse_args(argv)

    root = Path(args.project_root)
    try:
        config = load_config(args.config, project_root=root)
    except PageBlueprintConfigError as e:
        print(f"CONFIG ERROR\n{e}")
        return 1

    try:
        result = run_page_blueprint(
            args.cluster_strategy_sidecar,
            config=config,
            project_root=root,
        )
    except PageBlueprintError as e:
        print(f"PAGE BLUEPRINT FAILED\n{e}")
        return 1

    print(_summary(result))
    if result.validation_warnings:
        print("\nwarnings:")
        for w in result.validation_warnings:
            print(f"  - {w}")
    print("\nPAGE BLUEPRINT OK  (recommendation only — human approval required)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
