# AI Music Media Engine

An intelligent content-growth system for a wellness instrumental-music business.
See [`CLAUDE.md`](CLAUDE.md) for the operational specification and
[`docs/TECHNICAL-SPEC-V1.md`](docs/TECHNICAL-SPEC-V1.md) for the V1 implementation spec.
[`docs/SESSION-STATE.md`](docs/SESSION-STATE.md) is the current-state snapshot.

**Current phase: V1 — Market Intelligence + Opportunity Analysis** (canonical
pipeline stages 1–2). Everything downstream (Cluster Strategy → Learning) is
future architecture and is not built yet.

V1 turns market signals into a small set of **prioritised, evidenced,
evaluated Opportunity Reports** an operator can act on. It only ever
*recommends* — autonomy Level 1 (CLAUDE.md §13). It never publishes, schedules,
creates an asset, or advances an opportunity; a human does that.

## What the operator can do

1. Configure a run (`config/*.yaml`).
2. Collect real market signals (Web Search / YouTube / TikTok capture / internal
   data) — or replay recorded ones, fully offline.
3. Normalize, frame into opportunities, match to existing assets, evaluate,
   rank, and generate reports + a run digest.
4. Read `reports/<run_id>/` and fill `review.md`.
5. Re-run; run offline via replay; diagnose failures; tell a *technical* failure
   apart from a *business* decision; check the C10 3-run gate.

## Pipeline (spec §18)

| Stage | Module | Claude / deterministic |
|---|---|---|
| Foundation — enums, models, codec, ids, §13 validators, config + Knowledge Loader, preflight | `schema.*`, `config.loader`, `knowledge_loader`, `preflight` | deterministic |
| 1. Signal Collection — 4 modular collectors, per-source degrade, replay | `collect.*` | web search = Claude; the rest deterministic |
| 2. Signal Normalization — validate + dedup (config-driven) + Claude disambiguation | `normalize.*` | mixed |
| 3. Analysis / Framing — signals → `Opportunity` candidates | `framing` | Claude framing + deterministic C1 / id / taxonomy checks |
| 4. Asset Matching — inventory candidates + fit judgement, no asset invented | `matching` | deterministic candidates/existence + Claude fit |
| 5. Evaluation — 10 dimensions + 5 outcome axes + red flags + recommendation | `evaluation`, `guardrails` | Claude rates + deterministic completeness / no-score / compliance |
| 6. Ranking — ordinal comparator from `config/ranking.yaml` (no numeric score) | `ranking` | deterministic |
| 7. Report Generation — 9-section report + JSON sidecar + `digest.md` + `review.md` | `reporting` | deterministic structure + Claude prose |
| Registry Updater — append-only `opportunity-registry.yaml` | `registry` | deterministic |
| Orchestrator + CLI | `orchestrator`, `cli` | deterministic |

Principle: **Claude decides *what is true and how strong it is*; deterministic
code decides *whether the output is well-formed, traceable, and within V1
rules*** (spec §19).

## Development setup

Python 3.12 (`requires-python = ">=3.12,<3.13"`). Runtime deps: `PyYAML` and
`anthropic` (lazily imported — only a live, non-replay run needs it).
`pytest` + `ruff` for dev.

```bash
python3.12 -m venv .venv            # e.g. Homebrew: brew install python@3.12
./.venv/bin/python -m pip install -e ".[dev]"

./.venv/bin/python -m pytest          # the full suite — no network
./.venv/bin/ruff check src tests      # lint
```

## Commands

```bash
# validate config + knowledge base
python -m market_intelligence preflight config/run.example.yaml

# stage 1 only / stages 1–2 only
python -m market_intelligence collect   config/run.example.yaml
python -m market_intelligence normalize config/run.example.yaml

# the whole pipeline, fully offline against recorded fixtures (no network, no keys)
python -m market_intelligence run config/run.pipeline.replay.example.yaml

# the C10 3-run Definition-of-Done gate, from the three review.md files
python -m market_intelligence gate --reports-dir reports/
python -m market_intelligence gate reports/run_a/review.md reports/run_b/review.md reports/run_c/review.md
```

Every command prints a `… OK` / `… FAILED` line and exits non-zero on failure.

## Live vs replay

| Mode | Set in config | Network / keys | Use |
|---|---|---|---|
| **Live** | `replay.enabled: false` (or `replay.llm: live`) | yes | real discovery against current data |
| **Replay (recorded)** | `replay.enabled: true`, `replay.llm: recorded`, `replay.fixture_path: …` | none | offline regression; deterministic |
| **dry_run** | `dry_run: true` | as above | stop after Framing (cheap iteration) |

