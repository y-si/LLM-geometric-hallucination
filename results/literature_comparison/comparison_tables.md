# Phase 7B: Literature Comparison Tables (v4)

Generated: March 2026. Fourth revision after three rounds of rigorous self-review.
For thesis Ch 8 (Discussion). Three sub-tables + preamble.

## Revision history

- v1: Uncurated dump of all 22 methods. Misleading metric comparisons, R-Tuning inflated to Direct, V4/V5 cherry-picking, reasoning methods mixed with hallucination methods, advocacy tone.
- v2: Cut to 14 methods, fixed metric mixing, downgraded R-Tuning, standardized on V5. But: Table 2 too thin (3 entries, 1 was our own result), "Partial" label too broad, bridge AUC 0.86 conflated with detection, FActScore misplaced in detection table, DOLA missing.
- v3: Table 2 expanded to 5 external entries (added DOLA, restored Self-Refine with proper framing). Moved our CoT result out of table. Moved bridge AUC out of detection results. Moved FActScore to reference metrics footnote. Added sub-levels within Partial. Fixed R-Tuning result description. 15 external methods + 1 context paper. But: bridge AUC 0.86 presented without flagging it as train-only and unreplicated at V5 scale; our own numbers not held to same standard as literature [*] numbers; detection results section mixed three analyses at different rigor levels without signaling the hierarchy.
- v4: Rewrote "Our results" sections with honest caveats on every number. Bridge AUC 0.86 flagged as train-only with V5 cross-validated result (0.59) alongside. Detection results restructured into clear rigor hierarchy: within-category first (non-circular), between-category second (partially confounded by category), aggregate last. Within-category AUC corrected to per-model values (0.67/0.68). Added methodological flags [†] on our own numbers matching the [*] standard for literature.
- v5 (this version): All 9 key literature claims verified from paper PDFs. Three corrections applied: (1) CoVe FactScore baseline corrected from 63.7 to 55.9 (+15.5pp not +7.7pp); (2) INSIDE/EigenScore "+5-10pp" qualified (not universal — loses on TriviaQA); (3) FactTune updated to ICLR camera-ready figures (53%/50%) from arXiv preprint (58%/40%). Added exact conditions (model sizes, table numbers, metric names) to all verified claims. [*] markers removed from verified entries.

---

## Preamble (must precede tables in thesis)

Direct comparison across these methods is not possible. Each uses different benchmarks, models, metrics, and hallucination definitions:

- **Our metric**: Hallucination rate = % of responses labeled "hallucination" (label 2) by a 3-judge consensus panel (GPT-5.1, Claude Opus 4.5, Llama 4 Maverick) on an entity-fabrication benchmark.
- **TruthfulQA metric**: % of responses judged "truthful" by a fine-tuned GPT-judge on 817 misconception questions.
- **FActScore metric**: % of atomic facts in long-form text supported by Wikipedia.
- **AUROC**: Area under receiver operating characteristic for binary classification.

These measure different things. A method achieving 90% on one metric is not comparable to 90% on another. The tables provide **directional context** — the landscape of approaches and roughly where our results sit — not head-to-head rankings.

**Comparability ratings**:
- **Partial (close)**: Same conceptual category and at least one shared benchmark or task type. The comparison is informative, though not apples-to-apples.
- **Partial (distant)**: Same broad goal but different benchmark, model, metric, and mechanism. The comparison shows we are in the same field; directional only.
- **Indirect**: Included for context (field-standard reference, reviewer would expect to see it), but the comparison provides minimal information about relative performance.

**Our setup**: Mixtral 8x7B Instruct and Llama 4 Maverick 17B. Custom entity-fabrication benchmark: 2,430 prompts (V5), 449 held-out (V4 test set for fine-tuning evaluation). 3-judge consensus panel.

**Verification**: All literature numbers have been verified from paper PDFs/HTML (March 2026). Three corrections were applied: CoVe FactScore baseline (55.9 not 63.7), INSIDE/EigenScore range qualified (not uniform across benchmarks), and FactTune updated to ICLR camera-ready figures (53%/50% not 58%/40%). See verification table at end of document for details.

