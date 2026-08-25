# Thesis → Research Paper

## Target Venue
Boaz's guidance (Apr 2026): NeurIPS 2026 too soon, ICML/ICLR 2026 main deadlines passed. Realistic targets:
- **ICLR 2027** (main conference, deadline likely Sep/Oct 2026)
- **NeurIPS 2026 workshop** (deadline likely Aug-Sep 2026)
- Relevant workshops: TrustML, Reliable & Responsible Foundation Models, Geometry in ML

## Status
- Thesis submitted Mar 27, 2026
- Boaz approved pursuing publication, meeting TBD to discuss target/format

---

## What the thesis has (strengths to preserve)
1. Three-claim arc with statistical backing
2. Within-category density predicts hallucination (p<10^-5) AND fixability (p=0.0017)
3. Fine-tuning pipeline: 81-89% hallucination reduction, cross-domain transfer (TruthfulQA)
4. Template ablation: behavioral caution, not pattern memorization
5. Decontamination analysis addressing entity overlap

## What a paper needs that the thesis doesn't
- [ ] Tighter framing (1 core contribution, not 3 chapters)
- [ ] Related work that positions against concurrent/recent papers (not a lit review chapter)
- [ ] 8-page format discipline
- [ ] Stronger baselines / comparisons to existing hallucination detection methods
- [ ] Ablations reviewers will ask for

---

## Potential improvements beyond format conversion

### 1. Theoretical grounding (lightweight)
- Formalize density-hallucination connection for simplified model class
- Even a toy proof (single-layer attention, Gaussian keys) adds credibility
- Connects to epistemic uncertainty / generalization theory literature

### 2. Stronger baselines
- Compare geometric features against existing hallucination detectors:
  - P(true) / semantic entropy (Kadavath et al., Kuhn et al.)
  - Self-consistency / sampling-based methods
  - Probe-based methods (internal representations)
- If density beats or complements these → much stronger contribution
- If it doesn't → still publishable as "geometry provides complementary signal"

### 3. More models
- Current: Mixtral 8x7B, Llama 4 Maverick
- Adding 2-3 more models (different scales/families) strengthens generalizability claim
- Especially: a model where the finding DOESN'T hold would be informative

### 4. Tighten the geometric story
- Current thesis has density + oppositeness + nearest-neighbor distance
- Paper should lead with density (the winner) and use others as ablation
- Consider: can we define a single "geometric risk score" combining features?

### 5. Causal direction
- Current evidence is correlational (low density ↔ hallucination)
- Can we intervene? E.g., synthetically move an embedding to a higher-density region and show hallucination decreases?
- This would be a substantial new experiment but very compelling

### 6. Scale the fine-tuning story
- Current: fine-tuned on ~2.4K examples
- Scaling curve: does 500 examples suffice? 100? Where's the knee?
- Connects to data efficiency narrative

---

## Priority tiers for improvements

### High ROI (do these regardless of venue)
1. **Stronger baselines** — Compare density against established hallucination detection methods (semantic entropy, P(true), self-consistency, probe-based). Reviewers will reject without this. If density is competitive or complementary, contribution is rock-solid.
2. **More models** — 2 models is thin. Add 2-3 more (different scales/families: a 7B, a 70B, maybe closed-source via API). Turns an observation into a generalizable finding.
3. **Tighten to one story** — Lead with "embedding geometry predicts hallucination." Fine-tuning pipeline = downstream application, not co-equal claim. 8 pages demands focus.

### Medium ROI (discuss with Boaz)
4. **Lightweight theory** — Proposition showing density-uncertainty connection for a simplified model class (e.g., single-layer attention with Gaussian keys). Not a full proof, but theoretical plausibility. Bridges the "purely empirical" gap.
5. **Composite geometric risk score** — Combine density + other features into a single calibrated predictor. More practical/deployable framing.

### Low ROI (skip unless Boaz wants it)
6. **Causal intervention** — Synthetically move embeddings to higher-density regions, show hallucination decreases. Compelling but probably a separate paper.
7. **Fine-tuning scaling curves** — How few examples suffice? Interesting but secondary to geometry story.

