# Phase 7A: Literature Search Results — Compiled Notes

Generated: March 2026
Status: Step 7A COMPLETE. All 4 search axes covered. Ready for Step 7B (build tables).

---

## Search Summary

| Axis | Methods Found | Agent Status |
|---|---|---|
| Detection | 8 methods | Complete |
| Prompt mitigation | 8 methods | Complete |
| Fine-tuning mitigation | 8 methods | Complete |
| Surveys & benchmarks | 4 surveys, 3 benchmarks, 3 RAG papers | Complete |

---

## AXIS 1: DETECTION METHODS

### 1. SelfCheckGPT (Manakul et al., EMNLP 2023)
- **Citations**: ~600+
- **Category**: Black-box, sampling-based consistency
- **Benchmark**: WikiBio (GPT-3 biographies, sentence-level annotation)
- **Models**: GPT-3 (text-davinci-003); NLI/BERTScore/LLM variants for checking
- **Key result**: AUC-PR ~0.78 for sentence-level hallucination detection (best: LLM-Prompting variant using ChatGPT). Table 2, Figure 5.
- **Comparability to us**: Indirect — detects hallucinations in generated text; we predict them from entity geometry *before* generation
- **arXiv**: 2303.08896

### 2. Semantic Entropy (Farquhar et al., Nature 2024)
- **Citations**: ~773
- **Category**: White-box (requires sampling + token log-probs)
- **Benchmark**: TriviaQA, SQuAD, BioASQ, NQ-Open, SVAMP (averaged over 5)
- **Models**: Falcon Instruct (7B, 40B), LLaMA 2 Chat (7B-70B), Mistral 7B
- **Key result**: Best AUROC/AURAC across 5 datasets vs. all baselines including naive token-level entropy. Extended Data Figures.
- **Comparability to us**: Partial — both use embedding-level features to predict hallucination, but semantic entropy operates at generation time (post-hoc) while our geometry operates on the knowledge graph (pre-generation)
- **Nature**: s41586-024-07421-0

### 3. P(True) / P(IK) (Kadavath et al., 2022, Anthropic)
- **Citations**: ~373
- **Category**: White-box (logits)
- **Benchmark**: TriviaQA, Lambada, BIG-Bench
- **Models**: Anthropic LMs (800M–52B)
- **Key result**: 52B model well-calibrated on BIG-Bench; P(True)>50% strongly predictive of correctness. Figures 4-8.
- **Comparability to us**: Indirect — self-evaluation of correctness; we predict from entity features, not model self-assessment

### 4. Inference-Time Intervention / ITI (Li et al., NeurIPS 2023)
- **Citations**: ~200+
- **Category**: White-box, activation intervention (detection+mitigation hybrid)
- **Benchmark**: TruthfulQA (MC1, MC2, open-ended GPT-judge)
- **Models**: LLaMA, Alpaca
- **Key result**: Alpaca truthfulness 32.5% → 65.1% on TruthfulQA (open-ended). Table 1, Figure 3.
- **Comparability to us**: Partial — both work in embedding space, but ITI modifies activations at inference time while we use geometry to select training data. ITI requires labeled truthful/false examples; we derive signal from graph structure.
- **arXiv**: 2306.03341
- **NOTE**: This is primarily mitigation but the probing step is detection. Cite as both.

### 5. INSIDE / EigenScore (Chen et al., ICLR 2024)
- **Citations**: ~100+
- **Category**: White-box, embedding-based
- **Benchmark**: TriviaQA, NQ, CoQA, SQuAD
- **Models**: LLaMA-7B/13B, OPT-6.7B, Falcon-7B
- **Key result**: +5-10pp AUROC over logit-level and language-level baselines. Table 1.
- **Comparability to us**: Partial — closest conceptual kin. Both use embedding-space properties (they: eigenvalues of response embedding covariance; us: geometric features of entity embeddings in knowledge graph). Key difference: they detect per-response, we predict per-entity/prompt.
- **arXiv**: 2402.03744

