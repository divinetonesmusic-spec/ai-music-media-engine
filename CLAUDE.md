# AI Music Media Engine

> Consolidated operational specification for the project.
> The formal decisions and their detailed history live in `knowledge/DECISIONS-NEEDED.md`
> (C1–C10 and I1–I12 are DECIDED; P1–P10 are DEFERRED).
> Where this document and a DECIDED decision diverge, the decision prevails — surface the divergence instead of guessing.

---

## 1. Project Purpose

AI Music Media Engine is an intelligent content-growth system designed to scale a music business through market intelligence, opportunity analysis, content production, distribution, analytics and optimization.

The system transforms:

Market signals
→ opportunities
→ clusters
→ pages
→ content
→ publishing
→ analytics
→ learning

The long-term objective is a scalable media operation that discovers opportunities, creates content, distributes it and learns from performance. The authoritative stage-by-stage pipeline is in §16.

---

## 2. Business Context

The business produces AI-assisted instrumental relaxing music, positioned as **wellness**, and operates as a franchise/portfolio of **artists and playlists** organized by thematic cluster.

Full business identity, mission, monetization and musical DNA: `knowledge/business-dna/business-dna.md`. Key points:

- **Monetization:** primarily music royalties. Relevant ecosystems today: Spotify, TikTok, YouTube Music. A second business opportunity exists in **YouTube as a video platform** (own audiovisual media) — a later, dedicated effort, not part of V1 (see §16).
- **Priority language markets:** Portuguese, Spanish, English. No specific countries are assumed beyond this.
- **Historically relevant clusters (examples, not a fixed list):** Sleep; Anxiety / Relaxation; Abundance / Prosperity; Energetic Cleansing; Healing / Well-being; Study / Focus; Meditation.
- The system must be able to discover **new** clusters from market signals. In V1 a new cluster is only **proposed as a hypothesis** inside a report; formal cluster governance is deferred.
- **Brand non-negotiable:** the system must not become a spam tool (see §14).

Musical DNA detail (instrumentation, energy, duration, texture, BPM, use of frequencies, vocal/instrumental) is still `NEEDS_INPUT` in `business-dna.md` — do not invent it.

---

## 3. Existing Assets

The business already operates with real assets. The structured inventory lives in `knowledge/inventories/`, derived from the source spreadsheets in `knowledge/inventories/source/`. Strategic classification (cluster, market, language, positioning, hero artist) is `NEEDS_INPUT` until set by the owner.

- `artists.yaml` — artist roster (Spotify artist IDs, distributors, release history).
- `playlists.yaml` — Spotify playlists.
- `pages.yaml` — social pages, split into **own** vs **reference/competitor** as marked in the source.
- `catalog.yaml` — music catalog (releases, each traceable to its source row).

Rules:

- Treat the inventory as the source of truth for existing assets when assessing Asset Fit, Music Fit and the recommended playlist/page.
- An artist's catalogue/cluster affinity is **context, not a placement restriction**: any artist can be placed in any cluster or playlist per business strategy, and `hero_artist` status is a separate strategic classification. Never infer that an artist does not fit an opportunity from a cluster mismatch. Keep `catalog affinity`, `playlist placement` and `strategic hero status` distinct. (See `knowledge/business-dna/business-dna.md` §10–§11.)
- When a needed asset is not in the inventory, use `UNKNOWN` — never invent playlists, artists or pages.
- The current inventory covers TikTok pages, Spotify playlists, artists and catalog. Instagram and Facebook pages have been referenced historically but are **not yet inventoried** — treat them as `UNKNOWN` until added.
- Historical performance data (streams, saves, followers, skip rate) is **not yet available in structured form** — it is `UNKNOWN` across the current inventory.

**Asset reuse is the default (I5).** Spotify playlists are an established asset; do not assume an opportunity needs a new one. Whenever possible identify the best existing playlist / page / artist. A **new** page or asset may be **recommended** — never auto-created in V1 — only when, cumulatively or strongly enough:

