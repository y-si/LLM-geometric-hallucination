"""V5 Bridge Analysis: Do geometric features predict hallucination?

Tests whether the 5 geometric features computed on the combined corpus
(2,879 prompts) predict which V5 prompts (2,430) hallucinate at baseline
(no prefix). This is the V5 validation of the V3 finding.

Two levels of analysis:
  1. BETWEEN-CATEGORY: Do features differ across categories?
     (Potentially circular — borderline categories are *defined* as unusual)
  2. WITHIN-CATEGORY: Do features predict hallucination *within* a category?
     (The real test — controls for category-level confounds)

Also includes:
  - Logistic regression with AUC for overall and within-category prediction
  - Cross-validated AUC to avoid overfitting on the training set
  - Feature importance ranking
  - Comparison to V3 bridge analysis results

Usage:
    python3 scripts/analyze_v5_geometry_prediction.py

Output:
    results/v5_baselines/analysis/
    ├── v5_geometry_prediction_overall.csv
    ├── v5_geometry_prediction_within_category.csv
    ├── v5_geometry_vs_hallucination_{model}.png
    └── v5_within_category_{model}.png
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_score, StratifiedKFold

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

GEO_FEATURES = ["local_id", "curvature_score", "oppositeness_score", "density", "centrality"]
TARGET_MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]

GEOMETRY_PATH = PROJECT_ROOT / "data" / "processed" / "v5_geometry_features.csv"
BASELINES_DIR = PROJECT_ROOT / "results" / "v5_baselines"
OUTPUT_DIR = BASELINES_DIR / "analysis"


# ── Data loading ───────────────────────────────────────────────────────────

def load_data(model_key: str) -> pd.DataFrame:
    """Load and merge geometry features with baseline judging results."""
    geo = pd.read_csv(GEOMETRY_PATH)
    judged_path = BASELINES_DIR / model_key / "no_prefix" / "judged_answers.jsonl"
    judged = pd.DataFrame(read_jsonl(judged_path))

    # Merge on prompt ID
    merged = judged.merge(geo, on="id", how="inner", suffixes=("_judge", "_geo"))

    # Use geometry category (authoritative)
    if "category_geo" in merged.columns:
        merged["category"] = merged["category_geo"]
        merged.drop(columns=["category_judge", "category_geo"], inplace=True)

    # Binary hallucination label
    merged["hallucinated"] = (merged["judge_label"] == 2).astype(int)

    print(f"  {model_key}: {len(merged)} prompts merged "
          f"({merged['hallucinated'].sum()} hallucinations, "
          f"{merged['hallucinated'].mean()*100:.1f}%)")

    return merged


# ── Between-category analysis ──────────────────────────────────────────────

def between_category_analysis(df: pd.DataFrame, model_key: str) -> pd.DataFrame:
    """Test whether geometric features differ between hallucinated and correct prompts."""
    print(f"\n{'=' * 70}")
    print(f"  BETWEEN-CATEGORY ANALYSIS — {model_key}")
    print(f"{'=' * 70}")

    hall = df[df["hallucinated"] == 1]
    correct = df[df["judge_label"] == 0]

    print(f"  Hallucinated: {len(hall)}, Correct: {len(correct)}")

    results = []
    print(f"\n  {'Feature':<25s} {'Hall Mean':>10s} {'Corr Mean':>10s} {'Diff':>8s} {'p-value':>10s} {'Effect r':>10s}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*8} {'-'*10} {'-'*10}")

    for feat in GEO_FEATURES:
        h_vals = hall[feat].dropna()
        c_vals = correct[feat].dropna()

        if len(h_vals) < 5 or len(c_vals) < 5:
            continue

        u_stat, p_val = stats.mannwhitneyu(h_vals, c_vals, alternative="two-sided")
        n1, n2 = len(h_vals), len(c_vals)
        r = 1 - (2 * u_stat) / (n1 * n2)

        print(f"  {feat:<25s} {h_vals.mean():>10.4f} {c_vals.mean():>10.4f} "
              f"{h_vals.mean() - c_vals.mean():>+8.4f} {p_val:>10.6f} {r:>+10.4f}")

        results.append({
            "model": model_key,
            "analysis": "between_category",
            "feature": feat,
            "hall_mean": h_vals.mean(),
            "correct_mean": c_vals.mean(),
            "diff": h_vals.mean() - c_vals.mean(),
            "p_value": p_val,
            "effect_size_r": r,
            "n_hall": len(h_vals),
            "n_correct": len(c_vals),
        })

    return pd.DataFrame(results)


# ── Within-category analysis ──────────────────────────────────────────────

def within_category_analysis(df: pd.DataFrame, model_key: str) -> pd.DataFrame:
    """Test whether geometric features predict hallucination WITHIN each category.

    This is the key test. Between-category differences could be circular
    (borderline categories are defined as unusual → of course they have unusual
    geometry). Within-category prediction controls for this confound.
    """
    print(f"\n{'=' * 70}")
    print(f"  WITHIN-CATEGORY ANALYSIS — {model_key}")
    print(f"  (Controls for category-level confounds)")
    print(f"{'=' * 70}")

    results = []
    categories = sorted(df["category"].unique())

    for cat in categories:
        cat_df = df[df["category"] == cat]
        n_hall = cat_df["hallucinated"].sum()
        n_correct = (cat_df["judge_label"] == 0).sum()
        n_total = len(cat_df)

        print(f"\n  {cat} (n={n_total}, {n_hall} halluc, {n_hall/n_total*100:.1f}%)")

        if n_hall < 5 or n_correct < 5:
            print(f"    Skipped: too few samples (need >= 5 in each group)")
            continue

        hall = cat_df[cat_df["hallucinated"] == 1]
        correct = cat_df[cat_df["judge_label"] == 0]

        for feat in GEO_FEATURES:
            h_vals = hall[feat].dropna()
            c_vals = correct[feat].dropna()

            if len(h_vals) < 3 or len(c_vals) < 3:
                continue

            u_stat, p_val = stats.mannwhitneyu(h_vals, c_vals, alternative="two-sided")
            n1, n2 = len(h_vals), len(c_vals)
            r = 1 - (2 * u_stat) / (n1 * n2)

            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else ""
            print(f"    {feat:<25s} hall={h_vals.mean():.4f} corr={c_vals.mean():.4f} "
                  f"p={p_val:.4f} r={r:+.3f} {sig}")

            results.append({
                "model": model_key,
                "category": cat,
                "feature": feat,
                "hall_mean": h_vals.mean(),
                "correct_mean": c_vals.mean(),
                "diff": h_vals.mean() - c_vals.mean(),
                "p_value": p_val,
                "effect_size_r": r,
                "n_hall": len(h_vals),
                "n_correct": len(c_vals),
            })

        # Within-category logistic regression
        cat_clean = cat_df.dropna(subset=GEO_FEATURES)
        if cat_clean["hallucinated"].sum() >= 10 and (1 - cat_clean["hallucinated"]).sum() >= 10:
            X = cat_clean[GEO_FEATURES].values
            y = cat_clean["hallucinated"].values

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            lr = LogisticRegression(random_state=42, max_iter=1000)

            # Cross-validated AUC
            try:
                cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
                cv_aucs = cross_val_score(lr, X_scaled, y, cv=cv, scoring="roc_auc")
                print(f"    Logistic regression CV AUC: {cv_aucs.mean():.3f} (+/- {cv_aucs.std():.3f})")

                results.append({
                    "model": model_key,
                    "category": cat,
                    "feature": "LOGISTIC_CV_AUC",
                    "hall_mean": cv_aucs.mean(),
                    "correct_mean": cv_aucs.std(),
                    "diff": 0,
                    "p_value": 0,
                    "effect_size_r": 0,
                    "n_hall": int(y.sum()),
                    "n_correct": int((1 - y).sum()),
                })
            except Exception as e:
                print(f"    CV failed: {e}")

    return pd.DataFrame(results)


# ── Overall logistic regression ────────────────────────────────────────────

def overall_logistic_regression(df: pd.DataFrame, model_key: str):
    """Overall logistic regression: geometry → hallucination."""
    print(f"\n{'=' * 70}")
    print(f"  LOGISTIC REGRESSION — {model_key}")
    print(f"{'=' * 70}")

    clean = df.dropna(subset=GEO_FEATURES)
    X = clean[GEO_FEATURES].values
    y = clean["hallucinated"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    lr = LogisticRegression(random_state=42, max_iter=1000)

    # Train AUC (for comparison with V3's reported AUC=0.86)
    lr.fit(X_scaled, y)
    probs = lr.predict_proba(X_scaled)[:, 1]
    train_auc = roc_auc_score(y, probs)

    # Cross-validated AUC (the honest number)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_aucs = cross_val_score(lr, X_scaled, y, cv=cv, scoring="roc_auc")

    print(f"\n  n={len(clean)}, {y.sum()} hallucinations ({y.mean()*100:.1f}%)")
    print(f"  Train AUC:      {train_auc:.3f} (for comparison with V3's AUC=0.86)")
    print(f"  5-fold CV AUC:  {cv_aucs.mean():.3f} (+/- {cv_aucs.std():.3f})")
    print(f"\n  Feature coefficients (standardized):")
    for feat, coef in zip(GEO_FEATURES, lr.coef_[0]):
        direction = "→ more hallucination" if coef > 0 else "→ less hallucination"
        print(f"    {feat:<25s}: {coef:+.4f}  {direction}")

    # Category-controlled: add category dummies
    print(f"\n  --- With category controls ---")
    cat_dummies = pd.get_dummies(clean["category"], prefix="cat", drop_first=True)
    X_with_cat = np.hstack([X_scaled, cat_dummies.values])

    lr_cat = LogisticRegression(random_state=42, max_iter=1000)
    cv_aucs_cat = cross_val_score(lr_cat, X_with_cat, y, cv=cv, scoring="roc_auc")
    print(f"  CV AUC (geo only):         {cv_aucs.mean():.3f}")
    print(f"  CV AUC (geo + category):   {cv_aucs_cat.mean():.3f}")

    # Category-only baseline
    lr_catonly = LogisticRegression(random_state=42, max_iter=1000)
    cv_aucs_catonly = cross_val_score(lr_catonly, cat_dummies.values, y, cv=cv, scoring="roc_auc")
    print(f"  CV AUC (category only):    {cv_aucs_catonly.mean():.3f}")
    print(f"\n  Geo adds {cv_aucs_cat.mean() - cv_aucs_catonly.mean():+.3f} AUC over category-only baseline")


# ── Plots ──────────────────────────────────────────────────────────────────

def plot_overall(df: pd.DataFrame, model_key: str, output_dir: Path):
    """Scatter plots: geometry vs hallucination for one model."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    pairs = [
        ("centrality", "density"),
        ("centrality", "curvature_score"),
        ("density", "oppositeness_score"),
        ("curvature_score", "oppositeness_score"),
    ]

    colors = {0: "#2ecc71", 1: "#95a5a6", 2: "#e74c3c", 3: "#3498db"}
    labels = {0: "Correct", 1: "Partial", 2: "Hallucination", 3: "Refusal"}

    for ax, (xfeat, yfeat) in zip(axes.flat, pairs):
        for label in [0, 2]:  # Only plot correct and hallucinated
            subset = df[df["judge_label"] == label]
            ax.scatter(
                subset[xfeat], subset[yfeat],
                c=colors[label], label=labels[label],
                alpha=0.3, s=20, edgecolors="none",
            )
        ax.set_xlabel(xfeat, fontsize=10)
        ax.set_ylabel(yfeat, fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    model_label = "Mixtral 8x7B" if "mixtral" in model_key else "Llama 4 Maverick"
    fig.suptitle(f"V5 Geometry vs Hallucination: {model_label} (n={len(df)})",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = f"v5_geometry_vs_hallucination_{model_key}.png"
    plt.savefig(output_dir / fname, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Saved {fname}")


def plot_within_category(df: pd.DataFrame, model_key: str, output_dir: Path):
    """Box plots of key features within each category, split by hallucination."""
    categories = sorted(df["category"].unique())
    key_features = ["density", "centrality", "curvature_score"]

    fig, axes = plt.subplots(len(key_features), 1, figsize=(14, 4 * len(key_features)))

    for ax, feat in zip(axes, key_features):
        # Build plot data: within each category, compare hallucinated vs correct
        plot_data = df[df["judge_label"].isin([0, 2])].copy()
        plot_data["label"] = plot_data["judge_label"].map({0: "Correct", 2: "Hallucinated"})

        sns.boxplot(
            data=plot_data, x="category", y=feat, hue="label",
            palette={"Correct": "#2ecc71", "Hallucinated": "#e74c3c"},
            ax=ax, fliersize=2,
        )
        ax.set_xlabel("")
        ax.set_ylabel(feat, fontsize=11)
        ax.tick_params(axis="x", rotation=30)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    model_label = "Mixtral 8x7B" if "mixtral" in model_key else "Llama 4 Maverick"
    fig.suptitle(f"Within-Category Geometry: {model_label}", fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = f"v5_within_category_{model_key}.png"
    plt.savefig(output_dir / fname, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Saved {fname}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  V5 GEOMETRY → HALLUCINATION PREDICTION")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_between = []
    all_within = []

    for model_key in TARGET_MODELS:
        df = load_data(model_key)

        # Between-category
        between = between_category_analysis(df, model_key)
        all_between.append(between)

        # Within-category (the real test)
        within = within_category_analysis(df, model_key)
        all_within.append(within)

        # Overall logistic regression
        overall_logistic_regression(df, model_key)

        # Plots
        plot_overall(df, model_key, OUTPUT_DIR)
        plot_within_category(df, model_key, OUTPUT_DIR)

    # Save results
    if all_between:
        pd.concat(all_between).to_csv(
            OUTPUT_DIR / "v5_geometry_prediction_overall.csv", index=False
        )
    if all_within:
        pd.concat(all_within).to_csv(
            OUTPUT_DIR / "v5_geometry_prediction_within_category.csv", index=False
        )

    print(f"\n{'=' * 70}")
    print(f"  DONE — results saved to {OUTPUT_DIR}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
