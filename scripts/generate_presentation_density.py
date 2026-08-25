"""Dark-mode within-category density boxplot for presentation."""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "thesis" / "Dissertate-Harvard-LaTeX" / "figures" / "presentation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Dark theme ──
DARK_BG = "#1a1a1a"
AXES_BG = "#2d2d2d"
TEXT_COLOR = "#ffffff"

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
    "axes.edgecolor": "#555555",
    "text.color": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
})

COLORS = {
    "hallucinated": "#ff6b6b",
    "correct": "#5bc0eb",
}

# ── Load data ──
geo_df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "v5_geometry_features.csv")

def load_judge_labels(model_name):
    fpath = (PROJECT_ROOT / "results" / "v5_baselines" / model_name /
             "no_prefix" / "judged_answers.jsonl")
    records = []
    with open(fpath) as f:
        for line in f:
            obj = json.loads(line)
            records.append({"id": obj["id"], "category": obj["category"],
                            "judge_label": obj["judge_label"]})
    return pd.DataFrame(records)

models = {
    "mixtral-8x7b": "Mixtral 8x7B",
    "llama-4-maverick-17b": "Llama 4 Maverick",
}

model_data = {}
for model_id, model_label in models.items():
    labels_df = load_judge_labels(model_id)
    merged = geo_df.merge(labels_df[["id", "judge_label"]], on="id", how="inner")
    nonexistent = merged[merged["category"] == "nonexistent"].copy()
    hall = nonexistent[nonexistent["judge_label"] == 2]["density"].values
    correct = nonexistent[nonexistent["judge_label"] == 0]["density"].values
    model_data[model_id] = {
        "label": model_label, "hall": hall, "correct": correct,
        "n_hall": len(hall), "n_correct": len(correct),
    }

# ── Generate figure ──
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)

for ax, (model_id, data) in zip(axes, model_data.items()):
    bp = ax.boxplot(
        [data["correct"], data["hall"]],
        labels=[
            f"Correct\n(n={data['n_correct']})",
            f"Hallucinated\n(n={data['n_hall']})",
        ],
        patch_artist=True,
        widths=0.5,
        medianprops=dict(color=TEXT_COLOR, linewidth=1.5),
        whiskerprops=dict(linewidth=1.0, color="#aaaaaa"),
        capprops=dict(linewidth=1.0, color="#aaaaaa"),
        flierprops=dict(marker="o", markersize=4, alpha=0.5,
                        markerfacecolor="#aaaaaa", markeredgecolor="#aaaaaa"),
    )

    colors = [COLORS["correct"], COLORS["hallucinated"]]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor("#aaaaaa")
        patch.set_linewidth(0.5)

    ax.set_title(data["label"], fontweight="bold", color=TEXT_COLOR)
    ax.set_ylabel("Density" if ax == axes[0] else "")

    if model_id == "mixtral-8x7b":
        p_str = "$p = 5.7 \\times 10^{-7}$"
    else:
        p_str = "$p = 3.4 \\times 10^{-5}$"

    ymax = max(data["correct"].max(), data["hall"].max())
    ymin = min(data["correct"].min(), data["hall"].min())
    y_range = ymax - ymin

    ax.set_ylim(ymin - 0.05 * y_range, ymax + 0.18 * y_range)

    bracket_y = ymax + 0.05 * y_range
    ax.text(1.5, bracket_y + 0.03 * y_range, p_str, ha="center", va="bottom",
            fontsize=10, fontstyle="italic", color=TEXT_COLOR)

    bracket_color = "#aaaaaa"
    ax.plot([1, 2], [bracket_y, bracket_y], color=bracket_color, linewidth=0.8)
    ax.plot([1, 1], [bracket_y - 0.015 * y_range, bracket_y],
            color=bracket_color, linewidth=0.8)
    ax.plot([2, 2], [bracket_y - 0.015 * y_range, bracket_y],
            color=bracket_color, linewidth=0.8)

plt.tight_layout()

fig.savefig(OUTPUT_DIR / "dark_within_category_density.png", dpi=300,
            bbox_inches="tight", facecolor=DARK_BG, edgecolor=DARK_BG)
fig.savefig(OUTPUT_DIR / "dark_within_category_density.pdf",
            bbox_inches="tight", facecolor=DARK_BG, edgecolor=DARK_BG)
plt.close(fig)

print("Saved: dark_within_category_density.png/pdf")
for model_id, data in model_data.items():
    print(f"  {data['label']}: correct n={data['n_correct']}, hallucinated n={data['n_hall']}")
