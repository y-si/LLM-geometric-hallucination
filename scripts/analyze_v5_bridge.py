"""V5 Bridge Analysis (Step 8B).

Tests whether geometric features predict which V5 hallucinations are fixable
by prefixes. This is the V5 replication of the V4 bridge analysis (AUC=0.86).

Definitions (matching V4 code at src/evaluation/geometry_prefix_bridge.py):
- `fixed`: hallucinated at baseline (label=2), NOT hallucinating with at
  least 1 prefix (label != 2). Includes refusals and partials.
- `still_broken`: hallucinated at baseline, still hallucinating (label=2)
  with ALL 5 prefixes (or all available prefixes).
- `already_correct`: correct at baseline (label=0).
- `regressed`: correct at baseline, hallucinating with at least 1 prefix.
- `other`: partial/refused at baseline.

Usage:
    python3 scripts/analyze_v5_bridge.py

Output:
    results/v5_prefixes/analysis/
    ├── v5_bridge_data.csv
    ├── v5_bridge_stats.csv
    ├── v5_bridge_logistic_auc.csv
    ├── v5_bridge_within_category.csv
    ├── v5_bridge_mixtral-8x7b.png
    └── v5_bridge_llama-4-maverick-17b.png
"""

import sys
import json
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl

# ── Constants ─────────────────────────────────────────────────────────────

MODELS = ['mixtral-8x7b', 'llama-4-maverick-17b']
MODEL_LABELS = {
    'mixtral-8x7b': 'Mixtral 8x7B',
    'llama-4-maverick-17b': 'Llama 4 Maverick',
}
PREFIXES = [
    'epistemic_humility', 'fact_grounded', 'entity_aware',
    'structured_caution', 'cot_verification',
]
GEO_FEATURES = ['curvature_score', 'oppositeness_score', 'density', 'centrality']

BASELINES_DIR = PROJECT_ROOT / 'results' / 'v5_baselines'
PREFIXES_DIR = PROJECT_ROOT / 'results' / 'v5_prefixes'
GEOMETRY_FILE = PROJECT_ROOT / 'data' / 'processed' / 'v5_geometry_features.csv'
OUTPUT_DIR = PREFIXES_DIR / 'analysis'


# ── Data Loading ──────────────────────────────────────────────────────────

def load_baseline_labels():
    """Load baseline judge labels per (model, prompt_id)."""
    labels = {}
    for model in MODELS:
        path = BASELINES_DIR / model / 'no_prefix' / 'judged_answers.jsonl'
        entries = read_jsonl(path)
        labels[model] = {e['id']: int(e['judge_label']) for e in entries}
    return labels


def load_prefix_labels():
    """Load prefix judge labels per (model, prefix, prompt_id)."""
    labels = {}
    for model in MODELS:
        labels[model] = {}
        for prefix in PREFIXES:
            path = PREFIXES_DIR / model / prefix / 'judged_answers.jsonl'
            if path.exists():
                entries = read_jsonl(path)
                labels[model][prefix] = {e['id']: int(e['judge_label']) for e in entries}
    return labels


def load_geometry():
    """Load geometry features, filtering to V5 prompts only."""
    geo = pd.read_csv(GEOMETRY_FILE)
    v5_geo = geo[geo['id'].str.startswith('v5_')].copy()
    print(f"  Loaded {len(v5_geo)} V5 geometry rows (of {len(geo)} total)")
    return v5_geo


# ── Outcome Classification ───────────────────────────────────────────────

