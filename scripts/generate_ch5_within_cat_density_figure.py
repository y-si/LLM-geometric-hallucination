"""Generate Figure for Chapter 5 Section 5.4: Within-Category Density Distribution.

Focused box plot showing density distributions for hallucinated vs correct prompts
within the nonexistent category, side-by-side for Mixtral and Llama.

Usage:
    python3 scripts/generate_ch5_within_cat_density_figure.py
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "thesis" / "Dissertate-Harvard-LaTeX" / "figures"
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
    "hallucinated": "#bd6565",
    "correct": "#accd91",
}

# ── Load geometry features ───────────────────────────────────────────────

geo_df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "v5_geometry_features.csv")

# ── Load judge labels for each model ─────────────────────────────────────

def load_judge_labels(model_name):
    """Load judged answers and return DataFrame with id, category, judge_label."""
    fpath = (PROJECT_ROOT / "results" / "v5_baselines" / model_name /
             "no_prefix" / "judged_answers.jsonl")
    records = []
    with open(fpath) as f:
        for line in f:
            obj = json.loads(line)
            records.append({
                "id": obj["id"],
                "category": obj["category"],
                "judge_label": obj["judge_label"],
            })
    return pd.DataFrame(records)


models = {
    "mixtral-8x7b": "Mixtral 8x7B",
    "llama-4-maverick-17b": "Llama 4 Maverick",
}

# ── Build per-model data for nonexistent category ────────────────────────

model_data = {}
for model_id, model_label in models.items():
    labels_df = load_judge_labels(model_id)
    # Merge geometry with labels on prompt id
    merged = geo_df.merge(labels_df[["id", "judge_label"]], on="id", how="inner")
    # Filter to nonexistent category only
    nonexistent = merged[merged["category"] == "nonexistent"].copy()
    # Binary: hallucinated (label=2) vs correct (label=0)
    hall = nonexistent[nonexistent["judge_label"] == 2]["density"].values
    correct = nonexistent[nonexistent["judge_label"] == 0]["density"].values
    model_data[model_id] = {
        "label": model_label,
        "hall": hall,
        "correct": correct,
        "n_hall": len(hall),
        "n_correct": len(correct),
    }

# ── Generate figure ──────────────────────────────────────────────────────

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
        medianprops=dict(color="black", linewidth=1.5),
        whiskerprops=dict(linewidth=1.0),
        capprops=dict(linewidth=1.0),
        flierprops=dict(marker="o", markersize=4, alpha=0.5),
    )

    # Color the boxes
    colors = [COLORS["correct"], COLORS["hallucinated"]]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor("black")
        patch.set_linewidth(0.5)

    ax.set_title(data["label"], fontweight="bold")
    ax.set_ylabel("Density" if ax == axes[0] else "")

    # Add p-value annotation from the within-category CSV
    # (Mann-Whitney p-values verified from source data)
    if model_id == "mixtral-8x7b":
        p_str = "$p = 5.7 \\times 10^{-7}$"
    else:
        p_str = "$p = 3.4 \\times 10^{-5}$"

    # Position annotation at top with enough clearance
    ymax = max(data["correct"].max(), data["hall"].max())
    ymin = min(data["correct"].min(), data["hall"].min())
    y_range = ymax - ymin

    # Extend y-axis to make room for bracket and p-value text
    ax.set_ylim(ymin - 0.05 * y_range, ymax + 0.18 * y_range)

    bracket_y = ymax + 0.05 * y_range
    ax.text(1.5, bracket_y + 0.03 * y_range, p_str, ha="center", va="bottom",
            fontsize=10, fontstyle="italic")

    # Add bracket
    ax.plot([1, 2], [bracket_y, bracket_y], color="black", linewidth=0.8)
    ax.plot([1, 1], [bracket_y - 0.015 * y_range, bracket_y],
            color="black", linewidth=0.8)
    ax.plot([2, 2], [bracket_y - 0.015 * y_range, bracket_y],
            color="black", linewidth=0.8)

plt.tight_layout()

outpath = OUTPUT_DIR / "ch5_within_category_density_nonexistent.pdf"
fig.savefig(outpath, bbox_inches="tight")
print(f"Saved figure to {outpath}")

# Also save PNG for quick preview
outpath_png = OUTPUT_DIR / "ch5_within_category_density_nonexistent.png"
fig.savefig(outpath_png, bbox_inches="tight")
print(f"Saved preview to {outpath_png}")

# Print summary stats for verification
for model_id, data in model_data.items():
    print(f"\n{data['label']} — Nonexistent category:")
    print(f"  Correct: n={data['n_correct']}, mean={data['correct'].mean():.4f}, "
          f"median={np.median(data['correct']):.4f}")
    print(f"  Hallucinated: n={data['n_hall']}, mean={data['hall'].mean():.4f}, "
          f"median={np.median(data['hall']):.4f}")
