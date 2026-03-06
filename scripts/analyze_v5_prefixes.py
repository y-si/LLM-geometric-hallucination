"""V5 Prefix Summary Analysis (Step 8A).

Loads all V5 baseline + prefix judged results, computes aggregate metrics,
runs McNemar's tests, generates thesis-quality visualizations, and compares
with V4 results.

Usage:
    python3 scripts/analyze_v5_prefixes.py

Output:
    results/v5_prefixes/analysis/
    ├── v5_prefix_metrics.csv
    ├── v5_category_metrics.csv
    ├── v5_mcnemar_tests.csv
    ├── v5_judge_agreement.csv
    ├── v5_v4_comparison.csv
    ├── v5_tradeoff_curve.png
    ├── v5_category_heatmap_mixtral-8x7b.png
    ├── v5_category_heatmap_llama-4-maverick-17b.png
    ├── v5_refusal_rates.png
    └── v5_judge_agreement.png
"""

import sys
import json
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl

# ── Constants ─────────────────────────────────────────────────────────────

MODELS = ['mixtral-8x7b', 'llama-4-maverick-17b']
PREFIX_ORDER = [
    'epistemic_humility', 'fact_grounded', 'entity_aware',
    'structured_caution', 'cot_verification',
]
PREFIX_LABELS = {
    'epistemic_humility': 'Epistemic Humility',
    'fact_grounded': 'Fact-Grounded',
    'entity_aware': 'Entity-Aware',
    'structured_caution': 'Structured Caution',
    'cot_verification': 'CoT Verification',
    'no_prefix': 'No Prefix (Baseline)',
}
MODEL_LABELS = {
    'mixtral-8x7b': 'Mixtral 8x7B',
    'llama-4-maverick-17b': 'Llama 4 Maverick',
}
CATEGORY_LABELS = {
    'ambiguous': 'Ambiguous',
    'borderline_edge_factual': 'Borderline\nEdge Factual',
    'borderline_obscure_real': 'Borderline\nObscure Real',
    'borderline_plausible_fake': 'Borderline\nPlausible Fake',
    'factual': 'Factual',
    'impossible': 'Impossible',
    'nonexistent': 'Nonexistent',
}

BASELINES_DIR = PROJECT_ROOT / 'results' / 'v5_baselines'
PREFIXES_DIR = PROJECT_ROOT / 'results' / 'v5_prefixes'
OUTPUT_DIR = PREFIXES_DIR / 'analysis'

# V4 results for comparison (from V4 experiment)
V4_METRICS = {
    'mixtral-8x7b': {
        'baseline': {'correct_rate': 0.829, 'hallucination_rate': 0.118, 'refusal_rate': 0.020},
        'entity_aware': {'correct_rate': 0.911, 'hallucination_rate': 0.0067},
        'structured_caution': {'correct_rate': 0.911, 'hallucination_rate': 0.0089},
    },
    'llama-4-maverick-17b': {
        'baseline': {'correct_rate': 0.906, 'hallucination_rate': 0.058, 'refusal_rate': 0.009},
        'structured_caution': {'correct_rate': 0.933, 'hallucination_rate': 0.0045},
        'entity_aware': {'correct_rate': 0.929, 'hallucination_rate': 0.0067},
    },
}


# ── Data Loading ──────────────────────────────────────────────────────────

def load_all_results():
    """Load all V5 baseline + prefix judged results into a single DataFrame."""
    rows = []

    for model in MODELS:
        # Baselines
        baseline_path = BASELINES_DIR / model / 'no_prefix' / 'judged_answers.jsonl'
        if baseline_path.exists():
            entries = read_jsonl(baseline_path)
            for e in entries:
                rows.append({
                    'id': e['id'],
                    'category': e['category'],
                    'model_name': model,
                    'prefix_key': 'no_prefix',
                    'judge_label': int(e['judge_label']),
                    'judge_confidence': float(e['judge_confidence']),
                    'agreement_rate': float(e['agreement_rate']),
                    'individual_confidence_avg': float(e['individual_confidence_avg']),
                })
            print(f"  Loaded {len(entries)} baseline entries for {model}")

        # Prefixes
        for prefix in PREFIX_ORDER:
            prefix_path = PREFIXES_DIR / model / prefix / 'judged_answers.jsonl'
            if prefix_path.exists():
                entries = read_jsonl(prefix_path)
                for e in entries:
                    rows.append({
                        'id': e['id'],
                        'category': e['category'],
                        'model_name': model,
                        'prefix_key': prefix,
                        'judge_label': int(e['judge_label']),
                        'judge_confidence': float(e['judge_confidence']),
                        'agreement_rate': float(e['agreement_rate']),
                        'individual_confidence_avg': float(e['individual_confidence_avg']),
                    })
                print(f"  Loaded {len(entries)} entries for {model}/{prefix}")

    df = pd.DataFrame(rows)
    print(f"\n  Total: {len(df)} rows ({df['model_name'].nunique()} models, "
          f"{df['prefix_key'].nunique()} conditions)")
    return df


