# Boaz Meeting Prep: Everything After V3

## What Boaz Knows (V3, the class project)
Geometric features of prompt embeddings predict hallucination across 10 models. AUC = 0.86. This was the CS2881 class project.

## What Happened After V3

### 1. Boaz's Suggestion: Prompt Distillation into Fine-Tuning
Boaz suggested (before mid-December 2025) the idea of distilling prompt-level behavior into model weights. This became the third contribution of the thesis. He also required a PhD co-advisor — connected with **Sunny Qin** (advised by Sham Kakade & David Alvarez-Melis).

### 2. Sunny's Guidance (Feb 2026)
- Don't pick one best prompt prefix — use **best-per-prompt selection** across all prefixes
- Scale from 449 to 2,000-3,000+ prompts; hold the original 449 as test set
- The evaluation pipeline itself is a contribution

### 3. V4: Pilot Prompt Experiment (449 prompts, 5 prefixes)
Tested 5 system-prompt interventions on the original 449 prompts:
- **Entity-Aware**: best for Mixtral (hallucination: 11.8% → 1.34%)
- **Structured Caution**: best for Llama (5.8% → 1.34%)
- CoT Verification also tested but later **invalidated** (API failure artifact — see below)
- All four surviving prefixes significantly reduced hallucination while maintaining accuracy

### 4. V5: Scaled Benchmark (2,430 prompts, 7 categories)
Generated 2,430 new prompts across 7 categories (up from 4). V3's 449 held out as test set.

**Baselines** (no prefix): Mixtral 82.5% correct / 14.8% hallucination. Llama 87.9% / 9.7%.

**Prefix experiment at scale** (24,300 judgments): Replicated V4 results at 5× scale.
- Entity-Aware best for Mixtral (4.7% hallucination)
- Structured Caution best for Llama (3.0% hallucination)
- **68-69% relative reduction** in hallucination across both models

### 5. The Honest V3 Correction
V3's AUC of 0.86 was **inflated** — it conflated category structure. The real, non-trivial finding is **within-category**: among 600 nonexistent-entity prompts sharing the same structure, embedding density distinguishes hallucinated from correct prompts (p < 10⁻⁵, cross-validated AUC ≈ 0.67). Still significant, but more modest than 0.86.

