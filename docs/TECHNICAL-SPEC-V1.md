---
title: Technical Specification — Market Intelligence V1
status: draft
created: 2026-08-27
owner: Nicolas Alves (divinetonesmusic@gmail.com)
sources_of_truth:
  - CLAUDE.md
  - knowledge/DECISIONS-NEEDED.md
  - knowledge/business-dna/business-dna.md
  - knowledge/business-dna/content-methodology.md
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
| Run configuration | `RunConfig` (§20) | operator-provided file / CLI | scope, sources, limits, model, paths |
| Business DNA | Markdown + YAML front matter | `knowledge/business-dna/business-dna.md` | identity, monetization, markets, languages, positioning; some fields `NEEDS_INPUT` |
| Content methodology | Markdown | `knowledge/business-dna/content-methodology.md` | historical, **not rigid rules** (I11) |
| Compliance guardrails | this repo | `CLAUDE.md` §14 (C4); future `knowledge/rules/` | 10 guardrails, applied to generated text |
| Asset inventory | YAML | `knowledge/inventories/{artists,playlists,pages,catalog}.yaml` | **only** source of asset truth (I1); strategic fields `NEEDS_INPUT` |
| Opportunity registry | YAML | `knowledge/market/opportunity-registry.yaml` *(`TECHNICAL DEFAULT` path)* | prior opportunities + lifecycle state (I2) |
| Live web results | text | Live Web Search (C2) | gathered by Claude research |
| TikTok Creative Center signals | text | TikTok Creative Center (C2) | `TECHNICAL DEFAULT`: gathered via Claude-driven research / analyst capture, **not** a custom API client (paid APIs out of scope) |
| YouTube signals | text | YouTube (C2) | same as above |
| Internal business data | structured file(s) | operator-maintained, path in `RunConfig` | `TECHNICAL DEFAULT`: YAML or CSV; minimal shape in §6.4 |

The **Knowledge Loader** (deterministic) loads Business DNA, guardrails, all four inventories and the registry into an in-memory context bundle. Missing *required* knowledge (any inventory file, `business-dna.md`, guardrails) is a **hard failure** (§14).

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
| Registry update | `knowledge/market/opportunity-registry.yaml` | append new opportunities, append state-history entries (I2); human-reviewed via `git diff` |
| Raw captures & intermediates | `data/<run_id>/` | regenerable; `TECHNICAL DEFAULT`: `data/` is git-ignored (I7) |

The system **MUST NOT** write anywhere else in `knowledge/` and **MUST NOT** modify the inventories.

---

## 5. V1 Run Lifecycle

A run is a single invocation with one `RunConfig`. Deterministic orchestrator, sequential stages:

```
load & validate config
  → Knowledge Loader (load business DNA, guardrails, inventories, registry)   [hard-fail if required missing]
  → 1. Signal Collection
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
| `source` | string | yes | — | human-readable origin (e.g. `"Google — search interest"`, `"TikTok Creative Center — Trending hashtags"`) |
| `source_type` | enum | yes | `web_search` \| `tiktok_creative_center` \| `youtube` \| `internal_data` | C2 |
| `url` | string | no | — | present when the source is a web resource; else omitted / `UNKNOWN` |
| `observed_at` | date (ISO 8601, `YYYY-MM-DD`) | yes | — | when the phenomenon was observed / the data point is dated |
| `collected_at` | datetime (ISO 8601) | yes | — | when the run captured it |
| `market` | string | yes | free string; `UNKNOWN` allowed | named market (`TECHNICAL DEFAULT`, see §7.1) |
| `language` | enum | yes | `pt` \| `es` \| `en` \| `UNKNOWN` | ISO 639-1, restricted to V1 markets (business-dna §8) |
| `platform` | enum | yes | `tiktok` \| `youtube` \| `spotify` \| `instagram` \| `facebook` \| `web` \| `other` \| `UNKNOWN` | `TECHNICAL DEFAULT` enum |
| `signal_type` | enum | yes | see §6.2 | `TECHNICAL DEFAULT` starter set |
| `evidence` | string | yes | — | concise statement of what was observed (1–3 sentences) |
| `raw_excerpt` | string | no | — | verbatim snippet supporting `evidence` |
| `raw_ref` | string | yes | — | path under `data/<run_id>/signals/raw/…` to the full capture (§16) |
| `context` | string | yes | — | surrounding context needed to interpret the signal |
| `confidence` | enum | yes | `LOW` \| `MEDIUM` \| `HIGH` | source reliability + specificity of the observation |
| `metrics` | map<string, number \| string> | no | — | optional observed figures (e.g. `views`, `growth_rate`); `UNKNOWN` where a figure is not given — **never estimated** (C4.5) |

### 6.2 `signal_type` enum (`TECHNICAL DEFAULT`)

`search_trend` · `social_trend` · `hashtag` · `emerging_theme` · `content_format` · `competitor_activity` · `audience_behavior` · `emotional_need` · `regional_opportunity` · `language_opportunity` · `platform_opportunity` · `other`

Derived from CLAUDE.md §7. Extendable without schema change.

### 6.3 Validation rules

- `signal_id` unique within a run.
- `observed_at` `MUST NOT` be in the future relative to `collected_at`.
- `source_type` `MUST` be one of the four V1 sources; a `Signal` from any other origin is rejected in Normalization.
- `raw_ref` `MUST` resolve to an existing file under `data/<run_id>/`.
- `metrics` values that were not explicitly present in the source `MUST` be `UNKNOWN`, never a guess.

### 6.4 Internal business data input (`TECHNICAL DEFAULT`)

Operator-maintained file(s) at `RunConfig.internal_data_path`. Minimal shape — a list of records, each becoming one `Signal` with `source_type: internal_data`:

```yaml
- observed_at: "2026-08-20"
  market: "Brazil"
  language: "pt"
  platform: "tiktok"
  signal_type: "audience_behavior"
  evidence: "Own page X saw 3x saves-per-view on sleep-frequency reels in the last 30 days."
  context: "Internal page analytics, manually recorded."
  confidence: "MEDIUM"
  metrics: { saves_per_view_ratio: "0.04" }