- no existing asset has adequate fit;
- the opportunity has relevant potential;
- there is plausible differentiation potential;
- the opportunity has enough durability / window to justify the investment.

Existing content methodology is documented in `knowledge/business-dna/content-methodology.md` — **historical operational knowledge, not rigid rules**. The system preserves the principles that have shown value but keeps autonomy to propose and test new hooks, structures, formats, durations and ways to promote music beyond the ones currently in use.

---

## 4. Strategic Objective

Optimize for the funnel, not for views. Views are an intermediate metric.

Reach → Audience → Profile Visits → Traffic → Playlist Engagement → Streams → Saves → Followers

There are **two distinct value paths that must not be collapsed into one objective**:

- **Playlist Growth** — content drives traffic to playlists → consumption and engagement → playlist and artist growth → royalties.
- **Music Trend / UGC** — high-reach content increases the chance a track is reused as audio by others → the track becomes a trend → usage-related royalties.

### Business Outcome Profile

Every opportunity is assessed against the ecosystem's value engines, kept **separate**. An opportunity can be high in one and low in another and still be strategic.

- Playlist Growth Potential
- Music Trend / UGC Potential
- Streaming Royalty Potential
- Page Growth Potential
- YouTube Media Potential

These are **evaluation / context axes**, not independent revenue lines, and not the same as the evaluation dimensions of §8: the dimensions explain how strong the opportunity is; the Business Outcome Profile explains which engines it can feed.

The system seeks combinations of **cluster, audience, market, language, platform and page** — with hook, format, visual language, copy and CTA as **downstream** concerns (see §15 and §16) — that produce meaningful business outcomes.

---

## 5. Core Principle

The system must NOT begin with "What content should we make?".

It begins with "What market opportunity exists that can be turned into content and connected to our existing assets?".

Market Intelligence is therefore the first strategic layer (§16, stage 1).

---

## 6. What Is an Opportunity

**Official definition (provisional for V1; to be revised with post-V1 calibration data — C1):**

> An opportunity is a need, desire or behavior of an audience that shows signals of demand or growth and that can be turned into a content cluster, explored in a specific market/language and platform, and connected to an existing musical asset or a potential new content operation.

**Mandatory minimum structure of an opportunity:**

- need / desire / behavior
- audience
- market
- language
- platform
- consumption context

**Derived or hypothetical fields** (filled as hypotheses, non-binding — see §15):

- potential cluster
- potential angle
- format
- hook
- compatible musical assets

**Structural rule: `OPPORTUNITY ≠ CLUSTER`.** The opportunity is the market opportunity. The cluster is the editorial structure that may later be created to explore it, in a subsequent pipeline stage.

---

## 7. Market Signals & Discovery

**V1 signal sources (C2):**

1. Live Web Search
2. TikTok Creative Center
3. YouTube
4. Internal business data (initially provided manually / structured)

Spotify is **not** a primary source for discovering social trends in V1; it is used later mainly to assess an opportunity's fit with existing playlists, artists and assets. Paid APIs and additional integrations are out of V1 scope (deferred). The architecture must allow new sources and APIs to be added **without rebuilding the pipeline**.

**Signal schema.** Every piece of evidence is normalized to a `Signal` with at least:
`signal_id`, `source`, `source_type`, `observed_at`, `market`, `language`, `platform`, `signal_type`, `evidence`, `context`, `confidence`.

**Evidence typing.** The system must explicitly distinguish:

- `OBSERVED` — a fact observed in a source
- `INFERRED` — a reasoned inference
- `HYPOTHESIS` — a proposition still to be tested

Signal types the system may investigate include search and social trends, hashtags, emerging themes, content formats, competitor activity, audience behavior, wellness / sleep / meditation / relaxation / focus / abundance trends, emotional needs, and regional / language / platform-specific opportunities.

**Durability & Urgency (I9).** Each opportunity carries:

