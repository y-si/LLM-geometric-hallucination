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

**Ranking (honest)**: D > F > G > A > E > B > C. Simpler title = more confident work. D doesn't need a metaphor to sell it.

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

## Writing Progress (updated March 12, 2026)

| Chapter | Status | Est. Pages | Notes |
|---|---|---|---|
| Ch 4 Experimental Setup | **DONE** (opening para + flow pass remaining) | 15-18 | Sec 4.1-4.4 + closing written |
| Ch 5 Can Geometry Predict? | **Outlined** — ready to write | 15-20 | All data ready. 6 sections planned |
| Ch 6 Can Prompts Reduce? | Not started | 15-20 | All data ready |
| Ch 7 Can Geometry Guide? | Blocked on Phase 10 judging | 15-20 | Phase 9 ablation DONE. Phase 10 (cross-cat) judging in progress |
| Ch 2 Background | Not started | 15-20 | LLMs, hallucination, embeddings, geometry, LLM-as-judge |
| Ch 3 Literature Review | Draft exists (v3_paper.tex) | 10-15 | 6 subsections + Phase 7 comparison tables (v5, verified) |
| Ch 1 Introduction | Not started | 5-8 | Full arc + four contributions. Write after results chapters. |
| Ch 8 Discussion & Conclusion | Not started | 10-15 | Write last — needs all results |
| Bibliography | Draft exists (references.bib) | — | 26 entries → needs ~50-80 |
| Appendices | Not started | 10-20 | Judge diagnostics, prefix texts, stats supplement |
| **TOTAL** | **Ch 4 done** | **~95-130** | **Due March 27** |

### Writing order (decided Mar 12, 2026)

1. ~~**Ch 4 Experimental Setup**~~ — DONE
2. **Ch 5 Can Geometry Predict?** — first results chapter, all data ready, no Phase 10 dependency
3. **Ch 6 Can Prompts Reduce?** — builds on Ch 5 baseline, all data ready
4. **Ch 7 Can Geometry Guide?** — bridges Ch 5 + Ch 6, needs Phase 10 results (should be done by then)
5. **Ch 2 Background** — contextual, can write in parallel if blocked on anything
6. **Ch 3 Literature Review** — has v3 draft, needs expansion with Phase 7 comparison tables
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
- Centrality is inconsistent: not significant for Mixtral (p = 0.079) but significant for Llama (p = 0.0003). Moreover, the direction for Llama (hallucinated prompts have LOWER centrality = closer to corpus mean) is the opposite of what the V3 analysis found (higher centrality = farther from mean). This reversal will be explained in Section 5.3.
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

**Purpose**: The critical methodological section. Honestly decompose how much of the geometric prediction is just category structure.

**Content**:
- **Category-only baseline**: Logistic regression with 6 category dummies (one-hot) → CV AUC = 0.774 (Mixtral), 0.769 (Llama). Category alone is a strong predictor. This is unsurprising — we designed categories to span a difficulty spectrum.
- **Category + geometry**: CV AUC = 0.792 (Mixtral), 0.813 (Llama). Geometry adds +0.018 to +0.044 AUC beyond category.
- **Table 5.3**: Comparison of three models (geometry-only, category-only, category+geometry) with CV AUC and SEs.
- **Interpretation**: Geometry's predictive power largely operates *through* category structure. The between-category geometric differences (lower density in borderline categories, higher oppositeness) are real but reflect the same underlying phenomenon: some types of prompts are harder, and this hardness shows up both in category labels and in embedding geometry.
- **Why this is NOT a negative result**: (a) Category structure *is* geometric — the embedding space naturally separates easy from hard prompts. (b) The +0.02-0.04 AUC increment means geometry captures *some* within-category variation beyond labels. (c) The real test is within-category analysis (next section).
- **V3 → V5 reconciliation**: V3's AUC of 0.86 combined both signals without separation (only 2 categories with enough hallucinations, no cross-validation). V5 decomposes cleanly. Frame as scientific progress, not contradiction. "Initial results on a smaller dataset suggested strong predictive power (AUC = 0.86); the expanded benchmark reveals that most of this signal reflects category structure, with a more modest but genuine within-category component."