# ── Metrics ───────────────────────────────────────────────────────────────

def compute_prefix_metrics(df):
    """Compute rates per (model, prefix) combination."""
    def _rates(g):
        n = len(g)
        return pd.Series({
            'n_prompts': n,
            'correct': (g['judge_label'] == 0).sum(),
            'partial': (g['judge_label'] == 1).sum(),
            'hallucination': (g['judge_label'] == 2).sum(),
            'refusal': (g['judge_label'] == 3).sum(),
            'correct_rate': (g['judge_label'] == 0).mean(),
            'partial_rate': (g['judge_label'] == 1).mean(),
            'hallucination_rate': (g['judge_label'] == 2).mean(),
            'refusal_rate': (g['judge_label'] == 3).mean(),
            'safety_rate': 1 - (g['judge_label'] == 2).mean(),
        })
    return df.groupby(['model_name', 'prefix_key']).apply(
        _rates, include_groups=False
    ).reset_index()


def compute_category_metrics(df):
    """Compute rates per (model, prefix, category)."""
    def _rates(g):
        n = len(g)
        return pd.Series({
            'n_prompts': n,
            'correct_rate': (g['judge_label'] == 0).mean(),
            'hallucination_rate': (g['judge_label'] == 2).mean(),
            'refusal_rate': (g['judge_label'] == 3).mean(),
        })
    return df.groupby(['model_name', 'prefix_key', 'category']).apply(
        _rates, include_groups=False
    ).reset_index()


def compute_judge_agreement(df):
    """Compute judge agreement stats per (model, prefix) and per (model, prefix, category)."""
    overall = df.groupby(['model_name', 'prefix_key']).agg(
        mean_agreement=('agreement_rate', 'mean'),
        median_agreement=('agreement_rate', 'median'),
        unanimous_frac=('agreement_rate', lambda x: (x == 1.0).mean()),
        mean_confidence=('individual_confidence_avg', 'mean'),
        n=('agreement_rate', 'count'),
    ).reset_index()

    by_category = df.groupby(['model_name', 'prefix_key', 'category']).agg(
        mean_agreement=('agreement_rate', 'mean'),
        unanimous_frac=('agreement_rate', lambda x: (x == 1.0).mean()),
        n=('agreement_rate', 'count'),
    ).reset_index()

    return overall, by_category


# ── Statistical Tests ─────────────────────────────────────────────────────

def mcnemar_test(baseline_hall, prefix_hall):
    """McNemar's test for paired binary outcomes."""
    b = int(((baseline_hall == 1) & (prefix_hall == 0)).sum())  # improved
    c = int(((baseline_hall == 0) & (prefix_hall == 1)).sum())  # worsened

    if b + c == 0:
        return {'chi2': 0.0, 'p_value': 1.0, 'improved': b, 'worsened': c}

    chi2_stat = (b - c) ** 2 / (b + c)
    p_value = 1 - chi2.cdf(chi2_stat, df=1)

    return {
        'chi2': round(chi2_stat, 4),
        'p_value': p_value,
        'improved': b,
        'worsened': c,
    }


