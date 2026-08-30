"""Internal Data collector (spec §6.4, §6.5).

The operator maintains a YAML file (``RunConfig.internal_data_path``) — a list of
records, each becoming one ``Signal`` with ``source_type: internal_data`` and
``capture_method: internal_data``. Nothing is fetched or inferred: the record is
copied into the raw capture verbatim and mapped field-for-field.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ..io_utils import LoadError, read_yaml
from ..schema.codec import CodecError, decode
from ..schema.enums import CaptureMethod, SourceType
from ..schema.models import Signal
from .base import Collector, CollectorError, SignalCollectionContext, raw_ref_for, register_default

# The fields an internal-data record must carry (spec §6.4).
_REQUIRED_FIELDS = (
    "observed_at",
    "market",
    "language",
    "platform",
    "signal_type",
    "evidence",
    "context",
    "confidence",
)
_DEFAULT_SOURCE = "Internal business data"
_PASSTHROUGH_OPTIONAL = ("url", "raw_excerpt", "durability_hint", "metrics", "source_version")


class InternalDataCollector(Collector):
    source_type = SourceType.INTERNAL_DATA
    capture_method = CaptureMethod.INTERNAL_DATA

    def live_records(self, ctx: SignalCollectionContext) -> List[dict]:
        rel = ctx.config.internal_data_path
        if not rel:
            raise CollectorError(
                "internal_data is a signal source but internal_data_path is not set (spec §20.1)"
            )
        path = Path(rel)
        if not path.is_absolute():
            path = ctx.project_root / path
        if not path.exists():
            raise CollectorError(f"internal_data file not found: {path}")
        try:
            data = read_yaml(path)
        except LoadError as e:
            raise CollectorError(str(e)) from e
        if not isinstance(data, list) or not data:
            raise CollectorError(f"internal_data file must be a non-empty YAML list: {path}")
        return data

    def query_or_reference(
        self, record: dict, index: int, ctx: SignalCollectionContext
    ) -> str:
        return f"{ctx.config.internal_data_path} [record {index}]"

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
            raise CollectorError(f"internal_data record for {signal_id} is not a mapping")

        missing = [
            k for k in _REQUIRED_FIELDS
            if record.get(k) in (None, "") or not str(record.get(k)).strip()
        ]
        if missing:
            raise CollectorError(
                f"internal_data record for {signal_id} is missing required field(s) "
                f"{missing} (spec §6.4)"
            )

        source = str(record.get("source") or _DEFAULT_SOURCE)
        observed_at = str(record["observed_at"])
        payload = {
            "signal_id": signal_id,
            "schema_version": "1.0.0",
            "run_id": ctx.run_id,
            "source": source,
            "source_type": SourceType.INTERNAL_DATA.value,
            "observed_at": observed_at,
            "collected_at": collected_at,
            "market": str(record["market"]),
            "language": str(record["language"]),
            "platform": str(record["platform"]),
            "signal_type": str(record["signal_type"]),
            "evidence": str(record["evidence"]),
            "raw_ref": raw_ref_for(ctx.run_id, signal_id),
            "context": str(record["context"]),
            "confidence": str(record["confidence"]),
            "provenance": {
                "source": source,
                "source_type": SourceType.INTERNAL_DATA.value,
                "observed_at": observed_at,
                "collected_at": collected_at,
                "query_or_reference": query_or_reference,
                "capture_method": CaptureMethod.INTERNAL_DATA.value,
                "url": _opt(record, "url"),
                "source_version": _opt(record, "source_version"),
            },
        }
        for key in _PASSTHROUGH_OPTIONAL:
            if key == "source_version":
                continue
            value = record.get(key)
            if value is not None:
                payload[key] = value

        try:
            return decode(Signal, payload)
        except CodecError as e:
            raise CollectorError(
                f"internal_data record for {signal_id} is not a valid Signal: {e}"
            ) from e


def _opt(record: dict, key: str) -> Optional[str]:
    value = record.get(key)
    return None if value is None else str(value)


register_default(InternalDataCollector())