**Reviewer anticipation**:
- "So geometry barely helps beyond category labels?" → Yes, overall. But (1) this measures *aggregate* additional signal — within specific categories it's stronger. (2) The category structure itself is a geometric finding — categories were defined semantically, not geometrically. The embedding space independently discovers the difficulty gradient. (3) The within-category signal, while modest for prediction, is novel and theoretically interesting.
- "Why not just use category labels?" → For practical deployment, category labels aren't available for arbitrary queries. Geometry provides a label-free difficulty estimate.

**Tables/Figures**:
- **Table 5.3** (essential): AUC comparison — three rows (geometry-only, category-only, category+geometry) × two models. Simple, high-impact.
- **Figure** (recommended): Grouped bar chart showing the three AUC values side-by-side for each model. Makes the category dominance and geometry's marginal contribution immediately visual. Needs creation — no existing file.
- **Figure** (optional): UMAP/t-SNE of corpus colored by category, showing geometric clustering. Existing: `results/v3/figures/category_manifolds_umap.png` and `_tsne.png`. These are from V3 (449 prompts only) — may want to regenerate on the full 2,879 corpus, or use as-is with a note. Good for showing that categories occupy distinct geometric regions.

### 5.4 Within-Category Analysis (~3-4 pages)

**Purpose**: The core finding. Show that geometry predicts hallucination *within* categories, controlling for the category confound. This is the non-circular, novel result.

**Content**:
- **Table 5.4**: Within-category Mann-Whitney results. For each of the 7 categories: N, hallucination rate (Mixtral/Llama), density p-value, oppositeness p-value, best within-category CV AUC.
  - Source: `results/v5_baselines/analysis/v5_geometry_prediction_within_category.csv`
- **The density finding in nonexistent prompts**: Among 600 nonexistent prompts, density significantly predicts hallucination. p < 0.0001 for both models, effect size r ≈ 0.25. Hall_mean density lower than correct_mean density. Within-category CV AUC = 0.665 (Mixtral), 0.678 (Llama).
  - Interpretation: Among prompts about things that don't exist — all the same type, all asking the same kind of question — the ones with sparser embedding neighborhoods (fewer similar prompts nearby) are more likely to hallucinate. This cannot be explained by category membership.
  - Why nonexistent? Largest category (600), highest hallucination rate (19-30%), most statistical power. The signal is real where we can detect it.
- **Other categories**: Borderline_plausible_fake shows oppositeness signal (Llama p=0.008). Impossible shows density (Mixtral p=0.014). Factual shows oppositeness (Llama p=0.044). Ambiguous has too few hallucinations (<2%) to test. Pattern: density is the most consistent within-category predictor; other features are category-specific.
- **Multiple testing**: Report both uncorrected and Bonferroni-corrected p-values. With 5 features × 7 categories × 2 models = 70 tests, Bonferroni threshold is 0.05/70 = 0.0007. Density in nonexistent survives (p < 0.0001). Other findings don't survive Bonferroni — note honestly. These may be real but underpowered.

**Figures**:
- Box plots: density distribution for hallucinated vs. correct prompts within nonexistent category (both models). This is the hero figure of the chapter.
  - Existing: `results/v5_baselines/analysis/v5_within_category_*.png`
- Possibly: summary heatmap of p-values across features × categories

### 5.5 Feature-by-Feature Summary (~1-2 pages)

**Purpose**: Synthesize which features matter and which don't, comparing V3 initial findings with V5 controlled results.

**Content**:
- **Table 5.5**: Feature summary table. Columns: Feature, V3 Finding, V5 Between-Category, V5 Within-Category, Assessment.
  - Source: experiment log "Summary: Which features actually matter?" table
  - **Density**: Not emphasized in V3 → predicts hallucination AND fixability within categories → **the real geometric signal**
  - **Oppositeness**: Not in V3 → strongest overall discriminator (p<1e-10) → strong but partly between-category
  - **Centrality**: Strongest in V3 (OR=0.027) → weak, inconsistent across models → **downgraded** (was proxying category)
  - **Curvature**: Second in V3 (OR=0.300) → weak, near-zero coefficient → **downgraded**
  - **Local ID**: Not in V3 → near-zero coefficient, r=-0.97 correlated with curvature → **redundant**
