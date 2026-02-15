#!/usr/bin/env python3
"""Orchestration script for the prompt prefix experiment.

Runs individual phases or the full pipeline end-to-end.

Usage:
    # Full pipeline
    python scripts/run_prefix_experiment.py --phase all

    # Individual phases
    python scripts/run_prefix_experiment.py --phase baselines
    python scripts/run_prefix_experiment.py --phase generate
    python scripts/run_prefix_experiment.py --phase generate --model mixtral-8x7b
    python scripts/run_prefix_experiment.py --phase generate --model mixtral-8x7b --prefix epistemic_humility
    python scripts/run_prefix_experiment.py --phase judge
    python scripts/run_prefix_experiment.py --phase aggregate
    python scripts/run_prefix_experiment.py --phase analyze
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_DIR = "results/v4_prefix_experiment"
V3_RESULTS = "results/v3/multi_model/all_models_results.csv"
PREFIX_CONFIG = "experiments/prefix_configs.yaml"
TARGET_MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]


def phase_baselines():
    """Phase 1: Extract baseline metrics from V3 data."""
    print("\n" + "=" * 60)
    print("PHASE 1: Extract Baselines")
    print("=" * 60)
    from src.evaluation.extract_baselines import extract_baselines
    extract_baselines(V3_RESULTS, OUTPUT_DIR)


def phase_generate(model_filter=None, prefix_filter=None):
    """Phase 2-3: Generate responses with prompt prefixes."""
    print("\n" + "=" * 60)
    print("PHASE 2-3: Generate Responses with Prefixes")
    print("=" * 60)
    from src.pipeline.run_prefix_generation import load_prefixes, run_prefix_generation

    prefixes = load_prefixes(PREFIX_CONFIG)
    models = [model_filter] if model_filter else TARGET_MODELS

    for model_key in models:
        prefix_keys = [prefix_filter] if prefix_filter else list(prefixes.keys())
        for prefix_key in prefix_keys:
            if prefix_key not in prefixes:
                print(f"Unknown prefix: {prefix_key}, skipping")
                continue
            run_prefix_generation(model_key, prefix_key, prefixes[prefix_key], OUTPUT_DIR)


def phase_judge(model_filter=None, prefix_filter=None):
    """Phase 3: Judge all generated responses."""
    print("\n" + "=" * 60)
    print("PHASE 3: Judge Responses")
    print("=" * 60)
    from src.pipeline.run_prefix_judging import run_prefix_judging
    run_prefix_judging(OUTPUT_DIR, model_filter, prefix_filter)


def phase_aggregate():
    """Phase 3: Aggregate results into master CSV."""
    print("\n" + "=" * 60)
    print("PHASE 3: Aggregate Results")
    print("=" * 60)
    from src.pipeline.aggregate_prefix_results import aggregate_prefix_results
    aggregate_prefix_results(OUTPUT_DIR, f"{OUTPUT_DIR}/all_prefix_results.csv")


def phase_analyze():
    """Phase 3: Run analysis and produce visualizations."""
    print("\n" + "=" * 60)
    print("PHASE 3: Analysis & Visualization")
    print("=" * 60)
    from src.evaluation.prefix_analysis import run_analysis
    run_analysis(
        f"{OUTPUT_DIR}/all_prefix_results.csv",
        V3_RESULTS,
        f"{OUTPUT_DIR}/analysis",
    )


def main():
    parser = argparse.ArgumentParser(description="Run prompt prefix experiment")
    parser.add_argument("--phase", type=str, required=True,
                        choices=["baselines", "generate", "judge",
                                 "aggregate", "analyze", "all"],
                        help="Which phase to run")
    parser.add_argument("--model", type=str, default=None,
                        help="Filter to specific model (for generate/judge)")
    parser.add_argument("--prefix", type=str, default=None,
                        help="Filter to specific prefix (for generate/judge)")
    args = parser.parse_args()

    if args.phase == "all":
        phase_baselines()
        phase_generate()
        phase_judge()
        phase_aggregate()
        phase_analyze()
    elif args.phase == "baselines":
        phase_baselines()
    elif args.phase == "generate":
        phase_generate(args.model, args.prefix)
    elif args.phase == "judge":
        phase_judge(args.model, args.prefix)
    elif args.phase == "aggregate":
        phase_aggregate()
    elif args.phase == "analyze":
        phase_analyze()


if __name__ == "__main__":
    main()
