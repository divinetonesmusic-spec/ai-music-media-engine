"""TikTok Creative Center collector (spec §6.5 — ``tiktok_creative_center`` / ``analyst_capture``).

V1 assumes **no free public API**. An analyst manually reviews TikTok Creative
Center and records observations into a structured capture file
(``RunConfig.tiktok_capture_path``); this collector reads that file and maps each
record field-for-field to a ``Signal``. Nothing is fetched, scraped, automated or
inferred.

Fully deterministic. ``replay_uses_live_path = False`` — replay rebuilds signals
from ``<fixture_path>/signals/raw/*.json`` (no TikTok access).

Capture-file shape (same family as §6.4): a YAML/JSON list of records, or a
mapping with a ``records:`` list. Each record:

* required — ``panel``, ``market``, ``language``, ``signal_type``, ``evidence``,
  ``context``, ``confidence``;
* optional — ``observed_at`` (absent -> ``UNKNOWN``, never invented),
  ``url`` (absent -> ``null``), ``query_or_reference`` / ``filter`` (the panel
  filter used; defaults to ``panel``), ``platform`` (defaults to ``tiktok`` —
  ``TECHNICAL DEFAULT``, since Creative Center content is inherently TikTok),
  ``metrics`` (passed through unchanged), ``raw_excerpt``, ``durability_hint``.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import List, Optional

from ..io_utils import LoadError, read_yaml
from ..schema.codec import CodecError, decode
from ..schema.enums import CaptureMethod, SourceType
from ..schema.models import Signal
from .base import Collector, CollectorError, SignalCollectionContext, raw_ref_for, register_default

_REQUIRED_FIELDS = (
    "panel",
    "market",
    "language",
    "signal_type",
    "evidence",
    "context",
    "confidence",
)
_DEFAULT_PLATFORM = "tiktok"  # TECHNICAL DEFAULT — Creative Center content is TikTok content
_PASSTHROUGH_OPTIONAL = ("raw_excerpt", "durability_hint", "metrics")


def _blank(value) -> bool:
    return value in (None, "") or not str(value).strip()


def _opt(record: dict, key: str) -> Optional[str]:
    value = record.get(key)
    return None if value is None else str(value)


def _observed_at(value) -> str:
    """The analyst's date, normalised to ``YYYY-MM-DD``; ``UNKNOWN`` if absent.

    A present-but-unparseable value is a malformed record (the source degrades) —
    a date is never guessed or fabricated.
    """
    if _blank(value):
        return "UNKNOWN"
    text = str(value).strip()
    if text == "UNKNOWN":
        return "UNKNOWN"
    try:
        _dt.date.fromisoformat(text[:10])
    except ValueError:
        raise CollectorError(
            f"tiktok capture: malformed observed_at {value!r} — expected YYYY-MM-DD or UNKNOWN"
        ) from None
    return text[:10]


class TikTokCreativeCenterCollector(Collector):
    source_type = SourceType.TIKTOK_CREATIVE_CENTER
    capture_method = CaptureMethod.ANALYST_CAPTURE
    replay_uses_live_path = False

    def live_records(self, ctx: SignalCollectionContext) -> List[dict]:
        rel = ctx.config.tiktok_capture_path
        if not rel:
            raise CollectorError(
                "tiktok_creative_center is a signal source but tiktok_capture_path is not set "
                "(spec §20.1)"
            )
        path = Path(rel)
        if not path.is_absolute():
            path = ctx.project_root / path
        if not path.exists():
            raise CollectorError(f"tiktok capture file not found: {path}")
        try:
            data = read_yaml(path)
        except LoadError as e:
            raise CollectorError(str(e)) from e

        records = data.get("records") if isinstance(data, dict) else data
        if not isinstance(records, list) or not records:
            raise CollectorError(
                f"tiktok capture file must be a non-empty list of records "
                f"(or a mapping with a 'records:' list): {path}"
            )
        return records

    def query_or_reference(
        self, record: dict, index: int, ctx: SignalCollectionContext
    ) -> str:
        if not isinstance(record, dict):
            return f"TikTok Creative Center record {index}"
        return str(
            record.get("query_or_reference")
            or record.get("filter")
            or record.get("panel")
            or f"TikTok Creative Center record {index}"
        )

    def record_to_signal(
        self,
        record: dict,
        *,
        signal_id: str,
        collected_at: str,
        query_or_reference: str,
        ctx: SignalCollectionContext,
    ) -> Signal:
        if not isinstance(record, dict):
            raise CollectorError(f"tiktok capture record for {signal_id} is not a mapping")

        missing = [k for k in _REQUIRED_FIELDS if _blank(record.get(k))]
        if missing:
            raise CollectorError(
                f"tiktok capture record for {signal_id} is missing required field(s) "
                f"{missing} (spec §6.5)"
            )

        panel = str(record["panel"]).strip()
        source = f"TikTok Creative Center — {panel}"
        observed_at = _observed_at(record.get("observed_at"))
        url = _opt(record, "url")

        payload = {
            "signal_id": signal_id,
            "schema_version": "1.0.0",
            "run_id": ctx.run_id,
            "source": source,
            "source_type": SourceType.TIKTOK_CREATIVE_CENTER.value,
            "observed_at": observed_at,
            "collected_at": collected_at,
            "market": str(record["market"]),
            "language": str(record["language"]),
            "platform": str(record.get("platform") or _DEFAULT_PLATFORM),
            "signal_type": str(record["signal_type"]),
            "evidence": str(record["evidence"]),
            "raw_ref": raw_ref_for(ctx.run_id, signal_id),
            "context": str(record["context"]),
            "confidence": str(record["confidence"]),
            "provenance": {
                "source": source,
                "source_type": SourceType.TIKTOK_CREATIVE_CENTER.value,
                "observed_at": observed_at,
                "collected_at": collected_at,
                "query_or_reference": query_or_reference,
                "capture_method": CaptureMethod.ANALYST_CAPTURE.value,
                "url": url,
            },
        }
        if url is not None:
            payload["url"] = url
        for key in _PASSTHROUGH_OPTIONAL:
            value = record.get(key)
            if value is not None:
                payload[key] = value  # preserved as-is — no transformation (spec §6.3, G05)

        try:
            return decode(Signal, payload)
        except CodecError as e:
            raise CollectorError(
                f"tiktok capture record for {signal_id} is not a valid Signal: {e}"
            ) from e


register_default(TikTokCreativeCenterCollector())
