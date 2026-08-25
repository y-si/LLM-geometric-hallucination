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

**"Hallucination is a property of the prompt, not the model."**

Design (Boaz's spec):
1. Take 100–1000 prompts, 5–10 models
2. For each (prompt, model) pair: sample multiple completions → estimate *P(hallucinate)* per prompt per model
3. For each model: sort prompts by hallucination probability
4. Compute pairwise **Kendall's tau** between model orderings
5. **High tau ⇒ hallucination propensity is prompt-driven, not model-driven**

This is the load-bearing claim for the entire paper. If tau is low, the "predict-before-generate" framing collapses and we need to reframe. **Run this first**, on existing infrastructure (2 models) before scaling.

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

- [x] Boaz credits received — **Codex (coding agent), NOT OpenAI API platform**. Helps build the experiment faster (Phase 0–3 development) but does not pay for GPT-5.5 inference calls.
- [x] **Sunny re-engagement email sent** (~Aug 24, 2026). Awaiting response.
- [ ] **Send Boaz email about credits** (Codex vs. API platform; Anthropic/Google institutional access). Draft ready — see `CONTEXT.md`.
- [ ] Venue: see `DEADLINES.md`. With end-of-August start, **ICML 2027 (~late Jan 2027) is now the realistic primary target**; ICLR 2027 (~early Oct 2026) is a stretch sprint contingent on Phase 1 landing fast.

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

**Working model panel proposal (8 models, June 2026 SOTA):**

| Tier | Model | Role |
|---|---|---|
| Frontier closed | Claude Opus 4.8 | Anthropic frontier |
| Frontier closed | GPT-5.5 Thinking | OpenAI frontier (reasoning) |
| Frontier closed | Gemini 3.1 Pro | Google frontier |
| Mid-tier closed | Claude Haiku 4.5 | Cheap/fast Anthropic |
| Mid-tier closed | GPT-5.5 Instant | Cheap/fast OpenAI; pairs with Thinking for reasoning ablation |
| Mid-tier closed | Gemini 3.5 Flash | Cheap/fast Google |
| Frontier open | Llama 4 Maverick | Continuity with thesis; weights available for probe baseline |
| Small open | Llama 3 8B *or* Qwen 3 7B | Diversity tail; needed for probe baseline |

Notes:
- **Skip Fable 5** — 2× Opus pricing makes multi-sample eval prohibitive.
- **GPT-5.5 Thinking + Instant pair** is a free secondary result: tests whether extended reasoning changes the prompt-difficulty ordering or just shifts hallucination rates.
- **Lock to current model versions** — don't chase GPT-5.6 / Llama 5 news. Note newer variants as future work.
- Full SOTA snapshot mirrored into `CONTEXT.md` (source: `~/.claude/projects/.../memory/current_models.md`, does NOT sync via git).

### Phase 0.5 — Kendall's tau pilot (2-model sanity check)
*Goal: cheap early signal on whether the paper's premise holds. Runs while waiting on Sunny + Boaz.*

Uses only existing infrastructure (Mixtral 8x7B + Llama 4 Maverick via Together AI). No new credits, no sign-off needed.

- 100 prompts from V5 test set, stratified across the 7 categories (~15 per category)
- k=10 samples per (prompt, model) at temperature 0.7
- Judge: single-judge proxy (GPT-5.5-mini) for cost — this is a pilot, not final numbers
- Per-prompt P(hallucinate) = fraction of k=10 completions judged hallucination
- Rank prompts by P(hallucinate) per model
- Compute Kendall's tau + Spearman between the two orderings; bootstrap 1000× for 95% CI

**Interpretation** (guides Phase 1 decision):
- τ > 0.7: strong signal — invest in 8-model scale-up confidently
- τ 0.4–0.7: moderate — proceed but frame more carefully
- τ 0.2–0.4: weak — flag for Sunny, may need to reframe
- τ < 0.2: red flag — reframe before spending real money

Cost: under $100. Time: 1–2 days.

**Deliberate caveats to acknowledge with Sunny**:
- 2 open models trained with similar data may have inflated agreement (necessary-but-not-sufficient test)
- Low tau on this pilot is more informative than high tau
- Pilot is a sanity check, not a validation

### Phase 1 — Prompt-vs-model experiment at scale (load-bearing)
*Goal: prove hallucination is prompt-driven across a heterogeneous panel.*
- Extend the pilot to the full 5–10 model panel
- 500 prompts (still stratified), k=10 samples
- Full judge pipeline (3-judge consensus or single-judge — decide with Sunny)
- Compute pairwise Kendall's tau matrix + bootstrap CIs
- **Go/no-go decision**: if tau matrix is dominated by high values, proceed. If not, reframe.

### Phase 2 — Geometric prediction at scale
*Goal: show density predicts the prompt-level P(hallucinate) from Phase 1.*
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
- 8-page NeurIPS-format draft (template in `thesis_reference/`)
- Related work positioning vs. concurrent work
- Sunny review pass
- Boaz review pass
- Submit

---

## 6. Honest timeline notes

Today: **end of August 2026** (~Aug 24). We are ~4 months post-Boaz-meeting. Not "on schedule" but not catastrophic — post-grad summer lulls are normal. What matters is the reset from here.

- **NeurIPS 2026 workshops**: most deadlines already passed or imminent. Check `DEADLINES.md` for any late ones. Not the primary target.
- **ICLR 2027 main (~early Oct)**: ~5–6 weeks out. Aggressive sprint. Only realistic if Phase 0.5 pilot lands clean AND Sunny + Boaz respond in the next 2 weeks. Would require compressing Phases 3, 4, and 5.
- **ICML 2027 main (~late Jan)**: ~22 weeks out. Comfortable, full experimental program. **This is now the realistic primary target.**

What's NOT on the table: skipping Phase 0.5 or Phase 1's go/no-go decision. The Kendall's tau result has to land before we commit hard to the framing, regardless of deadline pressure.

## 7. Open questions to resolve before Phase 1

- Sample budget per prompt (5? 10? 20?) — cost vs. statistical resolution
- Final model panel composition (depends on Boaz credit clarification)
- Hallucination judging at scale: reuse the 3-judge consensus or switch to a cheaper proxy?
- Which external dataset (PopQA leading, alternatives: SimpleQA, FreshQA)
- Co-authorship: just Boaz + Sunny + me, or anyone else?
- Venue commitment (ICML primary, ICLR stretch — decide after Phase 1 result)
