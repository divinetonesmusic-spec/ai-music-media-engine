"""YouTube Data API collector (spec §6.5, §6.7, §16, §22). No network in any test."""

from __future__ import annotations

import datetime as dt
import json
import shutil

import pytest
from tests.conftest import load_fixture

from market_intelligence.collect.base import (
    DEFAULT_COLLECTORS,
    SignalCollectionError,
    collect_signals,
)
from market_intelligence.collect.youtube import (
    YouTubeClient,
    YouTubeCollector,
    YouTubeDataApiClient,
    _redact,
    _rfc3339_to_date,
)
from market_intelligence.schema.codec import decode
from market_intelligence.schema.enums import CaptureMethod, SourceType
from market_intelligence.schema.models import RunConfig
from market_intelligence.schema.validate import validate_signals

FIXED = dt.datetime(2026, 8, 28, 14, 3, 11, tzinfo=dt.timezone.utc)


class FakeYouTubeClient(YouTubeClient):
    def __init__(self, search_resp, videos_resp=None):
        self.search_resp = search_resp
        self.videos_resp = videos_resp if videos_resp is not None else {"items": []}
        self.search_calls = []
        self.videos_calls = []

    def search(self, *, query, max_results, order, region_code=None, relevance_language=None):
        self.search_calls.append(
            dict(query=query, max_results=max_results, order=order,
                 region_code=region_code, relevance_language=relevance_language)
        )
        return self.search_resp

    def videos(self, *, video_ids):
        self.videos_calls.append(list(video_ids))
        return self.videos_resp


class RaisingYouTubeClient(YouTubeClient):
    def __init__(self, where="search"):
        self.where = where

    def search(self, **kw):
        if self.where == "search":
            raise SignalCollectionError  # any exception; base wraps CollectorError only
        return load_fixture("youtube_search_list.json")

    def videos(self, **kw):
        from market_intelligence.collect.base import CollectorError

        raise CollectorError("simulated videos.list outage")


def _default_client():
    return FakeYouTubeClient(
        load_fixture("youtube_search_list.json"), load_fixture("youtube_videos_list.json")
    )


def _cfg(**scope_over) -> RunConfig:
    scope = {"languages": ["es"], "queries": ["frecuencia 528 hz dormir"]}
    scope.update(scope_over)
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_2026-08-28_01",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p",
        "signal_sources": ["youtube"],
        "scope": scope,
        "paths": {"data_dir": "data"},
    }
    return decode(RunConfig, raw)


def _run(tmp_path, client, cfg=None):
    return collect_signals(
        cfg or _cfg(),
        project_root=tmp_path,
        collectors={SourceType.YOUTUBE: YouTubeCollector(client=client)},
        now=lambda: FIXED,
    )


def _raw_root(tmp_path, run_id="run_2026-08-28_01"):
    return tmp_path / "data" / run_id / "signals" / "raw"


# --- 1. search.list -> valid Signals -----------------------------

def test_search_list_becomes_valid_signals(tmp_path):
    result = _run(tmp_path, _default_client())
    assert [o.ok for o in result.outcomes] == [True]
    assert len(result.signals) == 3  # 4 items, 1 has no title -> skipped
    assert validate_signals(result.signals, raw_root=_raw_root(tmp_path)) == []
    assert any("watch" in s.url for s in result.signals)
    assert any("/channel/" in s.url for s in result.signals)
    assert any("/playlist" in s.url for s in result.signals)


# --- 2. videos.list enrichment ---------------------------------

def test_videos_list_enriches_the_video_result_with_statistics(tmp_path):
    signals = _run(tmp_path, _default_client()).signals
    video = next(s for s in signals if "watch?v=" in s.url)
    assert video.metrics == {
        "view_count": "184213",
        "like_count": "5120",
        "comment_count": "212",
        "favorite_count": "0",
    }
    non_video = [s for s in signals if "watch?v=" not in s.url]
    assert all(s.metrics is None for s in non_video)


def test_videos_list_failure_is_best_effort(tmp_path):
    signals = _run(tmp_path, RaisingYouTubeClient(where="videos")).signals
    assert len(signals) == 3
    assert all(s.metrics is None for s in signals)  # statistics unavailable, not an error


# --- 3-5. request params recorded --------------------------------

def test_query_is_recorded_in_provenance(tmp_path):
    s = _run(tmp_path, _default_client()).signals[0]
    assert s.provenance.query_or_reference.startswith("search.list?")
    assert "q=frecuencia 528 hz dormir" in s.provenance.query_or_reference