---

## Boaz meeting agenda — Friday May 1, 2026

### Decisions to align on
1. **Venue**: Workshop (4-6pp, lower bar, faster turnaround, good for feedback) vs. main conference (8pp, higher impact, needs stronger baselines)? Workshop at NeurIPS 2026 → deadline ~Aug/Sep. ICLR 2027 main → deadline ~Oct.
2. **Paper scope**: Geometry-predicts-hallucination only? Or include the fine-tuning pipeline? Single-claim papers are cleaner but the pipeline story is what makes it practical.
3. **Co-authors**: Boaz, Sunny, anyone else? Sunny shaped the experimental design significantly.
4. **Division of labor**: What does Boaz want to be involved in vs. what do you execute independently?

### Things to get Boaz's read on
5. **Baseline comparison gap**: The thesis doesn't compare against semantic entropy, P(true), etc. Is this a dealbreaker for the venue we're targeting, or acceptable for a workshop?
6. **Theory angle**: Worth adding a theoretical proposition? Boaz is a theorist — he may have ideas for formalizing density → uncertainty that we haven't considered. Or he may say "don't bother, empirical is fine for this venue."
7. **More models**: How many is enough? 4-5 total? Does he have preferences on which models (open vs. closed, scale range)?
8. **Timeline**: If targeting ICLR 2027 (~Oct deadline), that's 5 months. Enough for baselines + more models + writing? Or is a workshop more realistic given your post-graduation schedule?

### Things to flag
9. **Known weaknesses a reviewer will hit**: AUC ~0.71 for density alone (useful signal but not a standalone detector), within-category Bonferroni doesn't survive for bridge analysis (24 tests), two-model generalizability
10. **Strongest selling points**: density predicts both hallucination AND fixability (unique), cross-domain transfer to TruthfulQA, behavioral caution framing is novel

---

## Meeting strategy notes

**Don't go in with all the answers.** The point is to let Boaz shape strategy — he knows what reviewers at these venues care about.

Key priorities for the meeting:
1. **Venue decision** — determines everything. Workshop = doable in weeks. Main conference = new experiments needed. What's realistic post-graduation?
2. **Get his theory instinct** — Don't pitch a specific formalization. Ask "do you see a way to formalize the density-hallucination connection?" He may see an angle we haven't, or say empirical is fine. Either answer saves time.
3. **Baselines question** — Be upfront that we didn't compare against existing hallucination detection methods (see explainer below). Ask: must-do, or is "geometry as complementary lens" enough for the venue?
4. **His involvement level** — Advising from a distance vs. hands-on? Affects timeline and planning.

---

## Concurrent work: geometry + hallucination (Feb-Mar 2026)

There's been a burst of "geometry meets hallucination" papers. **None are pre-generation.**

| Paper | Date | Approach | Pre-gen? |
|---|---|---|---|
| Semantic Entropy (Kuhn et al., Nature 2024) | 2024 | Sample multiple outputs, cluster by meaning, measure entropy | No — needs multiple generations |
| P(true) (Kadavath et al., 2022) | 2022 | Ask model "is this true?" after generating | No — needs generation + self-eval |
| Geometric Uncertainty (Phillips et al.) | Sep 2025 | Convex hull volume of sampled response archetypes | No — needs multiple generations |
| OOD → Hallucination (Liu et al.) | Feb 2026 | Treat hallucination as OOD in internal representations | No — needs internal states during generation |
| Geometric Taxonomy (Marín) | Mar 2026 | Output embedding displacement (DGI, AUROC=0.958) | No — analyzes output geometry |
| Cluster Geometry (Korun) | Feb 2026 | Three-type taxonomy via cluster structure across 11 models | No — static embedding analysis, not per-prompt prediction |
| Geometric Analysis of Small LMs | Feb 2026 | Hallucination patterns in small model embeddings | No — post-hoc analysis |
| "What do Geometric Metrics Measure?" | Feb 2026 | Critique paper questioning geometric metrics | N/A — meta-analysis |

