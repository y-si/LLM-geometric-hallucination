# Thesis Writing Guide

Central document for thesis content planning, structure, and expansion notes.
Experiment tracking remains in `results/v4_prefix_experiment/EXPERIMENT_LOG.md`.

**Current source**: `thesis_reference/v3_paper.tex` (671 lines, NeurIPS format, V3 results only)
**Target format**: Harvard Dissertate template (multi-chapter, double-spaced)
**Target template**: `thesis/` (extracted Dissertate.cls, XeLaTeX)

---

## Title Options (tabled for later)

Current: *"When the Manifold Bends, the Model Lies? Geometric Predictors of Hallucination in LLMs"*

**Issue**: "Manifold bends" implies high curvature = hallucination, but our finding is the opposite (Flat Manifold Paradox: low curvature correlates with hallucination). Also only captures V3 (prediction), not the full arc.

**Candidates**:
- **A**: *"Where the Manifold Thins: Geometric Predictors and Prompt-Based Mitigation of LLM Hallucination"* — "thins" = low density, our strongest predictor
- **B**: *"From Geometry to Intervention: Predicting and Reducing LLM Hallucination via Embedding Space Structure"* — full contribution
- **C**: *"The Geometry of Hallucination: Predicting, Diagnosing, and Mitigating LLM Failures in Embedding Space"* — punchier, thesis-scale
- **D**: *"Geometric Predictors of Hallucination in Large Language Models"* — clean, safe, descriptive

---

## V3 Paper Issues to Fix

| Issue | Location | Fix |
|---|---|---|
| "Why This is an AI Safety Project" title | Section 3 | Rename to "Motivation" or fold into Introduction |
| "class deliverable" | Conclusion, line 557 | Remove entirely |
| Oppositeness undefined | Results 5.8, RF importance | Add to Section 4.4 Geometric Features |
| n=3,680 unexplained | Section 4.5 | Add sentence explaining ~810 missing rows |
| No author affiliations | Author block | Add Harvard affiliation |
| Figure paths broken | All `\includegraphics` | Add `\graphicspath` directive |
| Scale claim overreach | Abstract | Remove "largest multi-model benchmark" or qualify carefully |
| Judge-evaluatee overlap | Not mentioned | Add to Limitations |
| Single annotator (n=1) | Appendix D | Flag in Limitations |

---

## Writing Progress

| Section | Status | Notes |
|---|---|---|
| Related Work | DONE (v3_paper.tex) | 6 subsections, 26 references |
| Bibliography | DONE (references.bib) | 26 entries, organized by topic |
| Everything else | Not started | |

---

## Content Expansion Guide: Conference Paper → Thesis

The core shift: the conference paper oversells geometry as a standalone predictor. The thesis tells the honest, more interesting story — geometry *explains category structure*, provides *modest within-category signal*, and most importantly *predicts which hallucinations are resistant to mitigation*.

### Introduction — Needs a Real Narrative Arc

The current intro is fine for a conference paper but reads as a pitch. A thesis intro should:

- **Motivate the problem more deeply** — why hallucination specifically matters *now* (not just "medical/legal harm"), with concrete examples of real-world failures
- **Tell the story of the research journey** — "We initially hypothesized X, found Y, which led us to investigate Z." The thesis should read as an intellectual narrative, not a sales pitch
- **Preview all contributions honestly** — the current intro only covers V3. The thesis spans V3→V4→V5, a progression from "can geometry predict hallucination?" to "can geometry predict *which hallucinations are fixable*?" to "can we actually fix them at scale?"
- **Drop the Theory of Change section** — that was a class requirement. The safety motivation should be woven into the intro naturally, not be its own section

### Related Work — Mostly Done, Needs Positioning

The expanded Related Work (6 subsections, 26 refs) is conference-quality. For the thesis:

- **Add a "gap" paragraph to each subsection** explicitly stating what the prior work doesn't do that we do. Right now the connections are implicit
- **Add fine-tuning / LoRA literature** since that's part of the pipeline (V5 next steps)
- **Add prompt engineering literature more seriously** — the current treatment of prompting-based mitigation is thin given that prefix intervention is half the thesis

### Methodology — Needs to ~3x in Length

