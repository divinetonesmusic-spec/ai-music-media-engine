"""D-CS-7 — link a Cluster Strategy back to the opportunity registry.

Appends ``cluster_strategy_ref`` and one ``state_history`` note to the
opportunity's entry in ``knowledge/market/opportunity-registry.yaml`` using the
SAME append-only mechanism as ``market_intelligence.registry`` (governance
exception, spec §17): existing entries keep their file order, nothing is
rewritten in place, every change is visible in ``git diff``. The opportunity's
``status`` (EXPLORE/TEST/PARK) is NOT touched — Cluster Strategy never transitions
the lifecycle (I2, autonomy L1).

If the opportunity is not yet in the registry (e.g. a replay-origin opportunity),
this is a no-op — Cluster Strategy does not create registry entries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import yaml

from market_intelligence.io_utils import LoadError, read_yaml, write_text

_SCHEMA_VERSION = "1.0.0"


def append_cluster_strategy_ref(
    cs, *, config, project_root: Union[str, Path], generated_at: str
) -> bool:
    root = Path(project_root)
    path = root / config.paths.registry_path
    if not path.exists():
        return False
    try:
        raw = read_yaml(path)
    except LoadError:
        return False
    entries = raw.get("opportunities", []) if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        return False

    oid = cs.opportunity.opportunity_id
    # the registry records the CANONICAL committed location, independent of a
    # test's reports_subdir override.
    ref = f"reports/cluster-strategy/{oid}.md"
    touched = False
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("opportunity_id") != oid:
            continue
        if entry.get("cluster_strategy_ref") == ref:
            return False  # idempotent — already linked to this report
        entry["cluster_strategy_ref"] = ref
        entry.setdefault("state_history", []).append({
            "to": entry.get("status"),  # unchanged — lifecycle is carried, not transitioned
            "at": generated_at,
            "by": "system",
            "note": (
                f"cluster strategy {config.run_id}: "
                f"{cs.cluster_decision.decision.value}"
                + (f" ({cs.cluster_decision.cluster_id})" if cs.cluster_decision.cluster_id else "")
                + f"; next: {cs.recommendation.target_next_stage.value}"
            ),
        })
        touched = True
        break

    if not touched:
        return False

    payload = {"schema_version": _SCHEMA_VERSION, "opportunities": entries}
    write_text(
        path,
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False),
    )
    return True