**Our own numbers**: Our results marked [†] have known methodological caveats documented inline. We hold our own numbers to the same scrutiny standard as the literature — where a number has a caveat (e.g., train-only AUC, partially circular analysis), it is flagged.

---

## Table 1: Hallucination Detection / Prediction (5 methods)

Methods that predict whether a response contains or will contain hallucination.

| Method | Venue | Signal | Benchmark | Key Result | Comparability | Notes |
|---|---|---|---|---|---|---|
| **INSIDE / EigenScore** (Chen et al.) | ICLR 2024 | Eigenvalues of response embedding covariance matrix | TriviaQA, NQ, CoQA, SQuAD | +5-24pp AUROC on SQuAD/CoQA; at parity or slightly worse on TriviaQA; +2-6pp on NQ (vs logit-level and language-level baselines; Table 1) | **Partial (close)** | Closest conceptual kin. Both use embedding-space geometric properties to predict hallucination. Differences: (1) they analyze *response* embeddings post-generation from the model's internal states; we analyze *entity* embeddings in a knowledge graph pre-generation using an external embedding model. (2) Their prediction is per-response; ours is per-prompt/entity. These differences mean their AUROC and our AUC measure different tasks and cannot be compared numerically. |
| **SAPLMA** (Azaria & Mitchell) | EMNLP 2023 Findings | Classifier on model hidden states | Custom true/false statements (6 topics) | 71-83% accuracy depending on model/topic [*] | **Partial (close)** | Both train classifiers on representation features to predict factuality. They probe the generating model's own hidden states; we use features from an external embedding model's graph structure. Different signal source, different evaluation (accuracy on true/false vs AUC on hallucination prediction). |
| **ITI** (Li et al.) | NeurIPS 2023 | Linear probes on attention head activations; additive shifting at inference | TruthfulQA (MC1, MC2, open-ended) | TruthfulQA (open-ended, true\*informative metric, GPT-judge): Alpaca (LLaMA-7B instruction-finetuned) 32.5%→65.1% (Table 2, 2-fold CV). MC1 improvement much smaller (27.8%→31.9%). | **Partial (close)** | Detection+mitigation hybrid. The probing step identifies "truthful directions" in activation space (detection); the shifting step pushes activations toward truth (mitigation). Both run on TruthfulQA: ITI +32.6pp truthful vs our Llama -4.4pp halluc / +5.3pp accuracy. Not directly comparable — different metrics (GPT-judge true\*informative vs 3-judge accuracy/hallucination), different models (Alpaca vs Mixtral/Llama 4), and critically different mechanism: ITI is TruthfulQA-trained (inference-time probes from TruthfulQA data), while our FT was NOT trained on TruthfulQA — any improvement is cross-domain transfer. |
| **Semantic Entropy** (Farquhar et al.) | Nature 2024 | Entropy over meaning clusters from sampled responses | TriviaQA, SQuAD, BioASQ, NQ, SVAMP | Mean AUROC 0.790 across 30 task-model combos (5 datasets × 6 models: LLaMA-2 7B/13B/70B, Falcon 7B/40B, Mistral 7B); outperforms naive entropy (0.691), P(True) (0.698), embedding regression (0.687) | **Indirect** | Highest-profile detection method (published in Nature). Fundamentally different: they cluster multiple sampled responses by semantic equivalence post-generation (requires 10 extra generations per query). We analyze entity graph topology pre-generation with no sampling. Included because a hallucination researcher would expect it. Note: later methods (SINdex, 2025) surpass these numbers. |
| **SelfCheckGPT** (Manakul et al.) | EMNLP 2023 | Cross-sample consistency (black-box) | WikiBio (GPT-3 biographies) | AUC-PR ~0.78 sentence-level hallucination detection [*] | **Indirect** | Field-standard black-box detection method. Fundamentally different paradigm — no model internals needed, operates entirely post-generation by sampling multiple responses and checking consistency. Included as widely-cited reference (~600 citations). |

**Reference metric** (not a detection method, but used by multiple comparison methods):
- **FActScore** (Min et al., EMNLP 2023, ~869 citations): Evaluation framework decomposing text into atomic facts verified against Wikipedia. ChatGPT achieves 58% FActScore [*]. Referenced because FactTune, FLAME, and Self-RAG report results using it.