def test_region_code_recorded_when_configured(tmp_path):
    client = _default_client()
    _run(tmp_path, client, cfg=_cfg(youtube_region_code="ES"))
    assert client.search_calls[0]["region_code"] == "ES"
    s = _run(tmp_path, _default_client(), cfg=_cfg(youtube_region_code="ES")).signals[0]
    assert "regionCode=ES" in s.provenance.query_or_reference


def test_relevance_language_recorded_for_a_single_language_scope(tmp_path):
    client = _default_client()
    s = _run(tmp_path, client).signals[0]
    assert client.search_calls[0]["relevance_language"] == "es"
    assert "relevanceLanguage=es" in s.provenance.query_or_reference
    assert s.language == "es"
    assert s.market == "Mercados hispanohablantes"


def test_multi_language_scope_omits_relevance_language(tmp_path):
    client = _default_client()
    _run(tmp_path, client, cfg=_cfg(languages=["pt", "es", "en"]))
    assert client.search_calls[0]["relevance_language"] is None
    s = _run(tmp_path, _default_client(), cfg=_cfg(languages=["pt", "es", "en"])).signals[0]
    assert s.language == "UNKNOWN" and s.market == "UNKNOWN"


# --- 6-9. type / capture_method / source_version / provenance ---

def test_source_type_and_capture_method_and_version(tmp_path):
    s = _run(tmp_path, _default_client()).signals[0]
    assert s.source_type is SourceType.YOUTUBE
    assert s.provenance.source_type is SourceType.YOUTUBE
    assert s.provenance.capture_method is CaptureMethod.YOUTUBE_DATA_API
    assert s.provenance.source_version == "v3"


def test_provenance_source_and_mirrors(tmp_path):
    s = _run(tmp_path, _default_client()).signals[0]
    assert s.source == "YouTube Data API — search.list"
    assert s.provenance.source == s.source
    assert s.provenance.url == s.url
    assert s.provenance.observed_at == s.observed_at
    assert s.provenance.collected_at == "2026-08-28T14:03:11Z"


# --- 10. deterministic URLs ------------------------------------

def test_urls_are_derived_deterministically_from_real_ids(tmp_path):
    by_url = {s.url: s for s in _run(tmp_path, _default_client()).signals}
    assert "https://www.youtube.com/watch?v=vid_abc123" in by_url
    assert "https://www.youtube.com/channel/UC_relaxlab" in by_url
    assert "https://www.youtube.com/playlist?list=PL_deepsleep" in by_url


def test_item_with_unrecognised_kind_is_dropped(tmp_path):
    resp = load_fixture("youtube_search_list.json")
    resp["items"].append({
        "id": {"kind": "youtube#movie", "movieId": "m1"},
        "snippet": {"title": "A movie", "channelTitle": "X"},
    })
    client = FakeYouTubeClient(resp, load_fixture("youtube_videos_list.json"))
    signals = _run(tmp_path, client).signals
    assert len(signals) == 3  # the movie item has no derivable URL -> skipped
    assert all(s.url and s.url.startswith("https://www.youtube.com/") for s in signals)


# --- 11. missing publishedAt -> UNKNOWN ----------------------

def test_missing_published_at_yields_unknown_observed_at(tmp_path):
    playlist = next(
        s for s in _run(tmp_path, _default_client()).signals if "/playlist?" in s.url
    )
    assert playlist.observed_at == "UNKNOWN"
    assert playlist.provenance.observed_at == "UNKNOWN"


def test_rfc3339_to_date_never_guesses():
    assert _rfc3339_to_date("2026-03-01T09:30:00Z") == "2026-03-01"
    assert _rfc3339_to_date("2024-11-12T00:00:00.000Z") == "2024-11-12"
    assert _rfc3339_to_date(None) is None
    assert _rfc3339_to_date("") is None
    assert _rfc3339_to_date("last week") is None
    assert _rfc3339_to_date("2026-13-40T00:00:00Z") is None


# --- 12. raw capture (§6.7) + no secrets --------------------

def test_raw_capture_shape_and_no_key(tmp_path):
    _run(tmp_path, _default_client())
    files = sorted(_raw_root(tmp_path).glob("*.json"))
    assert len(files) == 3
    cap = json.loads(files[0].read_text())
    assert set(cap) >= {
        "signal_id", "source_type", "capture_method", "query_or_reference",
        "url", "captured_at", "raw_content",
    }
    assert cap["source_type"] == "youtube"
    assert cap["capture_method"] == "youtube_data_api"
    assert cap["query_or_reference"].startswith("search.list?")
    assert "search_item" in cap["raw_content"]
    for f in files:
        text = f.read_text()
        assert "key=" not in text and "YOUTUBE_API_KEY" not in text