def classify_prompts(baseline_labels, prefix_labels, geometry_df):
    """Classify each V5 prompt's outcome per model.

    For each prompt, we look across ALL prefixes to determine:
    - fixed: hallucinated at baseline, at least 1 prefix produced non-hallucination
    - still_broken: hallucinated at baseline, ALL prefixes still hallucinated
    - already_correct: correct at baseline
    - regressed: correct at baseline, at least 1 prefix caused hallucination
    - other: partial/refused at baseline
    """
    records = []

    for model in MODELS:
        bl = baseline_labels[model]
        px = prefix_labels[model]

        prompt_ids = sorted(bl.keys())

        for pid in prompt_ids:
            baseline_label = bl[pid]

            # Collect prefix labels for this prompt
            prefix_results = {}
            for prefix in PREFIXES:
                if prefix in px and pid in px[prefix]:
                    prefix_results[prefix] = px[prefix][pid]

            if not prefix_results:
                continue

            baseline_hall = (baseline_label == 2)
            baseline_correct = (baseline_label == 0)

            any_prefix_not_hall = any(v != 2 for v in prefix_results.values())
            all_prefixes_hall = all(v == 2 for v in prefix_results.values())
            any_prefix_hall = any(v == 2 for v in prefix_results.values())

            if baseline_hall and any_prefix_not_hall:
                outcome = 'fixed'
            elif baseline_hall and all_prefixes_hall:
                outcome = 'still_broken'
            elif baseline_correct and any_prefix_hall:
                outcome = 'regressed'
            elif baseline_correct and not any_prefix_hall:
                outcome = 'already_correct'
            else:
                outcome = 'other'

            # Best prefix label (lowest = best: 0=correct, 1=partial, 2=halluc, 3=refusal)
            # For "best", prefer correct > partial > refusal > hallucination
            prefix_priority = {0: 0, 1: 1, 3: 2, 2: 3}
            best_prefix = min(prefix_results.items(), key=lambda x: prefix_priority.get(x[1], 99))

            records.append({
                'id': pid,
                'model': model,
                'baseline_label': baseline_label,
                'best_prefix': best_prefix[0],
                'best_prefix_label': best_prefix[1],
                'n_prefixes_tested': len(prefix_results),
                'n_prefixes_fixed': sum(1 for v in prefix_results.values() if v != 2),
                'outcome': outcome,
            })

    df = pd.DataFrame(records)

    # Merge geometry features
    geo_cols = ['id', 'category'] + GEO_FEATURES
    df = df.merge(geometry_df[geo_cols], on='id', how='left')

    return df


# ── Statistical Tests ─────────────────────────────────────────────────────

def run_bridge_stats(df):
    """Mann-Whitney U tests comparing geometric features between outcome groups."""
    print(f"\n{'=' * 70}")
    print("  BRIDGE ANALYSIS: Geometric Features by Outcome")
    print(f"{'=' * 70}")

    results = []

    for model in MODELS:
        model_df = df[df['model'] == model]
        model_label = MODEL_LABELS.get(model, model)

        print(f"\n  {model_label}")
        print(f"  {'-' * 50}")

        # Outcome counts
        counts = model_df['outcome'].value_counts()
        for outcome, count in counts.items():
            print(f"    {outcome}: {count}")

        fixed = model_df[model_df['outcome'] == 'fixed']
        broken = model_df[model_df['outcome'] == 'still_broken']
        correct = model_df[model_df['outcome'] == 'already_correct']

        # Test 1: fixed vs already_correct
        for feat in GEO_FEATURES:
            fixed_vals = fixed[feat].dropna()
            correct_vals = correct[feat].dropna()

            if len(fixed_vals) < 5 or len(correct_vals) < 5:
                continue

            u_stat, p_val = stats.mannwhitneyu(fixed_vals, correct_vals, alternative='two-sided')
            n1, n2 = len(fixed_vals), len(correct_vals)
            r = 1 - (2 * u_stat) / (n1 * n2)

            results.append({
                'model': model, 'comparison': 'fixed_vs_correct',
                'feature': feat,
                'group1_mean': fixed_vals.mean(), 'group2_mean': correct_vals.mean(),
                'group1_std': fixed_vals.std(), 'group2_std': correct_vals.std(),
                'u_statistic': u_stat, 'p_value': p_val, 'effect_size_r': r,
                'n_group1': n1, 'n_group2': n2,
            })

            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
            print(f"    {feat}: fixed={fixed_vals.mean():.4f} vs correct={correct_vals.mean():.4f} "
                  f"p={p_val:.2e} r={r:.3f} {sig}")

        # Test 2: fixed vs still_broken
        if len(broken) >= 5:
            print(f"\n    Fixed ({len(fixed)}) vs Still Broken ({len(broken)}):")
            for feat in GEO_FEATURES:
                fixed_vals = fixed[feat].dropna()
                broken_vals = broken[feat].dropna()

                if len(broken_vals) < 3:
                    continue

                u_stat, p_val = stats.mannwhitneyu(broken_vals, fixed_vals, alternative='two-sided')
                n1, n2 = len(broken_vals), len(fixed_vals)
                r = 1 - (2 * u_stat) / (n1 * n2)

                results.append({
                    'model': model, 'comparison': 'broken_vs_fixed',
                    'feature': feat,
                    'group1_mean': broken_vals.mean(), 'group2_mean': fixed_vals.mean(),
                    'group1_std': broken_vals.std(), 'group2_std': fixed_vals.std(),
                    'u_statistic': u_stat, 'p_value': p_val, 'effect_size_r': r,
                    'n_group1': n1, 'n_group2': n2,
                })

                sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
                print(f"      {feat}: broken={broken_vals.mean():.4f} vs fixed={fixed_vals.mean():.4f} "
                      f"p={p_val:.2e} r={r:.3f} {sig}")
        else:
            print(f"\n    Still Broken n={len(broken)} — too few for statistical test")

    return pd.DataFrame(results)