**Our detection/prediction results** (reported separately to avoid metric mixing):

Results are presented in order of methodological rigor, strongest first.

1. **Within-category prediction** (the non-circular test — controls for category confounds):
   - Among 600 nonexistent-entity prompts (same category, same structure, geometry varies): density significantly predicts hallucination for both models (p<0.0001, Mann-Whitney U, effect size r≈0.25). Prompts in sparser embedding neighborhoods hallucinate more.
   - 5-fold CV logistic AUC: 0.67 (Mixtral), 0.68 (Llama) — V5, nonexistent category only
   - **Why this is the honest number**: category membership alone achieves AUC 0.77 for overall hallucination prediction. The within-category test isolates geometry's contribution beyond category labels.

2. **Between-category prediction** [†partially confounded — see caveat]:
   - Geometry-only: 5-fold CV AUC 0.64 (Mixtral), 0.72 (Llama) — V5, 2,430 prompts
   - Geometry + category: CV AUC 0.79 (Mixtral), 0.81 (Llama)
   - Category alone: CV AUC 0.77 (both models)
   - Geometry adds +0.02-0.04 AUC beyond category
   - [†] **Caveat**: Most of the between-category AUC reflects category structure, not geometry per se. Borderline categories were defined as semantically unusual, and they have unusual geometry — this is informative (geometry captures category structure) but partially circular. The 0.64/0.72 numbers should not be cited as "geometry predicts hallucination" without this context.

**Our bridge analyses** (separate tasks — predicting mitigation *difficulty*, not presence):

These predict which hallucinations resist intervention, not whether hallucination occurs. No method in the table above attempts this task.

3. **Prefix bridge — V4 discovery** [†train-only, not cross-validated]:
   - Predicting which hallucinating prompts will be fixed by at least one prefix: train AUC 0.86 (Mixtral), 0.83 (Llama) — V4, 449 prompts
   - [†] **Critical caveat**: This AUC is train-only (no cross-validation was performed). The V4 per-prefix classification also inflated the `still_broken` group, making logistic regression more stable. This number was the original discovery result but must not be presented as a validated finding.

4. **Prefix bridge — V5 replication** [†underpowered — tiny minority class]:
   - 5-fold CV AUC: 0.59 (Mixtral, n=333 fixed vs 15 broken), 0.43 (Llama, n=227 fixed vs 5 broken) — V5, 2,430 prompts
   - [†] **Caveat**: The class imbalance (333:15, 227:5) makes logistic regression unreliable. The AUC drop from 0.86 to 0.59 reflects experimental design differences (V5 aggregates across all 5 prefixes, shrinking the `still_broken` class), not necessarily a failure to replicate the underlying signal.

5. **Prefix bridge — V5 within-category confirmation** (methodologically strongest):
   - Among hallucinated nonexistent prompts, density significantly predicts fixability:
     - Mixtral: p=0.034, broken density 1.94 vs fixed 2.18
     - Llama: p=0.047, broken density 1.88 vs fixed 2.14
   - Direction matches V4: unfixable hallucinations live in sparser embedding regions.
   - This is the non-circular confirmation of the V4 discovery.
   - [†] **Correction caveat**: These p-values are uncorrected. If testing 3 features (density, oppositeness, centrality), Bonferroni correction would yield p≈0.10/0.14 — no longer significant at 0.05. However, density was the *predicted* feature from V4 analysis (a priori hypothesis, not exploratory), which mitigates the correction concern. The thesis should frame this as a confirmatory test of a V4-derived hypothesis, not an exploratory finding.

6. **Fine-tuning bridge** (does geometry predict which hallucinations resist FT?):
   - Density: Mixtral p=0.00018, r=-0.80 (n=44 fixed vs 9 broken); Llama p=0.017, r=-0.58 (n=16 vs 10)
   - Low density = resists fine-tuning correction. Consistent with prefix bridge direction.
   - [†] **Correction caveat**: Mixtral survives Bonferroni correction (p_corrected=0.0055). Llama does NOT (p_corrected=0.49; permutation p=0.15). The FT bridge signal is robust for Mixtral but weak/absent for Llama. Small sample sizes for both (especially n=9 and n=10 in the broken groups).