- **The honest story**: "Two of the five features (density, oppositeness) carry genuine predictive signal. Centrality and curvature, which dominated initial results on a smaller dataset, appear to have been proxying for category membership. This is a cautionary finding about small-dataset geometric analyses: when categories have both different hallucination rates and different geometric properties, regression conflates the two."
- **Local_id–curvature correlation**: Both depend on the same k-NN neighborhood. Curvature uses local_id to determine PCA dimensionality. Their near-perfect anticorrelation makes them statistically redundant. Future work could drop one.

**Tables/Figures**:
- **Table 5.5** (essential): Feature evolution table — the centerpiece of this section. 5 rows × 4 columns. Compact but information-dense.
- **Figure** (optional): Feature correlation matrix (5×5 heatmap) showing local_id–curvature anticorrelation. Would support the redundancy claim visually. Needs creation — check if `analyze_v5_geometry_prediction.py` already computes this.

### 5.6 Discussion (~1-2 pages)

**Purpose**: Interpret the findings, acknowledge limitations, and set up Chapters 6-7.

**Content**:
- **What geometry captures**: Two-level prediction — category-level (where in the embedding space) and within-category (fine-grained density). The embedding space naturally encodes a "difficulty gradient" that aligns with hallucination risk.
- **Why density?** Intuition: sparse neighborhoods = less similar training data = model has fewer examples to draw on = more likely to fabricate. This aligns with entity popularity findings (Sun et al. 2024) and knowledge entanglement theory (Ferrando et al. 2024).
- **Why external embeddings work at all**: The question text alone — not the model's internal processing — carries enough geometric signal to predict hallucination. This is a stronger-than-expected finding, suggesting hallucination risk is partly a property of the question, not just the model.
- **Limitations specific to this chapter**:
  - Self-reference corpus dependency (adding prompts changes all features)
  - Single embedding model (text-embedding-3-large)
  - Within-category signal concentrated in nonexistent (largest, highest hallucination rate) — other categories underpowered
  - Effect sizes are modest (r ≈ 0.25 for density, CV AUC 0.67 within nonexistent) — not a silver bullet
  - Cross-model consistency untested at within-category level (only 2 models on expanded benchmark)
- **Forward references**: "The natural next question is whether these geometric features can guide *intervention*. Can we reduce hallucination by prompting models differently? And if so, does geometry predict where interventions succeed? Chapters 6 and 7 address these questions." (NO SPOILERS about prefix effectiveness or AUC values)

**Tables/Figures**: No new tables or figures in 5.6 — this is interpretive prose. References figures/tables from earlier sections as needed.

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

## Framing: Contributions Are Ideas, Not Pipeline Steps

> **Lesson from reference theses** (Angela Li, Tarun Prasad): The main contributions of a thesis are the theoretical ideas and findings — not the engineering work that produced them. Angela's contribution is mathematical derivations. Tarun's is the lemma extraction *technique*. Neither says "I ran a pipeline." Both say "here is a new way of thinking about X."
>
> Our fine-tuning pipeline is the *method*, not the *finding*. The thesis should be framed around **what we learned about hallucination**, not the engineering that got us there.

### The Four Contributions (ordered by novelty)

1. **Geometric structure predicts hallucination *difficulty*, not just occurrence.** The bridge analysis shows embedding geometry predicts where interventions work (within-category density, p<0.05) and where they fail. "Unfixable" prompts cluster in high-centrality, low-density regions. Prior work asks "will this model hallucinate?" — we ask "is this hallucination fixable?" and show the answer is geometric.

2. **Within-category embedding density is the real geometric signal.** Cross-category prediction (AUC=0.97 in initial study) is largely confounded by category structure. The honest, non-circular finding: within a single category (controlling for prompt structure), density distinguishes hallucinating from non-hallucinating prompts (p<0.0001). The model's local neighborhood sparsity matters.

3. **The precision-recall structure of learned caution.** Fine-tuning teaches a "skepticism heuristic" that massively reduces hallucination on nonexistent entities (70%→98%) but causes false negatives on obscure-but-real entities (-7 to -13%). This reveals that hallucination reduction and knowledge coverage are fundamentally in tension — and the tension is predictable from geometry (density distinguishes obscure-real from plausible-fake).

