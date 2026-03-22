"""Generate figures for Chapter 5 Section 5.3 (Decomposing Category vs. Geometric Signal).

Three figures:
  1. Grouped bar chart: three-model AUC comparison (geo-only, cat-only, cat+geo)
  2. Signal decomposition waterfall: V3 AUC vs V5 decomposed components
  3. Per-category within-category AUC dot plot (bridges 5.3 → 5.4)

Usage:
    python3 scripts/generate_ch5_decomposition_figures.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "thesis" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Style (matching existing thesis figures) ─────────────────────────────

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
    "mixtral": "#e74c3c",
    "llama": "#3498db",
    "geo_only": "#95a5a6",       # Gray
    "cat_only": "#f39c12",       # Orange
    "cat_geo": "#2ecc71",        # Green
    "increment": "#27ae60",      # Darker green
    "chance": "#bdc3c7",         # Light gray
    "v3": "#9b59b6",             # Purple
}


# ── Figure 1: Three-model AUC comparison ─────────────────────────────────

def fig1_auc_comparison():
    """Grouped bar chart: geo-only, cat-only, cat+geo AUC for both models."""

    # Post-fix verified numbers (Mar 14, 2026 script run)
    models = ["Mixtral 8x7B", "Llama 4 Maverick"]
    geo_only = [0.645, 0.726]
    cat_only = [0.782, 0.773]
    cat_geo  = [0.800, 0.814]

    x = np.arange(len(models))
    width = 0.22

    fig, ax = plt.subplots(figsize=(8, 5))

    bars1 = ax.bar(x - width, geo_only, width, label="Geometry-only",
                   color=COLORS["geo_only"], edgecolor="black", linewidth=0.5, alpha=0.85)
    bars2 = ax.bar(x, cat_only, width, label="Category-only",
                   color=COLORS["cat_only"], edgecolor="black", linewidth=0.5, alpha=0.85)
    bars3 = ax.bar(x + width, cat_geo, width, label="Category + Geometry",
                   color=COLORS["cat_geo"], edgecolor="black", linewidth=0.5, alpha=0.85)

    # Value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 0.008,
                    f"{height:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Chance line
    ax.axhline(y=0.5, color=COLORS["chance"], linestyle="--", linewidth=1.0, label="Chance (0.5)")

    # Increment annotations — bracket above bars connecting cat-only to cat+geo
    for i, (co, cg) in enumerate(zip(cat_only, cat_geo)):
        increment = cg - co
        top = cg + 0.022  # above the value label
        cat_x = x[i]
        geo_x = x[i] + width
        # Horizontal bracket with vertical ticks
        ax.plot([cat_x, cat_x, geo_x, geo_x],
                [co + 0.003, top, top, cg + 0.003],
                color=COLORS["increment"], lw=1.2, clip_on=False)
        ax.text((cat_x + geo_x) / 2, top + 0.006, f"+{increment:.3f}",
                fontsize=9, color=COLORS["increment"], fontweight="bold",
                ha="center", va="bottom")

    ax.set_ylabel("Cross-Validated AUC")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0.45, 0.90)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    path = OUTPUT_DIR / "ch5_decomposition_auc.png"
    fig.savefig(path)
    plt.close()
    print(f"  Saved: {path}")


# ── Figure 2: Signal decomposition (V3 → V5 reconciliation) ─────────────

def fig2_signal_decomposition():
    """Waterfall-style figure showing how V3 AUC 0.86 decomposes in V5."""

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)

    for ax, model, geo_auc, cat_auc, catgeo_auc, train_auc in [
        (axes[0], "Mixtral 8x7B", 0.645, 0.782, 0.800, 0.655),
        (axes[1], "Llama 4 Maverick", 0.726, 0.773, 0.814, 0.729),
    ]:
        increment = catgeo_auc - cat_auc

        # Bar positions and values
        labels = [
            "Initial study\n(train, pooled)",
            "Geometry\n-only (CV)",
            "Category\n-only (CV)",
            "Cat+Geo\n(CV)",
        ]
        values = [0.86, geo_auc, cat_auc, catgeo_auc]
        colors_list = [COLORS["v3"], COLORS["geo_only"], COLORS["cat_only"], COLORS["cat_geo"]]

        bars = ax.bar(range(len(labels)), values, color=colors_list,
                      edgecolor="black", linewidth=0.5, alpha=0.85, width=0.55)

        # Value labels
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.010,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

        # Chance line
        ax.axhline(y=0.5, color=COLORS["chance"], linestyle="--", linewidth=1.0)

        # Right-side annotation: category signal bracket (outside bars)
        bx = 3.42  # right of the last bar
        ax.annotate("", xy=(bx, 0.5), xytext=(bx, cat_auc),
                    arrowprops=dict(arrowstyle="<->", color=COLORS["cat_only"],
                                    lw=1.2))
        ax.text(bx + 0.08, (cat_auc + 0.5) / 2, "category\nsignal",
                fontsize=8, color="#c0800a", va="center", fontstyle="italic")

        # Right-side annotation: geometry increment bracket
        ax.annotate("", xy=(bx, cat_auc), xytext=(bx, catgeo_auc),
                    arrowprops=dict(arrowstyle="<->", color=COLORS["increment"],
                                    lw=1.5))
        ax.text(bx + 0.08, (cat_auc + catgeo_auc) / 2, f"+{increment:.3f}\ngeo",
                fontsize=8, color=COLORS["increment"], va="center", fontweight="bold")

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_xlim(-0.5, 4.3)
        ax.set_ylim(0.42, 0.92)
        ax.set_title(model, fontsize=12, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_ylabel("AUC")

    plt.tight_layout()
    path = OUTPUT_DIR / "ch5_signal_decomposition.png"
    fig.savefig(path)
    plt.close()
    print(f"  Saved: {path}")


# ── Figure 3: Per-category within-category AUC ──────────────────────────

def fig3_within_category_auc():
    """Dot plot: within-category CV AUC for each category × model."""

    # Read within-category data
    csv_path = PROJECT_ROOT / "results" / "v5_baselines" / "analysis" / "v5_geometry_prediction_within_category.csv"
    df = pd.read_csv(csv_path)
    auc_rows = df[df["feature"] == "LOGISTIC_CV_AUC"].copy()

    # Category display order (by Mixtral hallucination rate, matching Table 5.1)
    cat_order = [
        "borderline_plausible_fake",
        "nonexistent",
        "impossible",
        "factual",
        "borderline_obscure_real",
    ]
    cat_labels = {
        "borderline_plausible_fake": "Plausible\nFake",
        "nonexistent": "Nonexistent",
        "impossible": "Impossible",
        "factual": "Factual",
        "borderline_obscure_real": "Obscure\nReal",
    }

    fig, ax = plt.subplots(figsize=(9, 5))

    offset = 0.12
    for i, cat in enumerate(cat_order):
        for j, (model_key, color, marker, label) in enumerate([
            ("mixtral-8x7b", COLORS["mixtral"], "o", "Mixtral"),
            ("llama-4-maverick-17b", COLORS["llama"], "s", "Llama"),
        ]):
            row = auc_rows[(auc_rows["model"] == model_key) & (auc_rows["category"] == cat)]
            if row.empty:
                # Mark as missing
                ax.scatter(i + (j - 0.5) * offset * 2, 0.5, marker="x",
                          color=color, s=60, alpha=0.4, zorder=5)
                continue

            auc_val = row["hall_mean"].values[0]
            auc_std = row["correct_mean"].values[0]  # std stored in correct_mean column
            n_hall = row["n_hall"].values[0]

            x_pos = i + (j - 0.5) * offset * 2
            ax.scatter(x_pos, auc_val, marker=marker, color=color, s=80,
                      edgecolors="black", linewidth=0.5, zorder=5,
                      label=label if i == 0 else None)
            ax.errorbar(x_pos, auc_val, yerr=auc_std, color=color,
                       capsize=3, capthick=1, linewidth=1, alpha=0.6, zorder=4)

            # n label
            ax.text(x_pos, auc_val - auc_std - 0.035, f"n={int(n_hall)}",
                   fontsize=7, ha="center", color=color, alpha=0.7)

    # Chance line
    ax.axhline(y=0.5, color=COLORS["chance"], linestyle="--", linewidth=1.0, label="Chance")

    ax.set_xticks(range(len(cat_order)))
    ax.set_xticklabels([cat_labels[c] for c in cat_order])
    ax.set_ylabel("Within-Category CV AUC")
    ax.set_ylim(0.30, 0.80)
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)

    # Note about missing categories
    ax.text(0.02, 0.02, "× = too few hallucinations for logistic regression",
           transform=ax.transAxes, fontsize=8, fontstyle="italic", alpha=0.6)

    plt.tight_layout()
    path = OUTPUT_DIR / "ch5_within_category_auc_dots.png"
    fig.savefig(path)
    plt.close()
    print(f"  Saved: {path}")


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating Chapter 5.3 figures...\n")
    fig1_auc_comparison()
    fig2_signal_decomposition()
    fig3_within_category_auc()
    print("\nDone.")