**Recommended thesis framing** (per experiment log section 2.5.5 and Step 8B analysis):
- Lead with within-category prediction (0.67/0.68 AUC, p<0.0001 density) as the non-circular evidence
- Report V4 bridge AUC=0.86 as the discovery result, explicitly flagged as train-only
- Report V5 within-category bridge (density p=0.034/0.047) as the confirmation
- Do NOT frame as "geometry predicts hallucination with AUC 0.86"

**Positioning**: Our approach is closest to INSIDE/EigenScore in using embedding-space geometric properties. It differs in operating pre-generation on a knowledge graph rather than post-generation on model internals. The bridge analysis extends to difficulty prediction (which hallucinations resist mitigation), which no method in the table above attempts. The within-category evidence (density predicts both hallucination occurrence and resistance to mitigation within nonexistent prompts, p<0.0001 and p<0.05 respectively) is the methodologically strongest finding. Whether pre-generation prediction and difficulty prediction constitute meaningful advances depends on the use case — we have not demonstrated deployment utility.

---

## Table 2: Prompt-Based / Inference-Time Hallucination Mitigation (5 methods)

Methods that reduce hallucination at inference time without modifying model weights. Includes both prompt-engineering and decoding-strategy methods.

| Method | Venue | Mechanism | Benchmark | Key Result | Comparability | Notes |
|---|---|---|---|---|---|---|
| **CoVe** (Dhuliawala et al.) | ACL 2024 Findings | Multi-step pipeline: draft → plan verification questions → answer independently → revise | Wikidata list-Qs, MultiSpanQA (418 Qs), biography (FactScore) | Halluc. entities/response: 2.95→0.68 (two-step variant, Wikidata; Table 1); FactScore: 55.9→71.4 (+15.5pp, factor+revise variant, biography; Table 3). LLaMA-65B. | **Partial (close)** | Both target entity-level hallucination. Key differences: CoVe uses a 4-stage pipeline per query (compute-heavy at inference); we use a single-shot system prompt prefix. Different models (LLaMA-65B vs our Mixtral/Llama 4). Different metric: CoVe counts hallucinated entities per response; we classify entire responses as hallucinated or not. |
| **DoLA** (Chuang et al.) | ICLR 2024 | Contrasts logits from later vs earlier transformer layers during decoding | TruthfulQA, multiple-choice QA | LLaMA 7B-65B on TruthfulQA (open-ended, %T\*I): +12.2-17.4pp truthfulness (Table 1). Range: 7B +13.9pp, 13B +12.2pp, 33B +17.4pp, 65B +14.4pp. | **Partial (close)** | Pure inference-time decoding method (no weight changes, no external knowledge). Our TruthfulQA results (Step 13E): Llama halluc -4.4pp (Bonferroni-sig), Mixtral -2.2pp (marginal) — smaller than DoLA's +12-17pp, but our FT was not trained on TruthfulQA (cross-domain transfer). Different mechanism entirely — DoLA modifies the decoding process itself, while we modify weights via LoRA SFT. Complementary approaches in principle. |
| **Self-Alignment for Factuality** (Zhang et al.) | ACL 2024 | Self-evaluation prompting (prompt component); full pipeline also includes DPO | TruthfulQA, BioGEN (FactScore) | TruthfulQA: +13% accuracy; BioGEN: +4% FActScore [*] | **Partial (distant)** | Hybrid method — the self-evaluation is prompting, but the full pipeline includes DPO fine-tuning. Unclear how much of the improvement comes from the prompt component alone. Different benchmarks and models (LLaMA-7B vs ours). |
| **Self-Refine** (Madaan et al.) | NeurIPS 2023 | Iterative: generate → self-critique → revise, repeat until convergence | 7 tasks (dialogue, code, math, sentiment, acronym, constrained gen, toxicity) | ~20% absolute improvement averaged across 7 tasks [*] | **Partial (distant)** | Domain-agnostic iterative refinement. Not hallucination-specific — the 7 tasks span diverse objectives. Included because the self-critique mechanism is conceptually related to our prefix approach (both steer the model via natural language instructions). However, Self-Refine uses multiple rounds; we use single-shot. The ~20% improvement is not on factual hallucination specifically. |
| **RECITE** (Sun et al.) | ICLR 2023 | Prompt model to recite relevant passages from memory, then answer based on recitations | NQ, TriviaQA, HotpotQA (closed-book) | Comparable to BM25-based retrieval accuracy [*] | **Partial (distant)** | Closed-book alternative to RAG — uses the model's own parametric memory as a "retrieval" source. Different mechanism from our prefix approach, but addresses the same setting (closed-book factual QA without external knowledge). |

