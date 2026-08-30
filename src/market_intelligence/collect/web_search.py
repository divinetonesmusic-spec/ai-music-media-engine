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
import logging
import os
import re
from dataclasses import dataclass, field
from time import monotonic as _monotonic
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
# The structuring call runs with adaptive thinking on (Sonnet 5 default) AND emits
# the findings JSON. On the first live dry run, effort=high (the default) spent
# the whole 16000-token budget on thinking (stop_reason=max_tokens, only a
# `thinking` block returned). Structuring is pure extraction, so it runs at
# effort="low" (see _structure) and gets more room here.
_STRUCTURING_MAX_TOKENS = 24000
_MAX_PAUSE_RESTARTS = 5

# --- timeout / retry policy (spec §14; anthropic SDK 1.2.0) --------------------
# SDK defaults are Timeout(read=600) with max_retries=2 — a stalled call blocks
# for up to 600s and every timeout is retried, so a single messages.create can
# hang ~30 min, and _run_search loops on pause_turn. These bound it: an explicit
# read timeout well under 600s, one retry (keeps transient-429/5xx recovery
# without tripling the wait on a real timeout), and a wall-clock ceiling for the
# whole pause_turn loop. Non-streaming server-side web search still has no output
# for the entire server run, so the read timeout must clear a legitimately slow
# multi-search request — 420s, not tighter.
_CONNECT_TIMEOUT = 10.0
_READ_TIMEOUT = 420.0
_MAX_RETRIES = 1
_SEARCH_PHASE_BUDGET_S = 900.0

_LOG = logging.getLogger(__name__)

_KEY_IN_TEXT = re.compile(r"sk-ant-[A-Za-z0-9_-]+")


def _redact(text: str) -> str:
    return _KEY_IN_TEXT.sub("sk-ant-REDACTED", str(text))


def _timeout_exc_types() -> tuple:
    """``anthropic.APITimeoutError`` if importable, else an empty tuple (catches
    nothing) so a missing SDK never turns into an ``except`` failure."""
    try:
        import anthropic
    except ImportError:  # pragma: no cover - installed in dev
        return ()
    return (anthropic.APITimeoutError,)

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


def _nullable(inner: dict) -> dict:
    """``inner``'s value, or JSON null.

    Anthropic's ``output_config`` json_schema validator rejects a union ``type``
    array (``{"type": ["string", "null"]}`` -> ``400 output_config.format.schema:
    Invalid schema``); ``anyOf`` with an explicit null branch is the supported
    form (structured-outputs subset reference, verified 2026-08-30).
    """
    return {"anyOf": [inner, {"type": "null"}]}


