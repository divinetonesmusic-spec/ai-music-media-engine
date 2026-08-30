"""YouTube Data API collector (spec §6.5 — ``youtube`` / ``youtube_data_api``).

Fully deterministic — no Claude. ``search.list`` finds videos/channels/playlists
for each configured query; ``videos.list`` enriches video results with public
statistics. Every ``Signal`` is built from real fields of a real API item:

* ``url`` is derived deterministically from a valid resource id, or left ``null``;
* ``observed_at`` is the item's ``publishedAt`` date, or ``UNKNOWN`` — never invented;
* ``metrics`` carry only figures the API actually returned.

Auth: the API key comes from the ``YOUTUBE_API_KEY`` environment variable
(``TECHNICAL DEFAULT`` — spec §20.2 mandates an env var but does not name it). The
key is sent only on the wire; it is never written to a raw capture, a log, a
fixture or an error message.

Replay (spec §22): ``replay_uses_live_path = False`` — replay rebuilds signals
from ``<fixture_path>/signals/raw/*.json`` with no network and no key.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from ..schema.codec import CodecError, decode
from ..schema.enums import LANGUAGE_TO_MARKET, CaptureMethod, SourceType
from ..schema.models import Signal
from .base import Collector, CollectorError, SignalCollectionContext, raw_ref_for, register_default

API_BASE = "https://www.googleapis.com/youtube/v3"
API_VERSION = "v3"
API_KEY_ENV = "YOUTUBE_API_KEY"  # TECHNICAL DEFAULT
_SEARCH_ENDPOINT = "search.list"
_VIDEOS_ENDPOINT = "videos.list"
_DEFAULT_MAX_RESULTS = 10
_DEFAULT_ORDER = "relevance"
_VIDEOS_ID_LIMIT = 50  # videos.list `id` filter cap (TECHNICAL DEFAULT)
_HTTP_TIMEOUT = 30
_RFC3339_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})T")
_KEY_IN_URL = re.compile(r"([?&]key=)[^&\s]+")

_WATCH_URL = "https://www.youtube.com/watch?v={id}"
_CHANNEL_URL = "https://www.youtube.com/channel/{id}"
_PLAYLIST_URL = "https://www.youtube.com/playlist?list={id}"
_KIND_NOUN = {
    "youtube#video": "video",
    "youtube#channel": "channel",
    "youtube#playlist": "playlist",
}


def _redact(text: str) -> str:
    return _KEY_IN_URL.sub(r"\1REDACTED", str(text))


# --- injectable client -------------------------------------------------

class YouTubeClient:
    """Protocol: read-only access to the YouTube Data API."""

    def search(
        self,
        *,
        query: str,
        max_results: int,
        order: str,
        region_code: Optional[str] = None,
        relevance_language: Optional[str] = None,
    ) -> dict:  # pragma: no cover - interface
        raise NotImplementedError

    def videos(self, *, video_ids: List[str]) -> dict:  # pragma: no cover - interface
        raise NotImplementedError


class YouTubeDataApiClient(YouTubeClient):
    """Live implementation over ``https://www.googleapis.com/youtube/v3`` (stdlib HTTP)."""

    def __init__(self, *, api_key: Optional[str] = None, opener=None):
        self._api_key = api_key
        self._opener = opener or urllib.request.urlopen

    def _key(self) -> str:
        key = self._api_key or os.environ.get(API_KEY_ENV)
        if not key:
            raise CollectorError(
                f"youtube: no API key (set the {API_KEY_ENV} environment variable) — spec §20.2"
            )
        return key

    def _get(self, path: str, params: Dict[str, str]) -> dict:
        query = urllib.parse.urlencode({**params, "key": self._key()})
        url = f"{API_BASE}/{path}?{query}"
        try:
            with self._opener(url, timeout=_HTTP_TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise CollectorError(_redact(_http_error_message(e))) from None
        except urllib.error.URLError as e:
            raise CollectorError(f"youtube: API unreachable ({_redact(e.reason)})") from e
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise CollectorError(f"youtube: API returned non-JSON ({e})") from e

    def search(
        self, *, query, max_results, order, region_code=None, relevance_language=None
    ) -> dict:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video,channel,playlist",
            "maxResults": str(max(1, min(int(max_results), 50))),
            "order": order,
        }
        if region_code:
            params["regionCode"] = region_code
        if relevance_language:
            params["relevanceLanguage"] = relevance_language
        return self._get("search", params)

    def videos(self, *, video_ids: List[str]) -> dict:
        return self._get(
            "videos",
            {"part": "snippet,statistics", "id": ",".join(video_ids[:_VIDEOS_ID_LIMIT])},
        )