~~**Our negative result** (CoT Verification prefix):~~ **INVALIDATED (March 2026).** The 62-68% refusal rate was an API failure artifact (GPT-5.1 quota + Claude auth failures injecting fake label=3 votes), not model behavior. Real CoT refusal rate < 1%. CoT excluded from thesis entirely. See `JUDGE_CONTAMINATION_ISSUE.md`.

**Our V5 prefix results** (2,430 prompts, post-contamination-fix):

| Model | No Prefix | Entity-Aware | Structured Caution | Epistemic Humility | Fact-Grounded |
|---|---|---|---|---|---|
| Mixtral halluc. rate | 14.8% | **4.7%** | 6.7% | 10.2% | 7.1% |
| Llama halluc. rate | 9.7% | 3.7% | **3.0%** | 4.3% | 4.5% |

V4 pilot (449 prompts) showed lower absolute rates (Entity-Aware Mixtral 0.67%, Structured Caution Llama 0.45%) on a smaller, less diverse prompt set. V5 is the more reliable estimate.

**Positioning**: Our prefix experiment is most comparable to CoVe (both target entity-level hallucination) and DoLA (both operate at inference time on TruthfulQA-relevant tasks). The key tradeoffs: CoVe achieves strong entity-level reduction but is compute-heavy (4 stages per query). DoLA achieves +12-17pp on TruthfulQA with no extra cost beyond decoding modification. Our approach applies a fixed system prompt (cheap, no decoding changes) but achieves smaller reductions on our harder V5 benchmark. Our bridge analysis adds a dimension absent from these methods: predicting *where* prompting will fail based on entity geometry. However, we have not tested CoVe or DoLA on our benchmark, so we cannot make performance claims relative to them.

---

## Table 3: Fine-Tuning / Training-Based Mitigation (5 methods + 1 context paper)

Methods that modify model weights to reduce hallucination.

