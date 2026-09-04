"""OMR-03 Normalization Benchmark — harness (I/O layer: live model calls).

Isolated on purpose (decision OMR-01/OMR-02 precedent): imports
``market_intelligence.normalize.llm`` and ``external_llm_gateway`` — never the
reverse. No production file is modified, no ``select_*_client()`` is touched, no
pipeline stage is connected to this harness. The ONLY effect of running this
module is: (a) two real HTTP calls per dataset case (one to Anthropic, one to
OmniRoute/Groq) and (b) a results JSON file written under
``benchmark/omr03/results/``.

Reuses the pipeline's OWN prompt/schema/validator (``_prompt``, ``_response_schema``,
``validate_llm_response``) so both providers are judged by literally the same
deterministic rules Normalization already enforces in production — no benchmark-only
leniency, no benchmark-only strictness.

Credentials: read from the environment exactly like production code does
(``ANTHROPIC_API_KEY`` for Claude, nothing required for a local OmniRoute instance
with ``REQUIRE_API_KEY=false``). This module never reads, logs, or persists a key.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from external_llm_gateway.config import OmniRouteConfig
from external_llm_gateway.omniroute_client import OmniRouteStageClient
from market_intelligence.llm_stage import ResponseRejected as StageResponseRejected
from market_intelligence.llm_stage import StageError
from market_intelligence.normalize.llm import (
    AnthropicNormalization,
    NormalizationClient,
    NormalizationError,
    _context,
    _prompt,
    _response_schema,
    validate_llm_response,
)
from market_intelligence.normalize.llm import ResponseRejected as NormResponseRejected
from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import Signal

HERE = Path(__file__).resolve().parent
DATASET_DIR = HERE / "dataset" / "cases"
GROUND_TRUTH_DIR = HERE / "ground_truth"
RESULTS_DIR = HERE / "results"

CLAUDE_MODEL = "claude-sonnet-5"
GROQ_MODEL = "groq/openai/gpt-oss-120b"
OMNIROUTE_BASE_URL = "http://localhost:20128/v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CallOutcome:
    """One provider's attempt at one case. Exactly one of (suggestions,
    technical_error, rejected_reason) is set on a well-formed outcome.
    """

    provider: str
    model: str
    case_id: str
    latency_s: float
    timestamp: str
    suggestions: Optional[dict] = None
    rationale: Optional[str] = None
    confidence: Optional[str] = None
    technical_error: Optional[str] = None
    rejected_reason: Optional[str] = None
    raw_response_safe: Optional[dict] = None


def load_dataset() -> List[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(DATASET_DIR.glob("*.json"))]


def load_ground_truth(case_id: str) -> dict:
    return json.loads((GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))


def signal_from_case(case: dict) -> Signal:
    return decode(Signal, case["signal"])


def call_claude(
    signal: Signal, ambiguous: List[str], *, client: Optional[NormalizationClient] = None
) -> CallOutcome:
    ctx = _context(signal, ambiguous)
    active = client or AnthropicNormalization()
    t0 = time.monotonic()
    ts = _now_iso()
    try:
        raw = active.classify(
            signal.signal_id, context=ctx, ambiguous_fields=ambiguous, model=CLAUDE_MODEL
        )
    except NormalizationError as e:
        return CallOutcome(
            "claude", CLAUDE_MODEL, signal.signal_id, time.monotonic() - t0, ts,
            technical_error=str(e),
        )
    except NormResponseRejected as e:
        return CallOutcome(
            "claude", CLAUDE_MODEL, signal.signal_id, time.monotonic() - t0, ts,
            rejected_reason=str(e),
        )
    latency = time.monotonic() - t0
    try:
        clean, rationale, confidence = validate_llm_response(
            raw, signal_id=signal.signal_id, ambiguous_fields=ambiguous
        )
    except NormResponseRejected as e:
        return CallOutcome(
            "claude", CLAUDE_MODEL, signal.signal_id, latency, ts,
            rejected_reason=str(e), raw_response_safe=raw,
        )
    return CallOutcome(
        "claude", CLAUDE_MODEL, signal.signal_id, latency, ts,
        suggestions=clean, rationale=rationale, confidence=confidence, raw_response_safe=raw,
    )


def _groq_prompt(context: dict, ambiguous: List[str]) -> str:
    """Same task prompt as production (`_prompt`), plus a textual schema
    instruction — OmniRouteStageClient does not send `schema` to the provider
    (documented limitation, docs/EXTERNAL-LLM-GATEWAY.md §10), so this is the
    only enforcement mechanism available for the Groq path. This asymmetry
    versus Claude's real structured-output enforcement is a limitation to
    report, not to hide.
    """
    return (
        _prompt(context, ambiguous)
        + "\n\nRespond with ONLY a single JSON object — no markdown fence, no "
        "prose before or after — matching exactly this JSON Schema:\n"
        + json.dumps(_response_schema())
    )


def call_groq(
    signal: Signal, ambiguous: List[str], *, client: Optional[OmniRouteStageClient] = None
) -> CallOutcome:
    ctx = _context(signal, ambiguous)
    prompt = _groq_prompt(ctx, ambiguous)
    active = client or OmniRouteStageClient(
        OmniRouteConfig(base_url=OMNIROUTE_BASE_URL, model=GROQ_MODEL)
    )
    t0 = time.monotonic()
    ts = _now_iso()
    try:
        raw = active.complete(
            stage="omr03-benchmark", key=signal.signal_id, prompt=prompt,
            schema=_response_schema(), model=GROQ_MODEL,
        )
    except StageError as e:
        return CallOutcome(
            "groq", GROQ_MODEL, signal.signal_id, time.monotonic() - t0, ts,
            technical_error=str(e),
        )
    except StageResponseRejected as e:
        return CallOutcome(
            "groq", GROQ_MODEL, signal.signal_id, time.monotonic() - t0, ts,
            rejected_reason=str(e),
        )
    latency = time.monotonic() - t0
    try:
        clean, rationale, confidence = validate_llm_response(
            raw, signal_id=signal.signal_id, ambiguous_fields=ambiguous
        )
    except NormResponseRejected as e:
        return CallOutcome(
            "groq", GROQ_MODEL, signal.signal_id, latency, ts,
            rejected_reason=str(e), raw_response_safe=raw,
        )
    return CallOutcome(
        "groq", GROQ_MODEL, signal.signal_id, latency, ts,
        suggestions=clean, rationale=rationale, confidence=confidence, raw_response_safe=raw,
    )


def run_all(*, claude_client=None, groq_client=None) -> dict:
    """Runs every dataset case through both providers — exactly once each, no
    retry, no fallback, no post-hoc case removal (OMR-03 policy).
    """
    results = []
    for case in load_dataset():
        signal = signal_from_case(case)
        ambiguous = case["case_metadata"]["ambiguous_fields"]
        claude_outcome = call_claude(signal, ambiguous, client=claude_client)
        groq_outcome = call_groq(signal, ambiguous, client=groq_client)
        results.append({
            "case_id": signal.signal_id,
            "ambiguous_fields": ambiguous,
            "claude": asdict(claude_outcome),
            "groq": asdict(groq_outcome),
        })
    return {
        "generated_at": _now_iso(),
        "claude_model": CLAUDE_MODEL,
        "groq_model": GROQ_MODEL,
        "omniroute_base_url": OMNIROUTE_BASE_URL,
        "results": results,
    }


def main() -> Path:
    run = run_all()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = run["generated_at"].replace(":", "").replace("-", "").replace(".", "")
    out_path = RESULTS_DIR / f"run_{run_id}.json"
    out_path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out_path}")
    return out_path


if __name__ == "__main__":
    main()