```

---

## 7. Opportunity Model / Schema

The **unit of analysis (C1)**:

> An opportunity is a need, desire or behavior of an audience that shows signals of demand or growth and that can be turned into a content cluster, explored in a specific market/language and platform, and connected to an existing musical asset or a potential new content operation.

**Structural rule (C1): `OPPORTUNITY ≠ CLUSTER`.** The cluster is a downstream editorial structure; V1 only proposes it as a hypothesis.

### 7.1 `Opportunity`

| Field | Type | Required | Enum / Values | Notes |
|---|---|---|---|---|
| `opportunity_id` | string | yes | — | stable, deterministic. `TECHNICAL DEFAULT`: `opp_<run_date>_<slug>` where `slug` is a kebab-case short form of `title`; collisions get `-2`, `-3` |
| `schema_version` | string (semver) | yes | `"1.0.0"` | I4 |
| `run_id` | string | yes | — | run that created it |
| `created_at` | datetime (ISO 8601) | yes | — | |
| `title` | string | yes | — | short human label |
| **Mandatory minimum structure (C1)** | | | | all six required, non-empty |
| `need` | string | yes | — | the need / desire / behavior |
| `audience` | object | yes | `{ description: string, attributes?: map }` | who |
| `market` | string | yes | free string | named market. `TECHNICAL DEFAULT`: a market string (e.g. `"Brazil"`, `"Spanish-speaking LATAM"`, `"US"`, `"Global"`); exact taxonomy is `NEEDS_INPUT` (business-dna §8) |
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
| `provenance` | `Provenance` | yes | §16 | |
| **Registry fields (I2)** | | | | |
| `status` | enum | yes | `EXPLORE` \| `TEST` \| `PARK` (V1); model allows `LAUNCH`/`SCALE`/`KILL` | `TECHNICAL DEFAULT`: created as `EXPLORE`; non-top-N → `PARK` |
| `state_history` | list<`StateChange`> | yes | — | `{ from, to, at, by, note }`; `by` = `system` or a human id |
| `rank` | integer \| `null` | no | — | 1-based position in the presented set; `null` if not presented |
| `report_ref` | string \| `null` | no | — | relative path to the Opportunity Report; `null` if not presented |

### 7.2 `hypotheses` object (all optional, all `HYPOTHESIS`-typed)

| Field | Type | Notes |
|---|---|---|
| `potential_cluster` | string | existing cluster name, or a proposed new cluster (P6 — proposal only) |
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
Signal    *─* EvidenceItem   (via EvidenceItem.signal_ids, only for OBSERVED)
Opportunity 1─* EvidenceItem
Opportunity 1─1 AssetMatch 1─* (playlist_id | page_id | artist_id | catalog_id)  → inventory entries (MUST exist)
Opportunity 1─1 Evaluation
Opportunity 1─1 BusinessOutcomeProfile
Opportunity 1─1 Recommendation
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

The four inventory files, read-only:

- `artists.yaml` — `artist_id`, `name`, `spotify_artist_id`, `distributors_observed`, `release_months_observed`, strategic fields = `NEEDS_INPUT`.
- `playlists.yaml` — `playlist_id`, `name`, `platform` (`Spotify`), `url`, strategic fields = `NEEDS_INPUT`.
- `pages.yaml` — `page_id`, `name`, `platform` (`TikTok`), `handle`, `ownership` (`own` \| `reference_competitor`), strategic fields = `NEEDS_INPUT`.
- `catalog.yaml` — `catalog_id`, `artist_id`, `title`, `release_month`, `distributor`.

### 10.2 Method

1. **Candidate generation (deterministic):** filter inventory entries by any *observable* attributes that align with the opportunity (`platform`; page `ownership = own`; artist/playlist/track **name text** as a lexical hint). Because strategic classification is often `NEEDS_INPUT`, candidate generation is **coarse and permissive**. An artist's `primary_cluster` / catalog affinity is **not** an eligibility filter (see §10.2a) — artist candidate generation `MUST NOT` drop an artist for a cluster mismatch.
2. **Fit assessment (Claude):** for each candidate, judge fit against the opportunity and produce a rationale. For **artists**, the fit judgement weighs, together: (a) catalog affinity; (b) the artist's strategic portfolio role — especially `hero_artist` status (§10.2a); (c) the artist↔playlist relationship when known; (d) the opportunity itself. Fit judgements based on name/title text are **`INFERRED`**, `MUST` carry `LOW` or `MEDIUM` confidence, and `MUST NOT` be written back to the inventory.
3. **Selection (deterministic + Claude):** pick `best_playlist` / `best_page` / `best_artist` or set them to `UNKNOWN`. If nothing fits and the I5 criteria hold, produce a `new_asset_recommendation`.

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
| `fit_basis` | enum | yes | `OBSERVED` \| `INFERRED` | `INFERRED` whenever it relies on `NEEDS_INPUT` classification or name/title text |
| `fit_rationale` | string | yes | — | |
| `role` | enum | no | `candidate` \| `reference` \| `hero` | `reference` for `reference_competitor` pages; `hero` for an artist flagged `hero_artist: true` |

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
| `market` | string | yes | |
| `language` | enum | yes | `pt`\|`es`\|`en` |
| `platforms` | list<enum> | yes | |
| `durability` | enum | yes | |
| `urgency` | enum | yes | |
| `potential_cluster` | string \| `null` | yes | hypothesis; `null` if none |
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

- All four inventory files parse and are non-empty; `business-dna.md` and the guardrail source load. Otherwise → hard failure (§14).

**Signal**

- Conforms to §6.1/§6.3; `source_type` ∈ the four V1 sources; `raw_ref` resolves; `language` ∈ {`pt`,`es`,`en`,`UNKNOWN`}; `metrics` contain no invented figures.

**Opportunity**

- All six C1 mandatory fields present and non-empty.
- `language` ∈ {`pt`,`es`,`en`}.
- `durability` and `urgency` set to valid enum values.
- `evidence` has ≥ 1 item; **≥ 1 `OBSERVED`** item to be eligible for the presented set (`TECHNICAL DEFAULT`).
- Every `EvidenceItem` of type `OBSERVED` has `signal_ids` that all resolve to signals in this run.
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

- All generated free text that could be published-adjacent — `hypotheses.potential_positioning`, `hypotheses.first_content_direction`, `hypotheses.hook`, and report prose — is checked against the 10 guardrails (CLAUDE.md §14). A violation raises a `compliance` `RedFlag`; one Claude revision pass is attempted; if still violating, the offending hypothesis is removed and noted, and the report proceeds.

**Report**

- All 9 sections present and in order; front matter complete; `target_state` ∈ {`EXPLORE`,`TEST`,`PARK`}.
- Presented set size ≤ `max_opportunities_presented`.

**Registry**

- Every presented/parked opportunity has a registry entry with `opportunity_id`, `status`, `created_at`, `report_ref` (or `null`), and a `state_history` entry.

---

## 14. Error Handling

| Situation | Handling |
|---|---|
| Missing required knowledge (any inventory, `business-dna.md`, guardrails) | **Hard failure.** Abort before Signal Collection. Clear message naming the missing file. Exit non-zero. Nothing written to `reports/`. |
| A signal source is unavailable (web search error, no internal-data file, etc.) | **Degrade.** Continue with the remaining sources. Record the failure in `digest.sources_failed`. If **all** sources fail → hard failure. |
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
| `NEEDS_INPUT` | The information is knowable but depends on an owner decision that has not been made. | inventory strategic classification (`cluster`, `market`, `language`, `positioning`, hero artist), musical DNA detail, exact market taxonomy, value-engine weighting | Same handling as `UNKNOWN` for the run, **plus** the affected report section names the specific `NEEDS_INPUT` item so the owner can resolve it. Aggregated into the digest. |

Rules:

- A field that is `UNKNOWN`/`NEEDS_INPUT` in a source stays that way in the output; Claude `MUST NOT` fill it.
- `music_fit` and any regional/market judgement are **structurally capped** in confidence while their inputs are `NEEDS_INPUT` (business-dna §8, §9).
- The digest lists every distinct `NEEDS_INPUT` encountered, so the backlog of owner decisions is visible each run.

---

## 16. Provenance and Traceability

Goal: any claim in a report can be traced to its origin, and a run can be reproduced (C10.2, I4 §9).

- **Signals:** each carries `source`, `source_type`, `url` (if any), `observed_at`, `collected_at`, `run_id`, and `raw_ref` → a file under `data/<run_id>/signals/raw/` holding the full capture (search result text, page snapshot, analyst note).
- **Evidence:** `OBSERVED` items link to `signal_ids`; `INFERRED` items list `derived_from`; `HYPOTHESIS` items carry `rationale`.
- **Asset references:** every `AssetCandidate` names the inventory `asset_id` (which resolves to a specific entry, itself carrying `source_file` / `source_sheet` / `source_row` from I1).
- **Evaluation & profile:** every `justification` `SHOULD` cite evidence items by their statement or index.
- **Run digest** records the reproducibility set: `config_snapshot`, `sources_used`, `sources_failed`, `model`, `prompt_version` (`TECHNICAL DEFAULT` string in `RunConfig`), stage timings, and counts.
- **Reproducibility** = same `RunConfig` + same `data/<run_id>/signals/raw/` + same `prompt_version` + same `model`. Claude output is not bit-reproducible; the raw captures make the *inputs* reproducible and the digest records the *conditions*.
- Everything under `reports/` and the registry is Git-versioned; `data/` is not required to be.

---

## 17. File and Directory Contracts

```
ai-music-media-engine/
├── CLAUDE.md                         # spec authority (read-only to the pipeline)
├── docs/
│   └── TECHNICAL-SPEC-V1.md          # this file
├── config/
│   ├── run.example.yaml              # RunConfig template (TECHNICAL DEFAULT location)
│   └── ranking.yaml                  # ranking comparator constants (TECHNICAL DEFAULT)
├── knowledge/                        # SOURCE OF TRUTH — read-only during a run …
│   ├── DECISIONS-NEEDED.md
│   ├── business-dna/
│   │   ├── business-dna.md
│   │   └── content-methodology.md
│   ├── rules/                        # C4 guardrails to be consolidated here
│   ├── clusters/
│   ├── market/
│   │   └── opportunity-registry.yaml # … EXCEPT this file, appended by runs (I2; TECHNICAL DEFAULT)
│   └── inventories/
│       ├── artists.yaml  playlists.yaml  pages.yaml  catalog.yaml   # asset truth (I1) — never modified
│       └── source/                   # original spreadsheets
├── data/                             # generated, regenerable — git-ignored (TECHNICAL DEFAULT)
│   └── <run_id>/
│       ├── signals/raw/…             # raw captures (raw_ref targets)
│       ├── signals/normalized.json
│       ├── opportunities.json        # full structured records before rendering
│       └── run.log
└── reports/                          # generated, durable, versioned (I7)
    └── <run_id>/
        ├── digest.md
        ├── <opportunity_id>.md
        └── <opportunity_id>.json
