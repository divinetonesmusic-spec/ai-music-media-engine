"""Registry Updater — spec §17, §5, §13, I2. Deterministic, append-only, no network."""

from __future__ import annotations

import yaml
from tests.conftest import FIXTURES, PROJECT_ROOT, load_fixture

from market_intelligence.config.loader import load_ranking_config
from market_intelligence.evaluation import evaluate_opportunities
from market_intelligence.framing import frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.matching import match_assets
from market_intelligence.ranking import rank_opportunities
from market_intelligence.registry import RegistryError, update_registry
from market_intelligence.reporting import generate_reports
from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import RunConfig, RunPaths, Signal

_FIXTURE_ROOT = FIXTURES / "pipeline"
_OPP_ID = "opp_2026-08-28_e1a48ddf1c"
RANKING = load_ranking_config(project_root=PROJECT_ROOT)


def _cfg(run_id="run_pipe") -> RunConfig:
    return decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": run_id, "run_date": "2026-08-28",
        "model": "claude-sonnet-5", "prompt_version": "p1", "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(_FIXTURE_ROOT)},
    })


def _run(tmp_path, cfg, replay=False):
    kn = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)
    signals = [decode(Signal, d) for d in load_fixture("pipeline/signals.json")]
    framed = frame_signals(
        signals, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).opportunities
    matches = match_assets(
        framed, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).matches
    bundles = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles
    ranking = rank_opportunities(
        framed, bundles, ranking_config=RANKING, max_presented=cfg.max_opportunities_presented
    )
    reports = generate_reports(
        ranking, {o.opportunity_id: o for o in framed}, matches, bundles,
        signals=signals, knowledge=kn, run_config=cfg, project_root=tmp_path,
        generated_at="2026-08-28T12:00:00Z", replay=True,
    )
    reg = update_registry(
        reports.opportunities, ranking, {o.opportunity_id: o for o in framed},
        run_config=cfg, project_root=tmp_path, generated_at="2026-08-28T12:00:00Z",
        replay=replay,
    )
    return reg, ranking


def _registry(tmp_path):
    path = tmp_path / "knowledge" / "market" / "opportunity-registry.yaml"
    return yaml.safe_load(path.read_text())


def test_first_run_appends_a_new_entry(tmp_path):
    reg, _ = _run(tmp_path, _cfg())
    assert _OPP_ID in reg.added
    data = _registry(tmp_path)
    entry = next(e for e in data["opportunities"] if e["opportunity_id"] == _OPP_ID)
    assert entry["status"] == "EXPLORE"
    assert entry["created_at"] == "2026-08-28T00:00:00Z"
    assert entry["report_ref"].endswith(f"{_OPP_ID}.md")
    assert len(entry["state_history"]) == 1


def test_second_run_appends_history_and_never_rewrites_the_first(tmp_path):
    _run(tmp_path, _cfg("run_pipe"))
    first = _registry(tmp_path)
    first_entry = next(e for e in first["opportunities"] if e["opportunity_id"] == _OPP_ID)
    first_history = list(first_entry["state_history"])

    reg2, _ = _run(tmp_path, _cfg("run_pipe_2"))
    assert _OPP_ID in reg2.updated
    second = _registry(tmp_path)
    entry = next(e for e in second["opportunities"] if e["opportunity_id"] == _OPP_ID)
    assert entry["created_at"] == first_entry["created_at"]      # unchanged
    assert entry["first_run_id"] == "run_pipe"                   # unchanged
    assert entry["last_run_id"] == "run_pipe_2"                  # updated
    assert entry["state_history"][: len(first_history)] == first_history  # prior history intact
    assert len(entry["state_history"]) == len(first_history) + 1


def test_registry_is_the_only_knowledge_file_written(tmp_path):
    _run(tmp_path, _cfg())
    written = {p.relative_to(tmp_path).as_posix()
              for p in (tmp_path / "knowledge").rglob("*") if p.is_file()}
    assert written == {"knowledge/market/opportunity-registry.yaml"}


def test_existing_registry_entries_are_preserved_in_place_and_new_ones_appended(tmp_path):
    path = tmp_path / "knowledge" / "market" / "opportunity-registry.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    prior = {
        "opportunity_id": "opp_2026-01-01_deadbeef00",
        "status": "PARK", "created_at": "2026-01-01T00:00:00Z",
        "first_run_id": "run_old", "last_run_id": "run_old",
        "report_ref": None,
        "state_history": [{"to": "PARK", "at": "2026-01-01T00:00:00Z", "by": "system"}],
    }
    path.write_text(yaml.safe_dump({"schema_version": "1.0.0", "opportunities": [prior]}),
                    encoding="utf-8")

    _run(tmp_path, _cfg())
    entries = _registry(tmp_path)["opportunities"]
    assert entries[0] == prior           # untouched, still first (localized git diff, §17)
    assert entries[-1]["opportunity_id"] == _OPP_ID   # new one appended at the end


def test_replay_run_marks_registry_entries_as_replay_origin(tmp_path):
    _run(tmp_path, _cfg(), replay=True)
    entry = next(e for e in _registry(tmp_path)["opportunities"]
                 if e["opportunity_id"] == _OPP_ID)
    assert entry["replay_origin"] is True
    assert entry["state_history"][0]["replay"] is True


def test_malformed_registry_raises_rather_than_clobbering(tmp_path):
    import pytest

    path = tmp_path / "knowledge" / "market" / "opportunity-registry.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("opportunities: 42\n", encoding="utf-8")
    with pytest.raises(RegistryError):
        _run(tmp_path, _cfg())