This is the biggest content gap. The current methodology is 2 pages covering everything in broad strokes.

**Dataset construction (currently 1 paragraph, needs ~5 pages)**:
- Why these 7 categories? What's the design rationale for each?
- How were templates designed? Show examples of template → filled prompt
- What are the entity pools? How were they sourced and validated?
- V3 → V5 scaling: why 449 was insufficient, how we designed the 2,430 V5 set, the stratified template sampling and entity diversity caps, the V3 exclusion logic
- The placeholder validation issue and quality control

**Model selection (currently 1 paragraph, needs ~2 pages)**:
- Justify *why* these specific 10 models. What dimensions of variation do they cover?
- Discuss access constraints (API-only vs open-weight) and what that means for the study
- For V4/V5: why Mixtral and Llama specifically for prefix experiments?

**Consensus judging (currently ~1 page, needs ~4 pages)**:
- The judge design rationale: why 3 models, why these 3, why majority vote
- The diagnostic findings: per-judge bias (GPT-5.1 strictest, Llama most lenient), category-specific agreement rates (borderline_plausible_fake only 15-23% unanimous)
- How we handle disagreements and what they mean
- The human validation in more detail — 50 samples is thin, acknowledge this
- The sensitivity analysis: majority-vote vs unanimous-only results

**Geometric feature extraction (currently ~1 page, good but needs)**:
- Formal definitions with more mathematical rigor
- **Define oppositeness** — it's used in results but never defined anywhere in the paper
- Why k=20 for all features? Sensitivity analysis across k values?
- The embedding choice (text-embedding-3-large, 3072-dim) and robustness across embeddings deserves more treatment

**Prefix design (completely absent from current paper)**:
- What are the 5 prefixes? Full text of each system prompt
- Design rationale — why these 5? What aspects of hallucination does each target?
- Connection to prior work on prompting-based mitigation

### Results — Needs Restructuring and Honesty

The current paper presents V3 results with inflated claims. The thesis needs to tell the honest story:

**V3 Results (current paper, needs revision)**:
- The AUC=0.971 combined model needs the decomposition: category-only AUC=0.955, geometry adds +0.016. This is still statistically significant (p=0.012) but the framing needs to be honest that category structure does most of the work
- The logistic regression table (centrality beta=-3.62, p<0.001) is real but needs the caveat that this partially reflects category-level differences
- The cross-model consistency (tau=0.319) is a genuine finding

**V5 Geometry Prediction (new, ~5 pages)**:
- The honest decomposition: overall CV AUC=0.641 (Mixtral), 0.722 (Llama) — much lower than V3's train-only 0.86
- Category-only AUC=0.77 — geometry adds only +0.02-0.04 on top
- **Within-category analysis is the real finding**: density predicts hallucination within nonexistent entities (AUC 0.665, p<0.0001). This is non-circular because within a single category, all prompts share the same structure — the geometric variation is genuine
- local_id and curvature are essentially useless (r=-0.97 correlated, neither predictive)
- Frame this as: "geometry *explains* why categories differ, and density provides modest but real within-category signal"

**V4 Prefix Experiment (new, ~5 pages)**:
- 449 prompts x 5 prefixes x 2 models = 4,490 responses
- All prefixes significantly reduce hallucination (p<0.002)
- Entity-Aware best for Mixtral (11.8%->0.67%), Structured Caution best for Llama (5.8%->0.45%)
- Best-per-prompt selection: Mixtral 91.1%->95.5%, Llama 93.3%->98.0%

**V5 Baseline + Prefix Results (new, ~5 pages)**:
- V5 baselines: Mixtral 81.7% correct / 14.3% halluc, Llama 87.1% / 9.5%
- V5 prefix results: 24,299/24,300 judged (Step 7), fully analyzed (Step 8A)
- **V4 pattern replicates at 5x scale**: Entity-Aware best for Mixtral (14.3%→5.2%), Structured Caution best for Llama (9.5%→3.6%). All significant (p<0.001).
- **CoT Verification is catastrophic**: 62-68% refusal rate, 30% correctness. The "verify your claims" instruction causes over-refusal. Important negative finding — models interpret self-verification as permission to refuse.
- **V5 rates are higher than V4** (Mixtral Entity-Aware: 0.7% V4 → 5.2% V5). Expected — V5 prompts are new, structurally diverse, probe harder entity regions. This is evidence the V4 results weren't artifacts of overfitting to 449 prompts.

