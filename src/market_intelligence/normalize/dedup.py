"""Deterministic signal deduplication driven entirely by ``config/dedup.yaml`` (spec §6.6).

The dedup key is the ordered tuple of ``dedup_key_parts``; two signals are
duplicates only when their keys AND their ``observed_at`` calendar day match
(when ``duplicate_requires_same_observed_at``). On a duplicate: keep the higher
``confidence`` (tie → lower ``signal_id``), merge only the metrics keys the kept
signal lacks (``merge_absent_metrics``) — a conflicting value is never
overwritten — and record what was dropped and why.
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from typing import List, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..schema.models import Signal

_CONF_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
_WORD_RE = re.compile(r"[0-9a-z]+")
_WS_RE = re.compile(r"\s+")


class NormalizationError(Exception):
    """``config/dedup.yaml`` is malformed (e.g. names an unknown key part)."""


@dataclass
class DedupReason:
    kept: str
    dropped: str
    dedup_key: str            # the joined key string — deterministic and loggable
    observed_at: str          # the calendar day the duplicate shared
    merged_metric_keys: List[str]


# --- dedup key ---------------------------------------------------------

def dedup_key(sig: Signal, *, dedup_config: dict) -> Tuple[str, ...]:
    parts = dedup_config.get("dedup_key_parts") or []
    token = str(dedup_config.get("missing_part_token", "∅"))
    tracking = {str(p).lower() for p in dedup_config.get("url_tracking_params") or []}
    stopwords = _all_stopwords(dedup_config)
    return tuple(_key_part(str(p), sig, token, tracking, stopwords) for p in parts)


def _key_part(part: str, sig: Signal, token: str, tracking: set, stopwords: frozenset) -> str:
    if part == "normalized_source":
        return _casefold_ws(sig.provenance.source) or token
    if part == "canonical_url":
        return _canonical_url(sig.url, tracking) if sig.url else token
    if part == "market":
        return str(sig.market).strip().casefold() or token
    if part == "language":
        return str(sig.language).strip().casefold() or token
    if part == "platform":
        return sig.platform.value.strip().casefold()
    if part == "signal_type":
        return sig.signal_type.value.strip().casefold()
    if part == "normalized_subject":
        return _normalized_subject(sig.evidence, stopwords) or token
    raise NormalizationError(f"config/dedup.yaml names an unknown dedup_key part: {part!r}")


def _casefold_ws(text) -> str:
    return _WS_RE.sub(" ", str(text or "")).strip().casefold()


def _canonical_url(url: str, tracking: set) -> str:
    """Drop the fragment and the configured tracking params, lowercase scheme/host,
    sort the remaining query — a deterministic canonical form (spec §6.6)."""
    p = urlsplit(str(url).strip())
    query = sorted(
        (k, v)
        for k, v in parse_qsl(p.query, keep_blank_values=True)
        if k.lower() not in tracking
    )
    path = p.path.rstrip("/") or "/"
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), path, urlencode(query), ""))


def _all_stopwords(dedup_config: dict) -> frozenset:
    words = set()
    for lst in (dedup_config.get("stopwords") or {}).values():
        words.update(str(w).lower() for w in lst or [])
    return frozenset(words)


def _normalized_subject(evidence: str, stopwords: frozenset) -> str:
    tokens = _WORD_RE.findall(str(evidence or "").lower())
    return "-".join(t for t in tokens if len(t) > 1 and t not in stopwords)


def _conf_rank(confidence) -> int:
    value = str(getattr(confidence, "value", confidence)).upper()
    return _CONF_RANK.get(value, -1)


# --- dedup ------------------------------------------------------------

def deduplicate(
    signals: Sequence[Signal], dedup_config: dict
) -> Tuple[List[Signal], List[str], List[DedupReason]]:
    """Return (kept_signals, discarded_signal_ids, reasons) — all deterministically ordered.

    Input order does not affect the result. Original ``Signal`` objects are never
    mutated; a kept signal whose metrics were merged is returned as a new object.
    """
    require_same_day = bool(dedup_config.get("duplicate_requires_same_observed_at", True))
    on_dup = dedup_config.get("on_duplicate") or {}
    merge_metrics = bool(on_dup.get("merge_absent_metrics"))

    groups: dict = {}
    for sig in sorted(signals, key=lambda s: s.signal_id):
        key = "|".join(dedup_key(sig, dedup_config=dedup_config))
        day = sig.observed_at if require_same_day else ""
        groups.setdefault((key, day), []).append(sig)

    kept: List[Signal] = []
    discarded: List[str] = []
    reasons: List[DedupReason] = []

    for (key, day), members in groups.items():
        if len(members) == 1:
            kept.append(members[0])
            continue

        ordered = sorted(members, key=lambda s: (-_conf_rank(s.confidence), s.signal_id))
        winner, losers = ordered[0], ordered[1:]
        metrics = dict(winner.metrics) if winner.metrics else None

        for loser in sorted(losers, key=lambda s: s.signal_id):
            discarded.append(loser.signal_id)
            added: List[str] = []
            if merge_metrics and loser.metrics:
                if metrics is None:
                    metrics = {}
                for k, v in loser.metrics.items():
                    if k not in metrics:  # conflicting values are NEVER overwritten
                        metrics[k] = v
                        added.append(k)
            reasons.append(DedupReason(winner.signal_id, loser.signal_id, key, day, sorted(added)))

        if metrics != winner.metrics:
            winner = dataclasses.replace(winner, metrics=metrics)
        kept.append(winner)

    kept.sort(key=lambda s: s.signal_id)
    discarded.sort()
    reasons.sort(key=lambda r: (r.kept, r.dropped))
    return kept, discarded, reasons