def run_mcnemar_tests(df):
    """Run McNemar's test for each (model, prefix) vs baseline (no_prefix)."""
    results = []

    for model in df['model_name'].unique():
        model_df = df[df['model_name'] == model]
        baseline_df = model_df[model_df['prefix_key'] == 'no_prefix'].set_index('id')

        if len(baseline_df) == 0:
            print(f"  WARNING: no baseline for {model}")
            continue

        for prefix in PREFIX_ORDER:
            prefix_df = model_df[model_df['prefix_key'] == prefix].set_index('id')
            if len(prefix_df) == 0:
                continue

            common_ids = baseline_df.index.intersection(prefix_df.index)
            if len(common_ids) == 0:
                continue

            baseline_hall = (baseline_df.loc[common_ids, 'judge_label'] == 2).astype(int).values
            prefix_hall = (prefix_df.loc[common_ids, 'judge_label'] == 2).astype(int).values

            test = mcnemar_test(baseline_hall, prefix_hall)
            test['model'] = model
            test['prefix_key'] = prefix
            test['n_common'] = len(common_ids)
            test['baseline_rate'] = baseline_hall.mean()
            test['prefix_rate'] = prefix_hall.mean()
            test['reduction'] = baseline_hall.mean() - prefix_hall.mean()
            test['relative_reduction'] = (
                (baseline_hall.mean() - prefix_hall.mean()) / baseline_hall.mean()
                if baseline_hall.mean() > 0 else 0
            )
            test['significant'] = test['p_value'] < 0.05
            results.append(test)

    return pd.DataFrame(results)


# ── V4 Comparison ─────────────────────────────────────────────────────────

def build_v4_comparison(v5_metrics):
    """Build comparison table between V4 and V5 results."""
    rows = []

    for model in MODELS:
        v4_model = V4_METRICS.get(model, {})
        v4_baseline = v4_model.get('baseline', {})

        # Get V5 baseline
        v5_baseline = v5_metrics[
            (v5_metrics['model_name'] == model) &
            (v5_metrics['prefix_key'] == 'no_prefix')
        ]
        if len(v5_baseline) == 0:
            continue
        v5_bl = v5_baseline.iloc[0]

        rows.append({
            'model': model,
            'condition': 'baseline',
            'v4_correct_rate': v4_baseline.get('correct_rate', None),
            'v5_correct_rate': v5_bl['correct_rate'],
            'v4_hallucination_rate': v4_baseline.get('hallucination_rate', None),
            'v5_hallucination_rate': v5_bl['hallucination_rate'],
            'v4_n': 449,
            'v5_n': int(v5_bl['n_prompts']),
        })

        for prefix in PREFIX_ORDER:
            v5_prefix = v5_metrics[
                (v5_metrics['model_name'] == model) &
                (v5_metrics['prefix_key'] == prefix)
            ]
            if len(v5_prefix) == 0:
                continue
            v5_p = v5_prefix.iloc[0]

            v4_p = v4_model.get(prefix, {})
            rows.append({
                'model': model,
                'condition': prefix,
                'v4_correct_rate': v4_p.get('correct_rate', None),
                'v5_correct_rate': v5_p['correct_rate'],
                'v4_hallucination_rate': v4_p.get('hallucination_rate', None),
                'v5_hallucination_rate': v5_p['hallucination_rate'],
                'v4_n': 449 if v4_p else None,
                'v5_n': int(v5_p['n_prompts']),
            })

    return pd.DataFrame(rows)


# ── Visualizations ────────────────────────────────────────────────────────