def _findings_schema() -> dict:
    finding = _obj(
        {
            "query": {"type": "string"},
            "result_url": {"type": "string"},
            "result_title": {"type": "string"},
            "result_page_age": _nullable({"type": "string"}),
            "evidence": {"type": "string"},
            "context": {"type": "string"},
            "market": {"type": "string", "enum": [m.value for m in Market] + ["UNKNOWN"]},
            "language": {"type": "string", "enum": [x.value for x in Language] + ["UNKNOWN"]},
            "platform": {"type": "string", "enum": [p.value for p in Platform]},
            "signal_type": {"type": "string", "enum": [s.value for s in SignalType]},
            "confidence": {"type": "string", "enum": [c.value for c in Confidence]},
            "durability_hint": _nullable(
                {"type": "string", "enum": [d.value for d in Durability]}
            ),
            "raw_excerpt": _nullable({"type": "string"}),
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
        return anthropic.Anthropic(
            api_key=self._api_key,
            timeout=anthropic.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT),
            max_retries=_MAX_RETRIES,
        )

    def research(self, *, brief: str, model: str, max_uses: int) -> WebSearchResearch:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise CollectorError("web_search needs the 'anthropic' package") from e
        client = self._build_client()

        try:
            search_msg = self._run_search(client, model=model, brief=brief, max_uses=max_uses)
            results, queries, analysis = _parse_search_response(search_msg)
            findings, structuring_msg = self._structure(
                client, model=model, brief=brief,
                analysis=analysis, results=results, queries=queries,
            )
        except anthropic.APIError as e:  # network / auth / quota / 4xx-5xx
            raise CollectorError(_redact(f"web_search API call failed: {e}")) from e

        return WebSearchResearch(
            findings=findings,
            results=results,
            queries=queries,
            provider_response={
                "search": _safe_dump(search_msg),
                "structuring": _safe_dump(structuring_msg),
            },
        )

    def _run_search(self, client, *, model: str, brief: str, max_uses: int):
        user_msg = {"role": "user", "content": _search_prompt(brief)}
        messages = [user_msg]
        tools = [{"type": WEB_SEARCH_TOOL_TYPE, "name": "web_search", "max_uses": max_uses}]
        deadline = _monotonic() + _SEARCH_PHASE_BUDGET_S
        for attempt in range(_MAX_PAUSE_RESTARTS + 1):
            if _monotonic() > deadline:
                raise CollectorError(
                    f"web_search: the search phase exceeded its {_SEARCH_PHASE_BUDGET_S:.0f}s "
                    f"budget after {attempt} pause_turn resume(s)"
                )
            _LOG.info(
                "web_search: search request %d/%d (max_uses=%d)",
                attempt + 1, _MAX_PAUSE_RESTARTS + 1, max_uses,
            )
            try:
                msg = client.messages.create(
                    model=model, max_tokens=_DEFAULT_MAX_TOKENS, tools=tools, messages=messages,
                )
            except _timeout_exc_types() as e:
                raise CollectorError(
                    f"web_search: the server-side web search did not return within "
                    f"~{_READ_TIMEOUT:.0f}s (search request {attempt + 1})"
                ) from e
            if msg.stop_reason != "pause_turn":
                _LOG.info("web_search: search returned (stop_reason=%s)", msg.stop_reason)
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
    ) -> "tuple[List[WebSearchFinding], object]":
        prompt = _structuring_prompt(brief, analysis, results, queries)
        _LOG.info("web_search: structuring call (max_tokens=%d)", _STRUCTURING_MAX_TOKENS)
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=_STRUCTURING_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
                # `effort` is a direct key of output_config, sibling of `format`
                # (Anthropic effort docs, verified 2026-08-30) — NOT nested in
                # `format`. "low" keeps this extraction call from spending its
                # whole token budget on thinking (the first live run's
                # stop_reason=max_tokens).
                output_config={
                    "format": {"type": "json_schema", "schema": _findings_schema()},
                    "effort": "low",
                },
            )
        except _timeout_exc_types() as e:
            raise CollectorError(
                f"web_search: the structuring call did not return within ~{_READ_TIMEOUT:.0f}s"
            ) from e
        payload = _structured_json_object(msg, stage="web_search structuring")
        findings = [decode(WebSearchFinding, f) for f in payload.get("findings", [])]
        return findings, msg


def _block_types(msg) -> list:
    """Sorted distinct ``type`` values across ``msg.content`` (for diagnostics)."""
    return sorted({str(getattr(b, "type", "?")) for b in getattr(msg, "content", None) or []})


def _structured_output_text(msg) -> str:
    """Concatenate every ``text`` block. Per the Anthropic structured-output docs
    the JSON arrives in a ``text`` content block; with thinking on (Sonnet 5
    default) ``thinking`` blocks precede it, and the model may split the JSON
    across more than one ``text`` block."""
    parts = [
        b.text
        for b in getattr(msg, "content", None) or []
        if getattr(b, "type", None) == "text" and getattr(b, "text", None)
    ]
    return "".join(parts).strip()


def _structured_json_object(msg, *, stage: str) -> dict:
    """Parse a structured-output response into a JSON object, or raise a
    ``CollectorError`` that says exactly what came back instead of a bare
    ``json.loads("")``. Never fabricates JSON."""
    text = _structured_output_text(msg)
    if not text:
        stop = getattr(msg, "stop_reason", None)
        blocks = _block_types(msg)
        if stop == "refusal":
            cat = getattr(getattr(msg, "stop_details", None), "category", None)
            raise CollectorError(
                f"{stage}: the model refused the request (stop_reason=refusal"
                + (f", category={cat}" if cat else "")
                + ") — no structured output was produced"
            )
        if stop == "max_tokens":
            raise CollectorError(
                f"{stage}: the response hit the max_tokens cap before any JSON text "
                f"(stop_reason=max_tokens, blocks={blocks}); raise _STRUCTURING_MAX_TOKENS"
            )
        raise CollectorError(
            f"{stage}: the response carried no JSON text block "
            f"(stop_reason={stop!r}, blocks={blocks})"
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise CollectorError(
            f"{stage}: response text is not valid JSON ({e}); "
            f"starts with {_redact(text[:160])!r}"
        ) from e
    if not isinstance(payload, dict):
        raise CollectorError(
            f"{stage}: structured response is a {type(payload).__name__}, not a JSON object"
        )
    return payload


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
