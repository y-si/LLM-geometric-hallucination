"""Run V5 baseline generation and judging.

Generates responses from Mixtral-8x7B and Llama-4-Maverick-17B on all 2,430
V5 prompts with NO system prefix (bare baseline), then judges each response
with the 3-judge consensus panel (GPT-5.1, Claude Opus 4.5, Llama 4 Maverick).

Reuses the same model clients and judging infrastructure as V4 — no code
duplication of client/judge logic.

Usage:
    export TOGETHER_API_KEY=...
    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...

    # Run both phases (generate + judge):
    python3 scripts/run_v5_baselines.py

    # Run only generation:
    python3 scripts/run_v5_baselines.py --phase generate

    # Run only judging:
    python3 scripts/run_v5_baselines.py --phase judge

    # Filter to a single model:
    python3 scripts/run_v5_baselines.py --model mixtral-8x7b

Output:
    results/v5_baselines/{model}/no_prefix/answers.jsonl
    results/v5_baselines/{model}/no_prefix/judged_answers.jsonl
    results/v5_baselines/baseline_summary.json
"""

import sys
import json
import time
import argparse
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.multi_model_client import get_model_client
from src.models.consensus_judge import ConsensusJudge
from src.utils.io import read_jsonl, write_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

TARGET_MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]

