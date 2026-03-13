"""Step 12A.1-3: Fine-tuning geometric bridge analysis.

Tests whether geometric features predict where fine-tuning helps/hurts,
paralleling the V4 prefix bridge analysis.

12A.1: FT bridge — does geometry predict which hallucinations FT fixes?
12A.2: Borderline within-category — does density predict FT outcomes within
       borderline_obscure_real and borderline_plausible_fake?
12A.3: Regression profile — are broken_by_ft prompts geometrically
       distinguishable from always_correct?

Uses Mann-Whitney U tests + exact permutation tests (for n<10 groups).
No logistic regression (sample sizes too small and imbalanced).

Usage:
    python3 scripts/analyze_ft_bridge.py

Output:
    results/v5_finetuned/analysis/ft_bridge_data.csv
    results/v5_finetuned/analysis/ft_bridge_stats.csv
    results/v5_finetuned/analysis/ft_bridge_{model}.png
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

GEOMETRY_PATH = PROJECT_ROOT / "data" / "processed" / "v3_all_geometry_features.csv"
V3_BASELINE_DIR = PROJECT_ROOT / "results" / "v3" / "multi_model" / "judged_recalibrated"
V5_FINETUNED_DIR = PROJECT_ROOT / "results" / "v5_finetuned"
OUTPUT_DIR = V5_FINETUNED_DIR / "analysis"

# Best config per model (from Step 11)
CONFIGS = {
    "mixtral-8x7b": "C",
    "llama-4-maverick-17b": "A",
}

# Stable features only (oppositeness corr=0.37 — unstable, see 12A.0)
STABLE_FEATURES = ["curvature_score", "density", "centrality"]
ALL_FEATURES = ["curvature_score", "oppositeness_score", "density", "centrality"]

N_PERMUTATIONS = 10000
RANDOM_SEED = 2025


# ── Helpers ────────────────────────────────────────────────────────────────

def deduplicate_results(results):
    """Remove duplicate entries (keep first occurrence per ID)."""
    seen = set()
    deduped = []
    for r in results:
        if r["id"] not in seen:
            deduped.append(r)
            seen.add(r["id"])
    return deduped


def permutation_test(group_a, group_b, n_perms=N_PERMUTATIONS, seed=RANDOM_SEED):
    """Exact permutation test for difference in means.

    Returns two-sided p-value.
    """
    rng = np.random.RandomState(seed)
    observed_diff = abs(group_a.mean() - group_b.mean())
    combined = np.concatenate([group_a, group_b])
    n_a = len(group_a)
    count = 0
    for _ in range(n_perms):
        rng.shuffle(combined)
        perm_diff = abs(combined[:n_a].mean() - combined[n_a:].mean())
        if perm_diff >= observed_diff:
            count += 1
    return count / n_perms


def mann_whitney_with_effect(a, b):
    """Mann-Whitney U test with rank-biserial effect size."""
    u_stat, p_val = stats.mannwhitneyu(a, b, alternative="two-sided")
    n1, n2 = len(a), len(b)
    r = 1 - (2 * u_stat) / (n1 * n2)
    return u_stat, p_val, r


# ── Data Loading ──────────────────────────────────────────────────────────

def load_data():
    """Load geometry, baseline, and FT results. Merge on prompt ID."""
    # Geometry (449 rows)
    geo = pd.read_csv(GEOMETRY_PATH)
    print(f"Geometry: {len(geo)} prompts, {len(geo['category'].unique())} categories")

    records = []

    for model, config in CONFIGS.items():
        # Baseline
        bl_path = V3_BASELINE_DIR / f"judged_answers_{model}.jsonl"
        if not bl_path.exists():
            print(f"  WARNING: {bl_path} not found, skipping {model}")
            continue
        baseline = deduplicate_results(read_jsonl(bl_path))
        bl_map = {r["id"]: r["judge_label"] for r in baseline}

        # Fine-tuned
        ft_path = V5_FINETUNED_DIR / model / f"config{config}" / "judged_answers.jsonl"
        if not ft_path.exists():
            print(f"  WARNING: {ft_path} not found, skipping {model}")
            continue
        ft_results = deduplicate_results(read_jsonl(ft_path))
        ft_map = {r["id"]: r["judge_label"] for r in ft_results}

        # Merge
        for _, row in geo.iterrows():
            pid = row["id"]
            if pid not in bl_map or pid not in ft_map:
                continue

            bl_label = bl_map[pid]
            ft_label = ft_map[pid]

            # Classify outcome
            if bl_label == 2 and ft_label == 0:
                outcome = "fixed_by_ft"
            elif bl_label == 2 and ft_label != 0:
                outcome = "still_broken"
            elif bl_label == 0 and ft_label != 0:
                outcome = "broken_by_ft"
            elif bl_label == 0 and ft_label == 0:
                outcome = "always_correct"
            else:
                outcome = "other"

            records.append({
                "id": pid,
                "model": model,
                "config": config,
                "category": row["category"],
                "baseline_label": bl_label,
                "ft_label": ft_label,
                "outcome": outcome,
                "curvature_score": row["curvature_score"],
                "oppositeness_score": row["oppositeness_score"],
                "density": row["density"],
                "centrality": row["centrality"],
            })

    df = pd.DataFrame(records)
    print(f"\nTotal records: {len(df)}")
    return df


# ── 12A.1: FT Bridge Analysis ─────────────────────────────────────────────

def run_ft_bridge(df):
    """Test whether geometry predicts FT fixability."""
    print(f"\n{'='*70}")
    print(f"  12A.1: FINE-TUNING BRIDGE ANALYSIS")
    print(f"  Does geometry predict which hallucinations FT fixes?")
    print(f"{'='*70}")

    all_stats = []

    for model in CONFIGS:
        mdf = df[df["model"] == model]
        print(f"\n{'─'*50}")
        print(f"  {model} (config{CONFIGS[model]})")
        print(f"{'─'*50}")

        # Outcome counts
        counts = mdf["outcome"].value_counts()
        print(f"\n  Outcome distribution:")
        for outcome in ["always_correct", "fixed_by_ft", "broken_by_ft", "still_broken", "other"]:
            n = counts.get(outcome, 0)
            print(f"    {outcome:<20s}: {n:>4d}")
        print(f"    {'TOTAL':<20s}: {len(mdf):>4d}")

        # Per-category breakdown of outcomes
        print(f"\n  Per-category breakdown:")
        print(f"    {'Category':<30s} {'correct':>8s} {'fixed':>8s} {'broken':>8s} {'still_br':>8s} {'other':>8s}")
        print(f"    {'-'*30} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        for cat in sorted(mdf["category"].unique()):
            cdf = mdf[mdf["category"] == cat]
            cc = cdf["outcome"].value_counts()
            print(f"    {cat:<30s} "
                  f"{cc.get('always_correct', 0):>8d} "
                  f"{cc.get('fixed_by_ft', 0):>8d} "
                  f"{cc.get('broken_by_ft', 0):>8d} "
                  f"{cc.get('still_broken', 0):>8d} "
                  f"{cc.get('other', 0):>8d}")

        # ── Test 1: fixed_by_ft vs still_broken ──
        fixed = mdf[mdf["outcome"] == "fixed_by_ft"]
        broken = mdf[mdf["outcome"] == "still_broken"]

        print(f"\n  --- Fixed ({len(fixed)}) vs Still Broken ({len(broken)}) ---")
        if len(broken) < 3:
            print(f"    Still Broken n={len(broken)} — too few for any test. Descriptive only.")
            for feat in STABLE_FEATURES:
                f_vals = fixed[feat].dropna()
                b_vals = broken[feat].dropna()
                if len(b_vals) > 0:
                    print(f"    {feat}: fixed_mean={f_vals.mean():.4f}, still_broken_mean={b_vals.mean():.4f}")
        else:
            for feat in STABLE_FEATURES:
                f_vals = fixed[feat].dropna().values
                b_vals = broken[feat].dropna().values
                if len(f_vals) < 3 or len(b_vals) < 3:
                    continue

                u, p_mw, r = mann_whitney_with_effect(f_vals, b_vals)
                p_perm = permutation_test(f_vals, b_vals)

                direction = "fixed higher" if f_vals.mean() > b_vals.mean() else "still_broken higher"
                sig = "***" if p_mw < 0.001 else "**" if p_mw < 0.01 else "*" if p_mw < 0.05 else "ns"

                print(f"    {feat}:")
                print(f"      fixed={f_vals.mean():.4f} vs broken={b_vals.mean():.4f} ({direction})")
                print(f"      MW p={p_mw:.4f} {sig} | perm p={p_perm:.4f} | r={r:.3f}")

                all_stats.append({
                    "analysis": "12A.1", "model": model, "comparison": "fixed_vs_still_broken",
                    "feature": feat, "group_a": "fixed_by_ft", "group_b": "still_broken",
                    "mean_a": f_vals.mean(), "mean_b": b_vals.mean(),
                    "n_a": len(f_vals), "n_b": len(b_vals),
                    "u_stat": u, "p_mw": p_mw, "p_perm": p_perm, "effect_r": r,
                })

        # ── Test 2: broken_by_ft vs always_correct ──
        broken_ft = mdf[mdf["outcome"] == "broken_by_ft"]
        correct = mdf[mdf["outcome"] == "always_correct"]

        print(f"\n  --- Broken by FT ({len(broken_ft)}) vs Always Correct ({len(correct)}) ---")
        for feat in STABLE_FEATURES:
            b_vals = broken_ft[feat].dropna().values
            c_vals = correct[feat].dropna().values
            if len(b_vals) < 3:
                print(f"    {feat}: n={len(b_vals)} — too few")
                continue

            u, p_mw, r = mann_whitney_with_effect(b_vals, c_vals)
            p_perm = permutation_test(b_vals, c_vals) if len(b_vals) < 10 else None

            direction = "broken higher" if b_vals.mean() > c_vals.mean() else "correct higher"
            sig = "***" if p_mw < 0.001 else "**" if p_mw < 0.01 else "*" if p_mw < 0.05 else "ns"

            perm_str = f" | perm p={p_perm:.4f}" if p_perm is not None else ""
            print(f"    {feat}:")
            print(f"      broken={b_vals.mean():.4f} vs correct={c_vals.mean():.4f} ({direction})")
            print(f"      MW p={p_mw:.4f} {sig}{perm_str} | r={r:.3f}")

            all_stats.append({
                "analysis": "12A.1", "model": model, "comparison": "broken_vs_correct",
                "feature": feat, "group_a": "broken_by_ft", "group_b": "always_correct",
                "mean_a": b_vals.mean(), "mean_b": c_vals.mean(),
                "n_a": len(b_vals), "n_b": len(c_vals),
                "u_stat": u, "p_mw": p_mw,
                "p_perm": p_perm if p_perm is not None else np.nan,
                "effect_r": r,
            })

        # ── Oppositeness (reported with caveat) ──
        print(f"\n  --- Oppositeness (CAVEAT: corr=0.37 with original, unstable feature) ---")
        for comparison_name, group_a, group_b, label_a, label_b in [
            ("fixed_vs_still_broken", fixed, mdf[mdf["outcome"] == "still_broken"], "fixed", "still_broken"),
            ("broken_vs_correct", broken_ft, correct, "broken_by_ft", "always_correct"),
        ]:
            a_vals = group_a["oppositeness_score"].dropna().values
            b_vals = group_b["oppositeness_score"].dropna().values
            if len(a_vals) < 3 or len(b_vals) < 3:
                print(f"    {comparison_name}: insufficient n")
                continue
            u, p_mw, r = mann_whitney_with_effect(a_vals, b_vals)
            print(f"    {comparison_name}: {label_a}={a_vals.mean():.4f} vs {label_b}={b_vals.mean():.4f}, MW p={p_mw:.4f}, r={r:.3f}")

            all_stats.append({
                "analysis": "12A.1_unstable", "model": model, "comparison": comparison_name,
                "feature": "oppositeness_score", "group_a": label_a, "group_b": label_b,
                "mean_a": a_vals.mean(), "mean_b": b_vals.mean(),
                "n_a": len(a_vals), "n_b": len(b_vals),
                "u_stat": u, "p_mw": p_mw, "p_perm": np.nan, "effect_r": r,
            })

    return all_stats


# ── 12A.2: Borderline Within-Category ─────────────────────────────────────

def run_borderline_within_category(df):
    """Within-category density prediction for borderline categories."""
    print(f"\n{'='*70}")
    print(f"  12A.2: BORDERLINE WITHIN-CATEGORY ANALYSIS")
    print(f"  Does density predict FT outcomes WITHIN each borderline category?")
    print(f"{'='*70}")

    all_stats = []

    for model in CONFIGS:
        mdf = df[df["model"] == model]
        print(f"\n{'─'*50}")
        print(f"  {model}")
        print(f"{'─'*50}")

        for cat in ["borderline_obscure_real", "borderline_plausible_fake"]:
            cdf = mdf[mdf["category"] == cat]
            print(f"\n  {cat} (n={len(cdf)}):")

            # Within this category: FT correct vs FT not-correct
            correct = cdf[cdf["ft_label"] == 0]
            wrong = cdf[cdf["ft_label"] != 0]
            print(f"    FT correct: {len(correct)}, FT wrong: {len(wrong)}")

            if len(wrong) < 2:
                print(f"    Too few FT-wrong for any test")
                continue

            for feat in STABLE_FEATURES:
                c_vals = correct[feat].dropna().values
                w_vals = wrong[feat].dropna().values
                if len(c_vals) < 2 or len(w_vals) < 2:
                    continue

                p_perm = permutation_test(c_vals, w_vals)

                # Mann-Whitney only if both groups have n>=3
                if len(c_vals) >= 3 and len(w_vals) >= 3:
                    u, p_mw, r = mann_whitney_with_effect(c_vals, w_vals)
                else:
                    u, p_mw, r = np.nan, np.nan, np.nan

                direction = "correct higher" if c_vals.mean() > w_vals.mean() else "wrong higher"
                print(f"    {feat}: correct={c_vals.mean():.4f} vs wrong={w_vals.mean():.4f} ({direction})")
                mw_str = f"MW p={p_mw:.4f}" if not np.isnan(p_mw) else "MW n/a"
                print(f"      {mw_str} | perm p={p_perm:.4f} | r={r:.3f}" if not np.isnan(r) else f"      {mw_str} | perm p={p_perm:.4f}")

                all_stats.append({
                    "analysis": "12A.2", "model": model,
                    "comparison": f"within_{cat}",
                    "feature": feat, "group_a": "ft_correct", "group_b": "ft_wrong",
                    "mean_a": c_vals.mean(), "mean_b": w_vals.mean(),
                    "n_a": len(c_vals), "n_b": len(w_vals),
                    "u_stat": u, "p_mw": p_mw, "p_perm": p_perm,
                    "effect_r": r,
                })

        # Cross-category comparison (descriptive only — flagged as confounded)
        print(f"\n  Cross-category comparison (DESCRIPTIVE — confounded by category structure):")
        for cat in ["borderline_obscure_real", "borderline_plausible_fake", "borderline_edge_factual"]:
            cdf = mdf[mdf["category"] == cat]
            if len(cdf) == 0:
                continue
            print(f"    {cat:<30s} density={cdf['density'].mean():.4f}  "
                  f"centrality={cdf['centrality'].mean():.4f}  "
                  f"curvature={cdf['curvature_score'].mean():.4f}")

    return all_stats


# ── 12A.3: Regression Geometric Profile ───────────────────────────────────

def run_regression_profile(df):
    """Are broken_by_ft prompts geometrically distinguishable?"""
    print(f"\n{'='*70}")
    print(f"  12A.3: REGRESSION GEOMETRIC PROFILE")
    print(f"  Are broken_by_ft prompts geometrically distinct from always_correct?")
    print(f"{'='*70}")

    all_stats = []

    for model in CONFIGS:
        mdf = df[df["model"] == model]
        broken = mdf[mdf["outcome"] == "broken_by_ft"]
        correct = mdf[mdf["outcome"] == "always_correct"]

        print(f"\n{'─'*50}")
        print(f"  {model}: {len(broken)} broken_by_ft, {len(correct)} always_correct")
        print(f"{'─'*50}")

        if len(broken) < 3:
            print(f"  Too few broken_by_ft for analysis")
            continue

        # Category breakdown of regressions
        print(f"\n  Regression category breakdown:")
        for cat, n in broken["category"].value_counts().items():
            print(f"    {cat}: {n}")

        # What did they become? (label distribution)
        print(f"\n  Regression label distribution (what FT produced):")
        for label, n in broken["ft_label"].value_counts().items():
            label_name = {0: "correct", 1: "partial", 2: "hallucinated", 3: "refused"}.get(label, f"unknown({label})")
            print(f"    {label_name}: {n}")

        # Feature comparison
        print(f"\n  Feature comparison (broken_by_ft vs always_correct):")
        for feat in STABLE_FEATURES:
            b_vals = broken[feat].dropna().values
            c_vals = correct[feat].dropna().values

            u, p_mw, r = mann_whitney_with_effect(b_vals, c_vals)
            p_perm = permutation_test(b_vals, c_vals) if len(b_vals) < 15 else None

            direction = "broken higher" if b_vals.mean() > c_vals.mean() else "correct higher"
            sig = "***" if p_mw < 0.001 else "**" if p_mw < 0.01 else "*" if p_mw < 0.05 else "ns"

            perm_str = f" | perm p={p_perm:.4f}" if p_perm is not None else ""
            print(f"    {feat}:")
            print(f"      broken={b_vals.mean():.4f} (std={b_vals.std():.4f}) vs "
                  f"correct={c_vals.mean():.4f} (std={c_vals.std():.4f})")
            print(f"      MW p={p_mw:.4f} {sig}{perm_str} | r={r:.3f} ({direction})")

            all_stats.append({
                "analysis": "12A.3", "model": model,
                "comparison": "broken_vs_always_correct",
                "feature": feat, "group_a": "broken_by_ft", "group_b": "always_correct",
                "mean_a": b_vals.mean(), "mean_b": c_vals.mean(),
                "n_a": len(b_vals), "n_b": len(c_vals),
                "u_stat": u, "p_mw": p_mw,
                "p_perm": p_perm if p_perm is not None else np.nan,
                "effect_r": r,
            })

    return all_stats


# ── Visualization ─────────────────────────────────────────────────────────

def plot_ft_bridge(df, output_dir):
    """Scatter + box plots for FT bridge analysis."""
    colors = {
        "always_correct": "#2ecc71",
        "fixed_by_ft": "#3498db",
        "still_broken": "#e74c3c",
        "broken_by_ft": "#e67e22",
        "other": "#95a5a6",
    }
    labels = {
        "always_correct": "Always Correct",
        "fixed_by_ft": "Fixed by FT",
        "still_broken": "Still Broken",
        "broken_by_ft": "Broken by FT",
        "other": "Other",
    }

    for model in CONFIGS:
        mdf = df[df["model"] == model].copy()
        plot_df = mdf[mdf["outcome"].isin(["always_correct", "fixed_by_ft", "still_broken", "broken_by_ft"])]

        fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

        # Plot 1: Density vs Centrality scatter
        ax = axes[0]
        for outcome in ["always_correct", "fixed_by_ft", "broken_by_ft", "still_broken"]:
            sub = plot_df[plot_df["outcome"] == outcome]
            if len(sub) == 0:
                continue
            ax.scatter(sub["density"], sub["centrality"],
                       c=colors[outcome], label=f"{labels[outcome]} ({len(sub)})",
                       alpha=0.6, s=50, edgecolors="black", linewidth=0.3,
                       zorder=3 if outcome in ("still_broken", "broken_by_ft") else 1)
        ax.set_xlabel("Density", fontsize=11)
        ax.set_ylabel("Centrality", fontsize=11)
        ax.set_title("Density vs Centrality by FT Outcome", fontsize=12)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # Plot 2: Box plots of stable features by outcome
        ax = axes[1]
        melt_df = plot_df.melt(
            id_vars=["id", "outcome"],
            value_vars=STABLE_FEATURES,
            var_name="feature", value_name="value",
        )
        # Normalize
        for feat in STABLE_FEATURES:
            mask = melt_df["feature"] == feat
            vals = melt_df.loc[mask, "value"]
            if vals.max() != vals.min():
                melt_df.loc[mask, "value"] = (vals - vals.min()) / (vals.max() - vals.min())

        order = ["always_correct", "fixed_by_ft", "broken_by_ft", "still_broken"]
        order = [o for o in order if o in melt_df["outcome"].unique()]
        sns.boxplot(data=melt_df, x="feature", y="value", hue="outcome",
                    hue_order=order, palette=colors, ax=ax, fliersize=2)
        ax.set_xlabel("")
        ax.set_ylabel("Normalized Value", fontsize=11)
        ax.set_title("Feature Distributions by FT Outcome", fontsize=12)
        ax.tick_params(axis="x", rotation=15)
        ax.legend(fontsize=7)
        ax.grid(axis="y", alpha=0.3)

        # Plot 3: Category breakdown of outcomes (stacked bar)
        ax = axes[2]
        cats = sorted(mdf["category"].unique())
        outcome_order = ["always_correct", "fixed_by_ft", "broken_by_ft", "still_broken", "other"]
        cat_data = {}
        for cat in cats:
            cdf = mdf[mdf["category"] == cat]
            cat_data[cat] = {o: len(cdf[cdf["outcome"] == o]) for o in outcome_order}

        bottoms = np.zeros(len(cats))
        for outcome in outcome_order:
            vals = [cat_data[cat].get(outcome, 0) for cat in cats]
            ax.barh(range(len(cats)), vals, left=bottoms,
                    color=colors.get(outcome, "#ccc"),
                    label=labels.get(outcome, outcome))
            bottoms += vals
        ax.set_yticks(range(len(cats)))
        ax.set_yticklabels([c.replace("borderline_", "bl_") for c in cats], fontsize=9)
        ax.set_xlabel("Count", fontsize=11)
        ax.set_title("Outcomes by Category", fontsize=12)
        ax.legend(fontsize=7, loc="lower right")

        model_label = "Mixtral 8x7B" if "mixtral" in model else "Llama 4 Maverick"
        fig.suptitle(f"Fine-Tuning Bridge Analysis: {model_label} (config{CONFIGS[model]})",
                     fontsize=14, fontweight="bold")
        plt.tight_layout()

        fname = f"ft_bridge_{model}.png"
        plt.savefig(output_dir / fname, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"\n  Saved {fname}")


# ── Multiple Comparisons Correction ───────────────────────────────────────

def apply_corrections(stats_df):
    """Apply Bonferroni and BH FDR corrections."""
    if len(stats_df) == 0:
        return stats_df

    # Only correct stable features (exclude 12A.1_unstable)
    stable_mask = stats_df["analysis"] != "12A.1_unstable"
    p_vals = stats_df.loc[stable_mask, "p_mw"].dropna()

    if len(p_vals) == 0:
        return stats_df

    n_tests = len(p_vals)
    stats_df.loc[stable_mask, "p_bonferroni"] = np.minimum(
        stats_df.loc[stable_mask, "p_mw"] * n_tests, 1.0
    )

    # BH FDR
    sorted_idx = p_vals.sort_values().index
    ranks = np.arange(1, len(sorted_idx) + 1)
    fdr_vals = p_vals.loc[sorted_idx].values * n_tests / ranks
    # Enforce monotonicity
    for i in range(len(fdr_vals) - 2, -1, -1):
        fdr_vals[i] = min(fdr_vals[i], fdr_vals[i + 1])
    fdr_vals = np.minimum(fdr_vals, 1.0)
    for idx, fdr in zip(sorted_idx, fdr_vals):
        stats_df.loc[idx, "p_bh_fdr"] = fdr

    return stats_df


# ── V4 Bridge Comparison ─────────────────────────────────────────────────

def compare_to_v4_bridge():
    """Load V4 bridge stats and print side-by-side comparison."""
    v4_stats_path = PROJECT_ROOT / "results" / "v4_prefix_experiment" / "analysis" / "geometry_bridge_stats.csv"
    if not v4_stats_path.exists():
        print("\n  V4 bridge stats not found — skipping comparison")
        return

    print(f"\n{'='*70}")
    print(f"  COMPARISON: V4 Prefix Bridge vs 12A.1 FT Bridge")
    print(f"  (Direction consistency check — same geometry, different intervention)")
    print(f"{'='*70}")

    v4 = pd.read_csv(v4_stats_path)
    print(f"\n  V4 prefix bridge results (fixed vs already_correct):")
    print(f"  {'Model':<25s} {'Feature':<20s} {'Fixed Mean':>10s} {'Correct Mean':>12s} {'p-value':>10s} {'r':>8s}")
    print(f"  {'-'*25} {'-'*20} {'-'*10} {'-'*12} {'-'*10} {'-'*8}")
    for _, row in v4.iterrows():
        print(f"  {row['model']:<25s} {row['feature']:<20s} "
              f"{row['fixed_mean']:>10.4f} {row['correct_mean']:>12.4f} "
              f"{row['p_value']:>10.6f} {row['effect_size_r']:>8.4f}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load and merge data
    df = load_data()

    # Save tagged data
    df.to_csv(OUTPUT_DIR / "ft_bridge_data.csv", index=False)
    print(f"Saved bridge data to {OUTPUT_DIR / 'ft_bridge_data.csv'}")

    # Run analyses
    stats_1 = run_ft_bridge(df)
    stats_2 = run_borderline_within_category(df)
    stats_3 = run_regression_profile(df)

    # Combine and correct
    all_stats = stats_1 + stats_2 + stats_3
    if all_stats:
        stats_df = pd.DataFrame(all_stats)
        stats_df = apply_corrections(stats_df)
        stats_df.to_csv(OUTPUT_DIR / "ft_bridge_stats.csv", index=False)
        print(f"\nSaved {len(stats_df)} statistical tests to {OUTPUT_DIR / 'ft_bridge_stats.csv'}")

        # Summary of corrections
        stable = stats_df[stats_df["analysis"] != "12A.1_unstable"]
        n_tests = len(stable)
        n_sig_raw = (stable["p_mw"] < 0.05).sum()
        n_sig_bonf = (stable["p_bonferroni"] < 0.05).sum() if "p_bonferroni" in stable.columns else 0
        n_sig_fdr = (stable["p_bh_fdr"] < 0.05).sum() if "p_bh_fdr" in stable.columns else 0
        print(f"\n  Multiple comparisons ({n_tests} tests on stable features):")
        print(f"    Raw p<0.05:        {n_sig_raw}")
        print(f"    Bonferroni p<0.05: {n_sig_bonf}")
        print(f"    BH FDR q<0.05:     {n_sig_fdr}")

    # V4 comparison
    compare_to_v4_bridge()

    # Plots
    plot_ft_bridge(df, OUTPUT_DIR)

    print(f"\n{'='*70}")
    print(f"  DONE — Step 12A.1-3 complete")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
