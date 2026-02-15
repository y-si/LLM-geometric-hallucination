# Next Steps: Prompt Distillation for Hallucination Reduction

Based on professor feedback, December 2024.

## Research Direction

Our project found that **geometric properties of embedding space predict hallucinations** across 10 frontier models. The natural next step: **can we actually reduce hallucinations using this knowledge?**

---

## Research Agenda

### 1. Select an Open-Source Model That Hallucinates

Use an open-source model from our benchmark:
- **Mixtral 8x7B** (11.8% hallucination rate)
- **Llama 4 Maverick** (5.79% hallucination rate)

Open-source is key because we can fine-tune and inspect weights.

### 2. Find General Ways to Prompt It to Be More Careful

Develop system prompts or prefixes that reduce hallucination rates.

Example prompt strategies to test:
- "If uncertain, say 'I don't know' rather than guessing"
- "Only state facts you are confident about"
- "Acknowledge when a question involves fictional or nonexistent entities"

Evaluate which prompt strategies consistently lower hallucination rates across prompt categories.

### 3. Prompt Distillation

Once effective prompts are found:
1. Generate outputs from the model **with** the careful prompt prefix
2. **Fine-tune** the model on these outputs (LoRA/QLoRA)
3. The goal: internalize the "careful" behavior so the model is safer *without* needing the prompt at inference time

### 4. Test Generalization

Evaluate whether the fine-tuned model's improved behavior generalizes to:
- Held-out prompts from our benchmark
- Entirely new evaluation datasets (TruthfulQA, HaluEval, etc.)
- Different prompt categories than trained on

### 5. Establish Baselines

Compare our intervention against:
- Vanilla model (no intervention)
- Simple refusal prompt ("Only answer if certain")
- Chain-of-thought prompting
- Retrieval-augmented generation (RAG)
- Existing hallucination mitigation methods

### 6. Adversarial Testing ("Poke Holes")

Stress-test the approach:
- What prompts break the intervention?
- Can adversarial inputs bypass the safety gains?
- Edge cases and failure modes?

Our initial adversarial robustness experiment (0% hallucination on 50 perturbations) is a starting point.

---

## The Critical Tradeoff: Correctness vs. Safety

A model can reduce hallucinations by refusing everything—that's not useful.

### Key Metric Graph

```
Correctness Rate (X) vs Safety Rate (Y = 1 - Hallucination Rate)

        |                    * Goal: High correctness + High safety
   1.0  |                * Fine-tuned?
Safety  |            o With prefix
        |        . Baseline (no intervention)
        |    x Over-cautious (refuses too much)
   0.0  +------------------------------------
        0.0                              1.0
                    Correctness
```

### What to Measure

For each intervention (no prefix, with prefix, fine-tuned):
- **Correctness rate**: Ability to answer correctly when answer exists
- **Hallucination rate**: Rate of fabricated/incorrect responses
- **Refusal rate**: Rate of "I don't know" responses

Plot **1 - Hallucination Rate** vs **Correctness Rate** to visualize the tradeoff.

The ideal intervention moves toward the **upper right corner** (fewer hallucinations AND still correct), not just trading correctness for safety.

---

## Concrete Research Plan

| Phase | Task | Output |
|-------|------|--------|
| 1 | Pick open-source model (Mixtral or Llama) | Baseline hallucination rate |
| 2 | Design 3-5 "careful" prompt prefixes | Prompt library |
| 3 | Evaluate prefixes on 449 prompts | Hallucination vs correctness curves |
| 4 | Generate training data with best prefix | Fine-tuning dataset |
| 5 | Fine-tune model (LoRA/QLoRA) | Distilled model |
| 6 | Evaluate on held-out + new benchmarks | Generalization results |
| 7 | Compare to baselines (CoT, RAG, etc.) | Intervention comparison |
| 8 | Adversarial testing | Robustness analysis |

---

## Deliverables

- Blog post summarizing findings
- Paper submission (if results are strong)
- Open-source fine-tuned model (if successful)

---

## Connection to Current Work

This builds directly on our geometric hallucination prediction:
- We identified **which prompts are risky** (high centrality, low curvature)
- Now we test **whether we can make models safer on those risky prompts**
- The geometric features could inform which prompts to prioritize for fine-tuning data

---

# Plan: Prompt Prefix Experiment (Phases 1-3)

## Context

Our V3 experiment proved that geometric embedding properties predict hallucinations across 10 frontier models. The next step: **can we reduce hallucinations using "careful" system prompts, and eventually distill that behavior via fine-tuning?**

This plan covers Phases 1-3: extract baselines, design prompt prefixes, and evaluate them on both Mixtral 8x7B (11.8% hallucination) and Llama 4 Maverick (5.79%) using our existing 449-prompt benchmark via Together AI.

---

## Files to Modify (1)

| File | Change |
|------|--------|
| `src/models/multi_model_client.py` | Add `system_prompt` parameter to `generate()` (backward-compatible, default=None) |

## Files to Create (7)