- **Durability:** `EPHEMERAL` (very short-lived) · `EMERGING` (currently growing) · `STRUCTURAL` (relatively persistent demand) · `EVERGREEN` (recurring, lasting need)
- **Urgency:** `LOW` · `MEDIUM` · `HIGH`

Durability and Urgency are context / evaluation attributes — not automatic rules that decide alone whether an opportunity is good or bad. The business works simultaneously with fast trends and evergreen demand; the system must tell them apart.

---

## 8. Opportunity Evaluation

**V1 does NOT use a composite 0–100 numeric score (C6).** Evaluation is built from:

1. A multidimensional profile over the **10 evaluation dimensions (C9)**:
   1. Signal Strength
   2. Audience Potential
   3. Growth / Momentum
   4. Durability / Opportunity Window
   5. Music Fit
   6. Content Potential
   7. Competitive Position
   8. Differentiation Potential
   9. Asset Fit
   10. Business Outcome Potential — detailed via the Business Outcome Profile (§4)
2. A qualitative rating per dimension: `LOW` · `MEDIUM` · `HIGH` · `VERY HIGH`
3. A separate **confidence** level: `LOW` · `MEDIUM` · `HIGH`
4. Relevant **red flags** or blocking factors
5. An operational **recommendation** (see §9)

Each dimension carries a justification grounded in the available evidence whenever applicable. Confidence must be preserved: low confidence must not be presented as certainty just because some dimensions were rated high.

The system must not invent weights or mathematical formulas for a composite score without enough data to justify their validity. A quantitative model may be reconsidered later, once real performance data from tests exists (deferred).

---

## 9. Opportunity Lifecycle

**Conceptual long-term lifecycle:** `EXPLORE → TEST → LAUNCH → SCALE → KILL`, with `PARK` as an additional pause / prioritization state.

- `EXPLORE` — interesting signal, insufficient evidence.
- `TEST` — enough potential to justify a small content experiment.
- `LAUNCH` — enough evidence to justify a new page / content operation.
- `SCALE` — validated opportunity ready for significant expansion.
- `KILL` — failed to demonstrate potential after appropriate testing.
- `PARK` — a good opportunity that should not take attention or execution capacity right now.

**Operationally used in V1:** `EXPLORE`, `TEST`, `PARK`. `LAUNCH`, `SCALE` and `KILL` stay conceptual/deferred — their measurable transition criteria and any automation wait until real performance data from tests exists.

Market Intelligence may **recommend** advancing an opportunity from `EXPLORE` to `TEST`, but does not run the test. Advancing stays under human approval.

**`recommended_action` structure (I3):**

- `target_state` — any of the lifecycle states listed above; V1 execution stays limited to `EXPLORE` / `TEST` / `PARK`
- `suggested_next_step` — a concrete, actionable next step; still a recommendation, not executed automatically in V1
- `justification` — grounded in the opportunity's evidence and evaluation

A central persistent **opportunity registry** records at least: stable `opportunity_id`, `status`, `created_at`, a reference to the Opportunity Report, and a minimal state-change history. It must allow future evolution without breaking existing reports.

---

## 10. Opportunity Report

Output format: **Markdown with YAML front matter** — human- and machine-readable, Git-versionable. Versioned via `schema_version` so the schema can evolve without breaking older reports. No database in V1.

Minimum sections (I4):

1. **Identity** — `opportunity_id`, `created_at`, `run_id`, `schema_version`
2. **Market Context** — market, language, platforms, need / desire / behavior, audience, consumption context
3. **Evidence** — signals used, sources, URLs when available, observation dates, confidence, and the `OBSERVED` / `INFERRED` / `HYPOTHESIS` distinction
4. **Evaluation** — the 10 dimensions (§8), rating, justification, confidence, relevant red flags
5. **Business Outcome Profile** — the 5 axes (§4)
6. **Asset Fit** — matching artists, playlists, pages; `UNKNOWN` when evidence is insufficient
7. **Hypotheses** — potential cluster, potential positioning, potential page, first content direction
8. **Recommendation** — `target_state` (any conceptual lifecycle state — `EXPLORE` / `TEST` / `LAUNCH` / `SCALE` / `KILL` / `PARK`; V1 execution stays limited to `EXPLORE` / `TEST` / `PARK`), `suggested_next_step`, `justification`
9. **Provenance** — origin of the data used, signal sources, information relevant to reproducibility

