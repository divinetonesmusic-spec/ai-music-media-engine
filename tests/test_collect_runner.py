"""Signal Collection entry point (spec §5, §6.7, §18, §22) + the `collect` CLI.

Stage 1 only — no Normalization, no network."""

from __future__ import annotations

import datetime as dt
import json
import shutil

import pytest
from tests.conftest import FIXTURES, PROJECT_ROOT, load_fixture

from market_intelligence.cli import main
from market_intelligence.collect.internal_data import InternalDataCollector
from market_intelligence.collect.runner import build_manifest, manifest_path, run_collection
from market_intelligence.config.loader import ConfigError, load_run_config
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import SourceType
from market_intelligence.schema.models import RunConfig
from market_intelligence.schema.validate import blocking, validate_run_config

FIXED = dt.datetime(2026, 8, 28, 14, 3, 11, tzinfo=dt.timezone.utc)


def _cfg(tmp_path, **over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_2026-08-28_01",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p",
        "signal_sources": ["internal_data"],
        "internal_data_path": "inputs/internal.yaml",
        "paths": {"data_dir": "data"},
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _write_internal(tmp_path):
    dst = tmp_path / "inputs" / "internal.yaml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "internal_data_example.yaml", dst)


def _manifest(tmp_path, run_id="run_2026-08-28_01") -> dict:
    return json.loads(
        (tmp_path / "data" / run_id / "signals" / "collected.json").read_text()
    )


# --- run_collection --------------------------------------------------

def test_run_collection_with_internal_data(tmp_path):
    _write_internal(tmp_path)
    result = run_collection(_cfg(tmp_path), project_root=tmp_path, now=lambda: FIXED)
    assert len(result.signals) == 2
    assert result.sources_used == ["internal_data"]
    assert result.sources_failed == []


def test_run_collection_with_multiple_sources(tmp_path):
    _write_internal(tmp_path)
    from market_intelligence.collect.web_search import WebSearchCollector, WebSearchResearch

    research = decode(WebSearchResearch, load_fixture("web_search_research.json"))

    class FakeWS:
        def research(self, **kw):
            return research

    # run_collection uses the default registry; patch it for this test only
    from market_intelligence.collect import base as _base

    saved = dict(_base.DEFAULT_COLLECTORS)
    _base.DEFAULT_COLLECTORS[SourceType.WEB_SEARCH] = WebSearchCollector(client=FakeWS())
    try:
        cfg = _cfg(tmp_path, signal_sources=["internal_data", "web_search"])
        result = run_collection(cfg, project_root=tmp_path, now=lambda: FIXED)
    finally:
        _base.DEFAULT_COLLECTORS.clear()
        _base.DEFAULT_COLLECTORS.update(saved)

    assert sorted(result.sources_used) == ["internal_data", "web_search"]
    assert len(result.signals) == 4  # 2 internal + 2 web_search (3 fixture findings dropped)


def test_disabled_or_unregistered_source_is_reported_not_crashed(tmp_path):
    _write_internal(tmp_path)
    from market_intelligence.collect import base as _base

    saved = dict(_base.DEFAULT_COLLECTORS)
    _base.DEFAULT_COLLECTORS.clear()
    _base.DEFAULT_COLLECTORS[SourceType.INTERNAL_DATA] = InternalDataCollector()
    try:
        cfg = _cfg(tmp_path, signal_sources=["youtube", "internal_data"])
        result = run_collection(cfg, project_root=tmp_path, now=lambda: FIXED)
    finally:
        _base.DEFAULT_COLLECTORS.clear()
        _base.DEFAULT_COLLECTORS.update(saved)

    assert result.sources_used == ["internal_data"]
    assert [f["source"] for f in result.sources_failed] == ["youtube"]
    assert "not implemented" in result.sources_failed[0]["reason"]


def test_all_sources_failing_propagates(tmp_path):
    from market_intelligence.collect.base import SignalCollectionError

    cfg = _cfg(tmp_path, signal_sources=["internal_data"])  # no capture file written
    with pytest.raises(SignalCollectionError):
        run_collection(cfg, project_root=tmp_path, now=lambda: FIXED)
    # no manifest on a hard failure
    assert not manifest_path(cfg, tmp_path).exists()


def test_config_failure_propagates_as_config_error(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        'schema_version: "1.0.0"\nrun_id: "has spaces"\nmodel: m\nprompt_version: p\n'
        'signal_sources: ["internal_data"]\ninternal_data_path: "x"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        run_collection(tmp_path / "bad.yaml", project_root=PROJECT_ROOT, now=lambda: FIXED)


# --- manifest ------------------------------------------------------

def test_manifest_written_and_references_the_signals(tmp_path):
    _write_internal(tmp_path)
    result = run_collection(_cfg(tmp_path), project_root=tmp_path, now=lambda: FIXED)

    m = _manifest(tmp_path)
    assert m["schema_version"] == "1.0.0"
    assert m["run_id"] == "run_2026-08-28_01"
    assert m["replay"] is False
    assert m["signal_count"] == 2
    assert m["sources_used"] == ["internal_data"]
    assert m["sources_failed"] == []
    assert m["signal_ids"] == sorted(s.signal_id for s in result.signals)
    assert [s["signal_id"] for s in m["signals"]] == m["signal_ids"]
    # every referenced signal has a raw capture on disk
    raw_dir = tmp_path / "data" / "run_2026-08-28_01" / "signals" / "raw"
    for sid in m["signal_ids"]:
        assert (raw_dir / f"{sid}.json").is_file()


def test_manifest_does_not_replace_raw_captures(tmp_path):
    _write_internal(tmp_path)
    run_collection(_cfg(tmp_path), project_root=tmp_path, now=lambda: FIXED)
    signals_dir = tmp_path / "data" / "run_2026-08-28_01" / "signals"
    assert (signals_dir / "collected.json").is_file()
    assert (signals_dir / "raw").is_dir()
    assert len(list((signals_dir / "raw").glob("*.json"))) == 2
    assert not (signals_dir / "normalized.json").exists()  # Normalization not run


# --- replay ------------------------------------------------------

def _replay_cfg(tmp_path):
    return _cfg(
        tmp_path,
        run_id="run_replay",
        signal_sources=["internal_data", "youtube"],
        internal_data_path=None,
        replay={
            "enabled": True,
            "fixture_path": str(FIXTURES / "replay" / "collect_demo"),
        },
    )


def test_run_collection_replay_offline(tmp_path):
    result = run_collection(_replay_cfg(tmp_path), project_root=tmp_path, now=lambda: FIXED)
    assert result.replay is True
    assert result.sources_used == ["internal_data"]
    assert [f["source"] for f in result.sources_failed] == ["youtube"]
    m = _manifest(tmp_path, "run_replay")
    assert m["replay"] is True
    assert m["signal_ids"] == ["sig_run_replay_demo_0001", "sig_run_replay_demo_0002"]


def test_replay_is_byte_reproducible(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    run_collection(_replay_cfg(a), project_root=a, now=lambda: FIXED)
    run_collection(_replay_cfg(b), project_root=b, now=lambda: FIXED)
    ma = (a / "data" / "run_replay" / "signals" / "collected.json").read_bytes()
    mb = (b / "data" / "run_replay" / "signals" / "collected.json").read_bytes()
    assert ma == mb


def test_live_run_is_deterministic_given_a_fixed_clock(tmp_path):
    _write_internal(tmp_path / "a")
    _write_internal(tmp_path / "b")
    ca = _cfg(tmp_path / "a")
    cb = _cfg(tmp_path / "b")
    run_collection(ca, project_root=tmp_path / "a", now=lambda: FIXED)
    run_collection(cb, project_root=tmp_path / "b", now=lambda: FIXED)
    assert build_manifest(
        run_collection(ca, project_root=tmp_path / "a", now=lambda: FIXED), ca
    ) == build_manifest(
        run_collection(cb, project_root=tmp_path / "b", now=lambda: FIXED), cb
    )


# --- CLI --------------------------------------------------------

def _write_cfg_file(tmp_path, cfg: RunConfig, name="run.yaml"):
    from market_intelligence.schema.codec import encode

    path = tmp_path / name
    path.write_text(json.dumps(encode(cfg)), encoding="utf-8")  # YAML loader accepts JSON
    return path


def test_cli_collect_success(tmp_path, capsys):
    _write_internal(tmp_path)
    cfg_path = _write_cfg_file(tmp_path, _cfg(tmp_path))
    rc = main(["collect", str(cfg_path), "--project-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "COLLECT OK" in out
    assert "Normalization not run" in out
    assert "sources_used:   ['internal_data']" in out
    assert (tmp_path / "data" / "run_2026-08-28_01" / "signals" / "collected.json").is_file()


def test_cli_collect_reports_degraded_sources(tmp_path, capsys):
    cfg_path = _write_cfg_file(tmp_path, _replay_cfg(tmp_path))
    rc = main(["collect", str(cfg_path), "--project-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "sources_failed:" in out
    assert "youtube:" in out


def test_cli_collect_config_failure_returns_1(tmp_path, capsys):
    (tmp_path / "bad.yaml").write_text(
        'schema_version: "1.0.0"\nrun_id: "bad id!"\nmodel: m\nprompt_version: p\n'
        'signal_sources: ["internal_data"]\ninternal_data_path: "x"\n',
        encoding="utf-8",
    )
    rc = main(["collect", str(tmp_path / "bad.yaml"), "--project-root", str(PROJECT_ROOT)])
    assert rc == 1
    assert "COLLECT FAILED" in capsys.readouterr().out


def test_cli_still_runs_preflight(capsys):
    rc = main(["preflight", "config/run.example.yaml", "--project-root", str(PROJECT_ROOT)])
    assert rc == 0
    assert "PREFLIGHT OK" in capsys.readouterr().out


# --- the committed example stays valid -----------------------

def test_run_replay_example_config_is_valid():
    cfg = load_run_config("config/run.replay.example.yaml", project_root=PROJECT_ROOT)
    assert blocking(validate_run_config(cfg, project_root=PROJECT_ROOT)) == []
    assert cfg.replay.enabled is True