### 6. Bridge Analysis: Geometry Predicts Fixability
The same density feature that predicts hallucination **also predicts which hallucinations resist intervention**:
- Prompting bridge: p = 0.046 / 0.012 (suggestive, doesn't survive Bonferroni)
- **Fine-tuning bridge: Mixtral p = 0.0017, |r| = 0.80 (survives Bonferroni)**
- This is the strongest single result — geometry isn't just a risk indicator, it's a **difficulty indicator**

### 7. Fine-Tuning (Boaz's Suggestion Realized)
Best-per-prompt selection → ~2,400 training examples per model. LoRA fine-tuning on Mixtral and Llama.

**Results:**
- Hallucination reduction: 89% (Mixtral), 81% (Llama) relative to baseline
- **Matches** the best prompt prefix in accuracy (Mixtral: 94.4% vs Structured Caution 94.9%, p = 0.82 — no significant difference)
- Practical value: same accuracy, no runtime prompt engineering needed
- Tradeoff: increased factual refusals (70% of regressions are the model saying "I don't know" to real questions, not new hallucinations)

### 8. Three Generalization Tests (all pass)
Per Sunny's guidance, we needed to prove the model learned **behavioral caution**, not memorization:

1. **TruthfulQA transfer**: Fine-tuned models improve on an external benchmark testing a completely different type of hallucination (Llama +5.3pp, Bonferroni-significant)
2. **Template ablation**: Training on 5 templates ≈ training on all templates (McNemar p = 0.099/0.773). Diversity of templates doesn't matter — the model learned behavior, not patterns
3. **Cross-category generalization**: Training on entity-dependent categories only (~1K examples) matches or beats training on all categories (~2.4K). Entity-dep → entity-indep transfers; reverse fails

### 9. Data Quality Issues (all fixed)
- **Judge API failure contamination**: Silent failures injected fake "Refused" votes. 325 labels corrected (V5), 153 corrected (V4). Rankings unchanged. CoT finding invalidated.
- **Entity-level train-test contamination**: 61% of V3 test prompts share entities with V5 training. But decontamination analysis shows the gap is tiny (+0.5pp overall), supported by template ablation + TruthfulQA convergent evidence. Sunny's framing: "the model learned behavioral caution rather than memorizing specific entity names."

### 10. The Three Thesis Claims (all survive)
1. **Geometry predicts hallucination difficulty** — within-category density, confirmed at both prediction and intervention stages
2. **Prompting reduces hallucination** — 68-69% reduction, replicated at 5× scale
3. **Prompt behavior can be distilled into weights** — FT matches best prefix, three generalization tests confirm it's real

---

## Anticipated Questions & Answers

### Q: How/why was V3's AUC of 0.86 inflated?

The V3 logistic regression used geometric features (density, oppositeness, curvature, centrality) to predict hallucination across all prompts pooled together. It achieved AUC = 0.86. But this number is misleading because the geometric features were doing double duty: they were picking up **which category a prompt belongs to** (nonexistent entity vs. factual recall vs. impossible question), not just within-category difficulty.

This matters because different categories have very different hallucination rates by design — nonexistent-entity questions cause ~30% hallucination, while ambiguous questions cause ~1%. A classifier that simply learns "this prompt is in the nonexistent category" already gets most of the way to 0.86 without learning anything about geometry per se. In fact, category membership alone achieves AUC = 0.78. Geometry adds only +0.02-0.04 on top.

The honest finding is **within-category**: hold category constant (e.g., look only at 600 nonexistent-entity prompts that all have the same structure and purpose), and ask whether geometric features still distinguish hallucinated from correct. They do — density achieves within-category AUC ≈ 0.67, with p < 10⁻⁵ surviving Bonferroni correction. This is real but modest. The thesis leads with this honest framing.

**Analogy**: It's like predicting student test scores using geographic features. If you pool students from wealthy and poor districts, geography "predicts" scores at AUC = 0.85 — but it's really just picking up district-level differences. The interesting question is whether geography predicts scores *within* the same district. That's what within-category analysis does.

### Q: What exactly is prompt distillation?

The idea (Boaz's original suggestion): if a system prompt like "Before answering, consider whether the entity actually exists" reduces hallucination at runtime, can we **bake that behavior into the model weights** so we don't need the prompt at all?

The pipeline:
1. **Generate training data**: Run each of the 2,430 prompts through the model with each of the 4 prefix interventions. Judge all responses with the 3-judge consensus panel.
2. **Best-per-prompt selection**: For each prompt, pick the (prefix, response) pair that got the best judgment. This gives ~2,400 high-quality (prompt, response) training pairs per model where the response exhibits the cautious behavior we want.
3. **Fine-tune with LoRA**: Use parameter-efficient fine-tuning (LoRA adapters) to train the base model on these pairs. The model learns to produce the kind of cautious, accurate responses that previously required a system prompt — but now it does it by default, with no prompt engineering at runtime.

The key insight is that we're not teaching the model new facts. We're teaching it a **behavioral pattern** — the same epistemic caution that the system prompts elicited. The three generalization tests confirm this: the model doesn't memorize specific entities or templates, it learns to say "I don't know" when uncertain.

**Practical value**: Production deployment doesn't need carefully crafted system prompts. The caution is in the weights.

### Q: How did the bridge analysis work?

The bridge connects Chapter 5 (geometry predicts hallucination) to Chapter 7 (fine-tuning). The question: if geometry predicts *which prompts cause hallucination*, does it also predict *which hallucinations are hardest to fix*?

**Setup**: After running the prefix interventions, some hallucinations got fixed (model stopped hallucinating with the right prompt) and some remained broken across all prefixes — the "still-broken" prompts (27 for Mixtral, 24 for Llama). We already have geometric features for every prompt from the Chapter 5 analysis.

**Test**: Compare the geometric features (density, oppositeness, etc.) of fixed vs. still-broken prompts within the same category using Mann-Whitney U tests and logistic regression.

**Results for prompting bridge**: Within nonexistent-entity prompts, density is lower for still-broken prompts (Mixtral p = 0.046, Llama p = 0.012). Suggestive but doesn't survive Bonferroni correction for 24 tests.

**Results for fine-tuning bridge (the strong result)**: After fine-tuning, some prompts *still* hallucinate. We correlate per-category hallucination rate with mean category density. Result: Mixtral p = 0.0017, |r| = 0.80. This **survives Bonferroni** and shows a strong linear relationship — categories where prompts are geometrically sparse (low density) have higher residual hallucination even after fine-tuning.

**Why this matters**: Density isn't just telling us "this prompt is risky." It's telling us "this prompt is in a region of embedding space where the model's knowledge is thin, and no amount of prompting or fine-tuning will fully compensate." That's a stronger claim than just prediction — it's diagnosis.

---

---

## Density and Oppositeness: What They Are, What They Found, and Why

### What is density?

For each prompt, embed it with `text-embedding-3-large` (3,072 dimensions). Find its 20 nearest neighbors in the corpus. Density = inverse of the mean cosine distance to those neighbors. **High density** = many similar prompts nearby (well-represented region). **Low density** = isolated prompt in a sparse region.

Intuition: if a prompt sits in a dense neighborhood, the model likely saw many similar questions during pretraining and has reliable knowledge. If it sits in a sparse neighborhood, the model is operating at the edge of its training distribution — more likely to fabricate.

### What is oppositeness?

Take the prompt's embedding, run global PCA on the full corpus (10 components), flip the sign of the top 3 components. This produces an "opposite" point — maximally different along the dominant axes of corpus structure. Oppositeness = cosine distance from this flipped point to the nearest real prompt. **High oppositeness** = the corpus is asymmetric around this prompt (nothing "on the other side"). **Low oppositeness** = the corpus is more isotropic around it.

Intuition: if a prompt has high oppositeness, it sits in a directionally lopsided region of embedding space — there's data on one side but a void on the other. This is a novel feature (no prior work uses PCA sign-flip distance for this purpose).

### What did we find?

**Between-category (pooling all prompts):**
- Oppositeness is the strongest discriminator: hallucinated prompts have higher oppositeness (Mixtral |r| = 0.218, p < 10⁻¹⁰; Llama |r| = 0.367, p < 10⁻²⁰)
- Density is second: hallucinated prompts have lower density (Mixtral |r| = 0.142, p < 10⁻⁴; Llama |r| = 0.095, p = 0.017)
- Curvature and local intrinsic dimension: nothing (p > 0.7)

**But most of this is category structure.** Different question types (nonexistent entities vs. factual recall vs. impossible questions) cluster in different regions of embedding space, and they have very different hallucination rates by design. A classifier that just detects "this is a nonexistent-entity question" gets AUC = 0.78. Geometry only adds +0.02-0.04 on top.

**Within-category (the real test):**
We ran within-category Mann-Whitney tests on all 7 categories × 5 features × 2 models = 70 tests. But the nonexistent category (600 prompts, 177/114 hallucinations for Mixtral/Llama) is the only one where density survives Bonferroni for both models. Other categories either have too few hallucinations for statistical power (ambiguous: 4/9; edge factual: 4/1) or show **inconsistent effects** — meaning a feature is significant for one model but not the other, or shows opposite directions across models (e.g., plausible_fake within-category AUC is 0.492 for Mixtral but 0.643 for Llama; impossible is 0.617 for Mixtral but 0.411 for Llama). If a result only appears for one of two models, you can't confidently call it a real property of the embedding space vs. a quirk of that model.

**What is Bonferroni correction?** When you run many statistical tests, some will hit p < 0.05 by pure chance (~3.5 out of 70 expected). Bonferroni divides the significance threshold by the number of tests: α = 0.05/70 = 0.0007. Only results below that stricter threshold count as significant. It's conservative (probably rejects some real effects) but prevents reporting false positives. Density in nonexistent passes even this strict bar (Mixtral p = 5.7 × 10⁻⁷ < 0.0007).

Within the nonexistent category (the only one with sufficient power for both models):

- **Density is the winner**: Mixtral p = 5.7 × 10⁻⁷, |r| = 0.259; Llama p = 3.4 × 10⁻⁵, |r| = 0.249. Both survive Bonferroni. Hallucinated prompts sit in sparser neighborhoods.
- **Oppositeness flips roles**: Between categories it was the strongest feature; within the nonexistent category it's weaker (Mixtral p = 0.005, barely survives; Llama p = 0.037, doesn't survive). Oppositeness was mostly picking up category structure, not within-category variation.
- Centrality, curvature, intrinsic dimension: nothing within-category.

**This is a known limitation**: the within-category density signal is concentrated in one category. We can't tell if the absence of signal in other categories is a genuine null effect or just insufficient statistical power (too few hallucinations to detect an effect that may exist). The thesis acknowledges this explicitly.

### Why density and not oppositeness within-category?

Oppositeness is a **global** feature — it measures asymmetry relative to the corpus-level PCA axes. These axes primarily capture between-category variation (the biggest directions of variance in the corpus separate question types). So oppositeness is great at telling you "this prompt is in a weird part of the corpus" but that's mostly saying "this prompt is in a hard category."

Density is a **local** feature — it measures how many similar prompts are nearby, regardless of global structure. Within a category, all prompts share roughly the same global position, so the global PCA axes aren't informative. But local neighborhood density still varies: some nonexistent-entity prompts are surrounded by many similar questions, others sit in isolated pockets. The isolated ones hallucinate more.

**The analogy**: Oppositeness is like asking "is this neighborhood in a good part of town?" (global). Density is like asking "how many houses are on this specific block?" (local). Once you control for which part of town you're in, only the block-level measure still matters.

### Why does density predict hallucination?

We don't have a causal mechanism — this is correlational. But the working hypothesis: dense regions of embedding space correspond to well-represented topics in the model's training data. Questions about common entities (Albert Einstein, World War II) cluster densely; questions about obscure or fabricated entities sit in sparse regions. The model has seen more examples relevant to dense-region questions, so it has more reliable knowledge to draw on. In sparse regions, the model is extrapolating — and extrapolation is where hallucination lives.

This is consistent with the OOD (out-of-distribution) detection literature, where low-density regions of the input space are associated with unreliable model behavior.

### The bridge: density predicts difficulty, not just risk

**What "difficulty" means here**: a hallucination is "harder to fix" if it persists even after intervention — the model keeps hallucinating on that prompt despite our best efforts (prompting or fine-tuning).

**How we determined difficulty — two independent tests:**

1. **Prompting bridge**: After running all 4 prefix interventions on the 2,430 prompts, some hallucinations got fixed (model stopped hallucinating with at least one prefix) and some remained hallucinated under *every* prefix — the "still-broken" prompts (27 for Mixtral, 24 for Llama). We compared density of fixed vs. still-broken within the nonexistent category. Still-broken prompts have lower density (Mixtral p = 0.046, Llama p = 0.012). Suggestive but doesn't survive Bonferroni for 24 tests.

2. **Fine-tuning bridge (the strong result)**: After fine-tuning, some categories still have residual hallucination. We correlated each category's mean density with its post-fine-tuning hallucination rate across the 7 categories. Result: |r| = 0.80, p = 0.0017. This **survives Bonferroni**. Categories in sparser regions of embedding space retain more hallucination even after fine-tuning.

**The chain**: lower density (sparser neighborhood) → more likely to hallucinate → and if it does hallucinate, harder to fix with either prompting or weight updates. Density isn't just a risk flag — it's measuring something about how thin the model's knowledge is in that region, and that thinness resists correction.

**Why this matters**: if density were just noise or a proxy for something else, there's no reason it would also predict intervention difficulty. The fact that it predicts both occurrence AND fixability across two independent intervention methods (prompting and fine-tuning) is convergent evidence that it captures a real property of the embedding space — not a statistical artifact.

---

## Key Thing to Emphasize

Boaz's suggestion about distilling prompts into fine-tuning worked, and the geometric thread connects all three contributions: density predicts where hallucination happens AND where it's hardest to fix. The full arc is predict → intervene → distill, with geometry as the diagnostic running through all three stages.
