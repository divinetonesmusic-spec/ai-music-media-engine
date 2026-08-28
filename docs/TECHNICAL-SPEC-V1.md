---
title: Technical Specification — Market Intelligence V1
status: draft
created: "2026-08-27"
revised: "2026-08-28"
revision_note: "Implementation Readiness Review pass — concrete signal-collection mechanism, Provenance schema, dedup rule, guardrails.yaml, cluster & market taxonomy, review.md gate, replay mode. Architecture unchanged."
owner: Nicolas Alves (divinetonesmusic@gmail.com)
sources_of_truth:
  - CLAUDE.md
  - knowledge/DECISIONS-NEEDED.md
  - knowledge/business-dna/business-dna.md
  - knowledge/business-dna/content-methodology.md
  - knowledge/clusters/cluster-taxonomy.md
  - knowledge/rules/guardrails.yaml
  - knowledge/inventories/*.yaml
schema_version: "1.0.0"
---

# Technical Specification — Market Intelligence V1

Defines exactly how the Market Intelligence V1 is implemented. **No production code here.**

**Conventions used in this document**

- **`TECHNICAL DEFAULT`** — a technical choice not yet formally decided in `DECISIONS-NEEDED.md`. The simplest option compatible with existing decisions was chosen and is marked so it can be revisited.
- **`MUST` / `MUST NOT` / `SHOULD`** — RFC-2119 sense.
- Every referenced decision id (`C1`–`C10`, `I1`–`I12`) points to `knowledge/DECISIONS-NEEDED.md`.
- Where this spec and a `DECIDED` decision disagree, the decision wins — fix the spec.

---

## 1. Objective and Scope

**Objective.** Implement the first two stages of the canonical pipeline (C8) as a single functional workflow that turns market signals into ranked, evidenced, evaluated Opportunity Reports.

```
Market Intelligence → Opportunity Analysis → Opportunity Report
```

- **Market Intelligence** — discovers, collects and organizes relevant market signals.
- **Opportunity Analysis** — structures, evaluates, compares and prioritizes opportunities based on evidence, the 10 evaluation dimensions, confidence, red flags and the Business Outcome Profile.

**In scope for V1 (C7):**

- discover opportunities from the V1 signal sources (C2);
- structure each into the `Opportunity` model (C1);
- record evidence with `OBSERVED` / `INFERRED` / `HYPOTHESIS` typing (I4);
- evaluate each opportunity (C6, C9) and build its Business Outcome Profile (C5);
- assess fit with existing assets from the inventory (I1, I5);
- rank and present at most 10 opportunities per run (I12);
- generate one Opportunity Report per presented opportunity (I4) plus a run digest;
- maintain a persistent opportunity registry (I2);
- provide light, non-binding hypotheses about potential cluster, positioning, page and first content direction (C7).

**Operating mode.** Every V1 output is a **recommendation**. The system never executes (Level 1 autonomy — CLAUDE.md §13). Advancing an opportunity, creating any asset, or publishing anything is a human action.

---

## 2. Out of Scope

Explicitly **not** built in V1 (C7, C8, I8, I10, and the DEFERRED decisions P1–P9):

- Cluster Strategy, Page Blueprint, Content Strategy, Content Production, Video Engine, Audio Engine, Quality Control, Publishing, Analytics, Optimization, Learning (canonical stages 3–13).
- Automated social publishing; any posting or scheduling.
- Batch generation of hooks, copy, visuals, videos or audio.
- Formal cluster governance / cluster creation (V1 only *proposes* a new cluster as a hypothesis — P6).
- Automatic creation of playlists, pages, artists or any asset (I5 — new assets are recommendations only).
- Automated lifecycle transitions and measurable criteria for `LAUNCH` / `SCALE` / `KILL` (I2, P2).
- Quantitative / numeric scoring model, weights, formulas (C6; reconsidered only with real data — P1).
- Analytics ingestion or performance-based calibration (P1).
- Paid APIs and additional data-source integrations beyond the four V1 sources (C2, P3).
- Database, message queue, long-running server (I10).
- Multi-agent orchestration; a monolithic single-prompt agent (I8).
- Cross-run dashboards / trend tracking UI (P7); prompt-versioning infrastructure beyond a config string (P8); a curated competitor base (P9).
- `Spotify` as a trend-discovery source (C2 — Spotify is used only for asset-fit context, later).

---

## 3. System Inputs

| Input | Form | Source of truth | Notes |
|---|---|---|---|
| Run configuration | `RunConfig` (§20) | operator-provided file / CLI | scope, sources, limits, model, paths, `replay` |
| Business DNA | Markdown + YAML front matter | `knowledge/business-dna/business-dna.md` | identity, monetization, markets, languages, positioning; some fields `NEEDS_INPUT` |
| Content methodology | Markdown | `knowledge/business-dna/content-methodology.md` | historical, **not rigid rules** (I11) |
| Compliance guardrails | **YAML (structured)** | `knowledge/rules/guardrails.yaml` | 10 machine-readable guardrails transcribed from C4 / `CLAUDE.md` §14. **The pipeline loads this file — it does NOT parse `CLAUDE.md` prose.** `CLAUDE.md` remains human context; operational enforcement uses this data. |
| Cluster taxonomy | Markdown + embedded YAML | `knowledge/clusters/cluster-taxonomy.md` | the 11 canonical V1 cluster ids; used to validate `potential_cluster` (§7.2, §13) |
| Asset inventory | YAML | `knowledge/inventories/{artists,playlists,pages,catalog}.yaml` | **only** source of asset truth (I1). Strategic classification is now **partly consolidated** (§10.1): some assets are classified, the rest are `NEEDS_INPUT`. |
| Opportunity registry | YAML | `knowledge/market/opportunity-registry.yaml` | prior opportunities + lifecycle state (I2). Written by the pipeline — governance exception documented in §17. |
| Live web results | text + provenance | **Claude API server-side Web Search** (C2) | live research tool. Each result recorded with query, source, url, `observed_at`, evidence. **Not** the model's internal knowledge (§6.5). |
| YouTube signals | structured | **YouTube Data API** (C2) | automatable, modular integration; supports `query`, `region`/`market`, `language` when available; query parameters recorded as provenance (§6.5). |
| TikTok Creative Center signals | structured file | **analyst/operator structured capture** (C2) | V1 has **no** free public API — the analyst captures observations into a structured input file; `source_type = tiktok_creative_center`. Automated integration is a future extension (§23). The workflow stays implementable with manual capture. |
| Internal business data | structured file(s) | operator-maintained, path in `RunConfig` | YAML or CSV; shape in §6.4 |

The **Knowledge Loader** (deterministic) loads Business DNA, `guardrails.yaml`, `cluster-taxonomy.md`, all four inventories and the registry into an in-memory context bundle. Missing *required* knowledge (any inventory file, `business-dna.md`, `guardrails.yaml`, `cluster-taxonomy.md`) is a **hard failure** (§14).

---

## 4. System Outputs

Written under `reports/<run_id>/` (durable, versioned — I7):

| Output | File | Format |
|---|---|---|
| Run digest | `digest.md` | Markdown + YAML front matter |
| Opportunity Report (per presented opportunity, ≤10) | `<opportunity_id>.md` | Markdown + YAML front matter (I4) |
| Structured sidecar (per report) | `<opportunity_id>.json` | JSON mirror of the structured record *(`TECHNICAL DEFAULT`)* |

Side effects:

| Effect | Location | Notes |
|---|---|---|
| Registry update | `knowledge/market/opportunity-registry.yaml` | **append-only** for opportunities and state-history entries (I2). Governance exception — see §17. Every change must be visible in `git diff`. |
| Raw captures & intermediates | `data/<run_id>/` | regenerable; `TECHNICAL DEFAULT`: `data/` is git-ignored (I7) |

The system **MUST NOT** write anywhere in `knowledge/` **except** `knowledge/market/opportunity-registry.yaml`, and **MUST NOT** modify the inventories, `business-dna.md`, `content-methodology.md`, `cluster-taxonomy.md`, `guardrails.yaml` or `DECISIONS-NEEDED.md`.

---

## 5. V1 Run Lifecycle

A run is a single invocation with one `RunConfig`. Deterministic orchestrator, sequential stages:

```
load & validate config
  → Knowledge Loader (business DNA, guardrails.yaml, cluster-taxonomy.md, 4 inventories, registry)   [hard-fail if required missing]
  → 1. Signal Collection  (or: load fixtures if RunConfig.replay.enabled)
  → 2. Signal Normalization
  → 3. Analysis / Framing
  → 4. Asset Matching
  → 5. Evaluation
  → 6. Ranking / Prioritization      (select ≤10 presented; rest → PARK)
  → 7. Opportunity Report Generation (reports + digest + sidecars)
  → Registry update
  → run digest finalization (sources used/failed, counts, timings, model, prompt_version)
```

**Opportunity lifecycle within the registry (I2, CLAUDE.md §9):**

- Conceptual long-term lifecycle: `EXPLORE → TEST → LAUNCH → SCALE → KILL`, with `PARK` as an additional pause/prioritization state.
- **Operational in V1:** `EXPLORE`, `TEST`, `PARK`.
- `TECHNICAL DEFAULT`: every newly created opportunity enters the registry with `status: EXPLORE`. Opportunities identified but not in the presented top-N are stored with `status: PARK`. The pipeline never sets `LAUNCH` / `SCALE` / `KILL` — those are conceptual and deferred.
- A `Recommendation.target_state` (§12) may name any conceptual state, but **V1 recommendations are constrained to `EXPLORE` / `TEST` / `PARK`** (`TECHNICAL DEFAULT`); a clearly weak opportunity is de-prioritized (dropped from top-N), not actively `KILL`ed.
- State changes are human-approved; the pipeline only *proposes* a `target_state`.

**Idempotency.** `TECHNICAL DEFAULT`: re-running with the same `run_id` overwrites that run's `reports/<run_id>/` and `data/<run_id>/`; registry entries are keyed by `opportunity_id` and updated in place (state-history appended, never rewritten).

---

## 6. Signal Model / Schema

A `Signal` is a normalized, atomic observation from one source. **A `Signal` is inherently `OBSERVED`**; inference and hypothesis are represented on the `Opportunity` (§7.3), not here.

### 6.1 `Signal`

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `signal_id` | string | yes | — | stable within a run. `TECHNICAL DEFAULT`: `sig_<run_id>_<NNNN>` (zero-padded counter) |
| `schema_version` | string (semver) | yes | `"1.0.0"` | |
| `run_id` | string | yes | — | FK → `RunConfig.run_id` |
| `source` | string | yes | — | human-readable origin (e.g. `"Google — search interest"`, `"YouTube Data API — search.list"`) — mirror of `provenance.source` |
| `source_type` | enum | yes | `web_search` \| `youtube` \| `tiktok_creative_center` \| `internal_data` | C2 — mirror of `provenance.source_type` |
| `url` | string \| `UNKNOWN` | no | — | present for a web resource — mirror of `provenance.url` |
| `observed_at` | date (ISO 8601, `YYYY-MM-DD`) | yes | — | when the phenomenon was observed — mirror of `provenance.observed_at` |
| `collected_at` | datetime (ISO 8601) | yes | — | when the run captured it — mirror of `provenance.collected_at` |
| `market` | enum | yes | `Brasil` \| `Mercados hispanohablantes` \| `English-speaking markets` \| `UNKNOWN` | V1 market taxonomy (§7.1a). No country-level taxonomy in V1. |
| `language` | enum | yes | `pt` \| `es` \| `en` \| `UNKNOWN` | ISO 639-1, restricted to V1 markets (business-dna §8) |
| `platform` | enum | yes | `tiktok` \| `youtube` \| `spotify` \| `instagram` \| `facebook` \| `web` \| `other` \| `UNKNOWN` | `TECHNICAL DEFAULT` enum |
| `signal_type` | enum | yes | see §6.2 | `TECHNICAL DEFAULT` starter set |
| `evidence` | string | yes | — | concise statement of what was observed (1–3 sentences) |
| `raw_excerpt` | string | no | — | verbatim snippet supporting `evidence` |
| `raw_ref` | string | yes | — | path to the raw capture file, `data/<run_id>/signals/raw/<signal_id>.json` (§6.6, §16) |
| `context` | string | yes | — | surrounding context needed to interpret the signal |
| `confidence` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | source reliability + specificity of the observation |
| `durability_hint` | enum \| `null` | no | `EPHEMERAL` \| `EMERGING` \| `STRUCTURAL` \| `EVERGREEN` \| `null` | optional per-signal temporal read (C2 asks the system to tell ephemeral / emerging / evergreen apart). It is a **hint only** — the formal `durability` classification is assigned to the `Opportunity` in Framing (§7.1, I9). |
| `metrics` | map<string, number \| string> | no | — | optional observed figures (e.g. `views`, `growth_rate`); `UNKNOWN` where a figure is not given — **never estimated** (G05 / C4.5) |
| `provenance` | `Provenance` | yes | §16 | full trace of why this signal exists (query/reference, url, capture method, source version). The top-level `source_type` / `market` / `language` are convenience mirrors of `provenance` fields. |

### 6.2 `signal_type` enum (`TECHNICAL DEFAULT`)

`search_trend` · `social_trend` · `hashtag` · `emerging_theme` · `content_format` · `competitor_activity` · `audience_behavior` · `emotional_need` · `regional_opportunity` · `language_opportunity` · `platform_opportunity` · `other`

Derived from CLAUDE.md §7. Extendable without schema change.

### 6.3 Validation rules

- `signal_id` unique within a run.
- `observed_at` `MUST NOT` be in the future relative to `collected_at`.
- `source_type` `MUST` be one of the four V1 sources (`web_search`, `youtube`, `tiktok_creative_center`, `internal_data`); a `Signal` from any other origin is rejected in Normalization.
- `market` `MUST` be one of the three V1 markets or `UNKNOWN` (§7.1a); `language` `MUST` be `pt`/`es`/`en`/`UNKNOWN`.
- `raw_ref` `MUST` resolve to an existing file at `data/<run_id>/signals/raw/<signal_id>.json` (§6.6).
- `provenance` `MUST` be present and complete for its `capture_method` (§16).
- `metrics` values that were not explicitly present in the source `MUST` be `UNKNOWN`, never a guess (G05).
- Deduplication (§6.6) runs after per-signal validation.

### 6.4 Internal business data input (`TECHNICAL DEFAULT`)

Operator-maintained file(s) at `RunConfig.internal_data_path`. Minimal shape — a list of records, each becoming one `Signal` with `source_type: internal_data`:

```yaml
- observed_at: "2026-08-20"
  market: "Brasil"
  language: "pt"
  platform: "tiktok"
  signal_type: "audience_behavior"
  evidence: "Own page X saw 3x saves-per-view on sleep-frequency reels in the last 30 days."
  context: "Internal page analytics, manually recorded."
  confidence: "MEDIUM"
  metrics: { saves_per_view_ratio: "0.04" }
```

### 6.5 Signal source mechanisms (V1)

Concrete, implementable collection for each `source_type`. All four are **modular** — each is
an independent collector behind the same `Signal` output contract; adding or replacing one
does not touch the rest of the pipeline (I8).

**`web_search` — Claude API server-side Web Search**

- Use the Claude API's **server-side Web Search tool** as a *live research* capability.
- It is a search-the-web-now tool — the pipeline `MUST` treat its results as live external
  observations, **not** as the model's internal/training knowledge. A "fact" the model
  states without a Web Search result backing it is not a `Signal`.
- For each result kept, record in `provenance`: the `query_or_reference` (the exact query
  string), `source` (result title/site), `url`, `observed_at` (result/article date, or
  `UNKNOWN`), and `evidence` (what was observed).
- `capture_method: claude_web_search`.

**`youtube` — YouTube Data API**

- Use the **YouTube Data API** as an automatable research source (modular integration,
  API key via env var — §20.2).
- V1 supports at least: `query`; `region`/`market` and `language` (`relevanceLanguage`)
  when available. Endpoint set is a `TECHNICAL DEFAULT` (e.g. `search.list`, `videos.list`).
- Record in `provenance`: `query_or_reference` = the API request (endpoint + parameters),
  `source` = `"YouTube Data API — <endpoint>"`, `url` = canonical watch/channel URL when a
  specific resource, `source_version` = API version string.
- `capture_method: youtube_data_api`.

**`tiktok_creative_center` — analyst / operator structured capture**

- V1 assumes **no free public API**. The analyst/operator manually reviews TikTok Creative
  Center and records observations into a **structured capture file** (`RunConfig` path;
  same shape family as §6.4, but `source_type: tiktok_creative_center` and each record
  carries its own `provenance` with `capture_method: analyst_capture`, `source` =
  `"TikTok Creative Center — <panel>"`, `observed_at`, `url` when the panel exposes one,
  `query_or_reference` = the filter/panel used).
- The run `MUST` remain fully executable with only the manual capture present.
- Automated TikTok Creative Center integration is a **future extension** (§23); when it
  exists it plugs in behind the same `source_type` with a different `capture_method`.

**`internal_data` — operator YAML/CSV** — as §6.4. `capture_method: internal_data`.

### 6.6 Deduplication (deterministic)

Runs in Signal Normalization after per-signal validation.

**Dedup key** (all lowercased/trimmed; a missing part contributes the literal `∅`):

```
dedup_key = (
  normalized_source,          # provenance.source with tracking params stripped, case-folded
  canonical_url ?? ∅,         # url with query/fragment stripped and host lowercased; ∅ if none
  market,
  language,
  platform,
  signal_type,
  normalized_subject          # kebab-cased key phrase of evidence/query, stopwords removed
)
```

- Two signals are **duplicates** only if they share the **same `dedup_key`** *and* the
  same `observed_at` (same calendar day).
- On a duplicate, keep the one with the higher `confidence` (tie → lower `signal_id`);
  merge the other's `metrics` keys that are absent in the kept one; record the dropped
  `signal_id` in `data/<run_id>/run.log`.
- **Do not** drop different evidence just because it is about the same theme. Signals that
  share a subject but differ in `source`, `observed_at`, or `url` represent **distinct
  observations** and `MUST` stay separate — they strengthen the evidence base rather than
  duplicating it.
- The dedup key definition lives in `config/` (`TECHNICAL DEFAULT`) and is golden-tested
  (§22).

### 6.7 Raw capture layout

- One file per signal: `data/<run_id>/signals/raw/<signal_id>.json`.
- Minimal shape:

```json
{
  "signal_id": "sig_run_2026-08-28_01_0007",
  "source_type": "web_search",
  "capture_method": "claude_web_search",
  "query_or_reference": "\"frequência do sono\" tendência tiktok 2026",
  "url": "https://example.com/article",
  "captured_at": "2026-08-28T14:03:11Z",
  "raw_content": "…verbatim search result / API response / analyst note…"
}
```

- `raw_content` is opaque text or JSON — enough to re-derive the `Signal` fields and to
  support **replay** (§22).
- Normalized signals for the run are also written to `data/<run_id>/signals/normalized.json`.

---

## 7. Opportunity Model / Schema

The **unit of analysis (C1)**:

> An opportunity is a need, desire or behavior of an audience that shows signals of demand or growth and that can be turned into a content cluster, explored in a specific market/language and platform, and connected to an existing musical asset or a potential new content operation.

**Structural rule (C1): `OPPORTUNITY ≠ CLUSTER`.** The cluster is a downstream editorial structure; V1 only proposes it as a hypothesis.

### 7.1 `Opportunity`

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `opportunity_id` | string | yes | — | stable, deterministic. `TECHNICAL DEFAULT`: `opp_<run_date>_<short_hash>` where `short_hash` = first 10 hex of `sha1(need + '|' + audience.description + '|' + market + '|' + language + '|' + platform)` — the C1 mandatory tuple, **not** the `title`. Same opportunity in a re-run → same id (idempotent); a reworded `title` does not change it. Genuine hash collision → append `-2`. |
| `schema_version` | string (semver) | yes | `"1.0.0"` | I4 |
| `run_id` | string | yes | — | run that created it (first run; unchanged on re-run) |
| `created_at` | datetime (ISO 8601) | yes | — | |
| `title` | string | yes | — | short human label (may be reworded between runs — not part of the id) |
| **Mandatory minimum structure (C1)** | | | | all six required, non-empty |
| `need` | string | yes | — | the need / desire / behavior |
| `audience` | object | yes | `{ description: string, attributes?: map }` | who |
| `market` | enum | yes | `Brasil` \| `Mercados hispanohablantes` \| `English-speaking markets` | V1 market taxonomy (§7.1a). A signal whose market is `UNKNOWN` or outside the three is **flagged, not turned into an opportunity** in V1. |
| `language` | enum | yes | `pt` \| `es` \| `en` | business-dna §8; a signal in another language is flagged, not turned into an opportunity |
| `platform` | enum | yes | `tiktok` \| `youtube` \| `spotify` \| `instagram` \| `facebook` \| `other` | primary platform of the opportunity |
| `consumption_context` | string | yes | — | when / where / how the audience consumes |
| **Timing (I9)** | | | | |
| `durability` | enum | yes | `EPHEMERAL` \| `EMERGING` \| `STRUCTURAL` \| `EVERGREEN` | classification label |
| `urgency` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | separate from durability (I9) |
| **Evidence** | | | | |
| `evidence` | list<`EvidenceItem`> | yes | — | ≥1 item; ≥1 `OBSERVED` required to be eligible for the presented set (`TECHNICAL DEFAULT`, §13) |
| **Derived / hypothetical (C7 — non-binding)** | | | | |
| `hypotheses` | object | no | see §7.2 | every field here is a `HYPOTHESIS`; marked as such; never presented as decision |
| **Analysis outputs** | | | | |
| `asset_fit` | `AssetMatch` | yes | §10 | |
| `evaluation` | `Evaluation` | yes | §8 | |
| `business_outcome_profile` | `BusinessOutcomeProfile` | yes | §9 | |
| `recommendation` | `Recommendation` | yes | §12 | |
| `provenance` | `OpportunityProvenance` | yes | §16.2 | aggregate: run conditions + all `signal_ids` + distinct `Provenance` records |
| **Registry fields (I2)** | | | | |
| `status` | enum | yes | `EXPLORE` \| `TEST` \| `PARK` (V1); model allows `LAUNCH`/`SCALE`/`KILL` | `TECHNICAL DEFAULT`: created as `EXPLORE`; non-top-N → `PARK` |
| `state_history` | list<`StateChange`> | yes | — | `{ from, to, at, by, note }`; `by` = `system` or a human id |
| `rank` | integer \| `null` | no | — | 1-based position in the presented set; `null` if not presented |
| `report_ref` | string \| `null` | no | — | relative path to the Opportunity Report; `null` if not presented |

### 7.1a Market taxonomy (V1)

Aligned to the values already adopted in the inventories and `classification-input.yaml`.
**No country-level taxonomy in V1.**

| `language` | `market` |
|---|---|
| `pt` | `Brasil` |
| `es` | `Mercados hispanohablantes` |
| `en` | `English-speaking markets` |

- These are the **only** valid `market` values on an `Opportunity` (plus `UNKNOWN` on a `Signal`).
- `language` and `market` are consistent by the table above; a mismatch is a validation failure (§13).
- Extending the taxonomy (country granularity, new markets) is a future decision, not V1.

### 7.2 `hypotheses` object (all optional, all `HYPOTHESIS`-typed)

| Field | Type | Notes |
|---|---|---|
| `potential_cluster` | object | `{ value: string, canonical: bool, basis: "existing" \| "proposed_new" }`. `value` `MUST` be one of the **11 canonical cluster ids** from `knowledge/clusters/cluster-taxonomy.md` when `canonical: true`. A theme outside the 11 is `canonical: false`, `basis: "proposed_new"` — a **`HYPOTHESIS` only** (P6); the pipeline **never** creates a new canonical category. Validated before report write (§13). |
| `potential_positioning` | string | non-binding |
| `potential_page` | string \| `NEW_ASSET` | an existing `page_id`, or `NEW_ASSET` (see `AssetMatch.new_asset_recommendation`) |
| `first_content_direction` | string | light direction only; content strategy is a later stage (C7). Claude has autonomy to propose new hooks/formats/structures beyond current methodology (I11) |
| `format` | string | e.g. short-form reel, long-form video |
| `hook` | string | candidate hook idea |

### 7.3 `EvidenceItem`

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `type` | enum | yes | `OBSERVED` \| `INFERRED` \| `HYPOTHESIS` | distinct categories (I4) |
| `statement` | string | yes | — | the claim |
| `signal_ids` | list<string> | required when `type = OBSERVED` | — | FK → `Signal.signal_id` in the same run; `MUST` all exist |
| `derived_from` | list<string> | required when `type = INFERRED` | — | `signal_id`s and/or other `EvidenceItem` indices this inference rests on |
| `rationale` | string | required when `type ∈ {INFERRED, HYPOTHESIS}` | — | why the inference / what the hypothesis rests on |
| `test_idea` | string | no | — | for `HYPOTHESIS`: how it could be tested |
| `confidence` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | |

### 7.4 Relationships

```
RunConfig 1─* Signal
Signal 1─1 Provenance
Signal    *─* EvidenceItem   (via EvidenceItem.signal_ids, only for OBSERVED)
Opportunity 1─* EvidenceItem
Opportunity 1─1 AssetMatch 1─* (playlist_id | page_id | artist_id | catalog_id)  → inventory entries (MUST exist)
Opportunity 1─1 Evaluation
Opportunity 1─1 BusinessOutcomeProfile
Opportunity 1─1 Recommendation
Opportunity 1─1 OpportunityProvenance   (aggregates the opportunity's signal_ids + Provenance records)
Opportunity 1─1 OpportunityReport   (only when presented)
Opportunity 1─1 registry entry
```

---

## 8. Opportunity Evaluation Model

**No composite 0–100 numeric score (C6).** Evaluation is a qualitative multidimensional profile.

### 8.1 The 10 dimensions (C9)

| # | Dimension key | Meaning |
|---|---|---|
| 1 | `signal_strength` | how strong / clear the demand signals are |
| 2 | `audience_potential` | size and reachability of the audience |
| 3 | `growth_momentum` | current growth / trajectory of the demand |
| 4 | `durability_opportunity_window` | how favorable the timing window is — **informed by, not equal to,** `Opportunity.durability` (`TECHNICAL DEFAULT`) |
| 5 | `music_fit` | fit with the catalog / wellness positioning; a catalog-affinity mismatch with the opportunity's cluster is **not** a blocker (§10.2a); **capped at `LOW`/`MEDIUM` confidence** while musical DNA detail is `NEEDS_INPUT` (business-dna §9) |
| 6 | `content_potential` | how well it can be turned into content |
| 7 | `competitive_position` | our ability to compete for this demand (higher rating = more favorable position) |
| 8 | `differentiation_potential` | room to differentiate |
| 9 | `asset_fit` | summary of `AssetMatch` (§10) |
| 10 | `business_outcome_potential` | summary; detailed by the Business Outcome Profile (§9) |

### 8.2 `Evaluation` schema

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `schema_version` | string (semver) | yes | `"1.0.0"` | |
| `dimensions` | map<dimension_key, `DimensionRating`> | yes | exactly the 10 keys of §8.1 | all 10 `MUST` be present |
| `red_flags` | list<`RedFlag`> | yes | — | may be empty; blocking / impeding factors (C6) |
| `overall_confidence` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | `TECHNICAL DEFAULT`: explicitly assigned by Claude; if absent, = the **lowest** dimension confidence |
| `summary` | string | yes | — | 2–4 sentence synthesis, grounded in evidence |

**`DimensionRating`**

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `rating` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` \| `VERY_HIGH` | C6 |
| `confidence` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | separate from rating (C6) |
| `justification` | string | yes | — | `MUST` reference specific evidence items where applicable |
| `blocked_by` | list<string> | no | — | `NEEDS_INPUT` keys or `UNKNOWN` fields that limit this rating |

**`RedFlag`**

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `description` | string | yes | — | |
| `severity` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | |
| `kind` | enum | yes | `compliance` \| `feasibility` \| `evidence_gap` \| `asset_gap` \| `market` \| `other` | `TECHNICAL DEFAULT` set; `compliance` flags come from the guardrail check (§13, C4) |

### 8.3 Rules

- Confidence `MUST` be preserved: `overall_confidence = LOW` `MUST NOT` be overridden by high dimension ratings (C6).
- No weights, no formula, no numeric aggregation (C6).
- A dimension that cannot be rated from available evidence `MUST` be `rating: LOW`, `confidence: LOW`, with `blocked_by` populated — not omitted, not guessed.
- Rating anchors (`LOW`…`VERY_HIGH`) are described qualitatively per dimension in an appendix to be written with the first run; calibration is deferred (P1). `TECHNICAL DEFAULT` until then: Claude applies consistent qualitative judgement and records its reasoning.

---

## 9. Business Outcome Profile

Separate from the evaluation dimensions (C5): dimensions explain *how strong* the opportunity is; this profile explains *which value engines it can feed*. An opportunity may be high on one axis and low on another and still be strategic — **no aggregation into a single value**.

### 9.1 `BusinessOutcomeProfile` schema

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `schema_version` | string (semver) | yes | `"1.0.0"` | |
| `axes` | map<axis_key, `AxisRating`> | yes | exactly the 5 keys below | all 5 `MUST` be present |

**Axis keys (C5):** `playlist_growth_potential` · `music_trend_ugc_potential` · `streaming_royalty_potential` · `page_growth_potential` · `youtube_media_potential`

**`AxisRating`**

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `rating` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` \| `VERY_HIGH` | |
| `confidence` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | |
| `justification` | string | yes | — | grounded in evidence; relates the opportunity to that engine |

### 9.2 Rules

- `playlist_growth_potential` and `music_trend_ugc_potential` are **distinct** and `MUST NOT` be merged or averaged (CLAUDE.md §4, principle 26).
- `youtube_media_potential` concerns the **YouTube Video** operation (own audiovisual media), which is out of V1 build scope but is still assessed as an axis (C3, business-dna §7). It `MUST NOT` be conflated with YouTube Music.
- Relative weighting of value engines for ranking is **not decided** — the "peso relativo entre ecossistemas de royalties" is `NEEDS_INPUT` (business-dna §4). See §11 for the `TECHNICAL DEFAULT` ranking treatment.

---

## 10. Asset Matching

Connects an opportunity to **existing** assets from the inventory (I1). **No asset may be invented (I1, C10.4).**

### 10.1 Inputs

The four inventory files, read-only (current state — strategic classification is now
**partly consolidated**):

| File | Records | Facts (from source spreadsheets) | Consolidated classification |
|---|---|---|---|
| `artists.yaml` | **37** | `artist_id`, `name`, `spotify_artist_id`, `distributors_observed`, `release_months_observed` | **14** artists have `primary_cluster` (canonical) + `secondary_clusters` + `language` + `market`; **10** have `hero_artist: true`; `positioning` = `NEEDS_INPUT` for all 37; the other fields `NEEDS_INPUT` where not decided |
| `playlists.yaml` | **8** | `playlist_id`, `name`, `platform` (`Spotify`), `url` | all 8 have `cluster` (canonical), `secondary_clusters`, `language`, `market`, `purpose`; `priority` = `HIGH` for 1, `NEEDS_INPUT` for 7; `hero_artists` = the **same 10** artist ids on all 8 |
| `pages.yaml` | **49** (**5** `own` + **44** `reference_competitor`) | `page_id`, `name`, `platform` (`TikTok`), `handle`, `ownership` | the **5 own** pages have `cluster` (canonical), `language`, `market`, `purpose`; the 44 reference pages are unclassified (`NEEDS_INPUT`) |
| `catalog.yaml` | **133** releases | `catalog_id`, `artist_id`, `title`, `release_month`, `distributor` | — |

All `cluster` / `primary_cluster` values in the inventories are one of the **11 canonical
clusters** (`cluster-taxonomy.md`); `Sono Restaurador` is normalized to `Sono` there.

### 10.2 Method

1. **Candidate generation (deterministic):** filter inventory entries by observable
   attributes aligned with the opportunity — `platform`; page `ownership = own`;
   **consolidated `cluster` / `market` / `language`** where present; artist/playlist/track
   **name text** as a lexical hint where classification is absent. An artist's
   `primary_cluster` / catalog affinity is **not** an eligibility filter (§10.2a) — artist
   candidate generation `MUST NOT` drop an artist for a cluster mismatch, and the **10 hero
   artists** are always in the artist candidate set.
2. **Fit assessment (Claude + deterministic):** for each candidate, judge fit and produce a
   rationale, and set `fit_basis`:
   - **`OBSERVED`** — the judgement is supported by a **consolidated inventory
     classification** (e.g. a playlist whose `cluster` matches the opportunity's
     `potential_cluster`; a page whose `cluster`/`market`/`language` align; an artist that
     is `hero_artist: true` or whose consolidated `primary_cluster`/`secondary_clusters`
     relate to the opportunity).
   - **`INFERRED`** — the judgement rests on **name/title text**, a `NEEDS_INPUT` field, or
     a hypothesis. `MUST` carry `LOW` or `MEDIUM` confidence.
   - **`UNKNOWN`** — there is no adequate basis to judge fit at all.
   For **artists**, the judgement weighs together: (a) catalog affinity; (b) strategic
   portfolio role — especially `hero_artist` status (§10.2a); (c) the artist↔playlist
   relationship when known; (d) the opportunity itself. No fit judgement is ever written
   back to the inventory.
3. **Selection (deterministic + Claude):** pick `best_playlist` / `best_page` /
   `best_artist` or set them to `UNKNOWN` (with `unmatched_reason`). If nothing fits and
   the I5 criteria hold, produce a `new_asset_recommendation`.

### 10.2a Artist eligibility (owner decision, 2026-08-27)

An artist's `primary_cluster` / secondary clusters are **catalog affinity** — the
predominant theme or editorial context observed in the catalogue — **not** an eligibility
filter.

- **Any artist may serve any cluster / opportunity** when it fits the business strategy.
  Artist candidate generation and Asset Fit `MUST NOT` exclude or down-rank an artist
  solely because its catalog affinity differs from the opportunity's cluster.
- **Hero artists** (`hero_artist: true` in `classification-input.yaml` / the inventory) are
  selected strategically and are placed in **all predefined playlists** for maximum
  exposure and real consumption/engagement signals — they are strong candidates for any
  opportunity, regardless of catalog affinity.
- Keep three concepts **distinct** and never collapse them:
  `catalog affinity` · `playlist placement` · `strategic hero status`.
- The system `MUST NOT` infer that an artist "does not fit" an opportunity from a
  catalog-affinity mismatch alone.

### 10.3 `AssetMatch` schema

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `schema_version` | string (semver) | yes | `"1.0.0"` | |
| `matching_playlists` | list<`AssetCandidate`> | yes | — | may be empty |
| `matching_pages` | list<`AssetCandidate`> | yes | — | only `ownership = own` pages are usable assets; `reference_competitor` pages may appear with `role: reference` for competitive context, never as a recommended page |
| `matching_artists` | list<`AssetCandidate`> | yes | — | |
| `matching_catalog` | list<`AssetCandidate`> | no | — | `TECHNICAL DEFAULT`: catalog matching is coarse in V1; artist- and playlist-level matching is primary |
| `best_playlist` | string \| `UNKNOWN` | yes | `playlist_id` or `UNKNOWN` | |
| `best_page` | string \| `UNKNOWN` \| `NEW_ASSET` | yes | `page_id`, `UNKNOWN`, or `NEW_ASSET` | |
| `best_artist` | string \| `UNKNOWN` | yes | `artist_id` or `UNKNOWN` | |
| `new_asset_recommendation` | `NewAssetRecommendation` \| `null` | yes | — | non-null only when I5 criteria are met |
| `unmatched_reason` | string \| `null` | yes | — | required when any `best_*` is `UNKNOWN` |

**`AssetCandidate`**

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `asset_type` | enum | yes | `playlist` \| `page` \| `artist` \| `catalog` | |
| `asset_id` | string | yes | — | `MUST` exist in the corresponding inventory file |
| `name` | string | yes | — | copied from inventory |
| `fit` | enum | yes | `NONE` \| `LOW` \| `MEDIUM` \| `HIGH` | |
| `fit_basis` | enum | yes | `OBSERVED` \| `INFERRED` \| `UNKNOWN` | `OBSERVED` = supported by a consolidated inventory classification; `INFERRED` = relies on name/title text, a `NEEDS_INPUT` field, or a hypothesis (confidence `LOW`/`MEDIUM`); `UNKNOWN` = no adequate basis (§10.2 step 2) |
| `fit_rationale` | string | yes | — | |
| `role` | enum | no | `candidate` \| `reference` \| `hero` | `reference` for `reference_competitor` pages (context only, never recommended); `hero` for an artist flagged `hero_artist: true` |

**`NewAssetRecommendation`** (I5 — recommendation only, never executed)

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `asset_type` | enum | yes | `page` \| `playlist` \| `other` | |
| `rationale` | string | yes | — | `MUST` explicitly address the four I5 conditions: (1) no existing asset with adequate fit; (2) opportunity has relevant potential; (3) plausible differentiation potential; (4) sufficient durability / window |
| `i5_conditions_met` | object | yes | `{ no_adequate_fit: bool, relevant_potential: bool, differentiation_potential: bool, sufficient_window: bool }` | all four `SHOULD` be true, or the recommendation is downgraded to a note |

### 10.4 Rules

- Every `asset_id` referenced anywhere in `AssetMatch` **MUST** be present in the corresponding inventory file. A non-existent id is a validation failure; the reference is dropped and the field set to `UNKNOWN` with a logged warning.
- Asset reuse is the default (I5). `new_asset_recommendation` is the exception, is a recommendation only, and `MUST NOT` trigger any creation.
- The pipeline `MUST NOT` write inferred `cluster` / `market` / `language` / `positioning` back into any inventory file (I1 rule 4).

---

## 11. Ranking / Prioritization

Deterministic. Produces a total order over the run's opportunities; the top `N` (`N = RunConfig.max_opportunities_presented`, default 10 — I12) are **presented**; the rest are stored with `status: PARK` (I12).

**The limit of 10 applies to the *presented output* only** — the number of Opportunity Reports and the digest's primary list. Framing (§18 component 3) may produce more candidate opportunities internally; they are all evaluated, ranked, and recorded (`presented` / `parked` / `excluded`) — only the top `N` are surfaced to the owner (I12). There is no hard cap on internal candidates; `RunConfig` may set a soft `max_candidates` (`TECHNICAL DEFAULT`: unset = no cap) to bound cost.

### 11.1 `TECHNICAL DEFAULT` ordering algorithm

No numeric score (C6). Ordinal comparator over these keys, in order, until a difference is found:

1. **Hard exclusion first** — an opportunity with a `HIGH`-severity `compliance` red flag, or with zero `OBSERVED` evidence, is **not eligible for the presented set** (it may still be recorded as `EXPLORE`/`PARK`).
2. `overall_confidence` bucket: `HIGH` > `MEDIUM` > `LOW`.
3. Count of dimensions rated `HIGH` or `VERY_HIGH` (more is better).
4. Count of Business Outcome axes rated `HIGH` or `VERY_HIGH` (more is better).
5. `urgency`: `HIGH` > `MEDIUM` > `LOW`.
6. `durability`: `EVERGREEN` ≈ `STRUCTURAL` > `EMERGING` > `EPHEMERAL` (`TECHNICAL DEFAULT`: evergreen/structural preferred for a playlist-centric business; `EPHEMERAL` still allowed when `urgency = HIGH`).
7. Fewer / lower-severity non-compliance red flags.
8. `asset_fit` dimension rating (existing-asset opportunities preferred over new-asset ones — reuse default, I5).
9. Stable tie-break: `opportunity_id` ascending.

The comparator, its key order, and the exclusion rule are **configurable constants** documented in one place and covered by golden tests (§22). Owner-provided value-engine weighting (business-dna §4, currently `NEEDS_INPUT`) would replace/extend keys 3–4 when available.

### 11.2 Outputs

- ordered list of all opportunities with `rank` set on presented ones (`1..N`), `null` on the rest;
- `presented` set (≤ N), `parked` set (the remainder), `excluded` set (hard-excluded) — all recorded in the run digest with reasons.

---

## 12. Opportunity Report Generation

One report per **presented** opportunity (I4). Deterministic structure and front matter; Claude writes the prose within each section.

### 12.1 File

`TECHNICAL DEFAULT`: `reports/<run_id>/<opportunity_id>.md` (+ `<opportunity_id>.json` sidecar mirroring the structured record).

### 12.2 `OpportunityReport` — front matter

| Field | Type | Required | Notes |
|---|---|---|---|
| `opportunity_id` | string | yes | |
| `run_id` | string | yes | |
| `schema_version` | string (semver) | yes | `"1.0.0"` |
| `created_at` | datetime | yes | |
| `rank` | integer | yes | |
| `title` | string | yes | |
| `market` | enum | yes | `Brasil`\|`Mercados hispanohablantes`\|`English-speaking markets` (§7.1a) |
| `language` | enum | yes | `pt`\|`es`\|`en` |
| `platforms` | list<enum> | yes | |
| `durability` | enum | yes | |
| `urgency` | enum | yes | |
| `potential_cluster` | string \| `null` | yes | hypothesis; one of the 11 canonical cluster ids, or `<name> (proposed_new)` when `basis: proposed_new`, or `null` |
| `overall_confidence` | enum | yes | `LOW`\|`MEDIUM`\|`HIGH` |
| `target_state` | enum | yes | `EXPLORE`\|`TEST`\|`PARK` (V1) |

### 12.3 Body — the 9 sections (I4), in order

| # | Section | Content source |
|---|---|---|
| 1 | **Identity** | `opportunity_id`, `created_at`, `run_id`, `schema_version` |
| 2 | **Market Context** | `market`, `language`, `platform(s)`, `need`, `audience`, `consumption_context` |
| 3 | **Evidence** | every `EvidenceItem`: `type` badge (`OBSERVED`/`INFERRED`/`HYPOTHESIS`), statement, linked signals (with `source`, `url`, `observed_at`), `confidence` |
| 4 | **Evaluation** | the 10 dimensions: `rating`, `confidence`, `justification`, `blocked_by`; then `red_flags`; then `overall_confidence` and `summary` |
| 5 | **Business Outcome Profile** | the 5 axes: `rating`, `confidence`, `justification` |
| 6 | **Asset Fit** | `matching_*` candidates; `best_playlist` / `best_page` / `best_artist` or `UNKNOWN`; `new_asset_recommendation` (with the four I5 conditions) if any |
| 7 | **Hypotheses** | `potential_cluster`, `potential_positioning`, `potential_page`, `first_content_direction`, `format`, `hook` — each explicitly labelled a hypothesis (C7) |
| 8 | **Recommendation** | the `Recommendation` object (below) |
| 9 | **Provenance** | data origins, signal sources used, `prompt_version`, model, `run_id`, reproducibility notes (§16) |

The report **MUST** visually separate observed facts, inferences and hypotheses. Any required-but-missing information is rendered as `UNKNOWN` or `NEEDS_INPUT` (§15) — never omitted silently, never filled with a guess.

### 12.4 `Recommendation` schema (I3, C6)

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `schema_version` | string (semver) | yes | `"1.0.0"` | |
| `target_state` | enum | yes | `EXPLORE` \| `TEST` \| `PARK` (V1); model permits `LAUNCH`/`SCALE`/`KILL` | `TECHNICAL DEFAULT`: V1 emits only the three operational states |
| `suggested_next_step` | string | yes | — | concrete and actionable, still a recommendation, **not executed** in V1 |
| `justification` | string | yes | — | grounded in evidence, evaluation and red flags |
| `confidence` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | `TECHNICAL DEFAULT`: mirrors `Evaluation.overall_confidence` unless explicitly set |
| `execution_note` | string (fixed) | yes | — | constant: "V1 does not execute this action; it requires human approval." |

### 12.5 Run digest — `reports/<run_id>/digest.md`

Front matter: `run_id`, `run_date`, `schema_version`, `config_snapshot`, `sources_used`, `sources_failed`, `model`, `prompt_version`, counts (`signals`, `opportunities_total`, `presented`, `parked`, `excluded`), timings.
Body: ranked table of presented opportunities (`rank`, `title`, `market`/`language`, `target_state`, `overall_confidence`, top dimensions, key red flags, link to report); a short list of parked opportunities; a list of excluded opportunities with reasons; a "below target" note if `presented < 5` (C10).

---

## 13. Validation Rules

Run by deterministic validators after the relevant stage; a failure blocks that entity from the presented set (not necessarily the whole run — see §14).

**Config**

- `RunConfig` parses; `run_id` matches `^[A-Za-z0-9_\-]+$`; `max_opportunities_presented` ≥ 1; every path exists.

**Knowledge / inventory**

- All four inventory files parse and are non-empty; `business-dna.md`, `knowledge/rules/guardrails.yaml` (10 entries) and `knowledge/clusters/cluster-taxonomy.md` (11 canonical ids) load. Otherwise → hard failure (§14).

**Signal**

- Conforms to §6.1/§6.3; `source_type` ∈ the four V1 sources; `raw_ref` resolves; `language` ∈ {`pt`,`es`,`en`,`UNKNOWN`}; `metrics` contain no invented figures.

**Opportunity**

- All six C1 mandatory fields present and non-empty.
- `language` ∈ {`pt`,`es`,`en`} and `market` ∈ {`Brasil`,`Mercados hispanohablantes`,`English-speaking markets`}, consistent per §7.1a.
- `durability` and `urgency` set to valid enum values.
- `opportunity_id` matches the deterministic hash of the C1 tuple (§7.1) — re-run stability.
- `evidence` has ≥ 1 item; **≥ 1 `OBSERVED`** item to be eligible for the presented set (`TECHNICAL DEFAULT`).
- Every `EvidenceItem` of type `OBSERVED` has `signal_ids` that all resolve to signals in this run; every `INFERRED` item lists `derived_from` that resolves; every `HYPOTHESIS` item has `rationale` and its supporting base (§10, §16).
- `hypotheses.potential_cluster.value` ∈ the 11 canonical ids when `canonical: true`; a non-canonical value `MUST` have `basis: "proposed_new"` and be rendered as a hypothesis. **A canonical cluster value that is not in `cluster-taxonomy.md` is a validation failure** (§6, item 10 of the review).
- `hypotheses` fields (if present) are rendered/labelled as hypotheses only.

**Evaluation**

- Exactly the 10 dimension keys of §8.1, each with valid `rating`, `confidence`, non-empty `justification`.
- **No numeric score anywhere** in the entity (a validator scans for `0–100` / bare 0–100 integers presented as a score) (C6).
- `overall_confidence` present and valid.

**Business Outcome Profile**

- Exactly the 5 axis keys, each with valid `rating`, `confidence`, non-empty `justification`.

**Asset Fit**

- Every referenced `asset_id` exists in the matching inventory file (§10.4).
- `best_*` are either a valid id, `UNKNOWN`, or (`best_page` only) `NEW_ASSET`.
- `unmatched_reason` present whenever a `best_*` is `UNKNOWN`.
- No inferred classification written back to inventories.

**Compliance (C4)**

- Guardrails are loaded from `knowledge/rules/guardrails.yaml` (10 entries `G01`–`G10`). The pipeline **does not parse `CLAUDE.md` prose** for enforcement.
- All generated free text within a guardrail's `applies_to` scope — `hypotheses.potential_positioning`, `hypotheses.first_content_direction`, `hypotheses.hook`, `evidence`, `evaluation`/`business_outcome_profile` justifications, `recommendation`, and report prose — is checked against each guardrail.
- A violation raises a `compliance` `RedFlag` with `severity` and `kind: compliance` copied from the guardrail. Then the guardrail's `action_on_violation` applies: `reject_and_revise` → one Claude revision pass, and on failure the guardrail's `escalation` (strip the offending hypothesis, or `exclude_opportunity` if it is core required content); `flag` / `flag_for_validation` → the report proceeds with the red flag; `require_uncertainty_statement` → the invented text is replaced with an explicit `UNKNOWN` / uncertainty note; `none` (permissive/principle) → no action.

**Report**

- All 9 sections present and in order; front matter complete; `target_state` ∈ {`EXPLORE`,`TEST`,`PARK`}.
- Presented set size ≤ `max_opportunities_presented`.

**Registry**

- Every presented/parked opportunity has a registry entry with `opportunity_id`, `status`, `created_at`, `report_ref` (or `null`), and a `state_history` entry.

---

## 14. Error Handling

| Situation | Handling |
|---|---|
| Missing required knowledge (any inventory, `business-dna.md`, `guardrails.yaml`, `cluster-taxonomy.md`) | **Hard failure.** Abort before Signal Collection. Clear message naming the missing file. Exit non-zero. Nothing written to `reports/`. |
| A signal source is unavailable (Web Search error, YouTube API error/quota, no TikTok capture file, no internal-data file) | **Degrade.** Continue with the remaining sources. Record the failure in `digest.sources_failed`. If **all** sources fail → hard failure. In `replay` mode the live sources are not called at all. |
| Claude returns schema-invalid output for a stage | **Retry once** (`TECHNICAL DEFAULT`) with the validation errors fed back. If still invalid: mark the affected opportunity/field `blocked`, exclude that opportunity from the presented set, record it in `digest.excluded` with the reason. The run continues. |
| An `EvidenceItem` references a `signal_id` that does not exist | Drop the reference; if the item is left with no support, drop the item; if the opportunity then has no `OBSERVED` evidence, it becomes ineligible for the presented set. Log a warning. |
| An `AssetMatch` references a non-existent `asset_id` | Drop the reference, set field to `UNKNOWN`, log a warning. Never invent (I1). |
| Fewer than 5 opportunities produced | Run **completes**. Digest flags "below C10 target". Not a failure. |
| Zero eligible opportunities | Run completes with an empty presented set and a digest explaining why (sources used, signals collected, why nothing qualified). |
| Compliance violation that cannot be fixed in one pass | Strip the offending hypothesis/prose, add a `compliance` `RedFlag`, proceed. If the violation is in core required content, exclude the opportunity. |
| Write conflict / partial run | `TECHNICAL DEFAULT`: writes for a run go to a temp dir and are moved into `reports/<run_id>/` atomically at the end; a crashed run leaves no partial `reports/` dir. |

All warnings and errors are also written to `data/<run_id>/run.log` (`TECHNICAL DEFAULT`).

---

## 15. Unknown / Needs Input Semantics

Two distinct sentinels; **neither is ever replaced by a guess** (C4.5, C4.10, I1).

| Sentinel | Meaning | Used for | Effect |
|---|---|---|---|
| `UNKNOWN` | The information does not exist in the sources available to this run. | data fields — playlist followers, `best_page`, a missing metric, `observed_at` of a vague source | The pipeline proceeds using `UNKNOWN`. Dimensions that depend on it get `confidence: LOW` and a `blocked_by` note. Not an error. |
| `NEEDS_INPUT` | The information is knowable but depends on an owner decision that has not been made. | inventory strategic classification not yet consolidated (`positioning` for all 37 artists; `primary_cluster` / `secondary_clusters` / `language` / `market` for the 23 un-classified artists; `priority` for 7 playlists), musical DNA detail, value-engine weighting | Same handling as `UNKNOWN` for the run, **plus** the affected report section names the specific `NEEDS_INPUT` item so the owner can resolve it. Aggregated into the digest. |

Rules:

- A field that is `UNKNOWN`/`NEEDS_INPUT` in a source stays that way in the output; Claude `MUST NOT` fill it.
- `music_fit` and any regional/market judgement are **structurally capped** in confidence while their inputs are `NEEDS_INPUT` (business-dna §8, §9).
- The digest lists every distinct `NEEDS_INPUT` encountered, so the backlog of owner decisions is visible each run.

---

## 16. Provenance and Traceability

Goal: **every item presented in a report can be linked to the set of evidence that
supports its presence and its evaluation**, and a run can be reproduced (C10.2, I4 §9).

### 16.1 `Provenance` schema (per `Signal`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `source` | string | yes | human-readable origin |
| `source_type` | enum | yes | `web_search` \| `youtube` \| `tiktok_creative_center` \| `internal_data` |
| `observed_at` | date (ISO 8601) \| `UNKNOWN` | yes | when the phenomenon/data point is dated; `UNKNOWN` only when the source genuinely exposes no date |
| `collected_at` | datetime (ISO 8601) | yes | when this run captured it |
| `query_or_reference` | string | yes | the exact query string (`web_search`), the API request endpoint + parameters (`youtube`), the panel/filter used (`tiktok_creative_center`), or the file + row reference (`internal_data`) |
| `url` | string \| `UNKNOWN` | no | canonical URL of the specific resource when one exists |
| `capture_method` | enum | yes | `claude_web_search` \| `youtube_data_api` \| `analyst_capture` \| `internal_data` |
| `source_version` | string \| `UNKNOWN` | no | API version, dataset date, or panel snapshot label — when the source exposes one |

### 16.2 `OpportunityProvenance` (the `Opportunity.provenance` object)

| Field | Type | Required | Notes |
|---|---|---|---|
| `run_id` | string | yes | |
| `schema_version` | string (semver) | yes | |
| `model` | string | yes | Claude model id used (`RunConfig.model`) |
| `prompt_version` | string | yes | `RunConfig.prompt_version` |
| `generated_at` | datetime | yes | |
| `signal_ids` | list<string> | yes | every `Signal` that fed this opportunity, directly or via evidence |
| `sources` | list<`Provenance`> | yes | the distinct source records behind those signals |
| `replay` | bool | yes | `true` if produced under `RunConfig.replay.enabled` — **not** valid as current-trend evidence (§22) |

### 16.3 Traceability by evidence type (refines C10.2)

- **`OBSERVED`** — `MUST` have `source` + `observed_at` + a complete `Provenance` (via its
  `signal_ids` → each `Signal.provenance`). A raw capture (`data/<run_id>/signals/raw/<signal_id>.json`) `MUST` exist.
- **`INFERRED`** — `MUST` reference, in `derived_from`, the `OBSERVED` evidence item(s)
  (or `signal_id`s) it rests on, plus a `rationale`. It has **no** `observed_at` of its own.
- **`HYPOTHESIS`** — `MUST` reference in `rationale` the observed/inferred base that gave
  rise to it, and be explicitly labelled a hypothesis in the report (§12.3 §7, type badge
  in §3).
- **"100% traceable" (C10.2)** = for every **presented** opportunity, (a) every `OBSERVED`
  evidence item resolves to a dated signal with a raw capture; (b) every `INFERRED` /
  `HYPOTHESIS` item resolves to its stated base; (c) every `evaluation` /
  `business_outcome_profile` `justification` cites the evidence item(s) it uses;
  (d) `OpportunityProvenance.signal_ids` covers the union of all of the above. The §13
  validator checks (a)–(d).

### 16.4 Reproducibility

- **Run digest** records the reproducibility set: `config_snapshot`, `sources_used`,
  `sources_failed`, `model`, `prompt_version`, `replay` flag, stage timings, and counts.
- **Reproducibility** = same `RunConfig` + same `data/<run_id>/signals/raw/` + same
  `prompt_version` + same `model`. Claude output is not bit-reproducible; the raw captures
  make the *inputs* reproducible and the digest records the *conditions*.
- Everything under `reports/` and the registry is Git-versioned; `data/` is not required to be.

---

## 17. File and Directory Contracts

```
ai-music-media-engine/
├── CLAUDE.md                         # spec authority (read-only to the pipeline)
├── docs/
│   └── TECHNICAL-SPEC-V1.md          # this file
├── config/
│   ├── run.example.yaml              # RunConfig template (TECHNICAL DEFAULT location) — includes a `replay:` block
│   ├── ranking.yaml                  # ranking comparator constants (TECHNICAL DEFAULT)
│   └── dedup.yaml                    # dedup key definition (§6.6, TECHNICAL DEFAULT)
├── knowledge/                        # SOURCE OF TRUTH — read-only during a run …
│   ├── DECISIONS-NEEDED.md
│   ├── business-dna/
│   │   ├── business-dna.md
│   │   └── content-methodology.md
│   ├── rules/
│   │   └── guardrails.yaml           # 10 machine-readable C4 guardrails (§13) — pipeline loads this, not CLAUDE.md
│   ├── clusters/
│   │   └── cluster-taxonomy.md       # 11 canonical cluster ids (§7.2, §13)
│   ├── market/
│   │   └── opportunity-registry.yaml # … EXCEPT this file, append-only by runs (I2) — see governance note below
│   └── inventories/
│       ├── artists.yaml  playlists.yaml  pages.yaml  catalog.yaml   # asset truth (I1) — never modified
│       ├── classification-input.yaml # owner's strategic-classification form (read-only to the pipeline)
│       └── source/                   # original spreadsheets
├── data/                             # generated, regenerable — git-ignored (TECHNICAL DEFAULT)
│   └── <run_id>/
│       ├── signals/raw/<signal_id>.json   # raw captures — one file per signal (§6.7); replay reads these
│       ├── signals/normalized.json
│       ├── opportunities.json        # full structured records before rendering
│       └── run.log
└── reports/                          # generated, durable, versioned (I7)
    └── <run_id>/
        ├── digest.md
        ├── review.md                 # owner review-gate record (§21.1)
        ├── <opportunity_id>.md
        └── <opportunity_id>.json
```

- **Runtime: Python 3** (I10). Persistence formats: **YAML** (config, inventories, registry, guardrails), **Markdown + YAML front matter** (reports, digest, knowledge), **JSON** (intermediates, report sidecars, raw captures). **No database, queue or long-running server** (I10).
- The pipeline reads `knowledge/` and writes only `data/<run_id>/`, `reports/<run_id>/`, and appends `knowledge/market/opportunity-registry.yaml`.

**Registry governance exception.** `knowledge/` is human-owned source of truth, but
`knowledge/market/opportunity-registry.yaml` is an **operational, versionable artifact
written by the pipeline** — an index of opportunities and their lifecycle state (I2).
Constraints: writes are **append-only** (new opportunities; new `state_history` entries) —
existing entries are never rewritten in place beyond appending history; every change `MUST`
be visible in `git diff` and is human-reviewed; the pipeline `MUST NOT` write or overwrite
any other file under `knowledge/`, and `MUST NOT` touch strategic source knowledge
(`business-dna.md`, `content-methodology.md`, `cluster-taxonomy.md`, `guardrails.yaml`, the
inventories, `classification-input.yaml`, `DECISIONS-NEEDED.md`).

---

## 18. Component Responsibilities

Modular pipeline (I8). Each component is an independent unit with a typed input and output; the orchestrator calls them in sequence. Components communicate only through the orchestrator (no direct calls); no component is an "agent" with open-ended tool use; multi-component parallelism is **not** in V1 (P5).

| Component | Input | Output | Depends on | Owner | On failure |
|---|---|---|---|---|---|
| **Orchestrator** | `RunConfig` | run result + exit code | — | deterministic | propagate hard failures; collect per-opportunity exclusions |
| **Knowledge Loader** | paths from `RunConfig` | context bundle: business DNA, `guardrails.yaml` (G01–G10), `cluster-taxonomy.md` (11 ids), 4 inventories, registry | filesystem | deterministic | hard failure if any required file missing/unparseable |
| **1. Signal Collection** | `RunConfig.scope` + `signal_sources` (+ `replay`) | raw signal candidates + `data/<run_id>/signals/raw/<signal_id>.json` | RunConfig; Claude API Web Search; YouTube Data API (key); TikTok capture file; internal-data file — **OR** fixture dir when `replay.enabled` (§22) | Claude (Web Search research) + deterministic (YouTube API client, capture-file load, raw-file writing) | degrade per source; hard failure if all sources fail |
| **2. Signal Normalization** | raw candidates | `list<Signal>` (validated, deduplicated §6.6, id-assigned) | Knowledge Loader (market/taxonomy); `config/dedup.yaml` | deterministic (schema, ids, dedup, provenance completeness) + Claude (fill ambiguous `signal_type` / `market` / `language` / `durability_hint`) | reject invalid signals with logged reason |
| **3. Analysis / Framing** | `list<Signal>` | `list<Opportunity>` (C1 fields, evidence typing, `durability`/`urgency`, hypotheses) | business DNA; `cluster-taxonomy.md`; market taxonomy (§7.1a) | Claude (framing, evidence typing) + deterministic (C1 mandatory-field enforcement, `opportunity_id` hash, cluster/market validation) | exclude malformed opportunities after 1 retry |
| **4. Asset Matching** | `list<Opportunity>` | each opportunity's `AssetMatch` | 4 inventories (incl. consolidated classification, §10.1); `cluster-taxonomy.md` | deterministic (candidate filter, `asset_id` existence check, `fit_basis` gating) + Claude (fit judgement, I5 evaluation) | drop bad references → `UNKNOWN` |
| **5. Evaluation** | opportunities + evidence + `AssetMatch` | `Evaluation` + `BusinessOutcomeProfile` + `Recommendation` per opportunity | `guardrails.yaml`; business DNA; `AssetMatch` (dim 9); Business Outcome Profile (dim 10) | Claude (rate, justify, red flags, profile, recommend) + deterministic (enum/completeness/no-score validation, guardrail check §13, `target_state` constraint) | exclude opportunity after 1 failed retry |
| **6. Ranking / Prioritization** | evaluated opportunities | ordered list; `presented` (≤N) / `parked` / `excluded` sets; `rank` | `config/ranking.yaml` | deterministic (comparator §11) | n/a (pure function) |
| **7. Report Generation** | presented opportunities | `reports/<run_id>/*.md` + `*.json` + `digest.md` | §12 schema; §16 provenance | deterministic (structure, front matter, sidecar, digest, provenance assembly) + Claude (section prose) | fail the report → move opportunity to `excluded`, keep run |
| **Registry Updater** | presented + parked opportunities + current registry | updated `opportunity-registry.yaml` (append-only) | existing registry file | deterministic | fail run if registry write fails |

---

## 19. Claude vs Deterministic Code Responsibilities

| Claude (research, interpretation, framing, evaluation, synthesis) | Deterministic code (processing, validation, matching mechanics, aggregation, ranking, rendering) |
|---|---|
| **Web Search research** via the Claude API server-side Web Search tool (live; not model knowledge) | Loading knowledge, `guardrails.yaml`, `cluster-taxonomy.md` & inventories; integrity checks; **YouTube Data API** client; TikTok capture-file & internal-data loaders; raw-capture writing |
| Classifying ambiguous `signal_type` / `market` / `language` / `durability_hint` | `Signal` schema & `Provenance` validation, `signal_id` assignment, deduplication (§6.6), market/taxonomy enum checks |
| Framing signals into `Opportunity` objects (need, audience, consumption context) | Enforcing the six C1 mandatory fields; `opportunity_id` assignment |
| Assigning `durability` / `urgency` labels | Enum validation for `durability` / `urgency` |
| Typing evidence as `OBSERVED` / `INFERRED` / `HYPOTHESIS` and writing rationale | Checking that `OBSERVED` items resolve to real `signal_id`s |
| Judging asset fit and writing rationale; evaluating the four I5 conditions | Inventory candidate filtering; **asset existence verification**; blocking inventory write-back |
| Rating the 10 dimensions + confidence + justification; producing red flags | Verifying all 10 present; **scanning for any numeric 0–100 score**; enum validation |
| Producing the 5-axis Business Outcome Profile | Verifying all 5 axes present |
| Producing `Recommendation` (`target_state`, `suggested_next_step`, `justification`) | Constraining `target_state` to `EXPLORE`/`TEST`/`PARK`; attaching the fixed `execution_note` |
| Compliance self-check against `guardrails.yaml` (G01–G10); one revision pass | Loading `guardrails.yaml`; running the check per `applies_to` scope; applying `action_on_violation` / `escalation` |
| Writing report section prose; the digest narrative | Report structure, front matter, sidecar JSON, digest tables, ranking, top-N selection, registry update, provenance capture, retry orchestration |

Principle: **Claude decides *what is true and how strong it is*; deterministic code decides *whether the output is well-formed, traceable, and within V1 rules*.**

---

## 20. Configuration

### 20.1 `RunConfig` schema

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `run_id` | string | yes | — | `^[A-Za-z0-9_\-]+$`. `TECHNICAL DEFAULT` generator: `run_<YYYY-MM-DD>_<NN>` |
| `run_date` | date | yes | today | |
| `schema_version` | string (semver) | yes | `"1.0.0"` | |
| `scope` | object | yes | — | the research brief |
| `scope.clusters` | list<string> | no | `[]` (= open discovery) | subset of the 11 canonical cluster ids to focus discovery on; empty = open |
| `scope.markets` | list<enum> | no | `[]` (= all three) | subset of `Brasil` / `Mercados hispanohablantes` / `English-speaking markets` (§7.1a) |
| `scope.languages` | list<enum> | no | `["pt","es","en"]` | subset of `pt` / `es` / `en` (§7.1a) |
| `scope.discovery_platforms` | list<enum> | no | `["tiktok","youtube"]` | the **platforms the research is about** (what to look for). **Independent of `signal_sources`** (which collectors run): e.g. `web_search` may surface a TikTok trend even when `tiktok_creative_center` capture is absent. |
| `scope.notes` | string | no | — | free guidance for the framing step |
| `signal_sources` | list<enum> | yes | `["web_search","youtube","tiktok_creative_center","internal_data"]` | which **collectors run** (subset of the four — C2) |
| `internal_data_path` | path | no | — | required if `internal_data` ∈ `signal_sources` |
| `tiktok_capture_path` | path | no | — | required if `tiktok_creative_center` ∈ `signal_sources` (§6.5) |
| `max_opportunities_presented` | integer | yes | `10` | I12 — **presented output** cap only (§11) |
| `max_candidates` | integer \| `null` | no | `null` | `TECHNICAL DEFAULT`: soft cap on internal candidate opportunities from Framing; `null` = no cap |
| `min_opportunities_target` | integer | yes | `5` | C10 lower target (advisory, digest-flagged, not enforced) |
| `model` | string | yes | — | a Claude model id, **configurable** — chosen at config time (I10). Valid ids: see the `claude-api` reference. |
| `extraction_model` | string | no | = `model` | `TECHNICAL DEFAULT`: optional lighter model for classification/extraction |
| `prompt_version` | string | yes | — | recorded in provenance (`TECHNICAL DEFAULT` for P8) |
| `paths` | object | yes | repo defaults (§17) | `knowledge_dir`, `inventories_dir`, `guardrails_path`, `taxonomy_path`, `registry_path`, `reports_dir`, `data_dir` |
| `dry_run` | bool | no | `false` | `TECHNICAL DEFAULT`: stop after stage 3 (Framing); skip Evaluation/Ranking/Reports |
| `replay` | object | no | `{ enabled: false }` | see §20.2 and §22 |
| `replay.enabled` | bool | no | `false` | when `true`, live sources are **not** called |
| `replay.fixture_path` | path | conditional | — | required when `replay.enabled`; dir of recorded fixtures (§22) |

### 20.2 Other configuration

- `config/ranking.yaml` — the comparator key order and the exclusion rule of §11 as data, not code.
- `config/dedup.yaml` — the dedup key definition of §6.6 as data.
- **Model API credentials** (Claude API key; YouTube Data API key) via **environment variables** (`TECHNICAL DEFAULT`); never in `RunConfig` or the repo.
- Rating anchors appendix (per §8.3) — added alongside the first real run.
- **`replay` mode** — see §22. When `replay.enabled: true`: Web Search, the YouTube Data API and TikTok capture are **not** invoked; Signal Collection reads recorded fixtures from `replay.fixture_path` instead; the run's `OpportunityProvenance.replay` is `true`. Replay exists to test the **deterministic** stages end-to-end without network; it is **not** a validation of current trends (the fixtures are historical).

---

## 21. V1 Definition of Done

Verbatim from **C10**. V1 is validated when, over **3 consecutive runs**:

1. It produces **between 5 and 10** prioritized opportunities per run.
2. **100% of evidence is traceable**, including source and observation date.
3. It **explicitly distinguishes observed facts/evidence from hypotheses**.
4. It **does not invent** playlists, artists or pages; when an asset is not in the inventory it uses `UNKNOWN`.
5. **≥ 70%** of the opportunities in the Top 10 are considered by the owner relevant enough for analysis or testing.
6. **≥ 1** opportunity is selected by the owner to advance to the next stage during the validation period.

How the spec supports each:

| DoD | Mechanism |
|---|---|
| 1 | `max_opportunities_presented = 10`; digest flags `< 5` (§11, §12.5) |
| 2 | Traceability model §16.3: `OBSERVED` → dated signal + raw capture; `INFERRED` / `HYPOTHESIS` → stated base; justifications cite evidence; `OpportunityProvenance.signal_ids` covers the union. §13 validator checks (a)–(d). |
| 3 | `EvidenceItem.type` enum + report section 3 renders type badges (§7.3, §12.3) |
| 4 | Asset existence verification is deterministic and mandatory (§10.4, §19); `UNKNOWN` sentinel (§15) |
| 5 | Owner review recorded in `reports/<run_id>/review.md` (§21.1); the digest's ranked table + per-dimension summary supports the review |
| 6 | Owner action recorded in `review.md` + registry `state_history`; `Recommendation.target_state = TEST` + `suggested_next_step` gives the owner a concrete option |

Criteria 5 and 6 are human-judged; both are **recorded**, per run, in `reports/<run_id>/review.md` (§21.1) so the 3-run gate is auditable and measurable.

### 21.1 `review.md` template

`reports/<run_id>/review.md` — owner fills after reading the digest.

```markdown
---
run_id: run_2026-08-28_01
review_date: "2026-08-28"
reviewer: "Nicolas Alves"
opportunities_presented: 8
opportunities_relevant_count: 6        # C10.5 numerator
relevant_ratio: 0.75                   # opportunities_relevant_count / opportunities_presented
advanced_opportunity_id: opp_2026-08-28_a1b2c3d4e5   # C10.6; null if none this run
---

# Run Review — run_2026-08-28_01

| rank | opportunity_id | title | owner_decision | note |
|------|----------------|-------|----------------|------|
| 1 | opp_… | … | relevant / not_relevant / advance | … |
| 2 | opp_… | … | … | … |
| … | | | | |

## Notes
<free text: patterns, source quality, NEEDS_INPUT that blocked judgement, etc.>
```

- `owner_decision` enum: `relevant` · `not_relevant` · `advance` (`advance` implies `relevant`).
- `opportunities_relevant_count` = count of rows with `relevant` or `advance`.
- **C10.5** passes for the run when `relevant_ratio ≥ 0.70`. **C10.6** passes when
  `advanced_opportunity_id` is non-null for at least one run in the 3-run window.
- A deterministic checker reads the three `review.md` files and reports the gate status.

---

## 22. Test Strategy

**Test runner: `pytest`** (Python 3 — I10). Tests precede implementation code (TDD).

**Deterministic components — exact/golden tests**

- `Signal` / `Provenance` / `Opportunity` / `OpportunityProvenance` / `EvidenceItem` / `Evaluation` / `BusinessOutcomeProfile` / `AssetMatch` / `Recommendation` / `OpportunityReport` / `RunConfig` schema validators: fixture pairs (valid, and one invalid per rule in §13).
- Deduplication (§6.6): fixed signal set → fixed kept/dropped result (golden); asserts same-theme/different-source signals stay separate.
- `guardrails.yaml` loader: 10 entries, required fields present, enums valid.
- `cluster-taxonomy.md` loader: exactly 11 canonical ids; `potential_cluster` validator accepts canonical, flags `proposed_new`, rejects an unknown "canonical" value.
- Ranking comparator: fixed set of evaluated opportunities → fixed order (golden). Includes ties, hard exclusions, `EPHEMERAL + HIGH urgency` edge case.
- Report renderer: fixed `Opportunity` → byte-stable Markdown + front matter + sidecar JSON (golden).
- Digest renderer: fixed run result → golden digest.
- Registry updater: new opportunity appended; existing opportunity gets a `state_history` entry, no rewrite.

**Asset-integrity tests**

- Opportunity referencing a non-existent `playlist_id` → `best_playlist` becomes `UNKNOWN`, warning logged, run continues.
- Attempt to write a `cluster` value into an inventory file → rejected.

**"No score" test**

- Any evaluation output containing a 0–100 integer presented as a score → validator fails.

**Contract tests**

- Every generated report has all 9 sections in order + complete front matter + `target_state ∈ {EXPLORE,TEST,PARK}`.
- Presented set size ≤ `max_opportunities_presented`.

**Claude-in-the-loop tests (structural, not exact — output is non-deterministic)**

- Given a small fixed set of `Signal`s, run Framing + Evaluation and assert: output is schema-valid; all 10 dimensions and 5 axes present; every `OBSERVED` evidence item resolves; no numeric score; `music_fit.confidence ∈ {LOW,MEDIUM}` while musical DNA is `NEEDS_INPUT`; compliance check runs.
- Guardrail probe: a signal that invites a medical claim → the resulting positioning hypothesis must not assert cure/treatment (C4); a `compliance` red flag or a sanitized hypothesis is expected.

**Replay mode (`RunConfig.replay.enabled: true`)**

- **Purpose:** exercise the deterministic pipeline end-to-end without network. It is a **test/regression tool, not** a validation of current trends (fixtures are historical).
- **Signal Collection:** does **not** call Claude Web Search, the YouTube Data API, or read a live TikTok capture. Instead it loads recorded fixtures from `replay.fixture_path`:
  ```
  <fixture_path>/
    signals/raw/<signal_id>.json      # same shape as §6.7
    llm/<stage>/<key>.json            # optional: recorded model outputs, keyed by input hash
  ```
- **Deterministic stages** (Normalization dedup/validation, Asset Matching mechanics, Ranking, Report/digest structure, Registry update) run for real against the fixture signals → fully offline, golden-testable.
- **LLM-dependent sub-steps** (Normalization classification, Framing, Fit judgement, Evaluation prose) run in one of two controlled modes, per `replay` config:
  - `llm: recorded` — replay `llm/<stage>/<key>.json` (offline; deterministic).
  - `llm: live` — call the model normally (network + model calls; used to refresh fixtures or to test the Claude-in-the-loop assertions).
- Every replay run stamps `OpportunityProvenance.replay = true` and the digest `replay: true`.

**Other modes**

- `dry_run` — stop after Framing (stage 3) for cheap iteration.

**Acceptance**

- The 3-run C10 gate (§21), owner-reviewed, recorded in `reports/<run_id>/review.md` per run (§21.1); a deterministic checker aggregates the three files.

---

## 23. Future Extension Points

Each maps to a `DEFERRED` decision or an open item; none is built in V1.

| Extension | Enabled by | Decision |
|---|---|---|
| **Automated TikTok Creative Center collector** (replacing the analyst capture) | plugs in behind `source_type: tiktok_creative_center` with a new `capture_method`; §6.5 contract unchanged | C2, P3 |
| Additional signal sources / paid APIs behind the `Signal` schema | `source_type` enum + pluggable collectors | C2, P3 |
| Quantitative scoring model, weights, calibrated anchors | replace §11 comparator; add `score` fields | C6, P1 |
| Analytics ingestion → evaluation calibration loop | new input + a calibration component | P1 |
| Measurable `LAUNCH` / `SCALE` / `KILL` criteria + lifecycle automation | registry state machine; `target_state` already models the states | I2, P2 |
| Owner value-engine weighting in ranking | `config/ranking.yaml` keys 3–4; business-dna §4 `NEEDS_INPUT` | business-dna |
| Strategic classification of the inventory (fill `NEEDS_INPUT`) → sharper, `OBSERVED`-basis asset matching | inventory fields already exist | I1 |
| Cluster Strategy stage consuming Opportunity Reports | `OpportunityReport` schema is the contract | C8 (stage 3), P4 |
| Curated competitor base | `knowledge/market/` | P9 |
| Prompt/version registry beyond a config string | `prompt_version` field is the seam | P8 |
| Cross-run trend dashboards | `reports/` history + digests | P7 |
| Multi-component parallelism / orchestration | components are already isolated | P5, I8 |
| `knowledge/rules/` consolidated compliance ruleset | compliance check already reads guardrails | C4 |

---

## Appendix A — Consistency check against decisions

| Decision | Where honored |
|---|---|
| C1 opportunity definition + minimum structure | §7, §7.1; `opportunity_id` from the C1 tuple |
| C2 signal sources + `Signal` schema | §3, §6, §6.5 (concrete mechanism per source), `RunConfig.signal_sources` |
| C3 business DNA as source of truth | §3, §15 (`NEEDS_INPUT` handling), §9.2 (YouTube roles) |
| C4 guardrails | **`knowledge/rules/guardrails.yaml` (G01–G10)** loaded by the pipeline; §13 compliance check, §14, `RedFlag.kind = compliance` |
| cluster-taxonomy (11 canonical clusters) | §3, §7.2 (`potential_cluster` validation), §13, §18 Knowledge Loader |
| market taxonomy (`Brasil` / `Mercados hispanohablantes` / `English-speaking markets`) | §7.1a, §6.1, §13 |
| C5 Business Outcome Profile (5 axes, kept separate) | §9 |
| C6 no 0–100; qualitative + confidence + red flags + recommendation | §8, §13 "no score" test, `Evaluation` schema |
| C7 V1 scope; hypotheses non-binding | §1, §2, §7.2, `Recommendation` constrained |
| C8 canonical pipeline; V1 = stages 1–2 | §1, §5, §23 |
| C9 the 10 dimensions | §8.1, `Evaluation` schema |
| C10 Definition of Done | §21 |
| I1 inventories; never invent | §10, §17, §19 |
| I2 registry; EXPLORE/TEST/PARK; LAUNCH/SCALE/KILL deferred | §5, §7.1, §18 Registry Updater |
| I3 `recommended_action` = target_state + suggested_next_step + justification | §12.4 |
| I4 report 9-section schema | §12.3 |
| I5 reuse default; new asset = recommendation only, four conditions | §10.3 `NewAssetRecommendation`, §11 key 8 |
| I6 knowledge structure | §17 |
| I7 `data/` vs `reports/` | §4, §17 |
| I8 pipeline of components; no monolith; no multi-agent | §18, §19 |
| I9 durability (4 values) + urgency (3 values) | §7.1, §8.1 dim 4 |
| I10 Python 3 / Claude / YAML+MD+JSON / Git / no DB, queue, server | §17, §20, principles |
| I11 content methodology historical; creative autonomy | §7.2 `first_content_direction`, §3 |
| I12 ≤ 10 presented per run; PARK for the rest | §11, §5, `RunConfig` |

**Scope check:** every component's output feeds only Opportunity Analysis and the Opportunity Report. No component produces content, schedules posts, defines a Page Blueprint, or creates an asset. `Recommendation` cannot execute. ✅ within V1.
