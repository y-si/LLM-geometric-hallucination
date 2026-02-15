"""Aggregate prefix experiment results with geometric features.

Merges judged answers from all (model, prefix) combinations with pre-computed
geometric features into a single master CSV for analysis.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.io import read_jsonl


def load_geometry_features():
    """Load pre-computed geometric features from V2 archive."""
    v2_results = pd.read_csv("archive/v2_production_run/results/all_results.csv")

    geometry_cols = ['id', 'local_id', 'curvature_score', 'oppositeness_score',
                     'density', 'centrality']
    available_cols = [c for c in geometry_cols if c in v2_results.columns]

    return v2_results[available_cols].drop_duplicates(subset='id')


def aggregate_prefix_results(base_dir, output_file):
    """Aggregate all prefix experiment results into a master CSV."""

    base_path = Path(base_dir)
    judged_files = sorted(base_path.glob("*/*/judged_answers.jsonl"))

    if not judged_files:
        print(f"No judged files found in {base_dir}")
        return

    print(f"Found {len(judged_files)} judged files")

    geometry_df = load_geometry_features()
    print(f"Loaded geometry features for {len(geometry_df)} prompts")

    all_data = []

    for file in judged_files:
        model_key = file.parent.parent.name
        prefix_key = file.parent.name

        print(f"Processing {model_key}/{prefix_key}...")

        data = read_jsonl(file)
        df = pd.DataFrame(data)

        if 'id' not in df.columns:
            print(f"  Warning: no 'id' column, skipping")
            continue

        # Ensure model/prefix columns exist
        df['model_name'] = model_key
        df['prefix_key'] = prefix_key

        # Derive binary classification columns
        df['is_hallucinated'] = (df['judge_label'] == 2).astype(int)
        df['is_correct'] = (df['judge_label'] == 0).astype(int)
        df['is_refused'] = (df['judge_label'] == 3).astype(int)

        # Merge with geometry
        merged = df.merge(geometry_df, on='id', how='left')
        all_data.append(merged)

    final_df = pd.concat(all_data, ignore_index=True)

    # Drop heavy text columns to keep CSV manageable
    drop_cols = ['individual_judgments', 'judge_justification',
                 'system_prompt_used', 'metadata']
    final_df = final_df.drop(columns=[c for c in drop_cols if c in final_df.columns],
                              errors='ignore')

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)

    print(f"\nSaved aggregated results to {output_path}")
    print(f"Total rows: {len(final_df)}")
    print(f"Models: {sorted(final_df['model_name'].unique())}")
    print(f"Prefixes: {sorted(final_df['prefix_key'].unique())}")

    return final_df


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Aggregate prefix experiment results")
    parser.add_argument("--base-dir", type=str,
                        default="results/v4_prefix_experiment")
    parser.add_argument("--output-file", type=str,
                        default="results/v4_prefix_experiment/all_prefix_results.csv")
    args = parser.parse_args()

    aggregate_prefix_results(args.base_dir, args.output_file)


if __name__ == "__main__":
    main()