def plot_tradeoff_curve(metrics_df, output_dir):
    """Correctness vs Safety tradeoff plot with V5 baselines and prefix points."""
    fig, ax = plt.subplots(figsize=(11, 8))

    markers = {'mixtral-8x7b': 'o', 'llama-4-maverick-17b': 's'}
    colors = sns.color_palette('Set2', n_colors=len(PREFIX_ORDER))
    prefix_color = {k: colors[i] for i, k in enumerate(PREFIX_ORDER)}

    # Get baselines from the metrics
    baselines = {}
    for model in MODELS:
        bl = metrics_df[
            (metrics_df['model_name'] == model) &
            (metrics_df['prefix_key'] == 'no_prefix')
        ]
        if len(bl) > 0:
            baselines[model] = {
                'correct_rate': bl.iloc[0]['correct_rate'],
                'safety_rate': bl.iloc[0]['safety_rate'],
            }

    # Plot baseline points
    baseline_offsets = {
        'mixtral-8x7b': (15, 10),
        'llama-4-maverick-17b': (-15, -22),
    }
    for model, bl in baselines.items():
        marker = markers.get(model, 'D')
        ax.scatter(
            bl['correct_rate'], bl['safety_rate'],
            marker=marker, s=200, color='red', zorder=10,
            edgecolors='darkred', linewidth=1.5,
        )
        model_label = MODEL_LABELS.get(model, model)
        offset = baseline_offsets.get(model, (-15, -20))
        ax.annotate(
            f'{model_label}\n(baseline)',
            (bl['correct_rate'], bl['safety_rate']),
            textcoords="offset points", xytext=offset,
            fontsize=9, ha='center', color='red', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='red', alpha=0.8),
        )

    # Plot prefix points with arrows from baseline
    prefix_data = metrics_df[metrics_df['prefix_key'] != 'no_prefix']
    for model in prefix_data['model_name'].unique():
        model_data = prefix_data[prefix_data['model_name'] == model]
        marker = markers.get(model, 'D')
        bl = baselines.get(model)

        for _, row in model_data.iterrows():
            color = prefix_color.get(row['prefix_key'], 'gray')
            label = PREFIX_LABELS.get(row['prefix_key'], row['prefix_key'])

            ax.scatter(
                row['correct_rate'], row['safety_rate'],
                marker=marker, s=140, color=color, zorder=5,
                edgecolors='black', linewidth=0.8,
            )

            if bl:
                ax.annotate(
                    '', xy=(row['correct_rate'], row['safety_rate']),
                    xytext=(bl['correct_rate'], bl['safety_rate']),
                    arrowprops=dict(arrowstyle='->', color=color,
                                    lw=1.2, alpha=0.4),
                )

            ax.annotate(
                label,
                (row['correct_rate'], row['safety_rate']),
                textcoords="offset points", xytext=(10, 4),
                fontsize=7.5, ha='left',
            )

    # Legend
    for model, marker in markers.items():
        model_label = MODEL_LABELS.get(model, model)
        ax.scatter([], [], marker=marker, color='gray', s=80,
                   edgecolors='black', label=model_label)
    ax.scatter([], [], marker='o', color='red', s=80,
               edgecolors='darkred', label='Baseline (no prefix)')
    for key in PREFIX_ORDER:
        ax.scatter([], [], marker='o', color=prefix_color[key], s=60,
                   edgecolors='black', linewidth=0.5,
                   label=PREFIX_LABELS[key])

    # Zoom to relevant region
    all_x = list(metrics_df['correct_rate'])
    all_y = list(metrics_df['safety_rate'])
    x_min = min(all_x) - 0.03
    x_max = max(all_x) + 0.03
    y_min = min(all_y) - 0.015
    y_max = min(max(all_y) + 0.015, 1.005)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    ax.set_xlabel('Correctness Rate', fontsize=13)
    ax.set_ylabel('Safety Rate (1 − Hallucination Rate)', fontsize=13)
    ax.set_title('V5 Correctness vs Safety Tradeoff by Prompt Prefix (n=2,430)', fontsize=15)
    ax.legend(loc='lower right', fontsize=8, ncol=2, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'v5_tradeoff_curve.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Saved v5_tradeoff_curve.png")


def plot_category_heatmap(category_metrics, output_dir):
    """Heatmap of hallucination rate by prefix x category for each model."""
    for model in MODELS:
        model_data = category_metrics[
            (category_metrics['model_name'] == model) &
            (category_metrics['prefix_key'] != 'no_prefix')
        ]

        pivot = model_data.pivot_table(
            index='prefix_key', columns='category',
            values='hallucination_rate', aggfunc='first',
        )

        ordered = [p for p in PREFIX_ORDER if p in pivot.index]
        pivot = pivot.loc[ordered]
        pivot.columns = [CATEGORY_LABELS.get(c, c) for c in pivot.columns]

        fig, ax = plt.subplots(figsize=(14, 4.5))
        sns.heatmap(
            pivot, annot=True, fmt='.1%', cmap='RdYlGn_r',
            vmin=0, vmax=0.25, ax=ax, linewidths=0.5,
            yticklabels=[PREFIX_LABELS.get(p, p) for p in ordered],
            annot_kws={'fontsize': 9},
        )
        model_label = MODEL_LABELS.get(model, model)
        ax.set_title(f'V5 Hallucination Rate by Category: {model_label} (n=2,430)', fontsize=13)
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.tick_params(axis='x', rotation=30)
        ax.tick_params(axis='y', rotation=0)

        plt.tight_layout()
        fname = f'v5_category_heatmap_{model}.png'
        plt.savefig(output_dir / fname, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved {fname}")


def plot_refusal_rates(metrics_df, output_dir):
    """Grouped bar chart of refusal rates."""
    prefix_data = metrics_df[metrics_df['prefix_key'] != 'no_prefix']

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(PREFIX_ORDER))
    width = 0.35

    for i, model in enumerate(MODELS):
        model_data = prefix_data[prefix_data['model_name'] == model]
        rates = []
        for prefix in PREFIX_ORDER:
            row = model_data[model_data['prefix_key'] == prefix]
            rates.append(row['refusal_rate'].values[0] if len(row) > 0 else 0)

        offset = (i - 0.5) * width
        model_label = MODEL_LABELS.get(model, model)
        ax.bar(x + offset, rates, width, label=model_label, alpha=0.8)

    # Add baseline refusal rates as horizontal lines
    for model in MODELS:
        bl = metrics_df[
            (metrics_df['model_name'] == model) &
            (metrics_df['prefix_key'] == 'no_prefix')
        ]
        if len(bl) > 0:
            model_label = MODEL_LABELS.get(model, model)
            ax.axhline(y=bl.iloc[0]['refusal_rate'], linestyle='--', alpha=0.5,
                       label=f'{model_label} baseline')

    ax.set_xticks(x)
    ax.set_xticklabels([PREFIX_LABELS.get(p, p) for p in PREFIX_ORDER], fontsize=9)
    ax.set_ylabel('Refusal Rate', fontsize=12)
    ax.set_title('V5 Refusal Rate by Prompt Prefix (n=2,430)', fontsize=14)
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'v5_refusal_rates.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Saved v5_refusal_rates.png")


def plot_judge_agreement(agreement_df, output_dir):
    """Bar chart of judge agreement and unanimous fraction by condition."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for i, model in enumerate(MODELS):
        ax = axes[i]
        model_data = agreement_df[agreement_df['model_name'] == model]

        # Include baseline + prefixes
        conditions = ['no_prefix'] + PREFIX_ORDER
        labels = [PREFIX_LABELS.get(c, c) for c in conditions]
        means = []
        unanims = []
        for c in conditions:
            row = model_data[model_data['prefix_key'] == c]
            if len(row) > 0:
                means.append(row.iloc[0]['mean_agreement'])
                unanims.append(row.iloc[0]['unanimous_frac'])
            else:
                means.append(0)
                unanims.append(0)

        x = np.arange(len(conditions))
        width = 0.35
        ax.bar(x - width/2, means, width, label='Mean Agreement', alpha=0.8)
        ax.bar(x + width/2, unanims, width, label='Unanimous Fraction', alpha=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=7, rotation=30, ha='right')
        ax.set_ylabel('Rate', fontsize=11)
        model_label = MODEL_LABELS.get(model, model)
        ax.set_title(f'{model_label}', fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, 1.05)

    fig.suptitle('V5 Judge Agreement by Condition', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'v5_judge_agreement.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  Saved v5_judge_agreement.png")


# ── Console Summary ───────────────────────────────────────────────────────

def print_summary(metrics, mcnemar_df, agreement_df, comparison_df):
    """Print a human-readable summary to console."""
    print(f"\n{'=' * 70}")
    print(f"  V5 PREFIX EXPERIMENT SUMMARY")
    print(f"{'=' * 70}")

    for model in MODELS:
        model_label = MODEL_LABELS.get(model, model)
        print(f"\n  {model_label}")
        print(f"  {'-' * 50}")

        model_metrics = metrics[metrics['model_name'] == model]

        # Baseline
        bl = model_metrics[model_metrics['prefix_key'] == 'no_prefix']
        if len(bl) > 0:
            bl = bl.iloc[0]
            print(f"  Baseline (no prefix): {bl['correct_rate']*100:.1f}% correct, "
                  f"{bl['hallucination_rate']*100:.1f}% hallucination, "
                  f"{bl['refusal_rate']*100:.1f}% refusal (n={int(bl['n_prompts'])})")

        # Prefix results
        print(f"\n  {'Prefix':<22s} {'Correct':>8s} {'Halluc':>8s} {'Refusal':>8s} {'p-value':>10s} {'Sig':>4s}")
        print(f"  {'-'*22} {'-'*8} {'-'*8} {'-'*8} {'-'*10} {'-'*4}")

        for prefix in PREFIX_ORDER:
            row = model_metrics[model_metrics['prefix_key'] == prefix]
            if len(row) == 0:
                continue
            row = row.iloc[0]

            # Get McNemar p-value
            mc = mcnemar_df[
                (mcnemar_df['model'] == model) &
                (mcnemar_df['prefix_key'] == prefix)
            ]
            p_str = f"{mc.iloc[0]['p_value']:.2e}" if len(mc) > 0 else "N/A"
            sig = "***" if len(mc) > 0 and mc.iloc[0]['p_value'] < 0.001 else (
                  "**" if len(mc) > 0 and mc.iloc[0]['p_value'] < 0.01 else (
                  "*" if len(mc) > 0 and mc.iloc[0]['p_value'] < 0.05 else ""))

            label = PREFIX_LABELS.get(prefix, prefix)
            print(f"  {label:<22s} {row['correct_rate']*100:>7.1f}% "
                  f"{row['hallucination_rate']*100:>7.1f}% "
                  f"{row['refusal_rate']*100:>7.1f}% "
                  f"{p_str:>10s} {sig:>4s}")

        # Best prefix
        prefixes_only = model_metrics[model_metrics['prefix_key'] != 'no_prefix']
        if len(prefixes_only) > 0:
            best = prefixes_only.loc[prefixes_only['hallucination_rate'].idxmin()]
            print(f"\n  Best prefix (lowest halluc): {PREFIX_LABELS.get(best['prefix_key'], best['prefix_key'])} "
                  f"({best['hallucination_rate']*100:.2f}%)")

    # V4 comparison
    if len(comparison_df) > 0:
        print(f"\n{'=' * 70}")
        print(f"  V4 vs V5 COMPARISON")
        print(f"{'=' * 70}")
        print(f"\n  {'Model':<25s} {'Condition':<22s} {'V4 Hall':>8s} {'V5 Hall':>8s} {'V4 n':>5s} {'V5 n':>6s}")
        print(f"  {'-'*25} {'-'*22} {'-'*8} {'-'*8} {'-'*5} {'-'*6}")
        for _, row in comparison_df.iterrows():
            v4_h = f"{row['v4_hallucination_rate']*100:.1f}%" if pd.notna(row['v4_hallucination_rate']) else "N/A"
            v5_h = f"{row['v5_hallucination_rate']*100:.1f}%"
            v4_n = str(int(row['v4_n'])) if pd.notna(row['v4_n']) else "N/A"
            model_label = MODEL_LABELS.get(row['model'], row['model'])
            cond_label = PREFIX_LABELS.get(row['condition'], row['condition'])
            print(f"  {model_label:<25s} {cond_label:<22s} {v4_h:>8s} {v5_h:>8s} {v4_n:>5s} {int(row['v5_n']):>6d}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading V5 results...")
    df = load_all_results()

    print("\nComputing prefix metrics...")
    metrics = compute_prefix_metrics(df)
    metrics.to_csv(OUTPUT_DIR / 'v5_prefix_metrics.csv', index=False)

    print("Computing category metrics...")
    cat_metrics = compute_category_metrics(df)
    cat_metrics.to_csv(OUTPUT_DIR / 'v5_category_metrics.csv', index=False)

    print("Computing judge agreement...")
    agreement_overall, agreement_by_cat = compute_judge_agreement(df)
    agreement_overall.to_csv(OUTPUT_DIR / 'v5_judge_agreement.csv', index=False)
    agreement_by_cat.to_csv(OUTPUT_DIR / 'v5_judge_agreement_by_category.csv', index=False)

    print("Running McNemar's tests...")
    mcnemar_df = run_mcnemar_tests(df)
    mcnemar_df.to_csv(OUTPUT_DIR / 'v5_mcnemar_tests.csv', index=False)

    print("Building V4 comparison...")
    comparison = build_v4_comparison(metrics)
    comparison.to_csv(OUTPUT_DIR / 'v5_v4_comparison.csv', index=False)

    print("\nGenerating plots...")
    plot_tradeoff_curve(metrics, OUTPUT_DIR)
    plot_category_heatmap(cat_metrics, OUTPUT_DIR)
    plot_refusal_rates(metrics, OUTPUT_DIR)
    plot_judge_agreement(agreement_overall, OUTPUT_DIR)

    print_summary(metrics, mcnemar_df, agreement_overall, comparison)

    print(f"\n{'=' * 70}")
    print(f"  All outputs saved to {OUTPUT_DIR}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