4. **Careful prompt behavior can be distilled into weights.** LoRA fine-tuning on best-per-prompt curated data matches the best prompt prefix (91.1%, p=0.84) without any runtime prompt engineering. The "careful behavior" is learnable, not just promptable — a methodological contribution showing prompt engineering can be a stepping stone to permanent model improvement. Template ablation (Ch 7.6) further shows the model learns behavioral caution, not template-specific patterns: 5 templates perform indistinguishably from all ~194 (McNemar p=0.099/0.773), and accuracy on seen vs novel templates is comparable (T5 Mixtral: 96.3% seen vs 93.0% novel).

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

## Content Expansion Guide: Conference Paper → Thesis

The core shift: the conference paper oversells geometry as a standalone predictor. The thesis tells the honest, more interesting story — geometry *explains category structure*, provides *modest within-category signal*, and most importantly *predicts which hallucinations are resistant to mitigation*.

### Introduction — Needs a Real Narrative Arc

The current intro is fine for a conference paper but reads as a pitch. A thesis intro should:

- **Motivate the problem more deeply** — why hallucination specifically matters *now* (not just "medical/legal harm"), with concrete examples of real-world failures
- **Tell the story of the research journey** — "We initially hypothesized X, found Y, which led us to investigate Z." The thesis should read as an intellectual narrative, not a sales pitch
- **Preview all four contributions** — use the numbered list above. Frame them as intellectual findings, not pipeline steps
- **Drop the Theory of Change section** — that was a class requirement. The safety motivation should be woven into the intro naturally, not be its own section

### Literature Review — Mostly Done, Needs Positioning

The expanded Literature Review (6 subsections, 26 refs) is conference-quality. For the thesis:

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

**Prefix Pilot Study (Ch 6.2, new, ~3 pages)**:
- 449 prompts x 5 prefixes x 2 models = 4,490 responses
- All prefixes significantly reduce hallucination (p<0.002)
- Entity-Aware best for Mixtral (11.8%→0.67%), Structured Caution best for Llama (5.8%→0.45%)
- Best-per-prompt selection: Mixtral 91.1%→95.5%, Llama 93.3%→98.0%

**Replication at Scale (Ch 6.3, new, ~5 pages)**:
- 2,430 prompts x 5 prefixes x 2 models = 24,300 responses (24,299 judged)
- **Pilot pattern replicates at 5x scale**: Entity-Aware best for Mixtral (14.8%→4.7%), Structured Caution best for Llama (9.7%→3.0%). All significant (p<0.001).
- ~~**CoT Verification is catastrophic**~~: INVALIDATED — 62-68% refusal rate was API failure artifact (GPT-5.1 quota + Claude auth failures), not model behavior. Real refusal rate <1%. CoT excluded from thesis entirely.
- **Expanded benchmark rates are higher** (Mixtral Entity-Aware: 0.7% pilot → 4.7% at scale). Expected — new prompts probe harder entity regions. Evidence pilot results weren't artifacts.

**Geometric Difficulty Analysis (Ch 7.1-7.2, new, ~5 pages)**:
- Pilot study bridge: geometry predicts fixability, AUC=0.86 (train-only on 449 prompts)
- Expanded benchmark bridge: aggregate AUC drops to 0.59-0.66 (cross-validated), a class imbalance artifact (333 fixed vs 15 still_broken for Mixtral, 227 vs 5 for Llama)
- **Within-category density is the robust finding**: among nonexistent prompts, density significantly predicts fixability for both models (p=0.034, p=0.047). Unfixable prompts live in sparser embedding regions. Non-circular (same category, same structure, geometry varies).
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
- **Config selection explanation**: configC was best on held-out test set (91.1% accuracy); determined before seeing TruthfulQA results (pre-registered). State: "We test the best-performing configuration per model as determined by held-out evaluation (Section 7.4), selecting before observing TruthfulQA results."
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

### Discussion — Needs Complete Rewrite

The current discussion has good ideas (outlier hypothesis, flat manifold paradox) but frames them overconfidently. The thesis discussion should be organized around the four contributions:

