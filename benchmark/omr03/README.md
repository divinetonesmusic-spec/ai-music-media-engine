# OMR-03 — Normalization Benchmark (isolated harness)

Governing decisions: `knowledge/DECISIONS-NEEDED.md` — OMR-01 (adapter), OMR-02
(routing policy), OMR-03 (Threshold Policy V1, commit `ca95573`).

**Not part of the pipeline.** Nothing in `src/market_intelligence/` or
`src/cluster_strategy/` imports anything under `benchmark/`. This directory is
outside `pyproject.toml`'s `packages.find` scope and is not installed.

- `harness.py` — calls Claude (`AnthropicNormalization`, unmodified) and Groq
  (`OmniRouteStageClient`, unmodified, OMR-01) with the exact same task
  (reused `_prompt`/`_response_schema`/`validate_llm_response` from
  `market_intelligence.normalize.llm`), writes results to `results/`.
- `metrics.py` — pure, network-free metrics (accuracy, verdicts, severity,
  sensitivity table). Fully unit tested.
- `analysis.py` — turns a results file + `ground_truth/` into the metrics above.
- `dataset/` — the versioned benchmark cases (`manifest.json` + `cases/*.json`).
- `ground_truth/` — per-case, per-field ground truth, frozen before any live call.
- `results/` — raw output of live runs (safe: grepped clean of API keys/secrets).
- `tests/` — mocked/offline tests (`pytest benchmark/omr03/tests -q`). Not part
  of the main `pytest -q` collection from the repo root.
- `REPORT.md` — the full benchmark report for the run in `results/`.

**Read `REPORT.md` first.** Its conclusion is **D — INCONCLUSIVE**: the dataset
is far below the size needed for the pre-registered thresholds to mean
anything, ground truth is single-reviewer AI self-review (not independent
human review), and the Claude baseline failed on every call this run due to an
Anthropic account billing issue (not a quality signal). The harness itself
works end-to-end and is reusable once a larger dataset and independent ground
truth exist.

## Running it again

```bash
# offline, no network, no OmniRoute needed:
.venv/bin/python -m pytest benchmark/omr03/tests -q

# live (real calls, real cost, real OmniRoute):
omniroute serve &                 # wait for readiness
env ANTHROPIC_API_KEY="$(security find-generic-password \
    -a ANTHROPIC_API_KEY -s ai-music-media-engine -w)" \
  .venv/bin/python benchmark/omr03/harness.py
omniroute stop
```

No production file, `RunConfig`, `ReplayConfig`, `StageClient`,
`select_stage_client()`, `select_*_client()` in `normalize/llm.py`, Cluster
Strategy, Musical DNA, or value-engine weighting is touched by any of this.
