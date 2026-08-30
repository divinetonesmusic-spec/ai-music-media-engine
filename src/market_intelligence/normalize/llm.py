"""Claude-assisted Signal Normalization (spec §18 component 2, §19, §22).

Claude may only **disambiguate** four under-specified fields — ``signal_type``,
``market``, ``language``, ``durability_hint`` — on signals SN-1 already validated
and deduplicated. It never touches ``evidence`` / ``provenance`` / ``source`` /
``observed_at`` / ``collected_at`` / ``raw_ref`` / ``metrics`` / ``signal_id``,
never invents a fact, and cannot add or remove a signal. Every model response is
validated deterministically before any change is applied; anything unexpected is
rejected and the signal keeps its original (conservative) values.

Replay (§22): ``replay.enabled`` and ``replay.llm != "live"`` reads recorded
responses from ``<fixture_path>/llm/normalization/<signal_id>.json`` — no network.
``replay.llm == "live"`` calls the model. A missing recorded fixture degrades
that signal (its fields stay as they were); the network is never a fallback.
"""

from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

from ..io_utils import LoadError, read_json
from ..schema.models import RunConfig, Signal
from ..schema.validate import validate_signal
from .dedup import NormalizationError
from .deterministic import NormalizationResult

# The only fields Claude is allowed to fill, and the V1 taxonomy each must obey.
_NORMALISABLE_FIELDS = ("signal_type", "market", "language", "durability_hint")
_ALLOWED_TOP_KEYS = {"signal_id", "suggestions", "rationale", "confidence"}
_LLM_CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
_MAX_TOKENS = 2000

# Values a collector uses as a placeholder (not a considered classification) —
# these count as "under-specified" and are open for Claude to refine.
_COLLECTOR_DEFAULT_SIGNAL_TYPE = {"youtube": "content_format"}  # spec §6.5 TECHNICAL DEFAULT


def _markets() -> set:
    from ..schema.enums import Market

    return {m.value for m in Market} | {"UNKNOWN"}


def _languages() -> set:
    return {"pt", "es", "en", "UNKNOWN"}


def _signal_types() -> set:
    from ..schema.enums import SignalType

    return {s.value for s in SignalType}


def _durabilities() -> set:
    from ..schema.enums import Durability

    return {d.value for d in Durability}


class ResponseRejected(Exception):
    """A model response is malformed, out of taxonomy, or tries to touch a forbidden field."""


class MissingFixtureError(NormalizationError):
    """Recorded replay is on but no fixture exists for this signal (never fall back to network)."""


# --- result types -----------------------------------------------------

@dataclass
class FieldSuggestion:
    field: str
    from_value: Optional[str]  # the signal's value before normalization
    to_value: Optional[str]    # the model's proposal
    applied: bool              # False when the proposal was a no-op or rejected


@dataclass
class NormalizationChange:
    signal_id: str
    suggestions: List[FieldSuggestion]   # what the model proposed
    preserved_fields: List[str]          # under-specified fields left as-is
    rationale: str                       # short, from the model
    llm_confidence: Optional[str]        # LOW / MEDIUM / HIGH, or None
    applied: bool                        # any suggestion actually changed the signal
    rejection_reason: Optional[str]      # set when the whole response was rejected / unavailable


@dataclass
class LlmNormalizationResult:
    signals: List[Signal]                # normalized set, same order as the input
    changes: List[NormalizationChange]   # one per input signal — the traceability record
    replay: bool
    llm_mode: str                        # "live" | "recorded"


# --- the client -----------------------------------------------------

class NormalizationClient:
    """Protocol: classify one signal's ambiguous fields. Returns the raw model response."""

    def classify(
        self, signal_id: str, *, context: dict, ambiguous_fields: List[str], model: str
    ) -> dict:  # pragma: no cover - interface
        raise NotImplementedError


class RecordedNormalizationClient(NormalizationClient):
    """Reads ``<fixture_dir>/<signal_id>.json`` — never any network (spec §22)."""

    def __init__(self, fixture_dir: Path):
        self._dir = Path(fixture_dir)

    def classify(self, signal_id, *, context, ambiguous_fields, model) -> dict:
        path = self._dir / f"{signal_id}.json"
        if not path.is_file():
            raise MissingFixtureError(
                f"recorded replay: no normalization fixture at {path} (spec §22)"
            )
        try:
            return read_json(path)
        except LoadError as e:
            raise ResponseRejected(str(e)) from e


class AnthropicNormalization(NormalizationClient):
    """Live implementation — one structured-output call per signal (Anthropic SDK)."""

    def __init__(self, *, client=None, api_key: Optional[str] = None):
        self._client = client
        self._api_key = api_key

    def _build_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover - installed in dev
            raise NormalizationError("normalization needs the 'anthropic' package") from e
        if not (
            self._api_key
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        ):
            raise NormalizationError(
                "normalization: no Anthropic credentials (set ANTHROPIC_API_KEY) — spec §20.2"
            )
        return anthropic.Anthropic(api_key=self._api_key)

    def classify(self, signal_id, *, context, ambiguous_fields, model) -> dict:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise NormalizationError("normalization needs the 'anthropic' package") from e
        client = self._build_client()
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=_MAX_TOKENS,
                messages=[{"role": "user", "content": _prompt(context, ambiguous_fields)}],
                output_config={"format": {"type": "json_schema", "schema": _response_schema()}},
            )
        except anthropic.APIError as e:
            raise NormalizationError(f"normalization API call failed: {e}") from e
        text = next((b.text for b in msg.content if getattr(b, "type", None) == "text"), "")
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ResponseRejected(f"model returned non-JSON: {e}") from e