**Our differentiator**: Pre-generation prediction from input embedding density alone. No generation needed. Computationally cheap. Usable for:
- Inference-time risk flagging (before spending compute)
- Training data curation (filter high-risk prompts)
- Routing to stronger/specialized models
- Complementary to post-hoc methods (different information source)

**Key refs to cite and position against:**
- arxiv:2602.07253 (OOD → Hallucination, geometric view)
- arxiv:2602.13224 (Geometric taxonomy)
- arxiv:2602.14259 (Embedding cluster geometry)
- arxiv:2509.13813 (Geometric uncertainty)
- arxiv:2602.09158 (Critique of geometric metrics — must address)

---

## Boaz Meeting Notes — May 1, 2026

### Core reframing
- **Paper pitch**: "Predicting hallucination risk before generation, using prompt-level geometric features"
- Geometry = tool, prediction = goal
- Contributions: (1) benchmark dataset for evaluating hallucination prediction, (2) geometric method that's computationally efficient, (3) practical applications (inference-time flagging, training data curation)
- Must have baselines to beat: "here are existing approaches, here's something better"

### Key new experiment: "Hallucination is a property of the prompt, not the model"

> **⚠️ Superseded 2026-08-24 — historical record, do not use as the current design.**
> This section preserves Boaz's May 1 wording verbatim. Both the *claim* and the
> *estimator* below have since been corrected:
> - **Claim**: use "prompt difficulty ordering is largely model-invariant." The
>   wording in this heading is false as stated — models differ substantially in
>   absolute hallucination *rate*.
> - **Estimator**: pooled Kendall's tau across heterogeneous categories mostly
>   measures benchmark stratification, not model agreement. Use blocked
>   within-category τ_b, attenuation-corrected against a measured noise ceiling.
>
> Current design: `PHASE_0.5_SPEC.md`. Summary: `PLAN.md` §2.

- Take 100-1000 prompts, 5-10 models
- For each prompt, sample multiple times per model → compute P(hallucinate) per prompt per model
- Sort prompts by hallucination probability for each model
- Compute Kendall's tau between model orderings
- If tau is high → hallucination propensity is prompt-driven, not model-driven
- This would be a strong motivating result for the whole paper

### Other directions
- Run on external datasets beyond our own benchmark
- "Model harness" — framing the pipeline as a reusable tool
- Need more models (5-10 range, not just 2)

### Logistics
- Boaz offering OpenAI credits (send him email for ChatGPT account)
- Boaz says he's been out of the loop — reach out to Sunny again for the paper, but Boaz will have limited time
- Codex access incoming

---

### my notes

- paper needs to be more focused, more bottom line
- focus just on predicting hallucination risk based on prompt features and focusing on that to do work where you say "here are baselines, here's something better" and you focus only on this approach (the contributions will be a dataset that we can evaluate and a method based on geometry that could be computationally efficient, prompting could work but embedding too) --> twist on "instead of preventing/detecting hallucination after the fact, detecting in advance could be useful. which prompts could lead to hallucination" then use that in inference time, in training data, 
- model harness
- predicting hallucinations before they happen
- the focus becomes geometry is a tool, but the goal is prediction and we're providing tools 
- new experiments to run? other datasets beside that i own
- take a datset, create histogram to show hallucination. show its not a property of the model, but of the prompt (one way oculd be: suppose you took a collection of 100-1000 prompts and you took a collection of 5-10 models, for each prompt you sample multiple times in the model to compute teh probablity/fraction of time the model hallucinates. diff models might hallucinate in diff fractions (bigger might hallucinate less, etc) but what i want to do is fr every model, we sort the prompts according to the probability of hallucinations, and you compare some permutation ordering (kendalls tau) between other models. if perpencity to hallucinate is prompt, then this ordering is similar btw other models)
- send boaz the email i use for chatgpt and he'll send me credits holy shit i can use codex 

-(boaz says he's been out of the loop? what)
- reach out to sunny again on the paper bc he will have limited time LOL