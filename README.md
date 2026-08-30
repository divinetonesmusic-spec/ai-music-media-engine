# AI Music Media Engine

An intelligent content-growth system for a wellness instrumental-music business.
See [`CLAUDE.md`](CLAUDE.md) for the operational specification and
[`docs/TECHNICAL-SPEC-V1.md`](docs/TECHNICAL-SPEC-V1.md) for the V1 implementation spec.

**Current phase: V1 — Market Intelligence + Opportunity Analysis** (canonical
pipeline stages 1–2). Everything downstream (Cluster Strategy → Learning) is
future architecture and is not built yet.

## Status

The full V1 pipeline (canonical stages 1–2) is implemented and test-covered:

| Stage (spec §18) | Module | Claude / deterministic |
|---|---|---|
| Foundation — enums, models, codec, ids, §13 validators, config + Knowledge Loader, preflight | `schema.*`, `config.loader`, `knowledge_loader`, `preflight` | deterministic |
| 1. Signal Collection — 4 modular collectors, per-source degrade, replay | `collect.*` | web search = Claude; the rest deterministic |
| 2. Signal Normalization — validate + dedup (config-driven) + Claude disambiguation | `normalize.*` | mixed |
| 3. Analysis / Framing — signals → `Opportunity` candidates | `framing` | Claude framing + deterministic C1 / id / taxonomy checks |
| 4. Asset Matching — inventory candidates + fit judgement, no asset invented | `matching` | deterministic candidates/existence + Claude fit |
| 5. Evaluation — 10 dimensions + 5 outcome axes + red flags + recommendation | `evaluation`, `guardrails` | Claude rates + deterministic completeness / no-score / compliance |
| 6. Ranking — ordinal comparator from `config/ranking.yaml` (no numeric score) | `ranking` | deterministic |
| 7. Report Generation — 9-section report + JSON sidecar + `digest.md` + `review.md` | `reporting` | deterministic |
| Registry Updater — append-only `opportunity-registry.yaml` | `registry` | deterministic |
| Orchestrator + `run` CLI | `orchestrator`, `cli` | deterministic |

Downstream stages (Cluster Strategy → Learning) are future architecture and are **not** built.

## Development setup

Python 3.12 (`requires-python = ">=3.12,<3.13"`). Runtime deps: `PyYAML` and
`anthropic` (lazily imported — only needed for a live, non-replay run).
`pytest` + `ruff` for dev.

```bash
python3.12 -m venv .venv            # e.g. Homebrew: brew install python@3.12
./.venv/bin/python -m pip install -e ".[dev]"

./.venv/bin/python -m pytest          # run the test suite (no network)
./.venv/bin/ruff check src tests      # lint
```

## Running the pipeline

```bash
# validate config + knowledge base
./.venv/bin/python -m market_intelligence preflight config/run.example.yaml

# stage 1 only / stages 1–2 only
./.venv/bin/python -m market_intelligence collect   config/run.example.yaml
./.venv/bin/python -m market_intelligence normalize config/run.example.yaml

# the whole pipeline, fully offline against recorded fixtures (no network, no API keys)
./.venv/bin/python -m market_intelligence run config/run.pipeline.replay.example.yaml
```

A live run reads `ANTHROPIC_API_KEY` (and `YOUTUBE_API_KEY` for the YouTube
collector) from the environment — never from config or the repo. Reports land in
`reports/<run_id>/`; the run appends `knowledge/market/opportunity-registry.yaml`
(review the `git diff`).

## Layout

```
config/       run config template + ranking / dedup constants (data, not code)
knowledge/    human-owned source of truth — read-only to the pipeline
              (except knowledge/market/opportunity-registry.yaml, append-only)
src/market_intelligence/   the pipeline
tests/        pytest suite (TDD); tests/fixtures/ holds canonical valid entities
data/         generated, regenerable — git-ignored
reports/      generated, durable, versioned
```

## Engineering notes

- Deterministic code decides *whether output is well-formed, traceable and within
  V1 rules*; Claude decides *what is true and how strong it is* (spec §19).
- Every Claude stage takes an injectable client and supports a recorded-replay
  mode (`<fixture_path>/llm/<stage>/<key>.json`), so the whole pipeline is
  testable offline; no test touches the network.
- No composite 0–100 score (C6); no invented assets (I1); V1 lifecycle states are
  `EXPLORE` / `TEST` / `PARK`; the system only recommends (autonomy Level 1, CLAUDE.md §13).
- No database, queue or server (I10). Persistence is YAML + Markdown + JSON.