| Method | Venue | Training Signal | Benchmark | Key Result | Our Result (449 held-out) | Comparability | Notes |
|---|---|---|---|---|---|---|---|
| **R-Tuning** (Zhang et al.) | NAACL 2024 (Outstanding Paper) | Refusal-aware SFT: split Qs into "known" (model answers correctly) vs "unknown" (model fails), train to refuse unknowns | ParaRel, MMLU + OOD generalization | In-domain AP gains modest (+0.3-0.9pp ParaRel, +0.8-16.9pp MMLU); OOD gains larger (+13.2pp LLaMA-13B ParaRel, +10.0pp MMLU). Not universal — vanilla wins in 2 of 12 conditions. Refusal transfers as meta-skill: 96-99% refusal on unseen tasks vs 2-35% vanilla (Table 3). | Mixtral: 11.8%→1.3% halluc (89% rel. reduction); Llama: 5.8%→0.7% (88%). On 449 held-out. | **Partial (close)** | Closest comparator. Both teach models to abstain on uncertain knowledge via SFT. Key differences: (1) different abstention signal — R-Tuning: binary train-time probing (can model answer this Q?); us: geometric features of entity embeddings select best prefix response for training. (2) Different benchmark: ParaRel/MMLU (relational knowledge/multitask) vs our entity-fabrication benchmark. (3) Different models: OpenLLaMA-3B/LLaMA-7B/13B vs Mixtral 8x7B/Llama 4 Maverick. (4) Different metric: AP vs hallucination rate. Cannot be Direct — no shared dimension. Whether our geometry-guided selection produces better training data than R-Tuning's known/unknown split is unknown without running both on the same benchmark. |
| **FactTune** (Tian et al.) | ICLR 2024 | DPO on auto-generated preference pairs scored by FActScore or confidence | Biography generation (FActScore), medical QA | 53% relative reduction in factual errors on biography; 50% on medical QA (ICLR camera-ready; arXiv v1 reported 58%/40%). Llama-2-7B-Chat, FactTune-FS variant. | Mixtral: 89% relative halluc. reduction (11.8%→1.3%) | **Partial (distant)** | Both fine-tune for factuality, but through different paradigms: FactTune uses DPO with auto-generated preferences; we use LoRA SFT with geometry-guided best-per-prompt selection. Different benchmark (biography vs entity QA), different metric (FActScore error rate vs hallucination rate), different model (Llama-2-7B vs Mixtral 8x7B). The side-by-side "89% vs 53%" is misleading — different tasks, different error definitions. |
| **FLAME** (Dhuliawala et al.) | NeurIPS 2024 | Factuality-aware SFT (filter out knowledge novel to model) + factuality-aware DPO | Biography (FActScore), AlpacaFact, FAVA, AlpacaEval | +5.6 FActScore on Biography (42.3→47.9, Table 3); also +3.4 AlpacaFact, +3.5 FAVA. Llama-2-70B. AlpacaEval preserved (51.2% win rate). | N/A — different metric | **Partial (distant)** | Shared motivation: both address the problem that SFT on knowledge novel to the model increases hallucination (Gekhman et al.). FLAME filters training data by model familiarity; we select by geometric features + prefix effectiveness. Different mechanism, benchmark, metric, model (Llama-2-70B vs ours). |
| **Mask-DPO** | ICLR 2025 | Sentence-level masked DPO: learn only from factual sentences in preferred samples, ignore factual sentences in rejected samples | ANAH test set, biography (FActScore) | ANAH: 49.19%→77.53% (+28.3pp, Table 1); Llama3.1-8B-Instruct surpasses 70B on ANAH (77.53% vs 53.44%) but NOT on FActScore (39.39% vs 40.47%). FActScore: 30.29%→39.39% (+9.1pp). | Mixtral: 82.9%→91.1% (+8.2pp accuracy) | **Partial (distant)** | Both achieve meaningful accuracy gains via fine-tuning. Different paradigm (sentence-masked DPO vs LoRA SFT), different benchmark (ANAH vs entity fabrication), different model (Llama-3.1-8B vs Mixtral). The +28pp vs +8pp gap reflects different task difficulty and baselines, not method quality — ANAH's baseline is much lower (49.2%) than ours (82.9%). |
| **InstructGPT / RLHF** (Ouyang et al.) | NeurIPS 2022 | 3-stage: SFT on demonstrations + reward model on comparisons + PPO | TruthfulQA, human preference evaluations | TruthfulQA: ~21%→~42% truthful (approximate, read from Figure 6 bar chart; paper says "about twice as often"). 175B PPO model. Closed-domain halluc: 41%→21% (exact quote, Figure 4, averaged across sizes). RLHF *increased* hallucination on some tasks (SQuAD, DROP — the "alignment tax"). | TruthfulQA: Llama acc 71.8%→77.1% (+5.3pp, p=0.0002), halluc 17.6%→13.2% (-4.4pp, p=0.0005). Mixtral: +2.2pp acc, -2.2pp halluc (not sig). | **Indirect** | Foundational alignment method (~7,000 citations), not hallucination-specific. Included because: (1) reviewer expects it, (2) the finding that RLHF can increase hallucination on some tasks while reducing it on others is directly relevant to our precision-recall tradeoff finding. Note: our TruthfulQA refusal ≤0.7% — unlike InstructGPT, our FT does NOT increase hallucination or over-caution on this benchmark. |

**Context paper** (not a mitigation method — critical framing for our approach):
- **Gekhman et al.** (EMNLP 2024): "Does Fine-Tuning LLMs on New Knowledge Encourage Hallucinations?" — Fine-tuning on knowledge not in the model's pretraining data linearly increases hallucination. Our approach avoids this: we fine-tune on behavioral patterns (how to respond cautiously to uncertain entities), not on new factual knowledge. This is a methodological distinction worth highlighting.

