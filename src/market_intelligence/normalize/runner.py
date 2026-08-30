"""Signal Normalization entry point (spec §18 component 2, §6.7).

``run_normalization`` closes stage 2 end to end: take the collected signals →
``normalize_deterministic`` (SN-1: validate, drop invalid, dedup) →
``normalize_with_llm`` (SN-2: Claude disambiguates the four under-specified
fields) → write a run manifest. It does **not** run Opportunity Analysis or
anything downstream.

The manifest ``data/<run_id>/signals/normalized.json`` is a run artifact, not a
new business entity: it carries the final ``Signal`` list plus the full trace
(invalid signals, dedup decisions, LLM changes). Given a fixed input and replay
mode it is byte-reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

from ..config.loader import load_dedup_config
from ..io_utils import write_json
from ..schema.codec import encode
from ..schema.models import RunConfig, Signal
from .deterministic import (
    NormalizationResult,
    normalize_deterministic,
    signals_from_collected,
)
from .llm import LlmNormalizationResult, NormalizationClient, normalize_with_llm

MANIFEST_SCHEMA_VERSION = "1.0.0"

SignalsInput = Union[Sequence[Signal], str, Path]


@dataclass
class NormalizationRunResult:
    signals: List[Signal]                # the final normalized set (post SN-1 + SN-2)
    deterministic: NormalizationResult
    llm: LlmNormalizationResult
    manifest_path: Path


def normalized_path(cfg: RunConfig, project_root: Union[str, Path]) -> Path:
    return Path(project_root) / cfg.paths.data_dir / cfg.run_id / "signals" / "normalized.json"


def run_normalization(
    signals: SignalsInput,
    *,
    config: RunConfig,
    project_root: Union[str, Path],
    dedup_config: Optional[dict] = None,
    client: Optional[NormalizationClient] = None,
) -> NormalizationRunResult:
    """Run Signal Normalization and persist ``data/<run_id>/signals/normalized.json``.

    ``signals`` may be an in-memory ``Signal`` list or a path to a
    ``collected.json`` manifest. ``dedup_config`` defaults to ``config/dedup.yaml``.
    ``client`` is the injectable SN-2 model client (ignored in recorded replay).
    """
    root = Path(project_root)
    if isinstance(signals, (str, Path)):
        signals = signals_from_collected(signals)
    signals = list(signals)

    if dedup_config is None:
        dedup_config = load_dedup_config(project_root=root)

    det = normalize_deterministic(signals, dedup_config=dedup_config)
    llm = normalize_with_llm(det, config=config, project_root=root, client=client)

    path = normalized_path(config, root)
    path.parent.mkdir(parents=True, exist_ok=True)  # runtime structure only
    write_json(path, build_manifest(config, det, llm))
    return NormalizationRunResult(
        signals=llm.signals, deterministic=det, llm=llm, manifest_path=path
    )


def build_manifest(
    cfg: RunConfig, det: NormalizationResult, llm: LlmNormalizationResult
) -> dict:
    ordered = sorted(llm.signals, key=lambda s: s.signal_id)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": cfg.run_id,
        "replay": llm.replay,
        "llm_mode": llm.llm_mode,
        "signal_count": len(ordered),
        "signal_ids": [s.signal_id for s in ordered],
        "signals": [encode(s) for s in ordered],
        "invalid_signals": [
            {"signal_id": iv.signal_id, "errors": iv.errors} for iv in det.invalid_signals
        ],
        "discarded_signal_ids": list(det.discarded_signal_ids),
        "dedup_reasons": [
            {
                "kept": r.kept,
                "dropped": r.dropped,
                "dedup_key": r.dedup_key,
                "observed_at": r.observed_at,
                "merged_metric_keys": list(r.merged_metric_keys),
            }
            for r in det.dedup_reasons
        ],
        "llm_changes": [_encode_change(c) for c in llm.changes],
    }


def _encode_change(c) -> dict:
    return {
        "signal_id": c.signal_id,
        "suggestions": [
            {
                "field": s.field,
                "from": s.from_value,
                "to": s.to_value,
                "applied": s.applied,
            }
            for s in c.suggestions
        ],
        "preserved_fields": list(c.preserved_fields),
        "rationale": c.rationale,
        "llm_confidence": c.llm_confidence,
        "applied": c.applied,
        "rejection_reason": c.rejection_reason,
    }
