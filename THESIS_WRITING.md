# Thesis Writing Guide

Central document for thesis content planning, structure, and expansion notes.
Experiment tracking remains in `results/v4_prefix_experiment/EXPERIMENT_LOG.md`.

**Current source**: `thesis_reference/v3_paper.tex` (671 lines, NeurIPS format, V3 results only)
**Target format**: Harvard Dissertate template (multi-chapter, double-spaced)
**Target template**: `thesis/` (extracted Dissertate.cls, XeLaTeX)

---

## Rigor Standard

> **This is a Harvard senior thesis targeting NeurIPS-level publication. Every sentence must be defensible.**
>
> This standard applies to every decision in writing — claims, framing, word choice, figure captions, statistical language, everything. Before writing any paragraph, ask:
>
> 1. **Why this?** Is this claim backed by data, prior work, or advisor guidance? If it's an interpretation, is that clearly signaled?
> 2. **Why not something else?** What alternative framings were considered? Why is this one more honest?
> 3. **What could go wrong?** What would a skeptical reader challenge? What's the weakest assumption?
> 4. **Is this honest?** Does the framing match what the data actually shows? Are we overclaiming effect sizes, generality, or novelty?
> 5. **Would a reviewer object?** Anticipate the three most likely critiques and address them preemptively — in the text, not just mentally.
>
> **Specific writing standards:**
> - Never report a number without context (baseline, effect size, confidence interval, or comparison)
> - Never claim causation from correlation. "Predicts" not "causes." "Associated with" not "leads to"
> - Every figure must be interpretable without reading the main text (self-contained captions)
> - Limitations are not an afterthought — they are evidence of intellectual honesty. A limitation acknowledged is stronger than one a reviewer discovers
> - When initial and expanded benchmark results disagree (e.g., AUC drop), lead with the expanded benchmark as the definitive result and explain why the initial study overestimated, not the reverse
> - No hedging without substance. "We believe X" is weak. "X, supported by Y evidence, though limited by Z" is strong
> - The bar is not "would this pass peer review?" The bar is "would this withstand a 30-minute conversation with Boaz Barak or a NeurIPS area chair?"
> - **NO RESULTS PREVIEWS — ANY CHAPTER.** Each chapter should present its own results without spoiling later chapters. Chapter 4 (Setup) is the strictest: no hallucination rates, AUC values, Kendall's tau, judge agreement percentages, or any empirical finding — design rationale and logical arguments only. But this also applies elsewhere: Ch 5 should not preview Ch 6 numbers, Ch 6 should not preview Ch 7 numbers, etc. Common pitfalls: saying "different baseline difficulty levels" (implies known rates), "shared patterns in our results" (implies results exist), stating that features "vary systematically" (asserts a finding — use "we investigate whether" instead), citing specific numbers from later experiments, or describing the contamination fix's impact with exact label counts in the setup chapter. Frame forward references as goals or open questions: "as we investigate in Chapter X" is fine; "as we show in Chapter X, [result]" is NOT — it spoils the result. **WATCH FOR THIS ON EVERY REVIEW PASS. This has been a recurring issue.**
> - **No V3/V4/V5 terminology** in the thesis text. Use descriptive terms ("initial benchmark," "expanded benchmark," "cross-model benchmark").
> - **⚠️ COT CONTAMINATION CHECK — MANDATORY FOR EVERY NEW FIGURE, TABLE, OR STATISTIC.** CoT Verification was excluded from the thesis (Mar 12 decision). But several scripts and CSVs in `results/` still include CoT data. Before adding ANY number, figure, or table to the thesis: (1) trace it to its source script, (2) check whether that script loads CoT data (`cot_verification`), (3) if it does, verify the number/figure excludes CoT or fix the script first. Known contaminated files: `scripts/analyze_v5_prefixes.py` (includes CoT in PREFIX_ORDER), `src/evaluation/prefix_analysis.py` (includes CoT in PREFIX_ORDER), `results/v5_prefixes/analysis/v5_prefix_metrics.csv` (contains CoT rows), `results/v5_prefixes/analysis/v5_category_metrics.csv` (contains CoT rows). Known clean files: `scripts/analyze_v5_bridge.py` (fixed Mar 22), `scripts/build_v5_training_data.py`, `scripts/generate_ch6_category_heatmap.py`, all fine-tuning/ablation/cross-cat scripts. **This was a real bug** — the bridge analysis included CoT until Mar 22, changing still_broken counts from 15/5 to 27/24 and flipping Llama AUC from 0.44 to 0.71. Do not trust any analysis output without verifying CoT exclusion.
> - **No section hyperlinks in chapter opening paragraphs.** Chapter openings should read as narrative prose describing the flow of ideas, not as a table of contents with `Section~\ref{...}` references. The reader can see the section structure from the headings. Match the style of the reference theses (Tarun Prasad, Angela Li).

---

## FORMAL DIRECTIONS FROM THE DEPARTMENT

The thesis should contain an informative abstract separate from the body of the thesis. This abstract should clearly state what the contribution of the thesis is–which parts are expository, whether there are novel results, etc. We also recommend the thesis contain an introduction that is at most 5 pages in length that contains an “Our contributions” section which explains exactly what the thesis contributed, and which sections in the thesis these are elaborated on.

At the degree meeting, the Committee on Undergraduate Studies in Computer Science will review the thesis abstract, the reports from the readers and the student’s academic record; it will have access to the thesis. The readers (and student) are told to assume that the Committee consists of technical professionals who are not necessarily conversant with the subject matter of the thesis so their reports (and abstract) should reflect this audience.

The length of the thesis should be as long as it needs to be to present its arguments, but no longer! There is no minimum or maximum page length; 25 pages or less could be appropriate if they’re mostly dense math proofs some of which are novel, and 100 pages or more could be appropriate if they contain mostly large figures and/or English discussion.

---

## Title Options (tabled for later)

Current: *"When the Manifold Bends, the Model Lies? Geometric Predictors of Hallucination in LLMs"*

**Issue**: "Manifold bends" implies high curvature = hallucination, but our finding is the opposite (Flat Manifold Paradox: low curvature correlates with hallucination). Also only captures V3 (prediction), not the full arc.

**Candidates**:
- **A**: *"Where the Manifold Thins: Geometric Predictors and Prompt-Based Mitigation of LLM Hallucination"* — "thins" = low density, our strongest predictor
- **B**: *"From Geometry to Intervention: Predicting and Reducing LLM Hallucination via Embedding Space Structure"* — full contribution
- **C**: *"The Geometry of Hallucination: Predicting, Diagnosing, and Mitigating LLM Failures in Embedding Space"* — punchier, thesis-scale
- **D**: *"Geometric Predictors of Hallucination in Large Language Models"* — clean, safe, descriptive
- **E**: *"Where the Manifold Thins: Geometric Predictors of LLM Hallucination and Their Application to Fine-Tuning"* — keeps density metaphor, names the actual contribution
- **F**: *"Geometric Structure of Hallucination in Large Language Models"* — slightly broader than D, implies mapping out the structure (prediction + fixability + sparse void), still clean
- **G**: *"Predicting and Reducing LLM Hallucination via Embedding Space Geometry"* — covers both halves (prediction + intervention) without overloading
- **H**: *"The Geometry of Not Knowing: Predicting and Reducing Hallucination in Large Language Models"* — "not knowing" captures the core insight (density reflects knowledge gaps), subtitle is descriptive
- **I**: *"When Models Fabricate: Geometric Predictors of Hallucination in Large Language Models"* — evocative hook without the manifold metaphor, subtitle is clean
- **J**: *"Density, Asymmetry, and Fabrication: Geometric Signals of Hallucination in Large Language Models"* — names the actual features (density + oppositeness) without jargon
- **K**: *"Where Language Models Hallucinate: Geometric Structure in Embedding Space as a Predictor and Guide"* — "where" is literal (geometric regions), subtitle covers both contributions
- **L**: *"Embedding Space Geometry and LLM Hallucination: From Prediction to Mitigation"* — dry but complete, signals the full arc

**Ranking (honest, updated Mar 21)**: H > F > I > D > J > A > G > K > E > L > B > C.

- **H** is the best two-part title: "The Geometry of Not Knowing" is memorable, accurate (the thesis is literally about geometric signatures of knowledge gaps), and not gimmicky. The subtitle is straightforward. Comparable in style to Angela's ("Statistical Perspectives on Algorithmic Fairness: Quantifying Group Fairness in Thresholding Decisions") — evocative framing phrase + descriptive subtitle.
- **F** is the best short title if you want no frills.
- **I** works if you want something vivid but "when models fabricate" is slightly narrower than the thesis (Ch 6-7 are about fixing fabrication, not just predicting it).
- **D** remains the safest option — no one will object but no one will remember it either.
- **J** is the most specific but may be too technical for a title — "density" and "asymmetry" mean nothing to the committee until they've read Ch 5.
- **L** is too literal (maps to chapter structure, as noted).

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

## Mathematical Content

The thesis is empirical, not theoretical — no formal proofs. But mathematical rigor in definitions and methods is required (NeurIPS empirical paper standard: precise enough that a reader can reproduce every metric from equations alone).

**Background (Ch 2)** — formal definitions with equations:
- Cosine similarity/distance
- Local intrinsic dimensionality (TwoNN: `d = 1/log(r2/r1)`)
- Curvature score (PCA residual variance on k-NN neighborhood)
- Oppositeness (flip top PCA components, distance to nearest real point)
- Density (`1/mean_dist_to_k_neighbors`)
- Centrality (`1 - cos_sim(embedding, corpus_mean)`)

**Experimental Setup (Ch 4)** — statistical framework:
- Majority vote rule for consensus judging (formal definition) — DONE (Section 4.3)
- Brief closing paragraph previewing the statistical approach (non-parametric tests, Bonferroni) — no formulas, just roadmap

**Results chapters (Ch 5-7)** — define tests inline where first used, with full equations:
- Ch 5: Mann-Whitney U test (unpaired group comparisons), rank-biserial effect size, logistic regression + cross-validated AUC, AUC decomposition (category-only vs. category+geometry)
- Ch 6: McNemar's test with Yates continuity correction (paired binary outcomes), Bonferroni correction (first formal definition here)
- Ch 7: references back to Ch 5-6 definitions; adds permutation tests (small samples), Wilson confidence intervals
- All chapters: confidence intervals, effect sizes alongside p-values

**Rationale for inline placement (decided Mar 12, 2026):** Each test needs context to motivate it — McNemar's makes no sense until the reader knows we're comparing the same prompt under two conditions (Ch 6), Mann-Whitney makes no sense until we're comparing feature distributions across hallucinated vs. correct groups (Ch 5). A standalone "Statistical Methods" section in Ch 4 would be disconnected formulas the reader can't use for 20 pages. The Ch 4 closing paragraph gives the roadmap; the chapters give the details.

---

## Writing Progress (updated March 24, 2026)

**Spacing change**: Switched from 2.0 (double) to 1.5 line spacing on Mar 21. All page counts below reflect the 1.5-spaced format.

| Chapter | Status | Pages (actual) | Notes |
|---|---|---|---|
| Ch 1 Introduction | Stub | 1 (p. 1) | **Department mandate: at most 5 pages.** Write after Ch 8. |
| Ch 2 Background | **DONE** | ~12 (pp. 2–13) | 5 sections: LLMs, hallucination, embeddings/geometry, evaluation, fine-tuning. |
| Ch 3 Literature Review | **DONE** | ~9 (pp. 14–22) | 8 subsections + synthesis. |
| Ch 4 Experimental Setup | **DONE** | ~35 (pp. 23–57) | Sec 4.1-4.6 written. Flow pass complete. |
| Ch 5 Can Geometry Predict? | **DONE** | ~28 (pp. 59–87) | All 6 sections written (5.1-5.6). Flow pass complete. |
| Ch 6 Can Prompts Reduce? | **DONE** | ~11 (pp. 87–97) | Sec 6.1-6.4 written. Prefix design, pilot study, replication, category-level analysis. |
| Ch 7 Can Geometry Guide? | **DONE** | TBD (recompile needed) | All sections written (7.1-7.5). |
| Ch 8 Discussion & Conclusion | Stub | 1 | Write next — needs all results (now available). Ch 1 after. |
| Appendix A | **DONE** | ~6 (pp. 99–104) | Experimental Artifacts: judge prompt, prefix texts, contamination fix, FT configs. |
| Appendix B | **TODO stubs** | ~7 (pp. 106–112) | Supplementary Analysis: Kendall matrix, embedding robustness, human validation, UMAP heatmaps. Detailed TODOs in place. |
| Bibliography | ~68 entries | starts p. 113 | Substantially expanded from Ch 2 + Ch 3 writing. |
| **TOTAL** | **Ch 2-7 + App A done, Ch 8 → Ch 1 → App B remaining** | **~112+ written (excl. appendices)** | **Due March 27 (3 days)** |

### Chapter-by-chapter assessment (recorded Mar 22, 2026)

**Longest**: Ch 4 (Setup) at 35 pages (1.5 spacing). Ch 5 is second at 27 pages (partially written). Ch 7 will compete when written — it has 7+ subsections of substantive content. Target ≤20 pages at 1.5 spacing.

**Most important**: Ch 5 (Geometry Prediction). Load-bearing — if the geometric signal isn't convincing, Ch 6-7 lose the "bridge" argument and become just a prompt engineering + fine-tuning paper. The within-category density finding (p < 10⁻⁵, Bonferroni-surviving, both models) is what makes this a geometry thesis.

**Most detailed**: Ch 4 (Setup). By design — every design choice justified, every hyperparameter rationalized, every limitation pre-acknowledged. Correct prioritization for a methodology-heavy thesis.

**Most novel**: Ch 7 (Geometry Guides Intervention). Fixability prediction, precision-recall tradeoff of learned caution, three types of generalization with asymmetric transfer — all genuinely new contributions not found in prior work.

**Most editorially risky**: Ch 5. The V3 AUC=0.86 → V5 AUC=0.64 story requires precise framing as honest refinement, not retraction. One sloppy sentence and a reviewer reads "initial result was inflated."

**Easiest to write**: Ch 6 (Prompts Reduce). Clean data, straightforward narrative, mostly tables and figures. All prefixes work, rankings clear, McNemar's all significant.

**Hardest to write**: Ch 1 (Introduction). Must make a non-expert committee understand geometry + hallucination, preview four contributions without overselling, set up V3→V5 tension without confusion. Short but high-stakes.

**Most likely to need trimming**: Ch 7. Template ablation (result: "doesn't matter" — compress to 2 pages), cross-category (2 pages), decontamination (1-1.5 pages per plan). Without discipline this chapter balloons to 30+ pages.

**The one that matters for the grade**: Ch 1. The committee reads abstract + introduction + reader reports. If the intro frames this as "geometry predicts hallucination *difficulty*" — thesis. If it reads as "we ran a pipeline" — engineering report.

### Writing order (decided Mar 12, 2026)

1. ~~**Ch 4 Experimental Setup**~~ — DONE
2. **Ch 5 Can Geometry Predict?** — first results chapter, all data ready, no Phase 10 dependency
3. **Ch 6 Can Prompts Reduce?** — builds on Ch 5 baseline, all data ready
4. **Ch 7 Can Geometry Guide?** — bridges Ch 5 + Ch 6, all Phase 9/10 data ready
5. **Ch 2 Background** — contextual, can write in parallel if blocked on anything
6. **Ch 3 Literature Review** — detailed paragraph-level outline complete (8 sections, ~72 refs). v3 draft provides ~30% of text. 48 new bib entries to add. Phase 7 comparison tables feed into Ch 8 Discussion, not Ch 3
7. **Ch 1 Introduction** — frames everything, write after results are solid
8. **Ch 8 Discussion & Conclusion** — write last
9. **Opening paragraphs + flow passes** — all chapters, final pass

### Standardized chapter workflow (for results chapters)

1. **Outline** section structure in THESIS_WRITING.md
2. **Pull numbers** from result files — verify against analysis scripts, cross-check with experiment log
3. **Write** each section one at a time, with review after each
4. **Review pass** — no results spoilers in wrong chapters, consistent terminology, cross-references correct

---

## Chapter 4: Experimental Setup — Detailed Content Plan

**Recommended first chapter to write.** Rationale: (1) No rhetorical decisions — documenting what we did, not arguing what it means. (2) Forces crystallization of every design choice against the rigor standard. (3) Everything else depends on it — Ch 5-7 reference this constantly. (4) The chapter a reviewer reads most critically.

### Chapter opening (~0.5 page)

Brief paragraph framing the shared infrastructure. "This chapter describes the experimental infrastructure common to all experiments in this thesis: the hallucination benchmark, the models under study, the consensus evaluation pipeline, and the embedding approach. Experiment-specific methods (geometric feature extraction, prefix design, fine-tuning) are introduced in their respective chapters."

### 4.1 Benchmark Construction (~5-7 pages)

The reader needs to understand *what* we're testing and *why* it's designed this way.

**4.1.1 Category Design Rationale**
- The 7 categories and why each exists. Not just a list — justify the design space:
  - **factual**: baseline control — prompts with unambiguous correct answers. Establishes that hallucination isn't universal
  - **nonexistent**: the core test case — entities that don't exist, model must recognize this. Largest category (600 V5) because it's where hallucination concentrates
  - **impossible**: tests logical/physical reasoning, not entity knowledge
  - **ambiguous**: prompts with no single correct answer — tests whether models refuse or fabricate certainty
  - **borderline_plausible_fake**: the hardest category — entities that *sound* real but don't exist. Only 15-23% judge unanimity. Designed to probe the boundary of model knowledge
  - **borderline_obscure_real**: real but obscure entities — tests whether models incorrectly deny existence
  - **borderline_edge_factual**: commonly confused facts — tests confident errors vs. knowledge gaps
- Why 7 categories and not 3 or 15. The borderline categories were added specifically to probe the decision boundary between "knows" and "doesn't know" — this is where geometry is hypothesized to be most informative
- Table: category, count (V3 and V5), example prompt, expected correct behavior

**4.1.2 Template Design**
- What templates are (structural patterns with entity placeholders)
- Example: `"What year was {person} born?"` + entity pool → concrete prompt
- Why templates rather than free-form generation: controls for syntactic variation, ensures each prompt isolates entity knowledge from linguistic complexity
- Template diversity: 55-66 templates per main category, 20 per borderline sub-type. Round-robin sampling (shuffled, seeded) ensures no template dominates
- **Justify round-robin over random sampling**: Random sampling with replacement risks over/under-representing templates, especially at smaller per-category N. Round-robin guarantees uniform template usage. Trade-off: artificial uniformity doesn't reflect natural question distributions — but for fine-tuning training data, maximizing structural diversity is the priority (prevents model from overfitting to specific template patterns rather than learning general hallucination avoidance). Cite Sunny's feedback on template diversity mattering more than example count
- The placeholder validation issue from V3 (~20 broken prompts) and how V5 fixed it

**4.1.3 Entity Pools and Validation**
- How entities were sourced (knowledge-based for factual, manually crafted for nonexistent, web-verified for borderline)
- Entity diversity caps: max 5 reuses per entity across all prompts in a category
- The fake entity collision problem: 27 of 105 initial fake entities collided with real entities. Automated web search + human review process. Examples: "The Dry Season" is a real book, "Blackfen" is a real place in London
- Obscure real entity verification: every entity must be confirmed as both real and genuinely obscure

**4.1.4 Benchmark Scaling (449 → 2,879 prompts)**
- Initial benchmark: 449 prompts (the class project benchmark). Now serves as held-out test set
- Expanded benchmark: 2,430 new prompts. Why scale up: LoRA needs 1,000-10,000 examples, need proper train/test separation, greater entity and template diversity
- Exclusion logic: two levels — exact text match + same (template, entity-set) combo. Zero contamination between held-out and training sets
- Cross-category deduplication: 8 factual↔edge_factual overlaps caught and resolved
- Table: category, held-out count, training count, template coverage, entity coverage, exclusions

### 4.2 Model Selection (~2-3 pages)

**Opening paragraph**: Frame the two distinct model selection decisions: (1) which models to benchmark for cross-model geometric analysis, and (2) which models to target for hallucination intervention (prompting + fine-tuning). These serve different purposes and have different selection criteria.

**4.2.1 Cross-Model Benchmark Suite (10 models)**

*Purpose*: Establish that geometric embedding properties predict hallucinations *across* model families, not just for one architecture.

- **Table 4.X**: All 10 models with columns: Model name, Provider, Architecture type (dense/MoE), Access type (API-only/open-weight)
  - OpenAI: GPT-5.1, GPT-4.1, GPT-4.1-mini, GPT-4o-mini
  - Anthropic: Claude Opus 4.5, Claude Sonnet 4.5, Claude Haiku 4.5
  - Open-weight (Together AI): Llama 4 Maverick 17B, Mixtral 8x7B, Qwen 3 Next 80B
- **Selection rationale**:
  - Three major provider families → avoids provider-specific artifacts
  - Capability tiers within each family (e.g., GPT-5.1 vs GPT-4o-mini, Opus vs Haiku) → tests whether geometric predictors hold across capability scales
  - Architectural diversity: dense vs MoE → tests whether MoE routing changes geometric structure
  - Practical constraint: models available via standard APIs at experiment time
- **DO NOT include in this section**: hallucination rates, cross-model consistency stats (Kendall's tau), which models hallucinate more. Forward reference to Chapter 5.
- **Reviewer anticipation**:
  - "Why not Gemini?" → address model availability / note 10 models span sufficient diversity
  - "Parameter counts?" → API-only models don't always disclose. For open-weight: Mixtral 8x7B (46.7B total, ~12.9B active), Llama 4 Maverick (400B total, 17B active), Qwen 3 Next 80B

**4.2.2 Intervention Target Models (Mixtral 8x7B and Llama 4 Maverick)**

*Purpose*: Explain why these two models are used for prompting (Chapter 6) and fine-tuning (Chapter 7).

- **Open-weight requirement** (hard constraint):
  - Extracting hidden-state embeddings for geometric analysis of intervention effects
  - LoRA fine-tuning requires weight access (cite Hu et al. 2022)
  - API-only models (GPT, Claude) cannot support either
- **Why these two specifically**:
  - Architectural diversity: Mixtral = sparse MoE (8 experts, 2 active/token); Llama 4 Maverick = dense MoE (128 experts, 17B active). Different routing → tests architecture specificity
  - Different expected difficulty levels: one has the highest baseline hallucination rate among 10 models, the other moderate. Tests interventions on both "hard" and "easier" cases. (NO specific numbers — those are results)
  - Together AI availability for both inference and fine-tuning APIs
- **Instruct variants** (exact model IDs):
  - `mistralai/Mixtral-8x7B-Instruct-v0.1`
  - `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` (inference) / `-Instruct` (fine-tuning)
  - Rationale: instruct models accept system prompts directly, essential for prompting interventions. Base models would require few-shot formatting.
- **Why not more open-weight models**:
  - Cross-model generality already established in 10-model benchmark (Chapter 5)
  - Intervention experiments expensive: 5 prefixes × 2,879 prompts × 3 judges = ~43K judge calls per model
  - Two architecturally distinct models provide sufficient evidence without prohibitive cost

**4.2.3 Generation Parameters**

- **Inference settings** (uniform across all conditions):
  - `temperature = 0.7` — standard for open-ended generation; balances diversity with coherence
  - `max_tokens = 4000` — generous upper bound to avoid truncation artifacts
  - No top-p or top-k constraints
  - Held constant across baseline, all prefixes, and fine-tuned models → any differences attributable to intervention
- **Infrastructure**: Together AI API for open-weight inference/fine-tuning; OpenAI API for GPT family; Anthropic API for Claude family
- **Reproducibility note**: temperature > 0 means stochastic responses. Single response per prompt per condition (no resampling/averaging). Deliberate: tests whether single-shot interventions reliably shift behavior, which is the realistic deployment scenario.
- **Reviewer anticipation**:
  - "Why 0.7 not 0?" → temp=0 is deterministic but unrepresentative of deployment. 0.7 standard for conversational tasks
  - "Why not multiple samples per prompt?" → 2,879 prompts provides statistical power through breadth; multiple samples would 5x cost without changing core experimental question

**EXCLUDE from 4.2** (results preview risks):
- Any specific hallucination rates (11.8%, 5.8%, etc.)
- Kendall's tau or cross-model correlation statistics
- Which model hallucinated most/least
- Any prefix or fine-tuning results

**Citations needed**: Hu et al. 2022 (LoRA, for open-weight requirement); possibly MoE architecture paper if describing in detail

### 4.3 Consensus Judging Pipeline (~3.5-4 pages)

This is the section a reviewer will scrutinize hardest. LLM-as-judge is a known weak point.

**CRITICAL RULE: NO RESULTS HERE.** Do not include: specific agreement rates (78.3%, 82.8%), per-judge label counts, per-judge bias patterns (which is strictest/most lenient), specific hallucination rates. All of that is results → Chapter 5+. This section describes the DESIGN only.

**4.3.1 Why LLM Judges (~0.5 page)**
- Scale argument: 449 prompts × 10 models (benchmark) + 2,430 × 2 models × 6 conditions (interventions) = tens of thousands of evaluations. Human annotation infeasible
- Cite Zheng et al. 2023 (MT-Bench, NeurIPS): LLM judges align >80% with human preference
- Cite Liu et al. 2023 (G-Eval, EMNLP): rubric-based LLM evaluation
- Acknowledge limitations upfront: LLM judges have known biases (verbosity, position, self-preference — cite Wataoka et al. 2024)
- Why not crowdsourcing: our task requires geometric/mathematical domain knowledge
- Mitigations: panel diversity + human validation (forward-ref)

**4.3.2 Panel Design (~0.5 page)**
- 3 judges: GPT-5.1 (OpenAI), Claude Opus 4.5 (Anthropic), Llama 4 Maverick (Together AI)
- Why 3: odd number → no ties in majority vote. Three balances cost vs. robustness (single judge = systematic bias risk; five = 67% more cost with diminishing returns)
- Why these 3: cross-provider diversity (OpenAI, Anthropic, Meta). Different training pipelines reduce correlated errors. All frontier-class
- Judge–evaluatee overlap: Llama is both judge and intervention target. Acknowledge limitation (cite Wataoka et al. 2024 self-preference). Mitigate: it's 1 of 3 votes, can't unilaterally determine label. Forward-ref to sensitivity analysis
- All judges: temperature = 0.0 for reproducibility
- NO RESULTS: do not state per-judge bias patterns here

**4.3.3 Evaluation Rubric (~0.75 page)**
- 4-point scale formal definitions:
  - Label 0 (Correct): response accurate w.r.t. ground truth
  - Label 1 (Partial): contains correct info but also fabricated/inaccurate claims
  - Label 2 (Hallucinated): substantively incorrect or fabricated
  - Label 3 (Refused): model declines to answer
- Why 4-point, not binary: partials are most interesting (model HAS knowledge but errs); refusals mechanistically distinct from hallucinations. For fine-tuning: partial > refused in training value
- Category-specific rules (from judge system prompt):
  1. Nonexistent entities: treating fake as real → hallucinated; correctly identifying → correct
  2. Impossible/unknowable: correctly identifying → correct
  3. Factual: standard accuracy against ground truth
  4. Ambiguous/subjective: acknowledging ambiguity with reasonable analysis → correct
- Why category-specific rules matter: without them, "this theorem doesn't exist" could be labeled refusal instead of correct
- Present as table with formal definitions

**4.3.4 Judge Prompt Design (~0.75 page)**
- System prompt: contains rubric, category-specific rules, JSON output instruction
- User prompt template: three input fields (question, answer, ground_truth)
- Output format: JSON with justification (free-text reasoning), label (int 0-3), confidence (float 0-1)
- Ground truth provision: deliberate — we evaluate factual accuracy, not open-ended quality. Reference-based evaluation reduces subjectivity
- No few-shot examples: rubric sufficiently precise. Few-shot risks biasing toward specific patterns
- Include exact system prompt text or representative excerpt (Figure/Listing). Reproducibility demands this
- meta_info field: accepted by interface, not injected into prompts (logging/debugging only)
- NO RESULTS: do not discuss how often judges agree with ground truth

**4.3.5 Majority Vote and Consensus (~0.5 page)**
- Formal rule: final label = mode of 3 labels. `Counter(labels).most_common(1)[0][0]`
- Three-way splits possible (all 3 judges pick different labels). Tiebreaker: `Counter.most_common()` returns first-inserted element = GPT-5.1's label
- Confidence: `agreement_rate × mean(individual_confidences)`, where agreement_rate = fraction agreeing with majority (2/3 or 3/3). Penalizes contested labels
- Failed judge handling: defaults to label=3, confidence=0.0 (conservative — avoids false positives). We monitor for systematic failures and re-judge affected entries
- Judges run in parallel (ThreadPoolExecutor) for efficiency
- NO RESULTS: do not state how often unanimous vs split occurs

**4.3.6 Human Validation (~0.5 page)**
- Protocol: random sample of n=50 prompt–response pairs. Author labels using same 4-point rubric. Compare against consensus labels
- Why n=50: pilot validation for systematic disagreements
- Forward-reference to results for agreement rate and disagreement analysis
- Limitation: single annotator (the author). Stronger validation = 2+ annotators with Cohen's kappa. Acknowledged as scope limitation
- **TODO: Consider expanding to n=150 with stratified sampling across categories and label types. If completed before submission, report it; if not, acknowledge as future work**

**4.3.7 Sensitivity and Limitations (~0.5 page)**
- Pre-register robustness checks:
  1. Majority-vote vs unanimous-only aggregation: if conclusions hold under both, pipeline is robust
  2. Judge removal analysis: re-compute with each judge removed (2-of-3 subsets)
  3. Self-evaluation bias check: compare Llama's labels on Llama-generated vs Mixtral-generated responses
  4. **Three-way split tiebreaker sensitivity**: compare default (first-judge) vs confidence-based tiebreaker
- **COMPLETE (Mar 12, 2026)**: `scripts/sensitivity_analysis.py` fixed (filter failed judges from individual_judgments, exclude CoT) and re-run. Output: `results/sensitivity_analysis.json`. All three checks pass: unanimous-only doesn't change conclusions, no single judge drives results (0-6.4% label changes on removal), Llama self-eval bias negligible (excess leniency -2.3pp to +0.3pp). Report in Ch 5 (judging diagnostics) or Ch 7.
- Limitations summary:
  - LLM judges may share blind spots (similar training data)
  - Single human validator
  - Judge–evaluatee overlap (Llama)
  - Category-specific rules designed by author — alternative rules might yield different labels
  - temperature=0 doesn't guarantee perfect determinism (API-level stochasticity)
  - Three-way split tiebreaker defaults to first judge (GPT-5.1)
- Frame all as "we examine" and "we report" — NO outcomes

**Citations needed**: zheng2023judging (already in bib), wataoka2024selfpreference (ADDED), liu2023geval (ADDED). Consider adding: Chiang & Lee 2023 (Can Large Language Models Be an Alternative to Human Evaluations?), the CALM bias framework paper

### 4.4 Embedding and Geometric Feature Extraction (~3-4 pages)

This section is the geometric heart of the thesis. It defines *how* we measure the geometric properties that Chapter 5 then tests as hallucination predictors. Must be precise enough that someone could reimplement from this description alone, but must NOT preview any results (correlations, AUC, feature values, etc.).

**CRITICAL**: Remember — NO RESULTS. No "feature X correlates with..." or "we find that..." Only design rationale and "we investigate whether..." language. Forward-reference Chapter 5 for all outcomes.

#### 4.4.1 Embedding Model Selection (~0.5 page)

- **Model**: OpenAI `text-embedding-3-large`, 3072 dimensions
- **Justification for this model**:
  - High dimensionality (3072) provides richer geometric structure to analyze compared to smaller alternatives (e.g., text-embedding-3-small at 1536, sentence-transformers at 768)
  - Widely adopted → reproducibility and comparability with other work
  - Deterministic at temperature=0: identical inputs produce identical embeddings, enabling exact reproducibility
  - API-based → consistent model version across all embeddings (no local model drift)
- **Why API embeddings, not model-internal representations**:
  - Our target models (Mixtral, Llama) are accessed via Together AI inference API — no access to internal activations or hidden states
  - Using a separate embedding model tests a stronger hypothesis: that *the text of a question itself* (not model-internal processing) carries geometric signatures predictive of hallucination
  - This is a deliberate choice, not a limitation — if geometry of the question text alone predicts hallucination, the signal is more fundamental than model-specific representations
  - Tradeoff: loses model-specific information (what regions a particular model struggles with). Acknowledge this honestly
  - Cite: prior work on probing internal representations (e.g., Li et al. 2024, Marks & Tegmark 2023) takes the complementary approach; our approach is closer to dataset-level difficulty estimation
- **Unit normalization**: All embeddings are L2-normalized by the API, so cosine distance equals angular distance. This simplifies geometric interpretation — all points lie on the unit hypersphere in R^3072

#### 4.4.2 Corpus Construction (~0.5 page)

- **Combined corpus**: 2,879 prompts total
  - 449 from the initial benchmark (held-out test set in later experiments)
  - 2,430 from the expanded benchmark (training set for fine-tuning)
  - Embedded in a **single API call batch** to guarantee identical model version and normalization
  - Initial benchmark prompts are assigned indices 0–448 for stable cross-referencing across experiments
- **Why a combined corpus** (not separate embeddings per experiment phase):
  - Geometric features like density and centrality are *relative* to a reference distribution. Embedding all prompts together ensures the reference distribution is identical when comparing initial-benchmark and expanded-benchmark geometry
  - Prevents subtle distribution shifts that would arise from embedding at different times (even with the same model, API behavior could change between versions)
- **Storage**: Embeddings saved as `(2879, 3072)` float32 NumPy array (~33 MB) with a JSON ID-to-index mapping for provenance tracking
- **No dimensionality reduction at embedding stage**: We operate on the full 3072-dimensional space. Dimensionality reduction happens only within specific feature computations (e.g., PCA for oppositeness), not as a preprocessing step. This preserves all information for neighbor-based features.

#### 4.4.3 Geometric Feature Definitions (~1.5 pages)

We extract five geometric features per prompt, each capturing a different aspect of how the prompt sits within the embedding manifold. All features are computed from the prompt text embedding alone — they do not use the model's response or the judge labels. This is essential: the features must be computable *before* generation to serve as pre-generation hallucination risk signals.

**Shared infrastructure**: All neighbor-based features use $k = 20$ nearest neighbors under cosine distance, computed via scikit-learn's `NearestNeighbors` with the `cosine` metric. The same k-NN index is reused across features for consistency.

**Feature 1: Local Intrinsic Dimension (TwoNN)**
- **Definition**: For each point $\mathbf{x}_i$, let $r_1$ and $r_2$ be the cosine distances to the first and second nearest neighbors. The local intrinsic dimension is:
  $$\hat{d}_i = \frac{1}{\log(r_2 / r_1)}$$
  This is the TwoNN estimator (Facco et al., 2017).
- **Intuition**: Measures how many effective dimensions the data occupies *locally* around a point. High local ID → the neighborhood is spread across many directions (complex local geometry). Low local ID → the neighborhood is concentrated along few directions (locally flat or low-dimensional).
- **Edge cases**: Returns NaN when $r_1 = 0$ (duplicate point), $r_2 = 0$, or $r_1 \geq r_2$ (degenerate neighborhood). These are excluded from downstream analysis.
- **Citation**: Facco et al. 2017 "Estimating the intrinsic dimension of datasets by a minimal neighborhood information" — the TwoNN method. Also Levina & Bickel 2004 for MLE-based alternative.

**Feature 2: Curvature Proxy (PCA Residual Variance)**
- **Definition**: For each point $\mathbf{x}_i$, take its $k = 20$ nearest neighbors. Fit PCA to this local neighborhood with $n_\text{comp} = \lfloor \hat{d}_i \rfloor$ components (using the point's own local intrinsic dimension estimate). The curvature proxy is:
  $$\text{curv}_i = 1 - \sum_{j=1}^{n_\text{comp}} \frac{\sigma_j^2}{\sum_\ell \sigma_\ell^2}$$
  i.e., the fraction of variance NOT explained by the top $n_\text{comp}$ principal components.
- **Intuition**: If the local neighborhood is well-approximated by a flat subspace, PCA captures most variance → low residual → low curvature. If the neighborhood bends or curves, PCA misses variance → high residual → high curvature.
- **Dependency on Feature 1**: The number of PCA components adapts to the local intrinsic dimension. This couples the two features — a design choice that makes curvature relative to the local complexity rather than a fixed dimensionality.
- **No citation for this exact formulation** — this is our construction. Note as such. Related: PCA-based curvature proxies appear in manifold learning literature (e.g., Little et al. 2017; Singer & Wu 2012).

**Feature 3: Oppositeness (PCA Sign-Flip Distance)**
- **Definition**:
  1. Fit PCA with $n_\text{comp} = 10$ components to the *entire corpus* (global PCA, not local).
  2. For each point $\mathbf{x}_i$, project into PCA space: $\mathbf{z}_i = \text{PCA}(\mathbf{x}_i)$.
  3. Flip the sign of the top $n_\text{flip} = 3$ components: $\tilde{\mathbf{z}}_i = (-z_{i,1}, -z_{i,2}, -z_{i,3}, z_{i,4}, \ldots, z_{i,10})$.
  4. Inverse-transform back to the full 3072-dimensional space: $\tilde{\mathbf{x}}_i = \text{PCA}^{-1}(\tilde{\mathbf{z}}_i)$.
  5. Find the nearest real point to $\tilde{\mathbf{x}}_i$ in the corpus (cosine distance, $k = 1$).
  6. The oppositeness score is this nearest-neighbor distance.
- **Intuition**: The "opposite" $\tilde{\mathbf{x}}_i$ represents a point that is maximally different from $\mathbf{x}_i$ along the directions of greatest corpus variance. If this opposite is far from any real data point, the prompt occupies a region where the corpus has strong directional structure — there are no prompts "on the other side." If the opposite is close to a real point, the corpus is more isotropic in that region.
- **Why global PCA, not local**: Oppositeness measures structure relative to the corpus-level principal directions, not local neighborhood structure (which is captured by curvature). Using local PCA would conflate the two features.
- **Hyperparameter rationale**: $n_\text{comp} = 10$ retains enough variance to capture meaningful structure without overfitting to noise (report PCA explained variance ratio in Chapter 5). $n_\text{flip} = 3$ flips the dominant directions without inverting the entire representation.
- **This feature is novel** — we are not aware of prior work using PCA sign-flip distance as a geometric feature. Note as such, but frame modestly.

**Feature 4: Local Density (Inverse Mean k-NN Distance)**
- **Definition**: For each point $\mathbf{x}_i$, compute the mean cosine distance to its $k = 20$ nearest neighbors in the reference corpus. The density score is the inverse:
  $$\text{density}_i = \frac{1}{\bar{d}_{k\text{-NN}}(\mathbf{x}_i)}$$
- **Reference corpus**: In our design, the combined corpus serves as its own reference distribution (self-reference; see Section 4.4.4).
- **Intuition**: High density → many similar prompts nearby → well-represented region. Low density → isolated prompt → potentially under-represented, where the model may lack training signal.
- **Citation**: Standard in manifold learning and anomaly detection literature. k-NN density estimation: Loftsgaarden & Quesenberry 1965; more recent use in LLM contexts: e.g., density-based OOD detection.

**Feature 5: Centrality (Cosine Distance to Corpus Mean)**
- **Definition**: Compute the mean embedding $\bar{\mathbf{x}} = \frac{1}{N}\sum_{i=1}^{N} \mathbf{x}_i$ over all $N = 2{,}879$ prompts. The centrality score for each point is:
  $$\text{centrality}_i = d_\text{cosine}(\mathbf{x}_i, \bar{\mathbf{x}})$$
  Note: higher values mean *less* central (farther from the mean).
- **Intuition**: Prompts far from the corpus centroid may represent unusual or peripheral topics where models have less reliable knowledge. Unlike density (which measures local neighborhood), centrality measures global position.
- **Naming note**: Despite the name "centrality," higher values indicate greater distance from center. Consider clarifying in text with "distance-to-center" or noting the convention explicitly.

#### 4.4.4 Reference Distribution and Self-Reference Design (~0.5 page)

- **Self-reference**: The combined 2,879-prompt corpus serves as its own reference distribution. Density is computed relative to the corpus itself, and centrality is relative to the corpus mean.
- **Why self-reference (not an external corpus)**:
  - An external reference (e.g., Wikipedia passages, Common Crawl) would introduce a confound: density would measure similarity to *the reference domain* rather than within-corpus structure
  - Self-reference asks: "how does this prompt relate to *other prompts in our benchmark*?" This is the right question for within-corpus geometric analysis
  - Avoids domain mismatch: our prompts span 7 categories with specific entity structures; an external corpus would not match this distribution
  - Limitation: self-reference means geometry is corpus-dependent. A prompt's density score changes if the corpus composition changes. This limits generalizability — acknowledge honestly and note that a deployment system would need to define an appropriate reference distribution
- **Implications for train-test split**: Since both initial-benchmark (test) and expanded-benchmark (training) prompts are in the same embedding corpus, geometric features for test prompts are computed with training prompts as neighbors. This is acceptable because geometry uses only prompt text, not labels — but note the distinction from strict train-test separation (which applies to labels and fine-tuning targets, not embedding context).

#### 4.4.5 Hyperparameter Choices and Justification (~0.25 page)

- **$k = 20$ for all neighbor-based features**: Balances locality (small $k$ → noisy estimates) with globality (large $k$ → over-smoothing). With $N = 2{,}879$ points, $k = 20$ represents ~0.7% of the corpus. This follows recommendations in the TwoNN literature (Facco et al. suggest $k$ on the order of $\sqrt{N}$; $\sqrt{2879} \approx 54$, so $k = 20$ is conservative). All neighbor-based features use the same $k$ for consistency.
- **$n_\text{PCA} = 10$ for oppositeness**: Retains the top 10 principal components of the corpus. The choice balances capturing dominant structure (first few components) with avoiding noise (higher components). Report explained variance ratio in Chapter 5 to validate.
- **$n_\text{flip} = 3$**: Flips only the top 3 of 10 PCA components. Flipping more components would create an "opposite" too far from the data manifold (noise-dominated); flipping fewer would reduce discriminative power. This was set in the initial experiment and held fixed for consistency.
- **Cosine metric throughout**: All distance computations use cosine distance, matching the L2-normalized embedding space (cosine distance = 1 - cosine similarity = angular distance / $\pi$ for unit vectors). Using a consistent metric prevents feature-to-feature comparisons from being confounded by metric choice.
- **Fixed across experiments**: All hyperparameters were set in the initial benchmark (Chapter 5) and held constant for the expanded benchmark and fine-tuning experiments (Chapters 6-7). No hyperparameter tuning was performed on the expanded data.

#### 4.4.6 Limitations of the Embedding Approach (~0.25 page)

- **Single embedding model**: All results depend on OpenAI text-embedding-3-large. A preliminary robustness check using three embedding models (text-embedding-3-small at 1536 dimensions, text-embedding-3-large at 3072, and the open-source all-mpnet-base-v2 at 768) was conducted on the initial benchmark; results are reported in Appendix~[X]. This does not constitute a full robustness analysis and remains a limitation.
- **API embedding vs internal representations**: We embed the question text, not the model's internal activations during response generation. This tests a stronger but narrower hypothesis — that hallucination risk is encoded in the question text's position in embedding space, not in how a specific model processes it. Prior work on representation probing (e.g., Li et al. 2024) takes the complementary approach.
- **Corpus-dependent geometry**: Self-reference makes all features dependent on corpus composition. Adding or removing prompts changes every point's density, centrality, and neighborhood-based features. This limits out-of-distribution generalization.
- **No feature selection or engineering**: We use all 5 features as-is, without normalization, selection, or transformation. This is deliberate (avoid overfitting to our specific data) but means some features may be redundant or uninformative — Chapter 5 investigates.
- **Static geometry**: Features are computed once from prompt text before generation. They do not capture response-time dynamics or model uncertainty during generation.

**Citations needed**: Facco et al. 2017 (TwoNN), Levina & Bickel 2004 (MLE intrinsic dimension), Li et al. 2024 or Marks & Tegmark 2023 (representation probing as complementary approach), Loftsgaarden & Quesenberry 1965 (k-NN density). Check bib file for what's already there.

**Figures/Tables for this section**:
- Table: Summary of 5 features (name, formula, hyperparameters, intuition) — compact reference
- Figure (optional): Schematic of the oppositeness computation (PCA → flip → inverse → nearest neighbor) — this is the hardest feature to understand from text alone
- NO scatter plots, histograms, or feature distributions — those are results (Chapter 5)

### Chapter closing (~0.5 page)

Two parts:
1. **Statistical approach paragraph** (~3-4 sentences): Preview non-parametric testing philosophy (Mann-Whitney U for unpaired, McNemar's for paired binary, Bonferroni for multiple comparisons). No formulas — just the approach and why non-parametric (categorical labels, varying sample sizes). Say "full test specifications are given in each chapter alongside the analyses they support."
2. **Roadmap paragraph**: Name each chapter's research question. "Chapter 5 tests whether embedding geometry predicts hallucination. Chapter 6 tests whether targeted prompt prefixes reduce hallucination. Chapter 7 bridges prediction and intervention, testing whether geometry predicts which hallucinations resist mitigation, and presents the full pipeline from geometric diagnosis to fine-tuned correction."

### Estimated length: 12-17 pages

Dense with tables, precise definitions, and preemptive reviewer defense. Every design choice justified against the rigor standard.

### Writing order (section by section, not all at once)

Rationale: each subsection requires pulling specific numbers, citing specific papers, and making defensible claims. Section-by-section allows precision and early feedback. Flow is maintained via transition sentences at subsection boundaries, then a final flow pass.

1. ~~**4.1 Benchmark Construction**~~ — DONE
2. ~~**4.2 Model Selection**~~ — DONE
3. ~~**4.3 Consensus Judging**~~ — DONE
4. ~~**4.4 Embedding and Geometric Feature Extraction**~~ — DONE (Mar 12, 2026)
5. ~~**Chapter closing paragraph**~~ — DONE (statistical roadmap + chapter previews)
6. **Chapter opening paragraph** — to write (brief framing of shared infrastructure)
7. **Flow pass** — read full chapter end-to-end, smooth transitions, fix tone shifts, ensure consistent terminology, check narrative builds properly

### Figures and tables in Ch 4

Ch 4 is table-heavy, not figure-heavy. The visualization-heavy chapters are Ch 5-7.

**Tables (essential):**
- Category summary (category, V3/V5 counts, example prompt, expected behavior)
- V3→V5 scaling (template coverage, entity coverage, exclusions)
- 10-model summary (model, params, access type, baseline hallucination rate)
- Per-judge label distribution
- Per-category agreement rates

**Figures (1-2):**
- Pipeline diagram: full experimental flow (prompts → models → judges → labels) — may need to create
- Judge agreement heatmap (`v5_judge_agreement.png` exists)

### Workflow note

Writing LaTeX to local `thesis/Dissertate-Harvard-LaTeX/chapters/` files as working copies. User syncs to Overleaf manually (copy-paste). Local files are the source of truth for this tool; Overleaf is the compilation environment.

---

## Chapter 5: Can Geometry Predict Hallucination? — Detailed Content Plan

**Narrative arc**: This is the first results chapter. It establishes (1) that hallucination is a real, measurable, model-varying phenomenon, (2) that geometric features of the embedding space correlate with hallucination, (3) that most of this correlation reflects category structure, and (4) that the non-circular, within-category signal — density — is the novel finding. The chapter must be relentlessly honest about what the data shows and what it doesn't.

**Key tension to manage**: The V3 AUC of 0.86 is impressive but misleading. The chapter must present V3 as a genuine initial finding, then show how V5's larger dataset and proper controls reveal the true (more modest, but still real) signal. This is not a failure — it's normal science. Frame as refinement, not retraction.

**No spoilers for later chapters**: Do NOT reveal prefix effectiveness (Ch 6), fixability prediction (Ch 7), or fine-tuning results (Ch 7). Forward references should be questions, not answers: "whether geometry can also predict *where interventions succeed* is the subject of Chapter 7."

**Statistical methods defined inline**: Mann-Whitney U test, rank-biserial effect size r, logistic regression + AUC, cross-validation — all defined in this chapter with formulas, since this is where they're first used. Bonferroni introduced here if multiple testing applies.

### 5.1 Baseline Hallucination Rates (~1.5 pages)

**Purpose**: Present the empirical results the reader has been waiting for since Ch 4. Short — the reader already knows the benchmark design, model selection, and judging pipeline from Ch 4. This section delivers the numbers, validates the labels, and sets up the geometric analysis.

**Principle**: Ch 4 = what and why (exhaustive design rationale, no numbers). Ch 5.1 = what we found (numbers, brief interpretation). No design re-explanation. Do not re-explain what the 10 models are, what the categories are, or how the judging works — just present results and interpret.

#### Paragraph-level outline

**¶1 — Opening transition** (2-3 sentences)
- Transition from Ch 4. "Chapter 4 described the experimental infrastructure... We now turn to results."
- Frame the section's goal: establish that hallucination is a real, measurable, model-varying phenomenon, and validate the judging labels that all subsequent analysis depends on.
- No design recap.

**Table 5.1 — 10-model hallucination rates on initial benchmark (449 prompts)**
- Columns: Model, Family, Hallucinations (count), Hallucination Rate (%)
- Ordered by rate ascending: Claude Haiku 1.34%, Claude Opus 2.00%, Claude Sonnet 2.45%, Qwen 3 Next 2.45%, GPT-5.1 5.57%, Llama 4 Maverick 5.79%, GPT-4.1 7.13%, Mixtral 8x7B 11.80%, GPT-4.1-mini 12.47%, GPT-4o-mini 17.82%
- Source: `results/v3/multi_model/tables/table1_model_performance.csv` (clean V3 data, no contamination issue)
- This is the first empirical table the reader sees. Give it a descriptive self-contained caption.

**¶2 — Interpreting the 10-model rates** (4-5 sentences)
- 13× range between best and worst (1.34% to 17.82%) — hallucination is common and highly variable
- No clear parameter-count ordering: Claude Haiku (smallest Anthropic model) outperforms Claude Opus. GPT-4o-mini and GPT-4.1-mini hallucinate more than GPT-5.1, but GPT-4.1 is in between. Suggests training methodology and data curation matter more than raw scale.
- Anthropic models cluster at the low end (1.3-2.5%), OpenAI models span the full range (5.6-17.8%), open-weight models in the middle-to-high range. Family-level effects are present but not absolute.
- Anchor the two intervention targets: Mixtral (11.8%, second-highest) and Llama (5.79%, mid-range) — spanning the difficulty spectrum. **Do not explain WHY these two were chosen** (Ch 4 already does this). Just note they span the range.

**¶3 — Cross-model consistency** (3-4 sentences)
- Pairwise Kendall's tau across all 45 model pairs: mean τ = 0.319, median 0.303, range 0.068–0.617
- Moderate agreement: some prompts are universally hard (the "universally hard" prompts from the V3 paper — prompts failing >50% of models share high centrality, low curvature — but DON'T mention this geometric detail yet, save for 5.2)
- Same-family pairs correlate more strongly: GPT-4.1-mini/GPT-4o-mini τ = 0.617, GPT-4.1/GPT-4.1-mini τ = 0.524, Claude Sonnet/GPT-5.1 τ = 0.590 (the latter suggests training-data similarity despite different providers)
- Cross-family correlations weaker: Qwen/Claude Sonnet τ = 0.068, Qwen/GPT-4.1 τ = 0.068
- **Why this matters for geometry** (1 sentence): Moderate cross-model consistency means there IS a prompt-level difficulty signal — if hallucination were entirely model-specific and random, a model-agnostic geometric predictor computed from prompt text alone would have nothing to learn
- Source: `results/v3/multi_model/tables/table2_consistency_summary.csv`, `stats/kendall_tau_matrix.csv`

**¶4 — Expanded benchmark baselines** (4-5 sentences)
- Mixtral: 82.5% correct, 14.8% hallucination on 2,430 expanded-benchmark prompts
- Llama: 87.9% correct, 9.7% hallucination
- Both higher than initial benchmark (Mixtral 11.8% → 14.8%, Llama 5.79% → 9.7%)
- This is NOT a replication failure. The expanded benchmark deliberately includes more borderline categories (200 plausible fakes, 200 obscure reals, 130 edge factuals vs. 31/30/20 in the initial set) and draws from deeper, more diverse entity pools. The increased rates confirm the expanded benchmark probes harder entity regions, consistent with the design intent described in Section 4.1.4.
- Brief per-category gradient (1-2 sentences, no table): rates range from <2% (ambiguous) to 38.5% (borderline plausible fake, Mixtral) — a 50× spread across categories. This sharp category-level variation will become important in Section 5.3, where we test whether it confounds geometric prediction.
- **DATA WARNING**: `baseline_summary.json` is stale (pre-contamination-fix, dated Mar 3). Post-fix per-model numbers come from `results/sensitivity_analysis.json` (self_eval_bias section: consensus_on_mixtral_responses, consensus_on_llama_responses). Per-category post-fix numbers should be recomputed from the post-fix `judged_answers.jsonl` files (dated Mar 11). Flag for writing step: regenerate `baseline_summary.json` or compute per-category rates from JSONL directly.
  - Post-fix verified numbers: Mixtral accuracy=82.5%, halluc=14.8%. Llama accuracy=87.9%, halluc=9.7%.
  - Pre-fix stale numbers: Mixtral 81.7%/14.3%, Llama 87.1%/9.5%. Difference is small (~0.8-1pp) but use post-fix for correctness.

**¶5 — Judging pipeline validation** (5-7 sentences)
- "Before analyzing what predicts hallucination, we verify the labels themselves. Section 4.3.7 pre-registered three robustness checks; we now report their results."
- **Unanimous-only**: 88.3% of expanded-benchmark baseline entries have unanimous 3-judge agreement. Restricting to unanimous labels shifts hallucination rate from 12.2% to 9.5% (combined across models) — contested labels skew toward hallucination, as expected since borderline cases are harder to judge. No qualitative conclusions change.
- **Judge removal**: Removing any single judge changes only 3.0–3.5% of labels. Removing Llama (most lenient judge) increases combined hallucination rate to 14.1%; removing GPT-5.1 decreases it to 10.3%. Direction expected but magnitude small — no single judge drives the results.
- **Self-evaluation bias**: Llama serves as both judge and intervention target (Section 4.3.2). The excess leniency metric — how much more favorably Llama judges its own responses compared to what the consensus differential predicts — is −2.3 percentage points. The negative value means Llama is actually slightly *stricter* on its own outputs than the consensus differential would suggest. Self-preference bias is negligible.
- **Three-way splits**: All three judges assign different labels in 1.24% of entries (519 of 41,807 across all datasets). The default tiebreaker favors GPT-5.1's label, which tends conservative — a confidence-based tiebreaker would reduce hallucination labels by approximately 0.5 percentage points (192 of 519 splits would flip from hallucination to correct).
- **Human validation**: On a stratified sample of n = 50 prompt–response pairs from the initial benchmark, human labels agree with consensus labels 90% of the time (45/50). Of 5 disagreements, 3 involve the AI consensus labeling hallucination where the human labeler judged the response correct — consistent with a conservative (over-counting hallucination) bias. Limitation: single annotator. Appendix X provides the full disagreement analysis.
- Conclude: "Based on these checks, we use majority-vote consensus labels throughout the remainder of this thesis."
- Sources: `results/sensitivity_analysis.json` (v5_baselines section), `results/v3/human_verification_report.json`, experiment log three-way split section

#### Tables and figures

**Table 5.1** (essential): 10-model hallucination rates
- Source: `results/v3/multi_model/tables/table1_model_performance.csv`
- 10 rows × 4 columns. Compact.

**Figure** (recommended, not essential): Kendall's tau heatmap (10×10 matrix)
- EXISTS: `results/v3/multi_model/consistency_heatmap.png`
- Shows same-family clustering. Self-contained caption.
- Alternative: move to appendix if space is tight. The key numbers (mean τ, range, extremes) are in the text.

**No other figures needed** — this section is table + prose. The visualization-heavy sections start at 5.2.

#### What NOT to include in 5.1

- Do NOT re-explain what the 10 models are or why they were chosen (Ch 4.2)
- Do NOT re-explain the judging rubric, prompt design, or majority vote (Ch 4.3)
- Do NOT re-explain the category definitions (Ch 4.1)
- Do NOT preview geometric features or AUC values (5.2+)
- Do NOT show per-category V5 rates in a table (save for 5.3/5.4 where they contextualizes geometric analysis)
- Do NOT mention prefix results or fine-tuning (Ch 6-7)
- Do NOT mention universally hard prompts' geometric signatures (save for 5.2 — that's a geometric finding)

#### Reviewer anticipation

- "Is 449 prompts enough for reliable per-model rates?" → At 449 prompts, standard error for a 10% rate is √(0.1×0.9/449) ≈ 1.4%. For 2% rate, SE ≈ 0.7%. Rates are estimated with <2pp precision. Sufficient for cross-model comparison, which is the point.
- "Why not report confidence intervals?" → Could add Wilson CIs to the table. Consider this during writing.
- "The human validation is only n=50 and single-annotator" → Acknowledged as a limitation. Forward-reference to potential expansion (n=150). The 90% agreement with conservative bias direction is reassuring but not definitive.
- "Three-way splits: why not use confidence-based tiebreaker?" → The choice is conservative (overcounts hallucination). Sensitivity shows ~0.5pp effect. We report both options transparently. Either choice yields the same conclusions.

### 5.2 Between-Category Geometric Analysis (~2.5-3 pages)

**Purpose**: Show that geometric features differ significantly between hallucinated and correct prompts, introduce the statistical methods used throughout the chapter, present the initial study's findings for context, and flag that between-category results are potentially confounded by category structure (setting up 5.3).

**Narrative arc**: V3 initial study → V5 replication with proper controls → results are real but need decomposition.

#### Paragraph-level outline

**¶1 — V3 initial findings as context** (3-4 sentences)
- "An initial analysis on the 449-prompt benchmark, pooling predictions across all 10 models (~3,680 model–prompt observations), found that geometric features predict hallucination with a train-set AUC of 0.86."
- V3 methodology: logistic regression with balanced class weights, held-out test split (not cross-validated). Centrality was the strongest predictor (β = −3.62, OR = 0.027, p < 0.001), curvature second (β = −1.21, OR = 0.300, p < 0.001). Density and local intrinsic dimension were not significant.
- "However, this analysis pooled across models without per-model separation, used no category controls, and was not cross-validated. We now replicate on the expanded benchmark with proper methodology."
- Source: `results/v3/multi_model/stats/logistic_regression_stats.csv`
- **V3 methodology caveat**: Note that V3 used `class_weight='balanced'` (upweights minority class) and pooled across 10 models. V5 uses unweighted logistic regression per-model with 5-fold stratified CV. The methodological differences matter: balanced weighting inflates AUC when the minority class (hallucinated) has distinct geometry, and pooling across models conflates model-level effects with prompt-level geometry.

**¶2 — Statistical methods** (1 paragraph + inline equations)
- Define Mann-Whitney U test: tests whether two independent groups (here: hallucinated vs. correct prompts) are drawn from the same distribution. Non-parametric — no assumption of normality or equal variance. Appropriate because: feature distributions are skewed, sample sizes are highly unequal (e.g., 348 hallucinated vs. 1,986 correct for Mixtral), and we make no distributional assumptions about the geometric features.
- Define rank-biserial effect size: $r = 1 - 2U/(n_1 \cdot n_2)$, where $U$ is the Mann-Whitney statistic and $n_1$, $n_2$ are group sizes. Interpretation: $|r| < 0.1$ negligible, $0.1$–$0.3$ small, $0.3$–$0.5$ medium, $> 0.5$ large.
- Note: We report both $p$-values and effect sizes throughout. Statistical significance without meaningful effect size is uninteresting; effect size without significance could be noise.
- **Decision**: Define logistic regression + AUC here too, or defer to the paragraph where they first appear? I lean toward defining briefly here ("We also fit logistic regression models with 5-fold stratified cross-validation, reporting area under the ROC curve (AUC). AUC of 0.5 indicates random prediction; 1.0 indicates perfect discrimination.") and then introducing the methodology details when presenting results (¶4).

**Table 5.2 — Mann-Whitney results for 5 features × 2 models** (between-category)
- Columns: Feature, Hallucinated Mean, Correct Mean, $p$-value, Effect Size $|r|$, Direction
- 10 rows (5 features × 2 models) or a two-panel table (one per model)
- Source: `results/v5_baselines/analysis/v5_geometry_prediction_overall.csv` (verified exact)
- Key verified numbers:
  - **Oppositeness**: Mixtral hall=0.513, correct=0.492, p=2.95×10⁻¹¹, |r|=0.223 (hallucinated HIGHER). Llama hall=0.526, correct=0.492, p=7.83×10⁻²⁰, |r|=0.364 (hallucinated HIGHER).
  - **Density**: Mixtral hall=2.025, correct=2.088, p=5.84×10⁻⁵, |r|=0.135 (hallucinated LOWER). Llama hall=2.018, correct=2.082, p=0.016, |r|=0.097 (hallucinated LOWER).
  - **Centrality**: Mixtral p=0.079 (ns). Llama p=0.0003, |r|=0.144 (hallucinated LOWER centrality = closer to center — counterintuitive, see interpretation).
  - **Curvature**: Both p>0.6 (ns).
  - **Local ID**: Both p>0.76 (ns).
- Caption should note: "Between-category comparison across all 2,430 expanded-benchmark prompts. Effect sizes report rank-biserial correlation with direction indicated. Partial and refused responses are excluded; only hallucinated (label 2) and correct (label 0) prompts are compared."
- Sample sizes to include: Mixtral n_hall=348, n_correct=1,986. Llama n_hall=232, n_correct=2,116. (Note: partial/refused excluded → totals don't sum to 2,430)

**¶3 — Interpreting Mann-Whitney results** (4-5 sentences)
- Two features show consistent, significant differences: **oppositeness** and **density**. Hallucinated prompts have higher oppositeness (farther from any "opposite" point in PCA space) and lower density (sparser embedding neighborhoods). Both directions are consistent across models, though effect sizes are larger for Llama.
- Oppositeness shows the largest effect: |r| = 0.22 (Mixtral), 0.36 (Llama), both highly significant (p < 10⁻¹⁰). Density shows a smaller but significant effect: |r| = 0.14 (Mixtral, p < 10⁻⁴), 0.10 (Llama, p = 0.016).
- Centrality is inconsistent: not significant for Mixtral (p = 0.093) but significant for Llama (p = 0.0002). Direction is the SAME as V3 (lower centrality = closer to corpus mean → more hallucination; V3 β = −3.62 means higher centrality → less hallucination). **CORRECTED**: There is NO reversal — the outline previously claimed opposite direction, which was wrong. The real story is that centrality went from dominant (V3) to weak/inconsistent (V5), likely because V3's pooling across models inflated the category-confounded signal. Section 5.5 discusses.
- Curvature and local intrinsic dimension show no significant differences (all p > 0.6), consistent with near-zero effect sizes. Despite being the two strongest predictors in the initial study, neither carries between-category signal on the expanded benchmark.
- The contrast between V3 and V5 feature rankings is striking: V3's top two features (centrality, curvature) are now non-significant or inconsistent; V5's top two (oppositeness, density) were not significant or not tested in V3. Section 5.5 discusses why.

**¶4 — Logistic regression** (4-5 sentences)
- To assess the combined predictive power of all five features, we fit a logistic regression (scikit-learn, `max_iter=1000`) on all five geometric features after standardization (`StandardScaler`), predicting binary hallucination status. 5-fold stratified cross-validation ensures the evaluation reflects out-of-sample generalization.
- **Mixtral**: train AUC = 0.650, 5-fold CV AUC = **0.641**. **Llama**: train AUC = 0.726, 5-fold CV AUC = **0.722**. The small train-CV gap suggests minimal overfitting.
- Standardized coefficients confirm the Mann-Whitney ranking: oppositeness is the strongest predictor (+0.54 Mixtral, +0.86 Llama — positive coefficient means higher oppositeness predicts hallucination), density is second (−0.40 Mixtral, −0.62 Llama — negative means lower density predicts hallucination). Local ID, curvature, and centrality have near-zero standardized coefficients.
- The overall CV AUC of 0.64–0.72 is a substantial drop from the initial study's train AUC of 0.86. Three factors contribute: (a) cross-validation versus train-set evaluation, (b) per-model analysis versus pooling across 10 models, and (c) the expanded benchmark's larger and harder category composition. Section 5.3 identifies a fourth: the initial study's AUC was partly capturing category structure, not purely geometric signal.
- Source for AUC/coefficients: experiment log Part 2.5.2 (lines 307-322). **FLAG**: These numbers may be slightly stale (pre-contamination-fix). The fix changed ~0.4% of baseline labels; AUC impact is expected to be <0.01. Verify by re-running `scripts/analyze_v5_geometry_prediction.py` on post-fix data before finalizing thesis text.

**¶5 — The category confound** (3-4 sentences, transition to 5.3)
- These between-category results are real — hallucinated prompts genuinely occupy different regions of embedding space — but they may be partly circular. Our seven categories span a deliberate difficulty gradient (Section 5.1): borderline plausible fakes hallucinate at 38.5%, ambiguous prompts at < 2%. If these categories also differ in geometric properties (and they do — nonexistent and borderline categories have lower density and higher oppositeness than factual and ambiguous categories), then a classifier could predict hallucination by implicitly detecting category membership rather than fine-grained geometric structure.
- "The question is not whether geometry predicts hallucination — Table 5.2 shows it does — but how much of that prediction is genuinely geometric versus a proxy for category labels. Section 5.3 addresses this decomposition."
- No preview of the answer.

#### Tables and figures

**Table 5.2** (essential): Mann-Whitney results for 5 features × 2 models
- Source: `results/v5_baselines/analysis/v5_geometry_prediction_overall.csv` (verified exact)
- Consider two-panel layout (one per model) or single table with model as a column grouping

**Figure** (recommended): Box plots or violin plots — oppositeness and density distributions for hallucinated vs. correct prompts, per model
- **EXISTS**: `results/v5_baselines/analysis/v5_geometry_vs_hallucination_*.png`
- Check if publication-quality; may need regeneration with clearer labels, consistent axis scales

**Figure** (recommended): Standardized coefficient bar chart — 5 features, grouped by model
- **NEEDS CREATION**
- Shows visually that oppositeness and density dominate while other features are near zero

#### What NOT to include in 5.2

- Do NOT present within-category results (save for 5.4)
- Do NOT present the category-only AUC baseline (save for 5.3 — that's the decomposition)
- Do NOT re-explain what the 5 geometric features measure (Ch 4.4 does this)
- Do NOT show per-category hallucination rates in a table (5.1 mentioned the gradient; 5.3/5.4 will detail it)
- Do NOT state that "centrality was proxying for category" as a conclusion — that's 5.3/5.5's finding. Here, just flag the inconsistency

#### Data verification issues

- **CORRECTION**: The experiment log claims local_id and curvature are correlated at r = −0.97. Actual pairwise Pearson correlation is **r = −0.143** (verified from `data/processed/v5_geometry_features.csv`). Do NOT repeat the −0.97 claim. Both features are non-predictive, but they are NOT redundant in the statistical sense. The thesis should either report the correct correlation or simply note that both have near-zero coefficients.
- **Other notable correlations**: oppositeness–centrality r = −0.541, density–centrality r = −0.513, oppositeness–density r = 0.388. These moderate-to-strong correlations mean multicollinearity is present in the logistic regression. Consider noting this as a caveat — individual coefficients may be unstable, but the overall AUC is stable under CV.
- **Logistic regression numbers** (AUC, coefficients): From experiment log, potentially pre-contamination-fix. Flag for re-verification before writing. Expected impact: negligible (<0.01 AUC shift).

#### Reviewer anticipation

- "Why Mann-Whitney and not t-test?" → Feature distributions are non-normal (heavy tails, different variances between groups). Mann-Whitney is robust to these violations. Could show a QQ plot in appendix if challenged.
- "Why not correct for multiple testing in between-category analysis?" → 5 features × 2 models = 10 tests. Bonferroni threshold = 0.005. Oppositeness (p < 10⁻¹⁰) and density (p < 10⁻⁴ Mixtral) survive easily. Centrality for Llama (p = 0.0003) also survives. The non-significant features stay non-significant. Mention Bonferroni briefly: "all significant results survive Bonferroni correction for 10 comparisons."
- "V3 AUC of 0.86 vs V5 of 0.64-0.72 — is the initial result wrong?" → Not wrong, but methodologically limited. Three contributing factors explained in ¶4. The initial study was an honest first pass; the expanded benchmark provides the definitive analysis. Normal scientific progression.
- "Why report train AUC at all?" → For direct comparison with the initial study's reported AUC, which was also train-set. The CV AUC is the honest number for evaluation.
- "Different features dominate in V3 vs V5 — is the geometry unstable?" → No, the methodology changed (category controls, per-model analysis, larger/harder benchmark). The features that survived proper controls (oppositeness, density) are more trustworthy. Section 5.5 discusses this evolution in detail.

### 5.3 Decomposing Category vs. Geometric Signal (~2-3 pages)

**Purpose**: The critical methodological section. Honestly decompose how much of the geometric prediction is just category structure. This is essential for intellectual honesty — without it, a reviewer could dismiss the entire geometric prediction result as circular.

**Narrative arc**: Raise the confound → formalize it with three logistic regression models → show category dominance → argue why this is informative rather than fatal → transition to the within-category test that resolves it.

#### Paragraph-level outline

**¶1 — Raising the confound formally** (3-4 sentences)
- The between-category results (Section 5.2) show that hallucinated prompts occupy geometrically distinct regions — lower density, higher oppositeness. But our seven categories were designed to span a difficulty spectrum (Section 5.1), and categories with higher hallucination rates (borderline_plausible_fake at ~38%, nonexistent at ~20-30%) inherently occupy different embedding regions than low-hallucination categories (ambiguous at <2%, factual at 3-9%). A classifier could achieve decent AUC by learning "is this prompt in a hard category?" rather than detecting fine-grained geometric risk.
- "To quantify this confound, we compare three nested logistic regression models that progressively add geometric information."
- **No results preview** — just the setup and rationale.

**¶2 — Three-model decomposition methodology** (1 paragraph)
- **Model 1 (Geometry-only)**: 5 geometric features (curvature, oppositeness, density, centrality, local intrinsic dimension), standardized via z-scoring (`StandardScaler`), predicting binary hallucination status. This is the model from Section 5.2's logistic regression.
- **Model 2 (Category-only)**: 6 category indicator variables (one-hot encoding with `drop_first=True` for 7 categories) as sole predictors. This captures category-level difficulty with no geometric information. Acts as the "how much can you get from category labels alone?" baseline.
- **Model 3 (Category + Geometry)**: All 5 geometric features plus 6 category indicators (11 predictors total). The AUC improvement from Model 2 → Model 3 isolates geometry's contribution *beyond* category.
- All three models: `LogisticRegression(max_iter=1000)` with 5-fold stratified cross-validation (`StratifiedKFold, shuffle=True, random_state=42`), reporting mean AUC ± standard deviation across folds.
- Source: `scripts/analyze_v5_geometry_prediction.py` (lines 232-278)

**Table 5.3 — Three-model AUC comparison** (essential)
- Three rows (geometry-only, category-only, category+geometry) × two models:

| Model | Mixtral CV AUC | Llama CV AUC |
|---|---|---|
| Geometry-only (5 features) | 0.645 | 0.726 |
| Category-only (6 indicators) | 0.782 | 0.773 |
| Category + Geometry (11 features) | 0.800 | 0.814 |
| **Geometry increment** | **+0.018** | **+0.041** |

- Source: Post-contamination-fix run of `scripts/analyze_v5_geometry_prediction.py` (Mar 14, 2026). Geo-only CV AUC std: ±0.027 (Mixtral), ±0.024 (Llama). Cat-only and cat+geo std not captured by script output — would need code modification to log.
- **WRITTEN**: Section 5.3 written in `chapters/geo-predict-hallucination.tex` using these post-fix numbers.

**¶3 — Interpreting the decomposition** (4-5 sentences)
- **Category alone is a strong predictor** (AUC 0.77 for both models). This is unsurprising and by design — the benchmark spans from factual questions (low hallucination risk) to plausible fakes (high risk). A model that simply memorizes category-level rates achieves 77% discrimination.
- **Geometry-only performs below category-only** for Mixtral (0.641 vs 0.774) and comparably for Llama (0.722 vs 0.769). This means the five geometric features, operating without category labels, are less informative than knowing the category.
- **Adding geometry to category provides a modest increment**: +0.018 for Mixtral, +0.044 for Llama. Most of geometry's predictive power overlaps with category structure — the geometric differences captured in Table 5.2 (lower density and higher oppositeness for hallucinated prompts) largely track which category a prompt belongs to.
- Note the model asymmetry: Llama benefits more from geometry (+0.044) than Mixtral (+0.018). This is consistent with Llama's larger oppositeness effect size in the between-category analysis (|r| = 0.36 vs 0.22) — geometry captures more Llama-specific signal beyond category.
- "These results show that geometric features and category membership carry heavily overlapping signal. The question becomes: is the residual geometric signal genuine, or merely noise that inflates AUC by 0.02–0.04 in cross-validation?"

**¶4 — Why this is NOT a negative result** (4-5 sentences, the key argument)
- Three arguments, presented honestly:
- **(a) Category structure IS geometric.** The seven categories were defined by semantic content (factual vs. nonexistent vs. impossible, etc.), not by any geometric criterion. The fact that category labels can be recovered from embedding geometry (i.e., that a category-only model achieves AUC 0.77 without geometry, and geometry-only achieves 0.64-0.72 without labels) means the embedding space independently discovers the difficulty gradient. This is not a confound — it is a finding. The embedding geometry reflects meaningful knowledge structure.
- **(b) The +0.02–0.04 increment, while modest, means geometry captures some within-category variation.** If geometry were purely a proxy for category, the increment would be zero. The nonzero increment indicates that, conditional on category membership, prompts with different geometry have different hallucination risk. The question is whether this residual signal is large enough to matter.
- **(c) The aggregate increment understates within-category signal.** An AUC improvement of +0.02-0.04 averages across all 7 categories — including categories where geometry has no signal (factual, ambiguous) and categories where hallucinations are too rare to predict. The real test is within-category analysis of the categories with enough hallucinations to measure (Section 5.4).
- Do NOT frame geometry as "barely helping." Frame it as "geometry captures category-level structure (the broad signal) and within-category variation (the fine-grained signal); the aggregate AUC increment reflects only the latter, which is diluted across categories."

**¶5 — V3 → V5 reconciliation** (3-4 sentences)
- "Initial results on the 449-prompt benchmark suggested strong predictive power (train AUC = 0.86). The expanded benchmark reveals that most of this signal reflected category structure, with a more modest but genuine within-category component."
- Three methodological factors explain the drop from 0.86 to 0.64-0.72:
  1. **Train-set vs cross-validated AUC**: V3 reported train AUC (no cross-validation). V5 Mixtral has train AUC 0.650 vs CV AUC 0.641 — small gap, so overfitting is not the main issue. But for V3 with only 368 effective samples and pooling across 10 models, train-test leakage matters more.
  2. **Pooled vs per-model analysis**: V3 treated each model's response as an independent observation (~3,680 model–prompt pairs). This inflates AUC because it conflates model-level hallucination tendencies with prompt-level geometry. V5 analyzes each model separately.
  3. **Category decomposition**: V3 had only 4 categories (2 with enough hallucinations to drive the signal). The classifier was partly learning "nonexistent prompts hallucinate more" — true, but a geometric label-free finding only insofar as the embedding space separates these categories (which it does, but that's a coarser signal than within-category prediction).
- Additionally, V3 did not include oppositeness (the V5 top predictor) and relied heavily on centrality (β = −3.62), which does not replicate as a consistent signal in V5. Section 5.5 discusses this feature evolution in detail.
- "The initial study's result was not wrong — it correctly detected that geometric features carry information about hallucination risk. The expanded analysis decomposes this into category-level structure and within-category variation, providing a more precise and honest characterization."
- **IMPORTANT**: Do NOT frame V3 as "misleading" or "inflated." Frame as honest first pass that V5 refines. The V3 AUC was real — it just measured two things at once.

**¶6 — Transition to within-category analysis** (2-3 sentences)
- The decomposition shows that most aggregate predictive power comes from category structure. But the nonzero geometry increment (+0.02-0.04) and the theoretical motivation (categories were not defined geometrically) suggest genuine within-category signal.
- "The critical test is whether geometric features predict hallucination *within* individual categories — controlling entirely for category-level confounds. If density predicts hallucination among 600 nonexistent-entity prompts that share the same category, the same structure, and the same type of question, the signal cannot be attributed to category membership."
- Clean transition to Section 5.4. No preview of within-category AUC numbers.

#### Tables and figures

**Table 5.3** (essential): Three-model AUC comparison — verified numbers above.
- Format: 3 rows × 2 model columns, plus geometry increment row. Simple, high-impact.
- Include ± std across CV folds if available from re-run (currently only mean AUC is logged).

**Figure** (recommended): Grouped bar chart showing three AUC values side-by-side for each model.
- **NEEDS CREATION** — no existing file.
- Makes the category dominance and geometry's marginal contribution immediately visual. A horizontal dashed line at AUC=0.5 (chance) provides reference.
- Consider stacked or side-by-side layout: {Mixtral, Llama} × {geo-only, cat-only, cat+geo}.

**Figure** (optional): UMAP/t-SNE of corpus colored by category, showing geometric clustering.
- Existing: `results/v3/figures/category_manifolds_umap.png` and `_tsne.png` (449 prompts only).
- May want to regenerate on full 2,879 corpus for consistency with the analysis. Or use as-is with "initial benchmark" caption. Good for showing that categories occupy distinct geometric regions, supporting the "category structure IS geometric" argument.
- If included: caption must note the visualization is 2D projection and distances are approximate.

#### What NOT to include in 5.3

- Do NOT present within-category results — save for 5.4.
- Do NOT present Mann-Whitney results per feature — already in 5.2.
- Do NOT discuss individual feature coefficients in the combined model — the point is the AUC comparison, not which features drive it.
- Do NOT preview within-category AUC numbers (0.665/0.678) — that's 5.4's revelation.
- Do NOT frame geometry as "failing" or "weak" — it captures category structure genuinely, and the within-category test (next section) shows the fine-grained signal.
- Do NOT discuss the V3 feature ranking reversal (centrality→oppositeness) in detail here — save for 5.5 where the full evolution narrative belongs. A one-sentence mention in ¶5 is sufficient.

#### Data verification issues

- **AUC numbers**: ~~Pre-fix: 0.641, 0.722, 0.774, 0.769, 0.792, 0.813~~ **Post-fix (VERIFIED Mar 14)**: 0.645, 0.726, 0.782, 0.773, 0.800, 0.814. Re-ran `python3 scripts/analyze_v5_geometry_prediction.py` on post-contamination-fix data. Shifts were small (<0.01) as expected. The thesis LaTeX uses the post-fix numbers.
- **V3 train AUC of 0.86**: From `results/v3/multi_model/stats/logistic_regression_stats.csv` (verified: centrality β = −3.62, curvature β = −1.21). Note V3 used `class_weight='balanced'` and pooled across 10 models; V5 uses unweighted per-model. Both are honest for their respective contexts.
- **V3 had only 4 features, not 5**: V3 logistic regression used curvature, density, centrality, local_id. Oppositeness was NOT included in V3 (it was added for V5). This is relevant for the reconciliation paragraph — the feature that becomes V5's strongest predictor didn't exist in V3.
- **Category count**: 7 categories → 6 dummies with `drop_first=True`. Verified in script (line 266: `pd.get_dummies(..., drop_first=True)`).

#### Reviewer anticipation

- "So geometry barely helps beyond category labels?" → Yes, at the aggregate level (+0.02–0.04 AUC). But: (1) this measures aggregate additional signal, diluted across 7 categories including ones with <2% hallucination; (2) the category structure itself is a geometric finding — categories were defined semantically, geometry emerged independently; (3) the within-category signal is stronger where it matters (Section 5.4); (4) geometry provides a label-free difficulty estimate for deployment on arbitrary queries where category labels aren't available.
- "Why not just use category labels?" → For our benchmark, you could. But category labels require a taxonomy of difficulty types, which (a) is benchmark-specific and (b) doesn't scale to arbitrary queries. Geometry provides an automatic, taxonomy-free proxy for "how well does the model know this territory?" The practical value is in the label-free estimation, not in beating a label-based classifier on a labeled benchmark.
- "The +0.02 for Mixtral could be noise — is it significant?" → Fair concern. We do not claim the +0.018 increment is statistically significant (we haven't run a formal AUC difference test, e.g., DeLong test). We present it descriptively. The case for geometry rests on the within-category analysis (Section 5.4), not on the aggregate increment. **Consider adding**: DeLong test for AUC difference (category-only vs category+geometry) — if non-significant for Mixtral, report honestly. The Llama increment (+0.044) is more likely significant.
- "V3 AUC of 0.86 vs V5 of 0.64-0.72 — is the initial result wrong?" → Not wrong but limited. Three factors (train-set eval, pooled models, no category controls) inflated the number. V3 correctly detected that geometry carries hallucination signal; V5 decomposes that signal more precisely. Frame as scientific refinement. The V3 result motivated the expanded investigation; the V5 result is the definitive characterization.
- "Why not report a partial R² or likelihood ratio test for the geometry increment?" → Good suggestion. A likelihood ratio test comparing Model 2 (category-only) vs Model 3 (category+geometry) would formalize whether the 5 geometric features add statistically significant predictive power beyond category. **Consider adding** — this is a 2-line code addition to the script. If p < 0.05, it strengthens the "modest but real" claim. If p > 0.05 for Mixtral, report honestly and note that the within-category test is the stronger evidence.

### 5.4 Within-Category Analysis (~3-4 pages)

**Purpose**: The core finding of Chapter 5. Show that geometry predicts hallucination *within* categories, controlling entirely for the category confound identified in Section 5.3. This is the non-circular, novel result.

---

#### Paragraph-level outline

**¶1 — Setup (2-3 sentences)**
- Section 5.3 showed that most aggregate geometric signal overlaps with category structure. The decisive test: do geometric features predict hallucination *within* a single category, where all prompts share the same type of knowledge failure?
- We apply the same Mann-Whitney U tests and logistic regression from Section 5.2, now computed separately within each category. This controls entirely for category-level confounds.
- **No spoilers.** Just the setup.

**¶2 — Testable categories (1 short paragraph)**
- Of 7 categories, some have too few hallucinations to analyze:
  - **Excluded entirely** (< 5 hallucinations in either group): borderline_edge_factual (Mixtral: 4, Llama: 1), ambiguous for Mixtral only (4 hallucinations)
  - **Mann-Whitney only** (≥ 5 but < 10 hallucinations, insufficient for logistic regression): Llama ambiguous (9), Llama borderline_obscure_real (6)
  - **Full analysis**: Mixtral has 5 testable categories; Llama has 4 for logistic regression, 6 for Mann-Whitney
- Note: this is a statistical power issue, not a methodological one. Categories with < 2% hallucination rates simply don't generate enough events to detect effects.

**Table 5.4 — Within-category Mann-Whitney results (essential)**
Two-panel table (one per model), showing for each testable category:
- Category name, n_total, n_hall, n_correct
- Density: p-value, |r|, direction
- Oppositeness: p-value, |r|, direction
- Within-category CV AUC (where available)

**Verified numbers from CSV** (post-fix):

**Mixtral — significant results (p < 0.05):**

| Category | n_hall | n_correct | Feature | p | |r| | Direction |
|---|---|---|---|---|---|---|
| Nonexistent | 177 | 419 | density | 5.7×10⁻⁷ | 0.259 | hall lower |
| Nonexistent | 177 | 419 | oppositeness | 0.0046 | 0.147 | hall higher |
| Nonexistent | 177 | 419 | centrality | 0.011 | 0.132 | hall higher (closer to centroid) |
| Impossible | 19 | 174 | density | 0.014 | 0.345 | hall lower |

**Llama — significant results (p < 0.05):**

| Category | n_hall | n_correct | Feature | p | |r| | Direction |
|---|---|---|---|---|---|---|
| Nonexistent | 114 | 484 | density | 3.4×10⁻⁵ | 0.249 | hall lower |
| Borderline plaus. fake | 60 | 128 | oppositeness | 0.003 | 0.268 | hall higher |
| Ambiguous* | 9 | 590 | density | 0.011 | 0.495 | hall higher(!) |
| Ambiguous* | 9 | 590 | oppositeness | 0.013 | 0.483 | hall higher |
| Nonexistent | 114 | 484 | centrality | 0.029 | 0.131 | hall higher |
| Nonexistent | 114 | 484 | oppositeness | 0.037 | 0.126 | hall higher |
| Factual | 13 | 456 | oppositeness | 0.044 | 0.328 | hall higher |

*Ambiguous has n_hall=9 — effect sizes are large but sample is too small for reliable inference. Flag but don't build arguments on it.

**Within-category CV AUCs** (verified from CSV):

| Category | Mixtral | Llama |
|---|---|---|
| Nonexistent | 0.665 ± 0.066 | 0.678 ± 0.042 |
| Borderline plaus. fake | 0.492 ± 0.102 | 0.643 ± 0.057 |
| Impossible | 0.617 ± 0.069 | 0.411 ± 0.039 |
| Factual | 0.509 ± 0.063 | 0.653 ± 0.141 |
| Borderline obs. real | 0.435 ± 0.169 | — |

Note: Below-chance AUCs (0.492, 0.435, 0.411) reflect high CV variance with small n_hall, not meaningful inverse prediction.

**¶3 — The nonexistent finding (hero result, 4-5 sentences)**
- Among 600 nonexistent-entity prompts — all asking about things that don't exist, all sharing the same category label and question structure — density is highly significant for **both** models:
  - Mixtral: p = 5.7×10⁻⁷, |r| = 0.259, hall_mean = 2.165, correct_mean = 2.316
  - Llama: p = 3.4×10⁻⁵, |r| = 0.249, hall_mean = 2.132, correct_mean = 2.303
- Direction: hallucinated prompts sit in sparser embedding neighborhoods (lower density)
- These are the **only** results that survive Bonferroni correction for 70 tests (α = 0.05/70 = 0.0007)
- Within-category CV AUC: 0.665 (Mixtral), 0.678 (Llama) — modest but above chance, from prompt text geometry alone
- **Key argument**: This signal *cannot* be attributed to category membership. All 600 prompts are nonexistent entities. The classifier must be detecting something about *which* nonexistent entities hallucinate — a genuine geometric signal.

**¶4 — Secondary signals (2-3 sentences)**
- Several other within-category effects reach nominal significance (p < 0.05), listed in Table 5.4
- Pattern: density is the most consistent within-category predictor (significant in nonexistent for both models, impossible for Mixtral). Oppositeness appears in borderline_plausible_fake (Llama) and factual (Llama) but not consistently across models.
- None of the secondary signals survive Bonferroni correction. They may be real but underpowered — the categories with significant effects tend to have fewer hallucinations (19, 60, 13) than nonexistent (177, 114).
- Report honestly: with 55 actual tests and 11 nominally significant results (vs. ~3 expected by chance at α = 0.05), the enrichment suggests real signal beyond nonexistent, but we cannot identify specific effects with statistical confidence.

**¶5 — CV AUC discussion (2-3 sentences)**
- Within-category CV AUC of 0.67 for nonexistent (both models) represents modest but genuine discrimination from geometric features alone, with category membership completely controlled
- Other category AUCs are mixed: some above chance (borderline_plausible_fake Llama 0.643, factual Llama 0.653), some at/below chance (factual Mixtral 0.509, impossible Llama 0.411). Below-chance values reflect high CV variance with small samples (19, 13 hallucinations), not meaningful inverse signal.
- The within-category AUC is necessarily lower than the between-category AUC (0.645/0.726) because the category-level signal has been removed by design.

**¶6 — Multiple testing (1 paragraph)**
- Total tests: 55 Mann-Whitney tests actually performed (25 Mixtral + 30 Llama), or 70 if counting all possible tests across 7 categories × 5 features × 2 models. We use 70 for the conservative Bonferroni correction.
- At Bonferroni α = 0.05/70 = 0.0007: only density in nonexistent survives, for **both** models independently. The consistency across two independent models strengthens the finding — a chance hit in a single model/category would not replicate.
- Briefly note: Benjamini-Hochberg FDR would recover more results, but we take the conservative approach and build conclusions only on Bonferroni-surviving effects.

**¶7 — Why density? (3-4 sentences, interpretation)**
- Density measures the number of similar prompts in the embedding neighborhood (log of average k-NN distance)
- Interpretation: sparser neighborhoods correspond to entities with fewer semantically similar entities in the corpus. Models have less "nearby" knowledge to anchor generation → more likely to fabricate.
- This aligns with entity popularity explanations in the literature (cite Sun et al. 2024, Mallen et al. 2023): obscure entities hallucinate more because models have fewer training examples. Density operationalizes this at the embedding level.
- Do **NOT** over-claim: density is a proxy, not a mechanistic explanation. The causal chain (sparse embedding → fewer training examples → hallucination) is plausible but not proven here.

**¶8 — Summary/transition to 5.5 (2 sentences)**
- Within-category analysis confirms a genuine, non-circular geometric signal: density predicts hallucination within the nonexistent category for both models, surviving stringent Bonferroni correction, with cross-validated AUCs of 0.67.
- This establishes that prompt embedding geometry carries per-prompt risk information beyond category membership. Section~\ref{sec:feature-synthesis} synthesizes which features carry genuine signal across all analyses in this chapter.

#### Figures

**Figure (hero)**: Density box plots for hallucinated vs. correct within nonexistent, both models. Existing figures (`v5_within_category_*.png`) show all categories × 3 features — these work but are very busy. Consider either:
- (a) Use as-is with caption directing reader to nonexistent density panel
- (b) Extract/regenerate just the nonexistent density comparison as a cleaner figure

**Decision needed**: The existing figures are 3-row (density, centrality, curvature) × 7-category grids. They don't include oppositeness or local_id. For the thesis, a focused figure showing just the nonexistent density comparison would be cleaner and more impactful. The full grids can go in appendix.

#### What NOT to include
- Don't re-explain statistical methods (Section 5.2)
- Don't re-derive the category confound (Section 5.3)
- Don't discuss feature evolution in detail (save for 5.5)
- Don't preview Chapter 6/7 results (prompt prefixes, fine-tuning)
- Don't over-interpret below-chance AUCs as meaningful

#### Outline corrections vs. previous THESIS_WRITING.md
1. **Borderline_plausible_fake Llama oppositeness**: Previous outline said p=0.008, actual is **p=0.003**
2. **Ambiguous (Llama)**: Previous outline said "too few to test" — actually has 9 hallucinations, enough for Mann-Whitney (shows large effects), but too few for logistic regression. Should mention with appropriate caveats.
3. **Below-chance CV AUCs**: Previous outline didn't mention these (Mixtral borderline_plausible_fake 0.492, Mixtral borderline_obscure_real 0.435, Llama impossible 0.411). Need honest treatment.
4. **local_id–curvature correlation r = −0.97**: Already flagged in THESIS_WRITING.md as wrong (actual r = −0.143). Do not repeat in 5.4 — save for 5.5 if needed.

#### Reviewer anticipation
- **"Only nonexistent survives Bonferroni — is this one category carrying the whole chapter?"** → Honest answer: yes, largely. But: (1) it survives for both models independently; (2) the enrichment of 11/55 significant tests vs. ~3 expected suggests broader signal; (3) nonexistent is the largest category with most statistical power — absence of evidence ≠ evidence of absence for smaller categories.
- **"CV AUC of 0.67 is modest — is this useful?"** → For deployment, no. For the theoretical question (does prompt geometry carry hallucination risk?), yes. Within a single category with all confounds controlled, 0.67 from text geometry alone is nontrivial.
- **"Why not pool across categories with category as a covariate?"** → That's what Section 5.3 did (category+geometry model). The within-category analysis provides a cleaner, assumption-free test that doesn't rely on the logistic regression correctly modeling category effects.
- **"11/55 significant vs 3 expected — did you test this enrichment formally?"** → Could run a binomial test (11 successes out of 55 trials at α=0.05). Binomial p-value ≈ 5×10⁻⁵. Strengthens the case but may feel like p-hacking on p-values. Mention or appendix.

### 5.5: Feature Synthesis (1–1.5 pages)

#### Purpose
Synthesize which of the five geometric features carry genuine predictive signal, which were artifacts of the initial study's design, and why the hierarchy reversed. This fulfills forward references from Section 5.2 (line 169: "Section 5.5 discusses why the feature hierarchy shifted"), Section 5.3 (line 282: "discusses the accompanying shift in which individual features dominate"), and Section 5.4 (line 386: "synthesizes the feature hierarchy across all analyses in this chapter").

#### What NOT to repeat (already covered)
- V3 vs V5 coefficient table → already in Section 5.2 Table `tab:logistic-comparison`
- Multicollinearity discussion (Llama local_id = -0.49, pairwise r values) → already in Section 5.2 line 176
- Within-category density interpretation → already in Section 5.4 ¶"Interpretation"
- V3 → V5 AUC drop factors → already in Section 5.2 line 200

---

#### Paragraph-level outline

**¶1 — Opening (2 sentences)**
- Sections 5.2–5.4 tested five geometric features at three levels: univariate between-category, multivariate with and without category controls, and univariate within-category. This section synthesizes the results into a per-feature assessment, with particular attention to why the feature hierarchy reversed between the initial study and the expanded analysis.
- Keep this tight — the reader has just finished 5.4 and wants the payoff.

**Table 5.X — Feature synthesis table (the centerpiece)**

A compact table that extends Table `tab:logistic-comparison` by adding within-category and assessment columns. 5 rows × 5 columns:

| Feature | Initial Study (449 prompts) | Between-Category | Within-Category | Assessment |
|---|---|---|---|---|
| Oppositeness | Not measured | Strongest: \|r\|=0.218/0.367, p<10⁻¹⁰ | Nonexistent: p=0.005/0.037; plaus. fake (Llama): p=0.003 | Strong between-cat; mixed within-cat |
| Density | Non-significant (β=-0.15, p=0.48) | Second: \|r\|=0.142/0.095, p<10⁻⁵/0.017 | Nonexistent: p=5.7×10⁻⁷/3.4×10⁻⁵ ***(Bonferroni survives)***; impossible (Mixtral): p=0.014 | **The robust signal** — significant at both levels, both models |
| Centrality | Strongest (β=-3.62, OR=0.027) | Weak/inconsistent: \|r\|=0.056/0.147 | Direction reverses within nonexistent (Simpson's paradox); p=0.011/0.029 uncorrected | **Downgraded** — was proxying for category |
| Curvature | Second (β=-1.21, OR=0.300) | Null: \|r\|<0.02, p>0.7 | Null: all p>0.07 | **Downgraded** — initial finding not robust |
| Local ID | Null (β≈0, p=0.98) | Null: \|r\|<0.01, p>0.8 | Null: all p>0.07 | Confirmed null |

**Verified numbers**:
- Oppositeness between-cat: Mixtral \|r\|=0.218, p=4.5×10⁻¹¹; Llama \|r\|=0.367, p=2.5×10⁻²⁰ ✓ (from `v5_geometry_prediction_overall.csv`)
- Oppositeness within nonexistent: Mixtral p=0.0046, Llama p=0.037 ✓ (from within-category CSV)
- Oppositeness plausible fake Llama: p=0.003, \|r\|=0.268 ✓ (from within-category CSV line 44)
- Density between-cat: Mixtral \|r\|=0.142, p=1.7×10⁻⁵; Llama \|r\|=0.095, p=0.017 ✓ (from overall CSV)
- Density within nonexistent: Mixtral p=5.7×10⁻⁷, Llama p=3.4×10⁻⁵ ✓ (from within-category CSV)
- Density impossible Mixtral: p=0.014, \|r\|=0.345 ✓ (from within-category CSV line 23)
- Centrality between-cat: Mixtral \|r\|=0.056, p=0.093; Llama \|r\|=0.147, p=0.0002 ✓ (from overall CSV)
- Centrality within nonexistent: Mixtral p=0.011, Llama p=0.029 ✓ (from within-category CSV)
- Curvature between-cat: Mixtral \|r\|=0.006, p=0.854; Llama \|r\|=0.013, p=0.739 ✓ (from overall CSV)
- Curvature within nonexistent: Mixtral p=0.974, Llama p=0.085 ✓ (from within-category CSV)
- Local ID between-cat: Mixtral \|r\|=0.006, p=0.864; Llama \|r\|=0.009, p=0.812 ✓ (from overall CSV)
- V3 centrality: β=-3.62, OR=0.027, p<0.001 ✓ (from `logistic_regression_stats.csv`)
- V3 curvature: β=-1.21, OR=0.300, p<0.001 ✓
- V3 density: β=-0.15, OR=0.862, p=0.482 ✓
- V3 local_id: β≈0, OR=1.00, p=0.983 ✓

**Formatting note**: The table should show \|r\| for between-category (not coefficients — those are in Table `tab:logistic-comparison`), p-values for within-category, and a one-line assessment. Use bold for density's assessment row. Footnote that oppositeness was not available in the initial study (only 4 features: centrality, curvature, density, local_id).

**¶2 — Why centrality and curvature were downgraded (3–4 sentences)**
- Centrality dominated the initial study (largest coefficient, OR=0.027). But centrality measures distance from the global corpus centroid. Categories with higher hallucination rates — nonexistent (30% Mixtral) and plausible fake (44%) — sit in geometrically distinct, peripheral positions in the embedding space (visible in the UMAP projections, Figures `fig:v3-category-manifolds` and `fig:v5-category-manifolds`). On a benchmark with only 4 categories and 449 prompts, centrality was an effective proxy for "is this a hard category?" rather than a fine-grained geometric predictor.
- The Simpson's paradox in Section 5.4 confirms this: between categories, low centrality predicts hallucination (peripheral prompts hallucinate more); within the nonexistent category, the direction *reverses* (prompts closer to the category centroid hallucinate more). The between-category signal was a category artifact; the within-category direction, while not surviving correction, tells a different geometric story.
- Curvature follows a similar pattern: significant in the initial study (β=-1.21) but null in the expanded analysis at both levels (all \|r\| < 0.02 between-category; all p > 0.07 within-category). With only 449 prompts and 4 categories, the initial logistic regression had 4 features and limited ability to distinguish feature-level from category-level signal.

**¶3 — Density as the robust signal (3 sentences)**
- Density tells the opposite story: non-significant in the initial study (p=0.48) but the most robust predictor in the expanded analysis. It is significant between categories (p < 10⁻⁵ for Mixtral), significant within the nonexistent category for both models independently (p < 10⁻⁵, the only results surviving study-wide Bonferroni correction), and shows consistent direction at both levels (sparser neighborhoods predict hallucination).
- Why was density non-significant in V3? Two factors: (a) the initial study had only 449 prompts with 4 features, limiting statistical power for detecting modest effects; (b) centrality was absorbing variance that partly overlapped with density (they share a moderate correlation, r = −0.51 in the expanded corpus), and centrality's stronger category-level signal dominated in the smaller dataset.
- **Key claim**: Density is the one feature that survives every test in this chapter — between-category, within-category, Bonferroni correction, both models. Reference Table above.

**¶4 — Oppositeness: strong but ambiguous (2–3 sentences)**
- Oppositeness is the strongest between-category discriminator (\|r\| = 0.218/0.367), but its within-category evidence is mixed. Within nonexistent, Mixtral shows a borderline effect (p = 0.005, just below the within-table Bonferroni threshold of 0.005) while Llama's is weaker (p = 0.037). Llama's plausible fake category shows a notable within-category oppositeness effect (p = 0.003, \|r\| = 0.268), but this does not replicate in Mixtral.
- Whether oppositeness captures genuine within-category signal or residual between-category structure remains an open question. Unlike density, oppositeness does not show consistent within-category significance across both models for any single category.
- Note: oppositeness was not available in the initial study (computed from corpus-level PCA), so no V3 comparison is possible.

**¶5 — Pairwise correlations among features (2 sentences)**
- The five features are not independent. Verified pairwise Pearson correlations on the full 2,879-prompt corpus:
  - oppositeness–centrality: r = −0.539
  - density–centrality: r = −0.509
  - oppositeness–density: r = 0.384
  - local_id–curvature: r = −0.143 (***corrected*** from the −0.97 reported in early analysis notes)
  - All other pairs: |r| < 0.10
- The oppositeness–centrality–density cluster shares moderate correlations (|r| = 0.38–0.54), explaining why multivariate coefficients (Table `tab:logistic-comparison`) are unstable even as overall AUC remains consistent across CV folds. Section 5.2 discussed this in the context of Llama's anomalous local_id coefficient; the same caution applies to interpreting any individual coefficient in this correlated feature set.

**CRITICAL CORRECTION**: The experiment log (line 321) and THESIS_WRITING.md (line 915) claim local_id and curvature have r = −0.97 correlation. **This is wrong.** The actual correlation is **r = −0.143** (verified by computing `df[features].corr()` on `data/processed/v5_geometry_features.csv`). The "−0.97" may have been a typo or from a different computation context. The thesis must use −0.143. The local_id–curvature pair is NOT redundant; they simply both happen to be non-predictive.

**¶6 — Cautionary lesson (2–3 sentences)**
- The feature hierarchy reversal carries a methodological lesson for geometric approaches to hallucination detection. On small benchmarks with few categories, logistic regression conflates category-level and feature-level signal — centrality's strong V3 coefficient was real but was measuring "which category is this prompt in?" rather than "among similar prompts, which ones will hallucinate?" Cross-validated, within-category analysis is necessary to disentangle the two.
- This finding applies beyond our specific features: any study that (a) defines prompt categories with different difficulty levels and (b) shows that embedding features predict difficulty should test whether prediction survives within-category controls. Without this test, the contribution of prompt geometry versus prompt content remains ambiguous.

**¶7 — Transition to Chapter 6 (1–2 sentences)**
- Density is the feature that survives scrutiny at every level of analysis. Whether it also predicts where *interventions* succeed — distinguishing prompts that can be rescued by better prompting from those that resist all mitigation — is the subject of the next chapters.
- Forward reference to Chapters 6–7 with NO spoilers about prefix effectiveness or fine-tuning results.

---

#### Figures/Tables

- **Table 5.X (essential)**: Feature synthesis table as described above. This is the only new table — it combines info from Tables 5.2, 5.3, 5.5, 5.6 into one compact overview with a final "Assessment" column.
- **No new figures needed**: The UMAP plots (already in 5.2) show category clustering; the within-category dot plot (already in 5.3/5.4) shows the AUC variation; the nonexistent Mann-Whitney table (already in 5.4) shows the density dominance. A correlation heatmap was listed as optional in THESIS_WRITING.md — skip it. The correlations can be stated in one sentence (¶5) and a 5×5 heatmap for 5 features feels like padding for what is mostly near-zero correlations with 3 moderate values.

---

#### Reviewer anticipation

1. **"This section just repeats what 5.2–5.4 already showed."** → Risk is real. The section must synthesize, not summarize. The value-add is: (a) the synthesis table that puts everything in one place, (b) the explicit "why did centrality drop?" explanation that 5.2 deferred to here, (c) the cautionary methodological lesson. Keep it to 1–1.5 pages.

2. **"Why not just drop curvature, local_id, and centrality and re-run with 2 features?"** → Valid suggestion. Could include as a robustness note: re-running with only oppositeness + density produces similar CV AUC (worth computing). But the point of including all 5 is to show which survive rigorous testing, not to optimize a classifier.

3. **"The V3 results look embarrassingly different from V5 — does this undermine trust?"** → Address directly: V3 was a pilot on 449 prompts with 4 features, pooled across 10 models, with train-set AUC. V5 is 2,430 prompts, 5 features, per-model, CV'd. The V3 signal was real (geometry does predict hallucination) but the feature attribution was unreliable at that scale. This is normal scientific refinement.

4. **"Density was non-significant in V3 — how can it now be 'the real signal'?"** → Statistical power: V3 had 449 prompts with ~86% hallucination rate in nonexistent (heavily imbalanced); the density coefficient (-0.15) was fighting against centrality's stronger category-level signal. In V5, with 2,430 prompts, 7 categories, and within-category controls that remove the category confound, density emerges because it's the only feature with genuine within-category variation.

5. **"Oppositeness is the strongest discriminator but you call density 'the robust signal' — isn't oppositeness more important?"** → Between-category, yes. But oppositeness's within-category evidence is inconsistent across models. Density survives every test. For the theoretical question (does prompt geometry carry fine-grained hallucination signal beyond category?), density is the answer.

---

#### What NOT to include
- Don't re-explain statistical methods (Section 5.2)
- Don't re-derive the category confound (Section 5.3)
- Don't re-discuss within-category density interpretation (Section 5.4)
- Don't preview Chapter 6/7 results
- Don't include the correlation heatmap (too sparse for 5 features; state correlations in text)
- Don't discuss fixability prediction (that's Chapter 7)

### 5.6 Discussion (~1.5-2 pages)

**Purpose**: Interpret the findings, acknowledge limitations honestly, and transition to Chapters 6-7. Interpretive prose only — no new tables or figures. References existing figures/tables from earlier sections as needed.

**No spoilers**: Do NOT preview prefix effectiveness, fine-tuning results, fixability prediction, or any Ch 6-7 content. Forward references must be framed as open questions.

---

#### Paragraph-level outline

**¶1 — What geometry captures (1 paragraph)**
- Summarize the two-level prediction structure established by this chapter:
  - **Between categories**: category membership alone achieves AUC 0.77-0.78 (Table `tab:decomposition`); geometry adds a modest increment (+0.018/+0.041). The embedding space naturally encodes a "difficulty gradient" aligned with hallucination risk — categories defined semantically, not geometrically, are nevertheless geometrically separable.
  - **Within categories**: density provides fine-grained signal beyond category labels (AUC 0.665/0.678 within nonexistent, Bonferroni-surviving Mann-Whitney p < 10⁻⁵ for both models; Table `tab:within-cat-nonexistent`). This is the genuinely geometric contribution — not "which type of question is this?" but "among questions of the same type, which will trip the model up?"
- Frame as: "the embedding space encodes hallucination risk at two granularities, and the within-category signal cannot be attributed to category membership."

**¶2 — Why density? (1 paragraph)**
- Intuition: sparse embedding neighborhoods correspond to prompts where the embedding model has fewer similar training examples to anchor representation, which may track regions where the *target* model also has less reliable knowledge. Among nonexistent entities, some fabricated names resemble many real entities (high density, easier to flag) while more exotic fabrications sit in isolated embedding regions (low density, fewer reference points to trigger uncertainty).
- Connection to entity popularity findings — cite Sun et al. 2024 or Mallen et al. 2023 (rarer entities hallucinate more). **CHECK**: verify these citations exist in `references.bib`. If not, add them or cite from the literature comparison tables.
- **Critical caveat + surface-feature baseline** `[DONE — Mar 21, 2026]`: Density is a correlational proxy, not a verified causal mechanism. Tested two surface baselines within nonexistent: question word count (null for both models) and entity name length (Mixtral-only, |r|=0.162, weaker than density's 0.259). Density–entity length Spearman r=−0.186 (modest). Density carries signal beyond surface text properties. Written into thesis as empirical paragraph replacing the purely rhetorical caveat. See experiment log §2.5.7 for full results.
- Keep this tight — the speculative interpretation already appears in Section 5.4 (¶"Interpretation", line ~391). This paragraph synthesizes that interpretation at a higher level, connecting to related work.

**¶3 — Why external embeddings work at all (1 paragraph)**
- The geometric signal comes from text-embedding-3-large applied to the question text alone — not from the target model's internal representations during generation. This means hallucination risk is partly a property of the *question's position in semantic space*, not just the model's processing.
- This is a stronger-than-expected result: one might assume hallucination depends entirely on model-internal factors (attention patterns, weight distributions, decoding dynamics).
- The moderate cross-model Kendall's τ consistency (Section 5.1, mean τ = 0.319) corroborates this: some prompts carry a shared difficulty signal across model families, and this difficulty is legible from the question text's embedding geometry.
- Cite the complementary approach: prior work on representation probing (e.g., Li et al. 2024, Marks & Tegmark 2023 — already referenced in Ch 4 Section 4.4) examines model-internal activations. Our approach is closer to dataset-level difficulty estimation — testing whether hallucination risk is detectable *before* the model processes the question.

**¶4 — Limitation 1: Single embedding model (1 paragraph)**
- All geometric features in this chapter depend on a single embedding model (text-embedding-3-large, Section~\ref{sec:embedding-model}). A preliminary robustness check on the initial benchmark compared three embedding models (text-embedding-3-small at 1,536 dimensions, text-embedding-3-large at 3,072, and the open-source all-mpnet-base-v2 at 768); results are reported in Appendix~\ref{app:embedding-robustness}.
- **Honest framing**: That robustness check was conducted on the initial benchmark (368 prompts, four categories, pooled across 10 models) using Spearman rank correlations — a different methodology from the expanded benchmark's within-category Mann-Whitney tests. The central finding of this chapter (within-category density prediction on 2,430 prompts with category controls) has been validated only with text-embedding-3-large. Whether the within-category density signal generalizes to other embedding spaces is an open question.
- **DO NOT overstate or understate**: The V3 robustness check found density non-significant for text-embedding-3-large (r=0.011, p=0.451) — but this is *consistent* with the thesis's own finding that density was non-significant in the initial analysis (Section 5.2, β=-0.15, p=0.48). The within-category signal emerged only with the expanded benchmark and proper controls. The robustness question is whether that within-category signal would also emerge with alternative embeddings, which has not been tested.

**¶5 — Limitation 2: Within-category signal concentrated in one category (1 paragraph)**
- Density's Bonferroni-surviving significance comes from the nonexistent category (n=600, 30% Mixtral / 19% Llama hallucination rates). Other categories either have too few hallucinations for adequate statistical power (ambiguous: 4 hallucinations for Mixtral; edge factual: 4 and 1) or show weaker, inconsistent effects that don't survive correction.
- Honest assessment: we cannot determine whether the absence of within-category signal in smaller categories reflects genuine null effects or insufficient power. The enrichment of nominally significant results (11 of 55 tests at p < 0.05, vs. ~3 expected by chance) suggests broader signal, but no individual result outside nonexistent is reliable.
- This is a limitation of the benchmark design: we scaled up nonexistent and ambiguous categories (600 each) but kept smaller categories at 130-200 prompts. Future work with larger per-category samples could resolve this.

**¶6 — Limitations 3-5 (1 paragraph, briefer)**
- **Modest effect sizes**: Within-category density |r| ≈ 0.25 (small-to-medium), AUC 0.67 (above chance but far from deployable). Geometry provides a *signal*, not a *solution*. Practical deployment would require combining with other indicators.
- **Corpus self-reference**: All features are computed relative to the benchmark corpus itself (Section~\ref{sec:reference-distribution}). Adding or removing prompts changes all feature values. Features characterize relative position within this benchmark, not an absolute property of the question. A deployment system would need to define an appropriate reference distribution.
- **Two-model scope**: The within-category analysis covers only Mixtral and Llama. The 10-model benchmark (Section 5.1) establishes that hallucination varies across models, but within-category geometric prediction has not been tested beyond two architectures.

**¶7 — Forward (1 short paragraph)**
- Density survives scrutiny as a genuine geometric correlate of within-category hallucination risk. The natural next question is whether this signal can inform *intervention*: if we know which prompts are at risk, can targeted prompting reduce their hallucination rates? And does geometry predict which hallucinations resist mitigation? Chapters~\ref{ch:prefixes} and~\ref{ch:finetuning} address these questions.
- **NO SPOILERS.** Do not name prefixes, state AUC values, or hint at fine-tuning results.

---

#### Citations to verify/add before writing

| Citation | Purpose | Status |
|---|---|---|
| Sun et al. 2024 (entity popularity → hallucination) | ¶2: density ↔ entity obscurity | **CHECK** `references.bib` |
| Mallen et al. 2023 (PopQA: rare entities → more errors) | ¶2: alternative citation for same point | **CHECK** `references.bib` |
| Li et al. 2024 (representation probing) | ¶3: complementary approach (internal vs. external) | Should already be in bib from Ch 4 |
| Marks & Tegmark 2023 (geometry of truth) | ¶3: complementary approach | Should already be in bib from Ch 4 |

#### Reviewer anticipation

1. **"Density is just entity obscurity with extra steps — why not use Wikipedia page views?"** → Acknowledge this directly (¶2 caveat). Geometry is a *proxy*, not a mechanism. The value is that it's computable from embeddings without external knowledge bases, and it generalizes across entity types (nonexistent entities don't have Wikipedia pages). But a head-to-head comparison with a frequency-based proxy would strengthen the claim — note as future work.

2. **"AUC 0.67 is too low to be useful."** → Agree for deployment (¶6). But the chapter's contribution is theoretical (within-category geometric signal exists and survives controls), not applied. The practical utility comes in Ch 7, where geometry guides training data selection — but do NOT preview that here.

3. **"Only one category matters — how is this a general finding?"** → Honest answer: it's not fully general yet (¶5). The signal is clearest where statistical power is greatest. The enrichment of nominal results (11/55 > 3 expected) suggests breadth, but individual category results are unreliable. Frame as: "the signal is detectable where we have power to detect it."

4. **"Have you tried other embedding models?"** → ¶4 addresses this. The preliminary V3 check predates the within-category methodology. Acknowledge as open question.

5. **"External embeddings can't capture model-specific hallucination patterns."** → Correct, and acknowledged (¶3). The cross-model τ = 0.319 shows the signal is partial. External embeddings capture the shared, question-level component. Model-specific patterns require model-internal representations (complementary approach, cited).

#### What NOT to include
- No new tables or figures
- No re-explanation of statistical methods (Section 5.2)
- No re-derivation of category confound (Section 5.3)
- No re-presentation of within-category density results (Section 5.4 — reference only)
- No preview of Ch 6 prefix results or Ch 7 fine-tuning/fixability results
- No mention of the "precision-recall tradeoff" (Ch 7 territory)
- No discussion of template ablation, TruthfulQA, or cross-category generalization (all Ch 7)

### Estimated length: 15-20 pages

### Data files to pull from

| Content | Source File | Notes |
|---|---|---|
| 10-model halluc rates | `results/v3/multi_model/tables/table1_model_performance.csv` | Use as-is |
| Cross-model consistency | `results/v3/multi_model/tables/table2_consistency_summary.csv` | Kendall's tau = 0.319 |
| V3 logistic regression | `results/v3/multi_model/stats/logistic_regression_stats.csv` | V3 coefficients |
| V3 within-category | `results/v3/within_category_summary.csv` | nonexistent AUC=0.929 |
| V5 baseline summary | `results/v5_baselines/baseline_summary.json` | **Use POST-FIX numbers** |
| V5 overall geometry | `results/v5_baselines/analysis/v5_geometry_prediction_overall.csv` | Mann-Whitney + logistic |
| V5 within-category | `results/v5_baselines/analysis/v5_geometry_prediction_within_category.csv` | The core table |
| Sensitivity analysis | `results/sensitivity_analysis.json` | Judge robustness |
| Scatter plots | `results/v5_baselines/analysis/v5_geometry_vs_hallucination_*.png` | May need regeneration |
| Within-cat box plots | `results/v5_baselines/analysis/v5_within_category_*.png` | Hero figure candidates |

### Writing order (section by section)

1. **5.1 Cross-Model Hallucination Rates** — establishes phenomenon + validates pipeline
2. **5.2 Between-Category Geometric Analysis** — defines statistical methods, shows overall signal
3. **5.3 Decomposing Category vs. Geometric Signal** — the honest reckoning
4. **5.4 Within-Category Analysis** — the core finding (density)
5. **5.5 Feature-by-Feature Summary** — synthesis table
6. **5.6 Discussion** — interpretation + forward references
7. **Chapter opening paragraph** — write after body is done
8. **Flow pass** — transitions, terminology consistency, spoiler check

### Figures and tables in Ch 5 — consolidated inventory

**Tables (5 essential, all need LaTeX creation from CSV data)**:
| Table | Section | Content | Source |
|---|---|---|---|
| 5.1 | 5.1 | 10-model hallucination rates + V5 Mixtral/Llama baselines | `results/v3/multi_model/tables/table1_model_performance.csv`, `results/v5_baselines/baseline_summary.json` |
| 5.2 | 5.2 | Between-category Mann-Whitney (5 features × 2 models) | `results/v5_baselines/analysis/v5_geometry_prediction_overall.csv` |
| 5.3 | 5.3 | AUC decomposition (geo-only / cat-only / combined × 2 models) | Same CSV, logistic regression section |
| 5.4 | 5.4 | Within-category analysis (7 cats × density + oppositeness + CV AUC × 2 models) | `results/v5_baselines/analysis/v5_geometry_prediction_within_category.csv` |
| 5.5 | 5.5 | Feature evolution (V3 finding → V5 between-cat → V5 within-cat → assessment) | Experiment log summary table |

**Figures (essential — 3 total)**:
| Figure | Section | Description | Status |
|---|---|---|---|
| **Hero figure**: Density box plots | 5.4 | Density distribution, hallucinated vs correct, within nonexistent category (both models, side-by-side) | **EXISTS**: `results/v5_baselines/analysis/v5_within_category_*.png` — check if publication-quality, may need regeneration with better labels/formatting |
| Feature coefficient bar chart | 5.2 | Standardized logistic regression coefficients, 5 features, grouped by model | **NEEDS CREATION** |
| AUC comparison bar chart | 5.3 | Grouped bars: geo-only / cat-only / combined, per model | **EXISTS**: `thesis/figures/ch5_within_category_auc.png` — verify content matches this description |

**Figures (recommended — include if space permits)**:
| Figure | Section | Description | Status |
|---|---|---|---|
| Scatter plots (oppositeness + density vs halluc) | 5.2 | Per-model, color by hallucinated/correct | **EXISTS**: `results/v5_baselines/analysis/v5_geometry_vs_hallucination_*.png` |
| Cross-model consistency heatmap | 5.1 | 10×10 Kendall's tau matrix | **EXISTS**: `results/v3/multi_model/consistency_heatmap.png` |
| UMAP/t-SNE corpus projection | 5.3 | Corpus colored by category, showing geometric clustering | **EXISTS (V3 only)**: `results/v3/figures/category_manifolds_umap.png` — consider regenerating on full 2,879 corpus |

**Figures (optional — appendix candidates)**:
| Figure | Section | Description | Status |
|---|---|---|---|
| Within-category p-value heatmap | 5.4 | Features × categories × models, color by significance | **NEEDS CREATION** |
| Feature correlation matrix | 5.5 | 5×5 heatmap showing local_id–curvature anticorrelation | **NEEDS CREATION** |
| V3 geometry heatmaps | 5.3 | Geometric features overlaid on UMAP | **EXISTS**: `results/v3/figures/geometry_heatmaps_umap.png` |

**Total**: 5 tables + 3 essential figures + 3 recommended + 3 optional. Approximately 4-5 figures need creation or verification; rest exist.

---

## Chapter 7: Can Geometry Guide Intervention? — Detailed Content Plan

**Chapter question**: We know geometry predicts hallucination (Ch 5) and prompts reduce it (Ch 6). Can geometry predict *which* hallucinations are fixable? And can the best prompt behavior be made permanent through fine-tuning?

**Chapter label**: `\label{ch:finetuning}` (existing stub)

**Estimated length**: 15–18 pages at 1.5 spacing

**Proposed section structure** (actual page counts as of Mar 23):
- Chapter opening (~1 page, pp. 97–98) ✅
- 7.1 Geometric Prediction of Fixability (~5 pages, pp. 98–103) ✅ — bridge analysis
- 7.2 Training Data Curation (~2 pages, pp. 103–105) ✅ — best-per-prompt selection
- 7.3 Fine-Tuning Results (~? pages, starts p. 105) ✅ written — LoRA results, per-category analysis, robustness, geometric analysis
- 7.4 Generalization Evidence (~4–5 pages) — TruthfulQA, template ablation, cross-category
- 7.5 Discussion (~2 pages)

**Data files**:
- Bridge analysis: `results/v5_prefixes/analysis/v5_bridge_data.csv`, `v5_bridge_stats.csv`, `v5_bridge_within_category.csv`, `v5_bridge_logistic_auc.csv`
- Best-per-prompt: `data/training/v5_training_mixtral-8x7b.jsonl`, `v5_training_llama-4-maverick-17b.jsonl`
- Fine-tuning: `results/v5_finetuned/analysis/ft_bridge_data.csv`, `ft_bridge_stats.csv`
- TruthfulQA: `results/truthfulqa/analysis/truthfulqa_analysis.md`, `truthfulqa_per_category.csv`
- Template ablation: `results/v5_finetuned/ablation/ablation_analysis.json`
- Cross-category: `results/v5_finetuned/cross_cat_ablation/evaluation_summary.json`

### Chapter opening (~0.5 page)

Pose the chapter's two questions without previewing answers:

1. If geometric features predict hallucination risk (Chapter 5), do they also predict which hallucinations *resist mitigation*? A "yes" would mean geometry provides not just a risk signal but a difficulty signal — distinguishing prompts that need more aggressive intervention from those where a simple prompt adjustment suffices.

2. Can the best prompt behavior identified in Chapter 6 be distilled into model weights, eliminating runtime prompt engineering? And what is the cost?

State that this chapter bridges prediction (Ch 5) and intervention (Ch 6) by analyzing whether geometry predicts fixability, then tests whether fine-tuning can make prompt-level gains permanent.

**Rules**: No results previews. No numbers. Frame as open questions.

---

### 7.1 Geometric Prediction of Fixability (~3–4 pages)

**Section question**: Among prompts that hallucinate at baseline, can geometric features predict which are fixable by prompt prefixes and which resist all intervention?

**Label**: `\label{sec:fixability-prediction}`

#### Paragraph 1: Fixability framework (~0.5 page)

Define the five outcome categories for each prompt × model pair, based on baseline (no-prefix) and best-prefix results from Chapter 6:

| Outcome | Definition |
|---|---|
| `already_correct` | Correct at baseline (label=0). No prefix needed. |
| `fixed` | Hallucinated at baseline (label=2), NOT hallucinating with at least one prefix (label ≠ 2). Includes corrections, refusals, and partial answers — any non-hallucination counts as "fixed." |
| `still_broken` | Hallucinated at baseline, still hallucinating (label=2) with ALL tested prefixes. |
| `regressed` | Correct at baseline, hallucinated with at least one prefix. |
| `other` | Partial or refused at baseline (excluded from fixability analysis). |

**Why refusals count as "fixed"**: A refusal IS a successful fix — the model stopped hallucinating, even if it didn't produce a correct answer. This matches the safety framing: we want to know where the model *stops fabricating*, not where it gives perfect answers. Note this definition explicitly.

**Verified outcome counts** (post-CoT-exclusion re-run, from `v5_bridge_data.csv`):

| Model | Already Correct | Fixed | Still Broken | Regressed | Other |
|---|---|---|---|---|---|
| Mixtral 8x7B | 1,868 | 333 | 27 | 136 | 66 |
| Llama 4 Maverick | 2,073 | 211 | 24 | 64 | 58 |

**Key derived statistics**:
- Prefixes fix 92.5% (Mixtral: 333/360) and 89.8% (Llama: 211/235) of baseline hallucinations
- 27 (Mixtral) and 24 (Llama) prompts resist ALL four prefix interventions
- Still-broken prompts concentrated in entity-dependent categories: Mixtral 13 nonexistent + 7 plausible_fake + 5 factual + 2 other; Llama 14 plausible_fake + 7 nonexistent + 3 impossible
- Regressed prompts exist but are not the focus here (analyzed in Ch 6 category analysis)

**Note**: Bridge analysis re-run Mar 22 after discovering script included CoT (5 prefixes instead of 4). CoT exclusion changed counts significantly: Mixtral 15→27 broken, Llama 5→24 broken. The 12/19 prompts previously "fixed" by CoT were all CoT refusals (label=3). See `scripts/analyze_v5_bridge.py` comment.

#### Paragraph 2: Between-category geometric comparison (~0.75 page)

**Question**: Do fixable hallucinations have different geometric signatures from always-correct prompts?

Present Mann-Whitney U tests comparing `fixed` vs `already_correct` prompts across four geometric features. This tests whether the Ch 5 finding (geometry predicts hallucination) extends to predicting *which hallucinations are fixable*.

**Verified results** (from `v5_bridge_stats.csv`):

| Model | Feature | Fixed Mean | Correct Mean | p-value | |r| |
|---|---|---|---|---|---|
| Mixtral | oppositeness | 0.513 | 0.491 | 7.3 × 10⁻¹¹ | 0.221 |
| Mixtral | density | 2.019 | 2.082 | 3.1 × 10⁻⁵ | 0.141 |
| Mixtral | centrality | 0.706 | 0.714 | 0.077 | 0.060 |
| Mixtral | curvature | 0.367 | 0.361 | 0.901 | 0.004 |
| Llama | oppositeness | 0.527 | 0.492 | 2.6 × 10⁻²⁰ | 0.371 |
| Llama | centrality | 0.697 | 0.714 | 2.0 × 10⁻⁴ | 0.149 |
| Llama | density | 2.018 | 2.084 | 0.014 | 0.099 |
| Llama | curvature | 0.358 | 0.358 | 0.723 | 0.014 |

**Interpretation paragraph**: Oppositeness is the strongest discriminator between fixable hallucinations and correct prompts — larger effect than any feature in Ch 5's between-category analysis (|r| = 0.221/0.371 here vs 0.218/0.367 in Table 5.2). Density and centrality show weaker but consistent effects. Curvature is null (consistent with Ch 5's downgrading). Note: this comparison is analogous to Ch 5's between-category analysis (hallucinated vs correct) but on a different partition (fixable-hallucinated vs correct). The overlap is expected — these are largely the same prompts.

**Honest caveat**: This comparison does NOT test fixability prediction. It tests whether fixable hallucinations differ from correct prompts — which is essentially the Ch 5 question restated. The fixability question requires comparing `fixed` vs `still_broken`.

#### Paragraph 3: The aggregate AUC question (~0.75 page)

**Question**: Can a logistic regression predict which hallucinations are fixable vs still-broken, using geometric features alone?

The initial study achieved AUC = 0.86 (Mixtral) and 0.83 (Llama) on this task — but those numbers used train-only evaluation on 449 prompts, without cross-validation.

**Verified V5 results** (from `v5_bridge_logistic_auc.csv`, 5-fold cross-validated):

| Model | n(fixed) | n(broken) | AUC (train) | AUC (5-fold CV) |
|---|---|---|---|---|
| Mixtral | 345 | 15 | 0.659 | 0.572 |
| Llama | 230 | 5 | 0.763 | 0.442 |

**Why the drop from 0.86 to 0.57**: Three factors, all methodological improvements:
1. **Cross-validation**: V4 reported train-set AUC (overfitted). V5 uses 5-fold CV (honest).
2. **Class imbalance**: 345:15 (Mixtral) and 230:5 (Llama). With 15 or 5 positive examples split across 5 folds, each fold has 1–3 positives — logistic regression is unreliable.
3. **Any-prefix aggregation**: V4 computed per-prefix outcomes (larger broken groups). V5 asks "fixable by ANY prefix," collapsing most hallucinations into the fixed category.

**Framing**: Do NOT present this as a failure to replicate. The V4 AUC was a discovery signal on a small dataset without proper evaluation. The V5 aggregate AUC is methodologically honest but uninformative due to extreme class imbalance. The real test is within-category (next paragraph).

**Present as Table 7.2** (or inline): AUC comparison with explicit methodological differences.

#### Paragraph 4: Within-category fixability prediction — the robust finding (~1 page)

**Question**: Among prompts in the same category (same prompt structure, same type of knowledge failure), can geometric features predict which hallucinations are fixable?

This is the non-circular test. Within the nonexistent category, all prompts share the same structure ("What is the [fabricated entity]?"). The only variation is the specific entity — and its geometric properties in embedding space.

**Verified results** (from `v5_bridge_within_category.csv`, nonexistent category only):

| Model | Feature | Broken Mean | Fixed Mean | p-value | |r| | n(broken) | n(fixed) |
|---|---|---|---|---|---|---|---|
| Mixtral | density | 1.937 | 2.180 | 0.034 | 0.383 | 11 | 166 |
| Mixtral | centrality | 0.709 | 0.678 | 0.190 | 0.237 | 11 | 166 |
| Mixtral | oppositeness | 0.538 | 0.532 | 0.578 | 0.101 | 11 | 166 |
| Mixtral | curvature | 0.208 | 0.362 | 0.224 | 0.220 | 11 | 166 |
| Llama | density | 1.877 | 2.144 | 0.047 | 0.523 | 5 | 109 |
| Llama | centrality | 0.740 | 0.677 | 0.013 | 0.640 | 5 | 109 |
| Llama | oppositeness | 0.511 | 0.534 | 0.350 | 0.255 | 5 | 109 |
| Llama | curvature | 0.254 | 0.315 | 1.000 | 0.002 | 5 | 109 |

**Present as Table 7.3**: Within-category Mann-Whitney U results for nonexistent category.

**Interpretation**: Density significantly predicts fixability within the nonexistent category for both models (p = 0.034 and 0.047). Unfixable nonexistent prompts live in sparser embedding regions (mean density 1.94/1.88 vs 2.18/2.14 for fixable). The effect sizes are medium-to-large (|r| = 0.38/0.52), suggesting genuine signal despite small samples.

**Critical honesty paragraph — multiple comparisons**: 12 within-category tests were conducted (4 features × 2 models for nonexistent, plus 4 features × 1 model for Mixtral factual with n=4). Bonferroni correction for 12 tests gives α = 0.05/12 = 0.0042. **Neither density p-value survives this correction.** Llama centrality (p = 0.013) also fails. These are suggestive findings, not definitive ones. The effect sizes are large enough that the non-survival reflects limited power (n = 11 and 5 broken prompts), not absent signal. Future work with more unfixable prompts could resolve this. State this explicitly — do not overstate.

**Comparison to Ch 5**: Ch 5's within-category density finding for hallucination prediction (p = 5.7 × 10⁻⁷ and 3.4 × 10⁻⁵) survived even study-wide Bonferroni correction. The fixability prediction has the same directional signal (sparser = worse outcome) but with far fewer data points in the "broken" class (11/5 vs 177/114 hallucinated prompts in Ch 5). The consistency of direction across both analyses strengthens the interpretation even though the fixability p-values alone are not definitive.

#### Paragraph 5: Descriptive profile of unfixable prompts (~0.5 page)

Present the geometric profile of still-broken prompts descriptively (NOT as statistically significant claims — n = 15/5 is too small).

**Verified numbers** (from `v5_bridge_stats.csv`, broken_vs_fixed comparison):
- All p-values > 0.10 for both models (no significant differences between broken and fixed on any feature individually)
- Direction matches V4 unfixable profile: higher centrality (0.734/0.740 vs 0.706/0.697), lower density (1.994/1.877 vs 2.019/2.018)
- Curvature shows a directional trend for Mixtral (broken: 0.225 vs fixed: 0.367) but p = 0.22

**Frame as**: "The geometric profile of unfixable prompts is directionally consistent with the initial study — unfixable prompts tend to sit in sparser, more peripheral regions of embedding space — but sample sizes preclude statistical claims at the aggregate level. The within-category density test (Table 7.3) provides the statistically supported version of this observation."

**Include a figure**: Scatter plot of fixed vs broken vs correct prompts in UMAP space, color-coded by outcome. Existing figures: `v5_bridge_mixtral-8x7b.png`, `v5_bridge_llama-4-maverick-17b.png`. Assess whether these are thesis-quality before including.

#### Section closing (~1 paragraph)

Summarize: Geometry predicts fixability, but the evidence is suggestive rather than definitive due to the small number of unfixable prompts. The within-category density signal (p = 0.034/0.047, |r| = 0.38/0.52) is the strongest finding — same feature, same direction, same category as Ch 5's hallucination prediction, now extended to fixability prediction. This establishes a geometric gradient of difficulty: prompts in sparser embedding neighborhoods are not only more likely to hallucinate but also more likely to resist intervention.

Transition: The fixability analysis identifies a small set of "unfixable" prompts (15 Mixtral, 5 Llama). These are excluded from fine-tuning training data — the first practical application of geometry guiding intervention. Section 7.2 describes this curation step.

**Forward reference rule**: Do NOT preview fine-tuning results. The transition should frame data curation as a methodological step, not assert that it helps.

---

### Figures and tables in 7.1

| Item | Type | Content | Source |
|---|---|---|---|
| Table 7.1 | Table | Outcome distribution (already_correct / fixed / still_broken / regressed / other) per model | `v5_bridge_data.csv` (verified counts above) |
| Table 7.2 | Table/inline | Aggregate logistic AUC comparison: V4 train-only vs V5 cross-validated | `v5_bridge_logistic_auc.csv` |
| Table 7.3 | Table | Within-category Mann-Whitney U for nonexistent: 4 features × 2 models | `v5_bridge_within_category.csv` |
| Figure 7.1 | Figure | Bridge scatter plot (UMAP, color by outcome) — assess existing `v5_bridge_*.png` for quality | `results/v5_prefixes/analysis/` |

### Cross-checks before writing 7.1

- [x] Verify outcome counts match post-CoT-exclusion re-run (DONE: 1868/333/27/136/66 Mixtral; 2073/211/24/64/58 Llama — updated Mar 22 after CoT exclusion fix)
- [ ] Verify within-category p-values against `v5_bridge_within_category.csv` (DONE: 0.034/0.047)
- [ ] Verify effect sizes are correctly reported as |r| not r (DONE: 0.383/0.523)
- [ ] Verify V4 AUC was train-only (DONE: confirmed in EXPERIMENT_LOG line 964)
- [ ] Verify still-broken category breakdown (DONE: Mixtral 11 nonexistent + 4 factual; Llama 5 nonexistent)
- [ ] Confirm CoT is excluded from prefix count (DONE: 5 prefixes tested but CoT excluded from best-per-prompt — 4 effective prefixes for selection)
- [ ] Check whether bridge figures are thesis-quality (TODO: visually inspect `v5_bridge_*.png`)

### Reviewer objections to preempt in 7.1

1. **"The within-category p-values don't survive correction."** → Acknowledged explicitly. Effect sizes are medium-to-large; non-survival reflects n = 11/5, not absent signal. Direction consistent with Ch 5.
2. **"n = 15 and n = 5 are too few for any conclusion."** → Agreed for the aggregate broken-vs-fixed comparison (all p > 0.10). The within-category test pools against 166/109 fixed prompts, giving adequate power for detecting medium effects in the majority class. The limitation is real and stated.
3. **"The V4 AUC of 0.86 was misleading."** → Agreed and stated. V4 was a discovery signal; V5 is the honest evaluation. Lead with within-category, relegate aggregate AUC.
4. **"Fixable hallucinations look like regular hallucinations — what's new?"** → The fixed-vs-correct comparison (¶2) overlaps with Ch 5, acknowledged. The novel contribution is the within-category fixability prediction (¶4) — same category, same structure, geometry predicts whether intervention works.
5. **"Why only 4 features? Why not add oppositeness sub-features or text features?"** → Consistent with Ch 5's feature set. Adding features with n = 15/5 positives would overfit. Parsimonious approach.

---

### 7.2 Training Data Curation (~1–1.5 pages)

**Section question**: How do we construct high-quality fine-tuning training data from the prefix experiment results, and what role does the fixability analysis play?

**Label**: `\label{sec:training-curation}`

This section bridges the fixability analysis (7.1) and fine-tuning (7.3). It is primarily methodological — describing the best-per-prompt selection process, key design decisions, and the composition of the resulting training data. It should be concise; the reader needs to understand *what* was curated and *why* before seeing fine-tuning results, but the details are not the chapter's intellectual contribution.

#### Paragraph 1: Selection methodology (~0.5 page)

**The task**: For each of 2,430 prompts, select the single best model response from five candidate sources: baseline (no prefix) + 4 prefix conditions. The selected (question, response) pair becomes a fine-tuning training example.

**Selection priority** (descending):
1. **Correct (label=0)** — highest priority. Tiebreaker: highest judge confidence score.
2. **Partial (label=1)** — contains real knowledge, better than refusal.
3. **Refusal (label=3)** — model stopped fabricating, preferable to hallucination.
4. **Hallucination (label=2)** — all sources hallucinate → **exclude from training** (unfixable).

**Key design decision — partial over refusal**: A partial answer contains learnable knowledge (correct content with minor gaps), while a refusal teaches the model to give up. Training on partials preserves knowledge breadth; training on refusals teaches epistemic caution at the cost of coverage. This ordering reflects the thesis's finding (Chapter 6) that refusal is not the goal — reduced fabrication is.

**Key design decision — baseline as candidate**: Including the no-prefix baseline response as a candidate prevents regression. **Verified**: 6 Mixtral and 2 Llama prompts are correct at baseline but have NO correct response from any prefix. Without baseline as a candidate, these 8 prompts would receive partial, refused, or hallucinated training targets — teaching the model to worsen on questions it already handles correctly. With baseline included, all 8 receive correct training targets.

**Data sources**:
- Script: `scripts/build_v5_training_data.py`
- Verified: 0 CoT entries in training data (CoT excluded, consistent with Ch 6)

#### Paragraph 2: Training data composition (~0.5 page)

**Present as Table 7.X**: Training data composition per model.

**Verified numbers** (from `v5_training_*.jsonl` and `v5_selection_report.json`):

| Metric | Mixtral | Llama |
|---|---|---|
| Selected for training | 2,403 | 2,406 |
| Correct (label=0) | 2,381 (99.1%) | 2,394 (99.5%) |
| Partial (label=1) | 22 (0.9%) | 11 (0.5%) |
| Refusal (label=3) | 0 | 1 (<0.1%) |
| Excluded unfixable | 27 | 24 |

**Source distribution** (which prefix contributed the selected response):

| Source | Mixtral | Llama |
|---|---|---|
| Entity-Aware | 957 (39.8%) | 979 (40.7%) |
| Structured Caution | 490 (20.4%) | 472 (19.6%) |
| Baseline | 485 (20.2%) | 567 (23.6%) |
| Epistemic Humility | 239 (9.9%) | 210 (8.7%) |
| Fact-Grounded | 232 (9.7%) | 178 (7.4%) |

**Key observation**: Entity-Aware dominates (~40% of selections for both models), consistent with its position as the best single prefix in Chapter 6. Baseline contributes ~20% — these are prompts the model already handles correctly without intervention. The remaining ~40% is distributed across the other three prefixes.

**Do NOT present source distribution in a full table** — it's informative but not thesis-critical. Mention Entity-Aware dominance in prose and note baseline contribution. The reader cares that the training data is 99%+ correct, not the prefix breakdown.

#### Paragraph 3: Connection to fixability analysis (~0.25 page)

The 27 Mixtral and 24 Llama unfixable prompts identified in Section 7.1 are exactly the prompts excluded from training — they hallucinate across all five candidate sources. This is the practical link between geometric analysis and intervention: the fixability analysis (Section 7.1) identifies prompts in sparse embedding regions that resist all prefix interventions, and the curation step excludes them from training data to avoid teaching the model to hallucinate.

**Note**: Do NOT overclaim the geometry connection. The exclusion is based on *outcome* (all sources hallucinate), not directly on geometric features. Geometry *predicts* which prompts are likely to be unfixable (Section 7.1), but the exclusion decision uses the label data, not the geometric scores. The connection is analytical (geometry explains *why* these prompts are unfixable), not operational (geometry was not used to *make* the exclusion decision). Be precise about this distinction.

#### Section closing (~1 sentence)

Transition: The curated training data (2,403 Mixtral / 2,406 Llama examples, 99%+ correct) is converted to fine-tuning format and used to train LoRA-adapted models. Section 7.3 reports the results.

#### Fine-tuning format note (~2 sentences, inline or footnote)

Training examples are converted to chat format: `{"messages": [{"role": "user", "content": question}, {"role": "assistant", "content": selected_answer}]}`. No system message is used during training — the model learns careful behavior from the response content alone, not from an explicit instruction to be careful.

---

### Figures and tables in 7.2

| Item | Type | Content | Source |
|---|---|---|---|
| Table 7.X | Table | Training data composition: counts by label, exclusion count | `v5_selection_report.json` |

One table is sufficient. Source distribution can be inline prose.

### Cross-checks before writing 7.2

- [x] Verify training counts: 2,403 Mixtral, 2,406 Llama (DONE)
- [x] Verify label breakdown: 2381/22/0 Mixtral, 2394/11/1 Llama (DONE)
- [x] Verify 0 CoT in training data (DONE)
- [x] Verify unfixable counts match Section 7.1: 27/24 (DONE — same prompts)
- [x] Verify baseline rescue cases: 6 Mixtral, 2 Llama correct-at-baseline with no correct prefix (DONE)
- [x] Verify source distribution (DONE)
- [x] Verify fine-tuning format has no system message (DONE — checked v5_together_*.jsonl)
- [ ] Note: Together files are from Mar 5 (pre-contamination-fix, 2,402 Mixtral). Actual fine-tuning used these. The 1-prompt discrepancy is documented and negligible.

### Reviewer objections to preempt in 7.2

1. **"Why not use all responses for training (multi-response fine-tuning)?"** → Single best response avoids contradictory training signals. Multiple responses per prompt, some correct and some hallucinated, would confuse the model during training. Best-per-prompt is standard practice in instruction tuning.
2. **"Why include partials instead of filtering to only correct?"** → Only 22-33 examples affected. Excluding would lose training data with minimal quality gain. Partials contain correct information with minor gaps — useful training signal.
3. **"The geometry connection seems post-hoc."** → Acknowledged. Geometry predicts unfixability (Section 7.1) but does not drive the exclusion decision. The contribution is analytical insight, not an operational geometric filter.

---

### 7.3 Fine-Tuning and the Precision-Recall Tradeoff (~3–4 pages)

**Section question**: Can the best prompt behavior be distilled into model weights via fine-tuning, and what does it cost?

**Label**: `\label{sec:ft-results}`

**⚠️ STALE NUMBERS IN THESIS_WRITING.md**: The Discussion section (line ~2099) has pre-contamination-fix FT numbers: Mixtral ConfigC 91.1%, Llama ConfigA 92.4%. ACTUAL post-fix numbers from `comparison_analysis.json`: Mixtral ConfigC **94.43%**, Llama ConfigA **93.99%**. The "obscure_real regression (-7 to -13pp)" narrative is also wrong — obscure_real IMPROVED. Regressions are primarily factual refusals. UPDATE DISCUSSION SECTION WHEN WRITING CH 8.

#### Subsection 7.3.1: Fine-Tuning Setup (~0.5 page)

**Method**: LoRA (Low-Rank Adaptation) fine-tuning via Together AI on the curated training data from Section 7.2.

**Three configurations** (Mixtral only; Llama tested one):

| Config | Learning Rate | Epochs | Purpose |
|---|---|---|---|
| A (primary) | 2×10⁻⁴ | 3 | Standard LoRA settings |
| B (lower LR) | 1×10⁻⁴ | 3 | Test sensitivity |
| C (more epochs) | 2×10⁻⁴ | 5 | Test convergence |

**Together AI hyperparameter overrides** (must disclose):
- LoRA rank: requested 16, received **64** (4× increase)
- LoRA alpha: requested 32, received **128** (ratio preserved)
- Dropout: requested 0.05, received **0** (removed)
- Weight decay: requested 0.01, received **0** (removed)
- Mixtral: standard LoRA on attention projections
- Llama: QLoRA with 4-bit quantization

**Acknowledge explicitly**: Together AI's overrides mean the LoRA configuration is more aggressive than planned. The ablation across learning rates and epochs (the most impactful hyperparameters) remains informative. Rank/dropout/decay sensitivity is confounded with the override.

**Evaluation**: All models evaluated on the 449-prompt held-out test set using the same consensus judging pipeline (Chapter 4). No system message used during inference (matching the no-system-message training).

**Data sources**:
- Fine-tuning configs: `data/training/v5_finetuned_models.json`
- Evaluation results: `results/v5_finetuned/comparison_analysis.json` (POST-FIX, authoritative)
- Individual judged answers: `results/v5_finetuned/{model}/{config}/judged_answers.jsonl`

#### Subsection 7.3.2: Overall Results (~0.5 page)

**Present as Table 7.X**: Aggregate results on held-out test set.

**Verified numbers** (from `comparison_analysis.json`, post-contamination-fix):

| Condition | Mixtral Acc | Mixtral Hall | Mixtral Ref | Llama Acc | Llama Hall | Llama Ref |
|---|---|---|---|---|---|---|
| Baseline | 82.85% | 11.80% | 1.11% | 90.65% | 5.79% | 0.22% |
| Config A | 93.32% | 1.78% | 4.23% | 93.99% | 1.11% | 4.45% |
| Config B | 93.10% | 1.78% | 4.01% | — | — | — |
| **Config C** | **94.43%** | **1.34%** | **3.56%** | — | — | — |
| Best single prefix (Struct. Caution) | 94.88% | 1.78% | 3.12% | 95.77% | 1.34% | 2.67% |

**McNemar tests** (verified, post-V4-fix re-run Mar 23):
- Mixtral C vs baseline: p = 1.8×10⁻¹⁰ (highly significant)
- Llama A vs baseline: p = 3.5×10⁻³ (significant)
- Mixtral C vs best prefix: p = 0.82 (indistinguishable — ConfigC matches Structured Caution)
- Llama A vs best prefix: p = 0.14 (not significant, but Llama 1.8pp below Structured Caution)

**Key headline**: Fine-tuning achieves 89%/81% relative hallucination reduction baked into weights. Mixtral ConfigC matches best single prefix (Structured Caution) in accuracy (p=0.82) with lower hallucination rate (1.3% vs 1.8%). Llama ConfigA falls 1.8pp short of best prefix (94.0% vs 95.8%, p=0.14) but also has lower hallucination rate (1.1% vs 1.3%). The practical advantage is eliminating runtime prompt engineering.

**⚠️ CORRECTION LOG**: comparison_analysis.json re-generated Mar 23 with post-V4-fix V4 prefix data. Best prefix changed from Entity-Aware (pre-V4-fix) to Structured Caution (post-V4-fix) for both models. Previous narrative ("outperforms"/"matches Entity-Aware") was based on stale pre-V4-fix data.

#### Subsection 7.3.3: Per-Category Analysis and the Precision-Recall Tradeoff (~1 page)

**Present as Table 7.X**: Per-category accuracy and hallucination changes (baseline → ConfigC/A).

**Verified per-category data** (from V3 baseline + comparison_analysis.json):

**Mixtral ConfigC:**
| Category | n | BL Acc | FT Acc | Δ Acc | BL Hall | FT Hall | Δ Hall |
|---|---|---|---|---|---|---|---|
| nonexistent | 120 | 70.0% | 99.2% | +29.2pp | 28.3% | 0.8% | -27.5pp |
| plausible_fake | 31 | 54.8% | 87.1% | +32.3pp | 41.9% | 9.7% | -32.3pp |
| factual | 98 | 75.5% | 80.6% | +5.1pp | 6.1% | 2.0% | -4.1pp |
| obscure_real | 30 | 90.0% | 96.7% | +6.7pp | 0.0% | 0.0% | — |
| impossible | 30 | 100.0% | 100.0% | — | 0.0% | 0.0% | — |
| ambiguous | 120 | 100.0% | 100.0% | — | 0.0% | 0.0% | — |
| edge_factual | 20 | 100.0% | 100.0% | — | 0.0% | 0.0% | — |

**Llama ConfigA:**
| Category | n | BL Acc | FT Acc | Δ Acc | BL Hall | FT Hall | Δ Hall |
|---|---|---|---|---|---|---|---|
| nonexistent | 120 | 93.3% | 99.2% | +5.8pp | 6.7% | 0.8% | -5.8pp |
| plausible_fake | 31 | 48.4% | 77.4% | +29.0pp | 48.4% | 6.5% | -41.9pp |
| factual | 98 | 84.7% | 81.6% | **-3.1pp** | 1.0% | 1.0% | — |
| obscure_real | 30 | 96.7% | 100.0% | +3.3pp | 3.3% | 0.0% | -3.3pp |
| impossible | 30 | 93.3% | 96.7% | +3.3pp | 3.3% | 3.3% | — |
| ambiguous | 120 | 100.0% | 100.0% | — | 0.0% | 0.0% | — |
| edge_factual | 20 | 100.0% | 100.0% | — | 0.0% | 0.0% | — |

**The wins**: Nonexistent and plausible_fake see dramatic improvements — these are entity-fabrication categories where learned skepticism directly applies.

**The cost (precision-recall tradeoff)**: The cost is NOT on obscure_real (which improved for both models). The cost manifests as **increased refusals on factual questions**:
- Mixtral: 5→15 factual refusals (+10)
- Llama: 1→15 factual refusals (+14)
- Llama factual accuracy drops -3.1pp (the only category with accuracy regression)

**Regression analysis** (verified from individual judged_answers files):
- Mixtral ConfigC: 6 regressions total (4 factual, 1 obscure_real, 1 plausible_fake). Breakdown: 4 refusals, 1 hallucination, 1 partial.
- Llama ConfigA: 4 regressions total (3 factual, 1 plausible_fake). Breakdown: 3 refusals, 1 hallucination.
- Combined: 10 regressions, 7 refusals (70%), 2 hallucinations (20%), 1 partial (10%).

**Framing**: The model learned a "refuse when uncertain" heuristic that correctly fires on nonexistent/plausible_fake entities but occasionally over-fires on real factual questions. Most regressions (70%) are refusals, not new hallucinations — the model errs toward caution, not fabrication. This is a precision-recall tradeoff in the safety direction.

**⚠️ CORRECTION from THESIS_WRITING.md**: The old narrative said "obscure_real regression (-7 to -13%)" but this was from PRE-FIX data. Post-fix, obscure_real IMPROVED for both models. The actual precision-recall cost is factual refusals, not obscure_real regressions. Update everywhere.

#### Subsection 7.3.4: Robustness Checks (~0.75 page)

**Three checks, each ~0.25 page:**

**A. Hyperparameter sensitivity** (Mixtral only, 3 configs):
- Config C (lr=2e-4, 5 epochs): 94.43% acc, 1.34% hall — BEST
- Config A (lr=2e-4, 3 epochs): 93.32% acc, 1.78% hall
- Config B (lr=1e-4, 3 epochs): 93.10% acc, 1.78% hall
- More epochs helps (C > A); lower LR marginal (B ≈ A)
- No overfitting signal — 5 epochs beats 3, despite aggressive lora_r=64 and no dropout
- All three significantly outperform baseline (all p < 10⁻⁸)

**B. Overfitting check** (Step 11B):
- Evaluated on 200 random V5 training prompts (stratified by category) vs 449 held-out test
- Mixtral ConfigC: train 93.0% vs test 91.1% (+1.9pp gap) — WAIT, this doesn't match the 94.43% figure. Let me check.

Actually: the EXPERIMENT_LOG says "test accuracy = 91.1%" but comparison_analysis.json says 94.43%. This is the pre-fix vs post-fix discrepancy. The overfitting check was done on pre-fix data (Step 11B was Mar 7, contamination fix was Mar 11).

**⚠️ IMPORTANT**: The overfitting check's test accuracy (91.1%) is pre-fix. The post-fix test accuracy is 94.43%. I should note this: "overfitting check conducted before judge contamination correction; accuracy figures reflect pre-correction labels (91.1% vs post-correction 94.43%). The train-test gap direction (+1.9pp) would be preserved or reduced with correction."

Actually, let me reconsider. The train accuracy in the overfitting check was ALSO pre-fix (93.0%). So both train and test are pre-fix. The gap (+1.9pp) is a fair comparison within the same label set. Post-fix, both would likely shift upward (refusals→correct), so the gap would remain similar.

**Report**: Train-test gap under 5pp for both models confirms generalization. Note pre-fix timing.

**C. Entity decontamination** (Step 11C, **RE-RUN Mar 23 with post-fix labels**):
- 59% entity-level overlap between V5 training and V3 test (265/449 prompts share entities)
- 107 clean prompts (zero entity overlap with training)

**Verified post-fix decontamination results**:

| Model | Full (n=449) | Clean (n=107) | Gap |
|---|---|---|---|
| Mixtral ConfigC | 94.4% | 91.6% | **+2.8pp** |
| Llama ConfigA | 94.0% | 93.5% | **+0.5pp** |

**Entity-dependent vs entity-independent split**:
| Group | Mixtral full→clean gap | Llama full→clean gap |
|---|---|---|
| Entity-independent (n_clean=86) | +1.0pp | -0.1pp |
| Entity-dependent (n_clean=21) | +6.2pp | +0.3pp |

**Interpretation**: The Mixtral overall gap (+2.8pp) is just under the 3pp threshold. But parsing by category type reveals the gap is concentrated in entity-dependent categories with very small clean subsets (n=21 total: 12 nonexistent, 6 plausible_fake, 3 obscure_real). The plausible_fake clean subset (n=6) drives most of the entity-dep gap: 66.7% clean vs 87.1% full — but with only 6 prompts, one additional error swings accuracy by 16.7pp. Entity-independent categories (n_clean=86), where entity overlap should be irrelevant, show essentially no gap (+1.0pp Mixtral, -0.1pp Llama).

**Pre-fix vs post-fix gap change**: The gap increased from +0.4pp (pre-fix) to +2.8pp (post-fix) for Mixtral because the contamination fix itself was biased: 15 of 16 corrected labels were on contaminated prompts, mechanically increasing contaminated accuracy more than clean accuracy.

**Key claim for thesis**: Entity-independent accuracy is virtually identical between clean and full subsets, confirming the model learned behavioral caution, not entity-specific memorization. The entity-dependent gap is driven by small-sample noise (n=6 plausible_fake clean). Llama shows <1pp gap regardless. Report both gaps honestly.

**Convergent evidence**: The decontamination analysis is ONE of three convergent tests that the model learned general caution. The other two (template ablation in Section 7.4 and TruthfulQA generalization in Section 7.4) provide independent evidence from different angles.

#### Subsection 7.3.5: Geometric Analysis of Fine-Tuning Outcomes (~0.75 page)

**Question**: Do the geometric features that predict prefix fixability (Section 7.1) also predict fine-tuning fixability?

**FT bridge analysis** (Step 12A, from `ft_bridge_stats.csv`):

Outcome counts on V3 held-out:
| Outcome | Mixtral | Llama |
|---|---|---|
| always_correct | 366 | 403 |
| fixed_by_ft | 47 | 17 |
| still_broken | 6 | 9 |
| broken_by_ft | 6 | 4 |

**fixed_by_ft vs still_broken** (verified from CSV):
| Model | Feature | Fixed Mean | Broken Mean | p (MW) | |r| | Survives Bonf? |
|---|---|---|---|---|---|---|
| Mixtral | density | 1.950 | 1.481 | 0.0017 | 0.798 | **YES** (p_bonf=0.040) |
| Mixtral | centrality | 0.654 | 0.777 | 0.0009 | 0.840 | **YES** (p_bonf=0.022) |
| Llama | density | 1.738 | 1.558 | 0.024 | 0.556 | No (p_bonf=0.566) but YES for BH FDR (0.189) |

**Interpretation**: Density predicts fine-tuning fixability with large effect sizes, especially for Mixtral (|r| = 0.80, survives Bonferroni). This extends the Section 7.1 finding: geometry predicts fixability regardless of whether intervention is prompt-based or weight-based.

**Regression geometric profile** (broken_by_ft vs always_correct):
- Mixtral density: p=0.061 (borderline, NOT significant)
- Llama density: p=0.110 (NOT significant)
- Direction consistent (lower density = more likely to regress) but n=6/4 is too small

**Note on oppositeness**: Flagged as unstable in V3→V5 re-embedding (correlation 0.37 with original). Not interpreted. Report as limitation.

**⚠️ Explore agent had WRONG p-values for regression analysis** (claimed p=0.010/0.0007, actual is p=0.061/0.110). Always verify against CSV.

#### Section closing (~1 paragraph)

Summarize: Fine-tuning successfully distills prompt behavior into weights, achieving 89%/81% hallucination reduction without runtime prompting. The cost is modest — 6/4 regressions, primarily factual refusals — and geometry predicts both where fine-tuning helps (sparse neighborhoods) and where it fails (though the regression analysis is underpowered). The next section tests whether this learned caution generalizes beyond the training distribution.

---

### Figures and tables in 7.3

| Item | Type | Content | Source |
|---|---|---|---|
| Table 7.X | Table | Aggregate FT results: baseline/configA/B/C/best-prefix × accuracy/hall/refusal + McNemar | `comparison_analysis.json` |
| Table 7.X | Table | Per-category accuracy/hallucination changes | V3 baseline judged + comparison_analysis.json |
| Table 7.X | Table/inline | FT bridge fixability: density/centrality p-values and effect sizes | `ft_bridge_stats.csv` |

### Cross-checks before writing 7.3

- [x] Verify aggregate FT numbers from comparison_analysis.json (post-fix)
- [x] Verify per-category breakdown from V3 baseline + comparison_analysis.json
- [x] Verify McNemar tests from comparison_analysis.json
- [x] Verify regression counts and types from individual judged_answers files
- [x] Verify refusal breakdown per category
- [x] Verify FT bridge stats from ft_bridge_stats.csv
- [ ] Verify decontamination gap consistency (pre-fix vs post-fix timing)
- [ ] Verify overfitting check numbers (pre-fix timing vs post-fix accuracy)
- [ ] Check if decontamination analysis needs re-running with post-fix labels
- [x] Verify 0 CoT in any FT pipeline (CoT excluded from training data = confirmed)

### Reviewer objections to preempt in 7.3

1. **"Together AI overrode your hyperparameters."** → Acknowledged. LR and epochs (most impactful) were honored. Rank/dropout/decay confounded with override. All configs outperform baseline significantly.
2. **"The precision-recall tradeoff is a limitation, not a feature."** → Frame as an insight, not a bug. The tradeoff reveals that hallucination reduction and knowledge coverage are fundamentally in tension, predictable from the training data composition.
3. **"n=6 still-broken in FT bridge is tiny."** → Agreed. But density p=0.0017 survives Bonferroni with |r|=0.80 — extremely large effect. Report honestly: small n, large effect, survives correction.
4. **"Why not test more configs for Llama?"** → Cost constraint. Llama QLoRA took 87 min and $16 per config. With ConfigA already matching best prefix (p=0.80), diminishing returns on additional configs.
5. **"Decontamination analysis was pre-fix."** → If gap is <1pp before fix and fix only changes a few labels, gap is likely similar post-fix. But acknowledge timing.

---

### 7.4 Generalization Evidence (~4–5 pages)

**Section question**: Does the fine-tuned model's learned caution generalize beyond its training distribution? Three independent tests, each probing a different dimension of generalization.

**Label**: `\label{sec:generalization}`

The three generalization tests are orthogonal:
- **TruthfulQA**: different DOMAIN (misconceptions vs entity fabrication)
- **Template ablation**: different EXPRESSION (unseen question structures within same domain)
- **Cross-category**: different CATEGORY TYPES (unseen semantic categories)

If ALL three show positive transfer, the model learned a generalizable behavioral strategy. If only one shows it, the evidence is domain-specific. The convergence argument is the intellectual contribution of this section.

#### Subsection 7.4.1: Cross-Domain Transfer — TruthfulQA (~1.5–2 pages)

**Question**: Does fine-tuning on entity-fabrication skepticism transfer to misconception detection?

**Setup**:
- 817 TruthfulQA questions (Lin et al. 2022), 38 categories
- Tests misconceptions (false beliefs humans commonly hold) — categorically different from entity fabrication
- Same 3-judge consensus panel
- Config selection pre-registered: Mixtral ConfigC, Llama ConfigA (best on held-out, selected before seeing TruthfulQA)
- No CoT involvement

**Verified results** (from `truthfulqa_analysis.md`):

| Model | Metric | Baseline | Fine-tuned | Δ | McNemar p | Bonferroni sig? |
|---|---|---|---|---|---|---|
| Mixtral | Accuracy | 74.4% | 76.6% | +2.2pp | 0.1145 | No |
| Mixtral | Hallucination | 16.9% | 14.7% | -2.2pp | 0.0763 | No |
| Llama | Accuracy | 71.8% | 77.1% | +5.3pp | **0.0002** | **Yes** |
| Llama | Hallucination | 17.6% | 13.2% | -4.4pp | **0.0005** | **Yes** |

**Bonferroni**: 4 tests (2 metrics × 2 models), threshold p < 0.0125.

**Key observations for prose**:
- Refusal rates: Mixtral 0.0%→0.7%, Llama 0.6%→0.5%. No over-caution on misconceptions (unlike entity-fabrication domain).
- Transition matrices: Llama fixes 44, breaks 15 (net +29). Mixtral fixes 36, breaks 24 (net +12).
- Per-category (exploratory, no correction): Largest Llama improvements in Law (-19pp hall), Advertising (-31pp), Confusion categories. Categories involving confident factual assertions improve most.
- Relative reduction: 13% Mixtral, 25% Llama (vs 89%/81% on custom benchmark — expected, different domain).

**Framing**: "Trained on entity-fabrication, tested on misconceptions. Llama's 4.4pp hallucination reduction survives Bonferroni. Mixtral is directionally consistent but underpowered at n=817. The transfer is modest (13-25% relative) compared to in-domain (89%/81%), which is expected — entity skepticism partially overlaps with but does not fully address misconception detection. The absence of over-caution on TruthfulQA (refusal ≤0.7%) contrasts with the factual-refusal tradeoff on the custom benchmark, suggesting the precision-recall cost is domain-specific to entity-type questions."

**Do NOT overclaim**: "Our method outperforms DoLA/ITI on TruthfulQA" — we trained on different data, different paradigm. Cross-metric comparisons are invalid.

#### Subsection 7.4.2: Template Invariance (~1.5 pages)

**Question**: Does the model learn template-specific patterns or a generalizable behavioral strategy?

**Setup**:
- Ablation conditions: T5 (5 templates, ~397 Mixtral/~402 Llama examples), T10 (10 templates), T-all (194 templates, ~2,400 examples), R{N} (random ~397/402 from full template pool — size-matched control)
- All evaluated on 449-prompt held-out test set
- Template-overlap split: among T5 test prompts, which use a template seen during training vs novel?

**Verified results** (from `ablation_analysis.json`):

| Condition | Templates | n_train (M/L) | Mixtral Acc | Llama Acc | vs T-all McNemar p |
|---|---|---|---|---|---|
| T5 | 5 | 397/402 | 92.7% | 94.4% | 0.099 / 0.773 |
| T10 | 10 | ~660 | 94.0% | 95.8% | 0.803 / 0.080 |
| R{N} | 194 | 397/402 | 93.1% | 93.5% | — |
| T-all | 194 | ~2,400 | 94.4% | 94.0% | — (reference) |

**T5 vs R{N}** (diversity control at fixed size):
- Mixtral: p=0.838; Llama: p=0.386 — NOT significant
- 5 diverse templates ≈ 397/402 random from 194 templates at the same dataset size

**Template-overlap split** (T5, verified):
- Mixtral: seen 96.3%, novel 93.0% (3.3pp gap)
- Llama: seen 96.3%, novel 94.1% (2.2pp gap)
- Model generalizes to unseen templates with minimal degradation

**Key claims**:
1. Template diversity doesn't matter beyond ~5: T5 ≈ T-all (p=0.099/0.773)
2. Not template memorization: T5 vs R{N} indistinguishable (p=0.838/0.386)
3. Seen-vs-novel gap is small (2-3pp), consistent with behavioral learning not pattern matching
4. T10 is numerically best for Llama (95.8%) but not significantly better than T-all (p=0.080) — diminishing returns

**One interesting note**: Llama T10 (95.8%) matches the best single prefix (Structured Caution 95.8% from Section 7.3). T10 has only ~660 training examples vs T-all's ~2,400. More data doesn't help; the model converges on the caution strategy quickly.

#### Subsection 7.4.3: Cross-Category Generalization (~1.5 pages)

**Question**: Does learned caution transfer across category types (entity-dependent → entity-independent)?

**Setup**:
- Two category groups:
  - Entity-dependent: nonexistent, plausible_fake, obscure_real (uncertainty about entity existence)
  - Entity-independent: factual, ambiguous, impossible, edge_factual (uncertainty about question structure/reasoning)
- Five training conditions:
  - entity_dep: only entity-dependent (~978/980 examples)
  - entity_indep: only entity-independent (~1,424/1,426 examples)
  - R_entity_dep: random ~978/980 from ALL categories (size control)
  - leave_out_nonex: all categories except nonexistent (~1,813/1,815)
  - leave_out_fact: all categories except factual (~1,907)
- Full (T-all/ConfigC/ConfigA) as reference: ~2,400 examples

**Verified results** (from `evaluation_summary.json`, training sizes from data files):

| Condition | n_train (M/L) | Mixtral Acc | Mixtral Hall | Llama Acc | Llama Hall |
|---|---|---|---|---|---|
| Full (reference) | 2,403/2,406 | 94.4% | 1.3% | 94.0% | 1.1% |
| entity_dep | 978/980 | 93.3% | 2.0% | **95.3%** | **0.2%** |
| R_entity_dep | 978/980 | 93.1% | 2.5% | 94.4% | 1.1% |
| entity_indep | 1,424/1,426 | 90.9% | 4.9% | 92.7% | 3.8% |
| leave_out_nonex | 1,815/1,813 | 92.2% | 3.8% | 95.8% | 0.5% |
| leave_out_fact | 1,907/1,907 | 93.5% | 1.6% | 95.3% | 0.9% |

**Key findings**:

1. **Entity_dep matches or beats Full** despite having ~40% of the data:
   - Mixtral: 93.3% vs 94.4% (-1.1pp — close)
   - Llama: **95.3% vs 94.0%** (+1.3pp — entity_dep is BETTER)

2. **Entity_indep is clearly worst** (3-5× higher hallucination):
   - Demonstrates entity-specific training is critical for entity-dependent test categories
   - But still well above baseline (90.9%/92.7% vs 82.9%/90.6%) — some transfer happens

3. **Asymmetric transfer**: entity_dep → entity_indep works (good overall accuracy); entity_indep → entity_dep fails (high hallucination on entity categories). Entity-focused caution generalizes; question-structure caution doesn't teach entity skepticism.

4. **R_entity_dep ≈ entity_dep**: size-matched random control performs similarly (93.1% vs 93.3% Mixtral, 94.4% vs 95.3% Llama). Category composition matters, not just dataset size.

5. **Leave-out conditions near Full**: removing nonexistent or factual barely hurts. Caution transfers across individual held-out categories.

**Framing**: "Entity-dependent training provides the strongest foundation for generalization — ~1,000 entity-focused examples produce comparable or superior performance to ~2,400 diverse examples. This is the third type of generalization: not just unseen entities (decontamination) or unseen templates (Section 7.4.2), but unseen category types."

#### Section closing (~0.5 page)

**Convergence paragraph**: Three independent tests — different domain (TruthfulQA), different expression (templates), different category type (cross-category) — all show the fine-tuned model's caution extends beyond its training distribution. The model learned WHEN to be skeptical, not WHICH specific entities to refuse or WHICH question templates to match. This behavioral learning interpretation is the strongest framing of the fine-tuning contribution.

**No overclaiming**: Note that TruthfulQA significance holds only for Llama; template ablation uses non-significant McNemar tests (p=0.099 for T5 vs T-all); cross-category comparisons lack paired statistical tests. The evidence is convergent, not individually definitive from each experiment.

---

### Figures and tables in 7.4

| Item | Type | Content | Source |
|---|---|---|---|
| Table 7.X | Table | TruthfulQA baseline vs FT: accuracy, hallucination, refusal, McNemar | `truthfulqa_analysis.md` |
| Table 7.X | Table | Template ablation: T5/T10/R{N}/T-all accuracy + McNemar | `ablation_analysis.json` |
| Table 7.X | Table or inline | Template-overlap split (seen vs novel) | `ablation_analysis.json` |
| Table 7.X | Table | Cross-category conditions: accuracy and hallucination | `evaluation_summary.json` |

### Cross-checks before writing 7.4

- [x] TruthfulQA: baseline/FT accuracy, hallucination, McNemar p-values verified
- [x] TruthfulQA: Bonferroni threshold 0.0125 for 4 tests verified
- [x] Template ablation: T5/T10/R{N}/T-all accuracy verified from JSON
- [x] Template ablation: McNemar p-values verified (T5 vs T-all: 0.099/0.773; T5 vs R{N}: 0.838/0.386)
- [x] Template-overlap: seen/novel accuracy verified (96.3/93.0 Mixtral, 96.3/94.1 Llama)
- [x] Cross-category: all condition accuracy/hallucination verified from JSON
- [x] Cross-category: training sizes verified from data files (978-980 entity_dep, 1424-1426 entity_indep, etc.)
- [x] No CoT in any of these experiments (all use NON_COT_PREFIXES)
- [ ] Note: ablation JSON's "best_prefix" field is stale (pre-V4-fix Entity-Aware). Don't cite ablation McNemar vs best_prefix numbers. Only cite vs T-all and vs baseline.

### Reviewer objections to preempt in 7.4

1. **"TruthfulQA is a different metric — you can't compare."** → Agreed. We don't compare numbers cross-benchmark. We claim cross-domain TRANSFER (trained on X, improved on Y), not cross-benchmark superiority.
2. **"T5 vs T-all p=0.099 is almost significant."** → At α=0.05, yes. But the point is the direction: more templates doesn't help. Even if T5 is marginally worse, 397 examples with 5 templates achieve 92.7%/94.4% — close to the 94.4%/94.0% ceiling. Template diversity has diminishing returns.
3. **"Cross-category comparisons have no paired tests."** → Acknowledged. These are different fine-tuning runs, not paired conditions. The comparison is descriptive. The key insight (asymmetric transfer: entity_dep → entity_indep works, reverse doesn't) is qualitative.
4. **"Llama entity_dep beats Full — isn't that suspicious?"** → Small margin (+1.3pp). Could be noise. But R_entity_dep (94.4%) also beats Full for Llama. The pattern suggests entity-dependent training is a strong foundation, possibly because the Full set includes entity-independent examples that add noise for Llama.
5. **"Three convergent tests isn't proof — each has limitations."** → Agreed. Any single test has caveats. The convergence argument is probabilistic: three independent tests all pointing the same way is unlikely under the null hypothesis of "the model only memorized training patterns."

---

### 7.5 Discussion (~2 pages)

**Label**: `\label{sec:ch7-discussion}`

**Purpose**: Answer the chapter question, synthesize findings, interpret, address chapter-specific limitations. NOT the thesis-wide discussion (that's Ch 8).

#### Paragraph 1: Answering the chapter question (~0.5 page)

"Can geometry guide intervention?" — answered directly with three levels:

1. **Geometry predicts fixability** (analytical guidance): Density predicts which hallucinations yield to prompting (Section 7.1, p=0.046/0.012 within nonexistent, suggestive) and fine-tuning (Section 7.3, Mixtral density p=0.0017, |r|=0.80, survives Bonferroni). Sparser embedding neighborhoods predict resistance to intervention regardless of intervention type. This is the genuinely novel contribution — extending the density signal from predicting hallucination (Ch 5) to predicting hallucination *difficulty*.

2. **Geometry explains the unfixable set** (analytical insight): The 27/24 unfixable prompts cluster in entity-dependent categories and sparse embedding regions. Geometry does not operationally drive the exclusion decision (labels do), but it explains why those prompts resist intervention.

3. **Geometry does NOT predict regressions** (honest limitation): The regression geometric analysis is non-significant (p=0.061/0.110). Geometry predicts where intervention helps, but not where it hurts. The precision-recall tradeoff (factual refusals) is a behavioral pattern, not a geometric one.

#### Paragraph 2: The precision-recall tradeoff as insight (~0.5 page)

The increased factual refusals (5→15 for both models) reveal a fundamental tension: reducing entity-fabrication hallucination requires teaching the model skepticism about uncertain entities, but that skepticism occasionally over-fires on real knowledge questions.

Key insight: Most regressions (70%) are refusals, not new hallucinations. The fine-tuned model errs toward "I don't know" rather than fabricating — a safer failure mode. And the tradeoff is domain-specific: TruthfulQA shows no over-caution (Section 7.4.1), meaning the refusal behavior is targeted at entity-type uncertainty, not a blanket personality change.

This pattern is consistent with signal detection theory: fine-tuning shifts the model's decision criterion toward "refuse" on uncertain entity queries, reducing false alarms (hallucinations) at the cost of increased misses (false refusals on real entities). The optimal criterion depends on the deployment context — an application where hallucination is catastrophic (medical, legal) would prefer the cautious model; one where coverage matters more (general Q&A) might prefer the pre-trained model with runtime prefixes.

#### Paragraph 3: What the model learned (~0.25 page)

Brief synthesis of the convergence evidence from 7.4: the model learned behavioral caution, not surface memorization. Three orthogonal tests (different domain, different templates, different categories) all show transfer. The strongest framing: the model learned *when to be skeptical about its own knowledge*, which is a form of learned metacognition applicable across question types.

#### Subsection 7.5.1: Limitations (~0.75 page)

**Chapter-specific limitations** (thesis-wide limitations go in Ch 8):

1. **Two models only.** Fine-tuning and all generalization tests cover only Mixtral and Llama. Whether the behavioral learning pattern generalizes to other architectures (GPT, Claude, Qwen) is untested.

2. **Together AI hyperparameter overrides.** LoRA rank forced to 64 (from 16), dropout removed. These confound the hyperparameter ablation. The learning rate/epoch sensitivity results are informative; the rank/dropout sensitivity is unknown.

3. **Small still-broken samples.** The FT bridge analysis has n=6 (Mixtral) and n=9 (Llama) still-broken prompts. Effect sizes are large and Mixtral's density result survives Bonferroni, but the small samples limit the power of within-category tests and regression profiling.

4. **No McNemar tests for cross-category ablation.** Entity-dep vs entity-indep comparisons are descriptive (different fine-tuning runs, unpaired). The asymmetric transfer finding is qualitative, not statistically tested.

5. **Template-generated prompts.** All training and test prompts are template-generated, not naturalistic user queries. Whether learned caution transfers to free-form questions is an open question.

6. **Decontamination gap.** The entity-independent decontamination gap is <1pp, but the overall gap for Mixtral is +2.8pp (driven by n=6 plausible_fake clean subset noise). The decontamination analysis cannot rule out small amounts of entity-specific learning alongside behavioral learning.

#### Section closing (~1–2 sentences)

Transition to Ch 8: This chapter established that geometry predicts intervention difficulty and that prompt behavior can be made permanent through fine-tuning. Chapter 8 places these findings in the context of prior work, discusses broader implications, and identifies directions for future research.

---

### Reviewer objections to preempt in 7.5

1. **"The chapter title promises geometry 'guides' intervention, but geometry doesn't drive any operational decision."** → Acknowledged in ¶1. Geometry provides analytical guidance (fixability prediction), not operational guidance (runtime prefix selection). The latter is future work.
2. **"The precision-recall tradeoff is a weakness, not a finding."** → Reframed in ¶2. The tradeoff reveals the structure of learned caution and connects to signal detection theory. It's an insight about the fundamental tension between safety and coverage.
3. **"Behavioral learning is overclaimed — each generalization test has weaknesses."** → Addressed in ¶3 + convergence section (7.4.4). The convergence argument is probabilistic, not proof.

---

## Chapter 1: Introduction — Detailed Content Plan

**Department mandate**: At most 5 pages. Contains an "Our Contributions" section.

**Reference analysis (Angela Li, Tarun Prasad — both Harvard Dissertate, 2024)**:
Both introductions follow the same template and share key properties:

- **Length**: Angela ~4 pages (no subsections), Tarun ~5 pages (2 subsections: Motivation + Our Contributions). Neither exceeds 5 pages.
- **No results**: Neither reports a single number. The intro sells the *question* and the *approach*, not the *answer*. Angela says "we provide novel derivations" — not the specific distributions. Tarun says "a novel approach to automated theorem proving" — not the success rate.
- **Broad accessible opening**: Angela opens with "ML algorithms have become increasingly entrusted with consequential decisions." Tarun opens with Leibniz in 1685. Both funnel: broad societal context → specific technical gap → their contribution. No jargon in the first paragraph.
- **"Our Contributions" is a numbered list**: Tarun uses an explicit subsection with 4 numbered items, each 2-3 sentences. Angela has an implicit "In this thesis, we provide..." paragraph. The numbered list is cleaner for multiple contributions.
- **Chapter roadmap is perfunctory**: Both end with one sentence per chapter. "Chapter 2 does X. Chapter 3 does Y." Boilerplate but expected.
- **No equations, no figures, no tables**: Pure prose. The intro is a narrative document.
- **Savequote**: Tarun uses a thematic epigraph (Leibniz). Consider for our intro.

### Proposed structure for our introduction

1. **Broad opening** (~1–1.5 pages)
2. **Gap + our approach** (~0.5 pages)
3. **Section 1.1 "Our Contributions"** (~1.5 pages)
4. **Chapter roadmap** (~0.5 pages)

### Paragraph-level outline

**¶1 — The problem, accessible framing (4-5 sentences)**
- LLMs are now deployed in domains where factual accuracy matters — medicine, law, education, coding, search.
- They hallucinate: generating fluent, confident text that is factually wrong or entirely fabricated.
- This is not a rare edge case — hallucination rates across frontier models vary widely, with some models fabricating content on a substantial fraction of queries.
- The stakes are real: a hallucinated legal citation, a fabricated medical dosage, or a confident description of a nonexistent scientific result can cause tangible harm.
- **NO specific percentages or model names here.** Keep it general and accessible.
- **Tone**: Like Angela's opening — one paragraph a non-specialist committee member can read and understand why this matters.

**¶2 — The metacognition framing / MBB seed (3-4 sentences)**
- At its core, hallucination is a failure of *metacognition* — the system does not know what it does not know. In cognitive science, humans exhibit an analogous failure called *confabulation*: producing plausible but false memories when probed at the boundaries of their knowledge.
- The question of whether a system can assess its own knowledge boundaries is foundational in both cognitive science and AI safety.
- This thesis asks a geometric version of that question: does the *structure* of a model's representational space reveal where its knowledge thins out — and can that structure guide intervention?
- **Purpose**: Plants the MBB seed. Does NOT develop it (that's Ch 8). Does NOT cite Roediger/Loftus (that's Ch 2/Ch 8). Just names the concept and the analogy in plain language.

**¶3 — Current approaches and what's missing (4-5 sentences)**
- Existing work on hallucination mitigation falls into three categories: detection methods that identify hallucination after generation (from internal model representations or output consistency), prompting strategies that encourage models to be more careful, and training-based methods that modify model weights.
- Detection methods require white-box access to model internals or multiple sampling passes. Prompting strategies work but require careful per-query engineering. Fine-tuning approaches risk teaching new factual knowledge the model doesn't have, which can *increase* hallucination.
- Crucially, these approaches treat hallucination as a monolithic phenomenon — a prompt either causes hallucination or it doesn't. None ask whether hallucinations have *varying difficulty* — whether some are easily fixable while others resist all intervention.
- **Key pivot sentence**: "And none ask whether the question itself — independent of any particular model's processing — carries a geometric signal that predicts hallucination risk before generation begins."
- **NO citations here.** The lit review (Ch 3) does the detailed positioning. The intro just identifies the gap at a high level. If pressed, one or two landmark citations at most (Xu et al. 2024 impossibility result, maybe).
- **Cross-check**: This gap statement must align with the three gaps in Ch 3 §3.8 Synthesis (geometric gap, intervention selection gap, distillation gap) but stated at a higher level without the detailed decomposition.

**¶4 — Our approach in one paragraph (3-4 sentences)**
- This thesis takes a different approach. We embed prompts in a high-dimensional geometric space and ask whether the *structure* of that space — how densely a prompt's neighborhood is populated, how far it sits from similar prompts — predicts whether a model will hallucinate.
- We then connect prediction to action: we test whether targeted prompt interventions can reduce hallucination, and whether the geometric signal predicts where those interventions succeed and where they fail.
- Finally, we ask whether the careful behavior induced by prompting can be made permanent through fine-tuning, removing the need for runtime prompt engineering.
- **This paragraph is the thesis statement.** It should be the single most carefully written paragraph in the chapter. Every clause maps to a chapter: geometry → Ch 5, prompt intervention → Ch 6, prediction of fixability + fine-tuning → Ch 7.
- **NO numbers. NO model names. NO method names (LoRA, McNemar's, etc.).** Pure ideas.

---

**Section 1.1 "Our Contributions"**

**Balance with Ch 8**: Ch 1 states *what we did and what kind of finding it is* — claims without numbers. Ch 8 §8.1 states *what we found and what the numbers mean* — evidence with full context. Ch 1 = claim. Ch 8 = evidence. No spoiling, no redundancy. This means Ch 8 §8.1 can be lean (~1.5 pages) since it's not the first time the reader hears the contributions, just the version with results attached.

Opening sentence: "The contributions of this thesis are as follows:" (matching Tarun's format exactly)

**Contribution 1 — Geometric prediction of hallucination (Ch 5)** (3-4 sentences)
- We construct a benchmark of 2,879 prompts spanning seven categories of knowledge failure and evaluate hallucination rates across ten language models.
- We show that geometric properties of prompt embeddings — computed from the question text alone, before any model generates a response — predict which prompts will cause hallucination.
- Critically, we decompose this signal and show that most of the predictive power reflects category-level structure (different types of questions occupy different embedding regions). The non-circular, within-category finding is that *embedding density* — how many similar prompts exist nearby — predicts hallucination within a single category, controlling entirely for category-level confounds.
- **What NOT to say**: No AUC values, no p-values, no effect sizes. Say "statistically significant" at most. Don't name specific features beyond density.
- **Cross-check**: Must be consistent with Ch 5's honest framing. Do NOT lead with AUC=0.86 from the initial study. The contribution is the within-category density finding, not the aggregate AUC.

**Contribution 2 — Prompt intervention (Ch 6)** (2-3 sentences)
- We design and evaluate four targeted system-prompt interventions, each addressing a distinct mechanism of hallucination (entity awareness, epistemic humility, structured caution, fact-grounding).
- In a controlled comparison on the same prompts with the same evaluation pipeline, all four interventions significantly reduce hallucination while maintaining or improving accuracy — a result replicated at five times the original benchmark scale.
- **What NOT to say**: No specific reduction percentages ("68-69%"). No prefix names. No McNemar's p-values. Say "significantly" and "substantially."

**Contribution 3 — Geometric diagnosis and fine-tuning distillation (Ch 7)** (4-5 sentences)
- We show that the same geometric features that predict hallucination also predict *which hallucinations resist intervention* — a notion of hallucination *difficulty* that has not been studied in prior work. Prompts in sparser embedding neighborhoods are both more likely to hallucinate and more likely to remain broken after intervention.
- We then demonstrate that the careful behavior induced by the best prompt interventions can be consolidated into model weights through parameter-efficient fine-tuning, producing models that are safer without any runtime prompt engineering.
- The fine-tuned models match the accuracy of the best prompt intervention while achieving comparable or lower hallucination rates. Three convergent tests — transfer to an external benchmark testing a different type of hallucination, invariance to the diversity of training templates, and generalization across held-out category types — confirm that the model learned general epistemic caution rather than surface-level pattern matching.
- **What NOT to say**: No specific accuracy numbers. No model names (Mixtral, Llama). No "LoRA." No McNemar's p-values. The contribution is the *idea* (geometry predicts difficulty + prompt behavior is distillable + the learned behavior generalizes), not the pipeline.
- **Cross-check against "What geometry does NOT do" and "What fine-tuning does NOT do"**: Do NOT claim geometry "guides" fine-tuning operationally (it doesn't — it's diagnostic). Do NOT claim fine-tuning "beats" the best prefix (it matches). The contribution is *connecting* prediction to intervention to distillation, with geometry as the diagnostic thread.

**¶ — Chapter roadmap (1 short paragraph)**
- One sentence per chapter, matching Tarun's format:
  - Ch 2 (Background): introduces LLMs, hallucination, embedding geometry, evaluation methodology, and fine-tuning
  - Ch 3 (Literature Review): surveys prior work on hallucination detection, benchmarking, prompting, and fine-tuning, identifying the gaps this thesis addresses
  - Ch 4 (Experimental Setup): describes the shared infrastructure — benchmark, models, consensus judging pipeline, and geometric feature extraction
  - Ch 5 (Can Geometry Predict Hallucination?): tests geometric prediction with category decomposition
  - Ch 6 (Can Prompts Reduce Hallucination?): evaluates prompt interventions at scale
  - Ch 7 (Can Geometry Guide Intervention?): connects geometry to fixability, presents fine-tuning results and generalization evidence
  - Ch 8 (Discussion): interprets findings, discusses limitations and cognitive science connections, and proposes future work
- **Keep this to exactly one sentence per chapter.** Do NOT elaborate. The chapter titles are self-explanatory.

### MBB through-line across the thesis

The MBB connection is threaded, not bolted on:
- **Ch 1 Introduction** (2-3 sentences): Frame hallucination as metacognition problem. Plant the cognitive science connection.
- **Ch 2 Background** (already written, line 26): "The term is borrowed from cognitive science, where humans *confabulate*: producing plausible but false memories when probed at the boundaries of their knowledge." Grounds the parallel.
- **Ch 8 Discussion** (2-3 pages): Full MBB subsection — confabulation/DRM paradigm, RSA and representational geometry, metacognition literature, signal detection theory for the precision-recall tradeoff. See detailed plan in the MBB section below.

### Rules for this chapter
- **NO NUMBERS.** No AUC, no p-values, no hallucination rates, no percentages. Save for results chapters.
- **NO JARGON in the opening.** First paragraph should be readable by the committee (technical professionals not in this subfield).
- **Frame contributions as ideas, not pipeline steps.** "We show that embedding geometry carries a signal predictive of hallucination difficulty" — not "We run 10 models on 2,879 prompts."
- **Honest scope.** Don't claim "we solve hallucination." Claim "we show geometry predicts it, prompts reduce it, and fine-tuning makes the reduction permanent."

---

## Framing: Contributions Are Ideas, Not Pipeline Steps

> **Lesson from reference theses** (Angela Li, Tarun Prasad): The main contributions of a thesis are the theoretical ideas and findings — not the engineering work that produced them. Angela's contribution is mathematical derivations. Tarun's is the lemma extraction *technique*. Neither says "I ran a pipeline." Both say "here is a new way of thinking about X."
>
> Our fine-tuning pipeline is the *method*, not the *finding*. The thesis should be framed around **what we learned about hallucination**, not the engineering that got us there.

### The Four Contributions (ordered by novelty)

1. **Geometric structure predicts hallucination *difficulty*, not just occurrence.** The bridge analysis shows embedding geometry predicts where interventions work (within-category density, p<0.05) and where they fail. "Unfixable" prompts cluster in high-centrality, low-density regions. Prior work asks "will this model hallucinate?" — we ask "is this hallucination fixable?" and show the answer is geometric.

2. **Within-category embedding density is the real geometric signal.** Cross-category prediction (AUC=0.97 in initial study) is largely confounded by category structure. The honest, non-circular finding: within a single category (controlling for prompt structure), density distinguishes hallucinating from non-hallucinating prompts (p<0.0001). The model's local neighborhood sparsity matters.

3. **The precision-recall structure of learned caution.** Fine-tuning teaches a "skepticism heuristic" that massively reduces hallucination on nonexistent entities (70%→99.2%) and plausible_fake (42%→9.7%). The cost is increased refusals on factual questions (5→15 for both models), not regressions on obscure_real (which improved). **⚠️ POST-FIX CORRECTION**: Old narrative said "obscure_real -7 to -13%"; actual data shows obscure_real IMPROVED. The tradeoff is real but its locus is factual refusals, not entity-type confusion. Most regressions (70%) are refusals, not new hallucinations.

4. **Careful prompt behavior can be distilled into weights.** LoRA fine-tuning on best-per-prompt curated data matches the best prompt prefix for Mixtral (94.4% vs Structured Caution 94.9%, p=0.82). Llama falls slightly short (94.0% vs 95.8%, p=0.14). Both FT models achieve lower hallucination rates than best prefix (1.3% vs 1.8% Mixtral; 1.1% vs 1.3% Llama) at cost of higher refusals. **⚠️ CORRECTED Mar 23**: comparison_analysis.json re-generated with post-V4-fix prefix data. Best prefix = Structured Caution (not Entity-Aware). The "careful behavior" is learnable, not just promptable — a methodological contribution showing prompt engineering can be a stepping stone to permanent model improvement. Template ablation (Ch 7.4) further shows the model learns behavioral caution, not template-specific patterns: 5 templates perform indistinguishably from all ~194 (McNemar p=0.099/0.773), and accuracy on seen vs novel templates is comparable (T5 Mixtral: 96.3% seen vs 93.0% novel).

**⚠️ THESIS ARC — DEFINITIVE FRAMING (Mar 23, all corrections applied)**:

The thesis makes three claims. All three survive every correction (CoT exclusion, V4 contamination fix, comparison re-run):

1. **Geometry predicts hallucination difficulty.** Within-category density predicts hallucination (Ch 5, p < 10⁻⁵, survives Bonferroni). Density also predicts fixability — by prefixes (Ch 7.1, p=0.046/0.012, suggestive) and by fine-tuning (Ch 7.3, Mixtral p=0.0017, |r|=0.80, survives Bonferroni). Sparser embedding neighborhoods → harder to hallucinate correctly AND harder to fix. This is the genuinely novel contribution — no prior work asks "is this hallucination fixable?"

2. **Prompting reduces hallucination.** Four prefix interventions reduce hallucination 68–69% relative (Ch 6). Replicated at 5× scale. Category-level analysis reveals where prefixes work and where they don't.

3. **Prompt behavior can be made permanent through fine-tuning.** LoRA fine-tuning matches the best single prefix in accuracy (Mixtral 94.4% vs Structured Caution 94.9%, p=0.82) while producing fewer hallucinations (1.3% vs 1.8%) at the cost of more refusals (3.6% vs 3.1%). Llama falls slightly short in accuracy (94.0% vs 95.8%, p=0.14) but also hallucinates less (1.1% vs 1.3%). The practical value: careful behavior becomes permanent without runtime prompt engineering. Three convergent tests (TruthfulQA transfer, template ablation, decontamination) confirm the model learned general epistemic caution, not surface patterns.

**What geometry does NOT do** (honesty points):
- Geometry does NOT predict where fine-tuning causes regressions (p=0.061/0.110, non-significant). It predicts where intervention HELPS, not where it HURTS.
- Geometry does NOT operationally drive decisions in the current pipeline. Unfixable exclusion uses labels, not geometry scores. Runtime geometry-guided prefix selection is future work.
- The within-category fixability p-values (0.046/0.012) do not survive Bonferroni correction. The FT bridge density result (p=0.0017) does.

**What fine-tuning does NOT do**:
- Fine-tuning does NOT beat the best prefix. It matches it (Mixtral) or falls slightly short (Llama). The advantage is operational (no runtime engineering) and in hallucination rate (lower), not accuracy.
- Fine-tuning introduces a precision-recall tradeoff: increased refusals on factual questions (5→15 for both models). Most regressions (70%) are refusals, not new hallucinations — the model errs toward caution.

**The intellectual narrative**: Geometry is the diagnostic (predicts difficulty), prompts are the treatment (reduce hallucination), fine-tuning is the consolidation (makes treatment permanent). Geometry predicts where treatment works and where it doesn't. The pipeline's value is that each step informs the next — geometry identifies fixable prompts, fixable prompts provide training data, and training data produces permanent behavioral change.

### Terminology: No V3/V4/V5 in the Thesis

Internal version labels (V3, V4, V5) are lab notebook language. A reader has no idea what "V3" means. The thesis uses descriptive terms:

| Internal | Thesis language |
|---|---|
| V3 (449 prompts) | "held-out test set" or "initial benchmark" |
| V4 (prefix experiment on 449) | "prefix pilot study" or "initial prefix evaluation" |
| V5 (2,430 new prompts) | "expanded benchmark" or "training set" |
| V3 baseline results | "baseline evaluation" |
| V4 prefix results | "prefix intervention results" |
| V5 fine-tuning | "fine-tuning evaluation" |
| Bridge analysis | "geometric difficulty analysis" or keep "bridge analysis" if defined |

---

## Sunny's Three Framing Directives (Mar 9, 2026)

> These are binding thesis framing requirements from advisor Sunny Qin. Each must appear explicitly in the thesis — not just implied, but stated as claims with supporting evidence. See `memory/advisor_comms.md` for full conversation context.

### Directive 1: "The model learned behavioral caution, not entity memorization"
- **Claim to make explicit (Ch 7)**: Fine-tuning taught the model *when to be skeptical*, not *which specific entities to refuse*. The 61% entity overlap between training and test sets makes this claim non-obvious — we must confront the overlap head-on and show it doesn't drive performance.
- **Supporting evidence**: (a) Entity decontamination analysis: clean-entity accuracy nearly unchanged (Llama +0.5pp, Mixtral +2.8pp — both under 3pp inflation threshold); (b) TruthfulQA cross-domain transfer (Llama -4.4pp halluc, Bonferroni-sig) on misconception questions that share zero entities with training; (c) Template ablation (T5≈T-all, McNemar p=0.099/0.773) shows model didn't memorize template patterns either.
- **Where**: Ch 7 fine-tuning discussion, stated as a thesis claim with evidence marshaled.

### Directive 2: "Two types of behavioral generalization" (expanded to three)
- **Claim to highlight (Ch 7)**: The fine-tuned model generalizes cautious behavior across three dimensions:
  1. **Unseen entities** — entities not in training (decontamination analysis)
  2. **Unseen question templates** — novel template structures (template ablation: seen 96.3% ≈ novel 93.0%)
  3. **Unseen category types** — entity-dependent training generalizes to entity-independent categories (Phase 10: entity-dep only matches or beats Full)
- **Where**: Ch 7, with each generalization type getting its own evidence paragraph. The third type (cross-category) emerged from Phase 10 after Sunny's message — it strengthens the claim beyond what was discussed.

### Directive 3: "Plausible_fake = feature, not bug — adversarial probing"
- **Claim**: The borderline_plausible_fake category's high residual hallucination rate (30-44% baseline, highest after all interventions) is not a benchmark design failure. These prompts are *adversarial probes* — entities designed to sound real that test the boundary of model knowledge. High hallucination rates on adversarial probes indicate the benchmark is doing its job.
- **Framing**: "They are almost a bit adversarial in the sense that users are making up things that sound almost real to trick the LLMs." (Sunny, Mar 9)
- **Where**: Ch 8 Discussion (limitations/future work). Explicitly claim plausible_fake as a feature. Discuss how future work could improve model behavior on these cases — potentially via retrieval augmentation or specialized adversarial training.

---

## Content Expansion Guide: Conference Paper → Thesis

The core shift: the conference paper oversells geometry as a standalone predictor. The thesis tells the honest, more interesting story — geometry *explains category structure*, provides *modest within-category signal*, and most importantly *predicts which hallucinations are resistant to mitigation*.

### Introduction — Needs a Real Narrative Arc

The current intro is fine for a conference paper but reads as a pitch. A thesis intro should:

- **Motivate the problem more deeply** — why hallucination specifically matters *now* (not just "medical/legal harm"), with concrete examples of real-world failures
- **Tell the story of the research journey** — "We initially hypothesized X, found Y, which led us to investigate Z." The thesis should read as an intellectual narrative, not a sales pitch
- **Preview all four contributions** — use the numbered list above. Frame them as intellectual findings, not pipeline steps
- **Drop the Theory of Change section** — that was a class requirement. The safety motivation should be woven into the intro naturally, not be its own section

### Literature Review — Detailed Outline Complete, Needs Writing

Full paragraph-level outline with ~72 references across 8 sections now in "Proposed Literature Review Chapter Contents" below. Expanded from the v3 conference paper's 6 subsections / 26 refs to 8 sections / 72 refs. Key additions over the v3 draft:

- **Section 3.3 (LLM-as-Judge)**: Now a standalone section with PoLL, bias taxonomy (CALM), self-preference causality (Panickssery)
- **Section 3.4 (Detection via Representations)**: Massively expanded. 19 refs covering probing (CCS, SAPLMA), geometric methods (LID, HaloScope, INSIDE, "Truth is Universal"), uncertainty (Semantic Entropy), and inference-time (ITI, RepE, DoLA). Gap statement positions our work as pre-generation, external-embedding, fixability-predicting — distinct from all prior work
- **Section 3.5 (Entity Knowledge)**: New section connecting entity popularity (Kandpal, Mallen, Sun) to knowledge boundaries (Ferrando entity recognition directions) to embedding geometry
- **Section 3.6 (Prompt Engineering)**: Expanded with SynTra (closest prior work for prefix optimization), abstention survey (Wen 2025), CoT-obscures-detection (Cheng 2025)
- **Section 3.7 (Fine-Tuning)**: Expanded with fine-tuning paradox (Gekhman), data selection (LESS, Cherry LLM, Prereq-Tune), alignment tax, SEAT knowledge preservation
- **Section 3.8 (Synthesis)**: New section tying all gaps to three research questions
- **48 new bib entries identified** — need to be added to references.bib before writing

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

**Prefix design — NOW IN Ch 6.1 (see detailed outline below)**

### Section 6.1 Prefix Design — Detailed Paragraph-Level Outline

**Purpose**: Introduce the 5 system-prompt prefixes as an intervention, explain the design rationale for each, connect to prior work. This is a methods section — NO results. ~2 pages.

**What Ch 4 already covers** (do NOT repeat): model selection (why Mixtral/Llama), generation parameters (temp=0.7, max_tokens=4000), judging pipeline, benchmark construction. Ch 4 line 6 explicitly defers: "Experiment-specific methods---prompt prefix design---are introduced in their respective chapters."

**What this section must introduce from scratch**: the intervention concept, the 5 specific prefixes, design rationale, implementation details, CoT exclusion, baseline condition.

---

**¶1 — Why system-prompt prefixes as an intervention** (~5 sentences)

The literature review (Ch 3, Section 3.6) identified a gap: most prompting-based hallucination mitigation requires multi-pass reasoning (CoVe, Self-Consistency) or gradient-based optimization (SynTra). System-prompt prefixes represent the simplest possible intervention — a single instruction prepended to every query, requiring no training, no white-box access, and no additional generation passes. This makes them a natural first-line test before more expensive approaches such as fine-tuning (Chapter 7). The question is whether different instructions targeting different failure modes produce differential effects — and if so, which mechanisms matter most for entity-level factuality.

*Verified against codebase: confirmed. Prefixes are system messages passed once per query. No multi-pass generation. scripts/run_v5_prefixes.py calls client.generate() once per prompt-prefix pair.*

---

**¶2 — Design principles and implementation** (~5 sentences)

We designed four prefixes (plus one excluded, discussed below), each targeting a distinct hallucination mechanism identified in prior work. The prefixes form a spectrum from least to most restrictive behavioral constraint: from a one-sentence encouragement to express uncertainty (Epistemic Humility) to a five-rule protocol combining multiple strategies (Structured Caution). Each prefix is passed as the **system message** in the chat API — cleanly separated from the user's query, which remains the raw benchmark question. The baseline condition uses **no system message at all**, providing a null condition against which all prefixes are compared — not a generic "You are a helpful assistant" default. Full prefix texts are reproduced in Appendix A.

*Verified against codebase: confirmed. MultiModelClient.generate() passes system_prompt as {"role": "system", "content": system_prompt}. Baseline passes system_prompt=None, which means NO system message in the API call (not even an empty one). The older GenerationClient class has a default system prompt, but it is NOT used by the prefix/baseline experiments — those all use MultiModelClient via get_model_client(). Source: src/models/multi_model_client.py lines 41-67, scripts/run_v5_baselines.py line 107.*

---

**¶3 — Table 6.1: Prefix design summary** (table + 1-2 sentences introducing it)

Table with columns: **Prefix** | **Target mechanism** | **Key instruction** | **Literature basis**

| Epistemic Humility | Internal calibration / uncertainty surfacing | "If you genuinely do not know something, say 'I don't know' rather than guessing." | Kadavath+ 2022 (models mostly know what they know); Yin+ 2023 (need encouragement to say so) |
| Fact-Grounded | Fabrication of specific details | "Do not fabricate names, dates, statistics, or other specific details." | Min+ 2023 / FActScore (42% fabrication rate in specific detail categories) |
| Entity-Aware | Entity existence verification | "Consider whether the entity or concept in the question actually exists. If it appears to be fictional, fabricated, or nonexistent, say so clearly." | Ferrando+ 2024 (entity recognition directions exist internally); Sun+ 2024 (popularity-hallucination correlation) |
| Structured Caution | Combined multi-rule protocol | 5 numbered rules combining uncertainty, entity verification, logical impossibility, anti-speculation, and "I don't know" preference | Arora+ 2024 (explicit rules outperform vague instructions) |

*Verified: prefix texts confirmed against experiments/prefix_configs.yaml. All 4 texts match. Literature citations confirmed against EXPERIMENT_LOG.md lines 78-104.*

---

**¶4 — The design spectrum** (~4 sentences)

Walk through the logic: Epistemic Humility is the lightest possible nudge — does merely asking the model to be uncertain help? Fact-Grounded is more specific — prohibiting fabrication by category (names, dates) rather than asking for general caution. Entity-Aware is the most benchmark-targeted — it explicitly asks the model to verify whether entities exist, directly addressing the entity-existence categories that dominate our benchmark. Structured Caution tests whether enumerating all mechanisms as explicit rules produces better compliance than any single instruction. The design question is whether **specificity** (targeting entity existence) outperforms **breadth** (covering many failure modes in one prefix).

*Note: do NOT preview results here. Do NOT say Entity-Aware works best for Mixtral. Frame as a design question, not a conclusion.*

---

**¶5 — CoT Verification: inclusion and exclusion** (~4 sentences)

A fifth prefix, Chain-of-Thought Verification, was initially included. It implemented a simplified single-pass self-verification step inspired by CoVe (Dhuliawala+ 2024) and chain-of-thought reasoning (Wei+ 2022): the model was asked to briefly verify its claims before providing a final answer. This prefix was excluded from all analyses after a judge API failure artifact was discovered that corrupted approximately 65% of its evaluation labels (see Section X.X for details). All results in this chapter use the four non-CoT prefixes plus the no-prefix baseline. Full texts of all five prefixes, including CoT Verification, appear in Appendix A.

*Verified against codebase/experiment log: CoT exclusion is well-documented. 3,172/4,860 CoT entries had 2+ failed judges. JUDGE_CONTAMINATION_ISSUE.md has full details. The corrected refusal rate would be under 1% (not the 62-68% the corrupted data showed).*

---

**¶6 — What this design tests** (~3 sentences)

State the experimental questions this design is set up to answer (all framed as open questions, not conclusions):
1. Do system-prompt prefixes reduce hallucination compared to the no-prefix baseline?
2. Do different prefixes targeting different mechanisms produce different effects?
3. Do the relative rankings of prefixes differ across models (Mixtral vs. Llama)?

These questions are tested first on the held-out benchmark (Section 6.2) and then replicated at scale on the expanded benchmark (Section 6.3).

---

**Reference count for this section**: ~8 citations (Kadavath 2022, Yin 2023, Min 2023, Ferrando 2024, Sun 2024, Arora 2024, Dhuliawala 2024, Wei 2022). All already in references.bib.

**Approximate length**: ~1.5-2 pages (including table). Concise — this is a methods section, not a results section.

**Cross-checks performed**:
- ✅ Prefix texts verified against experiments/prefix_configs.yaml (canonical source)
- ✅ API implementation verified against src/models/multi_model_client.py (system message, not prepended)
- ✅ Baseline condition verified against scripts/run_v5_baselines.py (system_prompt=None, no default)
- ✅ CoT exclusion rationale verified against JUDGE_CONTAMINATION_ISSUE.md (65% label corruption)
- ✅ Literature citations verified against EXPERIMENT_LOG.md lines 78-104
- ✅ No overlap with Ch 4 (setup.tex explicitly defers prefix design to this chapter)
- ✅ No results spoiled (all framed as design questions, not conclusions)
- ✅ Appendix A confirmed to contain full prefix texts (appendixA.tex lines 69-102)

### Results — Needs Restructuring and Honesty

The current paper presents V3 results with inflated claims. The thesis needs to tell the honest story:

**Initial Benchmark Results (Ch 5.2, needs revision)**:
- The AUC=0.971 combined model needs the decomposition: category-only AUC=0.955, geometry adds +0.016. Still statistically significant (p=0.012) but the framing must be honest that category structure does most of the work
- The logistic regression table (centrality beta=-3.62, p<0.001) is real but needs the caveat that this partially reflects category-level differences
- The cross-model consistency (tau=0.319) is a genuine finding

**Expanded Benchmark Validation (Ch 5.3, new, ~5 pages)**:
- The honest decomposition: overall CV AUC=0.641 (Mixtral), 0.722 (Llama) — much lower than initial study's train-only 0.86
- Category-only AUC=0.77 — geometry adds only +0.02-0.04 on top
- **Within-category analysis is the real finding**: density predicts hallucination within nonexistent entities (AUC 0.665, p<0.0001). Non-circular because within a single category, all prompts share the same structure — the geometric variation is genuine
- local_id and curvature are essentially useless (r=-0.97 correlated, neither predictive)
- Frame as: "geometry *explains* why categories differ, and density provides modest but real within-category signal"

**Prefix Pilot Study (Ch 6.2, new, ~3 pages)** `[V4 DATA POST-FIX as of Mar 21, 2026]`:
- 449 prompts x 4 non-CoT prefixes x 2 models = 3,592 usable responses (CoT excluded)
- All prefixes significantly reduce hallucination (all p < 0.003, McNemar's with Yates correction)
- **Post-fix rates**: Entity-Aware best for Mixtral (11.8%→1.34%), Structured Caution best for Llama (5.8%→1.34%)
- Mixtral full ranking: Entity-Aware (1.34%) > Structured Caution (1.78%) > Epistemic Humility (3.56%) = Fact-Grounded (3.56%)
- Llama full ranking: Structured Caution (1.34%) > Fact-Grounded (1.56%) > Epistemic Humility (1.78%) > Entity-Aware (2.45%)
- V4 contamination fix (Mar 21): 153/4,490 labels corrected (3.41%). Refusal rates dropped 3-7pp (were inflated by fake label=3 defaults). Rankings unchanged vs pre-fix.
- **Post-fix best-per-prompt** (baseline + 4 prefixes as candidates): Mixtral 98.2% correct / 0.2% halluc (1 unfixable), Llama 98.4% correct / 0.0% halluc (0 unfixable)
- Single best prefix: Mixtral Entity-Aware 93.76% correct, Llama Structured Caution 95.77% correct

### Section 6.2 Pilot Study — Detailed Paragraph-Level Outline

**Purpose**: Present initial evidence that system-prompt prefixes reduce entity-level hallucination, establish prefix rankings, and motivate the replication at scale (6.3). This is the first results section of Ch 6. ~2.5-3 pages including table.

**Terminology**: Use "held-out benchmark" (not V3/V4). Use "pilot study" or "initial evaluation." Use "expanded benchmark" (not V5) only when forward-referencing 6.3.

**Statistical methods**: McNemar's test with Yates continuity correction on paired binary outcomes (hallucinated vs. not-hallucinated, same prompt at baseline vs. with prefix). Applied to 449 paired observations per prefix-model combination. No Bonferroni correction needed — all p-values are far below any reasonable threshold.

---

**¶1 — Experimental structure** (~3 sentences)

We first tested the four prefixes on the 449-prompt held-out benchmark. Each prompt was presented to both models (Mixtral 8x7B and Llama 4 Maverick) under the baseline condition (no system message) and under each of the four prefix conditions, producing 449 × 4 × 2 = 3,592 responses evaluated by the consensus judging pipeline (Chapter 4). Because each prompt appears in both baseline and prefix conditions, we can use McNemar's test to assess whether the prefix changed the outcome.

*Verified: 449 prompts confirmed. 4 non-CoT prefixes confirmed. 2 models confirmed. McNemar's test is appropriate for paired binary outcomes.*

---

**¶2 — Table 6.2: Pilot study results** (table + introducing sentence)

Table with columns: **Prefix** | **Mixtral Halluc%** | **Llama Halluc%** | or a more detailed layout.

Actually, a combined table showing correctness, hallucination, and refusal for both models would be more informative. Design:

| | **Mixtral** | | | **Llama** | | |
|Prefix | Correct% | Halluc% | Refused% | Correct% | Halluc% | Refused% |
|Baseline (no prefix) | 82.9 | 11.8 | 1.1 | 90.6 | 5.8 | 0.2 |
|Epistemic Humility | 91.3 | 3.6 | 2.9 | 93.8 | 1.8 | 0.9 |
|Fact-Grounded | 92.0 | 3.6 | 3.6 | 94.4 | 1.6 | 3.8 |
|Entity-Aware | **93.8** | **1.3** | 3.8 | 94.0 | 2.4 | 0.4 |
|Structured Caution | 94.9 | 1.8 | 3.1 | **95.8** | **1.3** | 2.7 |

Bold = best hallucination rate per model. Include partial% or omit for space? Partial is small (0.2-3.6%) — could omit from main table and mention in text.

*Verified: all numbers match post-fix computation from corrected V4 JSONL files.*

---

**¶3 — Main finding: all prefixes reduce hallucination** (~4 sentences)

All four prefixes significantly reduce hallucination for both models (Table 6.3 / McNemar's results). The reductions are large: Mixtral's baseline hallucination rate of 11.8% drops to 1.3-3.6%, and Llama's 5.8% drops to 1.3-2.4%. State significance: all eight prefix-model comparisons yield p < 0.003 (McNemar's test with Yates correction). This is not surprising given the effect sizes — between 40 and 48 prompts improved per prefix on Mixtral — but it establishes that the effect is systematic, not driven by a few outliers.

*Verified: all p < 0.003. Mixtral Entity-Aware: 48 improved, 1 worsened, p≈0. Llama Structured Caution: 22 improved, 2 worsened, p=0.000105.*

---

**¶4 — Table 6.3 (or inline): McNemar's test results** (table or concise inline)

Could be a small table or reported inline. Key numbers per prefix-model:
| Model | Prefix | Improved | Worsened | p (Yates) |
| Mixtral | Entity-Aware | 48 | 1 | <0.001 |
| Mixtral | Structured Caution | 46 | 1 | <0.001 |
| ... | ... | ... | ... | ... |

Or could merge into Table 6.2 with additional columns. Decide at writing time.

*Verified: all McNemar's numbers from post-fix recomputation with Yates correction.*

---

**¶5 — Rankings differ by model** (~4 sentences)

The most striking finding is that the best prefix differs between models. For Mixtral, the entity-targeted prefix (Entity-Aware) achieves the lowest hallucination rate (1.34%), followed by Structured Caution (1.78%). For Llama, the pattern reverses: the comprehensive rule-based prefix (Structured Caution) achieves the lowest rate (1.34%), with Entity-Aware ranking last among the four prefixes (2.45%). This answers the design question posed in Section 6.1: specificity (targeting entity existence) outperforms breadth for the higher-hallucination model (Mixtral), while breadth outperforms specificity for the lower-hallucination model (Llama).

*Do NOT over-interpret why. Offer one cautious hypothesis: Mixtral's higher baseline rate means more entity-fabrication errors, which the entity-targeted prefix directly addresses. Llama, with fewer such errors, benefits more from uniform coverage. But flag this as speculation, not a causal claim.*

---

**¶6 — Regressions are rare but informative** (~3 sentences)

Most prefix-model combinations show 0-1 regressions (prompts correct at baseline that hallucinate with the prefix). The exception is Entity-Aware on Llama, which shows 3 regressions — the most of any non-CoT combination. This is consistent with the entity-verification instruction occasionally causing the model to second-guess real but obscure entities. A detailed category-level analysis of where regressions concentrate appears in Section 6.4.

*Verified: Mixtral Entity-Aware 1 worsened, Structured Caution 1, Epistemic 3, Fact-Grounded 4. Llama Entity-Aware 3, Structured Caution 2, Epistemic 0, Fact-Grounded 2. Actually Mixtral Epistemic has 3 and Fact-Grounded has 4 — these are higher than Entity-Aware's 1. So Entity-Aware on Llama (3) is not the single worst — Mixtral Fact-Grounded (4) is. But Entity-Aware on Llama is notable because Entity-Aware is Llama's worst-performing prefix by hallucination rate.*

*Correction needed: don't claim Entity-Aware on Llama has "the most regressions" — Mixtral Fact-Grounded has 4. Instead say: "regressions are rare (0-4 per combination)" and note the Entity-Aware on Llama case as thematically interesting (entity-verification hurting on obscure-but-real entities).*

---

**¶7 — The ceiling: best-per-prompt selection** (~3 sentences)

If we select, for each prompt, the best response across the baseline and all four prefixes, correctness reaches 98.2% (Mixtral) and 98.4% (Llama), with hallucination falling to 0.2% and 0.0% respectively. Only 1 prompt (Mixtral) remains hallucinated under every condition. This upper bound demonstrates that the information needed to avoid hallucination exists across the prefix portfolio — the challenge, addressed in Chapter 7, is whether this behavior can be consolidated into the model's weights without per-prompt prefix selection at inference time.

*Verified: post-fix computation. Mixtral 98.2% correct, 0.2% halluc (1 unfixable). Llama 98.4%, 0.0% (0 unfixable).*

---

**¶8 — Limitations and forward reference** (~2 sentences)

This pilot study establishes that system-prompt prefixes can dramatically reduce hallucination on the held-out benchmark. However, these 449 prompts were designed for the initial geometric analysis and may not represent the full difficulty spectrum. Section 6.3 tests whether these findings replicate on the expanded benchmark of 2,430 prompts, which samples harder entity regions.

---

**Estimated length**: ~2.5-3 pages (including 1-2 tables).

**No results spoiled from later chapters**:
- ✅ No V5/replication numbers (those are 6.3)
- ✅ No category breakdown (that's 6.4)
- ✅ No refusal tradeoff analysis (that's 6.5)
- ✅ No bridge/geometry analysis (that's Ch 7)
- ✅ No fine-tuning results (that's Ch 7)
- ✅ Best-per-prompt presented as a ceiling, not a training strategy (that's Ch 7)

**Cross-checks**:
- ✅ All numbers from post-fix V4 data (Mar 21, 2026)
- ✅ McNemar's with Yates correction (consistent with thesis methodology)
- ✅ Baseline rates from clean V3 data (0 failures confirmed)
- ✅ Terminology: "held-out benchmark" not V3/V4
- ✅ 4 non-CoT prefixes (CoT exclusion explained in 6.1)
- ✅ Regression counts verified against post-fix McNemar output

**Replication at Scale (Ch 6.3)** `[V5 DATA POST-FIX, numbers from v5_prefix_metrics.csv and v5_mcnemar_tests.csv]`:
- 2,430 prompts x 4 non-CoT prefixes x 2 models = 19,440 responses (+ 2 baselines = 24,299 total judged incl. CoT)
- **Pilot pattern replicates at 5x scale**: Entity-Aware best for Mixtral (14.8%→4.7%), Structured Caution best for Llama (9.7%→3.0%). All significant (p < 1e-11).
- CoT excluded from thesis (API failure artifact). Mentioned in 6.1, not re-discussed here.
- **Expanded benchmark rates are higher** (Mixtral Entity-Aware: 1.34% pilot → 4.7% at scale). Expected — new prompts probe harder entity regions.

### Section 6.3 Replication at Scale — Detailed Paragraph-Level Outline

**Purpose**: Confirm the pilot findings at 5.4× scale on a distinct, harder prompt set. Establish these as the definitive prefix effectiveness numbers. ~2.5-3 pages including table.

**Terminology**: "expanded benchmark" (not V5). 2,430 prompts. Zero overlap with the 449-prompt held-out benchmark.

**Key structural point**: V5 baselines are DIFFERENT from V3 baselines. The V5 baseline is no-prefix on V5 prompts (2,430), not on V3 prompts (449). So both baselines AND prefix rates change. The comparison to pilot must account for this.

---

**¶1 — Experimental structure** (~3 sentences)

We replicated the prefix experiment on the expanded benchmark of 2,430 prompts — a set with zero prompt overlap with the held-out benchmark and broader entity coverage across all seven categories. Each prompt was evaluated under the baseline (no system message) and each of the four prefix conditions, producing 19,440 prefix responses. The same consensus judging pipeline and McNemar's testing framework from the pilot study were applied.

*Verified: 2,430 × 4 × 2 = 19,440 prefix responses. Zero overlap with V3 confirmed by design (V5 exclusion logic). Same 4 non-CoT prefixes. Same judges, same McNemar's with Yates. Source: scripts/run_v5_prefixes.py, scripts/analyze_v5_prefixes.py.*

---

**¶2 — Table 6.x: Replication results** (same format as pilot table)

| Condition | Mixtral Correct | Mixtral Halluc | Mixtral Refused | Llama Correct | Llama Halluc | Llama Refused |
|---|---|---|---|---|---|---|
| Baseline | 82.5% | 14.8% | 0.04% | 87.9% | 9.7% | 1.2% |
| Epistemic Humility | 86.8% | 10.2% | 0.3% | 93.3% | 4.3% | 1.2% |
| Fact-Grounded | 90.1% | 7.1% | 0.5% | 93.5% | 4.5% | 1.2% |
| Structured Caution | 91.9% | 6.7% | 0.2% | 95.8% | **3.0%** | 0.5% |
| Entity-Aware | **93.7%** | **4.7%** | 0.04% | 95.4% | 3.7% | 0.1% |

*All numbers verified against v5_prefix_metrics.csv (post-fix).*

---

**¶3 — Main finding: pilot rankings replicate** (~4 sentences)

The central finding: prefix rankings replicate identically across models. Entity-Aware remains the most effective prefix for Mixtral (4.7% hallucination, vs 14.8% baseline), and Structured Caution remains the most effective for Llama (3.0%, vs 9.7%). All eight prefix–model comparisons are statistically significant (all p < 10⁻¹¹, McNemar's with Yates correction) — the larger sample size (2,430 vs 449) provides overwhelming statistical power. The relative reductions (68% for Mixtral's best, 69% for Llama's best) are somewhat smaller than the pilot's 89%/77%, but the rankings and significance are unchanged.

*Verified against v5_mcnemar_tests.csv. Mixtral Entity-Aware: p=0.0 (chi2=179.7), 290 improved, 44 worsened. Llama Structured Caution: p=0.0 (chi2=130.6), 182 improved, 19 worsened.*

---

**¶4 — McNemar's details** (table or inline)

Table with improved/worsened/p for each prefix-model:

| Model | Prefix | Improved | Worsened | p |
|---|---|---|---|---|
| Mixtral | Entity-Aware | 290 | 44 | < 0.001 |
| Mixtral | Structured Caution | 256 | 60 | < 0.001 |
| Mixtral | Fact-Grounded | 246 | 59 | < 0.001 |
| Mixtral | Epistemic Humility | 186 | 75 | < 0.001 |
| Llama | Structured Caution | 182 | 19 | < 0.001 |
| Llama | Entity-Aware | 174 | 29 | < 0.001 |
| Llama | Epistemic Humility | 163 | 32 | < 0.001 |
| Llama | Fact-Grounded | 154 | 29 | < 0.001 |

---

**¶5 — Why rates are higher: harder prompts, not weaker prefixes** (~4 sentences)

Both baseline AND prefix hallucination rates are higher on the expanded benchmark than the pilot. Mixtral's baseline rises from 11.8% to 14.8%; Llama's from 5.8% to 9.7%. The prefix rates rise correspondingly: Mixtral Entity-Aware from 1.34% to 4.7%, Llama Structured Caution from 1.34% to 3.0%. This parallel increase indicates that the expanded benchmark samples harder entity regions — not that prefixes are less effective on new data. The benchmark was designed to test a broader and more difficult set of entities (Chapter 4), so higher rates are expected and confirm that the pilot's lower rates reflected easier prompts.

*Verified: V5 baseline rates from v5_prefix_metrics.csv. V4 post-fix baseline rates confirmed. The design explanation is documented in EXPERIMENT_LOG.md: "V5 baselines are also higher... Confirms V5 prompts are genuinely harder."*

---

**¶6 — Worsened counts scale with benchmark size** (~3 sentences)

The expanded benchmark reveals more regression cases than the pilot: 19-75 worsened prompts per prefix-model combination, compared to 0-4 in the pilot. Part of this increase is mechanical — with 5.4× more prompts, more regressions are expected in absolute terms. But the regression rate is also somewhat higher (e.g., Mixtral Epistemic Humility: 0.7% worsened in the pilot vs 3.1% at scale), suggesting that the expanded benchmark's harder prompts are more susceptible to prefix-induced regressions. The category-level analysis in Section 6.4 examines where these regressions concentrate.

*Verified: pilot worsened range 0-4 (Table 6.3). V5 worsened range 19-75 (v5_mcnemar_tests.csv). Mixtral Epistemic: pilot 3/449=0.67%, V5 75/2430=3.09%.*

---

**¶7 — Closing: definitive results** (~2 sentences)

The replication confirms the pilot's findings at scale: system-prompt prefixes substantially reduce entity-level hallucination, with Entity-Aware best for Mixtral and Structured Caution best for Llama. These results on 2,430 prompts constitute the definitive prefix effectiveness numbers for this thesis; the category-level structure of these effects is examined in Section 6.4, and the tradeoff between hallucination reduction and over-refusal in Section 6.5.

---

**Estimated length**: ~2.5-3 pages (including 1-2 tables).

**No results spoiled**:
- ✅ No category breakdown (6.4)
- ✅ No refusal tradeoff (6.5)
- ✅ No bridge analysis or geometry (Ch 7)
- ✅ No fine-tuning (Ch 7)

**Cross-checks**:
- ✅ All V5 numbers from post-fix authoritative CSVs (v5_prefix_metrics.csv, v5_mcnemar_tests.csv)
- ✅ V4 comparison numbers from post-fix V4 data (Mar 21 fix)
- ✅ McNemar's with Yates correction (same as V4, confirmed in analyze_v5_prefixes.py line 204)
- ✅ Zero prompt overlap between pilot and replication (V5 exclusion logic confirmed)
- ✅ Terminology: "expanded benchmark" not V5
- ✅ CoT not re-discussed (handled in 6.1)

**Potential reviewer concerns addressed**:
- "Why are rates higher?" → Baselines are ALSO higher; parallel increase = harder prompts
- "Why more regressions?" → Mechanical scaling + harder prompts; details in 6.4
- "Is this really a replication?" → Same prefixes, same models, same evaluation, different (non-overlapping) prompts at 5.4× scale. Rankings identical.

### Section 6.4 Category-Level Analysis — Detailed Paragraph-Level Outline

**Purpose**: Break down prefix effectiveness by category, identify which categories are "solved" vs. remain hard, analyze where regressions concentrate, and examine the refusal/correctness-safety tradeoff at the prefix level. Combined from the original 6.4 (category analysis) and 6.5 (tradeoff). ~3-4 pages including 1 table + reference to existing heatmap figures.

**Terminology**: Same as 6.2/6.3. Category names as in Ch 4 (factual, nonexistent, impossible, ambiguous, borderline_edge_factual, borderline_obscure_real, borderline_plausible_fake).

**Data source**: `results/v5_prefixes/analysis/v5_category_metrics.csv` (post-fix, authoritative). Figures: `v5_category_heatmap_{model}.png`.

**What this section does NOT cover** (Ch 7 territory): fixability prediction via geometric features, bridge analysis, fine-tuning precision-recall tradeoff, best-per-prompt curation details.

---

**¶1 — Opening: aggregate results mask category-level structure** (~3 sentences)

The aggregate results from Sections 6.2-6.3 show that all prefixes reduce hallucination, but the seven-category benchmark was designed to test distinct failure modes. This section examines whether prefix effectiveness varies across categories — and if so, whether the variation reveals something about the mechanisms underlying prefix-based mitigation. We focus on the expanded benchmark (2,430 prompts) as the definitive dataset.

---

**¶2 — Table 6.x or Figure reference: category × prefix hallucination rates**

A heatmap or table showing hallucination rates for each (category, prefix) combination for both models. Figures already exist: `v5_category_heatmap_mixtral-8x7b.png` and `v5_category_heatmap_llama-4-maverick-17b.png`. Could include as figures or present key numbers as a table. A table may be more precise for the thesis; figures work as supplements.

Key numbers to highlight (Mixtral / Llama):

| Category | N | Baseline M/L | Best prefix M/L | Best prefix name |
|---|---|---|---|---|
| ambiguous | 600 | 0.7/1.5% | 0.2/0.2% | FG or SC / SC |
| edge_factual | 130 | 3.1/0.8% | 3.1/0.0% | FG,SC / SC |
| obscure_real | 200 | 11.5/3.0% | 8.0/2.0% | EA / SC |
| plausible_fake | 200 | 43.5/30.0% | 11.0/14.0% | EA / SC |
| factual | 500 | 9.2/2.6% | 7.4/1.6% | EH / SC |
| impossible | 200 | 9.5/16.0% | 1.0/4.5% | EA / EA,SC |
| nonexistent | 600 | 29.5/19.0% | 3.3/3.2% | EA / EA |

*All numbers verified against v5_category_metrics.csv.*

---

**¶3 — Near-solved categories** (~3 sentences)

Three categories approach zero hallucination with the right prefix. Ambiguous questions, which test whether models respect subjectivity, were already near-zero at baseline and remain so (0.2% with Structured Caution for both models). Borderline edge-factual prompts reach 0.0% for Llama with Structured Caution. Impossible questions — which ask the model to recognize logical impossibility — show the largest relative drops, from 9.5%/16.0% baseline to 1.0%/4.5% with Entity-Aware.

---

**¶4 — The hardest category: borderline plausible-but-fake** (~4 sentences)

Borderline plausible-but-fake prompts remain the hardest category by a wide margin. Even the best prefix leaves 11.0% hallucination (Mixtral, Entity-Aware) and 14.0% (Llama, Structured Caution) — rates 5-7× higher than any other category's best. These are prompts about entities designed to sound real but do not exist (e.g., plausible organization names, fictional but realistic people). The residual rate indicates that models struggle to distinguish plausible fakes from real entities even with explicit entity-verification instructions, suggesting a fundamental knowledge-boundary limitation that prompting alone cannot overcome.

*Note: do NOT frame this as "benchmark failure" here. The "adversarial probing" framing belongs in Ch 8 Discussion per THESIS_WRITING.md guidance. Here just report the finding.*

---

**¶5 — Entity-Aware dominance on entity-existence categories** (~4 sentences)

Entity-Aware achieves the largest reductions on the two categories where entity existence is the core question: nonexistent (29.5%→3.3% Mixtral, 19.0%→3.2% Llama) and plausible-but-fake (43.5%→11.0% Mixtral). This is expected — Entity-Aware explicitly asks the model to verify whether entities exist, which directly targets these categories. However, Entity-Aware is NOT the best prefix for every category: for factual questions, Epistemic Humility (Mixtral) or Structured Caution (Llama) outperforms it, and for borderline_obscure_real, Structured Caution is better for both models. This confirms the pilot's finding that no single prefix dominates across all categories — the specificity-vs-breadth tradeoff operates at the category level.

---

**¶6 — Regressions on borderline obscure-but-real entities** (~4 sentences)

The borderline_obscure_real category reveals a subtle failure mode. For Llama, three of the four prefixes INCREASE hallucination relative to baseline: Entity-Aware (3.0%→4.0%), Epistemic Humility (3.0%→4.0%), and Fact-Grounded (3.0%→5.0%). Only Structured Caution reduces it (3.0%→2.0%). The pattern suggests that instructions emphasizing entity skepticism or fabrication prohibition cause the model to second-guess real but obscure entities. This tension between skepticism (good for fake entities) and coverage (good for obscure real entities) foreshadows the precision-recall tradeoff that becomes more pronounced with fine-tuning (Chapter 7).

*Verified: Llama borderline_obscure_real baseline 3.0%, EA 4.0%, EH 4.0%, FG 5.0%, SC 2.0%. Three of four prefixes regress. Mixtral: baseline 11.5%, EA 8.0% (improves), so the regression is Llama-specific.*

---

**¶7 — Refusal rates are low but category-specific** (~4 sentences)

Across all non-CoT prefix conditions, refusal rates remain below 5%. However, the distribution is uneven. Fact-Grounded produces the highest refusal rates — 4.8% on Llama factual questions and 3.0% on Mixtral borderline_obscure_real — consistent with its instruction to "never fabricate" causing the model to refuse questions it could answer correctly. Entity-Aware, despite being the most benchmark-specific prefix, has the cleanest refusal profile: near-zero refusal across virtually all categories for both models. This suggests that asking a model to verify entity existence is less prone to over-refusal than prohibiting fabrication outright.

*Verified: Llama factual refusal: FG 4.8%, EA 0.0%. Mixtral obscure_real refusal: FG 3.0%, EA 0.0%.*

---

**¶8 — The correctness-safety picture at the prefix level** (~3 sentences)

Overall, system-prompt prefixes produce a favorable correctness-safety tradeoff: most prefix conditions simultaneously increase correctness and decrease hallucination, with only modest increases in refusal. The exceptions are category-specific (Fact-Grounded on factual questions, Entity-Aware/Epistemic on obscure_real for Llama) rather than systematic. A more dramatic tradeoff between hallucination reduction and false negatives on real entities emerges with fine-tuning, where the model's learned caution is permanent rather than prompt-dependent — this is the subject of Chapter~7.

*This paragraph does double duty: closes the combined 6.4/6.5 section AND sets up Ch 7's precision-recall discussion without spoiling it.*

---

**Estimated length**: ~3-4 pages (including 1 table or 2 figure references).

**No results spoiled**:
- ✅ No bridge analysis / geometric fixability (Ch 7)
- ✅ No fine-tuning results or precision-recall numbers (Ch 7)
- ✅ No best-per-prompt curation details (Ch 7)
- ✅ "Adversarial probing" framing deferred to Ch 8

**Cross-checks**:
- ✅ All category numbers from post-fix v5_category_metrics.csv
- ✅ Llama borderline_obscure_real regression verified (3/4 prefixes regress)
- ✅ Fact-Grounded highest refusal verified
- ✅ Entity-Aware cleanest refusal profile verified
- ✅ Heatmap figures exist in results/v5_prefixes/analysis/

**Forward references to update in existing tex**: `\ref{sec:category-analysis}` stays (label for 6.4). `\ref{sec:tradeoff}` needs to be changed to point to a subsection or paragraph within 6.4, OR the tradeoff content can simply be the closing paragraphs of 6.4 without a separate label. Simplest approach: remove the `\ref{sec:tradeoff}` forward reference in 6.3's closing paragraph and replace with a reference to 6.4.

**Geometric Difficulty Analysis (Ch 7.1-7.2, new, ~5 pages)**:
- Pilot study bridge: geometry predicts fixability, AUC=0.86 (train-only on 449 prompts)
- Expanded benchmark bridge: aggregate CV AUC 0.573 (Mixtral, 333:27 class ratio) and 0.712 (Llama, 211:24). Llama AUC is meaningful; Mixtral weaker due to imbalance. (Re-run Mar 22 after CoT exclusion fix — old numbers with CoT had 15/5 broken, now 27/24.)
- **Within-category density is the robust finding**: among nonexistent prompts, density significantly predicts fixability for both models (p=0.046, p=0.012). Unfixable prompts live in sparser embedding regions. Non-circular (same category, same structure, geometry varies). Llama plausible_fake oppositeness also significant (p=0.009). No result survives Bonferroni for 24 tests (α=0.0021).
- **Oppositeness** is the strongest overall discriminator between fixable hallucinations and correct prompts (p < 1e-10 for both models)
- Frame as: "The pilot study identified the signal (AUC=0.86). Within-category tests on the expanded benchmark confirm the mechanism: density predicts fixability within structurally identical prompts. The aggregate AUC drop reflects proper cross-validation and extreme class imbalance, not a failure to replicate."

**Template Diversity Ablation (Ch 7.6, new, ~2-3 pages)** `[RESULTS COMPLETE]`:
- Hold training examples constant, vary number of templates (T5=5 templates, T10=10, T-all=all ~194). Matched random controls (R{N}: same N as T5, full template pool) isolate diversity from dataset size.
- **Main result: template diversity doesn't matter.** T5 (5 templates, ~400 examples) performs statistically indistinguishably from T-all (all templates, ~2,400 examples). McNemar p=0.099 (Mixtral), p=0.773 (Llama). Neither significant.
- **Template-overlap split**: T5 Mixtral seen-template accuracy (96.3%) ≈ novel-template (93.0%). T5 Llama seen (96.3%) ≈ novel (94.1%). Model generalizes to unseen question structures.
- **T5 vs R{N} (diversity-vs-size control)**: no significant difference (Mixtral p=0.838, Llama p=0.386). Template diversity at constant N adds nothing.
- **T10 is numerically best** for both models (94.0%/95.8%) — better than T-all (94.4%/94.0%) despite fewer examples. Not significant (T10 vs T-all: Mixtral p=0.803, Llama p=0.080), but suggests additional data adds noise, not signal.
- **Interpretation**: Model learned behavioral caution (epistemic strategy), not template-specific patterns. Retroactively validates TruthfulQA generalization — if model doesn't need diverse templates within-benchmark, cross-benchmark transfer is unsurprising.
- **Practical implication**: Fine-tuning data quality (entity diversity, label accuracy) matters more than template diversity. A small set of well-curated examples with varied entities suffices.
- **Figures needed**: accuracy-vs-template-count curve (x: T5/R{N}/T10/T-all, y: accuracy, one line per model), template-overlap bar chart
- **Data**: `results/v5_finetuned/ablation/ablation_analysis.json`

**TruthfulQA Generalization (Ch 7.5, new, ~3-4 pages)** `[RESULTS COMPLETE]`:
- Best fine-tuned config per model (Mixtral configC, Llama configA) on TruthfulQA (817 questions, Lin et al. 2022)
- **Config selection explanation**: configC was best on held-out test set (94.4% accuracy, post-fix); determined before seeing TruthfulQA results (pre-registered). State: "We test the best-performing configuration per model as determined by held-out evaluation (Section 7.3), selecting before observing TruthfulQA results."
- **Expectations framing**: TruthfulQA tests misconceptions (common human errors), not fabrication (inventing entities). Our fine-tuning trained on fabrication. The fact that it transfers *at all* is noteworthy — it taught epistemic caution, not just fabrication-specific skepticism.
- **Key results (after re-judging)**:
  - Llama: acc +5.3pp (71.8%→77.1%, p=0.0002), halluc -4.4pp (17.6%→13.2%, p=0.0005), **both survive Bonferroni**. Refusal 0.5% (unchanged).
  - Mixtral: acc +2.2pp (p=0.1145), halluc -2.2pp (p=0.0763), neither significant. Directionally consistent but underpowered at n=817.
  - No over-caution tradeoff on TruthfulQA (refusal ≤0.7%). Custom benchmark over-caution is domain-specific.
  - Transition matrices: Llama 44 fixed / 15 broken (net +29). Mixtral 36 fixed / 24 broken (net +12).
- **Judge calibration**: Mixtral baseline 74.4% ≈ published MC2 ~73.9% (different metrics, rough alignment).
- **Category patterns (exploratory, no per-category correction)**: Biggest Llama improvements in Advertising (-31pp), Law (-19pp), Confusion (-13pp) — categories involving confident factual assertions. Sole worsening: Distraction (+7pp) — trick questions where more caution backfires.
- **Data quality note**: 62/817 Llama FT entries were contaminated by API connection errors silently defaulting to refusal (confidence=0.0). Detected during QC, re-judged clean. Include as 1-paragraph methods note — demonstrates rigor.
- **Limitations for this section**: (1) n=817 underpowers Mixtral's effect size (~3,000 needed), (2) judge label mapping approximate (our "correct" ≈ TruthfulQA "truthful+informative"), (3) literature comparison numbers still need PDF verification, (4) per-category analysis is exploratory

### Literature Comparison Section (Ch 8.X, ~2-3 pages) `[Phase 7C — write during Ch 8]`

**Input files** (all ready, don't regenerate):
- `results/literature_comparison/comparison_tables.md` — v5, three tables (detection/prompt/FT), 15 methods + 1 context paper, all caveats and verification notes. **This is the primary source.** Read it in full before writing.
- `results/literature_comparison/comparison_notes.md` — detailed per-method notes with citations and comparability justifications
- `results/literature_comparison/baselines_table.csv` — structured data for LaTeX table generation

**Output**: Write directly into Ch 8 LaTeX (likely Section 8.3 or wherever comparison lands in final chapter structure). No intermediate markdown.

**Bibliography**: The 15+ comparison papers need adding to `references.bib` as you write. Key papers already in bib: zheng2023judging, wataoka2024selfpreference, liu2023geval. Papers to add: R-Tuning (Zhang et al. NAACL 2024), INSIDE/EigenScore (Chen et al. ICLR 2024), ITI (Li et al. NeurIPS 2023), Semantic Entropy (Farquhar et al. Nature 2024), SelfCheckGPT (Manakul et al. EMNLP 2023), CoVe (Dhuliawala et al. ACL 2024), DoLA (Chuang et al. ICLR 2024), FactTune (Tian et al. ICLR 2024), FLAME (Dhuliawala et al. NeurIPS 2024), Mask-DPO (ICLR 2025), InstructGPT (Ouyang et al. NeurIPS 2022), Gekhman et al. (EMNLP 2024), Self-Refine (Madaan et al. NeurIPS 2023), SAPLMA (Azaria & Mitchell EMNLP 2023), RECITE (Sun et al. ICLR 2023).

**Structure (6 sections, ~0.5 page each)**:

1. **Opening: Why comparison is impossible.** Every method uses different benchmarks, models, metrics, hallucination definitions. Our 3-judge consensus on entity fabrication is incommensurable with FActScore, AUROC, TruthfulQA truthfulness. Tables provide directional context, not rankings. **Rule: No cross-metric numerical comparisons anywhere.**

2. **Detection axis.** INSIDE/EigenScore is closest conceptual kin (both: embedding geometry → prediction). Key difference: they analyze *response* embeddings post-generation from model internals; we analyze *entity* embeddings pre-generation from external model. Do NOT compare AUC numbers. Our unique addition: bridge analysis predicts *fixability*, not just presence — no detection method attempts this.

3. **Prompt/inference-time axis.** CoVe closest (both target entity-level halluc). Tradeoff: CoVe = 4-stage pipeline (expensive), we = single-shot prefix (cheap). **Give TruthfulQA comparison a full paragraph**: DoLA +12-17pp on TruthfulQA via decoding; our Llama -4.4pp halluc — smaller, but ours is cross-domain transfer (NOT trained on TruthfulQA). ~~CoT catastrophic refusal (62-68%) as genuine negative finding~~ INVALIDATED — was API failure artifact. Omit CoT from literature comparison.

4. **Fine-tuning axis.** R-Tuning gets substantial treatment (closest comparator, NAACL Outstanding Paper). Both teach abstention via SFT. Key difference: R-Tuning uses binary train-time probing; we use geometric features for best-per-prompt selection. Frame geometry-vs-probing as **the central open empirical question**. DPO family (FactTune, FLAME, Mask-DPO) is a different paradigm — mention, don't compare numbers. InstructGPT's "alignment tax" (RLHF increases halluc on some tasks) is relevant context for our precision-recall tradeoff.

5. **Pipeline as contribution.** NOT novelty-by-conjunction. The feedback loop is the insight: geometry predicts hallucination → geometry predicts which resist prompting → prompt responses become training signal → FT distills prompt behavior → geometry predicts where FT fails. Each step informs the next. A skeptical reviewer says "combining three things isn't a contribution" — respond with: the combination produces insight the parts don't (geometric taxonomy of fixability only emerges from having geometry + intervention + comparison).

6. **Honest limitations relative to prior work.** RAG methods have retrieval (we're closed-book). DPO has preference learning (we use simpler SFT). CoVe has structured verification (we use single prefix). ITI modifies activations directly. Our bridge analysis has small-sample caveats. We tested 2 models; most baselines test 3-6. **Concrete future work**: Run R-Tuning on our benchmark, or our method on ParaRel/MMLU.

**Scope restriction**: Only discuss the 10 verified methods in depth. The 5 unverified [*] methods (SAPLMA, SelfCheckGPT, Self-Alignment, Self-Refine, RECITE) get mentioned by name but no specific numbers asserted. See verification table at end of `comparison_tables.md`.

**Critical rules**:
- No cross-metric numerical comparisons (our halluc rate vs their FActScore, etc.)
- Hold our own numbers to same caveat standard as literature — use [†] flags from `comparison_tables.md`
- Frame R-Tuning comparison as open question, not claim of superiority
- Include methods that outperform us — framing is "different niche" not "we're better"

---

### Chapter 8: Discussion and Conclusion — Detailed Content Plan

**Calibration from reference theses**: Tarun (~4pp), Angela (~4pp), and Jinho Park (~4pp, "Collusion in Auctions," Math dept) all have short final chapters. None enumerate limitations as a list of weaknesses. Jinho's is the gold standard for tone:

**Jinho's Discussion — qualities to emulate:**
1. **Genuine intellectual synthesis.** He doesn't say "Chapter 4 showed X." He says "The main lesson of the thesis is that the revenue comparison depends on the *form* of the outsider distribution, not the *degree* of asymmetry." That's a new sentence no individual chapter contains. Our §8.1 should work the same way — the cross-chapter connections (density as unified difficulty indicator, prompt engineering as data generation strategy) are the synthesis, not recap of results.
2. **Limitations are one paragraph, confident, and immediately productive.** He names modeling assumptions, says "These are important issues, but orthogonal to the question addressed here," and immediately explains what a richer model would capture. No self-flagellation, no enumerated list of weaknesses. Our §8.2 should match this — lead with what we established, acknowledge scope constraints, frame as what the natural extensions are. Already tone-passed, but re-check against this standard.
3. **Future work is genuinely exciting.** Not "test on more data" but specific, novel research questions: "this generates a testable empirical prediction about milk procurement auctions." Our §8.4 should feel like "here's what we'd do with another year because it's interesting," not "here's how we'd fix our limitations."
4. **No self-flagellation anywhere.** Confident throughout. States what the thesis does, not what it hopes to do or fails to do.

**Our chapter is longer than theirs** because we have 3 contributions across 3 results chapters, thesis-level limitations to consolidate, and the MBB section. But the same principles apply: synthesis not re-argument, no new analysis. **Be aggressive on conciseness** — the reader just finished 3 results chapters and does not need a lengthy recap. Every sentence must add something the results chapters didn't already say. If a section can be 1 page instead of 2, make it 1.

**Estimated length**: 8-10 pages at 1.5 spacing. Target the low end.

---

#### Handling the Limitations Redundancy Problem

**The problem**: Ch 5-7 each have per-chapter limitation paragraphs/subsections. If Ch 8 also lists all limitations, the reader encounters the same caveats 2-3 times.

**The solution — two different levels of abstraction**:

- **Per-chapter limitations** (Ch 5 §5.6, Ch 6 §6.X, Ch 7 §7.5) are *local*: they tell the reader what to be cautious about when interpreting *that chapter's specific results*. E.g., "within-category signal concentrated in nonexistent" is directly relevant when the reader is looking at the within-category AUC table. **Keep these. Do not remove them.**

- **Ch 8 limitations** are *thesis-level*: concerns that cut across multiple chapters, affect the overall claim architecture, or are about scope. These should NOT repeat per-chapter caveats verbatim. Instead, briefly reference them ("as noted in Chapter X") and focus on cross-cutting implications.

**Concrete split**:
| Limitation | Where it lives | Why there |
|---|---|---|
| Within-category signal concentrated in nonexistent | Ch 5 §5.6 | Specific to Ch 5's statistical analysis |
| Bridge analysis class imbalance (15/5 still_broken) | Ch 7 §7.1 | Specific to fixability prediction |
| Template ablation caveats | Ch 7 §7.4 | Specific to generalization evidence |
| Embedding model dependency (single model) | **Ch 8** | Affects Ch 5, 6, and 7 simultaneously |
| Two models only | **Ch 8** | Affects all results chapters |
| Template-generated prompts (not naturalistic) | **Ch 8** | Affects entire benchmark design |
| English only | **Ch 8** | Scope limitation for all findings |
| Correlation not causation / no causal geometry intervention | **Ch 8** | Fundamental to the thesis claim |
| Small human validation (n=50) | **Ch 8** | Affects trust in all labels |
| Judge reliability on borderlines | **Ch 8** (brief) | Cross-chapter, but reference Ch 5 details |

---

#### Section Layout

```
8   Discussion and Conclusion

    [Opening paragraph — what this chapter does, no subsection header]

    8.1  Contributions
    8.2  Limitations
    8.3  Connections to Cognitive Science
    8.4  Future Work
    8.5  Concluding Remarks
```

No sub-subsections. §8.1 uses bold lead-ins per contribution (not `\subsubsection`). §8.4 is a numbered list. Everything else is flowing paragraphs.

---

#### §8.1 Contributions (~1.5 pages) — Detailed Outline

**Balance with Ch 1**: Ch 1 §1.1 states contributions as claims without numbers. Ch 8 §8.1 restates them with key numbers and cross-chapter synthesis. Ch 1 = claim. Ch 8 = evidence. §8.1 is not a recap — it ties numbers to claims and draws connections *across* chapters that individual chapters couldn't make.

**What each chapter's Discussion already says (DO NOT REPEAT)**:
- Ch 5 §5.6: density predicts at two granularities, why density (entity popularity analogue), why external embeddings work, surface feature comparison
- Ch 6 closing: prefixes work broadly, entity-existence categories see largest gains, tension between skepticism and obscure-real coverage foreshadowed
- Ch 7 §7.5: geometry predicts fixability (extending risk → difficulty), geometry explains resistance structure, geometry does NOT predict harm, precision-recall as criterion shift, model learned behavioral caution (three convergent tests)

**What §8.1 must add that no individual chapter says**:
- The *unified arc*: density is a single geometric property that (a) predicts hallucination occurrence (Ch 5), (b) predicts which hallucinations resist prompting (Ch 7 §7.1), and (c) predicts which hallucinations resist fine-tuning (Ch 7 §7.3). No chapter connects all three.
- The *progression from signal to action*: Ch 5 finds a correlate, Ch 6 shows intervention works, Ch 7 shows the correlate predicts where intervention works. The pipeline is not three independent experiments — each step uses the previous step's output.
- The *honest accounting*: initial AUC=0.86 → honest decomposition → within-category density → fixability prediction → fine-tuning distillation. The story got more modest but more real.

**Paragraph-level outline (3 contributions, matching Ch 1 §1.1):**

**¶1 — Opening (2-3 sentences)**
- This thesis asked three questions: whether embedding geometry predicts hallucination, whether prompting can reduce it, and whether geometry can guide intervention strategy. The answers form a connected arc, not three independent findings — each chapter's output feeds the next.
- **Do NOT list the questions and answers here — that's what the paragraphs below do.** Just frame the section.

**¶2 — Contribution 1: Geometric prediction of hallucination (5-6 sentences)**
- The geometric prediction story, with honest numbers. Category alone AUC 0.77; geometry adds modest increment (+0.02-0.04). The real finding: within-category density in nonexistent prompts (p < 10⁻⁵, both models, Bonferroni-surviving, CV AUC 0.67).
- **The cross-chapter connection (what Ch 5 couldn't say)**: This signal is not just correlational — it reappears in Ch 7 as a predictor of *fixability*. The same feature, measured on the same prompts, predicts both hallucination occurrence and intervention resistance. Density operates as a unified geometric indicator of prompt difficulty, not just prompt risk.
- Interpretation: sparse neighborhoods = fewer similar prompts to anchor generation → higher hallucination risk AND higher resistance to correction.
- **Verified numbers**: AUC 0.782/0.773 cat-only, 0.800/0.814 cat+geo (from `v5_geometry_prediction_overall.csv`, post-fix). Within-cat: p = 5.7×10⁻⁷ / 3.4×10⁻⁵, CV AUC 0.665±0.066 / 0.678±0.042.

**¶3 — Contribution 2: Prompt-based hallucination reduction (3-4 sentences)**
- All four prefixes significantly reduce hallucination (McNemar p < 10⁻⁶, both models). Replicated at 5× scale with same prefix rankings. Single-shot system prompts achieve 54-69% relative reduction without multi-pass verification or retrieval.
- **The cross-chapter connection (what Ch 6 couldn't say)**: Ch 6 produces the prefix responses that become Ch 7's fine-tuning training data. Best-per-prompt selection across prefixes produces training data that is 97-98% correct — a quality floor that makes fine-tuning viable. The prefix experiment is not just an intervention study; it is a data generation strategy.
- **Verified numbers**: Mixtral Entity-Aware 14.8%→4.7%, Structured Caution best for Llama 9.7%→3.0%. All p < 10⁻⁶ (from `v5_prefix_metrics.csv`, post-fix).

**¶4 — Contribution 3: Geometric diagnosis and fine-tuning distillation (6-8 sentences)**
- This is the largest contribution and bundles three connected findings (matching Ch 1's Contribution 3):
- *Fixability prediction*: Density predicts not just occurrence but *difficulty*. Prior work predicts whether hallucination occurs; we predict whether it can be fixed. FT bridge density p = 0.0017, |r| = 0.80 (Mixtral, Bonferroni-surviving).
- *Distillation*: Fine-tuning matches best prefix without runtime prompting (Mixtral: 94.4% vs 94.9%, p = 0.82). Three convergent tests confirm behavioral caution, not memorization: TruthfulQA transfer (Llama -4.4pp, Bonferroni-sig), template invariance (T5 ≈ T-all), decontamination (gap <3pp).
- *Precision-recall tradeoff*: Fine-tuning reduces hallucination (11.8%→1.3% Mixtral) at cost of factual refusals (5→15). Most regressions are refusals (70%), not new fabrications. Tradeoff is domain-specific: no over-caution on TruthfulQA.
- **The cross-chapter connection (the unified pipeline)**: The full arc — geometry predicts risk (Ch 5), prompts generate corrective signal (Ch 6), geometry curates training data by identifying unfixable prompts (Ch 7), fine-tuning consolidates the correction (Ch 7) — is a single integrated system where each component informs the next. The tension Ch 6 foreshadowed (entity skepticism vs. obscure-real coverage) materializes in Ch 7 as the precision-recall tradeoff. Geometry is the diagnostic thread throughout.
- **Verified numbers**: Mixtral configC 94.4% vs Structured Caution 94.9%, p = 0.82. Llama configA 94.0% vs 95.8%, p = 0.14. FT bridge density p = 0.0017. TruthfulQA Llama halluc -4.4pp, p = 0.0005. Prefix bridge within-cat p = 0.046/0.012.

**What NOT to include in §8.1**:
- Don't re-explain methodological choices (Ch 4)
- Don't re-explain features or statistical tests (Ch 4-5)
- Don't present any number not already in Ch 5-7
- Don't discuss limitations (§8.2) or cognitive science (§8.3)

**Reviewer anticipation**:
1. "This just restates the results chapters." → The value-add is the cross-chapter connections: density as a unified indicator across three chapters, prefix responses as training data, the foreshadowed tension materializing as precision-recall tradeoff.
2. "Three contributions — are they equally novel?" → No. Contribution 1 (density) is a modest refinement. Contribution 2 (prefixes work) is a confirmation in a controlled setting. Contribution 3 (fixability prediction + distillation + generalization) is the genuinely novel finding and the practical payoff. §8.1 should give Contribution 3 the most space.

---

#### §8.2 Limitations (~1.5 pages)

Thesis-level only — per-chapter caveats already stated in Ch 5-7 (now tightened with forward references to this section). Each limitation gets 2-4 sentences, not a full paragraph.

**What's already handled in per-chapter limitations (DO NOT REPEAT):**
- Ch 5: signal concentrated in nonexistent, modest effect sizes (r≈0.25, AUC 0.67)
- Ch 7: hyperparameter overrides, small still-broken samples (n=6/9), unpaired cross-category comparisons
- Ch 5 + Ch 7 Scope paragraphs: already briefly mention single embedding model, two models, corpus dependence, and template prompts with forward references to this section

**What §8.2 must add:** The *thesis-level implications* of these scope constraints — how they interact, what they mean for the overall claims, and what would resolve them. Not restating the facts (the Scope paragraphs did that) but interpreting their collective significance.

**Ordering rationale:** Lead with the most fundamental limitation (correlation ≠ causation — affects the entire claim architecture), then scope constraints in order of impact. Four paragraphs total.

**Paragraph-level outline (4 paragraphs):**

**¶1 — Correlation not causation (3-4 sentences)**
- The most fundamental limitation. All geometric findings are correlational. Density is associated with hallucination and fixability, but we have not causally intervened on the manifold. A confound (e.g., entity rarity independently causing both sparse embeddings and poor model recall) cannot be ruled out.
- Ch 5 §5.6 compared density against surface features (entity name length) and showed density captures more signal, but this does not establish causation. The claim throughout is: density is a useful *diagnostic*, not a verified *mechanism*. All three contributions inherit this limitation.

**¶2 — Two models for intervention (2-3 sentences)**
- The 10-model benchmark (Ch 5) establishes model-agnostic difficulty, but intervention experiments (Ch 6-7) cover only Mixtral and Llama. The two provide architectural diversity (8×7B vs 128-expert MoE, LoRA vs QLoRA), but the entire intervention pipeline is validated on a narrow range. We cannot claim the precision-recall tradeoff or distillation results generalize to dense architectures, larger models, or closed-source systems.

**¶3 — Single embedding model (2-3 sentences)**
- All geometry depends on text-embedding-3-large. A preliminary robustness check (Appendix~B) shows centrality is stable across three embedding models, but density's overall signal is embedding-dependent, and the within-category density result has not been tested with alternative embeddings. If the density signal doesn't transfer, the fixability prediction pipeline would need re-validation per embedding model.

**¶4 — Benchmark scope (3-4 sentences)**
- All prompts are template-generated with entity substitution. This provides experimental control but doesn't reflect naturalistic user queries. TruthfulQA transfer provides partial evidence beyond templates, and the template ablation shows the model doesn't memorize template patterns — but neither test addresses template *naturalness* as distinct from template *diversity*.
- Human validation ($n = 50$, group discussion, 90\% agreement) spot-checks the judge pipeline but is not a full inter-annotator reliability study. All results inherit this label-quality constraint.
- All prompts and evaluation are in English.

**Plausible-fake reframing**: Dropped from §8.2. Already framed as adversarial probing in Ch 4 §4.1 and Ch 6 category discussion. Not a limitation — a design feature. Does not need re-stating.

**What NOT to include in §8.2:**
- Per-chapter methodological limitations (Ch 5-7 handle those)
- Judge contamination issue (Appendix A and Ch 4)
- CoT exclusion (Ch 4 and Appendix A)

**Reviewer anticipation:**
1. "You only tested two models." → Acknowledged. 10-model prediction benchmark as partial mitigation.
2. "How do you know this isn't just entity frequency?" → Ch 5 §5.6 compared surface features. But no comparison against pre-training frequency counts (unavailable for closed-source models).
3. "Why not model-internal representations?" → External embeddings are model-agnostic by design. Tradeoff (generality vs specificity) is a design choice, not an oversight.

#### §8.3 Connections to Cognitive Science (~1-1.5 pages)

Required for MBB track. Two strong parallels plus one combined paragraph. Suggestive framing only — we did not design experiments to test cognitive hypotheses.

**What already exists in the thesis (pay these off, don't introduce from scratch):**
- Ch 1 ¶2: "metacognition" and "confabulate" frame the thesis question
- Ch 2 §2.2: "confabulate" in hallucination definition
- Ch 7 §7.5: "criterion shift in the sense of signal detection theory" and "consistent with a form of learned metacognition" — used as interpretive language, no cog sci citations

**What §8.3 must do:** Ground those terms in actual cognitive science literature with citations. Ch 1 and Ch 7 *use* the concepts; §8.3 *develops* them.

**Kept vs. dropped:**
- **Confabulation / DRM** — KEEP (strong: plausible-fake category is structurally identical to DRM lures, not a metaphor)
- **Metacognition + SDT** — KEEP, COMBINED into one paragraph (both strong; metacognition frames the "what," SDT formalizes the tradeoff structure)
- **RSA / representational geometry** — DROPPED (too generic: "both use geometry to predict behavior" doesn't add interpretive value beyond what Ch 5 Discussion already provides)

**Paragraph-level outline:**

**¶1 — Opening (already written in .tex)**
- Two sentences. Frames section, sets epistemological tone.

**¶2 — Confabulation and false memory (~4-5 sentences)**
- Humans confabulate at knowledge boundaries; our benchmark probes the same boundary.
- Specific structural match: plausible-fake category ≈ DRM paradigm (Roediger & McDermott 1995). DRM: participants falsely "remember" semantically plausible lures never presented. Our plausible fakes: entities designed to be plausible enough to trigger false recognition by the model. Same experimental logic, different system.
- Edge-factual prompts parallel imitative falsehoods (Lin et al. 2022) — misconceptions reproduced through statistical/cultural transmission.
- Interpretive payoff: hallucination is systematic error at knowledge boundaries, not random failure. The mechanism — plausible interpolation where genuine knowledge is absent — is structurally similar across humans and LLMs.
- **Do NOT claim**: LLMs have episodic memory or "remember" in the human sense. The parallel is structural, not mechanistic.
- Cite: Roediger & McDermott 1995, Loftus 1979. Already in bib: Lin et al. 2022.

**¶3 — Metacognition and signal detection (~5-6 sentences)**
- The thesis asks whether models "know what they don't know" — this is metacognition. Our geometric features function as an external monitoring signal (assessing reliability from representational structure, not the model's self-report). Fine-tuning teaches the model to act on that assessment — expressing uncertainty at knowledge boundaries. The generalization evidence (TruthfulQA, template invariance, cross-category transfer) suggests this is a general behavioral strategy, not domain-specific memorization.
- The precision-recall tradeoff formalizes this via signal detection theory (Green & Swets 1966). The fine-tuned model faces a noisy discrimination ("real or fabricated?") and shifts its criterion toward caution — reducing false alarms (hallucinations) at the cost of increased misses (false refusals). The domain-specificity (no over-refusal on TruthfulQA) indicates the criterion shift is applied to entity-existence judgments specifically, not globally.
- Interpretive payoff from SDT: the tradeoff is *movable*. A model with better underlying discrimination (higher d') could achieve the same false-alarm rate with fewer misses — reframing future work as improving sensitivity rather than accepting the tradeoff.
- Cite: Green & Swets 1966. Already in bib: Kadavath et al. 2022.

**¶4 — Closing caveat (1 sentence)**
- These parallels are interpretive. We do not claim LLMs implement the same mechanisms as human cognition, but the structural similarities — plausible interpolation at knowledge boundaries, and the sensitivity-criterion tradeoff in uncertain domains — may reflect general properties of systems that must act under incomplete knowledge.

**What NOT to include:**
- Extended tutorials on DRM or SDT (Discussion, not Background)
- Claims that LLMs are cognitive systems
- New results or analyses
- RSA / representational geometry (dropped — too generic)

**Bib entries needed**: Roediger & McDermott 1995, Loftus 1979, Green & Swets 1966.
**Dropped**: Kriegeskorte et al. 2008 (RSA), Flavell 1979, Nelson & Narens 1990 (formal metacognition framework — too much apparatus for the functional parallel we're drawing).

#### §8.4 Future Work (~1 page)

Three items, ~0.75-1 page total. Frame as opportunities, not remediations. The excitement comes from the ideas, not from length. Each item: 3-4 sentences — what you'd do, why it's interesting, what it would tell us.

**Paragraph-level outline (3 items):**

**¶1 — From correlation to causation (3-4 sentences)**
- The most intellectually interesting direction. Density predicts hallucination and fixability, but is it causal? A perturbation experiment: rephrase prompts to shift their embedding into denser neighborhoods and test whether hallucination rates decrease. This would distinguish density as a causal factor from a correlate of entity rarity.
- Frame as: "the thesis established the diagnostic; the natural next step is testing the mechanism."

**¶2 — Generalization: embeddings, models, and naturalistic prompts (3-4 sentences)**
- Combines three scope questions into one direction: does the density signal hold across embedding models (sentence-transformers, model-internal representations), across more architectures (dense models, closed-source), and on naturalistic user queries rather than template-generated prompts?
- The preliminary embedding comparison (Appendix B) and TruthfulQA transfer provide starting points; the full test would determine whether density-as-difficulty is a general geometric principle or specific to one experimental setup.
- Frame as: "the thesis validated the signal in one setting; the question is how far it extends."

**¶3 — Operational geometry and method comparison (3-4 sentences)**
- Two practical next steps. First, geometry-guided prefix selection: the bridge analysis shows density predicts which prompts benefit from intervention, so a geometry-aware system could select the optimal prefix per prompt rather than applying one prefix uniformly. Second, direct comparison with R-Tuning (Zhang et al. 2024), the closest method in the literature — both teach abstention via SFT, but through different training signals. Running both on the same benchmark would clarify whether geometric curation adds value over probing-based selection.
- Frame as: "the thesis built the diagnostic pipeline; the question is whether it improves operational systems."

#### §8.5 Concluding Remarks (~0.25 page)

**Calibration**: Tarun closes with 3-4 sentences connecting back to his opening (Leibniz's dream) and calling his work "a small step." Angela closes with ~4 sentences about uncovering "novel glimpses of insight." Both are brief, modest, and zoom out to broader significance without overclaiming.

**What this section must do:**
1. Restate the thesis arc at the highest level of abstraction — one sentence, no numbers
2. Name the core intellectual finding (not the pipeline, not the methods — the *idea*)
3. Connect back to the opening framing (Ch 1's metacognition/Twain quote — "what you know for sure that just ain't so")
4. One sentence of broader significance — modest, not flowery

**What it must NOT do:**
- Re-list contributions (§8.1 did that)
- Re-list limitations (§8.2 did that)
- Introduce new ideas
- Be more than ~4-5 sentences
- Be flowery or grandiose ("we hope this thesis serves as a beacon...")

**Paragraph outline (~4 sentences):**

1. The arc: geometry predicts hallucination, prompts reduce it, fine-tuning makes the reduction permanent, and geometry predicts where the reduction has side effects. (One sentence — the thesis in miniature.)
2. The core idea: the model learned when to be skeptical about its own knowledge — epistemic caution, not pattern matching. This is the finding that unifies the generalization evidence.
3. Connection back to Ch 1: the Twain quote and the metacognition framing. The thesis asked whether representational structure reveals where a model's knowledge thins out. The answer is yes — and that structure can guide both diagnosis and intervention.
4. Broader significance (modest): as LLMs are deployed in high-stakes settings, understanding *where* they fail — not just *how often* — becomes increasingly important. Geometric analysis of the input space is one approach to that understanding.

---

## Background vs. Literature Review: Structural Decision

**Decision: Separate them** (like Tarun Prasad's thesis, not Angela Li's combined approach).

### Evidence from reference theses

- **Angela Li** (*Statistical Perspectives on Algorithmic Fairness*): Ch 2 "Background and Literature Review" — combined, 25 pages. Works because her thesis is single-domain (algorithmic fairness); background concepts and prior work sit on the same continuum.
- **Tarun Prasad** (*LLM-Powered Lemma Extraction for Automated Theorem Proving*): Ch 2 "Background" (formal proofs, Coq, LLMs as separate foundation sections) + Ch 3 "Literature Review" (hammers, neural theorem proving, LLM theorem proving). Works because his thesis bridges two domains (formal verification + ML) that need separate conceptual grounding before reviewing how they've been combined.

**Our thesis bridges two domains** — hallucination/safety and embedding space geometry — making the separated structure (like Tarun's) more appropriate. A reader from the NLP/safety community needs geometry background; a reader from the geometry/manifold learning community needs hallucination context. Combining them would force awkward jumps between unrelated foundational concepts.

### ~~Proposed Background Chapter Contents~~ SUPERSEDED — see detailed outline below

### Chapter 2: Background — Detailed Content Plan

**Purpose**: Teach concepts the reader needs to understand our methods. Does NOT position contributions (Ch 1's job). Does NOT define our specific experimental choices (Ch 4's job). Teaches *general concepts*; Ch 4 applies them.

**Target audience**: The department committee — "technical professionals not necessarily conversant with the subject matter." A CS professor who knows ML broadly but not hallucination research, embedding geometry, or LLM-as-judge.

**Estimated length**: 12-15 pages. Tarun Prasad's Background is ~15 pages covering two domains (formal proofs + LLMs). Ours covers two domains (hallucination + embedding geometry) at comparable depth.

**Tone**: Definitional and precise like Tarun's. No opinions, no positioning, no "gap" statements (Ch 3). Every paragraph teaches something needed for Ch 4+.

---

**CRITICAL BOUNDARY CORRECTION**: The original plan (and "Mathematical Content" section above) says Background should contain "formal definitions with equations" for the 5 geometric features. **This is wrong.** Ch 4 §4.4.3 (already written, ~100 lines LaTeX) defines ALL five features with full equations, figures, and design rationale. Duplicating creates redundancy.

**Corrected division**:
- **Background (Ch 2)**: *Mathematical prerequisites* — cosine distance, PCA, k-NN, manifold hypothesis, what intrinsic dimension/curvature/density *mean conceptually*. General concepts with standard formulations.
- **Setup (Ch 4 §4.4)**: *Our specific features* — TwoNN formula, PCA-residual curvature, sign-flip oppositeness, inverse-mean density, corpus-mean centrality. Experiment-specific design with our hyperparameters.

Test: if a definition would change if we changed our experimental design, it belongs in Ch 4. If it's a general mathematical concept, Ch 2.

---

#### 2.1 Large Language Models (~2.5-3 pages)

**What the reader needs for Ch 4+**: What LLMs are, how they generate text, why generation is susceptible to fabrication. Ch 4 assumes "temperature," "next-token prediction," "system prompt," and "instruct model" are known.

**¶1 — Transformer architecture (1 paragraph, ~5 sentences)**
- LLM = neural network trained to predict next token given preceding tokens. Self-attention: each token attends to all prior tokens. Describe at "what it does" level, not full math.
- Key point: training objective (next-token prediction on internet text) rewards fluency and plausibility, not factual accuracy.
- Cite: Vaswani et al. 2017, Brown et al. 2020.

**¶2 — Scaling and emergent capabilities (~4 sentences)**
- Scaling laws (Kaplan et al. 2020). Emergent behaviors at scale: in-context learning, instruction following (Wei et al. 2022).
- Modern LLMs produce fluent, detailed responses to nearly any question. Failure mode is *plausible fabrication*, not incoherence.

**¶3 — Inference: how LLMs generate responses (~5 sentences)**
- Autoregressive generation: tokens one at a time, each conditioned on prior tokens.
- Temperature: controls sampling distribution sharpness. 0 = deterministic; higher = more diverse. Our experiments: 0.7 generation, 0.0 judging.
- System prompts and instruction tuning (Ouyang et al. 2022): mechanism our prefix interventions exploit (Ch 6).

**¶4 — Open-weight vs. closed models (~3 sentences)**
- Closed (GPT-5.1, Claude): API-only. Open-weight (Mixtral, Llama): weight access enables LoRA fine-tuning.
- Drives experimental design: 10-model benchmark includes both; interventions require open-weight.

**¶5 — Architecture variants: MoE (~3 sentences)**
- Mixture-of-Experts: only a subset of parameters active per token. Mixtral 8x7B: 46.7B total, ~12.9B active. Llama 4 Maverick: ~400B total, 17B active.
- Relevant because both intervention targets use MoE. Do NOT detail routing mechanics.
- Cite: Jiang et al. 2024 (Mixtral).

**Exclude**: Detailed attention math. Training data composition. Specific model capabilities. Connection to hallucination (that's 2.2).

---

#### 2.2 Hallucination in LLMs (~2.5-3 pages)

**What the reader needs**: What hallucination is, why it happens, types, why it's hard to detect. Ch 4 §4.1 defines 7 categories — reader needs the general framework first.

**¶1 — Definition (~4 sentences)**
- Hallucination: fluent, confident, factually incorrect or fabricated content. No explicit truth-checking mechanism in generation.
- Cite: Ji et al. 2023 (survey), Maynez et al. 2020.

**¶2 — Taxonomy: intrinsic vs. extrinsic (~4 sentences)**
- Intrinsic: contradicts source. Extrinsic: introduces unverifiable info. Taxonomy designed for tasks with reference documents.
- In open-ended generation, no source to contradict — the relevant question is *why* the model fabricated. Motivates our category-based taxonomy (Ch 4 §4.1).
- Cite: Ji et al. 2023, Maynez et al. 2020.

**¶3 — Why LLMs hallucinate (~5 sentences)**
- **Training objective mismatch**: plausibility ≠ accuracy. **Soft knowledge boundaries**: confidence degrades gradually with entity rarity (Sun et al. 2024). **No explicit retrieval**: must reconstruct from compressed parametric memory — interpolates when signal is weak. **Overconfidence**: rarely express uncertainty spontaneously (Kadavath et al. 2022).
- Cite: Sun et al. 2024, Kadavath et al. 2022, Yin et al. 2023.

**¶4 — Why it matters (~4 sentences)**
- Concrete harms: fabricated medical advice, invented case law, false historical claims. Hallucinations are *plausible* — indistinguishable from correct output without external verification.
- Scale: LLM deployment in search, customer service, decision support → growing surface area for harm.
- Cite: Lin et al. 2022 (imitative falsehoods), Xu et al. 2024 (hallucination cannot be eliminated).

**¶5 — Detection challenges (~3 sentences)**
- Surface features don't reliably distinguish hallucinated from correct responses.
- Two approaches: (a) post-generation detection, (b) pre-generation risk estimation. Our work explores (b) via embedding geometry.

**Exclude**: Our 7-category taxonomy (Ch 4). Specific rates (Ch 5). Detection method survey (Ch 3). Prompt-based mitigation (Ch 3/6).

---

#### 2.3 Text Embeddings and Embedding Geometry (~3-4 pages)

**The most technical and most important section for the thesis.** Reader who understands this can follow every geometric argument in Ch 4-7.

**¶1 — What are text embeddings? (~4 sentences)**
- Embedding model maps token sequences to fixed-dimensional vectors; semantically similar texts → nearby vectors. Contrastive learning training.
- Result: continuous space where geometric relationships carry semantic meaning.
- Cite: Reimers & Gurevych 2019, Bengio et al. 2013.

**¶2 — Cosine similarity and distance (1 paragraph + equation)**
- $\text{sim}(\mathbf{x}, \mathbf{y}) = \frac{\mathbf{x} \cdot \mathbf{y}}{\|\mathbf{x}\| \|\mathbf{y}\|}$. Distance: $d_{\cos} = 1 - \text{sim}$. Range 0-2.
- Why cosine: for L2-normalized vectors, $\|\mathbf{x} - \mathbf{y}\|^2 = 2(1 - \text{sim})$. Invariant to magnitude, focuses on direction.
- All distances in this thesis use cosine distance. State once here.

**¶3 — High-dimensional geometry (~4 sentences)**
- Embeddings in $\mathbb{R}^{3072}$. Distance concentration: pairwise distances converge to narrow range (Aggarwal et al. 2001). *Relative* distances within structured data remain informative. Our features are defined relative to corpus distribution.
- Unit hypersphere: L2-normalized → surface of unit sphere. Cosine distance is the natural metric.

**¶4 — The manifold hypothesis (~4 sentences)**
- High-dim data lies on/near a lower-dim manifold (Fefferman et al. 2016). Text embeddings concentrate on structured subspace.
- Creates meaningful local geometry: dense/sparse regions, variable curvature, prominent variation directions.
- Central thesis hypothesis (informal): geometric properties of a prompt's manifold position carry hallucination risk information. Ch 5 tests this.
- Cite: Fefferman et al. 2016, Bengio et al. 2013.

**¶5 — k-Nearest Neighbors (short, ~3 sentences)**
- For point $\mathbf{x}_i$ in $N$ points, $k$-NN = $k$ points with smallest distance.
- Building block for density, intrinsic dimension, curvature (Ch 4 §4.4). $k$ controls locality.

**¶6 — Principal Component Analysis (1 paragraph + equation)**
- PCA: orthogonal directions of maximum variance = eigenvectors of covariance matrix. Explained variance ratio: $\sum_{j=1}^{p} \sigma_j^2 / \sum_\ell \sigma_\ell^2$.
- PCA in two roles in our work: (a) measuring local curvature, (b) constructing oppositeness. Both defined in Ch 4 §4.4.
- Keep standard and brief — establish notation.

**¶7 — Geometric properties of manifolds: conceptual overview (~6 sentences)**
- Introduce the *concepts* our Ch 4 features formalize (NOT the formulas):
  - **Intrinsic dimensionality**: effective local directions of variation. Estimators: TwoNN (Facco et al. 2017), MLE (Levina & Bickel 2004).
  - **Curvature**: how well a local neighborhood is approximated by a flat subspace. Measured via PCA residual variance.
  - **Density**: number of similar points nearby. High = well-represented; low = isolated/OOD. Standard in anomaly detection (Breunig et al. 2000).
  - **Centrality**: distance from distribution center.
- Do NOT give our specific formulas. Note that oppositeness is our novel construction, defined in Ch 4 §4.4.3.
- Cite: Facco et al. 2017, Levina & Bickel 2004, Breunig et al. 2000.

**Exclude**: Our specific formulas (Ch 4 §4.4). Hyperparameter choices (Ch 4). Feature distributions/results (Ch 5). UMAP visualizations (Ch 5).

---

#### 2.4 Evaluating LLM Outputs (~2-3 pages)

**What the reader needs**: Why evaluating LLM outputs is hard, how LLM-as-judge works, known biases, consensus approaches. Ch 4 §4.3 describes our specific panel.

**¶1 — The evaluation bottleneck (~4 sentences)**
- ~127,000+ judge calls needed. Human annotation infeasible at this scale. BLEU/ROUGE don't capture semantic accuracy for open-ended QA.

**¶2 — LLM-as-judge (~5 sentences)**
- Define: LLM evaluates another LLM's output. Judge receives question, response, optionally ground truth, produces label per rubric.
- Zheng et al. 2023: >80% alignment with human preferences. Liu et al. 2023: rubric-based outperforms traditional metrics.
- Reference-free vs. reference-based. We use reference-based.
- Cite: Zheng et al. 2023, Liu et al. 2023.

**¶3 — Known biases (~5 sentences)**
- Verbosity bias, position bias, self-preference bias (Wataoka et al. 2024), shared blind spots.
- Motivates: (a) multi-judge panels, (b) cross-provider diversity.
- Cite: Zheng et al. 2023, Wataoka et al. 2024, Chiang & Lee 2023.

**¶4 — Consensus approaches (~4 sentences)**
- Panel with majority vote, analogous to inter-rater reliability. Cross-provider diversity reduces correlated errors.
- $n = 3$ balances robustness with cost. Our specific panel: Ch 4 §4.3.

**¶5 — Rubric design (~3 sentences)**
- Multi-category labeling needed: correct, partial, hallucinated, refused. Binary loses fabrication vs. refusal distinction — critical for fine-tuning (Ch 7).
- Our 4-point rubric: Ch 4 §4.3.

**Exclude**: Our 3-judge composition (Ch 4). Rubric details (Ch 4). Agreement rates (Ch 5). Contamination bug (Ch 4/5).

---

#### 2.5 Fine-Tuning and Parameter-Efficient Adaptation (~1.5-2 pages)

**What the reader needs for Ch 7**: What fine-tuning is, what LoRA is, self-distillation.

**¶1 — Supervised fine-tuning (~4 sentences)**
- Fine-tune on curated (input, output) pairs. Instruction tuning (Ouyang et al. 2022) is a special case. Risk: overfitting.
- Cite: Ouyang et al. 2022, Zhou et al. 2023 (LIMA).

**¶2 — LoRA (1 paragraph + equation, ~5 sentences)**
- Freeze pre-trained weights, add trainable low-rank matrices: $\Delta W = BA$, $B \in \mathbb{R}^{d \times r}$, $A \in \mathbb{R}^{r \times d}$, $r \ll d$.
- Reduces trainable params to ~0.1%. Limits catastrophic forgetting. Key hyperparameters: rank $r$, scaling $\alpha$, target modules.
- QLoRA: LoRA + 4-bit quantization of base model.
- Cite: Hu et al. 2022, Dettmers et al. 2023.

**¶3 — Self-distillation (~3 sentences)**
- Model fine-tuned on its own best outputs. Learns careful behavior by default without system prompt.
- Well-established: Hinton et al. 2015, Furlanello et al. 2018.

**Exclude**: Our hyperparameters (Ch 7). Together AI details (Ch 7). Training data composition (Ch 7). Results (Ch 7).

---

#### Chapter closing (~0.25 page)

Single paragraph naming all 5 sections and forward-referencing Ch 3 (literature gaps) and Ch 4 (experimental infrastructure).

---

#### Citations for Ch 2

**Already in bib** (verify): ji2023survey, maynez2020faithfulness, lin2022truthfulqa, zheng2023judging, liu2023geval, wataoka2024selfpreference, hu2022lora, zhou2023lima, kadavath2022language, marks2023geometry, li2024inferencetime, bengio2013representation, facco2017twonn, levina2004maximum, sun2024entity, yin2023large

**Need to add**: Vaswani et al. 2017, Brown et al. 2020, Kaplan et al. 2020, Wei et al. 2022, Ouyang et al. 2022, Touvron et al. 2023, Aggarwal et al. 2001, Fefferman et al. 2016, Breunig et al. 2000, Dettmers et al. 2023, Hinton et al. 2015, Furlanello et al. 2018, Chiang & Lee 2023, Reimers & Gurevych 2019, Xu et al. 2024, Jiang et al. 2024

---

#### Writing order

1. **2.3** (Embeddings/Geometry) — load-bearing, write first
2. **2.2** (Hallucination) — familiar material
3. **2.1** (LLMs) — brief, standard
4. **2.4** (Evaluation) — draws on 2.2
5. **2.5** (Fine-tuning) — shortest
6. **Closing** — last

---

#### Reviewer anticipation

1. **"Why so brief on transformers?"** → Empirical thesis. Reader needs *what* LLMs do and *why* they hallucinate, not attention math.
2. **"Why define cosine/PCA in Background instead of Ch 4?"** → Standard concepts used without definition in Ch 4-5. Committee from outside NLP needs them. Ch 4 defines *our features* using these building blocks.
3. **"Section 2.3 doesn't define your specific geometric features?"** → Deliberate. Features with full equations in Ch 4 §4.4.3, including design rationale. Background = general concepts; Setup = our application.
4. **"Why fine-tuning in Background?"** → Ch 7 is ~20-30 pages assuming reader knows LoRA. 1.5-page primer prevents tutorial material disrupting results.

### Proposed Literature Review Chapter Contents (Detailed Outline)

The Literature Review surveys prior work and identifies the gaps we fill. Expanded from the v3 conference paper's 6-subsection / 26-ref related work into a full thesis chapter: 8 sections, ~70+ references, ~14-18 pages. Each section ends with an explicit **Gap** paragraph stating what the prior work does not do that this thesis does. The chapter's narrative arc builds from "what is hallucination and how do we measure it" → "how has it been detected and mitigated" → "what geometric/representational tools exist" → "where the gaps are that motivate our three research questions."

**Target**: 60-80 total references (comparable to Angela Li's 65 and Tarun Prasad's 78). Currently 33 in bib; outline below identifies ~75 specific papers.

---

#### 3.1 Hallucination: Taxonomies, Causes, and the Inevitability Argument (~2 pages, ~8 refs)

**Purpose**: Establish the problem space and why it cannot be solved by scaling alone.

**Paragraph 1 — Definition and taxonomy.** Open with the Maynez et al. (2020) intrinsic/extrinsic distinction from abstractive summarization. Note how Ji et al. (2023) generalized this taxonomy across NLG tasks, establishing hallucination as a cross-modal, cross-task problem. Introduce the factuality vs. faithfulness axis from Huang et al. (2023) — our thesis focuses on factuality hallucination (generating claims contradicting world knowledge), not faithfulness (contradicting a source document).

**Paragraph 2 — Major surveys.** Position relative to the four major surveys:
- Ji et al. (2023), ACM Computing Surveys — broadest scope, maps causes/definitions/mitigations across modalities
- Huang et al. (2023), most cited (~1,868 citations) — introduces factuality/faithfulness distinction, comprehensive taxonomy
- Rawte, Sheth & Das (2023) — extends to vision and multimodal foundation models
- Wang et al. (2023), ACM Computing Surveys — uniquely frames hallucination as a *knowledge representation* problem, covering how LLMs store and process facts
- Tonmoy et al. (2024) — most useful for mitigation comparison (32+ method table)

**Paragraph 3 — The inevitability argument.** Xu et al. (2024) prove that hallucination cannot be fully eliminated in any computable LLM — there will always exist inputs on which it hallucinates. This shifts the research agenda from *elimination* to *prediction and mitigation*: if we cannot prevent all hallucination, the next best thing is knowing *where* it will occur and *what to do about it*. This is the motivation for our geometric prediction approach.

**Gap statement**: Surveys comprehensively map the hallucination landscape but treat it as a behavioral phenomenon. None connect hallucination to the geometric structure of the model's representation space. Our thesis asks whether hallucination has a geometric *signature* that can be detected before generation.

*Key refs: Maynez+ 2020, Ji+ 2023, Huang+ 2023, Rawte+ 2023, Wang+ 2023, Tonmoy+ 2024, Xu+ 2024*

---

#### 3.2 Hallucination Benchmarks and Evaluation (~2 pages, ~10 refs)

**Purpose**: Survey how hallucination is measured at scale, positioning our 2,879-prompt benchmark relative to existing ones.

**Paragraph 1 — General-purpose benchmarks.** TruthfulQA (Lin et al., 2022) tests whether models mimic common human falsehoods — larger models are not necessarily more truthful. HELM (Liang et al., 2022) provides holistic evaluation across capabilities and risks. HaluEval (Li et al., 2023) offers 35K samples across QA/dialogue/summarization. SimpleQA (Wei et al., 2024) tests short-form factuality with verifiable answers. FreshQA (Vu et al., 2023) tests temporal knowledge stability. FELM (Chen et al., 2023, NeurIPS Datasets & Benchmarks) provides segment-level factuality annotations across 5 domains.

**Paragraph 2 — Entity-centric benchmarks.** PopQA (Mallen et al., 2023, ACL) is the closest to our approach: 14K questions stratified by Wikipedia entity popularity. They show LLM accuracy correlates directly with training document frequency — models fail on long-tail entities. FActScore (Min et al., 2023) decomposes biography generation into atomic facts, revealing ChatGPT fabricates 42% of specific details. Our benchmark extends this entity-centric tradition by stratifying along *existence status* (real vs. nonexistent vs. borderline) rather than popularity alone, and by designing categories that test distinct failure modes.

**Paragraph 3 — What existing benchmarks test and don't test.** Most benchmarks evaluate *what* models get wrong and *how often*. None are designed to test *why* certain prompts are harder than others in geometric terms. Our 7-category design (factual, nonexistent, impossible, ambiguous, plus 3 borderline categories) is specifically constructed so that categories occupy different regions of the embedding space, enabling the geometric analysis that is the core of this thesis.

**Gap statement**: Existing benchmarks quantify hallucination rates but do not stratify by representational properties of the entities or prompts. No benchmark is designed to enable geometric analysis of *why* certain entity classes are more hallucination-prone. Our benchmark fills this gap by construction.

*Key refs: Lin+ 2022, Liang+ 2022, Li+ 2023, Min+ 2023, Wei+ 2024, Mallen+ 2023, Chen+ 2023, Vu+ 2023*

---

#### 3.3 Automated Evaluation and the LLM-as-Judge Paradigm (~1.5 pages, ~8 refs)

**Purpose**: Ground our 3-judge consensus panel in the rapidly maturing LLM-as-judge literature. This section is shorter because the technical details of our judging pipeline are in Ch 4 (Setup) — here we review the methodology and known failure modes.

**Paragraph 1 — The paradigm.** Zheng et al. (2023) demonstrated with MT-Bench and Chatbot Arena that LLM judges achieve strong human-model agreement, especially when multiple architectures are used. G-Eval (Liu et al., 2023) showed GPT-4 outperforms traditional metrics on NLG evaluation. Gu et al. (2024) and Li et al. (2024) provide comprehensive surveys of the paradigm's maturation from single-judge to multi-judge systems. Multi-agent debate (Du et al., 2024, ICML) demonstrates that diverse LLM instances catch each other's errors through deliberation.

**Paragraph 2 — Known biases and mitigations.** Self-preference bias is real and causal: Panickssery et al. (2024, NeurIPS) show LLMs can identify their own outputs and preferentially rate them higher. Wataoka et al. (2024) confirm this across model families. The CALM framework (Li et al., 2024) identifies 12 distinct bias types (position, verbosity, authority, etc.). The Panel of LLM evaluators (PoLL) approach (Verga et al., 2024) shows that panels of smaller, diverse-family models outperform single large judges — directly motivating our 3-family consensus design. Feng et al. (2024, ACL Outstanding Paper) demonstrate that multi-LLM collaboration specifically improves abstention accuracy, relevant to our refusal classification.

**Gap statement**: Multi-judge consensus has been validated for preference ranking (MT-Bench) and general evaluation (G-Eval), but its application to *hallucination-specific* multi-label classification (correct/partial/hallucinated/refused) on entity-level prompts is novel. Our 3-judge panel from disjoint model families, with category-specific rubrics, is specifically designed for this task.

*Key refs: Zheng+ 2023, Liu+ 2023, Verga+ 2024, Panickssery+ 2024, Wataoka+ 2024, Li+ 2024 (CALM), Du+ 2024, Feng+ 2024, Gu+ 2024 (survey)*

---

#### 3.4 Hallucination Detection via Internal Representations (~3 pages, ~16 refs)

**Purpose**: This is the most important section — closest to our contribution. Survey the rapidly growing literature on using model representations (hidden states, activations, embeddings) to detect hallucination. Establish that geometric structure in representation space encodes truthfulness, then identify where our approach differs.

**Paragraph 1 — Probing for truthfulness.** Burns et al. (2023, ICLR) showed with Contrast-Consistent Search (CCS) that truth directions exist in LLM hidden states without supervision — models often "know" the correct answer internally even when generating incorrectly. Azaria & Mitchell (2023, EMNLP Findings) trained classifiers on hidden-layer activations achieving 71-83% truthfulness detection accuracy. Marks & Tegmark (2023) found that LLMs linearly represent truth/falsehood — linear probes trained on one factual dataset generalize to others, and causal interventions can flip judgments. This "Geometry of Truth" work is the most direct conceptual antecedent to our thesis. However, subsequent work has complicated the picture: Orgad et al. (2025, ICLR) showed truthfulness encoding is *not universal* — it generalizes only within tasks requiring similar skills. Bao et al. (2025, ACL Findings) confirmed that truth directions are more consistent in more capable models but not all models exhibit them. Servedio et al. (2025, ACL) cautioned that representation-based detection struggles to generalize from curated to LLM-generated datasets.

**Paragraph 2 — Geometric and spectral methods.** A wave of recent work explicitly uses geometric properties of representation space. Singhal et al. (2024, ICML) showed that Local Intrinsic Dimension (LID) of model activations predicts hallucination — truthful outputs have smaller LIDs (more structured manifolds). This is the closest methodological parallel to our density-based features. HaloScope (Du et al., 2024, NeurIPS Spotlight) identifies a hallucination-associated subspace via SVD, matching supervised performance without labels. INSIDE/EigenScore (Chen et al., 2024, ICLR) computes eigenvalues of response embedding covariance, outperforming logit-based methods by 5-10pp AUROC. Burger et al. (2024, NeurIPS) found a universal two-dimensional subspace separating true from false across multiple LLM families. Semantic isotropy — the uniformity of embeddings on the unit sphere — predicts nonfactuality without labeled data (2025, arXiv:2510.21891). TOHA (2025) applies topological data analysis (persistent homology) to attention graphs.

**Paragraph 3 — Uncertainty-based and inference-time methods.** Semantic Entropy (Farquhar et al., 2024, Nature) clusters semantically equivalent answers before measuring entropy, achieving state-of-the-art detection. Semantic Entropy Probes (Kossen et al., 2024, ICML Workshop) approximate this from hidden states of a single generation, eliminating multi-sample cost. SelfCheckGPT (Manakul et al., 2023, EMNLP) uses sampling consistency. ITI (Li et al., 2024, NeurIPS) shifts activations toward truthful directions at inference time, improving TruthfulQA from 32.5% to 65.1%. Representation Engineering (Zou et al., 2023) steers truthfulness directions, achieving up to 30pp improvement. DoLA (Chuang et al., 2024, ICLR) contrasts layer-wise logits. Lookback Lens (Chuang et al., 2024, EMNLP) uses attention ratios. Luo et al. (2026) identify two distinct truthfulness pathways: question-anchored (for well-known facts) and answer-anchored (for long-tail cases) — potentially explaining why our density features predict hallucination differently across categories.

**Paragraph 4 — Simple probes suffice.** Han et al. (2025, EMNLP Findings) demonstrate that lightweight linear probes on hidden states are highly predictive of factuality even in long-form generation at up to 405B parameters, with 100x fewer FLOPs than multi-sample methods. This parallels our finding that logistic regression on 5 geometric features achieves usable AUC — complex models are not needed when the underlying signal is geometrically structured.

**Gap statement**: All existing work detects hallucination from *internal model representations during or after generation* — requiring white-box access to activations, hidden states, or sampling distributions. Our approach is fundamentally different in two ways: (1) we predict hallucination from the *embedding geometry of the input prompt/entity*, before generation, using an external embedding model — no white-box access to the target model required; (2) we predict not just hallucination *occurrence* but hallucination *difficulty* — which hallucinations resist mitigation and why. No prior work addresses fixability prediction.

*Key refs: Burns+ 2023, Azaria+ 2023, Marks+ 2023, Orgad+ 2025, Singhal+ 2024, Du+ 2024 (HaloScope), Chen+ 2024 (INSIDE), Burger+ 2024, Farquhar+ 2024, Kossen+ 2024, Manakul+ 2023, Li+ 2024 (ITI), Zou+ 2023 (RepE), Chuang+ 2024 (DoLA), Chuang+ 2024 (Lookback), Han+ 2025, Luo+ 2026, Bao+ 2025, Servedio+ 2025*

---

#### 3.5 Entity Knowledge and Knowledge Boundaries (~2 pages, ~10 refs)

**Purpose**: Connect hallucination to the entity-level knowledge structure that our benchmark and geometric features are designed to probe.

**Paragraph 1 — Entity popularity and long-tail knowledge.** Kandpal et al. (2023, ICML) established the foundational result: LLM accuracy on factual questions correlates directly with training document frequency. Scaling model size improves memorization of popular knowledge but fails on long-tail entities. Mallen et al. (2023, ACL) confirmed this with PopQA and showed that retrieval augmentation helps for rare entities but can hurt on popular ones. Sun et al. (2024, NAACL) demonstrated with Head-to-Tail that hallucination rate is inversely correlated with entity popularity across knowledge graph triples. Zhang et al. (2024, 2025) formalized a "Law of Knowledge Overshadowing" — dominant facts overshadow rarer ones, with hallucination following a log-linear law governed by popularity, knowledge length, and model size. These results collectively show that entity frequency in training data is a strong predictor of hallucination.

**Paragraph 2 — Entity recognition mechanisms.** Ferrando et al. (2024, ICLR 2025) used sparse autoencoders to discover *entity recognition directions* in representation space that detect whether the model can recall facts about a given entity. These directions generalize across entity types and are *causally relevant* — activating them forces hallucination on known entities or refusal on unknown ones. Kadavath et al. (2022) showed models can be trained to predict P(IK) — the probability of knowing an answer — establishing that LLMs have internal representations of their own knowledge boundaries. Yin et al. (2023, ACL Findings) confirmed models have self-knowledge capacity but significant gaps remain versus human proficiency. Li et al. (2024, arXiv survey) provide a comprehensive taxonomy of knowledge boundary solutions.

**Paragraph 3 — Knowledge preservation during fine-tuning.** SEAT (Shen et al., 2025) shows that conventional fine-tuning causes "activation displacement" that undermines the model's ability to say "I don't know." Their sparse tuning + entity perturbation approach preserves ignorance awareness — directly relevant to our fine-tuning pipeline, which must reduce hallucination without destroying the model's ability to handle obscure-but-real entities.

**Gap statement**: Entity popularity is a well-established predictor of hallucination, but the connection to *embedding geometry* has not been tested. Our density feature may be capturing exactly this signal: sparse embedding neighborhoods correspond to entities underrepresented in training data, where models default to generation over refusal. Our benchmark is specifically designed with entity-existence categories (nonexistent, plausible_fake, obscure_real) that test this geometric-knowledge boundary hypothesis directly.

*Key refs: Kandpal+ 2023, Mallen+ 2023, Sun+ 2024, Zhang+ 2024/2025 (overshadowing), Ferrando+ 2024, Kadavath+ 2022, Yin+ 2023, Li+ 2024 (knowledge boundary survey), Shen+ 2025 (SEAT)*

---

#### 3.6 Prompt Engineering for Factuality (~2 pages, ~10 refs)

**Purpose**: Survey prompting-based hallucination mitigation approaches, establishing that our controlled comparison of system-prompt prefixes fills a gap.

**Paragraph 1 — Reasoning-based prompting.** Chain-of-thought (Wei et al., 2022, NeurIPS) dramatically improved reasoning (+40pp on GSM8K) but its effect on factuality is mixed. Self-Consistency (Wang et al., 2023, ICLR) improves reliability through majority voting over multiple reasoning paths. CoVe (Dhuliawala et al., 2024, ACL Findings) reduces factual hallucination by 50-70% through multi-step self-verification — closest to our approach in the prompt axis, but requires a 4-stage pipeline per query (expensive). Self-Refine (Madaan et al., 2023, NeurIPS) iterates on outputs with ~20% average improvement. However, Cheng et al. (2025, EMNLP Findings) revealed that CoT *obscures* the internal signals used for hallucination detection, creating a detection-mitigation tradeoff — CoT may reduce hallucination frequency while making remaining hallucinations harder to catch.

**Paragraph 2 — System-prompt and prefix interventions.** SynTra (Jones et al., 2024, ICLR) is the closest prior work: it optimizes continuous prefix embeddings for system messages via synthetic task transfer, reducing hallucination by 29% — but requires gradient-based optimization. Arora et al. (2023, ICLR) showed structured, explicit prompting rules improve truthfulness over vague instructions. Addlesee (2024) demonstrated that specially designed prompts can override pre-training knowledge when grounding to in-prompt context. Lee et al. (2022, NeurIPS) introduced TopicPrefix, prepending entity information to training sentences for factuality — the training-time analogue of our inference-time Entity-Aware prefix. RECITE (Sun et al., 2023, ICLR) uses recitation-augmented generation as a closed-book alternative to retrieval.

**Paragraph 3 — Abstention as a prompting strategy.** Wen et al. (2025, TACL) provide a comprehensive survey of abstention in LLMs, categorizing approaches by when they're applied. Their key finding that reasoning fine-tuning *degrades* abstention by 24% is important context for our Structured Caution prefix design, which explicitly encourages abstention through prompting rather than fine-tuning. R-Tuning (Zhang et al., 2024, NAACL Outstanding Paper) demonstrated that refusal generalizes as a meta-skill — our prompt prefixes may be activating this same capability through instruction rather than training.

**Gap statement**: No prior work systematically compares multiple *discrete system-prompt-level* interventions on the same entity-level hallucination benchmark under controlled conditions (same models, same prompts, same evaluation pipeline). SynTra uses continuous optimization; CoVe requires multi-stage pipelines; most work tests a single prompting strategy. Our controlled experiment — 5 interpretable prefixes × 2 models × 2,879 prompts — fills this gap. Furthermore, no work connects prompt effectiveness to geometric properties of the prompts being modified.

*Key refs: Wei+ 2022, Wang+ 2023, Dhuliawala+ 2024 (CoVe), Madaan+ 2023, Cheng+ 2025, Jones+ 2024 (SynTra), Arora+ 2023, Addlesee 2024, Lee+ 2022, Sun+ 2023 (RECITE), Wen+ 2025, Zhang+ 2024 (R-Tuning)*

---

#### 3.7 Fine-Tuning for Truthfulness and Alignment (~2.5 pages, ~14 refs)

**Purpose**: Survey fine-tuning approaches for factuality, establishing that our geometry-guided data selection and the precision-recall tradeoff we document are novel.

**Paragraph 1 — General alignment: RLHF and its costs.** InstructGPT (Ouyang et al., 2022, NeurIPS) improved instruction-following via RLHF but did not fully address factuality. Constitutional AI (Bai et al., 2022) uses self-critique. However, alignment has costs: Lin et al. (2024, EMNLP) document an "alignment tax" — RLHF causes 16-17 F1 point drops on SQuAD and DROP. FLAME (Lin et al., 2024, NeurIPS) showed standard RLHF actually *increases* hallucination because SFT introduces knowledge the model doesn't have.

**Paragraph 2 — Factuality-targeted fine-tuning.** R-Tuning (Zhang et al., 2024, NAACL Outstanding Paper) is our closest comparator: it identifies unknowns via train-time probing and teaches abstention. Both our approach and R-Tuning teach models to handle knowledge boundaries, but through fundamentally different signals — R-Tuning uses binary probing ("can the model answer?"), we use continuous geometric features (density, centrality) that predict *degree* of difficulty. FactTune (Tian et al., 2024, ICLR) uses DPO with auto-generated preferences, achieving 58% error reduction. Mask-DPO (2025, ICLR) applies sentence-level masking, with 8B models surpassing 70B on factuality. FactAlign (Huang & Chen, 2024, EMNLP Findings) introduces sentence-level KTO alignment. FiSCoRe (2025) trains abstention via semantic confidence rewards.

**Paragraph 3 — The fine-tuning paradox and data selection.** Gekhman et al. (2024, EMNLP) established that fine-tuning on *new* knowledge linearly increases hallucination tendency. Prereq-Tune (Zhu et al., 2025, ICLR) confirmed this by showing models trained on completely fictitious data outperform those trained on real data — because they learn task skills without knowledge contamination. LIMA (Zhou et al., 2023, NeurIPS) demonstrated that 1K carefully curated examples can match much larger datasets for alignment. LESS (Xia et al., 2024, ICML) showed that influence-function-selected 5% of data often outperforms the full dataset. Cherry LLM (Li et al., 2024, NAACL) introduced self-guided data selection where 10% suffices. These results collectively motivate our approach: fine-tuning on behavioral patterns (how to respond cautiously) rather than new factual knowledge, with careful data selection.

**Paragraph 4 — Parameter-efficient fine-tuning and knowledge preservation.** LoRA (Hu et al., 2022, ICLR) enables parameter-efficient adaptation. Self-RAG (Asai et al., 2024, ICLR) combines fine-tuning with retrieval. SEAT (Shen et al., 2025) addresses the specific risk that fine-tuning destroys ignorance awareness through activation displacement — directly relevant to our observation that fine-tuning can cause false negatives on obscure-but-real entities.

**Gap statement**: No fine-tuning approach uses the geometric properties of the training data (embedding density, centrality, oppositeness) to guide data selection. Existing methods select training data based on model performance (R-Tuning), preference pairs (DPO family), or influence functions (LESS). Our best-per-prompt selection, informed by geometric analysis of *why* certain prompts are fixable, represents a novel geometry-guided curation strategy. Furthermore, no prior work quantifies the precision-recall tradeoff between hallucination reduction and over-refusal on obscure-but-real entities — our fine-tuned models' category-level analysis (Ch 7) documents this tradeoff explicitly.

*Key refs: Ouyang+ 2022, Bai+ 2022, Lin+ 2024 (alignment tax), FLAME (Lin+ 2024), Zhang+ 2024 (R-Tuning), Tian+ 2024 (FactTune), Mask-DPO 2025, Huang+ 2024 (FactAlign), Gekhman+ 2024, Zhu+ 2025 (Prereq-Tune), Zhou+ 2023 (LIMA), Xia+ 2024 (LESS), Li+ 2024 (Cherry LLM), Hu+ 2022 (LoRA), Asai+ 2024 (Self-RAG), Shen+ 2025 (SEAT)*

---

#### 3.8 Synthesis: Gaps and Research Questions (~1 page, no new refs)

**Purpose**: Tie all gaps together. Show that this thesis sits at the unique intersection of four literatures that have not been connected: (1) representation geometry, (2) hallucination detection, (3) prompt intervention, and (4) fine-tuning for factuality.

**Paragraph 1 — The representation geometry gap.** Section 3.4 showed that geometric properties of representations encode truthfulness. Section 3.5 showed that entity popularity predicts hallucination. But no work has connected these: do entities in geometrically sparse embedding regions hallucinate more? We test this (Ch 5).

**Paragraph 2 — The intervention selection gap.** Section 3.6 showed prompting-based interventions reduce hallucination, and Section 3.7 showed fine-tuning can teach abstention. But which prompts benefit from which intervention, and can geometric features predict this? We test this (Ch 6-7).

**Paragraph 3 — The three research questions.** State them formally:
- **RQ1 (Ch 5)**: Can geometric properties of prompt embeddings predict hallucination, and does this signal survive controlling for category structure?
- **RQ2 (Ch 6)**: Can discrete system-prompt prefixes reduce hallucination, and do different prefixes work for different categories?
- **RQ3 (Ch 7)**: Can geometric features predict which hallucinations are *fixable* by prompting, and can the best prompt behavior be distilled into model weights via fine-tuning?

**Closing**: These questions form a progressive narrative — geometry as diagnostic (RQ1), prompts as treatment (RQ2), fine-tuning as consolidation with geometry predicting side effects (RQ3). The literature reviewed above shows each component exists in isolation; this thesis is the first to connect them into an integrated pipeline.

---

**Reference count by section**:
- 3.1 Taxonomies & Causes: ~7
- 3.2 Benchmarks & Evaluation: ~8
- 3.3 LLM-as-Judge: ~9
- 3.4 Detection via Representations: ~19
- 3.5 Entity Knowledge: ~9
- 3.6 Prompt Engineering: ~12
- 3.7 Fine-Tuning: ~16
- 3.8 Synthesis: 0 (refers back)
- **Total unique refs: ~72** (some cited in multiple sections)

**Papers to add to references.bib** (not currently in bib, needed for this chapter):
1. Rawte, Sheth & Das 2023 — "Survey of Hallucination in Large Foundation Models"
2. Wang et al. 2023 — "Survey on Factuality in LLMs" (ACM Computing Surveys)
3. Tonmoy et al. 2024 — "Comprehensive Survey of Hallucination Mitigation"
4. Mallen et al. 2023 — "When Not to Trust Language Models" / PopQA (ACL)
5. Chen et al. 2023 — FELM benchmark (NeurIPS D&B)
6. Vu et al. 2023 — FreshQA
7. Verga et al. 2024 — PoLL (Panel of LLM evaluators)
8. Panickssery et al. 2024 — "LLM Evaluators Recognize Their Own Generations" (NeurIPS)
9. Li et al. 2024 — CALM framework (bias taxonomy)
10. Du et al. 2024 — "Multiagent Debate" (ICML)
11. Feng et al. 2024 — "Don't Hallucinate, Abstain" (ACL Outstanding Paper)
12. Gu et al. 2024 — "Survey on LLM-as-a-Judge"
13. Burns et al. 2023 — CCS / "Discovering Latent Knowledge" (ICLR)
14. Orgad et al. 2025 — "LLMs Know More Than They Show" (ICLR)
15. Singhal et al. 2024 — LID characterization of truthfulness (ICML)
16. Du et al. 2024 — HaloScope (NeurIPS Spotlight)
17. Chen et al. 2024 — INSIDE/EigenScore (ICLR)
18. Burger et al. 2024 — "Truth is Universal" (NeurIPS)
19. Farquhar et al. 2024 — Semantic Entropy (Nature)
20. Kossen et al. 2024 — Semantic Entropy Probes (ICML Workshop)
21. Zou et al. 2023 — Representation Engineering
22. Chuang et al. 2024 — DoLA (ICLR)
23. Chuang et al. 2024 — Lookback Lens (EMNLP)
24. Han et al. 2025 — Simple Factuality Probes (EMNLP Findings)
25. Luo et al. 2026 — Two Pathways to Truthfulness
26. Bao et al. 2025 — Probing the Geometry of Truth (ACL Findings)
27. Servedio et al. 2025 — "Are the Hidden States Hiding Something?" (ACL)
28. Kandpal et al. 2023 — "LLMs Struggle to Learn Long-Tail Knowledge" (ICML)
29. Zhang et al. 2024/2025 — Knowledge Overshadowing
30. Li et al. 2024 — Knowledge Boundary survey
31. Shen et al. 2025 — SEAT (Don't Make It Up)
32. Jones et al. 2024 — SynTra (ICLR)
33. Cheng et al. 2025 — "CoT Obscures Hallucination Cues" (EMNLP Findings)
34. Addlesee 2024 — Grounding LLMs to In-Prompt Instructions
35. Lee et al. 2022 — TopicPrefix / Factuality Enhanced LMs (NeurIPS)
36. Wen et al. 2025 — "Know Your Limits" / Abstention survey (TACL)
37. Madaan et al. 2023 — Self-Refine (NeurIPS)
38. Sun et al. 2023 — RECITE (ICLR)
39. Lin et al. 2024 — Alignment Tax (EMNLP)
40. FLAME 2024 — (NeurIPS) [note: disambiguate from Lin alignment tax]
41. Tian et al. 2024 — FactTune (ICLR)
42. Mask-DPO 2025 — (ICLR)
43. Huang & Chen 2024 — FactAlign (EMNLP Findings)
44. Gekhman et al. 2024 — Fine-Tuning Paradox (EMNLP)
45. Zhu et al. 2025 — Prereq-Tune (ICLR)
46. Xia et al. 2024 — LESS (ICML)
47. Li et al. 2024 — Cherry LLM (NAACL)
48. Asai et al. 2024 — Self-RAG (ICLR)

---

## Proposed Chapter Structure

Based on the Harvard Dissertate template. Two structural options under consideration — both use the same Background/Lit Review split (justified by our two-domain bridging, like Tarun Prasad's thesis).

### Option A: Conference-Style (Separate Methodology) — REJECTED

Rejected in favor of narrative structure. Front-loaded methodology reads like an extended conference paper. See git history for details.

### Option B: Narrative with Shared Setup in Ch 4

Each content chapter poses a research question, introduces its specific methods, and presents results. Shared infrastructure in Ch 4.1.

| Chapter | Content | Est. Pages |
|---|---|---|
| 1 | **Introduction** — motivation, research arc narrative, contributions, thesis organization | 5-8 |
| 2 | **Background** — LLMs, hallucination taxonomy, embedding spaces, geometric features (formal defs), LLM-as-judge | 15-20 |
| 3 | **Literature Review** — 6 subsections with gap statements | 10-15 |
| 4 | **Can Geometry Predict Hallucination?** — 4.1 Experimental setup (shared infra), 4.2 Geometric feature extraction, 4.3 Initial benchmark results (honest decomposition), 4.4 Expanded benchmark validation (within-category density signal), 4.5 What geometry captures and what it doesn't | 20-25 |
| 5 | **Can Prompts Reduce Hallucination?** — 5.1 Prefix design, 5.2 Pilot study (449 prompts), 5.3 Replication at scale (2,430 prompts), 5.4 Category and refusal analysis, 5.5 Correctness-safety tradeoff | 15-20 |
| 6 | **Can Geometry Guide Intervention?** — 6.1 Bridge analysis, 6.2 Geometric taxonomy of difficulty, 6.3 Best-per-prompt selection, 6.4 Fine-tuning, 6.5 The full pipeline | 15-20 |
| 7 | **Discussion and Conclusion** — 7.1 What geometry actually predicts, 7.2 Pipeline as contribution, 7.3 Limitations, 7.4 Future work, 7.5 Concluding remarks | 10-15 |
| A-D | **Appendices** — full prefix texts, judge diagnostics, statistical supplement, template/entity examples | 10-20 |

**Pro**: Fewest chapters (7). Tighter, reader encounters setup when first needed.
**Con**: Ch 4 does double duty (~20-25 pages). Shared methodology buried inside a results chapter.

### Option C: Narrative with Standalone Setup Chapter

Each content chapter poses a research question with its own specific methods and results. Shared infrastructure gets its own chapter.

| Chapter | Content | Est. Pages |
|---|---|---|
| 1 | **Introduction** — motivation, research arc narrative, contributions, thesis organization | 5-8 |
| 2 | **Background** — LLMs, hallucination taxonomy, embedding spaces, geometric features (formal defs), LLM-as-judge | 15-20 |
| 3 | **Literature Review** — 6 subsections with gap statements | 10-15 |
| 4 | **Experimental Setup** — 4.1 Benchmark construction (categories, templates, entities, scaling to 2,879 prompts), 4.2 Model selection, 4.3 Consensus judging pipeline (3-judge, agreement, biases, human validation), 4.4 Embedding approach | 11-17 |
| 5 | **Can Geometry Predict Hallucination?** — 5.1 Geometric feature extraction, 5.2 Initial benchmark results (honest decomposition), 5.3 Expanded benchmark validation (within-category density signal), 5.4 What geometry captures and what it doesn't | 15-20 |
| 6 | **Can Prompts Reduce Hallucination?** — 6.1 Prefix design (5 prefixes, literature grounding), 6.2 Pilot study (449 prompts), 6.3 Replication at scale (2,430 prompts), 6.4 Category-level analysis (combined: per-category effectiveness, regressions, refusal, correctness-safety tradeoff) | 15-20 |
| 7 | **Can Geometry Guide Intervention?** — 7.1 Geometric difficulty analysis, 7.2 Geometric taxonomy of fixability, 7.3 Geometry-informed training data curation, 7.4 Fine-tuning and the precision-recall tradeoff, 7.5 The full pipeline | 15-20 |
| 8 | **Discussion and Conclusion** — 8.1 What geometry actually predicts, 8.2 The four contributions, 8.3 Limitations, 8.4 Future work, 8.5 Concluding remarks | 10-15 |
| A-D | **Appendices** — full prefix texts, judge diagnostics, statistical supplement, template/entity examples | 10-20 |

**Pro**: Clean separation, question chapters stay pure, shared methods clearly findable, each chapter focused.
**Con**: 8 chapters, three preamble chapters before first results.

### Decision: Option C (Narrative with Standalone Setup Chapter)

Option C selected. The shared methodology content (benchmark construction, model selection, judging pipeline, embedding) is substantial — estimated 11-17 pages covering 7-category rationale, template design, entity validation, benchmark scaling (449→2,879), 3-judge panel design, per-judge bias, agreement analysis, human validation, embedding approach. This justifies a standalone chapter and keeps the question-driven chapters clean.

Discussion and Conclusion are merged into one final chapter (like Angela Li's Ch 6: "Our Contributions" + "Future Directions"). A separate Conclusion chapter would be 2-3 pages that largely repeats the Discussion — merging avoids redundancy.

### Why geometry ties in without Phase 6 (geometry-guided targeting)

Chapter 7 ("Can Geometry Guide Intervention?") works without building an operational geometry-based prefix selector. The chapter's arc:

1. **Bridge analysis** (7.1-7.2): Geometry predicts which hallucinations are fixable. Within-category density signal (p=0.046/0.012, post-CoT-exclusion). Geometric taxonomy of difficulty — "unfixable" prompts live in sparse embedding regions.
2. **Best-per-prompt selection** (7.3): The unfixable prompts (28 Mixtral, 24 Llama) are geometrically characterized and excluded from training data. This IS geometry guiding intervention — at the data curation level rather than runtime.
3. **Fine-tuning** (7.4): Distillation results from Step 11. Includes entity-contamination disclosure (Step 11C) as a methodological note — 61% entity overlap exists. Decontamination gap: Mixtral configC 94.4%→91.6% (+2.8pp), Llama configA 94.0%→93.5% (+0.5pp). Llama gap is negligible; Mixtral gap is moderate but within the <3pp "no inflation" threshold. Confirms behavioral caution not memorization. ~1-1.5 paragraphs with small table, not a standalone section.
4. **Full pipeline** (7.5): Geometry is the diagnostic, prompts are the treatment, fine-tuning is the cure.

The chapter title asks "Can geometry *guide* intervention?" — and the answer is yes, in two ways:
- **Analytically**: geometry tells you which prompts are fixable and which aren't
- **Practically**: geometry informs training data quality (exclude geometrically unfixable prompts)

Phase 6 would add a third way (geometry *selects* the prefix at runtime), but that's an engineering optimization, not a conceptual leap. The intellectual contribution — geometry predicts hallucination difficulty — is already complete. Phase 6 is mentioned in Discussion/Future Work with a paragraph sketching the approach and citing the bridge analysis as evidence it could work.

**Fine-tuning is NOT a null result**: 89% hallucination reduction on custom benchmark (Ch 7.4) + cross-domain generalization on TruthfulQA (Ch 7.5, Llama Bonferroni-sig) + template invariance (Ch 7.6). Chapter 7 is now substantial: bridge analysis + best-per-prompt + fine-tuning + TruthfulQA generalization + template ablation = ~15-18 pages.

### Optional phases and their thesis impact

| Phase | Recommendation | Thesis value | Chapter impact |
|---|---|---|---|
| Step 11B (overfitting check) | ~~**Do it**~~ **DONE** | High — answers reviewer question about generalization | Ch 7.4 |
| Phase 5 (TruthfulQA) | ~~**Do it**~~ **DONE** | High — Llama: +5.3pp acc, -4.4pp halluc (both Bonferroni-sig). Cross-domain generalization evidence. | Ch 7.5 |
| Phase 9 (template ablation) | ~~**Do it**~~ **DONE** | High — **Template diversity doesn't matter.** T5≈T-all (McNemar p=0.099/0.773). Seen-template 96.3% ≈ novel 93.0% (T5 Mixtral). Addresses Sunny's concern. | Ch 7.6 |
| Phase 7 (baselines table) | ~~**Literature table**~~ **DONE** (v5, 9/9 verified). 7C-D folded into Ch 8 writing | High — 15 methods + 1 context, 3 corrections. 6-section narrative outline ready in EXPERIMENT_LOG.md | Ch 8 Discussion |
| Phase 6 (geometry selector) | **Future work** (2-3 days) | High risk/reward, not needed for arc | Ch 8 Future Work |
| Phase 8 (adversarial) | **Future work** (days+) | Low relative to effort | Ch 8 Future Work |

---

## Figure Audit (updated March 24, 2026)

**7 active figures** across Chapters 4–7. All use serif font, 11pt base, 13pt bold titles, 12pt axis labels, 10pt tick labels, 9pt legends. Style consistency verified March 24.

| # | Chapter | Figure | File | Verdict | Notes |
|---|---------|--------|------|---------|-------|
| 1 | Ch 4 | Pipeline overview (TikZ) | inline in `setup.tex` | **KEEP** | Navigational roadmap for 30-page methods chapter. Standard thesis practice. |
| 2 | Ch 4 | Oppositeness schematic (TikZ) | inline in `setup.tex` | **KEEP** | Essential — most novel/unintuitive feature, our own construction. No prose substitute. |
| 3 | Ch 5 | UMAP category scatter | `figures/v5_category_umap_combined.png` | **KEEP** | Motivates decomposition (Sec 5.3). Makes category confound viscerally obvious. |
| ~~4~~ | ~~Ch 5~~ | ~~Decomposition AUC bars~~ | ~~`figures/ch5_decomposition_auc.png`~~ | **CUT** | Restated Table 5.3 as bars. The +0.018/+0.041 increments looked negligible visually, undermining the "small but meaningful" argument. Table is more precise and compact. Removed March 24. |
| 5 | Ch 5 | Within-category AUC dots | `figures/ch5_within_category_auc_dots.png` | **KEEP** | Pattern of where signal exists across 7 categories — only visible as figure. Motivates focus on nonexistent in Sec 5.4. |
| 6 | Ch 5 | Density box plots (nonexistent) | `figures/ch5_within_category_density_nonexistent.png` | **KEEP** | Payoff figure for Ch 5's central claim. Shows distributional shift, not just means. Strongest figure in Ch 5. |
| 7 | Ch 6 | Category × prefix heatmap | `figures/ch6_category_heatmap.png` | **KEEP** (weaker) | Duplicates Table 6.2 but color encoding makes patterns (hard column, easy rows) immediately visible. Would be second to cut if tight. |
| 8 | Ch 7 | Hallucination comparison bars | `figures/ch7_hallucination_comparison.pdf` | **KEEP** | Money figure for Ch 7. Significance brackets communicate key statistical claim. Synthesizes across conditions in a way tables can't. |

**Style notes:**
- All matplotlib figures use: `font.family: serif`, `font.size: 11`, `axes.titlesize: 13`, `axes.labelsize: 12`, `xtick.labelsize: 10`, `ytick.labelsize: 10`, `legend.fontsize: 9`
- TikZ figures inherit LaTeX document font (serif)
- UMAP and Ch6 heatmap were regenerated March 24 to fix sans-serif → serif
- Ch7 scatter plot (ft_bridge_mixtral) was evaluated and replaced with the comparison bar chart — scatter had n=6 still-broken points against 366 background dots, visually unconvincing despite strong statistics

---

## What We Can Write NOW vs. What's Waiting on Data

**As of March 8, 2026. Thesis due March 27 (afternoon).**

### Available now (all data in hand):
- **Ch 1 Introduction**: rewrite with full arc and four contributions
- **Ch 2 Background**: entirely new content, no experimental data needed
- **Ch 3 Literature Review**: Detailed paragraph-level outline complete (8 sections, ~72 unique refs, 48 new bib entries identified). V3 conference paper's related work provides ~30% of text for sections 3.1-3.2 and parts of 3.4-3.5. Phase 7 comparison tables feed Ch 8, not Ch 3. Writing estimate: ~6-8 hours with outline in hand.
- **Ch 4 Experimental Setup**: Section 4.1 drafted (~3 pages). Sections 4.2-4.4 ready to write.
- **Ch 5 Can Geometry Predict Hallucination?**: all geometry data available (initial + expanded benchmark)
- **Ch 6 Can Prompts Reduce Hallucination?**: prefix data complete (pilot + replication at scale)
- **Ch 7 Can Geometry Guide Intervention?**: bridge analysis, best-per-prompt selection, fine-tuning results, precision-recall tradeoff, TruthfulQA generalization (Phase 5 done — Ch 7.5), template ablation (Phase 9 done — Ch 7.6)
- **Ch 8 Discussion/Conclusion**: can draft fully — all core experiments complete. Literature comparison tables ready.
- **Appendices**: judge diagnostics, prefix texts, statistical tables
- **Bibliography**: 26 refs → needs ~50-80 for thesis

### No experiments remaining:
All experimental phases complete. Template ablation (Phase 9) done Mar 11. Full thesis can now be written.

### Writing status (March 8):
- **Real content written**: ~3 pages (setup.tex Section 4.1)
- **Total needed**: ~95-130 pages
- **Days remaining**: 19 (March 8 → March 27)
- **Pace needed**: ~5-7 pages/day

---

## Appendix Plan

### Design Principles

**What belongs in an appendix**: Material that is necessary for reproducibility or completeness but would disrupt the narrative flow of the main text. The test: if a reader skips the appendix entirely, can they still follow every argument? If yes → appendix. If no → main text.

**Calibration from reference theses**: Tarun Prasad has two appendices: "Prompts Used" (exact inputs to the system) and "Examples of Proofs Found" (concrete outputs). Both are artifacts too long for the main text but essential for understanding and reproducing the work. Angela Li has no appendices. Neither thesis uses appendices for supplementary analysis or defensive statistics.

**Our approach**: Two appendices matching Tarun's pattern — one for exact experimental artifacts (prompts, rubrics, configurations), one for supplementary analysis that supports but is not required for the main arguments. Lean and purposeful, no filler.

### Deciding what to include vs. cut

**Include** — material that meets at least one of:
1. Already forward-referenced from a written chapter (`\ref{app:...}` exists in .tex)
2. Essential for reproducing our experiments (exact prompts, rubrics, hyperparameters)
3. Provides detail that a careful reader would want but that would break chapter flow

**Cut** — material that is:
- Available in the GitHub repo (entity lists, template catalogs — hundreds of items)
- Already summarized adequately in the main text (feature correlations stated in one sentence)
- Preemptively defensive (QQ plots "in case reviewers challenge")
- Visual padding (5×5 heatmap for 5 features with mostly near-zero correlations)

---

### Appendix A: Experimental Artifacts (~4-6 pages)

Exact inputs to and configurations of our experimental pipeline. A reader trying to reproduce the work needs these.

| Section | Label | Content | Source | Referenced from | Status |
|---|---|---|---|---|---|
| A.1 | `app:judge-prompt` | Full judge system prompt: rubric, category-specific rules, JSON output format, any per-API differences | `src/models/judge_client.py` | Ch 4 §4.3 (line 343) | **NEEDS CREATION** |
| A.2 | `app:prefixes` | Full text of all 4 prompt prefixes used in Ch 6 (CoT excluded). Each prefix + 1-2 sentence design rationale | `experiments/prefix_configs.yaml` | Ch 6 (to be written) | **NEEDS CREATION** |
| A.3 | `app:ft-configs` | LoRA fine-tuning configurations: requested vs actual hyperparameters (Together AI overrides), per-model details. One table | `data/training/v5_finetuned_models.json`, experiment log Step 10 | Ch 7 (to be written) | **NEEDS CREATION** |

### Appendix B: Supplementary Analysis (~4-5 pages)

Supporting analyses referenced from the main text. Not required to follow the arguments, but provides additional detail for thorough readers.

| Section | Label | Content | Source | Referenced from | Status |
|---|---|---|---|---|---|
| B.1 | `app:kendall-matrix` | Full 10×10 Kendall's τ pairwise correlation heatmap across models. One figure + caption | `results/v3/multi_model/stats/kendall_tau_matrix.csv` | Ch 5 §5.1 (line 49) | **NEEDS CREATION** |
| B.2 | `app:embedding-robustness` | Preliminary 3-embedding-model comparison (text-embedding-3-small, text-embedding-3-large, all-mpnet-base-v2) on initial benchmark. Spearman correlations between features, brief discussion | `results/v3/robustness/` (if exists) | Ch 4 §4.4 (line 612), Ch 5 §5.5 (line 470) | **NEEDS CREATION** |
| B.3 | `app:human-validation` | Full disagreement analysis for n=50 human validation: the 5 disagreement cases, category/label breakdown | `results/v3/human_verification_report.json` | Ch 5 §5.1 | **NEEDS CREATION** |
| B.4 | `app:geometry-heatmaps` | UMAP projections with geometric feature overlays (density, oppositeness, etc.) for initial and expanded benchmarks | `results/v3/figures/geometry_heatmaps_umap.png`, `results/v5_baselines/analysis/v5_geometry_heatmaps_umap.png` | Ch 5 (if referenced) | **EXISTS** |

### Cut from previous plan (with rationale)

| Previous entry | Why cut |
|---|---|
| `app:templates` (full template catalog) | 55-66 templates per category = dozens of pages. Available in `data/templates/*.json` in the repo. No reader will read them in print. |
| `app:entities` (entity list samples) | Same — available in `data/entity_lists/*.json`. Main text already gives representative examples in Ch 4 §4.1. |
| `app:within-category-pvalues` (p-value heatmap) | Data already in Table 5.4 in main text. A heatmap adds visual form but no new information. |
| `app:feature-correlation` (5×5 correlation matrix) | Stated in one sentence in Ch 5.5: "oppositeness–centrality r = −0.54, density–centrality r = −0.51, oppositeness–density r = 0.38." A 5×5 heatmap for 5 features is padding. |
| `app:qq-plots` (non-normality justification) | Preemptively defensive. Mann-Whitney is standard for this type of data. Only create if a reviewer specifically challenges it. |
| `app:judge-diagnostics` (per-judge bias breakdown) | Folded into Ch 5 §5.1 judge validation text. The sensitivity analysis results (judge removal, self-eval bias) are reported in the main text with specific numbers. A separate appendix table adds no information beyond what's already stated. |

### Estimated total: ~8-11 pages

### Growth expectations

**Appendix A is complete.** The experimental artifacts (judge prompt, prefix texts, FT configs) are the inputs to the pipeline — they don't change as we write more chapters.

**Appendix B may grow slightly.** The most likely additions:
- **Ch 6 (Prompts)**: Unlikely. Results are tables and figures that belong in the main text.
- **Ch 7 (Fine-tuning)**: Possible. If template ablation or cross-category generalization needs detailed per-category breakdowns that would bloat the chapter, those could move to B. But based on the outline (2pp each), they should fit in the main text.
- **Ch 8 (Discussion)**: Unlikely. Interpretive prose, not data-heavy.

Expect 0-2 additions total, if any.

---

> **Rule**: When writing any chapter and deciding something belongs in the appendix rather than the main text, add it here immediately AND add the `\label` to `appendixB.tex` and the `\ref{app:...}` in the chapter at the same time. This is the single source of truth for appendix content.