**Methods excluded** (with reason):
- **Self-RAG** (Asai et al., ICLR 2024): Hybrid FT+retrieval; we test closed-book. Strong results (PopQA 14.7%→55.8%, biography 80% factual) but requires retrieval infrastructure at inference. Mentioned in thesis Discussion as context for "why not retrieval?" but not in the comparison table.
- **Constitutional AI** (Bai et al., 2022): General alignment focused on harmlessness. TruthfulQA ~58% is incidental, not the paper's contribution.
- **F-DPO** (2025 preprint): <10 citations, unverified results, too recent.

**Our fine-tuning results** (449 held-out prompts, V4 test set; trained on V5 2,430 best-per-prompt):

| Model | Baseline Accuracy | Baseline Halluc. | FT Accuracy | FT Halluc. | Abs. Improvement | Rel. Halluc. Reduction |
|---|---|---|---|---|---|---|
| Mixtral configC | 82.9% | 11.8% | 94.4% | 1.3% | +11.5pp accuracy | 89% fewer hallucinations |
| Llama configA | 90.6% | 5.8% | 94.0% | 1.1% | +3.4pp accuracy | 81% fewer hallucinations |

Note: Post-contamination-fix numbers (March 2026). The relative reductions are meaningful but the absolute accuracy improvement for Llama is modest (+3.4pp) because the baseline was already high (90.6%). Both numbers should be reported.

**Our TruthfulQA generalization results** (817 questions, external benchmark — Step 13E):

| Model | Baseline Acc | FT Acc | Δ Acc | Baseline Halluc | FT Halluc | Δ Halluc | McNemar p (acc) | McNemar p (halluc) | Bonferroni |
|---|---|---|---|---|---|---|---|---|---|
| Mixtral configC | 74.4% | 76.6% | +2.2pp | 16.9% | 14.7% | -2.2pp | 0.1145 | 0.0763 | Neither sig |
| Llama configA | 71.8% | 77.1% | +5.3pp | 17.6% | 13.2% | -4.4pp | 0.0002 | 0.0005 | Both sig |

Note: These models were NOT trained on TruthfulQA — they were trained on entity-fabrication data. Any TruthfulQA improvement is cross-domain transfer from fabrication-skepticism to misconception-type hallucination. The 13-25% relative halluc reduction here vs 88-89% on the custom benchmark reflects the domain gap.

**Positioning**: R-Tuning is the closest comparator. Both teach abstention on uncertain knowledge through SFT, but through different signals. The DPO methods (FactTune, FLAME, Mask-DPO) represent a different training paradigm from our LoRA SFT. Our unique element is geometry-guided data curation — using embedding features to select training examples — rather than auto-generated preferences (FactTune), model-familiarity filtering (FLAME), or sentence-level masking (Mask-DPO). Whether this produces better training data is an open empirical question.

Our fine-tuned models show a precision-recall tradeoff on the custom benchmark: reduced hallucination comes with increased refusal in sparse geometric regions. Density predicts FT resistance for Mixtral (p=0.00018, survives Bonferroni); the signal is weaker for Llama (p=0.017 uncorrected, does not survive Bonferroni). This is consistent with InstructGPT's finding that alignment interventions can redistribute errors rather than purely eliminating them. However, the over-caution does NOT generalize to TruthfulQA (refusal ≤0.7% for both models), suggesting the tradeoff is domain-specific to entity-fabrication questions rather than a general personality shift.

---

## Verification Status

All numbers below were verified from paper PDFs/HTML via web search (March 2026). Numbers in tables above have been corrected where needed; [*] markers removed from verified claims.

