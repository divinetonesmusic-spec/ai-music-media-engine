"""Signal Normalization (docs/TECHNICAL-SPEC-V1.md §18 component 2, §6.6).

SN-1 — the **deterministic** part only:

* validate every ``Signal`` with the existing validators (§6.3); an invalid
  signal is removed from the output and its reason recorded — never auto-corrected;
* deduplicate using the key and rules defined **entirely** in ``config/dedup.yaml``
  (§6.6): same key + same ``observed_at`` day → duplicates; keep the higher
  ``confidence`` (tie → lower ``signal_id``); merge only the *absent* ``metrics``
  keys from a dropped signal; different source / observation stay separate.

SN-2 — the **Claude** step (``normalize.llm``): disambiguate only the
under-specified ``signal_type`` / ``market`` / ``language`` / ``durability_hint``
fields; every model response is validated deterministically before any change is
applied, and a signal keeps its original (conservative) values otherwise. No
files are written and no input is mutated.
"""

from .dedup import DedupReason, NormalizationError, dedup_key, deduplicate
from .deterministic import (
    InvalidSignal,
    NormalizationResult,
    normalize_deterministic,
    signals_from_collected,
)
from .llm import (
    AnthropicNormalization,
    FieldSuggestion,
    LlmNormalizationResult,
    MissingFixtureError,
    NormalizationChange,
    NormalizationClient,
    RecordedNormalizationClient,
    ResponseRejected,
    ambiguous_fields,
    normalize_with_llm,
    validate_llm_response,
)

__all__ = [
    "DedupReason",
    "NormalizationError",
    "dedup_key",
    "deduplicate",
    "InvalidSignal",
    "NormalizationResult",
    "normalize_deterministic",
    "signals_from_collected",
    "AnthropicNormalization",
    "FieldSuggestion",
    "LlmNormalizationResult",
    "MissingFixtureError",
    "NormalizationChange",
    "NormalizationClient",
    "RecordedNormalizationClient",
    "ResponseRejected",
    "ambiguous_fields",
    "normalize_with_llm",
    "validate_llm_response",
]
