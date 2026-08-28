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
specification are complete and reconciled. **V1 implementation has started** (owner
authorized code on 2026-08-28). The **Foundation layer** — controlled vocabularies,
dataclass schemas + codec, deterministic ids, §13 validators, config loading, Knowledge
Loader, preflight — is implemented and test-covered on **Python 3.12** (124 pytest tests
green, `ruff` clean). **Signal Collection and everything after it are not built yet.**

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
- **Implementation status:** **Foundation done** (`market_intelligence.{schema.*, config.loader,
  io_utils, knowledge_loader, preflight}`). Signal Collection onward **not started**. The
  orchestrator itself is not written yet — `preflight` covers the `load config → Knowledge
  Loader` head of §5.
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

Migrated the V1 dev/runtime to **Python 3.12** (owner decision — 3.9 is EOL): installed
Homebrew `python@3.12` (3.12.14), recreated `.venv` on it, set
`requires-python = ">=3.12,<3.13"` and `ruff` `target-version = "py312"`, reinstalled deps.
**No source changes were needed** — the codebase was already 3.12-compatible (`typing.Optional/
List` + `from __future__ import annotations` retained on purpose; codec resolves annotations
at runtime). `pytest` (124 passed), `ruff check src tests` (clean) and
`python -m market_intelligence preflight config/run.example.yaml` (`PREFLIGHT OK`, exit 0)
all pass on 3.12. Preceded, in the same session, by the full V1 Foundation-layer
implementation (schemas → codec → ids → §13 validators → fixtures → config loader →
Knowledge Loader → preflight). **Nothing committed.**

## Last Commit

```
0ee23b1  chore: add project engineering guardrails and session state
```

Full hash: `0ee23b1bd2a347147dd98c6575cf74824cde44de` — 2026-08-28T12:44:16-03:00
Files: `.claude/hooks/{guard-knowledge,block-dangerous-git}.sh`, `.claude/settings.json`,
`.claude/agents/spec-consistency-reviewer.md`, `.claude/skills/update-session-state/SKILL.md`,
`docs/SESSION-STATE.md` (new).

Recent history:

```
0ee23b1  chore: add project engineering guardrails and session state
b8fec98  feat: finalize market intelligence v1 specification
2154c07  feat: V1 knowledge base — asset classification, cluster taxonomy, technical spec
d236323  docs: reconcile V1 project specification
859c731  chore: ignore .DS_Store files
cf76fe1  chore: finalize V1 business decisions and inventories
00600cc  chore: initialize AI Music Media Engine
```

**Uncommitted working tree** (the entire V1 Foundation + the Python 3.12 migration — awaiting
owner review; nothing has been committed or pushed):

- Modified: `.gitignore`, `README.md`, `docs/SESSION-STATE.md` (this file).
- Untracked: `pyproject.toml`, `config/` (3 files), `src/` (13 modules), `tests/`
  (10 files + `fixtures/`).
- Git-ignored, present locally: `.venv/` (Python 3.12), `*.egg-info/`.

## Current Repository State

- **Branch:** `main`
- **Remote:** `origin` → `https://github.com/divinetonesmusic-spec/ai-music-media-engine.git` (PRIVATE)
- **Relation to `origin/main`:** committed history is **in sync** — local `HEAD` ==
  `origin/main` == `0ee23b1` (`git rev-list --left-right --count origin/main...HEAD` → `0 0`).
  The Foundation work sits on top as **uncommitted changes**.
- **Working tree:** **not clean** — modified `.gitignore`, `README.md`, `docs/SESSION-STATE.md`;
  untracked `pyproject.toml`, `config/`, `src/`, `tests/`. (`.venv/`, `/data/` and Python
  artifacts are git-ignored.)
- **Local runtime:** Python 3.12.14 in `.venv/`; `pip install -e ".[dev]"` (PyYAML, pytest, ruff).

## Next Action

Continue V1 pipeline implementation from where the Foundation stopped. The Foundation is
**validated** (124 tests green, `ruff` clean, `preflight` OK) and owner-authorized — **cleared
to proceed**. TDD with `pytest`, per spec §22; deterministic parts before Claude-in-the-loop,
per §18.

Build the remaining §18 components in order:

1. **Signal Collection** (§18 component 1, §6.5) — 4 modular collectors behind the one
   `Signal` output contract: Claude API server-side Web Search (live); YouTube Data API
   (key via env var); TikTok Creative Center analyst-capture file; internal-data YAML/CSV.
   Write one raw capture per signal to `data/<run_id>/signals/raw/<signal_id>.json`. Degrade
   per source; hard-fail only if all fail. Plus **`replay` mode** (read fixtures, no network).
2. **Signal Normalization** (§6.6) — validate each `Signal` (`validate_signals`), assign ids,
   deduplicate using `config/dedup.yaml`; Claude fills ambiguous `signal_type` / `market` /
   `language` / `durability_hint`.
3. **Analysis / Framing** → 4. **Asset Matching** → 5. **Evaluation** (+ guardrail check
   against `guardrails.yaml`) → 6. **Ranking / Prioritization** (`config/ranking.yaml`
   comparator) → 7. **Report Generation** (9-section Markdown + JSON sidecar + `digest.md` +
   `review.md`) → **Registry Updater** (append-only `knowledge/market/opportunity-registry.yaml`).
8. **Orchestrator** — wire `preflight → stages 1–7 → digest`; `dry_run` stops after Framing.

Reuse the existing layer: `schema.models` for every entity, `schema.validate` for §13,
`schema.ids` for id assignment, `knowledge_loader.KnowledgeBundle` +
`validate.InventoryIndex` for asset matching, `config.loader` for `ranking.yaml` / `dedup.yaml`.

**Owner decisions that gate later stages** (do not block Signal Collection): value-engine
weighting for ranking; musical DNA detail (caps `music_fit` confidence); the rating-anchors
appendix (§8.3), to be written alongside the first real run.

## Open Issues

Still open and relevant to the next step:

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
7. V1 implementation is **in progress and owner-authorized**. The Foundation layer is built;
   the next step is Signal Collection and the remaining §18 components (see **Next Action**).
   Set up the environment first: `python3.12 -m venv .venv && ./.venv/bin/python -m pip
   install -e ".[dev]"`, then `./.venv/bin/python -m pytest` and
   `./.venv/bin/ruff check src tests` should be green before making changes.
