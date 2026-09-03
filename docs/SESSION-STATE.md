---
title: Session State — AI Music Media Engine
status: current
updated: "2026-09-03"
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

**V1 — Market Intelligence + Opportunity Analysis: COMPLETE and C10-validated.** The
knowledge base and technical specification are complete and reconciled. The full V1
pipeline (canonical stages 1–2) is **implemented, tested, committed and pushed**.

**The C10 Definition-of-Done gate PASSED on 2026-09-01** (commit `39fe464`,
`chore: validate V1 through C10 gate`, pushed by the owner). Three consecutive live
runs — `run_2026-08-31_01` (6 presented), `run_2026-09-01_01` (10), `run_2026-09-01_02`
(10) — each with an owner `review.md`: `relevant_ratio` 0.83 / 0.80 / 0.70, ≥1 advanced
each, 100% traceable evidence, observed vs hypothesis distinguished, no invented assets.
`python -m market_intelligence gate --reports-dir reports/` reports **GATE PASS**.

**Phase 3 — Cluster Strategy V1 (canonical stage 3) — is COMPLETE and MERGED.** Built
2026-09-01 as a new sibling package `src/cluster_strategy/`; contract at
`docs/CLUSTER-STRATEGY-V1.md`; 75 new tests (617 total, all green, ruff clean); no change
to any stage-1–2 code file. Two `spec-consistency-reviewer` passes (FAIL → all fixes
applied); the D-CS decisions are recorded authoritatively in
`knowledge/DECISIONS-NEEDED.md` §4 (P4 updated) and `docs/TECHNICAL-SPEC-V1.md` §17 gained
one sentence for the opt-in registry append. **PR #1
(`feat: Cluster Strategy — canonical pipeline stage 3`) was MERGED to `main` on
2026-09-03** (rebase merge, fast-forward); the `feat/cluster-strategy-stage-3` branch was
deleted locally and remotely. The stage was then **validated live against the real
Anthropic API** (2026-09-03) — one call on Run 1's advanced opportunity returned
`MAP_TO_EXISTING → limpeza-energetica`, lifecycle `EXPLORE` preserved, deterministic
validation clean, 617 tests + ruff green (details in **Cluster Strategy (stage 3)** and
**Last Completed Step** below). **Canonical stages 4–13 remain DEFERRED (P4).**

`python -m market_intelligence run <config>` executes
`preflight → Signal Collection → Signal Normalization → Analysis/Framing → Asset Matching
→ Evaluation → Ranking → Report Generation (+ digest + review + opportunities.json + run.log)
→ Registry update`, and `config/run.pipeline.replay.example.yaml` runs the whole thing
**offline** (recorded LLM fixtures, no network, no API keys).

**Live status (2026-08-31):** **all 8 pipeline stages have now run successfully against
the real Anthropic API.** Web Search, Normalization, Framing, Asset Matching and
Evaluation are each validated live (fixtures under `tests/fixtures/replay/live_01/` and
`live_02/`); Ranking, Reporting and Registry are deterministic and fully covered offline.
Evaluation was validated after **removing structured outputs from that stage**
(owner-approved fallback C).

- **Asset Matching — VALIDATED LIVE (2026-08-31).** A targeted capture over 3 of the 13
  `live_02` opportunities: 3/3 calls returned valid structured output; the 3 real
  responses are captured at `tests/fixtures/replay/live_02/llm/matching/` (no secrets,
  regression test `test_replay_live_02_matching.py`). First attempt failed
  (`stop_reason=max_tokens` on all 3 — adaptive thinking consumed the 8000-token budget
  before any JSON, over the ~47-candidate prompt the §10.2a fix produces); fixed with
  `_STAGE_OUTPUT["matching"] = {max_tokens: 16000, effort: "low"}` (same per-stage-budget
  pattern as Framing). Second attempt: all 3 passed.
