"""Step 11B: Overfitting check — compare train vs test accuracy.

Samples 200 V5 training prompts (stratified by category), runs inference
with the best fine-tuned config per model (Mixtral configC, Llama configA),
then judges with the 3-judge consensus panel.

After running, compare train accuracy here vs test accuracy from Step 11
(results/v5_finetuned/{model}/config{X}/judged_answers.jsonl).

Usage:
    # 1. Deploy dedicated endpoints on Together dashboard
    # 2. Run generation + judging:
    python3 scripts/run_v5_overfitting_check.py \
        --model mixtral-8x7b --config C \
        --endpoint <endpoint-string-from-dashboard>

    # Or just generation:
    python3 scripts/run_v5_overfitting_check.py \
        --model mixtral-8x7b --config C \
        --endpoint <endpoint-string> --phase generate

    # Or just judging:
    python3 scripts/run_v5_overfitting_check.py \
        --model mixtral-8x7b --config C --phase judge

    # Then compare:
    python3 scripts/run_v5_overfitting_check.py --phase compare

Output:
    results/v5_finetuned/{model}/config{X}/train_sample_prompts.jsonl
    results/v5_finetuned/{model}/config{X}/train_sample_answers.jsonl
    results/v5_finetuned/{model}/config{X}/train_sample_judged.jsonl
"""

import sys
import json
import time
import random
import argparse
from pathlib import Path
from collections import Counter

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.multi_model_client import MultiModelClient
from src.models.consensus_judge import ConsensusJudge
from src.utils.io import read_jsonl, write_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

V5_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "v5_all.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "results" / "v5_finetuned"

SAMPLE_SIZE = 200
SAMPLE_SEED = 2025

JUDGES_CONFIG = [
    {"provider": "openai", "model": "gpt-5.1"},
    {"provider": "anthropic", "model": "claude-opus-4-5-20251101"},
    {"provider": "together", "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
]

MAX_TOKENS = 4000
TEMPERATURE = 0.7
SAVE_EVERY_GEN = 25
SAVE_EVERY_JUDGE = 10


# ── Sampling ───────────────────────────────────────────────────────────────

def create_stratified_sample(prompts, n, seed):
    """Stratified random sample: proportional to category sizes."""
    rng = random.Random(seed)
    by_cat = {}
    for p in prompts:
        by_cat.setdefault(p["category"], []).append(p)

    total = len(prompts)
    sampled = []
    for cat in sorted(by_cat.keys()):
        cat_prompts = by_cat[cat]
        # Proportional allocation, at least 1 per category
        k = max(1, round(len(cat_prompts) / total * n))
        k = min(k, len(cat_prompts))
        sampled.extend(rng.sample(cat_prompts, k))

    # If rounding gave us slightly too many/few, trim or pad
    if len(sampled) > n:
        rng.shuffle(sampled)
        sampled = sampled[:n]
    elif len(sampled) < n:
        remaining = [p for p in prompts if p not in sampled]
        sampled.extend(rng.sample(remaining, n - len(sampled)))

    return sampled


# ── Generation ─────────────────────────────────────────────────────────────

def run_generation(model_name, config, endpoint, prompts):
    """Generate responses for fine-tuned model on training sample."""
    print(f"\n{'=' * 60}")
    print(f"  GENERATION — {model_name} config{config} (train sample)")
    print(f"  Endpoint: {endpoint}")
    print(f"  Prompts: {len(prompts)}")
    print(f"{'=' * 60}")

    client = MultiModelClient(provider="together", model_name=endpoint)

    output_path = OUTPUT_DIR / model_name / f"config{config}" / "train_sample_answers.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resume
    existing_ids = set()
    if output_path.exists():
        existing_results = read_jsonl(output_path)
        existing_ids = {r["id"] for r in existing_results}
        remaining = len(prompts) - len(existing_ids)
        print(f"  Resuming: {len(existing_ids)} done, {remaining} remaining")

    results = []
    failed = 0

    for prompt_data in tqdm(prompts, desc=f"{model_name}/config{config} train"):
        if prompt_data["id"] in existing_ids:
            continue

        retry_delay = 2
        for attempt in range(3):
            try:
                response = client.generate(
                    prompt=prompt_data["question"],
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    system_prompt=None,
                )

                result = prompt_data.copy()
                result["model"] = model_name
                result["config"] = config
                result["model_answer"] = response
                result["split"] = "train_sample"
                results.append(result)
                break

            except Exception as e:
                error_msg = str(e)
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    print(f"\n  Rate limit, waiting {retry_delay}s...")
                else:
                    print(f"\n  Error on {prompt_data['id']}: {error_msg}")

                if attempt < 2:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"\n  Failed after 3 attempts: {prompt_data['id']}")
                    failed += 1

        # Periodic save
        if len(results) > 0 and len(results) % SAVE_EVERY_GEN == 0:
            _append_results(output_path, results, existing_ids)
            existing_ids.update(r["id"] for r in results)
            results = []

    # Final save
    if results:
        _append_results(output_path, results, existing_ids)
        existing_ids.update(r["id"] for r in results)

    total = len(existing_ids)
    print(f"\n  Done: {total}/{len(prompts)} completed, {failed} failed")
    return total, failed


