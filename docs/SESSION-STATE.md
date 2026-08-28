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

**V1 — Market Intelligence + Opportunity Analysis.** The full V1 knowledge base and the
technical specification are complete and internally reconciled; **no pipeline code has been
written yet** and the project is at the point of starting V1 implementation.

## Completed

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

## Current Architecture

Per `docs/TECHNICAL-SPEC-V1.md` (the authoritative implementation spec):

- **Scope:** canonical pipeline stages 1–2 only —
  `Market Intelligence → Opportunity Analysis → Opportunity Report` — run as one functional
  workflow. Stages 3–13 are out of scope (C7, C8).
- **Shape:** a deterministic sequential orchestrator over a **modular pipeline of specialized
  components** (I8) — Knowledge Loader → 1 Signal Collection → 2 Signal Normalization →
  3 Analysis/Framing → 4 Asset Matching → 5 Evaluation → 6 Ranking/Prioritization →
  7 Report Generation → Registry Updater. No monolithic prompt, no multi-agent orchestration.
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
- **Stack (I10):** Python 3, Claude, YAML + Markdown + JSON, Git. No database, queue or
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

Minimal revision of `docs/TECHNICAL-SPEC-V1.md` following the Implementation Readiness
Review, plus creation of `knowledge/rules/guardrails.yaml` (10 guardrails `G01`–`G10`).
This resolved the single BLOCKER (signal-collection mechanism undefined) and all
NEEDS_CLARIFICATION items without changing the approved architecture; the re-run readiness
verdict is **READY**. Committed and pushed.

## Last Commit

```
b8fec98  feat: finalize market intelligence v1 specification
```

Full hash: `b8fec980d0c2e0f2de2916e77b979b773b4705f5`
Files: `docs/TECHNICAL-SPEC-V1.md` (modified), `knowledge/rules/guardrails.yaml` (new).

Recent history:

```
b8fec98  feat: finalize market intelligence v1 specification
2154c07  feat: V1 knowledge base — asset classification, cluster taxonomy, technical spec
d236323  docs: reconcile V1 project specification
859c731  chore: ignore .DS_Store files
cf76fe1  chore: finalize V1 business decisions and inventories
00600cc  chore: initialize AI Music Media Engine
```

## Current Repository State

- **Branch:** `main`
- **Remote:** `origin` → `https://github.com/divinetonesmusic-spec/ai-music-media-engine.git` (PRIVATE)
- **Relation to `origin/main`:** in sync — local `HEAD` == `origin/main` == `b8fec98`.
- **Expected working tree:** clean (`nothing to commit`). Only untracked artifacts expected
  are OS files already ignored (`.DS_Store`).

## Next Action

Begin **V1 pipeline implementation** in Python 3, following `docs/TECHNICAL-SPEC-V1.md`
(TDD with `pytest`, per §22). Concrete first steps:

1. Scaffold the project layout from spec §17 (`config/`, `data/`, `reports/`, package dirs)
   and add `data/` to `.gitignore` (`TECHNICAL DEFAULT`).
2. Write the deterministic schema validators (§6, §7, §8, §9, §10, §12, §16, §20) with
   valid/invalid fixture pairs — one invalid case per §13 rule.
3. Create the config data files: `config/run.example.yaml`, `config/ranking.yaml`,
   `config/dedup.yaml`.
4. Implement the Knowledge Loader (§18) — load `business-dna.md`, `guardrails.yaml` (10
   entries), `cluster-taxonomy.md` (11 ids), the 4 inventories and the registry; hard-fail
   on any missing required file.
5. Build the pipeline components in order (§18), deterministic parts first, then the
   Claude-in-the-loop steps; then `replay` mode.

**This requires explicit owner authorization to start writing code** — every prior step in
this project was done under a "no production code yet" constraint.

## Open Issues

Still open and relevant to the next step:

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
6. Keep any ETL / validation scripts out of the repo (use a scratch/tmp directory).
7. The natural next step is V1 implementation (see **Next Action**) — but confirm the owner
   wants code written before starting.