### 6. Lookback Lens (Chuang et al., EMNLP 2024)
- **Citations**: ~74
- **Category**: White-box, attention-based
- **Benchmark**: XSum, NQ, CNN/DailyMail
- **Models**: LLaMA-2-7B/13B
- **Key result**: Train AUROC 0.987, Test AUROC 0.914, cross-task 0.853 (NQ). Decoding reduces hallucination by 9.6% on XSum. Table 1, Table 2.
- **Comparability to us**: Indirect — attention pattern analysis; we use entity embedding geometry
- **arXiv**: 2407.07071

### 7. FActScore (Min et al., EMNLP 2023)
- **Citations**: ~869
- **Category**: Black-box (evaluation metric / framework)
- **Benchmark**: Custom biography generation (Wikipedia people)
- **Models**: InstructGPT, ChatGPT, GPT-4, Vicuna, Alpaca, +7 others
- **Key result**: ChatGPT achieves only 58% FActScore. Automated estimator <2% error vs. human. Table 2, Figure 3.
- **Comparability to us**: Indirect — evaluation metric, not prediction/mitigation. Our judge consensus panel serves a similar evaluation function.
- **arXiv**: 2305.14251

### 8. SAPLMA / "LLM Knows When Lying" (Azaria & Mitchell, Findings of EMNLP 2023)
- **Citations**: ~200+
- **Category**: White-box, hidden-state probing
- **Benchmark**: Custom true/false statements across 6 topics
- **Models**: OPT-6.7B/13B, LLaMA-13B
- **Key result**: 71-83% accuracy distinguishing true/false generated statements. Table 1.
- **Comparability to us**: Partial — both analyze internal representations, but they probe hidden states of the generating model while we analyze the knowledge graph topology independently of the model.
- **arXiv**: 2304.13734

---

## AXIS 2: PROMPT-BASED MITIGATION

### 1. Chain-of-Thought / CoT (Wei et al., NeurIPS 2022)
- **Citations**: ~14,400
- **Category**: Few-shot reasoning prompting
- **Benchmark**: GSM8K, SVAMP, AQuA, StrategyQA, ARC, CSQA
- **Models**: PaLM-540B, LaMDA-137B, GPT-3
- **Key result**: GSM8K: 17.9% → 58.1% (+40.2pp) with PaLM-540B. New SOTA.
- **Comparability to us**: Partial — our V4 tested 5 prompt prefixes on entity-level hallucination (different task domain). CoT primarily helps reasoning tasks. Important context: ACL Findings 2025 showed CoT can *obscure* hallucination detection cues.
- **arXiv**: 2201.11903

### 2. Self-Consistency (Wang et al., ICLR 2023)
- **Citations**: ~3,500
- **Category**: Multi-sample voting
- **Benchmark**: GSM8K, SVAMP, AQuA, StrategyQA, ARC
- **Models**: PaLM-540B, GPT-3, LaMDA-137B, UL2-20B
- **Key result**: +17.9% over CoT on GSM8K, +11.0% SVAMP, +12.2% AQuA. Consistent across 4 model families.
- **Comparability to us**: Indirect — aggregation-based, requires multiple samples. Our prompt prefixes are single-shot. Different mechanism entirely.
- **arXiv**: 2203.11171

### 3. Chain-of-Verification / CoVe (Dhuliawala et al., ACL 2024 Findings)
- **Citations**: ~308
- **Category**: Multi-step verification pipeline
- **Benchmark**: Wikidata list questions, MultiSpanQA (418 q), biography generation (FactScore)
- **Models**: LLaMA-65B
- **Key result**: Hallucinated negatives 2.95 → 0.68/response (two-step variant, Wikidata). FactScore 55.9 → 71.4 (+15.5pp, factor+revise variant, biography). Note: 63.7 is CoVe (factored), not baseline.
- **Comparability to us**: Partial — both reduce entity-level hallucination. CoVe uses multi-step self-verification; we use single-shot prefix + fine-tuning. CoVe is inference-time compute-heavy; ours bakes in via training.
- **arXiv**: 2309.11495

