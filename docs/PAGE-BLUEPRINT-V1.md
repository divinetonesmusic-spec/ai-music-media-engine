# Page Blueprint V1 — Contract

> **Status: DECIDED — 2026-09-04.** Canonical pipeline **stage 4 (Page
> Blueprint)** is open; stages 5–13 stay deferred. Cluster Strategy (stage 3)
> is built, merged and live-validated (`docs/CLUSTER-STRATEGY-V1.md`, PR #1),
> and its output — the `ClusterStrategy` sidecar — is this stage's input
> contract. On 2026-09-04 the owner opened stage 4 — and only stage 4 — with an
> explicit authorization *"equivalente ao padrão D-CS-1"*, and the twelve open
> decisions (**D-PB-1 … D-PB-12**) are decided at their recommended answers.
> Those decisions are recorded in `knowledge/DECISIONS-NEEDED.md`, section
> **"# 6. ESTÁGIO 4 — PAGE BLUEPRINT"** (P4 updated accordingly). §11 below
> mirrors them for reference; the authoritative record is the decision log.
>
> Page Blueprint is **canonical pipeline stage 4 (C8)**. Autonomy **Level 1** —
> it recommends, the human approves and executes. This document is the contract
> that every `src/page_blueprint/` module cites (`contract §N`). Where this
> document and a DECIDED decision (C1–C10 / I1–I12 / D-CS-1–D-CS-12 /
> D-PB-1–D-PB-12 in `knowledge/DECISIONS-NEEDED.md`) diverge, **the decision
> prevails** — surface the divergence instead of guessing.
>
> **P4 / D-PB-1.** Opening canonical stage 4 is decision **D-PB-1**, recorded in
> `knowledge/DECISIONS-NEEDED.md` (§6; P4 now reads "estágios 3–4 abertos;
> estágios 5–13 seguem DEFERRED"). This document does not substitute for that
> record — it implements it.
>
> Derived from the 2026-09-04 Stage 4 mission, which cross-referenced `CLAUDE.md`,
> `docs/TECHNICAL-SPEC-V1.md`, `docs/CLUSTER-STRATEGY-V1.md`,
> `docs/SESSION-STATE.md`, `knowledge/DECISIONS-NEEDED.md`,
> `AI Music Media Engine — Business DNA V1.md`, `knowledge/business-dna/*`
> (including the owner-approved Musical DNA §9), `knowledge/clusters/cluster-taxonomy.md`,
> `knowledge/rules/guardrails.yaml`, `knowledge/inventories/*`, and the stage 1–3
> implementation. It changed none of those sources.

---

## Preamble — the gate condition and the one contradiction to preserve

**Page Blueprint = canonical pipeline stage 4 (C8).** Its build was governed by
**P4 (`Estágios seguintes do pipeline`)**, owner-decided. Stage 3 (Cluster
Strategy) was opened on 2026-09-01 via D-CS-1; **D-CS-1's own record already
names "Page Blueprint" as one of the stages 4–13 that "permanecem DEFERRED sob a
P4"** — so opening stage 4 is a distinct, explicit owner action, exactly as
D-CS-1 was for stage 3.

**Gate check for stage 4.** Stage 4's one *technical* precondition — an
owner-approved Musical DNA §9 in `knowledge/business-dna/business-dna.md` — is
**met** (transferred by the owner, commit `2b8df10`; `_musical_dna_needs_input()`
returns `False` in production). Rating Anchors, the Musical DNA MI wiring, and
value-engine weighting do **not** gate this stage. The owner opened it on
2026-09-04.

**The load-bearing contradiction between documents** (surfaced, not silently
reconciled):

| `AI Music Media Engine — Business DNA V1.md` §11–§13 | The DECIDED V1 contract | This contract keeps |
|---|---|---|
| §11 — "Cluster Strategy" already defines *linguagem, estética, conteúdo, CTA* | **C8 / D-CS-8** put visual identity + tone of voice in **Page Blueprint (stage 4)** and pillars/formats/hooks/CTAs in **Content Strategy (stage 5)**. | **The established boundary.** Cluster Strategy stops at cluster concept + positioning; Page Blueprint adds page identity + **visual identity** + **tone of voice** + a page-level content framing; it stops before the content *system*. |
| §12 — Page Blueprint produces "identidade visual, tom de voz, cadência, **pilares de conteúdo dessa página**" | C8: Page Blueprint's pillars are **page-level and broad**; the content *system* (formats, hooks, structures, CTA copy, calendar) is stage 5. | Page Blueprint produces `content_pillars` (≤5 broad thematic pillars for *this page only*), platforms, and a *qualitative* posting-cadence recommendation. **No formats, hooks, structures, CTA copy, linguistic/visual production rules, or a calendar** (D-PB-6). |
| §12 — Page Blueprint "escolhe playlist e artista associados" | **I5 / D-CS-8** already have Cluster Strategy carry the `AssetMatch` asset decision (playlist reuse / page recommendation) forward; re-deciding it in stage 4 would duplicate the judgement. | **The asset is carried verbatim** from `ClusterStrategy.asset_strategy` — Page Blueprint never re-decides whether a new asset is warranted (I5) or which asset anchors the page (D-PB-3). Claude never sees it as a decision to make. |
| §8 — every opportunity gets a **0–100 score** | **C6** — no composite 0–100 score, ever | No 0–100 score in Page Blueprint either. One qualitative `overall_confidence ∈ {LOW, MEDIUM, HIGH}`, **clamped to the input Cluster Strategy's own `overall_confidence`** and never raised by the page synthesis. |
| §9/§10 — states are `EXPLORE / TEST / LAUNCH / SCALE / KILL` (no PARK) | **I2** — V1 operational states are `EXPLORE / TEST / PARK`; LAUNCH/SCALE/KILL conceptual/deferred | Page Blueprint **does not transition** the opportunity lifecycle (autonomy L1). It never carries or reads a lifecycle state — that stayed with Cluster Strategy. Its only output vocabulary is a *pipeline-action* recommendation (`target_next_stage`), which is not a lifecycle state. |
| §5 — 9 stages ("Distribution") | **C8** — 13 stages ("Publishing") | C8 (DECIDED). Naming divergence noted, non-blocking (D-PB-12). |

Per the mission's critical rules: **the established V1 contract prevails;
`AI Music Media Engine — Business DNA V1.md` supplies strategic intent for *what a
page blueprint should contain*, not the contract style.**

---

# 1. PURPOSE

**Problem it solves.** Cluster Strategy (stage 3) answers *"does this
owner-approved opportunity map to a canonical cluster, and what is the cluster's
strategic definition and asset strategy?"* and stops there — deliberately, at
D-CS-8's boundary. It produces a positioning statement and carries the asset
decision, but it produces **no page**: no concept name, no bio, no visual
identity, no tone of voice, no page-level content framing. Content Strategy
(stage 5) needs a concrete page to design a content system against; without stage
4 it would either invent the page ad hoc or design a system against a cluster
abstraction.

**Page Blueprint converts one Cluster-Strategy-recommended opportunity into one
concrete page design** — identity, visual identity + tone of voice grounded in
the business's Musical DNA (§9), the carried asset link, and a shallow page-level
content framing — that is stable enough for Content Strategy to consume.

**Where it sits.**

```
[stage 1–2]  Market Intelligence → Opportunity Analysis → Opportunity Report      (built, C10-validated)
                                          │  owner reviews review.md, marks one "advance"
                                          ▼
[stage 3]    Cluster Strategy   ──────────────────────────▶  Cluster Strategy Report   (built, merged, live-validated — PR #1)
                                          │  Cluster Strategy recommends target_next_stage = PAGE_BLUEPRINT
                                          ▼
[stage 4]    PAGE BLUEPRINT     ── this contract ──▶  Page Blueprint Report
                                          │
                                          ▼
[stage 5]    Content Strategy                                                     (still deferred, P4)
```

Input contract: the `ClusterStrategy` machine sidecar
`reports/cluster-strategy/<opportunity_id>.json` (`docs/CLUSTER-STRATEGY-V1.md`
§14 — *"the `ClusterStrategy` sidecar is Page Blueprint's input contract (stage
4)"*). Output contract: a new `PageBlueprint` object that becomes Content
Strategy's input.

**What it must NOT do yet.**

- **Not** re-decide the cluster, the positioning, the audience, or the market —
  those are carried from Cluster Strategy, frozen in a `ClusterStrategySnapshot`.
- **Not** re-decide the asset. Which page / playlist / artist anchors this page,
  and whether a new page is warranted (I5), were decided by Cluster Strategy and
  are carried **verbatim** (D-PB-3). Claude is given the asset as *context*, never
  as a choice.
- **Not** produce a content system (pillars beyond a broad page-level outline,
  formats, hooks, structures, CTA copy, linguistic/visual production rules,
  posting *calendar*, batch sizes, templates, variations, the `CONTENT_OBJECT`
  schema) — Content Strategy, stage 5. Business DNA V1 §13 (D-PB-6).
- **Not** consume anything from Musical DNA §9 beyond the house-sound principle
  and the per-cluster sonic expression (§9.9). Instrumentation, BPM, frequency
  use, sonority-rejection criteria are **Audio Engine's** (stage 8) — Page
  Blueprint reads none of them (D-PB-4).
- **Not** invent an artist, playlist, or page (I1). Every id resolves in the
  inventory or is `UNKNOWN` / `NEW_ASSET`.
- **Not** write anything under `knowledge/`. Page Blueprint has **no** registry
  or taxonomy write path — not even the opt-in append Cluster Strategy has
  (D-CS-7). It reads `knowledge/`, it writes only `reports/page-blueprint/`
  (D-PB-9).
- **Not** introduce a 0–100 score, weights, or a formula (C6).
- **Not** introduce `LAUNCH / SCALE / KILL`; **not** transition an opportunity's
  lifecycle state (autonomy L1, I2).
- **Not** run automatically. It runs on an **owner-selected** Cluster Strategy
  sidecar that Cluster Strategy itself recommended for this stage (autonomy L1;
  I12 volume discipline; D-PB-7).

---

# 2. INPUT CONTRACT

### 2.1 Primary input — the Cluster Strategy sidecar

Page Blueprint consumes the **machine sidecar**
`reports/cluster-strategy/<opportunity_id>.json` (the JSON encoding of the full
`ClusterStrategy`, `cluster_strategy.reporting` → `codec.encode`), **not** the
Markdown. It is the authoritative structured record; the `.md` is human
rendering.

`page_blueprint.input_loader.load_input` decodes it with the shared codec and
enforces **four hard gates** — every failure is a `PageBlueprintInputError`
(→ `PageBlueprintError`, the owner re-runs); Page Blueprint never runs on a
half-ready strategy:

| Gate | Rule | Why |
|---|---|---|
| **schema_version** | `schema_version` MUST be exactly `"1.0.0"` — on the sidecar and on the assembled `PageBlueprint` | D-PB-11 — decoding an unknown schema corrupts the input silently; hard-fail and surface it (Engineering Rule #9) |
| **cluster decision** | `cluster_decision.decision ∈ {MAP_TO_EXISTING, PROPOSE_NEW_CLUSTER}` — a `DEFER` / `REJECT` is refused | a deferred or rejected strategy has no cluster to design a page against |
| **strategy sections present** | `strategic_definition`, `asset_strategy`, and `content_direction` must **all** be non-null | a `MAP_TO_EXISTING` / `PROPOSE_NEW_CLUSTER` with a missing section is a malformed `ClusterStrategy` |
| **recommended for this stage** | `recommendation.target_next_stage` MUST equal `PAGE_BLUEPRINT` — a `FORMALIZE_CLUSTER` / `BACK_TO_MARKET_INTELLIGENCE` / `HOLD` is refused | the structural proof that Cluster Strategy itself recommended proceeding here — mirrors the `review.md` "advance" gate one stage up (autonomy L1, D-PB-7) |

### 2.2 What is carried into the `ClusterStrategySnapshot` (frozen, unchanged)

`input_loader._snapshot` copies the decision-relevant fields of the
`ClusterStrategy` into a `ClusterStrategySnapshot` (contract §4.1). Everything
here is **O**bserved (carried from stage 3, never re-decided):

| Field | From `ClusterStrategy` | Used for |
|---|---|---|
| `cluster_strategy_id`, `cluster_strategy_ref`, `opportunity_id`, `opportunity_run_id`, `schema_version` | identity / provenance link | the traceability chain |
| `cluster_id` (canonical id, or `null` for a proposed cluster), `cluster_name`, `subcluster_or_angle` | `cluster_decision` | the cluster the page belongs to; the §9.9 expression hint |
| `central_concept`, `positioning_statement`, `editorial_promise` | `strategic_definition` | the page identity synthesis must refine, never contradict, these |
| `market`, `language`, `consumption_context` | `strategic_definition` | fixed page market / language; localization context |
| `music_relationship`, `first_content_direction`, `editorial_angles` | `content_direction` | seeds for the page-level content framing (non-binding) |
| `overall_confidence` | `evaluation.overall_confidence` | **the ceiling on this stage's `overall_confidence`** (C6 rule, carried) |

The `asset_strategy` (`page_strategy` / `playlist_strategy` / `artist_strategy` +
any `new_page_recommendation`) is **not** flattened into the snapshot — it is
carried whole into the `PageAssetLink` (contract §3, §4.4), verbatim.

### 2.3 Existing business knowledge it may consume (read-only)

All loaded by the **existing `market_intelligence.knowledge_loader`** (no new
loader — same tree as Market Intelligence / Cluster Strategy):

| Source | Used for |
|---|---|
| `knowledge/business-dna/business-dna.md` **§9 (Musical DNA)** — the full section, read verbatim into the prompt | visual identity + tone of voice grounding (§5, D-PB-4); the `musical_dna_needs_input` detector; the §9.9 per-cluster expression hint |
| `knowledge/inventories/{artists,playlists,pages,catalog}.yaml` (+ consolidated classifications) | asset-honesty validation — every carried `*_id` must still resolve in the inventory (I1); a `reference_competitor` page can never be the designed page |
| `knowledge/rules/guardrails.yaml` — G01–G10 | the deterministic disease-claim scan over the page's prose + the claims-vs-topics self-check in the prompt (§6) |

It **must not** parse `CLAUDE.md` or `DECISIONS-NEEDED.md` prose for enforcement —
same rule as the pipeline (spec §3, §13) and Cluster Strategy.

---

# 3. WHAT PAGE BLUEPRINT DECIDES — AND WHAT IT CARRIES

The single sharpest rule of this stage, and the reason it is small: **it decides
the page, it does not decide the asset.**

| | Decided by Page Blueprint (Claude synthesis + deterministic assembly) | Carried verbatim from Cluster Strategy (never re-opened) |
|---|---|---|
| **Cluster** | — | `cluster_id` / `cluster_name` / `subcluster_or_angle`, `central_concept`, `positioning_statement`, `editorial_promise`, `market`, `language` |
| **Asset** | — | `page_strategy` (incl. `primary_page_id` — an own-page id, `UNKNOWN`, or `NEW_ASSET` — and any `new_page_recommendation` with its four I5 conditions), `primary_playlist_id`, `primary_artist_id` |
| **Page identity** | `concept_name`, a refined `positioning_statement` (may sharpen stage 3's, must not contradict it), `bio` | — |
| **Visual identity** | `visual_language`, `tone_of_voice`, and the `musical_dna_expression_used` phrase they were grounded in | — |
| **Content framing** | `content_pillars` (≤5 broad), `platforms`, `posting_cadence` (qualitative) | seeds: `first_content_direction`, `editorial_angles`, `music_relationship` |
| **Confidence** | `overall_confidence` (clamped ≤ stage 3's), `justification`, `blocked_by` | the ceiling: `cluster_strategy.overall_confidence` |
| **Recommendation** | `target_next_stage`, `recommended_next_step`, `justification` | — |

**D-PB-3 (the asset-inheritance rule).** `PageAssetLink` embeds the stage-3
`PageStrategy` object *by construction*. The blueprint prompt is given the asset
as a **`PAGE CONTEXT` block, "reference only, never re-decide"**, and the strict
response parser has no field in which Claude could return a different asset. The
deterministic assembler reads the ids straight off `ClusterStrategy.asset_strategy`.
Page Blueprint states *how to design* the page that anchors on that asset; it
never revisits *whether* the asset is right or *whether* a new page is warranted —
that judgement (I5) was made and carried by Cluster Strategy.

A fixed `asset_inheritance_note` travels on every `PageAssetLink`, byte-exact
(tamper-checked, §6):

> *"The page/playlist/artist decision is carried verbatim from Cluster Strategy
> (stage 3) — Page Blueprint designs the page, it does not re-decide whether a
> new asset is warranted (I5) or which asset anchors it."*

---

# 4. OUTPUT — the `PageBlueprint` object

One per Cluster-Strategy-recommended opportunity. **Markdown + YAML front matter +
JSON sidecar** (I4 pattern), `schema_version: "1.0.0"`, written to
`reports/page-blueprint/<opportunity_id>.md` / `.json` (D-PB-8).

**O/D/H/R attribution.** Every field below is classed **O**bserved (carried from
Cluster Strategy / inventory, unchanged) · **D**erived (Page Blueprint's reasoned
synthesis) · **H**ypothesis (non-binding) · **R**ecommendation (a proposed action,
never executed). As with Cluster Strategy, that attribution is expressed **in the
human-readable `.md` report**, which separates its sections into *Identity &
Provenance / Page Identity / Visual Identity / Asset Link (carried) / Content
Framing / Evaluation / Recommendation*. The `.json` sidecar is a structural
encoding of the `PageBlueprint` object and does not carry a per-field O/D/H/R tag.

### 4.1 Identity & Provenance

| Field | Purpose | Type | Req | Source | O/D/H/R |
|---|---|---|---|---|---|
| `page_blueprint_id` | stable id | string; `pb_<opportunity_id>` (idempotent — one per opportunity) | yes | derived | D |
| `schema_version` | forward-compat | `"1.0.0"` | yes | — | — |
| `cluster_strategy` | the frozen `ClusterStrategySnapshot` (§2.2) — `cluster_strategy_id`, `cluster_strategy_ref`, `opportunity_id`, `opportunity_run_id`, cluster fields, `central_concept`, `positioning_statement`, `editorial_promise`, `market`, `language`, `consumption_context`, `music_relationship`, `first_content_direction`, `editorial_angles`, `overall_confidence` | object | yes | Cluster Strategy | O |
| `provenance` | `run_id`, `schema_version`, `model`, `prompt_version`, `generated_at`, `replay`, `signal_ids` (carried union from the Opportunity Report via Cluster Strategy), `sources: list<Provenance>` (carried distinct records), `knowledge_snapshot { guardrails_count, musical_dna_needs_input, cluster_strategy_replay }` | object | yes | mixed | O + D |

`replay` is `true` when **either** this run is a recorded-replay run **or** the
input `ClusterStrategy` was itself produced under replay — a replay-tainted
blueprint is stamped *"not current-trend evidence"* in the report (spec §22).

### 4.2 Page Identity (Claude-authored synthesis)

| Field | Purpose | Type | Req | O/D/H/R |
|---|---|---|---|---|
| `concept_name` | the page's name / concept | string | yes | **R** (a recommendation the owner approves) |
| `positioning_statement` | one sentence — may **refine** Cluster Strategy's, must not contradict it | string | yes | D (refines an O base) |
| `bio` | a short profile-bio-length text (a page bio, not a caption) | string | yes | **R** |

### 4.3 Visual Identity — the Musical DNA §9 consumption point (see §5, D-PB-4)

| Field | Purpose | Type | Req | O/D/H/R |
|---|---|---|---|---|
| `visual_language` | palette / mood / imagery descriptors | string | yes | D (grounded in §9.9 + positioning) |
| `tone_of_voice` | copy register / voice | string | yes | D + guardrail-checked |
| `musical_dna_expression_used` | the exact §9.9 cluster-expression phrase the visual identity was grounded in — **must be non-empty** (validator-enforced); "never invent a visual identity untethered from §9" | string | yes | O (quoted from §9.9) |

### 4.4 Asset Link — carried verbatim, never re-decided (D-PB-3)

| Field | Type | Req | O/D/H/R |
|---|---|---|---|
| `page_strategy` | the stage-3 `PageStrategy` object, embedded whole: `primary_page_id` (own `page_id` \| `UNKNOWN` \| `NEW_ASSET`), `page_fit_basis`, `note`, `new_page_recommendation` (`{asset_type, rationale, i5_conditions_met}` \| `null`) | yes | O |
| `primary_playlist_id` | from `ClusterStrategy.asset_strategy.playlist_strategy.primary_playlist_id` | yes | O |
| `primary_artist_id` | from `ClusterStrategy.asset_strategy.artist_strategy.best_artist_id` | yes | O |
| `asset_inheritance_note` | fixed disclaimer (§3) — byte-exact, tamper-checked | yes | — |

### 4.5 Content Framing (deliberately shallow — see §5, D-PB-6)

| Field | Purpose | Type | Req | O/D/H/R |
|---|---|---|---|---|
| `content_pillars` | 3–5 **broad thematic pillars for this page only** — never specific content ideas, formats, or hooks. `> 5` is a soft `WARNING` ("reads as a content system"); `0` is a hard error | `[string]` | yes (≥1) | **H** |
| `platforms` | the platform(s) this page should run on | `[string]` | yes (≥1) | H/D |
| `posting_cadence` | a **qualitative** recommendation, e.g. *"3–4x per week"* — **never a schedule / calendar** | string | yes | **R** |
| `content_boundary_note` | fixed: *"Content pillars here are a broad thematic outline for this page only — not formats, hooks, structures, CTA copy, linguistic/visual production rules, or a content calendar. Those are Content Strategy's job (stage 5, C7/I11)."* — byte-exact, tamper-checked | yes | — |

### 4.6 Evaluation & Confidence (no 0–100, no multi-dimension rubric — D-PB-5)

| Field | Type | Req | O/D/H/R |
|---|---|---|---|
| `overall_confidence` | `LOW / MEDIUM / HIGH` — **MUST NOT exceed `ClusterStrategy.overall_confidence`** (a page design cannot be more confident than the strategy it rests on, C6), and — while Musical DNA §9 is `NEEDS_INPUT` — **capped at MEDIUM** | yes | D |
| `justification` | grounded in the carried strategy, the asset picture, and the §9 grounding | string | yes | D |
| `red_flags` | `[{ description, severity: LOW/MEDIUM/HIGH, kind: compliance\|feasibility\|evidence_gap\|asset_gap\|other }]` — carried compliance flags from Cluster Strategy **plus** any found in Page Blueprint's own prose (deduped on description) | yes (may be `[]`) | O (carried) + D |
| `blocked_by` | `[string]` — `NEEDS_INPUT` / `UNKNOWN` items that limited the design (e.g. *"no own page for this cluster/market — a new page is recommended, not yet created"*; *"musical DNA (NEEDS_INPUT)"* is appended automatically when the §9 cap fires) | yes (may be `[]`) | D |

**Why no per-dimension rubric.** Cluster Strategy has 4 qualitative dimensions
(D-CS-4) because it *evaluates* a cluster fit. Page Blueprint *synthesises* a
page from an already-evaluated strategy — it adds no new evidence and re-rates
nothing. A single `overall_confidence`, transparently clamped, is the honest
representation (D-PB-5). No persistent per-page `status` field either — a re-run
overwrites `reports/page-blueprint/<opportunity_id>.*` (idempotent).

### 4.7 Recommendation (I3 pattern)

| Field | Type | Req | O/D/H/R |
|---|---|---|---|
| `target_next_stage` | enum `CONTENT_STRATEGY` \| `BACK_TO_CLUSTER_STRATEGY` \| `HOLD` — **the next pipeline action, not a lifecycle state** (§7) | yes | **R** |
| `recommended_next_step` | concrete, actionable, still a recommendation | string | yes | **R** |
| `justification` | grounded in the blueprint, the carried strategy, the red flags | string | yes | D |
| `execution_note` | fixed: *"V1 does not execute this action; it requires human approval."* — byte-exact, tamper-checked | yes | — |

There is **no `opportunity_lifecycle_state` field** on a `PageBlueprint`. Cluster
Strategy carries the opportunity's `EXPLORE`/`TEST`/`PARK` status (I2); Page
Blueprint is one stage further from the registry and touches the lifecycle in no
way at all.

---

# 5. PAGE SYNTHESIS — VISUAL IDENTITY, TONE OF VOICE & CONTENT FRAMING

This is the section Business DNA V1 §11–§13 most over-reaches on; it is where the
stage-4 / stage-5 boundary is drawn.

### 5.1 Visual identity & tone of voice — grounded in Musical DNA §9.9 (D-PB-4)

Page Blueprint is *the* stage that most needs Musical DNA (`docs/MUSICAL-DNA-INPUT.md`):
visual identity and tone of voice are meant to *express, visually and verbally,
the same house sound the music has*.

- **What §9 is consumed.** Only: the **house-sound principle** and the
  **per-cluster sonic expression (§9.9)**. `page_blueprint.musical_dna` reads the
  **full §9 markdown verbatim into the prompt** (it never pre-parses business
  content into a hand-written table — mirrors `cluster_strategy.mapping.load_taxonomy_markdown`)
  and computes a best-effort §9.9 line for the snapshot's `cluster_name` as an
  attention *hint*; Claude still receives the whole section and can locate the
  right expression itself.
- **What §9 is NOT consumed.** Instrumentation, energy curves, BPM ranges,
  duration, texture, use of frequencies, vocal/instrumental rule, sonority-rejection
  criteria. Those are **Audio Engine's** (stage 8, deferred). The `VisualIdentity`
  model's docstring and the validator both enforce this by construction — no
  field exists to hold them, and the scope-leakage scanner (§B) flags their key
  names.
- **Output.** `visual_language`, `tone_of_voice`, and — mandatory —
  `musical_dna_expression_used`: the exact §9.9 phrase the identity was grounded
  in. An empty `musical_dna_expression_used` is a hard validation error: *"never
  invent a visual identity untethered from §9"*.
- **`NEEDS_INPUT` fallback.** If §9 is `NEEDS_INPUT` (the pre-2026-09-03 state,
  kept as a code path — D-PB-10): the prompt tells Claude to ground the identity
  in the cluster's positioning alone, set `musical_dna_expression_used` to a short
  "§9 unavailable" note, and hold `overall_confidence ≤ MEDIUM`; the deterministic
  assembler enforces the cap and appends `"musical DNA (NEEDS_INPUT)"` to
  `blocked_by`. In production §9 is owner-approved, so this path is inert but not
  removed.

### 5.2 Content framing — page-level pillars only, not a content system (D-PB-6)

| Page Blueprint **produces** | Page Blueprint **must NOT produce** — all → Content Strategy (stage 5) |
|---|---|
| `content_pillars` — 3–5 **broad thematic** pillars *for this page* (e.g. *"the cleansing ritual when you move into a new home"*, *"music to 'renew' the home and start over"*) | content **formats**, **hook libraries**, **structures**, **CTA copy**, **captions**, **linguistic rules**, **visual production rules**, **templates**, **variations / A-B design**, **batch sizes**, the `CONTENT_OBJECT` schema |
| `platforms` — which platform(s) the page runs on | a **posting calendar / schedule** (dates, slots) |
| `posting_cadence` — a *qualitative* recommendation (*"3–4x per week"*) | a per-post plan; anything a scheduler could execute |

The seeds are the carried `first_content_direction`, `editorial_angles`, and
`music_relationship` from Cluster Strategy — non-binding, for Content Strategy to
test. The deterministic validator raises a **soft `WARNING`** at `> 5` pillars
(*"reads as a content system, which is Content Strategy's job — contract §5"*) and
a **hard error** at `0`.

---

# 6. COMPLIANCE / GUARDRAILS & DETERMINISTIC VALIDATION

### 6.1 Guardrails (contract §6, `page_blueprint.guardrails`)

- **Same mechanism as Market Intelligence and Cluster Strategy.** Page Blueprint
  loads `knowledge/rules/guardrails.yaml` (G01–G10) via the existing
  `knowledge_loader` (never `CLAUDE.md`), and reuses
  `market_intelligence.guardrails` (`check_texts` + the deterministic
  disease-claim scanner for G01/G03/G04) with **Page-Blueprint field → `applies_to`
  scope** mapping:
  - `concept_name`, `positioning_statement`, `bio`, `visual_language`,
    `tone_of_voice`, `posting_cadence`, `recommendation.justification` →
    **`report_prose`** scope (broadest — G01, G03, G04, G05, G06, G09, G10).
  - `content_pillars` → **`hypotheses_direction`** scope (a non-binding starting
    direction — same family as Cluster Strategy's `editorial_angles`: G01, G03,
    G06, G07).
- **Claims-vs-topics calibration (inherited).** Naming a ritual, a cluster, a
  theme, or the audience's belief is fine; asserting a cure / treatment /
  diagnosis / guaranteed outcome / proven mechanism is not. The prompt states
  this explicitly ("flag CLAIMS, not TOPICS — same standard as Evaluation/Cluster
  Strategy"), and `positioning_statement` / `bio` / `tone_of_voice` are written as
  **experience / ritual / intention / atmosphere** (G02, permitted), never as an
  effect the music produces.
- **Carry-forward.** Every carried `red_flag` from Cluster Strategy is copied into
  `PageBlueprintEvaluation.red_flags` and re-tested against Page Blueprint's own
  prose; deduped on `description` (an exact restatement collapses, a distinct flag
  is never dropped).

### 6.2 Compliance escalation — the full `ComplianceResult` (mirrors Cluster Strategy §9, spec §14)

The deterministic scanner's result is applied exactly as the MI Evaluation and
Cluster Strategy stages apply it — **a HIGH compliance hit is a business outcome,
not a crash**:

| Scanner result | Trigger | Effect |
|---|---|---|
| **`exclude_opportunity`** | a HIGH-severity hit in **core** page content (`report_prose` scope: `concept_name`, `positioning_statement`, `bio`, `visual_language`, `tone_of_voice`, `posting_cadence`, `recommendation.justification`) | `recommendation.target_next_stage` is forced to **`HOLD`**; `recommended_next_step` and `justification` are replaced with a fixed forced-HOLD reason; the run **still writes a report**. The offending identity/bio text is **left intact** (a forced HOLD, not a silent rewrite) so the owner sees exactly what tripped it. |
| **`strip_scopes`** (the `hypotheses_direction` scope) | a HIGH-severity hit confined to `content_pillars` | `content_pillars` is replaced with a single fixed *"[removed — a HIGH-severity compliance guardrail flagged the drafted content pillars; Content Strategy (stage 5) must supply compliant ones]"* note; the run **proceeds** and the page design stands; the compliance red flag is still surfaced. |
| **`needs_uncertainty_note`** | (no scanner currently emits this, matching MI) | would become a `blocked_by` entry |

A carried MEDIUM/LOW compliance flag is kept; the prose is written to clear it;
`blocked_by` / `open`-style notes record the constraint for Content Strategy.

### 6.3 Deterministic validation (`page_blueprint.schema.validate.validate_page_blueprint`)

Semantic rules only — structural checks (field presence / type / enum,
unknown-key rejection) are the shared codec's job. Reuses the pipeline's
`ValidationError` / `ERROR` / `WARNING` / `InventoryIndex` and its C6 score
scanner. `ERROR` blocks the run (`PageBlueprintError`); `WARNING` is surfaced but
non-blocking.

| Check | Severity | Rule |
|---|---|---|
| `schema_version` pin | ERROR | `PageBlueprint` and the source `ClusterStrategySnapshot` must both be `"1.0.0"` |
| no 0–100 score anywhere | ERROR | `scan_json_for_numeric_score` over the whole encoding — any `N/100`, `N out of 100`, `score: N` (C6) |
| scope-leakage (§B) | ERROR | any Content-Strategy structural key name (`formats`, `hook_library`, `hooks`, `structures`, `cta_copy`, `captions`, `batch_size`, `templates`, `variations`, `content_object`, `linguistic_rules`, `visual_rules`, `schedule`, `publishing_calendar`) anywhere in the encoding — a regression guard; the models carry none |
| fixed-disclaimer tampering | ERROR | `content_boundary_note`, `asset_inheritance_note`, and the execution note must be byte-exact |
| content pillars | ERROR at 0 / WARNING at >5 | at least one; more than five reads as a content system |
| `overall_confidence` ≤ Cluster Strategy's | ERROR | a page design cannot be more confident than the strategy it rests on (C6) |
| Musical DNA §9 cap | ERROR | `overall_confidence` is `HIGH` while §9 is `NEEDS_INPUT` — not allowed (D-PB-4); the assembler normally prevents this by clamping to `MEDIUM` first |
| `musical_dna_expression_used` present | ERROR | must cite the §9.9 phrase used — never an untethered visual identity |
| asset honesty (I1) | ERROR | `primary_page_id` (unless `UNKNOWN` / `NEW_ASSET`) ∈ own-page ids; a `reference_competitor` page can **never** be the designed page (spec §10.3); `primary_playlist_id` ∈ playlist ids (or `UNKNOWN` / `NEW_ASSET`); `primary_artist_id` ∈ artist ids (or `UNKNOWN`) |

---

# 7. DECISION STATES

**No `LAUNCH` / `SCALE` / `KILL` is introduced.** No source requires them for
stage 4, and D1 forbids operationalising them in V1.

**The opportunity lifecycle is not touched — and is not even carried here.**
`EXPLORE` / `TEST` / `PARK` (I2) belong to the opportunity registry; Cluster
Strategy carries them one stage up. A `PageBlueprint` has no lifecycle field at
all (§4.7).

Page Blueprint needs exactly **one** small, non-lifecycle vocabulary — an
*output of one run of the stage*, not a persistent state machine:

| Vocabulary | Values | Meaning |
|---|---|---|
| `target_next_stage` (recommendation) | `CONTENT_STRATEGY` · `BACK_TO_CLUSTER_STRATEGY` · `HOLD` | the recommended next pipeline action — still a recommendation, human-approved (I3, autonomy L1). **`CONTENT_STRATEGY` stays DEFERRED under P4 regardless of this value; the recommendation never triggers execution.** |

`BACK_TO_CLUSTER_STRATEGY` is the "the carried strategy is not actually
page-ready — send it back" path (e.g. the positioning cannot be expressed for a
page without a compliance claim, but the concept is salvageable). `HOLD` is the
forced-compliance outcome (§6.2) or a Claude-judged "do not proceed".

`LAUNCH/SCALE/KILL` is **structurally impossible**, not value-scanned: the
`PageBlueprintTargetNextStage` enum has no such values, and there is no lifecycle
field to carry them.

---

# 8. IMPLEMENTATION

### Packaging

A **new sibling package `src/page_blueprint/`** (stage 4 is a distinct pipeline
stage; C8's "conceptually separate for modularity"). It **imports, does not
modify** the existing packages (no refactor of stage-1–3 code):

- `market_intelligence.schema.{enums, models, codec, validate}` — shared vocab
  (`Rating`, `Confidence`, `Severity`, `RedFlagKind`, `RedFlag`, `Market`,
  `Language`, `Provenance`, `Guardrail`, `RunPaths`), the shared codec, the C6
  score scanner, `ValidationError` / `InventoryIndex`.
- `market_intelligence.knowledge_loader` — `load_knowledge` / `KnowledgeBundle`.
- `market_intelligence.llm_stage` — the injectable `StageClient` /
  `RecordedStageClient` + `call_stage` + `stage_key` +
  `<fixture_path>/llm/<stage>/<key>.json` replay convention (spec §22).
- `market_intelligence.guardrails` — `check_texts`, `ComplianceResult`, the
  scope constants, the disease-claim scanner.
- `market_intelligence.io_utils` — `read_json` / `read_yaml` / `write_text` /
  `write_json` / `LoadError`.
- `market_intelligence.orchestrator._musical_dna_needs_input` — re-exported as
  the single source of truth for the §9 detector.
- `cluster_strategy.schema.{enums, models}` — `ClusterStrategy`, `PageStrategy`,
  `PlaylistStrategy`, `ArtistStrategy`, `ClusterDecisionKind`, `TargetNextStage`
  (the stage-3 output types, carried verbatim — D-PB-3).

*(Future cleanup — not now: extract the modules stages 3 and 4 both share into a
`src/engine_core/` package. Flagged, not done — same flag Cluster Strategy
raised.)*

### Modules

| File | Purpose |
|---|---|
| `src/page_blueprint/__init__.py`, `__main__.py` | package + `python -m page_blueprint` |
| `src/page_blueprint/cli.py` | `python -m page_blueprint <cluster-strategy-sidecar.json>`; `--config`, `--project-root`; prints a summary + `PAGE BLUEPRINT OK` / `PAGE BLUEPRINT FAILED` |
| `src/page_blueprint/config.py` | `PageBlueprintConfig` + `PBReplayConfig` + `load_config` (spec §14 style; reuses `RunPaths`) |
| `src/page_blueprint/schema/models.py` | dataclasses: `PageBlueprint`, `ClusterStrategySnapshot`, `PageIdentity`, `VisualIdentity`, `PageAssetLink`, `PageContentFraming`, `PageBlueprintEvaluation`, `PageBlueprintRecommendation`, `PageBlueprintProvenance` + the three fixed-note constants |
| `src/page_blueprint/schema/enums.py` | `PageBlueprintTargetNextStage`, `SCHEMA_VERSION`, `EXECUTION_NOTE` |
| `src/page_blueprint/schema/validate.py` | `validate_page_blueprint(...)` + `scan_for_scope_leakage(...)` — see §6.3 |
| `src/page_blueprint/input_loader.py` | load `<opportunity_id>.json` → `LoadedInput` (`ClusterStrategy` + `ClusterStrategySnapshot`); the four §2.1 hard gates |
| `src/page_blueprint/musical_dna.py` | deterministic, text-based §9 access: `musical_dna_needs_input` (re-exported detector), `extract_section_9` (verbatim, fail-safe), `extract_cluster_expression_hint` (best-effort §9.9 line) |
| `src/page_blueprint/blueprint.py` | the one Claude sub-step (via `llm_stage`): `build_prompt` + `reject_malformed_blueprint` (strict shape gate — a deviation is a `ResponseRejected`, never a silent repair) + `run_blueprint` |
| `src/page_blueprint/guardrails.py` | `check_page_blueprint_prose(...)` — field → scope map over `market_intelligence.guardrails` |
| `src/page_blueprint/llm.py` | re-exports the MI stage plumbing; lenient `_extract_json_object`; `AnthropicPageBlueprintClient` (non-structured, prompt-guided JSON, bounded timeout, `max_retries=1`, `sk-ant-…` redaction); `select_client` |
| `src/page_blueprint/reporting.py` | render `reports/page-blueprint/<opportunity_id>.md` (front matter + 7 sections, carried facts / synthesis / recommendation separated) + `.json` sidecar (`codec.encode`) |
| `src/page_blueprint/orchestrator.py` | deterministic driver: `input_loader` → §9 extraction → Claude blueprint call → confidence clamp (ceiling + §9 cap) → guardrail check (`exclude` / `strip`) → assemble → validate → render; `PageBlueprintError` on hard fail |
| `config/page-blueprint.example.yaml` | `model`, `prompt_version`, paths, `replay` block |

### Claude-vs-deterministic split (spec §19)

*Claude decides what the page is and how confident to be; deterministic code
decides whether the output is well-formed, traceable, in-scope, asset-honest, and
compliant — and it owns the asset link itself, which Claude never sees as a
choice.* One new pipeline stage, one Claude sub-step (`blueprint.py`), no
multi-agent orchestration (I8, P5).

### Tests (TDD, `pytest` — spec §22) — 68 tests

- `test_page_blueprint_input_loader.py` (8) — a real `PAGE_BLUEPRINT`-recommended
  sidecar loads; `schema_version` mismatch → hard fail; wrong `target_next_stage`
  → refused; `DEFER` / `REJECT` → refused; missing strategy section → refused;
  missing sidecar / non-object → hard fail.
- `test_page_blueprint_validate.py` (14) — any `N/100` in any prose → error; a
  Content-Strategy field name (scope leakage) → error; `overall_confidence` above
  the Cluster Strategy's ceiling → error; `overall_confidence` HIGH while §9 is
  `NEEDS_INPUT` → error; tampered fixed note → error; empty
  `musical_dna_expression_used` → error; invented / `reference_competitor` asset
  id → error; `> 5` pillars → warning; `0` pillars → error.
- `test_page_blueprint_blueprint.py` (16) — `reject_malformed_blueprint` rejects
  every missing/blank field and every bad enum; `build_prompt` carries the hard
  rules, the §9 branch, the guardrail list, and the "reference only" asset block.
- `test_page_blueprint_musical_dna.py` (6) — `extract_section_9` pulls §9
  verbatim, returns a `NEEDS_INPUT` note when absent; `extract_cluster_expression_hint`
  best-effort matches a cluster name, `None` on no match.
- `test_page_blueprint_guardrails.py` (6) — "cures your disorder" as a claim →
  `compliance` red flag; naming a ritual / emotional state alone → no flag
  (claims-not-topics preserved); field → scope mapping.
- `test_page_blueprint_orchestrator.py` (11) — recorded-replay end-to-end on the
  real live-produced sidecar for `opp_2026-08-31_1bca4af972` (frozen as a test
  fixture): page identity synthesised, visual identity grounded in §9.9, asset
  link carried verbatim, confidence clamped to the Cluster Strategy's `LOW`
  ceiling, no 0–100 score, all 7 sections + a round-tripping sidecar, replay
  stamped, nothing written under `knowledge/`, a missing LLM fixture → hard fail.
- `test_page_blueprint_decision_branches.py` (2) — a HIGH compliance claim in
  core content → forced `HOLD` (identity text left intact); a HIGH compliance
  claim confined to `content_pillars` → stripped, run proceeds, page design
  stands.
- `test_page_blueprint_cli.py` (5) — runs the stage and prints a summary;
  reports a bad config; nonzero on a run failure (an Opportunity Report passed
  where a `ClusterStrategy` sidecar is required); config defaults.

### Fixtures

- **Input:** `tests/fixtures/page_blueprint/input/opp_2026-08-31_1bca4af972.json`
  — a byte copy of the real, live-produced Cluster Strategy sidecar for that
  opportunity (`MAP_TO_EXISTING → limpeza-energetica`, `target_next_stage
  PAGE_BLUEPRINT`), frozen so the stage-4 suite is hermetic. No secrets, no
  machine paths (`replay: false`, real run).
- **Recorded LLM responses:** `tests/fixtures/page_blueprint{,_reject,_strip}/llm/page_blueprint/page_blueprint__<opportunity_id>.json`
  — the normal branch, the forced-HOLD branch, the strip branch.

### Integration points

- **In:** `reports/cluster-strategy/<opportunity_id>.json` (Cluster Strategy
  sidecar — `docs/CLUSTER-STRATEGY-V1.md` §14 contract) + the knowledge base
  (existing loader).
- **Out:** `reports/page-blueprint/<opportunity_id>.md` + `.json` (D-PB-8). No
  per-run digest in V1-of-stage-4 (one opportunity at a time).
- **Knowledge writes:** **none.** Unlike Cluster Strategy's opt-in
  `opportunity-registry.yaml` append (D-CS-7), Page Blueprint has no
  `knowledge/` write path at all (D-PB-9). A normal or offline run — and a live
  run — leave `knowledge/` untouched.
- **Downstream:** the `PageBlueprint` sidecar is Content Strategy's future input
  contract (stage 5, deferred).
- **Decision record:** opening the stage is decision **D-PB-1**, recorded in
  `knowledge/DECISIONS-NEEDED.md` §6 (with P4 updated).

---

# 9. CONFIDENCE / EVIDENCE

**No new composite 0–100 score. No weights, no formula, no aggregation (C6, spec
§8.3).** The deterministic validator reuses
`market_intelligence.schema.validate.scan_json_for_numeric_score` over the whole
`PageBlueprint` encoding and fails on any `N/100`, `N out of 100`, or `score: N`
pattern.

**Representation:**

- **One** qualitative `overall_confidence ∈ {LOW, MEDIUM, HIGH}` — explicitly
  assigned by Claude, then **clamped by deterministic code** to
  `min(model_confidence, ClusterStrategy.overall_confidence)` and, while Musical
  DNA §9 is `NEEDS_INPUT`, further capped at `MEDIUM`. The synthesis never raises
  confidence.
- No per-dimension rubric (D-PB-5, §4.6) — Page Blueprint re-rates nothing.
- **Evidence typing carried through.** Every OBSERVED claim in the carried
  `ClusterStrategySnapshot` still traces back through
  `signal_ids → Signal.provenance → raw capture` (spec §16.3), inherited two
  stages up from the Opportunity Report. Page Blueprint adds **no** new
  observation — its outputs are `D` (synthesis), `H` (content seeds), or `R`
  (recommendations). The `.md` report keeps the carried facts visually separate
  from the synthesis and the recommendation, preserving the C10.3 requirement
  (observed facts distinguished from hypotheses) in the human-reviewed report.
- `UNKNOWN` (fact absent) and `NEEDS_INPUT` (pending owner decision) are **never**
  replaced with a guess (G10, spec §15). `blocked_by` names each one; the report
  renders it.

---

# 10. ARCHITECTURAL BOUNDARY

| Stage | Question it answers | **Produces** | **Must NOT produce** |
|---|---|---|---|
| **Market Intelligence + Opportunity Analysis** (stages 1–2 — *built*) | *"Which opportunities exist, and which deserve our attention?"* (C7) | Discovery of opportunities; typed evidence + provenance; the 10-dimension qualitative evaluation + the 5-axis Business Outcome Profile; ranking / Top-10; `AssetMatch` (fit with **existing** assets); an operational `Recommendation`. **Light, non-binding hypotheses** about cluster, positioning, page, first content direction. | A confirmed cluster; a strategic cluster definition; a page; any content. |
| **Cluster Strategy** (stage 3 — *built, merged*) | *"Does this owner-approved opportunity map to an existing canonical cluster, a subcluster/angle, or a proposed new cluster — and what is the cluster's strategic definition and asset strategy?"* | The **cluster decision** + justification vs the taxonomy boundary; the **strategic cluster definition** (concept, audience, intent, emotional register, editorial promise, positioning statement, localization notes, durability read, strategic coherence); the **cluster-level asset strategy** (playlist reuse / page recommendation carried / hero + candidate artist anchors / market-language fit / gaps — **no asset invented**); **one** non-binding first content direction + candidate angles + music role; qualitative confidence + carried compliance flags + open questions; a **recommended next stage**. A **new-cluster *proposal*** (P6 still deferred). | **Any page design** (name, bio, visual identity, tone of voice, cadence — Page Blueprint). **Any content system** (pillars, formats, hooks, structures, CTA copy, linguistic/visual rules, frequency, variations, templates — Content Strategy). Any 0–100 score. Any lifecycle transition. Any write to `cluster-taxonomy.md` or the inventories. Any new canonical cluster. |
| **PAGE BLUEPRINT** (stage 4 — *this contract*) | *"Given the cluster (or the new-page recommendation) and its positioning, what is the concrete page?"* | Page concept name, bio, language, market, **visual identity**, **tone of voice** (grounded in Musical DNA §9.9), the associated playlist + artist **carried verbatim**, platform(s), a *qualitative* posting cadence, **content pillars for that page** (broad, ≤5). Qualitative `overall_confidence` (clamped to the Cluster Strategy's) + carried compliance flags + `blocked_by`. A **recommended next stage**. (Business DNA V1 §12.) | The content *system* detail (formats, hooks, structures, CTA copy, linguistic/visual production rules, a posting calendar, batch sizes, templates, variations, the content-object schema — Content Strategy). Any re-decision of the cluster, the positioning, or the asset. Any consumption of §9 beyond the house sound / §9.9. Any 0–100 score. Any lifecycle transition. Any write under `knowledge/`. |
| **Content Strategy** (stage 5 — *deferred, P4*) | *"Given the page, what is the reusable content system?"* | Pillars (detailed), formats, **hooks**, structures, styles, **CTAs**, linguistic rules, visual rules, frequency, variation design, the `CONTENT_OBJECT` schema. (Business DNA V1 §13–§15.) | Content production, video, audio, publishing. |

**The precise seam Page Blueprint sits on:** it takes the confirmed cluster + the
positioning statement + the carried asset link, and produces the **page** — what
it is called, what it says about itself, what it looks and sounds like (visually
and in voice), where it runs and how often, and the handful of broad themes it is
about. It **stops before** the content system: how a post is built, what hook it
opens with, what the CTA says, when it goes out.

---

# 11. OPEN DECISIONS — DECIDED 2026-09-04 (`DECISIONS-NEEDED.md` §6 is authoritative)

**On 2026-09-04 the owner opened canonical stage 4 and decided every decision
below at its recommended answer** (authorization: *"Fica explicitamente
autorizado o início do Stage 4 — Page Blueprint … equivalente ao padrão
D-CS-1"*). They are recorded in `knowledge/DECISIONS-NEEDED.md`, section
**"# 6. ESTÁGIO 4 — PAGE BLUEPRINT"** (D-PB-1 … D-PB-12), with P4 updated to
*"estágios 3–4 abertos; estágios 5–13 seguem DEFERRED"*. The table below mirrors
those decisions for the reader; the decision log is the authoritative record.

| # | Decision | Why it could not be inferred | Decision (D-PB, 2026-09-04) | Mirrors |
|---|---|---|---|---|
| **D-PB-1** | Authorize opening canonical stage 4 (Page Blueprint). | P4 keeps stages 4–13 `DEFERRED`; D-CS-1 explicitly named Page Blueprint among them. Opening a stage is an explicit owner action. | **Stage 4 opened**, scoped to Page Blueprint only (stages 5–13 stay deferred under P4). Recorded as D-PB-1 + the P4 update. Autonomy stays Level 1. | D-CS-1 |
| **D-PB-2** | Confirm the stage-4 boundary against Business DNA V1 §11–§13. | §11 puts *linguagem, estética, conteúdo, CTA* in "Cluster Strategy"; §12 gives Page Blueprint "pilares de conteúdo dessa página"; C8 / D-CS-8 split visual identity (4) from the content system (5). A direct document divergence. | **Confirm the established boundary.** Page Blueprint = page identity + visual identity + tone of voice + a shallow page-level content framing. The content *system* (formats, hooks, structures, CTA copy, calendar) is stage 5. The vision doc supplies intent, not the contract. | D-CS-8 |
| **D-PB-3** | Does Page Blueprint re-decide the asset (page/playlist/artist), or carry it? | Business DNA V1 §12 says Page Blueprint "escolhe playlist e artista"; I5 + D-CS-8 already have Cluster Strategy carry the `AssetMatch` decision. Re-deciding duplicates the judgement. | **Carry verbatim.** `PageAssetLink` embeds the stage-3 `PageStrategy`; the ids come straight off `ClusterStrategy.asset_strategy`. Claude sees the asset as context ("reference only, never re-decide"), never as a choice. Page Blueprint never re-judges whether a new page is warranted (I5). | — |
| **D-PB-4** | How much of Musical DNA §9 does Page Blueprint consume? | §9 (now owner-approved) has both a house-sound principle / per-cluster expression **and** instrumentation / BPM / frequency / sonority detail. Page Blueprint needs the former; the latter is Audio Engine's (stage 8). | **Only the house-sound principle + the per-cluster §9.9 expression.** Visual identity and tone of voice ground there and nowhere else; `musical_dna_expression_used` must cite the §9.9 phrase. Instrumentation/BPM/frequency/sonority are not read. The `NEEDS_INPUT` fallback (confidence ≤ MEDIUM + `blocked_by`) is kept as a code path. | — |
| **D-PB-5** | The stage-4 evaluation / confidence model. | C9 fixes the *opportunity* dimensions; D-CS-4 fixes 4 *cluster-strategy* dimensions. There is no decided model for a page blueprint. | **One qualitative `overall_confidence`**, no per-dimension rubric, **clamped to `ClusterStrategy.overall_confidence`** and never raised by the synthesis; capped at MEDIUM while §9 is `NEEDS_INPUT`. No 0–100 score (C6). No persistent per-page `status` — a re-run overwrites the report (idempotent). | D-CS-4 |
| **D-PB-6** | Content-framing depth. | Business DNA V1 §12 lists "pilares de conteúdo dessa página"; the content system is §13 / stage 5. Without a line, stage 4 invades stage 5. | **Shallow.** `content_pillars` = 3–5 **broad thematic** pillars for this page only; `platforms`; a **qualitative** `posting_cadence`. No formats, hooks, structures, CTA copy, linguistic/visual production rules, calendar, batch sizes, templates. `> 5` pillars → soft WARNING; `0` → error. | D-CS-5 |
| **D-PB-7** | Trigger — which strategies enter Page Blueprint, and how is the stage invoked? | Neither the spec nor Business DNA V1 defines the hand-off; autonomy L1 + I12 imply human selection. | **Explicit, per-opportunity, owner-invoked CLI** (`python -m page_blueprint reports/cluster-strategy/<opportunity_id>.json`); the stage refuses to run unless `recommendation.target_next_stage == PAGE_BLUEPRINT` on the input `ClusterStrategy`. No batch / automatic run. | D-CS-3 |
| **D-PB-8** | Output location and whether a per-run digest exists. | I7 (`reports/` = durable) applies; the exact path and whether stage 4 emits a digest are undecided. | `reports/page-blueprint/<opportunity_id>.md` + `.json`. **No digest** in V1-of-stage-4 (one opportunity at a time); the report is the deliverable. | D-CS-6 |
| **D-PB-9** | Does Page Blueprint touch `knowledge/`? | Cluster Strategy got an opt-in `opportunity-registry.yaml` append (D-CS-7). The question is whether stage 4 needs an equivalent. | **No.** Page Blueprint has **no** `knowledge/` write path — not even opt-in. It reads `knowledge/`, it writes only `reports/page-blueprint/`. The registry link stays a stage-3 concern. | D-CS-7 (contrast) |
| **D-PB-10** | Is a `NEEDS_INPUT` Musical DNA an acceptable state for Page Blueprint to run in? | §9 is now owner-approved, but the code path and the possibility of a future `NEEDS_INPUT` window remain. | **Acceptable** — run with `overall_confidence ≤ MEDIUM`, `musical_dna_expression_used` set to a "§9 unavailable" note, and a `blocked_by` entry; same cap the pipeline applies to `music_fit`. Page Blueprint names *what* would need §9 detail, never invents it (G10). In production the path is inert. | D-CS-9 |
| **D-PB-11** | Contract-version handling. | The `ClusterStrategy` `schema_version` is `1.0.0`; behaviour on a future mismatch is undecided. | **Pin to `schema_version == 1.0.0` and hard-fail** on any other value — on the input sidecar and on the assembled `PageBlueprint` — surfacing the divergence (Engineering Rule #9) rather than guessing. | D-CS-11 |
| **D-PB-12** | Naming reconciliation. | Business DNA V1 §5 uses different stage names; C8 is canonical. Minor, non-blocking. | **Use the C8 canonical names** (`Page Blueprint`, stage 4). No document edits; the divergence is noted (same treatment as P10 / D-CS-12). | D-CS-12 |

---

# A. Page Blueprint V1 — Contract summary

- **Identity in the pipeline:** canonical stage 4 (C8). Consumes **one
  Cluster-Strategy-recommended `ClusterStrategy`** (the `<opportunity_id>.json`
  sidecar, `schema_version 1.0.0`, `target_next_stage == PAGE_BLUEPRINT`).
  Produces **one `PageBlueprint`** (Markdown + YAML front matter + JSON sidecar,
  `schema_version 1.0.0`) at `reports/page-blueprint/<opportunity_id>.*`. Autonomy
  **Level 1** — recommend only; the `execution_note` is fixed.
- **Carries verbatim (never re-decides):** the cluster, the positioning, the
  audience, the market/language, and the asset (page/playlist/artist +
  new-page-recommendation) — all frozen from Cluster Strategy (D-PB-3).
- **Synthesises (Claude):** page `concept_name`, a refined `positioning_statement`,
  a `bio`; `visual_language` + `tone_of_voice` grounded in the Musical DNA §9.9
  cluster expression (D-PB-4) with the exact phrase recorded; `content_pillars`
  (≤5 broad), `platforms`, a qualitative `posting_cadence` (D-PB-6);
  `overall_confidence` + `justification` + `blocked_by`; a `target_next_stage`
  recommendation.
- **Confidence:** one qualitative `overall_confidence`, **no per-dimension
  rubric**, **no 0–100 score**, clamped to `ClusterStrategy.overall_confidence`
  and capped at MEDIUM while §9 is `NEEDS_INPUT` (D-PB-5).
- **States:** no `LAUNCH/SCALE/KILL`; no lifecycle field at all; one non-lifecycle
  vocabulary — `target_next_stage ∈ {CONTENT_STRATEGY, BACK_TO_CLUSTER_STRATEGY,
  HOLD}`. Content Strategy stays DEFERRED under P4 regardless (D-PB-2).
- **Guardrails:** loads `guardrails.yaml` (G01–G10); reuses
  `guardrails.check_texts`; applies the **full** `ComplianceResult` — a HIGH hit
  in core page content → forced `HOLD` (identity text left intact); a HIGH hit
  confined to `content_pillars` → those pillars stripped, the page design stands;
  inherits the **claims-not-topics** calibration; `UNKNOWN`/`NEEDS_INPUT` never
  guessed (§6.2).
- **Knowledge writes:** **none** — no registry, no taxonomy, no opt-in append
  (D-PB-9). Reads `knowledge/`, writes only `reports/page-blueprint/`.
- **Provenance:** full traceability chain carried from the Opportunity Report via
  Cluster Strategy (`signal_ids → Signal.provenance → raw capture`); `model`,
  `prompt_version`, `generated_at`, `replay` recorded; a replay-tainted blueprint
  (this run **or** the input strategy) flagged "not current-trend evidence".

# B. Architecture Boundary — deterministic enforcement

`page_blueprint.schema.validate` combines several checks over the encoded
`PageBlueprint`:

- **`scan_for_scope_leakage`** — a **key-name** denylist: it walks the encoded
  object and flags any dict key that belongs to Content Strategy (`formats`,
  `hook_library`, `hooks`, `structures`, `cta_copy`, `captions`, `batch_size`,
  `templates`, `template`, `variations`, `content_object`, `linguistic_rules`,
  `visual_rules`, `schedule`, `publishing_calendar`). This is a **regression
  guard** — the dataclass models carry none of these, so the shared codec already
  rejects a rogue field on decode.
- **`scan_json_for_numeric_score`** (reused from Market Intelligence) — fails on
  any `N/100`, `N out of 100`, or `score: N` pattern anywhere in the encoding
  (C6).
- **asset honesty (I1)** — `primary_page_id` (`UNKNOWN` / `NEW_ASSET` aside) must
  be an own-page id; a `reference_competitor` page can **never** be the designed
  page (spec §10.3); `primary_playlist_id` / `primary_artist_id` must resolve in
  the inventory.
- **confidence ceilings** — `overall_confidence` must be ≤
  `ClusterStrategy.overall_confidence`, and must not be `HIGH` while §9 is
  `NEEDS_INPUT`.
- **Musical DNA grounding** — `musical_dna_expression_used` must be non-empty.
- **fixed-disclaimer tamper checks** — the content-boundary note, the
  asset-inheritance note, and the execution note must be byte-exact.

There is **no explicit `LAUNCH/SCALE/KILL` value scan** — those values are
structurally impossible: the `PageBlueprintTargetNextStage` enum has no lifecycle
values, and a `PageBlueprint` carries no lifecycle field.

# C. Owner Decisions (DECIDED 2026-09-04)

D-PB-1 open stage 4 (P4 updated) · D-PB-2 confirm the boundary vs Business DNA V1
§11–§13 · D-PB-3 asset carried verbatim from Cluster Strategy, never re-decided ·
D-PB-4 Musical DNA §9 consumption limited to the house sound / §9.9 expression ·
D-PB-5 one qualitative `overall_confidence`, no rubric, clamped, no score ·
D-PB-6 shallow content framing (broad page-level pillars only) · D-PB-7
owner-invoked, per-opportunity, `target_next_stage`-gated trigger · D-PB-8 output
path, no digest · D-PB-9 no `knowledge/` write path (contrast D-CS-7) · D-PB-10
run with musical-DNA `NEEDS_INPUT` + confidence cap (fallback path) · D-PB-11
hard-fail on `schema_version` mismatch · D-PB-12 use C8 canonical names.

**All twelve are DECIDED (2026-09-04) and recorded in
`knowledge/DECISIONS-NEEDED.md` §6** ("# 6. ESTÁGIO 4 — PAGE BLUEPRINT"), with P4
updated. That decision log is the authoritative record; §11 mirrors it.

# D. Implementation Plan (executed 2026-09-04)

1. Owner opened stage 4 and decided **D-PB-1 … D-PB-12** at the recommended
   answers; recorded in `DECISIONS-NEEDED.md` §6 with P4 updated.
2. New package **`src/page_blueprint/`** (sibling of `market_intelligence` and
   `cluster_strategy`), importing — not modifying —
   `market_intelligence.{schema, knowledge_loader, llm_stage, guardrails,
   io_utils, orchestrator._musical_dna_needs_input}` and
   `cluster_strategy.schema.{enums, models}`.
3. Modules: `schema/{models,enums,validate}.py` · `input_loader.py` ·
   `musical_dna.py` (deterministic §9 access) · `blueprint.py` (one Claude
   sub-step via `llm_stage`) · `guardrails.py` · `llm.py` · `reporting.py` ·
   `orchestrator.py` · `cli.py` · `config.py` · `config/page-blueprint.example.yaml`.
4. TDD, `pytest`, recorded-replay for the Claude sub-step
   (`<fixture_path>/llm/page_blueprint/<key>.json`), input fixture =
   the frozen live Cluster Strategy sidecar
   `tests/fixtures/page_blueprint/input/opp_2026-08-31_1bca4af972.json`; a
   `no-knowledge-write` guarantee and a `scope-leakage` guarantee as hard tests.
5. Deliverable: `reports/page-blueprint/<opportunity_id>.{md,json}` — the JSON
   sidecar is Content Strategy's future input contract.
6. Future cleanup (flagged, not now): extract the modules stages 3 and 4 share
   into `src/engine_core/`.

---

## Implementation status (2026-09-04)

- `src/page_blueprint/` package built end-to-end, TDD, `ruff` clean, full suite
  green (zero regressions in the stage-1–3 tests): **718 tests** at build time.
- The normal branch plus the forced-`HOLD` and content-pillar-`strip` branches
  are exercised end-to-end with recorded fixtures
  (`tests/fixtures/page_blueprint{,_reject,_strip}/`).
- The stage runs offline via recorded replay on the frozen live Cluster Strategy
  sidecar; a live run needs `ANTHROPIC_API_KEY` (same Keychain-wrapper convention
  as the pipeline — never Claude Code's OAuth).
- No change to any stage-1–3 code file, `CLAUDE.md`, `cluster-taxonomy.md`,
  `guardrails.yaml`, the inventories, or `business-dna/*`. No secret in any
  fixture or committed file.
- **Committed locally** (`d471823` `wip(page-blueprint): implement + test Stage 4
  module`, plus the follow-up docs/decision commit that records D-PB-1 … D-PB-12
  and freezes the test input fixture). **Not pushed** — the owner pushes.
