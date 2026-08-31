"""Registry Updater — spec §17, §5, §13, I2. Deterministic, append-only, no network."""

from __future__ import annotations

from pathlib import Path

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


def test_a_technical_failure_is_never_written_to_the_registry(tmp_path):
    from market_intelligence.ranking import TECHNICAL_FAILURE, RankedOpportunity, RankingResult

    fo = frame_signals(
        [decode(Signal, d) for d in load_fixture("pipeline/signals.json")],
        knowledge=load_knowledge(RunPaths(), project_root=PROJECT_ROOT),
        config=_cfg(), project_root=PROJECT_ROOT,
    ).opportunities[0]

    ranking = RankingResult(
        ordered=[RankedOpportunity(
            fo.opportunity_id, TECHNICAL_FAILURE, None, None,
            technical_failure_reason="evaluation API call failed: 400 grammar too large",
        )],
        technical_failures=[fo.opportunity_id],
    )
    reg = update_registry(
        {}, ranking, {fo.opportunity_id: fo},
        run_config=_cfg(), project_root=tmp_path, generated_at="2026-08-28T12:00:00Z",
    )

    assert reg.added == [] and reg.updated == [] and reg.total == 0
    assert not (tmp_path / "knowledge" / "market" / "opportunity-registry.yaml").exists()


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


# --- atomic write (LOW-2) -----------------------------------------

def test_registry_write_goes_through_the_shared_atomic_helper(tmp_path, monkeypatch):
    import market_intelligence.io_utils as io_utils
    import market_intelligence.registry as registry_mod

    # the updater must use the project's atomic writer, not a bare write_text
    assert registry_mod.write_text is io_utils.write_text

    seen = {}
    real_atomic = io_utils._atomic_write

    def spy(path, content):
        seen["path"] = Path(path)
        seen["content"] = content
        return real_atomic(path, content)

    monkeypatch.setattr(io_utils, "_atomic_write", spy)

    reg, _ = _run(tmp_path, _cfg())
    assert seen["path"] == tmp_path / "knowledge" / "market" / "opportunity-registry.yaml"
    # atomic write leaves no temp file behind, and the content is valid registry YAML
    assert list((tmp_path / "knowledge" / "market").glob(".*tmp*")) == []
    parsed = yaml.safe_load(seen["content"])
    assert parsed["schema_version"] == "1.0.0"
    assert any(e["opportunity_id"] == _OPP_ID for e in parsed["opportunities"])


def test_registry_format_is_byte_identical_to_a_plain_yaml_dump(tmp_path):
    # the atomic helper must not change the on-disk format (LOW-2 constraint)
    _run(tmp_path, _cfg())
    on_disk = (tmp_path / "knowledge" / "market" / "opportunity-registry.yaml").read_text()
    reparsed = yaml.safe_load(on_disk)
    expected = yaml.safe_dump(
        reparsed, sort_keys=False, allow_unicode=True, default_flow_style=False
    )
    assert on_disk == expected            # exactly one trailing newline, same key order


def test_append_only_holds_across_three_runs(tmp_path):
    for rid in ("run_a", "run_b", "run_c"):
        _run(tmp_path, _cfg(rid))
    entry = next(e for e in _registry(tmp_path)["opportunities"]
                 if e["opportunity_id"] == _OPP_ID)
    assert entry["created_at"] == "2026-08-28T00:00:00Z"   # never rewritten
    assert entry["first_run_id"] == "run_a"                # never rewritten
    assert entry["last_run_id"] == "run_c"
    assert len(entry["state_history"]) == 3                # one appended per run
    assert entry["state_history"][0]["at"] == "2026-08-28T12:00:00Z"