def run_logistic_regression(df):
    """Logistic regression: predict fixed vs still_broken using geometry.

    Uses 5-fold cross-validation (V4 used train-only, which overfits).
    Falls back to train-only if n < 30.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    print(f"\n{'=' * 70}")
    print("  LOGISTIC REGRESSION: Predicting fixability from geometry")
    print(f"{'=' * 70}")

    auc_results = []

    for model in MODELS:
        model_df = df[df['model'] == model]
        model_label = MODEL_LABELS.get(model, model)

        # Only prompts that hallucinated at baseline
        hall_df = model_df[model_df['outcome'].isin(['fixed', 'still_broken'])].copy()
        hall_df['y'] = (hall_df['outcome'] == 'fixed').astype(int)
        hall_df = hall_df.dropna(subset=GEO_FEATURES)

        n_fixed = hall_df['y'].sum()
        n_broken = len(hall_df) - n_fixed

        if len(hall_df) < 10 or hall_df['y'].nunique() < 2:
            print(f"\n  {model_label}: insufficient samples (n={len(hall_df)})")
            auc_results.append({
                'model': model, 'n_total': len(hall_df),
                'n_fixed': n_fixed, 'n_broken': n_broken,
                'auc_cv': None, 'auc_train': None, 'method': 'skipped',
            })
            continue

        X = hall_df[GEO_FEATURES].values
        y = hall_df['y'].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        lr = LogisticRegression(random_state=42, max_iter=1000)

        # Train-only AUC (for V4 comparison)
        lr.fit(X_scaled, y)
        probs_train = lr.predict_proba(X_scaled)[:, 1]
        auc_train = roc_auc_score(y, probs_train)

        # 5-fold CV AUC (honest estimate)
        auc_cv = None
        method = 'train_only'
        if len(hall_df) >= 30 and min(n_fixed, n_broken) >= 5:
            try:
                n_splits = min(5, min(n_fixed, n_broken))
                cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
                probs_cv = cross_val_predict(
                    LogisticRegression(random_state=42, max_iter=1000),
                    X_scaled, y, cv=cv, method='predict_proba'
                )[:, 1]
                auc_cv = roc_auc_score(y, probs_cv)
                method = f'{n_splits}-fold_cv'
            except Exception as e:
                print(f"    CV failed: {e}")

        print(f"\n  {model_label} (n={len(hall_df)}: {n_fixed} fixed, {n_broken} still broken)")
        print(f"    AUC (train-only): {auc_train:.3f}  [comparable to V4]")
        if auc_cv is not None:
            print(f"    AUC ({method}):  {auc_cv:.3f}  [honest estimate]")

        # Feature importance
        print(f"    Feature coefficients (standardized):")
        for feat, coef in zip(GEO_FEATURES, lr.coef_[0]):
            direction = "-> more likely FIXED" if coef > 0 else "-> more likely BROKEN"
            print(f"      {feat:25s}: {coef:+.4f}  {direction}")

        auc_results.append({
            'model': model, 'n_total': len(hall_df),
            'n_fixed': n_fixed, 'n_broken': n_broken,
            'auc_train': round(auc_train, 4),
            'auc_cv': round(auc_cv, 4) if auc_cv else None,
            'method': method,
        })

    return pd.DataFrame(auc_results)


# ── Within-Category Analysis ─────────────────────────────────────────────

def within_category_bridge(df):
    """Test if geometry predicts fixability WITHIN each category.

    This is the non-circular test — same category (same prompt structure),
    geometry varies. Category is no longer a confounder.
    """
    print(f"\n{'=' * 70}")
    print("  WITHIN-CATEGORY BRIDGE ANALYSIS")
    print(f"{'=' * 70}")

    results = []

    for model in MODELS:
        model_df = df[df['model'] == model]
        model_label = MODEL_LABELS.get(model, model)
        print(f"\n  {model_label}")

        categories = sorted(model_df['category'].dropna().unique())
        for cat in categories:
            cat_df = model_df[model_df['category'] == cat]
            fixed = cat_df[cat_df['outcome'] == 'fixed']
            broken = cat_df[cat_df['outcome'] == 'still_broken']

            if len(fixed) < 3 or len(broken) < 3:
                continue

            print(f"\n    {cat}: {len(fixed)} fixed, {len(broken)} still broken")

            for feat in GEO_FEATURES:
                fixed_vals = fixed[feat].dropna()
                broken_vals = broken[feat].dropna()

                if len(fixed_vals) < 3 or len(broken_vals) < 3:
                    continue

                u_stat, p_val = stats.mannwhitneyu(broken_vals, fixed_vals, alternative='two-sided')
                n1, n2 = len(broken_vals), len(fixed_vals)
                r = 1 - (2 * u_stat) / (n1 * n2)

                sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
                print(f"      {feat}: broken={broken_vals.mean():.4f} vs fixed={fixed_vals.mean():.4f} "
                      f"p={p_val:.4f} {sig}")

                results.append({
                    'model': model, 'category': cat, 'feature': feat,
                    'broken_mean': broken_vals.mean(), 'fixed_mean': fixed_vals.mean(),
                    'broken_std': broken_vals.std(), 'fixed_std': fixed_vals.std(),
                    'u_statistic': u_stat, 'p_value': p_val, 'effect_size_r': r,
                    'n_broken': n1, 'n_fixed': n2,
                })

    return pd.DataFrame(results)


# ── Visualization ─────────────────────────────────────────────────────────

def plot_bridge(df, output_dir):
    """Scatter plots of geometric features colored by outcome."""
    for model in MODELS:
        model_df = df[df['model'] == model]
        model_label = MODEL_LABELS.get(model, model)

        plot_df = model_df[model_df['outcome'].isin(
            ['fixed', 'still_broken', 'already_correct']
        )].copy()
        plot_df = plot_df.dropna(subset=['centrality', 'density'])

        colors = {
            'already_correct': '#2ecc71',
            'fixed': '#3498db',
            'still_broken': '#e74c3c',
        }
        labels = {
            'already_correct': 'Already Correct',
            'fixed': 'Fixed by Prefix',
            'still_broken': 'Still Hallucinated',
        }

        fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

        # Plot 1: Centrality vs Density
        ax = axes[0]
        for outcome in ['already_correct', 'fixed', 'still_broken']:
            subset = plot_df[plot_df['outcome'] == outcome]
            ax.scatter(subset['centrality'], subset['density'],
                       c=colors[outcome], label=f"{labels[outcome]} (n={len(subset)})",
                       alpha=0.4, s=30, edgecolors='black', linewidth=0.2)
        ax.set_xlabel('Centrality', fontsize=11)
        ax.set_ylabel('Density', fontsize=11)
        ax.set_title('Centrality vs Density', fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Plot 2: Oppositeness vs Centrality
        ax = axes[1]
        for outcome in ['already_correct', 'fixed', 'still_broken']:
            subset = plot_df[plot_df['outcome'] == outcome]
            ax.scatter(subset['oppositeness_score'], subset['centrality'],
                       c=colors[outcome], label=f"{labels[outcome]}",
                       alpha=0.4, s=30, edgecolors='black', linewidth=0.2)
        ax.set_xlabel('Oppositeness Score', fontsize=11)
        ax.set_ylabel('Centrality', fontsize=11)
        ax.set_title('Oppositeness vs Centrality', fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Plot 3: Box plots
        ax = axes[2]
        melt_df = plot_df.melt(
            id_vars=['id', 'outcome'],
            value_vars=GEO_FEATURES,
            var_name='feature', value_name='value'
        )
        # Normalize per feature
        for feat in GEO_FEATURES:
            mask = melt_df['feature'] == feat
            vals = melt_df.loc[mask, 'value']
            if vals.max() != vals.min():
                melt_df.loc[mask, 'value'] = (vals - vals.min()) / (vals.max() - vals.min())

        sns.boxplot(data=melt_df, x='feature', y='value', hue='outcome',
                    palette=colors, ax=ax, fliersize=2)
        ax.set_xlabel('')
        ax.set_ylabel('Normalized Value', fontsize=11)
        ax.set_title('Feature Distributions', fontsize=12)
        ax.tick_params(axis='x', rotation=20)
        ax.legend(fontsize=7)
        ax.grid(axis='y', alpha=0.3)

        fig.suptitle(f'V5 Bridge Analysis: {model_label}', fontsize=14, fontweight='bold')
        plt.tight_layout()

        fname = f'v5_bridge_{model}.png'
        plt.savefig(output_dir / fname, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved {fname}")


def print_unfixable_profile(df):
    """Characterize the geometric signature of still_broken prompts."""
    print(f"\n{'=' * 70}")
    print("  UNFIXABLE PROMPT PROFILE")
    print(f"{'=' * 70}")

    for model in MODELS:
        model_df = df[df['model'] == model]
        model_label = MODEL_LABELS.get(model, model)
        broken = model_df[model_df['outcome'] == 'still_broken']
        fixed = model_df[model_df['outcome'] == 'fixed']
        correct = model_df[model_df['outcome'] == 'already_correct']

        print(f"\n  {model_label}: {len(broken)} unfixable prompts")

        if len(broken) == 0:
            print("    No unfixable prompts!")
            continue

        # Category distribution
        print(f"    Category distribution:")
        for cat, count in broken['category'].value_counts().items():
            total_cat = len(model_df[model_df['category'] == cat])
            print(f"      {cat}: {count} ({count/total_cat*100:.1f}% of category)")

        # Geometric profile
        print(f"\n    Geometric profile (mean ± std):")
        print(f"    {'Feature':<25s} {'Unfixable':>15s} {'Fixed':>15s} {'Correct':>15s}")
        print(f"    {'-'*25} {'-'*15} {'-'*15} {'-'*15}")
        for feat in GEO_FEATURES:
            b_mean = broken[feat].mean()
            b_std = broken[feat].std()
            f_mean = fixed[feat].mean()
            f_std = fixed[feat].std()
            c_mean = correct[feat].mean()
            c_std = correct[feat].std()
            print(f"    {feat:<25s} {b_mean:>6.4f}±{b_std:>5.4f} "
                  f"{f_mean:>6.4f}±{f_std:>5.4f} {c_mean:>6.4f}±{c_std:>5.4f}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    baseline_labels = load_baseline_labels()
    prefix_labels = load_prefix_labels()
    geometry = load_geometry()

    print("\nClassifying prompt outcomes...")
    df = classify_prompts(baseline_labels, prefix_labels, geometry)
    df.to_csv(OUTPUT_DIR / 'v5_bridge_data.csv', index=False)
    print(f"  {len(df)} prompt-model pairs classified")

    # Summary counts
    for model in MODELS:
        model_df = df[df['model'] == model]
        print(f"  {MODEL_LABELS[model]}: {dict(model_df['outcome'].value_counts())}")

    print("\nRunning statistical tests...")
    stats_df = run_bridge_stats(df)
    stats_df.to_csv(OUTPUT_DIR / 'v5_bridge_stats.csv', index=False)

    print("\nRunning logistic regression...")
    auc_df = run_logistic_regression(df)
    auc_df.to_csv(OUTPUT_DIR / 'v5_bridge_logistic_auc.csv', index=False)

    print("\nWithin-category analysis...")
    within_df = within_category_bridge(df)
    within_df.to_csv(OUTPUT_DIR / 'v5_bridge_within_category.csv', index=False)

    print_unfixable_profile(df)

    print("\nGenerating plots...")
    plot_bridge(df, OUTPUT_DIR)

    print(f"\n{'=' * 70}")
    print(f"  All outputs saved to {OUTPUT_DIR}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
