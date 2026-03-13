"""Step 9D/E: Evaluate ablation fine-tuned models on V3 held-out test set.

Runs inference on the 449 V3 prompts using each ablation fine-tuned model,
then judges with the 3-judge consensus panel.

Deployment notes:
  - Llama models: serverless LoRA via "-adapter" suffix (no endpoint needed)
  - Mixtral models: requires dedicated endpoint deployed from Together dashboard
    ($0.13/min). Deploy one at a time, run, stop to minimize cost.

Usage:
    export TOGETHER_API_KEY=...
    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...

    # Run all phases for all models:
    python3 scripts/run_ablation_evaluation.py

    # Generation only (no judging):
    python3 scripts/run_ablation_evaluation.py --phase generate

    # Judging only:
    python3 scripts/run_ablation_evaluation.py --phase judge

    # Single condition:
    python3 scripts/run_ablation_evaluation.py --condition T5_mixtral

    # Override endpoint (for Mixtral dedicated endpoints):
    python3 scripts/run_ablation_evaluation.py --condition T5_mixtral --endpoint "your-endpoint-id"

    # Summary only:
    python3 scripts/run_ablation_evaluation.py --phase summary

Output:
    results/v5_finetuned/ablation/{condition}/answers.jsonl
    results/v5_finetuned/ablation/{condition}/judged_answers.jsonl
    results/v5_finetuned/ablation/evaluation_summary.json
"""

import sys
import json
import time
import argparse
from pathlib import Path

from tqdm import tqdm

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.multi_model_client import MultiModelClient
from src.models.consensus_judge import ConsensusJudge
from src.utils.io import read_jsonl, write_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

V3_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "prompts.jsonl"
ABLATION_JOBS_PATH = PROJECT_ROOT / "data" / "training" / "ablation" / "ablation_ft_jobs.json"
OUTPUT_DIR = PROJECT_ROOT / "results" / "v5_finetuned" / "ablation"

