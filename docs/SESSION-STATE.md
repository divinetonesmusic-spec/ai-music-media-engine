---
title: Session State — AI Music Media Engine
status: current
updated: "2026-08-28"
owner: Nicolas Alves (divinetonesmusic@gmail.com)
purpose: >
  Snapshot of the current project state so a new Claude Code session can resume
  work without the previous conversation history. Records the current state, not
  the full conversation log.
sources_of_truth:
  - CLAUDE.md
  - docs/TECHNICAL-SPEC-V1.md
  - knowledge/DECISIONS-NEEDED.md
  - knowledge/business-dna/business-dna.md
  - knowledge/business-dna/content-methodology.md
  - knowledge/clusters/cluster-taxonomy.md
  - knowledge/rules/guardrails.yaml
  - knowledge/inventories/*.yaml
---

# Session State

## Current Phase

**V1 — Market Intelligence + Opportunity Analysis.** The knowledge base and technical
specification are complete and reconciled. The **Foundation layer** is **committed**
(`37b0db4`, pushed to `origin/main`).

**The full V1 pipeline (canonical stages 1–2) is now implemented end-to-end and
UNCOMMITTED** (one working tree, owner authorized code 2026-08-28). It runs locally:
`python -m market_intelligence run <config>` executes
`preflight → Signal Collection → Signal Normalization → Analysis/Framing → Asset Matching
→ Evaluation → Ranking → Report Generation (+ digest + review + opportunities.json + run.log)
→ Registry update`, and `config/run.pipeline.replay.example.yaml` runs the whole thing
**offline** (recorded LLM fixtures, no network, no API keys).

- **Signal Collection** (`collect.*`): 4 modular collectors (`internal_data`, `web_search`
  = Claude server-side search, `youtube` = deterministic Data API, `tiktok` = deterministic
  analyst-capture file), per-source degrade, replay, `collected.json` manifest.
- **Signal Normalization** (`normalize.*`): SN-1 validate + config-driven dedup; SN-2 Claude
  disambiguation (injectable + recorded replay, deterministic response validation); SN-3
  `run_normalization` chains both and writes `data/<run_id>/signals/normalized.json`.
- **`llm_stage.py`**: shared injectable-client + recorded-replay plumbing for the 3 analysis
  stages — `RecordedStageClient` reads `<fixture_path>/llm/<stage>/<key>.json`,
  `AnthropicStageClient` reads creds from env and `redact()`s `sk-ant-…` from errors.
- **Framing** (`framing.py`): Claude frames signals → `FramedOpportunity`; deterministic
  enforces the 6 C1 fields, the `opportunity_id` hash (§7.1), §7.1a market/language, the
  canonical-cluster check, and evidence→signal resolution. Candidates that fail these are
  *flagged* in `run.log`, not turned into opportunities (§7.1).
- **Asset Matching** (`matching.py`): deterministic candidate generation from the real
  inventory (10 hero artists always candidates §10.2a; catalog affinity ≠ eligibility);
  Claude judges fit; `fit_basis` OBSERVED is downgraded to INFERRED unless a consolidated
  classification backs it; Claude cannot pick an asset outside the generated candidate set;
  `matching_catalog` is null in V1 (§10.3 "coarse in V1").
- **Guardrails** (`guardrails.py`): deterministic scan of `guardrails.yaml` for the explicit
  disease-claim constructions of G01/G03/G04 per `applies_to` scope; the Evaluation prompt
  now enumerates all of G01–G10 and asks Claude for a self-check + in-line fix (§19).
- **Evaluation** (`evaluation.py`): Claude rates the 10 dimensions + 5 BOP axes + red flags
  + `Recommendation`; deterministic completeness, no-0–100-score scan, `music_fit`
  confidence cap while musical DNA is `NEEDS_INPUT`, `target_state` clamp to
  EXPLORE/TEST/PARK, fixed `execution_note`; runs the compliance check; a stage failure
  excludes that opportunity, run continues.
- **Ranking** (`ranking.py`): pure ordinal comparator from `config/ranking.yaml` (no numeric
  score); hard exclusion = HIGH-severity compliance red flag OR zero OBSERVED evidence OR
  Evaluation-stage exclusion; presented / parked / excluded sets.
- **Report Generation** (`reporting.py`): `assemble_opportunity` builds the full
  `Opportunity` (+ `OpportunityProvenance`), runs `validate_opportunity` (fail → excluded
  and itemized in the digest), renders the 9-section Markdown + YAML front matter +
  `<id>.json` sidecar + `digest.md` (with `config_snapshot`, §12.5) + `review.md`
  (§21.1 template) + `data/<run_id>/opportunities.json` (§17).
- **Registry Updater** (`registry.py`): append-only `opportunity-registry.yaml` — the ONLY
  file under `knowledge/` the pipeline writes; existing entries kept in place (localized
  git diff §17), new ones appended; replay runs mark entries `replay_origin: true`.
- **Orchestrator** (`orchestrator.py`) + `run` CLI: sequential driver with stage timings;
  hard-fails only on preflight / all-sources-down / framing-cannot-run; writes
  `data/<run_id>/run.log` (§14). `dry_run` stops after Framing.

**354 pytest tests green (no network), `ruff check src tests` clean, `preflight` OK,
`run config/run.pipeline.replay.example.yaml` OK offline.** Runtime deps: `PyYAML` +
`anthropic>=1.2.0` (lazily imported — only a live run needs it).

## Completed

### Knowledge base & specification (2026-08-27)

- **Architectural review** of the repo against `CLAUDE.md`.
- **Critical review of `CLAUDE.md`** formalized into `knowledge/DECISIONS-NEEDED.md`
  (32 decisions: C1–C10 critical, I1–I12 important, P1–P10 deferrable).
- **All C1–C10 and I1–I12 decisions recorded as `DECIDED (2026-08-27)`** by the owner
  (I1 with strategic classification still partly pending; I2 with post-`TEST` transitions
  deferred). P1–P9 `DEFERRED (2026-08-27)`; **P10 `DECIDED (2026-08-27)`**.
- **Business DNA captured** — `knowledge/business-dna/business-dna.md` (15 sections,
  provisional, `NEEDS_INPUT` markers) and `knowledge/business-dna/content-methodology.md`
  (historical heuristics, not rigid rules).
- **Factual asset inventories built** from the source spreadsheets in
  `knowledge/inventories/source/` — `artists.yaml`, `playlists.yaml`, `pages.yaml`,
  `catalog.yaml` (facts + provenance + stable ids; strategic fields `NEEDS_INPUT`/`UNKNOWN`).
- **Canonical cluster taxonomy** — `knowledge/clusters/cluster-taxonomy.md`, 11 canonical
  clusters, machine-readable block, open-taxonomy rule, `Sono` root / `Sono Restaurador`
  subcluster.
- **Owner strategic classification** captured in
  `knowledge/inventories/classification-input.yaml` and **consolidated into the official
  inventories**: 14 artists with canonical `primary_cluster` + `secondary_clusters` +
  `language` + `market`; 10 hero artists (`hero_artist: true`); all 8 playlists classified
  (+ `hero_artists` = the same 10 ids); all 5 own pages classified.
- **`reports/artist-classification-review.md`** — evidence-based classification suggestions
  for all 37 artists.
- **`CLAUDE.md` reconciled** with every `DECIDED` decision (17 sections).
- **`docs/TECHNICAL-SPEC-V1.md`** written and then revised via an Implementation Readiness
  Review — verdict **READY**. 23 sections + Appendix A; 8 core schemas + provenance schemas.
- **`knowledge/rules/guardrails.yaml`** — 10 machine-readable guardrails `G01`–`G10`
  transcribed verbatim from C4 / `CLAUDE.md` §14 (the pipeline loads this file, not
  `CLAUDE.md` prose).
- **Private GitHub repo** created and all work pushed:
  `divinetonesmusic-spec/ai-music-media-engine` (visibility PRIVATE).

### V1 Foundation implementation (2026-08-28) — uncommitted working tree

- **Owner ratified the Foundation stack `TECHNICAL DEFAULT`s**, with one change:
  **Python 3.12, not 3.9** (3.9 is EOL). Homebrew `python@3.12` installed; `.venv` recreated
  on it; `pyproject.toml` pins `requires-python = ">=3.12,<3.13"`, `ruff` `target-version = "py312"`.
  Also ratified: stdlib `dataclasses` + hand-written validators (**no pydantic**); `src/`
  layout; missing registry ⇒ treated as empty. **Not yet folded into
  `knowledge/DECISIONS-NEEDED.md`** — I10's text still just says "Python 3".
- **Foundation layer implemented** (TDD; `src/market_intelligence/`): **124 pytest tests
  pass, `ruff check` clean.**
  - `schema/enums.py` — controlled vocabularies (§6.2, §7.1a, §8.1, §9); `LANGUAGE_TO_MARKET`,
    `DIMENSION_KEYS` (10), `AXIS_KEYS` (5), `V1_OPERATIONAL_STATES`.
  - `schema/models.py` — dataclass models for every entity (§6 Signal/Provenance, §7
    Opportunity/EvidenceItem/Hypotheses, §8 Evaluation, §9 BusinessOutcomeProfile, §10
    AssetMatch, §12 Recommendation/report front matter, §16 OpportunityProvenance, §20
    RunConfig).
  - `schema/codec.py` — generic dataclass ⇄ plain-dict codec (YAML/JSON round-trip; structural
    checks only; field-alias support for the reserved word `from`).
  - `schema/ids.py` — deterministic `opportunity_id` (sha1 of the C1 tuple, §7.1) and
    `signal_id` (§6.1); collision-suffix helper.
  - `schema/validate.py` — §13 validators returning `list[ValidationError]` (severity
    `ERROR` blocks presentation / `WARNING` logged); `InventoryIndex`; the "no 0–100 score"
    scanner (C6); one valid + one invalid fixture per §13 rule (52 tests).
  - `config/loader.py` + `config/{run.example,ranking,dedup}.yaml` — RunConfig load + default
    fill (§20); ranking comparator constants (§11.1) and dedup-key definition (§6.6) as data.
  - `io_utils.py` — YAML / Markdown-front-matter / fenced-`yaml`-block readers; `LoadError`.
  - `knowledge_loader.py` — Knowledge Loader (§18): loads business-dna, `guardrails.yaml`
    (validates 10 = G01–G10), `cluster-taxonomy.md` (validates 11 canonical ids), the 4
    inventories (non-empty, id present), the registry (absent ⇒ `[]`). **Hard-fails
    (`KnowledgeError`) on any missing/malformed required file** (§3, §14).
  - `preflight.py` + `__main__.py` — `load & validate config → Knowledge Loader` (head of the
    §5 run lifecycle); CLI `python -m market_intelligence preflight config/run.example.yaml`
    → `PREFLIGHT OK` against the real repo.
  - `tests/fixtures/` — canonical spec-§13-valid `Opportunity` + `Signal` JSON fixtures.
- **`README.md`** populated (dev setup, layout, Foundation status table).
- **`.gitignore`** extended: `/data/`, `.venv/`, Python build/cache artifacts. `reports/`
  stays tracked (durable output, I7).

## Current Architecture

Per `docs/TECHNICAL-SPEC-V1.md` (the authoritative implementation spec):

- **Scope:** canonical pipeline stages 1–2 only —
  `Market Intelligence → Opportunity Analysis → Opportunity Report` — run as one functional
  workflow. Stages 3–13 are out of scope (C7, C8).
- **Shape:** a deterministic sequential orchestrator over a **modular pipeline of specialized
  components** (I8) — Knowledge Loader → 1 Signal Collection → 2 Signal Normalization →
  3 Analysis/Framing → 4 Asset Matching → 5 Evaluation → 6 Ranking/Prioritization →
  7 Report Generation → Registry Updater. No monolithic prompt, no multi-agent orchestration.
- **Implementation status:** **Foundation done + committed**; the **whole stage-1–2 pipeline
  is implemented and uncommitted** — see **Current Phase** for the per-component picture.
  `market_intelligence.{collect.*, normalize.*, llm_stage, framing, matching, guardrails,
  evaluation, ranking, reporting, registry, orchestrator, cli}`.
- **Orchestrator** — `orchestrator.run_pipeline(config | RunConfig, *, project_root, now=,
  stage_client=, normalization_client=)` drives the components in sequence; each component
  is an isolated unit and they communicate only through the orchestrator (§18).
- **CLI:** `market_intelligence.cli` (unified `main`, dispatched from `__main__`). Commands:
  `preflight` · `collect` (stage 1) · `normalize` (stages 1–2) · `run` (the whole pipeline).
- **Claude-in-the-loop:** Web Search collector (SC-2) + SN-2 normalization + the 3 analysis
  stages (framing / matching / evaluation via `llm_stage`). All use the Anthropic SDK
  (`anthropic>=1.2.0`, lazily imported), injectable clients, and recorded replay under
  `<fixture_path>/llm/<stage>/<key>.json` — tests never touch the network.
- **Schema layer:** stdlib `dataclasses` + a generic codec; the §13 rules are hand-written
  validators returning `ValidationError` (`ERROR` blocks presentation, `WARNING` is logged).
  **No pydantic** (I10 — no unnecessary complexity). Enums are `(str, Enum)`, so `.value` is
  used wherever the raw string matters (id hashing, serialization).
- **Claude vs deterministic:** Claude does research (server-side Web Search), framing,
  evidence typing, fit judgement, rating/justification, prose. Deterministic code does
  loading, schema validation, id assignment, dedup, candidate filtering, asset-existence
  checks, ranking, rendering, registry update.
- **Signal sources (C2):** Claude API server-side Web Search (live); YouTube Data API;
  TikTok Creative Center (analyst/operator structured capture file — no free public API in
  V1); internal business data (operator YAML/CSV). Spotify is **not** a discovery source.
- **Evaluation (C6, C9):** no composite 0–100 score. 10 qualitative dimensions
  (`LOW`/`MEDIUM`/`HIGH`/`VERY_HIGH`) + separate confidence (`LOW`/`MEDIUM`/`HIGH`) +
  red flags + an operational recommendation.
- **Business Outcome Profile (C5):** 5 value-engine axes kept separate, never aggregated —
  `playlist_growth_potential`, `music_trend_ugc_potential`, `streaming_royalty_potential`,
  `page_growth_potential`, `youtube_media_potential`.
- **Output (I4, I7):** one Opportunity Report per presented opportunity (Markdown + YAML
  front matter, 9 sections, `schema_version`) + a run digest + a per-run `review.md` gate,
  written under `reports/<run_id>/`. Regenerable data under `data/<run_id>/`.
- **Opportunity registry (I2):** `knowledge/market/opportunity-registry.yaml`, append-only,
  written by the pipeline (governance exception documented in spec §17).
- **Stack (I10):** **Python 3.12** (owner decision 2026-08-28 — refines I10's "Python 3";
  3.9 is EOL. `pyproject.toml` pins `requires-python = ">=3.12,<3.13"`; local runtime is
  Homebrew `python@3.12`), Claude, YAML + Markdown + JSON, Git. No database, queue or
  server. Test runner `pytest`, TDD. `replay` mode for offline deterministic testing.
- **Autonomy:** Level 1 for every action — the system only recommends; humans execute.

## Important Decisions

Essential decisions for resuming (full text + history in `knowledge/DECISIONS-NEEDED.md`):

- **C1 — Opportunity unit:** an opportunity is an audience need/desire/behavior with demand
  or growth signals, turnable into a content cluster, in a specific market/language/platform,
  connected to an existing musical asset or a potential new content operation. Mandatory
  minimum: need, audience, market, language, platform, consumption context. `OPPORTUNITY ≠ CLUSTER`.
- **C6 / C9 — Evaluation:** qualitative multidimensional profile (10 dimensions), no 0–100
  numeric score, confidence preserved separately, red flags, one recommendation.
- **C5 — Business Outcome Profile:** 5 axes, kept distinct, no single aggregated value.
- **C7 — MI V1 scope is deliberately narrow:** discover / structure / evidence / evaluate /
  prioritize / assess asset fit / recommend a next action. Cluster, positioning, page and
  first content direction are **light non-binding hypotheses** only.
- **C8 — Canonical pipeline:** 13 stages; V1 implements stages 1–2 only.
- **C2 — Signal sources:** the four listed above, behind a pluggable `Signal` schema.
- **C4 — Guardrails:** 10 compliance/safety rules, now in `knowledge/rules/guardrails.yaml`.
- **C10 — Definition of Done:** over 3 consecutive runs — 5–10 prioritized opportunities/run;
  100% evidence traceability (source + observation date); observed vs hypothesis explicitly
  distinguished; no invented assets (`UNKNOWN` instead); ≥70% of the Top 10 judged relevant
  by the owner; ≥1 opportunity advanced to the next stage.
- **Lifecycle (C6, I2, `CLAUDE.md` §9):** conceptual `EXPLORE → TEST → LAUNCH → SCALE → KILL`
  + `PARK`. **V1 operational states: `EXPLORE`, `TEST`, `PARK`.** `LAUNCH`/`SCALE`/`KILL`
  stay conceptual/deferred.
- **I1 — Inventories** are the only source of asset truth; strategic classification is
  **partly consolidated** (see Current Assets), the rest `NEEDS_INPUT`.
- **I5 — Asset reuse is the default;** a new asset is a *recommendation only* (never
  auto-created in V1) and only when the four I5 conditions hold.
- **I9 — Durability** (`EPHEMERAL`/`EMERGING`/`STRUCTURAL`/`EVERGREEN`) + separate
  **Urgency** (`LOW`/`MEDIUM`/`HIGH`).
- **I12 — At most 10 presented opportunities per run;** the rest are kept internally as `PARK`.
- **Cluster taxonomy:** exactly **11 canonical clusters**, open taxonomy — a new cluster
  appears only as a report hypothesis (`potential_cluster`), never auto-created (P6).
- **Cluster / catalog affinity ≠ playlist placement ≠ strategic hero status** — three
  distinct concepts; any artist can serve any cluster/opportunity; hero status is independent
  of catalog affinity (`business-dna.md` §10–§11, spec §10.2a).
- **Market taxonomy (V1):** `pt`↔`Brasil`, `es`↔`Mercados hispanohablantes`,
  `en`↔`English-speaking markets`. No country-level taxonomy in V1.

## Current Assets

Counts from `knowledge/inventories/` (current):

| Asset | Count | Classification state |
|---|---|---|
| Artists | **37** | 14 have canonical `primary_cluster` + `secondary_clusters` + `language` + `market`; 23 `NEEDS_INPUT`; `positioning` `NEEDS_INPUT` for all 37 |
| Playlists | **8** | all 8 classified (`cluster`, `secondary_clusters`, `language`, `market`, `purpose`); `priority` `HIGH` for 1, `NEEDS_INPUT` for 7 |
| Pages (total) | **49** | — |
| Own pages | **5** | all 5 classified (`cluster`, `language`, `market`, `purpose`) |
| Reference/competitor pages | **44** | unclassified (context only, never a recommended asset) |
| Hero artists | **10** | `hero_artist: true`; the same 10 ids listed on all 8 playlists |
| Catalog items (releases) | **133** | facts only; `release_month` preserved, year `UNKNOWN` |
| Canonical clusters | **11** | `knowledge/clusters/cluster-taxonomy.md` |

Not yet inventoried: Instagram and Facebook pages (`UNKNOWN`). Historical performance data
(streams, saves, followers, skip rate) is not available in structured form (`UNKNOWN`).

## Last Completed Step

**The complete V1 Market Intelligence pipeline** (2026-08-28, uncommitted): SN-3 +
Analysis/Framing + Asset Matching + Guardrails + Evaluation + Ranking + Report Generation +
Registry Updater + Orchestrator + the `normalize` / `run` CLI commands. Built TDD; the
end-to-end integration test (`tests/test_pipeline_e2e.py`) exercises
`fixture signals → normalization → framing → matching → evaluation → ranking → report →
registry` fully offline. **354 pytest tests green, `ruff` clean, `preflight` OK,
`run config/run.pipeline.replay.example.yaml` OK offline.**

Three reviews were run and their in-scope findings fixed: **spec-consistency** (verdict
PASS), a **code review**, and a **security review** (no HIGH/MEDIUM). Fixes applied this
pass: framing wraps `ResponseRejected` as a clean `FramingError`; an INFERRED evidence item
with no basis is dropped (not the whole opportunity); the G01/G03/G04 compliance scanners
no longer false-positive on the permitted wellness themes (anxiety / insomnia / stress) or
the PT/ES "trata-se de" idiom; the Evaluation prompt now enumerates G01–G10 for a Claude
self-check; the digest gained `config_snapshot` and itemizes report-time exclusions; the
run writes `data/<run_id>/run.log` (§14) and `data/<run_id>/opportunities.json` (§17); the
"no 0–100 score" scan covers the Recommendation and BOP too; `validate_opportunity` now
checks §16.3(d) (`provenance.signal_ids` covers every cited signal); the registry keeps
existing entries in place and marks replay-run entries `replay_origin: true`; file writes
are atomic (`.tmp` + `os.replace`); `reporting` receives the real `musical_dna_needs_input`.

Historical increment detail (SN-1/SN-2/SC-1..SC-5) is retained below.

### SN-2 (also uncommitted)

**The Claude-assisted step of §18 component 2** — disambiguate only under-specified fields.

- `normalize/llm.py` — `normalize_with_llm(NormalizationResult | list[Signal], *, config,
  project_root, client=None) -> LlmNormalizationResult`. For each signal, `ambiguous_fields`
  is the subset of `{signal_type, market, language, durability_hint}` the collector left
  under-specified (`market`/`language` == `UNKNOWN`; `durability_hint` is `None`;
  `signal_type` == `other` or a collector `TECHNICAL DEFAULT` — currently only YouTube's
  `content_format`). A signal with none passes through with **no model call**.
- **The model can only disambiguate.** Its response goes through `validate_llm_response`
  first: only `{signal_id, suggestions, rationale, confidence?}` at the top level;
  `suggestions` may hold only the four normalisable keys AND only the ones ambiguous for
  *this* signal; each value must be in the V1 taxonomy. Any deviation → the whole response
  is rejected and the signal keeps its original (conservative) values. Applying a
  suggestion is a `dataclasses.replace` touching only that field; the new signal is
  re-validated; `evidence` / `provenance` / `source` / dates / `raw_ref` / `metrics` /
  `signal_id` are never in scope. A `UNKNOWN` / `null` / no-change suggestion is a no-op
  (the field stays preserved).
- `LlmNormalizationResult.changes` — one `NormalizationChange(signal_id, suggestions=[…],
  preserved_fields=[…], rationale, llm_confidence, applied, rejection_reason)` per input
  signal: the full traceability record (every change → its `signal_id` and `from`/`to`).
- **Injectable client** in the `WebSearchClient` / `YouTubeClient` pattern:
  `NormalizationClient` (interface), `AnthropicNormalization` (real — lazy `import
  anthropic`, structured-output `messages.create` per signal, key from env, never stored;
  no creds → degrades every signal), `RecordedNormalizationClient` (replay). Tests inject
  a stub and never hit the network.
- **Replay (§22):** `replay.enabled` + `replay.llm != "live"` → read
  `<fixture_path>/llm/normalization/<signal_id>.json`; a missing fixture degrades that
  signal (its fields stay as they were) — the network is **never** a fallback.
  `replay.llm == "live"` → real call.
- **No `Signal` field added.** Normalization metadata lives on `NormalizationChange`, not
  the `Signal`.
- Changed only `normalize/__init__.py` (added the `.llm` re-exports); everything else is new.

### SN-1 (also uncommitted)

**The deterministic half of §18 component 2** — validation + deduplication, no Claude.

- `normalize/dedup.py` — `dedup_key(sig, *, dedup_config)` builds the ordered tuple of
  `dedup_key_parts` from `config/dedup.yaml`; `deduplicate(signals, dedup_config)` groups
  by `(key, observed_at day)` (when `duplicate_requires_same_observed_at`), keeps the
  higher `confidence` (tie → lower `signal_id`), merges only the metric keys the kept
  signal **lacks** (`merge_absent_metrics` — a conflicting value is never overwritten),
  and returns `(kept, discarded_ids, [DedupReason])` in a fully input-order-independent
  order. `normalized_source` = case-folded `provenance.source`; `canonical_url` = fragment
  + `url_tracking_params` stripped, host lowercased, query sorted; `normalized_subject` =
  kebab-cased evidence tokens minus the configured stopwords. An unknown key part in the
  config raises `NormalizationError`.
- `normalize/deterministic.py` — `normalize_deterministic(signals | collected.json path,
  *, dedup_config, raw_root=None)`: runs `validate_signal` per signal (+ within-run
  duplicate-`signal_id` check), records every invalid signal as `InvalidSignal(signal_id,
  errors=[{code, path, message}])` and drops it (never auto-corrected), then deduplicates.
  Returns `NormalizationResult`. Writes no files; mutates no input (a metrics-merged kept
  signal is a new object via `dataclasses.replace`). `signals_from_collected(path)` loads
  the `Signal` list out of a `collected.json` manifest.
- **Not done:** the Claude step (SN-2 — `signal_type` / `market` / `language` /
  `durability_hint` when ambiguous) and writing `data/<run_id>/signals/normalized.json`.
- **No existing file changed** — SN-1 is all new modules + tests + fixtures.

### SC-5 (also uncommitted)

**The collection entry point** — stage 1 of the canonical pipeline runs end to end.

- `collect/runner.py` — `run_collection(config, *, project_root, now=None) -> CollectionResult`.
  Accepts a resolved `RunConfig` (trusted) or a config path (loaded + validated, with
  `validate_run_config(..., require_knowledge_paths=False)` — Collection reads no
  `knowledge/`; `TECHNICAL DEFAULT`). Runs `collect_signals`, then writes the run manifest.
  Propagates `SignalCollectionError` (all sources failed, §14) and `ConfigError`.
- Manifest `data/<run_id>/signals/collected.json` (`TECHNICAL DEFAULT` — a run artifact, not
  a new business entity): `schema_version`, `run_id`, `replay`, `signal_count`,
  `sources_used`, `sources_failed`, `signal_ids`, and the collected `Signal` list (an
  existing §6 entity). Byte-reproducible in replay mode; deterministic given a fixed clock
  otherwise. Does **not** replace the raw captures; `normalized.json` is left for
  Normalization.
- `cli.py` — unified `main`; new `collect <config>` command (prints
  `sources_used` / `sources_failed`, the manifest path, a "below C10 target" note, and
  `COLLECT OK  (Signal Collection only — Normalization not run)`). `__main__` → `cli.main`;
  `preflight`'s argparse `main` + `_summary` moved into `cli.py`.
- `config/run.replay.example.yaml` — a committed offline demo (`replay.enabled: true`,
  fixtures under `tests/fixtures/replay/collect_demo/`). `python -m market_intelligence
  collect config/run.replay.example.yaml` runs with no network / no keys.
- `schema/validate.py` — `validate_run_config` gained `require_knowledge_paths=True`
  (default) and now skips the source capture-file checks when `replay.enabled` (`TECHNICAL
  DEFAULT` — §22: replay reads fixtures, not those paths).
- `collect/base.py` — the "no replay fixtures" failure reason now references the config's
  `replay.fixture_path` as written (portable), not the machine-resolved absolute path, so
  the manifest stays reproducible.

### SC-4 (also uncommitted)

**The TikTok Creative Center collector** — the last of the four V1 collectors.

- `collect/tiktok.py` — `TikTokCreativeCenterCollector` (§6.5). **Deterministic, no Claude,
  no API, no scraping, no browser.** V1 assumes no free public API: an analyst records
  Creative Center observations into a structured capture file
  (`RunConfig.tiktok_capture_path` — a YAML/JSON list of records, or a mapping with a
  `records:` list). Each record → one `Signal` field-for-field. `source_type` =
  `tiktok_creative_center`; `capture_method` = `analyst_capture`; `source` =
  `"TikTok Creative Center — <panel>"`; `provenance.query_or_reference` = the record's
  `query_or_reference` / `filter` / `panel`. Never invented: `observed_at` (absent →
  `UNKNOWN`; present-but-unparseable → the source degrades), `url` (absent → `null`),
  `metrics` (passed through unchanged, no coercion). Required fields: `panel`, `market`,
  `language`, `signal_type`, `evidence`, `context`, `confidence`; `platform` defaults to
  `tiktok` (`TECHNICAL DEFAULT`). A structurally invalid record degrades the source
  (`CollectorError`), matching `internal_data`. `replay_uses_live_path = False` — replay
  rebuilds from `signals/raw/*.json`. Auto-registered in `DEFAULT_COLLECTORS`.
- `RunConfig.tiktok_capture_path` already existed (Foundation) — no config change needed.

### SC-3 (also uncommitted)

- `collect/youtube.py` — `YouTubeCollector` (§6.5). **Fully deterministic — no Claude.**
  `search.list` finds video/channel/playlist results for each configured query;
  `videos.list` enriches video results with public `statistics` (best-effort — a
  `videos.list` failure means metrics are unavailable, not an error, §6.3). `YouTubeClient`
  is injectable; the real `YouTubeDataApiClient` uses **stdlib `urllib`** (no new
  dependency), reads the key from the `YOUTUBE_API_KEY` env var (`TECHNICAL DEFAULT` — §20.2
  mandates an env var, doesn't name it), and **never writes the key** to a raw capture,
  log, fixture or error message (a `_redact` pass strips `key=…` from any string). Every
  `Signal`: `url` derived deterministically from a real resource id (or `null` — never
  invented, §12); `observed_at` = the item's `publishedAt` date or `UNKNOWN`; `metrics` =
  only figures the API returned; `source` = `"YouTube Data API — search.list"`;
  `provenance.query_or_reference` = endpoint + params (no key); `source_version` = `"v3"`;
  `capture_method` = `youtube_data_api`. `signal_type` / `confidence` are `TECHNICAL
  DEFAULT`s (`content_format` / `LOW`) for Normalization to refine. `replay_uses_live_path
  = False` — replay rebuilds from `signals/raw/*.json`, no network, no key. Malformed API
  items (missing id/title) are skipped, never turned into invalid Signals.
- `schema/models.py` — `RunScope` gained `queries: list[str]` and
  `youtube_region_code: str | None` (both `TECHNICAL DEFAULT` — §6.5 needs a `query`; §20.1
  had no field; §7.1a bars a country taxonomy so `regionCode` is an operator-set API hint
  that does **not** change a Signal's `market`).
- `config/run.example.yaml` — documents the two new `scope` fields.

### SC-2 (also uncommitted)

- `collect/web_search.py` — `WebSearchCollector` (§6.5). Uses the Claude API server-side
  web search tool (`web_search_20250305`) via the Anthropic SDK. Two model calls per
  collection: (1) a web-search call gathering real results + analysis; (2) a structuring
  call (`output_config` JSON schema) turning that into `Signal` candidates. **Every
  emitted `Signal` is anchored to a real `web_search_result`** (`result_url` must match a
  returned result) — an unbacked model claim is dropped (§6.5). `Provenance`:
  `query_or_reference` = the exact query, `source` = result title, `url` = result url (or
  `null`, never invented), `observed_at` = `page_age` normalised to ISO or `UNKNOWN`,
  `capture_method` = `claude_web_search`. `WebSearchClient` is injectable (tests never
  hit the network); the real `AnthropicWebSearch` degrades (`CollectorError`) on missing
  SDK / credentials / API error. Recorded replay (`replay.llm != "live"`) reads
  `<fixture_path>/llm/web_search/*.json`.
- `collect/base.py` (SC-2) — added `Collector.replay_uses_live_path` (a collector that
  sources its own recorded fixtures), `ctx.fixture_path` / `ctx.replay_llm_mode`, and made
  `_load_replay_records` tolerant of a missing dir (a source with no fixtures becomes a
  per-source failure, not a crash). Backward-compatible; SC-1 behaviour unchanged.

### SC-1 (also uncommitted)

- `collect/base.py` — `SignalIdAllocator` (wraps `schema.ids.signal_id`), `RawCapture` +
  `RawCaptureStore` (`data/<run_id>/signals/raw/<signal_id>.json`, §6.7 shape),
  `Collector` ABC, `SignalCollectionContext`, `collect_signals(...)` orchestrator —
  degrades per source, hard-fails (`SignalCollectionError`) only when every source fails
  (§14); an unimplemented source is recorded in `sources_failed`, never crashes.
- `collect/internal_data.py` — `InternalDataCollector` (§6.4): reads
  `RunConfig.internal_data_path`, maps each record → `Signal` with full `Provenance`.
- **Replay (§22)** — the deterministic collectors rebuild from
  `<fixture_path>/signals/raw/*.json` (copied into the run's own raw dir so `raw_ref`
  resolves, §6.3); result stamped `replay=True`.
- `schema/validate.py` — `validate_signal` / `validate_signals` gained an optional
  `raw_root=` for the §6.3 "raw_ref resolves to an existing file" check.

`pytest` (256 passed, no network), `ruff check src tests` (clean),
`preflight config/run.example.yaml` (`PREFLIGHT OK`),
`collect config/run.replay.example.yaml` (`COLLECT OK`, fully offline).
Preceded, earlier in the project, by the committed Foundation layer and the Python 3.12
migration.

## Last Commit

```
37b0db4  feat: implement V1 foundation layer
```

Full hash: `37b0db45200034a9861e36aeb0cf14d11901d516`
The full Foundation layer (schemas, codec, ids, §13 validators, fixtures, config loader +
`config/*.yaml`, Knowledge Loader, preflight, `pyproject.toml`, README, `.gitignore`) —
32 files. Pushed to `origin/main`.

Recent history:

```
37b0db4  feat: implement V1 foundation layer
0ee23b1  chore: add project engineering guardrails and session state
b8fec98  feat: finalize market intelligence v1 specification
2154c07  feat: V1 knowledge base — asset classification, cluster taxonomy, technical spec
d236323  docs: reconcile V1 project specification
859c731  chore: ignore .DS_Store files
00600cc  chore: initialize AI Music Media Engine
```

**Uncommitted working tree** — the full stage-1–2 pipeline, awaiting owner review
(nothing committed or pushed):

- Untracked src: `src/market_intelligence/{collect/*, normalize/*, cli.py, llm_stage.py,
  framing.py, matching.py, guardrails.py, evaluation.py, ranking.py, reporting.py,
  registry.py, orchestrator.py}`.
- Untracked tests: `tests/test_{collect_*, normalize_*, llm_stage, framing, matching,
  guardrails, evaluation, ranking, reporting, registry, pipeline_e2e}.py` +
  `tests/fixtures/{pipeline/, replay/, normalize/, internal_data_example.yaml,
  web_search_research.json, youtube_*_list.json, tiktok_capture.yaml}`.
- Untracked config: `config/run.replay.example.yaml`, `config/run.pipeline.replay.example.yaml`.
- Modified (committed files touched this work): `pyproject.toml` (`anthropic>=1.2.0`),
  `src/market_intelligence/{schema/validate.py, schema/models.py, preflight.py, io_utils.py,
  __main__.py}`, `config/run.example.yaml`, `README.md`, `tests/test_validate.py`,
  `docs/SESSION-STATE.md`.
- **`knowledge/`, `CLAUDE.md`, `docs/TECHNICAL-SPEC-V1.md`, `knowledge/DECISIONS-NEEDED.md`
  are untouched.**

## Current Repository State

- **Branch:** `main`
- **Remote:** `origin` → `https://github.com/divinetonesmusic-spec/ai-music-media-engine.git` (PRIVATE)
- **Relation to `origin/main`:** **in sync** — local `HEAD` == `origin/main` == `37b0db4`.
  The whole stage-1–2 pipeline sits on top as uncommitted changes.
- **Working tree:** **not clean** — the files above. (`.venv/`, `/data/` and Python
  artifacts are git-ignored. Tests write only under pytest `tmp_path`. No test touches the
  network. The `reports/` dir has no run output committed — the replay demo's
  `reports/run_pipeline_replay_demo/` should be removed before commit.)
- **Local runtime:** Python 3.12.14 in `.venv/`; `pip install -e ".[dev]"` (PyYAML,
  anthropic, pytest, ruff).

## Next Action

**The full V1 pipeline is implemented, tested and reviewed. It is not committed.**

1. **Owner review of the working tree**, then a commit (the pipeline package + tests +
   fixtures + the two config examples + the touched Foundation files). Remove the replay
   demo's `reports/run_pipeline_replay_demo/` first. Do **not** push without asking.
2. Before the 3-run C10 validation gate, decide on the deferred-but-in-spec items in
   **Open Issues** below — chiefly the compliance-enforcement depth and whether a live
   (non-replay) run should be done first.
3. Owner decisions that still gate quality (not blocking): value-engine weighting for
   ranking (`NEEDS_INPUT` → §11 keys 3–4); musical DNA detail (caps `music_fit`
   confidence); the rating-anchors appendix (§8.3), to be written alongside the first
   real run.

**How to run it:** `./.venv/bin/python -m market_intelligence run <config>` — or
`config/run.pipeline.replay.example.yaml` for a fully offline demo.

## Open Issues

### V1 pipeline — known limitations / deliberate partial implementations

Surfaced by the spec-consistency + code reviews; each is a documented gap, not a bug:

- **Compliance enforcement depth (spec §13/§19).** Deterministic scanners exist only for the
  explicit disease-claim constructions of **G01/G03/G04**; G05–G10 rely on the Claude
  self-check now enumerated in the Evaluation prompt. There is **no separate live
  "reject_and_revise → one revision pass" loop** — Claude revises in-line within its single
  call, and deterministic escalation (strip the offending hypothesis, or exclude on core
  content) handles the rest. `require_uncertainty_statement` (G10) rendering is wired
  (`ComplianceResult.needs_uncertainty_note`) but dormant (no G10 scanner). **Owner
  decision needed before the C10 gate:** is this depth acceptable, or must the fuller flow
  land first?
- **§16.3(c)** — "every justification cites the evidence item(s) it uses" is not
  deterministically verified (too noisy); the Evaluation prompt asks for it. (d) *is* now
  checked.
- **Atomic run output (§14 TECHNICAL DEFAULT).** Writes are atomic per file
  (`.tmp` + `os.replace`), not a whole-dir staged move — a mid-run crash can leave a subset
  of report files (each individually complete); a same-`run_id` re-run overwrites cleanly.
- **`reference_competitor` pages** are never surfaced as `role: reference` candidates in
  `AssetMatch` (spec §10.3 permits it for competitive context) — the implementation is
  stricter (own pages only). Safe; competitive context lives in the `competitive_position`
  dimension instead.
- **A live (non-replay) run has not been done.** Every stage is exercised only against
  recorded fixtures.

### New TECHNICAL DEFAULTs (this pipeline) — to record in `knowledge/DECISIONS-NEEDED.md`

- `opportunity_id` collision suffix extends past `-2` (`-3`, `-4`, …) for multi-collisions.
- Framing keys its LLM replay fixture by `sha1(sorted signal-id set)`, not `run_id`
  (idempotent re-runs, §5/§22).
- Recommendation `target_state` down-maps LAUNCH/SCALE → TEST, KILL → PARK (spec §5 only
  says V1 emits the three operational states).
- Registry entries carry `first_run_id` / `last_run_id` (beyond the I2 minimum) and
  `replay_origin: true` for replay runs; existing entries keep file order (localized diff).
- `AssetMatch.matching_catalog` is `null` in V1 (§10.3 "catalog matching is coarse in V1").
- `_musical_dna_needs_input` is detected by scanning `business-dna.md` for "Music DNA" then
  "NEEDS INPUT" within 800 chars (brittle if the doc is restructured).
- `data/<run_id>/run.log` and `data/<run_id>/opportunities.json` formats.
- The `llm_stage` fixture convention: `<fixture_path>/llm/<stage>/<key>.json`.

### Earlier open issues

- **Foundation stack decisions not yet in `knowledge/DECISIONS-NEEDED.md`** — the owner
  ratified Python 3.12, stdlib-`dataclasses` schemas (no pydantic), the `src/` layout, and
  "missing registry ⇒ empty", but I10's *Resultado* text still just says "Python 3". Fold
  these in when convenient (the file is owner-protected — needs a manual edit or an explicit
  per-task instruction).
- **`knowledge/market/opportunity-registry.yaml` does not exist yet** — it is created by the
  Registry Updater on the first real run; the Knowledge Loader treats its absence as an empty
  registry (not an error). A manual placeholder is unnecessary.
- **Strategic classification backlog (`NEEDS_INPUT`)** — `positioning` for all 37 artists;
  `primary_cluster` / `secondary_clusters` / `language` / `market` for the 23 unclassified
  artists; `priority` for 7 of 8 playlists; the 44 reference/competitor pages. Owner form:
  `knowledge/inventories/classification-input.yaml`.
- **Business DNA `NEEDS_INPUT`** — musical DNA detail (instrumentation, energy, duration,
  texture, BPM, use of frequencies, vocal/instrumental); target countries per language and
  priority among `pt`/`es`/`en`; royalty-ecosystem weighting, expected YouTube Video revenue
  share, other revenue sources (sync, Content ID, brand deals).
- **Value-engine weighting for ranking** is `NEEDS_INPUT` — affects spec §11 comparator
  keys 3–4; V1 uses the `TECHNICAL DEFAULT` ordinal comparator until the owner provides it.
- **Rating anchors appendix** (spec §8.3) — to be written alongside the first real run;
  calibration is deferred (P1).
- **Instagram / Facebook pages** are referenced historically but not inventoried (`UNKNOWN`).
- **Historical performance data** is not yet available in structured form (`UNKNOWN`).
- **Minor documentation drift** (not blocking, do not fix without an explicit task):
  `knowledge/DECISIONS-NEEDED.md` preamble still says "no business decision has been taken
  here" and its "Caminho crítico" section still marks C2/C3/C4 as `NEEDS INPUT`, though all
  are `DECIDED`; the I1 *Resultado* text predates the strategic-classification consolidation
  (spec §10.1 has the accurate "partly consolidated" picture); `CLAUDE.md` §3 implies the
  inventories are entirely `NEEDS_INPUT`, and the `CLAUDE.md` header line says "P1–P10 are
  DEFERRED" although P10 is `DECIDED`.

## Deferred

Explicitly deferred — a new session must **not** implement these prematurely:

- **P1** — score calibration loop with real performance data.
- **P2** — automated lifecycle transitions / autonomy Levels 2–3.
- **P3** — real-time data integrations / paid APIs beyond the four V1 sources.
- **P4** — pipeline stages 3–13 (Cluster Strategy → Learning).
- **P5** — multi-agent orchestration.
- **P6** — formal new-cluster governance (V1 only proposes a cluster as a hypothesis).
- **P7** — cross-run dashboards / trend-tracking UI.
- **P8** — prompt-versioning infrastructure beyond a `prompt_version` config string.
- **P9** — curated competitor reference base per cluster.
- **Within decided decisions:** measurable `TEST → LAUNCH → SCALE → KILL` criteria and any
  transition automation (I2); a quantitative / numeric scoring model, weights, formulas
  (C6); an automated TikTok Creative Center collector (spec §23); analytics ingestion
  (P1); a database, queue or long-running server (I10).

## How To Resume

1. **Read this file first.** Then read `CLAUDE.md` and `docs/TECHNICAL-SPEC-V1.md` in full,
   then `knowledge/DECISIONS-NEEDED.md`, `knowledge/business-dna/business-dna.md`,
   `knowledge/business-dna/content-methodology.md`, `knowledge/clusters/cluster-taxonomy.md`,
   `knowledge/rules/guardrails.yaml` and `knowledge/inventories/*.yaml` **before modifying
   anything**.
2. Where this document, `CLAUDE.md` or the spec disagree with a `DECIDED` decision in
   `knowledge/DECISIONS-NEEDED.md`, the **decision wins** — surface the divergence, do not
   guess.
3. **Do not modify without an explicit per-task instruction:** `CLAUDE.md`,
   `knowledge/DECISIONS-NEEDED.md`, `knowledge/business-dna/*.md`,
   `knowledge/clusters/cluster-taxonomy.md`, `knowledge/rules/guardrails.yaml`, and every
   file in `knowledge/inventories/`.
4. **Never invent** business rules or asset classifications. Use `NEEDS_INPUT` for a pending
   owner decision and `UNKNOWN` for a fact absent from the sources — never a guess. Never
   infer cluster / language / market / positioning / hero status from a name or track title.
5. **Do not commit or push** unless explicitly asked. The GitHub repo is and must stay
   **PRIVATE**.
6. Keep any one-off ETL / data-massaging scripts out of the repo (use a scratch/tmp
   directory). This does **not** apply to the pipeline package itself (`src/market_intelligence/`),
   which is the V1 deliverable and is tracked.
7. V1 implementation is **functionally complete and owner-authorized**, uncommitted. The
   next step is owner review → commit (see **Next Action**), not more building. Set up the
   environment first: `python3.12 -m venv .venv && ./.venv/bin/python -m pip install -e
   ".[dev]"`, then `./.venv/bin/python -m pytest` and `./.venv/bin/ruff check src tests`
   should be green (354 tests), and
   `./.venv/bin/python -m market_intelligence run config/run.pipeline.replay.example.yaml`
   should print `RUN OK`.
