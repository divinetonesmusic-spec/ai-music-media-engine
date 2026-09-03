# Cluster Strategy V1 — Contract

> **Status: DECIDED — 2026-09-01.** Canonical pipeline **stage 3 (Cluster
> Strategy)** is open; stages 4–13 stay deferred. The C10 Definition-of-Done gate
> passed and is recorded (see C10; commit `39fe464`), meeting P4's stated
> precondition. On 2026-09-01 the owner opened stage 3 — and only stage 3 — and
> decided every open decision (**D-CS-1 … D-CS-12**) at its recommended answer.
> Those decisions are recorded in `knowledge/DECISIONS-NEEDED.md`, section
> **"# 4. ESTÁGIO 3 — CLUSTER STRATEGY"** (P4 updated accordingly). §15 below
> mirrors them for reference; the authoritative record is the decision log.
>
> Cluster Strategy is **canonical pipeline stage 3 (C8)**. Autonomy **Level 1** —
> it recommends, the human approves and executes. This document is the contract
> that every `src/cluster_strategy/` module cites (`contract §N`). Where this
> document and a DECIDED decision (C1–C10 / I1–I12 / D-CS-1–D-CS-12 in
> `knowledge/DECISIONS-NEEDED.md`) diverge, **the decision prevails** — surface
> the divergence instead of guessing.
>
> **P4 / D-CS-1.** Opening canonical stage 3 is decision **D-CS-1**, recorded in
> `knowledge/DECISIONS-NEEDED.md` (§4; P4 now reads "estágio 3 aberto; estágios
> 4–13 seguem DEFERRED"). This document does not substitute for that record — it
> implements it.
>
> Derived from the 2026-09-01 specification mission, which cross-referenced
> `CLAUDE.md`, `docs/TECHNICAL-SPEC-V1.md`, `docs/SESSION-STATE.md`,
> `knowledge/DECISIONS-NEEDED.md`, `AI Music Media Engine — Business DNA V1.md`,
> `knowledge/business-dna/*`, `knowledge/clusters/cluster-taxonomy.md`,
> `knowledge/rules/guardrails.yaml`, `knowledge/inventories/*`, and the stage 1–2
> implementation. It changed none of those sources.

---

## Preamble — the gate condition and the one contradiction to preserve

**Cluster Strategy = canonical pipeline stage 3 (C8).** Its build was governed by
**P4 (`Estágios seguintes do pipeline`)**, owner-decided, with the explicit
recommendation *"não abrir antes de C10 ser atendido"*. **D1 (owner, 2026-08-31)
restated this: "The canonical stages 3–13 (incl. Cluster Strategy, Content Plan)
stay deferred (P4) until the V1 C10 gate passes."**

The C10 gate **passed on 2026-09-01** (`GATE PASS`, commit `39fe464`, pushed);
the precondition was met. On 2026-09-01 the owner opened stage 3 via **D-CS-1**,
recorded in `DECISIONS-NEEDED.md` (§4). P4 now reads: *DEFERRED (2026-08-27) —
estágio 3 aberto 2026-09-01 (ver D-CS-1); estágios 4–13 seguem DEFERRED*.

**The load-bearing contradiction between documents** (surfaced, not silently
reconciled):

| `AI Music Media Engine — Business DNA V1.md` §11 / §35 | The DECIDED V1 contract | This contract keeps |
|---|---|---|
| §11 — "Cluster Strategy" defines *conceito, audiência, intenção, estado emocional, **linguagem, estética, conteúdo**, relação com música, relação com playlist, **CTA*** | **C8** puts Page Blueprint (stage 4 — visual identity, tone of voice) and Content Strategy (stage 5 — pillars, formats, hooks, structures, CTAs) *after* Cluster Strategy. `cluster-taxonomy.md`: *"Angle (editorial) … Tactical … changes per campaign … internal organization"*. | **The established boundary.** Cluster Strategy V1 stops at *cluster concept + audience + intent + emotion + positioning + music/playlist relationship + one non-binding first content direction*. It does **not** produce visual identity, content formats, hook libraries, CTA copy, schedules, or batch sizes. (Decision **D-CS-8**.) |
| §8 — every opportunity gets a **0–100 score** | **C6** — no composite 0–100 score, ever | No 0–100 score in Cluster Strategy either. Same qualitative `LOW/MEDIUM/HIGH/VERY_HIGH` rating + *separate* `LOW/MEDIUM/HIGH` confidence + red flags. |
| §9/§10 — states are `EXPLORE / TEST / LAUNCH / SCALE / KILL` (no PARK) | **I2** — V1 operational states are `EXPLORE / TEST / PARK`; LAUNCH/SCALE/KILL conceptual/deferred | Cluster Strategy **does not transition** the opportunity lifecycle (autonomy L1). It carries the state forward unchanged. It adds only a *pipeline-action* recommendation, which is not a lifecycle state. |
| §7 — an opportunity *"pode ser: um novo cluster; um subcluster"* | **C1** — `OPPORTUNITY ≠ CLUSTER` (structural rule) | C1. The opportunity is the market opportunity; Cluster Strategy is the stage that turns the opportunity's cluster *hypothesis* into a cluster *decision*. |
| §5 — 9 stages ("Opportunity Discovery", "Distribution") | **C8** — 13 stages ("Opportunity Analysis", "Publishing") | C8 (DECIDED). Naming divergence noted, non-blocking (D-CS-12). |

Per the mission's critical rules: **the established V1 contract prevails;
`AI Music Media Engine — Business DNA V1.md` supplies strategic intent for *what a
cluster strategy should contain*, not the contract style.**

---

# 1. PURPOSE

**Problem it solves.** Market Intelligence (stages 1–2) answers *"which
opportunities exist and which deserve our attention?"* and stops there. Every
opportunity carries only a **non-binding hypothesis** about its cluster
(`hypotheses.potential_cluster`, C7). It is never confirmed, never reconciled
against the canonical taxonomy's conceptual boundaries; the asset picture is
opportunity-scoped rather than cluster-scoped; and the strategic definition of
the cluster (concept, audience, intent, emotional register, positioning,
relationship to existing playlists/artists) does not exist anywhere. Without
this, Page Blueprint (stage 4) has no stable input: it would either re-derive the
cluster ad hoc or design a page against a guess.

**Cluster Strategy converts a single owner-approved opportunity into a confirmed
cluster decision plus a strategic cluster definition** that is stable enough for
Page Blueprint to consume.

**Where it sits.**

```
[stage 1–2]  Market Intelligence → Opportunity Analysis → Opportunity Report      (built, C10-validated)
                                          │  owner reviews review.md, marks one "advance"
                                          ▼
[stage 3]    CLUSTER STRATEGY   ── this contract ──▶  Cluster Strategy Report
                                          │
                                          ▼
[stage 4]    Page Blueprint                                                       (still deferred, P4)
[stage 5]    Content Strategy                                                     (still deferred, P4)
```

Input contract: the `OpportunityReport` (`docs/TECHNICAL-SPEC-V1.md` §23 —
*"Cluster Strategy stage consuming Opportunity Reports | `OpportunityReport`
schema is the contract | C8 (stage 3), P4"*). Output contract: a new
`ClusterStrategy` object that becomes Page Blueprint's input.

**What it must NOT do yet.**

- **Not** design a page (name, bio, visual identity, tone of voice, cadence) — Page Blueprint, stage 4.
- **Not** produce a content system (pillars, formats, hooks, structures, CTA copy, linguistic/visual rules, frequency, variations) — Content Strategy, stage 5. Business DNA V1 §13.
- **Not** produce content, templates, batch sizes, schedules, visual assets — stages 5–8.
- **Not** create, rename, merge, or formalize a canonical cluster — **P6 (`Governança de criação de cluster novo`) is still DEFERRED.** It may only *propose* a new cluster as a hypothesis, exactly as Market Intelligence does today (`cluster-taxonomy.md` open-taxonomy rule; CLAUDE.md §2).
- **Not** write `knowledge/clusters/cluster-taxonomy.md` or any file under `knowledge/` except (D-CS-7) an append to `opportunity-registry.yaml`.
- **Not** introduce a 0–100 score, weights, or a formula (C6).
- **Not** introduce `LAUNCH / SCALE / KILL` operationally; **not** transition an opportunity's lifecycle state (autonomy L1, I2).
- **Not** run automatically on every opportunity — it runs on an **owner-selected** opportunity (autonomy L1; I12 volume discipline).
- **Not** re-run Market Intelligence, re-collect signals, or re-evaluate the opportunity's 10 dimensions.

---

# 2. INPUT CONTRACT

### 2.1 Primary input — the Opportunity Report

Cluster Strategy consumes the **machine sidecar**
`reports/<run_id>/<opportunity_id>.json` (the JSON mirror of the full
`Opportunity`, `reporting.encode(opp)`), not the Markdown. It is the
authoritative structured record; the `.md` is human rendering.

| Field group (from `Opportunity`, spec §7) | Required? | Used for | Evidence character on input |
|---|---|---|---|
| `opportunity_id`, `schema_version`, `run_id`, `created_at`, `title` | **required** | identity, provenance link; **`schema_version` MUST be `1.0.0`** or the run hard-fails (D-CS-11) | OBSERVED (given) |
| C1 minimum: `need`, `audience{description,attributes}`, `market`, `language`, `platform`, `consumption_context` | **required** (all six, non-empty — already §13-enforced upstream) | the raw material for the cluster's strategic definition | OBSERVED |
| `durability`, `urgency` (I9) | **required** | cluster durability read; whether the angle is evergreen or a fast trend | OBSERVED |
| `evidence: list<EvidenceItem>` with `type ∈ {OBSERVED,INFERRED,HYPOTHESIS}`, `signal_ids`, `derived_from`, `rationale`, `confidence` | **required**, and **≥ 1 `OBSERVED`** item (mirrors ranking §11.1 hard-exclusion; an opportunity with zero OBSERVED evidence is refused) | separating fact from inference in the cluster definition; the new-cluster proposal's supporting evidence | typed as-is |
| `asset_fit: AssetMatch` (§10) — `matching_playlists/pages/artists`, `best_playlist/page/artist`, `new_asset_recommendation{asset_type, rationale, i5_conditions_met}`, `unmatched_reason`, each candidate's `fit`, `fit_basis ∈ {OBSERVED,INFERRED,UNKNOWN}`, `role ∈ {candidate,reference,hero}` | **required** | the entire Asset Strategy section is a **consolidation** of this — Cluster Strategy adds cluster-level framing but **introduces no asset not already here / in the inventory** | `fit_basis` carried verbatim |
| `evaluation: Evaluation` (§8) — 10 `dimensions{rating,confidence,justification,blocked_by}`, `red_flags{description,severity,kind}`, `overall_confidence`, `summary` | **required** | `overall_confidence` is carried as the ceiling on Cluster Strategy's own confidence (C6 rule: not raised by high sub-ratings); `red_flags` (esp. `kind: compliance`) are carried forward and re-checked; `blocked_by` NEEDS_INPUT/UNKNOWN items propagate | as-is |
| `business_outcome_profile` (§9), 5 axes | **required** | context for the positioning and the differentiation judgement; **not** re-rated | as-is |
| `status` (the opportunity's own lifecycle field, §7 — `EXPLORE`/`TEST`/`PARK`) | **required** | carried unchanged into `opportunity_snapshot.status` and `recommendation.opportunity_lifecycle_state` — Cluster Strategy never transitions it (I2, autonomy L1) | as-is |
| `recommendation: Recommendation` (§12.4) — `target_state ∈ {EXPLORE,TEST,PARK}`, `suggested_next_step`, `justification`, `confidence`, `execution_note` | **required** | `target_state` (a *recommendation*, e.g. advance to TEST) is carried into `opportunity_snapshot.target_state` as **context only** — it is not the lifecycle state; `suggested_next_step` seeds `target_next_stage` | as-is |
| `hypotheses: Hypotheses` (§7.2) — `potential_cluster{value,canonical,basis}`, `potential_positioning`, `potential_page`, `first_content_direction`, `format`, `hook` | **optional** (may be `null`, or fields stripped by the guardrail escalation) | `potential_cluster` is **the hypothesis Cluster Strategy confirms, overrides, or escalates**; the others are non-binding seeds | HYPOTHESIS |
| `provenance: OpportunityProvenance` — `signal_ids`, `sources: list<Provenance>`, `model`, `prompt_version`, `generated_at`, `replay` | **required** | full traceability chain is carried into the Cluster Strategy provenance; **`replay: true` opportunities are flagged "not current-trend evidence" (spec §22) and are strategy-testing only** | as-is |

**Required vs optional summary:** everything except `hypotheses`,
`hypotheses.*`, `audience.attributes`, `unmatched_reason`,
`new_asset_recommendation` is required (these already reflect §13 upstream
enforcement). Cluster Strategy adds no new "required-from-the-opportunity" field
beyond `schema_version == 1.0.0`.

### 2.2 Owner-authorization gate (autonomy L1)

Cluster Strategy runs **only** on an opportunity the owner has marked to advance.
The authoritative record is `reports/<run_id>/review.md` (spec §21.1): the
front-matter `advanced_opportunity_id` must equal the input opportunity's id
(`gate.parse_review(...).advanced_opportunity_id`). **D-CS-3:** explicit
per-opportunity, owner-invoked CLI; refuse if the opportunity is not the advanced
one for that run. No batch / automatic run.

### 2.3 Existing business knowledge it may consume (read-only)

All loaded by the **existing `market_intelligence.knowledge_loader`** (no new
loader):

| Source | Used for |
|---|---|
| `knowledge/clusters/cluster-taxonomy.md` — the 11 canonical ids + per-cluster **conceptual boundary / adjacency / subcluster** prose + the 5 registered ambiguities | the cluster-mapping decision; the "why not a subcluster" test; the boundary statement of any new-cluster proposal |
| `knowledge/inventories/{artists,playlists,pages,catalog}.yaml` (+ consolidated `primary_cluster`/`secondary_clusters`/`language`/`market`/`hero_artist`/`purpose`/`priority`) | the Asset Strategy consolidation; hero roster; catalog affinity; market/language fit. **Only source of asset truth (I1). Never invent.** |
| `knowledge/business-dna/business-dna.md` (§2 clusters, §4 strategic objective / funnel, §10 artist architecture, §11 playlist strategy, §14 strategic horizon) | strategic coherence check; the funnel the positioning must serve; hero-artist doctrine (§10.2a) |
| `knowledge/business-dna/content-methodology.md` (I11 — historical, not rules) | the *first content direction* hypothesis (with autonomy to go beyond current formats) |
| `knowledge/rules/guardrails.yaml` — G01–G10 | the compliance self-check on every piece of Cluster Strategy prose (see §9) |
| `knowledge/market/opportunity-registry.yaml` | context: prior opportunities and whether a related cluster decision was already made (avoid re-proposing) |

It **must not** parse `CLAUDE.md` or `DECISIONS-NEEDED.md` prose for enforcement —
same rule as the pipeline (spec §3, §13).

---

# 3. CLUSTER DECISION

`cluster_decision ∈ { MAP_TO_EXISTING, PROPOSE_NEW_CLUSTER, DEFER, REJECT }` — a
classification of *this stage's output*, **not a lifecycle state**.

### 3.1 Mapping to an existing canonical cluster (`MAP_TO_EXISTING`)

1. **Deterministic pre-normalisation (code).** Before any judgement: normalise
   the opportunity's `hypotheses.potential_cluster.value` — strip
   language/spelling variants and known aliases (`limpieza-energetica` es ⇄
   canonical `limpeza-energetica`; `Sono Restaurador` → `sono`, per the
   taxonomy's own normalisation rule). This alone resolves cases like **Run 3's
   advanced opportunity `opp_2026-09-01_92016b7992`**, where Framing tagged
   `limpieza-energetica (proposed_new)` purely because of the Spanish spelling —
   it is the existing canonical `limpeza-energetica`.
2. **Claude confirms or overrides.** Test the opportunity's `need` +
   `consumption_context` + `audience` + OBSERVED evidence against **each
   canonical cluster's stated conceptual boundary** in `cluster-taxonomy.md`.
   Output: `cluster_id` (one of the 11), and `framing_hypothesis_comparison` — a
   sentence stating whether the Opportunity Report's hypothesis was **confirmed**
   or **overridden**, and why (citing the boundary and the evidence).
3. **Subcluster / angle detection.** If the opportunity is a specific occasion,
   sub-theme or intersection *within* the cluster (e.g. *"limpieza energética for
   a new-home / moving ritual"*), set `subcluster_or_angle` and
   `is_new_subcluster: true`. Per `cluster-taxonomy.md`, **subclusters and angles
   are internal organisation, not official categories** — this is **not** a new
   cluster and produces no proposal.
4. **Ambiguity carry-through.** If the opportunity lands on one of the taxonomy's
   5 registered ambiguities (Sono ↔ Sonho Lúcido; "Relaxamento" in clusters 7 vs
   8; Frequência Divina ↔ Glândula Pineal; non-Judaeo-Christian content under
   Anjos; the `classification-input.yaml` reconciliation), Cluster Strategy
   **surfaces it as an `open_question`** and picks the reading most consistent
   with the taxonomy's stated resolution — it does not silently invent a new
   resolution.

### 3.2 Proposed / new clusters (`PROPOSE_NEW_CLUSTER`)

Only when, after §3.1, the opportunity genuinely fits **no** canonical cluster
**and** is **not** a subcluster/angle of one. The output is a
**`new_cluster_proposal`** — a hypothesis and a hand-off, never a taxonomy edit:

- `proposed_id`, `proposed_name` (recommendation)
- `concept` — one paragraph, in the style of the 11 taxonomy entries
- `boundary_vs_adjacent` — `map<canonical_cluster_id → string>`: for **every
  adjacent existing cluster**, the sentence that distinguishes the proposal from
  it (mirrors how each of the 11 taxonomy entries has a "Fronteira conceitual" +
  "Relação com outros clusters")
- `why_not_subcluster` — the explicit argument that it cannot be an angle inside
  an existing cluster
- `supporting_evidence` — refs to the opportunity's OBSERVED / INFERRED evidence
  items only
- `governance_note` — fixed: *"Formalizing a canonical cluster is an owner
  decision (P6, DEFERRED). This is a proposal only; the pipeline does not modify
  `cluster-taxonomy.md`."*

### 3.3 Rules against duplicate / artificial clusters

- **Never** propose a cluster that is a spelling, language, or synonym variant of
  an existing one (§3.1 step 1 blocks this deterministically).
- **Never** propose a cluster for what is an **angle/occasion/intersection**
  inside an existing cluster (`why_not_subcluster` must survive scrutiny).
- **Never** propose a cluster on thin evidence: require the same floor as ranking
  §11.1 — **≥ 1 OBSERVED evidence item** — and, because a cluster is a
  portfolio-level commitment, `PROPOSE_NEW_CLUSTER` **SHOULD** additionally
  require either `Opportunity.overall_confidence ≥ MEDIUM` or **≥ 2 OBSERVED
  signals from distinct sources** (cross-corroboration). Below that → `DEFER`.
- A proposal **must** state its boundary against every adjacent cluster (§3.2) —
  a proposal that cannot articulate its distinctness is auto-downgraded to
  `DEFER`.
- **Never** propose a cluster whose concept can only be expressed as a prohibited
  claim (compliance) — that is `REJECT`.

### 3.4 When to reject or defer

| `cluster_decision` | Trigger | Meaning |
|---|---|---|
| `DEFER` (`deferral_reason` required) | (a) fit is `proposed_new` **and** the owner has not opened P6 (D-CS-2); (b) evidence below the §3.3 floor for a new cluster; (c) the opportunity sits on an unresolved taxonomy ambiguity that materially changes the cluster; (d) musical-DNA `NEEDS_INPUT` blocks the music-relationship definition to a degree the owner has said is unacceptable (D-CS-9) | the strategy is documented but not finalized; recommends `BACK_TO_MARKET_INTELLIGENCE` or `FORMALIZE_CLUSTER` first |
| `REJECT` (`rejection_reason` required) | the cluster concept is untenable — a **HIGH-severity `compliance` red flag** that cannot be reframed without abandoning the concept; or the opportunity, on closer reading against the taxonomy, has **no coherent cluster** at all | recommends `HOLD`; the opportunity's lifecycle state is **not** changed by Cluster Strategy — the owner decides |

---

# 4. STRATEGIC OUTPUT — the `ClusterStrategy` object

One per advanced opportunity. **Markdown + YAML front matter + JSON sidecar** (I4
pattern), `schema_version: "1.0.0"`, written to
`reports/cluster-strategy/<opportunity_id>.md` / `.json` (D-CS-6).

**O/D/H/R attribution.** Every field below is classed **O**bserved (carried from
the Opportunity Report / inventory, unchanged) · **D**erived (Cluster Strategy's
reasoned decision) · **H**ypothesis (non-binding) · **R**ecommendation (a proposed
action, never executed). In V1 that attribution is expressed **in the
human-readable `.md` report**, which visually separates *Observed facts / Derived
decisions / Hypotheses / Recommendations* (and labels the recommendation and the
hypothesis sections as such). The `.json` sidecar is a structural encoding of the
`ClusterStrategy` object — it does **not** carry a per-field O/D/H/R tag. The
tables in this section are the reference for which class each field belongs to;
per-field tagging in the sidecar is a possible V2 refinement.

### 4.1 Identity & Provenance

| Field | Purpose | Type | Req | Source | O/D/H/R |
|---|---|---|---|---|---|
| `cluster_strategy_id` | stable id | string; default `cs_<opportunity_id>` (idempotent — one per opportunity) | yes | derived | D |
| `schema_version` | forward-compat | `"1.0.0"` | yes | — | — |
| `opportunity_id` / `opportunity_run_id` / `opportunity_report_ref` | link to the input | string / path | yes | Opportunity Report | O |
| `opportunity_snapshot` | frozen copy of the input's `need`, `audience`, `market`, `language`, `platform`, `consumption_context`, `durability`, `urgency`, `overall_confidence`, **`status`** (the opportunity's actual registry lifecycle state — `EXPLORE`/`TEST`/`PARK`), **`target_state`** (the Market Intelligence *recommendation*, e.g. "advance to TEST" — context only, never the carried lifecycle state), `hypotheses.potential_cluster` | object | yes | Opportunity Report | O |
| `owner_authorization` | the `review.md` reference + `advanced_opportunity_id` proving the opportunity was advanced | object | yes | `review.md` | O |
| `provenance` | `run_id`, `model`, `prompt_version`, `generated_at`, `replay`, `signal_ids` (carried union), `sources: list<Provenance>` (carried), `knowledge_snapshot { taxonomy_generated, guardrails_transcribed_at, inventory_generated_at, registry_len }` | object | yes | mixed | O + D |

### 4.2 Cluster Decision (see §3)

| Field | Purpose | Type | Req | O/D/H/R |
|---|---|---|---|---|
| `cluster_decision` | the decision | enum `MAP_TO_EXISTING`\|`PROPOSE_NEW_CLUSTER`\|`DEFER`\|`REJECT` | yes | **R** (recommendation — owner approves before stage 4) |
| `cluster_id` | canonical id | string ∈ 11 canonical ids, or `null` | yes when `MAP_TO_EXISTING` | D |
| `cluster_name` | display | string | copied from taxonomy | O |
| `subcluster_or_angle` | the editorial subdivision this opportunity represents inside the cluster | string \| `null` | optional | H/D |
| `is_new_subcluster` | flags a subdivision new to the cluster | bool | yes when `subcluster_or_angle` set | D |
| `framing_hypothesis_comparison` | confirmed / overrode the Opportunity Report's `potential_cluster`, and why | string, MUST cite taxonomy boundary + an evidence item | yes | D |
| `cluster_decision_justification` | the full reasoning | string | yes | D |
| `new_cluster_proposal` | see §3.2 | object \| `null` | yes when `PROPOSE_NEW_CLUSTER` | R + O(evidence refs) |
| `deferral_reason` / `rejection_reason` | | string \| `null` | required for `DEFER` / `REJECT` | D |

### 4.3 Cluster Strategic Definition (the Business DNA V1 §11 content, at cluster level)

| Field | Purpose | Type | Req | O/D/H/R |
|---|---|---|---|---|
| `central_concept` | the editorial idea of the cluster *as this opportunity expresses it* | string | yes | D |
| `audience` | `{ description, attributes }` — refined from `Opportunity.audience` + evidence | object | yes | O (base) + D (refinement) |
| `intent` | what the audience wants to **do** (fall asleep, cleanse a space, focus) | string | yes | O/D |
| `emotional_state` | the felt experience — **framed as subjective experience (G02), never an outcome** | string | yes | D + guardrail-checked |
| `consumption_context` | when/where/how | string | yes | O (carried) |
| `editorial_promise` | the non-medical, non-outcome promise | string | yes | D + guardrail-checked |
| `positioning_statement` | one sentence: *for [audience] who [need], [cluster/angle] is [promise]* | string | yes | **R** |
| `market` / `language` | | enum | yes | O (carried) |
| `localization_notes` | how the concept adapts to this market/language; what stays fixed | string | yes | D |
| `durability_read` | `{ label: EPHEMERAL/EMERGING/STRUCTURAL/EVERGREEN, note }` — informed by `Opportunity.durability`, may refine with a rationale | object | yes | O + D |
| `strategic_coherence_note` | how this cluster serves the funnel (business-dna §4) and the portfolio (§14 fast-trend + evergreen) | string | yes | D |

### 4.4 Asset Strategy — see §5 for rules

| Field | Type | Req | O/D/H/R |
|---|---|---|---|
| `playlist_strategy` | `{ primary_playlist_id: playlist_id\|UNKNOWN\|NEW_ASSET, playlist_fit_basis: OBSERVED\|INFERRED\|UNKNOWN, secondary_playlist_ids: [id], new_playlist_recommendation: NewAssetRecommendation\|null, reuse_rationale: string }` | yes | O (ids, fit_basis) + D (rationale) + R (new-asset rec) |
| `page_strategy` | `{ primary_page_id: own page_id\|UNKNOWN\|NEW_ASSET, page_fit_basis, new_page_recommendation: {asset_type, rationale, i5_conditions_met} \| null, note }` — **the page's design is Page Blueprint; this is only "a new page is/isn't warranted + why", carried verbatim from `AssetMatch`** | yes | O + R |
| `artist_strategy` | `{ anchor_hero_artist_ids: [id], catalog_affinity_artist_ids: [id], candidate_artist_ids: [id], best_artist_id: id\|UNKNOWN, affinity_note (fixed) }` | yes | O (roster, candidates) + D (anchor selection) |
| `catalog_affinity_summary` | which existing releases relate (coarse, spec §10.3) | string | yes | O |
| `market_language_fit` | `{ rating: LOW/MEDIUM/HIGH/VERY_HIGH, confidence: LOW/MEDIUM/HIGH, justification }` — **no score** | yes | D (capped — see §11) |
| `asset_gaps` | `[string]` — from `AssetMatch.unmatched_reason` + inventory gaps | yes | O |

The fixed `execution_note` (*"V1 does not execute this action; it requires human
approval."*) travels with the recommendation (§4.7) on every `ClusterStrategy`.

### 4.5 Content Direction (deliberately shallow — see §8)

| Field | Type | Req | O/D/H/R |
|---|---|---|---|
| `first_content_direction` | carried/refined from `hypotheses.first_content_direction` | string | yes | **H** |
| `editorial_angles` | candidate angles within the cluster/subcluster (tactical, non-binding) | `[string]` | optional | **H** |
| `music_relationship` | the role the track plays in the content (mood/function); sonic criteria are `NEEDS_INPUT` | string | yes | D (confidence-capped) |
| `content_boundary_note` | fixed: *"Content pillars, formats, hooks, structures, CTAs, cadence and visual language are defined by Content Strategy (stage 5) and Page Blueprint (stage 4). This section is a non-binding starting direction only (C7, I11)."* | string | yes | — |

### 4.6 Evaluation & Confidence (no 0–100 — see §11)

| Field | Type | Req | O/D/H/R |
|---|---|---|---|
| `dimensions` | `map<key → { rating: LOW/MEDIUM/HIGH/VERY_HIGH, confidence: LOW/MEDIUM/HIGH, justification, blocked_by?: [string] }>` — keys: `cluster_fit`, `differentiation_within_cluster`, `asset_readiness`, `strategic_coherence` (D-CS-4) | yes (all keys present) | D |
| `overall_confidence` | `LOW/MEDIUM/HIGH` — **MUST NOT exceed `Opportunity.overall_confidence`**, and **MUST NOT be raised by high dimension ratings** (C6 rule, carried) | yes | D |
| `red_flags` | `[{ description, severity: LOW/MEDIUM/HIGH, kind: compliance\|feasibility\|evidence_gap\|asset_gap\|taxonomy\|other }]` — carried compliance flags **plus** any found in Cluster Strategy's own prose | yes (may be `[]`) | O (carried) + D |
| `open_questions` | `[string]` — what the owner / a downstream stage must resolve | yes (may be `[]`) | D |

### 4.7 Recommendation (I3 pattern)

| Field | Type | Req | O/D/H/R |
|---|---|---|---|
| `target_next_stage` | enum `PAGE_BLUEPRINT` \| `FORMALIZE_CLUSTER` \| `BACK_TO_MARKET_INTELLIGENCE` \| `HOLD` — **the next pipeline action, not a lifecycle state** | yes | **R** |
| `recommended_next_step` | concrete, actionable, still a recommendation | string | yes | **R** |
| `opportunity_lifecycle_state` | `EXPLORE`/`TEST`/`PARK` — **the opportunity's actual registry `status`, carried unchanged** (never the Market Intelligence `target_state` recommendation). The deterministic validator fails the run if this diverges from `opportunity_snapshot.status` (autonomy L1, I2). | yes | O |
| `justification` | grounded in the decision, the evidence, the red flags | string | yes | D |
| `execution_note` | fixed: *"V1 does not execute this action; it requires human approval."* | string | yes | — |

---

# 5. ASSET STRATEGY

**Hard rule (I1, C10.4, spec §10.4, §19): NEVER invent artists, playlists, pages,
or assets.** Every `*_id` in the output MUST resolve in the corresponding
inventory file; the deterministic validator drops any non-existent reference to
`UNKNOWN` with a logged warning. Cluster Strategy **adds no asset that is not
already in the opportunity's `AssetMatch` or the inventory** — it *consolidates
and frames*, it does not re-do Asset Matching.

| Question | How Cluster Strategy decides |
|---|---|
| **Playlist usage** | Start from `AssetMatch.best_playlist`. If it is a real `playlist_id` with `fit_basis: OBSERVED` (consolidated inventory `cluster` matches) → **reuse it** (`reuse_rationale`, I5 default). Secondary playlists = other `matching_playlists` with `fit ≥ MEDIUM`. **Never** recommend a new playlist unless `AssetMatch.new_asset_recommendation.asset_type == playlist` with all four I5 conditions true — and even then it is `R`, never executed (Business DNA V1 §12: *"Não deve criar playlists novas automaticamente"*; I5). |
| **Page usage** | Carry `AssetMatch.best_page` and `new_asset_recommendation` **verbatim**. Cluster Strategy states *whether* a new page is warranted and *why* (the four I5 conditions), and which existing playlist/artist should anchor it. It does **not** name, position, or design the page — that is Page Blueprint (D-CS-8). Only `ownership: own` pages are usable; `reference_competitor` pages are context for `differentiation_within_cluster` only, never recommended (spec §10.3). |
| **Artist usage** | From `AssetMatch.matching_artists`. Cluster Strategy names 1–3 **anchor artists** for the cluster. |
| **Hero artists** | The **10 hero artists** (`hero_artist: true`, same 10 on all 8 playlists) are **always eligible for any cluster** regardless of catalog affinity (`business-dna.md` §11; spec §10.2a). Cluster Strategy selects which hero(es) to anchor this cluster; `affinity_note` (fixed) restates the doctrine. |
| **Existing vs new assets** | **Reuse is the default (I5).** New asset = recommendation only, only when cumulatively: no existing asset with adequate fit **and** relevant potential **and** plausible differentiation **and** sufficient window — carried from `AssetMatch.i5_conditions_met`, not re-judged. |
| **Catalog affinity** | An artist's `primary_cluster` / `secondary_clusters` = **catalog affinity = context, not a placement restriction** (`business-dna.md` §10; `cluster-taxonomy.md`; spec §10.2a). Cluster Strategy MUST NOT conclude "artist X does not fit" from an affinity mismatch. Keep three concepts distinct and never collapse: **catalog affinity · playlist placement · strategic hero status.** `catalog_affinity_summary` lists which *releases* (from `catalog.yaml`, coarse per §10.3) relate to the cluster. |
| **Market / language fit** | Compares the opportunity's `market`/`language` against the consolidated `market`/`language` on candidate playlists/pages/artists. `market_language_fit` is a `{rating, separate confidence, justification}` triple — **no score**. Structurally capped (§11): confidence ≤ MEDIUM while musical-DNA detail is `NEEDS_INPUT` and while the strategic-classification backlog remains `NEEDS_INPUT`. |
| **Asset gaps** | `asset_gaps` = `AssetMatch.unmatched_reason` + any inventory gap Cluster Strategy observes (e.g. "no `own` page in cluster X for market Y"). These are `O`, drawn from the inventory, never speculative. |

---

# 6. MARKET / LANGUAGE STRATEGY

- **The market/language of the cluster strategy is fixed by the opportunity** —
  `market ∈ {Brasil, Mercados hispanohablantes, English-speaking markets}`,
  `language ∈ {pt, es, en}`, consistent by the spec §7.1a table (already
  §13-enforced). **No country-level taxonomy in V1** (spec §7.1a). Target
  countries per language remain `NEEDS_INPUT` (`business-dna.md` §8) — Cluster
  Strategy does not invent them.
- **Influence on strategy.** `localization_notes` states: which parts of
  `central_concept` / `intent` / `emotional_state` are universal to the cluster
  and which are market-specific (idiom, cultural framing, occasion salience). It
  must not import a strategy from another market's assets as fact — an es cluster
  strategy anchored on a pt playlist is an `asset_gap`, not a fit.
- **Localization.** V1 keeps it descriptive, not generative: Cluster Strategy
  names *what would need to be localized* (page language, hook language,
  culturally-specific angles) and *which existing localized assets exist* (from
  the inventory's consolidated `language`/`market`). It does **not** write
  localized copy — that is Content Strategy.
- **Missing assets in a target market.** If no `own` page / no classified artist
  / no playlist exists for the opportunity's `market`+`cluster`, Cluster
  Strategy:
  1. records the gap in `asset_gaps`;
  2. carries the opportunity's `new_asset_recommendation` (if the I5 conditions
     were met upstream);
  3. still names the **cross-market hero roster** as eligible anchors (§10.2a —
     hero status is market-independent);
  4. sets `market_language_fit.rating` accordingly, with confidence capped.

---

# 7. POSITIONING

**Transform: opportunity → strategic positioning**, with fact and hypothesis kept
apart at every step.

| Positioning element | Built from | Type |
|---|---|---|
| `audience` (refined) | `Opportunity.audience` + attributes that are **directly supported by an OBSERVED evidence item** | O base, D refinement — refinements not backed by evidence are typed as inference in the justification |
| `intent` | `Opportunity.need` + `consumption_context` | O/D |
| `emotional_state` | inferred from the cluster's taxonomy definition + the opportunity's framing — **stated as subjective experience, never as an effect the music produces** (G02, G01, G03) | D, guardrail-checked |
| `editorial_promise` | the smallest true promise the content can make without a claim | D, guardrail-checked |
| `positioning_statement` | the synthesis — one sentence | **R** (a recommendation the owner approves before Page Blueprint) |
| `differentiation` | vs `reference_competitor` context in the Opportunity's `competitive_position` dimension + `differentiation_potential` dimension — **carried, not re-scored**; expressed qualitatively | D |

**Rules (C7, guardrails.yaml G09/G10):**

- Every sentence in the positioning is one of: **observed fact** (cite the
  evidence item), **derived decision** (Cluster Strategy's reasoning, labelled),
  or **hypothesis** (labelled, non-binding).
- A hypothesis is **never** promoted to a fact by Cluster Strategy.
  `hypotheses.potential_positioning` from the Opportunity Report enters as `H`;
  if Cluster Strategy adopts it, `positioning_statement` is `R` (a
  recommendation) — still not a fact.
- Claims that depend on evidence the run does not have are **flagged for
  validation** (G09) in `open_questions`, not asserted.
- Where the input is `UNKNOWN` / `NEEDS_INPUT`, the positioning says so (G10) —
  it does not fill the gap.

---

# 8. CONTENT DIRECTION

**Cluster Strategy says the minimum about content that Page Blueprint / Content
Strategy need to start, and no more.** This is the sharpest boundary in the
contract because Business DNA V1 §11 explicitly over-reaches here.

**What Cluster Strategy produces:**

- `first_content_direction` — **one** non-binding direction, carried and lightly
  refined from `hypotheses.first_content_direction` (C7; I11 gives Claude
  autonomy to propose beyond current methodology). Type: **HYPOTHESIS**.
- `editorial_angles` — a short list of candidate angles/occasions *within* the
  cluster/subcluster. Tactical, non-binding, explicitly for Content Strategy to
  test. Type: **HYPOTHESIS**.
- `music_relationship` — the **role** the music plays in the content (ambient
  bed, foreground, ritual-paced), *not* the sonic spec (that is `NEEDS_INPUT`
  musical DNA — `business-dna.md` §9). Confidence-capped.
- `content_boundary_note` — the fixed disclaimer (§4.5).

**What Cluster Strategy MUST NOT produce** (all → Content Strategy stage 5 / Page
Blueprint stage 4, per C8, `cluster-taxonomy.md`, Business DNA V1 §12–§15):
content **pillars**, **formats**, **hook libraries**, **structures**, **CTA
copy**, **linguistic rules**, **visual language / aesthetics**, **posting
frequency / cadence**, **batch sizes**, **templates**, **schedules**,
**variations / A-B design**, the `CONTENT_OBJECT` schema.

**D-CS-5 / D-CS-8 (DECIDED 2026-09-01, `DECISIONS-NEEDED.md` §4):** this boundary
is confirmed. Everything Business DNA V1 §11 lists beyond the four items above is
stage 4/5.

---

# 9. COMPLIANCE / GUARDRAILS

- **Same mechanism as Market Intelligence.** Cluster Strategy loads
  `knowledge/rules/guardrails.yaml` (G01–G10) via the existing `knowledge_loader`;
  it does **not** parse `CLAUDE.md`. It reuses `market_intelligence.guardrails`
  (`check_texts` / the scanners) with **Cluster-Strategy scopes** mapped to the
  guardrail `applies_to` families:
  - `central_concept`, `emotional_state`, `editorial_promise`,
    `positioning_statement`, `localization_notes`, `first_content_direction`,
    `editorial_angles`, `music_relationship`, `cluster_decision_justification`,
    `new_cluster_proposal.*`, report prose → checked against **G01, G03, G04,
    G05, G06, G07, G08, G09, G10** as applicable.
  - `market_language_fit.justification`, `dimensions.*.justification` → G04, G05,
    G09.
- **Carry-forward.** Every `red_flag` with `kind: compliance` on the input
  Opportunity is copied into `ClusterStrategy.red_flags` **and** re-tested
  against Cluster Strategy's own prose (deduped by normalised text, so an exact
  restatement collapses but a distinct flag is never dropped).
- **Escalation — the full Market Intelligence `ComplianceResult`, not just
  exclusion.** The deterministic scanner's result is applied exactly as the MI
  Evaluation stage applies it:
  - **`exclude_opportunity`** — a HIGH-severity hit in **core** content
    (`report_prose` scope: `central_concept`, `emotional_state`,
    `editorial_promise`, `positioning_statement`, `music_relationship`,
    `cluster_decision_justification`, …) → `cluster_decision = REJECT`,
    `target_next_stage = HOLD` (§3.4).
  - **`strip_scopes`** — a HIGH-severity hit in a **non-core hypothesis** scope
    (`hypotheses.first_content_direction`, which covers both
    `first_content_direction` and `editorial_angles`) → that scope is **stripped**
    from the assembled strategy (`first_content_direction` replaced with a fixed
    "[removed — compliance]" note, `editorial_angles` emptied) and the run
    **proceeds**. The compliance red flag is still surfaced.
  - **`needs_uncertainty_note`** — the scope is recorded as an `open_question`
    asking for an explicit UNKNOWN / uncertainty statement (no scanner currently
    emits this, matching MI).
- A carried MEDIUM/LOW compliance flag → kept; the prose is written to clear it;
  `open_questions` notes the constraint for downstream stages.
- **Claims-vs-topics calibration (preserved).** The Evaluation-stage prompt was
  tightened (commit `39fe464`) so the compliance self-check flags **prohibited
  claims**, not **sensitive topics** — a topic mention ("energetic cleansing",
  "432 Hz", "sleep music") is not a violation; a claim about it ("removes
  negative energy", "treats insomnia", "scientifically proven") is. **Cluster
  Strategy inherits exactly this calibration** in its own self-check prompt:
  naming the cluster, the theme, or the audience's belief is fine; asserting an
  effect / cure / treatment / proven mechanism is not. `emotional_state` and
  `editorial_promise` are written as **subjective experience / intention /
  ritual** (G02, permitted), never as an outcome.
- **Uncertainty propagation (G10, spec §15).** `UNKNOWN` (fact absent from
  sources) and `NEEDS_INPUT` (pending owner decision) are **never** replaced with
  a guess. `blocked_by` on any Cluster Strategy dimension names the specific
  `NEEDS_INPUT`/`UNKNOWN` item; the report section renders it. `music_relationship`
  and `market_language_fit` are **structurally confidence-capped** while
  musical-DNA detail and the classification backlog are `NEEDS_INPUT`.

---

# 10. DECISION STATES

**No `LAUNCH` / `SCALE` / `KILL` is introduced.** No source requires them for
stage 3, and D1 forbids operationalising them in V1.

**The opportunity lifecycle is not touched.** `EXPLORE` / `TEST` / `PARK` (I2)
belong to the opportunity registry; Cluster Strategy carries
`opportunity_lifecycle_state` forward unchanged and never proposes a transition
(autonomy L1 — the owner transitions state).

**Cluster Strategy needs exactly two small, non-lifecycle vocabularies** (both
are *outputs of one run of the stage*, not a persistent state machine):

| Vocabulary | Values | Meaning |
|---|---|---|
| `cluster_decision` | `MAP_TO_EXISTING` · `PROPOSE_NEW_CLUSTER` · `DEFER` · `REJECT` | what this stage concluded about the cluster (§3) |
| `target_next_stage` (recommendation) | `PAGE_BLUEPRINT` · `FORMALIZE_CLUSTER` · `BACK_TO_MARKET_INTELLIGENCE` · `HOLD` | the recommended next pipeline action — still a recommendation, human-approved (I3, autonomy L1) |

**No persistent per-cluster or per-strategy `status` field** (D-CS-4). A re-run
overwrites `reports/cluster-strategy/<opportunity_id>.*` (idempotent, like a
same-`run_id` MI re-run, spec §5); the registry link (D-CS-7) is the durable
record.

---

# 11. CONFIDENCE / EVIDENCE

**No new composite 0–100 score. No weights, no formula, no aggregation (C6, spec
§8.3, §13 "no score" test).** The deterministic validator reuses
`market_intelligence.schema.validate.scan_json_for_numeric_score` over the whole
`ClusterStrategy` encoding and **fails on any `N/100`, `N out of 100`, or
`score: N` pattern**.

**Representation — identical to the pipeline's:**

- Each Cluster Strategy dimension (`cluster_fit`,
  `differentiation_within_cluster`, `asset_readiness`, `strategic_coherence`): a
  **qualitative `rating ∈ {LOW, MEDIUM, HIGH, VERY_HIGH}`** and a **separate
  `confidence ∈ {LOW, MEDIUM, HIGH}`** and a `justification` that cites specific
  evidence items where applicable, and `blocked_by` when a
  `NEEDS_INPUT`/`UNKNOWN` limits it.
- `overall_confidence ∈ {LOW, MEDIUM, HIGH}`: **explicitly assigned**, **capped
  at `Opportunity.overall_confidence`** (Cluster Strategy cannot be more
  confident than the opportunity it rests on), and **MUST NOT be raised by high
  dimension ratings** (C6, spec §8.3 — the rule that `overall_confidence = LOW`
  is not overridden by `HIGH` sub-ratings, carried verbatim).
- Confidence is **structurally capped ≤ MEDIUM** on `market_language_fit` and
  `music_relationship` while musical-DNA detail (`business-dna.md` §9) and the
  strategic-classification backlog remain `NEEDS_INPUT` — same structural cap the
  pipeline applies to `music_fit` (spec §8.1, §15).
- **Evidence typing carried through:** the `ClusterStrategy` **`.md` report**
  visually separates **Observed facts / Derived decisions / Hypotheses /
  Recommendations** (see §4 — the O/D/H/R class of each field). The `.json`
  sidecar is a structural encoding and does not carry a per-field O/D/H/R tag.
  Every OBSERVED claim still traces back through
  `signal_ids → Signal.provenance → raw capture` (spec §16.3), inherited from the
  Opportunity Report — Cluster Strategy adds no un-traceable observation. This
  preserves the C10.3 requirement (observed facts explicitly distinguished from
  hypotheses) in the human-reviewed report.

---

# 12. EXAMPLE — Opportunity → Cluster Strategy

**Input:** `reports/run_2026-08-31_01/opp_2026-08-31_1bca4af972.json` —
*"Energetic cleansing music for new-home rituals (ES market)"*. This is **Run 1's
owner-advanced opportunity** (`review.md`: `advance`).

### OBSERVED FACTS (carried from the Opportunity Report / inventory — unchanged, traceable)

- Market `Mercados hispanohablantes` / `es` / platform `tiktok`;
  `durability: EMERGING`; `urgency: MEDIUM`; `overall_confidence: LOW`;
  `status: EXPLORE` (the opportunity's actual registry lifecycle state);
  `target_state: TEST` (the Market Intelligence *recommendation* — context
  only, not the lifecycle state).
- `need`: *"Música para limpiar energéticamente una casa nueva o espacio"*;
  `consumption_context`: *"Durante o después de mudarse a un nuevo hogar, como
  parte de un ritual de limpieza"*.
- **3 OBSERVED evidence items, cross-platform:** `sig_run_2026-08-31_01_0014` —
  TikTok discovery page "Limpieza Energética Casa Nueva" (confidence LOW,
  `observed_at 2026-05-11`); `sig_…_0015` — YouTube playlist "LIMPIEZA
  ENERGÉTICA • Música para PURIFICAR tu HOGAR…" (MEDIUM); `sig_…_0016` — Spotify
  album "Música para Limpiar la Energía Negativa y Espacios" (MEDIUM).
  `signal_strength` dimension = MEDIUM / MEDIUM.
- `hypotheses.potential_cluster = { value: "limpeza-energetica", canonical: true,
  basis: "existing" }`.
- `AssetMatch`: `best_playlist = pl_4oV5F1W2E6azZePnmqBanN` ("Limpieza Energética
  & Protección del Hogar" — inventory `cluster: Limpeza Energética`,
  `language: es`, `market: Mercados hispanohablantes`; candidate `fit: HIGH`,
  `fit_basis: OBSERVED`); `best_page = UNKNOWN` (0 matching own pages);
  `best_artist = art_7bnKOg3GDWAbLFtNhyn8Gw` ("Sonia Amor Divino" —
  `hero_artist: true`; `Limpeza Energética` in `secondary_clusters`; `fit: HIGH`,
  `role: hero`); `new_asset_recommendation = { asset_type: page,
  i5_conditions_met: {all four true} }`; `unmatched_reason`: *"No page asset
  exists matching the limpeza-energetica cluster for ES TikTok home-cleansing
  rituals."*
- `red_flags`: `compliance / MEDIUM` — *framing as "energetic cleansing" that
  "removes negative energy" risks a therapeutic claim (G03); reframe as
  intention/ritual/subjective (G02), flag for validation (G09)*;
  `evidence_gap / MEDIUM`; `asset_gap / LOW`.
- `hypotheses.potential_positioning`: *"Música ritual para limpiar
  energéticamente casas nuevas"*; `hypotheses.first_content_direction`: *"Video
  corto mostrando ritual de mudanza con música de limpieza energética de
  fondo"*; `hypotheses.hook`: *"Haz esto al mudarte a tu casa nueva"*.
- Owner authorization: `review.md` of `run_2026-08-31_01`,
  `advanced_opportunity_id = opp_2026-08-31_1bca4af972`.

### DERIVED DECISIONS (Cluster Strategy's output)

- **`cluster_decision = MAP_TO_EXISTING`; `cluster_id = limpeza-energetica`;
  `cluster_name = "Limpeza Energética"`.**
  `framing_hypothesis_comparison`: *"Confirmed. `cluster-taxonomy.md` defines
  Limpeza Energética as music for the 'limpeza / purificação energética de
  pessoas, ambientes e do lar, proteção espiritual', with 'proteção do lar' and
  'purificação do campo áurico' as named subclusters. The moving-into-a-new-home
  occasion sits inside that stated scope, and the cross-platform demand evidence
  (`sig_…_0014/0015/0016`) is all cluster-consistent. Boundary check passed
  against adjacent clusters: not Cura / Bem-estar (recuperação/restauração), not
  Frequência Divina / Espiritualidade (ativação, not limpeza), not Abundância
  (financial field)."*
- **`subcluster_or_angle = "energetic cleansing tied to the moving-in / new-home
  occasion"`; `is_new_subcluster = true`.** This is a new **angle/occasion inside
  an existing cluster**, not a new canonical cluster (`cluster-taxonomy.md`:
  angles are tactical/internal). **No `new_cluster_proposal`.** (Contrast: Run
  3's `opp_2026-09-01_92016b7992`, same theme, was framed
  `limpieza-energetica (proposed_new)` only because of the Spanish spelling — the
  §3.1-step-1 deterministic normalisation maps it to this same canonical cluster;
  it too would be `MAP_TO_EXISTING`, not a new cluster.)
- `central_concept`: *"Music that accompanies the ritual of energetically
  settling a home you have just moved into."*
- `audience`: *"Spanish-speaking people in the weeks around a house move who
  practice, or are curious about, home-cleansing rituals."* (base from
  `Opportunity.audience`; the "weeks around a move" attribute is a derived
  inference, labelled as such.)
- `intent`: *"soundtrack / accompany a moving-in ritual performed at home."*
- `emotional_state`: *"a fresh start; a felt sense of order, welcome and calm in
  the new space"* — **subjective experience (G02)**; not "removes negative
  energy".
- `editorial_promise`: *"a calming ritual to welcome and settle into your new
  home"* — **passes the guardrail check**; the rejected phrasing "limpia la
  energía negativa de tu casa" (as fact) is recorded in `open_questions` as a
  constraint for Content Strategy.
- `positioning_statement` (**R**): *"For Spanish-speaking people settling into a
  new home who want a calming moving-in ritual, this is instrumental music for
  the ritual of welcoming a new space — an occasion angle within our Limpeza
  Energética cluster, anchored on an existing es playlist and hero artist."*
- `localization_notes`: *"Concept is es-native; the moving-house ritual is
  culturally salient across hispanohablante markets. The existing playlist and
  hero anchor are already es/Mercados hispanohablantes — no cross-market
  borrowing. Target countries within es remain `NEEDS_INPUT` (business-dna
  §8)."*
- **Asset Strategy:**
  - `playlist_strategy`: `primary_playlist_id = pl_4oV5F1W2E6azZePnmqBanN`
    (**reuse — I5 default**; `playlist_fit_basis = OBSERVED`).
    `new_playlist_recommendation = null`. `reuse_rationale`: *"an existing es
    Limpeza Energética playlist covers exactly this cluster/market."*
  - `page_strategy`: `primary_page_id = UNKNOWN`; `new_page_recommendation` =
    carried verbatim (`asset_type: page`, four I5 conditions true). `note`: *"the
    page's name, bio, visual identity and cadence are Page Blueprint's (stage 4)
    — Cluster Strategy only records that a new es Limpeza Energética page is
    warranted and that it should anchor on `pl_4oV5F1W2E6azZePnmqBanN` +
    `art_7bnKOg3GDWAbLFtNhyn8Gw`."*
  - `artist_strategy`: `anchor_hero_artist_ids = [art_7bnKOg3GDWAbLFtNhyn8Gw]`;
    `best_artist_id = art_7bnKOg3GDWAbLFtNhyn8Gw`; `catalog_affinity_artist_ids`
    = the other artists whose consolidated clusters relate (from
    `AssetMatch.matching_artists`); the full hero roster is noted eligible
    (§10.2a).
  - `market_language_fit`: `rating = HIGH`, `confidence = MEDIUM`,
    `justification`: *"an existing es playlist and an es-market hero artist sit
    in exactly this cluster; capped at MEDIUM because playlist
    follower/performance data is UNKNOWN and musical-DNA detail is
    NEEDS_INPUT."*
  - `asset_gaps`: *"No `own` page targets es Limpeza Energética (from
    `AssetMatch.unmatched_reason`)."*
- **Evaluation:** `cluster_fit` HIGH / HIGH; `differentiation_within_cluster`
  MEDIUM / LOW (*"the occasion angle is distinct, but competitor content already
  exists on YouTube and Spotify per `sig_…_0015/0016`"*); `asset_readiness`
  MEDIUM / MEDIUM (*"playlist + hero yes; own page no"*); `strategic_coherence`
  HIGH / MEDIUM (*"core canonical cluster; a recurring life-event occasion;
  serves the funnel per business-dna §4"*).
  `overall_confidence = LOW` — **carried from the Opportunity; not raised by
  `cluster_fit: HIGH`** because the underlying demand evidence is still thin
  (`evidence_gap / MEDIUM` on the opportunity).
- `red_flags`: `compliance / MEDIUM` (carried; the prose was written to clear it,
  the constraint is logged), `evidence_gap / MEDIUM` (carried).

### HYPOTHESES (non-binding — carried / lightly refined)

- `first_content_direction` (**H**): *"a short vertical video showing a moving-in
  ritual with the cluster's music underneath"* (from
  `hypotheses.first_content_direction`).
- `editorial_angles` (**H**): `["the first night in the new home", "room-by-room
  settling", "before the furniture arrives"]` — tactical, for Content Strategy to
  test.
- `music_relationship` (**D**, confidence-capped): *"ambient background to a slow
  ritual gesture; specific sonic criteria (instrumentation, BPM, texture, use of
  frequencies) are `NEEDS_INPUT` (business-dna §9)."*

### RECOMMENDATIONS

- `target_next_stage = PAGE_BLUEPRINT` (**R**) — *"a new es Limpeza Energética
  page is warranted (I5 conditions met upstream); Page Blueprint designs it,
  anchored on `pl_4oV5F1W2E6azZePnmqBanN` and `art_7bnKOg3GDWAbLFtNhyn8Gw`."*
- `recommended_next_step` (**R**): *"Proceed to Page Blueprint for a
  Spanish-language Limpeza Energética page focused on the moving-in occasion;
  keep all copy on ritual / intention / welcome, never on 'removing negative
  energy' as fact."*
- `opportunity_lifecycle_state = EXPLORE` — carries the opportunity's real
  registry `status` **unchanged** (never the Market Intelligence `target_state`
  recommendation; the owner marking the opportunity `advance` in `review.md`
  authorises stage 3, it does not transition the lifecycle). Cluster Strategy
  never transitions the lifecycle (I2, autonomy L1).
- `execution_note`: *"V1 does not execute this action; it requires human
  approval."*
- `open_questions` (**D**): (1) *"platform: the opportunity's `platform` is
  `tiktok`, but the demand evidence spans YouTube and Spotify — Page Blueprint /
  owner to decide the page's platform(s)."* (2) *"does the moving-in occasion
  warrant a dedicated page, or a content pillar inside a broader es Limpeza
  Energética page? (Page Blueprint / owner)."* (3) *"the phrase 'limpia la
  energía negativa' as fact is disallowed (compliance/MEDIUM) — Content Strategy
  must frame all cleansing language as ritual/intention."*

---

# 13. ARCHITECTURAL BOUNDARY

| Stage | Question it answers | **Produces** | **Must NOT produce** |
|---|---|---|---|
| **Market Intelligence + Opportunity Analysis** (stages 1–2 — *built*) | *"Which opportunities exist, and which deserve our attention?"* (C7) | Discovery of opportunities; typed evidence + provenance; the 10-dimension qualitative evaluation + the 5-axis Business Outcome Profile; ranking / Top-10; `AssetMatch` (fit with **existing** assets); an operational `Recommendation` (`target_state` ∈ EXPLORE/TEST/PARK + `suggested_next_step`). **Light, non-binding hypotheses** about cluster, positioning, page, first content direction. | A confirmed cluster; a strategic cluster definition; a page; any content. |
| **CLUSTER STRATEGY** (stage 3 — *this contract*) | *"Does this owner-approved opportunity map to an existing canonical cluster, a subcluster/angle, or a proposed new cluster — and what is the cluster's strategic definition and asset strategy?"* | The **cluster decision** (`MAP_TO_EXISTING` / `PROPOSE_NEW_CLUSTER` / `DEFER` / `REJECT`) + justification vs the taxonomy boundary; the **strategic cluster definition** (concept, audience, intent, emotional register, editorial promise, positioning statement, localization notes, durability read, strategic coherence); the **cluster-level asset strategy** (playlist reuse / page recommendation carried / hero + candidate artist anchors / market-language fit / gaps — **no asset invented**); **one** non-binding first content direction + candidate angles + music role; qualitative confidence + carried compliance flags + open questions; a **recommended next stage**. A **new-cluster *proposal*** (hypothesis + hand-off to the owner — P6 still deferred). | **Any page design** (name, bio, visual identity, tone of voice, cadence — Page Blueprint). **Any content system** (pillars, formats, hooks, structures, CTA copy, linguistic/visual rules, frequency, variations, templates — Content Strategy). Any 0–100 score. Any lifecycle transition. Any write to `cluster-taxonomy.md` or the inventories. Any new canonical cluster (formalization = owner + P6). |
| **Page Blueprint** (stage 4 — *deferred, P4*) | *"Given the cluster (or the new-page recommendation), what is the concrete page?"* | Page concept name, bio, language, market, **visual identity**, **tone of voice**, associated playlist + artist, platform(s), posting cadence, content pillars *for that page*. (Business DNA V1 §12.) | The content system detail; the content objects. |
| **Content Strategy** (stage 5 — *deferred, P4*) | *"Given the page, what is the reusable content system?"* | Pillars, formats, **hooks**, structures, styles, **CTAs**, linguistic rules, visual rules, frequency, variation design, the `CONTENT_OBJECT` schema. (Business DNA V1 §13–§15.) | Content production, video, audio, publishing. |

**The precise seam Cluster Strategy sits on:** it turns the opportunity's cluster
**hypothesis** into a cluster **decision** and gives that cluster a **strategy** —
audience, intent, emotion, positioning, asset anchors — that is stable,
evidence-separated, and guardrail-clean. It hands Page Blueprint a confirmed
cluster + a positioning statement + the anchor assets + the (carried) page
recommendation, and **stops before** deciding what the page looks like or what it
posts.

---

# 14. IMPLEMENTATION

### Packaging

A **new sibling package `src/cluster_strategy/`** (stage 3 is a distinct pipeline
stage; keeping it inside `market_intelligence` would conflate stages 1–2 with 3,
against C8's "conceptually separate for modularity"). It **imports, does not
modify** the following existing modules (no refactor of V1 code):

- `market_intelligence.schema.{enums, models, codec}` — shared vocab (`Rating`,
  `Confidence`, `Severity`, `RedFlag`, `Market`, `Language`, `Durability`,
  `Urgency`, `LifecycleState`, `NewAssetRecommendation`, `Provenance`).
- `market_intelligence.knowledge_loader` — `load_knowledge` / `KnowledgeBundle`.
- `market_intelligence.llm_stage` — the injectable `StageClient` /
  `RecordedStageClient` / `AnthropicStageClient` + `call_stage` +
  `<fixture_path>/llm/<stage>/<key>.json` replay convention.
- `market_intelligence.guardrails` — `check_texts`, `ComplianceResult`, the
  scanners.
- `market_intelligence.io_utils` — `read_yaml` / front-matter / `write_text` /
  `write_json`.
- `market_intelligence.schema.validate.scan_json_for_numeric_score` — the C6 "no
  score" scanner.
- `market_intelligence.config.loader` / `RunPaths` pattern — for the new config.
- `market_intelligence.gate.parse_review` — the owner-authorization check.

*(Future cleanup — not now: extract the shared modules into a `src/engine_core/`
package both stages depend on. Flagged, not done.)*

### Modules

| File | Purpose |
|---|---|
| `src/cluster_strategy/__init__.py`, `__main__.py` | package + `python -m cluster_strategy` |
| `src/cluster_strategy/cli.py` | `python -m cluster_strategy <opportunity-report.json>`; `--config`, `--review`, `--project-root` |
| `src/cluster_strategy/config.py` | `ClusterStrategyConfig` + `CSReplayConfig` + `load_config` (spec §14 style) |
| `src/cluster_strategy/schema/models.py` | dataclasses: `ClusterStrategy`, `ClusterDecision`, `NewClusterProposal`, `ClusterStrategicDefinition`, `ClusterAssetStrategy` (`PlaylistStrategy`/`PageStrategy`/`ArtistStrategy`), `ClusterContentDirection`, `ClusterDimensionRating`, `ClusterEvaluation`, `ClusterRecommendation`, `ClusterStrategyProvenance`, `OpportunitySnapshot` |
| `src/cluster_strategy/schema/enums.py` | `ClusterDecisionKind`, `TargetNextStage`, `ClusterDimensionKey` (+ constants) |
| `src/cluster_strategy/schema/validate.py` | `validate_cluster_strategy(...)` + `scan_for_scope_leakage(...)` (a **key-name** denylist for stage-4/5 field names): `cluster_id ∈ canonical`; every asset id ∈ inventory; `schema_version` pin; no-0–100-score (reused scanner); `overall_confidence ≤ opportunity`; `new_cluster_proposal` completeness; dimension-key set; fixed-note tampering; `opportunity_lifecycle_state == opportunity.status`; a soft `editorial_angles` length WARNING (§8) |
| `src/cluster_strategy/input_loader.py` | load `<opportunity_id>.json` → `OpportunitySnapshot` + full `AssetMatch`/`Evaluation`; hard-fail on `schema_version != 1.0.0`, on zero OBSERVED evidence, on "opportunity not the advanced one in `review.md`" |
| `src/cluster_strategy/mapping.py` | deterministic: alias/spelling/language normalisation of `potential_cluster.value` against the 11 canonical ids + taxonomy aliases; `load_taxonomy_markdown` |
| `src/cluster_strategy/strategy.py` | the Claude sub-step (via `llm_stage`): cluster decision + strategic definition + new-cluster proposal + content direction + dimension ratings + red-flag self-check; `reject_malformed_strategy` strict parser |
| `src/cluster_strategy/asset_strategy.py` | deterministic consolidation of the opportunity's `AssetMatch` into the cluster-level asset strategy (introduces no new asset judgement) |
| `src/cluster_strategy/guardrails.py` | `check_cluster_strategy_prose(...)` — field→scope map over `market_intelligence.guardrails` |
| `src/cluster_strategy/llm.py` | re-exports MI stage plumbing; lenient `_extract_json_object`; `AnthropicClusterStrategyClient` (non-structured); `select_client` |
| `src/cluster_strategy/reporting.py` | render `reports/cluster-strategy/<opportunity_id>.md` (front matter + sections, Observed/Derived/Hypotheses/Recommendations visually separated) + `.json` sidecar |
| `src/cluster_strategy/registry_link.py` | D-CS-7 — **opt-in** (`write_registry_link`, default `False`): append `cluster_strategy_ref` + one `state_history` note to the opportunity's registry entry, append-only, `status` untouched; idempotent; no-op if the registry file is absent |
| `src/cluster_strategy/orchestrator.py` | deterministic driver: input_loader → mapping pre-checks → strategy (Claude) → asset_strategy → guardrails (exclude / strip_scopes / uncertainty) → assemble → validate → render → (opt-in) registry link; `ClusterStrategyError` on hard fail |
| `config/cluster-strategy.example.yaml` | model, `prompt_version`, paths, `replay` block |

### Claude-vs-deterministic split (spec §19)

*Claude decides what the cluster is and how strong the fit is; deterministic code
decides whether the output is well-formed, traceable, scoped, and asset-honest.*
One new pipeline stage, one Claude sub-step (`strategy.py`), no multi-agent
orchestration (I8, P5).

### Tests (TDD, `pytest` — spec §22)

- `test_cluster_strategy_input_loader.py` — valid sidecar loads; `schema_version`
  mismatch → hard fail; not-advanced opportunity → refused; zero OBSERVED
  evidence → refused.
- `test_cluster_strategy_mapping.py` — `limpieza-energetica` (es) → canonical
  `limpeza-energetica`; `Sono Restaurador` → `sono`; the moving-in-ritual angle
  does **not** trigger `PROPOSE_NEW_CLUSTER`.
- `test_cluster_strategy_validate.py` — non-canonical `cluster_id` → error; a
  `85/100` anywhere in prose → error; an invented `playlist_id` → error;
  `new_cluster_proposal` missing `boundary_vs_adjacent` → error; a `pillars` /
  `visual_identity` key present → scope-leakage error; `overall_confidence` above
  the opportunity's → error.
- `test_cluster_strategy_asset_strategy.py` — consolidation never introduces an
  asset absent from the opportunity's `AssetMatch` / inventory; hero roster
  always eligible (§10.2a); `reference_competitor` pages never become a
  recommended page.
- `test_cluster_strategy_guardrails.py` — "removes negative energy" as fact →
  `compliance` red flag + reframe requirement; naming the topic "energetic
  cleansing" alone → no flag (claims-not-topics calibration preserved).
- `test_cluster_strategy_models.py` / `_reporting` (golden) — all sections
  present + front matter complete + Observed/Derived/Hypotheses/Recommendations
  visually separated; JSON sidecar round-trips through `codec`.
- `test_cluster_strategy_orchestrator.py` — recorded-replay end-to-end on
  `opp_2026-08-31_1bca4af972` (the §12 example) → `MAP_TO_EXISTING
  limpeza-energetica`, no invented asset, no score, compliance flag carried; the
  stage writes nothing under `knowledge/` except the registry append.
- `test_cluster_strategy_decision_branches.py` — the DEFER / PROPOSE_NEW_CLUSTER
  / forced-REJECT branches on the same input with different recorded responses.
- `test_cluster_strategy_registry.py` — append-only `cluster_strategy_ref`,
  `status` unchanged, idempotent, no-op without a registry file.
- `test_cluster_strategy_cli.py` — runs the stage; reports a bad config; nonzero
  on a run failure.

### Fixtures

- `tests/fixtures/cluster_strategy/` (+ `_defer/`, `_propose/`, `_reject/`) —
  recorded LLM responses keyed
  `llm/cluster_strategy/cluster_strategy__<opportunity_id>.json`.
- Input fixture: the committed `reports/run_2026-08-31_01/opp_2026-08-31_1bca4af972.json`.

### Integration points

- **In:** `reports/<run_id>/<opportunity_id>.json` (Opportunity Report sidecar —
  spec §23 contract) + `reports/<run_id>/review.md` (owner `advance`) + the
  knowledge base (existing loader).
- **Out:** `reports/cluster-strategy/<opportunity_id>.md` + `.json` (D-CS-6). No
  per-run digest in V1-of-stage-3 (one opportunity at a time).
- **Registry (D-CS-7) — OPT-IN, off by default.** `write_registry_link` defaults
  to `False` (`ClusterStrategyConfig`, and the example config). A normal or
  offline run **does not touch `knowledge/`**. Only when a config or the owner
  sets it `True` does the run append `cluster_strategy_ref` + one `state_history`
  note (`by: system`, `to:` = the **unchanged** status) to the opportunity's
  `opportunity-registry.yaml` entry, via the same append-only mechanism as
  `market_intelligence.registry` — idempotent, existing entries keep their order,
  every change visible in `git diff`.
- **Downstream:** the `ClusterStrategy` sidecar is Page Blueprint's input
  contract (stage 4).
- **Governance hand-off:** a `PROPOSE_NEW_CLUSTER` output is a hand-off to the
  owner (P6); the pipeline never edits `cluster-taxonomy.md`. If the owner
  formalizes, that is a manual edit of `cluster-taxonomy.md` (and, per I6, a
  per-cluster definition file under `knowledge/clusters/`).
- **Decision record:** opening the stage is decision **D-CS-1**, recorded in
  `knowledge/DECISIONS-NEEDED.md` §4 (with P4 updated). If the owner later
  formalizes a proposed cluster, that is a separate manual edit of
  `cluster-taxonomy.md` — a Claude session never edits that file.

---

# 15. OPEN DECISIONS — DECIDED 2026-09-01 (`DECISIONS-NEEDED.md` §4 is authoritative)

**On 2026-09-01 the owner opened canonical stage 3 and decided every decision
below at its *Recommendation* answer.** They are recorded in
`knowledge/DECISIONS-NEEDED.md`, section **"# 4. ESTÁGIO 3 — CLUSTER STRATEGY"**
(D-CS-1 … D-CS-12), with P4 updated to *"estágio 3 aberto; estágios 4–13 seguem
DEFERRED"*. The table below mirrors those decisions for the reader; the decision
log is the authoritative record. No substantive implementation or contract
decision changed in the recording.

| # | Decision | Why it could not be inferred | Decision (D-CS, 2026-09-01) |
|---|---|---|---|
| **D-CS-1** | Authorize opening canonical stage 3 (Cluster Strategy). | P4 was `DEFERRED`, owner-decided. The C10 gate (its stated precondition) passed — but "open the stage" is an explicit owner action. | **Stage 3 opened**, scoped to Cluster Strategy only (stages 4–13 stay deferred under P4). Recorded as D-CS-1 + the P4 update in `DECISIONS-NEEDED.md` §4. |
| **D-CS-2** | Does Cluster Strategy get P6 (formal new-cluster governance) opened, or stay "propose-only"? | P6 is `DEFERRED`. A `proposed_new` opportunity cannot fully advance if Cluster Strategy can only propose, not formalize. | **P6 stays deferred.** Cluster Strategy **proposes** a new cluster (hypothesis + boundary + evidence); the owner formalizes manually in `cluster-taxonomy.md` when convinced; such opportunities get `cluster_decision = DEFER` (`FORMALIZE_CLUSTER`) until formalized. |
| **D-CS-3** | Trigger — which opportunities enter Cluster Strategy, and how is the stage invoked? | Neither the spec nor Business DNA V1 defines the hand-off mechanism; autonomy L1 + I12 imply the human selects. | **Explicit, per-opportunity, owner-invoked CLI** (`python -m cluster_strategy reports/<run_id>/<opportunity_id>.json`); refuse if the opportunity is not the `advanced_opportunity_id` in that run's `review.md`. No batch / automatic run. |
| **D-CS-4** | The Cluster Strategy dimension key set, and whether the stage has a persistent `status`. | C9 fixes the *opportunity* dimensions; there is no decided list for a cluster strategy. | **Dimensions:** `cluster_fit`, `differentiation_within_cluster`, `asset_readiness`, `strategic_coherence` (qualitative + separate confidence, no score). **No** persistent `status` field — a re-run overwrites the report (idempotent). |
| **D-CS-5** | Content-direction depth. | Business DNA V1 §11 lists pillars / aesthetics / CTA as cluster-strategy outputs; C8 + `cluster-taxonomy.md` put them in stages 4–5. | **Shallow.** Cluster Strategy produces **only**: one non-binding `first_content_direction`, a short `editorial_angles` list, and a `music_relationship` role statement. Pillars, formats, hooks, CTAs, visual language, cadence → Content Strategy / Page Blueprint. |
| **D-CS-6** | Output location and whether a per-run digest exists. | I7 (`reports/` = durable) applies; the exact path and whether stage 3 emits a digest are undecided. | `reports/cluster-strategy/<opportunity_id>.md` + `.json`. **No digest** in V1-of-stage-3 (one opportunity at a time); the report is the deliverable. |
| **D-CS-7** | Does Cluster Strategy touch `opportunity-registry.yaml`? | The registry is a governance exception (spec §17), append-only, human-reviewed; adding a `cluster_strategy_ref` is a schema extension. | **Yes, but OPT-IN.** When explicitly enabled (`write_registry_link: true` — **default `false`**), append a `cluster_strategy_ref` (and a `state_history` note `by: system`, status unchanged) to the opportunity's registry entry, using the exact append-only mechanism of `market_intelligence.registry` — every change visible in `git diff`. A normal / offline run leaves the registry untouched. Until D-CS-7 is recorded in `DECISIONS-NEEDED.md`, keep it off. |
| **D-CS-8** | Confirm the stage boundary against Business DNA V1 §11. | Business DNA V1 §11 explicitly puts *linguagem, estética, conteúdo, CTA* in "Cluster Strategy"; the established V1 architecture puts them in stages 4–5. A direct document divergence, not a gap. | **Confirm the established boundary** (this contract): Cluster Strategy = cluster concept + audience + intent + emotion + positioning + music/playlist relationship + one non-binding content direction. Everything Business DNA V1 §11 lists beyond that is stage 4/5. |
| **D-CS-9** | Is a `NEEDS_INPUT` musical DNA an acceptable state for Cluster Strategy to run in? | `business-dna.md` §9 musical DNA detail is `NEEDS_INPUT`; it structurally caps `music_relationship` and `market_language_fit` confidence. | **Acceptable** — run with the confidence cap and a `blocked_by` note, same as the pipeline caps `music_fit`. Cluster Strategy names *what* would need musical-DNA detail, does not invent it. |
| **D-CS-10** | Value-engine weighting is still `NEEDS_INPUT`. | `business-dna.md` §4; `config/ranking.yaml: value_engine_weighting: NEEDS_INPUT`. If Cluster Strategy ever prioritizes multiple angles, it needs a rule. | **V1-of-stage-3 does not prioritize** (one opportunity in, one strategy out). If multi-angle prioritization is later added, it stays ordinal-only (C6) until the owner provides weighting. |
| **D-CS-11** | Contract-version handling. | The Opportunity Report `schema_version` is `1.0.0`; behaviour on a future mismatch is undecided. | **Pin to `schema_version == 1.0.0` and hard-fail** on any other value (surfacing the divergence, per Engineering Rule #9), rather than guessing. |
| **D-CS-12** | Naming reconciliation. | Business DNA V1 §5/§28 say "Opportunity Discovery" / "Cluster Strategist" / "Distribution"; C8 says "Opportunity Analysis" / "Publishing". Minor, non-blocking. | **Use the C8 canonical names** (`Cluster Strategy`, stage 3). No document edits; the divergence is noted here. |

---

# A. Cluster Strategy V1 — Contract summary

- **Identity in the pipeline:** canonical stage 3 (C8). Consumes **one
  owner-advanced `OpportunityReport`** (the `<opportunity_id>.json` sidecar,
  `schema_version 1.0.0`). Produces **one `ClusterStrategy`** (Markdown + YAML
  front matter + JSON sidecar, `schema_version 1.0.0`) at
  `reports/cluster-strategy/<opportunity_id>.*`. Autonomy **Level 1** — recommend
  only; the `execution_note` is fixed.
- **Cluster decision:** `MAP_TO_EXISTING` (one of the 11 canonical ids,
  confirming or overriding the opportunity's hypothesis against the taxonomy
  boundary; new subcluster/angle allowed and expected) · `PROPOSE_NEW_CLUSTER`
  (hypothesis + `boundary_vs_adjacent` for every adjacent cluster +
  `why_not_subcluster` + evidence refs + fixed governance note — **P6 stays
  deferred; the pipeline never edits `cluster-taxonomy.md`**) · `DEFER` (needs P6
  / more evidence / unresolved ambiguity) · `REJECT` (untenable — HIGH compliance
  flag or no coherent cluster). Deterministic pre-normalisation of
  spelling/language/alias variants (`limpieza-energetica` es → canonical
  `limpeza-energetica`) prevents artificial clusters.
- **Strategic definition:** `central_concept`, `audience` (refined,
  evidence-typed), `intent`, `emotional_state` (subjective experience, G02),
  `editorial_promise` (guardrail-clean), `positioning_statement` (recommendation),
  `localization_notes`, `durability_read`, `strategic_coherence_note`.
- **Asset strategy (never invent — I1):** playlist reuse by default (I5); page
  recommendation **carried verbatim** from `AssetMatch` (design is Page
  Blueprint's); hero + candidate artist anchors (hero roster always eligible,
  §10.2a); `market_language_fit` (rating + separate confidence, **no score**,
  confidence-capped while musical DNA / classification backlog are
  `NEEDS_INPUT`); `asset_gaps` from the inventory.
- **Content direction (shallow):** one non-binding `first_content_direction` (H),
  `editorial_angles` (H), `music_relationship` (D, capped) + the fixed
  `content_boundary_note`. **No pillars / formats / hooks / CTAs / visual
  language / cadence.**
- **Confidence / evidence:** 4 qualitative dimensions (`rating` + **separate**
  `confidence`), `overall_confidence` ≤ the opportunity's and not raised by high
  sub-ratings (C6), carried + re-checked `red_flags`, `open_questions`. **No
  0–100 score anywhere** (validator-enforced).
- **States:** no `LAUNCH/SCALE/KILL`; `opportunity_lifecycle_state` carries the
  opportunity's actual registry `status` (`EXPLORE`/`TEST`/`PARK`), **not** the MI
  `target_state` recommendation, and never transitions it (validator-enforced);
  two non-lifecycle vocabularies — `cluster_decision` and `target_next_stage`
  (`PAGE_BLUEPRINT` / `FORMALIZE_CLUSTER` / `BACK_TO_MARKET_INTELLIGENCE` /
  `HOLD`).
- **Guardrails:** loads `guardrails.yaml` (G01–G10); reuses
  `guardrails.check_texts`; applies the **full** `ComplianceResult` the way MI
  does — `exclude_opportunity` → REJECT, `strip_scopes` → blank the offending
  hypothesis field, `needs_uncertainty_note` → an open question; inherits the
  **claims-not-topics** calibration; `UNKNOWN`/`NEEDS_INPUT` never guessed (G10,
  spec §15).
- **Registry link:** OPT-IN, `write_registry_link` default `False` — a normal or
  offline run never writes under `knowledge/`.
- **Provenance:** full traceability chain carried from the Opportunity Report
  (`signal_ids → Signal.provenance → raw capture`); `model`, `prompt_version`,
  `generated_at`, `replay` recorded; `replay: true` inputs flagged "not
  current-trend evidence".

# B. Architecture Boundary

**Market Intelligence (1–2):** *which opportunities, and which matter* —
discovery, evidence, evaluation, ranking, existing-asset fit, a recommended next
action, **light hypotheses only**. → **Cluster Strategy (3):** *confirm the
cluster; define the cluster's strategy and asset anchors* — turns the cluster
**hypothesis** into a **decision** + a positioning + anchor assets + the carried
page recommendation; **stops before page design and content**. → **Page Blueprint
(4):** *what the page is* — name, bio, visual identity, tone of voice, cadence,
page-level pillars. → **Content Strategy (5):** *the reusable content system* —
pillars, formats, hooks, structures, CTAs, linguistic/visual rules, frequency,
variations, the content-object schema.

Enforced deterministically by `cluster_strategy.schema.validate`, which combines
several checks over the encoded `ClusterStrategy`:

- **`scan_for_scope_leakage`** — a **key-name** denylist: it walks the encoded
  object and flags any dict key that belongs to Page Blueprint / Content Strategy
  (`visual_identity`, `tone_of_voice`, `bio`, `pillars`, `content_pillars`,
  `formats`, `hook_library`, `hooks`, `structures`, `cta_copy`, `captions`,
  `posting_frequency`, `cadence`, `schedule`, `batch_size`, `templates`,
  `template`, `variations`, `content_object`, `linguistic_rules`,
  `visual_rules`). This is a regression guard — the dataclass models carry none
  of these, so the shared codec already rejects a rogue field on decode.
- **`scan_json_for_numeric_score`** (reused from Market Intelligence) — fails on
  any `N/100`, `N out of 100`, or `score: N` pattern anywhere in the encoding (C6).
- **asset honesty** — every `*_id` must resolve in the inventory (`UNKNOWN` /
  `NEW_ASSET` sentinels aside); a `reference_competitor` page can never be the
  recommended page.
- **fixed-disclaimer tamper checks** — the content-boundary note, the
  catalog-affinity note, the P6 governance note, and the execution note must be
  byte-exact.
- **lifecycle not transitioned** — `recommendation.opportunity_lifecycle_state`
  must equal `opportunity_snapshot.status`.

There is **no explicit `LAUNCH/SCALE/KILL` value scan** — those values are
structurally impossible: the `TargetNextStage` enum has no lifecycle values, and
`opportunity_lifecycle_state` carries the opportunity's own already-constrained
`status` (`EXPLORE`/`TEST`/`PARK`, I2).

# C. Owner Decisions (DECIDED 2026-09-01)

D-CS-1 open stage 3 (P4 updated) · D-CS-2 new-cluster governance stays
propose-only (P6 deferred) · D-CS-3 owner-invoked, per-opportunity, advance-gated
trigger · D-CS-4 dimension key set + no persistent status · D-CS-5 shallow content
direction only · D-CS-6 output path, no digest · D-CS-7 registry link
(`cluster_strategy_ref`), opt-in · D-CS-8 confirm the boundary vs Business DNA V1
§11 · D-CS-9 run with musical-DNA `NEEDS_INPUT` + confidence cap · D-CS-10 no
multi-angle prioritization in V1 · D-CS-11 hard-fail on `schema_version` mismatch ·
D-CS-12 use C8 canonical names.

**All twelve are DECIDED (2026-09-01) and recorded in
`knowledge/DECISIONS-NEEDED.md` §4** ("# 4. ESTÁGIO 3 — CLUSTER STRATEGY"), with
P4 updated. That decision log is the authoritative record; §15 mirrors it.

# D. Implementation Plan (executed 2026-09-01)

1. Owner opened stage 3 and decided **D-CS-1 … D-CS-12** at the recommended
   answers; recorded in `DECISIONS-NEEDED.md` §4 with P4 updated.
2. New package **`src/cluster_strategy/`** (sibling of `market_intelligence`),
   importing — not modifying — `market_intelligence.{schema, knowledge_loader,
   llm_stage, guardrails, io_utils, config, gate}`.
3. Modules: `schema/{models,enums,validate}.py` · `input_loader.py` ·
   `mapping.py` (deterministic) · `strategy.py` (one Claude sub-step via
   `llm_stage`) · `asset_strategy.py` (deterministic) · `guardrails.py` ·
   `llm.py` · `reporting.py` · `registry_link.py` · `orchestrator.py` ·
   `cli.py` · `config.py` · `config/cluster-strategy.example.yaml`.
4. TDD, `pytest`, recorded-replay for the Claude sub-step
   (`<fixture_path>/llm/cluster_strategy/<key>.json`), fixture input =
   `opp_2026-08-31_1bca4af972.json`; a `no-knowledge-write` guarantee and a
   `scope-leakage` guarantee as hard tests.
5. Deliverable: `reports/cluster-strategy/<opportunity_id>.{md,json}` — the JSON
   sidecar is Page Blueprint's future input contract. `PROPOSE_NEW_CLUSTER`
   outputs are hand-offs to the owner (P6), never taxonomy edits.
6. Future cleanup (flagged, not now): extract the shared modules into
   `src/engine_core/`.

---

## Implementation status (2026-09-01)

- `src/cluster_strategy/` package built end-to-end, TDD, `ruff` clean, full suite
  green (zero regressions in the stage-1–2 tests).
- All three cluster decisions plus the forced-`REJECT` path are exercised
  end-to-end with recorded fixtures (`tests/fixtures/cluster_strategy*/`), and so
  are the compliance-strip and red-flag-dedup paths.
- The stage runs offline via recorded replay; a live run needs
  `ANTHROPIC_API_KEY` (same Keychain-wrapper convention as the pipeline — never
  Claude Code's OAuth).
- **Uncommitted** — commit-ready, awaiting the owner's commit. No change to any
  stage-1–2 code file, `CLAUDE.md`, `cluster-taxonomy.md`, `guardrails.yaml`, the
  inventories, or `business-dna/*`.
- **Authoritative decisions recorded (2026-09-01):** `knowledge/DECISIONS-NEEDED.md`
  gains section **"# 4. ESTÁGIO 3 — CLUSTER STRATEGY"** (D-CS-1 … D-CS-12, all
  `DECIDED (2026-09-01)`) and its P4 entry is updated to *"estágio 3 aberto;
  estágios 4–13 seguem DEFERRED"*. `docs/TECHNICAL-SPEC-V1.md` §17 gains one
  sentence sanctioning the opt-in stage-3 `cluster_strategy_ref` append.

### Post-review fixes (2026-09-01, spec-consistency reviewer)

- `opportunity_lifecycle_state` now carries the opportunity's real registry
  `status` (`OpportunitySnapshot.status`), not the MI `target_state`
  recommendation; the validator check compares against `status`.
- Deterministic guardrail escalation now applies the full `ComplianceResult` —
  `strip_scopes` blanks the offending content-direction hypothesis;
  `needs_uncertainty_note` becomes an open question — matching the MI Evaluation
  stage, not only `exclude_opportunity`.
- `write_registry_link` defaults to `False`; the example config sets it `false`.
  A normal / offline run does not mutate `knowledge/`.
- Contract reconciled: O/D/H/R attribution is the `.md` report's job, not a
  per-field JSON tag; §B describes what `scan_for_scope_leakage` actually checks
  (dict keys) and that `LAUNCH/SCALE/KILL` is structurally impossible, not
  scanned.
- `_MAX_EDITORIAL_ANGLES` wired as the soft `editorial_angles` length WARNING it
  documented; `_red_flags` dedup replaced its fuzzy 40-char substring match with a
  normalised exact-match key (an exact restatement collapses; a distinct flag is
  never dropped).
- **Close-out (2026-09-01):** the D-CS decisions are now recorded authoritatively
  in `DECISIONS-NEEDED.md` §4 with P4 updated, and spec §17 sanctions the opt-in
  registry append. The "Status" header, Preamble, §15, §A/§C/§D and this footer
  were revised from "provisional / pending" to the now-authoritative "DECIDED
  2026-09-01" state. `strategy.py` was updated to send the opportunity's real
  `status` to the prompt alongside the (clearly labelled) MI `target_state`
  recommendation. No substantive implementation or contract decision changed.
