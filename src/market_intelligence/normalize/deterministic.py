"""The deterministic Signal Normalization pass (spec §6.3, §6.6, §18).

``normalize_deterministic`` validates every signal, drops the invalid ones (with
their reasons), then deduplicates. It does **not** call Claude, write files, or
mutate its inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

from ..io_utils import LoadError, read_json
from ..schema.codec import CodecError, decode
from ..schema.models import Signal
from ..schema.validate import ValidationError, validate_signal
from .dedup import DedupReason, NormalizationError, deduplicate

SignalsInput = Union[Sequence[Signal], str, Path]


@dataclass
class InvalidSignal:
    signal_id: str
    errors: List[dict]  # [{code, path, message}] — recorded, never fixed


@dataclass
class NormalizationResult:
    valid_signals: List[Signal]         # passed validation (pre-dedup), ordered by signal_id
    invalid_signals: List[InvalidSignal]
    deduplicated_signals: List[Signal]  # the deterministic normalized set
    discarded_signal_ids: List[str]     # dropped by dedup
    dedup_reasons: List[DedupReason]


def signals_from_collected(path: Union[str, Path]) -> List[Signal]:
    """Load the ``Signal`` list out of a ``data/<run_id>/signals/collected.json`` manifest."""
    try:
        data = read_json(Path(path))
    except LoadError as e:
        raise NormalizationError(str(e)) from e
    if not isinstance(data, dict) or not isinstance(data.get("signals"), list):
        raise NormalizationError(f"{path} is not a collected.json manifest (no 'signals' list)")
    try:
        return [decode(Signal, s) for s in data["signals"]]
    except CodecError as e:
        raise NormalizationError(f"{path} has a malformed signal: {e}") from e


def normalize_deterministic(
    signals: SignalsInput,
    *,
    dedup_config: dict,
    raw_root: Optional[Path] = None,
) -> NormalizationResult:
    if isinstance(signals, (str, Path)):
        signals = signals_from_collected(signals)
    signals = list(signals)

    valid: List[Signal] = []
    invalid: List[InvalidSignal] = []
    seen: set = set()

    for sig in signals:
        errs = list(validate_signal(sig, raw_root=raw_root))
        if sig.signal_id in seen:
            errs.append(ValidationError(
                "signal.duplicate_id", sig.signal_id,
                "signal_id is not unique within the run (spec §6.3)",
            ))
        seen.add(sig.signal_id)

        if errs:
            invalid.append(InvalidSignal(
                signal_id=sig.signal_id,
                errors=[{"code": e.code, "path": e.path, "message": e.message} for e in errs],
            ))
        else:
            valid.append(sig)

    deduped, discarded, reasons = deduplicate(valid, dedup_config)

    valid.sort(key=lambda s: s.signal_id)
    invalid.sort(key=lambda iv: iv.signal_id)
    return NormalizationResult(
        valid_signals=valid,
        invalid_signals=invalid,
        deduplicated_signals=deduped,
        discarded_signal_ids=discarded,
        dedup_reasons=reasons,
    )