# --- 13. API error degrades ---------------------------------

def test_search_api_error_degrades(tmp_path):
    from market_intelligence.collect.base import CollectorError

    class Boom(YouTubeClient):
        def search(self, **kw):
            raise CollectorError("youtube: API quota exceeded (quotaExceeded)")

        def videos(self, **kw):
            return {"items": []}

    with pytest.raises(SignalCollectionError):
        _run(tmp_path, Boom())


def test_api_error_degrades_but_run_continues_with_another_source(tmp_path):
    from tests.conftest import FIXTURES

    from market_intelligence.collect.base import CollectorError
    from market_intelligence.collect.internal_data import InternalDataCollector

    (tmp_path / "inputs").mkdir()
    shutil.copy(FIXTURES / "internal_data_example.yaml", tmp_path / "inputs" / "internal.yaml")

    class Boom(YouTubeClient):
        def search(self, **kw):
            raise CollectorError("youtube: API error HTTP 400 badRequest")

        def videos(self, **kw):
            return {"items": []}

    cfg = _cfg()
    cfg.signal_sources = list(cfg.signal_sources) + [SourceType.INTERNAL_DATA]
    cfg.internal_data_path = "inputs/internal.yaml"
    result = collect_signals(
        cfg,
        project_root=tmp_path,
        collectors={
            SourceType.YOUTUBE: YouTubeCollector(client=Boom()),
            SourceType.INTERNAL_DATA: InternalDataCollector(),
        },
        now=lambda: FIXED,
    )
    assert result.sources_used == ["internal_data"]
    assert [f["source"] for f in result.sources_failed] == ["youtube"]


# --- 14 & 16. missing API key ------------------------------

def test_missing_api_key_degrades(tmp_path, monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    with pytest.raises(SignalCollectionError):
        collect_signals(
            _cfg(),
            project_root=tmp_path,
            collectors={SourceType.YOUTUBE: YouTubeCollector(client=YouTubeDataApiClient())},
            now=lambda: FIXED,
        )


# --- 15 & 16. replay recorded, no network, no key --------

def test_replay_recorded_needs_no_network_and_no_key(tmp_path, monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)

    # 1) a real (faked) run produces raw captures
    _run(tmp_path, _default_client())
    fixture_dir = tmp_path / "fixtures" / "run1"
    (fixture_dir / "signals" / "raw").mkdir(parents=True)
    for p in _raw_root(tmp_path).glob("*.json"):
        shutil.copy(p, fixture_dir / "signals" / "raw" / p.name)

    # 2) replay in a fresh root with a client that must never be touched
    class Exploding(YouTubeClient):
        def search(self, **kw):
            raise AssertionError("no network in replay")

        def videos(self, **kw):
            raise AssertionError("no network in replay")

    replay_root = tmp_path / "replay"
    replay_root.mkdir()
    cfg = _cfg()
    cfg.run_id = "run_2026-08-29_01"
    cfg.replay.enabled = True
    cfg.replay.fixture_path = str(fixture_dir)

    result = collect_signals(
        cfg,
        project_root=replay_root,
        collectors={SourceType.YOUTUBE: YouTubeCollector(client=Exploding())},
        now=lambda: FIXED,
    )
    assert result.replay is True
    assert len(result.signals) == 3
    assert validate_signals(
        result.signals, raw_root=_raw_root(replay_root, "run_2026-08-29_01")
    ) == []


# --- 17. malformed items ----------------------------------

def test_malformed_search_item_is_skipped_not_turned_into_a_bad_signal(tmp_path):
    result = _run(tmp_path, _default_client())
    assert len(result.signals) == 3  # the title-less video item is skipped
    assert validate_signals(result.signals, raw_root=_raw_root(tmp_path)) == []


def test_empty_queries_degrades(tmp_path):
    with pytest.raises(SignalCollectionError):
        _run(tmp_path, _default_client(), cfg=_cfg(queries=[]))


# --- 18. DEFAULT_COLLECTORS + helpers ---------------------

def test_registered_in_default_collectors():
    import market_intelligence.collect  # noqa: F401

    assert SourceType.YOUTUBE in DEFAULT_COLLECTORS
    assert isinstance(DEFAULT_COLLECTORS[SourceType.YOUTUBE], YouTubeCollector)


def test_redact_strips_the_key_from_any_url():
    assert _redact("GET https://x/y?part=snippet&key=AIzaSyABC123&q=z") == (
        "GET https://x/y?part=snippet&key=REDACTED&q=z"
    )
