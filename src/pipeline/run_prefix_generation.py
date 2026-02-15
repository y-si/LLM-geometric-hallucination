"""Run generation pipeline with prompt prefixes.

For each (model, prefix) combination, generates responses for all benchmark
prompts using the specified system prompt prefix. Supports resume capability.
"""

import sys
import argparse
import json
import time
from pathlib import Path

import yaml
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.multi_model_client import get_model_client
from src.utils.io import read_jsonl, write_jsonl


def load_prefixes(config_path="experiments/prefix_configs.yaml"):
    """Load prompt prefix configurations from YAML."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return {p['key']: p for p in config['prefixes']}


def load_prompts(data_dir="data/prompts"):
    """Load all prompts from the benchmark dataset."""
    prompts = []
    for file in sorted(Path(data_dir).glob("*.jsonl")):
        prompts.extend(read_jsonl(file))
    return prompts


def run_prefix_generation(model_key, prefix_key, prefix_config, output_dir):
    """Run generation for a specific model + prefix with resume capability."""

    system_prompt = prefix_config.get('system_prompt')
    prefix_name = prefix_config['name']

    print(f"\n{'='*60}")
    print(f"Model: {model_key}")
    print(f"Prefix: {prefix_name} ({prefix_key})")
    if system_prompt:
        print(f"System prompt: {system_prompt[:80]}...")
    else:
        print("System prompt: (none)")
    print(f"{'='*60}\n")

    client = get_model_client(model_key)
    prompts = load_prompts()
    print(f"Loaded {len(prompts)} prompts")

    # Output path: results/v4_prefix_experiment/{model}/{prefix}/answers.jsonl
    output_path = Path(output_dir) / model_key / prefix_key / "answers.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resume capability
    existing_ids = set()
    if output_path.exists():
        existing_results = read_jsonl(output_path)
        existing_ids = {r['id'] for r in existing_results}
        print(f"Resuming: {len(existing_ids)} already completed, "
              f"{len(prompts) - len(existing_ids)} remaining")

    results = []
    failed = 0

    for prompt_data in tqdm(prompts, desc=f"{model_key}/{prefix_key}"):
        if prompt_data['id'] in existing_ids:
            continue

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = client.generate(
                    prompt=prompt_data['question'],
                    max_tokens=4000,
                    temperature=0.7,
                    system_prompt=system_prompt,
                )

                result = prompt_data.copy()
                result['model'] = model_key
                result['prefix_key'] = prefix_key
                result['prefix_name'] = prefix_name
                result['system_prompt_used'] = system_prompt or ""
                result['model_answer'] = response
                results.append(result)
                break

            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    print(f"\n  Timeout on {prompt_data['id']}, attempt {attempt+1}/{max_retries}")
                elif "rate_limit" in error_msg.lower() or "429" in error_msg:
                    print(f"\n  Rate limit hit, waiting {retry_delay}s...")
                else:
                    print(f"\n  Error on {prompt_data['id']}: {error_msg}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"\n  Failed after {max_retries} attempts: {prompt_data['id']}")
                    failed += 1

        # Periodic save every 25 results
        if len(results) > 0 and len(results) % 25 == 0:
            _append_results(output_path, results, existing_ids)
            existing_ids.update(r['id'] for r in results)
            results = []

    # Final save
    if results:
        _append_results(output_path, results, existing_ids)

    total_completed = len(existing_ids) + len(results)
    print(f"\nSummary: {model_key} + {prefix_key}")
    print(f"  Completed: {total_completed}/{len(prompts)}")
    print(f"  Failed: {failed}")


def _append_results(output_path, results, existing_ids):
    """Append new results to file."""
    if existing_ids:
        with open(output_path, 'a', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
    else:
        write_jsonl(output_path, results)


def main():
    parser = argparse.ArgumentParser(description="Run prefix generation experiment")
    parser.add_argument("--model-key", type=str, required=True,
                        help="Model key from multi_model_config.yaml")
    parser.add_argument("--prefix-key", type=str, default=None,
                        help="Specific prefix key to run (from prefix_configs.yaml)")
    parser.add_argument("--all-prefixes", action="store_true",
                        help="Run all prefixes for the given model")
    parser.add_argument("--output-dir", type=str,
                        default="results/v4_prefix_experiment")
    parser.add_argument("--prefix-config", type=str,
                        default="experiments/prefix_configs.yaml")

    args = parser.parse_args()

    prefixes = load_prefixes(args.prefix_config)

    if args.all_prefixes:
        for key, config in prefixes.items():
            run_prefix_generation(args.model_key, key, config, args.output_dir)
    elif args.prefix_key:
        if args.prefix_key not in prefixes:
            print(f"Unknown prefix: {args.prefix_key}. Available: {list(prefixes.keys())}")
            sys.exit(1)
        run_prefix_generation(args.model_key, args.prefix_key,
                              prefixes[args.prefix_key], args.output_dir)
    else:
        print("Specify --prefix-key or --all-prefixes")
        sys.exit(1)


if __name__ == "__main__":
    main()