- **Contribution 1 — Geometric difficulty prediction**: Lead with the bridge analysis finding. Within-category density predicts fixability (p=0.034/0.047 for nonexistent prompts). "Unfixable" prompts cluster in sparse embedding regions. This is the most novel finding — prior work asks "will this hallucinate?" but not "is this hallucination fixable?"
- **Contribution 2 — Density as the honest geometric signal**: "We initially found AUC=0.86, but proper cross-validated analysis shows geometry adds +0.02-0.04 beyond category structure. The flat manifold paradox (curvature beta=-1.21 in initial study) doesn't replicate — curvature is essentially useless as a predictor. The real finding is within-category density (p<0.0001). This connects to the sparse void hypothesis: hallucinations occur where entities sit in sparse neighborhoods."
- **Contribution 3 — Precision-recall tradeoff in learned caution**: Fine-tuning teaches "entity skepticism" that dramatically reduces hallucination on nonexistent entities (70%→98%) but causes false negatives on obscure-real entities (-7 to -13%). This reveals hallucination reduction and knowledge coverage are in tension. Geometry predicts which side of this tradeoff a prompt falls on (density distinguishes obscure-real from plausible-fake).
- **Contribution 4 — Prompt distillation into weights**: Fine-tuning matches best prefix accuracy (91.1%, p=0.84) without runtime prompt engineering. The practical implication: prompt engineering is not just a band-aid — it can be a data generation strategy for permanent model improvement. Three convergent lines of evidence confirm the model learned general epistemic caution, not surface patterns: (1) TruthfulQA cross-domain transfer (Llama -4.4pp halluc on misconceptions, Bonferroni-sig); (2) template ablation shows 5 templates ≈ all ~194 (p=0.099/0.773), with seen-template and novel-template accuracy comparable (T5 Mixtral: 96.3% seen vs 93.0% novel); (3) entity decontamination gap is small (Llama configA: 94.0%→93.5% clean, +0.5pp; Mixtral configC: 94.4%→91.6% clean, +2.8pp — near but under the 3pp inflation threshold). The no-over-caution finding on TruthfulQA also refines Contribution 3: the precision-recall tradeoff is domain-specific to entity fabrication, not a blanket personality change.
- ~~**CoT Verification failure**~~: INVALIDATED. Was API failure artifact, not model behavior. Excluded from thesis.
- **Why expanded benchmark rates are higher**: The expanded benchmark probes harder regions of entity space. Higher baseline rates (Mixtral 14.8% vs 11.8%) and higher prefix residual rates (4.7% vs 0.7%) confirm some hallucinations are intrinsically harder — evidence of discriminative power, not failure.
- **Dimensionality paradox**: The finding that lower-dim embeddings work better is interesting and underexplored.

### Limitations — Needs Major Expansion

Currently 3 bullet points. Needs to be thorough:
- **Initial AUC inflation**: Explicitly acknowledge that the initial benchmark AUC conflated category structure with within-category signal
- **Judge reliability on borderlines**: borderline_plausible_fake has only 15-23% unanimous agreement — this category's results should be interpreted cautiously
- **Bridge analysis class imbalance**: Expanded benchmark bridge AUC drops from pilot's 0.86 to 0.59-0.66 partly because only 15/5 prompts are "still_broken." The within-category tests are more reliable but have smaller effect sizes
- **CoT Verification exclusion**: We excluded CoT from analysis due to judge API failures corrupting 65% of labels. Mention briefly in limitations that CoT was attempted but excluded due to data quality issues — shows methodological honesty.
- **Embedding dependency**: Still only one primary embedding model
- **English only**
- **Template-generated prompts**: Not naturalistic user queries
- **Small human validation sample** (n=50)
- **Correlation vs causation** (already in paper but expand)
- **No causal intervention on geometry** — we observe correlation but haven't reshaped the manifold to test causally
- **Rate differences across benchmarks**: The higher expanded benchmark hallucination/residual rates could reflect prompt difficulty OR model sensitivity to entity novelty — we can't fully disentangle these

### MBB (Mind, Brain, Behavior) Connections (~2-3 pages, Discussion subsection)