The report must explicitly separate observed facts, inferences and hypotheses. Use `UNKNOWN` whenever required information is unavailable or unsupported by sources.

Reports and run digests are written to `reports/` (see §11).

---

## 11. Knowledge & Data Organization

**`knowledge/` is the source of truth** for the business and its rules — human-owned, Markdown with YAML front matter when structured metadata is needed. Structure (I6):

- `knowledge/business-dna/` — business identity, strategy, monetization, metric priorities, markets, languages, musical DNA, positioning.
- `knowledge/rules/` — compliance, safety, copyright, operational limits, autonomy limits, other execution restrictions.
- `knowledge/market/` — accumulated market knowledge, historical signals, learnings, competitors, opportunities and market context.
- `knowledge/clusters/` — formal cluster definitions; rules and characteristics of formalized clusters.
- `knowledge/inventories/` — artists, playlists, pages, catalog and other structured assets.

**Generated output (I7):**

- `data/` — raw signals, caches, intermediate and regenerable data, temporary run artifacts.
- `reports/` — Opportunity Reports, run digests, durable workflow results, analysis artifacts that must be preserved and versioned.

Temporary or regenerable data must never be treated as source knowledge.

The formal decision log is `knowledge/DECISIONS-NEEDED.md`.

---

## 12. Architecture Principles & Technical Stack

Prefer specialized components over one giant agent.

- **AI** for: research, strategy, reasoning, classification, copy generation, interpretation, synthesis, optimization.
- **Deterministic code** for: signal collection, normalization, validation, matching, aggregation, ranking, file / video / audio processing, batch operations, data transformation.
- **APIs / integrations** for: external services, publishing, analytics, data collection.

**Market Intelligence V1 is a pipeline of specialized components (I8), not a single monolithic prompt.** Conceptual flow:

1. signal collection
2. signal normalization
3. analysis / framing
4. asset matching
5. evaluation
6. ranking / prioritization
7. Opportunity Report generation

Multi-agent orchestration is **not** required for V1 and is deferred.

**Initial technical stack (I10):**

- Runtime: Python 3
- LLM: Claude
- Persistence: YAML + Markdown + JSON as needed — no database in V1
- Version control: Git
- Dev environment: Claude Code + VS Code
- No queue or server in V1

Do not introduce unnecessary complexity. The stack may evolve as the production, video, audio, publishing and analytics stages are implemented.

---

## 13. Human Approval & Autonomy

Autonomy levels:

- **Level 1** — recommendation only.
- **Level 2** — execute after human approval.
- **Level 3** — execute automatically under explicit rules.

**V1 operates strictly at Level 1 for every action.** The system recommends; the human approves and executes — advancing an opportunity to `TEST`, creating any new asset, and so on. Level 2 and Level 3 are deferred until reliability is demonstrated.

---

## 14. Compliance & Safety Guardrails

Minimum operational guardrails for V1 (C4). Full rules will be consolidated in `knowledge/rules/`.

1. Do not create claims of cure, treatment, diagnosis or prevention of diseases.
2. Wellness content may address relaxation, environment, ritual, intention, focus, comfort and subjective experience.
3. Do not present frequencies, music, meditation or related practices as medical treatment.
4. Do not invent scientific evidence.
5. Do not fabricate numbers, trends, research results or other evidence.
6. Do not improperly copy third-party content, identity or assets.
7. Do not produce spam or mass content whose only purpose is to flood platforms.
8. Prioritize content genuinely relevant and useful to the audience.
9. Claims that depend on evidence must be flagged for validation.
10. When in doubt, state the uncertainty instead of inventing an answer.

These guardrails are operational for V1 and will be refined as later stages are implemented.

---

## 15. Current Development Phase — V1

