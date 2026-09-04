# OMR-03 — Normalization Benchmark Report

> **Conclusion: D — INCONCLUSIVE, confirmed across two runs.** See §21/§22 and
> the **Run 2** section at the end of this document. Governing decision:
> `knowledge/DECISIONS-NEEDED.md` OMR-03 (commit `ca95573`, Threshold Policy
> V1, BALANCEADA). This report does not alter that policy.
>
> **Run log:**
> - **Run 1** (`run_20260904T202402658296+0000`, §1–§23 below) — Claude
>   blocked by an Anthropic account billing error on all 4 calls.
> - **Run 2** (`run_20260904T203604499438+0000`, see the dedicated section at
>   the end) — re-run requested after the user reported the billing issue
>   resolved. **The exact same billing error recurred on all 4 Claude calls.**
>   No Claude-vs-Groq comparison exists yet. Run 1's sections below are
>   preserved unmodified as the historical record of that run.

Legend used throughout: **FACT** (directly observed, reproducible from the
artifacts in this directory) · **OBSERVATION** (a pattern noticed in the FACTs)
· **INFERENCE** (a reasoned conclusion drawn from OBSERVATIONs — could be wrong)
· **RECOMMENDATION** (a suggested next step — not a decision).

---

## 1. Executive Summary

**FACT.** A benchmark harness was built and run once, live, against 4 dataset
cases (all inherited from the existing repository test fixture
`tests/fixtures/normalize/llm/ambiguous_signals.json`), producing 5 field-level
evaluation points. Claude failed on **all 4 calls** with a billing error
(`"Your credit balance is too low to access the Anthropic API"`) before
generating any content. Groq (`openai/gpt-oss-120b` via OmniRoute) completed 3
of 4 calls successfully and had 1 whole-response rejection (a `signal_id` typo
by the model). **No Claude-vs-Groq comparison could be produced** — every
comparative verdict is `INCONCLUSIVE`.

**RECOMMENDATION.** Do not treat this run as evidence for or against using Groq
for Normalization. Re-run once (a) Anthropic billing is resolved and (b) a
dataset meeting the previously-proposed minimum size (~150 cases with
independent human ground truth) exists.

---

## 2. Objective

Determine whether `groq/openai/gpt-oss-120b` via OmniRoute is good enough for
Signal Normalization to justify considering a future integration — per OMR-02
(candidate approved) and OMR-03 Threshold Policy V1 (`ca95573`, BALANCEADA).

## 3. Scope

Signal Normalization only (4 fields: `signal_type`, `market`, `language`,
`durability_hint`). Does not touch Asset Matching (OMR-02's secondary,
conditional candidate) or any other stage.

## 4. Architecture

```
Claude/Anthropic                    Groq/openai/gpt-oss-120b
      |  baseline                          |
      v                                     v
market_intelligence.normalize.llm    OmniRoute (localhost:20128/v1)
AnthropicNormalization (existing,           |
unmodified)                                 v
      |                              external_llm_gateway.OmniRouteStageClient
      v                              (existing, unmodified)
      +---------------- benchmark/omr03/harness.py ----------------+
                     (both -> validate_llm_response, unmodified)
                                    |
                                    v
                       benchmark/omr03/results/*.json
```

**FACT.** `benchmark/omr03/` imports `market_intelligence.normalize.llm` and
`external_llm_gateway` — the dependency runs one way, same as OMR-01/OMR-02.
Nothing in `market_intelligence` or `cluster_strategy` imports `benchmark/`.
`select_stage_client()`, `_select_client()` (Normalization), `RunConfig`,
`ReplayConfig`, `StageClient`, `OmniRouteStageClient` — **all unmodified**
(verified: `git diff` shows zero changes to any of these files, see §23).

## 5. Dataset

