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

Availability verified 2026-08-25 by probing each candidate with a real 1-token
request. **`/v1/models` is not an availability check** — it lists every model
Together knows about, including dedicated-endpoint-only ones.

| Role | Model ID | Family | Provider |
|---|---|---|---|
| Model A | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Meta | Together (serverless) |
| Model B | `openai/gpt-oss-120b` | OpenAI open-weight | Together (serverless) |
| Judge | `claude-haiku-4-5` | Anthropic | Anthropic API |

**Together's serverless tier on this account offers exactly three chat models:**
`Llama-3.3-70B-Instruct-Turbo`, `gpt-oss-120b`, and `gpt-oss-20b`. Everything else
probed — all Mistral/Mixtral builds, all Qwen builds, Gemma, GLM, DeepSeek,
Llama-4-Maverick-FP4, Llama-4-Scout, and the older Llama-3.x Turbo builds — returns
`400 model_not_available` requiring a paid dedicated endpoint. Dedicated endpoints
bill per running minute, which is the wrong economics for 28,160 completions.

### 3.1 Consequence: the pilot no longer runs the thesis's models

Both thesis models are gone from serverless. `Mixtral-8x7B-Instruct-v0.1` and every
`Llama-4-Maverick` build are dedicated-only. **Direct continuity with the thesis is
lost**, and no thesis-era number may be compared against this pilot's rates.

**This is arguably a better pilot, and the reasoning should survive review.**
Limitation §9.1 says the pilot's central weakness is that "two open models trained
with similar data may have inflated agreement." Mixtral and Llama-4-Maverick are both
mixture-of-experts models from adjacent lineages — that critique had real force.
Llama-3.3-70B (Meta, dense) and gpt-oss-120b (OpenAI, MoE) are separated by vendor,
architecture, and training lineage, so shared-corpus inflation is a materially weaker
objection. The forced swap strengthens the ordering-invariance test rather than
weakening it. `gpt-oss-20b` is available as a within-family scale pair if Phase 1
wants one.

Decoding: temperature 0.7, top_p 1.0, **max_tokens 2048**, no system prompt beyond
the benchmark's standard instruction. **P̂ is defined relative to this decoding
config** — a scope statement to carry into the paper, not a flaw. The generation
script writes the config to `results/phase05/decoding_config.json` and refuses to
resume across a change, because appending completions from a different config to the
same file would silently mix two populations.

### 3.2 max_tokens is set from measurement, and the two models differ ~7×

Probing both models at a generous 1536-token cap (2026-08-25, 15 prompts each spread
across categories) gave:

| | Llama-3.3-70B | gpt-oss-120b |
|---|---|---|
| p50 completion tokens | **96** | **699** |
| p90 | 555 | 1536 |
| max | 595 | 1536 |
| Still hit the 1536 cap | 0/15 | **3/15** |

**max_tokens=2048** covers gpt-oss's p90 with headroom and leaves Llama untouched.
The original 256 truncated gpt-oss mid-sentence on most prompts; because the judge
scores a truncated answer *as* the model's answer, and the two models truncate at
different rates, that error lands asymmetrically and corrupts the ranking comparison.
A single shared value is deliberate — an identical decoding config across models is
what makes the two P̂ estimates comparable.

**The ~7× verbosity gap is a confound in its own right, not just a sizing problem.**
A longer answer has more opportunities to trip the judge's hallucination rule, so
gpt-oss's P̂ may be inflated by verbosity rather than by worse factual reliability.
If verbosity were constant per model this would shift *rates* and leave *ordering*
intact — which is all the paper's claim needs. It is not constant: on `nonexistent`
prompts (a primary decision-surface category) Llama wrote ~90 tokens both times while
gpt-oss wrote 1536 and 1533, and both models scale length by category differently.
Prompt-dependent, model-specific verbosity can therefore distort the ordering itself.
Checked in §6.5.4; logged as limitation §9.13.

`finish_reason` and `output_tokens` are recorded per completion so truncation is
**measured**, not inferred. `MultiModelClient.generate()` discards both, which is why
`generate_with_meta()` exists.

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

**Judge model: `claude-haiku-4-5` on the Anthropic API** (provider `anthropic` in
`judge_client.py`, which already has a working Anthropic branch). $1.00 / $5.00 per
million input / output tokens — the cheapest Anthropic model, and third-family to
both evaluated models. Verified against current model data 2026-08-25.

