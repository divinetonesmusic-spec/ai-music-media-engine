"""Internal Data collector (spec §6.4, §6.5) + the collect_signals orchestrator (§14, §22)."""

from __future__ import annotations

import datetime as dt
import json
import shutil

import pytest

from market_intelligence.collect.base import (
    CollectorError,
    SignalCollectionError,
    collect_signals,
    make_context,
)
from market_intelligence.collect.internal_data import InternalDataCollector
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import CaptureMethod, SourceType
from market_intelligence.schema.models import RunConfig, Signal
from market_intelligence.schema.validate import validate_signals

FIXED = dt.datetime(2026, 8, 28, 14, 3, 11, tzinfo=dt.timezone.utc)


def _config(tmp_path, **over):
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_2026-08-28_01",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "mi-v1-2026-08-28",
        "signal_sources": ["internal_data"],
        "internal_data_path": "inputs/internal.yaml",
        "paths": {"data_dir": "data"},
    }
    raw.update(over)
    cfg = decode(RunConfig, raw)
    return cfg


def _write_internal(tmp_path, src="internal_data_example.yaml"):
    from tests.conftest import FIXTURES

    dst = tmp_path / "inputs" / "internal.yaml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / src, dst)
    return dst


# --- collector unit ------------------------------------------------------

def test_records_become_valid_signals(tmp_path):
    _write_internal(tmp_path)
    cfg = _config(tmp_path)
    result = collect_signals(cfg, project_root=tmp_path, now=lambda: FIXED)

    assert [o.ok for o in result.outcomes] == [True]
    assert len(result.signals) == 2
    raw_root = tmp_path / "data" / "run_2026-08-28_01" / "signals" / "raw"
    assert validate_signals(result.signals, raw_root=raw_root) == []

    s0 = result.signals[0]
    assert isinstance(s0, Signal)
    assert s0.signal_id == "sig_run_2026-08-28_01_0001"
    assert s0.source_type is SourceType.INTERNAL_DATA
    assert s0.provenance.capture_method is CaptureMethod.INTERNAL_DATA
    assert s0.observed_at == "2026-08-20"
    assert s0.collected_at == "2026-08-28T14:03:11Z"
    assert s0.market == "Brasil" and s0.language == "pt"
    assert s0.raw_ref == "data/run_2026-08-28_01/signals/raw/sig_run_2026-08-28_01_0001.json"
    assert s0.metrics == {"saves_per_view_ratio": "0.04", "window_days": 30}
    # provenance mirrors (spec §6.1)
    assert s0.provenance.source == s0.source
    assert s0.provenance.observed_at == s0.observed_at


def test_raw_capture_written_per_signal_in_the_spec_6_7_shape(tmp_path):
    _write_internal(tmp_path)
    cfg = _config(tmp_path)
    collect_signals(cfg, project_root=tmp_path, now=lambda: FIXED)

    raw_dir = tmp_path / "data" / "run_2026-08-28_01" / "signals" / "raw"
    files = sorted(raw_dir.glob("*.json"))
    assert [f.name for f in files] == [
        "sig_run_2026-08-28_01_0001.json",
        "sig_run_2026-08-28_01_0002.json",
    ]
    cap0 = json.loads(files[0].read_text())
    assert cap0["source_type"] == "internal_data"
    assert cap0["capture_method"] == "internal_data"
    assert cap0["query_or_reference"] == "inputs/internal.yaml [record 0]"
    assert cap0["captured_at"] == "2026-08-28T14:03:11Z"
    assert cap0["raw_content"]["evidence"].startswith("Own page")


def test_second_record_optional_source_and_durability_hint(tmp_path):
    _write_internal(tmp_path)
    cfg = _config(tmp_path)
    signals = collect_signals(cfg, project_root=tmp_path, now=lambda: FIXED).signals
    assert signals[1].source == "Spotify for Artists — playlist analytics export"
    assert signals[1].durability_hint.value == "STRUCTURAL"


