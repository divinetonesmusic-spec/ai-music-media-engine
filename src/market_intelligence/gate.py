"""C10 Definition-of-Done gate checker — spec §21, §21.1, §22 "Acceptance".

V1 is validated when, over **3 consecutive runs**, the owner-filled
``reports/<run_id>/review.md`` files show:

* **C10.1** — each run presents between 5 and 10 opportunities.
* **C10.5** — each run's ``relevant_ratio`` (relevant + advance ÷ presented) is ≥ 0.70.
* **C10.6** — at least one run in the window advanced an opportunity to the next stage.

C10.2–C10.4 (traceability, observed-vs-hypothesis, no invented assets) are
structural and enforced by the pipeline validators on every run (§13); this
checker covers the human-judged criteria that live in ``review.md``.

Pure functions over the review files — no network, no model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

from .io_utils import LoadError, read_yaml_front_matter

WINDOW = 3
VOLUME_MIN = 5
VOLUME_MAX = 10
RELEVANCE_THRESHOLD = 0.70

_DECISIONS = {"relevant", "not_relevant", "advance"}
_RELEVANT_DECISIONS = {"relevant", "advance"}


class GateError(Exception):
    """The review files cannot be read as a C10 gate window."""


@dataclass
class RunReview:
    """One run's owner review, parsed from ``reports/<run_id>/review.md``."""

    run_id: str
    path: Path
    opportunities_presented: Optional[int]
    relevant_count: Optional[int]
    relevant_ratio: Optional[float]
    advanced_opportunity_id: Optional[str]
    reviewed: bool


@dataclass
class GateResult:
    runs: List[RunReview]
    complete: bool = False
    c10_1_volume: bool = False
    c10_5_relevance: bool = False
    c10_6_advanced: bool = False
    passed: bool = False
    failures: List[str] = field(default_factory=list)


# --- parsing ---------------------------------------------------------

_ROW = re.compile(r"^\|(?P<cells>.+)\|\s*$")


def _decision_rows(body: str) -> List[tuple]:
    """``(rank, opportunity_id, title, owner_decision)`` for each filled table row."""
    rows: List[tuple] = []
    for line in body.splitlines():
        m = _ROW.match(line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group("cells").split("|")]
        if len(cells) < 4:
            continue
        rank, oid, title, decision = cells[0], cells[1], cells[2], cells[3].lower()
        if rank.lower() in ("rank", "") or set(rank) <= set("-: "):
            continue  # header / separator
        if not oid or oid.lower() == "opportunity_id":
            continue
        rows.append((rank, oid, title, decision))
    return rows


def _as_int(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _as_float(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_review(path: Path) -> RunReview:
    """Parse one ``review.md``. Front-matter values win; missing ones are
    derived from the owner's decision table when it is filled."""
    path = Path(path)
    try:
        fm, body = read_yaml_front_matter(path)
    except LoadError as e:
        raise GateError(f"{path}: {e}") from e

    run_id = str(fm.get("run_id") or path.parent.name)
    presented = _as_int(fm.get("opportunities_presented"))
    fm_count = _as_int(fm.get("opportunities_relevant_count"))
    fm_ratio = _as_float(fm.get("relevant_ratio"))
    advanced = fm.get("advanced_opportunity_id")
    advanced = str(advanced) if advanced not in (None, "", "null") else None

    rows = _decision_rows(body)
    decided = [d for (_, _, _, d) in rows if d]
    bad = sorted({d for d in decided if d not in _DECISIONS})
    if bad:
        raise GateError(
            f"{path}: unknown owner_decision value(s) {bad} — "
            f"use one of {sorted(_DECISIONS)}"
        )

    table_count = sum(1 for d in decided if d in _RELEVANT_DECISIONS) if decided else None
    table_advanced = next(
        (oid for (_, oid, _, d) in rows if d == "advance"), None
    )

    relevant_count = fm_count if fm_count is not None else table_count
    if advanced is None:
        advanced = table_advanced

    relevant_ratio = fm_ratio
    if relevant_ratio is None and relevant_count is not None and presented:
        relevant_ratio = relevant_count / presented

    reviewed = relevant_count is not None or bool(decided)

    return RunReview(
        run_id=run_id,
        path=path,
        opportunities_presented=presented,
        relevant_count=relevant_count,
        relevant_ratio=relevant_ratio,
        advanced_opportunity_id=advanced,
        reviewed=reviewed,
    )


# --- discovery ------------------------------------------------------


def discover_reviews(reports_dir: Path) -> List[Path]:
    """The 3 most recently modified ``review.md`` files under ``reports_dir``."""
    reports_dir = Path(reports_dir)
    found = sorted(
        reports_dir.glob("*/review.md"), key=lambda p: p.stat().st_mtime
    )
    if len(found) < WINDOW:
        raise GateError(
            f"need {WINDOW} review.md files for the C10 gate, found {len(found)} "
            f"under {reports_dir}"
        )
    return found[-WINDOW:]


# --- the gate ------------------------------------------------------


def check_gate(review_paths: Sequence[Path]) -> GateResult:
    paths = list(review_paths)
    if len(paths) != WINDOW:
        raise GateError(
            f"the C10 gate is defined over exactly {WINDOW} consecutive runs — "
            f"got {len(paths)}"
        )

    runs = [parse_review(p) for p in paths]
    result = GateResult(runs=runs)
    failures: List[str] = []

    result.complete = all(r.reviewed for r in runs)
    for r in runs:
        if not r.reviewed:
            failures.append(f"{r.run_id}: review.md has not been filled in by the owner")

    # C10.1 — volume band, per run
    volume_ok = True
    for r in runs:
        n = r.opportunities_presented
        if n is None or not (VOLUME_MIN <= n <= VOLUME_MAX):
            volume_ok = False
            failures.append(
                f"{r.run_id}: volume {n} outside the C10.1 band {VOLUME_MIN}–{VOLUME_MAX}"
            )
    result.c10_1_volume = volume_ok

    # C10.5 — relevance ratio ≥ 0.70, per run
    relevance_ok = result.complete
    for r in runs:
        if r.relevant_ratio is None:
            relevance_ok = False
            if r.reviewed:
                failures.append(
                    f"{r.run_id}: reviewed but relevant_ratio could not be computed "
                    f"(fill opportunities_relevant_count / relevant_ratio, or the "
                    f"decision table, and opportunities_presented)"
                )
            continue
        if r.relevant_ratio < RELEVANCE_THRESHOLD:
            relevance_ok = False
            failures.append(
                f"{r.run_id}: relevant_ratio {r.relevant_ratio:.2f} below the "
                f"C10.5 threshold {RELEVANCE_THRESHOLD:.2f}"
            )
    result.c10_5_relevance = relevance_ok

    # C10.6 — at least one advanced opportunity in the window
    advanced = [r.run_id for r in runs if r.advanced_opportunity_id]
    result.c10_6_advanced = bool(advanced)
    if not advanced:
        failures.append(
            "no run in the window advanced an opportunity to the next stage (C10.6)"
        )

    result.failures = failures
    result.passed = (
        result.complete
        and result.c10_1_volume
        and result.c10_5_relevance
        and result.c10_6_advanced
    )
    return result