**Why not a Together-hosted judge.** Together's serverless tier on this account has
exactly three chat models (§3): one Meta and two OpenAI open-weight. Any judge chosen
from that set shares a family with one of the two evaluated models, so the §5
independence requirement is **unsatisfiable within Together**. Every Qwen build —
the original third-family candidate — is dedicated-endpoint-only. Going outside
Together for the judge is what makes the family constraint satisfiable at all.

**Why the family constraint is worth paying ~$27 for.** Family-level self-preference
in LLM-as-judge setups is documented (Panickssery et al. and others). If the judge
shared a family with one evaluated model, that model's P̂ would be biased
*asymmetrically* — and differential per-model judge error is precisely the error mode
that corrupts a cross-model *ranking* comparison. It does not average out. Anthropic
is equidistant from Meta and OpenAI.

**Why not Sonnet 5 or a larger judge:** $3.00 / $15.00 per million puts the same
volume near $80. Haiku 4.5's adequacy is an empirical question, and §5.2 is the test
that answers it — if per-model agreement is poor or unequal, escalate the judge then
rather than pre-paying for capability the task may not need.

**Prompt caching does not apply.** The judge system prompt is identical across all
28,160 calls, but Haiku 4.5's minimum cacheable prefix is 4096 tokens and the prompt
is well under that — a `cache_control` marker would silently do nothing. Do not add
one.

**Requires `ANTHROPIC_API_KEY` in `.env`** and the `anthropic` package installed
(now added to `requirements.txt`; it was previously imported but undeclared). Note
this is the only part of the pilot that is *not* covered by the Together balance —
it bills to the Anthropic account separately.

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
4. **Completion-length and truncation.** The two models differ ~7× in natural
   completion length and the gap varies by prompt within category (§3.2).

   **Do NOT residualize P̂ on completion length.** An earlier draft of this section
   specified exactly that, and it was wrong. Length here is not a confounder sitting
   beside the outcome — it is a **consequence** of it: the model writes at length
   *because* it is confabulating. Measured 2026-08-25: on `nonexistent` prompts
   gpt-oss's median completion is 2048 tokens (hitting the cap) against Llama's 85.
   Residualizing on a mediator strips real signal rather than nuisance variance, and
   would have driven τ_corr down spuriously — i.e. manufactured a false NO-GO.

   The real question is measurement error, not confounding: **does truncation change
   the label?** Report:
   - **Label-neutrality test (primary).** For prompts that produced *both* truncated
     and complete samples, compare the hallucination-label distribution between them
     **holding the prompt fixed** (Fisher exact per prompt; pooled across such prompts
     with a Cochran–Mantel–Haenszel test). No difference ⇒ truncation is label-neutral
     and the confound is closed. This costs no extra API calls — it falls out of the
     judged data.
   - **Coverage caveat.** Prompts truncated on *every* sample admit no within-prompt
     contrast (`nonexistent_001` was 20/20 in the smoke test). Report how many prompts
     fall in that class; they are untestable by this method and must be named.
   - **Descriptive only:** the association between `output_tokens` and the
     hallucination label, per model, within category — reported as a finding about
     confabulation behaviour, explicitly **not** used as a control.
   - Truncation rate per model from `finish_reason == "length"`, with the per-category
     breakdown.

   Why `max_tokens` is not raised further to chase this: at 2048 a model that is still
   generating has already committed to its answer, so truncation is very unlikely to
   flip a label — unlike at 256, where a model could be cut off before reaching its
   disclaimer. Raising the cap roughly doubles judge input cost for no measurement
   gain.

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
2 models = **28,160 completions**, plus one judge call each.

| Stage | Provider | Estimate |
|---|---|---|
| Generation (28,160 completions; Llama ~160 tok avg, gpt-oss ~800 tok avg ≈ 13M output tokens) | Together, open-model rates | **~$5–9** |
| Judging (28,160 calls. Input = 628-token judge system prompt + ~55 prompt/ground-truth + the completion ≈ 33M input; output ~3.4M. `claude-haiku-4-5` at $1/$5 per M) | Anthropic | **~$50** |
| | | **~$55–60 total** |

**Two separate bills.** The $56 Together balance covers generation with wide margin;
the judge bills to the Anthropic account. Verify per-token pricing before the run.

