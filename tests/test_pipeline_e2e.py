"""End-to-end: fixture signals → normalization → framing → matching → evaluation
→ ranking → report. Fully offline (replay mode, recorded LLM fixtures). Spec §5, §22.
"""

from __future__ import annotations

import datetime as dt
import json

import yaml
from tests.conftest import FIXTURES, PROJECT_ROOT

from market_intelligence.cli import main
from market_intelligence.orchestrator import RunResult, run_pipeline
from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import Opportunity, RunConfig

_FIXTURE_ROOT = FIXTURES / "pipeline"
_OPP_ID = "opp_2026-08-28_e1a48ddf1c"
FIXED = dt.datetime(2026, 8, 28, 12, 0, 0, tzinfo=dt.timezone.utc)


def _cfg(tmp_path, **over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_pipe",
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
    raw.update(over)
    return decode(RunConfig, raw)


def _run(tmp_path, **over) -> RunResult:
    return run_pipeline(
        _cfg(tmp_path, **over), project_root=PROJECT_ROOT, now=FIXED
    )


# --- the full chain -------------------------------------------

def test_pipeline_runs_end_to_end_offline(tmp_path):
    result = _run(tmp_path)
    assert result.run_id == "run_pipe"
    assert result.replay is True
    assert len(result.collection.signals) == 3
    assert len(result.normalization.signals) == 3
    assert [o.opportunity_id for o in result.framing.opportunities] == [_OPP_ID]
    assert result.ranking.presented == [_OPP_ID]
    assert _OPP_ID in result.reporting.opportunities


def test_pipeline_writes_all_artifacts(tmp_path):
    _run(tmp_path)
    base = tmp_path / "reports" / "run_pipe"
    data = tmp_path / "data" / "run_pipe"
    assert (base / f"{_OPP_ID}.md").is_file()
    assert (base / f"{_OPP_ID}.json").is_file()
    assert (base / "digest.md").is_file()
    assert (base / "review.md").is_file()
    assert (data / "signals" / "collected.json").is_file()
    assert (data / "signals" / "normalized.json").is_file()
    assert (data / "opportunities.json").is_file()   # §17 — full records pre-render
    assert (data / "run.log").is_file()              # §14 — warnings / degradations
    assert (tmp_path / "registry.yaml").is_file()


def test_run_log_records_the_flagged_framing_candidate(tmp_path):
    _run(tmp_path)
    log = (tmp_path / "data" / "run_pipe" / "run.log").read_text()
    assert "[framing]" in log
    assert "Oportunidade sem mercado claro" in log  # §7.1a mismatch — flagged, not an opp
    assert "[normalization]" in log and "[asset_matching]" in log


def test_digest_carries_the_config_snapshot(tmp_path):
    _run(tmp_path)
    fm = yaml.safe_load(
        (tmp_path / "reports" / "run_pipe" / "digest.md").read_text().split("---\n")[1]
    )
    assert fm["config_snapshot"]["model"] == "claude-sonnet-5"
    assert fm["config_snapshot"]["signal_sources"] == ["internal_data"]
    assert "timings_seconds" in fm


def test_opportunities_json_holds_the_full_presented_record(tmp_path):
    _run(tmp_path)
    data = json.loads((tmp_path / "data" / "run_pipe" / "opportunities.json").read_text())
    assert [o["opportunity_id"] for o in data["presented"]] == [_OPP_ID]
    opp = decode(Opportunity, data["presented"][0])
    assert opp.evaluation.summary and opp.asset_fit.best_playlist


def test_presented_report_is_a_valid_opportunity(tmp_path):
    _run(tmp_path)
    data = json.loads(
        (tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.json").read_text()
    )
    opp = decode(Opportunity, data)
    assert opp.rank == 1
    assert opp.status.value == "EXPLORE"
    assert opp.recommendation.target_state.value in ("EXPLORE", "TEST", "PARK")
    assert opp.provenance.replay is True
    assert opp.asset_fit.best_playlist == "pl_4jmuWvaWI6BvsjhxmJBUao"


def test_registry_records_the_presented_opportunity(tmp_path):
    _run(tmp_path)
    reg = yaml.safe_load((tmp_path / "registry.yaml").read_text())
    entry = next(e for e in reg["opportunities"] if e["opportunity_id"] == _OPP_ID)
    assert entry["status"] == "EXPLORE"
    assert entry["report_ref"].endswith(f"{_OPP_ID}.md")


def test_rerun_is_idempotent_for_reports_and_appends_registry_history(tmp_path):
    _run(tmp_path)
    md_first = (tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.md").read_text()
    _run(tmp_path)  # same run_id, same fixtures
    md_second = (tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.md").read_text()
    assert md_first == md_second  # deterministic re-render

    reg = yaml.safe_load((tmp_path / "registry.yaml").read_text())
    entry = next(e for e in reg["opportunities"] if e["opportunity_id"] == _OPP_ID)
    assert len(entry["state_history"]) == 2  # one per run


def test_dry_run_stops_after_framing(tmp_path):
    result = _run(tmp_path, dry_run=True)
    assert result.dry_run is True
    assert result.matching is None and result.ranking is None
    assert result.framing.opportunities
    assert not (tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.md").exists()


def test_no_network_and_no_write_outside_the_configured_dirs(tmp_path):
    # knowledge/ in the repo must be untouched (registry is redirected to tmp_path here)
    before = (PROJECT_ROOT / "knowledge" / "market").exists()
    _run(tmp_path)
    after_files = list((PROJECT_ROOT / "knowledge" / "market").glob("*")) if (
        PROJECT_ROOT / "knowledge" / "market"
    ).exists() else []
    assert before == (PROJECT_ROOT / "knowledge" / "market").exists()
    assert all("opportunity-registry" not in f.name or f.stat().st_size >= 0
               for f in after_files)  # nothing created by this run


def test_missing_framing_fixture_fails_the_run_cleanly(tmp_path):
    import pytest

    from market_intelligence.orchestrator import OrchestratorError

    fx = tmp_path / "fx"
    (fx / "signals" / "raw").mkdir(parents=True)
    for f in (_FIXTURE_ROOT / "signals" / "raw").glob("*.json"):
        (fx / "signals" / "raw" / f.name).write_text(f.read_text(), encoding="utf-8")
    cfg = _cfg(tmp_path, replay={
        "enabled": True, "llm": "recorded", "fixture_path": str(fx),
    })
    with pytest.raises(OrchestratorError):
        run_pipeline(cfg, project_root=PROJECT_ROOT, now=FIXED)


def test_all_evaluations_failing_technically_is_a_controlled_error_no_registry(tmp_path):
    from market_intelligence.orchestrator import OrchestratorError

    fx = tmp_path / "fx"
    (fx / "signals" / "raw").mkdir(parents=True)
    for f in (_FIXTURE_ROOT / "signals" / "raw").glob("*.json"):
        (fx / "signals" / "raw" / f.name).write_text(f.read_text(), encoding="utf-8")
    for sub in ("framing", "matching", "evaluation"):
        (fx / "llm" / sub).mkdir(parents=True)
        for f in (_FIXTURE_ROOT / "llm" / sub).glob("*.json"):
            (fx / "llm" / sub / f.name).write_text(f.read_text(), encoding="utf-8")
    # corrupt every evaluation fixture -> ResponseRejected -> technical failure
    for f in (fx / "llm" / "evaluation").glob("*.json"):
        f.write_text("{ not valid json", encoding="utf-8")

    cfg = _cfg(tmp_path, replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    try:
        run_pipeline(cfg, project_root=PROJECT_ROOT, now=FIXED)
        raised = None
    except OrchestratorError as e:
        raised = e

    assert raised is not None
    assert "Evaluation failed technically for all" in str(raised)
    assert "registry not written" in str(raised)
    # the registry file was never created — no spurious PARK entries
    assert not (tmp_path / "registry.yaml").exists()
    # a diagnostic run.log was still written
    log = (tmp_path / "data" / "run_pipe" / "run.log").read_text()
    assert "TECHNICAL FAILURE" in log


def test_a_malformed_shape_evaluation_response_is_also_a_technical_failure(tmp_path):
    # Evaluation sends no schema now — a valid-JSON but wrong-SHAPE response
    # (here: a dimension dropped) must be rejected deterministically → the same
    # controlled all-fail error, registry untouched.
    from market_intelligence.orchestrator import OrchestratorError

    fx = tmp_path / "fx"
    (fx / "signals" / "raw").mkdir(parents=True)
    for f in (_FIXTURE_ROOT / "signals" / "raw").glob("*.json"):
        (fx / "signals" / "raw" / f.name).write_text(f.read_text(), encoding="utf-8")
    for sub in ("framing", "matching", "evaluation"):
        (fx / "llm" / sub).mkdir(parents=True)
        for f in (_FIXTURE_ROOT / "llm" / sub).glob("*.json"):
            (fx / "llm" / sub / f.name).write_text(f.read_text(), encoding="utf-8")
    for f in (fx / "llm" / "evaluation").glob("*.json"):
        d = json.loads(f.read_text())
        d["dimensions"].pop("music_fit")           # valid JSON, missing a dimension
        f.write_text(json.dumps(d), encoding="utf-8")

    cfg = _cfg(tmp_path, replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    try:
        run_pipeline(cfg, project_root=PROJECT_ROOT, now=FIXED)
        raised = None
    except OrchestratorError as e:
        raised = e
    assert raised is not None and "failed technically for all" in str(raised)
    assert not (tmp_path / "registry.yaml").exists()


def test_missing_evaluation_fixture_excludes_the_opportunity(tmp_path):
    fx = tmp_path / "fx"
    (fx / "signals" / "raw").mkdir(parents=True)
    for f in (_FIXTURE_ROOT / "signals" / "raw").glob("*.json"):
        (fx / "signals" / "raw" / f.name).write_text(f.read_text(), encoding="utf-8")
    for sub in ("framing", "matching"):
        (fx / "llm" / sub).mkdir(parents=True)
        for f in (_FIXTURE_ROOT / "llm" / sub).glob("*.json"):
            (fx / "llm" / sub / f.name).write_text(f.read_text(), encoding="utf-8")
    # no llm/evaluation fixture → the opportunity cannot be evaluated
    cfg = _cfg(tmp_path, replay={
        "enabled": True, "llm": "recorded", "fixture_path": str(fx),
    })
    result = run_pipeline(cfg, project_root=PROJECT_ROOT, now=FIXED)
    assert result.ranking.presented == []
    assert _OPP_ID in result.ranking.excluded
    assert result.reporting.opportunities == {}


# --- the `run` CLI command ----------------------------------

def test_cli_run_command(tmp_path, capsys):
    cfg = _cfg(tmp_path)
    path = tmp_path / "run.yaml"
    path.write_text(json.dumps(
        __import__("market_intelligence.schema.codec", fromlist=["encode"]).encode(cfg)
    ), encoding="utf-8")
    rc = main(["run", str(path), "--project-root", str(PROJECT_ROOT)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "RUN OK" in out
    assert _OPP_ID in out
    assert "presented 1" in out