Required for MBB track certificate. Currently zero cognitive science engagement in the thesis — all citations are ML papers. This section bridges the gap. Frame as "Implications for Cognitive Science" or "Connections to Human Cognition" — NOT as a bolted-on afterthought, but as genuine intellectual connections that strengthen the thesis.

**1. LLM hallucination ↔ human confabulation.**
- Humans confabulate when probed at the edge of their knowledge — so do LLMs. The borderline categories (plausible fake, obscure real, edge factual) probe the same boundary cognitive psychologists study in false memory research.
- Key citations: Roediger & McDermott 1995 (DRM paradigm — false memories for semantically related items), Loftus 1979 (misinformation effect). Our plausible_fake category is structurally identical to the misinformation paradigm: entities plausible enough to trigger false recognition.
- The "imitative falsehoods" in edge_factual (from TruthfulQA, Lin et al. 2022) directly parallel cultural transmission of false beliefs — models reproduce popular misconceptions, just as humans do through social learning.

**2. Embedding geometry ↔ representational geometry in neuroscience.**
- Representational Similarity Analysis (RSA; Kriegeskorte et al. 2008) studies the geometry of neural population codes. Our density/oppositeness features are analogous: we study the geometry of a representational space and find that structure predicts behavior (hallucination).
- The "sparse void hypothesis" (hallucinations cluster in low-density regions) parallels findings in neural coding: sparse neural representations are associated with uncertainty and errors. The principle — sparse = unreliable — may be general across knowledge representation systems, biological or artificial.
- NOT claiming LLMs are brains. Claiming the geometric principle generalizes.

**3. Metacognition.**
- The entire thesis tests whether models "know what they don't know" — this is metacognition, a core topic in cognitive science (Flavell 1979, Nelson & Narens 1990).
- Our geometric features function as an *external* metacognitive signal — assessing model reliability from representational structure rather than the model's own self-report. This is analogous to neuroimaging studies that predict confidence from neural activity patterns rather than subjective report.
- The fine-tuning result (model learns "when to be skeptical") is a form of learned metacognition — the model acquires a behavioral policy of epistemic caution.

**4. The precision-recall tradeoff ↔ signal detection theory.**
- The obscure-real regression (fine-tuned model denies real entities) maps directly onto signal detection theory (Green & Swets 1966): shifting the criterion toward "say no" reduces false alarms (hallucinations) but increases misses (false negatives on real entities). This is a foundational framework in psychophysics.
- Framing: the model's post-fine-tuning behavior reflects a criterion shift in a noisy representational space — exactly the situation SDT was designed to analyze.

**Scope**: This is 2-3 pages of Discussion, not a new chapter. Draw the parallels, cite the cognitive science work, note that these connections are suggestive rather than tested. Do NOT overclaim — we did not design experiments to test these cognitive hypotheses. Frame as "our findings are consistent with / suggest connections to" rather than "our findings demonstrate."

**Bib entries needed**: Roediger & McDermott 1995, Loftus 1979, Kriegeskorte et al. 2008, Flavell 1979, Nelson & Narens 1990, Green & Swets 1966.

### Conclusion — Should Reflect the Evolved Understanding

The current conclusion claims "curvature and centrality are strong, cross-model predictors." The thesis conclusion should honestly say: "Category structure is the dominant predictor. Within categories, density provides modest but real geometric signal. The more surprising finding is that geometry predicts hallucination *difficulty* — which prompts resist mitigation — pointing toward a geometric taxonomy of fixability."

The conclusion should tell the complete arc through contributions, not pipeline steps:
1. We asked whether embedding geometry predicts hallucination. Answer: yes, but mostly through category structure. The non-circular signal is within-category density.
2. We asked whether prompts can reduce hallucination. Answer: dramatically (89% reduction), replicated at 5x scale.
3. We asked whether geometry predicts *which hallucinations resist mitigation*. Answer: yes — unfixable prompts live in geometrically sparse regions. This is the novel contribution.
4. We asked whether the careful behavior can be made permanent. Answer: fine-tuning matches best-prefix accuracy without runtime prompting — but reveals a precision-recall tradeoff where the model trades knowledge breadth for safety.
5. We asked what the model actually learned. Answer: behavioral caution, not surface memorization. Three tests converge: cross-domain transfer to TruthfulQA, invariance to template diversity (5 templates ≈ 194), and unchanged accuracy on novel entities. The model learned *when to be skeptical*, not *which questions to refuse*.

