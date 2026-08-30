"""Web Search collector (spec §6.5 — ``web_search`` / ``claude_web_search``).

Uses the Claude API's **server-side Web Search tool** as live research. Every
``Signal`` it produces is anchored to a real ``web_search_result`` returned by the
API — a statement the model makes without a search result behind it is discarded
(spec §6.5, §14). Two model calls per collection:

1. a web-search call that gathers real results + the model's analysis;
2. a structuring call (no tools) that turns that into ``Signal`` candidates.

Deduplication, evaluation and Opportunity framing are **not** done here.

Replay (spec §22): with ``replay.enabled`` and ``replay.llm != "live"`` the
collector reads recorded research from ``<fixture_path>/llm/web_search/*.json``
instead of calling the API; ``replay.llm == "live"`` re-runs the real call (used
to refresh fixtures). Tests inject a ``WebSearchClient`` and never touch the
network.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

from ..io_utils import LoadError, read_json
from ..schema.codec import CodecError, decode
from ..schema.enums import (
    CaptureMethod,
    Confidence,
    Durability,
    Language,
    Market,
    Platform,
    SignalType,
    SourceType,
)
from ..schema.models import Signal
from .base import Collector, CollectorError, SignalCollectionContext, raw_ref_for, register_default

# Basic web search — one of the three current tool versions (no beta header),
# defaults allowed_callers=["direct"], returns every result (no dynamic filtering).
# The newer web_search_20260209 / _20260318 only add optional capabilities the
# pipeline does not need. Verified against the official tool reference 2026-08-30.
WEB_SEARCH_TOOL_TYPE = "web_search_20250305"
_DEFAULT_MAX_USES = 8
_DEFAULT_MAX_TOKENS = 8000
_MAX_PAUSE_RESTARTS = 5

_PAGE_AGE_FORMATS = (
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
    "%Y/%m/%d",
    "%m/%d/%Y",
)


# --- research data types -------------------------------------------------

@dataclass
class WebSearchResult:
    """One ``web_search_result`` block from the API (spec: url / title / page_age)."""

    url: Optional[str] = None
    title: Optional[str] = None
    page_age: Optional[str] = None  # verbatim from the API; free-form, may be null


@dataclass
class WebSearchFinding:
    """A single observation the model extracted, anchored to a real search result."""

    query: str
    result_url: Optional[str]
    result_title: Optional[str]
    evidence: str
    context: str
    market: str
    language: str
    platform: str
    signal_type: str
    confidence: str
    result_page_age: Optional[str] = None
    durability_hint: Optional[str] = None
    raw_excerpt: Optional[str] = None


@dataclass
class WebSearchResearch:
    """The full output of one ``WebSearchClient.research`` call."""

    findings: List[WebSearchFinding] = field(default_factory=list)
    results: List[WebSearchResult] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    provider_response: Optional[dict] = None  # recorded for the llm/ fixture + provenance


class WebSearchClient:
    """Protocol: perform live web research and return structured findings."""

    def research(
        self, *, brief: str, model: str, max_uses: int
    ) -> WebSearchResearch:  # pragma: no cover - interface
        raise NotImplementedError


# --- the real client ---------------------------------------------------

def _obj(properties: dict, required: list) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def _findings_schema() -> dict:
    finding = _obj(
        {
            "query": {"type": "string"},
            "result_url": {"type": "string"},
            "result_title": {"type": "string"},
            "result_page_age": {"type": ["string", "null"]},
            "evidence": {"type": "string"},
            "context": {"type": "string"},
            "market": {"type": "string", "enum": [m.value for m in Market] + ["UNKNOWN"]},
            "language": {"type": "string", "enum": [x.value for x in Language] + ["UNKNOWN"]},
            "platform": {"type": "string", "enum": [p.value for p in Platform]},
            "signal_type": {"type": "string", "enum": [s.value for s in SignalType]},
            "confidence": {"type": "string", "enum": [c.value for c in Confidence]},
            "durability_hint": {
                "type": ["string", "null"],
                "enum": [d.value for d in Durability] + [None],
            },
            "raw_excerpt": {"type": ["string", "null"]},
        },
        [
            "query", "result_url", "result_title", "result_page_age", "evidence",
            "context", "market", "language", "platform", "signal_type", "confidence",
            "durability_hint", "raw_excerpt",
        ],
    )
    return _obj({"findings": {"type": "array", "items": finding}}, ["findings"])


class AnthropicWebSearch(WebSearchClient):
    """Live implementation backed by the Anthropic SDK's server-side web search."""

    def __init__(self, *, client=None, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _build_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic  # lazy: keeps the deterministic layer import-light
        except ImportError as e:  # pragma: no cover - dependency always installed in dev
            raise CollectorError(
                "web_search needs the 'anthropic' package; install the project's dependencies"
            ) from e
        if not (
            self._api_key
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        ):
            raise CollectorError(
                "web_search: no Anthropic credentials (set ANTHROPIC_API_KEY) — spec §20.2"
            )
        return anthropic.Anthropic(api_key=self._api_key)

    def research(self, *, brief: str, model: str, max_uses: int) -> WebSearchResearch:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise CollectorError("web_search needs the 'anthropic' package") from e
        client = self._build_client()

        try:
            search_msg = self._run_search(client, model=model, brief=brief, max_uses=max_uses)
            results, queries, analysis = _parse_search_response(search_msg)
            findings = self._structure(client, model=model, brief=brief,
                                       analysis=analysis, results=results, queries=queries)
        except anthropic.APIError as e:  # network / auth / quota / 4xx-5xx
            raise CollectorError(f"web_search API call failed: {e}") from e

        return WebSearchResearch(
            findings=findings,
            results=results,
            queries=queries,
            provider_response={"search": _safe_dump(search_msg)},
        )

    def _run_search(self, client, *, model: str, brief: str, max_uses: int):
        user_msg = {"role": "user", "content": _search_prompt(brief)}
        messages = [user_msg]
        tools = [{"type": WEB_SEARCH_TOOL_TYPE, "name": "web_search", "max_uses": max_uses}]
        for _ in range(_MAX_PAUSE_RESTARTS + 1):
            msg = client.messages.create(
                model=model, max_tokens=_DEFAULT_MAX_TOKENS, tools=tools, messages=messages,
            )
            if msg.stop_reason != "pause_turn":
                return msg
            # Resume a paused server-tool turn: re-send [user, latest paused assistant].
            # REPLACE the list (do not append) — consecutive assistant turns are a 400,
            # and the paused assistant turn already carries the accumulated
            # server_tool_use / web_search_tool_result blocks. The server detects the
            # trailing server_tool_use block and resumes; no "Continue" message is added.
            # (Anthropic web-search tool + server-tools docs, verified 2026-08-30.)
            messages = [user_msg, {"role": "assistant", "content": msg.content}]
        raise CollectorError("web_search still paused after max restarts")

    def _structure(
        self, client, *, model, brief, analysis, results, queries
    ) -> List[WebSearchFinding]:
        prompt = _structuring_prompt(brief, analysis, results, queries)
        msg = client.messages.create(
            model=model,
            max_tokens=_DEFAULT_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": _findings_schema()}},
        )
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as e:
            raise CollectorError(f"web_search structuring returned non-JSON: {e}") from e
        return [decode(WebSearchFinding, f) for f in payload.get("findings", [])]


def _search_prompt(brief: str) -> str:
    return (
        "You are a market-intelligence researcher for an AI-assisted wellness "
        "instrumental-music business. Use web search to find CURRENT, externally "
        "observable signals of audience demand, behaviour or growth relevant to the "
        "brief below. Report only what a specific search result actually shows — never "
        "your own background knowledge. If a claim is not supported by a search result, "
        "do not make it.\n\n"
        f"Brief:\n{brief}"
    )


def _structuring_prompt(brief, analysis, results, queries) -> str:
    listing = "\n".join(
        f"- url: {r.url}\n  title: {r.title}\n  page_age: {r.page_age}" for r in results
    )
    return (
        "Turn the web-search research below into a list of discrete findings. Each "
        "finding MUST be anchored to one of the search results listed (copy its url and "
        "title exactly). Set result_page_age to the result's page_age string verbatim, or "
        "null if it has none — never invent a date. evidence is a 1-2 sentence statement "
        "of what that result shows. Classify market / language / platform / signal_type / "
        "confidence. Use UNKNOWN where a market or language is not clear.\n\n"
        f"Brief:\n{brief}\n\n"
        f"Queries run:\n" + "\n".join(f"- {q}" for q in queries) + "\n\n"
        f"Search results:\n{listing}\n\n"
        f"Researcher analysis:\n{analysis}"
    )


def _parse_search_response(msg):
    results: List[WebSearchResult] = []
    queries: List[str] = []
    analysis_parts: List[str] = []
    for block in msg.content:
        btype = getattr(block, "type", None)
        if btype == "server_tool_use" and getattr(block, "name", None) == "web_search":
            q = (getattr(block, "input", None) or {}).get("query")
            if q:
                queries.append(q)
        elif btype == "web_search_tool_result":
            content = getattr(block, "content", None)
            if isinstance(content, list):
                for item in content:
                    if getattr(item, "type", None) == "web_search_result":
                        results.append(WebSearchResult(
                            url=getattr(item, "url", None),
                            title=getattr(item, "title", None),
                            page_age=getattr(item, "page_age", None),
                        ))
            # an error object (not a list) -> no results from this call, not fatal
        elif btype == "text":
            analysis_parts.append(getattr(block, "text", "") or "")
    return results, queries, "\n".join(p for p in analysis_parts if p)


def _safe_dump(msg) -> dict:
    for attr in ("to_dict", "model_dump"):
        fn = getattr(msg, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:  # pragma: no cover - best-effort recording
                pass
    return {"repr": repr(msg)}


# --- the collector ---------------------------------------------------

class WebSearchCollector(Collector):
    source_type = SourceType.WEB_SEARCH
    capture_method = CaptureMethod.CLAUDE_WEB_SEARCH
    replay_uses_live_path = True

    def __init__(
        self,
        *,
        client: Optional[WebSearchClient] = None,
        max_uses: int = _DEFAULT_MAX_USES,
    ):
        self._client = client
        self._max_uses = max_uses

    def _get_client(self) -> WebSearchClient:
        return self._client or AnthropicWebSearch()

    def live_records(self, ctx: SignalCollectionContext) -> List[dict]:
        if ctx.replay and ctx.replay_llm_mode != "live":
            research = self._load_recorded(ctx)
        else:
            try:
                research = self._get_client().research(
                    brief=self._brief(ctx),
                    model=ctx.config.model,
                    max_uses=self._max_uses,
                )
            except CollectorError:
                raise
            except Exception as e:  # any client bug / SDK surprise -> degrade, don't crash
                raise CollectorError(f"web_search research failed: {e}") from e

        anchored_urls = {r.url for r in research.results if r.url}
        kept: List[dict] = []
        for f in research.findings:
            if not f.result_url or f.result_url not in anchored_urls:
                continue  # spec §6.5: a finding not backed by a real result is not a Signal
            if not str(f.evidence or "").strip():
                continue  # nothing observable to record
            kept.append(_finding_record(f))
        return kept

    def query_or_reference(self, record, index, ctx) -> str:
        return record.get("query") or f"web_search finding {index}"

    def record_url(self, record) -> Optional[str]:
        return record.get("result_url")

    def record_to_signal(
        self,
        record: dict,
        *,
        signal_id: str,
        collected_at: str,
        query_or_reference: str,
        ctx: SignalCollectionContext,
    ) -> Signal:
        evidence = str(record.get("evidence") or "").strip()
        if not evidence:
            raise CollectorError(f"web_search record for {signal_id} has no evidence")

        observed_at = _page_age_to_iso(record.get("result_page_age")) or "UNKNOWN"
        url = record.get("result_url") or None
        source = str(record.get("result_title") or "Web search result")

        payload = {
            "signal_id": signal_id,
            "schema_version": "1.0.0",
            "run_id": ctx.run_id,
            "source": source,
            "source_type": SourceType.WEB_SEARCH.value,
            "observed_at": observed_at,
            "collected_at": collected_at,
            "market": str(record.get("market") or "UNKNOWN"),
            "language": str(record.get("language") or "UNKNOWN"),
            "platform": str(record.get("platform") or "web"),
            "signal_type": str(record.get("signal_type") or "other"),
            "evidence": evidence,
            "raw_ref": raw_ref_for(ctx.run_id, signal_id),
            "context": str(record.get("context") or ""),
            "confidence": str(record.get("confidence") or "LOW"),
            "provenance": {
                "source": source,
                "source_type": SourceType.WEB_SEARCH.value,
                "observed_at": observed_at,
                "collected_at": collected_at,
                "query_or_reference": query_or_reference,
                "capture_method": CaptureMethod.CLAUDE_WEB_SEARCH.value,
                "url": url,
            },
        }
        if url is not None:
            payload["url"] = url
        for key in ("raw_excerpt", "durability_hint"):
            value = record.get(key)
            if value is not None:
                payload[key] = value

        try:
            return decode(Signal, payload)
        except CodecError as e:
            raise CollectorError(
                f"web_search record for {signal_id} is not a valid Signal: {e}"
            ) from e

    # --- helpers ---

    def _brief(self, ctx: SignalCollectionContext) -> str:
        s = ctx.config.scope
        clusters = s.clusters or "open discovery (any of the 11 canonical clusters)"
        lines = [
            f"Markets: {[m.value for m in s.markets] or 'all three V1 markets'}",
            f"Languages: {[x.value for x in s.languages]}",
            f"Clusters of interest: {clusters}",
            f"Platforms the research is about: {[p.value for p in s.discovery_platforms]}",
        ]
        if s.notes:
            lines.append(f"Notes: {s.notes}")
        return "\n".join(f"- {line}" for line in lines)

    def _load_recorded(self, ctx: SignalCollectionContext) -> WebSearchResearch:
        base = ctx.fixture_path
        if base is None:
            raise CollectorError("web_search replay: replay.fixture_path is not set")
        directory = base / "llm" / "web_search"
        if not directory.is_dir():
            raise CollectorError(
                f"web_search replay: no recorded fixtures at {directory} (spec §22)"
            )
        files = sorted(directory.glob("*.json"))
        if not files:
            raise CollectorError(f"web_search replay: no *.json fixtures in {directory}")

        merged = WebSearchResearch()
        for path in files:
            try:
                raw = read_json(path)
            except LoadError as e:
                raise CollectorError(str(e)) from e
            one = decode(WebSearchResearch, raw)
            merged.findings.extend(one.findings)
            merged.results.extend(one.results)
            merged.queries.extend(one.queries)
            if merged.provider_response is None:
                merged.provider_response = one.provider_response
        return merged


def _finding_record(f: WebSearchFinding) -> dict:
    return {
        "query": f.query,
        "result_url": f.result_url,
        "result_title": f.result_title,
        "result_page_age": f.result_page_age,
        "evidence": f.evidence,
        "context": f.context,
        "market": f.market,
        "language": f.language,
        "platform": f.platform,
        "signal_type": f.signal_type,
        "confidence": f.confidence,
        "durability_hint": f.durability_hint,
        "raw_excerpt": f.raw_excerpt,
    }


def _page_age_to_iso(value: Optional[str]) -> Optional[str]:
    """Normalise a free-form ``page_age`` to an ISO date, or ``None`` (never guessed)."""
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    try:
        return _dt.date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        pass
    for fmt in _PAGE_AGE_FORMATS:
        try:
            return _dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None  # "3 days ago", "last week", etc. -> observed_at becomes UNKNOWN


register_default(WebSearchCollector())