| File | Purpose |
|------|---------|
| `experiments/prefix_configs.yaml` | Define the 5 prompt prefixes |
| `src/evaluation/extract_baselines.py` | Extract correctness/hallucination/refusal rates from V3 data |
| `src/pipeline/run_prefix_generation.py` | Generation pipeline with system_prompt support |
| `src/pipeline/run_prefix_judging.py` | Judging wrapper for prefix experiment results |
| `src/pipeline/aggregate_prefix_results.py` | Merge judged results into master CSV |
| `src/evaluation/prefix_analysis.py` | Analysis, statistical tests, tradeoff plots |
| `scripts/run_prefix_experiment.py` | Single-entry orchestration script |

---

## Step 1: Add `system_prompt` to MultiModelClient

Modify `src/models/multi_model_client.py` — add `system_prompt: str = None` parameter to `generate()`:
- **Anthropic**: pass as `system=system_prompt` kwarg
- **OpenAI/Together**: prepend `{"role": "system", "content": system_prompt}` to messages list
- Default `None` preserves all existing behavior (no other files need changes)

## Step 2: Define 5 Prompt Prefixes (`experiments/prefix_configs.yaml`)

Each targets a distinct hallucination reduction mechanism, ordered least → most restrictive:

| Key | Name | Strategy |
|-----|------|----------|
| `epistemic_humility` | Epistemic Humility | Light nudge: "say I don't know rather than guessing" |
| `fact_grounded` | Fact-Grounded | "Don't fabricate names, dates, statistics" |
| `entity_aware` | Entity-Aware | "Consider whether the entity actually exists before answering" |
| `structured_caution` | Structured Caution | Explicit numbered rules combining all strategies |
| `cot_verification` | CoT Verification | "Before answering, verify your claims" (CoT baseline) |

## Step 3: Extract Baselines (`src/evaluation/extract_baselines.py`)

Read existing `results/v3/multi_model/all_models_results.csv` for Mixtral + Llama. Compute per-model and per-category: correctness rate, hallucination rate, refusal rate. Save to `results/v4_prefix_experiment/baselines.csv`.

## Step 4: Generation Pipeline (`src/pipeline/run_prefix_generation.py`)

Follows `run_multi_model_generation.py` patterns (resume capability, retry with backoff). Key difference: passes `system_prompt` from prefix config to `client.generate()`.

```
python -m src.pipeline.run_prefix_generation \
    --model-key mixtral-8x7b \
    --prefix-key epistemic_humility \
    --output-dir results/v4_prefix_experiment
```

Also supports `--all-prefixes` to run all 5 for a given model.

Output: `results/v4_prefix_experiment/{model_key}/{prefix_key}/answers.jsonl`

## Step 5: Judging Pipeline (`src/pipeline/run_prefix_judging.py`)

Walks `results/v4_prefix_experiment/*/*/answers.jsonl`, runs consensus judging (same 3-judge panel as V3: GPT-5.1 + Claude Opus 4.5 + Llama 4 Maverick).

**Llama-as-judge concern**: Use the standard 3-judge panel for everything (including when judging Llama's own outputs) so results are directly comparable to V3 baselines. Include a post-hoc analysis checking whether Llama's individual judgments of its own outputs are biased vs the other two judges.

Output: `results/v4_prefix_experiment/{model_key}/{prefix_key}/judged_answers.jsonl`

## Step 6: Aggregation (`src/pipeline/aggregate_prefix_results.py`)

Merge all judged results + geometry features into `results/v4_prefix_experiment/all_prefix_results.csv`. Add columns: `is_hallucinated`, `is_correct`, `is_refused`.

## Step 7: Analysis & Visualization (`src/evaluation/prefix_analysis.py`)

Key outputs:
1. **Tradeoff plot**: Correctness Rate (X) vs Safety Rate (Y=1-hallucination) — each point is a (model, prefix) combo
2. **Per-category heatmap**: Hallucination rate reduction by prefix × category
3. **Refusal rate bar chart**: Cost of each prefix in over-caution
4. **Statistical tests**: McNemar's test for paired prompt-level significance (same 449 prompts, baseline vs prefix)

Output: `results/v4_prefix_experiment/analysis/`

## Step 8: Orchestration (`scripts/run_prefix_experiment.py`)

Single entry point to run individual phases or the full pipeline:
```
python scripts/run_prefix_experiment.py --phase all
python scripts/run_prefix_experiment.py --phase generate --model mixtral-8x7b
```

---

## Directory Structure

```
results/v4_prefix_experiment/
    baselines.csv
    mixtral-8x7b/
        epistemic_humility/
            answers.jsonl
            judged_answers.jsonl
        fact_grounded/
            ...
        (5 prefix dirs)
    llama-4-maverick-17b/
        (same structure)
    all_prefix_results.csv
    analysis/
        tradeoff_curve.png
        category_heatmap.png
        refusal_rates.png
        statistical_tests.csv
        prefix_metrics_summary.csv
```

## API Cost Estimate

- **Generation**: 2 models x 5 prefixes x 449 prompts = **4,490 Together AI calls**
- **Judging**: 4,490 x 3 judges = **~13,470 calls** (OpenAI + Anthropic + Together)
- All fully resumable if interrupted

## Verification

1. Run baseline extraction, confirm rates match known values (Mixtral: 11.8%, Llama: 5.79%)
2. Test `system_prompt` change with a single prompt on each model before full run
3. After generation, spot-check a few answers to confirm prefix is influencing behavior
4. After judging + aggregation, verify the tradeoff plot shows meaningful variation across prefixes
