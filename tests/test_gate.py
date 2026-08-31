"""C10 3-run Definition-of-Done gate checker — spec §21, §21.1, §22 "Acceptance".

A deterministic checker reads the per-run ``reports/<run_id>/review.md`` files the
owner filled in and reports whether the 3-run C10 gate has been met. No network,
no model. Pure function over the review files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market_intelligence.gate import (
    GateError,
    check_gate,
    discover_reviews,
    parse_review,
)

# --- a review.md the owner has filled in --------------------------------


def _review_md(
    *,
    run_id: str,
    presented: int,
    relevant_count=None,
    relevant_ratio=None,
    advanced=None,
    rows: list[tuple[int, str, str, str]] | None = None,
) -> str:
    fm = [
        "---",
        f"run_id: {run_id}",
        'review_date: "2026-09-01"',
        "reviewer: Nicolas Alves",
        f"opportunities_presented: {presented}",
        f"opportunities_relevant_count: {relevant_count if relevant_count is not None else 'null'}",
        f"relevant_ratio: {relevant_ratio if relevant_ratio is not None else 'null'}",
        f"advanced_opportunity_id: {advanced or 'null'}",
        "---",
        "",
        f"# Run Review — {run_id}",
        "",
        "| rank | opportunity_id | title | owner_decision | note |",
        "|------|----------------|-------|----------------|------|",
    ]
    for rank, oid, title, decision in rows or []:
        fm.append(f"| {rank} | {oid} | {title} | {decision} | |")
    fm += ["", "## Notes", "ok"]
    return "\n".join(fm) + "\n"


def _write_run(tmp_path: Path, run_id: str, **kw) -> Path:
    d = tmp_path / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "review.md").write_text(_review_md(run_id=run_id, **kw), encoding="utf-8")
    return d / "review.md"


# --- parse_review ------------------------------------------------------


def test_parse_review_reads_front_matter(tmp_path):
    p = _write_run(tmp_path, "run_a", presented=8, relevant_count=6,
                   relevant_ratio=0.75, advanced="opp_x")
    r = parse_review(p)
    assert r.run_id == "run_a"
    assert r.opportunities_presented == 8
    assert r.relevant_count == 6
    assert r.relevant_ratio == pytest.approx(0.75)
    assert r.advanced_opportunity_id == "opp_x"


def test_parse_review_derives_relevant_count_from_the_decision_table(tmp_path):
    # owner filled the table but not the front-matter count
    rows = [
        (1, "opp_1", "A", "relevant"),
        (2, "opp_2", "B", "advance"),
        (3, "opp_3", "C", "not_relevant"),
    ]
    p = _write_run(tmp_path, "run_b", presented=3, rows=rows)
    r = parse_review(p)
    assert r.relevant_count == 2          # relevant + advance
    assert r.relevant_ratio == pytest.approx(2 / 3)
    assert r.advanced_opportunity_id == "opp_2"   # the row marked "advance"


def test_parse_review_front_matter_count_wins_over_the_table(tmp_path):
    rows = [(1, "opp_1", "A", "relevant")]
    p = _write_run(tmp_path, "run_c", presented=5, relevant_count=4,
                   relevant_ratio=0.8, rows=rows)
    r = parse_review(p)
    assert r.relevant_count == 4
    assert r.relevant_ratio == pytest.approx(0.8)


def test_parse_review_flags_an_unreviewed_file(tmp_path):
    p = _write_run(tmp_path, "run_d", presented=7)   # nothing filled in
    r = parse_review(p)
    assert r.reviewed is False


def test_parse_review_rejects_a_bad_owner_decision(tmp_path):
    rows = [(1, "opp_1", "A", "maybe")]
    p = _write_run(tmp_path, "run_e", presented=3, rows=rows)
    with pytest.raises(GateError):
        parse_review(p)


# --- check_gate ------------------------------------------------------


def _three_good(tmp_path):
    return [
        _write_run(tmp_path, "run_1", presented=8, relevant_count=6,
                   relevant_ratio=0.75, advanced="opp_a"),
        _write_run(tmp_path, "run_2", presented=6, relevant_count=5,
                   relevant_ratio=0.83),
        _write_run(tmp_path, "run_3", presented=9, relevant_count=7,
                   relevant_ratio=0.78),
    ]


def test_gate_passes_when_all_three_criteria_hold(tmp_path):
    result = check_gate(_three_good(tmp_path))
    assert result.passed is True
    assert result.c10_1_volume is True         # 5..10 presented each run
    assert result.c10_5_relevance is True      # ratio >= 0.70 each run
    assert result.c10_6_advanced is True       # >=1 advanced in the window
    assert len(result.runs) == 3


def test_gate_fails_when_a_run_is_below_the_volume_band(tmp_path):
    paths = _three_good(tmp_path)
    _write_run(tmp_path, "run_2", presented=3, relevant_count=3, relevant_ratio=1.0)
    result = check_gate(paths)
    assert result.passed is False
    assert result.c10_1_volume is False
    assert any("run_2" in r and "volume" in r.lower() for r in result.failures)


def test_gate_fails_when_a_run_misses_the_relevance_threshold(tmp_path):
    paths = _three_good(tmp_path)
    _write_run(tmp_path, "run_3", presented=9, relevant_count=5, relevant_ratio=0.55)
    result = check_gate(paths)
    assert result.passed is False
    assert result.c10_5_relevance is False


def test_gate_fails_when_no_run_advanced_an_opportunity(tmp_path):
    paths = [
        _write_run(tmp_path, "run_1", presented=8, relevant_count=6, relevant_ratio=0.75),
        _write_run(tmp_path, "run_2", presented=6, relevant_count=5, relevant_ratio=0.83),
        _write_run(tmp_path, "run_3", presented=9, relevant_count=7, relevant_ratio=0.78),
    ]
    result = check_gate(paths)
    assert result.passed is False
    assert result.c10_6_advanced is False


def test_gate_is_incomplete_when_a_review_is_not_filled_in(tmp_path):
    paths = _three_good(tmp_path)
    _write_run(tmp_path, "run_3", presented=9)   # owner has not reviewed run_3
    result = check_gate(paths)
    assert result.passed is False
    assert result.complete is False
    assert any("run_3" in f for f in result.failures)


def test_gate_needs_exactly_three_runs(tmp_path):
    two = _three_good(tmp_path)[:2]
    with pytest.raises(GateError):
        check_gate(two)


# --- discover_reviews ------------------------------------------------


def test_discover_reviews_picks_the_three_most_recent_review_files(tmp_path):
    import os
    import time

    for i, rid in enumerate(["old", "run_1", "run_2", "run_3"]):
        d = tmp_path / rid
        d.mkdir()
        f = d / "review.md"
        f.write_text(_review_md(run_id=rid, presented=7), encoding="utf-8")
        t = time.time() + i
        os.utime(f, (t, t))

    found = discover_reviews(tmp_path)
    assert [p.parent.name for p in found] == ["run_1", "run_2", "run_3"]


def test_discover_reviews_errors_when_fewer_than_three_exist(tmp_path):
    (tmp_path / "run_1").mkdir()
    (tmp_path / "run_1" / "review.md").write_text(
        _review_md(run_id="run_1", presented=7), encoding="utf-8"
    )
    with pytest.raises(GateError):
        discover_reviews(tmp_path)
