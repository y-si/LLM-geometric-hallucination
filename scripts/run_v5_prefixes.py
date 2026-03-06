"""Run V5 prefix generation and judging.

Generates responses from Mixtral-8x7B and Llama-4-Maverick-17B on all 2,430
V5 prompts with each of the 5 system prefixes, then judges each response
with the 3-judge consensus panel.

Reuses the same model clients, judging infrastructure, and prefix configs as V4.
Loads only V5 prompts (not V3) to maintain train/test separation.

Usage:
    export TOGETHER_API_KEY=...
    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...

    # Generate all prefixes for one model:
    python3 scripts/run_v5_prefixes.py --phase generate --model mixtral-8x7b

    # Generate one specific prefix:
    python3 scripts/run_v5_prefixes.py --phase generate --model mixtral-8x7b --prefix entity_aware

    # Judge all completed results:
    python3 scripts/run_v5_prefixes.py --phase judge

    # Full pipeline:
    python3 scripts/run_v5_prefixes.py

Output:
    results/v5_prefixes/{model}/{prefix}/answers.jsonl
    results/v5_prefixes/{model}/{prefix}/judged_answers.jsonl
"""

import sys
import json
import time
import argparse
from pathlib import Path

import yaml
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
PREFIX_CONFIG_PATH = PROJECT_ROOT / "experiments" / "prefix_configs.yaml"
OUTPUT_DIR = PROJECT_ROOT / "results" / "v5_prefixes"

# Generation parameters (matching V4 for comparability)
MAX_TOKENS = 4000
TEMPERATURE = 0.7
SAVE_EVERY_GEN = 25
SAVE_EVERY_JUDGE = 10


# ── Prefix loading ─────────────────────────────────────────────────────────

def load_prefixes():
    """Load prefix configurations from YAML."""
    with open(PREFIX_CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return {p["key"]: p for p in config["prefixes"]}


# ── Generation ─────────────────────────────────────────────────────────────

def run_generation(model_key: str, prefix_key: str, prefix_config: dict):
    """Generate responses for one model + prefix combination."""
    system_prompt = prefix_config.get("system_prompt")
    prefix_name = prefix_config["name"]

    print(f"\n{'=' * 60}")
    print(f"  GENERATION — {model_key} / {prefix_name} ({prefix_key})")
    print(f"{'=' * 60}")

    prompts = read_jsonl(V5_PROMPTS_PATH)
    print(f"  Loaded {len(prompts)} V5 prompts")

    client = get_model_client(model_key)

    output_path = OUTPUT_DIR / model_key / prefix_key / "answers.jsonl"
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

    for prompt_data in tqdm(prompts, desc=f"{model_key}/{prefix_key}"):
        if prompt_data["id"] in existing_ids:
            continue

        retry_delay = 2
        for attempt in range(3):
            try:
                response = client.generate(
                    prompt=prompt_data["question"],
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    system_prompt=system_prompt,
                )

                result = prompt_data.copy()
                result["model"] = model_key
                result["prefix_key"] = prefix_key
                result["prefix_name"] = prefix_name
                result["system_prompt_used"] = system_prompt or ""
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

def run_judging(model_key: str, prefix_key: str):
    """Judge responses for one model + prefix combination."""
    answers_path = OUTPUT_DIR / model_key / prefix_key / "answers.jsonl"
    output_path = OUTPUT_DIR / model_key / prefix_key / "judged_answers.jsonl"

    if not answers_path.exists():
        print(f"  No answers for {model_key}/{prefix_key}, skipping")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  JUDGING — {model_key} / {prefix_key}")
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

    for answer_data in tqdm(answers, desc=f"Judging {model_key}/{prefix_key}"):
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


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run V5 prefix generation and judging"
    )
    parser.add_argument(
        "--phase",
        choices=["generate", "judge", "all"],
        default="all",
        help="Which phase to run (default: all)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Filter to a single model (e.g. mixtral-8x7b)",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Filter to a single prefix (e.g. entity_aware)",
    )
    args = parser.parse_args()

    models = [args.model] if args.model else TARGET_MODELS
    prefixes = load_prefixes()

    if args.prefix:
        if args.prefix not in prefixes:
            print(f"Unknown prefix: {args.prefix}. Available: {list(prefixes.keys())}")
            sys.exit(1)
        prefix_keys = [args.prefix]
    else:
        prefix_keys = list(prefixes.keys())

    # Validate V5 prompts exist
    if not V5_PROMPTS_PATH.exists():
        print(f"ERROR: V5 prompts not found at {V5_PROMPTS_PATH}")
        sys.exit(1)

    print(f"V5 Prefix Experiment")
    print(f"  Prompts:  {V5_PROMPTS_PATH}")
    print(f"  Models:   {', '.join(models)}")
    print(f"  Prefixes: {', '.join(prefix_keys)}")
    print(f"  Output:   {OUTPUT_DIR}")
    print(f"  Phase:    {args.phase}")

    if args.phase in ("generate", "all"):
        for model_key in models:
            for prefix_key in prefix_keys:
                run_generation(model_key, prefix_key, prefixes[prefix_key])

    if args.phase in ("judge", "all"):
        print("\nInitializing judge panel:")
        for j in JUDGES_CONFIG:
            print(f"  - {j['provider']}/{j['model']}")

        for model_key in models:
            for prefix_key in prefix_keys:
                run_judging(model_key, prefix_key)

    print(f"\n{'=' * 60}")
    print(f"  DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