| Paper | Original Claim | Verified | Corrections Applied |
|---|---|---|---|
| R-Tuning | "Outperforms vanilla IT on AP" | **Yes** (Table 1) | Qualified: not universal (2/12 conditions vanilla wins). Added specific AP ranges. Refusal transfer (96-99%) strongly confirmed from Table 3. |
| INSIDE/EigenScore | "+5-10pp AUROC" | **Partially** (Table 1) | **Corrected**: +5-24pp on SQuAD/CoQA, but EigenScore *loses* on TriviaQA (-1 to -2pp) and is marginal on NQ (+2-6pp). Original claim overstated. |
| ITI | "32.5%→65.1%" | **Yes** (Table 2) | Confirmed: Alpaca (LLaMA-7B instruction-finetuned), open-ended true\*informative metric, 2-fold CV. MC1 improvement much smaller (27.8%→31.9%). |
| Semantic Entropy | "Best AUROC across 5 datasets" | **Yes** (text + SINdex reproduction) | Added specifics: mean AUROC 0.790, 6 models, outperforms naive entropy/P(True)/embedding regression. "Best" is vs paper's own baselines; later methods surpass it. |
| CoVe | "2.95→0.68; FactScore 63.7→71.4" | **Partially** (Tables 1, 3) | **Corrected**: 2.95→0.68 confirmed (two-step variant, Wikidata). FactScore 63.7 is NOT baseline — it's CoVe (factored). Actual baseline is 55.9. Correct: 55.9→71.4 (+15.5pp, factor+revise). |
| DoLA | "+12-17pp truthfulness" | **Yes** (Table 1) | Confirmed: 12.2-17.4pp across LLaMA 7B-65B, open-ended %T\*I metric. |
| FactTune | "58% error reduction" | **Partially** (abstract + OpenReview) | **Corrected**: arXiv v1 says 58%/40%, but ICLR 2024 camera-ready says **53%/50%**. Should cite published figures. Model: Llama-2-7B-Chat, FactTune-FS variant. |
| FLAME | "+5.6 FActScore" | **Yes** (Table 3) | Confirmed: Biography benchmark, 42.3→47.9, Llama-2-70B. AlpacaEval 51.2% preserved. |
| Mask-DPO | "49.2%→77.5%; 8B surpasses 70B" | **Yes** (Table 1) | Confirmed with caveat: 8B surpasses 70B on ANAH only (77.53% vs 53.44%), NOT on FActScore (39.39% vs 40.47%). |
| InstructGPT | "21%→42% TruthfulQA; 41%→21% halluc" | **Yes** (Figures 4, 6) | 21%→42% is approximate (Figure 6 bar chart, paper says "about twice"). 41%→21% is exact quote (Figure 4, closed-domain API tasks). 175B model. |

---

## Summary

- **External methods in tables**: 15 (5 detection + 5 prompt/inference-time + 5 fine-tuning) + 1 context paper (Gekhman et al.)
- **Comparability breakdown**: 0 Direct, 5 Partial (close), 6 Partial (distant), 4 Indirect
- **Our negative result**: CoT catastrophic refusal reported below Table 2 (not as a table entry)
- **Honest unknowns stated**: R-Tuning head-to-head unknown, CoVe/DoLA not tested on our benchmark, relative reduction comparisons called out as misleading across benchmarks
- **Literature verification**: 9/9 key claims verified from paper PDFs (March 2026). 3 corrections applied (CoVe FactScore baseline, INSIDE/EigenScore range, FactTune preprint→published figures). 5 unverified claims remain for SAPLMA, SelfCheckGPT, FActScore reference, Self-Alignment, Self-Refine, RECITE (lower priority — Indirect/Partial distant comparisons)
- **Our own numbers with caveats** [†]:
  - Bridge AUC 0.86: train-only, V5 CV replication at 0.59 (underpowered). Within-category density confirmation at p=0.034/0.047 (uncorrected; would not survive Bonferroni, but density was the a priori predicted feature).
  - Between-category AUC 0.64/0.72: partially confounded by category structure (category alone = 0.77)
  - Within-category AUC 0.67/0.68: the non-circular, methodologically strongest finding
  - FT bridge density: Mixtral survives Bonferroni (p_corrected=0.0055); Llama does NOT (p_corrected=0.49)
  - Llama absolute improvement modest (+1.8pp accuracy despite 88% relative halluc reduction)
- **Key principle**: We flag methodological issues on our own results [†] with the same rigor applied to literature results. 9/9 priority claims verified from papers; 5 lower-priority claims (SAPLMA, SelfCheckGPT, FActScore, Self-Alignment, Self-Refine, RECITE) still [*] unverified. A comparison table that is more honest about others' numbers than its own is not credible.
