"""Analysis and visualization for the prompt prefix experiment.

Produces:
1. Correctness vs Safety tradeoff plot
2. Per-category hallucination heatmap
3. Refusal rate bar chart
4. McNemar's test for statistical significance
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from scipy.stats import chi2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ── Metric computation ──────────────────────────────────────────────────────

def compute_prefix_metrics(df):
    """Compute rates per (model, prefix) combination."""
    def _rates(g):
        return pd.Series({
            'n_prompts': len(g),
            'correct_rate': (g['judge_label'] == 0).mean(),
            'partial_rate': (g['judge_label'] == 1).mean(),
            'hallucination_rate': (g['judge_label'] == 2).mean(),
            'refusal_rate': (g['judge_label'] == 3).mean(),
            'safety_rate': 1 - (g['judge_label'] == 2).mean(),
        })
    metrics = df.groupby(['model_name', 'prefix_key']).apply(
        _rates, include_groups=False
    ).reset_index()
    return metrics


def compute_category_metrics(df):
    """Compute rates per (model, prefix, category)."""
    def _rates(g):
        return pd.Series({
            'n_prompts': len(g),
            'correct_rate': (g['judge_label'] == 0).mean(),
            'hallucination_rate': (g['judge_label'] == 2).mean(),
            'refusal_rate': (g['judge_label'] == 3).mean(),
        })
    metrics = df.groupby(['model_name', 'prefix_key', 'category']).apply(
        _rates, include_groups=False
    ).reset_index()
    return metrics


# ── Statistical tests ────────────────────────────────────────────────────────

def mcnemar_test(baseline_labels, prefix_labels):
    """McNemar's test for paired binary outcomes (hallucinated vs not).

    Args:
        baseline_labels: Array of is_hallucinated (0/1) for baseline.
        prefix_labels: Array of is_hallucinated (0/1) for prefix condition.

    Returns:
        dict with chi2 statistic, p-value, and counts.
    """
    b = int(((baseline_labels == 1) & (prefix_labels == 0)).sum())  # improved
    c = int(((baseline_labels == 0) & (prefix_labels == 1)).sum())  # worsened

    if b + c == 0:
        return {'chi2': 0.0, 'p_value': 1.0, 'improved': b, 'worsened': c}

    chi2_stat = (b - c) ** 2 / (b + c)
    p_value = 1 - chi2.cdf(chi2_stat, df=1)

    return {
        'chi2': round(chi2_stat, 4),
        'p_value': round(p_value, 6),
        'improved': b,
        'worsened': c,
    }


def run_statistical_tests(df, baselines_file=None):
    """Run McNemar's test for each (model, prefix) vs the V3 baseline.

    If baselines_file is provided, loads V3 baseline labels.
    Otherwise, assumes the master CSV includes a 'no_prefix' condition.
    """
    results = []

    # Try to load V3 baseline data for comparison
    if baselines_file and Path(baselines_file).exists():
        v3_df = pd.read_csv(baselines_file)
    else:
        v3_df = None

    for model in df['model_name'].unique():
        model_df = df[df['model_name'] == model]
        prefixes = model_df['prefix_key'].unique()

        for prefix in prefixes:
            prefix_df = model_df[model_df['prefix_key'] == prefix].set_index('id')

            # Get baseline for this model (from V3 data or 'no_prefix' condition)
            if v3_df is not None and model in v3_df['model_name'].values:
                baseline_df = v3_df[v3_df['model_name'] == model].set_index('id')
            else:
                continue

            # Align on common prompt IDs
            common_ids = prefix_df.index.intersection(baseline_df.index)
            if len(common_ids) == 0:
                continue

            baseline_hall = (baseline_df.loc[common_ids, 'judge_label'] == 2).astype(int).values
            prefix_hall = (prefix_df.loc[common_ids, 'judge_label'] == 2).astype(int).values

            test_result = mcnemar_test(baseline_hall, prefix_hall)
            test_result['model'] = model
            test_result['prefix_key'] = prefix
            test_result['n_common'] = len(common_ids)
            test_result['baseline_rate'] = baseline_hall.mean()
            test_result['prefix_rate'] = prefix_hall.mean()
            test_result['reduction'] = baseline_hall.mean() - prefix_hall.mean()
            results.append(test_result)

    return pd.DataFrame(results)


# ── Visualizations ───────────────────────────────────────────────────────────

PREFIX_ORDER = [
    'epistemic_humility', 'fact_grounded', 'entity_aware',
    'structured_caution', 'cot_verification',
]

PREFIX_LABELS = {
    'epistemic_humility': 'Epistemic\nHumility',
    'fact_grounded': 'Fact-\nGrounded',
    'entity_aware': 'Entity-\nAware',
    'structured_caution': 'Structured\nCaution',
    'cot_verification': 'CoT\nVerification',
}


def plot_tradeoff_curve(metrics_df, output_dir):
    """Correctness Rate (X) vs Safety Rate (Y) per (model, prefix)."""
    fig, ax = plt.subplots(figsize=(10, 8))

    markers = {'mixtral-8x7b': 'o', 'llama-4-maverick-17b': 's'}
    colors = sns.color_palette('tab10', n_colors=len(PREFIX_ORDER))
    prefix_color = {k: colors[i] for i, k in enumerate(PREFIX_ORDER)}

    for model in metrics_df['model_name'].unique():
        model_data = metrics_df[metrics_df['model_name'] == model]
        marker = markers.get(model, 'D')

        for _, row in model_data.iterrows():
            color = prefix_color.get(row['prefix_key'], 'gray')
            label = PREFIX_LABELS.get(row['prefix_key'], row['prefix_key'])
            ax.scatter(
                row['correct_rate'], row['safety_rate'],
                marker=marker, s=120, color=color, zorder=5,
                edgecolors='black', linewidth=0.5,
            )
            ax.annotate(
                label,
                (row['correct_rate'], row['safety_rate']),
                textcoords="offset points", xytext=(8, 5),
                fontsize=7, ha='left',
            )

    # Legend entries for models
    for model, marker in markers.items():
        ax.scatter([], [], marker=marker, color='gray', s=80, label=model)

    ax.set_xlabel('Correctness Rate', fontsize=12)
    ax.set_ylabel('Safety Rate (1 - Hallucination Rate)', fontsize=12)
    ax.set_title('Correctness vs Safety Tradeoff by Prompt Prefix', fontsize=14)
    ax.legend(loc='lower left', fontsize=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'tradeoff_curve.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved tradeoff_curve.png")


def plot_category_heatmap(category_metrics, output_dir):
    """Heatmap of hallucination rate by prefix x category for each model."""
    for model in category_metrics['model_name'].unique():
        model_data = category_metrics[category_metrics['model_name'] == model]

        pivot = model_data.pivot_table(
            index='prefix_key', columns='category',
            values='hallucination_rate', aggfunc='first',
        )

        # Reorder rows
        ordered = [p for p in PREFIX_ORDER if p in pivot.index]
        pivot = pivot.loc[ordered]

        fig, ax = plt.subplots(figsize=(12, 5))
        sns.heatmap(
            pivot, annot=True, fmt='.1%', cmap='RdYlGn_r',
            vmin=0, vmax=0.5, ax=ax,
            yticklabels=[PREFIX_LABELS.get(p, p) for p in ordered],
        )
        ax.set_title(f'Hallucination Rate: {model}', fontsize=13)
        ax.set_ylabel('')
        ax.set_xlabel('Prompt Category')

        plt.tight_layout()
        fname = f'category_heatmap_{model}.png'
        plt.savefig(Path(output_dir) / fname, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved {fname}")


def plot_refusal_rates(metrics_df, output_dir):
    """Grouped bar chart of refusal rates by (model, prefix)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    models = sorted(metrics_df['model_name'].unique())
    x = np.arange(len(PREFIX_ORDER))
    width = 0.35

    for i, model in enumerate(models):
        model_data = metrics_df[metrics_df['model_name'] == model]
        rates = []
        for prefix in PREFIX_ORDER:
            row = model_data[model_data['prefix_key'] == prefix]
            rates.append(row['refusal_rate'].values[0] if len(row) > 0 else 0)

        offset = (i - (len(models) - 1) / 2) * width
        ax.bar(x + offset, rates, width, label=model, alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels([PREFIX_LABELS.get(p, p) for p in PREFIX_ORDER], fontsize=9)
    ax.set_ylabel('Refusal Rate', fontsize=12)
    ax.set_title('Refusal Rate by Prompt Prefix', fontsize=14)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'refusal_rates.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved refusal_rates.png")


# ── Main ─────────────────────────────────────────────────────────────────────

def run_analysis(results_file, v3_results_file, output_dir):
    """Run full prefix experiment analysis."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(results_file)
    print(f"Loaded {len(df)} rows from {results_file}")

    # Compute metrics
    metrics = compute_prefix_metrics(df)
    metrics.to_csv(output_path / 'prefix_metrics_summary.csv', index=False)
    print("\n=== Prefix Metrics Summary ===")
    print(metrics.to_string(index=False))

    category_metrics = compute_category_metrics(df)
    category_metrics.to_csv(output_path / 'category_metrics_summary.csv', index=False)

    # Statistical tests
    stat_tests = run_statistical_tests(df, v3_results_file)
    if len(stat_tests) > 0:
        stat_tests.to_csv(output_path / 'statistical_tests.csv', index=False)
        print("\n=== Statistical Tests (McNemar) ===")
        print(stat_tests.to_string(index=False))

    # Plots
    plot_tradeoff_curve(metrics, output_path)
    plot_category_heatmap(category_metrics, output_path)
    plot_refusal_rates(metrics, output_path)

    print(f"\nAll outputs saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze prefix experiment results")
    parser.add_argument("--results-file", type=str,
                        default="results/v4_prefix_experiment/all_prefix_results.csv")
    parser.add_argument("--v3-results-file", type=str,
                        default="results/v3/multi_model/all_models_results.csv")
    parser.add_argument("--output-dir", type=str,
                        default="results/v4_prefix_experiment/analysis")
    args = parser.parse_args()

    run_analysis(args.results_file, args.v3_results_file, args.output_dir)


if __name__ == "__main__":
    main()
