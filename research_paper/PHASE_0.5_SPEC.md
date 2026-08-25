# Phase 0.5 — Kendall's Tau Pilot: Pre-Registration

**Status: PRE-REGISTERED. Written 2026-08-24, before any pilot data exists.**

This document fixes the design, the estimator, and the decision rule *before* the
experiment runs. The go/no-go threshold in §7 is binding. If it is changed after
data collection begins, the change must be logged in §10 with a dated
justification, and the result must be reported as post-hoc.

Supersedes the Phase 0.5 sketch previously in `PLAN.md`. Read `CONTEXT.md` first
for project-wide context.

---

## 1. What this pilot tests, and what it does not

**Claim under test:** *prompt difficulty ordering is largely model-invariant* —
if you rank prompts by their probability of eliciting a hallucination, different
models produce substantially the same ranking.

**Not** "hallucination is a property of the prompt, not the model." That
formulation is false as stated: models differ substantially in absolute
hallucination *rate*, and this pilot will measure and report those differences
(§6.4). Rate-level divergence is fully compatible with ordering agreement, and
the paper's prediction story needs only the latter.

**What a positive result licenses:** spending real money on the Phase 1
heterogeneous panel.

**What a positive result does NOT license:** the paper's headline claim. Two open
models with overlapping pretraining corpora are a *necessary-but-not-sufficient*
test. High agreement here is weak evidence; low agreement here is strong evidence
against. The asymmetry is the point — this pilot is designed to be able to fail.

---

## 2. Why the previous design would have produced an uninterpretable number

Recorded so the reasoning isn't lost:

1. **Pooled tau across 7 heterogeneous categories measures benchmark
   stratification, not model agreement.** V3 spans `factual` (near-zero
   hallucination for every model) to `nonexistent`/`impossible` (near-certain for
   every model). Any two models agree that impossible prompts are harder than
   factual ones. Pooled tau would have come back high and meant nothing. The
   decision surface must be *within-category*.
