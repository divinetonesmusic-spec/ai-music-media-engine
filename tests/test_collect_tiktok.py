"""TikTok Creative Center collector (spec §6.5, §6.7, §16, §22). No API / scraping / browser."""

from __future__ import annotations

import datetime as dt
import json
import shutil

import pytest
import yaml
from tests.conftest import FIXTURES

from market_intelligence.collect.base import (
    DEFAULT_COLLECTORS,
    SignalCollectionError,
    collect_signals,
)
from market_intelligence.collect.tiktok import TikTokCreativeCenterCollector
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import CaptureMethod, SourceType
from market_intelligence.schema.models import RunConfig
from market_intelligence.schema.validate import validate_signals

FIXED = dt.datetime(2026, 8, 28, 14, 3, 11, tzinfo=dt.timezone.utc)


def _cfg(tmp_path, **over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_2026-08-28_01",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p",
        "signal_sources": ["tiktok_creative_center"],
        "tiktok_capture_path": "inputs/tiktok.yaml",
        "paths": {"data_dir": "data"},
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _write_capture(tmp_path, records=None):
    dst = tmp_path / "inputs" / "tiktok.yaml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if records is None:
        shutil.copy(FIXTURES / "tiktok_capture.yaml", dst)
    else:
        dst.write_text(yaml.safe_dump(records), encoding="utf-8")
    return dst


def _run(tmp_path, cfg=None):
    return collect_signals(cfg or _cfg(tmp_path), project_root=tmp_path, now=lambda: FIXED)


def _raw_root(tmp_path, run_id="run_2026-08-28_01"):
    return tmp_path / "data" / run_id / "signals" / "raw"


# --- 1. valid capture -> valid Signals ---------------------------

def test_capture_becomes_valid_signals(tmp_path):
    _write_capture(tmp_path)
    result = _run(tmp_path)
    assert [o.ok for o in result.outcomes] == [True]
    assert len(result.signals) == 3
    assert validate_signals(result.signals, raw_root=_raw_root(tmp_path)) == []


# --- 2-5. source_type / capture_method / source / query_or_reference ---

def test_source_type_and_capture_method(tmp_path):
    _write_capture(tmp_path)
    s = _run(tmp_path).signals[0]
    assert s.source_type is SourceType.TIKTOK_CREATIVE_CENTER
    assert s.provenance.source_type is SourceType.TIKTOK_CREATIVE_CENTER
    assert s.provenance.capture_method is CaptureMethod.ANALYST_CAPTURE


def test_source_names_the_panel(tmp_path):
    _write_capture(tmp_path)
    sources = {s.source for s in _run(tmp_path).signals}
    assert sources == {
        "TikTok Creative Center — Hashtags",
        "TikTok Creative Center — Songs",
        "TikTok Creative Center — Trends",
    }


def test_query_or_reference_is_the_panel_filter(tmp_path):
    _write_capture(tmp_path)
    by_source = {s.source: s for s in _run(tmp_path).signals}
    assert by_source["TikTok Creative Center — Hashtags"].provenance.query_or_reference == (
        "Hashtags panel; region=Brazil; industry=All; period=Last 30 days"
    )
    # the third record uses `filter:` instead of `query_or_reference:`
    assert by_source["TikTok Creative Center — Trends"].provenance.query_or_reference == (
        "Trends overview; region=English-speaking; category=Music"
    )


# --- 6-9. observed_at / url ------------------------------------

def test_observed_at_is_preserved(tmp_path):
    _write_capture(tmp_path)
    hashtags = next(
        s for s in _run(tmp_path).signals if s.source.endswith("Hashtags")
    )
    assert hashtags.observed_at == "2026-08-24"
    assert hashtags.provenance.observed_at == "2026-08-24"


def test_url_is_preserved_when_present(tmp_path):
    _write_capture(tmp_path)
    hashtags = next(s for s in _run(tmp_path).signals if s.source.endswith("Hashtags"))
    assert hashtags.url == "https://ads.tiktok.com/business/creativecenter/hashtag/sonoprofundo/pt"
    assert hashtags.provenance.url == hashtags.url


def test_absent_url_is_not_invented(tmp_path):
    _write_capture(tmp_path)
    songs = next(s for s in _run(tmp_path).signals if s.source.endswith("Songs"))
    assert songs.url is None
    assert songs.provenance.url is None


def test_absent_observed_at_becomes_unknown(tmp_path):
    _write_capture(tmp_path)
    trends = next(s for s in _run(tmp_path).signals if s.source.endswith("Trends"))
    assert trends.observed_at == "UNKNOWN"
    assert trends.provenance.observed_at == "UNKNOWN"


# --- 10. metrics preserved unchanged --------------------------

def test_metrics_are_preserved_without_transformation(tmp_path):
    _write_capture(tmp_path)
    hashtags = next(s for s in _run(tmp_path).signals if s.source.endswith("Hashtags"))
    assert hashtags.metrics == {"posts": "18400", "trend_direction": "up"}
    others = [s for s in _run(tmp_path).signals if not s.source.endswith("Hashtags")]
    assert all(s.metrics is None for s in others)


# --- 11. raw capture (§6.7) ----------------------------------

def test_raw_capture_shape(tmp_path):
    _write_capture(tmp_path)
    _run(tmp_path)
    files = sorted(_raw_root(tmp_path).glob("*.json"))
    assert len(files) == 3
    cap = json.loads(files[0].read_text())
    assert cap["source_type"] == "tiktok_creative_center"
    assert cap["capture_method"] == "analyst_capture"
    assert cap["query_or_reference"].startswith("Hashtags panel;")
    assert cap["raw_content"]["evidence"].startswith("#sonoprofundo")


# --- 12. replay without network -----------------------------

def test_replay_rebuilds_from_raw_captures_only(tmp_path):
    _write_capture(tmp_path)
    _run(tmp_path)
    fixture_dir = tmp_path / "fixtures" / "run1"
    (fixture_dir / "signals" / "raw").mkdir(parents=True)
    for p in _raw_root(tmp_path).glob("*.json"):
        shutil.copy(p, fixture_dir / "signals" / "raw" / p.name)

    replay_root = tmp_path / "replay"
    replay_root.mkdir()
    cfg = _cfg(tmp_path, run_id="run_2026-08-29_01", tiktok_capture_path=None)
    cfg.replay.enabled = True
    cfg.replay.fixture_path = str(fixture_dir)

    result = collect_signals(cfg, project_root=replay_root, now=lambda: FIXED)
    assert result.replay is True
    assert len(result.signals) == 3
    assert validate_signals(
        result.signals, raw_root=_raw_root(replay_root, "run_2026-08-29_01")
    ) == []


# --- 13-14. error / degradation ----------------------------

def test_missing_capture_file_degrades(tmp_path):
    with pytest.raises(SignalCollectionError):
        _run(tmp_path)  # no file written


def test_path_not_set_degrades(tmp_path):
    with pytest.raises(SignalCollectionError):
        _run(tmp_path, cfg=_cfg(tmp_path, tiktok_capture_path=None))


def test_malformed_record_missing_panel_degrades(tmp_path):
    _write_capture(tmp_path, records=[
        {
            "market": "Brasil", "language": "pt", "signal_type": "hashtag",
            "evidence": "x", "context": "y", "confidence": "LOW",
        }
    ])
    with pytest.raises(SignalCollectionError):
        _run(tmp_path)


def test_malformed_observed_at_degrades(tmp_path):
    _write_capture(tmp_path, records=[
        {
            "panel": "Hashtags", "observed_at": "last week",
            "market": "Brasil", "language": "pt", "signal_type": "hashtag",
            "evidence": "x", "context": "y", "confidence": "LOW",
        }
    ])
    with pytest.raises(SignalCollectionError):
        _run(tmp_path)


def test_capture_file_that_is_not_a_list_degrades(tmp_path):
    dst = tmp_path / "inputs" / "tiktok.yaml"
    dst.parent.mkdir(parents=True)
    dst.write_text("just a string, not records\n", encoding="utf-8")
    with pytest.raises(SignalCollectionError):
        _run(tmp_path)


def test_mapping_with_records_key_is_accepted(tmp_path):
    _write_capture(tmp_path, records={"panel_meta": "ignored", "records": [
        {
            "panel": "Hashtags", "observed_at": "2026-08-24",
            "market": "Brasil", "language": "pt", "signal_type": "hashtag",
            "evidence": "e", "context": "c", "confidence": "LOW",
        }
    ]})
    assert len(_run(tmp_path).signals) == 1


# --- degrade-and-continue with another source --------------

def test_degrades_but_run_continues_with_another_source(tmp_path):
    from market_intelligence.collect.internal_data import InternalDataCollector

    (tmp_path / "inputs").mkdir()
    shutil.copy(FIXTURES / "internal_data_example.yaml", tmp_path / "inputs" / "internal.yaml")
    cfg = _cfg(
        tmp_path,
        signal_sources=["tiktok_creative_center", "internal_data"],
        tiktok_capture_path="inputs/missing.yaml",
        internal_data_path="inputs/internal.yaml",
    )
    result = collect_signals(
        cfg,
        project_root=tmp_path,
        collectors={
            SourceType.TIKTOK_CREATIVE_CENTER: TikTokCreativeCenterCollector(),
            SourceType.INTERNAL_DATA: InternalDataCollector(),
        },
        now=lambda: FIXED,
    )
    assert result.sources_used == ["internal_data"]
    assert [f["source"] for f in result.sources_failed] == ["tiktok_creative_center"]


# --- 15-16. integration + no automation ----------------------

def test_registered_in_default_collectors():
    import market_intelligence.collect  # noqa: F401

    assert SourceType.TIKTOK_CREATIVE_CENTER in DEFAULT_COLLECTORS
    assert isinstance(
        DEFAULT_COLLECTORS[SourceType.TIKTOK_CREATIVE_CENTER], TikTokCreativeCenterCollector
    )


def test_module_uses_no_network_or_browser_imports():
    src = (
        FIXTURES.parent.parent
        / "src" / "market_intelligence" / "collect" / "tiktok.py"
    ).read_text()
    for banned in (
        "import urllib", "import http", "import requests", "import httpx",
        "playwright", "selenium", "anthropic", "webdriver", "socket",
    ):
        assert banned not in src, f"tiktok.py must not use {banned!r}"