**Bridge Analysis (new, ~5 pages)**:
- V4 bridge: geometry predicts fixability, AUC=0.86 (train-only on 449 prompts)
- V5 bridge: aggregate AUC drops to 0.59-0.66 (cross-validated), BUT this is a class imbalance artifact (333 fixed vs 15 still_broken for Mixtral, 227 vs 5 for Llama)
- **Within-category density is the robust finding**: among nonexistent prompts, density significantly predicts fixability for both models (p=0.034, p=0.047). Unfixable prompts live in sparser embedding regions. This is non-circular (same category, same structure, geometry varies).
- **Oppositeness** is the strongest overall discriminator between fixable hallucinations and correct prompts (p < 1e-10 for both models)
- Frame as: "V4 discovery AUC=0.86 identified the signal. V5 within-category tests confirm the mechanism: density predicts fixability within structurally identical prompts. The aggregate AUC drop reflects proper cross-validation and extreme class imbalance, not a failure to replicate."

### Discussion — Needs Complete Rewrite

The current discussion has good ideas (outlier hypothesis, flat manifold paradox) but frames them overconfidently. The thesis discussion should:

- **Lead with the honest story**: "We initially found AUC=0.86 in V3, but proper cross-validated analysis on V5 shows geometry adds +0.02-0.04 beyond category structure. Here's what that means and why it's still interesting."
- **The flat manifold paradox needs rethinking**: The current paper claims curvature beta=-1.21 is a strong finding. V5 shows curvature is essentially useless as a predictor. Discuss why V3 overestimated this.
- **Density as the real geometric signal**: Within-category, density is the only feature that consistently predicts hallucination AND fixability. This connects to the "sparse void" hypothesis — hallucinations occur where the entity sits in a sparse neighborhood, and unfixable hallucinations occur in the sparsest regions. The V5 within-category bridge analysis (density predicts fixability within nonexistent prompts, p=0.034/0.047) is the strongest evidence for a genuine geometric mechanism.
- **Oppositeness as the discriminator between fixable hallucinations and correct prompts**: The V5 bridge analysis shows oppositeness is the strongest feature distinguishing prompts that hallucinate-then-get-fixed from those that were correct at baseline (p < 1e-10). High oppositeness means the entity has contradictory semantic associations — the model is pulled in multiple directions. Prefix interventions help because they give the model license to express uncertainty, which resolves the tension.
- **CoT Verification failure**: The catastrophic over-refusal (62-68%) is a meaningful negative finding. It shows that explicit self-verification instructions don't scale — models interpret "verify your claims" as "if in doubt, refuse." This has implications for the RLHF alignment literature where refusal is often treated as a safe fallback.
- **The pipeline as contribution**: As Sunny noted, the full pipeline (prompt generation -> responses -> judging -> prefix intervention -> best-per-prompt selection -> fine-tuning data) is itself a methodological contribution, independent of whether geometry is a strong predictor.
- **Why V5 hallucination rates are higher than V4**: V4 tested on 449 prompts, V5 on 2,430 new prompts with greater entity diversity and structural variety. The higher V5 baseline rates (Mixtral 14.3% vs 11.8%, Llama 9.5% vs 5.8%) confirm that V5 probes harder regions of the entity space. The higher V5 prefix residual rates (Entity-Aware: 5.2% vs 0.7%) confirm that some hallucinations are intrinsically harder. This is not a failure — it's evidence that the V5 benchmark has higher coverage and discriminative power.
- **Dimensionality paradox**: The finding that lower-dim embeddings work better is interesting and underexplored.

### Limitations — Needs Major Expansion

