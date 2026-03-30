"""Generate 3-panel overview figure for thesis introduction chapter.

Panels:
  (a) Geometry Predicts Hallucination — density for hallucinated vs correct (nonexistent)
  (b) Interventions Reduce Hallucination — baseline → prefix → fine-tuned
  (c) Caution Transfers Across Domains — TruthfulQA accuracy

Usage:
    python3 scripts/generate_intro_figure.py
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LATEX_FIG_DIR = PROJECT_ROOT / "thesis" / "Dissertate-Harvard-LaTeX" / "figures"
THESIS_FIG_DIR = PROJECT_ROOT / "thesis" / "figures"
LATEX_FIG_DIR.mkdir(parents=True, exist_ok=True)
THESIS_FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ────────────────────────────────────────────────────────────────

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

# Subdued, professional palette
C_HALLUC = "#bd6565"       # Muted red (matches Ch5 figures)
C_CORRECT = "#accd91"      # Muted green (matches Ch5 figures)
C_BASELINE = "#7f8c8d"     # Gray
C_PREFIX = "#2980b9"       # Steel blue
C_FINETUNED = "#1a5276"    # Dark navy
C_MIXTRAL = "#f59f57"      # Orange
C_LLAMA = "#4a6da7"        # Steel blue


def _sig_stars(p: float) -> str:
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    return "n.s."


def _annotate_sig(ax, x1, x2, y, text, h=0.008):
    """Draw a bracket with significance text between two x positions."""
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=1.0, color="0.4")
    ax.text((x1 + x2) / 2, y + h + 0.002, text, ha="center", va="bottom",
            fontsize=11, color="0.3")


# ── Panel (a): Geometry Predicts Hallucination ───────────────────────────

def panel_a(ax):
    csv_path = (PROJECT_ROOT / "results" / "v5_baselines" / "analysis"
                / "v5_geometry_prediction_within_category.csv")
    df = pd.read_csv(csv_path)
    subset = df[(df["category"] == "nonexistent") & (df["feature"] == "density")]

    models = ["mixtral-8x7b", "llama-4-maverick-17b"]
    model_labels = ["Mixtral", "Llama"]

    x = np.arange(len(models))
    width = 0.30

    hall_means = []
    corr_means = []
    p_vals = []
    for m in models:
        row = subset[subset["model"] == m].iloc[0]
        hall_means.append(row["hall_mean"])
        corr_means.append(row["correct_mean"])
        p_vals.append(row["p_value"])

    bars_h = ax.bar(x - width / 2, hall_means, width, label="Hallucinated",
                    color=C_HALLUC, alpha=0.85, edgecolor="white", linewidth=0.5)
    bars_c = ax.bar(x + width / 2, corr_means, width, label="Correct",
                    color=C_CORRECT, alpha=0.85, edgecolor="white", linewidth=0.5)

    # Value labels above bars
    for i, (hv, cv) in enumerate(zip(hall_means, corr_means)):
        ax.text(x[i] - width / 2, hv + 0.005, f"{hv:.2f}", ha="center",
                va="bottom", fontsize=10, color="0.2")
        ax.text(x[i] + width / 2, cv + 0.005, f"{cv:.2f}", ha="center",
                va="bottom", fontsize=10, color="0.2")

    # Significance annotations with brackets
    for i, p in enumerate(p_vals):
        stars = _sig_stars(p)
        top = max(hall_means[i], corr_means[i])
        _annotate_sig(ax, x[i] - width/2, x[i] + width/2, top + 0.03, stars, h=0.012)

    ax.set_xticks(x)
    ax.set_xticklabels(model_labels)
    ax.set_ylabel("Embedding Density (log scale)")
    ax.set_title("Geometry Predicts\nHallucination", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.9, edgecolor="0.85")
    # Zoom y-axis to show the difference clearly
    all_vals = hall_means + corr_means
    ymin = min(all_vals) - 0.08
    ymax = max(all_vals) + 0.12
    ax.set_ylim(ymin, ymax)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Subtle annotation
    ax.text(0.5, -0.15, "Within the nonexistent category", transform=ax.transAxes,
            ha="center", va="top", fontsize=11, fontstyle="italic", color="0.25")


# ── Panel (b): Interventions Reduce Hallucination ────────────────────────

def panel_b(ax):
    conditions = ["Baseline", "Best Prefix", "Fine-tuned"]
    mixtral_rates = [11.8, 1.8, 1.3]
    llama_rates = [5.8, 1.3, 1.1]

    x = np.arange(len(conditions))
    width = 0.30

    ax.bar(x - width / 2, mixtral_rates, width, label="Mixtral",
           color=C_MIXTRAL, alpha=0.85, edgecolor="white", linewidth=0.5)
    ax.bar(x + width / 2, llama_rates, width, label="Llama",
           color=C_LLAMA, alpha=0.85, edgecolor="white", linewidth=0.5)

    # Value labels on bars
    for i, (mv, lv) in enumerate(zip(mixtral_rates, llama_rates)):
        ax.text(x[i] - width / 2, mv + 0.25, f"{mv}%", ha="center",
                va="bottom", fontsize=10, color="0.2")
        ax.text(x[i] + width / 2, lv + 0.25, f"{lv}%", ha="center",
                va="bottom", fontsize=10, color="0.2")

    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylabel("Hallucination Rate (%)")
    ax.set_title("Interventions Reduce\nHallucination", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.9, edgecolor="0.85")
    ax.set_ylim(0, max(mixtral_rates) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)



# ── Panel (c): Caution Transfers Across Domains ─────────────────────────

def panel_c(ax):
    models = ["Mixtral", "Llama"]
    baseline_acc = [74.4, 71.8]
    finetuned_acc = [76.6, 77.1]

    x = np.arange(len(models))
    width = 0.30

    ax.bar(x - width / 2, baseline_acc, width, label="Baseline",
           color=C_BASELINE, alpha=0.85, edgecolor="white", linewidth=0.5)
    ax.bar(x + width / 2, finetuned_acc, width, label="Fine-tuned",
           color=C_FINETUNED, alpha=0.85, edgecolor="white", linewidth=0.5)

    # Value labels above bars (consistent with panels a and b)
    for i, (bv, fv) in enumerate(zip(baseline_acc, finetuned_acc)):
        ax.text(x[i] - width / 2, bv + 0.25, f"{bv}%", ha="center",
                va="bottom", fontsize=10, color="0.2")
        ax.text(x[i] + width / 2, fv + 0.25, f"{fv}%", ha="center",
                va="bottom", fontsize=10, color="0.2")

    # Significance annotations with brackets
    top_m = max(baseline_acc[0], finetuned_acc[0])
    _annotate_sig(ax, x[0] - width/2, x[0] + width/2, top_m + 1.8, "n.s.", h=0.8)
    top_l = max(baseline_acc[1], finetuned_acc[1])
    _annotate_sig(ax, x[1] - width/2, x[1] + width/2, top_l + 1.8, "**", h=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Caution Transfers\nAcross Domains", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.9, edgecolor="0.85")
    ax.set_ylim(65, max(max(baseline_acc), max(finetuned_acc)) * 1.12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Domain annotation
    ax.text(0.5, -0.15, "TruthfulQA (unseen domain)", transform=ax.transAxes,
            ha="center", va="top", fontsize=11, fontstyle="italic", color="0.25")


# ── Assemble ─────────────────────────────────────────────────────────────

def main():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    panel_a(axes[0])
    panel_b(axes[1])
    panel_c(axes[2])

    # Panel labels
    for i, label in enumerate(["(a)", "(b)", "(c)"]):
        axes[i].text(-0.08, 1.12, label, transform=axes[i].transAxes,
                     fontsize=14, fontweight="bold", va="top", ha="left")

    plt.tight_layout(w_pad=3.0)

    # Significance key below figure
    fig.text(0.5, -0.02,
             "Significance: *** p < 0.001,  ** p < 0.01,  * p < 0.05,  n.s. not significant",
             ha="center", va="top", fontsize=11, color="0.25")

    out_latex = LATEX_FIG_DIR / "intro_overview.png"
    out_thesis = THESIS_FIG_DIR / "intro_overview.png"
    fig.savefig(out_latex)
    fig.savefig(out_thesis)
    print(f"Saved: {out_latex}")
    print(f"Saved: {out_thesis}")
    plt.close(fig)


if __name__ == "__main__":
    main()
