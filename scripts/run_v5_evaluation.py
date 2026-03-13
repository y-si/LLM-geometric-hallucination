"""Step 11: Evaluate fine-tuned models on V3 held-out test set.

Runs inference on the 449 V3 prompts using each fine-tuned model (no system
prompt), then judges with the 3-judge consensus panel.

Usage:
    export TOGETHER_API_KEY=...
    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...

    # Run both phases (generate + judge) for all fine-tuned models:
    python3 scripts/run_v5_evaluation.py

    # Run only generation:
    python3 scripts/run_v5_evaluation.py --phase generate

    # Run only judging:
    python3 scripts/run_v5_evaluation.py --phase judge

    # Filter to a single base model:
    python3 scripts/run_v5_evaluation.py --model mixtral-8x7b

    # Filter to a single config:
    python3 scripts/run_v5_evaluation.py --config A

Output:
    results/v5_finetuned/{model}/config{X}/answers.jsonl
    results/v5_finetuned/{model}/config{X}/judged_answers.jsonl
    results/v5_finetuned/evaluation_summary.json
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
FINETUNED_MODELS_PATH = PROJECT_ROOT / "data" / "training" / "v5_finetuned_models.json"
OUTPUT_DIR = PROJECT_ROOT / "results" / "v5_finetuned"

JUDGES_CONFIG = [
    {"provider": "openai", "model": "gpt-5.1"},
    {"provider": "anthropic", "model": "claude-opus-4-5-20251101"},
    {"provider": "together", "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
]

MAX_TOKENS = 4000
TEMPERATURE = 0.7
SAVE_EVERY_GEN = 25
SAVE_EVERY_JUDGE = 10


# ── Load fine-tuned model IDs ─────────────────────────────────────────────

def load_finetuned_models():
    """Load fine-tuned model IDs from Step 10 results."""
    with open(FINETUNED_MODELS_PATH) as f:
        data = json.load(f)

    models = []
    for job in data["jobs"]:
        if job["status"] != "completed":
            continue
        # Use output_name — all models require dedicated endpoints
        model_id = job.get("output_name", "unknown")
        if model_id == "unknown":
            print(f"  WARNING: Job {job['job_id']} has no output_name, skipping")
            continue
        models.append({
            "base_model": job["model"],
            "config": job["config"],
            "together_model_id": model_id,
            "job_id": job["job_id"],
        })
    return models


# ── Generation ─────────────────────────────────────────────────────────────

def run_generation(ft_model: dict, prompts: list):
    """Generate responses for one fine-tuned model on V3 prompts."""
    base_model = ft_model["base_model"]
    config = ft_model["config"]
    model_id = ft_model["together_model_id"]

    print(f"\n{'=' * 60}")
    print(f"  GENERATION — {base_model} config{config}")
    print(f"  Model ID: {model_id}")
    print(f"  Prompts: {len(prompts)}")
    print(f"{'=' * 60}")

    # Use Together API directly with fine-tuned model ID
    client = MultiModelClient(provider="together", model_name=model_id)

    output_path = OUTPUT_DIR / base_model / f"config{config}" / "answers.jsonl"
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

    for prompt_data in tqdm(prompts, desc=f"{base_model}/config{config}"):
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
                result["model"] = base_model
                result["finetuned_model_id"] = model_id
                result["config"] = config
                result["prefix_key"] = "finetuned"
                result["prefix_name"] = f"Fine-tuned config{config}"
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

def run_judging(ft_model: dict):
    """Judge fine-tuned model responses."""
    base_model = ft_model["base_model"]
    config = ft_model["config"]

    answers_path = OUTPUT_DIR / base_model / f"config{config}" / "answers.jsonl"
    output_path = OUTPUT_DIR / base_model / f"config{config}" / "judged_answers.jsonl"

    if not answers_path.exists():
        print(f"  No answers file for {base_model}/config{config}, skipping")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  JUDGING — {base_model} config{config}")
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

    for answer_data in tqdm(answers, desc=f"Judging {base_model}/config{config}"):
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
    """Generate evaluation_summary.json comparing all conditions."""
    print(f"\n{'=' * 60}")
    print(f"  EVALUATION SUMMARY")
    print(f"{'=' * 60}")

    summary = {"finetuned": {}, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    # Find all judged results
    for model_dir in sorted(OUTPUT_DIR.iterdir()):
        if not model_dir.is_dir() or model_dir.name.startswith("."):
            continue
        model_key = model_dir.name

        for config_dir in sorted(model_dir.iterdir()):
            if not config_dir.is_dir():
                continue

            judged_path = config_dir / "judged_answers.jsonl"
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

            key = f"{model_key}/{config_dir.name}"
            model_summary = {
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
                model_summary["categories"][cat] = {
                    "total": cat_total,
                    "correct": cat_labels.count(0),
                    "hallucination": cat_labels.count(2),
                    "accuracy": cat_labels.count(0) / cat_total,
                    "hallucination_rate": cat_labels.count(2) / cat_total,
                }

            summary["finetuned"][key] = model_summary

            # Print
            print(f"\n  {key}:")
            print(f"    Overall: {correct}/{total} correct ({correct/total*100:.1f}%), "
                  f"{hallucination} hallucinations ({hallucination/total*100:.1f}%)")
            print(f"    {'Category':<30s} {'N':>5s} {'Acc':>7s} {'Halluc':>7s}")
            print(f"    {'-'*30} {'-'*5} {'-'*7} {'-'*7}")
            for cat in categories:
                cs = model_summary["categories"][cat]
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
        description="Step 11: Evaluate fine-tuned models on V3 held-out test set"
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
        help="Filter to a single base model (e.g. mixtral-8x7b)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Filter to a single config (e.g. A)",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help="Override model ID with dedicated endpoint string (from Together dashboard)",
    )
    args = parser.parse_args()

    # Load V3 prompts
    if not V3_PROMPTS_PATH.exists():
        print(f"ERROR: V3 prompts not found at {V3_PROMPTS_PATH}")
        sys.exit(1)
    prompts = read_jsonl(V3_PROMPTS_PATH)
    print(f"Loaded {len(prompts)} V3 held-out prompts")

    # Load fine-tuned model IDs
    if not FINETUNED_MODELS_PATH.exists():
        print(f"ERROR: Fine-tuned models file not found at {FINETUNED_MODELS_PATH}")
        print("Run run_v5_finetuning.py first.")
        sys.exit(1)
    ft_models = load_finetuned_models()
    print(f"Found {len(ft_models)} fine-tuned models")

    # Apply filters
    if args.model:
        ft_models = [m for m in ft_models if m["base_model"] == args.model]
    if args.config:
        ft_models = [m for m in ft_models if m["config"] == args.config]

    if not ft_models:
        print("No fine-tuned models match the specified filters.")
        sys.exit(1)

    # Override model ID with dedicated endpoint if provided
    if args.endpoint:
        if len(ft_models) != 1:
            print("ERROR: --endpoint requires exactly one model (use --model and --config to filter)")
            sys.exit(1)
        ft_models[0]["together_model_id"] = args.endpoint
        print(f"\nUsing dedicated endpoint: {args.endpoint}")

    print(f"\nEvaluating {len(ft_models)} models on {len(prompts)} V3 prompts:")
    for m in ft_models:
        print(f"  - {m['base_model']} config{m['config']}: {m['together_model_id']}")

    if args.phase in ("generate", "all"):
        for ft_model in ft_models:
            run_generation(ft_model, prompts)

    if args.phase in ("judge", "all"):
        print("\nInitializing judge panel:")
        for j in JUDGES_CONFIG:
            print(f"  - {j['provider']}/{j['model']}")

        for ft_model in ft_models:
            run_judging(ft_model)

    if args.phase in ("summary", "all"):
        generate_summary()

    print(f"\n{'=' * 60}")
    print(f"  DONE")
    print(f"{'=' * 60}")
    print(f"\nRun analysis: python3 scripts/analyze_v5_finetuned.py")


if __name__ == "__main__":
    main()