def _response_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["signal_id", "suggestions", "rationale"],
        "properties": {
            "signal_id": {"type": "string"},
            "suggestions": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "signal_type": {"type": "string", "enum": sorted(_signal_types())},
                    "market": {"type": "string", "enum": sorted(_markets())},
                    "language": {"type": "string", "enum": sorted(_languages())},
                    # A union `type` array (["string", "null"]) is rejected by the
                    # Anthropic output_config json_schema validator; `anyOf` with an
                    # explicit null branch is the supported nullable form (verified
                    # 2026-08-30). durability_hint stays optional (not in `required`).
                    "durability_hint": {
                        "anyOf": [
                            {"type": "string", "enum": sorted(_durabilities())},
                            {"type": "null"},
                        ],
                    },
                },
            },
            "rationale": {"type": "string"},
            "confidence": {"type": "string", "enum": sorted(_LLM_CONFIDENCE)},
        },
    }


def _prompt(context: dict, ambiguous_fields: List[str]) -> str:
    return (
        "You are normalising ONE market-intelligence signal. Fill ONLY the fields in "
        "`ambiguous_fields`, and ONLY from what this signal's evidence and context actually "
        "show. If the evidence does not clearly determine a field, omit it (leave it UNKNOWN). "
        "Do not restate or change any other field. Never invent facts, dates, URLs or "
        "evidence.\n\n"
        "market ∈ {Brasil, Mercados hispanohablantes, English-speaking markets, UNKNOWN}\n"
        "language ∈ {pt, es, en, UNKNOWN}\n"
        f"signal_type ∈ {sorted(_signal_types())}\n"
        "durability_hint ∈ {EPHEMERAL, EMERGING, STRUCTURAL, EVERGREEN} (omit if unclear)\n\n"
        f"ambiguous_fields: {ambiguous_fields}\n"
        f"signal: {json.dumps(context, ensure_ascii=False)}\n\n"
        'Return {"signal_id", "suggestions": {only the ambiguous fields you can determine}, '
        '"rationale": "<one sentence>", "confidence": "LOW|MEDIUM|HIGH"}.'
    )


# --- deterministic validation of a response --------------------------

def validate_llm_response(
    response, *, signal_id: str, ambiguous_fields: Sequence[str]
) -> "tuple[dict, str, Optional[str]]":
    """Return (clean_suggestions, rationale, confidence) or raise ``ResponseRejected``."""
    if not isinstance(response, dict):
        raise ResponseRejected("response is not an object")

    extra = set(response) - _ALLOWED_TOP_KEYS
    if extra:
        raise ResponseRejected(f"response has forbidden top-level key(s): {sorted(extra)}")
    if response.get("signal_id") != signal_id:
        raise ResponseRejected(
            f"signal_id mismatch: {response.get('signal_id')!r} != {signal_id!r}"
        )

    suggestions = response.get("suggestions")
    if suggestions is None:
        suggestions = {}
    if not isinstance(suggestions, dict):
        raise ResponseRejected("suggestions is not an object")

    bad = set(suggestions) - set(_NORMALISABLE_FIELDS)
    if bad:
        raise ResponseRejected(f"suggestions has forbidden key(s): {sorted(bad)}")
    non_ambiguous = set(suggestions) - set(ambiguous_fields)
    if non_ambiguous:
        raise ResponseRejected(
            f"suggestion for non-ambiguous field(s): {sorted(non_ambiguous)}"
        )

    for f, v in suggestions.items():
        if f == "signal_type" and v not in _signal_types():
            raise ResponseRejected(f"invalid signal_type {v!r}")
        if f == "market" and v not in _markets():
            raise ResponseRejected(f"invalid market {v!r}")
        if f == "language" and v not in _languages():
            raise ResponseRejected(f"invalid language {v!r}")
        if f == "durability_hint" and v is not None and v not in _durabilities():
            raise ResponseRejected(f"invalid durability_hint {v!r}")

    confidence = response.get("confidence")
    if confidence is not None and confidence not in _LLM_CONFIDENCE:
        raise ResponseRejected(f"invalid confidence {confidence!r}")

    return dict(suggestions), str(response.get("rationale") or "").strip(), confidence


# --- ambiguity + safe application -------------------------------

def ambiguous_fields(sig: Signal) -> List[str]:
    from ..schema.enums import SignalType

    out: List[str] = []
    st_value = sig.signal_type.value
    if st_value == SignalType.OTHER.value or (
        _COLLECTOR_DEFAULT_SIGNAL_TYPE.get(sig.source_type.value) == st_value
    ):
        out.append("signal_type")
    if sig.market == "UNKNOWN":
        out.append("market")
    if sig.language == "UNKNOWN":
        out.append("language")
    if sig.durability_hint is None:
        out.append("durability_hint")
    return out