### 4. Self-Refine (Madaan et al., NeurIPS 2023)
- **Citations**: ~2,548
- **Category**: Iterative self-feedback
- **Benchmark**: 7 diverse tasks (dialogue, code, math, etc.)
- **Models**: GPT-3.5, ChatGPT, GPT-4
- **Key result**: ~20% absolute improvement on average across 7 tasks vs. single-pass.
- **Comparability to us**: Indirect — iterative refinement across diverse tasks; we target entity hallucination specifically
- **arXiv**: 2303.17651

### 5. Ask Me Anything / AMA (Arora et al., ICLR 2023)
- **Citations**: ~252
- **Category**: Question reformulation + aggregation
- **Benchmark**: 20 NLP benchmarks including SuperGLUE
- **Models**: GPT-J-6B, EleutherAI, BLOOM, OPT, T0
- **Key result**: +10.2% avg over few-shot baseline. GPT-J-6B matched few-shot GPT-3-175B on 15/20 benchmarks.
- **Comparability to us**: Indirect — different task setup, different mechanism
- **arXiv**: 2210.02441

### 6. SelfCheckGPT (Manakul et al., EMNLP 2023)
- *Also listed under Detection. See Axis 1 #1.*
- Relevant here as: can be composed with rejection/regeneration for mitigation pipeline.

### 7. Self-Alignment for Factuality (Zhang et al., ACL 2024)
- **Citations**: ~50+
- **Category**: Self-evaluation prompting (hybrid: prompt + DPO)
- **Benchmark**: TruthfulQA (MC + open-ended), BioGEN (FactScore)
- **Models**: LLaMA-7B, LLaMA2-7B
- **Key result**: TruthfulQA MC: +13% accuracy over base LLaMA-7B. BioGEN: +4% FactScore.
- **Comparability to us**: Partial — hybrid method with prompt-based self-eval component. Our prefix experiment is pure prompting (V4); our fine-tuning (V5) is LoRA, not DPO.
- **arXiv**: 2402.09267

### 8. RECITE (Sun et al., ICLR 2023)
- **Citations**: ~200+
- **Category**: Recitation-augmented generation
- **Benchmark**: NaturalQuestions, TriviaQA, HotpotQA (closed-book)
- **Models**: PaLM-540B, UL2-20B, code-davinci-002
- **Key result**: Comparable to BM25-based retrieval on closed-book QA.
- **Comparability to us**: Indirect — closed-book alternative to RAG. Different mechanism from our prefix approach.
- **arXiv**: 2210.01296

---

## AXIS 3: FINE-TUNING / TRAINING-BASED MITIGATION