JUDGES_CONFIG = [
    {"provider": "openai", "model": "gpt-5.1"},
    {"provider": "anthropic", "model": "claude-opus-4-5-20251101"},
    {"provider": "together", "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
]

V5_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "v5_all.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "results" / "v5_baselines"

# Generation parameters (matching V4 for comparability)
MAX_TOKENS = 4000
TEMPERATURE = 0.7
SAVE_EVERY_GEN = 25   # periodic save interval for generation
SAVE_EVERY_JUDGE = 10  # periodic save interval for judging


# ── Generation ─────────────────────────────────────────────────────────────

def run_generation(model_key: str):
    """Generate baseline responses for one model (no system prefix)."""
    print(f"\n{'=' * 60}")
    print(f"  GENERATION — {model_key} (no prefix)")
    print(f"{'=' * 60}")

    # Load V5 prompts only
    prompts = read_jsonl(V5_PROMPTS_PATH)
    print(f"  Loaded {len(prompts)} V5 prompts")

    client = get_model_client(model_key)

    output_path = OUTPUT_DIR / model_key / "no_prefix" / "answers.jsonl"
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

    for prompt_data in tqdm(prompts, desc=f"{model_key}/no_prefix"):
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
                result["model"] = model_key
                result["prefix_key"] = "no_prefix"
                result["prefix_name"] = "No Prefix (Baseline)"
                result["system_prompt_used"] = ""
                result["model_answer"] = response
                results.append(result)
                break

            except Exception as e:
                error_msg = str(e)
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    print(f"\n  Rate limit, waiting {retry_delay}s...")
                elif "timeout" in error_msg.lower():
                    print(f"\n  Timeout on {prompt_data['id']}, attempt {attempt + 1}/3")
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

def run_judging(model_key: str):
    """Judge baseline responses for one model."""
    answers_path = OUTPUT_DIR / model_key / "no_prefix" / "answers.jsonl"
    output_path = OUTPUT_DIR / model_key / "no_prefix" / "judged_answers.jsonl"

    if not answers_path.exists():
        print(f"  No answers file for {model_key}, skipping judging")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  JUDGING — {model_key} (no prefix)")
    print(f"{'=' * 60}")

    answers = read_jsonl(answers_path)
    print(f"  Loaded {len(answers)} answers")

    judge = ConsensusJudge(JUDGES_CONFIG)
    print(f"  Judge panel: {', '.join(j['model'].split('/')[-1] for j in JUDGES_CONFIG)}")

    # Resume
    results = []
    existing_ids = set()
    if output_path.exists():
        results = read_jsonl(output_path)
        existing_ids = {r["id"] for r in results}
        remaining = len(answers) - len(existing_ids)
        print(f"  Resuming: {len(existing_ids)} judged, {remaining} remaining")

    for answer_data in tqdm(answers, desc=f"Judging {model_key}"):
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
                    print(f"\n  Error judging {answer_data.get('id', '?')}: {e}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"\n  Failed after 3 attempts: {answer_data.get('id', '?')}: {e}")

        # Periodic save (outside retry loop to avoid duplicates on write failure)
        if len(results) > 0 and len(results) % SAVE_EVERY_JUDGE == 0:
            write_jsonl(output_path, results)

    write_jsonl(output_path, results)
    print(f"  Saved {len(results)} judgments")
    return len(results)


# ── Summary ────────────────────────────────────────────────────────────────

def generate_summary():
    """Generate baseline_summary.json with accuracy by model × category."""
    print(f"\n{'=' * 60}")
    print(f"  BASELINE SUMMARY")
    print(f"{'=' * 60}")

    summary = {"models": {}, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    for model_key in TARGET_MODELS:
        judged_path = OUTPUT_DIR / model_key / "no_prefix" / "judged_answers.jsonl"
        if not judged_path.exists():
            print(f"  {model_key}: no judged results, skipping")
            continue

        results = read_jsonl(judged_path)
        total = len(results)

        # Overall stats
        labels = [r["judge_label"] for r in results]
        correct = labels.count(0)
        partial = labels.count(1)
        hallucination = labels.count(2)
        refusal = labels.count(3)

        model_summary = {
            "total": total,
            "correct": correct,
            "partial": partial,
            "hallucination": hallucination,
            "refusal": refusal,
            "accuracy": correct / total if total > 0 else 0,
            "hallucination_rate": hallucination / total if total > 0 else 0,
            "categories": {},
        }

        # Per-category
        categories = sorted(set(r["category"] for r in results))
        for cat in categories:
            cat_results = [r for r in results if r["category"] == cat]
            cat_total = len(cat_results)
            cat_labels = [r["judge_label"] for r in cat_results]
            cat_correct = cat_labels.count(0)
            cat_halluc = cat_labels.count(2)

            model_summary["categories"][cat] = {
                "total": cat_total,
                "correct": cat_correct,
                "hallucination": cat_halluc,
                "accuracy": cat_correct / cat_total if cat_total > 0 else 0,
                "hallucination_rate": cat_halluc / cat_total if cat_total > 0 else 0,
            }

        summary["models"][model_key] = model_summary

        # Print
        print(f"\n  {model_key}:")
        print(f"    Overall: {correct}/{total} correct ({correct/total*100:.1f}%), "
              f"{hallucination} hallucinations ({hallucination/total*100:.1f}%)")
        print(f"    {'Category':<30s} {'N':>5s} {'Acc':>7s} {'Halluc':>7s}")
        print(f"    {'-'*30} {'-'*5} {'-'*7} {'-'*7}")
        for cat in categories:
            cs = model_summary["categories"][cat]
            print(f"    {cat:<30s} {cs['total']:>5d} "
                  f"{cs['accuracy']*100:>6.1f}% {cs['hallucination_rate']*100:>6.1f}%")

    # Save
    summary_path = OUTPUT_DIR / "baseline_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Saved: {summary_path}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run V5 baseline generation and judging"
    )
    parser.add_argument(
        "--phase",
        choices=["generate", "judge", "summary", "all"],
        default="all",
        help="Which phase to run (default: all)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Filter to a single model (e.g. mixtral-8x7b)",
    )
    args = parser.parse_args()

    models = [args.model] if args.model else TARGET_MODELS

    # Validate V5 prompts exist
    if not V5_PROMPTS_PATH.exists():
        print(f"ERROR: V5 prompts not found at {V5_PROMPTS_PATH}")
        print("Run build_v5_benchmark.py first.")
        sys.exit(1)

    print(f"V5 Baseline Experiment")
    print(f"  Prompts: {V5_PROMPTS_PATH}")
    print(f"  Models:  {', '.join(models)}")
    print(f"  Output:  {OUTPUT_DIR}")
    print(f"  Phase:   {args.phase}")

    if args.phase in ("generate", "all"):
        for model_key in models:
            run_generation(model_key)

    if args.phase in ("judge", "all"):
        print("\nInitializing judge panel:")
        for j in JUDGES_CONFIG:
            print(f"  - {j['provider']}/{j['model']}")

        for model_key in models:
            run_judging(model_key)

    if args.phase in ("summary", "all"):
        generate_summary()

    print(f"\n{'=' * 60}")
    print(f"  DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
