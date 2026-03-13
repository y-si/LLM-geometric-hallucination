"""Step 13B-D: Run TruthfulQA generalization testing.

Runs baseline and fine-tuned models on TruthfulQA (817 questions),
then judges with the 3-judge consensus panel.

Usage:
    export TOGETHER_API_KEY=...
    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...

    # Run baseline generation for both models:
    python3 scripts/run_truthfulqa.py --phase generate --condition baseline

    # Run fine-tuned generation (Mixtral needs dedicated endpoint):
    python3 scripts/run_truthfulqa.py --phase generate --condition finetuned \
        --endpoint <mixtral-endpoint-from-dashboard>

    # Run judging for all completed generations:
    python3 scripts/run_truthfulqa.py --phase judge

    # Run only one model:
    python3 scripts/run_truthfulqa.py --phase generate --condition baseline \
        --model mixtral-8x7b

    # Run everything (baseline gen → finetuned gen → judge):
    python3 scripts/run_truthfulqa.py --phase all \
        --endpoint <mixtral-endpoint-from-dashboard>

Output:
    results/truthfulqa/{model}/baseline_answers.jsonl
    results/truthfulqa/{model}/baseline_judged.jsonl
    results/truthfulqa/{model}/finetuned_answers.jsonl
    results/truthfulqa/{model}/finetuned_judged.jsonl
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

TRUTHFULQA_PATH = PROJECT_ROOT / "data" / "prompts" / "truthfulqa.jsonl"
FINETUNED_MODELS_PATH = PROJECT_ROOT / "data" / "training" / "v5_finetuned_models.json"
OUTPUT_DIR = PROJECT_ROOT / "results" / "truthfulqa"

# Base models on Together AI (serverless)
BASE_MODELS = {
    "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "llama-4-maverick-17b": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
}

# Best fine-tuned configs (from Step 11)
BEST_CONFIGS = {
    "mixtral-8x7b": "C",
    "llama-4-maverick-17b": "A",
}

JUDGES_CONFIG = [
    {"provider": "openai", "model": "gpt-5.1"},
    {"provider": "anthropic", "model": "claude-opus-4-5-20251101"},
    {"provider": "together", "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
]

MAX_TOKENS = 4000
TEMPERATURE = 0.7
SAVE_EVERY_GEN = 25
SAVE_EVERY_JUDGE = 10


# ── Generation ─────────────────────────────────────────────────────────────

def run_generation(model_name, condition, prompts, model_id):
    """Generate responses for one model/condition on TruthfulQA."""
    print(f"\n{'=' * 60}")
    print(f"  GENERATION — {model_name} ({condition})")
    print(f"  Model ID: {model_id}")
    print(f"  Prompts: {len(prompts)}")
    print(f"{'=' * 60}")

    client = MultiModelClient(provider="together", model_name=model_id)

    output_path = OUTPUT_DIR / model_name / f"{condition}_answers.jsonl"
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

    for prompt_data in tqdm(prompts, desc=f"{model_name}/{condition}"):
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
                result["condition"] = condition
                result["model_id"] = model_id
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

def run_judging(model_name, condition):
    """Judge TruthfulQA responses."""
    answers_path = OUTPUT_DIR / model_name / f"{condition}_answers.jsonl"
    output_path = OUTPUT_DIR / model_name / f"{condition}_judged.jsonl"

    if not answers_path.exists():
        print(f"  No answers for {model_name}/{condition}, skipping")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  JUDGING — {model_name} ({condition})")
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

    for answer_data in tqdm(answers, desc=f"Judging {model_name}/{condition}"):
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


# ── Fine-tuned model ID resolution ────────────────────────────────────────

def get_finetuned_model_id(model_name, endpoints=None):
    """Get the fine-tuned model ID for a given base model.

    Both Mixtral and Llama require dedicated endpoints.
    Pass endpoints as a dict: {"mixtral-8x7b": "...", "llama-4-maverick-17b": "..."}.
    """
    endpoints = endpoints or {}

    if model_name in endpoints:
        return endpoints[model_name]

    with open(FINETUNED_MODELS_PATH) as f:
        data = json.load(f)

    config = BEST_CONFIGS[model_name]
    key = f"{model_name}_config{config}"
    model_id = data["completed_models"].get(key, "unknown")

    print(f"ERROR: Fine-tuned model requires --endpoint for {model_name}")
    print(f"  Deploy from Together dashboard using model:")
    print(f"  {model_id}")
    sys.exit(1)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Step 13B-D: TruthfulQA generalization testing"
    )
    parser.add_argument(
        "--phase",
        choices=["generate", "judge", "all"],
        default="all",
        help="Which phase to run (default: all)",
    )
    parser.add_argument(
        "--condition",
        choices=["baseline", "finetuned", "both"],
        default="both",
        help="Which condition to generate (default: both)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Filter to one model (e.g. mixtral-8x7b)",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help="Dedicated endpoint for fine-tuned model (when running a single --model)",
    )
    parser.add_argument(
        "--mixtral-endpoint",
        type=str,
        default=None,
        help="Dedicated endpoint for Mixtral fine-tuned (when running both models)",
    )
    parser.add_argument(
        "--llama-endpoint",
        type=str,
        default=None,
        help="Dedicated endpoint for Llama fine-tuned (when running both models)",
    )
    args = parser.parse_args()

    # Load prompts
    if not TRUTHFULQA_PATH.exists():
        print(f"ERROR: TruthfulQA prompts not found at {TRUTHFULQA_PATH}")
        print(f"  Run: python3 scripts/prepare_truthfulqa.py")
        sys.exit(1)

    prompts = read_jsonl(TRUTHFULQA_PATH)
    print(f"Loaded {len(prompts)} TruthfulQA prompts")

    models = list(BASE_MODELS.keys())
    if args.model:
        if args.model not in BASE_MODELS:
            print(f"ERROR: Unknown model {args.model}. Options: {list(BASE_MODELS.keys())}")
            sys.exit(1)
        models = [args.model]

    conditions = []
    if args.condition in ("baseline", "both"):
        conditions.append("baseline")
    if args.condition in ("finetuned", "both"):
        conditions.append("finetuned")

    # Build per-model endpoint mapping
    endpoints = {}
    if args.mixtral_endpoint:
        endpoints["mixtral-8x7b"] = args.mixtral_endpoint
    if args.llama_endpoint:
        endpoints["llama-4-maverick-17b"] = args.llama_endpoint
    # --endpoint applies to the single model specified by --model
    if args.endpoint and args.model:
        endpoints[args.model] = args.endpoint

    # ── Generation ──
    if args.phase in ("generate", "all"):
        for model_name in models:
            for condition in conditions:
                if condition == "baseline":
                    model_id = BASE_MODELS[model_name]
                else:
                    model_id = get_finetuned_model_id(model_name, endpoints)

                run_generation(model_name, condition, prompts, model_id)

    # ── Judging ──
    if args.phase in ("judge", "all"):
        for model_name in models:
            for condition in ["baseline", "finetuned"]:
                answers_path = OUTPUT_DIR / model_name / f"{condition}_answers.jsonl"
                if answers_path.exists():
                    run_judging(model_name, condition)

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print(f"  TRUTHFULQA SUMMARY")
    print(f"{'=' * 60}")

    for model_name in BASE_MODELS:
        for condition in ["baseline", "finetuned"]:
            judged_path = OUTPUT_DIR / model_name / f"{condition}_judged.jsonl"
            if not judged_path.exists():
                print(f"\n  {model_name}/{condition}: not yet judged")
                continue

            results = read_jsonl(judged_path)
            labels = [r["judge_label"] for r in results]
            total = len(results)
            correct = labels.count(0)
            halluc = labels.count(2)
            refused = labels.count(3)

            print(f"\n  {model_name}/{condition} (n={total}):")
            print(f"    Accuracy:          {correct / total * 100:.1f}%")
            print(f"    Hallucination:     {halluc / total * 100:.1f}%")
            print(f"    Refusal:           {refused / total * 100:.1f}%")

    print(f"\n{'=' * 60}")
    print(f"  DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
