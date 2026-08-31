"""CLI surface — argument wiring and operator-facing output. No network."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from tests.conftest import FIXTURES, PROJECT_ROOT

from market_intelligence.cli import main

_FIXTURE_ROOT = FIXTURES / "pipeline"
_OPP_ID = "opp_2026-08-28_e1a48ddf1c"
FIXED = dt.datetime(2026, 8, 28, 12, 0, 0, tzinfo=dt.timezone.utc)


def _pipeline_cfg(tmp_path) -> Path:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_cli",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["internal_data"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(_FIXTURE_ROOT)},
        "paths": {
            "reports_dir": str(tmp_path / "reports"),
            "data_dir": str(tmp_path / "data"),
            "registry_path": str(tmp_path / "registry.yaml"),
        },
    }
    p = tmp_path / "run.yaml"
    p.write_text(json.dumps(raw), encoding="utf-8")
    return p


# --- gate command -------------------------------------------------


def _review(dirp: Path, run_id, presented, rel_count, ratio, advanced=None):
    d = dirp / run_id
    d.mkdir(parents=True, exist_ok=True)
    fm = [
        "---",
        f"run_id: {run_id}",
        'review_date: "2026-09-01"',
        "reviewer: Owner",
        f"opportunities_presented: {presented}",
        f"opportunities_relevant_count: {rel_count}",
        f"relevant_ratio: {ratio}",
        f"advanced_opportunity_id: {advanced or 'null'}",
        "---",
        f"# Run Review — {run_id}",
    ]
    (d / "review.md").write_text("\n".join(fm) + "\n", encoding="utf-8")


def test_gate_command_reports_pass(tmp_path, capsys):
    reports = tmp_path / "reports"
    _review(reports, "run_1", 8, 6, 0.75, advanced="opp_a")
    _review(reports, "run_2", 7, 6, 0.86)
    _review(reports, "run_3", 9, 7, 0.78)
    rc = main(["gate", "--reports-dir", str(reports)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "GATE PASS" in out
    assert "C10.1" in out and "C10.5" in out and "C10.6" in out


def test_gate_command_reports_fail_with_reasons(tmp_path, capsys):
    reports = tmp_path / "reports"
    _review(reports, "run_1", 3, 3, 1.0, advanced="opp_a")   # below volume band
    _review(reports, "run_2", 7, 3, 0.43)                    # below relevance
    _review(reports, "run_3", 9, 7, 0.78)
    rc = main(["gate", "--reports-dir", str(reports)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "GATE FAIL" in out
    assert "volume" in out.lower()


def test_gate_command_accepts_explicit_review_paths(tmp_path, capsys):
    reports = tmp_path / "reports"
    for i in range(1, 4):
        _review(reports, f"run_{i}", 8, 6, 0.75, advanced=("opp_a" if i == 1 else None))
    paths = [str(reports / f"run_{i}" / "review.md") for i in range(1, 4)]
    rc = main(["gate", *paths])
    out = capsys.readouterr().out
    assert rc == 0
    assert "GATE PASS" in out


# --- run command surfaces a technical failure ----------------------


def test_run_command_surfaces_a_technical_failure(tmp_path, capsys):
    # corrupt the evaluation fixture -> the opportunity is a technical failure,
    # not a business exclusion. The operator must see that distinction.
    fx = tmp_path / "fx"
    (fx / "signals" / "raw").mkdir(parents=True)
    for f in (_FIXTURE_ROOT / "signals" / "raw").glob("*.json"):
        (fx / "signals" / "raw" / f.name).write_text(f.read_text(), encoding="utf-8")
    for sub in ("framing", "matching"):
        (fx / "llm" / sub).mkdir(parents=True)
        for f in (_FIXTURE_ROOT / "llm" / sub).glob("*.json"):
            (fx / "llm" / sub / f.name).write_text(f.read_text(), encoding="utf-8")
    (fx / "llm" / "evaluation").mkdir(parents=True)
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        "{ not valid json", encoding="utf-8"
    )
    raw = {
        "schema_version": "1.0.0", "run_id": "run_cli_tf", "run_date": "2026-08-28",
        "model": "claude-sonnet-5", "prompt_version": "p1",
        "signal_sources": ["internal_data"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(fx)},
        "paths": {
            "reports_dir": str(tmp_path / "reports"),
            "data_dir": str(tmp_path / "data"),
            "registry_path": str(tmp_path / "registry.yaml"),
        },
    }
    p = tmp_path / "tf.yaml"
    p.write_text(json.dumps(raw), encoding="utf-8")

    rc = main(["run", str(p), "--project-root", str(PROJECT_ROOT)])
    out = capsys.readouterr().out
    # every opportunity failed technically -> controlled non-zero, and the word
    # "technical" must appear so the operator does not read it as a business call
    assert rc == 1
    assert "technical" in out.lower()


def test_run_command_shows_where_the_artifacts_landed(tmp_path, capsys):
    rc = main(["run", str(_pipeline_cfg(tmp_path)), "--project-root", str(PROJECT_ROOT)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "RUN OK" in out
    assert "reports" in out and "run_cli" in out   # a path hint to the run's output
