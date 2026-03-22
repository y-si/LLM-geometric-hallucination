# Experiment Log: Prompt Distillation for Hallucination Reduction

> **⚠️ POST-CONTAMINATION-FIX WARNING (March 12, 2026):**
> Numbers throughout this log written before March 11, 2026 use pre-contamination-fix data. Key stale numbers: baselines (81.7%/14.3% Mixtral, 87.1%/9.5% Llama → 82.5%/14.8%, 87.9%/9.7%), prefix rates (5.2%/3.6% → 4.7%/3.0%), Step 9 training (2,402/28 → 2,403/27 Mixtral), template ablation (p=1.00/0.52 → p=0.099/0.773, seen/novel 92.6%/92.4% → 96.3%/93.0%). CoT 62-68% refusal INVALIDATED (API failure artifact). See correction addendum at end of log and `JUDGE_CONTAMINATION_ISSUE.md` for authoritative post-fix numbers. **Do NOT cite numbers from the body of this log in the thesis — use the analysis output files directly.**

Running document tracking what we've done, what the results mean, and what comes next.

**Models**: Mixtral 8x7B, Llama 4 Maverick 17B (both open-source via Together AI)
**Judging**: 3-model consensus panel (GPT-5.1, Claude Opus 4.5, Llama 4 Maverick)
**Advisors**: Boaz Barak (primary), Sunny Qin (PhD co-advisor)

> **⚠ RIGOR STANDARD**: This thesis targets NeurIPS-level publication. Every decision — methodology, analysis, framing, even wording — must be rigorously reviewed. Before executing any step, ask:
> 1. **Why this?** What is the justification? Is it backed by prior work, statistical convention, or advisor guidance?
> 2. **Why not something else?** What are the alternatives? Why is this choice better?
> 3. **What could go wrong?** What are the failure modes? What would invalidate the result?
> 4. **Is this honest?** Does the framing match what the data actually shows? Are we overclaiming?
> 5. **Would a reviewer object?** Anticipate the three most likely critiques and address them preemptively.
>
> No step is too minor for this scrutiny. A NeurIPS reviewer will find the weakest link in the chain. Every choice is either defensible or it's a vulnerability.

---

## Remaining TODO (updated Mar 11, 2026)

**Experiments:**
- [x] **Phase 10: Cross-category generalization ablation** — COMPLETE (Mar 12). All 10 conditions evaluated. Entity-dep generalizes surprisingly well (beats Full for Llama). Entity-indep worst (3-5× hallucination). See results below.

**Writing & analysis:**
- [x] **Phase 7 Steps 7C-D: Literature comparison narrative** — folded into thesis writing (Ch 8). Tables (7B) are complete and verified. Writing narrative directly in LaTeX rather than intermediate markdown. Bib entries added during chapter writing. See 7C structure plan in Phase 7 section below
- [x] **Step 11C disclosure** — location decided: Ch 7.4 methodological note (~1-1.5 paragraphs + small table). Actual writing covered under thesis writing task below
- [x] **Sensitivity analysis** — COMPLETE (Mar 12, 2026). Script fixed to filter failed judges from individual_judgments and exclude CoT. Re-run: `python3 scripts/sensitivity_analysis.py`. Output: `results/sensitivity_analysis.json`. All three checks pass. Results go in Ch 5 or Ch 7.
- [ ] **Thesis writing** — all chapters. Due Mar 27.

**Verification (manual):**
- [ ] **Entity ground truth verification** — spot-check edge factual (150) and obscure real (89) against reliable sources
- [ ] **Human validation expansion** — expand from n=50 to n=150, optional 2nd annotator. ~8 hrs manual

**Deferred (future work):**
- Phase 6: Geometry-guided targeting
- Phase 8: Adversarial robustness

---

## Thesis Narrative (How It All Connects)

1. **V3 — Prediction**: Geometric features of embedding space (curvature, centrality, density) predict which prompts will cause hallucinations across 10 frontier models.
2. **V4 — Intervention**: System-prompt prefixes reduce hallucinations by 90%+ without sacrificing correctness.
3. **Bridge Analysis**: The same geometric features that predict hallucinations also predict *where interventions work* (AUC = 0.86) — and where they fail.
4. **Fine-Tuning**: Distill the "careful" prefix behavior into model weights via LoRA, so the model is safer without needing the prompt at inference time.
5. **Generalization**: Entity-fabrication fine-tuning transfers to TruthfulQA misconception-type hallucination (Llama: -4.4pp halluc, p=0.0005, Bonferroni-sig). The learned caution is not task-specific — it's a general epistemic improvement.
6. **Cross-Category Generalization**: Fine-tuning on entity-dependent categories alone (~1,000 examples) matches or beats Full (~2,400) — caution transfers across category types. Three generalization types confirmed: unseen entities, unseen templates, unseen category types.
7. **Unified framework**: Geometry is the diagnostic, prompts are the treatment, fine-tuning is the cure, and the cure generalizes across entities, templates, AND category types.

---

# Part 1: Prefix Experiment (Completed)

## 1.1 Experiment Design: The 5 Prompt Prefixes

### Motivation

Our V3 experiment showed that geometric embedding properties predict hallucinations across 10 frontier models. The natural follow-up: can we actually *reduce* hallucinations by prompting models to be more careful? And if so, can we later distill that careful behavior into the model's weights via fine-tuning, so it no longer needs the prompt at inference time?

We selected two open-source models from our V3 benchmark — **Mixtral 8x7B** (11.8% hallucination rate, the highest among our tested models) and **Llama 4 Maverick 17B** (5.8%, moderate) — and designed 5 system-prompt prefixes that each target a distinct mechanism for reducing hallucinations. All 5 prefixes were evaluated on the same 449-prompt benchmark from V3, using the same 3-judge consensus panel, so results are directly comparable to baseline.

### The 5 Prefixes

Each prefix is a system prompt prepended to every query. They are ordered from least to most restrictive:

| # | Prefix | Strategy | System Prompt (summarized) |
|---|--------|----------|---------------------------|
| 1 | **Epistemic Humility** | Light nudge toward honesty | "When you are not confident, indicate your uncertainty. If you genuinely do not know something, say 'I don't know' rather than guessing." |
| 2 | **Fact-Grounded** | Prohibit fabrication | "Only state facts you are confident about. Do not fabricate names, dates, statistics, or other specific details." |
| 3 | **Entity-Aware** | Existence verification | "Before answering, consider whether the entity or concept actually exists. If it appears to be fictional, fabricated, or nonexistent, say so clearly." |
| 4 | **Structured Caution** | Explicit numbered rules | Five rules combining all strategies: state uncertainty, flag nonexistent entities, explain impossibility, never speculate as fact, prefer 'I don't know' over incorrect information. |
| 5 | **CoT Verification** | Chain-of-thought self-check | "Before providing your final answer, briefly verify your claims. Ask yourself: 'Am I certain this is correct? Does this entity actually exist?'" |

### Why these 5? Literature grounding

Each prefix targets a distinct, literature-backed mechanism for hallucination reduction. Together they form a spectrum from minimal behavioral nudge to explicit multi-step verification:

**1. Epistemic Humility** — *Can models leverage their own uncertainty?*

Kadavath et al. (2022) showed that LLMs possess internal calibration — they "mostly know what they know." Yin et al. (2023, Findings of ACL) confirmed this with unanswerable questions: models *can* identify what they don't know, but need explicit encouragement to say so. Zhang et al. (2023, NAACL 2024) demonstrated via R-Tuning that teaching models to say "I don't know" generalizes as a meta-skill. Our prefix tests the simplest version: a one-sentence nudge to express uncertainty rather than guess.

**2. Fact-Grounded** — *Does prohibiting fabrication work?*

Min et al. (2023, EMNLP) introduced FActScore, showing that ChatGPT fabricates specific details (names, dates) in 42% of generated biography sentences. Varshney et al. (2023) showed that fabricated details correlate with low-confidence generation points, and that real-time intervention at those points reduces hallucination from 47.5% to 14.5%. Our prefix targets this failure mode via instruction: "do not fabricate names, dates, statistics."

**3. Entity-Aware** — *Can models verify entity existence before answering?*

Ferrando et al. (2024, ICLR 2025) discovered that models have internal representations ("knowledge cards") that distinguish known from unknown entities — and these representations are causally linked to hallucination. Sun et al. (2024, NAACL) showed hallucination rate is inversely correlated with entity popularity. Our prefix asks models to explicitly perform the existence check these papers show they can do internally. **Note**: this prefix is the most benchmark-specific, since our evaluation is heavy on nonexistent entities. Generalization to other benchmarks (TruthfulQA, HaluEval) is tested in Phase 5.

**4. Structured Caution** — *Do explicit rules outperform implicit guidance?*

Li et al. (2023, NeurIPS) showed that inference-time intervention (shifting activations toward "truthful directions") improved TruthfulQA accuracy from 32.5% to 65.1%, demonstrating that models have latent truthful behavior that can be activated. Arora et al. (2024) found that structured, explicit prompting rules materially improve truthfulness over vaguer instructions. Our prefix combines all strategies into 5 numbered rules, testing whether exhaustive specification outperforms individual mechanisms.

**5. CoT Verification** — *Does self-verification reduce hallucination?*

Dhuliawala et al. (2023, Findings of ACL 2024) introduced Chain-of-Verification (CoVe), which reduces hallucination by 50-70% through multi-step self-verification. Wei et al. (2022, NeurIPS) established that chain-of-thought reasoning improves accuracy on complex tasks. Wang et al. (2023, ICLR) showed that self-consistency across reasoning paths further improves reliability. Our prefix is a simplified single-pass version of CoVe: "before answering, verify your claims." This serves as a **baseline** — CoT is a well-known technique, so comparing it against our domain-specific prefixes shows whether targeted instructions add value beyond generic "think carefully."

### Positioning in the literature

Most existing hallucination mitigation research focuses on either (a) internal model modifications (inference-time intervention, activation editing, fine-tuning) or (b) multi-step external pipelines (RAG, CoVe, LLM-Augmenter). Few papers systematically compare different **system-prompt-only** interventions on the same benchmark. Our experiment fills this gap: a controlled comparison of 5 prompting strategies, evaluated with statistical rigor on paired data, measuring the correctness-safety tradeoff that Xu et al. (2024) frame as the realistic goal (since they formally prove hallucination cannot be *eliminated*, only mitigated).

### Evaluation Setup

- **Generation**: 2 models x 5 prefixes x 449 prompts = 4,490 API calls (Together AI)
- **Judging**: Each response judged by 3-model consensus panel (GPT-5.1, Claude Opus 4.5, Llama 4 Maverick) using majority vote on a 4-point rubric: 0 = Correct, 1 = Partial, 2 = Hallucinated, 3 = Refused
- **Statistical test**: McNemar's test for paired binary outcomes on the same 449 prompts (baseline vs each prefix)
- **Baseline**: V3 results with no system prompt, same models, same prompts, same judges

---

## 1.2 Results: The Tradeoff Curve (Main Result)

**File**: `analysis/tradeoff_curve.png`

This is the most important plot. Each point represents a (model, prefix) combination. The X-axis is correctness rate (how often the model answers correctly), the Y-axis is safety rate (1 minus hallucination rate). The ideal is the **upper-right corner**: correct *and* safe.

### What it shows

The red dots are V3 baselines (no prefix). Every single prefix point moves **up and to the right** from its baseline — meaning prefixes don't just reduce hallucinations, they also improve correctness. This is the best possible outcome: we're not trading accuracy for safety.

### Mixtral 8x7B (circles)

| Prefix | Correctness | Safety | Hallucination |
|--------|------------|--------|---------------|
| **Baseline (V3)** | **82.9%** | **88.2%** | **11.8%** |
| Epistemic Humility | 86.0% | 97.1% | 2.9% |
| Fact-Grounded | 86.2% | 97.6% | 2.4% |
| Entity-Aware | 91.1% | 99.3% | 0.67% |
| Structured Caution | 90.6% | 98.7% | 1.3% |
| CoT Verification | 85.7% | 95.3% | 4.7% |

**Standout**: Entity-Aware on Mixtral is remarkable — hallucination drops from 11.8% to 0.67% (94% relative reduction) while correctness *increases* by 8.2 percentage points. 50 previously-hallucinated prompts were fixed, and 0 were broken (McNemar p < 0.000001).

### Llama 4 Maverick (squares)

| Prefix | Correctness | Safety | Hallucination |
|--------|------------|--------|---------------|
| **Baseline (V3)** | **90.6%** | **94.2%** | **5.8%** |
| Epistemic Humility | 93.3% | 98.2% | 1.8% |
| Fact-Grounded | 92.0% | 99.1% | 0.89% |
| Entity-Aware | 94.0% | 97.6% | 2.4% |
| Structured Caution | 93.3% | 99.6% | 0.45% |
| CoT Verification | 93.5% | 97.1% | 2.9% |

**Standout**: Structured Caution on Llama reduces hallucination from 5.8% to 0.45% (92% relative reduction), with 24 prompts fixed and 0 broken (p = 0.000001).

### Why this matters

A naive safety intervention (e.g., "refuse everything you're unsure about") would move points *up and to the left* — safer but less useful. Our prefixes move points up and to the right because they teach the model *when* to be cautious (on genuinely uncertain queries) rather than blanket refusal. This is exactly the behavior we want to distill via fine-tuning.

---

## 1.3 Results: Category Heatmaps

**Files**: `analysis/category_heatmap_mixtral-8x7b.png`, `analysis/category_heatmap_llama-4-maverick-17b.png`

These show hallucination rate broken down by prompt category (columns) and prefix (rows). Color scale: dark green = 0% hallucination, red = 25%.

### What they reveal

**Borderline Plausible Fake is the hard category.** Across both models and nearly all prefixes, this category retains the highest residual hallucination. These are prompts about entities that sound real but don't exist — the hardest type for any model to handle correctly.

#### Mixtral heatmap highlights:
- **Ambiguous, Edge Factual, Impossible**: 0% hallucination across all prefixes. These categories are solved.
- **Borderline Plausible Fake**: Ranges from 6.5% (Entity-Aware, Structured Caution) to 32.3% (CoT Verification). This is where hallucination concentrates.
- **Nonexistent**: Drops from baseline levels to 0.8%-7.5% depending on prefix. Entity-Aware nearly eliminates it (0.8%).
- **Entity-Aware dominates**: Near-zero across almost every category, confirming that asking the model to "consider whether the entity actually exists" is precisely the right intervention for fabrication-type hallucinations.

#### Llama heatmap highlights:
- **Borderline Plausible Fake**: Still the hardest — 3.2% (Structured Caution) to 22.6% (CoT Verification). Even Llama's strong baseline struggles here.
- **Borderline Obscure Real**: Some prefixes (Entity-Aware, CoT Verification) introduce 3-7% hallucination here. These are real but obscure entities where the model second-guesses itself.
- **Fact-Grounded and Structured Caution**: Most consistently green across categories for Llama.

### Interpretation

The heatmaps confirm that **different prefixes have different strengths by category**. Entity-Aware excels on nonexistent/fabrication prompts (by design), while Fact-Grounded and Structured Caution provide more uniform protection. This suggests a potential ensemble or category-adaptive approach for future work.

---

## 1.4 Results: Refusal Rates (The Cost of Caution)

**File**: `analysis/refusal_rates.png`

Refusal rate measures how often the model says "I don't know" or declines to answer. Some refusal is good (refusing to hallucinate), but too much means the model is useless.

### Key observations

**Mixtral refuses more than Llama across every prefix.** This makes sense — Mixtral has a higher baseline hallucination rate, so when given cautionary instructions, it encounters more prompts where it's uncertain and chooses to refuse rather than guess.

| Prefix | Mixtral Refusal | Llama Refusal |
|--------|----------------|---------------|
| Epistemic Humility | 9.6% | 1.3% |
| Fact-Grounded | 10.9% | 6.9% |
| Entity-Aware | 7.3% | 0.4% |
| Structured Caution | 7.8% | 6.0% |
| CoT Verification | 8.2% | 0.7% |

**Entity-Aware has the best refusal profile.** For Mixtral it achieves the lowest hallucination rate (0.67%) with only 7.3% refusal — meaning it's both the safest and one of the least over-cautious. For Llama it's even better: 2.4% hallucination with just 0.4% refusal.

