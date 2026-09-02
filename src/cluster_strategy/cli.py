"""``python -m cluster_strategy <opportunity-report.json>`` — Cluster Strategy V1.

Runs canonical pipeline stage 3 on ONE owner-advanced Opportunity Report and
writes ``reports/cluster-strategy/<opportunity_id>.{md,json}``. Autonomy L1 —
recommends, never executes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .config import ClusterStrategyConfigError, load_config
from .orchestrator import ClusterStrategyError, run_cluster_strategy

_DEFAULT_CONFIG = "config/cluster-strategy.example.yaml"


def _summary(result) -> str:
    cs = result.cluster_strategy
    d = cs.cluster_decision
    lines = [
        f"opportunity:      {cs.opportunity.opportunity_id}  ({cs.opportunity.title})",
        f"cluster decision: {d.decision.value}"
        + (f"  -> {d.cluster_id} ({d.cluster_name})" if d.cluster_id else ""),
    ]
    if d.subcluster_or_angle:
        lines.append(f"subcluster/angle: {d.subcluster_or_angle}"
                     + ("  (new)" if d.is_new_subcluster else ""))
    if d.new_cluster_proposal:
        lines.append(f"new cluster:      PROPOSAL {d.new_cluster_proposal.proposed_id} "
                     "(hand-off to the owner — P6 deferred)")
    lines += [
        f"overall_confidence: {cs.evaluation.overall_confidence.value}  "
        f"(opportunity: {cs.opportunity.overall_confidence.value})",
        f"next stage:       {cs.recommendation.target_next_stage.value}  "
        f"(opportunity lifecycle unchanged: {cs.recommendation.opportunity_lifecycle_state.value})",
        f"red flags:        {len(cs.evaluation.red_flags)}  "
        f"| open questions: {len(cs.evaluation.open_questions)}",
        f"llm mode:         {result.llm_mode}",
        f"report:           {result.report_path}",
        f"sidecar:          {result.sidecar_path}",
        "registry link:    "
        + ("appended cluster_strategy_ref" if result.registry_updated else "not written"),
    ]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="cluster_strategy")
    parser.add_argument(
        "opportunity_report",
        help="path to an Opportunity Report sidecar (reports/<run_id>/<opportunity_id>.json)",
    )
    parser.add_argument("--config", default=_DEFAULT_CONFIG,
                        help=f"cluster-strategy config YAML (default: {_DEFAULT_CONFIG})")
    parser.add_argument("--review", default=None,
                        help="path to the run's review.md (default: alongside the sidecar)")
    parser.add_argument("--project-root", default=".", help="repo root (default: cwd)")
    args = parser.parse_args(argv)

    root = Path(args.project_root)
    try:
        config = load_config(args.config, project_root=root)
    except ClusterStrategyConfigError as e:
        print(f"CONFIG ERROR\n{e}")
        return 1

    try:
        result = run_cluster_strategy(
            args.opportunity_report,
            config=config,
            project_root=root,
            review_md_path=args.review,
        )
    except ClusterStrategyError as e:
        print(f"CLUSTER STRATEGY FAILED\n{e}")
        return 1

    print(_summary(result))
    if result.validation_warnings:
        print("\nwarnings:")
        for w in result.validation_warnings:
            print(f"  - {w}")
    print("\nCLUSTER STRATEGY OK  (recommendation only — human approval required)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