The intellectual narrative is: **geometry is the diagnostic, prompts are the treatment, fine-tuning is the cure — and geometry predicts where the cure has side effects. The cure works because it teaches epistemic caution, not pattern matching.**

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
| 6 | **Can Prompts Reduce Hallucination?** — 6.1 Prefix design (5 prefixes, literature grounding), 6.2 Pilot study (449 prompts), 6.3 Replication at scale (2,430 prompts), 6.4 Category and refusal analysis, 6.5 Correctness-safety tradeoff | 15-20 |
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

1. **Bridge analysis** (7.1-7.2): Geometry predicts which hallucinations are fixable. Within-category density signal (p=0.034/0.047). Geometric taxonomy of difficulty — "unfixable" prompts live in sparse embedding regions.
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

## Figure Inventory by Chapter

All figures are generated. New figures in `thesis/figures/`; existing figures in their respective `results/*/analysis/` directories. The only figure not yet created is the Ch 4 pipeline diagram (conceptual — create manually in TikZ/draw.io).

| Chapter | Figure | File | Source |
|---|---|---|---|
| Ch 4 | Pipeline diagram | *create manually* | TikZ/draw.io |
| Ch 4 | Judge agreement heatmap | `v5_judge_agreement.png` | `results/v5_prefixes/analysis/` |
| Ch 5 | Geometry vs hallucination scatter (Mixtral) | `v5_geometry_vs_hallucination_mixtral-8x7b.png` | `results/v5_baselines/analysis/` |
| Ch 5 | Geometry vs hallucination scatter (Llama) | `v5_geometry_vs_hallucination_llama-4-maverick-17b.png` | `results/v5_baselines/analysis/` |
| Ch 5 | Within-category density violin (Mixtral) | `v5_within_category_mixtral-8x7b.png` | `results/v5_baselines/analysis/` |
| Ch 5 | Within-category density violin (Llama) | `v5_within_category_llama-4-maverick-17b.png` | `results/v5_baselines/analysis/` |
| Ch 5 | Within-category AUC decomposition | `ch5_within_category_auc.png` | `thesis/figures/` |
| Ch 5 | Cross-model consistency heatmap | `consistency_heatmap.png` | `results/v3/multi_model/` |
| Ch 6 | Category heatmap (Mixtral) | `v5_category_heatmap_mixtral-8x7b.png` | `results/v5_prefixes/analysis/` |
| Ch 6 | Category heatmap (Llama) | `v5_category_heatmap_llama-4-maverick-17b.png` | `results/v5_prefixes/analysis/` |
| Ch 6 | Accuracy-safety tradeoff curve | `v5_tradeoff_curve.png` | `results/v5_prefixes/analysis/` |
| Ch 6 | Refusal rates by prefix | `v5_refusal_rates.png` | `results/v5_prefixes/analysis/` |
| Ch 6 | Pilot vs scale comparison | `ch6_v4_v5_comparison.png` | `thesis/figures/` |
| Ch 7 | Prefix bridge scatter (Mixtral) | `v5_bridge_mixtral-8x7b.png` | `results/v5_prefixes/analysis/` |
| Ch 7 | Prefix bridge scatter (Llama) | `v5_bridge_llama-4-maverick-17b.png` | `results/v5_prefixes/analysis/` |
| Ch 7 | FT bridge analysis (Mixtral) | `ft_bridge_mixtral-8x7b.png` | `results/v5_finetuned/analysis/` |
| Ch 7 | FT bridge analysis (Llama) | `ft_bridge_llama-4-maverick-17b.png` | `results/v5_finetuned/analysis/` |
| Ch 7 | Baseline vs prefix vs FT comparison | `ch7_ft_comparison.png` | `thesis/figures/` |
| Ch 7 | Per-category FT heatmap | `ch7_ft_category_heatmap.png` | `thesis/figures/` |
| Ch 7 | LoRA hyperparameter sensitivity | `ch7_hyperparameter_sensitivity.png` | `thesis/figures/` |
| Ch 7 | Regression error type breakdown | `ch7_regression_breakdown.png` | `thesis/figures/` |
| Ch 7 | Density by FT outcome (key figure) | `ch7_density_by_ft_outcome.png` | `thesis/figures/` |
| Ch 7 | Template ablation: accuracy vs template count | *to generate* | `results/v5_finetuned/ablation/` |
| Ch 7 | Template ablation: seen vs novel template split | *to generate* | `results/v5_finetuned/ablation/` |