This is roughly double the earlier estimate, for two reasons, both worth stating:
`max_tokens` rose from 256 to 2048 so completions are much longer (§3.2), and the
earlier figure omitted the **628-token judge system prompt, which is re-sent on all
28,160 calls** — about 17.7M input tokens on its own.

**The Anthropic Batch API is now worth considering rather than not:** 50% off token
cost, and this workload is entirely offline, which would bring judging to ~$25 and the
total to ~$32. It is still not in the design because batch results arrive
asynchronously and the §5.1 per-call retry contract has to be reworked around them —
but at Phase 1 volume that rework pays for itself.

**Prompt caching remains unavailable.** The judge system prompt is identical across
all calls, but at 628 tokens it is far below Haiku 4.5's 4096-token minimum cacheable
prefix, so a `cache_control` marker would silently do nothing.

**Wall clock.** The 256-token smoke test sustained 1.2 completions/sec (8 workers).
Throughput scales roughly inversely with output length, so at `max_tokens=2048` expect
substantially slower — plan an overnight run for the full 28,160, not an afternoon.

**Cost is not the binding constraint on this pilot.** The earlier
100-prompt/k=10 design sacrificed statistical power for savings that do not exist.

Time: 1–2 days of wall clock, dominated by rate limits, plus ~2 hours of
hand-labelling for §5.2.

---

## 9. Known limitations to put in front of Sunny

State these before she finds them:

1. **Two open models with overlapping pretraining data.** Agreement may be
   inflated by shared corpora. Necessary-but-not-sufficient; a low result is far
   more informative than a high one (§1). **Weaker than it was under the original
   model pair** — Llama-3.3-70B (Meta, dense) and gpt-oss-120b (OpenAI, MoE) are
   separated by vendor, architecture, and training lineage, where Mixtral and
   Llama-4-Maverick were both MoE from adjacent lineages (§3.1).
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
11. **Neither evaluated model is a thesis model** (§3.1). Both thesis models are
    dedicated-endpoint-only on Together, so direct continuity with the thesis is lost
    and no thesis-era rate may be compared against this pilot's.
12. **The judge is a different vendor from both evaluated models, but is also the
    cheapest model in its line.** Independence is bought at the cost of judge
    capability; §5.2 is the check on whether that trade held.
13. **The two models differ ~7× in natural completion length** (§3.2), and the gap is
    prompt-dependent within category. A verbose model has more chances to trip the
    judge's hallucination rule, so part of the measured P̂ difference — and possibly
    part of the ordering — may be a verbosity artifact. §6.5.4 tests this; if τ_corr
    survives length residualization the claim stands, and if it does not the honest
    report is that the pilot measured verbosity agreement.
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
- 2026-08-25 (still pre-data) — **§3 and §5 rewritten: all three models replaced.**
  The prior amendment relied on `/v1/models` to confirm availability. That was wrong:
  the endpoint lists every model Together knows about, including dedicated-endpoint-
  only ones. Probing each candidate with a real 1-token request showed Together's
  serverless tier on this account offers **exactly three chat models** —
  `meta-llama/Llama-3.3-70B-Instruct-Turbo`, `openai/gpt-oss-120b`,
  `openai/gpt-oss-20b`. Both previously pinned evaluated models
  (`Mixtral-8x7B-Instruct-v0.1`, `Llama-4-Maverick-…-FP4`) and **every** Qwen build
  return `400 model_not_available`.

  Changes: Model A → `meta-llama/Llama-3.3-70B-Instruct-Turbo`, Model B →
  `openai/gpt-oss-120b`. Judge moved off Together entirely to
  **`claude-haiku-4-5`** on the Anthropic API — with only Meta and OpenAI available
  on Together's serverless tier, the §5 family-independence requirement is
  unsatisfiable there, so a third vendor is the only way to keep it. Cost model
  rewritten (§8): ~$4 generation on Together, ~$27 judging on Anthropic, two separate
  bills. `anthropic` added to `requirements.txt` (previously imported but undeclared);
  `ANTHROPIC_API_KEY` now required in `.env`.

  Consequences logged rather than buried: **neither evaluated model is a thesis
  model** (§3.1, limitation §9.11), so continuity with the thesis is gone. Against
  that, the new pair is separated by vendor, architecture, and training lineage where
  the old pair were both MoE from adjacent lineages — which materially weakens
  limitation §9.1, the pilot's central critique. The forced swap strengthens the
  ordering-invariance test.

  The family guard in `run_phase05_judging.py` now derives forbidden family tokens
  from the models actually present in the completions file rather than a hardcoded
  list, so it cannot drift out of sync with §3 again. Still no data collected; the §7
  go/no-go rule is unchanged.