**Current phase: V1 — Market Intelligence + Opportunity Analysis.**

V1 implements **only**:

Market Intelligence → Opportunity Analysis → Opportunity Report

- **Market Intelligence** — discovers, collects and organizes relevant market signals.
- **Opportunity Analysis** — structures, evaluates, compares and prioritizes opportunities based on evidence, evaluation dimensions, confidence, red flags and the Business Outcome Profile.

In V1 these run as a single functional workflow but stay conceptually separate for modularity.

### V1 scope (C7)

Market Intelligence V1 **is responsible for**: discovering opportunities; structuring them; recording evidence; evaluating them; prioritizing them; assessing fit with existing assets; recommending an action for the next step.

It **may provide light hypotheses** about potential cluster, positioning, page and first content direction. These are not final decisions and do not replace the later stages.

Market Intelligence V1 is **NOT responsible for**: defining the full Page Blueprint; the full content strategy; producing batches of hooks and content; producing video; producing audio; publishing content; running the social operation. Do not implement automated social publishing or the production system yet. Do not build infrastructure ahead of a validated V1 workflow.

Separation rule: Market Intelligence answers *"which opportunities exist and which deserve our attention?"*; the later stages answer *"how should we explore this opportunity?"*. Observations and creative hypotheses must be explicitly marked as observation or hypothesis, not as definitive strategy.

### Output volume (I12)

At most **10 prioritized opportunities per run** are presented to the owner as the main result. The pipeline may identify and keep additional opportunities internally (`PARK`), but only the prioritized set is the primary output. Avoid generating a volume of opportunities beyond the operator's real review capacity.

### Definition of Done (C10)

V1 is considered validated when, over **3 consecutive runs**:

1. It produces between 5 and 10 prioritized opportunities per run.
2. 100% of evidence is traceable, including source and observation date.
3. It explicitly distinguishes observed facts / evidence from hypotheses.
4. It does not invent playlists, artists or pages; when an asset is not available in the inventory it uses `UNKNOWN`.
5. At least 70% of the opportunities presented in the Top 10 are considered by the owner relevant enough for analysis or testing.
6. At least one opportunity is selected by the owner to advance to the next stage during the validation period.

These criteria are V1-specific and may be replaced or complemented by quantitative metrics once real test and performance data exist.

---

## 16. Canonical Pipeline & Long-Term Architecture

Canonical pipeline (C8):

1. Market Intelligence
2. Opportunity Analysis
3. Cluster Strategy
4. Page Blueprint
5. Content Strategy
6. Content Production
7. Video Engine
8. Audio Engine
9. Quality Control
10. Publishing
11. Analytics
12. Optimization
13. Learning

Only stages 1–2 are implemented in V1 (§15). Stages 3–13 are the official future architecture and must not be built ahead of a validated V1.

**YouTube has two distinct roles that must not be merged into a single operation:**

- **YouTube Music** — distribution / consumption of the music catalog and royalty generation.
- **YouTube Video** — the business's own audiovisual media operation, with strategy, content, retention, audience and monetization different from short-form. Its strategy is a later, dedicated effort, outside V1.

The architecture may evolve as the project develops. The current goal is not to build everything — it is to build the foundation correctly.

---

## 17. Engineering Rules

Before creating code:

1. Inspect the existing project — including `knowledge/`, the inventories, and `knowledge/DECISIONS-NEEDED.md`.
2. Reuse existing structures when appropriate.
3. Do not create duplicate systems.
4. Prefer small, composable components.
5. Keep business logic documented.
6. Keep generated data (`data/`, `reports/`) separate from source knowledge (`knowledge/`).
7. Make important decisions explicit — record them in `knowledge/DECISIONS-NEEDED.md`.
8. Do not silently change business strategy.
9. When uncertain about a business rule, surface the uncertainty (`NEEDS_INPUT` / `UNKNOWN`) instead of inventing a rule.
10. Build incrementally and validate each stage — see the §15 Definition of Done — before expanding.
