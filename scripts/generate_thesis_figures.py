"""Step 12B: Generate publication-quality thesis figures.

Produces figures organized by thesis chapter. Reads existing analysis
data (CSVs, JSONs) and generates matplotlib/seaborn plots.

Existing figures (not regenerated):
  - v5_judge_agreement.png (Ch 4)
  - v5_within_category_*.png (Ch 5)
  - v5_geometry_vs_hallucination_*.png (Ch 5)
  - v5_category_heatmap_*.png (Ch 6)
  - v5_tradeoff_curve.png (Ch 6)
  - v5_refusal_rates.png (Ch 6)
  - v5_bridge_*.png (Ch 7)
  - ft_bridge_*.png (Ch 7)

New figures generated:
  Ch 5: AUC decomposition (within-category logistic AUC by category)
  Ch 6: V4 vs V5 scale comparison
  Ch 7: Baseline vs prefix vs FT comparison bar chart
  Ch 7: Per-category FT heatmap
  Ch 7: Hyperparameter sensitivity (config comparison)
  Ch 7: Regression error type breakdown

Usage:
    python3 scripts/generate_thesis_figures.py

Output:
    thesis/figures/*.png (all new figures)
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Output ────────────────────────────────────────────────────────────────

OUTPUT_DIR = PROJECT_ROOT / "thesis" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

COLORS = {
    "baseline": "#95a5a6",
    "best_prefix": "#3498db",
    "finetuned": "#2ecc71",
    "oracle": "#f39c12",
    "mixtral": "#e74c3c",
    "llama": "#3498db",
}

CATEGORY_ORDER = [
    "factual", "nonexistent", "impossible", "ambiguous",
    "borderline_obscure_real", "borderline_plausible_fake",
    "borderline_edge_factual",
]

CAT_LABELS = {
    "factual": "Factual",
    "nonexistent": "Nonexistent",
    "impossible": "Impossible",
    "ambiguous": "Ambiguous",
    "borderline_obscure_real": "Obscure Real",
    "borderline_plausible_fake": "Plausible Fake",
    "borderline_edge_factual": "Edge Factual",
}


# ── Ch 5: Within-Category AUC Decomposition ──────────────────────────────

def fig_auc_decomposition():
    """Bar chart of within-category logistic AUC by category and model."""
    csv_path = PROJECT_ROOT / "results" / "v5_baselines" / "analysis" / "v5_geometry_prediction_within_category.csv"
    df = pd.read_csv(csv_path)

    # Extract AUC rows
    auc_df = df[df["feature"] == "LOGISTIC_CV_AUC"].copy()
    auc_df = auc_df.rename(columns={"hall_mean": "auc_cv"})
    auc_df["auc_std"] = auc_df["correct_mean"]  # std stored in correct_mean column

    fig, ax = plt.subplots(figsize=(10, 5))

    models = ["mixtral-8x7b", "llama-4-maverick-17b"]
    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}
    model_colors = {"mixtral-8x7b": COLORS["mixtral"], "llama-4-maverick-17b": COLORS["llama"]}

    # Filter to categories present in data
    cats_in_data = [c for c in CATEGORY_ORDER if c in auc_df["category"].values]
    x = np.arange(len(cats_in_data))
    width = 0.35

    for i, model in enumerate(models):
        mdf = auc_df[auc_df["model"] == model]
        aucs = []
        stds = []
        for cat in cats_in_data:
            row = mdf[mdf["category"] == cat]
            if len(row) > 0:
                aucs.append(row["auc_cv"].values[0])
                stds.append(row["auc_std"].values[0])
            else:
                aucs.append(0.5)
                stds.append(0)

        offset = -width / 2 + i * width
        bars = ax.bar(x + offset, aucs, width * 0.9, yerr=stds,
                      label=model_labels[model], color=model_colors[model],
                      alpha=0.8, capsize=3, edgecolor="black", linewidth=0.5)

    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="Random (AUC=0.5)")
    ax.set_xlabel("Category")
    ax.set_ylabel("Cross-Validated AUC")
    ax.set_title("Within-Category Geometry → Hallucination Prediction (V5, 2,430 prompts)")
    ax.set_xticks(x)
    ax.set_xticklabels([CAT_LABELS.get(c, c) for c in cats_in_data], rotation=25, ha="right")
    ax.set_ylim(0.3, 0.85)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    fname = OUTPUT_DIR / "ch5_within_category_auc.png"
    plt.savefig(fname)
    plt.close()
    print(f"  Saved {fname.name}")


# ── Ch 6: V4 vs V5 Scale Comparison ──────────────────────────────────────

def fig_v4_v5_comparison():
    """Grouped bar chart comparing V4 pilot (449) vs V5 scale (2,430) results."""
    csv_path = PROJECT_ROOT / "results" / "v5_prefixes" / "analysis" / "v5_v4_comparison.csv"
    df = pd.read_csv(csv_path)

    # Only show conditions with V4 data
    df = df[df["v4_correct_rate"].notna()].copy()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    models = ["mixtral-8x7b", "llama-4-maverick-17b"]
    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}

    for idx, model in enumerate(models):
        ax = axes[idx]
        mdf = df[df["model"] == model].copy()

        conditions = mdf["condition"].values
        cond_labels = {"baseline": "Baseline", "entity_aware": "Entity-Aware",
                       "structured_caution": "Structured\nCaution"}
        x = np.arange(len(conditions))
        width = 0.35

        v4_rates = mdf["v4_correct_rate"].values * 100
        v5_rates = mdf["v5_correct_rate"].values * 100

        bars1 = ax.bar(x - width / 2, v4_rates, width, label="V4 Pilot (n=449)",
                       color="#3498db", alpha=0.8, edgecolor="black", linewidth=0.5)
        bars2 = ax.bar(x + width / 2, v5_rates, width, label="V5 Scale (n=2,430)",
                       color="#2ecc71", alpha=0.8, edgecolor="black", linewidth=0.5)

        # Add value labels
        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=8)
        for bar in bars2:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{bar.get_height():.1f}%", ha="center", va="bottom", fontsize=8)

        ax.set_xlabel("Condition")
        ax.set_ylabel("Accuracy (%)")
        ax.set_title(model_labels[model])
        ax.set_xticks(x)
        ax.set_xticklabels([cond_labels.get(c, c) for c in conditions])
        ax.set_ylim(70, 100)
        ax.legend(loc="lower right")
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Pilot (449 prompts) vs Scale (2,430 prompts) Accuracy", fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = OUTPUT_DIR / "ch6_v4_v5_comparison.png"
    plt.savefig(fname)
    plt.close()
    print(f"  Saved {fname.name}")


# ── Ch 7: Baseline vs Prefix vs Fine-Tuned Comparison ────────────────────

def fig_ft_comparison_bar():
    """Bar chart: baseline vs best-prefix vs fine-tuned vs oracle accuracy."""
    json_path = PROJECT_ROOT / "results" / "v5_finetuned" / "comparison_analysis.json"
    with open(json_path) as f:
        data = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

    configs = {"mixtral-8x7b": "C", "llama-4-maverick-17b": "A"}
    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}

    for idx, (model, config) in enumerate(configs.items()):
        ax = axes[idx]
        md = data[model]

        conditions = ["Baseline", "Best Prefix", f"Fine-Tuned\n(config {config})", "Oracle"]
        accuracies = [
            md["baseline"]["accuracy"] * 100,
            md["best_prefix"]["accuracy"] * 100,
            md["finetuned"][f"config{config}"]["aggregate"]["accuracy"] * 100,
            md["oracle"]["accuracy"] * 100,
        ]
        hall_rates = [
            md["baseline"]["hallucination_rate"] * 100,
            md["best_prefix"]["hallucination_rate"] * 100,
            md["finetuned"][f"config{config}"]["aggregate"]["hallucination_rate"] * 100,
            md["oracle"].get("hallucination_rate", md["oracle"]["hallucination"] / md["oracle"]["total"]) * 100,
        ]

        colors = [COLORS["baseline"], COLORS["best_prefix"], COLORS["finetuned"], COLORS["oracle"]]

        bars = ax.bar(conditions, accuracies, color=colors, edgecolor="black", linewidth=0.5, alpha=0.85)

        # Add accuracy labels on bars
        for bar, acc in zip(bars, accuracies):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{acc:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

        # Add hallucination rates below bars
        for bar, hall in zip(bars, hall_rates):
            ax.text(bar.get_x() + bar.get_width() / 2, 2,
                    f"H: {hall:.1f}%", ha="center", va="bottom", fontsize=8, color="white", fontweight="bold")

        ax.set_ylabel("Accuracy (%)")
        ax.set_title(model_labels[model])
        ax.set_ylim(0, 105)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Intervention Comparison: Accuracy on Held-Out Test Set (449 prompts)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = OUTPUT_DIR / "ch7_ft_comparison.png"
    plt.savefig(fname)
    plt.close()
    print(f"  Saved {fname.name}")


# ── Ch 7: Per-Category Fine-Tuning Heatmap ───────────────────────────────

def fig_ft_category_heatmap():
    """Heatmap of accuracy by category for baseline / best-prefix / fine-tuned."""
    json_path = PROJECT_ROOT / "results" / "v5_finetuned" / "comparison_analysis.json"
    with open(json_path) as f:
        data = json.load(f)

    configs = {"mixtral-8x7b": "C", "llama-4-maverick-17b": "A"}
    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    for idx, (model, config) in enumerate(configs.items()):
        ax = axes[idx]
        md = data[model]

        # Get baseline per-category from the V4 analysis (baseline in comparison_analysis)
        # comparison_analysis.json has baseline at aggregate level but we need per-category
        # Use fine-tuned per_category data which is available
        ft_cats = md["finetuned"][f"config{config}"]["per_category"]
        cats = [c for c in CATEGORY_ORDER if c in ft_cats]

        # Build matrix: rows = categories, cols = [baseline, best_prefix, fine-tuned]
        # We only have per-category for fine-tuned configs; for baseline/prefix we need
        # to read from the FT bridge data
        ft_bridge_path = PROJECT_ROOT / "results" / "v5_finetuned" / "analysis" / "ft_bridge_data.csv"
        bridge_df = pd.read_csv(ft_bridge_path)
        mbridge = bridge_df[bridge_df["model"] == model]

        matrix = []
        for cat in cats:
            row = []
            # Baseline accuracy from bridge data
            cat_data = mbridge[mbridge["category"] == cat]
            if len(cat_data) > 0:
                baseline_acc = (cat_data["baseline_label"] == 0).mean() * 100
            else:
                baseline_acc = 0
            row.append(baseline_acc)

            # Fine-tuned accuracy
            ft_acc = ft_cats[cat]["accuracy"] * 100
            row.append(ft_acc)

            # Hallucination rate for annotation
            matrix.append(row)

        matrix = np.array(matrix)
        col_labels = ["Baseline", f"Fine-Tuned\n(config {config})"]
        row_labels = [CAT_LABELS.get(c, c) for c in cats]

        # Heatmap
        im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=50, vmax=100)
        ax.set_xticks(range(len(col_labels)))
        ax.set_xticklabels(col_labels)
        ax.set_yticks(range(len(row_labels)))
        ax.set_yticklabels(row_labels)

        # Annotate cells
        for i in range(len(cats)):
            for j in range(len(col_labels)):
                val = matrix[i, j]
                color = "white" if val < 70 else "black"
                ax.text(j, i, f"{val:.0f}%", ha="center", va="center",
                        fontsize=10, fontweight="bold", color=color)

        ax.set_title(model_labels[model])

    fig.suptitle("Per-Category Accuracy: Baseline vs Fine-Tuned (449 held-out prompts)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = OUTPUT_DIR / "ch7_ft_category_heatmap.png"
    plt.savefig(fname)
    plt.close()
    print(f"  Saved {fname.name}")


# ── Ch 7: Hyperparameter Sensitivity ─────────────────────────────────────

def fig_hyperparameter_sensitivity():
    """Bar chart comparing configs A/B/C accuracy and hallucination rate."""
    json_path = PROJECT_ROOT / "results" / "v5_finetuned" / "comparison_analysis.json"
    with open(json_path) as f:
        data = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}
    config_info = {
        "A": "LR=2e-4, 3 epochs",
        "B": "LR=1e-4, 3 epochs",
        "C": "LR=2e-4, 5 epochs",
    }
    config_colors = {"A": "#3498db", "B": "#e67e22", "C": "#2ecc71"}

    for idx, model in enumerate(["mixtral-8x7b", "llama-4-maverick-17b"]):
        ax = axes[idx]
        md = data[model]

        configs_available = sorted([k for k in md["finetuned"].keys()])
        config_letters = [c.replace("config", "") for c in configs_available]

        accuracies = []
        hall_rates = []
        for c in configs_available:
            agg = md["finetuned"][c]["aggregate"]
            accuracies.append(agg["accuracy"] * 100)
            hall_rates.append(agg["hallucination_rate"] * 100)

        x = np.arange(len(config_letters))
        width = 0.35

        bars1 = ax.bar(x - width / 2, accuracies, width, label="Accuracy",
                       color="#2ecc71", alpha=0.8, edgecolor="black", linewidth=0.5)
        ax2 = ax.twinx()
        bars2 = ax2.bar(x + width / 2, hall_rates, width, label="Hallucination Rate",
                        color="#e74c3c", alpha=0.8, edgecolor="black", linewidth=0.5)

        # Labels
        for bar, val in zip(bars1, accuracies):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}%", ha="center", va="bottom", fontsize=9)
        for bar, val in zip(bars2, hall_rates):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=9)

        ax.set_xlabel("LoRA Configuration")
        ax.set_ylabel("Accuracy (%)", color="#2ecc71")
        ax2.set_ylabel("Hallucination Rate (%)", color="#e74c3c")
        ax.set_title(model_labels[model])
        ax.set_xticks(x)
        ax.set_xticklabels([f"Config {c}\n({config_info[c]})" for c in config_letters], fontsize=8)
        ax.set_ylim(80, 100)
        ax2.set_ylim(0, 5)

        # Baseline reference line
        bl_acc = md["baseline"]["accuracy"] * 100
        ax.axhline(y=bl_acc, color="gray", linestyle="--", alpha=0.6)
        ax.text(len(config_letters) - 0.5, bl_acc + 0.3, f"Baseline: {bl_acc:.1f}%",
                fontsize=8, color="gray", ha="right")

        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

    fig.suptitle("LoRA Hyperparameter Sensitivity (449 held-out prompts)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = OUTPUT_DIR / "ch7_hyperparameter_sensitivity.png"
    plt.savefig(fname)
    plt.close()
    print(f"  Saved {fname.name}")


# ── Ch 7: Regression Error Type Breakdown ─────────────────────────────────

def fig_regression_breakdown():
    """Stacked bar showing regression error types (refusal vs hallucination) by category."""
    bridge_path = PROJECT_ROOT / "results" / "v5_finetuned" / "analysis" / "ft_bridge_data.csv"
    df = pd.read_csv(bridge_path)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    configs = {"mixtral-8x7b": "C", "llama-4-maverick-17b": "A"}
    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}

    for idx, model in enumerate(configs.keys()):
        ax = axes[idx]
        mdf = df[(df["model"] == model) & (df["outcome"] == "broken_by_ft")].copy()

        if len(mdf) == 0:
            ax.text(0.5, 0.5, "No regressions", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(model_labels[model])
            continue

        # Count by category and error type
        cats = sorted(mdf["category"].unique())
        refusals = []
        hallucinations = []
        other = []
        for cat in cats:
            cdf = mdf[mdf["category"] == cat]
            refusals.append(len(cdf[cdf["ft_label"] == 3]))
            hallucinations.append(len(cdf[cdf["ft_label"] == 2]))
            other.append(len(cdf[~cdf["ft_label"].isin([2, 3])]))

        x = np.arange(len(cats))
        width = 0.6

        ax.bar(x, refusals, width, label="Refusal (over-caution)", color="#e67e22",
               edgecolor="black", linewidth=0.5)
        ax.bar(x, hallucinations, width, bottom=refusals, label="New hallucination",
               color="#e74c3c", edgecolor="black", linewidth=0.5)
        if any(o > 0 for o in other):
            ax.bar(x, other, width, bottom=[r + h for r, h in zip(refusals, hallucinations)],
                   label="Other", color="#95a5a6", edgecolor="black", linewidth=0.5)

        # Annotate totals
        for i, (r, h, o) in enumerate(zip(refusals, hallucinations, other)):
            total = r + h + o
            if total > 0:
                ax.text(i, total + 0.1, str(total), ha="center", va="bottom", fontsize=10, fontweight="bold")

        ax.set_xlabel("Category")
        ax.set_ylabel("Number of Regressions")
        ax.set_title(model_labels[model])
        ax.set_xticks(x)
        ax.set_xticklabels([CAT_LABELS.get(c, c) for c in cats], rotation=30, ha="right")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    fig.suptitle("Fine-Tuning Regressions: Error Type Breakdown",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = OUTPUT_DIR / "ch7_regression_breakdown.png"
    plt.savefig(fname)
    plt.close()
    print(f"  Saved {fname.name}")


# ── Ch 7: Density Distribution by FT Outcome ─────────────────────────────

def fig_density_by_outcome():
    """Violin plot of density by FT outcome — the thesis's key figure."""
    bridge_path = PROJECT_ROOT / "results" / "v5_finetuned" / "analysis" / "ft_bridge_data.csv"
    df = pd.read_csv(bridge_path)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}
    outcome_order = ["always_correct", "fixed_by_ft", "broken_by_ft", "still_broken"]
    outcome_labels = {
        "always_correct": "Always\nCorrect",
        "fixed_by_ft": "Fixed\nby FT",
        "broken_by_ft": "Broken\nby FT",
        "still_broken": "Still\nBroken",
    }
    palette = {
        "always_correct": "#2ecc71",
        "fixed_by_ft": "#3498db",
        "broken_by_ft": "#e67e22",
        "still_broken": "#e74c3c",
    }

    for idx, model in enumerate(["mixtral-8x7b", "llama-4-maverick-17b"]):
        ax = axes[idx]
        mdf = df[(df["model"] == model) & (df["outcome"].isin(outcome_order))].copy()
        mdf["outcome"] = pd.Categorical(mdf["outcome"], categories=outcome_order, ordered=True)

        sns.violinplot(data=mdf, x="outcome", y="density", order=outcome_order,
                       palette=palette, ax=ax, inner="box", cut=0, scale="width")

        # Add individual points
        for i, outcome in enumerate(outcome_order):
            sub = mdf[mdf["outcome"] == outcome]
            jitter = np.random.RandomState(42).uniform(-0.15, 0.15, len(sub))
            ax.scatter(i + jitter, sub["density"], color="black", alpha=0.3, s=8, zorder=3)

        ax.set_xticklabels([outcome_labels[o] for o in outcome_order])
        ax.set_xlabel("")
        ax.set_ylabel("Local Density")
        ax.set_title(model_labels[model])
        ax.grid(axis="y", alpha=0.3)

        # Add n labels
        for i, outcome in enumerate(outcome_order):
            n = len(mdf[mdf["outcome"] == outcome])
            ax.text(i, ax.get_ylim()[0] + 0.05, f"n={n}", ha="center", fontsize=8, color="gray")

    fig.suptitle("Embedding Density by Fine-Tuning Outcome (449 held-out prompts)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()

    fname = OUTPUT_DIR / "ch7_density_by_ft_outcome.png"
    plt.savefig(fname)
    plt.close()
    print(f"  Saved {fname.name}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Step 12B: Generating Thesis Figures")
    print("=" * 60)

    print("\nCh 5 — Can Geometry Predict?")
    fig_auc_decomposition()

    print("\nCh 6 — Can Prompts Reduce?")
    fig_v4_v5_comparison()

    print("\nCh 7 — Can Geometry Guide Intervention?")
    fig_ft_comparison_bar()
    fig_ft_category_heatmap()
    fig_hyperparameter_sensitivity()
    fig_regression_breakdown()
    fig_density_by_outcome()

    print(f"\n{'=' * 60}")
    print(f"  DONE — all figures saved to {OUTPUT_DIR}")
    print(f"{'=' * 60}")

    # Summary of all figures (existing + new)
    print("\n  COMPLETE FIGURE INVENTORY:")
    print("\n  Ch 4 (Experimental Setup):")
    print("    - v5_judge_agreement.png (exists)")
    print("    - Pipeline diagram (create manually in TikZ/draw.io)")
    print("\n  Ch 5 (Can Geometry Predict?):")
    print("    - v5_within_category_*.png (exists, 2 files)")
    print("    - v5_geometry_vs_hallucination_*.png (exists, 2 files)")
    print("    - ch5_within_category_auc.png (NEW)")
    print("    - consistency_heatmap.png (exists, from V3)")
    print("\n  Ch 6 (Can Prompts Reduce?):")
    print("    - v5_category_heatmap_*.png (exists, 2 files)")
    print("    - v5_tradeoff_curve.png (exists)")
    print("    - v5_refusal_rates.png (exists)")
    print("    - ch6_v4_v5_comparison.png (NEW)")
    print("\n  Ch 7 (Can Geometry Guide?):")
    print("    - v5_bridge_*.png (exists, 2 files)")
    print("    - ft_bridge_*.png (exists from 12A, 2 files)")
    print("    - ch7_ft_comparison.png (NEW)")
    print("    - ch7_ft_category_heatmap.png (NEW)")
    print("    - ch7_hyperparameter_sensitivity.png (NEW)")
    print("    - ch7_regression_breakdown.png (NEW)")
    print("    - ch7_density_by_ft_outcome.png (NEW)")


if __name__ == "__main__":
    main()
