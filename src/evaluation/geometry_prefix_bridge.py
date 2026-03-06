"""Bridge analysis: Do geometric features predict where prefixes help?

Tests whether prompts "fixed" by prefixes (hallucinated at baseline, correct
with prefix) have different geometric signatures than other prompts.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

GEO_FEATURES = ['curvature_score', 'oppositeness_score', 'density', 'centrality']
TARGET_MODELS = ['mixtral-8x7b', 'llama-4-maverick-17b']


def load_and_merge(v3_file, v4_file):
    """Load V3 baseline and V4 prefix results, merge on prompt ID."""
    v3 = pd.read_csv(v3_file)
    v4 = pd.read_csv(v4_file)

    v3 = v3[v3['model_name'].isin(TARGET_MODELS)]
    v4 = v4[v4['model_name'].isin(TARGET_MODELS)]

    return v3, v4


def tag_prompt_outcomes(v3, v4):
    """For each (model, prefix, prompt), classify the outcome.

    Categories:
    - 'fixed': hallucinated at baseline, correct/partial/refused with prefix
    - 'still_broken': hallucinated at baseline AND with prefix
    - 'already_correct': correct at baseline
    - 'regressed': correct at baseline, hallucinated with prefix
    - 'other': partial/refused at baseline
    """
    records = []

    for model in TARGET_MODELS:
        v3_model = v3[v3['model_name'] == model].set_index('id')

        for prefix in v4[v4['model_name'] == model]['prefix_key'].unique():
            v4_slice = v4[(v4['model_name'] == model) & (v4['prefix_key'] == prefix)].set_index('id')

            common = v3_model.index.intersection(v4_slice.index)

            for pid in common:
                baseline_label = v3_model.loc[pid, 'judge_label']
                prefix_label = v4_slice.loc[pid, 'judge_label']

                # Handle duplicate indices by taking first
                if isinstance(baseline_label, pd.Series):
                    baseline_label = baseline_label.iloc[0]
                if isinstance(prefix_label, pd.Series):
                    prefix_label = prefix_label.iloc[0]

                baseline_hall = (baseline_label == 2)
                prefix_hall = (prefix_label == 2)
                baseline_correct = (baseline_label == 0)

                if baseline_hall and not prefix_hall:
                    outcome = 'fixed'
                elif baseline_hall and prefix_hall:
                    outcome = 'still_broken'
                elif baseline_correct and prefix_hall:
                    outcome = 'regressed'
                elif baseline_correct and not prefix_hall:
                    outcome = 'already_correct'
                else:
                    outcome = 'other'

                # Get geometry features
                geo = {}
                for feat in GEO_FEATURES:
                    val = v4_slice.loc[pid, feat]
                    if isinstance(val, pd.Series):
                        val = val.iloc[0]
                    geo[feat] = val

                records.append({
                    'id': pid,
                    'model': model,
                    'prefix': prefix,
                    'baseline_label': baseline_label,
                    'prefix_label': prefix_label,
                    'outcome': outcome,
                    **geo,
                })

    return pd.DataFrame(records)


def run_statistical_tests(df):
    """Compare geometric features between 'fixed' and other categories."""
    print("\n" + "=" * 70)
    print("STATISTICAL TESTS: Geometric features by outcome")
    print("=" * 70)

    results = []

    for model in TARGET_MODELS:
        model_df = df[df['model'] == model]
        print(f"\n{'─' * 50}")
        print(f"Model: {model}")
        print(f"{'─' * 50}")

        # Outcome counts (across all prefixes)
        print("\nOutcome counts (summed across prefixes):")
        print(model_df['outcome'].value_counts().to_string())

        # For meaningful comparison: fixed vs already_correct
        fixed = model_df[model_df['outcome'] == 'fixed']
        correct = model_df[model_df['outcome'] == 'already_correct']
        broken = model_df[model_df['outcome'] == 'still_broken']

        print(f"\nFixed: {len(fixed)} | Already Correct: {len(correct)} | Still Broken: {len(broken)}")

        for feat in GEO_FEATURES:
            fixed_vals = fixed[feat].dropna()
            correct_vals = correct[feat].dropna()

            if len(fixed_vals) < 5 or len(correct_vals) < 5:
                print(f"\n  {feat}: too few samples for test")
                continue

            # Mann-Whitney U test (non-parametric)
            u_stat, p_val = stats.mannwhitneyu(fixed_vals, correct_vals, alternative='two-sided')

            # Effect size (rank-biserial correlation)
            n1, n2 = len(fixed_vals), len(correct_vals)
            r = 1 - (2 * u_stat) / (n1 * n2)

            print(f"\n  {feat}:")
            print(f"    Fixed mean:   {fixed_vals.mean():.4f} (std {fixed_vals.std():.4f})")
            print(f"    Correct mean: {correct_vals.mean():.4f} (std {correct_vals.std():.4f})")
            print(f"    Mann-Whitney U p = {p_val:.6f}  |  effect size r = {r:.4f}")

            results.append({
                'model': model,
                'feature': feat,
                'fixed_mean': fixed_vals.mean(),
                'correct_mean': correct_vals.mean(),
                'fixed_std': fixed_vals.std(),
                'correct_std': correct_vals.std(),
                'u_statistic': u_stat,
                'p_value': p_val,
                'effect_size_r': r,
                'n_fixed': len(fixed_vals),
                'n_correct': len(correct_vals),
            })

        # Also test: still_broken vs fixed (if enough samples)
        if len(broken) >= 5:
            print(f"\n  --- Still Broken ({len(broken)}) vs Fixed ({len(fixed)}) ---")
            for feat in GEO_FEATURES:
                broken_vals = broken[feat].dropna()
                fixed_vals = fixed[feat].dropna()
                if len(broken_vals) < 3:
                    continue
                u_stat, p_val = stats.mannwhitneyu(broken_vals, fixed_vals, alternative='two-sided')
                print(f"    {feat}: broken_mean={broken_vals.mean():.4f} vs fixed_mean={fixed_vals.mean():.4f}  p={p_val:.6f}")

    return pd.DataFrame(results)


def run_logistic_regression(df):
    """Logistic regression: can geometry predict whether a prefix will fix a hallucination?"""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score, classification_report

    print("\n" + "=" * 70)
    print("LOGISTIC REGRESSION: Predicting 'fixed' vs 'still_broken'")
    print("=" * 70)

    for model in TARGET_MODELS:
        model_df = df[df['model'] == model]

        # Only look at prompts that hallucinated at baseline
        hall_df = model_df[model_df['outcome'].isin(['fixed', 'still_broken'])].copy()
        hall_df['y'] = (hall_df['outcome'] == 'fixed').astype(int)

        # Drop rows with missing geometry
        hall_df = hall_df.dropna(subset=GEO_FEATURES)

        if len(hall_df) < 10 or hall_df['y'].nunique() < 2:
            print(f"\n{model}: Not enough samples for regression (n={len(hall_df)})")
            continue

        X = hall_df[GEO_FEATURES].values
        y = hall_df['y'].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        lr = LogisticRegression(random_state=42, max_iter=1000)
        lr.fit(X_scaled, y)

        probs = lr.predict_proba(X_scaled)[:, 1]
        auc = roc_auc_score(y, probs)

        print(f"\n{model} (n={len(hall_df)}, {y.sum()} fixed, {len(y)-y.sum()} still broken):")
        print(f"  AUC-ROC: {auc:.3f}")
        print(f"  Feature coefficients (standardized):")
        for feat, coef in zip(GEO_FEATURES, lr.coef_[0]):
            direction = "→ more likely FIXED" if coef > 0 else "→ more likely STILL BROKEN"
            print(f"    {feat:25s}: {coef:+.4f}  {direction}")


def plot_geometry_by_outcome(df, output_dir):
    """Scatter plots of geometric features colored by outcome."""
    output_path = Path(output_dir)

    for model in TARGET_MODELS:
        model_df = df[df['model'] == model]

        # Deduplicate to unique prompts (take most common outcome across prefixes)
        prompt_outcomes = model_df.groupby('id').agg({
            'outcome': lambda x: x.value_counts().index[0],  # most common
            'curvature_score': 'first',
            'oppositeness_score': 'first',
            'density': 'first',
            'centrality': 'first',
        }).reset_index()

        # Focus on interesting categories
        plot_df = prompt_outcomes[prompt_outcomes['outcome'].isin(
            ['fixed', 'still_broken', 'already_correct']
        )].copy()
        plot_df = plot_df.dropna(subset=['centrality', 'curvature_score'])

        colors = {
            'already_correct': '#2ecc71',
            'fixed': '#3498db',
            'still_broken': '#e74c3c',
        }
        labels = {
            'already_correct': 'Already Correct (baseline)',
            'fixed': 'Fixed by Prefix',
            'still_broken': 'Still Hallucinated',
        }

        fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

        # Plot 1: Centrality vs Curvature
        ax = axes[0]
        for outcome in ['already_correct', 'fixed', 'still_broken']:
            subset = plot_df[plot_df['outcome'] == outcome]
            ax.scatter(subset['centrality'], subset['curvature_score'],
                      c=colors[outcome], label=labels[outcome],
                      alpha=0.5, s=40, edgecolors='black', linewidth=0.3)
        ax.set_xlabel('Centrality', fontsize=11)
        ax.set_ylabel('Curvature Score', fontsize=11)
        ax.set_title('Centrality vs Curvature', fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Plot 2: Density vs Centrality
        ax = axes[1]
        for outcome in ['already_correct', 'fixed', 'still_broken']:
            subset = plot_df[plot_df['outcome'] == outcome]
            ax.scatter(subset['density'], subset['centrality'],
                      c=colors[outcome], label=labels[outcome],
                      alpha=0.5, s=40, edgecolors='black', linewidth=0.3)
        ax.set_xlabel('Density', fontsize=11)
        ax.set_ylabel('Centrality', fontsize=11)
        ax.set_title('Density vs Centrality', fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Plot 3: Box plots of all features by outcome
        ax = axes[2]
        melt_df = plot_df.melt(
            id_vars=['id', 'outcome'],
            value_vars=GEO_FEATURES,
            var_name='feature', value_name='value'
        )
        # Normalize features to [0,1] for comparable box plots
        for feat in GEO_FEATURES:
            mask = melt_df['feature'] == feat
            vals = melt_df.loc[mask, 'value']
            if vals.max() != vals.min():
                melt_df.loc[mask, 'value'] = (vals - vals.min()) / (vals.max() - vals.min())

        melt_df = melt_df[melt_df['outcome'].isin(['fixed', 'still_broken', 'already_correct'])]
        sns.boxplot(data=melt_df, x='feature', y='value', hue='outcome',
                   palette=colors, ax=ax, fliersize=2)
        ax.set_xlabel('')
        ax.set_ylabel('Normalized Value', fontsize=11)
        ax.set_title('Feature Distributions by Outcome', fontsize=12)
        ax.tick_params(axis='x', rotation=20)
        ax.legend(fontsize=7, title_fontsize=8)
        ax.grid(axis='y', alpha=0.3)

        model_label = 'Mixtral 8x7B' if 'mixtral' in model else 'Llama 4 Maverick'
        fig.suptitle(f'Geometric Features vs Prefix Effectiveness: {model_label}',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()

        fname = f'geometry_bridge_{model}.png'
        plt.savefig(output_path / fname, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved {fname}")


def main():
    v3_file = "results/v3/multi_model/all_models_results.csv"
    v4_file = "results/v4_prefix_experiment/all_prefix_results.csv"
    output_dir = "results/v4_prefix_experiment/analysis"

    v3, v4 = load_and_merge(v3_file, v4_file)
    df = tag_prompt_outcomes(v3, v4)

    # Save tagged data
    df.to_csv(Path(output_dir) / 'geometry_bridge_data.csv', index=False)

    # Run analyses
    stat_results = run_statistical_tests(df)
    stat_results.to_csv(Path(output_dir) / 'geometry_bridge_stats.csv', index=False)

    run_logistic_regression(df)

    plot_geometry_by_outcome(df, output_dir)

    print("\nDone.")


if __name__ == "__main__":
    main()