JUDGES_CONFIG = [
    {"provider": "openai", "model": "gpt-5.1"},
    {"provider": "anthropic", "model": "claude-opus-4-5-20251101"},
    {"provider": "together", "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
]

MAX_TOKENS = 4000
TEMPERATURE = 0.7
SAVE_EVERY_GEN = 25
SAVE_EVERY_JUDGE = 10


# ── Load ablation models ─────────────────────────────────────────────────

def load_ablation_models():
    """Load ablation fine-tuned model info."""
    with open(ABLATION_JOBS_PATH) as f:
        jobs = json.load(f)

    models = []
    for job in jobs:
        if job["status"] != "completed":
            print(f"  Skipping {job['label']}: status={job['status']}")
            continue

        output_name = job.get("output_name", "")
        if not output_name:
            print(f"  Skipping {job['label']}: no output_name")
            continue

        # Determine base model short name
        if "mixtral" in job["label"].lower():
            base_model = "mixtral-8x7b"
            # Mixtral needs dedicated endpoint — use output_name directly
            # User can override with --endpoint
            endpoint = output_name
        else:
            base_model = "llama-4-maverick-17b"
            # Llama uses serverless with -adapter suffix
            endpoint = output_name + "-adapter"

        models.append({
            "label": job["label"],
            "base_model": base_model,
            "output_name": output_name,
            "endpoint": endpoint,
            "job_id": job["job_id"],
        })

    return models


# ── Generation ─────────────────────────────────────────────────────────────

def run_generation(model_info: dict, prompts: list):
    """Generate responses for one ablation model on V3 prompts."""
    label = model_info["label"]
    endpoint = model_info["endpoint"]

    print(f"\n{'=' * 60}")
    print(f"  GENERATION — {label}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Prompts: {len(prompts)}")
    print(f"{'=' * 60}")

    client = MultiModelClient(provider="together", model_name=endpoint)

    output_path = OUTPUT_DIR / label / "answers.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resume
    existing_ids = set()
    existing_results = []
    if output_path.exists():
        existing_results = read_jsonl(output_path)
        existing_ids = {r["id"] for r in existing_results}
        remaining = len(prompts) - len(existing_ids)
        print(f"  Resuming: {len(existing_ids)} done, {remaining} remaining")

    results = []
    failed = 0

    for prompt_data in tqdm(prompts, desc=label):
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
                result["model"] = model_info["base_model"]
                result["finetuned_model_id"] = model_info["output_name"]
                result["ablation_condition"] = label
                result["prefix_key"] = "finetuned"
                result["prefix_name"] = f"Ablation {label}"
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

def run_judging(model_info: dict):
    """Judge ablation model responses."""
    label = model_info["label"]

    answers_path = OUTPUT_DIR / label / "answers.jsonl"
    output_path = OUTPUT_DIR / label / "judged_answers.jsonl"

    if not answers_path.exists():
        print(f"  No answers file for {label}, skipping")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  JUDGING — {label}")
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

    for answer_data in tqdm(answers, desc=f"Judging {label}"):
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

        # Periodic save
        if len(results) > 0 and len(results) % SAVE_EVERY_JUDGE == 0:
            write_jsonl(output_path, results)

    write_jsonl(output_path, results)
    print(f"  Saved {len(results)} judgments")
    return len(results)


# ── Summary ────────────────────────────────────────────────────────────────

def generate_summary():
    """Generate evaluation_summary.json for ablation conditions."""
    print(f"\n{'=' * 60}")
    print(f"  ABLATION EVALUATION SUMMARY")
    print(f"{'=' * 60}")

    summary = {"ablation": {}, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    for condition_dir in sorted(OUTPUT_DIR.iterdir()):
        if not condition_dir.is_dir() or condition_dir.name.startswith("."):
            continue

        judged_path = condition_dir / "judged_answers.jsonl"
        if not judged_path.exists():
            continue

        results = read_jsonl(judged_path)
        total = len(results)
        if total == 0:
            continue

        labels = [r["judge_label"] for r in results]
        correct = labels.count(0)
        partial = labels.count(1)
        hallucination = labels.count(2)
        refusal = labels.count(3)

        condition_summary = {
            "total": total,
            "correct": correct,
            "partial": partial,
            "hallucination": hallucination,
            "refusal": refusal,
            "accuracy": correct / total,
            "hallucination_rate": hallucination / total,
            "categories": {},
        }

        # Per-category
        categories = sorted(set(r["category"] for r in results))
        for cat in categories:
            cat_results = [r for r in results if r["category"] == cat]
            cat_total = len(cat_results)
            cat_labels = [r["judge_label"] for r in cat_results]
            condition_summary["categories"][cat] = {
                "total": cat_total,
                "correct": cat_labels.count(0),
                "hallucination": cat_labels.count(2),
                "accuracy": cat_labels.count(0) / cat_total,
                "hallucination_rate": cat_labels.count(2) / cat_total,
            }

        summary["ablation"][condition_dir.name] = condition_summary

        # Print
        print(f"\n  {condition_dir.name}:")
        print(f"    Overall: {correct}/{total} correct ({correct/total*100:.1f}%), "
              f"{hallucination} hallucinations ({hallucination/total*100:.1f}%)")
        print(f"    {'Category':<30s} {'N':>5s} {'Acc':>7s} {'Halluc':>7s}")
        print(f"    {'-'*30} {'-'*5} {'-'*7} {'-'*7}")
        for cat in categories:
            cs = condition_summary["categories"][cat]
            print(f"    {cat:<30s} {cs['total']:>5d} "
                  f"{cs['accuracy']*100:>6.1f}% {cs['hallucination_rate']*100:>6.1f}%")

    # Save
    summary_path = OUTPUT_DIR / "evaluation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Saved: {summary_path}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Step 9D/E: Evaluate ablation fine-tuned models on V3 held-out test set"
    )
    parser.add_argument(
        "--phase",
        choices=["generate", "judge", "summary", "all"],
        default="all",
        help="Which phase to run (default: all)",
    )
    parser.add_argument(
        "--condition",
        type=str,
        default=None,
        help="Filter to a single condition label (e.g. T5_mixtral)",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help="Override endpoint for generation (e.g. dedicated Mixtral endpoint)",
    )
    args = parser.parse_args()

    # Load V3 prompts
    if not V3_PROMPTS_PATH.exists():
        print(f"ERROR: V3 prompts not found at {V3_PROMPTS_PATH}")
        sys.exit(1)
    prompts = read_jsonl(V3_PROMPTS_PATH)
    print(f"Loaded {len(prompts)} V3 held-out prompts")

    # Load ablation models
    if not ABLATION_JOBS_PATH.exists():
        print(f"ERROR: Ablation jobs file not found at {ABLATION_JOBS_PATH}")
        sys.exit(1)
    abl_models = load_ablation_models()
    print(f"Found {len(abl_models)} completed ablation models")

    # Apply filters
    if args.condition:
        abl_models = [m for m in abl_models if m["label"] == args.condition]

    if not abl_models:
        print("No ablation models match the specified filters.")
        sys.exit(1)

    # Override endpoint if provided
    if args.endpoint:
        if len(abl_models) != 1:
            print("ERROR: --endpoint requires exactly one model (use --condition to filter)")
            sys.exit(1)
        abl_models[0]["endpoint"] = args.endpoint
        print(f"\nUsing override endpoint: {args.endpoint}")

    print(f"\nEvaluating {len(abl_models)} models on {len(prompts)} V3 prompts:")
    for m in abl_models:
        print(f"  - {m['label']}: {m['endpoint']}")

    if args.phase in ("generate", "all"):
        for model_info in abl_models:
            run_generation(model_info, prompts)

    if args.phase in ("judge", "all"):
        print("\nInitializing judge panel:")
        for j in JUDGES_CONFIG:
            print(f"  - {j['provider']}/{j['model']}")

        for model_info in abl_models:
            run_judging(model_info)

    if args.phase in ("summary", "all"):
        generate_summary()

    print(f"\n{'=' * 60}")
    print(f"  DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