Currently 3 bullet points. Needs to be thorough:
- **V3 AUC inflation**: Explicitly acknowledge that the V3 AUC conflated category structure with within-category signal
- **Judge reliability on borderlines**: borderline_plausible_fake has only 15-23% unanimous agreement — this category's results should be interpreted cautiously
- **Bridge analysis class imbalance**: V5 bridge AUC drops from V4's 0.86 to 0.59-0.66 partly because only 15/5 prompts are "still_broken." The within-category tests are more reliable but have smaller effect sizes
- **CoT Verification exclusion**: We exclude CoT from best-per-prompt selection due to catastrophic refusal. A reviewer might ask whether CoT's low hallucination rate (1.6% Llama) has value if refusals are acceptable
- **Embedding dependency**: Still only one primary embedding model
- **English only**
- **Template-generated prompts**: Not naturalistic user queries
- **Small human validation sample** (n=50)
- **Correlation vs causation** (already in paper but expand)
- **No causal intervention on geometry** — we observe correlation but haven't reshaped the manifold to test causally
- **V5 vs V4 rate differences**: The higher V5 hallucination/residual rates could reflect prompt difficulty OR model sensitivity to entity novelty — we can't fully disentangle these

### Conclusion — Should Reflect the Evolved Understanding

The current conclusion claims "curvature and centrality are strong, cross-model predictors." The thesis conclusion should honestly say: "Category structure is the dominant predictor. Within categories, density provides modest but real geometric signal. The more surprising finding is that geometry predicts hallucination *difficulty* — which prompts resist mitigation — pointing toward a geometric taxonomy of fixability."

The conclusion should now be able to tell the complete arc:
1. Geometry predicts hallucination (V3 discovery, V5 confirmation via within-category density)
2. Prefixes reduce hallucination by 50-96% (V4 discovery, V5 confirmation at 5x scale)
3. Geometry predicts *which hallucinations resist mitigation* (V4 bridge, V5 within-category bridge)
4. This enables geometry-guided training data curation (best-per-prompt selection, unfixable exclusion)
5. The full pipeline — from geometric diagnosis to prompt intervention to fine-tuning — is the methodological contribution

### What to Add That Doesn't Exist Yet

1. **A full chapter on the prefix intervention pipeline** (design, V4 results, V5 replication)
2. **The bridge analysis** as a standalone results section — this is potentially the most novel contribution
3. **Best-per-prompt selection** analysis and its implications for fine-tuning data curation
4. **Detailed diagnostic analysis** of judge behavior (per-judge bias, category-specific agreement)

---

## Background vs. Literature Review: Structural Decision

**Decision: Separate them** (like Tarun Prasad's thesis, not Angela Li's combined approach).

### Evidence from reference theses

- **Angela Li** (*Statistical Perspectives on Algorithmic Fairness*): Ch 2 "Background and Literature Review" — combined, 25 pages. Works because her thesis is single-domain (algorithmic fairness); background concepts and prior work sit on the same continuum.
- **Tarun Prasad** (*LLM-Powered Lemma Extraction for Automated Theorem Proving*): Ch 2 "Background" (formal proofs, Coq, LLMs as separate foundation sections) + Ch 3 "Literature Review" (hammers, neural theorem proving, LLM theorem proving). Works because his thesis bridges two domains (formal verification + ML) that need separate conceptual grounding before reviewing how they've been combined.