- **Evaluation — structured outputs REMOVED; VALIDATED LIVE 3/3 (2026-08-31).** The first
  isolated Evaluation run returned the grammar-size `400` on all 3 calls even after the
  `5d9781f` flatten. **Owner approved fallback C:** Evaluation no longer sends
  `output_config.format`. New path: prompt-guided JSON → `_response_to_json_object(...,
  lenient=True)` (strips a ``` fence / prose preamble, joins split text blocks, rejects a
  top-level array) → `_reject_malformed_evaluation` (strict raw-shape / enum / completeness
  / no-0–100-score check; any deviation → `technical_failure`) → `_build_bundle` (the §13
  business layer, unchanged). `_STAGE_OUTPUT["evaluation"] = {max_tokens: 24000, structured:
  False}`, effort left at the default `high`. Live result: **`output_config` = None on
  every call → the grammar 400 is gone.** First isolated run: 2/3 clean, 1 model
  property-name JSON slip (`stop_reason=end_turn` — not truncation, not the 400) → correctly
  a `technical_failure`. Re-run with `call_stage`'s retry-once enabled (the first harness's
  capturing wrapper had defeated the `isinstance(client, AnthropicStageClient)` check):
  **the 3rd opp passed on the first attempt — no retry needed** (the slip was a one-off).
  **All 3 evaluations are clean and deterministic-valid** (10 dims + 5 axes,
  `rating`≠`confidence`, `music_fit` capped LOW, `overall_confidence` LOW, compliance
  self-check fires a `G09/G10` red_flag, no score, `target_state` EXPLORE/TEST) and flow
  through Ranking (3 presented, 0 excluded, 0 technical failures). 3 real fixtures at
  `tests/fixtures/replay/live_02/llm/evaluation/`, regression test
  `test_replay_live_02_evaluation.py` (8).

**8 Anthropic-API robustness bugs** found and fixed across this and prior sessions (union
`type` array in a schema; a framing open-map field; the Web Search structuring response
parser; unbounded client timeouts; the Framing `max_tokens` budget; the Normalization
response parser; the Matching `max_tokens` budget; the Evaluation compiled-grammar size
limit — resolved by removing structured outputs from that stage). See the per-session
memory notes and the `fix:` commits `341236b`…`5d9781f`.

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

- **`gate` command** (`gate.py`): the deterministic C10 3-run Definition-of-Done
  checker (spec §21.1, §22). Reads the 3 per-run `reports/<run_id>/review.md` files
  the owner filled in and reports C10.1 (5–10 presented/run), C10.5 (relevant_ratio
  ≥ 0.70/run) and C10.6 (≥1 opportunity advanced) as PASS / FAIL / INCOMPLETE.
- **CLI** now has 5 commands: `preflight` · `collect` · `normalize` · `run` · `gate`.
  `run` surfaces technical failures separately from presented/parked/excluded and
  prints where the `reports/` and `data/` artifacts landed.

**617 pytest tests green (no network), `ruff check src tests` clean, `preflight` OK,
`run config/run.pipeline.replay.example.yaml` OK offline.** Runtime deps: `PyYAML` +
`anthropic>=1.2.0` (lazily imported — only a live run needs it).

## Cluster Strategy (canonical stage 3) — COMPLETE and MERGED (PR #1, 2026-09-03)

**Contract:** `docs/CLUSTER-STRATEGY-V1.md`. On 2026-09-01 the owner opened canonical
pipeline stage 3 (and only stage 3) and decided all twelve open decisions
(D-CS-1 … D-CS-12) at their recommended answers. Those are **recorded authoritatively** in
`knowledge/DECISIONS-NEEDED.md` §4 ("# 4. ESTÁGIO 3 — CLUSTER STRATEGY"), with the P4 entry
updated to *"estágio 3 aberto; estágios 4–13 seguem DEFERRED"*. Derived from the 2026-09-01
specification mission.

**What it is.** A new **sibling package `src/cluster_strategy/`** (imports, never modifies,
`market_intelligence.{schema, knowledge_loader, llm_stage, guardrails, io_utils, config,
gate}`). It converts **one owner-advanced Opportunity Report** into **one `ClusterStrategy`**
(Markdown + YAML front matter + JSON sidecar) at `reports/cluster-strategy/<opportunity_id>.*`.
Autonomy **Level 1** — recommend only. Canonical pipeline stage 3 (C8); its predecessor
gate (C10) passed and is recorded (commit `39fe464`); stage 3 opened via D-CS-1.
`docs/TECHNICAL-SPEC-V1.md` §17 was reconciled with one sentence sanctioning the opt-in
stage-3 `cluster_strategy_ref` registry append.

**Cluster decision** ∈ `MAP_TO_EXISTING` · `PROPOSE_NEW_CLUSTER` · `DEFER` · `REJECT`.
Deterministic alias/spelling/language pre-normalisation maps `limpieza-energetica` (es) →
canonical `limpeza-energetica` etc. before any judgement (kills artificial
spelling-variant clusters). `PROPOSE_NEW_CLUSTER` is a hypothesis + `boundary_vs_adjacent`
+ `why_not_subcluster` + evidence refs + a fixed governance note — **P6 stays deferred;
the stage never edits `cluster-taxonomy.md`.** A HIGH compliance claim in core content
forces `REJECT` + `target_next_stage: HOLD`.

**Boundary (D-CS-8, sharpest point).** Cluster Strategy stops at *cluster concept +
audience + intent + emotion + positioning + music/playlist relationship + one non-binding
first content direction*. It does **not** produce visual identity, tone of voice, content
pillars, formats, hook libraries, CTA copy, cadence, schedules, batch sizes — those are
Page Blueprint (4) / Content Strategy (5). Enforced by `cluster_strategy.schema.validate`:
`scan_for_scope_leakage` is a **key-name** denylist for stage-4/5 field names; separate
checks cover no-0–100-score (reused MI scanner), asset ids ∈ inventory, fixed-disclaimer
tampering, and `opportunity_lifecycle_state == opportunity.status`. `LAUNCH/SCALE/KILL` is
structurally impossible (not in the `TargetNextStage` enum; lifecycle carries the
opportunity's constrained `status`), not value-scanned.

**Confidence / evidence.** 4 qualitative dimensions (`cluster_fit`,
`differentiation_within_cluster`, `asset_readiness`, `strategic_coherence`) — each a
`rating` + a **separate** `confidence`, no score. `overall_confidence` ≤ the opportunity's
and never raised by high sub-ratings (C6, carried). `market_language_fit` /
`music_relationship` confidence structurally capped ≤ MEDIUM while musical DNA is
`NEEDS_INPUT`. Compliance flags carried forward and re-checked; claims-not-topics
calibration inherited from the tightened Evaluation prompt.

**Lifecycle (I2).** `recommendation.opportunity_lifecycle_state` carries the opportunity's
actual registry `status` (`EXPLORE`/`TEST`/`PARK`), **never** the MI `target_state`
recommendation (which may say "advance to TEST"); the validator fails the run if they
diverge. Cluster Strategy never transitions the lifecycle.

**Compliance escalation.** Applies the full MI `ComplianceResult`: `exclude_opportunity`
(HIGH hit in core prose) → forced `REJECT` + `HOLD`; `strip_scopes` (HIGH hit in a
`first_content_direction`/`editorial_angles` hypothesis) → those fields blanked, run
proceeds; `needs_uncertainty_note` → an open question. Red-flag dedup keys on normalised
text (exact restatement collapses; a distinct flag is never dropped).

**Registry link (D-CS-7) — OPT-IN, `write_registry_link` default `False`.** A normal or
offline run does **not** touch `knowledge/`. When explicitly enabled, appends
`cluster_strategy_ref` + one `state_history` note (`by: system`, status **unchanged**) to
the opportunity's `opportunity-registry.yaml` entry, append-only, idempotent, no-op if the
registry file is absent.

**Modules:** `schema/{models,enums,validate}.py` · `input_loader.py` · `mapping.py`
(deterministic) · `strategy.py` (the one Claude sub-step via `llm_stage`) ·
`asset_strategy.py` (deterministic consolidation of `AssetMatch`) · `guardrails.py` ·
`llm.py` · `reporting.py` · `registry_link.py` · `orchestrator.py` · `cli.py` ·
`config.py` · `__main__.py`; `config/cluster-strategy.example.yaml`.

**Tests: 75 new** (`tests/test_cluster_strategy_*.py`, 11 files) — input-loader gating,
mapping normalisation, validator rules (incl. the soft `editorial_angles` WARNING), asset
consolidation, guardrails, models/reporting, the strategy prompt (lifecycle_status vs MI
recommendation), orchestrator e2e (recorded replay on `opp_2026-08-31_1bca4af972` — the §12
worked example → `MAP_TO_EXISTING limpeza-energetica`), the DEFER / PROPOSE / forced-REJECT
/ compliance-strip / red-flag-dedup / registry-opt-in branches, CLI. Fixtures:
`tests/fixtures/cluster_strategy{,_defer,_propose,_reject,_strip,_dupflag}/` keyed
`llm/cluster_strategy/cluster_strategy__<opportunity_id>.json`. TDD throughout.

**Status: COMPLETE and MERGED.** Committed 2026-09-01 on branch
`feat/cluster-strategy-stage-3` (`8ac61b9`), PR #1 opened 2026-09-02, **MERGED to `main`
2026-09-03** (rebase merge, fast-forward; new SHA `3084f50`; branch deleted locally and
remotely). 617 tests green, `ruff check src tests` clean. The merge commit touched no
stage-1–2 code file; it did update `knowledge/DECISIONS-NEEDED.md` §4 (D-CS-1 … D-CS-12,
P4 entry), `docs/TECHNICAL-SPEC-V1.md` §17 (one sentence) and `docs/SESSION-STATE.md` —
all owner-authorised. `CLAUDE.md`, `knowledge/business-dna/*`, the cluster taxonomy, the
guardrails file and the inventories are untouched. Offline recorded-replay passes; a live
run needs `ANTHROPIC_API_KEY` (same Keychain convention as the pipeline).

**Live validation — DONE (2026-09-03).** One real Anthropic API call, on Run 1's
owner-advanced opportunity `opp_2026-08-31_1bca4af972`, key sourced from the macOS
Keychain and scoped to the child process only (never in Claude Code's environment).
Result: **`MAP_TO_EXISTING → limpeza-energetica`** (core decision identical to contract
§12, the offline replay fixture and every Cluster Strategy test); `overall_confidence
LOW` (capped at the opportunity's LOW, C6); **`opportunity_lifecycle_state = EXPLORE`
preserved** (== the opportunity's registry `status`, not the MI `target_state: TEST`);
`target_next_stage = PAGE_BLUEPRINT`; playlist `pl_4oV5F1W2E6azZePnmqBanN` reused + a
new-page recommendation carried (no asset invented); no 0–100 score; 4 red flags
(compliance/MEDIUM carried) + 4 open questions. **`write_registry_link: false` →
`knowledge/` untouched** (git-verified). Deterministic re-validation of the live output
against the real knowledge base: **`validate_cluster_strategy` → 0 findings**,
`scan_for_scope_leakage` → none, numeric-score scan → none, JSON round-trips exactly.
Post-run: **617 pytest tests green, `ruff check src tests` clean** (no regression — the
run wrote only report files). Output: `reports/cluster-strategy/opp_2026-08-31_1bca4af972.{md,json}`
— left **untracked and uncommitted** (a validation run using the example config, not a
committed stage-3 deliverable; the owner decides whether any real run's output is
versioned). Live vs recorded-fixture judgement variance (expected, non-blocking): live
set `is_new_subcluster=false` + angle "Proteção do lar / ritual de mudança para casa
nova" (an existing named sub-angle) where the fixture frames it as a new angle
(`is_new_subcluster=true`); both are valid `MAP_TO_EXISTING` and neither is pinned for
live runs.

**Future cleanup (flagged, not done):** extract the modules both stages share into a
`src/engine_core/` package.

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

- **Scope:** `docs/TECHNICAL-SPEC-V1.md` covers canonical pipeline stages 1–2 only —
  `Market Intelligence → Opportunity Analysis → Opportunity Report` — run as one functional
  workflow. Canonical **stage 3 (Cluster Strategy)** is implemented and merged as a separate
  sibling package `src/cluster_strategy/` under its own contract
  `docs/CLUSTER-STRATEGY-V1.md` (see the **Cluster Strategy (canonical stage 3)** section).
  **Stages 4–13 remain out of scope / DEFERRED (P4)** (C7, C8).
- **Shape:** a deterministic sequential orchestrator over a **modular pipeline of specialized
  components** (I8) — Knowledge Loader → 1 Signal Collection → 2 Signal Normalization →
  3 Analysis/Framing → 4 Asset Matching → 5 Evaluation → 6 Ranking/Prioritization →
  7 Report Generation → Registry Updater. No monolithic prompt, no multi-agent orchestration.
- **Implementation status:** the **whole stage-1–2 pipeline is implemented, committed and
  pushed**; the C10 gate passed (`39fe464`). Canonical stage 3 (`src/cluster_strategy/`)
  is merged on top (PR #1, `3084f50`) and validated live (2026-09-03). See **Current
  Phase** for the per-component picture.
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

- **D1 — Business DNA V1 vs the V1 contract (owner, 2026-08-31):** `AI Music Media Engine —
  Business DNA V1.md` is the **strategic vision**, not implementation governance.
  **C6 / I2 / C7-C8 / I4 remain the operational V1 contract** — no 0–100 score, no
  operational LAUNCH/SCALE/KILL, V1 = canonical stages 1–2, the 9-section report is
  unchanged. Full record in **Open Issues → D1**.
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

**Cluster Strategy V1 live validation + doc hygiene (2026-09-03).** After the PR #1 merge
(below), the stage was run once against the real Anthropic API on Run 1's advanced
opportunity `opp_2026-08-31_1bca4af972` — see **Cluster Strategy (stage 3) → Live
validation** above for the full result. Headline: `MAP_TO_EXISTING → limpeza-energetica`,
`opportunity_lifecycle_state = EXPLORE` preserved, `write_registry_link: false` so
`knowledge/` was untouched, deterministic re-validation of the output returned 0 findings,
**617 pytest tests green, `ruff check src tests` clean**. The two generated files under
`reports/cluster-strategy/` are left untracked/uncommitted. Two documentation-hygiene
edits followed (this change): the contract §12 worked example now shows
`opportunity_lifecycle_state = EXPLORE` (was `TEST`, a lag behind the authoritative
sections), and this file records the live run.

**Prior step — Cluster Strategy V1 (canonical stage 3) merged to `main` (2026-09-03).**
PR #1 was merged (rebase merge, fast-forward), `main` fast-forwarded to `3084f50`
(`feat: implement Cluster Strategy (canonical pipeline stage 3)`), and the
`feat/cluster-strategy-stage-3` branch was deleted locally and remotely. `docs/SESSION-STATE.md`
was then refreshed post-merge and pushed (`8b711bd`). The four intentionally-untracked
owner files (`config/run.live-01.yaml`, `scripts/run-live.sh`,
`tests/test_run_live_script.py`, `AI Music Media Engine — Business DNA V1.md`) remain
untracked and were not part of any commit.

### Earlier history

**Targeted live validation of Asset Matching + Evaluation (2026-08-31, working tree).**
Offline: reconstructed the 13 `live_02` FramedOpportunities, picked the first 3 by
`opportunity_id`. Live (Keychain-sourced key, via a scratchpad harness — same mechanism
as `scripts/run-live.sh`): 1-token balance probe (OK) → 3 Matching calls → 3 Evaluation
calls.

- **Asset Matching: 3/3 PASS.** Real responses captured at
  `tests/fixtures/replay/live_02/llm/matching/`; regression test
  `test_replay_live_02_matching.py` (6). A first attempt failed on
  `stop_reason=max_tokens` → fixed with `_STAGE_OUTPUT["matching"]`
  (`max_tokens: 16000, effort: "low"`).
- **Evaluation: 0/3 — grammar-size 400 persists.** Not auto-fixed; owner decision
  pending (Open Issues → Evaluation schema).

**Earlier the same day — V1 hardening + operability pass:**

- `gate.py` + the `gate` CLI command — the C10 3-run Definition-of-Done checker the
  spec requires (§21.1, §22) but that had never been built. `tests/test_gate.py` (13),
  `tests/test_cli.py` (5).
- Robust Anthropic-response parsing in `normalize/llm.py` (the last call site still on
  the weak parser — `stop_reason` / block types / refusal / truncation are now named).
- `call_stage` retries once on a transient live `ResponseRejected` (spec §14).
- `matching._artist_candidates` — §10.2a fix: every artist is now a candidate (was
  gated on cluster/lexical match).
- `run` CLI surfaces technical failures separately and prints artifact locations.
- 4 reviewer agent definitions under `.claude/agents/` (implementation-conformance,
  security, replay-integration, report-quality) beside the existing spec-consistency
  reviewer.

An **implementation-conformance review** (`.claude/agents/implementation-conformance-reviewer`)
found and this pass fixed: (1) HIGH — `matching._artist_candidates` dropped a non-hero
artist whose catalog affinity did not match the opportunity's cluster and whose name had
no lexical overlap, violating **§10.2a** (DECIDED: catalog affinity is not an eligibility
filter). Now **every** artist is an Asset-Matching candidate; the cluster relation only
sets whether an `OBSERVED` fit basis is available. (2) MEDIUM — `call_stage` now **retries
once** on a transient `ResponseRejected` from a live client (spec §14), skipping the retry
for truncation / refusal which an identical call cannot fix.

**533 pytest tests green, `ruff check src tests` clean, `preflight` OK,
`run config/run.pipeline.replay.example.yaml` OK offline (deterministic across re-runs
except the recorded wall-clock `generated_at` and measured stage timings — §16.4).**

Prior committed work (`8e13e62` "implement V1 Market Intelligence pipeline" and the
`fix:` commits through `5d9781f`): the full stage-1–2 pipeline; the "technical failure
≠ business exclusion ≠ PARK" mechanism; the Evaluation schema flattened to fit the
Anthropic grammar-size limit; 7 Anthropic-API robustness fixes; two live replay
fixtures (`live_01` 37 signals, `live_02` 23 signals + a real 13-opportunity Framing
response).

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
8b711bd  docs: refresh session state after cluster strategy merge   (origin/main)
```

Refreshed this file after the PR #1 merge; single-file commit, pushed to `origin/main`.
The Cluster Strategy V1 build itself is the prior commit `3084f50`
(`feat: implement Cluster Strategy (canonical pipeline stage 3)`) — **merged to `main` on
2026-09-03** via PR #1 (rebase merge, fast-forward; same content committed 2026-09-01 on
branch `feat/cluster-strategy-stage-3` as `8ac61b9`, re-hashed by the rebase). That merge
commit staged: `src/cluster_strategy/` (whole package),
`config/cluster-strategy.example.yaml`, `docs/CLUSTER-STRATEGY-V1.md`,
`tests/test_cluster_strategy_*.py` (11), `tests/fixtures/cluster_strategy*/` (6 dirs); and
modified `knowledge/DECISIONS-NEEDED.md` (D-CS-1 … D-CS-12 in new §4; P4 entry —
owner-authorised), `docs/TECHNICAL-SPEC-V1.md` (§17 one sentence), `docs/SESSION-STATE.md`.

Recent history:

```
8b711bd  docs: refresh session state after cluster strategy merge      (origin/main)
3084f50  feat: implement Cluster Strategy (canonical pipeline stage 3)
39fe464  chore: validate V1 through C10 gate
ac117d6  chore: record C10 validation Run 1 (run_2026-08-31_01)
1c6a0ca  feat: carry evaluation red flags into the excluded/parked artifacts
6f9060e  feat: harden V1 for live end-to-end and add the C10 gate checker
5d9781f  fix: harden evaluation failures and structured output schema
f1e0100  test: preserve live framing replay fixture
f57d4c7  fix: harden framing and preserve live run replay fixture
9b06f77  fix: run Web Search structuring at effort=low
```

**Uncommitted (this doc-hygiene change, 2026-09-03):** `docs/CLUSTER-STRATEGY-V1.md` (§12
worked example: `opportunity_lifecycle_state` `TEST` → `EXPLORE`) and `docs/SESSION-STATE.md`
(this refresh). Nothing else tracked is modified.

**Untracked — the four intentionally-excluded owner files, none ever to be committed:**

- `config/run.live-01.yaml`, `scripts/run-live.sh`, `tests/test_run_live_script.py` — the
  Keychain live-run wrapper and its config/tests; kept out of the repo per the owner's
  credential-isolation instruction.
- `AI Music Media Engine — Business DNA V1.md` at the repo root — the business's
  **strategic vision / evolution architecture**. Per **owner decision D1 (2026-08-31)** it
  does **not** supersede the DECIDED decisions governing the current V1 (see
  **Open Issues → D1**). Whether/where it is committed is an owner call.

**Untracked — live validation output:** `reports/cluster-strategy/opp_2026-08-31_1bca4af972.{md,json}`
from the 2026-09-03 live run. Left uncommitted (a validation run on the example config,
not a committed stage-3 deliverable).

**`CLAUDE.md`, `knowledge/business-dna/*`, `knowledge/clusters/cluster-taxonomy.md`,
`knowledge/rules/guardrails.yaml`, the inventories, and all stage-1–2 and
`src/cluster_strategy/` code are untouched.**

## Current Repository State

- **Branch:** `main`
- **Remote:** `origin` → `https://github.com/divinetonesmusic-spec/ai-music-media-engine.git` (PRIVATE)
- **Relation to `origin/main`:** local `HEAD` = `origin/main` = **`8b711bd`**. Two tracked
  doc files are modified locally and **not yet committed** (the doc-hygiene change above).
- **PR #1** (`feat: Cluster Strategy — canonical pipeline stage 3`): **MERGED** (2026-09-03).
  The `feat/cluster-strategy-stage-3` branch was deleted locally and remotely.
- **Working tree:** `docs/CLUSTER-STRATEGY-V1.md` + `docs/SESSION-STATE.md` modified
  (uncommitted); the four intentionally-untracked owner files; the untracked
  `reports/cluster-strategy/` live output. `.venv/`, `/data/` and Python artifacts are
  git-ignored; tests write only under pytest `tmp_path`; no test touches the network.
- **Local runtime:** Python 3.12.14 in `.venv/`; `pip install -e ".[dev]"` (PyYAML,
  anthropic, pytest, ruff). **617 tests green**, `ruff check src tests` clean.

## Next Action

**Stages 1–2 are done and C10-validated (`39fe464`, pushed). Stage 3 (Cluster Strategy) is
COMPLETE, MERGED (`3084f50`, PR #1) and now validated live against the real Anthropic API
(2026-09-03). Canonical stages 4–13 remain DEFERRED (P4) — do not build them.** No pending
build work; one uncommitted doc-hygiene change (see **Last Commit**). The real strategic
choices are the three **owner quality decisions** (none blocking anything):

1. **value-engine weighting for ranking** — `NEEDS_INPUT` → spec §11 comparator keys 3–4;
   V1 uses the ordinal `TECHNICAL DEFAULT` comparator until the owner provides it.
2. **musical DNA detail** — instrumentation, energy, duration, texture, BPM, use of
   frequencies, vocal/instrumental. While `NEEDS_INPUT` it structurally caps `music_fit`
   (MI) and `market_language_fit` / `music_relationship` (Cluster Strategy) confidence at
   `MEDIUM`.
3. **the rating-anchors appendix** (spec §8.3) — to be written alongside the first real
   run; calibration is deferred (P1).

The optional live Cluster Strategy run is **done** (2026-09-03) — `MAP_TO_EXISTING →
limpeza-energetica`, lifecycle `EXPLORE` preserved, `write_registry_link: false` so
`knowledge/` untouched, deterministic validation clean, 617 tests + ruff green; the two
output files under `reports/cluster-strategy/` are left untracked. To re-run:
`./.venv/bin/python -m cluster_strategy reports/run_2026-08-31_01/opp_2026-08-31_1bca4af972.json
--config config/cluster-strategy.example.yaml --project-root .` with `ANTHROPIC_API_KEY`
in the environment (Keychain-sourced; `run-live.sh` itself is hardcoded to
`-m market_intelligence`). Keep `write_registry_link: false` unless the registry link
should be recorded.

**How to run stages 1–2:** `./.venv/bin/python -m market_intelligence run <config>` — or
`config/run.pipeline.replay.example.yaml` for a fully offline demo.
**How to run stage 3 (offline):** `./.venv/bin/python -m cluster_strategy
reports/run_2026-08-31_01/opp_2026-08-31_1bca4af972.json --config
<a config with replay.enabled: true> --project-root .`

## Open Issues

### V1 pipeline — known limitations / deliberate partial implementations

Surfaced by the spec-consistency + code reviews; each is a documented gap, not a bug:

- **Compliance enforcement depth (spec §13/§19).** Deterministic scanners exist only for the
  explicit disease-claim constructions of **G01/G03/G04**; G05–G10 rely on the Claude
  self-check now enumerated in the Evaluation prompt. There is **no separate live
  "reject_and_revise → one revision pass" loop** — Claude revises in-line within its single
  call, and deterministic escalation (strip the offending hypothesis, or exclude on core
  content) handles the rest. `require_uncertainty_statement` (G10) rendering is wired
  (`ComplianceResult.needs_uncertainty_note`) but dormant (no G10 scanner). The C10 gate
  passed with this enforcement depth (2026-09-01), so it is accepted for V1; a fuller
  `reject_and_revise` loop remains a possible later enhancement, not a blocker.
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
### Evaluation — structured outputs removed (owner-approved fallback C, 2026-08-31)

**Resolved in code; one sub-question open.** The `5d9781f` flatten did not clear the
grammar-size limit (confirmed live: 3/3 calls `400 "compiled grammar is too large …
reduce the number of strict tools"`). The owner approved **fallback C**: Evaluation
sends no `output_config.format`.

Final Evaluation architecture:
`Claude (prompt-guided JSON, effort default `high`, `max_tokens: 24000`, NO schema)`
→ `_response_to_json_object(msg, stage="evaluation", lenient=True)` — strips a ``` fence
   / prose preamble, joins JSON split across text blocks, rejects a top-level array, names
   `stop_reason` / refusal / truncation
→ `_reject_malformed_evaluation(raw)` — strict: exactly the 10 `DIMENSION_KEYS` + 5
   `AXIS_KEYS`; each rating node `{rating∈Rating, confidence∈Confidence, non-empty
   justification[, blocked_by: [str]]}`; `red_flags` a list of `{description, severity∈
   Severity, kind∈RedFlagKind}`; valid `overall_confidence`, non-empty `summary`; a
   `recommendation` with `target_state∈LifecycleState`, non-empty `suggested_next_step` /
   `justification`, valid `confidence`; **no 0–100 score** anywhere
   (`scan_json_for_numeric_score`). ANY deviation → `ResponseRejected` → `technical_failure`
   (never PARK, never registry). `call_stage` retries a transient `ResponseRejected` once.
→ `_build_bundle(raw)` — the §13 business layer, **unchanged** (coercion kept as a second
   net; `validate_evaluation` / `validate_business_outcome_profile` / compliance / the
   `music_fit` cap / `_constrain_target_state` / `EXECUTION_NOTE` all still run).

`evaluation._response_schema()` is kept as the machine-readable *reference* shape (not
sent); `test_structured_output_schema.py` pins it to the strict validator's key sets.

**Isolated live validation (2026-08-31) — 3/3 PASS.** `output_config` = None on every
call → the grammar 400 is **gone**. First run: 2/3 clean + 1 model property-name JSON
slip (`stop_reason=end_turn`, 6463 tokens — not truncation, not the 400) → correctly a
`technical_failure`. Re-run with `call_stage`'s retry-once enabled: the 3rd opp passed on
the first attempt (no retry needed — the slip was a one-off). **All 3 real fixtures
captured** (`tests/fixtures/replay/live_02/llm/evaluation/`, secret-clean); all 3
deterministic-valid; all 3 flow through Ranking. Regression: `test_replay_live_02_evaluation.py`.
The lenient parser was **not** made to tolerate trailing commas / `//` — `call_stage`'s
retry-once is the safety net for a transient model JSON slip, and a live re-attempt
produced clean JSON directly.

### D1 — Business DNA V1 vs the current V1 contract — RESOLVED (owner, 2026-08-31)

An untracked strategic document, `AI Music Media Engine — Business DNA V1.md`, was added
at the repo root. It is a broad vision doc (the full 9-stage system, agent hierarchy).
Where it specifies **V1 mechanics** it diverges from DECIDED decisions:

| Business DNA V1 | Diverges from | Current behaviour (kept) |
|---|---|---|
| §8 — every opportunity gets a **0–100 Opportunity Score** with a weighted formula (Trend 25% / Audience 15% / …) | **C6** (DECIDED: no composite 0–100 score) + spec §8 | qualitative 10-dimension profile, `rating` + separate `confidence`, no score; `_scan_for_numeric_score` rejects any 0–100 score in evaluation / BOP / recommendation |
| §9 / §10 — recommendation set is **EXPLORE / TEST / LAUNCH / SCALE / KILL** (no PARK) | **I2** (DECIDED: V1 operational states are EXPLORE / TEST / PARK; LAUNCH/SCALE/KILL deferred) | `_constrain_target_state` clamps to EXPLORE / TEST / PARK (KILL→PARK, LAUNCH/SCALE→TEST) |
| §35 — "V1 will have: MARKET INTELLIGENCE → OPPORTUNITY REPORT → OPPORTUNITY SCORE → **CLUSTER STRATEGY → CONTENT PLAN**" | **C7 / C8** (DECIDED: V1 = canonical stages 1–2 only) + spec §2 | V1 stops at the Opportunity Report; cluster / positioning / first-content-direction are non-binding hypotheses only; no Cluster Strategy / Content Plan stage exists |
| §10 — Opportunity Report has **Conteúdo** (formats, hooks, structures, pillars, duration…) and **Execução** (batch sizes, templates, schedule) as required sections | **I4** (DECIDED: the 9-section report schema) + **C7** | 9 sections per I4; content/execution detail is out of V1 scope |

**Owner decision (Nicolas Alves, 2026-08-31):** for the current implementation,
**C6 / I2 / C7-C8 / I4 remain the operational V1 contract.** `AI Music Media Engine —
Business DNA V1.md` represents the **strategic vision and the business's evolution
architecture** — it does **not** supersede the DECIDED decisions that govern the current
V1 implementation. Consequently: do **not** implement a 0–100 score; do **not** implement
LAUNCH/SCALE/KILL operationally in V1; do **not** build Cluster Strategy or Content Plan
as pipeline stages yet; do **not** change the Opportunity Report contract; do **not**
change the current architecture. The canonical stages 3–13 (incl. Cluster Strategy,
Content Plan) stay **deferred (P4)** until the V1 C10 gate passes.

This decision is recorded here only. `knowledge/DECISIONS-NEEDED.md` is human-owned
source knowledge protected by the `guard-knowledge` PreToolUse hook (fail-closed); the
project process is that a Claude Code session does not edit it. If the owner wants D1
folded into that file (e.g. a note under C6 / C7 / I2 / I4, or the P4 entry), that is a
manual owner edit — the minimal text to paste is the "Owner decision" paragraph above.
No decision `status` changes: C6 / I2 / C7 / C8 / I4 were already `DECIDED`; D1 only
reaffirms them against a newer document.

**Update (2026-09-01).** D1's precondition — "stages 3–13 stay deferred until the V1 C10
gate passes" — is now satisfied: C10 passed and is recorded (`39fe464`). The owner then
opened **canonical stage 3 (Cluster Strategy) only** and decided D-CS-1 … D-CS-12, all
recorded in `knowledge/DECISIONS-NEEDED.md` §4 with the P4 entry updated (this session
edited that file under an explicit owner authorisation; the `guard-knowledge` hook was
bypassed via a script for that one edit only, not disabled). D1's substance is unchanged:
no 0–100 score (C6); no LAUNCH/SCALE/KILL operationally (I2); the Opportunity Report
contract (I4) untouched; and stages 4–13 stay DEFERRED. Cluster Strategy V1 keeps the
established V1 boundary (D-CS-8) — it does not build page design or a content system.

**Verified 2026-08-31 that the current code still obeys the contract** (see
`pytest -q` / `ruff` / `preflight`, all green; and the checks in **Last Completed Step**):
`_scan_for_numeric_score` wired into all three validators; no `score` field on any model;
`ranking` is a purely ordinal comparator (`config/ranking.yaml`:
`value_engine_weighting: NEEDS_INPUT`, not applied); `V1_OPERATIONAL_STATES = {EXPLORE,
TEST, PARK}`; `_constrain_target_state` enforced; the 8-stage orchestrator ends at
Report + Registry; no `cluster` / `content` / `page-blueprint` / `video` / `audio` /
`publishing` / `analytics` / `optimization` / `learning` module exists; the report
renders exactly the 9 I4 sections in order.

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
- **P4** — pipeline stages 3–13 (Cluster Strategy → Learning). **Stage 3 (Cluster Strategy)
  is DONE, MERGED and LIVE-VALIDATED** (merged 2026-09-03, PR #1, `3084f50`; one real
  Anthropic run 2026-09-03 → `MAP_TO_EXISTING → limpeza-energetica`, lifecycle `EXPLORE`
  preserved, deterministic validation clean): C10 passed and is recorded (`39fe464`); the
  owner opened stage 3 via **D-CS-1** and decided **D-CS-1 … D-CS-12**, all recorded in
  `knowledge/DECISIONS-NEEDED.md` §4 ("# 4. ESTÁGIO 3 — CLUSTER STRATEGY") with the P4
  entry updated. **Stages 4–13 stay DEFERRED under P4 — a new session must not build
  them.**
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
7. **V1 stages 1–2 are complete, C10-validated, committed and pushed (`39fe464`). Stage 3
   (Cluster Strategy) is complete, merged (`3084f50`, PR #1) and live-validated
   (2026-09-03).** Stages 4–13 stay deferred (P4) — the next step is **not** more building
   (see **Next Action**: the three owner quality decisions). Set up the environment first:
   `python3.12 -m venv .venv && ./.venv/bin/python -m pip install -e ".[dev]"`, then
   `./.venv/bin/python -m pytest` and `./.venv/bin/ruff check src tests` should be green
   (**617 tests**), and
   `./.venv/bin/python -m market_intelligence run config/run.pipeline.replay.example.yaml`
   should print `RUN OK`.