**Total**: 23 figures (1 pending manual creation, 2 pending generation from data, 13 existing, 7 newly generated).

---

## What We Can Write NOW vs. What's Waiting on Data

**As of March 8, 2026. Thesis due March 27 (afternoon).**

### Available now (all data in hand):
- **Ch 1 Introduction**: rewrite with full arc and four contributions
- **Ch 2 Background**: entirely new content, no experimental data needed
- **Ch 3 Literature Review**: conference paper's 6 subsections as starting point, expand to ~50-80 refs. Phase 7 comparison tables (v5, fully verified) provide structured content.
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

## Appendix Inventory

Centralized tracker for everything that should go in the appendix. Each entry includes the appendix label (for `\ref{}` in the main text), what it contains, source data, and which chapter references it.

### Appendix A: Supplementary Tables and Figures

| Label | Content | Source file | Referenced from | Status |
|---|---|---|---|---|
| `app:kendall-matrix` | Full 10×10 Kendall's τ pairwise correlation matrix (heatmap or table) | `results/v3/multi_model/stats/kendall_tau_matrix.csv` | §5.1 (Cross-Model Benchmark) | **NEEDS CREATION** |
| `app:within-category-pvalues` | Within-category p-value heatmap: features × categories × models | TBD (from `analyze_v5_geometry_prediction.py` output) | §5.4 (Within-Category) | **NEEDS CREATION** |
| `app:feature-correlation` | 5×5 feature correlation matrix heatmap (showing local_id–curvature r = −0.143) | `data/processed/v5_geometry_features.csv` | §5.5 (Feature Synthesis) | **NEEDS CREATION** |
| `app:v3-geometry-heatmaps` | V3 geometric features overlaid on UMAP projection | `results/v3/figures/geometry_heatmaps_umap.png` | §5.3 (Category Confound) | **EXISTS** |

### Appendix B: Judge Diagnostics

| Label | Content | Source file | Referenced from | Status |
|---|---|---|---|---|
| `app:judge-diagnostics` | Per-judge accuracy/leniency breakdown, category-specific agreement rates | `results/sensitivity_analysis.json` | §5.1 (Judge Validation) | **NEEDS CREATION** |
| `app:human-validation` | Full disagreement analysis for n=50 human validation sample | `results/v3/human_verification_report.json` | §5.1 (Judge Validation) | **NEEDS CREATION** |

### Appendix C: Prompt Prefix Texts

| Label | Content | Source file | Referenced from | Status |
|---|---|---|---|---|
| `app:prefix-texts` | Full text of all 5 prompt prefixes used in Ch 6 | Scripts / config files | Ch 6 (Prefixes) | **NEEDS CREATION** |

### Appendix D: Embedding Model Robustness

| Label | Content | Source file | Referenced from | Status |
|---|---|---|---|---|
| `app:embedding-robustness` | Preliminary robustness check with 3 embedding models (text-embedding-3-small, text-embedding-3-large, all-mpnet-base-v2) on initial benchmark | TBD | §5.6 or Ch 8 (Limitations) | **NEEDS CREATION** |

### Appendix E: Additional Statistical Details

| Label | Content | Source file | Referenced from | Status |
|---|---|---|---|---|
| `app:qq-plots` | QQ plots showing non-normality of geometric feature distributions (justifying Mann-Whitney over t-test) | `data/processed/v5_geometry_features.csv` | §5.2 (Between-Category) | **NEEDS CREATION** — only if reviewers challenge |

> **Rule**: When writing any chapter and deciding something belongs in the appendix rather than the main text, add it here immediately AND add the `\ref{app:label}` + TODO comment in the .tex file. This is the single source of truth for appendix content.