- 2026-08-25 (after a 400-completion smoke test; **no pilot data**) — **§3 decoding
  config corrected from measurement.** A 10-prompt smoke test showed completions being
  truncated mid-sentence at `max_tokens=256`. Probing both models at a 1536-token cap
  established why: natural completion length differs ~7× at the median (Llama p50=96,
  gpt-oss p50=699, gpt-oss still hitting the cap on 3/15). `max_tokens` raised
  **256 → 2048**, set from gpt-oss's p90 plus headroom, kept as a single shared value
  so the decoding config stays identical across models.

  Two errors of mine are recorded here because both distorted the earlier reading.
  First, `--limit N` took the first N of a `(category, id)`-sorted manifest, so the
  smoke test drew **100% `ambiguous`** prompts — one of seven categories, and Llama's
  most verbose one. That made a gpt-oss-specific truncation problem look symmetric and
  led me to report Llama as "pinned at the cap on 76% of prompts" when its overall
  natural median is 96 tokens. `--limit` now samples round-robin across categories.
  Second, truncation was being *inferred* from trailing punctuation because
  `MultiModelClient.generate()` discards `finish_reason`; a new `generate_with_meta()`
  records `finish_reason` and `output_tokens` per completion, and the generation script
  reports truncation rate per model and warns above a 5-point gap.

  New confound check **§6.5.4** covers the verbosity asymmetry, which is a threat in
  its own right and not merely a sizing problem: a longer answer has more chances to
  trip the judge's hallucination rule, and the length gap varies by prompt *within*
  category (on `nonexistent`, Llama ~90 tokens vs gpt-oss ~1535). The check
  residualizes P̂ on per-prompt mean completion length and recomputes τ_cross; if
  τ_corr collapses, the honest report is that the pilot measured verbosity agreement
  rather than prompt-difficulty agreement. Logged as limitation §9.13.

  A decoding-config fingerprint (`results/phase05/decoding_config.json`) is now written
  and checked, so resuming across a config change fails loudly instead of appending a
  second population to the same file. The 400 smoke-test completions were generated at
  `max_tokens=256` and have been deleted rather than resumed across.

  Cost estimate updated (§8): ~$55–60, roughly double the prior figure — longer
  completions plus the 628-token judge system prompt re-sent on all 28,160 calls,
  which the earlier estimate omitted. Progress reporting cadence made adaptive so short
  runs report and a slow run is distinguishable from a wedged one.

  **No pilot data has been collected.** The §7 go/no-go rule is unchanged.

- 2026-08-28 — **Phase 0.5b pre-registered (new §11). Post-data for Phase 0.5, PRE-data
  for Phase 0.5b.** Phase 0.5 returned NO-GO (τ_corr = 0.3098, CI [0.1913, 0.4467]) and
  the diagnosis is a floor effect in the V3 benchmark, not an absent signal: Llama sits
  at exactly P̂ = 0 on 86% of `nonexistent` and 49% of `borderline_plausible_fake`,
  while coarse category-level agreement is τ_b = 0.905. §11 re-runs the identical
  estimator and the identical §7 thresholds on TruthfulQA, which supplies real sourced
  ground truth and graded within-category difficulty.

  Nothing in §§1–9 is modified. Phase 0.5's NO-GO stands as recorded and is reported as
  the pilot's result regardless of what §11 returns; §11 is a **replication on a second
  benchmark**, not a re-analysis and not a second chance at the same test.

  Also in this amendment, and affecting §5 rather than §11 alone: **judge rubric v2**
  (`JUDGE_RUBRIC_VERSION = "v2-2026-08-28"`), forced by the §5.2 hand-labelling result.
  Three edits, all to the written rules and none to the judge model, because §5.2
  showed the disagreement was rubric ambiguity that a stronger judge cannot resolve:
  (1) for a fabricated entity, declining *because the entity cannot be found* is pinned
  to CORRECT (0) and REFUSAL (3) is reserved for a bare no-reason refusal — this single
  cell was 50 of 150 hand-labelled items; (2) a new rule for correct-rejection-then-
  unmarked-fabrication, pinned to HALLUCINATION (2), with a new
  `mixed_rejection_then_fabrication` output flag so the §6.1 label-boundary sensitivity
  on that choice is computable without re-judging; (3) a new **CATEGORY 5** for sourced
  reference answers, required because TruthfulQA's three-part ground truth had no rule
  and fell through to CATEGORY 3, which told the judge to consult "established reality"
  and ignore the authoritative known-incorrect list.

  Consequence recorded rather than buried: **Phase 0.5's 28,160 judgments and its 150
  §5.2 hand-labels were all produced under v1 and are not comparable to v2 labels.**
  Every label now carries `rubric_version`; `run_judge_validation.py --score` refuses to
  pool across versions. Phase 0.5 is **not** re-judged under v2 — doing so would
  replace a pre-registered result with a post-hoc one. The v1 §5.2 figures stand as the
  validation of the v1 run, and §11 requires fresh validation under v2.

