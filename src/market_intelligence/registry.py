"""Registry Updater — spec §17, §18 Registry Updater, §5, §13, I2.

Maintains ``knowledge/market/opportunity-registry.yaml`` — the **one** file under
``knowledge/`` the pipeline may write (governance exception, §17). Rules:

* **append-only** — a new opportunity is appended; an opportunity already in the
  registry keeps its entry and gets one new ``state_history`` record for this run.
  Prior ``state_history`` is never rewritten; ``created_at`` and the first
  ``run_id`` are never changed.
* every change is visible in ``git diff`` (plain YAML, stable key order).
* ``status`` is EXPLORE (presented), PARK (parked / excluded) — never
  LAUNCH / SCALE / KILL (those stay conceptual in V1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

from .framing import FramedOpportunity
from .io_utils import LoadError, read_yaml
from .ranking import RankingResult
from .schema.models import Opportunity, RunConfig

SCHEMA_VERSION = "1.0.0"


class RegistryError(Exception):
    """The registry file exists but is not a shape the updater can safely append to."""


@dataclass
class RegistryUpdateResult:
    path: Path
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    total: int = 0


def _load_existing(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        raw = read_yaml(path)
    except LoadError as e:
        raise RegistryError(str(e)) from e
    if raw is None:
        return []
    if isinstance(raw, dict):
        entries = raw.get("opportunities", [])
    elif isinstance(raw, list):
        entries = raw
    else:
        raise RegistryError("registry must be a mapping with 'opportunities' or a list")
    if not isinstance(entries, list):
        raise RegistryError("registry 'opportunities' must be a list")
    return [dict(e) for e in entries if isinstance(e, dict)]


def _state_entry(to: str, at: str, note: str, from_: Optional[str] = None,
                 replay: bool = False) -> dict:
    entry = {"to": to, "at": at, "by": "system"}
    if from_ is not None:
        entry["from"] = from_
    entry["note"] = note
    if replay:
        entry["replay"] = True
    return entry


def _new_entry(opportunity_id: str, status: str, created_at: str, run_id: str,
               report_ref: Optional[str], at: str, note: str, replay: bool) -> dict:
    entry = {
        "opportunity_id": opportunity_id,
        "status": status,
        "created_at": created_at,
        "first_run_id": run_id,
        "last_run_id": run_id,
        "report_ref": report_ref,
        "state_history": [_state_entry(status, at, note, replay=replay)],
    }
    if replay:
        # §22 — a replay run's opportunities are historical fixtures, not current-trend
        # evidence. Mark the entry so a reader never mistakes it for a live discovery.
        entry["replay_origin"] = True
    return entry


def update_registry(
    presented: Dict[str, Opportunity],
    ranking: RankingResult,
    framed: Dict[str, FramedOpportunity],
    *,
    run_config: RunConfig,
    project_root: Union[str, Path],
    generated_at: str,
    registry_path: Optional[Path] = None,
    replay: bool = False,
) -> RegistryUpdateResult:
    root = Path(project_root)
    path = registry_path or (root / run_config.paths.registry_path)

    existing = _load_existing(path)
    by_id = {e.get("opportunity_id"): e for e in existing if e.get("opportunity_id")}

    added: List[str] = []
    updated: List[str] = []

    for ranked in ranking.ordered:
        oid = ranked.opportunity_id
        fo = framed.get(oid)
        if fo is None:
            continue
        status = ranked.status.value
        opp = presented.get(oid)
        report_ref = opp.report_ref if opp is not None else None
        note = f"run {run_config.run_id}: {ranked.bucket}"
        if ranked.exclusion_reason:
            note += f" — {ranked.exclusion_reason}"

        if oid not in by_id:
            entry = _new_entry(
                oid, status, fo.created_at, run_config.run_id, report_ref, generated_at, note,
                replay,
            )
            existing.append(entry)  # append-only: new entries go at the end (§17)
            by_id[oid] = entry
            added.append(oid)
        else:
            entry = by_id[oid]
            prev_status = entry.get("status")
            history = entry.setdefault("state_history", [])
            history.append(_state_entry(
                status, generated_at, note,
                from_=prev_status if prev_status and prev_status != status else None,
                replay=replay,
            ))
            entry["status"] = status
            entry["last_run_id"] = run_config.run_id
            if report_ref:
                entry["report_ref"] = report_ref
            updated.append(oid)

    # Existing entries keep their file order (localized git diff, §17); only the
    # newly appended ones extend the list.
    payload = {"schema_version": SCHEMA_VERSION, "opportunities": existing}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )
    return RegistryUpdateResult(path=path, added=added, updated=updated, total=len(existing))