def _append_results(output_path, results, existing_ids):
    """Append new results to JSONL file."""
    if existing_ids:
        with open(output_path, "a", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        write_jsonl(output_path, results)


# ── Judging ────────────────────────────────────────────────────────────────

def run_judging(model_name, config):
    """Judge train sample responses."""
    answers_path = OUTPUT_DIR / model_name / f"config{config}" / "train_sample_answers.jsonl"
    output_path = OUTPUT_DIR / model_name / f"config{config}" / "train_sample_judged.jsonl"

    if not answers_path.exists():
        print(f"  No train sample answers for {model_name}/config{config}")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  JUDGING — {model_name} config{config} (train sample)")
    print(f"{'=' * 60}")

    answers = read_jsonl(answers_path)
    print(f"  Loaded {len(answers)} answers")

    judge = ConsensusJudge(JUDGES_CONFIG)

    # Resume
    results = []
    existing_ids = set()
    if output_path.exists():
        results = read_jsonl(output_path)
        existing_ids = {r["id"] for r in results}
        remaining = len(answers) - len(existing_ids)
        print(f"  Resuming: {len(existing_ids)} judged, {remaining} remaining")

    for answer_data in tqdm(answers, desc=f"Judging {model_name}/config{config} train"):
        if answer_data["id"] in existing_ids:
            continue

        retry_delay = 2
        for attempt in range(3):
            try:
                judgment = judge.judge(
                    question=answer_data["question"],
                    answer=answer_data["model_answer"],
                    ground_truth=answer_data["ground_truth"],
                    meta_info=answer_data.get("metadata", {}),
                )

                result = {
                    **answer_data,
                    "judge_label": judgment["label"],
                    "judge_confidence": judgment["confidence"],
                    "judge_justification": judgment["justification"],
                    "judge_model": "consensus_panel",
                    "individual_judgments": judgment["individual_judgments"],
                    "agreement_rate": judgment["agreement_rate"],
                    "individual_confidence_avg": judgment["individual_confidence_avg"],
                }
                results.append(result)
                break

            except Exception as e:
                if attempt < 2:
                    print(f"\n  Error judging {answer_data.get('id', '?')}: {e}, retrying...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"\n  Failed: {answer_data.get('id', '?')}: {e}")

        if len(results) > 0 and len(results) % SAVE_EVERY_JUDGE == 0:
            write_jsonl(output_path, results)

    write_jsonl(output_path, results)
    print(f"  Saved {len(results)} judgments")
    return len(results)


# ── Comparison ─────────────────────────────────────────────────────────────

def run_comparison():
    """Compare train sample accuracy vs held-out test accuracy."""
    print(f"\n{'=' * 60}")
    print(f"  OVERFITTING CHECK: TRAIN vs TEST ACCURACY")
    print(f"{'=' * 60}")

    configs = [
        ("mixtral-8x7b", "C"),
        ("llama-4-maverick-17b", "A"),
    ]

    for model_name, config in configs:
        train_path = OUTPUT_DIR / model_name / f"config{config}" / "train_sample_judged.jsonl"
        test_path = OUTPUT_DIR / model_name / f"config{config}" / "judged_answers.jsonl"

        if not train_path.exists():
            print(f"\n  {model_name} config{config}: train sample not found, skipping")
            continue
        if not test_path.exists():
            print(f"\n  {model_name} config{config}: test results not found, skipping")
            continue

        train_results = read_jsonl(train_path)
        test_results = read_jsonl(test_path)

        # Deduplicate test results (same fix as analyze_v5_finetuned.py)
        seen = set()
        test_deduped = []
        for r in test_results:
            if r["id"] not in seen:
                test_deduped.append(r)
                seen.add(r["id"])
        test_results = test_deduped

        train_labels = [r["judge_label"] for r in train_results]
        test_labels = [r["judge_label"] for r in test_results]

        train_correct = train_labels.count(0)
        train_halluc = train_labels.count(2)
        test_correct = test_labels.count(0)
        test_halluc = test_labels.count(2)

        train_acc = train_correct / len(train_results) * 100
        test_acc = test_correct / len(test_results) * 100
        train_hal = train_halluc / len(train_results) * 100
        test_hal = test_halluc / len(test_results) * 100

        gap = train_acc - test_acc

        print(f"\n  {model_name} config{config}:")
        print(f"    {'':20s} {'Train Sample':>15s} {'Test (held-out)':>15s} {'Gap':>10s}")
        print(f"    {'-'*20} {'-'*15} {'-'*15} {'-'*10}")
        print(f"    {'N':20s} {len(train_results):>15d} {len(test_results):>15d}")
        print(f"    {'Accuracy':20s} {train_acc:>14.1f}% {test_acc:>14.1f}% {gap:>+9.1f}pp")
        print(f"    {'Hallucination':20s} {train_hal:>14.1f}% {test_hal:>14.1f}%")

        # Per-category comparison
        train_cats = {}
        for r in train_results:
            cat = r["category"]
            train_cats.setdefault(cat, []).append(r["judge_label"])
        test_cats = {}
        for r in test_results:
            cat = r["category"]
            test_cats.setdefault(cat, []).append(r["judge_label"])

        print(f"\n    {'Category':<30s} {'Train Acc':>10s} {'Test Acc':>10s} {'Gap':>8s}")
        print(f"    {'-'*30} {'-'*10} {'-'*10} {'-'*8}")
        for cat in sorted(set(list(train_cats.keys()) + list(test_cats.keys()))):
            t_labels = train_cats.get(cat, [])
            e_labels = test_cats.get(cat, [])
            t_acc = t_labels.count(0) / len(t_labels) * 100 if t_labels else 0
            e_acc = e_labels.count(0) / len(e_labels) * 100 if e_labels else 0
            print(f"    {cat:<30s} {t_acc:>9.1f}% {e_acc:>9.1f}% {t_acc - e_acc:>+7.1f}pp")

        # Verdict
        if gap <= 5:
            print(f"\n    Verdict: NO OVERFITTING (gap ≤5pp)")
        elif gap <= 15:
            print(f"\n    Verdict: MILD OVERFITTING (gap 5-15pp) — held-out results still valid")
        else:
            print(f"\n    Verdict: SIGNIFICANT OVERFITTING (gap >15pp) — caveat fine-tuning claims")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Step 11B: Overfitting check — train vs test accuracy"
    )
    parser.add_argument(
        "--phase",
        choices=["generate", "judge", "compare", "all"],
        default="all",
        help="Which phase to run (default: all)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Base model name (e.g. mixtral-8x7b)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Config letter (e.g. C)",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help="Dedicated endpoint string from Together dashboard",
    )
    args = parser.parse_args()

    if args.phase == "compare":
        run_comparison()
        return

    if args.phase in ("generate", "all"):
        if not args.model or not args.config:
            print("ERROR: --model and --config required for generation")
            sys.exit(1)
        if not args.endpoint:
            print("ERROR: --endpoint required for generation (deploy on Together dashboard first)")
            sys.exit(1)

    # Load and sample V5 training prompts
    if not V5_PROMPTS_PATH.exists():
        print(f"ERROR: V5 prompts not found at {V5_PROMPTS_PATH}")
        sys.exit(1)

    all_prompts = read_jsonl(V5_PROMPTS_PATH)
    print(f"Loaded {len(all_prompts)} V5 training prompts")

    # Check if sample already exists for this model/config
    sample_path = OUTPUT_DIR / args.model / f"config{args.config}" / "train_sample_prompts.jsonl"
    if sample_path.exists():
        sample = read_jsonl(sample_path)
        print(f"Using existing sample: {len(sample)} prompts from {sample_path}")
    else:
        sample = create_stratified_sample(all_prompts, SAMPLE_SIZE, SAMPLE_SEED)
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(sample_path, sample)
        print(f"Created stratified sample: {len(sample)} prompts")

    cats = Counter(p["category"] for p in sample)
    for cat, n in sorted(cats.items()):
        print(f"  {cat}: {n}")

    if args.phase in ("generate", "all"):
        run_generation(args.model, args.config, args.endpoint, sample)

    if args.phase in ("judge", "all"):
        run_judging(args.model, args.config)

    if args.phase == "all":
        run_comparison()

    print(f"\n{'=' * 60}")
    print(f"  DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