### 1. R-Tuning (Zhang et al., NAACL 2024 — Outstanding Paper)
- **Citations**: ~120-180
- **Category**: Refusal-aware instruction tuning
- **Benchmark**: ParaRel, MMLU + OOD generalization
- **Models**: OpenLLaMA-3B, LLaMA-7B
- **Key result**: Significantly outperforms vanilla IT in Average Precision (AP) on in-domain and OOD. Refusal transfers as meta-skill. Table 1 (AP scores, not raw accuracy — nuanced comparison).
- **Comparability to us**: **CLOSEST COMPARATOR**. Both teach models to abstain on uncertain knowledge. Key difference: R-Tuning identifies unknowns via train-time probing (model can/can't answer); we identify them via geometric features of entity embeddings (centrality, density). Our geometric taxonomy adds *why* some prompts are harder to fix.
- **arXiv**: 2311.09677
- **PAYWALL STATUS**: Free (arXiv + ACL Anthology). Exact numbers from Table 1 should be verified.

### 2. FactTune (Tian et al., ICLR 2024)
- **Citations**: ~200+
- **Category**: DPO on auto-generated factuality preferences
- **Benchmark**: Biography generation (FActScore), medical QA
- **Models**: Llama-2-7B-Chat, Llama-2-13B-Chat
- **Key result**: 58% reduction in factual error rate (biography). 40% reduction (medical QA). At 7B: 17.06 correct facts, 2.00 errors per biography.
- **Comparability to us**: Partial — both fine-tune for factuality, but FactTune uses DPO with auto-generated preferences while we use LoRA SFT with geometry-guided best-per-prompt selection. Different training signal.
- **arXiv**: 2311.08401

### 3. InstructGPT / RLHF (Ouyang et al., NeurIPS 2022)
- **Citations**: ~7,000+
- **Category**: SFT + reward model + PPO
- **Benchmark**: TruthfulQA, human preference evals
- **Models**: GPT-3 (1.3B–175B)
- **Key result**: TruthfulQA: 21% → 42% truthful (2x improvement). Hallucination 41% → 21% on closed-domain. BUT increased hallucination on some open-ended tasks.
- **Comparability to us**: Indirect — RLHF is a general alignment approach, not hallucination-specific. Our fine-tuning is targeted at entity-level hallucination with geometry-guided data curation.
- **arXiv**: 2203.02155

### 4. FLAME (Dhuliawala et al., NeurIPS 2024)
- **Citations**: ~40-60
- **Category**: Factuality-aware SFT + DPO
- **Benchmark**: Biography generation (FActScore), AlpacaFact, FAVA, AlpacaEval
- **Models**: Llama-2-Chat-70B
- **Key result**: +5.6 FActScore improvement over standard DPO without sacrificing instruction-following (51.2% vs 50.4% AlpacaEval).
- **Comparability to us**: Partial — both address the problem that SFT on novel knowledge encourages hallucination. FLAME filters training data by model familiarity; we select training examples by geometric features + prompt prefix effectiveness.
- **arXiv**: 2405.01525

### 5. Mask-DPO (ICLR 2025)
- **Citations**: ~10-20 (very recent)
- **Category**: Sentence-level masked DPO
- **Benchmark**: ANAH test set, biography generation (FActScore)
- **Models**: Llama-3.1-8B-Instruct
- **Key result**: ANAH: 49.19% → 77.53% (+28.3pp). Surpasses Llama-3.1-70B (53.44%). Standard DPO only reaches 68.44%. OOD biography: +9.1pp FActScore.
- **Comparability to us**: Partial — fine-grained factuality alignment. Different mechanism (sentence-level DPO masking vs. our LoRA SFT).
- **arXiv**: 2503.02846

### 6. Constitutional AI / CAI (Bai et al., 2022, Anthropic)
- **Citations**: ~2,500+
- **Category**: Self-critique SFT + RLAIF
- **Benchmark**: TruthfulQA, HHH evals
- **Models**: Anthropic internal models
- **Key result**: TruthfulQA ~58% truthfulness. Primarily harmlessness-focused; hallucination reduction is secondary.
- **Comparability to us**: Indirect — general alignment, not hallucination-specific
- **arXiv**: 2212.08073

### 7. Self-RAG (Asai et al., ICLR 2024)
- **Citations**: ~500+
- **Category**: Fine-tune for retrieval + reflection tokens (hybrid)
- **Benchmark**: PopQA, TriviaQA, PubHealth, ARC, ASQA
- **Models**: Llama-2-7B/13B (fine-tuned)
- **Key result**: PopQA: 14.7% → 55.8%. TriviaQA: 47.0% → 69.3%. Biography factuality: 80% (vs. ChatGPT 71%).
- **Comparability to us**: Indirect — hybrid FT+retrieval. We operate in closed-book setting without retrieval infrastructure.
- **arXiv**: 2310.11511

### 8. Fine-Tuning Paradox (Gekhman et al., EMNLP 2024)
- **Category**: Empirical finding (not a method, but critical context)
- **Key finding**: Fine-tuning on *new* knowledge linearly increases hallucination tendency.
- **Relevance to us**: Our approach avoids this — we fine-tune on behavioral patterns (entity skepticism), not new facts. This is an important methodological distinction to highlight.
- **arXiv**: 2405.05904

---

## SURVEYS

### 1. Huang et al. (2023) — Most Cited
- "A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions"
- ACM TOIS, arXiv:2311.05232
- ~1,868 citations
- Broadest taxonomy. Detection + mitigation organized by stage (data/training/inference).

### 2. Zhang et al. (2023) — "Siren's Song"
- Computational Linguistics, arXiv:2309.01219
- ~814 citations
- Connects detection and mitigation; emphasis on training data memorization.

### 3. Tonmoy et al. (2024) — Most Useful for Our Table
- "A Comprehensive Survey of Hallucination Mitigation Techniques in Large Language Models"
- arXiv:2401.01313
- ~166 citations
- **Gold mine**: 32+ methods comparison table organized by: prompt engineering with RAG, self-refinement, training-based.

### 4. Alansari & Luqman (2025) — Most Recent
- arXiv:2510.06265
- Recent, lower count. Full lifecycle taxonomy.

---

## BENCHMARK BASELINES

### TruthfulQA (Lin et al., 2022) — 817 questions, 38 categories
| Model | Score | Metric |
|---|---|---|
| Mixtral 8x7B Instruct | 73.9% | MC2 |
| Llama 2 70B Chat | 44.9% | MC2 |
| Llama 2 7B Chat | 45.3% | MC2 |
| Llama 3 8B | ~44% | MC2 |
| InstructGPT 175B | ~42% | Truthful (GPT-judge) |
| GPT-3 175B | ~21% | Truthful (GPT-judge) |
| Alpaca + ITI | 65.1% | Truthful (GPT-judge) |

### SimpleQA (OpenAI, 2024) — 4,326 questions
| Model | Correct | Notes |
|---|---|---|
| GPT-4.5 | 62.5% | |
| o1-preview | 42.7% | Best at release |
| GPT-4o | 38.2% | |
| Claude 3.5 Sonnet | 28.9% | 36.1% wrong |
| Llama 3.1 70B | ~20% | Community evals |
| Mixtral | — | No published score |

### HaluEval (Li et al., 2023) — 35,000 samples
| Task | ChatGPT Baseline | With Knowledge |
|---|---|---|
| QA | 62.59% | 76.83% |
| General (generation) | 19.5% hallucination rate | — |

---

## RAG BASELINES (for "why not just use RAG?" response)

| Paper | Year | Key Result |
|---|---|---|
| Original RAG (Lewis et al., NeurIPS 2020) | 2020 | NQ: 44.5 EM (vs. 41.5 DPR) |
| Shuster et al., Findings EMNLP 2021 | 2021 | 60%+ reduction in factual error in dialogue |
| Self-RAG (Asai et al., ICLR 2024) | 2024 | 80% biography factuality (vs. ChatGPT 71%) |

---

## KEY GAPS OUR THESIS FILLS

1. **No prior work predicts hallucination *difficulty*** — existing detection methods predict presence/absence. Our bridge analysis (AUC=0.86) predicts which hallucinations resist mitigation.

2. **No geometric taxonomy of hallucination** — INSIDE/EigenScore analyze embedding covariance of *responses*; we analyze geometric features of the *knowledge graph* (pre-generation).

3. **No prompt-to-weights distillation pipeline** — existing work treats prompting and fine-tuning as separate. We show prompt prefix effects can be distilled into LoRA weights (V4→V5 pipeline).

4. **R-Tuning comparison**: R-Tuning teaches refusal via train-time probing; we teach refusal via geometry-guided best-per-prompt selection. Complementary mechanisms.

---

## PAPERS REQUIRING PAYWALL VERIFICATION

All papers listed above are available on arXiv (free access). Specific quantitative results to verify from the actual PDFs:

1. **R-Tuning Table 1**: Exact AP scores on ParaRel/MMLU for OpenLLaMA-3B and LLaMA-7B. The search results report AP rather than raw accuracy, making comparison nuanced.
2. **Semantic Entropy**: Exact AUROC values are in Extended Data Figures and Supplementary Tables (main paper uses figures). Worth pulling exact numbers.
3. **ITI Table 1**: Verify the 32.5% → 65.1% improvement and conditions (which model variant, which TruthfulQA metric).

---

## CITATION COUNTS CAVEAT

All citation counts are approximate from Semantic Scholar (March 2026). Google Scholar counts will differ (typically higher). Verify exact counts before thesis submission.
