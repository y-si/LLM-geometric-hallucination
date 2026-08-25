"""Dark-mode 3-panel overview figure for presentation."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "thesis" / "Dissertate-Harvard-LaTeX" / "figures" / "presentation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Dark theme ──
DARK_BG = "#1a1a1a"
AXES_BG = "#2d2d2d"
TEXT_COLOR = "#ffffff"
SUBTLE_TEXT = "#aaaaaa"
SPINE_COLOR = "#555555"

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
    "figure.facecolor": DARK_BG,
    "axes.facecolor": AXES_BG,
    "axes.edgecolor": SPINE_COLOR,
    "text.color": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "legend.facecolor": "#333333",
    "legend.edgecolor": "#555555",
    "legend.labelcolor": TEXT_COLOR,
})

# Dark-mode palette
C_HALLUC = "#ff6b6b"
C_CORRECT = "#5bc0eb"
C_BASELINE = "#888888"
C_PREFIX = "#5bc0eb"
C_FINETUNED = "#2ecc71"
C_MIXTRAL = "#f59f57"
C_LLAMA = "#5bc0eb"
BRACKET_COLOR = "#aaaaaa"


def _sig_stars(p):
    if p < 0.001: return "***"
    elif p < 0.01: return "**"
    elif p < 0.05: return "*"
    return "n.s."


def _annotate_sig(ax, x1, x2, y, text, h=0.008):
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=1.0, color=BRACKET_COLOR)
    ax.text((x1 + x2) / 2, y + h + 0.002, text, ha="center", va="bottom",
            fontsize=11, color=SUBTLE_TEXT)


def panel_a(ax):
    csv_path = (PROJECT_ROOT / "results" / "v5_baselines" / "analysis"
                / "v5_geometry_prediction_within_category.csv")
    df = pd.read_csv(csv_path)
    subset = df[(df["category"] == "nonexistent") & (df["feature"] == "density")]

    models = ["mixtral-8x7b", "llama-4-maverick-17b"]
    model_labels = ["Mixtral", "Llama"]
    x = np.arange(len(models))
    width = 0.30

    hall_means, corr_means, p_vals = [], [], []
    for m in models:
        row = subset[subset["model"] == m].iloc[0]
        hall_means.append(row["hall_mean"])
        corr_means.append(row["correct_mean"])
        p_vals.append(row["p_value"])

    ax.bar(x - width / 2, hall_means, width, label="Hallucinated",
           color=C_HALLUC, alpha=0.85, edgecolor=AXES_BG, linewidth=0.5)
    ax.bar(x + width / 2, corr_means, width, label="Correct",
           color=C_CORRECT, alpha=0.85, edgecolor=AXES_BG, linewidth=0.5)

    for i, (hv, cv) in enumerate(zip(hall_means, corr_means)):
        ax.text(x[i] - width / 2, hv + 0.005, f"{hv:.2f}", ha="center",
                va="bottom", fontsize=10, color=SUBTLE_TEXT)
        ax.text(x[i] + width / 2, cv + 0.005, f"{cv:.2f}", ha="center",
                va="bottom", fontsize=10, color=SUBTLE_TEXT)

    for i, p in enumerate(p_vals):
        stars = _sig_stars(p)
        top = max(hall_means[i], corr_means[i])
        _annotate_sig(ax, x[i] - width/2, x[i] + width/2, top + 0.03, stars, h=0.012)

    ax.set_xticks(x)
    ax.set_xticklabels(model_labels)
    ax.set_ylabel("Embedding Density (log scale)")
    ax.set_title("Geometry Predicts\nHallucination", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.7)
    all_vals = hall_means + corr_means
    ax.set_ylim(min(all_vals) - 0.08, max(all_vals) + 0.12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(0.5, -0.15, "Within the nonexistent category", transform=ax.transAxes,
            ha="center", va="top", fontsize=11, fontstyle="italic", color=SUBTLE_TEXT)


def panel_b(ax):
    conditions = ["Baseline", "Best Prefix", "Fine-tuned"]
    mixtral_rates = [11.8, 1.8, 1.3]
    llama_rates = [5.8, 1.3, 1.1]
    x = np.arange(len(conditions))
    width = 0.30

    ax.bar(x - width / 2, mixtral_rates, width, label="Mixtral",
           color=C_MIXTRAL, alpha=0.85, edgecolor=AXES_BG, linewidth=0.5)
    ax.bar(x + width / 2, llama_rates, width, label="Llama",
           color=C_LLAMA, alpha=0.85, edgecolor=AXES_BG, linewidth=0.5)

    for i, (mv, lv) in enumerate(zip(mixtral_rates, llama_rates)):
        ax.text(x[i] - width / 2, mv + 0.25, f"{mv}%", ha="center",
                va="bottom", fontsize=10, color=SUBTLE_TEXT)
        ax.text(x[i] + width / 2, lv + 0.25, f"{lv}%", ha="center",
                va="bottom", fontsize=10, color=SUBTLE_TEXT)

    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylabel("Hallucination Rate (%)")
    ax.set_title("Interventions Reduce\nHallucination", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.7)
    ax.set_ylim(0, max(mixtral_rates) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def panel_c(ax):
    models = ["Mixtral", "Llama"]
    baseline_acc = [74.4, 71.8]
    finetuned_acc = [76.6, 77.1]
    x = np.arange(len(models))
    width = 0.30

    ax.bar(x - width / 2, baseline_acc, width, label="Baseline",
           color=C_BASELINE, alpha=0.85, edgecolor=AXES_BG, linewidth=0.5)
    ax.bar(x + width / 2, finetuned_acc, width, label="Fine-tuned",
           color=C_FINETUNED, alpha=0.85, edgecolor=AXES_BG, linewidth=0.5)

    for i, (bv, fv) in enumerate(zip(baseline_acc, finetuned_acc)):
        ax.text(x[i] - width / 2, bv + 0.25, f"{bv}%", ha="center",
                va="bottom", fontsize=10, color=SUBTLE_TEXT)
        ax.text(x[i] + width / 2, fv + 0.25, f"{fv}%", ha="center",
                va="bottom", fontsize=10, color=SUBTLE_TEXT)

    top_m = max(baseline_acc[0], finetuned_acc[0])
    _annotate_sig(ax, x[0] - width/2, x[0] + width/2, top_m + 1.8, "n.s.", h=0.8)
    top_l = max(baseline_acc[1], finetuned_acc[1])
    _annotate_sig(ax, x[1] - width/2, x[1] + width/2, top_l + 1.8, "**", h=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Caution Transfers\nAcross Domains", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.7)
    ax.set_ylim(65, max(max(baseline_acc), max(finetuned_acc)) * 1.12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(0.5, -0.15, "TruthfulQA (unseen domain)", transform=ax.transAxes,
            ha="center", va="top", fontsize=11, fontstyle="italic", color=SUBTLE_TEXT)


def main():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    panel_a(axes[0])
    panel_b(axes[1])
    panel_c(axes[2])

    for i, label in enumerate(["(a)", "(b)", "(c)"]):
        axes[i].text(-0.08, 1.12, label, transform=axes[i].transAxes,
                     fontsize=14, fontweight="bold", va="top", ha="left", color=TEXT_COLOR)

    plt.tight_layout(w_pad=3.0)

    fig.text(0.5, -0.02,
             "Significance: *** p < 0.001,  ** p < 0.01,  * p < 0.05,  n.s. not significant",
             ha="center", va="top", fontsize=11, color=SUBTLE_TEXT)

    fig.savefig(OUTPUT_DIR / "dark_intro_overview.png", facecolor=DARK_BG, edgecolor=DARK_BG)
    fig.savefig(OUTPUT_DIR / "dark_intro_overview.pdf", facecolor=DARK_BG, edgecolor=DARK_BG)
    print("Saved: dark_intro_overview.png/pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