`replay.llm` is **global** — it flips *every* Claude touchpoint (Web Search
structuring, Normalization, Framing, Matching, Evaluation) at once. Live and
replay never mix within a run. A replay run stamps `replay: true` on the digest,
`OpportunityProvenance.replay = true`, and `replay_origin: true` on each registry
entry — replay output is historical, **not** current-trend evidence.

## Credentials

A live run reads `ANTHROPIC_API_KEY` (and `YOUTUBE_API_KEY` for the YouTube
collector) from the **environment only** — never from config, a fixture, a log,
a report, or the repo. Error paths redact `sk-ant-…` and `key=…`.

For a live run without exporting the key into your shell, a Keychain wrapper is
available (kept out of the repo): `scripts/run-live.sh` reads the key from the
macOS Keychain (`security find-generic-password -s ai-music-media-engine -a
ANTHROPIC_API_KEY -w`) and passes it only to the Python child process.

```bash
security add-generic-password -s ai-music-media-engine -a ANTHROPIC_API_KEY -w
./scripts/run-live.sh run config/run.live-01.yaml
```

## Output layout

```
reports/<run_id>/
  digest.md            ranked table, parked list, excluded list (+ reasons),
                       technical-failures section, NEEDS_INPUT roll-up, config snapshot, timings
  review.md            owner fills this after reading the digest (spec §21.1)
  <opportunity_id>.md   the 9-section Opportunity Report (I4)
  <opportunity_id>.json structured mirror of the report

data/<run_id>/          regenerable — git-ignored
  signals/raw/<signal_id>.json   raw captures (replay reads these)
  signals/collected.json · signals/normalized.json
  opportunities.json    full structured records before rendering
  run.log               warnings, degradations, per-stage exclusions, technical failures

knowledge/market/opportunity-registry.yaml   append-only; the ONLY file under
                       knowledge/ the pipeline writes (governance exception, spec §17) —
                       review the git diff
```

## Technical failure ≠ business decision

If a stage fails on infrastructure — an API 400, a timeout, a truncated or
over-limit response — the affected opportunity is recorded as a **technical
failure**: it is *not* PARKed, *not* a business exclusion, and *never* written to
the registry. It appears in `run.log`, the digest's "Technical failures" section,
and the `run` command's output. If *every* opportunity fails a stage technically,
the run stops with a controlled error and the registry is left untouched.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `PREFLIGHT FAILED … missing` | a required knowledge file is absent — the message names it (spec §14). All four inventories + `business-dna.md` + `guardrails.yaml` + `cluster-taxonomy.md` must load. |
| `RUN FAILED … every configured signal source failed` | no source produced signals. In replay, check `replay.fixture_path` and that `signals/raw/*.json` exist. Live: check keys / network / the source-specific error in the output. |
| `RUN FAILED … Analysis / Framing could not run` | the Framing model call failed — the message carries `stop_reason` / an HTTP error / a `request_id`. `credit balance too low` = restore Anthropic credit. `truncated at the max_tokens cap` = the input was unusually large. |
| `RUN FAILED … Evaluation failed technically for all …` | every opportunity's Evaluation call failed (controlled stop — registry untouched). Check the first failure reason in the message. |
| `no fixture at …/llm/<stage>/<key>.json` | recorded replay with a missing fixture. Framing/Evaluation fixtures are keyed by a hash of the input; a config that re-mints signal ids will not match a captured fixture. Use the fixture-level tests or capture a fresh fixture with `replay.llm: live`. |
| `GATE INCOMPLETE` | one of the three `review.md` files has not been filled in by the owner. |
| model returns non-JSON with a `stop_reason` | the response was truncated / refused / empty — the error names which. Raise the stage's `max_tokens` if truncated; otherwise it is a model-side issue to retry. |

## Engineering notes

- Every Claude stage takes an injectable client and supports recorded replay
  (`<fixture_path>/llm/<stage>/<key>.json`), so the whole pipeline is testable
  offline; no test touches the network.
- Anthropic structured outputs: schemas stay inside the accepted subset (no union
  `type` arrays, `additionalProperties: false` on every object, no open maps) and
  small enough to compile to a bounded grammar (few optional fields). Responses
  are parsed robustly — `stop_reason`, block types, refusal and truncation are
  named, never a bare `json.loads` failure.
- No composite 0–100 score (C6); no invented assets (I1); V1 lifecycle states are
  `EXPLORE` / `TEST` / `PARK`; the system only recommends (Level 1, CLAUDE.md §13).
- No database, queue or server (I10). Persistence is YAML + Markdown + JSON.
- Reviewer agents live in `.claude/agents/` — spec-consistency, implementation-
  conformance, security, replay-integration, report-quality.