**FACT.** 4 cases, `benchmark/omr03/dataset/cases/*.json`, copied verbatim from
`tests/fixtures/normalize/llm/ambiguous_signals.json` — the only versioned, real
repository fixture usable for this task at the time of construction (see the
prior session's "OMR-03 — Dataset & Ground Truth Protocol Proposal" analysis).
No evidence, context, or signal field was invented. `data/<run_id>/` (the 3 real
C10 runs) is `.gitignore`d and was not treated as available (per the task's own
instruction).

| case_id | source_type | ambiguous field(s) | intended difficulty |
|---|---|---|---|
| sig_norm_llm_0001 | web_search | market | easy |
| sig_norm_llm_0002 | tiktok_creative_center | market, language | mixed |
| sig_norm_llm_0003 | youtube | signal_type | hard / dual-defensible |
| sig_norm_llm_0004 | internal_data | durability_hint | genuinely indeterminate |

**OBSERVATION.** `sig_norm_llm_0002`'s raw `Signal` has **both** `market` and
`language` set to `"UNKNOWN"`, so `ambiguous_fields()` yields both — even though
the historical fixture response (`tests/fixtures/normalize/llm_replay/llm/
normalization/sig_norm_llm_0002.json`) only ever resolved `language`. That
historical answer is a **partial** resolution, not proof `market` is
unresolvable from this signal.

**INFERENCE.** 5 field-level evaluation points (`market`×2, `language`×1,
`signal_type`×1, `durability_hint`×1) is far below the ~40-per-field minimum
this session's own prior sizing analysis proposed for the pre-registered
thresholds to be discretely meaningful. See `dataset/manifest.json`'s
`size_assessment` field (written before this run).

## 6. Ground Truth Protocol

**FACT.** Ground truth (`benchmark/omr03/ground_truth/*.json`) was written by
this AI session, reading only each case's `evidence`/`context` text, **before**
any live model call was made in this execution (verified: git history — files
created; then the harness ran). Every entry carries `"reviewer_type":
"AI_SELF_REVIEW"` and an explicit `independence_note` stating this is **not**
an independent human reviewer and does not satisfy the full 2-human-reviewer
protocol proposed earlier. Two entries carry a status other than plain
`DETERMINABLE`:

- `sig_norm_llm_0003.signal_type` → `DETERMINABLE_WITH_ACCEPTABLE_ALTERNATIVE`,
  set `{search_trend, content_format}`, both pre-registered as correct.
- `sig_norm_llm_0004.durability_hint` → `INDETERMINATE` (four weeks of growth
  is exactly the class of case spec Appendix B already documents as
  insufficient for a durability rating).

**INFERENCE.** This ground truth is text-grounded and defensible (each entry
cites the exact evidence phrase behind it) but is a **single, non-independent
reviewer** — a materially weaker standard than the protocol this session
proposed. Results below must be read as preliminary for this reason alone,
independent of the Claude billing issue.

## 7. Pre-registered Thresholds

**FACT.** Reproduced from `knowledge/DECISIONS-NEEDED.md` OMR-03 (`ca95573`),
**unchanged** by this report: `language` ≥ 97%, `market` ≥ 95%, `signal_type` ≥
90%, `durability_hint` ≥ 80% (ground-truth-establishable cases only). Hard
gates: zero field-boundary violation, zero fabricated evidence, no systematic
per-class failure, technical-error rate not materially worse than Claude's
(undefined operationally — see §19).

## 8. Models

| Provider | Model | Path |
|---|---|---|
| Claude | `claude-sonnet-5` | `AnthropicNormalization` (existing, unmodified) — real Anthropic API |
| Groq | `groq/openai/gpt-oss-120b` | `OmniRouteStageClient` (OMR-01, unmodified) → OmniRoute `localhost:20128/v1` → Groq |

**FACT.** Only this one Groq model was used — the single route already proven
end-to-end in OMR-01. No other model or provider was tried.

## 9. Execution Method

**FACT.** `omniroute serve` started in background for this run only, confirmed
ready (`HTTP 400` on an empty POST = server up), stopped immediately after
(`omniroute stop`; verified no orphan process, port refuses connections
afterward). `ANTHROPIC_API_KEY` was read from the macOS Keychain
(`security find-generic-password -a ANTHROPIC_API_KEY -s
ai-music-media-engine -w`) and passed **only** to the harness subprocess's
environment (`env ANTHROPIC_API_KEY=... .venv/bin/python
benchmark/omr03/harness.py`) — never printed, never written to a file, never
present in Claude Code's own process environment. The results file was grepped
for `sk-ant` / `Bearer ` after the run: **0 matches**.

One run, one pass, both providers called exactly once per case (`run_all()`),
no retry, no fallback, no case removed after seeing results (`run_id`:
`run_20260904T202402658296+0000`, `benchmark/omr03/results/`).

## 10. Structural Validity

| Provider | Calls | Valid JSON | Required fields present | Enum-adherent (when present) |
|---|---|---|---|---|
| Claude | 4 | 0/4 (never reached generation) | N/A | N/A |
| Groq | 4 | 4/4 (HTTP + JSON envelope) | 3/4 message-content passed `validate_llm_response`; 1/4 rejected (`signal_id` mismatch) | 3/3 of the surviving responses (no out-of-taxonomy value observed) |

**FACT.** The Groq rejection was `"signal_id mismatch: 'sig_norm_lll_0002' !=
'sig_norm_llm_0002'"` — the model echoed the id with a typo (`lll` vs `llm`).
This is exactly the class of failure `validate_llm_response` (shared,
unmodified, identical for both providers) exists to catch — the **whole**
response for that case (both `market` and `language`) was discarded, not just
the malformed part.

## 11. Accuracy by Field

**Paired (Claude vs Groq) accuracy is not computable — Claude has 0 evaluable
observations in every field** (see §7 threshold table below, both columns
reproduced for transparency).

**Groq, standalone, against ground truth** (not gated on Claude also
succeeding):

| Field | n instances | technical/rejected | indeterminate excluded | evaluable | correct | accuracy | pre-registered threshold |
|---|---|---|---|---|---|---|---|
| market | 2 | 1 (the 0002 rejection) | 0 | 1 | 1 | 100% | ≥95% |
| language | 1 | 1 (same rejection) | 0 | 0 | 0 | N/A | ≥97% |
| signal_type | 1 | 0 | 0 | 1 | 1 | 100% | ≥90% |
| durability_hint | 1 | 0 | 1 (INDETERMINATE) | 0 | 0 | N/A | ≥80% |

**Claude, standalone:** 0/5 evaluable in every field (100% technical error).

**OBSERVATION.** Groq's one correct `signal_type` answer (`content_format`) is
a member of the pre-registered acceptable set `{search_trend, content_format}`
— it would have scored correct even under a stricter single-answer ground
truth reading of `search_trend`.

## 12. Joint Accuracy

**Diagnostic only (OMR-03 item 4 — never a gate).** Groq: 2/2 evaluable cases
(0001, 0003) fully correct → 100%; naive independent prediction from the field
table above is also ~100% at this sample size — no correlated-failure signal
detectable with n=2. Claude: 0 evaluable cases.

## 13. Divergence

**Not computable.** Divergence requires both providers to have produced an
answer for the same field; Claude produced none. `verdicts` in
`benchmark/omr03/results/` + `analysis.summarize()` mark all 5 field
observations `INCONCLUSIVE` for this reason.

## 14. Improvement vs Degradation

**Not computable**, for the same reason as §13 — `ADVANTAGE`/`DEGRADATION`
verdicts require a Claude answer to compare against. Zero of either observed.

## 15. Severity Analysis

Not applicable this run (§14). The severity taxonomy (`market`/`language` =
HIGH, `signal_type` = MEDIUM, `durability_hint` = LOW) and the required
sensitivity-table mechanism (`metrics.sensitivity_table`, never a fixed
multiplier) are implemented and tested (`tests/test_metrics.py`); the table
produced this run is trivially all-zero because there is no comparative data
to feed it (see `analysis.summarize()["sensitivity_table"]` above).

## 16. Technical Errors

**FACT.** Claude: `Error code: 400 — "Your credit balance is too low to access
the Anthropic API. Please go to Plans & Billing to upgrade or purchase
credits."` — identical message on all 4 calls, each with a distinct
`request_id`, confirming 4 independent real API round-trips, not a cached/local
failure. **This is an account-level billing state, not a transient error — a
retry would not fix it and none was attempted** (also required by OMR-03's
no-automatic-retry rule).

Groq: 0 HTTP-level technical errors (no 400/402/503/504, no timeout, no
transport error) across 4 calls; 1 content-level `ResponseRejected` (§10).

## 17. Cost

**FACT.** No pricing data exists anywhere in this repository (`pyproject.toml`,
`config/`, `src/`) — confirmed again this session. Claude's 4 calls were
rejected at the billing-check stage before any token generation, so they
plausibly cost \$0 (Anthropic's documented behavior for a pre-generation
billing rejection), but this is **not directly verified** from the API
response, which does not itemize cost for a rejected call. Groq/OmniRoute
token usage was **not captured** by this harness run — `raw_response_safe`
stores the model's own JSON content, not the outer HTTP envelope's `usage`
block. **Registering as an open input, as instructed:** actual per-call cost
for both providers remains undetermined; a future run should capture the
response envelope's usage/cost fields, not just the parsed message content.

## 18. Latency

| Provider | n | mean | note |
|---|---|---|---|
| Claude | 4 | 0.458s | time-to-**rejection** (billing check), not generation latency — not comparable to Groq's numbers |
| Groq | 4 | 1.006s | real call latency (3 successful + 1 rejected-content, all completed the HTTP round trip) |

**p50/p95 not reported** — n=4 is not large enough for a percentile to mean
anything (flagged as a pre-condition in the prior sizing analysis). Per OMR-03
policy, latency is informative only, never a gate.

## 19. Threshold Evaluation

| Threshold | n evaluable (Groq) | Result | Verdict |
|---|---|---|---|
| language ≥ 97% | 0 | undefined | **cannot evaluate** |
| market ≥ 95% | 1 | 100% (1/1) | technically "passes" at this n, but 1 data point proves nothing |
| signal_type ≥ 90% | 1 | 100% (1/1) | same caveat |
| durability_hint ≥ 80% | 0 (indeterminate, excluded) | undefined | **cannot evaluate**; abstention rate was 0% (Groq forced a guess) |

**"Materially worse" technical-error rate — PROPOSED operational rule, NOT a
decision:** compare each provider's technical-error rate on the *same* dataset;
flag "materially worse" if the candidate's rate exceeds Claude's by more than a
fixed number of *absolute* failures (not a percentage, given how small n
typically is) — e.g. "more than 1 additional failure out of every 20 calls,
whichever dataset size is in force." This specific number is **not** approved;
it is offered only as a concrete, measurable *shape* for the rule OMR-03 left
open, and cannot be evaluated at all this run because Claude's failure was
100% (a billing wall, not a provider-quality signal) — comparing Groq's 0%
HTTP-error rate to Claude's 100% billing-blocked rate would be comparing
different failure classes, not the same measurement.

## 20. Limitations

1. **n = 4 cases, 5 field observations** — an order of magnitude below the
   previously-proposed minimum (~40/field) for the pre-registered thresholds
   to be discretely meaningful (§5).
2. **Ground truth is single-reviewer AI self-review, not independent human
   review** — every result here is preliminary for this reason alone (§6).
3. **Claude produced zero usable data this run** — an Anthropic billing wall,
   external to this benchmark, blocked every call before generation (§16).
4. **No cost data captured** for either provider (§17).
5. **Groq path uses prompt-embedded schema instructions, not enforced
   structured output** — `OmniRouteStageClient` does not send `schema` to
   OmniRoute (documented limitation, `docs/EXTERNAL-LLM-GATEWAY.md` §10);
   Claude's (failed) calls would have used real Anthropic structured outputs.
   This asymmetry means even a future successful comparison would not be
   perfectly apples-to-apples on the *enforcement mechanism*, only on the task.
6. **One data point (`durability_hint` abstention) is suggestive, not
   conclusive**: Groq forced a guess (`EMERGING`) on the one case this
   session's ground truth marked indeterminate. With n=1 this cannot
   distinguish "Groq systematically over-guesses on ambiguous durability" from
   "this one case."

## 21. Conclusion

**D — INCONCLUSIVE.** Both independent triggers for this conclusion (either
alone would suffice) are present:

- Dataset/ground truth insufficiency (§5, §6, §20.1–2).
- Total absence of comparative data — Claude produced no usable output this
  run (§16, §20.3).

Per the task's own instruction, D is the correct and preferred conclusion here
— **not** a failure to complete the benchmark. Every phase that could run
without fabricating data, ground truth, or comparisons, did run (harness built,
tested, executed live end-to-end for both providers, metrics computed on the
data that does exist).

## 22. Recommendation

1. **Do not use this run as evidence for or against Groq on Normalization.**
   Neither "it looked perfect (100% on the 2 cases it could answer)" nor
   "Claude failed" say anything about relative quality — the first is 2 data
   points, the second is a billing issue, not a model comparison.
2. Before drawing any real conclusion: (a) resolve the Anthropic account
   billing state; (b) build the dataset to at least the "recomendado" tier
   (~150–200 cases) from the prior sizing analysis, with independent human
   ground truth review (2 reviewers); (c) re-run this same harness unchanged
   — it is already built, tested, and reusable at any dataset size.
3. The one qualitative signal worth carrying forward, clearly labeled as
   *preliminary, n=1*: Groq did not abstain on a case this session judged
   genuinely indeterminate. If this replicates at scale, it would matter for
   the `durability_hint` abstention-appropriateness metric specifically — not
   a reason to reject the candidate outright on this evidence alone.
4. This is a technical recommendation only, per OMR-02/OMR-03 governance —
   no threshold, gate, or policy in `ca95573` is being proposed for change.

## 23. Reproducibility Information

- **Harness:** `benchmark/omr03/harness.py` — reuses
  `market_intelligence.normalize.llm._prompt` / `_response_schema` /
  `validate_llm_response` / `_context` (unmodified) and
  `external_llm_gateway.OmniRouteStageClient` (unmodified, OMR-01).
- **Dataset version:** `benchmark/omr03/dataset/manifest.json`
  (`omr03-dataset-v1-preliminary`).
- **Ground truth:** `benchmark/omr03/ground_truth/*.json`, each with a
  `reviewed_at` date and an explicit independence caveat.
- **Raw results:** `benchmark/omr03/results/run_20260904T202402658296+0000.json`
  (grepped clean of `sk-ant`/`Bearer ` before being committed).
- **Analysis:** `benchmark/omr03/analysis.py` (`summarize()`) —
  `PYTHONPATH=benchmark .venv/bin/python -c "from omr03.analysis import
  summarize; import json; print(json.dumps(summarize(json.load(open(<results
  file>))), indent=2))"` reproduces every number in §11–§15.
- **Tests:** `benchmark/omr03/tests/` — `.venv/bin/python -m pytest
  benchmark/omr03/tests -q` (35 tests, mocked/offline, no network, no
  dependency on this specific run's results file).
- **Re-running live:** start `omniroute serve`, wait for readiness, then
  `env ANTHROPIC_API_KEY="$(security find-generic-password -a
  ANTHROPIC_API_KEY -s ai-music-media-engine -w)" .venv/bin/python
  benchmark/omr03/harness.py`, then `omniroute stop`. No production file is
  touched by any of this.

---

## Run 2 — re-run after reported billing resolution

**Requested reason:** the user reported the Anthropic billing block from Run 1
resolved and asked for an exact re-run — same dataset, same ground truth, same
harness, same thresholds (none modified; verified by diff against the commits
that introduced each, before this run: `3114e17` for dataset/ground truth,
`6f9f1eb` for harness/metrics, `ca95573` for the threshold policy — all three
diffs empty).

**FACT — the billing block is still present.** All 4 Claude calls failed with
the identical error as Run 1: `"Your credit balance is too low to access the
Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."`
— 4 distinct `request_id`s (`req_011Cej3J9uJP...`, `req_011Cej3JGoHY...`,
`req_011Cej3JMzKt...`, `req_011Cej3JSkZu...`), confirming 4 independent real
API round-trips, not a cached/local failure. **This contradicts the premise
that billing had been resolved** — it had not, at the time of this execution.
Per the task's own instruction ("Se a API Anthropic ainda retornar billing
error, pare e reporte o erro exato. Não faça retries inúteis"), no retry was
attempted and no Claude-vs-Groq comparison was produced.

**Run identifier:** `run_20260904T203604499438+0000` — a **new** file, Run 1's
results file was not overwritten or modified.

**Groq (standalone vs. ground truth, this run):**

| Field | n evaluable | correct | accuracy |
|---|---|---|---|
| market | 1 | 1 | 100% |
| language | 1 | 1 | 100% |
| signal_type | 1 | 1 | 100% |
| durability_hint | 0 (indeterminate) | — | N/A (forced a guess, `EMERGING`, again — 0% abstention-appropriateness, same as Run 1) |

**OBSERVATION — cross-run non-determinism in Groq's `signal_id` echo.** Run 1
had a `signal_id` typo rejection (`sig_norm_lll_0002` for case `...0002`); Run
2 had a *different* case rejected the same way (`sig_norm_lll_0001` for case
`...0001`) — case `...0002` succeeded this time instead. This is the same
failure *mode* recurring on a *different, effectively random* case each run,
not a fixed bug tied to one case. **INFERENCE:** at n=1 per case, Groq's
success/failure on any single case is not a stable measurement — this is
exactly the kind of run-to-run noise the prior sizing analysis warned a
4-case dataset cannot average out.

**Conclusion: unchanged — D, INCONCLUSIVE.** Now confirmed across two
independent live attempts: the dataset/ground-truth insufficiency (§20) and
the total absence of Claude comparative data both still hold. Thresholds
(§7, `ca95573`) were not evaluated against a comparison because none exists.

**RECOMMENDATION.** Do not attempt a third live run against this same 4-case
dataset — it will not produce a paired comparison while the Anthropic account
remains blocked, and repeating identical calls burns real (if small) Groq
cost for no new information. Confirm the Anthropic account's billing state
directly (e.g. the Anthropic Console billing page) before requesting another
run of this harness.