def test_missing_required_field_raises_collector_error(tmp_path):
    bad = tmp_path / "inputs" / "internal.yaml"
    bad.parent.mkdir(parents=True)
    bad.write_text(
        '- observed_at: "2026-08-20"\n  market: "Brasil"\n  language: "pt"\n'
        '  platform: "tiktok"\n  evidence: "no signal_type / context / confidence here"\n',
        encoding="utf-8",
    )
    with pytest.raises(SignalCollectionError):  # the only source fails -> hard fail
        collect_signals(_config(tmp_path), project_root=tmp_path, now=lambda: FIXED)


def test_missing_internal_data_file_degrades(tmp_path):
    # internal_data is configured but no file -> collector fails; it's the only source -> hard fail
    with pytest.raises(SignalCollectionError):
        collect_signals(_config(tmp_path), project_root=tmp_path, now=lambda: FIXED)


def test_internal_data_path_not_set_is_a_collector_error(tmp_path):
    cfg = _config(tmp_path, internal_data_path=None)
    ctx = make_context(cfg, project_root=tmp_path, now=lambda: FIXED)
    with pytest.raises(CollectorError):
        InternalDataCollector().live_records(ctx)


# --- orchestrator: degrade / hard-fail (§14) --------------------------

def test_a_source_with_no_registered_collector_is_reported_not_crashed(tmp_path):
    # All four V1 collectors are now built; this pins the "collector is None" branch
    # (a restricted `collectors=` registry, or a future source) — it must degrade, not crash.
    _write_internal(tmp_path)
    cfg = _config(tmp_path, signal_sources=["youtube", "internal_data"])
    result = collect_signals(
        cfg,
        project_root=tmp_path,
        collectors={SourceType.INTERNAL_DATA: InternalDataCollector()},
        now=lambda: FIXED,
    )

    assert result.sources_used == ["internal_data"]
    assert [f["source"] for f in result.sources_failed] == ["youtube"]
    assert "not implemented" in result.sources_failed[0]["reason"]
    assert len(result.signals) == 2


def test_all_sources_failing_raises(tmp_path):
    cfg = _config(tmp_path, signal_sources=["youtube", "tiktok_creative_center"])
    with pytest.raises(SignalCollectionError):
        # empty registry -> neither source has a collector -> every source fails
        collect_signals(cfg, project_root=tmp_path, collectors={}, now=lambda: FIXED)


# --- replay (§22) ----------------------------------------------------

def test_replay_rebuilds_signals_from_fixtures_without_reading_live_input(tmp_path):
    # 1) a real run produces raw captures
    _write_internal(tmp_path)
    first = collect_signals(_config(tmp_path), project_root=tmp_path, now=lambda: FIXED)
    fixture_dir = tmp_path / "fixtures" / "run1"
    (fixture_dir / "signals" / "raw").mkdir(parents=True)
    for p in (tmp_path / "data" / "run_2026-08-28_01" / "signals" / "raw").glob("*.json"):
        shutil.copy(p, fixture_dir / "signals" / "raw" / p.name)

    # 2) a replay run in a fresh root with NO live input file
    replay_root = tmp_path / "replay_root"
    replay_root.mkdir()
    cfg = _config(
        tmp_path,
        run_id="run_2026-08-29_01",
        internal_data_path=None,
        replay={"enabled": True, "fixture_path": str(fixture_dir)},
    )
    result = collect_signals(cfg, project_root=replay_root, now=lambda: FIXED)

    assert result.replay is True
    assert len(result.signals) == 2
    assert validate_signals(result.signals) == []
    # raw captures are copied into the replay run's own data dir (§6.3)
    replay_raw = replay_root / "data" / "run_2026-08-29_01" / "signals" / "raw"
    assert len(list(replay_raw.glob("*.json"))) == 2
    # the signal evidence is reproduced verbatim
    assert sorted(s.evidence for s in result.signals) == sorted(s.evidence for s in first.signals)


def test_replay_enabled_but_no_fixtures_is_an_error(tmp_path):
    cfg = _config(
        tmp_path,
        internal_data_path=None,
        replay={"enabled": True, "fixture_path": str(tmp_path / "nope")},
    )
    with pytest.raises(SignalCollectionError):
        collect_signals(cfg, project_root=tmp_path, now=lambda: FIXED)