---

## 11. Phase 0.5b — TruthfulQA replication (pre-registered 2026-08-28, pre-data)

### 11.0 Why, and what is being held fixed

Phase 0.5 could not test its own claim. τ asks whether two models *order prompts by
difficulty the same way*, which presupposes that prompts differ in difficulty and that
both models fail on enough of them to be ordered. On the V3 primary set one model
almost never failed. The §7 verdict is therefore correct as a verdict about that
benchmark and uninformative as a verdict about the claim.

Phase 0.5b changes **the prompt set and nothing else that bears on the decision.** The
estimator (§6.1–§6.7), the thresholds (§7), k = 20, the decoding configuration (§3.2),
the judge failure contract (§5.1) and the blinding protocol (§5.2) are all carried over
verbatim. This is deliberate: if the two runs disagree, the prompt set is the only
candidate explanation, which is the entire scientific point.

**Disclosure — what was seen before this pre-registration.** A feasibility probe
(`scripts/probe_truthfulqa_rates.py`, 80 of the 817 prompts, k = 10, rubric v1) was run
on 2026-08-27/28 and its thresholds were **not** pre-registered. It measured, on those
80 prompts: mean P̂ (0.295 Llama / 0.219 gpt-oss), the fraction at exactly 0 (55% /
61%), a chi-square dispersion ratio (pooled 8.02 / 7.04; within-category 4.81 / 4.49),
and the tie-asymmetry ceiling on max τ_cross (0.963 pooled, 0.981 blocked). **τ_cross,
τ_self and τ_corr were not computed on probe data and must not be, at any point before
the full run is judged.** So the decision statistic is unseen, but the marginals are
seen on ~10% of the prompt set. The 80 probe prompts are **retained** in the 0.5b set —
excluding them would bias the set toward prompts never screened — and probe completions
are **discarded**, not reused, being k = 10 and rubric v1.

### 11.1 Prompt set

`data/prompts/truthfulqa.jsonl` — all **817** prompts, 38 native categories, taken
whole. No sampling, no filtering, no top-up, so there is no construction rule to
get wrong and nothing to dedupe against a training set.

Ground truth is TruthfulQA's own three-part reference:
`Best answer: … / Also acceptable: … / Known incorrect answers: …`. This satisfies
the §4.0 verifiability criterion **uniformly**, which the V3 categories did not: the
judge is given the sourced answer set rather than being asked to consult its own
parametric knowledge. Judged under rubric v2 CATEGORY 5.

Two properties that motivated the choice and should be stated as such, since neither
is a result: TruthfulQA is adversarial by construction (questions were selected
*because* models fail them), which is why an intermediate rate is expected rather than
hoped for; and it is public, which forecloses the otherwise fatal objection that the
critique and the benchmark share an author.

### 11.2 Strata — decided before data, deliberately the conservative choice

Category sizes are severely unbalanced (100 `Misconceptions` down to 4
`Misconceptions: Topical`, median 15), so the blocking level had to be fixed in advance.

**Primary strata = the 38 native TruthfulQA categories.** 14,831 blocked
within-category pairs. Not the largest available number of pairs, and chosen anyway:
finer blocking admits less between-category difficulty variance into τ, so it is the
conservative option, and **coarsening strata can only raise τ.** Pre-committing to the
finer blocking forecloses the accusation that the strata were loosened until the number
cleared §7.