**Our thesis bridges two domains** — hallucination/safety and embedding space geometry — making the separated structure (like Tarun's) more appropriate. A reader from the NLP/safety community needs geometry background; a reader from the geometry/manifold learning community needs hallucination context. Combining them would force awkward jumps between unrelated foundational concepts.

### Proposed Background Chapter Contents

The Background chapter teaches concepts a reader needs to understand our methods. It should NOT position our contributions (that's the Literature Review's job).

1. **Large Language Models** — transformer architecture (brief), next-token prediction, emergent capabilities, the gap between training objective and user expectations
2. **Hallucination in LLMs** — definition and taxonomy (intrinsic vs extrinsic, closed-domain vs open-domain), why it happens (memorization gaps, distribution shift, overconfidence), why it matters (medical, legal, educational harms)
3. **Embedding Spaces** — what embeddings are, how text-embedding models work, the geometry of high-dimensional spaces (curse of dimensionality, distance concentration), why cosine similarity is the standard metric
4. **Geometric Features of Manifolds** — intrinsic dimensionality, curvature, density, centrality, oppositeness. Formal definitions matching our methodology. This is the technical foundation for Chapter 4 (Results: Geometric Prediction)
5. **LLM-as-Judge Paradigm** — why human evaluation doesn't scale, how LLM judges work, known biases (verbosity, position, self-preference), consensus approaches. Foundation for understanding our 3-judge panel methodology

### Proposed Literature Review Chapter Contents

The Literature Review surveys prior work and identifies the gaps we fill.

1. **Hallucination Detection & Benchmarks** — TruthfulQA, HaluEval, FActScore, SimpleQA. Gap: none use geometric features
2. **Hallucination Mitigation** — RAG, CoVe, inference-time intervention, RLHF/DPO. Gap: few systematic comparisons of prompt-only interventions
3. **Prompt Engineering for Safety** — system prompts, chain-of-thought, self-consistency. Gap: no controlled comparison of prompt strategies on paired hallucination data
4. **Geometric Analysis of Neural Representations** — intrinsic dimensionality estimation, manifold hypothesis, representation topology. Gap: not applied to hallucination prediction
5. **Knowledge Representation in LLMs** — knowledge neurons, probing, entity representations. Gap: connection to geometric structure is implicit, not tested
6. **Fine-Tuning for Alignment** — LoRA/QLoRA, RLHF, DPO, constitutional AI. Gap: none use geometry-guided training data selection

---

## Proposed Chapter Structure

Based on the Harvard Dissertate template (Introduction + 3-4 content chapters + Conclusion):

| Chapter | Content | Source |
|---|---|---|
| 0 | **Introduction** — motivation, research journey narrative, contribution preview | v3_paper.tex intro + theory of change (merged, class language removed) |
| 1 | **Background** — LLMs, hallucination taxonomy, embeddings, geometric features, LLM-as-judge | New content (see above) |
| 2 | **Literature Review** — 6 subsections with explicit gap statements | v3_paper.tex related work (restructured) + new prompt engineering + fine-tuning lit |
| 3 | **Methodology** — dataset, models, judges, geometry, prefixes (significantly expanded) | v3_paper.tex methodology + new prefix design content |
| 4 | **Results: Geometric Prediction** — V3 results + V5 geometry analysis (honest framing) | v3_paper.tex results (revised) + new V5 analysis |
| 5 | **Results: Prompt Prefix Mitigation** — V4 + V5 prefix experiments, bridge analysis | New content from EXPERIMENT_LOG.md Parts 1-2 |
| 6 | **Discussion & Future Work** — honest reframing, pipeline contribution, limitations | v3_paper.tex discussion (rewritten) |
| 7 | **Conclusion** | Rewritten to reflect evolved understanding |
| A | **Appendix** — statistical details, judge diagnostics, full prompt lists | v3_paper.tex appendix + new supplementary |

---

## What We Can Write NOW vs. What's Waiting on Data

### Available now (all data in hand):
- Introduction rewrite
- Related Work (done)
- Methodology expansion (all details documented in EXPERIMENT_LOG.md)
- V3 Results revision (honest framing)
- V5 Geometry Prediction section (Part 2.5 of experiment log)
- V4 Prefix Experiment section (Part 1 of experiment log)
- V3 Bridge Analysis section (Part 2 of experiment log)
- Discussion rewrite
- Limitations expansion
- Bibliography (done, 26 refs, needs ~50-80 for thesis)

### Newly available (Steps 7-8 complete — Mar 2026):
- V5 prefix results: 24,299/24,300 judged, fully analyzed (Step 8A)
- V5 bridge analysis: within-category density confirms fixability prediction (Step 8B)
- Best-per-prompt selection complete (Step 9): Mixtral 2,402 training (97.7% correct, 28 unfixable), Llama 2,406 training (98.2% correct, 24 unfixable). Baseline included as 5th candidate source — prevents 6 regression cases. Entity-aware dominates unique saves.
- All thesis figures for Chapters 4-6 can now be generated from existing data

### Waiting on data:
- Fine-tuning results — Step 10 IN PROGRESS (3 Mixtral jobs complete, Llama running). Step 11 evaluation next.
- Generalization testing — TruthfulQA, HaluEval (Phase 5)