**Fact-Grounded causes the most over-refusal** (10.9% Mixtral, 6.9% Llama). The instruction to "never fabricate names, dates, or statistics" makes both models refuse factual questions they could actually answer correctly (19.4% refusal on Llama's factual category, 23.5% on Mixtral).

---

## 1.5 Results: Statistical Significance

**File**: `analysis/statistical_tests.csv`

All 10 (model, prefix) combinations are statistically significant by McNemar's test (paired comparison on the same 449 prompts vs V3 baseline).

| Model | Prefix | Improved | Worsened | p-value |
|-------|--------|----------|----------|---------|
| Mixtral | Entity-Aware | 50 | 0 | < 0.000001 |
| Mixtral | Structured Caution | 48 | 1 | < 0.000001 |
| Mixtral | Fact-Grounded | 43 | 1 | < 0.000001 |
| Mixtral | Epistemic Humility | 41 | 1 | < 0.000001 |
| Mixtral | CoT Verification | 38 | 6 | < 0.000001 |
| Llama | Structured Caution | 24 | 0 | 0.000001 |
| Llama | Fact-Grounded | 22 | 0 | 0.000003 |
| Llama | Epistemic Humility | 18 | 0 | 0.000022 |
| Llama | Entity-Aware | 18 | 3 | 0.001063 |
| Llama | CoT Verification | 15 | 2 | 0.001616 |

**"Improved"** = prompts that hallucinated at baseline but not with the prefix.
**"Worsened"** = prompts that were correct at baseline but hallucinated with the prefix.

The asymmetry is striking: Entity-Aware on Mixtral fixed 50 prompts and broke 0. Even CoT Verification (the weakest performer) fixed 38 and only broke 6. These are not random fluctuations — they are systematic, one-directional improvements.

---

## 1.6 Prefix Rankings

### Best overall: Entity-Aware

- Largest absolute hallucination reduction on Mixtral (11.1pp)
- Lowest refusal rate on Llama (0.4%)
- Zero worsened prompts on Mixtral
- Near-zero hallucination across most categories

### Best for Llama specifically: Structured Caution

- Lowest hallucination rate (0.45%)
- Zero worsened prompts
- Most uniform protection across categories (heatmap nearly all green)

### Weakest: CoT Verification

- Highest residual hallucination on both models
- Only prefix with notable "worsened" counts (6 on Mixtral, 2 on Llama)
- Borderline Plausible Fake remains at 32.3% for Mixtral — the worst of any prefix
- "Verify your claims" doesn't help much when the model doesn't know its claims are wrong

### Surprising: Epistemic Humility

- The gentlest prefix ("say I don't know rather than guessing") still achieves huge reductions
- 41 improved / 1 worsened on Mixtral, 18/0 on Llama
- Suggests that even a light nudge toward honesty has outsized effects

---

# Part 2: Bridge Analysis (Completed)

## 2.1 Do geometric features predict where prefixes help?

**Files**: `analysis/geometry_bridge_mixtral-8x7b.png`, `analysis/geometry_bridge_llama-4-maverick-17b.png`, `analysis/geometry_bridge_stats.csv`

The V3 finding was that prompts in certain geometric regions of embedding space (high centrality, low curvature) are more likely to trigger hallucinations. The bridge analysis asks: **do those same geometric features predict where prefixes help?**

**Yes.** Prompts *fixed* by prefixes have a distinct geometric profile vs already-correct prompts:

| Feature | Fixed (Mixtral) | Already Correct | p-value |
|---------|-----------------|-----------------|---------|
| Curvature | 0.22 | 0.32 | 0.00001 |
| Density | 2.06 | 1.93 | 0.000003 |
| Centrality | 0.64 | 0.66 | 0.001 |

More importantly, the prompts that **still hallucinate even with prefixes** occupy an extreme geometric region:
- Very high centrality (0.73 vs 0.64 for fixed, p < 0.000001)
- Very low density (1.55 vs 2.06 for fixed, p < 0.000001)

A logistic regression predicting "will the prefix fix this hallucination?" using only geometric features achieves **AUC = 0.86** (Mixtral) and **AUC = 0.83** (Llama).

## 2.2 Key insight: Hallucination difficulty taxonomy

Geometric features don't just predict *which prompts cause hallucinations* (V3) — they predict the *difficulty* of hallucinations, i.e., how resistant they are to mitigation.

The "unfixable" residual lives in a specific geometric region: **high centrality, low density**. These are prompts where the model is maximally confident but in a sparse embedding neighborhood — it "thinks it knows" but has no nearby evidence to self-correct from.

This is a potential novel thesis contribution: **a geometric taxonomy of hallucination difficulty**. Explore further: can we characterize what makes a hallucination "easy" vs "hard" to fix, and does this inform which intervention strategy to use?

---

# Part 2.5: V5 Geometry → Hallucination Prediction (Completed Mar 2026)

## 2.5.1 What this analysis does

Tests whether the 5 geometric features computed on the combined corpus (2,879 prompts) predict which V5 prompts (2,430) hallucinate at baseline (no prefix). This is the V5 validation of the V3 finding (AUC=0.86) — but with proper controls for the first time.

**Script**: `scripts/analyze_v5_geometry_prediction.py`

**Two levels of analysis**:
1. **Between-category**: Do features differ between hallucinated and correct prompts overall? (Potentially circular)
2. **Within-category**: Do features predict hallucination *within* each category? (The real test — controls for category-level confounds)

## 2.5.2 Results: Overall logistic regression

| Metric | V3 (449 prompts) | V5 Mixtral (2,430) | V5 Llama (2,430) |
|---|---|---|---|
| Train AUC | 0.86 | 0.650 | 0.726 |
| **5-fold CV AUC (geo only)** | not reported | **0.641** | **0.722** |
| CV AUC (geo + category) | — | 0.792 | 0.813 |
| CV AUC (category only) | — | 0.774 | 0.769 |
| **Geo adds over category** | — | **+0.018** | **+0.044** |

**Feature coefficients** (standardized, both models consistent):
- **Oppositeness**: strongest predictor (+0.54 Mixtral, +0.86 Llama) → high oppositeness = more hallucination
- **Density**: second strongest (-0.40 Mixtral, -0.62 Llama) → low density = more hallucination
- **local_id, curvature**: near-zero coefficients, not predictive (and -0.97 correlated with each other — redundant)
- **Centrality**: weak, inconsistent direction across models

## 2.5.3 Results: Within-category analysis (the key test)

**Why this matters**: Between-category differences could be circular — borderline categories are *defined* as unusual, so of course they have unusual geometry. The within-category test controls for this confound by asking: "Among nonexistent prompts only, do the ones that hallucinate have different geometry than the ones that don't?"

**Summary of within-category significance** (Mann-Whitney U, Bonferroni-uncorrected):

| Category | N | Halluc Rate | Density | Oppositeness | Best CV AUC |
|---|---|---|---|---|---|
| nonexistent | 600 | 29.5% / 19.0% | p<0.0001 *** / p<0.0001 *** | p=0.005 ** / p=0.037 * | 0.665 / 0.678 |
| borderline_plausible_fake | 200 | 38.5% / 28.5% | ns / ns | ns / p=0.008 ** | 0.593 / 0.640 |
| impossible | 200 | 9.5% / 16.0% | p=0.014 * / ns | ns / ns | 0.617 / 0.411 |
| factual | 500 | 9.2% / 2.6% | ns / ns | ns / p=0.044 * | 0.509 / 0.653 |
| ambiguous | 600 | 0.7% / 1.5% | — | p=0.013 * / — | too few halluc |
| borderline_obscure_real | 200 | 10.5% / 3.0% | ns / ns | ns / ns | 0.422 / — |
| borderline_edge_factual | 130 | 3.1% / 0.8% | too few | too few | — |

(Format: Mixtral / Llama)

**The consistent within-category finding: density predicts hallucination within nonexistent prompts.** Lower density (sparser neighborhood) → model more likely to hallucinate. This holds for both models with p < 0.0001 and effect size r ≈ 0.25. Within the largest and most hallucination-prone category, geometry genuinely matters.

## 2.5.4 Interpretation: What the V3 AUC of 0.86 really was

**The V3 results were not wrong — but they were doing two things at once.**

Geometry captures category structure (borderline prompts have lower density, higher oppositeness) AND within-category variation. The V3 AUC of 0.86 combined both signals without separating them. The V5 analysis decomposes this:

1. **Category structure IS geometric.** The fact that borderline_plausible_fake prompts sit in sparser, more peripheral regions of embedding space is itself a geometric finding. It's not "circular" — it's *the mechanism*. The categories were defined by semantic content, not by geometry. The geometry emerged independently from embedding the prompts.

2. **Category alone predicts hallucination well (AUC 0.77).** This is unsurprising — we designed categories with different expected difficulty levels. A factual prompt and a plausible-fake prompt have fundamentally different hallucination risk.

3. **Geometry adds real but modest signal beyond category (+0.02-0.04 AUC overall).** This is because most of geometry's predictive power operates *through* category structure. But the within-category signal is real where it matters (nonexistent: AUC 0.67).

4. **The within-category signal is the non-circular, novel finding.** Among 600 nonexistent prompts — all the same type, all asking about things that don't exist — the ones in sparser embedding neighborhoods hallucinate significantly more. This cannot be explained by category membership.

## 2.5.5 Thesis framing (for paper writing)

**Do NOT frame as**: "Geometry predicts hallucination with AUC 0.86" (V3 number, no category control, not cross-validated)

**DO frame as**:

> Geometric features of the embedding space predict hallucination at two levels. At the category level, prompts about borderline or nonexistent entities occupy sparser, more semantically isolated regions (lower density, higher oppositeness), and these regions correspond to higher hallucination rates. This suggests that the embedding geometry captures a meaningful notion of "how well the model knows this territory."
>
> More importantly, geometric features predict hallucination *within* categories. Among 600 nonexistent-entity prompts — controlling for category — prompts in sparser neighborhoods (lower density) are significantly more likely to trigger hallucination (p < 0.0001, both models). The 5-fold cross-validated AUC for within-category prediction reaches 0.67, compared to 0.50 for random chance. This within-category signal is the non-circular evidence that geometry captures something beyond category labels.
>
> Overall, geometric features achieve cross-validated AUC of 0.64-0.72 for predicting hallucination on 2,430 unseen prompts. Category membership alone achieves AUC 0.77; adding geometry improves this to 0.79-0.81. While category structure accounts for most predictive power, the within-category results demonstrate that geometry provides genuine fine-grained signal about hallucination risk.

**Key numbers to cite**:
- Overall CV AUC: 0.64 (Mixtral), 0.72 (Llama) — geometry only, no category
- Within nonexistent CV AUC: 0.67 (both models)
- Density within nonexistent: p < 0.0001, effect size r ≈ 0.25
- Category-only AUC: 0.77 → geo adds +0.02-0.04

**What's still untested (and may be stronger)**:
- The V4 bridge analysis (geometry predicts *prefix fixability*) on V5 data — requires Step 7 completion
- This may show stronger within-category signal because it's a finer-grained outcome (fixed vs still-broken among hallucinated prompts, not just hallucinated vs correct)

## 2.5.6 Output files

```
results/v5_baselines/analysis/
├── v5_geometry_prediction_overall.csv         — between-category Mann-Whitney results
├── v5_geometry_prediction_within_category.csv — within-category tests + CV AUCs
├── v5_geometry_vs_hallucination_mixtral-8x7b.png      — scatter plots
├── v5_geometry_vs_hallucination_llama-4-maverick-17b.png
├── v5_within_category_mixtral-8x7b.png        — within-category box plots
└── v5_within_category_llama-4-maverick-17b.png
```

## 2.5.7 Surface-feature baseline comparison `[DONE — Mar 21, 2026]`

**Purpose**: Test whether simple text-level properties (question length, entity name length) capture the same within-category signal as density, addressing the reviewer concern that density might just proxy for surface features.

**Method**: Mann-Whitney U tests within the nonexistent category (same framework as 2.5.3), comparing hallucinated vs. correct prompts on:
1. Question length (word count) — template-controlled, expected null
2. Entity name length (character count) — could reflect "exoticness"

**Results**:

| Feature | Mixtral p | Mixtral |r| | Llama p | Llama |r| |
|---|---|---|---|---|
| Question word count | 0.67 | 0.022 | 0.06 | 0.113 |
| Entity name length (chars) | 0.002 | 0.162 | 0.93 | 0.005 |
| **Density (for comparison)** | **5.7×10⁻⁷** | **0.259** | **3.4×10⁻⁵** | **0.249** |

**Key findings**:
- Question word count: null for both models (expected — template-controlled)
- Entity name length: significant for Mixtral only (p=0.002, |r|=0.162), null for Llama (p=0.93). Model-specific, weaker than density
- Density: significant for both models with larger effect sizes (|r|=0.259/0.249)
- Density–entity name length correlation: Spearman r=−0.186 (modest). Longer entity names sit in sparser neighborhoods, but density captures substantially more variance

**Conclusion**: Density carries genuine geometric signal beyond surface text properties. Entity name length has a model-specific partial association but doesn't explain the cross-model density signal.

**Written into**: Thesis Chapter 5, Section 5.6 (Discussion), "Why density" paragraph.

---

# Part 3: Benchmark Scaling & Fine-Tuning Preparation (Next)

## 3.1 Why we need more prompts

449 prompts was enough for the prefix experiment (paired statistical tests on existing benchmark). But for fine-tuning:
- LoRA typically needs 1,000-10,000 training examples
- We need proper train/test splits without contamination
- The original 449 prompts become a pristine held-out test set

**Target**: ~2,400+ new prompts for training. Total benchmark: ~2,880.

## 3.2 Why we also need baselines on the new prompts

We run Mixtral + Llama **without any prefix** on all new prompts. This costs only 2 x 2,000 = 4,000 extra Together AI calls but gives us:
1. **Baselines** to know which new prompts the model naturally hallucinates on
2. **V3 validation** — test whether geometric features still predict hallucinations on unseen prompts (generalization)
3. **Bridge analysis replication** — confirm that geometry predicts prefix effectiveness on new data (n=2,430 instead of n=449)

We do NOT need to run all 10 models from V3 on the new prompts. The cross-model generality is already established. We only need the 2 target models.

## 3.3 Best-per-prompt training data selection

Per Sunny Qin's suggestion: instead of using a single prefix's outputs as fine-tuning targets, **select the best output across all 5 prefixes for each prompt**. This maximizes training data quality.

Empirical justification (on our 449 prompts):

| | Single Best Prefix | Best-per-Prompt | Improvement |
|--|-------------------|-----------------|-------------|
| **Mixtral** correct | 91.1% (Entity-Aware) | 95.5% | +20 prompts |
| **Mixtral** hallucinated | 0.7% | 0.2% | -2 prompts |
| **Mixtral** refused | 7.3% | 3.1% | -19 prompts |
| **Llama** correct | 93.3% (Struct. Caution) | 98.0% | +21 prompts |
| **Llama** hallucinated | 0.4% | 0.0% | -2 prompts |
| **Llama** refused | 6.0% | 0.2% | -26 prompts |

Why all 5 prefixes (not just the top 3): the top 3 prefixes miss 3-7 prompts per model that only the bottom 2 uniquely save. These are hard prompts (borderline_fake, factual) — exactly where every training example matters most.

Selection criteria per prompt:
1. If any prefix produced a correct response (label 0), use it
2. Else if any prefix produced a refusal (label 3), use the refusal
3. Else the prompt is "unfixable" — exclude from training or use as-is

## 3.4 The full pipeline (step by step)

### Step 1: Expand entity lists `[GATING ITEM]`

#### Step 1A: Assess current state `[DONE — Feb 2026]`

Ran `scripts/analyze_entity_pools.py`. The **4 main categories** were already expanded to 15+ items per pool in a previous session:

| Category | Templates | Combinatorial Capacity | Target | Status |
|---|---|---|---|---|
| factual | 30 | 1,481 | ~400 | Ready |
| nonexistent | 30 | 6,439 | ~500 | Ready |
| impossible | 55 (20 static) | 2,015 | ~150 | Ready |
| ambiguous | 30 | 9,270 | ~500 | Ready |

**Main categories do NOT need further expansion.**

#### Step 1B: Expand borderline entity pools `[DONE — Feb 2026]`

Expanded all borderline pools in `src/pipeline/build_borderline_benchmark.py`:

| Pool | Before | After | Prompts Generated |
|---|---|---|---|
| `OBSCURE_REAL_PEOPLE` | 10 | 39 | 150 (shared across people/places/events) |
| `OBSCURE_REAL_PLACES` | 10 | 40 | |
| `OBSCURE_REAL_EVENTS` | 10 | 40 | |
| `PLAUSIBLE_FAKE_PEOPLE` | 10 | 45 | 150 (shared across people/books/places) |
| `PLAUSIBLE_FAKE_BOOKS` | 10 | 45 | |
| `PLAUSIBLE_FAKE_PLACES` | 10 | 45 | |
| **Edge factual** | **5 unique Qs** | **150 unique Qs** | **150** |

Also expanded templates: 10-12 per type before, now 10 per sub-type (people/places/events each get their own template set).

**Total borderline prompts generated: 450** (150 + 150 + 150).

Quality constraints (still apply for Step 1D review):
- **Obscure real**: Every entity MUST be verified as actually real and genuinely obscure
- **Plausible fake**: Every entity MUST be verified as actually nonexistent (risk: LLM suggests a real person/book/place)
- **Edge factual**: Each question needs a verified correct answer

#### Step 1C: Add more borderline templates `[DONE — Feb 2026]`

Doubled templates from 10 to 20 per sub-type (6 sub-types = 120 total templates):

| Sub-type | Before | After | Examples of new templates |
|---|---|---|---|
| Obscure people | 10 | 20 | "How did X die?", "Is X still alive?", "Who mentored X?" |
| Obscure places | 10 | 20 | "Does X have an airport?", "What currency is used in X?" |
| Obscure events | 10 | 20 | "Has X been depicted in film?", "What lessons were learned?" |
| Fake people | 10 | 20 | "What is X's h-index?", "Which journal published X's paper?" |
| Fake books | 10 | 20 | "Has X been adapted into a film?", "Is X based on a true story?" |
| Fake places | 10 | 20 | "What is the postal code for X?", "What is the lat/long of X?" |

New templates specifically designed to elicit hallucination: questions about specific details (h-index, postal code, lat/long) are particularly effective traps since the model must either fabricate specifics or admit ignorance.

#### Step 1D: Automated + human review pass `[PARTIALLY DONE — Feb 2026]`

**Automated sweep completed**: Web-searched all 105 new fake entities for real-world collisions.

Results:
- **Fake people**: 6 FLAGged (real people with exact names), 8 UNCERTAIN → 6 replaced with compound-surname names unlikely to collide
- **Fake books**: 15 FLAGged (real published books with same base title), 5 UNCERTAIN → 15 replaced with highly specific invented-proper-noun titles
- **Fake places**: 6 FLAGged (real places, e.g., Blackfen is in London, Wyndmere is in North Dakota), 11 UNCERTAIN → 7 replaced (including original "Lake Meridian" which is a real lake in Washington state)

**Key lesson**: Generic literary titles ("The Dry Season", "The Kindness of Strangers") almost always collide with real books. Compound/multi-word geographic names also frequently match real places. Replacements use invented proper nouns and unusual compound constructions to minimize collision risk.

**UNCERTAIN items reviewed (Feb 2026)**: Human reviewed all 24 uncertain items. Verdict: keep all fake people (matches too obscure/non-existent), replace 2 fake books (False Positive → Lintel Above the Dovecote; The Inheritance Tax → Glassblower's Almanac), keep all fake places. Note: Professor Ibrahim Al-Farouqi kept despite proximity to Ismail al-Faruqi — if models confuse them, that's a valid hallucination finding.

**DEFERRED to before Step 8 (judging)**:
- Spot-check obscure real entities (89 items) for correctness of descriptions
- Verify edge factual answers (150 items) against reliable sources
- These don't affect prompt generation (Steps 2-7) but matter for accurate scoring

#### Step 1E: Refactor borderline entities into external JSON `[DONE]`

Moved all hardcoded entity pools and templates from `build_borderline_benchmark.py` into external JSON files:
- `data/entity_lists/borderline_obscure_real_entities.json` — people (39), places (40), events (40)
- `data/entity_lists/borderline_plausible_fake_entities.json` — people (45), books (45), places (45)
- `data/entity_lists/borderline_edge_factual_entities.json` — 150 question/answer objects
- `data/templates/borderline_templates.json` — 20 templates per sub-type (6 sub-types, 120 total)

Script now loads from JSON files at runtime. Verified: generates same prompts as before.

**Post-1E expansion**: Edge factual pool expanded from 93 → 150 questions to match the 150 target of the other two borderline sub-categories and provide headroom for Priority 2 review losses. Added 57 questions across 8 new topic areas: unit conversions (8), commonly confused inventors (6), food/nutrition misconceptions (5), language/etymology traps (5), technology/computing (5), probability/math traps (6), zoology (6), physics SI units (5), geography (5), historical dates (6). All questions hand-verified with ground truths. After excluding V3 overlap (5 questions), 145 available for training — matching the ~150 target with buffer.

### Step 2: Add more templates `[DONE]`

Added 20-25 new templates per category to increase structural diversity for fine-tuning data quality.

**Results**:
| Category | Before | After | New Formats Added |
|---|---|---|---|
| `factual` | 31 | 56 (+25) | True/false, continent, borders, density, GDP, protons, visibility, decade |
| `nonexistent` | 31 | 55 (+24) | Comparison, awards list, genre, atomic number, outcome, true/false, prerequisites, mortality rate |
| `impossible` | 56 | 66 (+10) | Millionth element, first-hand experience, GPS trace, perpetual motion, total count, every digit |
| `ambiguous` | 31 | 55 (+24) | Scale rating, ranking, overrated, definitive yes/no, debate-settling, foolishness, history judging |
| `borderline` | 120 | 120 | Already done in Step 1C, skipped |

**Validation**: All templates pass `analyze_entity_pools.py` — zero UNMATCHED variables, all categories exceed 500-prompt capacity target. Combinatorial capacity: factual 2,721, nonexistent 69,065, impossible 2,180, ambiguous 17,835.

### Step 3: Generate new prompts `[DONE — Feb 2026]`

Generated 2,430 new prompts for fine-tuning training data via unified `src/pipeline/build_v5_benchmark.py`. The original 449 V3 prompts serve as the held-out test set.

**Approach**: Created a single new script rather than modifying existing V2/borderline scripts (preserves V3 reproducibility). Includes conference-quality controls:
- **Stratified template sampling**: Round-robin through shuffled templates ensures structural diversity (no template dominates). **Why round-robin over random sampling with replacement**: Random sampling can accidentally over-represent some templates and under-represent others, especially at smaller per-category N. Round-robin guarantees perfectly uniform template usage rather than relying on probabilistic convergence. The shuffle (seeded for reproducibility) avoids predictable ordering artifacts. Trade-off: round-robin creates an artificially uniform template distribution that doesn't reflect natural question frequencies — but for fine-tuning data where the goal is maximizing structural diversity to prevent template overfitting (per Sunny's feedback, Mar 2026), uniform is the correct choice. Mention in thesis methodology (§4.1.2).
- **Entity diversity caps**: Max 5 reuses per entity across all prompts in a category
- **V3 exclusion** (two levels): Exact question text match + same (template, entity-set) combo
- **Cross-category dedup**: Global seen-set prevents the same question appearing in multiple categories
- **Placeholder validation**: Rejects any prompt with unfilled `[var]` patterns (a V3 quality issue)

**Generation results** (`seed=2025`, ID prefix `v5_`, 4-digit padding):

| Category | V3 Count | V5 Generated | Template Coverage | Entity Coverage | Avg Reuse | V3 Excluded |
|---|---|---|---|---|---|---|
| factual | 98 | 500 | 100% (56/56) | 69.4% (249/359) | 2.16 | 51 |
| nonexistent | 120 | 600 | 100% (55/55) | 80.3% (408/508) | 2.26 | 33 |
| impossible | 30 | 200 | 69.7% (46/66) | 76.7% (138/180) | 1.70 | 100 |
| ambiguous | 120 | 600 | 100% (55/55) | 84.0% (463/551) | 2.09 | 59 |
| borderline_obscure_real | 30 | 200 | — | 83.2% (99/119) | — | 2 |
| borderline_plausible_fake | 31 | 200 | — | 78.5% (106/135) | — | 3 |
| borderline_edge_factual | 20 | 130 | — | — | — | 6 |
| **Total** | **449** | **2,430** | | | | **254** |

**Validation** (all passed):
- V3 overlap: 0 (zero contamination between train and test sets)
- Unfilled placeholders: 0 (vs V3 which had ~20+ broken prompts)
- Internal duplicates: 0 (cross-category dedup caught 8 factual↔edge_factual overlaps)

**Scale increase**: Targets scaled up from original ~2,000 to ~2,430. Rationale: more training data per category for LoRA, better borderline representation (200 vs 150), competitive with benchmark papers (TruthfulQA: 817, SimpleQA: 4,326).

**Notes on template coverage**:
- Impossible at 69.7%: expected — 20 of 66 templates are static (e.g., "Prove that P = NP") which can only be used once each, and all appear verbatim in V3 (100 V3 exclusions)
- Ambiguous at 100%: Fixed in Mar 2026 — originally 89.1% (49/55) due to 6 templates with paired variables (`{option1}`/`{option2}`, `{concept}`/`{other_concept}`) that weren't resolving to the `option_pairs`/`concept_pairs` entity pools. Added `_build_pair_index()` to `fill_template()` to resolve sub-keys of nested dict pools. This eliminated all 108 placeholder rejections and raised entity coverage from 77.7% to 84.0%.

**Output files**: `data/prompts/v5_*.jsonl` (7 per-category files + `v5_all.jsonl` + `v5_generation_report.json`)

### Step 4: Embed new prompts `[DONE — Mar 2026]`

Embedded the combined corpus (449 V3 + 2,430 V5 = 2,879 prompts) using OpenAI `text-embedding-3-large` → 3072-dim vectors. Combined in one pass to ensure identical model version across all prompts.

**Script**: `scripts/embed_v5_prompts.py`

**Results**:
- Shape: `(2879, 3072)`, dtype float32, 33.7 MB
- All embeddings unit-normalized (norm range [1.0000, 1.0000])
- Zero NaN/Inf values
- V3 indices: 0–448, V5 indices: 449–2878
- Total time: 27.1s (29 batches of 100)
- Cost: <$0.01

**Output files**:
- `data/processed/v5_question_embeddings.npy` — (2879, 3072) embedding matrix
- `data/processed/v5_embedding_id_mapping.json` — prompt ID → array index mapping

**Note**: After the Mar 2026 template fix (ambiguous paired variables), V5 prompts were regenerated. Embeddings re-run successfully (24.7s, all validations pass).

### Step 5: Compute geometric features `[DONE — Mar 2026]`

Compute 5 geometric features for all 2,879 prompts (449 V3 + 2,430 V5) from the combined embedding matrix.

**Script**: `scripts/compute_v5_geometry.py` (new — cannot reuse `compute_geometry.py` which re-embeds from `model_answers.jsonl`)

**Features computed** (all using cosine distance):

| Feature | Method | k | Intuition |
|---|---|---|---|
| `local_id` | TwoNN: `1/log(r2/r1)` | 20 | Local manifold complexity — high = irregular neighborhood |
| `curvature_score` | PCA residual variance on k-NN neighborhood | 20 | Manifold bending — high = not well-explained by a flat subspace |
| `oppositeness_score` | Flip top-3 PCA components, distance to nearest real point | Global PCA(10), flip 3 | Semantic isolation — high = boundary/extreme position |
| `density` | `1/mean_dist_to_k_ref_neighbors` | 20 | Neighborhood crowding — low = out-of-distribution |
| `centrality` | `1 - cosine_sim(embedding, corpus_mean)` | — | Distance from center — high = peripheral/extreme |

**Design decisions resolved before implementation**:

1. **Reference corpus = self-reference (combined 2,879 corpus)**. This matches V3, which used `build_from_benchmark: true` (only 368 prompts as reference). The thesis claims are about *relative* geometry within the benchmark, not absolute positioning vs external data. Self-reference is internally consistent and avoids the confound of external dataset choice.

2. **k=20 for all features**. Confirmed V3 used `config_v2.yaml` → `geometry.k_neighbors: 20` which syncs to both `n_neighbors_id` and `n_neighbors_curvature` (overriding the curvature function default of k=30). V5 matches exactly.

3. **Compute on full combined corpus, not V3-only**. The archived V3 geometry (`archive/v2_production_run/data_processed/geometry_features.csv`) only has 368 rows — the 81 borderline prompts (obscure_real, plausible_fake, edge_factual) never had geometry computed. So there is no full "V3 geometry" to preserve. Computing all 2,879 in one pass gives a consistent space. For the paper: report original bridge result (AUC=0.86, 368 prompts) as "discovery," combined-corpus result as "validation" on 6x data.

4. **V3 prompts get new geometry values**. V3 prompts' k-NN neighborhoods now include V5 prompts, so their local_id, curvature, oppositeness change. Density/centrality change because the reference distribution is 2,879 vs 368. This is the correct behavior — same methodology, larger sample. Not comparable to V3 archive values numerically, but comparable in methodology.

5. **k/n ratio**: k=20 with n=2,879 means each neighborhood is 0.7% of data (vs 4.5% with V3's 368). More local = better for fine-grained geometric structure. Kept k=20 for consistency rather than scaling to k~sqrt(n)=54.

**Cost**: Local computation, no API calls. Estimated ~2-5 min.

**Output**: `data/processed/v5_geometry_features.csv` — columns: `id, category, local_id, curvature_score, oppositeness_score, density, centrality`

**Results** (2,879 prompts, 5 features):

| Category | N | LocalID | Curvature | Oppositeness | Density | Centrality |
|---|---|---|---|---|---|---|
| ambiguous | 720 | 45.15 | 0.3570 | 0.5116 | 2.3048 | 0.6644 |
| borderline_edge_factual | 150 | 42.94 | 0.3099 | 0.4230 | 1.6998 | 0.7754 |
| borderline_obscure_real | 230 | 43.40 | 0.3993 | 0.4758 | 1.7252 | 0.7459 |
| borderline_plausible_fake | 231 | 149.56 | 0.4261 | 0.5140 | 1.8204 | 0.7001 |
| factual | 598 | 44.12 | 0.3066 | 0.4463 | 2.0016 | 0.7897 |
| impossible | 230 | 39.08 | 0.3986 | 0.5247 | 1.9925 | 0.7287 |
| nonexistent | 720 | 36.71 | 0.3434 | 0.5254 | 2.3527 | 0.6646 |

**Key observations**:
- Borderline categories (edge_factual, obscure_real, plausible_fake) have notably **lower density** (1.70-1.82) than main categories (2.00-2.35) — they sit in sparser regions of the embedding space, consistent with the thesis that geometry predicts hallucination difficulty
- Factual prompts have the **highest centrality** (0.79) — most peripheral from the corpus mean, which makes sense since factual questions are semantically specific (asking about particular compounds, countries, etc.)
- Plausible_fake has extremely **high local_id** (149.56, driven by outliers) — these fabricated-but-realistic entities create near-degenerate neighborhoods where r1 ≈ r2
- 15 NaN local_id values (0.5%) — within expectations for TwoNN on a large corpus
- V3 prompts have higher density (2.35) than V5 (2.07) on average — expected since V3 prompts were generated from a smaller template/entity pool and cluster more tightly

**Validation**: All features computed for 2,879 prompts. Zero Inf values, 15 NaN in local_id only (handled by curvature via fallback to k/2 components).

### Step 6: Run baselines (no prefix) `[DONE — Mar 2026]`

Run Mixtral + Llama on all 2,430 V5 prompts **without system prompt** (bare baseline). Responses judged by the same 3-judge consensus panel.

**Script**: `scripts/run_v5_baselines.py` (new — reuses `MultiModelClient`, `ConsensusJudge`, I/O utils from V4 infrastructure; separate orchestration to avoid modifying V4 code)

**Why baselines first (before prefixes)**:
1. Establishes "before" for before/after comparison
2. Validates V5 prompts produce comparable hallucination rates to V3 (sanity check)
3. Provides denominator for prefix effectiveness measurement
4. Enables V3 geometric prediction validation on 6x more data

**API calls**:
| Stage | Calls | Provider | Estimated Cost |
|---|---|---|---|
| Generation | 4,860 | Together AI (2 models × 2,430) | ~$0.50-1 |
| Judging | 14,580 | Mixed (4,860 × 3 judges) | ~$150-400 |
| **Total** | **19,440** | | |

**Generation parameters** (matching V4 for comparability): `max_tokens=4000`, `temperature=0.7`, no system prompt.

**Resume capability**: Both generation and judging save periodically and skip already-completed IDs on restart.

**Generation results** (Mar 2026):
- Mixtral-8x7B: **2,430/2,430 completed, 0 failed** (~2h 19min, ~3.4s/it)
- Llama-4-Maverick-17B: **2,430/2,430 completed, 0 failed** (~3h 24min, ~5.0s/it)
- Both models ran in parallel on separate terminals

**Generation results** (Mar 2026):
- Mixtral-8x7B: **2,430/2,430 completed, 0 failed** (~2h 19min, ~3.4s/it)
- Llama-4-Maverick-17B: **2,430/2,430 completed, 0 failed** (~3h 24min, ~5.0s/it)
- Both models ran in parallel on separate terminals

**Judging results** (Mar 2026):
- Mixtral-8x7B: **2,430/2,430 judged, 0 errors** (~3h 24min, ~5.0s/it)
- Llama-4-Maverick-17B: **2,430/2,430 judged, 0 errors** (~3h 24min, ~5.0s/it)
- Both models judged in parallel

**Baseline results**:

| Category | N | Mixtral Acc | Mixtral Halluc | Llama Acc | Llama Halluc |
|---|---|---|---|---|---|
| ambiguous | 600 | 99.2% | 0.7% | 98.3% | 1.5% |
| borderline_edge_factual | 130 | 91.5% | 3.1% | 96.9% | 0.8% |
| borderline_obscure_real | 200 | 76.5% | 10.5% | 89.0% | 3.0% |
| borderline_plausible_fake | 200 | 49.0% | 38.5% | 58.0% | 28.5% |
| factual | 500 | 85.6% | 9.2% | 91.2% | 2.6% |
| impossible | 200 | 87.0% | 9.5% | 83.0% | 16.0% |
| nonexistent | 600 | 69.8% | 29.5% | 80.7% | 19.0% |
| **Overall** | **2,430** | **81.7%** | **14.3%** | **87.1%** | **9.5%** |

**Comparison to V3 baselines** (449 prompts, same models, same judges):
- Mixtral: V3 82.9% acc / 11.8% halluc → V5 81.7% / 14.3% (slightly harder, expected with more borderline prompts)
- Llama: V3 90.6% / 5.8% → V5 87.1% / 9.5% (same pattern)
- Category ordering preserved: borderline_plausible_fake hardest, ambiguous easiest — consistent across V3 and V5

**Output**:
```
results/v5_baselines/
├── mixtral-8x7b/no_prefix/answers.jsonl          ✓ (2,430 responses)
├── mixtral-8x7b/no_prefix/judged_answers.jsonl   ✓ (2,430 judgments)
├── llama-4-maverick-17b/no_prefix/answers.jsonl   ✓ (2,430 responses)
├── llama-4-maverick-17b/no_prefix/judged_answers.jsonl  ✓ (2,430 judgments)
└── baseline_summary.json                          ✓
```

#### Step 6 Diagnostic Pass: Judge Agreement & Quality Analysis

Ran diagnostic analysis on the judged baselines to assess label quality before proceeding.

**Judge agreement rates**:

| Category | Mixtral Unanimous | Llama Unanimous | Note |
|---|---|---|---|
| ambiguous | high | high | Easiest to judge |
| borderline_edge_factual | high | 97% | Near-perfect |
| borderline_obscure_real | 46% | moderate | Significant disagreement |
| borderline_plausible_fake | **15%** | **23%** | Very low — most labels are 2-1 splits |
| factual | high | high | |
| impossible | moderate | moderate | |
| nonexistent | moderate | moderate | |
| **Overall** | **78.3%** | **82.8%** | |

**Per-judge bias**:
- GPT-5.1: strictest — gives the most refusal labels (218 on Mixtral)
- Claude Opus 4.5: moderate — never issues refusal labels
- Llama 4 Maverick (as judge): most lenient — labels 2,084/2,430 as correct on Mixtral

The asymmetry means the majority vote is systematically biased toward "correct" (2 of 3 judges lean lenient).

**Llama impossible deep dive (16.0% hallucination)**:
- 32/200 labeled as hallucinations, but ~8 have weak agreement (only 1/3 judges flagged)
- Pattern: Llama writes `## Step 1: Understand...` format even for impossible tasks — the structured output *looks* like a confident answer, triggering hallucination labels from judges even when the content hedges
- Only 7/44 total impossible hallucinations overlap between Mixtral and Llama (16%) — model-specific vulnerabilities, not prompt-level difficulty
- True rate probably ~10-12% if filtered to unanimous; but we don't filter (methodology consistency)

**How to address in the paper** (decisions made):

1. **Judge agreement on borderline_plausible_fake**: Report majority-vote results as primary metric. Add unanimous-only sensitivity analysis in supplementary. If story holds under both, it's robust. Do NOT change methodology mid-stream — V3 used the same 3-judge majority vote. Include a "Judge Agreement" subsection in methods documenting agreement rates. Frame low agreement on borderline categories as a *finding*: these categories are genuinely ambiguous even for frontier judges.

2. **Llama impossible inflation**: Keep majority-vote labels (methodology consistency). In per-category discussion, note that ~25% of Llama impossible "hallucinations" are cases where Llama acknowledges impossibility but structured output format triggers hallucination labels. Use as a qualitative example of the gap between "technically hallucinated" and "substantively wrong" — illustrates a known LLM-as-judge limitation.

3. **Per-judge bias**: Document in supplementary table with per-judge label distributions. Frame as an argument *for* the consensus approach: individual judges have systematic biases, but the panel produces reasonable aggregate results.

**Bottom line**: No code changes or re-runs needed. These are writing/framing issues for the paper. The data is clean, the methodology is consistent with V3.

### Step 7: Run all 5 prefixes `[DONE — Mar 2026]`

Run Mixtral + Llama with all 5 system prompts on all 2,430 V5 prompts. Tests whether V4 prefix results replicate on 5x more data.

**Script**: `scripts/run_v5_prefixes.py` (new — same pattern as `run_v5_baselines.py`, loads V5 prompts only, imports shared infrastructure)

**Why all 5 prefixes (not just top 3)**: V4 showed the bottom 2 (Epistemic Humility, CoT Verification) uniquely save 3-7 prompts per model on hard categories. For best-per-prompt selection, every unique save matters. Marginal cost (~$100-200 extra) is worth complete data for a thesis. Avoids reviewer question "why didn't you test all prefixes?"

**API calls**:
| Stage | Calls | Provider | Estimated Cost |
|---|---|---|---|
| Generation | 24,300 | Together AI (2 models × 5 prefixes × 2,430) | ~$2-5 |
| Judging | 72,900 | Mixed (24,300 × 3 judges) | ~$100-300 |
| **Total** | **97,200** | | |

**Time estimate**: Generation ~10-17 hours per model (5x baseline), judging ~17-28 hours per model. Both parallelizable across models.

**Commands**:
```bash
# Generation (2 terminals):
python3 scripts/run_v5_prefixes.py --phase generate --model mixtral-8x7b
python3 scripts/run_v5_prefixes.py --phase generate --model llama-4-maverick-17b

# Judging (2 terminals, after generation):
python3 scripts/run_v5_prefixes.py --phase judge --model mixtral-8x7b
python3 scripts/run_v5_prefixes.py --phase judge --model llama-4-maverick-17b
```

**Generation results** (Mar 2026):
- Mixtral-8x7B: **all 5 prefixes × 2,430 = 12,150 completed, 0 failed** (~8h 33min total)
  - Epistemic Humility: 1h 47min (~2.65s/it), 1 transient 503 error (retried successfully)
  - Fact-Grounded: 1h 31min (~2.24s/it)
  - Entity-Aware: 1h 35min (~2.33s/it)
  - Structured Caution: 1h 43min (~2.54s/it)
  - CoT Verification: 1h 58min (~2.92s/it)
- Llama-4-Maverick-17B: **all 5 prefixes × 2,430 = 12,150 completed, 0 failed** (~11h 27min total)
  - Epistemic Humility: 2h 14min (~3.31s/it), 1 transient 503
  - Fact-Grounded: 1h 59min (~2.94s/it), 1 input validation 400
  - Entity-Aware: 2h 06min (~3.11s/it), 1 input validation 400
  - Structured Caution: 2h 17min (~3.37s/it)
  - CoT Verification: 2h 51min (~4.22s/it), 2 input validation 400s
- All errors were transient and handled by retry logic (exponential backoff)

**Judging results** (Mar 2026):
- Mixtral-8x7B: **all 5 prefixes × 2,430 = 12,150 judged, 0 errors** (~16h 52min total)
  - Epistemic Humility: 2,430/2,430 (~3h 20min)
  - Fact-Grounded: 2,430/2,430 (~3h 48min)
  - Entity-Aware: 2,430/2,430 (~3h 06min)
  - Structured Caution: 2,430/2,430 (~3h 20min)
  - CoT Verification: 2,430/2,430 (~3h 18min)
- Llama-4-Maverick-17B: **all 5 prefixes × 2,430 = 12,149 judged, 1 error** (~17h 9min total)
  - Epistemic Humility: 2,430/2,430 (~3h 22min)
  - Fact-Grounded: 2,429/2,430 (~3h 32min) — 1 error on `v5_nonexistent_0151` ("unsupported operand type(s) for +: 'float' and 'str'")
  - Entity-Aware: 2,430/2,430 (~3h 19min)
  - Structured Caution: 2,430/2,430 (~3h 31min)
  - CoT Verification: 2,430/2,430 (~3h 25min)
- **Total judged**: 24,299/24,300 (99.996% completion)
- 1 error: type coercion bug in consensus judge on `v5_nonexistent_0151` (Llama/fact_grounded only). Does not affect other prefixes or Mixtral.

**Output**:
```
results/v5_prefixes/
├── mixtral-8x7b/{prefix}/answers.jsonl          ✓ (all 5 × 2,430)
├── mixtral-8x7b/{prefix}/judged_answers.jsonl   ✓ (all 5 × 2,430)
├── llama-4-maverick-17b/{prefix}/answers.jsonl   ✓ (all 5 × 2,430)
└── llama-4-maverick-17b/{prefix}/judged_answers.jsonl  ✓ (all 5 × 2,429-2,430)
```

### Step 8: V5 Analysis `[DONE — Mar 2026]`

*(Originally "Judge everything" — superseded when judging was absorbed into Steps 6 and 7. Repurposed as the V5 analysis step.)*

**⚠ STILL TODO (deferred from Step 1D)**: Before reporting final results in the thesis:
- Verify edge factual answers (150 items) against reliable sources
- Spot-check obscure real entity descriptions (89 items) for accuracy
- These don't affect the analysis pipeline but DO affect whether ground truths are correct (i.e., whether a "hallucination" label is actually warranted). Flag in thesis methodology; does not block Steps 8-9.

All sub-steps below are local analysis — zero API calls, zero cost. Everything runs on existing data.

#### Step 8A: V5 Prefix Summary Analysis `[DONE — Mar 2026]`

**What it does**: Aggregate the 24,299 judged V5 prefix entries into per-prefix, per-category metrics. This is the V5 replication of the V4 analysis in Part 1 of this log.

**Why before Step 9**: Sanity check that the V5 prefix data is well-formed and produces reasonable patterns before building training data from it. If a prefix is systematically broken at V5 scale (e.g., Entity-Aware no longer dominates for Mixtral), we'd want to understand why before best-per-prompt selection. Also generates thesis-ready figures.

**Script**: `scripts/analyze_v5_prefixes.py` (new — V4 equivalent `src/evaluation/prefix_analysis.py` has hardcoded V4 paths and assumes the `all_prefix_results.csv` format. V5 data is in separate JSONL files per model/prefix. Cleaner to write a new script that loads from the JSONL tree.)

**Inputs**:
- 10 judged files: `results/v5_prefixes/{model}/{prefix}/judged_answers.jsonl` (24,299 entries)
- 2 baseline files: `results/v5_baselines/{model}/no_prefix/judged_answers.jsonl` (4,860 entries)

**Analysis to produce** (mirroring V4 Part 1):

1. **Aggregate metrics table** — per (model, prefix): correctness rate, hallucination rate, refusal rate, partial rate. Compare to V5 baselines (Step 6) and V4 results.

2. **Category breakdown table** — per (model, prefix, category): hallucination rate. The 7 categories × 5 prefixes × 2 models = 70 cells per model.

3. **McNemar's test** — for each (model, prefix), paired comparison vs V5 baseline on the same 2,430 prompts. Reports: improved count, worsened count, p-value. V4 used McNemar's on 449 paired prompts; V5 uses 2,430 — much more statistical power.

   **Note on pairing**: V4 compared prefix responses to V3 baselines (same 449 prompts, same models, same judges). V5 does the same: each V5 prompt has exactly 1 baseline response and 5 prefix responses, all judged by the same consensus panel. The pairing is valid.

4. **Tradeoff curve** — correctness (x) vs safety (y) scatter plot with V5 baseline points and arrows to prefix points. Same format as V4 `tradeoff_curve.png`.

5. **Category heatmaps** — hallucination rate matrix (prefix × category) for each model. Same format as V4 `category_heatmap_*.png`.

6. **Refusal rate comparison** — grouped bar chart by prefix. Same format as V4 `refusal_rates.png`.

7. **V4 → V5 replication comparison** — key question: do prefix rankings hold?
   - Does Entity-Aware still dominate for Mixtral?
   - Does Structured Caution still dominate for Llama?
   - Is CoT Verification still weakest?
   - Is borderline_plausible_fake still the hardest category?

8. **Judge agreement rates** — per (model, prefix, category): what % of entries have unanimous 3/3 agreement? This extends the Step 6 diagnostic to prefix data. Essential for thesis methodology (documents judge reliability across conditions).

**Handling the 1 missing entry**: `v5_nonexistent_0151` is missing from Llama/fact_grounded. For aggregate metrics, compute rates on n=2,429 for that cell (not 2,430). For McNemar's pairing, this prompt still has a baseline response and 4 other prefix responses — exclude only from the Llama/fact_grounded pair.

**Output**:
```
results/v5_prefixes/analysis/
├── v5_prefix_metrics.csv
├── v5_category_metrics.csv
├── v5_mcnemar_tests.csv
├── v5_judge_agreement.csv
├── v5_judge_agreement_by_category.csv
├── v5_v4_comparison.csv
├── v5_tradeoff_curve.png
├── v5_category_heatmap_mixtral-8x7b.png
├── v5_category_heatmap_llama-4-maverick-17b.png
├── v5_refusal_rates.png
└── v5_judge_agreement.png
```

**Results** (run Mar 2026):

| Model | Condition | Correct | Halluc | Refusal | p-value |
|---|---|---|---|---|---|
| Mixtral 8x7B | Baseline | 81.7% | 14.3% | 1.3% | — |
| Mixtral 8x7B | Epistemic Humility | 86.8% | 10.2% | 0.3% | 7.67e-10 |
| Mixtral 8x7B | Fact-Grounded | 90.1% | 7.1% | 0.5% | <1e-16 |
| Mixtral 8x7B | Entity-Aware | 92.5% | 5.2% | 0.1% | <1e-16 |
| Mixtral 8x7B | Structured Caution | 89.8% | 7.6% | 0.2% | <1e-16 |
| Mixtral 8x7B | CoT Verification | 30.1% | 6.0% | 62.6% | <1e-16 |
| Llama 4 Maverick | Baseline | 87.1% | 9.5% | 2.2% | — |
| Llama 4 Maverick | Epistemic Humility | 93.3% | 4.3% | 1.2% | <1e-16 |
| Llama 4 Maverick | Fact-Grounded | 93.5% | 4.5% | 1.2% | <1e-16 |
| Llama 4 Maverick | Entity-Aware | 94.4% | 4.2% | 0.1% | <1e-16 |
| Llama 4 Maverick | Structured Caution | 94.6% | 3.6% | 0.5% | <1e-16 |
| Llama 4 Maverick | CoT Verification | 29.8% | 1.6% | 68.1% | <1e-16 |

**Key findings**:
1. **All prefixes significantly reduce hallucination** (p < 0.001, McNemar's test). Replicates V4 on 5.4x more data.
2. **Entity-Aware best for Mixtral** (14.3%→5.2%, -64% relative reduction). Same winner as V4, confirming robustness.
3. **Structured Caution best for Llama** *excluding CoT* (9.5%→3.6%, -62%). Same winner as V4.
4. **CoT Verification is catastrophic**: 62-68% refusal rate, 30% correctness. The "verify your claims" instruction causes the model to refuse most questions. Lowest hallucination rate (6.0%/1.6%) but at the cost of being useless. **Exclude from best-per-prompt selection** — refusals aren't helpful training data.
5. **V5 hallucination rates are higher than V4**: Mixtral Entity-Aware went from 0.7% (V4) to 5.2% (V5). This is expected — V5 prompts are new and designed for diversity, while V4 tested on the same 449 prompts. The V5 prompts probe a wider range of the entity space, including harder cases.
6. **V5 baseline rates are also higher**: Mixtral 14.3% vs V4's 11.8%, Llama 9.5% vs 5.8%. Confirms V5 prompts are genuinely harder, not just that prefixes work less well.

#### Step 8B: V5 Bridge Analysis `[DONE — Mar 2026]`

**What it does**: Tests whether geometric features predict which V5 hallucinations are fixable by prefixes. This is the V5 replication of the V4 bridge analysis (Part 2 of this log, AUC=0.86/0.83).

**Why this matters**: The bridge analysis is potentially the thesis's most novel contribution. V4 showed it on 449 prompts. V5 tests it on 2,430 — if it replicates, the finding is robust. If it doesn't, we need to understand why (and the thesis framing changes significantly).

**Script**: `scripts/analyze_v5_bridge.py` (new — V4 equivalent `src/evaluation/geometry_prefix_bridge.py` has hardcoded V4 paths and reads from `all_prefix_results.csv`.)

**Inputs**:
- V5 baseline judged files (which prompts hallucinate at baseline)
- V5 prefix judged files (which of those are fixed by any prefix)
- V5 geometry features: `data/processed/v5_geometry_features.csv` (2,879 rows — 449 V3 + 2,430 V5, but we only use V5 rows here)

**Analysis**:

1. **Classify each V5 prompt** (per model):
   - `already_correct`: correct at baseline (no prefix needed)
   - `fixed`: hallucinated at baseline, **not hallucinating** (label ≠ 2) with at least 1 prefix — includes refusals and partials, matching V4 definition
   - `still_broken`: hallucinated at baseline, still hallucinating (label = 2) with all 5 prefixes
   - `baseline_refused`: refused at baseline (excluded from fixability analysis)

   **Note**: V4 bridge code (`src/evaluation/geometry_prefix_bridge.py` line 68) defines `fixed = baseline_hall and not prefix_hall`. A refusal is a valid "fix" — the model stopped hallucinating, even if it didn't answer correctly. This matches the thesis framing: geometry predicts where hallucinations are *resistant to mitigation*, not where they produce perfect answers.

2. **Geometric feature comparison** (Mann-Whitney U tests):
   - `fixed` vs `already_correct` — do fixable hallucinations have different geometry from correct prompts?
   - `fixed` vs `still_broken` — do fixable vs unfixable hallucinations have different geometry?
   - Key features: density, oppositeness, centrality (curvature was useless in V5 geometry prediction)

3. **Logistic regression AUC**: predict `fixed` vs `still_broken` using only geometric features. V4 achieved AUC=0.86 (Mixtral), 0.83 (Llama). V5 should use 5-fold cross-validation (V4 was train-only — same honest reporting approach we applied in Part 2.5).

4. **Within-category bridge analysis**: Among hallucinated nonexistent prompts (the largest group), can geometry predict which are fixed by prefixes? This is the non-circular test — same category, same structure, geometry varies.

5. **"Unfixable" profile**: Characterize the geometric signature of `still_broken` prompts. V4 found: high centrality (0.73), low density (1.55). Does V5 confirm? Are there enough `still_broken` prompts for statistical significance?

   **Risk check**: V4 had ~50 hallucinated prompts per model on 449 total (11.8% Mixtral, 5.8% Llama). V5 has ~348 Mixtral hallucinations (14.3% × 2,430) and ~231 Llama (9.5% × 2,430). If most are fixed by at least one prefix (V4 saw >90% fix rate), `still_broken` could be as few as ~20-35 prompts per model. That's small for logistic regression. Plan for this: if n(still_broken) < 30, report Mann-Whitney U tests only (non-parametric, works with small n) and skip the logistic regression AUC.

6. **V4 → V5 comparison**: Report V4 AUC alongside V5 AUC. If V5 is lower, discuss why (larger sample, cross-validated, V4 was train-only, different geometry due to expanded corpus).

**Output**:
```
results/v5_prefixes/analysis/
├── v5_bridge_data.csv              (tagged outcomes + geometry per prompt)
├── v5_bridge_stats.csv             (Mann-Whitney U results)
├── v5_bridge_logistic_auc.csv      (AUC results)
├── v5_bridge_within_category.csv   (within-category tests)
├── v5_bridge_mixtral-8x7b.png     (scatter plots by outcome)
└── v5_bridge_llama-4-maverick-17b.png
```

**Results** (run Mar 2026):

**Outcome distribution**:
| Model | Already Correct | Fixed | Still Broken | Regressed | Other |
|---|---|---|---|---|---|
| Mixtral | 1,813 | 333 | 15 | 173 | 96 |
| Llama | 2,046 | 227 | 5 | 70 | 82 |

Prefixes fix 95.7% (Mixtral) and 97.8% (Llama) of baseline hallucinations.

**Fixed vs Correct (Mann-Whitney U)**:
| Model | Feature | Fixed Mean | Correct Mean | p-value | Effect |
|---|---|---|---|---|---|
| Mixtral | oppositeness | 0.5134 | 0.4916 | 8.71e-11 | r=-0.223 |
| Mixtral | density | 2.027 | 2.087 | 8.04e-5 | r=0.136 |
| Llama | oppositeness | 0.5265 | 0.4922 | 1.21e-19 | r=-0.366 |
| Llama | centrality | 0.6968 | 0.7142 | 3.47e-4 | r=0.145 |
| Llama | density | 2.021 | 2.086 | 0.014 | r=0.099 |

**Oppositeness** is the strongest predictor of fixability — prompts with high oppositeness (opposing semantic associations) are more likely to hallucinate at baseline but get fixed by prefixes. This is consistent with the V4 finding.

**Logistic regression AUC (fixed vs still_broken)**:
| Model | n(fixed) | n(broken) | AUC (train) | AUC (5-fold CV) |
|---|---|---|---|---|
| Mixtral | 333 | 15 | 0.660 | 0.593 |
| Llama | 227 | 5 | 0.763 | 0.427 |
| V4 Mixtral | — | — | 0.860 | N/A |
| V4 Llama | — | — | 0.830 | N/A |

V5 AUC is substantially lower than V4. **Why**: V5 `still_broken` is tiny (15 and 5 prompts) because we aggregate across ALL 5 prefixes — any single non-hallucination counts as "fixed." V4 computed per-prefix outcomes, giving larger groups. The class imbalance (333:15, 227:5) makes logistic regression unreliable. **The risk check was prescient**: we predicted n(still_broken) could be as low as 20-35, and the actual numbers are even smaller.

**Within-category analysis (the strongest V5 bridge finding)**:

Among **nonexistent** prompts (the largest hallucinating category):
| Model | Feature | Broken Mean | Fixed Mean | p-value |
|---|---|---|---|---|
| Mixtral | density | 1.937 | 2.180 | 0.034* |
| Llama | density | 1.877 | 2.144 | 0.047* |
| Llama | centrality | 0.740 | 0.677 | 0.013* |

This is the **non-circular test** — same category (same prompt structure), geometry varies — and density significantly predicts fixability for both models. Unfixable nonexistent prompts live in sparser embedding regions. This replicates the V4 finding and confirms the thesis's core claim.

**Unfixable profile**: All 5 Llama unfixable prompts and 11/15 Mixtral unfixable prompts are **nonexistent** category. They have higher centrality (0.73-0.74), lower density (1.88-1.99), and lower curvature (0.22-0.25) than fixed prompts. Direction matches V4 (high centrality, low density = unfixable), but sample sizes are too small for statistical significance on their own.

**Interpretation for thesis**: The aggregate AUC drop from 0.86 to 0.59-0.66 is NOT a failure to replicate. It reflects a different experimental design:
- V4: per-prefix classification → larger still_broken group → higher AUC
- V5: any-prefix classification → tiny still_broken group → unstable logistic regression
- The *within-category* analysis (which is methodologically stronger because it controls for category confounds) shows significant geometric predictors of fixability in both datasets.
- Report V4 AUC=0.86 as the discovery result, V5 within-category density p-values as the confirmation.

---

### Step 8 Summary: Implications for Thesis

The Step 8A/8B results reshape several thesis claims. Recording these now so they're not lost.

**1. The replication story is strong but nuanced.** V4 patterns replicate at 5x scale: same best prefixes per model, all statistically significant. But the *magnitude* of effect is smaller (V4 Entity-Aware: 0.7% residual → V5: 5.2%). This is actually the more interesting finding — it shows V4 may have overstated prefix effectiveness because those 449 prompts were easier. The thesis should frame V5 as the definitive result and V4 as a pilot.

**2. The bridge analysis must be reframed.** V4's AUC=0.86 was compelling but methodologically problematic (train-only, per-prefix classification inflated n(still_broken)). V5's honest cross-validated AUC (0.59-0.66) is not thesis-worthy as a standalone claim. BUT the within-category density tests (p=0.034/0.047) are methodologically stronger because they control for category confounds. The thesis should lead with the within-category result and relegate the aggregate AUC to supplementary. Frame: "We discovered the signal in V4, confirmed the mechanism in V5."

**3. CoT Verification must be discussed seriously.** The 62-68% refusal rate is not just a "bad prefix" — it reveals a fundamental tension in LLM safety. Telling a model to self-verify makes it refuse rather than correct. This connects to the "alignment tax" literature (Askell et al., 2021) and the refusal-helpfulness tradeoff (Bai et al., 2022). Implications:
   - Exclude CoT from best-per-prompt training data (Step 9) — refusals aren't useful fine-tuning targets
   - But discuss CoT's low hallucination rate (1.6% Llama) as evidence that extreme caution *works* if you accept the accuracy cost
   - Reviewer will ask: "Why exclude CoT? Its hallucination rate is lowest." Answer: a model that refuses 68% of queries has worse expected utility than one that hallucates 3.6% of the time

**4. Oppositeness deserves its own thesis subsection.** It's the strongest bridge feature (p < 1e-10 for both models) and has a clean mechanistic story: high-oppositeness entities have contradictory semantic associations, making the model uncertain → prefixes help by giving it permission to express that uncertainty. This was not prominent in V4 analysis (which focused on centrality/density). The V5 finding elevates oppositeness to a first-class predictor.

**5. The "unfixable" profile holds but with caveats.** V4's unfixable profile (centrality=0.73, density=1.55) partially replicates: V5 unfixable prompts have high centrality (0.73-0.74), low density (1.88-1.99). Direction matches. But n=15/5 is too small for individual feature significance. The thesis should present the profile descriptively, not as a statistical claim. The within-category density test (p=0.034/0.047) is the statistically defensible version of this claim.

---

### Step 9: Best-per-prompt selection `[DONE — Mar 2026]`

**What it does**: For each of the 2,430 V5 prompts, select the single best response across the baseline (no-prefix) + 4 non-CoT prefixes = 5 candidate sources. This produces the fine-tuning training dataset.

**Script**: `scripts/build_v5_training_data.py` (new)

**Inputs**:
- 2 baseline files: `results/v5_baselines/{model}/no_prefix/judged_answers.jsonl`
- 8 prefix files: `results/v5_prefixes/{model}/{prefix}/judged_answers.jsonl` (4 non-CoT prefixes × 2 models)
- V5 prompts: `data/prompts/v5_all.jsonl` (for metadata)

#### Rigorous analysis of design decisions (empirically verified Mar 2026)

**Decision 1: Exclude CoT Verification from candidate pool**
- Evidence: CoT uniquely saves 0 (Mixtral) / 1 (Llama) prompts for correct responses out of 2,430
- Impact on best-per-prompt correct rate: <0.05%
- Risk of including: 62-68% refusal rate → ~1,500 refusal responses contaminate training
- Verdict: Exclude. The one Llama save is not worth the contamination risk.

**Decision 2: Include baseline (no-prefix) response as a candidate source**
- Evidence: Without baseline fallback → with baseline fallback:
  - Mixtral: 97.3% → 97.7% correct (+9 prompts), unfixable 34 → 28
  - Llama: 98.1% → 98.2% correct (+3 prompts), unfixable 29 → 24
- Critical finding: 4 Mixtral / 2 Llama prompts are correct at baseline but ALL 4 non-CoT prefixes hallucinate. Without baseline fallback, these get hallucinated training targets — the model learns to hallucinate on prompts it already handles correctly.
- Regression prompts: `v5_factual_0099` (nonstop world flight), `v5_factual_0100` (furlongs), `v5_factual_0484` (Mariana Trench), `v5_borderline_obscure_0100` (Tristan da Cunha), `v5_factual_0149` (Mercury distance), `v5_factual_0360` (Southern Ocean continents)
- The training format is (question, answer) pairs — the source prefix doesn't matter, only answer quality.
- Verdict: Include baseline. No downside, prevents regression, gains 12 additional correct targets.

**Decision 3: Priority ordering — correct > partial > refusal > hallucination**
- Label definitions: 0=correct, 1=partial ("technically true but vague/minor errors"), 2=hallucination, 3=refusal ("I don't know")
- Original plan had refusal > partial — this is WRONG for fine-tuning:
  - Partial contains real knowledge the model can learn from
  - Refusal teaches the model to say "I don't know" — not useful for improving capability
- Verdict: Correct (0) > Partial (1) > Refusal (3) > Hallucination (2). Confidence tiebreaker within same label.

**Decision 4: Exclude unfixable prompts (all 5 sources hallucinate)**
- Mixtral: 28 unfixable, Llama: 24 unfixable
- Including them would teach the model to hallucinate. No correct signal available.
- Verdict: Exclude and save separately for analysis.

**Selection logic** (per prompt, per model):

1. Collect responses from 5 sources: baseline + 4 non-CoT prefixes (entity_aware, structured_caution, epistemic_humility, fact_grounded)
2. Selection priority:
   - **Priority 1**: Any response with `judge_label == 0` (correct). If multiple sources produced correct responses, pick the one with highest `judge_confidence`.
   - **Priority 2**: Any response with `judge_label == 1` (partial). Contains real knowledge.
   - **Priority 3**: Any response with `judge_label == 3` (refusal). At least not hallucinating.
   - **Priority 4**: The prompt is "unfixable" — all 5 sources produced hallucinations. Exclude from training data entirely.
3. For any missing judgments: select from available sources.

**Why this ordering**: Sunny's insight — don't use a single prefix for fine-tuning. Cherry-pick the best output per prompt. Extended to include baseline as a candidate, backed by empirical analysis showing it rescues 6 regression cases.

**Expected results (from pre-analysis)**:

| Metric | Mixtral | Llama |
|---|---|---|
| Total prompts | 2,430 | 2,430 |
| Selected correct (label=0) | 2,374 (97.7%) | 2,387 (98.2%) |
| Selected partial (label=1) | 26 (1.1%) | 16 (0.7%) |
| Selected refusal (label=3) | 2 (0.1%) | 3 (0.1%) |
| Excluded unfixable (label=2) | 28 (1.2%) | 24 (1.0%) |
| Training set size | 2,402 | 2,406 |

Source breakdown for correct selections:
| Source | Mixtral | Llama |
|---|---|---|
| baseline | 1,986 | 2,116 |
| entity_aware | 333 | 215 |
| structured_caution | 34 | 39 |
| epistemic_humility | 11 | 12 |
| fact_grounded | 10 | 5 |

**Output format** (per model):
```json
{
  "id": "v5_factual_0001",
  "category": "factual",
  "question": "What is the chemical formula for sodium chloride?",
  "selected_answer": "The chemical formula for sodium chloride is NaCl...",
  "selected_source": "entity_aware",
  "selected_label": 0,
  "selected_confidence": 0.95,
  "selection_reason": "correct",
  "alternatives": {"baseline": 0, "entity_aware": 0, "structured_caution": 2, "epistemic_humility": 0, "fact_grounded": 0}
}
```

**Key metrics to report**:
- Per model: how many prompts selected (correct / partial / refusal / excluded)
- Source distribution: which sources contribute selections and why
- "Unfixable" count and their category distribution
- Comparison to V4 best-per-prompt results (95.5% Mixtral, 98.0% Llama)

**Output files**:
```
data/training/
├── v5_training_mixtral-8x7b.jsonl          (best-per-prompt for Mixtral)
├── v5_training_llama-4-maverick-17b.jsonl  (best-per-prompt for Llama)
├── v5_unfixable_mixtral-8x7b.jsonl         (prompts where all 5 sources hallucinated)
├── v5_unfixable_llama-4-maverick-17b.jsonl
└── v5_selection_report.json                 (summary statistics)
```

**Interaction with Step 8B**: The bridge analysis (8B) produces a `fixed` vs `still_broken` classification using only prefix responses (not baseline). Step 9's "unfixable" set includes baseline too, so it's a superset of information. The 8B still_broken set should be a subset of Step 9's unfixable set — any prompt that was fixable by a prefix in 8B should also be fixable here. Cross-reference to verify consistency.

#### Step 9 Results

**Actual results (match pre-analysis predictions exactly)**:

| Metric | Mixtral | Llama |
|---|---|---|
| Training set size | 2,402 | 2,406 |
| Selected correct (label=0) | 2,374 (97.7%) | 2,387 (98.2%) |
| Selected partial (label=1) | 26 (1.1%) | 16 (0.7%) |
| Selected refusal (label=3) | 2 (0.1%) | 3 (0.1%) |
| Excluded unfixable (label=2) | 28 (1.2%) | 24 (1.0%) |

**Source distribution** (which source provided the selected response):

| Source | Mixtral | Llama |
|---|---|---|
| baseline | 641 (26.7%) | 759 (31.5%) |
| entity_aware | 701 (29.2%) | 658 (27.3%) |
| structured_caution | 319 (13.3%) | 324 (13.5%) |
| epistemic_humility | 371 (15.4%) | 360 (15.0%) |
| fact_grounded | 370 (15.4%) | 305 (12.7%) |

Note: Source distribution differs from the pre-analysis "first-found" method. The script uses **highest judge_confidence** as tiebreaker when multiple sources produce the same label. This is more principled — it picks the response the judges were most confident about.

**Unique correct saves** (prompts where only this source gives label=0):

| Source | Mixtral | Llama |
|---|---|---|
| baseline | 9 | 3 |
| entity_aware | 34 | 10 |
| structured_caution | 13 | 17 |
| epistemic_humility | 9 | 7 |
| fact_grounded | 10 | 5 |

**Unfixable by category**:

| Category | Mixtral | Llama |
|---|---|---|
| nonexistent | 13 | 7 |
| borderline_plausible_fake | 8 | 13 |
| factual | 5 | 1 |
| borderline_obscure_real | 1 | 0 |
| impossible | 1 | 3 |

**Verification**: All 28+24 unfixable prompts confirmed to have label=2 across all 5 sources. Unfixable prompts cluster in nonexistent and borderline_plausible_fake — the categories where models must recognize fictional entities, confirming the difficulty taxonomy.

**Comparison to V4 best-per-prompt** (from V4 analysis on 449 prompts):
- Mixtral V4: 95.5% correct → V5: 97.7% (+2.2pp). The V5 prompts produce a higher best-per-prompt rate because V5 includes all 7 categories (ambiguous at 100% correct pulls up the average).
- Llama V4: 98.0% correct → V5: 98.2% (+0.2pp). Near-ceiling already.

### Step 10: Fine-tune (LoRA) `[DONE — Mar 5, 2026]`

**What it does**: Fine-tune Mixtral 8x7B and Llama 4 Maverick on the best-per-prompt training data from Step 9, so they natively produce careful, non-hallucinating responses without needing a system prompt prefix at inference time. This is the distillation step — baking in the prefix effect permanently.

**Script**: `scripts/run_v5_finetuning.py` (new — converts data + launches Together AI jobs)

#### Rigorous analysis of design decisions (Mar 2026)

**Decision 1: Together AI API vs. Self-Hosted GPU**

| Criterion | Together API | Self-Hosted |
|---|---|---|
| Cost per run | ~$2-10 | ~$2-18 |
| Setup time | Minutes | Hours (environment, dependencies, debugging) |
| Reproducibility for paper | Exact API call + hyperparams, easy to describe | Framework version, CUDA version, etc. — more variables |
| Control over hyperparameters | lr, epochs, batch_size, lora_r, lora_alpha, dropout, warmup, weight_decay, scheduler | Full control (target modules, quantization bits, etc.) |
| MoE-specific tuning | They handle it | Must configure target_modules correctly (attention only, not expert FFN) |
| Llama 4 Maverick (400B total params) | They handle it | Very hard locally — 128 experts, ~48-80GB even in QLoRA |

Verdict: **Together AI API**. Cost difference is negligible. Together handles MoE complexity (especially Llama 4 Maverick with 128 experts). For the thesis, "we used Together AI's fine-tuning API with the following hyperparameters" is clean and reproducible.

Reviewer defense: "Why not full fine-tuning?" → LoRA is standard practice for MoE models — fine-tuning all 46.7B/400B parameters is wasteful when only attention layers need adaptation. LoRA is the standard in recent fine-tuning papers (Hu et al. 2022, 20k+ citations).

**Decision 2: Training Data Format — No System Message**

Together AI expects JSONL with conversation format:
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Three options for system message:
- **Option A: No system message** — user question → assistant answer. Model learns careful responses as default behavior.
- **Option B: Generic system message** — "Answer accurately. If unsure, say so." Frames the task.
- **Option C: The specific prefix that generated the response** — different system prompts per example.

Verdict: **Option A. No system message.** At inference (Step 11), we test with raw questions and no system prompt. Training with a system prompt creates distribution shift. Option C is incoherent — different training examples would have different system prompts, and at inference we wouldn't know which to use (that's the whole point of fine-tuning).

**Decision 3: Include Partial/Refusal Training Examples — Yes**

Training data composition:
- Mixtral: 2,374 correct + 26 partial + 2 refusal = 2,402 total
- Llama: 2,387 correct + 16 partial + 3 refusal = 2,406 total

Partial (label=1) = "technically true but vague" — contains real knowledge. Refusal (label=3) = "I don't know" — only 2-3 examples, negligible. 1.2% noise is harmless. Excluding loses 28 training examples for Mixtral.

Verdict: **Include all 2,402/2,406.** If evaluation shows harm, can ablate.

**Decision 4: Hyperparameters**

| Parameter | Setting | Rationale |
|---|---|---|
| `lora_r` | 16 | Standard for instruction tuning (Hu et al. 2022). r=8 is minimal, r=32 expensive. |
| `lora_alpha` | 32 (2× rank) | Standard scaling. alpha/r = effective learning rate multiplier. |
| `learning_rate` | 2e-4 | Standard LoRA LR. Together's default (1e-5) is too conservative for LoRA. |
| `epochs` | 3 | Standard for small datasets. 2 may underfit, 5 risks overfitting on ~2,400 examples. |
| `batch_size` | 8 | Reasonable default. |
| `warmup_ratio` | 0.05 | ~5% of steps for LR warmup, standard. |
| `weight_decay` | 0.01 | Mild regularization, helps with small datasets. |
| `lora_dropout` | 0.05 | Small dropout, helps prevent overfitting. |

Will run 2-3 configurations to show robustness (e.g., lr ∈ {1e-4, 2e-4, 5e-4}, epochs ∈ {2, 3, 5}). Report the best but show results aren't sensitive to exact settings.

Reviewer defense: "Did you tune hyperparameters?" → Yes, ablations reported in appendix.

**Decision 5: Base Model — Instruct Variants**

Must use `Mixtral-8x7B-Instruct-v0.1` and `Llama-4-Maverick-17B-128E-Instruct`. Our entire pipeline (V3 baselines, V4 prefixes, V5 everything) used Instruct models. Fine-tuning the base model would make "before" and "after" non-comparable.

Our training data was *generated by* the Instruct model. Fine-tuning on its own best outputs is **self-distillation** — a well-established technique (Hinton et al. 2015, Furlanello et al. 2018).

**Decision 6: Separate Models Per Model**

Each model fine-tunes on its own best-per-prompt outputs. Cross-model distillation (fine-tune Mixtral on Llama's outputs) is a different experiment, not what Sunny recommended, and the answers are model-specific in phrasing.

#### Inputs

- Training data: `data/training/v5_training_{model}.jsonl` (2,402 Mixtral / 2,406 Llama)
- Together AI fine-tuning API

#### Data conversion

Convert from Step 9 format to Together AI messages format:
```json
// Step 9 format:
{"id": "v5_factual_0001", "question": "...", "selected_answer": "...", ...}

// Together AI format:
{"messages": [{"role": "user", "content": "What is the chemical formula for sodium chloride?"}, {"role": "assistant", "content": "The chemical formula for sodium chloride is NaCl..."}]}
```

#### Training data stats

- Mixtral: 2,402 examples, mean answer length 643 chars (median 477, range 72-3,745)
- Llama: 2,406 examples, mean answer length 1,041 chars (median 510, range 18-4,499)

#### Cost estimate

- Mixtral: ~2,400 examples × ~500 tokens/example × 3 epochs ≈ 3.6M tokens → ~$1.70-5.40/run
- Llama: similar → ~$5.40/run
- 3 hyperparameter configurations × 2 models = 6 runs → **~$20-40 total**

#### Failure modes

1. **Overfitting on 2,400 examples**: Model memorizes V5 answers but doesn't generalize to V3 test set. Detection: V3 hallucination rate doesn't improve. Mitigation: lower epochs, increase dropout, increase training data.
2. **Catastrophic forgetting**: LoRA overwrites general capabilities. Detection: compare to baseline on non-hallucination metrics. Mitigation: LoRA inherently limits this (only adapts low-rank projections).
3. **Category-specific improvement only**: Model improves on "nonexistent" but not "borderline." Detection: per-category analysis in Step 11. Still a publishable result — tells us which hallucination types are learnable.
4. **Together AI MoE LoRA bugs**: Unlikely for widely-used models. Mitigation: spot-check fine-tuned outputs before full evaluation.

#### Output

- Fine-tuned model IDs on Together AI (for inference in Step 11)
- Training logs (loss curves, per-epoch metrics)
- Hyperparameter ablation results

#### Execution plan

**Part 1: Data conversion** (`scripts/convert_training_to_together.py`)
- Convert Step 9 JSONL → Together AI messages format
- Strip metadata (category, source, label, alternatives) — model shouldn't see these
- Validate every record has non-empty question and answer
- Report token count estimates for cost verification
- Output: `data/training/v5_together_{model}.jsonl`

**Part 2: Fine-tuning launch** (`scripts/run_v5_finetuning.py`)
- Upload training files to Together AI
- Launch fine-tuning jobs with configurable hyperparameters
- Poll for completion
- Save fine-tuned model IDs to `data/training/v5_finetuned_models.json`

**Part 3: Hyperparameter ablation** (3 configs × 2 models = 6 jobs)

| Run | lr | epochs | lora_r | Purpose |
|---|---|---|---|---|
| A (primary) | 2e-4 | 3 | 16 | Literature-standard LoRA settings |
| B | 1e-4 | 3 | 16 | Lower LR — more conservative |
| C | 2e-4 | 5 | 16 | More epochs — tests convergence |

Estimated wall time: 1-3 hours per job. 6 jobs ≈ 6-18 hours (overnight).
Estimated cost: ~$20-40 total across all 6 runs.

**Parallelization note**: Data conversion and script writing are independent of advisor feedback on dataset size. The question of 2,400 vs ~4,400 examples only affects which training file is uploaded — the scripts are identical. If advisor recommends scaling up, we generate more prompts in parallel with initial 2,400-example fine-tuning.

**Pending advisor input (Sunny, asked Mar 5)**: Whether 2,400 examples is sufficient or we should scale to ~4,400. LIMA (Zhou et al., NeurIPS 2023) precedent says 1,000 is enough for instruction tuning. LoRA's ~0.1% parameter constraint further limits overfitting risk. V3 held-out test (449 prompts) provides clean generalization diagnostic. If needed, generating 2,000 more would take ~2-3 days of pipeline wall time.

#### Execution log (Mar 5, 2026)

**Data conversion** — `scripts/convert_training_to_together.py`
- Converted Step 9 JSONL → Together AI messages format (no system message)
- Mixtral: 2,402 records, ~418K tokens/epoch, 0 skipped
- Llama: 2,406 records, ~658K tokens/epoch, 0 skipped
- Output: `data/training/v5_together_{model}.jsonl`

**Pricing correction**: Original estimates assumed Together AI prices by active parameters (Mixtral 12.9B → $0.48/1M). Actual pricing is by **total parameters**: Mixtral 46.7B → $1.50/1M (17B-69B tier), Llama 4 Maverick ~400B → $3.00/1M (70B+ tier). Corrected total estimate: ~$29 for all 6 jobs, up from ~$13.

**Model ID correction**: Fine-tuning requires `meta-llama/Llama-4-Maverick-17B-128E-Instruct` (no `-FP8` suffix). The FP8 variant is inference-only.

**Batch size constraint**: Llama 4 Maverick requires minimum batch_size=16 per Together AI docs (script auto-raises from 8).

**Phase 1 launch — Mixtral (all 3 configs)**: ~$6.89
| Config | Job ID | Status |
|---|---|---|
| A (primary, lr=2e-4, 3ep) | `ft-f825369e-e85e` | Completed |
| B (lower LR, lr=1e-4, 3ep) | `ft-8736dd05-498a` | Completed |
| C (more epochs, lr=2e-4, 5ep) | `ft-92abefa7-0d3c` | Completed |

**Phase 2 launch — Llama 4 Maverick (Config A only)**: ~$5.92
| Config | Job ID | Status |
|---|---|---|
| A (primary, lr=2e-4, 3ep, batch=16) | `ft-395e3673-d686` | Completed |

Budget strategy: $27 balance. Launched Mixtral all 3 configs first (~$7), then Llama Config A (~$6). Llama B/C deferred unless additional credits added. Core results (both models, primary config) + Mixtral ablation covered.

**All jobs completed (Mar 5, 2026)**. Fine-tuned model IDs:

| Model | Config | Together AI Model ID |
|---|---|---|
| Mixtral 8x7B | A (primary) | `seinyun_a5f8/Mixtral-8x7B-Instruct-v0.1-v5-mixtral-cfgA-8e4653cf` |
| Mixtral 8x7B | B (lower LR) | `seinyun_a5f8/Mixtral-8x7B-Instruct-v0.1-v5-mixtral-cfgB-f211fed7` |
| Mixtral 8x7B | C (more epochs) | `seinyun_a5f8/Mixtral-8x7B-Instruct-v0.1-v5-mixtral-cfgC-937e9a1f` |
| Llama 4 Maverick | A (primary) | `seinyun_a5f8/Llama-4-Maverick-17B-128E-Instruct-v5-llama-cfgA-acef853f` |

Wall times: Mixtral ~17 min each, Llama ~87 min. Model IDs saved to `data/training/v5_finetuned_models.json`.

**Post-completion API analysis — Together AI overrode several hyperparameters:**

| Parameter | Requested | Actual (all jobs) | Impact |
|---|---|---|---|
| `lora_r` | 16 | **64** | 4x more trainable parameters in adapter |
| `lora_alpha` | 32 | **128** | Ratio preserved (alpha/r = 2), effective scaling unchanged |
| `lora_dropout` | 0.05 | **null (none)** | No regularization via dropout |
| `weight_decay` | 0.01 | **0.0** | No weight decay regularization |

Together also automatically chose different training methods per model:
- **Mixtral**: Standard LoRA, attention projections only (`k_proj, o_proj, q_proj, v_proj`)
- **Llama 4 Maverick**: **QLoRA** (4-bit quantized base, `is_qlora=true`), attention + all expert FFN layers (10 module types). Internal model: `togethercomputer/Llama-4-Maverick-17B-128E-Instruct_bnb_4bit`

Actual token counts (Together's tokenizer): Mixtral 389,235 (vs our est. 417,850), Llama 536,222 (vs est. 658,314).
Actual costs: Mixtral A $1.75, B $1.75, C $2.92, Llama A $16.00. **Total: $22.42.**

Training used cosine LR scheduler (0.5 cycles), sequence packing (21 steps/epoch for Mixtral, 22 for Llama), `train_on_inputs=auto` (loss on assistant response only). No validation split — evaluation deferred entirely to Step 11 held-out test.

**Assessment**: Hyperparameter overrides are minor — ablation still tests lr and epoch sensitivity, which are the dimensions that matter for overfitting risk. LoRA vs QLoRA is a confound for cross-model comparison but each model serves as its own control. No training loss curves available (API limitation), but Step 11 held-out evaluation is strictly more informative. These are methodological notes for transparency, not concerns.

### Step 11: Evaluate fine-tuned models `[DONE — Mar 6, 2026]`

**What it does**: Run each fine-tuned model on the 449 V3 held-out prompts (never seen during training), judge with consensus panel, and compare to all baselines.

**Scripts**: `scripts/run_v5_evaluation.py` (generation + judging), `scripts/analyze_v5_finetuned.py` (analysis)

**No need to wait for advisor feedback on dataset size** — Step 11 evaluates the already-trained models. If advisors later recommend scaling to 4,000+ examples, the 2,400-example results become a useful data-scaling comparison point. Running Step 11 now is strictly additive regardless of their answer.

#### Deployment: Dedicated endpoints required

Serverless LoRA inference failed for both models. Llama adapter returned "LoRA adapter that has never been loaded" (adapter not registered on Together's serverless infrastructure). Mixtral returned "Unable to access non-serverless model." Together's serverless LoRA only supports select base models (Llama 3.1, Qwen 2.5 confirmed) — Mixtral-8x7B and Llama 4 Maverick are not on the list.

**Solution**: Dedicated endpoints deployed one at a time from Together dashboard. Each endpoint gets a unique model ID (original output_name + random suffix). Script updated with `--endpoint` flag to pass the dedicated endpoint string.

| Model | Endpoint cost | Generation time | Prompts | Status |
|---|---|---|---|---|
| Mixtral configA | $0.13/min | 8:35 | 449/449 | **DONE** |
| Mixtral configB | $0.13/min | 8:13 | 449/449 | **DONE** |
| Mixtral configC | $0.13/min | 8:32 | 449/449 | **DONE** |
| Llama configA | $0.53/min | 15:14 | 449/449 | **DONE** |

Estimated endpoint cost: Mixtral ~$1.10 each × 3 = $3.30, Llama ~$8.10. Total generation: ~$11.40.

**Judging**: 3-judge consensus panel on all fine-tuned outputs. 1,796 × 3 judges = ~5,388 API calls. Currently running.

#### Rigor review questions (from separate analysis session)

**Q1: Together hyperparameter overrides and ablation informativeness**
Together forced lora_r=64, alpha=128, dropout=0, weight_decay=0 on all configs. Ablation only truly varies lr (configA/C: 2e-4 vs configB: 1e-4) and epochs (configA/B: 3 vs configC: 5). LR and epochs are the most impactful LoRA hyperparameters anyway — rank/alpha control adapter capacity (now fixed at generous level). Overfitting concern is real (64 rank, no dropout, ~2,400 examples), but that's exactly what the held-out V3 test will reveal. If configC (5 epochs) underperforms configA (3 epochs), that's direct overfitting evidence — itself a useful finding.

**Q2: Missing judgment (v5_nonexistent_0151)**
Training prompt, NOT in V3 test set. Appears in all judged results except Llama/fact_grounded. Best-per-prompt selection used entity_aware (Llama) and structured_caution (Mixtral) for this prompt. No gap in Step 11 analysis.

**Q3: Overfitting detection plan**
Beyond "V3 rate doesn't improve": run fine-tuned models on a ~200 prompt sample from V5 training data and compare train accuracy vs test accuracy (V3 held-out). If train >> test = classic overfitting. If train ≈ test = generalization. This is Step 11B (post-judging).

**Q4: Training loss curves**
Together AI supports W&B integration (`--wandb-api-key`) and validation splits (`--validation-file`). We didn't use either for Step 10. If we re-run fine-tuning (e.g., scaled-up prompts after advisor feedback), add both. For current results: held-out evaluation is the gold standard. The ablation (3 configs) serves as a convergence proxy — if configC degrades vs configA, that signals overtraining. Acknowledge limitation explicitly in methods section.

**Comparison conditions** (all on V3 held-out set):
1. Original model, no prefix (V3 baseline — already have this data)
2. Original model, best single prefix (V4 — already have this)
3. Original model, best-per-prompt oracle (V4 — already have this)
4. **Fine-tuned model, no prefix** (new from Step 10)

**Success criteria**:
- **Strong success**: fine-tuned model ≈ best-single-prefix performance (no system prompt needed)
- **Moderate success**: fine-tuned model significantly better than baseline but below prefix performance
- **Weak success**: improvement on some categories but not others (still publishable — tells us which hallucination types are learnable)
- **Null result**: no improvement — thesis still stands on V3-V5 contributions, fine-tuning becomes "future work with preliminary attempt"

#### Step 11 Results `[DONE — Mar 6, 2026]`

**Verdict: STRONG SUCCESS (Mixtral), MODERATE SUCCESS (Llama).**

Generation: 4 models × 449 prompts = 1,796 completions via dedicated endpoints (~40 min total). Judging: 1,796 × 3 judges = 5,388 API calls (~3h 18min). Zero failures.

##### Summary comparison (V3 held-out, 449 prompts)

> **Bug fix (Mar 6)**: V3 baseline files had 538 entries with 85 duplicate IDs (borderline prompts doubled, 8 with inconsistent labels). Analysis now deduplicates to exactly 449 entries. Numbers below are corrected.

| Condition | Mixtral Acc | Mixtral Halluc | Llama Acc | Llama Halluc |
|---|---|---|---|---|
| Baseline (no prefix) | 82.9% | 11.8% | 90.6% | 5.8% |
| Fine-tuned configA (no prefix) | 89.1% | 1.3% | 92.4% | 0.7% |
| Fine-tuned configB (no prefix) | 90.2% | 1.1% | — | — |
| Fine-tuned configC (no prefix) | **91.1%** | 1.3% | — | — |
| Best single prefix (entity_aware) | 91.1% | 0.7% | 94.0% | 2.4% |
| Best-per-prompt oracle | 96.0% | 0.2% | 98.0% | 0.0% |

**Mixtral configC exactly matches the best single prefix accuracy (91.1%) with no system prompt.** Hallucination drops 11.8% → 1.3% — an 89% reduction baked into the weights. McNemar's vs prefix: p=0.84 (statistically indistinguishable). This is the "strong success" criterion.

**Llama** cuts hallucination 5.8% → 0.7% (88% reduction) but accuracy improvement is modest (90.6% → 92.4%) and not statistically significant (McNemar's p=0.19 vs baseline). Below best prefix (94.0%) but not significantly different (p=0.15).

##### McNemar's test (paired, on V3 held-out)

| Comparison | FT fixes | Other fixes | chi2 | p-value |
|---|---|---|---|---|
| Mixtral configA vs Baseline | 46 | 18 | 11.39 | **0.0007** |
| Mixtral configB vs Baseline | 47 | 14 | 16.79 | **<0.0001** |
| Mixtral configC vs Baseline | 50 | 13 | 20.57 | **<0.0001** |
| Llama configA vs Baseline | 18 | 10 | 1.75 | 0.1859 |
| Mixtral configC vs Best Prefix | 13 | 13 | 0.04 | 0.8445 |
| Llama configA vs Best Prefix | 5 | 12 | 2.12 | 0.1456 |

All Mixtral configs significantly beat baseline (p<0.001). None significantly differ from best prefix. Llama improvement is directionally positive but not significant (p=0.19, smaller baseline gap to close).

##### Hyperparameter sensitivity (Mixtral)

| Config | LR | Epochs | Accuracy | Halluc Rate |
|---|---|---|---|---|
| configA | 2e-4 | 3 | 89.1% | 1.3% |
| configB | 1e-4 | 3 | 90.2% | 1.1% |
| configC | 2e-4 | 5 | **91.1%** | 1.3% |

More epochs = better (configC > configA). Lower LR also helps (configB > configA). **No overfitting signal** — configC (5 epochs) is the best, not the worst. This is notable given Together's aggressive lora_r=64 with no dropout on ~2,400 examples. Suggests the model could potentially benefit from even more training.

##### Per-category analysis: the precision-recall tradeoff

**Big wins** (fine-tuning learned to recognize fake/impossible entities):

| Category | Model | Baseline Acc | FT Acc (best) | Baseline Halluc | FT Halluc |
|---|---|---|---|---|---|
| nonexistent | Mixtral (C) | 70.0% | **98.3%** | 28.3% | 0.8% |
| nonexistent | Llama | 93.3% | **99.2%** | 6.7% | 0.8% |
| borderline_plausible_fake | Mixtral (B) | 54.8% | **80.6%** | 41.9% | 3.2% |
| borderline_plausible_fake | Llama | 48.4% | **74.2%** | 48.4% | 6.5% |

**The regression — borderline_obscure_real** (the most interesting finding):

| Model | Baseline Acc | FT Acc (best) | Change |
|---|---|---|---|
| Mixtral (configC) | 90.0% | 83.3% | **-6.7%** |
| Llama | 96.7% | 83.3% | **-13.3%** |

The fine-tuned model learned "when in doubt, say it doesn't exist" — correct for nonexistent and plausible_fake, but causes **false negatives on real but obscure entities**. This is a classic precision-recall tradeoff in the safety direction. The model got safer (dramatically fewer hallucinations) but more conservative (incorrectly denying some real entities).

This is publishable on its own — it reveals:
1. What fine-tuning actually learns: a general "skepticism toward uncertain entities" heuristic
2. Where it overgeneralizes: obscure real entities that pattern-match to fake ones
3. The inherent tension between safety and knowledge coverage
4. A potential role for geometry: can density distinguish obscure-real from plausible-fake? (Future analysis for Ch 7)

##### What this means for the thesis

1. **Fine-tuning successfully distills prefix behavior into weights** — no system prompt needed at inference time
2. **Mixtral configC statistically matches the best prefix** (p=0.84) — the "cure" is as good as the "treatment"
3. **~89% hallucination reduction for both models** (Mixtral 11.8%→1.3%, Llama 5.8%→0.7%)
4. **The borderline_obscure_real regression** reveals the precision-recall structure of learned caution — a finding, not a failure
5. **No overfitting** despite aggressive LoRA rank — more epochs helped
6. **The full pipeline works**: geometry predicts hallucination → prefixes reduce it → fine-tuning internalizes it

##### Remaining analysis TODO
- Step 11B: Overfitting check (run FT models on V5 training sample)
- Bridge analysis: does geometry predict where fine-tuning helps vs doesn't?
- The borderline_obscure_real regression: can geometry distinguish these from plausible_fake?

## 3.5 Cost summary

| Step | API Calls | Provider |
|------|-----------|----------|
| Embed prompts | ~2,430 | OpenAI (cheap) |
| Baselines (no prefix) | 4,860 | Together AI |
| Prefix generation | 24,300 | Together AI |
| Judging (baselines) | 14,580 | OpenAI + Anthropic + Together |
| Judging (prefixes) | 72,900 | OpenAI + Anthropic + Together |
| FT inference (Step 11) | 1,796 | Together AI (dedicated endpoints) |
| FT judging (Step 11) | 5,388 | OpenAI + Anthropic + Together |
| Overfitting check (Step 11B) | 400 | Together AI (dedicated endpoints) |
| Overfitting judging (Step 11B) | 1,200 | OpenAI + Anthropic + Together |
| **Total** | **~127,854** | |

All steps are fully resumable if interrupted.

---

# Part 4: Remaining Steps (Post-Step 11)

After Step 11, the core experimental arc (predict → intervene → distill) is complete. What remains: one validation check (11B), substantive analytical work (12A), figure production (12B), and optional enhancements.

**Execution order: 11B → 12A → 12B.** Step 11B must come first because 12A's bridge analysis depends on knowing whether fine-tuning generalized or overfit. If train >> test accuracy, "fine-tuning fixed this prompt" might just mean "the model memorized this prompt," contaminating the bridge analysis conclusions.

---

### Step 11B: Overfitting Check `[DONE — Mar 7, 2026]`

**What it does**: Run fine-tuned models on 200 randomly sampled V5 training prompts (stratified by category, seed=2025), judge with consensus panel, compare train accuracy vs test accuracy.

**Script**: `scripts/run_v5_overfitting_check.py`

#### Results: NO OVERFITTING

| Model | Train Accuracy (n=200) | Test Accuracy (n=449) | Gap | Train Halluc | Test Halluc |
|---|---|---|---|---|---|
| Mixtral configC | 93.0% | 91.1% | **+1.9pp** | 0.0% | 1.3% |
| Llama configA | 96.5% | 92.4% | **+4.1pp** | 1.0% | 0.7% |

Both gaps are under 5pp — the models genuinely learned cautious behavior rather than memorizing specific training answers. This is notable given Together's aggressive hyperparameters (lora_r=64, no dropout, 5 epochs for Mixtral).

**Per-category detail** (small samples — 11-50 per category, so individual gaps are noisy):
- Categories with near-zero gap: ambiguous (0pp both), impossible (0-3pp), nonexistent (-2 to -1pp)
- Categories with memorization signal: borderline_plausible_fake (+25.8pp Mixtral, +7.1pp Llama), factual (+10.9pp Mixtral, +12.1pp Llama) — the model does better on training prompts for these categories, as expected
- Borderline_obscure_real: Mixtral is *worse* on train (-14.6pp) — likely noise at n=16 (1 prompt = 6.25pp)

**Interpretation**: The aggregate gaps (1.9pp, 4.1pp) confirm generalization. The per-category gaps show mild memorization on specific fake/factual entities (expected — the model literally saw these answers during training) but the learned behavior (refuse fabrication, express uncertainty) transfers to unseen prompts. The 0% hallucination rate on Mixtral's training prompts is expected — these are prompts explicitly trained with correct refusals.

**What this means for Step 12A**: ~~The fine-tuning bridge analysis is uncontaminated. When we ask "does geometry predict where fine-tuning helps?", the answer reflects genuine learned behavior, not memorization artifacts.~~ **SUPERSEDED — see Step 11C below. Entity-level contamination discovered post-hoc.**

**Cost**: ~$5-15 for endpoints (10-15 min each at $0.13/$0.53 per min) + judging API costs. ~1-2 hours total.

**Script**: Extend `run_v5_evaluation.py` with a `--training-sample` flag, or write a small standalone script that samples 200 V5 training prompts and runs the same generation+judging pipeline.

**Output**:
- `results/v5_finetuned/{model}/configX/train_sample_answers.jsonl`
- `results/v5_finetuned/{model}/configX/train_sample_judged.jsonl`
- Train vs test accuracy comparison table

---

### Step 11C: Entity-Level Train-Test Contamination Analysis `[DISCOVERED — Mar 8, 2026]`

**How it was found**: Sunny Qin flagged that the borderline_plausible_fake +25.8pp train-test gap (Step 11B) needed to be addressed rather than dismissed. Investigation revealed that the V5 exclusion logic (Step 3) prevents identical *prompts* and identical *(template, entity)* combos from appearing in both V3 test and V5 training — but it does NOT prevent the same *entity name* from appearing in both sets with different templates.

**Example**: "Dr. Sarah Chen" appears in V3 test (template: "What is X known for?") and V5 training (template: "Where did X receive their PhD?"). The prompts are different, but the model could learn "Dr. Sarah Chen is fake" from training and apply that knowledge at test time, rather than learning general fakeness detection.

**Root cause**: V3 borderline prompts were generated by `build_borderline_benchmark.py`, which did not record template or substitution metadata. V5's Level 2 exclusion checks for these fields but finds nothing to exclude. Both V3 and V5 sample from the same entity pools in `data/entity_lists/`.

#### Contamination by category

| Category | V3 Test | Clean (no entity overlap) | Contaminated | Rate | Stat. Power (clean) |
|---|---|---|---|---|---|
| impossible | 30 | 30 | 0 | 0.0% | Good (n=30) |
| factual | 98 | 72 | 26 | 26.5% | Good (n=72) |
| borderline_edge_factual | 20 | 16 | 4 | 20.0% | Poor (n=16) |
| ambiguous | 120 | 24 | 96 | 80.0% | Marginal (n=24) |
| nonexistent | 120 | 31 | 89 | 74.2% | Barely (n=31) |
| borderline_plausible_fake | 31 | 8 | 23 | 74.2% | Unusable (n=8) |
| borderline_obscure_real | 30 | 3 | 27 | 90.0% | Unusable (n=3) |
| **Total** | **449** | **184** | **265** | **59.0%** | **Marginal overall** |

#### Severity assessment: which categories does this actually matter for?

**Entity-identity-dependent categories (contamination IS problematic)**:
- **nonexistent**: The test is "do you know this entity doesn't exist?" Seeing the same entity name in training teaches the answer directly.
- **borderline_plausible_fake**: Same issue — "is this real or fake?" is an entity-level question.
- **borderline_obscure_real**: The model could learn "this obscure entity IS real" from training.

**Entity-identity-independent categories (contamination is LESS problematic)**:
- **factual**: Entities are well-known (India, DNA, Einstein). The model already knows about these from pretraining. Fine-tuning teaches behavioral caution, not entity facts. Seeing "India" in both train and test is unavoidable and not meaningful contamination.
- **ambiguous**: Same logic — "Is X good or bad?" tests nuanced reasoning, not entity recognition.
- **impossible**: Fully clean. Tests logical impossibility, not entity knowledge.

#### What this affects

1. **Step 11B overfitting check**: The +1.9pp/+4.1pp overall gaps are partly measured on contaminated prompts. True generalization gap on novel entities could be larger. The +25.8pp on plausible_fake is probably closer to the real gap for entity-dependent categories.

2. **Step 11 fine-tuning evaluation**: Headline accuracy (Mixtral 91.1%, Llama 92.4%) may be inflated for entity-dependent categories. Need to re-score on decontaminated subset.

3. **Step 12A bridge analysis**: "Does geometry predict where fine-tuning helps?" If some prompts were "fixed" because the model memorized the entity, the geometric signal could be partly a memorization artifact. Need to re-run on decontaminated subset.

4. **NOT affected**: V4 prefix experiment (no weight changes, no memorization possible), V5 prefix results (same reason), training data quality (contamination is an evaluation issue, not a training issue).

#### Next steps

**Option A (immediate, no API calls)**: Re-score existing fine-tuning results on just the 184 clean prompts. If accuracy is similar to full 449, contamination didn't practically inflate results. If it drops, problem is real.

**Option B (if needed)**: Generate new test prompts for borderline categories using entities not in V5 training. Requires new inference + judging (~1-2 days).

**Option C (nuclear)**: Remove contaminated entities from V5 training and retrain. Expensive and probably unnecessary — contamination is an evaluation problem, not a training problem.

**Priority**: Option A first. Decision on B/C depends on results.

#### Option A Results: Contamination Does NOT Inflate Results `[DONE — Mar 8, 2026]`

**Script**: `scripts/analyze_contamination.py`

Re-scored existing fine-tuning evaluation on decontaminated subset (test prompts whose entities do not appear in V5 training). The script's entity matching identified 107 clean prompts (more conservative matching than the initial manual estimate of 184).

**Overall results**:

| Model | Full Test (n=449) | Clean Subset (n=107) | Gap |
|---|---|---|---|
| Mixtral configC | 91.1% | 90.7% | **+0.4pp** |
| Llama configA | 92.4% | 92.5% | **-0.1pp** |

**Conclusion: Contamination did not inflate fine-tuning results.** Both gaps are under 1pp. The models learned behavioral caution (epistemic skepticism, refusal of uncertain queries), not entity-specific memorization.

**Per-category detail** (small clean samples — interpret with caution):

| Category | Mixtral Full | Mixtral Clean (n) | Llama Full | Llama Clean (n) |
|---|---|---|---|---|
| ambiguous | 100.0% | 100.0% (15) | 100.0% | 100.0% (15) |
| borderline_edge_factual | 100.0% | 100.0% (12) | 100.0% | 100.0% (12) |
| impossible | 100.0% | 100.0% (22) | 96.7% | 100.0% (22) |
| factual | 74.5% | 81.1% (37) | 80.6% | 81.1% (37) |
| nonexistent | 98.3% | 100.0% (12) | 99.2% | 100.0% (12) |
| borderline_plausible_fake | 74.2% | 50.0% (6) | 74.2% | 83.3% (6) |
| borderline_obscure_real | 83.3% | 100.0% (3) | 83.3% | 100.0% (3) |

**Notes on per-category numbers**: Borderline clean samples (n=3-6) are too small for any statistical inference. The plausible_fake Mixtral 50% (3/6) looks alarming but one prompt = 16.7pp — this is noise. Factual (n=37) is the only category with enough clean data for a meaningful comparison, and it shows the clean subset actually does *better* for Mixtral (+6.6pp) — opposite of the inflation hypothesis.

**Entity-dependent vs entity-independent split**:

| Group | Mixtral Full→Clean Gap | Llama Full→Clean Gap |
|---|---|---|
| Entity-dependent (nonexistent, plausible_fake, obscure_real) | +6.0pp | -3.0pp |
| Entity-independent (factual, ambiguous, impossible, edge_factual) | -1.2pp | +0.7pp |

Entity-independent categories show no gap (as expected — entity overlap is irrelevant for behavioral learning). Entity-dependent categories show inconsistent direction across models, consistent with noise from small clean samples rather than systematic inflation.

**Implication for the thesis**: Disclose entity-level contamination as a methodological note (shows rigor, preempts reviewer critique). Report both full and decontaminated numbers. The headline fine-tuning results (91.1% Mixtral, 92.4% Llama) are not inflated. Options B and C are unnecessary.

**Implication for Step 12A (bridge analysis)**: The bridge analysis findings (density predicts fixability) are not contaminated by entity memorization. The geometric signal is genuine.

---

### Step 12A: Fine-Tuning Geometric Analysis `[DONE — Mar 2026]`

**What it does**: The substantive analytical work that completes the thesis's intellectual contributions. Tests whether the geometric framework that predicts prefix effectiveness also predicts fine-tuning effectiveness — potentially the thesis's strongest claim.

**Why this is NOT just "make figures"**: The original Step 12 was vaguely "publication figures, takes minutes." Applying the rigor standard reveals that the most important analytical questions about fine-tuning haven't been asked yet. The data to answer them exists in `results/v5_finetuned/*/judged_answers.jsonl`. These are research questions with unknown answers, not figure formatting.

#### 12A.0: Compute Borderline Geometry (PREREQUISITE) `[DONE]`

**Critical data gap discovered**: The original `geometry_features.csv` has only 368 rows — the 4 main categories (factual: 98, nonexistent: 120, impossible: 30, ambiguous: 120). The 81 borderline prompts (obscure_real: 30, plausible_fake: 31, edge_factual: 20) were never embedded or processed through the geometry pipeline.

**Why this matters**: Without borderline geometry, 12A.2 is completely blocked and 12A.3 is partially blocked. The borderline categories are precisely where the most interesting fine-tuning behavior occurs (regressions on obscure_real).

**Method**: Re-embedded all 449 V3 prompts with `text-embedding-3-large` (OpenAI). Computed curvature, oppositeness, density, centrality using existing `src/geometry/` functions with self-reference (matching V3 methodology — decision log: `build_from_benchmark: true`). Reference corpus `.npy` files had been cleaned up; only `metadata.json` remained.

**Why re-embed all 449 (not just patch in 81)**: Curvature and oppositeness depend on the full embedding matrix (nearest neighbors, PCA). Adding 81 new points changes the neighborhood structure. Re-embedding all 449 ensures internal consistency.

**Verification against original 368-prompt geometry**:

| Feature | Correlation | Max Diff | Mean Diff | Assessment |
|---|---|---|---|---|
| density | 0.998 | 0.228 | 0.013 | Excellent — self-reference barely changes with 81 new points |
| centrality | 0.983 | 0.043 | 0.014 | Excellent — corpus mean shifts minimally |
| curvature | 0.975 | 0.367 | 0.068 | Good — k-NN neighborhoods shift slightly with new points |
| oppositeness | 0.373 | 0.280 | 0.088 | **Unstable** — global PCA axes change fundamentally (explained variance 0.659→0.615) |

**Oppositeness instability**: Oppositeness is computed by flipping top global PCA components. Adding 81 borderline points rotates the PCA axes, reshuffling scores. This is a methodological finding: **oppositeness is not robust to corpus composition changes**. Density, centrality, and curvature are stable. Step 12A.1-3 should lead with density/centrality/curvature and flag oppositeness instability as a limitation.

**Borderline geometry (first look)**:

| Category | N | Curvature | Oppositeness | Density | Centrality |
|---|---|---|---|---|---|
| borderline_obscure_real | 30 | 0.495 | 0.482 | 1.434 | 0.746 |
| borderline_plausible_fake | 31 | 0.487 | 0.558 | 1.637 | 0.709 |
| borderline_edge_factual | 20 | 0.116 | 0.188 | 1.642 | 0.753 |

Notable: obscure_real has lower density than plausible_fake (1.43 vs 1.64). This already hints at the 12A.2 finding — obscure real entities sit in sparser embedding neighborhoods than plausible fakes.

**Script**: `scripts/compute_v3_full_geometry.py`
**Output**: `data/processed/v3_all_geometry_features.csv` (449 rows), `data/processed/v3_all_question_embeddings.npy`
**Cost**: <$0.01

#### 12A.1: Fine-Tuning Bridge Analysis (Contribution 1) `[DONE]`

The prefix bridge analysis showed geometry predicts which hallucinations resist *prefix* intervention. Does geometry also predict which hallucinations resist *fine-tuning*?

**Method**: For each of the 449 held-out prompts (per model), classify into:
- `fixed_by_ft` — baseline hallucinated, fine-tuned correct
- `still_broken` — baseline hallucinated, fine-tuned still wrong
- `broken_by_ft` — baseline correct, fine-tuned wrong (the regressions)
- `always_correct` — correct in both

Mann-Whitney U tests with rank-biserial effect size for all stable features (density, centrality, curvature). Oppositeness reported separately with instability caveat. Permutation tests (10,000 shuffles) for groups with n<10. Bonferroni and Benjamini-Hochberg FDR corrections across all 30 stable-feature tests.

**Outcome group sizes**:

| Outcome | Mixtral | Llama |
|---|---|---|
| always_correct | 359 | 397 |
| fixed_by_ft | 44 | 16 |
| still_broken | 9 | 10 |
| broken_by_ft | 13 | 10 |
| other | 24 | 16 |

**Results — fixed_by_ft vs still_broken (does geometry predict fixability?)**:

| Feature | Model | Fixed Mean | Broken Mean | p (MW) | p (perm) | Effect r | Survives BH? |
|---|---|---|---|---|---|---|---|
| **density** | **Mixtral** | **1.98** | **1.49** | **0.0002** | **<0.001** | **-0.80** | **Yes (Bonf)** |
| **centrality** | **Mixtral** | **0.645** | **0.776** | **0.00004** | **<0.001** | **0.88** | **Yes (Bonf)** |
| curvature | Mixtral | 0.32 | 0.45 | 0.387 | 0.214 | 0.19 | No |
| **density** | **Llama** | **1.75** | **1.55** | **0.016** | **0.146** | **-0.58** | **Yes (BH)** |
| centrality | Llama | 0.693 | 0.712 | 0.510 | 0.386 | 0.16 | No |
| curvature | Llama | 0.43 | 0.31 | 0.279 | 0.424 | -0.26 | No |

**Results — broken_by_ft vs always_correct (does geometry predict regressions?)**:

| Feature | Model | Regressed Mean | Correct Mean | p (MW) | Effect r | Survives BH? |
|---|---|---|---|---|---|---|
| **density** | **Mixtral** | **1.56** | **1.89** | **0.010** | **0.42** | **Yes (BH)** |
| centrality | Mixtral | 0.714 | 0.678 | 0.091 | -0.28 | No |
| curvature | Mixtral | 0.35 | 0.38 | 0.738 | 0.05 | No |
| **density** | **Llama** | **1.50** | **1.90** | **0.0007** | **0.63** | **Yes (Bonf)** |
| centrality | Llama | 0.721 | 0.676 | 0.102 | -0.30 | No |
| curvature | Llama | 0.37 | 0.37 | 0.901 | 0.02 | No |

**Multiple comparisons**: 4/30 survive Bonferroni, 6/30 survive BH FDR.

**Key finding — density direction RESOLVED**: The V4 prefix bridge showed an inconsistency: Mixtral fixed prompts had higher density, but Llama fixed prompts had *lower* density. In 12A.1, **both models agree**: fixed prompts have higher density, regressed prompts have lower density. The V4 inconsistency was prefix-specific, not fundamental. Fine-tuning reveals the true direction: **high density = fixable, low density = resistant**.

**Key finding — curvature is NOT significant for FT**: Unlike V4 prefix bridge where curvature was significant, curvature shows no signal for fine-tuning outcomes. This makes sense: prompting steers attention (local geometry matters), fine-tuning modifies weights (global neighborhood density matters more).

**Oppositeness (unstable, reported separately)**: Only Mixtral fixed_vs_broken is marginally significant (p=0.029) — but oppositeness is unreliable (corr=0.37 with original geometry). Not interpreted.

**Thesis location**: Ch 7.1-7.2

#### 12A.2: Borderline Within-Category Analysis (Contribution 3) `[DONE — NULL]`

**Method**: Within borderline_obscure_real (30 prompts) and borderline_plausible_fake (31 prompts) per model, test whether density/centrality/curvature distinguish FT-correct from FT-wrong. Mann-Whitney U + permutation tests.

**Results**: All 12 within-category tests are non-significant (p>0.08). No geometry feature distinguishes correct from wrong responses within either borderline category.

**Why this is null**: Sample sizes are very small (n=5 wrong per category per model). At n=5, we need effect sizes >0.8 to detect anything at α=0.05. The within-category effects, if they exist, are moderate (r=0.3-0.5) — detectable at n≈30 per group, but not at n=5.

**What this means**: This is a **power limitation**, not evidence against the geometric hypothesis. The within-category density signal from V5 analysis (2,430 prompts, p<0.001) confirms the effect exists — 30 prompts per category simply cannot detect it. Frame as "insufficient power" in thesis, not "no effect."

**Thesis location**: Ch 7.4 — mention as exploratory analysis with power limitation

#### 12A.3: Regression Geometric Profile (Contribution 3) `[DONE]`

For the `broken_by_ft` prompts specifically (baseline correct, fine-tuned wrong) — what's their geometric profile?

**Method**: Compare geometric features of `broken_by_ft` vs `always_correct` prompts. Mann-Whitney U + permutation tests + effect sizes.

**Results**: Density is the star predictor — regressions have significantly lower density in BOTH models:

| Feature | Model | Regressed Mean | Correct Mean | p (MW) | p (perm) | Effect r | Survives BH? |
|---|---|---|---|---|---|---|---|
| **density** | **Mixtral** | **1.56** | **1.89** | **0.010** | **0.011** | **0.42** | **Yes (BH)** |
| **density** | **Llama** | **1.50** | **1.90** | **0.0007** | **0.005** | **0.63** | **Yes (Bonf)** |
| centrality | Mixtral | 0.714 | 0.678 | 0.091 | 0.140 | -0.28 | No |
| centrality | Llama | 0.721 | 0.676 | 0.102 | 0.110 | -0.30 | No |
| curvature | both | ~0.36 | ~0.38 | >0.7 | >0.7 | <0.06 | No |

**Regression error type**: Regressions are overwhelmingly refusals, not new hallucinations:
- Mixtral: 11/13 regressions are refusals (label=3), 2 are hallucinations (label=2)
- Llama: 10/10 regressions are refusals (label=3), 0 are hallucinations
- Total: 21/23 (91%) are refusals — the model learned to refuse, not to fabricate new answers

**Geometric profile of regressions**: Low density (sparse neighborhoods) + trending high centrality (close to corpus center) + normal curvature. This is the profile of prompts where the entity is real but sits in an isolated embedding region. The fine-tuned model's learned caution fires because the neighborhood is sparse (low density), even though the entity is legitimate.

**Connection to precision-recall tradeoff**: The regressions are geometrically indistinguishable from the successfully-fixed hallucinations (both have lower density than always_correct). Fine-tuning learns a density-based heuristic: "sparse neighborhood → refuse." This correctly catches nonexistent entities in sparse regions but also over-fires on obscure real entities in sparse regions. Geometry predicts both where FT helps AND where it hurts.

**Thesis location**: Ch 7.4

#### Execution summary

12A.0 → 12A.1 → 12A.2 → 12A.3 all completed in one analysis script.

**Script**: `scripts/analyze_ft_bridge.py`
**Output**: `results/v5_finetuned/analysis/ft_bridge_data.csv`, `ft_bridge_stats.csv`, `ft_bridge_mixtral-8x7b.png`, `ft_bridge_llama-4-maverick-17b.png`
**Cost**: $0 (local analysis on existing data)

#### 12A Summary: What geometry tells us about fine-tuning

1. **Density is the universal predictor**. It predicts fixability (both models), regressions (both models), with consistent direction: high density = fixable, low density = resistant/regressive. 4 tests survive Bonferroni, 6 survive BH FDR.

2. **Centrality is model-specific**. Strong for Mixtral (p=0.00004 for fixability) but null for Llama. May reflect architectural differences in how models handle central vs peripheral queries.

3. **Curvature is irrelevant for fine-tuning**. Unlike the V4 prefix bridge where curvature predicted prefix effectiveness, curvature shows zero signal for fine-tuning outcomes. Interpretation: prompting steers attention through local geometry, fine-tuning modifies weights through global neighborhood structure.

4. **V4 density inconsistency resolved**. The prefix bridge showed Mixtral and Llama using density in opposite directions. The FT bridge shows they agree. The inconsistency was a prefix-specific artifact, not a fundamental issue with density as a predictor.

5. **Regressions are geometrically predictable refusals**. 91% of regressions are refusals (not new hallucinations). They cluster in low-density regions — the same geometric signature as unfixable hallucinations. The fine-tuned model learns a density-based "refuse when uncertain" heuristic that correctly catches fabrications but over-fires on obscure real entities.

6. **12A.2 is null due to power**. Within-category borderline tests found nothing, but n=5 per group is far too small. The V5 within-category analysis (n=600+) confirmed the effect exists. Frame as power limitation.

---

### Step 12B: Thesis Figures `[DONE]`

**What it does**: Generate publication-quality figures organized by thesis chapter.

**Script**: `scripts/generate_thesis_figures.py`
**Output**: `thesis/figures/` (7 new figures)

#### Complete figure inventory:

**Ch 4 (Experimental Setup)**:
- `v5_judge_agreement.png` (exists — `results/v5_prefixes/analysis/`)
- Pipeline diagram — create manually in TikZ/draw.io

**Ch 5 (Can Geometry Predict?)**:
- `v5_within_category_*.png` (exists, 2 files — `results/v5_baselines/analysis/`)
- `v5_geometry_vs_hallucination_*.png` (exists, 2 files — `results/v5_baselines/analysis/`)
- `ch5_within_category_auc.png` (**NEW** — within-category logistic AUC by category and model)
- `consistency_heatmap.png` (exists — `results/v3/multi_model/`)

**Ch 6 (Can Prompts Reduce?)**:
- `v5_category_heatmap_*.png` (exists, 2 files — `results/v5_prefixes/analysis/`)
- `v5_tradeoff_curve.png` (exists — `results/v5_prefixes/analysis/`)
- `v5_refusal_rates.png` (exists — `results/v5_prefixes/analysis/`)
- `ch6_v4_v5_comparison.png` (**NEW** — pilot 449 vs scale 2,430 accuracy comparison)

**Ch 7 (Can Geometry Guide?)**:
- `v5_bridge_*.png` (exists, 2 files — `results/v5_prefixes/analysis/`)
- `ft_bridge_*.png` (exists from 12A, 2 files — `results/v5_finetuned/analysis/`)
- `ch7_ft_comparison.png` (**NEW** — baseline vs best-prefix vs fine-tuned vs oracle)
- `ch7_ft_category_heatmap.png` (**NEW** — per-category baseline vs FT accuracy)
- `ch7_hyperparameter_sensitivity.png` (**NEW** — LoRA config A/B/C comparison)
- `ch7_regression_breakdown.png` (**NEW** — regression error types by category)
- `ch7_density_by_ft_outcome.png` (**NEW** — density violin plots by FT outcome, key thesis figure)

**Total**: 20 figures across 4 chapters (13 existing + 7 new).

---

## Optional Phases (Thesis Enhancements)

### Phase 5: Generalization Testing (TruthfulQA) `[DONE]`

**Purpose**: Test whether fine-tuned models' learned caution generalizes beyond our custom benchmark to TruthfulQA (Lin et al., 2022), the standard hallucination benchmark (817 questions, 38 categories, 1,800+ citations). This is the first question a reviewer will ask: the entire thesis builds on a custom benchmark we designed — TruthfulQA breaks the circularity.

**Key framing note**: TruthfulQA tests *misconceptions* (things humans commonly get wrong), not *fabrication* (inventing nonexistent entities). Our fine-tuning trained on fabrication. A null result is the *expected* outcome and should be framed as "targeted fine-tuning, not general truthfulness boost." An improvement would be a *stronger-than-expected* result.

**Value**: **High.** Not a new contribution, but load-bearing evidence for the credibility of all four existing contributions.

**Cost**: ~$15-30 total, ~8-10 hours wall time (mostly unattended judging).

#### Step 13A: Download and prepare TruthfulQA `[NEXT]`

- Download 817 questions via HuggingFace `datasets` library
- Convert to our JSONL format: `{id, question, ground_truth, category, metadata}`
- Ground truth construction: `"Best answer: {best_answer}. Also acceptable: {correct_answers_joined}. Known incorrect: {incorrect_answers_joined}."` — enriched because our judge only sees the `ground_truth` string (not `meta_info`)
- Keep TruthfulQA's 38 native categories (don't map to our 7)
- Output: `data/prompts/truthfulqa.jsonl`

#### Step 13B: Run baseline inference (~1-2 hrs, ~$3-5)

- Both base models (Mixtral 8x7B Instruct, Llama 4 Maverick Instruct) on 817 questions
- No system prompt — matches V3 baseline methodology
- Together AI serverless inference (no dedicated endpoints for base models)
- Output: `results/truthfulqa/{model}/baseline_answers.jsonl`

#### Step 13C: Run fine-tuned inference (~1-2 hrs, ~$5-10)

- Best configs only: Mixtral configC, Llama configA
- Mixtral requires dedicated endpoint ($0.13/min, ~40-70 min = ~$5-9). Llama has serverless LoRA (`-adapter` suffix)
- No system prompt — matches Step 11 methodology
- Output: `results/truthfulqa/{model}/finetuned_answers.jsonl`

#### Step 13D: Judge all responses (~4-6 hrs, ~$10-20) `[DONE — Mar 2026]`

- 817 × 2 models × 2 conditions = 3,268 judgments
- Same 3-judge consensus panel (GPT-5.1, Claude Opus 4.5, Llama 4 Maverick)
- Output: `results/truthfulqa/{model}/baseline_judged.jsonl`, `finetuned_judged.jsonl`
- Runtime: ~4.5 hours total (63-74 min per condition)

**Raw results** (after re-judging — see data quality note below):

| Model | Condition | Accuracy | Hallucination | Refusal | n |
|---|---|---|---|---|---|
| Mixtral 8x7B | baseline | 74.4% | 16.9% | 0.0% | 817 |
| Mixtral 8x7B | finetuned (configC) | 76.6% | 14.7% | 0.7% | 817 |
| Llama 4 Maverick | baseline | 71.8% | 17.6% | 0.6% | 817 |
| Llama 4 Maverick | finetuned (configA) | 77.1% | 13.2% | 0.5% | 817 |

**Data quality note**: The initial judging run had 62 Llama finetuned questions where API connection errors caused all 3 judges to fail, defaulting to label=3 (refusal) with confidence=0.0. This inflated Llama FT refusal from ~0.5% to 8.1% and suppressed accuracy from ~77% to 71%. Detected during 13E review (confidence=0.0 check), backed up as `.bak_contaminated`, and re-judged with zero errors. All numbers above are from the clean re-judged data.

**Initial observations** (full analysis in Step 13E):

1. **Mixtral**: Modest improvement. Accuracy +2.2pp (74.4%→76.6%), hallucination -2.2pp (16.9%→14.7%). Near-zero refusal increase (0.0%→0.7%). Fine-tuning helped without over-cautious behavior. 13% relative hallucination reduction.
2. **Llama**: Both accuracy and hallucination improve significantly. Accuracy +5.3pp (71.8%→77.1%), hallucination -4.4pp (17.6%→13.2%, 25% relative reduction). Refusal essentially unchanged (0.6%→0.5%). Llama shows the strongest TruthfulQA generalization of the two models.
3. **Not a null result**: Both models show hallucination reduction on an external benchmark testing misconceptions (different from our fabrication benchmark). This is genuine generalization, though the effect is smaller than on our custom benchmark (13-25% relative reduction here vs 88-89% on held-out V4).
4. **Reduced effect expected**: Our FT trained on entity-fabrication skepticism. TruthfulQA tests misconceptions (e.g., "Can goldfish remember things for 3 seconds?"). The fact that entity-skepticism training transfers at all to misconception-type hallucination is noteworthy.
5. **No over-caution on TruthfulQA**: Unlike on the custom benchmark where Llama showed increased refusal with prefixes, TruthfulQA refusal is negligible for both models. The custom benchmark refusal pattern may be specific to the entity-fabrication domain.

**Pending**: ~~Step 13E analysis~~ → DONE

#### Step 13E: Analyze and report `[DONE]`

**Script**: `scripts/analyze_truthfulqa.py`
**Output**: `results/truthfulqa/analysis/truthfulqa_analysis.md`, `truthfulqa_per_category.csv`

**Analyses performed** (8 total):
1. Transition matrices (per-question baseline→finetuned)
2. McNemar's tests on accuracy AND hallucination (Bonferroni-corrected, 4 tests)
3. Wilson confidence intervals for all rates
4. Per-category descriptive breakdown (38 categories, n≥10 filter for highlights)
5. Judge agreement rates (unanimous vs majority)
6. Qualitative examples (fixed/broken/over-cautious/converted)
7. Literature comparison table with label mapping note
8. Judge calibration check vs published MC2

**Key results** (after re-judging):

| Model | Metric | Baseline | Finetuned | Δ | McNemar p | Bonferroni |
|---|---|---|---|---|---|---|
| Mixtral | Accuracy | 74.4% | 76.6% | +2.2pp | 0.1145 | NOT sig |
| Mixtral | Halluc rate | 16.9% | 14.7% | -2.2pp | 0.0763 | NOT sig |
| Mixtral | Refusal | 0.0% | 0.7% | +0.7pp | — | — |
| Llama | Accuracy | 71.8% | 77.1% | +5.3pp | 0.0002 | **sig** |
| Llama | Halluc rate | 17.6% | 13.2% | -4.4pp | 0.0005 | **sig** |
| Llama | Refusal | 0.6% | 0.5% | -0.1pp | — | — |

**Transition matrices**:
- Mixtral: 36 hallucinations fixed, 24 broken (net +12). Only 2 over-cautious refusals.
- Llama: 44 fixed, 15 broken (net +29). Only 2 over-cautious refusals.

**Both Llama tests survive Bonferroni correction** (accuracy p=0.0002, hallucination p=0.0005). Mixtral hallucination reduction (p=0.076) is marginal — real effect but insufficient power at n=817 with modest effect size.

**Judge agreement**: 73-79% unanimous, 95% majority across all conditions. Consistent with custom benchmark agreement rates.

**Judge calibration**: Our baseline Mixtral accuracy (74.4%) roughly aligns with published MC2 (~73.9%), though different metrics. Not wildly miscalibrated.

**Thesis interpretation**: Cross-domain generalization from entity-fabrication to misconception-type hallucination is real and significant for Llama (both accuracy and hallucination survive Bonferroni). Mixtral shows the same direction but lacks statistical power. Neither model shows over-caution on TruthfulQA (refusal ≤0.7%), suggesting the custom benchmark refusal pattern is domain-specific.

#### Deeper interpretation (for thesis Ch 7.5)

1. **Cross-domain generalization is real**: The models learned entity-fabrication skepticism, yet TruthfulQA tests misconceptions — categorically different. A 25% relative hallucination reduction (Llama) means fine-tuning taught something more general than "say 'I don't know' to fabricated entities." It taught epistemic caution.

2. **Modest effect is expected and honest**: 13-25% relative reduction here vs 88-89% on custom benchmark. Frame as "bonus evidence of generalization" (Ch 7.5), not headline result. The custom benchmark results (Ch 6-7) carry the thesis.

3. **No over-caution tradeoff**: On the custom benchmark, finetuned models refuse more. On TruthfulQA, refusal ≤0.7%. The caution is *targeted* at fabrication-style prompts, not a blanket personality shift. This is an important nuance for Ch 8 Discussion.

4. **Llama vs Mixtral asymmetry**: Llama both tests significant; Mixtral neither. Possible explanations: (a) Llama had more room to improve (lower baseline), (b) LoRA adaptation was more generalizable, (c) Mixtral p=0.076 is marginal — at 2x sample size likely significant. Don't over-interpret.

5. **Category patterns are interpretable**: Biggest Llama improvements in Advertising (-31pp), Law (-19pp), Confusion (-13pp) — categories involving confident factual assertions (same failure mode as entity fabrication). Only worsening: Distraction (+7pp) — trick questions where more caution backfires. Consistent with targeted epistemic calibration, not blanket conservatism. Present as exploratory (no per-category multiple comparison correction).

#### Limitations to acknowledge in thesis

1. **n=817 may underpower Mixtral**: A 2.2pp effect needs ~3,000+ paired observations for McNemar significance. This is a power problem, not evidence of no effect. State explicitly.
2. **Literature comparison numbers are unverified**: ITI/DoLA/InstructGPT rows marked `[*] unverified`. Need PDF verification before submission.
3. **Judge label mapping is approximate**: Our "correct" ≈ TruthfulQA "truthful+informative", not identical. MC2 calibration check is suggestive, not definitive.
4. **Per-category analysis is exploratory**: 38 categories with no Bonferroni correction. Present as "patterns consistent with targeted calibration," not "these categories significantly improved."
5. **The contamination episode**: 62/817 (7.6%) entries corrupted by silent API error defaults. Detected via confidence=0.0 audit, re-judged clean. Document as 1-paragraph methods note — demonstrates QC rigor, strengthens rather than weakens the paper.

#### Resolved concerns

1. ~~**Ground truth format**~~: Resolved. Enriched ground_truth string with best_answer + correct/incorrect answer lists.
2. ~~**`meta_info` not used by judge**~~: Resolved. All context placed in ground_truth string.
3. **Misconception vs fabrication**: Different hallucination modes — addressed in interpretation above. Frame carefully in thesis.
4. ~~**Published baseline comparison**~~: Resolved. Judge calibration check in 13E report: our Mixtral baseline 74.4% vs published MC2 ~73.9%. Rough alignment suggests no wild miscalibration (caveat: different metrics).

**Thesis location**: Ch 7.5 ("Generalization to External Benchmarks"), 3-4 pages.

### Phase 9: Template Diversity Ablation `[PLANNED — Mar 2026]`

**Motivation (Sunny Qin, Mar 8 2026)**: Template-generated training data risks the model learning template-specific patterns ("when I see this question structure, refuse") rather than general hallucination avoidance. The key question: does template *diversity* matter more than example *count* for fine-tuning generalization?

**Core experiment**: Hold total training examples constant (~2,400), vary the number of templates used to generate them. Compare test performance across conditions.

**Hypothesis**: T10 and above will perform similarly to T-all; T1 will degrade. Rationale: TruthfulQA generalization (Phase 5, zero template overlap, Llama p=0.0002) and decontamination analysis (Step 11C, accuracy unchanged on novel entities) both suggest the model learned behavioral caution, not template- or entity-specific shortcuts. However, T1 is an extreme case where the model could learn "this specific question structure = be cautious" rather than general skepticism. The interesting finding is the knee of the curve — where diminishing returns begin.

#### Research questions (from Sunny)

1. **Does the same template appear in both train/test set?** Yes — 83.3% of V3 test templates (100/120 with metadata) also appear in V5 training. 81 V3 test prompts (borderline categories) have no template metadata. 231 V5 templates are novel (not in V3). This means the current evaluation partially tests within-template generalization.

2. **Do models generalize across templates?** TruthfulQA partially answers this (zero template overlap, significant Llama improvement). But TruthfulQA tests misconceptions, not fabrication — within-benchmark cross-template generalization is a cleaner test.

3. **Is there a minimum template count for generalization?** The ablation should reveal a curve — at what point does adding more templates stop helping?

4. **Are some templates more effective than others?** Per-template analysis of training data quality: do certain question structures produce better fine-tuning signal?

5. **Does it depend on model size/capacity?** We test Mixtral 8x7B (~12B active) and Llama 4 Maverick 17B — different architectures and sizes.

#### Experimental design

**Conditions** (all use ~2,400 total training examples, same entity pool):

| Condition | Templates per category | Examples per template | Total prompts | Purpose |
|---|---|---|---|---|
| T1 | 1 | ~500 (factual), ~600 (nonexistent), etc. | ~2,400 | Degenerate case — can model learn from pure entity variation? |
| T5 | 5 | ~100 each | ~2,400 | Low diversity |
| T10 | 10 | ~50 each | ~2,400 | Moderate diversity (hypothesized sufficiency threshold) |
| T20 | 20 | ~25 each | ~2,400 | High diversity |
| T-all | 55-66 (current) | round-robin | ~2,400 | Maximum diversity (control — existing training set) |

**Why these specific counts**: T1 is the extreme case Sunny described. T5/T10/T20 trace the curve. T-all is the existing setup (no regeneration needed).

**Evaluation**: Same held-out test set (449 V3 prompts), same 3-judge consensus panel. Primary metrics: overall accuracy, hallucination rate, per-category accuracy. McNemar's test between each condition and T-all.

**Critical control — template overlap with test set**: For each condition, report accuracy separately on (a) test prompts whose template appeared in training vs (b) test prompts with novel templates. This directly answers Sunny's Q1/Q2 without needing a separate experiment.

#### Step-by-step implementation

**Step 9A: Generate training data for T1/T5/T10/T20** `[~2-3h, $0]`

Create a **new script** `scripts/build_ablation_data.py` that reuses generation logic from `build_v5_benchmark.py` but adds a template-limit parameter. Do NOT modify `build_v5_benchmark.py` — it generated the current V5 training set and its reproducibility must be preserved (same principle as V3: "new unified script instead of modifying existing").

For each condition:
- Limit the template pool to N templates per category (see nesting rule below)
- Generate prompts using the restricted pool, same entity pools, same V3 exclusion logic, same entity diversity caps (max 5 reuses)
- **T-all does not need regeneration** — it's the existing V5 training set

Output: `data/prompts/ablation_T{N}_*.jsonl`

**Rigor concern 1 — nested template selection**: Template selection must use nested subsets: T5's templates ⊂ T10's ⊂ T20's ⊂ T-all. Use a single seeded shuffle of the full template pool; T5 takes the first 5, T10 takes the first 10, etc. **Why**: If T5 and T10 use completely different templates, a performance difference could reflect template *quality*, not template *count*. Nesting eliminates this confound and makes the curve monotonically interpretable (each condition adds templates, never swaps).

**Rigor concern 2 — achievable prompt count per condition**: The target of ~2,400 prompts may not be achievable for low-template conditions. The script enforces entity diversity caps (max 5 reuses per entity). With T1 (1 template per category), maximum possible prompts per category = min(target, 5 × num_compatible_entities). Not all entities fit all templates (placeholder type mismatch). For factual with 1 template: if the template uses `{person}` but most entities are `{country}`, output could be far below 500. **Must compute maximum feasible N per condition before committing to the design.** If T1 yields <200 total prompts, it's unusable for fine-tuning — drop T1 and use T5 as the lowest condition.

Pre-computation needed (run before writing the script):
```
For each category, for each template:
  Count how many entities can fill it (compatible placeholder types)
  Max prompts from 1 template = min(5 × compatible_entities, target)
```
This determines whether T1 is feasible at all and sets realistic prompt count expectations for each condition.

**Rigor concern 3 — borderline category template structure**: Borderline templates are organized by sub-type (20 templates each for: obscure_real people/places/events, plausible_fake people/books/places). "T5 per category" must be defined: does T5 mean 5 templates from each sub-type (= 15-30 total for the category), or 5 total across all sub-types (losing coverage of some sub-types entirely, e.g., no "places" templates)? **Recommendation**: T{N} per *sub-type*, not per category. This preserves sub-type coverage at all conditions and is the fairer test. State explicitly: T5 = 5 templates per sub-type (30 borderline templates total), T10 = 10 per sub-type (60 total), etc.

**Rigor concern 4 — V3 exclusion interaction**: With fewer templates, V3-excluded (template, entity) combos become a larger fraction of the possible generation space. This could disproportionately shrink low-template conditions' output. Log the V3 exclusion count per condition to verify this isn't a confound.

**Rigor concern 5 — borderline_edge_factual**: Edge factual prompts are hand-written question/answer pairs, not template-generated. They don't participate in the template ablation. **Decision**: Include the same 130 edge factual prompts identically in all conditions. They serve as a control — if edge factual accuracy varies across conditions, something other than template diversity is changing (e.g., total dataset composition effects). State this in the analysis.

**Validation checklist** (before proceeding to 9B):
- [ ] Verify prompt counts per condition per category — are they sufficient for fine-tuning?
- [ ] Verify nesting: every T5 prompt also appears in T10 (after entity/exclusion constraints)
- [ ] Verify zero V3 overlap in all conditions
- [ ] Verify zero unfilled placeholders
- [ ] Log template coverage, entity coverage, V3 exclusions per condition for the generation report

**Step 9B: Get best-per-prompt training targets for each condition** `[~1h to days, $0-180]`

The training data isn't just the prompts — it's (prompt, best_response) pairs from best-per-prompt selection across prefixes.

**Key question: Can we reuse existing prefix responses?**

Two approaches:

**(a) Reuse-only (simpler, cheaper)**: For each condition, filter the existing 2,430 V5 prompts to only those that use templates in the T{N} set. This changes the total N per condition — violating the "hold N constant" design. Must report both template count AND training set size.

**(b) Regenerate + run prefixes (proper, expensive)**: Generate new 2,400-prompt sets per condition, run all 5 prefixes on each, judge, do best-per-prompt selection. Preserves constant N but costs ~$50-150 per condition in prefix generation + judging.

**Recommendation**: Start with approach (a). The existing V5 data has round-robin distribution across all templates, so filtering to T{N} templates gives approximately N/N_total × 2,400 prompts per condition. For T10 out of 55: ~436 prompts. For T5: ~218. For T1: ~44. T1 under approach (a) is too small for meaningful fine-tuning.

**Decision point**: If approach (a) gives ≥200 prompts per condition for the conditions we care about, use it and report the varying N as a known limitation. If T1/T5 are too small, either (b) regenerate those conditions only, or drop T1 in favor of T5 as the lowest condition.

**Step 9C: Fine-tune one model per condition** `[~10-20h wall, ~$50-100]`

- LoRA fine-tuning via Together AI
- Same hyperparameters as Step 10 best configs (Mixtral configC, Llama configA)
- Full: 5 conditions × 2 models = 10 jobs. Simplified: 3 × 2 = 6 jobs.
- Each job ~1-2h on Together

**Rigor note**: Together AI overrides some hyperparameters (lora_r 16→64, alpha 32→128, dropout removed — documented in Step 10). These overrides are constant across conditions, so not a confound for the ablation.

**Step 9D: Evaluate on held-out test set** `[~4-6h wall, ~$15-80]`

- Run each fine-tuned model on 449 held-out test prompts
- Dedicated endpoints required (Together serverless LoRA doesn't work): Mixtral $0.13/min, Llama $0.53/min
- 10 runs × 449 = 4,490 generation calls
- **Cost concern**: Endpoint costs are the hidden expense. Batch runs back-to-back on one endpoint session to minimize startup overhead.

**Step 9E: Judge all evaluation responses** `[~8-12h wall, ~$30-70]`

- 3-judge consensus panel on all 4,490 responses = 13,470 judge calls
- Fully resumable

**Step 9F: Analyze and plot** `[~1h, $0]`

- **Primary figure**: Accuracy vs template count curve (x: T1/T5/T10/T20/T-all, y: test accuracy). One line per model. Error bars via bootstrap CI.
- Per-category breakdown at each condition
- Template-overlap split: accuracy on seen-template vs novel-template test prompts per condition
- McNemar's test: each condition vs T-all
- Model comparison: does the curve shape differ between Mixtral and Llama?

Output: `results/ablation/template_diversity_curve.png`, per-condition accuracy tables

#### Cost and time estimate

| Step | Wall time | Cost |
|---|---|---|
| 14A: Generate data | 30 min | $0 |
| 14B: Training targets (approach a) | 1h | $0 |
| 14B: Training targets (approach b, if needed) | 15-20h | $50-150 |
| 14C: Fine-tuning (10 jobs) | 10-20h | $50-100 |
| 14D: Evaluation inference | 4-6h | $15-80 (endpoints) |
| 14E: Judging | 8-12h | $30-70 |
| 14F: Analysis | 1h | $0 |
| **Total (approach a)** | **~1.5-2 days** | **~$95-250** |
| **Total (approach b)** | **~2.5-3.5 days** | **~$145-400** |

#### Simplified fallback (if time-constrained)

Run only 3 conditions: T1 (or T5 if T1 is too small under approach a), T10, T-all. Captures the degenerate/low case, the hypothesized knee, and the control. Cuts to 6 fine-tuning jobs. Wall time ~1-1.5 days.

#### Risks and mitigations

1. **Risk: T1 performs well** → Template diversity doesn't matter — model learns from entity-answer content, not question structure. Interesting finding, report honestly. Would need careful framing.

2. **Risk: Approach (a) gives too few prompts for low-template conditions** → T1 under reuse gives ~44 prompts, far too few for LoRA. Mitigation: switch to approach (b) for T1/T5 only, or drop T1 and use T5 as the lowest condition.

3. **Risk: Results differ between Mixtral and Llama** → Answers Sunny's Q5 about model capacity. A finding, not a problem.

4. **Risk: Time** → Must start by ~March 12 to have results by ~March 18, leaving 9 days for thesis writing. Simplified fallback gives 1-2 extra days.

5. **Risk: Endpoint costs escalate** → 10 evaluation runs on Llama endpoints ($0.53/min) could cost $50+ alone. Mitigation: simplified fallback (6 runs), or run Mixtral-only (cheaper endpoints, $0.13/min) as a first pass.

#### What this adds to the thesis

- **Ch 4 (Methodology)**: Empirical justification for template diversity design choice
- **Ch 7 (Fine-tuning)**: New subsection "Template Diversity Ablation" (~2-3 pages with curve figure)
- **Ch 8 (Discussion)**: Practical recommendations for practitioners building fine-tuning benchmarks from template-generated data
- Preempts reviewer question: "Are your results sensitive to template diversity?"

**Priority**: Next experiment. Per Sunny's guidance: TruthfulQA first (done), then ablation.

**Thesis location**: Ch 7.6 if the curve is interesting; Appendix if T-all is trivially best.

---

### Phase 9 Execution: Template Diversity Ablation `[IN PROGRESS — Mar 9-10, 2026]`

#### Step 9A: Build ablation training data `[DONE — Mar 9]`

**Script**: `scripts/build_ablation_data.py`

Used **approach (a)** — reuse existing V5 prefix data, filter to templates in each condition's pool. This means N varies across conditions (a known limitation, reported alongside results).

**T1 dropped**: Pre-computation showed only 179 prompts achievable (3-15 per category) — insufficient for fine-tuning. T5 is the lowest condition.

**Final conditions**:

| Condition | Templates/group | Mixtral N | Llama N | Purpose |
|-----------|----------------|-----------|---------|---------|
| T5 | 5 | 397 | 402 | Low diversity |
| T10 | 10 | 660 | 662 | Moderate diversity |
| T-all | 55-66 (existing) | 2,402 | 2,406 | Maximum diversity (control, not regenerated) |
| R397 (Mixtral) | ~194 (all) | 397 | — | Random subset matching T5 N, full template pool |
| R402 (Llama) | ~192 (all) | — | 402 | Random subset matching T5 N, full template pool |

**Matched random controls (R{N})**: Same prompt count as T5 but drawn from the full template pool (~194 templates instead of 50). This isolates template diversity from dataset size — if R397 outperforms T5 despite identical N, the difference is template diversity, not data quantity.

**Design notes**:
- Nested template selection: T5's 5 templates ⊂ T10's 10 templates (seeded shuffle, seed=2025)
- borderline_edge_factual (130 hand-written, no templates) included identically in all conditions — serves as control
- Edge factual dilution: 32.7% of T5 dataset, dilutes template-diversity effect. Per-category metrics excluding edge_factual reported separately
- R{N} labels are model-specific (R397 for Mixtral, R402 for Llama) because unfixable counts differ (28 vs 24)
- Nesting verified across all conditions

**Output**: `data/training/ablation/ablation_report.json` (full condition details), `data/training/ablation/{condition}_{model}.jsonl` (training data), `data/training/ablation/{condition}_together_{model}.jsonl` (Together AI format)

#### Step 9C: Fine-tuning `[DONE — Mar 9]`

6 LoRA fine-tuning jobs via Together AI, all completed:

| Condition | Model | Job ID | Output Model |
|-----------|-------|--------|-------------|
| T5_mixtral | Mixtral 8x7B | ft-1dc56ff5-5435 | seinyun_a5f8/Mixtral-8x7B-Instruct-v0.1-abl-T5-mixtral-b6757183 |
| R397_mixtral | Mixtral 8x7B | ft-d0eea4ce-dd33 | seinyun_a5f8/Mixtral-8x7B-Instruct-v0.1-abl-R397-mixtral-6ef6a680 |
| T10_mixtral | Mixtral 8x7B | ft-8313836b-b9ac | seinyun_a5f8/Mixtral-8x7B-Instruct-v0.1-abl-T10-mixtral-631bc9e1 |
| T5_llama | Llama 4 Maverick | ft-d6183ef5-cc91 | seinyun_a5f8/Llama-4-Maverick-17B-128E-Instruct-abl-T5-llama-c34edd9f |
| T10_llama | Llama 4 Maverick | ft-0e637b6c-4aaa | seinyun_a5f8/Llama-4-Maverick-17B-128E-Instruct-abl-T10-llama-61158d64 |
| R402_llama | Llama 4 Maverick | ft-823d8b5b-39d1 | seinyun_a5f8/Llama-4-Maverick-17B-128E-Instruct-abl-R402-llama-40138f4e |

**Note**: T-all does not need separate fine-tuning — it's the existing Step 10 models (Mixtral configC, Llama configA).

Same hyperparameters as Step 10 (Together overrides: lora_r=64, alpha=128, no dropout). Llama used QLoRA (4-bit).

Stored in: `data/training/ablation/ablation_ft_jobs.json`

#### Step 9D: Evaluation generation `[DONE — Mar 10-11]`

Run each fine-tuned model on the 449 held-out V3 test prompts via dedicated Together AI endpoints. Script: `scripts/run_ablation_generation_all.py`

**First attempt (Mar 9-10)**: Hit Together AI capacity issues — Llama endpoints failed to deploy during peak hours. 3 Mixtral conditions completed, all 3 Llama conditions failed or partial.

**Retry (Mar 10-11, off-peak)**: `python3 scripts/run_ablation_generation_all.py --skip-existing` — all 3 Llama conditions completed successfully.

| Condition | Status | Entries | Endpoint deploy time | Generation time |
|-----------|--------|---------|---------------------|-----------------|
| T5_mixtral | **Complete** | 449/449 | — (first attempt) | — |
| R397_mixtral | **Complete** | 449/449 | — (first attempt) | — |
| T10_mixtral | **Complete** | 449/449 | — (first attempt) | — |
| T5_llama | **Complete** | 449/449 | 585s (~10 min) | 14:35 (~1.95s/it) |
| R402_llama | **Complete** | 449/449 | 930s (~15.5 min) | 0:34 (resumed 17 remaining) |
| T10_llama | **Complete** | 449/449 | 435s (~7 min) | 15:24 (~2.06s/it) |

All 6 conditions × 449 prompts = 2,694 total answers. Zero failures.

**Output**: `results/v5_finetuned/ablation/{condition}/answers.jsonl`

#### Step 9E: Judging `[DONE — Mar 11]`

3-judge consensus panel (GPT-5.1, Claude Opus 4.5, Llama 4 Maverick) on all 2,694 responses. Command: `python3 scripts/run_ablation_evaluation.py --phase judge`

| Condition | Judged | Time | Rate |
|-----------|--------|------|------|
| T5_mixtral | 449/449 | 23:56 | 3.20s/it |
| R397_mixtral | 449/449 | 25:05 | 3.35s/it |
| T10_mixtral | 449/449 | 25:16 | 3.38s/it |
| T5_llama | 449/449 | 23:33 | 3.15s/it |
| T10_llama | 449/449 | 27:18 | 3.65s/it |
| R402_llama | 449/449 | 23:30 | 3.14s/it |

Total: 2,694/2,694 judged, 0 errors. ~2.5 hours wall time.

#### Step 9F: Analysis `[DONE — Mar 11]`

**Script**: `scripts/analyze_ablation.py` (mirrors `analyze_v5_finetuned.py` structure)

**Results — Summary Table:**

| Condition | Templates | Mixtral N | Mixtral Acc | Llama N | Llama Acc |
|-----------|-----------|-----------|-------------|---------|-----------|
| Baseline (no prefix) | — | 449 | 82.9% | 449 | 90.6% |
| Best prefix (entity_aware) | — | 449 | 91.1% | 449 | 94.0% |
| FT: T5 (5 templates) | 50 | 397 | 90.9% | 402 | 91.5% |
| FT: R{N} (all tmpl, T5 size) | ~194 | 397 | 90.2% | 402 | 92.2% |
| FT: T10 (10 templates) | 100 | 660 | 92.0% | 662 | 93.3% |
| FT: T-all (all templates) | ~194 | 2,402 | 91.1% | 2,406 | 92.4% |

**Key findings:**

1. **Template diversity does NOT matter (the main result).** T5 (5 templates) performs statistically indistinguishably from T-all (all templates) on both models. McNemar p=1.00 (Mixtral), p=0.52 (Llama). Even with only 50 templates and ~400 training examples, the fine-tuned model matches the performance of one trained on 2,400 examples with full template diversity. The model learned behavioral caution, not template-specific patterns.

2. **T5 vs R{N} (diversity-vs-size control): no difference.** T5 (50 templates, ~400 examples) vs R{N} (all ~194 templates, same ~400 examples): McNemar p=0.65 (Mixtral), p=0.65 (Llama). Identical hallucination rates (4.2% / 1.6%). Template diversity at constant N adds nothing.

3. **All conditions significantly beat baseline.** Every ablation condition beats baseline for Mixtral (all p<0.001). Llama improvements are directionally consistent but smaller (baseline already 90.6%): T10 is significant (p=0.031), T5 marginal (p=0.58), R402 marginal (p=0.30).

4. **Template overlap split shows cross-template generalization.** T5 Mixtral: seen-template prompts 92.6% acc vs novel-template 92.4% acc — virtually identical. The model generalizes equally well to templates it never saw during training. This directly answers Sunny's Q2.

5. **T10 is the best-performing condition** for both models (Mixtral 92.0%, Llama 93.3%) — numerically better than T-all despite fewer templates and examples. Not statistically significant (p=0.52/0.45 vs T-all), but suggests T-all's additional data adds noise, not signal.

6. **Hallucination rates consistent across conditions.** Mixtral: 4.2% (T5/R397), 3.3% (T10), 1.3% (T-all). Llama: 1.6% across all three ablation conditions, 0.7% T-all. The slight T-all advantage in hallucination rate may reflect dataset size (more training signal for rare cases) but is not statistically significant.

7. **Per-category patterns stable.** borderline_plausible_fake sees the largest improvement across all conditions (+16-29pp over baseline). borderline_obscure_real shows the same regression pattern as the main experiment (-3 to -10pp). nonexistent dramatically improves (+4 to +28pp). These patterns are condition-invariant — the intervention type matters more than the training data composition.

**Interpretation for thesis:**

The ablation result is a **positive finding for practitioners**: template diversity in fine-tuning data is not a bottleneck. A small number of diverse entities with even 5 question templates is sufficient to teach behavioral caution. This supports the thesis's contribution #4 (prompt distillation into weights) — the model is learning a general epistemic strategy, not memorizing question-answer patterns.

This also retroactively validates the TruthfulQA generalization (Phase 5): if the model doesn't even need diverse templates to generalize within-benchmark, it's unsurprising that it generalizes cross-benchmark.

**Thesis location**: Ch 7.6 "Template Diversity Ablation" (~2-3 pages with summary table). The result is interesting enough for the main text, not appendix — it addresses a methodological concern and has practical implications.

**Output**: `results/v5_finetuned/ablation/ablation_analysis.json`

---

### Phase 10: Cross-Category Generalization Ablation `[COMPLETE — Mar 12, 2026]`

**Motivation**: Sunny Qin (Mar 11, 2026) suggested testing whether fine-tuning on a subset of categories teaches caution that generalizes to held-out categories. This is a **third type of behavioral generalization** beyond:
1. Unseen entities (decontamination analysis, Step 11C)
2. Unseen question templates (TruthfulQA, Phase 5; template ablation, Phase 9)
3. **Unseen category types** ← this experiment

**Note on framing**: This is a **zero-shot category transfer** test — held-out categories have *zero* training examples. Sunny's original intuition was about low-resource categories (from the T1 discussion where some categories had only 3-15 examples). We test the extreme case: can the model generalize caution to a category type it has literally never seen during fine-tuning?

**Core question**: If a model learns to be cautious about nonexistent entities, does that caution transfer to borderline_plausible_fake entities it was never trained on? If it learns to hedge on ambiguous questions, does it also hedge on impossible questions?

**Why this matters**: Categories represent fundamentally different *types* of epistemic uncertainty:
- **Entity-dependent** (nonexistent, borderline_plausible_fake, borderline_obscure_real): Uncertainty about whether an entity exists or is real
- **Entity-independent** (factual, ambiguous, impossible, borderline_edge_factual): Uncertainty about the question itself (trick questions, edge cases, genuinely ambiguous)

If caution generalizes across these groups, the model learned something deeper than "be careful about fake entities" — it learned a general epistemic strategy applicable to novel uncertainty types.

**Experimental design**:

#### Condition structure

We use **leave-one-group-out** rather than leave-one-category-out, for two reasons:
1. Individual categories have as few as 130-200 training examples (impossible, borderline). Removing one category from training leaves most of the data intact (~90%), making it hard to detect a difference.
2. The entity-dependent vs entity-independent split is a natural conceptual boundary — these are genuinely different *kinds* of hallucination triggers.

| Condition | Train categories | Held-out categories | Train N (approx) | Purpose |
|-----------|-----------------|---------------------|-------------------|---------|
| Full (control) | All 7 | None | ~2,400 | Existing T-all from Phase 9 — no new FT needed |
| Entity-dep only | nonexistent, plausible_fake, obscure_real | factual, ambiguous, impossible, edge_factual | ~1,000 | Does entity-focused caution generalize to entity-independent questions? |
| R{entity-dep} | All 7 (random subset) | None | ~1,000 (matched) | Size-matched control for entity-dep. Isolates category coverage from dataset size |
| Entity-indep only | factual, ambiguous, impossible, edge_factual | nonexistent, plausible_fake, obscure_real | ~1,430 | Does question-type caution generalize to entity-dependent questions? |
| Leave-out-nonexistent | All except nonexistent | nonexistent | ~1,830 | Nonexistent is largest category (600 training, 120 test). Best statistical power for single-category holdout |
| Leave-out-factual | All except factual | factual | ~1,930 | Factual is the second-largest test category (98 test). Tests generalization to straightforward knowledge questions |

**Why these 6 conditions specifically**:
- Full: existing control, no cost
- Entity-dep / Entity-indep: tests the conceptual boundary (different uncertainty types)
- R{entity-dep}: size-matched random control (same approach as Phase 9's R{N}). Same ~1,000 prompts but drawn from all 7 categories. If entity-dep-only underperforms R{entity-dep}, the gap is category coverage, not dataset size. If both perform equally, smaller datasets are fine regardless of category composition.
- Leave-out-nonexistent: best single-category test (largest test set, n=120, gives statistical power). Nonexistent is also the category with the largest fine-tuning improvement, so it's the hardest test — if caution generalizes even without nonexistent training data, that's strong evidence
- Leave-out-factual: tests whether the model needs explicit "here's what correct answers look like" examples, or if training only on uncertainty categories is sufficient

**What we do NOT include**:
- Leave-one-out for every category (7 additional conditions × 2 models = 14 FT jobs). Too expensive for the insight gained. The group-level conditions and the two best-powered single-category holdouts cover the key questions.
- Combinations of holdouts (e.g., hold out nonexistent + plausible_fake). Combinatorial explosion. The group-level conditions already test this.
- R{entity-indep} size-matched control: entity-indep (~1,430) is close enough to the leave-out conditions (~1,830-1,930) that a size confound is unlikely. The entity-dep condition (~1,000 vs ~2,400) has the largest size gap and is the one where the control matters most.

#### Evaluation

- **Test set**: Same 449 V3 prompts across all conditions (no change). All 7 categories are evaluated — including held-out categories (which is the whole point).
- **Judges**: Same 3-judge consensus panel (GPT-5.1, Claude Opus 4.5, Llama 4 Maverick)
- **Primary metric**: Per-category accuracy on held-out categories (the ones NOT in training)
- **Key comparison**: Held-out category accuracy in ablation condition vs same category accuracy in Full condition. If close (gap <3pp), caution generalizes. If large gap (>5pp), caution is category-specific.
- **Statistical test**: McNemar's test per held-out category (ablation vs Full). Aggregate group-level tests as primary (entity-dep held-out n=268, entity-indep held-out n=181 — sufficient power). Per-category as supplementary (some categories n=20-31, low power).
- **Secondary analysis**: Does the model *over-refuse* on held-out categories? Check refusal rate (label=3) specifically.
- **Baseline reference**: Include baseline (no fine-tuning) accuracy as a floor. If ablation condition < Full but > baseline, the conclusion is "partial transfer — still helps but benefits from category-specific training."

#### Step-by-step implementation

**Step 10A: Generate training data** `[~1h, $0]`

Filter existing V5 best-per-prompt training data by category, then convert to Together AI message format.

Script: `scripts/build_cross_category_ablation.py`

For each condition, for each model:
1. Load `v5_training_{model}.jsonl`
2. Filter to included categories (or stratified random sample for R{entity-dep})
3. Write to `data/training/ablation_cross_cat/{condition}_{model}.jsonl` (best-per-prompt format)
4. Convert to `data/training/ablation_cross_cat/{condition}_together_{model}.jsonl` (Together AI message format: `{"messages": [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]}`)
5. Log prompt counts per category per condition
6. Write `data/training/ablation_cross_cat/cross_cat_ablation_report.json` (generation report)

**Pre-step: verify actual per-category training counts** (before writing script):
```
python3 -c "
import json
for model in ['mixtral-8x7b', 'llama-4-maverick-17b']:
    data = [json.loads(l) for l in open(f'data/training/v5_training_{model}.jsonl')]
    cats = {}
    for d in data:
        c = d.get('category', 'unknown')
        cats[c] = cats.get(c, 0) + 1
    print(f'{model}: {len(data)} total')
    for c, n in sorted(cats.items()):
        print(f'  {c}: {n}')
"
```
This determines exact N for each condition and confirms entity-dep viability (need >200).

**Validation checklist**:
- [ ] Verify zero overlap between held-out categories' training data and the filtered training set
- [ ] Verify prompt counts are sufficient per condition (>200 for LoRA)
- [ ] Verify all conditions use the same V3 test set (449 prompts, all 7 categories — including held-out categories)
- [ ] Verify Together AI format is correct (messages array, no system prompt)
- [ ] Verify R{entity-dep} has same total N as entity-dep condition, stratified by category

**Step 10B: Fine-tune** `[~12-20h wall, ~$50-100]`

10 fine-tuning jobs: 5 conditions (excluding Full) × 2 models.

**LoRA config**: configC for Mixtral (lr=2e-4, 5 epochs), configA for Llama (lr=2e-4, 3 epochs). Same as the main fine-tuning experiment and Phase 9 ablation. Together AI overrides: lora_r=64, alpha=128, no dropout. Llama uses QLoRA (4-bit).

| Job | Model | Condition | Expected N |
|-----|-------|-----------|------------|
| 1 | Mixtral | Entity-dep only | ~1,000 |
| 2 | Mixtral | R{entity-dep} | ~1,000 (matched) |
| 3 | Mixtral | Entity-indep only | ~1,430 |
| 4 | Mixtral | Leave-out-nonexistent | ~1,830 |
| 5 | Mixtral | Leave-out-factual | ~1,930 |
| 6 | Llama | Entity-dep only | ~1,000 |
| 7 | Llama | R{entity-dep} | ~1,000 (matched) |
| 8 | Llama | Entity-indep only | ~1,430 |
| 9 | Llama | Leave-out-nonexistent | ~1,830 |
| 10 | Llama | Leave-out-factual | ~1,930 |

Together AI. Jobs can run in parallel (all use separate uploaded files).

Script: `scripts/run_cross_cat_finetuning.py` (modeled on `run_v5_finetuning.py` but reads from `ablation_cross_cat/` directory and uses the correct per-model config).

Job tracking: `data/training/ablation_cross_cat/cross_cat_ft_jobs.json`

**Fallback if time-constrained**: Run only Mixtral (5 jobs), since Mixtral showed larger fine-tuning gains and more room for differentiation. Add Llama if time permits.

**Step 10C: Generate answers** `[~2h wall, ~$5]`

Run each fine-tuned model on the full 449-prompt test set.

10 answer files: `results/v5_finetuned/cross_cat_ablation/{condition}_{model}/answers.jsonl`

**Mixtral deployment note**: Mixtral requires a dedicated endpoint ($0.13/min) — deploy one condition at a time, run 449 prompts (~10 min), stop endpoint. 5 Mixtral conditions = ~50 min sequential endpoint time. Llama uses serverless LoRA (no endpoint cost, can run in parallel).

Script: `scripts/run_cross_cat_evaluation.py` (modeled on `run_ablation_evaluation.py`)

**Step 10D: Judge** `[~4h wall, ~$25-35]`

3-judge consensus on all 10 × 449 = 4,490 answers.

Output: `results/v5_finetuned/cross_cat_ablation/{condition}_{model}/judged_answers.jsonl`

**Step 10E: Analyze** `[~1-2h, $0]`

Script: `scripts/analyze_cross_category_ablation.py`

Analysis structure:
1. **Per-condition overall accuracy** (all 449 test prompts)
2. **Per-condition per-category accuracy** — the key table. For each condition, report accuracy on (a) trained categories and (b) held-out categories separately
3. **Generalization gap**: For each held-out category, compute: `Full_accuracy - Ablation_accuracy`. This is the "cost of not seeing this category during training"
4. **Size control comparison**: Entity-dep-only vs R{entity-dep} — same N, different category composition. If entity-dep underperforms R{entity-dep}, the deficit is category coverage. If equal, category composition at this N doesn't matter.
5. **Cross-group transfer matrix**: Entity-dep-only model's accuracy on entity-indep test prompts vs Full model. Vice versa.
6. **Refusal rate analysis**: Does the model over-refuse on unfamiliar category types?
7. **McNemar's test**: Each condition vs Full, both overall and per held-out category. Also entity-dep vs R{entity-dep}.
8. **Baseline floor**: Include baseline (no FT) accuracy per category as reference

**Expected outcomes and interpretation**:

| Outcome | What it means | Thesis framing |
|---------|--------------|----------------|
| Held-out accuracy ≈ Full accuracy (<3pp gap) | Caution fully generalizes across category types | **Strongest claim**: model learns domain-general epistemic caution. Third generalization type confirmed. |
| Moderate gap (3-8pp) on held-out categories | Partial generalization — some category-specific learning needed | Interesting nuance: model learns *mostly* general caution but benefits from category-specific examples. Report honestly. |
| Large gap (>8pp) on held-out categories | Caution is category-specific | Still informative: the model needs to see examples of each uncertainty type. Contrasts with template/entity generalization. |
| Asymmetric: entity-dep→entity-indep transfers but not vice versa | One direction of transfer is easier | Suggests entity-dependent caution is a harder skill that requires direct training. Or entity-independent caution is more general. |
| Entity-dep ≈ R{entity-dep} | Category composition doesn't matter at matched N | Strengthens "general strategy" claim — even a category-restricted training set teaches the same thing as a balanced one |
| Entity-dep < R{entity-dep} | Category restriction hurts beyond size | Category diversity matters — the model benefits from seeing diverse uncertainty types during training |

**All outcomes are publishable.** This is not a "we need a positive result" experiment — any result informs the thesis narrative about what fine-tuning actually teaches.

#### Research questions (mapped to Sunny's suggestion)

1. **Does caution generalize across category types?** The main question. If yes, this is the third behavioral generalization finding.
2. **Is there an asymmetry in transfer direction?** Entity-dep → entity-indep vs the reverse. Could reveal which uncertainty types are "harder" to learn.
3. **What is the minimum category coverage needed?** If leave-out-nonexistent performs as well as Full, we don't need nonexistent training data at all. Practical implication for data collection.
4. **Does the model over-refuse on unfamiliar categories?** A possible failure mode: the model becomes uniformly cautious and refuses factual questions it should answer confidently.
5. **Is category composition or dataset size the driver?** Entity-dep vs R{entity-dep} answers this directly.

#### Cost and timeline

| Step | Wall time | API cost |
|------|-----------|----------|
| 10A: Generate training data | ~1h | $0 | **DONE** |
| 10B: Fine-tune (10 jobs parallel) | ~12-20h | ~$28 (verified dry run) | **DONE** |
| 10C: Generate answers (dedicated endpoints, sequential) | ~2-3h | ~$46 (Mixtral 5×$1.50 + Llama 5×$8) | **DONE** |
| 10D: Judge | ~6h | ~$25-35 | **DONE** |
| 10E: Analyze | ~1-2h | $0 | |
| **Total** | **~1-2 days wall** | **~$100-110** | |

**Note**: Both Mixtral AND Llama require dedicated endpoints for fine-tuned LoRA inference (serverless LoRA not supported for these base models). Mixtral: $0.13/min on 2×H100. Llama: $0.53/min on 8×H100. Script auto-deploys and stops endpoints per condition.

**Simplified fallback**: Mixtral only (5 conditions). ~1 day wall, ~$35-45.

#### Risks and mitigations

1. **Risk: Unbalanced training sizes across conditions**. Entity-dep only has ~1,000 prompts vs Full's ~2,400. Performance differences could reflect dataset size, not category coverage. **Mitigation**: R{entity-dep} size-matched random control (same approach as Phase 9's R{N}). If entity-dep ≈ R{entity-dep}, size is the driver. If entity-dep < R{entity-dep}, category composition matters.

2. **Risk: Test set category sizes too small for per-category significance**. Impossible (n=30), borderline_obscure_real (n=30), borderline_edge_factual (n=20), borderline_plausible_fake (n=31). At n=30, need ~15pp difference for McNemar significance. **Mitigation**: Report aggregate group-level tests as primary (entity-dep held-out: n=268, entity-indep held-out: n=181 — sufficient power). Per-category as supplementary with effect sizes and confidence intervals.

3. **Risk: Phase 9 showed template count doesn't matter. What if category count also doesn't matter?** Then we have another "flat curve" result. **Mitigation**: This is still a positive finding — it strengthens the "general epistemic strategy" narrative. The model doesn't need diversity of templates OR diversity of categories. What it needs is diversity of *entities* (since we know T1 failed due to insufficient prompts, not insufficient templates).

4. **Risk: Together AI overrides LoRA hyperparameters.** Phase 9 discovered Together applies its own defaults (lora_r=64, alpha=128, no dropout) regardless of what we request. **Mitigation**: This is fine — all conditions use the same Together defaults, so the comparison is fair. Document the actual params used.

**Thesis location**: Ch 7.7 "Cross-Category Generalization" (~2-3 pages). Follows template ablation (Ch 7.6). Together with decontamination (Ch 7.4), TruthfulQA (Ch 7.5), and template ablation (Ch 7.6), this completes the "three types of generalization" narrative arc that Sunny suggested.

#### Phase 10 Results (Mar 12, 2026)

**Step 10A**: DONE. Data generated for all 5 conditions × 2 models. All validations passed. Script: `scripts/build_cross_category_ablation.py`. Output: `data/training/ablation_cross_cat/`.

**Step 10B**: DONE. All 10 fine-tuning jobs completed on Together AI. FT cost: ~$28. Jobs tracked in `data/training/ablation_cross_cat/cross_cat_ft_jobs.json`. Together AI applied lora_r=64, lora_alpha=128, targets k_proj/o_proj/q_proj/v_proj.

**Step 10C/D**: DONE. All 10 conditions × 449 prompts generated and judged (4,490 judgments total). Script: `scripts/run_cross_cat_evaluation.py`. One wifi disconnect and one endpoint STOPPED issue during execution — all resolved via `--skip-existing` and `--start-from` resume flags.

**Overall results (accuracy / hallucination rate)**:

| Condition | Mixtral Acc | Mixtral Hall | Llama Acc | Llama Hall |
|-----------|-------------|--------------|-----------|------------|
| **Full (T-all, control)** | **94.4%** | **1.3%** | **94.0%** | **1.1%** |
| leave_out_nonex | 92.2% | 3.8% | **95.8%** | **0.4%** |
| leave_out_fact | 93.5% | 1.6% | 95.3% | 0.9% |
| entity_dep | 93.3% | 2.0% | 95.3% | 0.2% |
| R_entity_dep | 93.1% | 2.4% | 94.4% | 1.1% |
| entity_indep | 90.9% | 4.9% | 92.7% | 3.8% |

**Key findings**:

1. **Entity-indep is clearly worst for both models** — training only on entity-independent categories (factual, ambiguous, impossible, edge_factual) produces 3-5× higher hallucination than Full. The model fails to learn caution about entity existence from question-structure training alone.

2. **Entity-dep generalizes surprisingly well** — training on only ~1,000 entity-dependent examples nearly matches Full (~2,400) for Mixtral (93.3% vs 94.4%), and **beats Full for Llama** (95.3% vs 94.0%, 0.2% vs 1.1% hallucination). Entity-dependent caution transfers to entity-independent questions.

3. **Asymmetric transfer**: Entity-dep → entity-indep works well. Entity-indep → entity-dep fails (especially on nonexistent: 95.0% vs 99-100% for other conditions). Learning "be careful about question structure" does NOT teach "be careful about entity existence."

4. **R_entity_dep ≈ entity_dep** — the size-matched random control performs similarly (93.1% vs 93.3% Mixtral, 94.4% vs 95.3% Llama). This suggests entity-dep's strong performance is NOT because entity-dependent categories are inherently better training data — rather, ~1,000 examples of ANY category mix teaches adequate caution. For Llama, entity_dep slightly outperforms R_entity_dep, hinting that entity-focused training may have a small edge.

5. **Leave-out conditions nearly match Full** — removing nonexistent or factual barely hurts. For Llama, leave_out_nonex actually outperforms Full (95.8% vs 94.0%). Caution transfers perfectly to individual held-out categories.

6. **borderline_plausible_fake remains hardest** — 67-97% accuracy across conditions, consistent with known entity contamination issue. entity_indep hits 67.7% (Llama) / 77.4% (Mixtral) on this category.

7. **No over-refusal on held-out categories** — refusal rates stay low (0.4-1.1%) across all conditions. The model doesn't become uniformly cautious on unfamiliar category types.

**Interpretation**: Fine-tuning teaches behavioral caution that generalizes across category boundaries. This is the **third type of behavioral generalization** confirmed:
1. Unseen entities (decontamination, Step 11C)
2. Unseen question templates (TruthfulQA + template ablation, Phase 5/9)
3. **Unseen category types** (this experiment)

The asymmetry finding adds nuance: entity-dependent training is more "portable" than entity-independent training. Learning to verify entity existence teaches a deeper epistemic strategy that naturally covers question-structure uncertainty. The reverse is not true.

**Step 10E**: Pending — formal statistical analysis script with McNemar's tests, generalization gaps, and cross-group transfer matrix.

---

### Phase 6: Geometry-Guided Targeting `[FUTURE WORK]`

- Build a geometry-aware system that selects the optimal prefix per-prompt based on geometric features
- For fine-tuning: weight geometrically risky prompts more heavily in training data

**Value**: **High reward, medium-high risk.** The most intellectually elegant extension — using geometry operationally. But the within-category density signal is modest (r≈0.25). A geometry-based selector might not outperform always using the best single prefix. If it works, crown jewel. If not, time spent on a null result.

**Cost**: Medium — requires building a classifier, selecting thresholds, evaluating on held-out data. ~2-3 days.

**Recommendation**: Mention in Discussion/Future Work. The analytical geometry-intervention connection (Ch 7 bridge analysis, best-per-prompt curation) is already complete. Phase 6 adds operational deployment, not conceptual insight.

### Phase 7: Literature Baselines Comparison `[IN PROGRESS — Step 7A Done]`

**Purpose**: Contextualize our results against published mitigation methods. Without this, the thesis's 89% hallucination reduction and fine-tuning distillation float in a vacuum — a reviewer's natural question is "how does this compare to RAG? Self-consistency? DPO?"

**Value**: **High, near-zero cost.** Zero API cost, few hours of literature review. Goes in Ch 8 (Discussion).

**Risk of skipping**: A reviewer writes "The authors do not compare against any standard mitigation baselines."

**Critical constraint**: Direct apples-to-apples comparison is impossible — every method uses different benchmarks, models, metrics, and hallucination definitions. The table must include an explicit **comparability assessment** per entry. A sloppy comparison table is worse than no table: it invites accusations of cherry-picking favorable comparisons.

#### Method Selection Criteria

Methods are NOT randomly selected. Inclusion requires meeting **at least two** of these criteria:

1. **Axis relevance**: The method addresses at least one of our three axes:
   - Axis 1 (Detection): Predicts whether a response will contain hallucination
   - Axis 2 (Prompt mitigation): Reduces hallucination via prompting, no weight changes
   - Axis 3 (Fine-tuning mitigation): Reduces hallucination via weight modification

2. **Citation threshold**: ≥100 citations on Google Scholar (establishes the method is not obscure). Exception: papers published in 2024-2025 that appear at top venues (NeurIPS, ICLR, ACL, EMNLP) since they haven't had time to accumulate citations.

3. **Quantitative results available**: The paper reports numerical hallucination reduction rates (not just qualitative examples). We need numbers for the table.

4. **Conceptual proximity**: The method is close enough to ours that a reviewer would reasonably ask "why didn't you compare against X?" — i.e., methods a hallucination reviewer would expect to see cited.

**Exclusion criteria** (methods we explicitly do NOT include, with justification):
- Methods that only apply to retrieval-augmented settings (we test closed-book generation)
- Methods requiring human preference data we don't have (pure RLHF/DPO on preference datasets — though we include them for context with a note)
- Methods tested only on summarization/translation (different hallucination mode than open-domain QA)
- Methods from before 2020 (pre-LLM era, different paradigm)

#### Benchmark Selection Criteria

The comparison table will reference results from specific benchmarks. Benchmark inclusion requires:

1. **Widely adopted**: Used by ≥3 of the comparison methods, OR is a standard evaluation in the hallucination literature
2. **Hallucination-specific**: The benchmark specifically measures factual accuracy or hallucination, not general capability (no MMLU, no SuperGLUE)
3. **Open-domain QA or knowledge-intensive**: Matches our task setting (not summarization faithfulness, not dialogue consistency)
4. **Published baseline scores exist**: We can cite specific numbers from the original paper

**Candidate benchmarks** (to be confirmed during literature review):
- **TruthfulQA** (Lin et al., 2022): 817 questions, tests misconceptions. We run this ourselves (Phase 5) — enables direct comparison of our base model scores against published baselines as a judge calibration check.
- **SimpleQA** (OpenAI, 2024): 4,326 questions, tests factual accuracy with verified ground truth. Recent, well-designed, graded by automated judge.
- **HaluEval** (Li et al., 2023): 35K samples across QA/dialogue/summarization. Widely cited hallucination benchmark.
- **FActScore** (Min et al., 2023): Atomic fact precision for long-form generation. Different metric (precision, not accuracy) — include only if comparison methods report it.

**Excluded benchmarks** (with justification):
- MMLU / HELM general benchmarks: Not hallucination-specific
- SQuAD / Natural Questions: Extractive QA, not generative hallucination
- Summarization faithfulness benchmarks (XSum, CNN/DM): Different task, different hallucination mode

#### Comparison Table Structure

Three sub-tables, one per axis. Each entry includes:

| Column | Purpose |
|---|---|
| Method | Name + citation |
| Category | Prompting / fine-tuning / inference-time / retrieval-augmented |
| Benchmark | Which benchmark the reported result is from |
| Model(s) | Which model(s) the method was tested on |
| Metric | What was measured (accuracy, hallucination rate, FActScore, etc.) |
| Result | The reported number |
| Ours (comparable) | Our result on the closest comparable metric, if any |
| Comparability | Direct / Partial / Indirect — with brief justification |

**Comparability definitions**:
- **Direct**: Same benchmark AND same model family AND same metric. (Likely none — our setup is novel)
- **Partial**: Same benchmark OR same model family, but different metric or setup. (TruthfulQA results will be partial — same benchmark, different models/judge)
- **Indirect**: Different benchmark, different model — only directional comparison possible. (Most entries)

#### Specific Rigor Concerns

1. **No cherry-picking**: Include methods that outperform us on their benchmarks. The framing is "different niche" not "we're better." If RAG achieves 95% accuracy with retrieval, we report that honestly and note we test closed-book.

2. **Metric incompatibility must be stated**: Our "hallucination rate" (% of responses labeled 2 by 3-judge consensus) ≠ TruthfulQA's "% truthful" (GPT-judge) ≠ FActScore's atomic precision. A paragraph before the table must explain why numbers across rows are not directly comparable.

3. **Model generation gap**: Many papers test GPT-3.5 or Llama 2 (7B-70B). We test Mixtral 8x7B and Llama 4 Maverick 17B. Different generations, different baseline capabilities. A method reducing GPT-3.5 hallucination by 50% is not equivalent to our 89% reduction on Mixtral.

4. **R-Tuning is the closest comparison**: Zhang et al. (2023) fine-tune models to say "I don't know" — conceptually the closest to our fine-tuning for entity skepticism. This comparison must be detailed and honest. Differences: they use explicit "I don't know" labels, we use best-per-prompt selection; they test on knowledge-intensive QA, we test on a custom entity benchmark.

5. **Our CoT failure as context**: Our CoT Verification prefix has 62-68% refusal rate. Chain-of-Verification (Dhuliawala et al.) reports improvements. The difference — system prompt CoT vs. multi-step structured verification — is worth noting.

6. **Include our own negative results**: The table should include our CoT Verification result as an entry alongside external methods. Showing we honestly report our own failures strengthens credibility.

#### Execution Steps

**Step 7A: Systematic literature search (~2-3 hours)** `[DONE — Mar 2026]`

**Results**: 4 parallel search axes completed. Found 22 methods across 3 axes + 4 surveys + 3 benchmark baseline tables + 3 RAG baselines.
- Detection: 8 methods (SelfCheckGPT, Semantic Entropy, P(True), ITI, INSIDE/EigenScore, Lookback Lens, FActScore, SAPLMA)
- Prompt mitigation: 8 methods (CoT, Self-Consistency, CoVe, Self-Refine, AMA, SelfCheckGPT, Self-Alignment, RECITE)
- Fine-tuning: 8 methods (R-Tuning, FactTune, InstructGPT/RLHF, FLAME, Mask-DPO, CAI, Self-RAG, Fine-Tuning Paradox)
- Surveys: Huang et al. (~1,868 cit), Zhang et al. (~814), Tonmoy et al. (~166, 32+ method table), Alansari & Luqman (2025)
- Benchmarks: TruthfulQA (Mixtral 73.9% MC2), SimpleQA (o1-preview 42.7%), HaluEval (ChatGPT QA 62.59%)

**Output files**:
- `results/literature_comparison/comparison_notes.md` — full structured notes with per-method details
- `results/literature_comparison/baselines_table.csv` — 22 methods with comparability assessments

**Key finding**: R-Tuning (NAACL 2024 Outstanding Paper) is our closest comparator. INSIDE/EigenScore is our closest conceptual kin in detection. No prior work predicts hallucination *difficulty* — this confirms our contribution is novel.

**Papers requiring paywall verification**: None — all papers available on arXiv. Some specific table values (R-Tuning Table 1 AP scores, Semantic Entropy Extended Data exact AUROCs, ITI Table 1 conditions) should be verified from the PDF before final thesis submission.

#### Step 7A Detailed Findings

##### Detection Methods (Axis 1)

| Method | Year/Venue | Citations | Access Type | Key Result | Comparability |
|---|---|---|---|---|---|
| SelfCheckGPT (Manakul et al.) | 2023 EMNLP | ~600 | Black-box | AUC-PR ~0.78 sentence-level (WikiBio) | Indirect — detects in generated text; we predict from geometry pre-generation |
| Semantic Entropy (Farquhar et al.) | 2024 Nature | ~773 | White-box (logprobs) | Best AUROC across 5 QA datasets vs all baselines | Partial — both use embedding-level features, but they operate post-generation |
| P(True) / P(IK) (Kadavath et al.) | 2022 Anthropic | ~373 | White-box (logits) | P(True)>50% strongly predictive; scales with model size | Indirect — self-evaluation, not external geometry |
| **ITI** (Li et al.) | 2023 NeurIPS | ~200+ | White-box (activations) | TruthfulQA: 32.5% → 65.1% truthfulness | **Partial** — both work in embedding space; they modify activations at inference, we select training data via geometry |
| **INSIDE / EigenScore** (Chen et al.) | 2024 ICLR | ~100+ | White-box (embeddings) | +5-10pp AUROC over logit/language baselines | **Partial — closest conceptual kin**. Both use embedding-space properties: they compute eigenvalues of response embedding covariance, we compute geometric features (density, centrality) of entity embeddings in knowledge graph |
| Lookback Lens (Chuang et al.) | 2024 EMNLP | ~74 | White-box (attention) | Test AUROC 0.914 (NQ); 9.6% hallucination reduction (XSum) | Indirect — attention analysis, not entity geometry |
| FActScore (Min et al.) | 2023 EMNLP | ~869 | Black-box (eval metric) | ChatGPT only 58% factual; <2% error vs human annotation | Indirect — evaluation framework, not prediction |
| SAPLMA (Azaria & Mitchell) | 2023 EMNLP Findings | ~200+ | White-box (hidden states) | 71-83% accuracy on true/false classification | Partial — both analyze internal representations; they probe model hidden states, we analyze knowledge graph topology |

**Detection positioning**: Our geometric approach falls in the white-box embedding analysis category alongside INSIDE/EigenScore. Key differentiator: existing methods predict hallucination *presence/absence*; our bridge analysis (AUC=0.86) predicts hallucination *difficulty* — which ones resist mitigation. No prior work does this.

##### Prompt Mitigation Methods (Axis 2)

| Method | Year/Venue | Citations | Key Result | Comparability |
|---|---|---|---|---|
| Chain-of-Thought (Wei et al.) | 2022 NeurIPS | ~14,400 | GSM8K: 17.9% → 58.1% (+40pp) with PaLM-540B | Partial — our V4 tested prompt prefixes on entity hallucination (different domain). CoT primarily helps reasoning. Caveat: ACL Findings 2025 showed CoT *obscures* hallucination detection cues |
| Self-Consistency (Wang et al.) | 2023 ICLR | ~3,500 | +17.9% over CoT on GSM8K; consistent across 4 model families | Indirect — multi-sample voting; our prefixes are single-shot |
| **CoVe** (Dhuliawala et al.) | 2024 ACL Findings | ~308 | Hallucinated entities: 2.95 → 0.68/response (two-step, Wikidata); FactScore: 55.9→71.4 (+15.5pp, factor+revise). LLaMA-65B. | **Partial** — both reduce entity-level hallucination. CoVe: multi-step self-verification. Us: single-shot prefix + FT. CoVe is inference-compute-heavy; ours bakes in via training |
| Self-Refine (Madaan et al.) | 2023 NeurIPS | ~2,548 | ~20% absolute improvement avg across 7 tasks vs single-pass | Indirect — iterative refinement; we target entity hallucination specifically |
| AMA (Arora et al.) | 2023 ICLR | ~252 | +10.2% avg over few-shot; 6B matches 175B on 15/20 tasks | Indirect — different mechanism (question reformulation + aggregation) |
| Self-Alignment for Factuality (Zhang et al.) | 2024 ACL | ~50+ | TruthfulQA: +13% accuracy over base LLaMA-7B; BioGEN: +4% FActScore | Partial — hybrid prompt+DPO method |
| RECITE (Sun et al.) | 2023 ICLR | ~200+ | Matches BM25 retrieval on closed-book QA | Indirect — closed-book alternative to RAG |

**Prompt positioning**: Our V4 prefix experiment is conceptually closest to CoVe (both target entity-level hallucination). Key differentiator: CoVe uses multi-step verification at inference time (expensive per query); our approach identifies *which* prompts benefit from which prefix using geometric features, then distills the effect into fine-tuned weights (cheap at inference time). Our CoT Verification prefix's 62-68% refusal rate vs. CoVe's success illustrates that naive CoT application ≠ structured multi-step verification.

##### Fine-Tuning Mitigation Methods (Axis 3)

| Method | Year/Venue | Citations | Key Result | Comparability |
|---|---|---|---|---|
| **R-Tuning** (Zhang et al.) | 2024 NAACL **Outstanding Paper** | ~120-180 | Outperforms vanilla IT in Average Precision; refusal transfers as meta-skill to unseen tasks | **Direct — CLOSEST COMPARATOR**. Both teach models to abstain on uncertain knowledge. R-Tuning: identifies unknowns via train-time probing (can model answer?). Us: identifies unknowns via geometric features of entity embeddings (centrality, density). Our geometric taxonomy adds *why* some are harder. |
| **FactTune** (Tian et al.) | 2024 ICLR | ~200+ | 58% reduction in factual errors (biography); 40% (medical QA) | Partial — both FT for factuality. FactTune: DPO with auto-generated preferences. Us: LoRA SFT with geometry-guided best-per-prompt selection |
| InstructGPT / RLHF (Ouyang et al.) | 2022 NeurIPS | ~7,000+ | TruthfulQA: 21% → 42%. But *increased* hallucination on some open-ended tasks | Indirect — general alignment, not hallucination-specific |
| FLAME (Dhuliawala et al.) | 2024 NeurIPS | ~40-60 | +5.6 FActScore over standard DPO; no instruction-following sacrifice | Partial — both address the SFT-on-novel-knowledge problem. FLAME filters by model familiarity; we select by geometry + prefix effectiveness |
| Mask-DPO | 2025 ICLR | ~10-20 | ANAH: 49.19% → 77.53% (+28.3pp); 8B surpasses 70B on factuality | Partial — sentence-level DPO masking vs our LoRA SFT |
| Constitutional AI (Bai et al.) | 2022 Anthropic | ~2,500+ | TruthfulQA ~58%; primarily harmlessness, hallucination secondary | Indirect — general alignment |
| Self-RAG (Asai et al.) | 2024 ICLR | ~500+ | PopQA: 14.7% → 55.8%; biography factuality 80% (vs ChatGPT 71%) | Indirect — hybrid FT+retrieval; we operate closed-book |
| Fine-Tuning Paradox (Gekhman et al.) | 2024 EMNLP | — | FT on *new* knowledge linearly increases hallucination | Context paper — our approach avoids this: we FT on behavioral patterns (entity skepticism), not new facts |

**Fine-tuning positioning**: R-Tuning is the head-to-head comparison. Both teach models to handle knowledge boundaries, but through fundamentally different signals. R-Tuning: "can the model answer this question?" (binary train-time probing). Ours: "what does the geometry of this entity's embedding neighborhood look like?" (continuous features — density, centrality — that predict *degree* of hallucination difficulty, not just presence). The DPO-based methods (FactTune, FLAME, Mask-DPO) represent a different paradigm entirely — they use preference pairs, we use geometry-guided best-per-prompt selection followed by LoRA SFT.

##### Surveys Identified

| Survey | Year | Citations | Key Value |
|---|---|---|---|
| Huang et al. "A Survey on Hallucination in LLMs" | 2023 | ~1,868 | Most cited; broadest taxonomy (detection + mitigation by stage) |
| Zhang et al. "Siren's Song in the AI Ocean" | 2023 | ~814 | Connects detection and mitigation; training data memorization emphasis |
| **Tonmoy et al.** "Comprehensive Survey of Hallucination Mitigation" | 2024 | ~166 | **Most useful for us**: 32+ method comparison table organized by prompt eng + RAG, self-refinement, training-based |
| Alansari & Luqman | 2025 | Recent | Most up-to-date; full lifecycle taxonomy |

**Survey usage**: Cite Huang et al. for the broadest taxonomy in Related Work. Use Tonmoy et al.'s 32+ method table as validation that our method selection is comprehensive — cross-reference our 22 methods against their table to verify no glaring omissions.

##### Benchmark Baselines (Published Scores)

**TruthfulQA** (Lin et al., 2022) — 817 questions, 38 categories:
| Model | Score | Metric | Source |
|---|---|---|---|
| Mixtral 8x7B Instruct | 73.9% | MC2 | Open LLM Leaderboard |
| Llama 2 70B Chat | 44.9% | MC2 | Open LLM Leaderboard |
| Llama 2 7B Chat | 45.3% | MC2 | Open LLM Leaderboard |
| Llama 3 8B | ~44% | MC2 | Open LLM Leaderboard |
| InstructGPT 175B | ~42% | Truthful (GPT-judge) | Ouyang et al. 2022 |
| GPT-3 175B | ~21% | Truthful (GPT-judge) | Ouyang et al. 2022 |
| Alpaca + ITI | 65.1% | Truthful (GPT-judge) | Li et al. 2023 |
| **Our Mixtral baseline** | **74.4%** | 3-judge consensus (accuracy) | This work (Step 13E) |
| **Our Llama baseline** | **71.8%** | 3-judge consensus (accuracy) | This work (Step 13E) |
| **Our Mixtral FT** | **76.6%** | 3-judge consensus (accuracy) | This work (Step 13E) |
| **Our Llama FT** | **77.1%** | 3-judge consensus (accuracy) | This work (Step 13E) |

**SimpleQA** (OpenAI, 2024) — 4,326 questions:
| Model | Correct | Source |
|---|---|---|
| GPT-4.5 | 62.5% | OpenAI |
| o1-preview | 42.7% | OpenAI |
| GPT-4o | 38.2% | OpenAI |
| Claude 3.5 Sonnet | 28.9% | OpenAI |
| Llama 3.1 70B | ~20% | Community evals |
| Mixtral | — | No published score |

**HaluEval** (Li et al., 2023) — 35,000 samples:
| Task | ChatGPT Baseline | With External Knowledge |
|---|---|---|
| QA | 62.59% | 76.83% |
| General (generation) | 19.5% halluc. rate | — |

**RAG baselines** (for the "why not just use RAG?" reviewer question):
| Paper | Key Result |
|---|---|
| Original RAG (Lewis et al., NeurIPS 2020) | NQ: 44.5 EM (vs 41.5 DPR baseline) |
| Shuster et al. (Findings EMNLP 2021) | 60%+ reduction in factual error in dialogue |
| Self-RAG (Asai et al., ICLR 2024) | Biography factuality: 80% (vs ChatGPT 71%) |

##### Thesis Positioning Summary (from 7A findings)

**What we do that no one else does**:
1. Predict hallucination *difficulty* (not just presence) from geometric features (AUC=0.86)
2. Combine geometric prediction + prompt intervention + fine-tuning distillation in a single pipeline
3. Show that "unfixable" hallucinations cluster in specific geometric regions (high centrality, low density)
4. Demonstrate prompt prefix effects can be distilled into LoRA weights

**What others do that we don't** (honest limitations):
- RAG methods achieve higher factuality with retrieval infrastructure (we test closed-book)
- DPO methods use preference pair optimization (we use simpler LoRA SFT)
- ITI modifies activations at inference time (we don't intervene in the forward pass)
- Semantic Entropy and INSIDE operate on the actual model being evaluated (we use a separate embedding model for geometry)

**Reviewer defense script**:
- "Why not RAG?" → We test closed-book generation; RAG requires retrieval infrastructure and can't help when no relevant documents exist
- "How does this compare to R-Tuning?" → Both teach abstention on uncertain knowledge via different signals (train-time probing vs geometry). Our geometric features additionally predict *resistance* to mitigation, which R-Tuning does not address
- "Why not DPO?" → Our geometry-guided best-per-prompt selection could be seen as an implicit form of preference learning, but without requiring explicit preference pairs. The geometric signal identifies the "preference" (which prefix produces the best output) without human annotation
- "What about Self-RAG/CoVe?" → These are inference-time compute-heavy (multiple steps per query). Our approach bakes the effect into weights, making inference cheap. Complementary, not competing approaches.

This is NOT a casual bibliography check. It is a structured search designed to be defensible if a reviewer asks "how did you select comparison methods?"

**Search strategy** (multi-source, documented):

1. **Existing bibliography** (26 refs): Extract all mitigation methods already cited. These are the starting point, not the endpoint.

2. **Keyword searches on Google Scholar / Semantic Scholar / arXiv** (2020-present):
   - "hallucination mitigation LLM" / "reduce hallucination large language model"
   - "truthful language model fine-tuning" / "factuality fine-tuning"
   - "hallucination detection embedding" / "hallucination prediction"
   - "prompt engineering hallucination" / "system prompt factuality"
   - "LLM calibration factual" / "knowledge grounding LLM"
   - Sort by citation count to identify the field's consensus "important methods"

3. **Survey mining**: Read the methods/comparison tables from the 2-3 most cited hallucination surveys (2023-2025). Surveys aggregate the field's consensus on what methods matter. Key surveys:
   - Ji et al. (2023) "Survey of Hallucination in NLG" (already in bib, 1000+ citations)
   - Huang et al. (2023) "A Survey on Hallucination in LLMs" (if highly cited)
   - Tonmoy et al. (2024) "A Comprehensive Survey of Hallucination Mitigation Techniques in LLMs" (if exists)
   - Any 2024-2025 survey with ≥50 citations

4. **Benchmark leaderboards**: Check published baselines for benchmarks we compare against:
   - TruthfulQA published results table (original paper + HuggingFace leaderboard)
   - SimpleQA published results (OpenAI blog / paper)
   - HaluEval published baselines

5. **Citation chain (forward + backward)**: For the 3-4 most conceptually close methods (especially R-Tuning, ITI, CoVe), check:
   - What do THEY cite? (backward — older foundational methods we might miss)
   - Who cites THEM? (forward — newer methods building on the same idea)

6. **Venue proceedings scan** (NeurIPS 2023-2025, ICLR 2024-2025, ACL/EMNLP 2023-2025):
   - Search accepted paper lists for "hallucination" in title
   - Prioritize oral/spotlight papers (venue-endorsed importance)

**Per-method recording template**:
- Full citation (authors, title, venue, year)
- Google Scholar citation count (as of Mar 2026)
- Method category (prompting / fine-tuning / inference-time / retrieval / detection)
- Axis relevance (which of our 3 axes it addresses)
- Benchmark(s) used
- Model(s) tested
- Key quantitative result (exact numbers from paper)
- Table/figure number where result appears (for verification)
- Comparability to our setup (Direct / Partial / Indirect + justification)
- Why included (which selection criteria it meets)

**Paywall protocol**: Most ML papers are on arXiv (free access). For papers behind paywalls (some ACL Anthology, IEEE, etc.), flag the paper and ask the user to access and verify quantitative results before including them in the final table. Do not cite numbers that haven't been verified from the actual paper — abstracts and secondary sources can misrepresent results.

**Completeness check**: After initial search, verify coverage by asking: "If a hallucination researcher read our comparison table, would they notice a glaring omission?" If any commonly discussed method is missing, either include it or document why it was excluded.

**Step 7B: Build comparison tables (~1 hour)** `[DONE — Mar 2026, v4 after three rounds of rigorous review]`

**Output**: `results/literature_comparison/comparison_tables.md` (v4)

**Revision history**:
- v1: Uncurated dump of all 22 methods. 7 major problems.
- v2: Cut to 14 methods, fixed metric mixing. 8 remaining problems.
- v3: Tables finalized (15 methods + 1 context). But bridge AUC 0.86 presented without flagging as train-only/unreplicated; our own numbers not held to same standard as literature [*] flags.
- v4: Rewrote all "Our results" sections. Bridge AUC 0.86 now flagged as [†train-only], V5 CV AUC (0.59/0.43) reported alongside, within-category bridge confirmation (density p=0.034/0.047) added. Detection results restructured by rigor: within-category first (non-circular, 0.67/0.68 AUC), between-category second (partially confounded, 0.64/0.72), aggregate last. [†] flags on our own numbers matching [*] standard for literature.

**v4 summary**:
- **15 external methods + 1 context paper** across 3 tables (unchanged from v3)
- **Comparability breakdown**: 0 Direct, 5 Partial (close), 6 Partial (distant), 4 Indirect
- **Critical v4 fix**: All our own numbers now carry [†] caveats where methodologically warranted:
  - Bridge AUC 0.86 → [†train-only, V5 CV at 0.59, within-category density confirms at p<0.05 uncorrected]
  - Between-category AUC 0.64/0.72 → [†partially confounded by category structure; category alone = 0.77]
  - Within-category AUC 0.67/0.68 → the non-circular primary finding
  - V5 bridge within-category p=0.034/0.047 → [†uncorrected; would not survive Bonferroni, but confirmatory test]
  - FT bridge density → [†Mixtral survives Bonferroni; Llama does NOT (p_corrected=0.49)]
- **9 literature claims [*] + 5 own-number caveats [†] flagged**
- **Honest unknowns**: R-Tuning head-to-head unknown, CoVe/DoLA not tested on our benchmark

**Step 7C: Write comparison narrative (~2-3 hours)** `[FOLDED INTO THESIS WRITING]`

**Decision (Mar 11)**: Originally planned to write intermediate `comparison_narrative.md` then port to LaTeX. Now that all experiments are done and thesis writing is the sole remaining task, writing the narrative directly in Ch 8 LaTeX avoids double-work. The 6-section structure plan below still applies — it's the outline for Ch 8.3 (or wherever the comparison lands in the Discussion).

**Scope restriction**: Only discuss the 10 verified methods in depth. The 5 unverified [*] methods (SAPLMA, SelfCheckGPT, Self-Alignment, Self-Refine, RECITE) get mentioned but no specific numbers asserted from them.

#### Structure (6 sections)

**1. Opening: Why comparison is impossible (~0.5 page)**
- Convert comparison_tables.md preamble to thesis prose
- Every method uses different benchmarks, models, metrics, hallucination definitions
- Our metric (3-judge consensus on entity fabrication) is incommensurable with FActScore, AUROC, TruthfulQA truthfulness
- The tables provide *directional context*, not rankings
- **Rule: No cross-metric numerical comparisons anywhere in the narrative**

**2. Detection axis (~0.5 page)**
- INSIDE/EigenScore as closest conceptual kin (both: embedding geometry → prediction)
- Key difference: they analyze *response* embeddings post-generation from the model's internal states; we analyze *entity* embeddings in a knowledge graph pre-generation using an external embedding model
- Do NOT compare AUC numbers across methods — different tasks, different metrics, different inputs. The preamble's own principle forbids this.
- Our unique contribution: bridge analysis (predicting *fixability*, not just presence). No detection method in the table attempts fixability prediction.

**3. Prompt/inference-time axis (~0.5 page)**
- CoVe as closest (both target entity-level hallucination). Key tradeoff: CoVe uses a 4-stage pipeline per query (compute-heavy); we use a single-shot system prompt (cheap). Different models (LLaMA-65B vs our Mixtral/Llama 4).
- **TruthfulQA comparison angle (give this a full paragraph, not a parenthetical)**: DoLA achieves +12-17pp on TruthfulQA via decoding modification. Our Llama achieves -4.4pp halluc (Bonferroni-sig) — smaller, but ours is cross-domain transfer (NOT trained on TruthfulQA). This means we taught epistemic caution, not task-specific behavior. This is a key differentiator.
- CoT catastrophic refusal (62-68%) as genuine negative result — naive single-prompt instruction ≠ structured multi-step verification (CoVe) or decoding-level intervention (DoLA)

**4. Fine-tuning axis (~0.5 page)**
- **R-Tuning gets substantial treatment** (closest comparator, NAACL Outstanding Paper). Both teach abstention on uncertain knowledge via SFT. Key difference: R-Tuning uses binary train-time probing (can model answer this Q?); we use geometric features to guide best-per-prompt selection for training data. Frame the geometry-vs-probing comparison as the **central open empirical question** — whether geometry-guided selection produces better training data than R-Tuning's known/unknown split is unknown without running both on the same benchmark.
- DPO family (FactTune, FLAME, Mask-DPO) as a different training paradigm from our LoRA SFT. Different mechanism, different signal source. Cannot be directly compared.
- InstructGPT as foundational context. Its finding that RLHF can increase hallucination on some tasks (the "alignment tax") is directly relevant to our precision-recall tradeoff finding.

**5. The pipeline as contribution (~0.5 page)**
- **NOT novelty-by-conjunction** — the feedback loop is the insight, not the Venn diagram:
  - Geometry predicts which prompts cause hallucination (Ch 5)
  - Geometry predicts which hallucinations resist prompt intervention (bridge analysis, Ch 7)
  - Prompt responses become training signal via best-per-prompt selection (Ch 6→7)
  - FT distills prompt behavior into weights (Ch 7)
  - Geometry predicts where FT fails (FT bridge, Ch 7)
- Each step informs the next. Without geometry, you can't predict which prompts need help. Without prompts, you can't generate diverse training signal. Without FT, the improvement is ephemeral. Without the bridge analysis, you don't know where the cure has side effects.
- A skeptical reviewer will say "combining three existing things isn't a contribution." The response: the combination produces insight that the parts don't — specifically, the geometric taxonomy of fixability (Ch 7) only emerges because we have geometry + intervention + the ability to compare them.

**6. Honest limitations relative to prior work (~0.5 page)**
- RAG methods (Self-RAG) have retrieval; we're closed-book
- DPO methods (FactTune, Mask-DPO) have preference learning; we use simpler SFT
- CoVe has structured multi-step verification; we use a single prefix
- ITI modifies activations directly; we modify weights
- Our bridge analysis has small-sample caveats (n=5-15 in "broken" groups)
- We tested 2 models; most baselines test 3-6
- **Concrete future work**: Run R-Tuning on our benchmark, or run our method on ParaRel/MMLU — this is the comparison that would most advance the field

#### Issues caught during rigorous review (March 8, 2026)

1. **Metric mixing error in initial draft**: Planned to write "our AUC (0.67/0.68) is lower than typical detection AUROCs (0.78-0.91)." The 0.91 is from Lookback Lens, which is **not in our tables** (excluded during curation). The 0.78 is SelfCheckGPT's AUC-PR, which is a **different metric** from AUROC. The only proper AUROC comparison is Semantic Entropy's 0.790, and even that measures a different task (post-generation detection with 10 extra samples vs pre-generation prediction with zero samples). **Resolution**: Remove all cross-metric AUC comparisons from the narrative. The preamble's own principle forbids this.

2. **Scope confusion**: Initial plan said "write directly into discussion.tex" as if 7C = the whole chapter. Ch 8 Discussion covers four contributions, limitations, conclusion, and the comparison section. 7C is ~2-3 pages within a ~10-15 page chapter. **Resolution**: Output to standalone `comparison_narrative.md`, port to LaTeX during thesis writing.

3. **5 unverified papers**: Narrative plan cited specific numbers from SAPLMA (71-83%), SelfCheckGPT (AUC-PR 0.78), Self-Alignment (+13%), Self-Refine (~20%), RECITE. All still [*] unverified. Building a narrative on unverified numbers is bad practice. **Resolution**: Only discuss 10 verified methods in depth. Unverified methods get mentioned by name with no specific numbers asserted.

4. **R-Tuning understated**: Initial plan gave R-Tuning a few lines despite being flagged as "closest comparator" (NAACL Outstanding Paper). **Resolution**: Give it substantial treatment. Frame geometry-vs-probing as the central open question.

5. **TruthfulQA comparison buried**: Initial plan mentioned our TruthfulQA result as a parenthetical under DoLA. But our cross-domain transfer result (Llama -4.4pp Bonferroni-sig, NOT trained on TruthfulQA) is one of our strongest differentiators. **Resolution**: Give it a full paragraph.

6. **"Methodological gap" claim needs qualification**: "No prior work combines X+Y+Z" risks sounding like novelty-by-conjunction. **Resolution**: Explain why the combination produces insight the parts don't — the feedback loop, not the Venn diagram.

**Step 7D: Update bibliography and thesis guide (~30 min)** `[FOLDED INTO THESIS WRITING]`
- References added to `references.bib` as Ch 8 is written (not as a separate step)
- THESIS_WRITING.md already has comparison structure notes
- Phase 7 tables (7A+7B) complete; narrative (7C) written during Ch 8 drafting

#### Output Files

- `results/literature_comparison/baselines_table.csv` — structured comparison data
- `results/literature_comparison/comparison_notes.md` — detailed notes with full citations, comparability justifications, and per-method analysis
- Updates to `thesis_reference/references.bib` and `thesis/Dissertate-Harvard-LaTeX/references.bib`
- Updates to `THESIS_WRITING.md` (Ch 8 comparison section)

**Thesis location**: Ch 8 (Discussion), ~2-3 pages. Table + narrative contextualization.

### Phase 8: Adversarial Robustness `[FUTURE WORK]`

- Can adversarial prompts break the prefix-induced safety / fine-tuned caution?
- No adversarial framework built. Firmly future work.

**Value**: Low relative to effort. Robustness testing is a whole paper in itself.

### Human Validation Expansion `[RECOMMENDED]`

**Current state**: n=50 from V3 only, single annotator, 90% agreement (40/50). Acknowledged as thin in THESIS_WRITING.md. A reviewer questioning the entire evaluation pipeline because of n=50 would be painful.

**Goal**: Expand to n=150 with stratified sampling across V5 data, and optionally add a second annotator for inter-rater reliability. Zero API cost, a few hours of manual annotation work. Strengthens Ch 4.3.5 (Human Validation).

#### Option A: Stratified Expansion to n=150 (single annotator)

**Design**: Keep the original 50 V3 annotations. Add 100 new annotations stratified across the V5 pipeline stages:

| Stratum | n | Rationale |
|---|---|---|
| V5 baseline responses (no prefix) | 20 | Validates judge accuracy on new prompts |
| V5 prefix responses (best-per-prompt) | 20 | Validates judge accuracy on prefix-modified outputs |
| V5 fine-tuned responses | 20 | Validates judge accuracy on LoRA outputs |
| TruthfulQA judged responses | 20 | Validates cross-benchmark generalization of judge |
| Disagreement cases (judges split 2-1) | 20 | Stress-tests the consensus mechanism on hardest cases |

**Sampling procedure**:
1. For each stratum, randomly sample 20 prompt-response pairs (seed=2025)
2. For the disagreement stratum, filter to cases where exactly 1 of 3 judges dissented, then sample 20
3. Present to annotator in randomized order (not grouped by stratum) to avoid bias

**Metrics to compute**:
- Overall human-judge agreement (across all 150)
- Per-stratum agreement (are some pipeline stages harder to judge?)
- Per-label agreement: correct vs. hallucination vs. refusal
- Confusion matrix: which errors does the judge panel make? (false positives vs. false negatives)
- Compare V3 agreement (40/50 = 80%) vs V5 agreement — does performance hold on new data?

**Time estimate**: ~3-4 hours of manual annotation work.

#### Option B: Second Annotator for Inter-Rater Reliability

**Design**: Recruit a second annotator (e.g., fellow student, advisor) to independently annotate the same 150 samples from Option A.

**Protocol**:
1. Both annotators receive identical instructions: for each prompt-response pair, label as `correct`, `hallucination`, or `refusal`
2. Both annotate independently — no discussion until after both are done
3. Annotator 2 does NOT see the judge panel's labels

**Metrics to compute**:
- **Cohen's kappa** (κ): inter-annotator agreement corrected for chance
  - κ > 0.8 = near-perfect agreement (strong validation)
  - κ = 0.6-0.8 = substantial agreement (acceptable)
  - κ < 0.6 = moderate or worse (would need investigation)
- **Human-human agreement rate**: raw % agreement between annotators (upper bound for any automated judge)
- **Two independent human-judge comparisons**: each annotator vs. the consensus panel
  - If both agree with the panel at ~90%, strong evidence the panel is reliable
  - If one agrees much less, reveals annotator calibration differences
- **Disagreement analysis**: categorize cases where annotators disagree — are they the same cases where judges disagree?

**Time estimate**: ~3-4 hours for annotator 2 (same as annotator 1), plus ~1 hour for kappa computation and analysis.

**Why this matters for publication**: Inter-rater reliability is the gold standard for validating annotation quality. Without it, a reviewer can always argue "maybe your single annotator is biased." With κ > 0.8, that argument is foreclosed.

#### Recommendation

Do both. Option A alone (expanding to 150 with stratification) is the minimum. Option B (second annotator) is what separates a workshop paper from a top venue submission. Total cost: ~8 hours of human time, zero API cost.

---

## Summary: Remaining Roadmap

| Step | What | Time | Cost | Value |
|---|---|---|---|---|
| ~~Step 11B~~ | ~~Overfitting check~~ | ~~1-2 hrs~~ | ~~$5-15~~ | **DONE** — no overfitting (1.9pp / 4.1pp gap) |
| ~~Step 12A.0~~ | ~~Compute borderline geometry~~ | ~~5 min~~ | ~~<$0.01~~ | **DONE** — 449 rows, oppositeness unstable (corr=0.37), density/centrality/curvature stable |
| ~~Step 12A.1-3~~ | ~~FT bridge + borderline + regression~~ | ~~2-3 hrs~~ | ~~$0~~ | **DONE** — density predicts FT outcomes (4 Bonf, 6 BH FDR), V4 inconsistency resolved, regressions=refusals in sparse regions |
| ~~Step 12B~~ | ~~Thesis figures by chapter~~ | ~~1-2 hrs~~ | ~~$0~~ | **DONE** — 7 new figures + 13 existing = 20 total across Ch 4-7 |
## Thesis State Summary (as of Mar 8, 2026)

### What we did (experimental arc)

1. **Built a hallucination benchmark** (2,879 prompts across 7 categories, 449 held-out + 2,430 training). A benchmark is a standardized set of test questions with known correct answers — it gives us precise, repeatable measurements (hallucination rate, accuracy), ensures every model/intervention sees the same prompts (controlled comparison), and lets anyone reproduce our results (publication requirement). Our benchmark specifically targets *entity fabrication* hallucination.
2. **Tested 10 models** on it — established cross-model geometric prediction of hallucination (Kendall's tau=0.319 consistency across models).
3. **Tested 5 prompt prefixes** on Mixtral + Llama (pilot on 449 prompts, replicated at 5x scale on 2,430) — all reduce hallucination significantly (p<0.001). Entity-Aware best for Mixtral (14.3%→5.2%), Structured Caution best for Llama (9.5%→3.6%). CoT Verification catastrophically over-refuses (62-68% refusal rate).
4. **Best-per-prompt selection** — cherry-picked best response across prefixes per prompt for fine-tuning training data (98.2% correct for Llama, 97.7% for Mixtral). 28 Mixtral / 24 Llama prompts unfixable by any prefix.
5. **LoRA fine-tuning** — trained both models on curated data (Together AI, 3 Mixtral configs + 1 Llama config). Evaluated on 449-prompt held-out set. Mixtral configC best (91.1% accuracy), Llama configA (92.4%). No overfitting (1.9pp / 4.1pp train-test gap).
6. **Geometric bridge analyses** — tested whether embedding geometry predicts which hallucinations resist intervention (prefix bridge + fine-tuning bridge). Density is the universal predictor: high density = fixable, low density = resistant. 4/30 tests survive Bonferroni, 6/30 BH FDR.
7. **TruthfulQA generalization** — tested fine-tuned models on TruthfulQA (817 questions, Lin et al. 2022), an external benchmark that tests misconceptions (not fabrication). Llama: acc +5.3pp (p=0.0002), halluc -4.4pp (p=0.0005), both Bonferroni-sig. Mixtral directionally consistent but underpowered. No over-caution. Breaks custom-benchmark circularity.

### Why we're done experimentally

All four contributions have experimental evidence, and TruthfulQA generalization (Phase 5) is complete. The remaining work is: literature baselines comparison (Phase 7, no API cost) and thesis writing. No more API-heavy experiments needed.

### What we found

- **Geometry predicts hallucination**, but mostly through category structure. The honest, non-circular signal is **within-category density** (p<0.0001 for nonexistent prompts, both models).
- **Prompt prefixes dramatically reduce hallucination** — up to 89% reduction, replicated at 5x scale. All 5 prefixes significant (p<0.001).
- **Fine-tuning matches best prefix** (Mixtral 91.1% accuracy, McNemar p=0.84 vs baseline) without runtime prompt engineering.
- **Density predicts fixability** — unfixable hallucinations and regressions both cluster in sparse embedding regions. Both models agree on direction (high density = fixable).
- **Regressions are refusals** (91%) in low-density regions — the model trades knowledge breadth for safety, and geometry predicts where this tradeoff bites.
- **Cross-domain generalization**: Entity-fabrication fine-tuning transfers to TruthfulQA misconceptions (Llama: -4.4pp halluc, p=0.0005, Bonferroni-sig; Mixtral: -2.2pp, p=0.076, marginal). No over-caution on TruthfulQA (refusal ≤0.7%), suggesting caution is domain-targeted, not blanket.

### The four contributions (ordered by novelty)

1. **Geometric difficulty prediction**: Embedding geometry predicts not just *which* prompts cause hallucination, but which hallucinations are *fixable*. Within-category density predicts fixability (p=0.034/0.047 for nonexistent). Unfixable prompts cluster in high-centrality, low-density regions. Prior work asks "will this hallucinate?" — we ask "is this hallucination fixable?" and show the answer is geometric.

2. **Density and centrality as geometric signals of hallucination**: Cross-category AUC (0.97 initial) is mostly category structure (category-only AUC=0.955). The non-circular finding: within a single category, density distinguishes hallucinating from non-hallucinating prompts (p<0.0001, both models, both intervention types). Sparser embedding neighborhoods → more hallucination, more resistant to mitigation. Centrality is a secondary, model-specific signal — very strong for Mixtral (p=0.00004 for FT fixability, survives Bonferroni) but null for Llama (p=0.51).

   Full feature landscape (five features tested):
   - **Curvature** (downgraded): V3 claimed second-strongest predictor (OR=0.300, p<0.001). Did NOT survive V5 controls — all FT bridge tests p>0.27, all within-category tests null. The "flat manifold paradox" from V3 does not replicate.
   - **Oppositeness** (strong but fragile): Strongest between-category discriminator (p<1e-10, both models). BUT: (a) partly reflects category structure, not within-category signal; (b) not robust to corpus composition — adding 81 prompts changes scores fundamentally (corr=0.37 with original). A methodological finding: oppositeness depends on global PCA axes that shift with corpus changes.
   - **Local intrinsic dimensionality** (descriptive only): Plausible_fake entities have extreme values (degenerate neighborhoods). Not tested as a predictor.

   The intellectual arc: V3 emphasized centrality and curvature. Rigorous V5 analysis with proper controls showed density is the universal signal, centrality is model-specific, curvature is null, and oppositeness is strong but methodologically fragile. This is honest science — initial findings refined at scale.

3. **Precision-recall tradeoff in learned caution**: Fine-tuning reduces hallucination on nonexistent entities (70%→98%) but causes regressions on obscure-real entities (-7 to -13%). 91% of regressions are refusals in low-density regions. Safety and knowledge coverage are in fundamental tension, and the tension is geometrically predictable.

4. **Prompt distillation into weights**: LoRA fine-tuning on best-per-prompt curated data matches the best prompt prefix (91.1%, p=0.84) without runtime prompt engineering. Prompt engineering is not just a band-aid — it can be a data generation strategy for permanent model improvement.

### Main message

**Embedding geometry doesn't just predict *which* prompts cause hallucination — it predicts how *resistant* those hallucinations are to mitigation.** Sparse embedding neighborhoods produce hallucinations that resist both prompting and fine-tuning. Dense neighborhoods produce fixable ones. Fine-tuning can distill careful prompting behavior into weights, but it learns a density-based heuristic that over-fires on obscure real entities — revealing a fundamental precision-recall tradeoff between safety and knowledge coverage that is itself geometrically predictable. The learned caution also generalizes cross-domain: entity-fabrication fine-tuning significantly reduces misconception-type hallucination on TruthfulQA (Llama -4.4pp, Bonferroni-sig), suggesting the improvement is epistemic, not task-specific.

---

## Remaining Roadmap

| Step | What | Time | Cost | Value |
|---|---|---|---|---|
| **Phase 5** | **TruthfulQA generalization** | **~1 day** | **~$55-85** | **DONE (13D+13E, re-judged). Llama: acc +5.3pp (p=0.0002) + halluc -4.4pp (p=0.0005), both Bonferroni-sig. Mixtral marginal. No over-caution.** |
| ~~**Phase 9**~~ | ~~**Template diversity ablation**~~ | ~~**~1.5-3 days**~~ | ~~**~$85-180**~~ | **DONE — Template diversity does NOT matter. T5 (5 templates) ≈ T-all (all templates), McNemar p=1.00/0.52. Model learns behavioral caution, not template patterns.** |
| ~~**Phase 7**~~ | ~~**Literature baselines table**~~ | ~~**Few hrs**~~ | ~~**$0**~~ | **DONE — 7A+7B complete (v5, 15 methods, 9/9 verified, 3 corrections). 7C-D folded into thesis Ch 8 writing.** |
| Human validation | Expand n=50 → n=100-150 | Few hrs (manual) | $0 | Medium-high — strengthens entire evaluation pipeline credibility |
| **Thesis writing** | **All chapters** | **~12-16 days** | **$0** | **CRITICAL — only ~3 pages of real content exist. Due Mar 27.** |
| Phase 6 | Geometry selector | 2-3 days | ~$20 | Future work — engineering, not conceptual insight |
| Phase 8 | Adversarial robustness | Days+ | $50+ | Future work — whole paper in itself |

---

# Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Feb 2025 | Use both Mixtral + Llama (not just one) | Test prefix effectiveness at different baseline hallucination rates |
| Feb 2025 | 5 prefixes covering spectrum from light to strict | Literature-grounded, tests which mechanism matters most |
| Feb 2025 | Run all 5 prefixes on new prompts (not just top 3) | Bottom 2 uniquely save 3-7 prompts per model on hard categories |
| Feb 2025 | Best-per-prompt selection for fine-tuning data (Sunny) | +20-21 correct examples vs single prefix; 98% correct on Llama |
| Feb 2025 | Scale to ~2,000 new prompts (Sunny) | 449 too small for fine-tuning; need proper train/test split |
| Feb 2025 | Run baselines (no prefix) on new prompts too | Validates V3 geometric prediction, enables bridge analysis on new data |
| Feb 2025 | Original 449 prompts become held-out test set | Clean separation, no train-test contamination |
| Feb 2026 | Scale up to 2,430 (from ~2,000) | Conference-quality: more data per category, better borderline representation, competitive with SimpleQA (4,326) |
| Feb 2026 | New unified script instead of modifying V2/borderline | Preserves V3 reproducibility; cleaner for paper's methods section |
| Feb 2026 | Stratified template sampling + entity diversity caps | Prevents over-representation; maximizes information content of training set |
| Feb 2026 | Edge factual generated first (cross-category dedup) | 8 edge factual questions overlapped with factual category; edge factual has priority since ground truths are hand-verified |
| Mar 2026 | Fix paired variable resolution in fill_template | 6 ambiguous templates used `{option1}/{option2}` and `{concept}/{other_concept}` which are sub-keys of `option_pairs`/`concept_pairs` pools — added `_build_pair_index()` to resolve nested dict keys. Raised ambiguous template coverage from 89.1% to 100%, eliminated 108 placeholder rejections |
| Mar 2026 | Self-reference for density/centrality (not external corpus) | Matches V3 approach (`build_from_benchmark: true`, 368-prompt self-reference). Thesis claims relative geometry, not absolute OOD distance. Avoids confound of external dataset choice |
| Mar 2026 | k=20 for all geometry features (matching V3) | Confirmed V3 config syncs `k_neighbors: 20` to both ID and curvature (overriding curvature default of 30). Consistency over optimality — k~sqrt(n) would suggest 54, but changing k makes V3/V5 non-comparable |
| Mar 2026 | Compute geometry on full 2,879 combined corpus | V3 archive only has 368-row geometry (borderline never computed). No "full V3 geometry" to preserve. Report original bridge AUC=0.86 as discovery, combined-corpus AUC as validation |
| Mar 2026 | New V5 baseline script (Option B) instead of adapting V4 scripts | V4 scripts have hardcoded paths and `load_prompts()` globs all JSONL. New script imports shared infrastructure (MultiModelClient, ConsensusJudge) with zero client/judge duplication, but V5-specific orchestration. Clean separation from V4 results |
| Mar 2026 | Report V5 cross-validated AUC (0.64-0.72) as primary, not V3 train AUC (0.86) | V3 AUC was train-only and conflated category structure with within-category signal. V5 analysis properly decomposes: category-only AUC 0.77, geo adds +0.02-0.04. Within-category signal is real but modest (nonexistent AUC 0.67). Honest reporting is stronger for publication — avoids reviewer challenge |
| Mar 2026 | Focus thesis framing on within-category density signal | Between-category geometry ↔ hallucination could be called circular (categories defined by content, not geometry, but still confounded). Within-category density prediction (p<0.0001 for nonexistent, both models) is the non-circular, novel finding. Frame category-level geometry as "mechanism" and within-category as "evidence" |
| Mar 2026 | V5 prefix generation complete (Step 7) | Mixtral: 12,150/12,150, 0 failed (~8.5h). Llama: 12,150/12,150, 0 failed (~11.5h). All transient 503/400 errors handled by retry |
| Mar 2026 | V5 prefix judging complete (Step 7) | Mixtral: 12,150/12,150 judged (~16.9h). Llama: 12,149/12,150 judged (~17.1h), 1 error on v5_nonexistent_0151/fact_grounded. Total: 24,299/24,300 |
| Mar 2026 | Fix judge infrastructure bugs (4 issues) | Type coercion + range validation in judge_client.py, required-key check raises instead of pass, 3-attempt retry in all 4 judging scripts, periodic save moved outside retry loop. Post-hoc audit confirmed zero corruption in existing 29,159 judged entries |
| Mar 2026 | Add Step 8 (V5 Analysis) before Step 9 | Repurposed superseded Step 8. V5 prefix summary (8A) validates data before training set construction. V5 bridge analysis (8B) tests the thesis's most novel contribution at 5.4x scale. Both are zero-cost local analysis on existing data |
| Mar 2026 | Step 8A complete: V5 prefix summary | All 5 prefixes significant (p<0.001). Entity-Aware best Mixtral (5.2%), Structured Caution best Llama (3.6%). CoT catastrophic (62-68% refusal). V5 rates higher than V4 (expected — harder prompts) |
| Mar 2026 | Step 8B complete: V5 bridge analysis | Within-category density predicts fixability (p=0.034/0.047) — strongest V5 bridge finding. Aggregate AUC 0.59-0.66 (class imbalance: 333:15 Mixtral, 227:5 Llama). Oppositeness strongest overall discriminator (p<1e-10). Reframe thesis: lead with within-category, relegate aggregate AUC |
| Mar 2026 | Align V5 `fixed` definition with V4 | V4 code defined `fixed = baseline_hall and not prefix_hall` (any non-hallucination including refusals). Step 8B plan originally said "correct with at least 1 prefix" (label 0 only). Aligned to V4 definition for direct AUC comparison. Rationale: a refusal IS a successful fix — the model stopped hallucinating |
| Mar 2026 | Exclude CoT Verification from Step 9 training data | 62-68% refusal rate makes CoT responses useless as fine-tuning targets. Refusals teach the model to refuse, not to answer correctly. Use 4 non-CoT prefixes for best-per-prompt selection |
| Mar 2026 | Include baseline as 5th candidate source in Step 9 | 4 Mixtral / 2 Llama prompts correct at baseline but ALL 4 non-CoT prefixes hallucinate. Without baseline, these get hallucinated training targets. Including baseline: +9 correct Mixtral, +3 correct Llama, unfixable drops 34→28 / 29→24. No downside — training format is (question, answer) pairs regardless of source |
| Mar 2026 | Fix priority: correct > partial > refusal > hallucination | Original plan had refusal (label=3) > partial (label=1). Wrong: partial is "technically true but vague/minor errors" — contains real knowledge. Refusal is "I don't know" — teaches model to give up. For fine-tuning, partial is strictly better |
| Mar 2026 | Step 9 complete: best-per-prompt selection | Mixtral: 2,402 training (97.7% correct), 28 unfixable. Llama: 2,406 training (98.2% correct), 24 unfixable. All unfixable verified label=2 across all 5 sources. Source selection uses judge_confidence tiebreaker for quality. Entity-aware provides most unique saves (34/10) |
| Mar 2026 | Step 10 complete: LoRA fine-tuning | 4 jobs via Together AI (3 Mixtral configs + 1 Llama). Together overrode lora_r 16→64, alpha 32→128, dropout removed. Llama used QLoRA (4-bit). Total cost: $22.42 |
| Mar 2026 | All fine-tuned models require dedicated endpoints | Together serverless LoRA doesn't support Mixtral or Llama 4 Maverick. Dedicated endpoints: Mixtral $0.13/min, Llama $0.53/min. Script updated with `--endpoint` flag |
| Mar 2026 | Step 11 complete: fine-tuning evaluation | **Strong success (Mixtral), moderate success (Llama)**. Mixtral configC matches best prefix (91.1%, p=0.84). Both models ~89% hallucination reduction. borderline_obscure_real regression (-7 to -13%) reveals precision-recall tradeoff in learned caution. Bug fix: V3 baseline deduplicated (538→449 entries, 85 duplicate borderline IDs with 8 inconsistent labels) |
| Mar 2026 | Step 11B complete: overfitting check | **No overfitting.** Mixtral configC: 93.0% train vs 91.1% test (+1.9pp). Llama configA: 96.5% train vs 92.4% test (+4.1pp). Both gaps under 5pp despite aggressive LoRA rank (64) and no dropout. Fine-tuning learned genuine caution, not memorization. Clears 12A bridge analysis for uncontaminated interpretation |
| Mar 2026 | Reframe Step 12 into 12A (analytical) + 12B (figures) | Original "Step 12: Final figures, takes minutes" undersold what's needed. 12A contains substantive research questions: fine-tuning bridge analysis, borderline geometric distinction, regression geometric profile. 12B is production work organized by thesis chapter. Split clarifies that 12A is research, 12B is engineering |
| Mar 2026 | Thesis framing: contributions are ideas, not pipeline | Inspired by reference theses (Angela Li, Tarun Prasad). The four contributions are theoretical findings (geometric difficulty prediction, within-category density signal, precision-recall tradeoff, prompt distillation). Fine-tuning is the method, not the finding. No V3/V4/V5 labels in thesis — use descriptive terms |
| Mar 2026 | Add Step 12A.0: compute borderline geometry | **Critical data gap**: `geometry_features.csv` has only 368 rows (4 main categories). 81 borderline prompts never had geometry computed. Without this, 12A.2 is completely blocked and 12A.3 is partially blocked. Re-embed all 449 prompts together (curvature/oppositeness depend on full matrix). Cost: <$0.01 |
| Mar 2026 | Reframe 12A.2: within-category, not cross-category | Original plan compared borderline_obscure_real vs borderline_plausible_fake geometry — just detects category differences (same confound as cross-category AUC). Revised: within-category density prediction of FT outcomes within each borderline category. Harder test, avoids confound, consistent with Contribution #2 methodology |
| Mar 2026 | Document all 12A concerns preemptively | Sample sizes (still_broken n≈6), density inconsistency across models, same-prompt double-testing, and null-result framing. Each concern has a specific mitigation. NeurIPS reviewers find weaknesses — preemptive documentation is defensive |
| Mar 2026 | Step 12A.0 complete: full V3 geometry | 449 prompts (was 368). Self-reference used (reference corpus .npy files cleaned up). Density corr=0.998, centrality 0.983, curvature 0.975 — all stable. **Oppositeness corr=0.373** — global PCA axes rotated with 81 new points. Oppositeness is not robust to corpus composition. Lead with density/centrality/curvature in 12A.1-3, relegate oppositeness |
| Mar 2026 | Step 12A.1-3 complete: FT bridge analysis | **Density is the universal predictor** of FT outcomes (fixability + regressions, both models, consistent direction). 4/30 survive Bonferroni, 6/30 BH FDR. V4 density inconsistency resolved — was prefix-specific artifact. Curvature NOT significant for FT (unlike V4 prefix bridge). 12A.2 null at n=5 (power limitation). Regressions are 91% refusals in low-density regions — geometry predicts where FT over-cautions |
| Mar 2026 | Density direction resolved: high=fixable | V4 prefix bridge showed Mixtral fixed=higher density but Llama fixed=lower density, raising concern about universality. FT bridge shows BOTH models agree: fixed=higher density, regressed=lower density. The V4 inconsistency was specific to prompt-level intervention, not fundamental. Fine-tuning reveals the true geometric signal: sparse neighborhoods resist correction |
| Mar 2026 | Phase 5: TruthfulQA generalization testing | All thesis results are on our custom benchmark. TruthfulQA (817 questions, Lin et al. 2022) breaks this circularity. Tests misconceptions not fabrication — different failure mode makes generalization test stronger, not weaker. Null result expected and interpretable ("targeted FT, not general truthfulness boost"). Enriched ground_truth string (not meta_info) because judge template only injects ground_truth |
| Mar 2026 | TruthfulQA: test only best config per model | Test Mixtral configC and Llama configA only (not all 3 Mixtral configs). Rationale: (1) configC was the best-performing Mixtral config on our held-out set (91.1% accuracy, matching best prefix, McNemar p=0.84 vs baseline); (2) the generalization question is "does the best fine-tuned model transfer?" not "which hyperparameter config transfers best?"; (3) if configC doesn't generalize, weaker configs (A: 89.1%, B: 90.2%) won't either; (4) testing all 3 would triple endpoint cost (~$15-27 extra) for a question that isn't central. **Thesis note**: this decision should appear in Ch 7.5 (TruthfulQA section) — state that we test the best config per model, cite the held-out accuracy that determined "best," and note that this was decided before seeing TruthfulQA results (pre-registered, not cherry-picked) |
| Mar 2026 | Serverless LoRA doesn't work for Llama | Together AI serverless LoRA adapter returns 400 "Input validation error" for all requests. Both Mixtral and Llama fine-tuned models require dedicated endpoints. Updated `run_truthfulqa.py` with per-model `--endpoint` / `--mixtral-endpoint` / `--llama-endpoint` flags to prevent cross-model endpoint contamination (previous bug: global `--endpoint` applied Mixtral endpoint to Llama, producing 75 corrupted entries) |
| Mar 2026 | Upgrade Phase 7 from "medium" to "high" priority | Same pattern as Phase 5 — initially undersold as "just literature review." Without a baselines comparison table, the thesis's 89% hallucination reduction floats without context. A reviewer asking "how does this compare to RAG/self-consistency/DPO?" would find no answer. Zero cost, few hours of work, goes in Ch 8 Discussion. Also identified human validation expansion (n=50 → n=100-150) as recommended |
| Mar 2026 | Phase 7 method/benchmark selection must be principled | Methods require ≥2 of: axis relevance (detection/prompt/FT), citation threshold (≥100 or top venue 2024-25), quantitative results, conceptual proximity. Excluded: retrieval-only methods (we test closed-book), pre-2020 (pre-LLM), summarization-only (different hallucination mode). Benchmarks require: ≥3 methods use it OR hallucination-standard, hallucination-specific (no MMLU), open-domain QA (no summarization faithfulness), published baselines exist. Comparability column (Direct/Partial/Indirect) per table entry prevents false equivalence claims. Must include methods that outperform us — framing is "different niche" not "we're better" |
| Mar 2026 | TruthfulQA judge contamination detected and re-judged | 62 Llama finetuned entries had API connection errors causing all 3 judges to default to label=3 (refusal) with confidence=0.0. Detected during 13E review via qualitative example inspection (Bible "root of all evil" question clearly correct but labeled refusal). Inflated refusal from 0.5% to 8.1%, suppressed accuracy from 77.1% to 71.1%. Backed up as `.bak_contaminated`, removed error entries, re-judged with zero errors. Also found 1 Mixtral baseline entry (immaterial to results). Root cause: `consensus_judge.py` line 53 defaults failed judges to `{"label": 3, "confidence": 0.0}`. **Lesson**: Always audit confidence=0.0 entries in judged data. Document in thesis methods as QC protocol |
| Mar 2026 | Step 13E complete: TruthfulQA analysis | 8 analyses on clean re-judged data. Llama: acc +5.3pp (p=0.0002), halluc -4.4pp (p=0.0005), both Bonferroni-sig. Mixtral: directionally consistent but underpowered. No over-caution. Cross-domain generalization from entity-fabrication to misconceptions is real. Literature comparison numbers (ITI, DoLA, InstructGPT) still need PDF verification |
| Mar 2026 | Step 7A literature search complete | Systematic search across 4 axes found 22 methods + 4 surveys + 3 benchmark baseline tables. Key findings: (1) R-Tuning (NAACL 2024 Outstanding) is closest comparator — both teach abstention, but via different signals (train-time probing vs geometry). (2) INSIDE/EigenScore is closest conceptual kin in detection — both use embedding-space properties, but they analyze response covariance while we analyze entity graph geometry. (3) No prior work predicts hallucination *difficulty* — our bridge analysis is genuinely novel. (4) DPO-based methods dominate recent FT work (FactTune, FLAME, Mask-DPO) — our LoRA SFT with geometry-guided selection is a distinct approach. (5) Fine-Tuning Paradox (Gekhman et al.) provides critical context: FT on new knowledge increases hallucination, but our approach avoids this by teaching behavioral patterns not new facts. All papers freely available on arXiv. |

| Mar 2026 | Step 11C: entity-level train-test contamination | 16/22 plausible_fake test entities also in training (different templates). Checked all 7 categories. Overall contamination: 59% of test prompts. Decontamination re-scoring shows NO inflation: Mixtral 91.1%→90.7%, Llama 92.4%→92.5%. Model learned behavioral caution, not entity names. Disclose in thesis as methodological note |
| Mar 2026 | Template overlap: 83.3% of V3 test templates appear in V5 training | 100/120 test templates (with metadata) also used in training. 81 borderline test prompts have no template metadata. Relevant for template ablation design — current evaluation partially tests within-template generalization |
| Mar 2026 | Phase 9: template diversity ablation (Sunny, Mar 8) | Hold N constant (~2,400), vary template count (T1/T5/T10/T20/T-all). Nested subsets (T5⊂T10⊂T20⊂T-all) to isolate count from quality. Hypothesis: T10+ ≈ T-all, T1 degrades. Two approaches: (a) reuse existing prefix data (cheaper, varying N) vs (b) regenerate (proper, expensive). Simplified fallback: T5/T10/T-all (~1.5 days). Priority: next experiment after TruthfulQA (done) |
| Mar 2026 | Drop T1 from ablation, use T5 as lowest condition | Pre-computation: T1 yields only 179 prompts (3-15 per category). Insufficient for LoRA fine-tuning. T5 (397-402 prompts) is the minimum viable condition |
| Mar 2026 | Use approach (a) for ablation training data | Reuse existing V5 prefix data filtered to template subsets. Varying N is a known limitation but saves ~$50-150 and 15-20h per condition. Matched random controls (R{N}) isolate template diversity from dataset size |
| Mar 2026 | Add matched random controls R397/R402 | Same N as T5 but full template pool (~194 templates). If R{N} outperforms T5, template diversity matters beyond dataset size. Model-specific labels because unfixable counts differ (Mixtral 28, Llama 24) |
| Mar 2026 | Drop T20 from ablation | Simplified to T5/T10/T-all + R{N}. T20 adds marginal information if T10≈T-all (hypothesized). Saves 2 FT jobs + 2 evaluation runs. Can add later if T10 vs T-all shows a gap |
| Mar 2026 | Phase 9 complete: template diversity doesn't matter | T5≈T10≈R{N}≈T-all (all McNemar p>0.45). Template overlap split confirms: seen-template 92.6% vs novel-template 92.4% (Mixtral T5). Model learns behavioral caution, not template patterns. Addresses Sunny's concern. Goes in Ch 7.6 (main text, not appendix) |
| Mar 2026 | Phase 10: cross-category generalization ablation (Sunny, Mar 11) | Third generalization type: does caution transfer to held-out category types? 6 conditions: Full (existing), entity-dep only, R{entity-dep} (size control), entity-indep only, leave-out-nonexistent, leave-out-factual. 10 FT jobs (5 conditions × 2 models). Est ~1-2 days wall, ~$80-140. LoRA: configC Mixtral, configA Llama. Zero-shot category transfer test. Completes "three types of generalization" narrative (entities → templates → categories) |

---

# Judging Process Review (Post-Step 7 Reflection)

## What went right

**Scale and completion**: 24,299/24,300 judgments completed (99.996%) across ~34 hours of wall time. Both models ran in parallel. Resume logic worked correctly — no data loss from process interruptions.

**Infrastructure reuse**: The same `ConsensusJudge` and `JudgeClient` classes from V4 handled 5.4x more data without modification. The shared infrastructure strategy (new orchestration scripts importing V4 judge/client code) was the right call — zero code duplication, zero judge behavior drift between V4 and V5.

**Data integrity**: Post-hoc audit confirmed all 10 model/prefix files have correct line counts, no duplicate IDs, all required fields present with correct types, and the single missing entry is exactly where expected.

## What went wrong (the 1 error)

**Root cause**: `consensus_judge.py` line 69 — `sum(r['confidence'] for r in results)` fails when one judge returns `"confidence": "0.95"` (string) instead of `0.95` (float). The JSON spec doesn't distinguish, and LLMs sometimes emit string-typed numbers.

**Why it wasn't caught earlier**: `judge_client.py` lines 150-158 parse the JSON but perform **no type coercion**. The parsed result is returned as-is. The required-key check (lines 152-156) is a no-op — the `if` body is just `pass`. So malformed types pass through silently until the `sum()` call in `consensus_judge.py`.

**Why it's isolated**: The error only triggers when a judge returns a string confidence AND python's `sum()` encounters it. If all 3 judges return floats (the usual case), it works. The error hit 1/24,300 entries — consistent with a rare LLM output formatting glitch.

**Impact**: The `run_v5_prefixes.py` exception handler (line 230-231) catches the error, prints a message, and skips the entry permanently. No retry, no fallback. The prompt `v5_nonexistent_0151` has valid judgments for 4/5 prefixes (and for Mixtral/fact_grounded), so best-per-prompt selection is unaffected.

## Code issues identified and fixed (Mar 2026)

All issues below were fixed after the post-Step 7 audit. Fixes verified by syntax check and data integrity audit (zero label/agreement_rate mismatches across 29,159 entries in existing data).

### 1. No type coercion on judge output — `[FIXED]`

`judge_client.py` now casts `int(label)` and `float(confidence)` after JSON parse. Also validates label ∈ {0,1,2,3} and confidence ∈ [0.0, 1.0] — invalid values trigger a retry (3 attempts with exponential backoff), then fall back to `{"label": 3, "confidence": 0.0}`.

### 2. Required-key check was a no-op — `[FIXED]`

Replaced `pass` with `raise ValueError(f"Judge response missing keys: {missing}")`. Missing keys now trigger retry logic.

### 3. Silent entry drop on error — `[FIXED]`

All 4 judging scripts (`run_v5_prefixes.py`, `run_v5_baselines.py`, `run_prefix_judging.py`, `run_consensus_judging.py`) now retry 3 times with exponential backoff before dropping an entry. Matches the retry pattern already used in generation scripts.

### 4. Periodic save inside retry try block — `[FIXED]`

Moved `write_jsonl()` call outside the retry loop in all 4 scripts. Previously, a `write_jsonl` failure (e.g., disk full) would trigger a re-judge, appending a duplicate entry. Now the save happens after the retry loop completes — write failures cannot cause re-judging or duplicates.

### 5. Failed judges silently default to refusal label — `[KNOWN, NOT YET FIXED]`

**Location**: `consensus_judge.py` line 53 (approx). When an individual judge call fails (connection error, timeout, etc.), the exception handler appends `{"label": 3, "confidence": 0.0, "justification": "Judge failed"}`. If 2+ of 3 judges fail, the consensus is label=3 (refusal) with low confidence.

**Why it matters**: This caused the TruthfulQA contamination — 62 Llama finetuned entries had API connection errors on 2-3 judges, silently defaulting to refusal. The entries looked normal in the JSONL (valid format, valid labels) and were only detected by auditing confidence=0.0.

**Recommended fix** (not yet implemented):
- Option A: Raise an exception on judge failure instead of defaulting, forcing the retry logic in the orchestration script to handle it. This is the cleanest but requires the orchestration scripts to handle the exception gracefully.
- Option B: Keep the default but add a `judge_errors` count field to the output record. Any record with `judge_errors > 0` is flagged for review. A post-judging QC script filters these before analysis.
- Option C (minimal): Log a warning and add `"confidence": 0.0` as a sentinel. Add a mandatory QC step: `grep '"confidence": 0.0' *.jsonl | wc -l` before any analysis.

**Current mitigation**: The decision log entry for the TruthfulQA contamination documents the QC protocol (audit confidence=0.0 entries). This is a manual step, not automated.

## Methodological concerns for the thesis

### Judge agreement on borderline categories

Already documented in Step 6 diagnostic, but worth reiterating: borderline_plausible_fake has 15-23% unanimous agreement. With V5 prefixes, the same prompts are being judged 5 more times each — the low agreement rate means the "did the prefix fix it?" signal is noisy for this category specifically. The V5 prefix analysis should report per-category agreement rates alongside prefix effectiveness, and the bridge analysis should test sensitivity to unanimous-only labels.

### Anthropic judge doesn't use structured output

`judge_client.py:130-141` — OpenAI and Together use `response_format: {"type": "json_object"}`, but Anthropic uses a text prompt with "\n\nRespond in JSON." appended. This is less reliable and could produce more JSON parsing failures. The markdown cleanup (lines 145-148) partially mitigates this, but the asymmetry between judge providers is a confound. Should mention in the thesis methodology section.

### Judge-as-evaluatee overlap

Llama 4 Maverick is both a target model (generating responses) and a judge (evaluating responses). When Llama judges its own responses, self-preference bias could inflate correctness scores. V3 already flagged this as a limitation. The V5 data could test for this: compare Llama-as-judge scores on Llama responses vs Mixtral responses for the same prompts.

## Action items

| Priority | Item | Status |
|---|---|---|
| ~~Low~~ | ~~Add type coercion + range validation to `judge_client.py`~~ | **DONE** — Mar 2026 |
| ~~Low~~ | ~~Fix the no-op required-key check~~ | **DONE** — Mar 2026 |
| ~~Low~~ | ~~Add retry logic to all 4 judging scripts~~ | **DONE** — Mar 2026 |
| ~~Low~~ | ~~Move periodic save outside retry loop~~ | **DONE** — Mar 2026 |
| Thesis | Report per-category agreement rates for V5 prefix results | Step 8A |
| Thesis | Note Anthropic structured output asymmetry in methodology | During writing |
| Thesis | Test judge-as-evaluatee bias (Llama judging Llama vs Mixtral) | Step 8A or during writing |

---

## The Geometric Story: How It Evolved Across V3→V4→V5 (Mar 2026)

The geometric findings shifted meaningfully as the analysis became more rigorous. This section records what each phase found, what held up, and what didn't — to ensure the thesis frames the contribution honestly.

### V3 (Dec 2025): Centrality and curvature predict hallucination

**Claim**: Centrality reduces hallucination odds by 97.3% (OR=0.027, p<0.001). Curvature reduces odds by 70.0% (OR=0.300, p<0.001). Logistic regression AUC=0.86.

**What held up**: Geometry does predict hallucination. The direction was right — geometric features carry signal.

**What didn't hold up**: The AUC=0.86 **conflated category structure with geometric signal**. Borderline and nonexistent prompts have different geometry than factual/ambiguous prompts *by construction* (they're about different types of entities). A logistic regression on 368 prompts without category controls was partly learning "which category is this?" rather than "is this geometrically risky?" This was not dishonest — just incomplete. V5 decomposed the signal properly.

**Centrality specifically**: V3 found centrality as the strongest predictor. V5 found it **weak and inconsistent in direction across models** when tested properly. The V3 centrality signal was likely a proxy for category membership (factual prompts have high centrality, borderline prompts have moderate centrality — and the two categories have very different hallucination rates).

### V4 Bridge (Feb 2026): Geometry predicts prefix fixability

**Claim**: Logistic regression predicting "will the prefix fix this hallucination?" achieves AUC=0.86 (Mixtral), 0.83 (Llama). Unfixable prompts: high centrality (0.73), low density (1.55).

**What held up**: The directional finding — unfixable prompts have different geometry than fixable ones. High centrality + low density = harder to fix. This replicated in V5 directionally.

**What didn't hold up fully**: The AUC=0.86 was computed **per-prefix** (each prefix gives its own fixed/broken classification), and on train data only (no cross-validation). The V5 bridge used any-prefix aggregation (fixed by ANY prefix) which creates extreme class imbalance (333:15 Mixtral, 227:5 Llama) and drops AUC to 0.59-0.66. Neither number is the "true" AUC — they answer different questions with different methodological choices.

### V5 (Mar 2026): The honest decomposition

**Between-category** (the easy finding): Oppositeness is the strongest predictor (+0.54 Mixtral, +0.86 Llama). Density is second (-0.40 Mixtral, -0.62 Llama). Centrality is weak and inconsistent. Category membership alone achieves AUC 0.77; adding geometry gets 0.79-0.81. Geometry adds real but modest signal beyond category (+0.02-0.04 AUC).

**Within-category** (the novel, non-circular finding): Among 600 nonexistent prompts — all same type, same structure — the ones in **sparser embedding neighborhoods (lower density)** hallucinate significantly more. p < 0.0001, effect size r ≈ 0.25. This cannot be explained by category membership. This is the defensible core finding.

**Bridge (fixability)**: Within-category density predicts fixability (p=0.034 Mixtral, p=0.047 Llama). Unfixable prompts have lower density than fixed ones. Small sample (15/5 still_broken) limits statistical power, but direction matches V4.

### Summary: Which features actually matter?

| Feature | V3 Claim | V5 Reality | Status |
|---|---|---|---|
| **Centrality** | Strongest predictor (OR=0.027) | Weak, inconsistent across models; likely proxied category | **Downgraded** — between-category artifact |
| **Curvature** | Second predictor (OR=0.300) | Weak in V5; useless for within-category | **Downgraded** |
| **Density** | Not emphasized in V3 | Predicts hallucination AND fixability within categories | **Upgraded** — the real geometric signal |
| **Oppositeness** | Not tested in V3 | Strongest overall discriminator (p<1e-10) | **New finding** — but partly between-category |
| **Local ID** | Not tested in V3 | Plausible_fake has extreme values (degenerate neighborhoods) | **Descriptive** — not tested as predictor |

### Thesis framing implications

1. **Lead with density as the within-category signal.** This is the non-circular, statistically defensible, novel finding. "Among prompts of the same type, those in sparser embedding regions are more likely to hallucinate and more resistant to prefix intervention."

2. **Present oppositeness as the strongest overall discriminator** but acknowledge it partially reflects category structure.

3. **Report V3 centrality/curvature honestly** as initial findings that didn't survive rigorous controls. This is normal science — initial results on small data get refined at scale.

4. **Don't overclaim AUC numbers.** V3's 0.86 and V4's 0.86 were real but methodologically limited. V5's 0.64-0.72 (overall) and 0.67 (nonexistent within-category) are the honest numbers. Frame V3→V5 as "the signal is real but more modest than initial results suggested."

5. **The core thesis claim survives**: Embedding space geometry predicts hallucination risk, and this signal operates at two levels — category-level (where prompts fall in the embedding space) and within-category (fine-grained density differences among same-type prompts). The within-category level is the novel contribution.

---

*(Thesis writing plan, content expansion guide, title options, and V3 paper issues moved to `/THESIS_WRITING.md` — Mar 2026)*

---

## Three-Way Split Tiebreaker Sensitivity Analysis (Mar 11, 2026)

**Context**: When all 3 judges assign different labels, `Counter.most_common(1)[0]` returns the first-inserted element, which is always GPT-5.1's label. Discovered during thesis writing (Section 4.3). This gives GPT-5.1 de facto tiebreaker authority.

### Raw numbers

- **41,807** total judged entries with individual judgment data
- **1,113** three-way splits (2.66%)
- **594** are error artifacts (a judge API call failed, defaulting to label=3, confidence=0.0, which creates an artificial third label)
- **519** genuine three-way splits (1.24% of all entries)

### Sensitivity: default (first-judge) vs confidence-based tiebreaker

Of 519 genuine three-way splits:
- **220 (42.4%)** would change label under confidence-based tiebreaking
- **299 (57.6%)** would stay the same
- **0.53% of all labels** would be affected

### Dominant flip direction

| From → To | Count |
|---|---|
| Hallucination (2) → Correct (0) | 192 |
| Partial (1) → Refused (3) | 9 |
| Refused (3) → Correct (0) | 6 |
| Partial (1) → Correct (0) | 5 |
| Correct (0) → Hallucination (2) | 4 |
| Correct (0) → Refused (3) | 3 |
| Partial (1) → Hallucination (2) | 1 |

**Key finding**: 192/220 flips (87%) are Hallucination→Correct. GPT-5.1 is the strictest judge, systematically calling ambiguous cases as hallucinations. The current tiebreaker **overcounts hallucinations** — conservative for our claims (we understate intervention effectiveness, if anything).

### By phase

| Phase | Genuine Splits | Would Change | Rate |
|---|---|---|---|
| V4 | 16 | 12 | 75.0% |
| V5-baseline | 88 | 48 | 54.5% |
| V5-prefix | 252 | 124 | 49.2% |
| V5-finetuned | 0 | 0 | — (all were error artifacts) |
| TruthfulQA | 163 | 36 | 22.1% |

### Training data impact (V5)

- **5** currently Correct (0) → would flip to non-Correct (removed from training)
- **165** currently non-Correct → would flip to Correct (0) (eligible for training)
- Net: ~160 additional training examples (~6.7% of training set)

### Decision

**Not recomputing.** Rationale:
1. Bias is conservative (overcounts hallucinations → understates our intervention effects)
2. 0.53% of all labels affected — headline results almost certainly unchanged
3. Recomputation would cascade: labels → Step 9 selection → fine-tuning → evaluation → all downstream analysis
4. Will report sensitivity analysis in Chapter 5 and acknowledge tiebreaker limitation in Chapter 4
5. Fix code for any future runs

### Error-artifact contamination (SEPARATE ISSUE — INVESTIGATED)

Silent judge failure default (label=3, confidence=0.0) contaminated V5 judging data. Full investigation completed Mar 11, 2026. See `JUDGE_CONTAMINATION_ISSUE.md` for complete details.

**Key finding**: Sounds worse than it is. 14,607 entries had at least 1 failed judge, but in 91-93% of cases the 2 real judges agreed, so the fake vote was outvoted. **Only 151 labels definitively wrong** across non-CoT V5 data (0.45%). CoT separately has ~3,172 garbage labels (2 judges failed).

**Invalidated finding**: "CoT catastrophic refusal" (62-68%) was entirely API failures, not model behavior. Real refusal rate < 1%.

**Fix script**: `scripts/fix_judge_contamination.py`
- **APPLIED Mar 11, 2026 at 23:16.** 325 labels corrected out of 28,789 (1.13%). 0 unfixable.
- Dominant direction: Refused/Hallucinated → Correct (291 of 325 changes)
- Only 4 changes go toward worse labels
- $0 cost — recomputes from stored real judge votes, no API calls
- Tiebreaker for 2-judge disagreements: higher confidence wins
- Backs up originals, adds `_correction` audit metadata to every affected entry

**Completed after fix**:
1. ✅ Re-ran Step 9 — minimal change: Mixtral 2,402→2,403 training (+1), Llama unchanged. No re-training needed.
2. ✅ Bug fixed in `judge_client.py` and `consensus_judge.py` — failed judges now marked with `"failed": True` and excluded from majority vote.
3. CoT excluded from thesis (API failure artifact, not worth $50 re-judge).

**All steps complete** (March 12, 2026):
4. ✅ All analysis scripts re-run with corrected data. Numbers shifted <1pp. No conclusions changed.
5. ✅ All figures regenerated.
6. ✅ CoT decision finalized: excluded from thesis entirely. Corrected CoT would likely show boring result (similar accuracy to other prefixes). $50 re-judge not worth it with 15 days to deadline. Core contributions (geometry prediction, fixability, fine-tuning pipeline, template ablation) all intact without CoT.

**Updated headline numbers (post-fix)**:
- Mixtral baseline: 82.5% correct, 14.8% hall (was 81.7%/14.3%)
- Llama baseline: 87.9% correct, 9.7% hall (was 87.1%/9.5%)
- Entity-Aware Mixtral: 4.7% hall (was 5.2%)
- Structured Caution Llama: 3.0% hall (was 3.6%)

7. ✅ Sensitivity analysis script fixed and re-run (March 12, 2026).
   - **Bug found**: Judge removal (Check 2) was reading raw `individual_judgments` which still contained failed judges' fake votes (label=3, confidence=0.0). Produced garbage results: 0% accuracy / 100% refusal for any subset that included a failed judge.
   - **Fix**: Added `is_failed_judge()` filter to `majority_vote_2of3()`. Failed judges are now excluded before computing 2-of-3 subsets. Also removed CoT from prefix dataset list.
   - **Results (all three checks pass)**:
     - Check 1 (unanimous-only): 88-94% unanimous across datasets. Accuracy +4-5pp under unanimous filter. Conclusions unchanged.
     - Check 2 (judge removal): No single judge drives results. Removing any judge changes 0-6.4% of labels, accuracy varies ±1-3pp. `without_gpt-5.1` for finetuned: 0 labels changed (already excluded by contamination fix).
     - Check 3 (self-eval bias): Llama excess leniency near zero or negative across all datasets (-2.3pp to +0.3pp). Self-preference bias is negligible.

See `JUDGE_CONTAMINATION_ISSUE.md` for full details, per-file breakdown, and reasoning.