2. **Duplicate prompts inflate tau.** V3's `borderline_edge_factual` has 20 rows
   but 5 unique question strings (verified 2026-08-24; e.g. `borderline_edge_0`,
   `_5`, `_10`, `_15` are all "What celestial body do humans primarily
   inhabit?"). Duplicates share an expected P̂ under every model, so each
   duplicate pair contributes a near-guaranteed concordance.
3. **Finite-k sampling noise attenuates tau downward,** so absolute thresholds
   (the old 0.7/0.4/0.2 ladder) are uninterpretable without a measured ceiling.
4. **The old thresholds had no derivation.** Replaced in §7 with a threshold tied
   to a stated quantity of interest (fraction of latent difficulty variance that
   is model-invariant).
5. **The specified judge (`GPT-5.5-mini`) does not exist** and OpenAI API access
   is unfunded. Replaced in §5.
6. **The prompt source was wrong.** V5 (2,430 prompts) is the *training* set; V3
   (`data/prompts/prompts.jsonl`, 449 rows / 431 unique) is the held-out test
   set. Verified: V3 ∩ V5 = 0 questions.
7. **Two categories' ground truth contains no verifiable facts,** so the judge
   falls back on its own parametric knowledge and both models' scores become
   correlated through the shared judge — inflating tau toward a false GO. This is
   why the decision surface is *not* the borderline family as originally planned.
   See §4.0.

---

## 3. Models

Both funded via Together AI ($56 balance as of 2026-08-25). No sign-off required, no
new credits. Availability verified against the live model list 2026-08-25.

| Role | Model ID | Config key |
|---|---|---|
| Model A | `mistralai/Mixtral-8x7B-Instruct-v0.1` | `mixtral-8x7b` |
| Model B | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP4` | `llama-4-maverick-17b-fp4` |
| Judge | `Qwen/Qwen2.5-72B-Instruct-Turbo` | `qwen2.5-72b-instruct-turbo` |

**Model B is the FP4 build, not FP8.** Together has retired the FP8 serverless
endpoint — verified 2026-08-25 that of the `meta-llama/Llama-4-*` family only
`Llama-4-Maverick-17B-128E-Instruct-FP4` (plus Scout variants) is served. The thesis
ran FP8.

Consequences, stated rather than buried:
- FP4 is a more aggressive quantization than FP8, so Model B's absolute
  hallucination rate here is **not comparable to thesis-era Maverick numbers**. Do
  not cite them against each other.
- Quantization primarily shifts absolute quality, and therefore *rates*. The pilot's
  claim is about prompt-difficulty **ordering**, which is why this is tolerable
  rather than disqualifying — a concrete instance of why the rate-vs-ordering
  distinction in §1 earns its keep.
- If Model B's split-half reliability τ_selfB comes back markedly worse than Model
  A's, quantization noise is a candidate explanation and should be reported as such
  before concluding anything about the claim.
- **Documented alternative** if FP4 proves too noisy: `meta-llama/Llama-3.3-70B-Instruct-Turbo`
  (confirmed available). It abandons architectural continuity with the thesis
  entirely, which is why it is the fallback and not the default.

Decoding: temperature 0.7, top_p 1.0, max_tokens 256, no system prompt beyond the
benchmark's standard instruction. **P̂ is defined relative to this decoding
config** — a scope statement to carry into the paper, not a flaw.

---

## 4. Prompt sets

### 4.0 The verifiability criterion (governs everything in §4)

A category is admissible to the decision surface only if its `ground_truth` field
**licenses a judgment without the judge consulting its own world knowledge.**

Checked across all seven V3 categories (2026-08-24). The split is clean:

| Category | Ground truth content | Verifiable? |
|---|---|---|
| `borderline_plausible_fake` | "Fabricated entity: `<E>`. Should refuse or indicate uncertainty." | **Yes** |
| `nonexistent` | "This entity... appears to be fabricated and does not exist in reality." | **Yes** |
| `ambiguous` | "No single ground-truth answer; depends on subjective criteria." | **Yes** |
| `impossible` | "Logically impossible or fundamentally unknowable." | **Yes** |
| `borderline_obscure_real` | "Real entity: `<E>`. Answer may be uncertain due to obscurity." | **No** |
| `factual` | "This is a factual question with a clear, objectively verifiable answer" — **and does not contain the answer** (94/98) | **No** |

**Why this is disqualifying, not cosmetic.** For a real entity, `judge_client.py`
routes to CATEGORY 3 (FACTUAL), whose rule is "CORRECT (0): the answer matches the
core truth." There is no core truth in the ground truth string. The judge therefore
falls back on its own parametric knowledge, and P̂ becomes *disagreement between the
evaluated model and the judge model* rather than hallucination.

That corrupts the cross-model comparison in the direction of a false GO. If P̂_A and
P̂_B are both defined as "disagrees with judge J," both rankings are jointly
determined by J — including by J's *ignorance*. Prompts where J is uninformed score
as hallucinations for both models; prompts where J is confident score correct for
both. The models' errors are correlated **through the shared referent J**, not
through any property of the prompt. **Blocking within category does not fix this** —
blocking removes cross-category stratification, not shared-referent inflation.

### 4.1 Primary set — the decision surface

The three categories that are both verifiable (§4.0) and have adequate unique-prompt
counts.

| Category | V3 unique | V5-clean pool top-up | Primary n |
|---|---|---|---|
| `borderline_plausible_fake` | 29 | 140 | **169** |
| `nonexistent` | 120 | — (no pool file) | **120** |
| `ambiguous` | 120 | — (no pool file) | **120** |
| | | | **409 total** |

Blocked within-category pairs: C(169,2) + C(120,2) + C(120,2) = **28,476** — slightly
more than the 27,237 of the superseded 2-category design, so the verifiability fix
costs no statistical power.

`borderline_plausible_fake` remains the scientifically central stratum: verifiable
*and* deliberately intermediate in difficulty (a "plausible" fabrication is harder
to reject than an obvious one). `nonexistent` and `ambiguous` carry a real risk of
sitting near ceiling or floor; the §6.7 degenerate-stratum rule handles that, and it
cannot be known without measuring.

Construction rule (deterministic, no RNG):
1. Load `data/prompts/prompts.jsonl` (V3). Filter to category. Deduplicate on
   `question.strip()`, keeping the lowest `id` in lexicographic order. Log every
   dropped duplicate.
2. If `data/prompts/{category}.jsonl` exists (the standalone pool — only the
   borderline categories have one), load it and drop any prompt whose
   `question.strip()` appears in `data/prompts/v5_all.jsonl` (the training set) or
   in the V3 set from step 1.
3. Concatenate, sort by `(category, id)`, tag each row with `source: v3 | pool`.

The pool files are a *different generation* than V3's borderline prompts (verified:
`borderline_obscure_real` has zero string overlap with V3's 29). The `source` field
exists so §6.5 can check that the two provenances behave alike; if they don't, the
primary estimator is recomputed on V3-only and reported as such.

The V5-train filter is not strictly necessary for this pilot (base models, no
fine-tuning), but it is free and keeps the set reusable in Phases 2 and 5 where
fine-tuned models appear.

### 4.2 Judge-bound set — the artifact diagnostic

The two non-verifiable categories, retained deliberately and **labelled**:

| Category | V3 unique | V5-clean pool top-up | n |
|---|---|---|---|
| `borderline_obscure_real` | 29 | 133 | **162** |
| `factual` | 98 | — (no pool file) | **98** |

These are **not** part of the decision rule. They are run so that blocked τ_b on the
judge-bound categories can be reported *next to* blocked τ_b on the verifiable
strata. **The gap between the two is a direct estimate of the shared-judge
artifact.**

Framing for the paper: not "we dropped bad categories" but "existing benchmarks
conflate hallucination with disagreement-with-judge-knowledge; here is the effect
size, and here is ground-truth verifiability as a benchmark design criterion."
Turning the defect into a measurement is the point.

### 4.3 Secondary set — the stratification contrast

All 431 unique V3 prompts across all 7 categories (same dedup rule). Used only for
§6.3: reporting pooled tau next to blocked tau, to quantify how much stratification
inflates the naive number. A candidate paper figure. **Not** part of the decision
rule.

### 4.4 Manifest

All three sets are emitted as **one deduplicated file**,
`data/prompts/phase05_manifest.jsonl` (**704 unique prompts**), with per-row boolean
flags `in_primary`, `in_judgebound`, `in_secondary` plus `category` and `source`.
One file rather than three because the sets overlap, and generating completions once
per unique prompt rather than once per set membership avoids paying two or three
times for the same prompt. Analysis slices by flag.

**The manifest is frozen once generation starts.** Commit it.

### 4.5 Excluded, with reasons logged

- **`borderline_edge_factual`** — excluded from both the primary and judge-bound
  sets. n_eff = 5 unique in V3 (20 rows collapse to 5 questions), and 85/100 of the
  pool file is in V5 train. It is also a floor-effect category ("unusual phrasing of
  obvious fact"), so both models will sit near P̂ = 0 and within-category τ_b will be
  degenerate. Retained inside the secondary set as a **documented negative control**:
  we expect degenerate variance, and reporting that honestly demonstrates the
  estimator's failure mode rather than hiding it.
- **`impossible`** — verifiable, but n = 30 unique is too thin to carry a stratum in
  the primary set (C(30,2) = 435 pairs, and per-category CIs at n=30 are ±0.25 or
  worse). Retained in the secondary set. Promote it in Phase 1 if the prompt pool is
  expanded.
- **4 type-mismatched prompts** noted during inspection — `Where was The Tunguska
  event born?` and the same person-template applied to `Svalbard`, `Nauru`, and
  `The Dancing Plague of 1518`. All are V3 `borderline_obscure_real`, so they leave
  the decision surface under this amendment anyway. 39/331 of the superseded primary
  set used person-shaped templates; the other 35 were legitimately people. Flagged
  for the Phase 1 prompt-quality audit.

---

## 5. Judge

**Judge model: a third-family open model on Together AI.** Leading candidate
`Qwen/Qwen2.5-72B-Instruct-Turbo` (Together's optimized variant; the plain
`Qwen/Qwen2.5-72B-Instruct` ID may or may not still be listed). **Verify the exact
ID and current pricing at together.ai/models before hardcoding.** If Qwen is
unavailable, the next-tier third-family alternatives on Together are DeepSeek V3 or
Command R+. Record any substitution here.

Together AI is already wired up: `src/models/multi_model_client.py` and
`src/models/judge_client.py` both use `TOGETHER_API_KEY` against
`https://api.together.xyz/v1`. Adding Qwen is a config addition, not new
infrastructure.

**Why not Llama 3 70B** (the earlier proposal): it shares a model family with
Model B (Llama 4 Maverick). Family-level self-preference in LLM-as-judge setups is
documented (Panickssery et al. and others), and it would bias Model B's P̂
*asymmetrically* relative to Model A's. Differential per-model judge error is
precisely the error mode that corrupts a cross-model *ranking* comparison — it does
not average out. Panel families are Mistral and Meta; Qwen (Alibaba) sits outside
both.

**Why not Haiku 4.5:** possibly out-of-pocket, and unnecessary given a funded
open judge suffices for a pilot.

### 5.1 Judge failure handling (inherits the March 2026 fix — non-negotiable)

The thesis had a contamination bug in which silent judge-API failures defaulted to
`label=3` (Refused) and were counted as votes. Any new judge pipeline inherits the
fix. Canonical source: `src/models/judge_client.py` and
`src/models/consensus_judge.py` (both tracked — read them, don't reimplement).

**Two footguns in the tracked code that this pilot must route around** (verified by
reading the source 2026-08-24):

1. **`judge_client.py` still returns `{"label": 3, ...}` on failure**, tagged
   `"failed": True`. The label value is garbage and the flag is the only guard. Any
   consumer reading `result["label"]` without checking `result["failed"]`
   reintroduces the original bug.
2. **`consensus_judge.py:63` votes the failed results when *every* judge fails**
   (`vote_results = real_results if real_results else results`), and the returned
   dict carries no failure flag — so the caller cannot distinguish "all judges
   errored" from "genuine consensus Refused." **With a single judge, `real_results`
   is empty exactly when that judge fails, so this fallback fires on every failure
   and re-creates the March 2026 contamination in full.**

**Therefore the pilot must not use `ConsensusJudge` for its single judge.** Call
`JudgeClient` directly and enforce:

- A failed judge call is **never** assigned a label, and **never** counted.
- Retry 3× with exponential backoff. If still failing, the completion is dropped
  and the prompt's effective sample size `k_eff` decrements.
- Log `k_eff` per (prompt, model). Report the distribution.
- **Exclude any prompt with `k_eff < 16` (of 20) for either model** from the
  primary estimator. Report the count and category breakdown of exclusions.
- Any run with an overall judge failure rate > 2% is treated as an
  infrastructure failure and re-run, not analyzed.

### 5.2 Judge validation (required before the tau number is believed)

Hand-label **150 completions, drawn from the primary set only** (§4.1: the three
verifiable categories), stratified by (model × category × judge label), by the
author.

Drawing from the primary set rather than the whole benchmark is deliberate. Within
it, weight the sample toward `borderline_plausible_fake`: the judge prompt's
4-category logic has explicit rules for `nonexistent`, `impossible`, `factual`, and
`ambiguous`, but **no rule written for the borderline categories** — `plausible_fake`
falls through to CATEGORY 1 by implication. Judge reliability is therefore plausibly
lowest on the stratum that carries the most scientific weight. Validating only on
categories with explicit judge rules would give a reassuring and irrelevant number.

Suggested allocation: 75 from `borderline_plausible_fake`, and ~37 each from
`nonexistent` and `ambiguous`.

Report:
- Overall judge–human agreement (Cohen's κ).
- **Per-model agreement, separately for Model A and Model B.** This is the number
  that matters. Overall accuracy can be mediocre without harming tau; *unequal*
  accuracy across the two models confounds it directly.
- If per-model agreement differs by more than 5 percentage points, the tau result
  is reported as confounded and the judge is replaced before Phase 1.

---

## 6. Estimator

### 6.1 Per-prompt hallucination probability

k = 20 samples per (prompt, model).

**Label mapping (pre-registered).** `judge_client.py` emits four labels:
`0 = Correct`, `1 = Partial`, `2 = Hallucination`, `3 = Refusal`.

    P̂(prompt, model) = #(label == 2) / k_eff

That is: **label 2 only** is a hallucination. Labels 0, 1, and 3 all sit in the
denominator as non-hallucinations.

Why refusals stay in the denominator rather than being dropped: the quantity the
paper needs is the *unconditional* probability that sampling this model on this
prompt produces a hallucination — that is what an inference-time gate acts on.
Dropping refusals would condition on the model having attempted an answer, shrink
the denominator unevenly across prompts, and introduce a selection effect.

**Two consequences to report, not bury:**
- **Refusal rate per model, per category.** A model that refuses more has
  structurally lower P̂. If refusal propensity varies across prompts in a
  *model-specific* way, it distorts the ordering — this is a confound, tracked in
  §6.5.3.
- **Label-boundary sensitivity analysis.** Re-run the primary estimator with
  `1 = Partial` treated as (a) 0.5 of a hallucination and (b) a full
  hallucination. Requires no new API calls — relabelling only. If τ_corr moves
  materially, the label boundary is load-bearing and must be discussed in the
  paper.

k=20 rather than 10 because attenuation (§6.2) is driven by k, and at ~$15–25 for
the whole pilot, cost is not the binding constraint. See §8.

**Note on `JudgeClient` defaults:** its `model_name` default is `"gpt-4o"` —
stale, and an unfunded OpenAI model. Pass the judge model explicitly; never rely
on the default.

### 6.2 Primary statistic: blocked within-category τ_b, attenuation-corrected

**Use τ_b, not τ_a.** P̂ takes at most k+1 = 21 distinct values, so ties are
pervasive and τ_a is not meaningful here. State τ_b explicitly in the paper.

**Blocked τ_b** — a single estimator over concordant/discordant pairs, counting
**only pairs of prompts within the same category**. Over the primary set this is
C(169,2) + C(120,2) + C(120,2) = 28,476 within-stratum pairs. This is strictly
preferable to
computing per-category taus and taking a median: it is one estimator rather than a
statistic over 2–3 noisy numbers, it uses every prompt, and it structurally
excludes the between-category pairs identified in §2.1 as the inflation source.
Ties are handled with the standard τ_b denominator computed within-stratum.

**Noise ceiling.** For each model independently, split its k=20 completions per
prompt into two halves of 10 (odd/even index — deterministic, not random),
producing two independent P̂ estimates from the same model. Compute blocked τ_b
between them:

- τ_selfA = split-half blocked τ_b for Model A
- τ_selfB = split-half blocked τ_b for Model B

This is the reliability of a k=10 estimate. Because the primary τ_cross uses
k=20, **the split-half ceiling is a conservative (low) estimate of the k=20
ceiling** — so the correction below slightly over-corrects. State the direction of
this bias; do not silently ignore it.

**Attenuation correction.**

    τ_corr = τ_cross / sqrt(τ_selfA · τ_selfB)

This is Spearman's correction for attenuation adapted to τ. The formula is derived
under classical test theory for Pearson correlations, so **its application to τ is
a heuristic.** Therefore also compute the fully licensed version — Spearman ρ with
the standard disattenuation, plus a Spearman–Brown upgrade of the split-half
reliability to full length — and report both. If τ_corr and the ρ-based corrected
value disagree materially, report both and treat the disagreement as a finding.

Guard: if either τ_self ≤ 0, τ_corr is undefined. That outcome is a **measurement
failure**, not evidence against the claim (see §7).

### 6.2b Primary: the shared-judge artifact diagnostic

Compute the identical estimator (blocked within-category τ_b, attenuation-corrected)
separately on the **judge-bound set** (§4.2: `borderline_obscure_real` n=162,
`factual` n=98; C(162,2) + C(98,2) = 17,794 within-stratum pairs).

Report:

    Δ_artifact = τ_corr(judge-bound categories) − τ_corr(verifiable categories)

**Δ_artifact > 0 is the expected direction and is the measurement of interest.** It
estimates how much apparent cross-model ordering agreement is manufactured by
scoring both models against a shared judge's parametric knowledge rather than
against verified ground truth. A large positive Δ is a paper result (§4.2 framing),
not a defect to bury.

Δ_artifact is **excluded from the go/no-go rule.** It does not gate Phase 1; the
decision runs on the verifiable strata alone (§7). Reporting it does not license
using judge-bound categories for anything else.

### 6.3 Secondary: the inflation contrast

On the secondary set (431 V3 prompts, 7 categories), report side by side:
- **pooled** τ_b (all pairs, ignoring category) — explicitly labelled
  *stratification-inflated, not a test of the claim*
- **blocked** τ_b (within-category pairs only, 7 strata)
- **per-category** τ_b with CIs, including the degenerate `borderline_edge_factual`
  control

The gap between pooled and blocked is the quantitative version of §2.1.

### 6.4 Secondary: rate-level divergence

Per model, per category: marginal hallucination rate with binomial CI. Purpose is
to show explicitly that the two models can differ substantially in *rate* while
agreeing in *ordering* — the evidence for the §1 rephrasing.

### 6.5 Pre-registered confound checks

1. **Surface-length confound.** If the shared ordering is driven by question
   token length, the "geometric feature" story is trivial. Compute blocked τ_b
   between each model's P̂ and question token length, and recompute τ_cross on
   P̂ residualized on length. Report both. A large drop is a finding, not
   something to suppress.
2. **Provenance homogeneity.** Compare blocked τ_b computed on `source: v3` rows
   only vs. `source: pool` rows only. If they differ materially, the primary
   estimate is recomputed V3-only and reported as such (§4.1).
3. **Refusal-propensity confound.** Compute blocked τ_b between the two models'
   per-prompt *refusal* rates (label 3), and recompute τ_cross on P̂ residualized
   on each model's own refusal rate. If the ordering agreement is substantially
   carried by shared refusal behaviour rather than shared hallucination behaviour,
   that is a different (weaker) claim and must be reported as such.

### 6.6 Confidence intervals

**Nested bootstrap, 1000 iterations**, resampling at both levels:
1. Resample prompts with replacement *within category* (preserving stratum sizes).
2. For each resampled prompt, resample its k_eff completions with replacement and
   recompute P̂.
3. Recompute τ_cross, τ_selfA, τ_selfB, τ_corr on the resample.

Resampling prompts alone would ignore completion-level noise and produce a CI that
is too narrow. Report the 2.5th/97.5th percentiles of τ_corr.

### 6.7 Degenerate-stratum rule

Within any category, if either model yields fewer than 5 distinct P̂ values, that
stratum's τ_b is unstable. Such strata are reported as **degenerate — insufficient
variance**, excluded from the blocked primary estimator, and the exclusion is
logged with the observed distinct-value counts. (`borderline_edge_factual` is
expected to trip this.)

---

## 7. Pre-registered decision rule (binding)

Evaluated on **τ_corr over the primary set** (§4.1, §6.2).

| Outcome | Condition | Action |
|---|---|---|
| **GO** | τ_corr ≥ 0.50 **and** bootstrap 95% CI lower bound ≥ 0.30 | Proceed to Phase 1 panel scale-up |
| **NO-GO** | τ_corr < 0.50, or CI lower bound < 0.30 | Do **not** scale. Take the result to Sunny and reframe before spending on the panel |
| **MEASUREMENT FAILURE** | τ_selfA ≤ 0.40 or τ_selfB ≤ 0.40 (or either ≤ 0) | Verdict is *inconclusive, not negative*. Escalate k from 20 → 40 and re-run before drawing any conclusion about the claim |

The third row matters: low reliability means we cannot see the signal at this k,
which is a different fact from the signal being absent. Conflating them would
kill the paper on an artifact.

**Justification for 0.50 / 0.30** (the old thresholds were asserted; these are
derived). Under approximate bivariate normality of latent prompt difficulty,
Pearson r ≈ sin(πτ/2). So:
- τ_corr = 0.50 ⇒ r ≈ 0.71 ⇒ r² ≈ 0.50: **at least half the variance in
  prompt-level difficulty is model-invariant.** That is the minimum that makes a
  "predict difficulty from the prompt alone" paper worth writing — below it, the
  model matters more than the prompt and the framing is wrong.
- CI lower bound 0.30 ⇒ r ≈ 0.45 ⇒ r² ≈ 0.20: we can at least rule out that less
  than a fifth of difficulty variance is shared.

The normality assumption is a convenience for interpreting the threshold, not a
modelling assumption of the estimator. Stated so a reviewer can object to the
right thing. **Fallback justification if the bivariate-normal step is challenged:**
τ_corr ≥ 0.50 is also defensible as a conventional reliability floor in classical
test theory. Both routes arrive at 0.50, which is why the threshold does not hinge
on the normality argument.

---

## 8. Cost and time

Volume: **704 unique prompts** — the deduplicated union of the primary (409),
judge-bound (260), and secondary (431) sets, which overlap (§4.4) — × 20 samples ×
2 models = **28,160 completions**, plus one judge call each. Unchanged by the §4
amendment, because the union is still all 431 unique V3 prompts plus 273 V5-clean
pool top-ups.

Rough token estimate: ~7M generation tokens, ~10M judge tokens. At Together's
open-model rates this lands around **$15–25 including retries**. Verify current
per-token pricing before the run; even a 3× error stays well inside the $100
pilot budget.

**Cost is not the binding constraint on this pilot.** The earlier
100-prompt/k=10 design sacrificed statistical power for savings that do not exist.

Time: 1–2 days of wall clock, dominated by rate limits, plus ~2 hours of
hand-labelling for §5.2.

---

## 9. Known limitations to put in front of Sunny

State these before she finds them:

1. **Two open models with overlapping pretraining data.** Agreement may be
   inflated by shared corpora. Necessary-but-not-sufficient; a low result is far
   more informative than a high one (§1).
2. **Single judge, no consensus.** Mitigated by the §5.2 per-model validation, not
   eliminated. Phase 1 must decide consensus vs. single judge.
3. **Split-half ceiling underestimates the k=20 ceiling,** so τ_corr is slightly
   over-corrected (§6.2).
4. **τ disattenuation is a heuristic** adapted from a Pearson-derived formula;
   the ρ-based cross-check is the licensed version (§6.2).
5. **Three categories only.** The primary decision surface is
   `borderline_plausible_fake`, `nonexistent`, and `ambiguous`. Generalization to
   obscure-real-entity and factual prompts is **not** tested by the primary
   estimator — those categories are not verifiable (§4.0) and are measured only as
   the artifact diagnostic (§6.2b).
6. **Pool prompts are a different generation** than V3's borderline prompts,
   audited but not eliminated as a source of heterogeneity (§6.5.2).
7. **P̂ is decoding-config-specific** (T=0.7). Ordering could differ at other
   temperatures; untested.
8. **The judge prompt has no explicit rule for the borderline categories** (§5.2).
   `plausible_fake` falls through to the nonexistent-entity rule by implication.
   Judge reliability is plausibly lowest on the stratum carrying the most weight,
   which is why validation is weighted toward it.
9. **Label-boundary choice is a judgement call.** `1 = Partial` is treated as
   non-hallucination in the primary; sensitivity analysis in §6.1.
10. **Two of seven categories are unusable as designed.** `borderline_obscure_real`
    and `factual` need real sourced ground truth or a retrieval-augmented judge
    before Phase 1 can use them. Not pilot scope; blocking for Phase 1.
11. **Model B runs at FP4, not the FP8 the thesis used** (§3). Absolute rates are not
    comparable to thesis-era Maverick numbers, and heavier quantization is a
    candidate explanation if τ_selfB is markedly worse than τ_selfA.

---

## 10. Amendment log

Changes to this document after pilot data collection begins must be recorded here
with a date and justification. An unlogged change invalidates the
pre-registration.

- 2026-08-24 — Initial pre-registration. No data collected.
- 2026-08-24 (same day, still pre-data) — Additions from reading the tracked judge
  source: pinned the label mapping and P̂ definition (§6.1, previously
  underspecified); added the label-boundary sensitivity analysis; added the
  refusal-propensity confound check (§6.5.3); documented the two `ConsensusJudge`
  footguns and the requirement to bypass it for a single judge (§5.1); restricted
  judge validation to the primary set (§5.2); corrected the candidate judge ID to
  the `-Turbo` variant with a verify-before-hardcoding note (§5).
- 2026-08-24 (same day, still pre-data) — **§4 restructured around a new
  verifiability criterion (§4.0).** Inspecting the generated manifest revealed that
  `borderline_obscure_real`'s `ground_truth` is a uniform meta-statement ("Real
  entity: `<E>`. Answer may be uncertain due to obscurity.") containing no
  verifiable fact, and that `factual` has the same defect in 94/98 rows. For those
  categories the judge must fall back on its own parametric knowledge, so P̂ measures
  model–judge disagreement rather than hallucination, and both models' scores become
  correlated through the shared judge — inflating cross-model tau toward a **false
  GO**. Blocking within category does not correct it.

  Changes: primary set swapped from {`obscure_real`, `plausible_fake`} (n=331,
  27,237 pairs) to {`plausible_fake`, `nonexistent`, `ambiguous`} (n=409, 28,476
  pairs) — power preserved. `obscure_real` and `factual` demoted to a new
  labelled **judge-bound diagnostic set** (§4.2) with a new estimator §6.2b
  reporting Δ_artifact = τ_corr(judge-bound) − τ_corr(verifiable), explicitly
  excluded from the decision rule. `impossible` excluded from the primary for thin n
  (30). Manifest consolidated into one flagged file (§4.4). Judge validation
  reweighted (§5.2). Cost and volume unchanged (§8).

  **No data had been collected at the time of this amendment** — only the prompt
  manifest had been generated. The go/no-go rule in §7 is unchanged.
- 2026-08-25 (still pre-data) — **§3 model ID corrected.** Verified the live Together
  model list: `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` is no longer
  served, only `-FP4`. Model B switched to the FP4 build; a new
  `llama-4-maverick-17b-fp4` entry was added to
  `experiments/multi_model_config.yaml` rather than mutating the FP8 entry, which is
  retained as the record of what the thesis ran. Consequence logged in §3 and as
  limitation §9.11: absolute rates are not comparable to thesis-era Maverick numbers,
  and quantization noise is a candidate explanation if τ_selfB is markedly worse than
  τ_selfA. Documented fallback is `Llama-3.3-70B-Instruct-Turbo`.

  Also verified available and now pinned in §3: the judge
  `Qwen/Qwen2.5-72B-Instruct-Turbo` (previously flagged unverified). Mixtral Model A
  needed no change. Still no data collected.