def _http_error_message(err: urllib.error.HTTPError) -> str:
    """Build our own message from the Google error body — never ``str(err)`` (has the URL)."""
    reason, message = "", ""
    try:
        detail = json.loads(err.read().decode("utf-8")).get("error", {})
        errs = detail.get("errors") or []
        reason = (errs[0].get("reason") if errs else "") or ""
        message = detail.get("message", "") or ""
    except (ValueError, AttributeError, KeyError, IndexError, TypeError):
        pass
    if reason == "quotaExceeded":
        return "youtube: API quota exceeded (quotaExceeded)"
    tail = f" {reason}" if reason else ""
    return f"youtube: API error HTTP {err.code}{tail} — {message}".strip(" —")


# --- record types (JSON dicts) ---------------------------------------

def _resource_url(id_obj: dict) -> tuple:
    """Return (resource_id, canonical_url) or (None, None) for an unrecognised kind."""
    kind = id_obj.get("kind")
    if kind == "youtube#video" and id_obj.get("videoId"):
        return id_obj["videoId"], _WATCH_URL.format(id=id_obj["videoId"])
    if kind == "youtube#channel" and id_obj.get("channelId"):
        return id_obj["channelId"], _CHANNEL_URL.format(id=id_obj["channelId"])
    if kind == "youtube#playlist" and id_obj.get("playlistId"):
        return id_obj["playlistId"], _PLAYLIST_URL.format(id=id_obj["playlistId"])
    return None, None


def _statistics(video_item: Optional[dict]) -> Optional[dict]:
    stats = (video_item or {}).get("statistics") or {}
    mapping = {
        "viewCount": "view_count",
        "likeCount": "like_count",
        "commentCount": "comment_count",
        "favoriteCount": "favorite_count",
    }
    out = {mapping[k]: str(v) for k, v in stats.items() if k in mapping and v is not None}
    return out or None


def _request_params_string(query, order, region_code, relevance_language) -> str:
    parts = [
        "part=snippet",
        f"q={query}",
        "type=video,channel,playlist",
        f"maxResults={_DEFAULT_MAX_RESULTS}",
        f"order={order}",
    ]
    if region_code:
        parts.append(f"regionCode={region_code}")
    if relevance_language:
        parts.append(f"relevanceLanguage={relevance_language}")
    return f"{_SEARCH_ENDPOINT}?" + "&".join(parts)


# --- the collector ---------------------------------------------------

class YouTubeCollector(Collector):
    source_type = SourceType.YOUTUBE
    capture_method = CaptureMethod.YOUTUBE_DATA_API
    replay_uses_live_path = False

    def __init__(
        self,
        *,
        client: Optional[YouTubeClient] = None,
        max_results: int = _DEFAULT_MAX_RESULTS,
        order: str = _DEFAULT_ORDER,
    ):
        self._client = client
        self._max_results = max_results
        self._order = order

    def _get_client(self) -> YouTubeClient:
        return self._client or YouTubeDataApiClient()

    def live_records(self, ctx: SignalCollectionContext) -> List[dict]:
        scope = ctx.config.scope
        queries = [q for q in scope.queries if str(q).strip()]
        if not queries:
            raise CollectorError(
                "youtube: scope.queries is empty — the collector has nothing to search "
                "(spec §6.5 requires a query)"
            )
        client = self._get_client()

        region = scope.youtube_region_code or None
        relevance_language = scope.languages[0].value if len(scope.languages) == 1 else None
        market, language = _market_language(scope)

        records: List[dict] = []
        for query in queries:
            search_resp = client.search(
                query=query,
                max_results=self._max_results,
                order=self._order,
                region_code=region,
                relevance_language=relevance_language,
            )
            items = search_resp.get("items") or []
            videos_by_id = self._enrich(client, items)
            request_params = _request_params_string(
                query, self._order, region, relevance_language
            )
            for item in items:
                rec = _build_record(
                    item, videos_by_id, query=query, region_code=region,
                    relevance_language=relevance_language, market=market, language=language,
                    request_params=request_params,
                )
                if rec is not None:
                    records.append(rec)
        return records

    def _enrich(self, client: YouTubeClient, items: List[dict]) -> Dict[str, dict]:
        video_ids = [
            it["id"]["videoId"]
            for it in items
            if (it.get("id") or {}).get("kind") == "youtube#video" and it["id"].get("videoId")
        ]
        if not video_ids:
            return {}
        try:
            resp = client.videos(video_ids=video_ids)
        except CollectorError:
            # Enrichment is best-effort: a videos.list failure means statistics are
            # unavailable this run (§6.3 — a missing figure is UNKNOWN, not an error).
            return {}
        return {v["id"]: v for v in (resp.get("items") or []) if v.get("id")}

    def query_or_reference(self, record, index, ctx) -> str:
        return record.get("request_params") or _SEARCH_ENDPOINT

    def record_url(self, record) -> Optional[str]:
        return record.get("url")

    def record_to_signal(
        self,
        record: dict,
        *,
        signal_id: str,
        collected_at: str,
        query_or_reference: str,
        ctx: SignalCollectionContext,
    ) -> Signal:
        if not isinstance(record, dict) or not record.get("title") or not record.get("kind"):
            raise CollectorError(f"youtube record for {signal_id} is missing kind/title")

        observed_at = _rfc3339_to_date(record.get("published_at")) or "UNKNOWN"
        url = record.get("url") or None
        source = f"YouTube Data API — {record.get('endpoint', _SEARCH_ENDPOINT)}"

        payload = {
            "signal_id": signal_id,
            "schema_version": "1.0.0",
            "run_id": ctx.run_id,
            "source": source,
            "source_type": SourceType.YOUTUBE.value,
            "observed_at": observed_at,
            "collected_at": collected_at,
            "market": str(record.get("market") or "UNKNOWN"),
            "language": str(record.get("language") or "UNKNOWN"),
            "platform": "youtube",
            "signal_type": "content_format",  # TECHNICAL DEFAULT — Normalization refines
            "evidence": _evidence(record),
            "raw_ref": raw_ref_for(ctx.run_id, signal_id),
            "context": _context(record),
            "confidence": "LOW",  # TECHNICAL DEFAULT — one result is weak evidence
            "provenance": {
                "source": source,
                "source_type": SourceType.YOUTUBE.value,
                "observed_at": observed_at,
                "collected_at": collected_at,
                "query_or_reference": query_or_reference,
                "capture_method": CaptureMethod.YOUTUBE_DATA_API.value,
                "url": url,
                "source_version": API_VERSION,
            },
        }
        if url is not None:
            payload["url"] = url
        metrics = record.get("metrics")
        if metrics:
            payload["metrics"] = metrics

        try:
            return decode(Signal, payload)
        except CodecError as e:
            raise CollectorError(
                f"youtube record for {signal_id} is not a valid Signal: {e}"
            ) from e