The §6.7 degenerate rule costs almost nothing at this level, which is what made the
conservative choice affordable: the 8 categories with n < 10 hold 59 prompts and 203
pairs, **1.4% of blocked pairs**, so even if every one of them is dropped the primary
estimate is essentially unaffected. Exclusions are logged with distinct-value counts as
§6.7 requires.

**A coarse 13-stratum merge is ALSO pre-specified, as a secondary only.** It is
reported next to the primary and is *never* the decision statistic under any outcome.
Its purpose is §6.3: the ladder pooled → coarse-13 → native-38 measures how much
stratification inflates τ, on a benchmark where the strata are externally defined
rather than ours. The map is fixed here, in full, so it cannot be tuned after seeing
data (verified to be a strict partition of all 38 categories, 817 prompts):

| Coarse stratum | n | Native categories merged |
|---|---|---|
| Misconceptions | 116 | Misconceptions; Misconceptions: Topical; Misinformation |
| Sociology & Stereotypes | 79 | Sociology; Stereotypes |
| Law & Politics | 74 | Law; Politics |
| Paranormal & Conspiracies | 73 | Paranormal; Conspiracies; Superstitions |
| Health & Nutrition | 71 | Health; Nutrition |
| Fiction & Folklore | 69 | Fiction; Myths and Fairytales; Proverbs |
| Indexical Error | 57 | Indexical Error: Other / Time / Location / Identity |
| Science & Psychology | 55 | Science; Education; Weather; Psychology |
| Reasoning & Subjectivity | 52 | Logical Falsehood; Distraction; Subjective; Religion |
| Confusion | 46 | Confusion: People / Places / Other |
| History & Quotation | 46 | History; Misquotations; Mandela Effect |
| Economics & Finance | 45 | Economics; Finance; Statistics |
| Language & Advertising | 34 | Language; Advertising |

### 11.3 What is NOT carried over

- **§6.2b Δ_artifact is not recomputed.** It requires a non-verifiable comparison arm,
  and TruthfulQA has none by construction — every prompt is verifiable, which is the
  reason for using it. The Phase 0.5 value (Δ_artifact = +0.118) stands as the estimate
  and is reported as coming from the V3 run. No judge-bound set is generated for 0.5b.
- **§4.1–§4.5 construction rules** are void here; §11.1 replaces them. The V3 manifest
  and the ground-truth defects documented in `CONTEXT.md` do not touch 0.5b.
- **The §5.2 v1 validation does not license the v2 judge.** Fresh hand-labelling under
  v2 is required before the 0.5b τ number is believed, on a fresh stratified draw.

### 11.4 Decision rule

**§7 applies verbatim and unchanged** — GO at τ_corr ≥ 0.50 with CI lower ≥ 0.30,
MEASUREMENT FAILURE at τ_self ≤ 0.40 — evaluated on τ_corr over the native-38 blocked
primary. The thresholds are not renegotiated for a benchmark chosen after seeing them.

One floor-effect check is added and pre-committed, because it is the failure mode that
made Phase 0.5 uninterpretable and it should be declared before it can be argued about:
if either model sits at exactly P̂ = 0 on more than **70%** of the 817 prompts, the run
is reported as **inconclusive on the same grounds as Phase 0.5** rather than as a
negative result, whatever τ_corr comes out at. The probe measured 55% / 61%, so this is
expected to pass; it is stated so that failing it cannot later be framed as a surprise.
Unlike §7's measurement-failure row, the remedy is not more samples — it is a harder
prompt set, and at that point the honest conclusion is that the claim is not testable
with these two models.

### 11.5 Volume and cost

817 prompts × 20 samples × 2 models = **32,680 completions**, one judge call each.

| Stage | Provider | Estimate |
|---|---|---|
| Generation | Together | ~$10, ~16 h wall clock |
| Judging | Anthropic (`claude-haiku-4-5`) | ~$70, ~3.5 h at 2.6/s |

The judging figure is above the ~$50 previously carried in the plan for two reasons
worth naming: rubric v2 roughly doubled the judge system prompt (628 → ~1,270 tokens,
re-sent on all 32,680 calls, ~$20), and TruthfulQA's three-part ground truth is longer
than V3's one-line assertion. Prompt caching remains unavailable — Haiku 4.5's minimum
cacheable prefix is 4,096 tokens and the v2 system prompt is ~1,270. **Check the
Anthropic balance before starting:** the Phase 0.5 judging run silently exhausted credit
at row 1,896 and returned 33% of the run unlabelled.
