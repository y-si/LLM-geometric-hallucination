# Paper Plan

Working document for turning the thesis into a research paper. Sibling to `RESEARCH_PAPER.md` (which holds the meeting notes + raw priority lists). This file is the synthesized plan: what we're building, in what order, and why.

**If you're a fresh Claude Code session, read `CONTEXT.md` first.**

---

## 1. The reframing (from Boaz, May 1, 2026)

The paper is **NOT** "geometric features explain hallucination across 10 models." It is:

**Pitch**: *Predicting hallucination risk before generation, using prompt-level geometric features.*

- Geometry = tool. Prediction = goal.
- Three contributions, in this order:
  1. **Benchmark dataset** for evaluating *pre-generation* hallucination prediction
  2. **Geometric method** — computationally efficient (no sampling, no internal states required)
  3. **Practical applications**: inference-time flagging, training data curation, model routing
- **Must beat (or Pareto-dominate) baselines.** Frame as "here are existing approaches, here's something better or complementary."

Consequences for the existing thesis material:
- The fine-tuning chapter (thesis Ch 7) is demoted from co-equal claim to a **downstream application** subsection.
- Within-category density is the lead signal. Oppositeness and NN-distance become ablation rows.
- The three-claim arc of the thesis collapses into one claim with applications.

## 2. The load-bearing experiment

**"Prompt difficulty ordering is largely model-invariant."** Rank prompts by their probability of eliciting a hallucination, and different models produce substantially the same ranking.

Do **not** write this as "hallucination is a property of the prompt, not the model." That version is false as stated — models differ substantially in absolute hallucination *rate*, and a reviewer will quote it back at you. Rate-level divergence coexists with ordering agreement; the paper's prediction story needs only the latter, and we report the rate differences explicitly.