def _current(sig: Signal, field_name: str) -> Optional[str]:
    if field_name == "signal_type":
        return sig.signal_type.value
    if field_name == "market":
        return sig.market
    if field_name == "language":
        return sig.language
    if field_name == "durability_hint":
        return sig.durability_hint.value if sig.durability_hint else None
    raise NormalizationError(f"not a normalisable field: {field_name!r}")


def _coerce(field_name: str, value):
    from ..schema.enums import Durability, SignalType

    if field_name == "signal_type":
        return SignalType(value)
    if field_name == "durability_hint":
        return Durability(value) if value is not None else None
    return value  # market / language are plain strings on the model


def _is_meaningful(field_name: str, value, current: Optional[str]) -> bool:
    if value == current:
        return False
    if field_name in ("market", "language") and value == "UNKNOWN":
        return False
    if field_name == "durability_hint" and value is None:
        return False
    return True


def _apply(sig: Signal, ambiguous: List[str], clean: dict):
    kwargs = {}
    suggestion_log: List[FieldSuggestion] = []
    preserved: List[str] = []

    for f in ambiguous:
        if f not in clean:
            preserved.append(f)
            continue
        current = _current(sig, f)
        if _is_meaningful(f, clean[f], current):
            kwargs[f] = _coerce(f, clean[f])
            suggestion_log.append(FieldSuggestion(f, current, clean[f], applied=True))
        else:
            preserved.append(f)
            suggestion_log.append(FieldSuggestion(f, current, clean[f], applied=False))

    if not kwargs:
        return sig, suggestion_log, preserved, False, None

    new_sig = dataclasses.replace(sig, **kwargs)
    errs = validate_signal(new_sig)
    if errs:
        reason = "applying the suggestion broke validation: " + "; ".join(e.code for e in errs)
        for s in suggestion_log:
            s.applied = False
        return sig, suggestion_log, list(ambiguous), False, reason
    return new_sig, suggestion_log, preserved, True, None


# --- the pass ------------------------------------------------------

def _context(sig: Signal, ambiguous: List[str]) -> dict:
    return {
        "signal_id": sig.signal_id,
        "evidence": sig.evidence,
        "context": sig.context,
        "source": sig.source,
        "current": {
            "signal_type": sig.signal_type.value,
            "market": sig.market,
            "language": sig.language,
            "platform": sig.platform.value,
            "observed_at": sig.observed_at,
            "durability_hint": sig.durability_hint.value if sig.durability_hint else None,
        },
        "ambiguous_fields": list(ambiguous),
    }


def _select_client(
    config: RunConfig, project_root: Path, client: Optional[NormalizationClient]
):
    if config.replay.enabled and (config.replay.llm or "recorded") != "live":
        fp = config.replay.fixture_path
        if not fp:
            raise NormalizationError("replay is enabled but replay.fixture_path is not set")
        base = Path(fp)
        base = base if base.is_absolute() else Path(project_root) / base
        return RecordedNormalizationClient(base / "llm" / "normalization"), "recorded"
    return (client or AnthropicNormalization()), "live"


def normalize_with_llm(
    signals: Union[NormalizationResult, Sequence[Signal]],
    *,
    config: RunConfig,
    project_root: Union[str, Path],
    client: Optional[NormalizationClient] = None,
) -> LlmNormalizationResult:
    if isinstance(signals, NormalizationResult):
        signals = signals.deduplicated_signals
    signals = list(signals)

    active, mode = _select_client(config, Path(project_root), client)

    out_signals: List[Signal] = []
    changes: List[NormalizationChange] = []

    for sig in signals:
        ambiguous = ambiguous_fields(sig)
        if not ambiguous:
            out_signals.append(sig)
            changes.append(NormalizationChange(
                sig.signal_id, [], [], "no ambiguous fields", None, False, None,
            ))
            continue

        try:
            raw = active.classify(
                sig.signal_id, context=_context(sig, ambiguous),
                ambiguous_fields=ambiguous, model=config.model,
            )
            clean, rationale, confidence = validate_llm_response(
                raw, signal_id=sig.signal_id, ambiguous_fields=ambiguous,
            )
        except (ResponseRejected, NormalizationError) as e:
            out_signals.append(sig)
            changes.append(NormalizationChange(
                sig.signal_id, [], list(ambiguous), "", None, False, str(e),
            ))
            continue

        new_sig, sugg_log, preserved, applied, reject = _apply(sig, ambiguous, clean)
        out_signals.append(new_sig)
        changes.append(NormalizationChange(
            signal_id=sig.signal_id,
            suggestions=sugg_log,
            preserved_fields=preserved,
            rationale=rationale,
            llm_confidence=confidence,
            applied=applied,
            rejection_reason=reject,
        ))

    return LlmNormalizationResult(
        signals=out_signals, changes=changes, replay=bool(config.replay.enabled), llm_mode=mode,
    )