```

- The pipeline reads `knowledge/` and writes only `data/<run_id>/`, `reports/<run_id>/`, and appends `knowledge/market/opportunity-registry.yaml`.
- Persistence formats: **YAML** (config, inventories, registry), **Markdown + YAML front matter** (reports, digest, knowledge), **JSON** (intermediates, report sidecars). No database (I10).

---

## 18. Component Responsibilities

Modular pipeline (I8). Each component is an independent unit with a typed input and output; the orchestrator calls them in sequence.

| Component | Input | Output | Owner | On failure |
|---|---|---|---|---|
| **Orchestrator** | `RunConfig` | run result + exit code | deterministic | propagate hard failures; collect per-opportunity exclusions |
| **Knowledge Loader** | paths from config | context bundle (business DNA, guardrails, 4 inventories, registry) | deterministic | hard failure if required file missing/unparseable |
| **1. Signal Collection** | `RunConfig.scope`, sources | raw signal candidates + `data/<run_id>/signals/raw/` | Claude (research) + deterministic (internal-data load, capture writing) | degrade per source; hard failure if all sources fail |
| **2. Signal Normalization** | raw candidates | `list<Signal>` (validated, de-duplicated, id-assigned) | deterministic (schema, ids, dedupe) + Claude (fill ambiguous `signal_type`/`market`/`language`) | reject invalid signals with logged reason |
| **3. Analysis / Framing** | `list<Signal>` + business DNA | `list<Opportunity>` (C1 fields, evidence typing, durability/urgency, hypotheses) | Claude (framing) + deterministic (mandatory-field enforcement, `opportunity_id`) | exclude malformed opportunities after 1 retry |
| **4. Asset Matching** | `list<Opportunity>` + inventories | each opportunity's `AssetMatch` | deterministic (candidate filter, existence check) + Claude (fit judgement, I5 evaluation) | drop bad references → `UNKNOWN` |
| **5. Evaluation** | opportunities + evidence + `AssetMatch` | `Evaluation` + `BusinessOutcomeProfile` + `Recommendation` per opportunity | Claude (rate, justify, red flags, profile, recommend) + deterministic (enum/completeness/no-score validation, compliance check) | exclude opportunity after 1 failed retry |
| **6. Ranking / Prioritization** | evaluated opportunities | ordered list; `presented` / `parked` / `excluded` sets; `rank` | deterministic (comparator §11) | n/a (pure function) |
| **7. Report Generation** | presented opportunities | `reports/<run_id>/*.md` + `*.json` + `digest.md` | deterministic (structure, front matter, sidecar, digest) + Claude (section prose) | fail the report → move opportunity to `excluded`, keep run |
| **Registry Updater** | presented + parked opportunities | updated `opportunity-registry.yaml` | deterministic | fail run if registry write fails |

No component calls another directly; no component is an "agent" with open-ended tool use. Multi-component parallelism is **not** in V1 (P5).

---

## 19. Claude vs Deterministic Code Responsibilities

| Claude (research, interpretation, framing, evaluation, synthesis) | Deterministic code (processing, validation, matching mechanics, aggregation, ranking, rendering) |
|---|---|
| Web-search research; gathering TikTok Creative Center / YouTube observations | Loading knowledge & inventories; integrity checks |
| Classifying ambiguous `signal_type` / `market` / `language` | `Signal` schema validation, `signal_id` assignment, de-duplication, raw-capture writing |
| Framing signals into `Opportunity` objects (need, audience, consumption context) | Enforcing the six C1 mandatory fields; `opportunity_id` assignment |
| Assigning `durability` / `urgency` labels | Enum validation for `durability` / `urgency` |
| Typing evidence as `OBSERVED` / `INFERRED` / `HYPOTHESIS` and writing rationale | Checking that `OBSERVED` items resolve to real `signal_id`s |
| Judging asset fit and writing rationale; evaluating the four I5 conditions | Inventory candidate filtering; **asset existence verification**; blocking inventory write-back |
| Rating the 10 dimensions + confidence + justification; producing red flags | Verifying all 10 present; **scanning for any numeric 0–100 score**; enum validation |
| Producing the 5-axis Business Outcome Profile | Verifying all 5 axes present |
| Producing `Recommendation` (`target_state`, `suggested_next_step`, `justification`) | Constraining `target_state` to `EXPLORE`/`TEST`/`PARK`; attaching the fixed `execution_note` |
| Compliance self-check against the C4 guardrails; one revision pass | Triggering the compliance check; enforcing removal of unfixable violations |
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
| `scope` | object | yes | — | the research brief (`TECHNICAL DEFAULT` shape below) |
| `scope.clusters` | list<string> | no | `[]` (= all / open discovery) | existing cluster names to focus on; empty = open |
| `scope.markets` | list<string> | no | `[]` | market strings to focus on |
| `scope.languages` | list<enum> | no | `["pt","es","en"]` | subset of the three |
| `scope.platforms` | list<enum> | no | `["tiktok","youtube"]` | discovery platforms (`TECHNICAL DEFAULT`) |
| `scope.notes` | string | no | — | free guidance for the framing step |
| `signal_sources` | list<enum> | yes | `["web_search","tiktok_creative_center","youtube","internal_data"]` | subset of the four (C2) |
| `internal_data_path` | path | no | — | required if `internal_data` in `signal_sources` |
| `max_opportunities_presented` | integer | yes | `10` | I12 upper bound |
| `min_opportunities_target` | integer | yes | `5` | C10 lower target (advisory, not enforced) |
| `model` | string | yes | — | a Claude model identifier; chosen at config time (I10) |
| `extraction_model` | string | no | = `model` | `TECHNICAL DEFAULT`: optional lighter model for classification/extraction |
| `prompt_version` | string | yes | — | recorded in provenance (`TECHNICAL DEFAULT` for P8) |
| `paths` | object | yes | repo defaults (§17) | `knowledge_dir`, `inventories_dir`, `registry_path`, `reports_dir`, `data_dir` |
| `dry_run` | bool | no | `false` | `TECHNICAL DEFAULT`: stop after stage 3 (Framing), skip Evaluation/Ranking/Reports |

### 20.2 Other configuration

- `config/ranking.yaml` — the comparator key order and the exclusion rule of §11 as data, not code.
- Model API credentials via **environment variable** (`TECHNICAL DEFAULT`); never in `RunConfig` or the repo.
- Rating anchors appendix (per §8.3) — added alongside the first real run.

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
| 2 | Provenance model (§16): `raw_ref` per signal, `signal_ids` per `OBSERVED` evidence, `observed_at` required; validator §13 |
| 3 | `EvidenceItem.type` enum + report section 3 renders type badges (§7.3, §12.3) |
| 4 | Asset existence verification is deterministic and mandatory (§10.4, §19); `UNKNOWN` sentinel (§15) |
| 5 | Human judgement over 3 runs; the digest's ranked table + per-dimension summary supports the review |
| 6 | Human action; `Recommendation.target_state = TEST` + `suggested_next_step` gives the owner a concrete option; registry records the advance |

Criteria 5 and 6 are human-judged. `TECHNICAL DEFAULT`: the owner records the per-run verdict (relevance %, advanced opportunity id) in `reports/<run_id>/review.md` so the 3-run gate is auditable.

---

## 22. Test Strategy

Tests precede implementation code (repo uses the `superpowers:test-driven-development` skill).

**Deterministic components — exact/golden tests**

- `Signal` / `Opportunity` / `Evaluation` / `BusinessOutcomeProfile` / `AssetMatch` / `Recommendation` / `OpportunityReport` / `RunConfig` schema validators: fixture pairs (valid, and one invalid per rule in §13).
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

**Modes**

- `dry_run` path (stop after Framing) for cheap iteration.
- A recorded-fixtures mode (`TECHNICAL DEFAULT`): replay saved raw captures instead of live web search, so deterministic stages can be tested end-to-end without network or model calls.

**Acceptance**

- The 3-run C10 gate (§21), owner-reviewed, recorded in `review.md` per run.

---

## 23. Future Extension Points

Each maps to a `DEFERRED` decision or an open item; none is built in V1.

| Extension | Enabled by | Decision |
|---|---|---|
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
| C1 opportunity definition + minimum structure | §7, §7.1 |
| C2 signal sources + `Signal` schema | §3, §6, `RunConfig.signal_sources` |
| C3 business DNA as source of truth | §3, §15 (`NEEDS_INPUT` handling), §9.2 (YouTube roles) |
| C4 guardrails | §13 compliance check, §14, `RedFlag.kind = compliance` |
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
