"""Extract baseline metrics from V3 results for the prefix experiment.

Computes correctness, hallucination, and refusal rates per model and category
for the two target models (Mixtral 8x7B and Llama 4 Maverick).
"""

import sys
import argparse
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

TARGET_MODELS = ['mixtral-8x7b', 'llama-4-maverick-17b']


def extract_baselines(results_file, output_dir):
    """Extract baseline metrics from V3 master results."""
    df = pd.read_csv(results_file)
    df = df[df['model_name'].isin(TARGET_MODELS)]

    print(f"Loaded {len(df)} rows for {df['model_name'].nunique()} models")

    def _compute_rates(g):
        return pd.Series({
            'n_prompts': len(g),
            'correct_rate': (g['judge_label'] == 0).mean(),
            'partial_rate': (g['judge_label'] == 1).mean(),
            'hallucination_rate': (g['judge_label'] == 2).mean(),
            'refusal_rate': (g['judge_label'] == 3).mean(),
        })

    # Overall metrics per model
    overall = df.groupby('model_name').apply(
        _compute_rates, include_groups=False
    ).reset_index()
    overall['category'] = 'ALL'

    # Per-category metrics
    per_category = df.groupby(['model_name', 'category']).apply(
        _compute_rates, include_groups=False
    ).reset_index()

    baselines = pd.concat([overall, per_category], ignore_index=True)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    out_file = output_path / 'baselines.csv'
    baselines.to_csv(out_file, index=False)

    # Print summary
    print(f"\nBaseline metrics saved to {out_file}")
    print("\n=== Overall Rates ===")
    for _, row in overall.iterrows():
        print(f"\n{row['model_name']}:")
        print(f"  Correct:       {row['correct_rate']:.1%}")
        print(f"  Partial:       {row['partial_rate']:.1%}")
        print(f"  Hallucinated:  {row['hallucination_rate']:.1%}")
        print(f"  Refused:       {row['refusal_rate']:.1%}")

    return baselines


def main():
    parser = argparse.ArgumentParser(description="Extract baseline metrics from V3 results")
    parser.add_argument(
        "--results-file", type=str,
        default="results/v3/multi_model/all_models_results.csv",
    )
    parser.add_argument(
        "--output-dir", type=str,
        default="results/v4_prefix_experiment",
    )
    args = parser.parse_args()

    extract_baselines(args.results_file, args.output_dir)


if __name__ == "__main__":
    main()