Design (Boaz's spec, corrected for the confounds in `PHASE_0.5_SPEC.md` §2):
1. Take 100–1000 prompts, 5–10 models
2. For each (prompt, model) pair: sample multiple completions → estimate *P(hallucinate)* per prompt per model
3. For each model: sort prompts by hallucination probability
4. Compute pairwise **blocked within-category Kendall's τ_b** between model orderings, attenuation-corrected against a measured within-model noise ceiling

Three corrections to Boaz's sketch, all load-bearing:
- **Within-category, not pooled.** Pooled tau across heterogeneous categories mostly measures benchmark stratification — every model agrees that impossible prompts are harder than factual ones. Report pooled tau for transparency, never as the test.
- **τ_b, not τ_a.** P̂ takes at most k+1 distinct values, so ties are pervasive.
- **Correct for finite-k attenuation.** Sampling noise biases observed tau downward, so absolute thresholds are uninterpretable without a measured ceiling.

This is the load-bearing claim for the entire paper. If corrected tau is low, the "predict-before-generate" framing collapses and we need to reframe. **Run this first**, as the 2-model Phase 0.5 pilot, before scaling.

## 3. What needs to be built

### High-priority new work
1. **Kendall's tau experiment** (above) — load-bearing, runs first
2. **More models**: 2 → 5–10. Mix of scales/families and open/closed. Credits are in hand.
3. **Baseline comparisons** against existing hallucination detectors:
   - Semantic entropy (Kuhn et al., Nature 2024)
   - P(true) (Kadavath et al., 2022)
   - Self-consistency / sampling-based
   - Probe-based (internal representations) — harder for closed models
   - Frame on the Pareto frontier (cost × pre-gen vs. post-gen × signal quality)
4. **External dataset(s)** beyond our benchmark + TruthfulQA. Candidates: SimpleQA, PopQA, FreshQA.
9. **Ground-truth verifiability as a benchmark design criterion** — promoted from caveat to candidate contribution. Our own benchmark's `factual` and `borderline_obscure_real` categories have ground_truth fields containing no embedded facts, so any judgment on them measures model–judge disagreement rather than hallucination (see `CONTEXT.md`). Phase 0.5 measures the effect size directly (Δ_artifact, `PHASE_0.5_SPEC.md` §6.2b). Framing: *existing benchmarks conflate hallucination with disagreement-with-judge-knowledge; here is the effect size, and here is verifiability as a design criterion.* This is a paper section, not a limitations bullet.

### Structural rewrites
5. **8-page discipline.** Density leads; everything else is ablation or appendix.
6. **"Model harness" framing**: package the pipeline as a named, reusable artifact.
7. **Related work positioning** against the Feb–Mar 2026 geometry+hallucination burst (Liu, Marín, Korun, Phillips). Our differentiator: **pre-generation, from input embedding alone.**
8. **Composite geometric risk score**: single calibrated predictor combining density + oppositeness + NN-distance.

### Deprioritized (Boaz did not push)
- Theory proposition — proceed as empirical paper
- Causal embedding intervention — separate paper
- Fine-tuning scaling curves — secondary

## 4. Logistics

- [~] Boaz credits received — **deduced to be Codex (coding agent), NOT OpenAI API platform. UNCONFIRMED.** The inference is from the product name plus typical OpenAI billing structure; Boaz has not confirmed it. If correct, credits help build the experiment faster (Phase 0–3 development) but do not pay for GPT-5.5 inference calls. Until confirmed, treat the entire closed-model panel as unfunded.
- [x] **Sunny re-engagement email sent** (~Aug 24, 2026). Awaiting response.
- [ ] **Send Boaz email about credits** (Codex vs. API platform; Anthropic/Google institutional access). Draft ready — see `CONTEXT.md`.
- [ ] Venue: see `DEADLINES.md`. **ICML 2027 (~late Jan 2027 est.) is the honest primary target.** ICLR 2027 was a stretch gated on Phase 0.5 + advisor replies landing in the first week of September; that didn't happen.

---

## 5. Phased roadmap (broad strokes)

Phases are sequenced by dependency, not by calendar. Phases 3 and 4 can parallelize with Phase 2 once Phase 1 lands.

### Phase 0 — Setup
*Goal: unblock everything else.*
- [x] Re-engage Sunny — email sent Aug 24
- [ ] Clarify Boaz's credit scope — draft email in `CONTEXT.md`; send today
- [ ] Verify actual venue deadlines (see `DEADLINES.md`)
- [ ] Lock the model panel (proposal below; **may need to drop OpenAI models if API access isn't covered**)
- [ ] Pick the external dataset to port to — leading candidate: **PopQA** (matches our entity-obscurity framing)

**Currently reachable panel: `Llama-3.3-70B-Instruct-Turbo` + `gpt-oss-120b` (+ `gpt-oss-20b`). That is three models, and it is a hard ceiling, not a budget choice.** Verified 2026-08-25 by probing with real requests: Together's serverless tier on this account serves exactly those three chat models. **Both thesis models — Mixtral 8x7B and every Llama-4-Maverick build — are dedicated-endpoint-only**, which bills per running minute and is the wrong economics for batch evaluation. Every Mistral, Qwen, Gemma, GLM, and DeepSeek build is likewise dedicated-only.

Two consequences: (1) the panel cannot be widened on Together no matter what the budget is — additional breadth requires closed-model API access, i.e. the Boaz credit reply and any Harvard institutional access; (2) a judge that shares no family with the evaluated models is **unsatisfiable within Together**, so Phase 0.5's judge runs on the Anthropic API. The 8-model table below is a proposal, not a plan of record.

One anomaly worth a support ticket in parallel: `Qwen2.5-72B-Instruct-Turbo` is normally serverless on Together for everyone, which suggests an account-tier restriction rather than a catalog change. Unknown latency — do not block on it.

**Working model panel proposal (8 models, June 2026 SOTA):**

| Tier | Model | Role |
|---|---|---|
| Frontier closed | Claude Opus 4.8 | Anthropic frontier |
| Frontier closed | GPT-5.5 Thinking | OpenAI frontier (reasoning) |
| Frontier closed | Gemini 3.1 Pro | Google frontier |
| Mid-tier closed | Claude Haiku 4.5 | Cheap/fast Anthropic |
| Mid-tier closed | GPT-5.5 Instant | Cheap/fast OpenAI; pairs with Thinking for reasoning ablation |
| Mid-tier closed | Gemini 3.5 Flash | Cheap/fast Google |
| Frontier open | Llama 4 Maverick | ~~Continuity with thesis~~ — **dedicated-endpoint-only on Together as of 2026-08-25; not reachable on serverless.** Replace with `Llama-3.3-70B-Instruct-Turbo` |
| Small open | Llama 3 8B *or* Qwen 3 7B | Diversity tail; needed for probe baseline. **All Qwen builds are dedicated-only** — `gpt-oss-20b` is the reachable small-open option |

Notes:
- **Skip Fable 5** — 2× Opus pricing makes multi-sample eval prohibitive.
- **GPT-5.5 Thinking + Instant pair** is a free secondary result: tests whether extended reasoning changes the prompt-difficulty ordering or just shifts hallucination rates.
- **Lock to current model versions** — don't chase GPT-5.6 / Llama 5 news. Note newer variants as future work.
- Full SOTA snapshot mirrored into `CONTEXT.md` (source: `~/.claude/projects/.../memory/current_models.md`, does NOT sync via git).

### Phase 0.5 — Kendall's tau pilot (2-model sanity check)
*Goal: cheap early signal on whether the paper's premise holds. Runs while waiting on Sunny + Boaz.*

**Full design is pre-registered in `PHASE_0.5_SPEC.md` (2026-08-24, written before any data exists). That document is authoritative; this is a summary.**

Models: `meta-llama/Llama-3.3-70B-Instruct-Turbo` (Meta, dense) and `openai/gpt-oss-120b` (OpenAI, MoE) via Together serverless — **neither is a thesis model**, because both thesis models are dedicated-endpoint-only (spec §3.1). Continuity with the thesis is lost; in exchange the new pair is separated by vendor, architecture, and training lineage where Mixtral and Maverick were both MoE from adjacent lineages, which materially weakens the pilot's central "shared pretraining data inflates agreement" critique.

- **Claim under test**: *prompt difficulty ordering is largely model-invariant.* (NOT "hallucination is a property of the prompt, not the model" — that version is false as stated; models differ substantially in absolute rate, and the pilot measures that too.)
- **Prompts**: 409 across the three *verifiable* categories (`borderline_plausible_fake` n=169, `nonexistent` n=120, `ambiguous` n=120), drawn from V3 (the held-out test set, 431 unique, verified zero overlap with V5 train) plus V5-train-clean top-up from the standalone pool files. Deduplicated on question text. **Category admission turns on ground-truth verifiability** — `factual` and `borderline_obscure_real` are excluded from the decision surface because their ground_truth contains no facts, making the judge fall back on its own knowledge and correlating both models' scores through a shared referent (spec §4.0). They are run separately as a labelled artifact diagnostic (§4.2, §6.2b). `borderline_edge_factual` is excluded as well (n_eff=5 unique in V3, floor effect) and kept only as a degenerate-variance control; `impossible` is excluded for thin n=30.
- **k=20** samples per (prompt, model) at T=0.7 — attenuation is driven by k, and cost is not the constraint.
- **Judge**: `claude-haiku-4-5` on the **Anthropic API**, not Together. With only Meta and OpenAI models on Together's serverless tier, a judge sharing no family with either evaluated model is unsatisfiable there — and family self-preference would bias one model's P̂ asymmetrically, which does not average out in a ranking comparison. ~$27 for the run, billed separately from the $56 Together balance. Requires `ANTHROPIC_API_KEY`. Inherits the March 2026 failure rule: failed judge calls are never assigned a label and never counted.
- **Cost**: ~$4 generation (Together) + ~$27 judging (Anthropic) ≈ **$31**, across two separate bills.
- **Primary statistic**: blocked **within-category** τ_b (only same-category prompt pairs counted; 28,476 pairs), attenuation-corrected against a within-model split-half noise ceiling. Nested bootstrap over prompts *and* completions, 1000×.
- **Reported alongside**: (i) Δ_artifact = τ_corr(judge-bound categories) − τ_corr(verifiable categories), a direct effect-size estimate of the shared-judge artifact; (ii) pooled τ_b on all 7 V3 categories, explicitly labelled stratification-inflated. Neither gates the decision. Both are candidate paper figures.

**Pre-registered decision rule** (binding; see spec §7 for the derivation of the thresholds):
- **GO** to Phase 1 if τ_corr ≥ 0.50 **and** bootstrap 95% CI lower bound ≥ 0.30 — i.e. at least half the variance in prompt-level difficulty is model-invariant.
- **NO-GO** otherwise: take the result to Sunny and reframe before spending on the panel.
- **MEASUREMENT FAILURE** if either model's split-half reliability ≤ 0.40 — inconclusive, *not* negative. Escalate k to 40 and re-run rather than concluding anything.

Cost: ~$15–25. Time: 1–2 days, plus ~2h hand-labelling 150 completions for judge validation.

**Why this replaced the earlier sketch**: pooled tau across 7 heterogeneous categories measures benchmark stratification, not model agreement; duplicate prompts inflate tau; the old 0.7/0.4/0.2 thresholds had no derivation and ignored finite-k attenuation; the specified judge (`GPT-5.5-mini`) does not exist and OpenAI access is unfunded; and the prompt source was wrong (V5 is train, V3 is test). Full reasoning in spec §2.

**Deliberate caveats to acknowledge with Sunny** (full list in spec §9):
- 2 open models trained with similar data may have inflated agreement (necessary-but-not-sufficient test)
- Low tau on this pilot is more informative than high tau
- Pilot is a sanity check, not a validation
- Primary decision surface is 2 borderline categories only; generalization untested

### Phase 1 — Prompt-vs-model experiment at scale (load-bearing)
*Goal: establish that prompt difficulty ordering is largely model-invariant across a heterogeneous panel.*
- **Entry condition: Phase 0.5 returned GO** under the pre-registered rule in `PHASE_0.5_SPEC.md` §7. Do not start otherwise.
- **Blocking prerequisite**: the `factual` and `borderline_obscure_real` categories need real sourced ground truth or a retrieval-augmented judge before Phase 1 can use them at all. Their current ground_truth fields contain no facts, making any judgment judge-parametric-knowledge-bound (see `CONTEXT.md`). Phase 0.5 works around this by excluding them from its decision surface; Phase 1 cannot, if it wants to claim coverage of factual and obscure-entity prompts.
- Extend the pilot to the full 5–10 model panel (**funding-gated — currently 2 models**)
- 500 prompts (still stratified), k=20 samples — inherit the pilot's estimator, not Boaz's original sketch
- Full judge pipeline (3-judge consensus or single judge — decide with Sunny). Third-family judge requirement carries over: the judge must not share a model family with any panel member.
- Compute the pairwise blocked within-category τ_b matrix, attenuation-corrected, with nested-bootstrap CIs
- **Go/no-go decision rule must be pre-registered before the run**, the same way Phase 0.5's was. With an 8-model panel that means 28 pairs — state the aggregate statistic (e.g. minimum corrected pairwise tau, not mean) and the threshold *before* seeing data.

### Phase 2 — Geometric prediction at scale
*Goal: show density predicts the prompt-level P(hallucinate) from Phase 1.*
- **Recompute, do not reuse.** Any factual-adjacent analysis that reaches the paper must be recomputed from scratch — thesis-era judgments on the `factual` and `borderline_obscure_real` categories are judge-parametric-knowledge-bound (see `CONTEXT.md`).
- Extract input embeddings across the panel
- Compute density + other geometric features per prompt
- Regress P(hallucinate) on geometric features — per-model and pooled
- AUC for binary "high-risk prompt" classification
- Construct composite geometric risk score; calibrate (ECE, reliability diagrams)

### Phase 3 — Baselines (parallelizable with Phase 2)
*Goal: position against existing methods.*
- Implement semantic entropy (NLI clustering, k samples)
- Implement P(true) (post-gen self-eval)
- Implement self-consistency
- Probe-based if feasible
- Comparison table: AUC, compute cost, pre- vs. post-generation, complementarity

### Phase 4 — External dataset transfer (parallelizable with Phase 2/3)
*Goal: rule out the "this only works because we built the benchmark" critique.*
- Port pipeline to chosen external dataset (PopQA leading)
- Replicate density → P(hallucinate) prediction
- Replicate baselines comparison on this dataset

### Phase 5 — Downstream applications
*Goal: demonstrate the "practical" pillar.*
- Inference-time flagging: ROC for prompt-level gate
- Training data curation: filter by geometric features, compare downstream fine-tune quality (thesis Ch 7 work re-enters here, demoted)
- (Optional) Model routing: high-risk prompts → stronger model

### Phase 6 — Writing
- 8-page NeurIPS-format draft (style files to be fetched from the official venue site — the old `thesis_reference/` pointer was stale, that directory is not in the repo)
- Related work positioning vs. concurrent work
- Sunny review pass
- Boaz review pass
- Submit

---

## 6. Honest timeline notes

Today: **end of August 2026** (~Aug 24). We are ~4 months post-Boaz-meeting. Not "on schedule" but not catastrophic — post-grad summer lulls are normal. What matters is the reset from here.

- **NeurIPS 2026 workshops**: most deadlines already passed or imminent. Check `DEADLINES.md` for any late ones. Not the primary target.
- **ICLR 2027 main (~early Oct)**: **effectively off the table.** The sprint was gated on the pilot landing clean and both advisors replying within the first week of September. Neither happened. Retained only as an opportunistic option if the pilot returns a strong GO in the next few days.
- **ICML 2027 main (~late Jan)**: ~22 weeks out. Comfortable, full experimental program. **This is the primary target.**

What's NOT on the table: skipping Phase 0.5, or overriding a NO-GO from its pre-registered decision rule because of deadline pressure. The corrected tau result has to land before we commit hard to the framing.

## 7. Open questions to resolve before Phase 1

Resolved for the pilot in `PHASE_0.5_SPEC.md`; still open for Phase 1:

- Sample budget per prompt — **pilot uses k=20** (attenuation is driven by k and cost is negligible on open models). Revisit for closed models where per-token cost actually binds.
- Final model panel composition (depends on Boaz credit clarification + institutional access)
- Hallucination judging at scale: reuse the 3-judge consensus or a single third-family judge? Whichever, the judge must not share a family with any panel member, and the failed-call contract in `CONTEXT.md` applies.
- Which external dataset (PopQA leading, alternatives: SimpleQA, FreshQA)
- Co-authorship: just Boaz + Sunny + me, or anyone else?
- Venue commitment (ICML primary — decide finally after Phase 1 result)
- Phase 1's aggregate tau statistic and threshold, pre-registered before the run