def _build_record(
    item: dict,
    videos_by_id: Dict[str, dict],
    *,
    query: str,
    region_code: Optional[str],
    relevance_language: Optional[str],
    market: str,
    language: str,
    request_params: str,
) -> Optional[dict]:
    id_obj = item.get("id") or {}
    resource_id, url = _resource_url(id_obj)
    snippet = item.get("snippet") or {}
    title = snippet.get("title")
    if not resource_id or not title:
        return None  # rule 17: a malformed item is skipped, never a broken Signal

    video_item = videos_by_id.get(resource_id) if id_obj.get("kind") == "youtube#video" else None
    return {
        "endpoint": _SEARCH_ENDPOINT,
        "kind": id_obj.get("kind"),
        "resource_id": resource_id,
        "url": url,
        "title": title,
        "channel_title": snippet.get("channelTitle"),
        "published_at": snippet.get("publishedAt"),
        "description": snippet.get("description"),
        "query": query,
        "region_code": region_code,
        "relevance_language": relevance_language,
        "order": _DEFAULT_ORDER,
        "market": market,
        "language": language,
        "request_params": request_params,
        "metrics": _statistics(video_item),
        "search_item": item,
        "video_item": video_item,
        "api_version": API_VERSION,
    }


def _evidence(record: dict) -> str:
    noun = _KIND_NOUN.get(record.get("kind"), "result")
    bits = [f'YouTube {noun} "{record["title"]}"']
    if record.get("channel_title"):
        bits.append(f'by {record["channel_title"]}')
    views = (record.get("metrics") or {}).get("view_count")
    if views:
        bits.append(f"({views} views)")
    return " ".join(bits) + f' returned by {_SEARCH_ENDPOINT} for the query "{record["query"]}".'


def _context(record: dict) -> str:
    hints = [f"order={record.get('order')}"]
    if record.get("region_code"):
        hints.append(f"regionCode={record['region_code']}")
    if record.get("relevance_language"):
        hints.append(f"relevanceLanguage={record['relevance_language']}")
    return (
        f"YouTube Data API {_SEARCH_ENDPOINT} result ({', '.join(hints)}) "
        f'for the query "{record.get("query")}".'
    )


def _market_language(scope) -> tuple:
    languages = scope.languages
    if len(scope.markets) == 1:
        market = scope.markets[0].value
    elif len(languages) == 1:
        market = LANGUAGE_TO_MARKET[languages[0]].value
    else:
        market = "UNKNOWN"
    language = languages[0].value if len(languages) == 1 else "UNKNOWN"
    return market, language


def _rfc3339_to_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    m = _RFC3339_DATE.match(str(value))
    if not m:
        return None
    try:
        return _dt.date.fromisoformat(m.group(1)).isoformat()
    except ValueError:
        return None


register_default(YouTubeCollector())
