"""
3MT Slide V5: Two-panel side-by-side.

Left panel: Factual questions (2% hallucinated) — a cloud of blue
Right panel: Nonexistent entities (86% hallucinated) — a cloud of red

Same dark aesthetic, same "looking inside the AI" feel.
The contrast is immediately obvious from across the room.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
import umap

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.seed import set_seed

set_seed(42)

# --- Load data ---
print("Loading...")
embeddings = np.load("data/processed/v5_question_embeddings.npy")
with open("data/processed/v5_embedding_id_mapping.json") as f:
    id_mapping = json.load(f)

geo = pd.read_csv("data/processed/v5_geometry_features.csv")

mixtral_results = []
with open("results/v5_baselines/mixtral-8x7b/no_prefix/judged_answers.jsonl") as f:
    for line in f:
        mixtral_results.append(json.loads(line))
mixtral_df = pd.DataFrame(mixtral_results)

df = mixtral_df[["id", "category", "judge_label"]].copy()
df = df[df["judge_label"].isin([0, 2])].copy()
df["is_hallucinated"] = (df["judge_label"] == 2).astype(int)

# Run UMAP on ALL data (shared space)
all_ids = geo["id"].tolist()
valid_ids = [pid for pid in all_ids if pid in id_mapping]
all_indices = [id_mapping[pid] for pid in valid_ids]

print(f"Running 2D UMAP on {len(valid_ids)} embeddings...")
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords = reducer.fit_transform(embeddings[all_indices])

coord_df = pd.DataFrame({"id": valid_ids, "x": coords[:, 0], "y": coords[:, 1]})
plot_df = df.merge(coord_df, on="id", how="inner")

# Split by category
factual = plot_df[plot_df["category"] == "factual"]
nonexistent = plot_df[plot_df["category"] == "nonexistent"]

fact_correct = factual[factual["is_hallucinated"] == 0]
fact_hall = factual[factual["is_hallucinated"] == 1]
nonex_correct = nonexistent[nonexistent["is_hallucinated"] == 0]
nonex_hall = nonexistent[nonexistent["is_hallucinated"] == 1]

fact_rate = factual["is_hallucinated"].mean() * 100
nonex_rate = nonexistent["is_hallucinated"].mean() * 100
print(f"Factual: {len(factual)} points, {fact_rate:.0f}% hallucinated")
print(f"Nonexistent: {len(nonexistent)} points, {nonex_rate:.0f}% hallucinated")


def draw_panel(ax, correct_data, hall_data, bg='#08080f'):
    """Draw one UMAP panel with glow effects."""
    ax.set_facecolor(bg)

    np.random.seed(42)

    # Blue correct
    if len(correct_data) > 0:
        sizes = np.random.uniform(15, 35, len(correct_data))
        ax.scatter(correct_data["x"], correct_data["y"],
                   c='#5DADE2', alpha=0.5, s=sizes,
                   edgecolors='none', zorder=2)

    # Red hallucinated with glow
    if len(hall_data) > 0:
        hall_sizes = np.random.uniform(25, 45, len(hall_data))
        # Glow layers
        for gs_mult, ga in [(6, 0.04), (3, 0.08)]:
            ax.scatter(hall_data["x"], hall_data["y"],
                       c='#E74C3C', alpha=ga, s=hall_sizes * gs_mult,
                       edgecolors='none', zorder=3)
        # Core
        ax.scatter(hall_data["x"], hall_data["y"],
                   c='#FF6B6B', alpha=0.9, s=hall_sizes,
                   edgecolors='#E74C3C', linewidths=0.4, zorder=4)

    ax.axis('off')


# =====================================================
# VERSION A: Two-panel, shared coordinate system
# =====================================================
bg = '#08080f'
fig = plt.figure(figsize=(16, 9), facecolor=bg)
gs = GridSpec(1, 2, figure=fig, wspace=0.05, left=0.03, right=0.97,
             top=0.82, bottom=0.1)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

# Use same axis limits for both panels (shared space)
all_x = plot_df["x"]
all_y = plot_df["y"]
xmin, xmax = all_x.min(), all_x.max()
ymin, ymax = all_y.min(), all_y.max()
xpad = (xmax - xmin) * 0.08
ypad = (ymax - ymin) * 0.08

draw_panel(ax1, fact_correct, fact_hall)
draw_panel(ax2, nonex_correct, nonex_hall)

for ax in [ax1, ax2]:
    ax.set_xlim(xmin - xpad, xmax + xpad)
    ax.set_ylim(ymin - ypad, ymax + ypad)

# Panel labels
ax1.text(0.5, 0.95, "Questions about real things",
         transform=ax1.transAxes, ha='center', va='top',
         fontsize=18, fontweight='bold', color='#7EC8E3',
         fontfamily='sans-serif')
ax1.text(0.5, 0.88, f"{fact_rate:.0f}% fabricated",
         transform=ax1.transAxes, ha='center', va='top',
         fontsize=14, color='#5DADE2', alpha=0.7,
         fontfamily='sans-serif')

ax2.text(0.5, 0.95, "Questions about fake things",
         transform=ax2.transAxes, ha='center', va='top',
         fontsize=18, fontweight='bold', color='#FF9999',
         fontfamily='sans-serif')
ax2.text(0.5, 0.88, f"{nonex_rate:.0f}% fabricated",
         transform=ax2.transAxes, ha='center', va='top',
         fontsize=14, color='#E74C3C', alpha=0.7,
         fontfamily='sans-serif')

# Divider line
fig.patches.append(plt.Rectangle((0.5, 0.1), 0.001, 0.72,
                                  transform=fig.transFigure,
                                  color='#333344', zorder=10))

# Title
fig.text(0.5, 0.95, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=34, fontweight='bold',
         color='white', fontfamily='sans-serif')
fig.text(0.5, 0.895,
         "Same AI, same internal map  —  different regions, different reliability",
         ha='center', va='center', fontsize=13, color='#777788',
         fontfamily='sans-serif')

# Legend centered at bottom
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
           markersize=10, label='Correct answer', linestyle='None'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
           markeredgecolor='#E74C3C', markersize=10, label='Fabricated answer',
           linestyle='None'),
]
fig.legend(handles=legend_elements, loc='lower center',
           fontsize=12, frameon=False, labelcolor='white',
           ncol=2, bbox_to_anchor=(0.5, 0.04))

fig.text(0.5, 0.015,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#444455',
         fontfamily='sans-serif')

plt.savefig("3mt_v5_twopanel.png", dpi=250, bbox_inches='tight',
            facecolor=bg, edgecolor='none')
plt.close()
print("Saved 3mt_v5_twopanel.png")


# =====================================================
# VERSION B: Three panels (factual, mixed, nonexistent)
# =====================================================
ambiguous = plot_df[plot_df["category"] == "ambiguous"]
amb_correct = ambiguous[ambiguous["is_hallucinated"] == 0]
amb_hall = ambiguous[ambiguous["is_hallucinated"] == 1]
amb_rate = ambiguous["is_hallucinated"].mean() * 100 if len(ambiguous) > 0 else 0

# Also try impossible
impossible = plot_df[plot_df["category"] == "impossible"]
imp_correct = impossible[impossible["is_hallucinated"] == 0]
imp_hall = impossible[impossible["is_hallucinated"] == 1]
imp_rate = impossible["is_hallucinated"].mean() * 100 if len(impossible) > 0 else 0

# Use borderline_plausible_fake as middle (should be ~50%)
plausible = plot_df[plot_df["category"] == "borderline_plausible_fake"]
plaus_correct = plausible[plausible["is_hallucinated"] == 0]
plaus_hall = plausible[plausible["is_hallucinated"] == 1]
plaus_rate = plausible["is_hallucinated"].mean() * 100 if len(plausible) > 0 else 0

print(f"\nMiddle categories: ambiguous={amb_rate:.0f}%, impossible={imp_rate:.0f}%, plausible_fake={plaus_rate:.0f}%")

fig = plt.figure(figsize=(16, 9), facecolor=bg)
gs = GridSpec(1, 3, figure=fig, wspace=0.03, left=0.02, right=0.98,
             top=0.82, bottom=0.1)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])

draw_panel(ax1, fact_correct, fact_hall)
draw_panel(ax2, plaus_correct, plaus_hall)
draw_panel(ax3, nonex_correct, nonex_hall)

for ax in [ax1, ax2, ax3]:
    ax.set_xlim(xmin - xpad, xmax + xpad)
    ax.set_ylim(ymin - ypad, ymax + ypad)

ax1.text(0.5, 0.95, "Real things",
         transform=ax1.transAxes, ha='center', va='top',
         fontsize=17, fontweight='bold', color='#7EC8E3',
         fontfamily='sans-serif')
ax1.text(0.5, 0.87, f"{fact_rate:.0f}% fabricated",
         transform=ax1.transAxes, ha='center', va='top',
         fontsize=13, color='#7EC8E3', alpha=0.6,
         fontfamily='sans-serif')

ax2.text(0.5, 0.95, "Plausible-sounding\nbut fake",
         transform=ax2.transAxes, ha='center', va='top',
         fontsize=17, fontweight='bold', color='#CCAA77',
         fontfamily='sans-serif')
ax2.text(0.5, 0.80, f"{plaus_rate:.0f}% fabricated",
         transform=ax2.transAxes, ha='center', va='top',
         fontsize=13, color='#CCAA77', alpha=0.6,
         fontfamily='sans-serif')

ax3.text(0.5, 0.95, "Totally made up",
         transform=ax3.transAxes, ha='center', va='top',
         fontsize=17, fontweight='bold', color='#FF9999',
         fontfamily='sans-serif')
ax3.text(0.5, 0.87, f"{nonex_rate:.0f}% fabricated",
         transform=ax3.transAxes, ha='center', va='top',
         fontsize=13, color='#FF9999', alpha=0.6,
         fontfamily='sans-serif')

# Dividers
for x_pos in [0.345, 0.665]:
    fig.patches.append(plt.Rectangle((x_pos, 0.1), 0.001, 0.72,
                                      transform=fig.transFigure,
                                      color='#333344', zorder=10))

fig.text(0.5, 0.95, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=34, fontweight='bold',
         color='white', fontfamily='sans-serif')
fig.text(0.5, 0.895,
         "Same AI  —  the type of question determines where it lands on the map",
         ha='center', va='center', fontsize=13, color='#777788',
         fontfamily='sans-serif')

fig.legend(handles=legend_elements, loc='lower center',
           fontsize=12, frameon=False, labelcolor='white',
           ncol=2, bbox_to_anchor=(0.5, 0.04))

fig.text(0.5, 0.015,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#444455',
         fontfamily='sans-serif')

plt.savefig("3mt_v5_threepanel.png", dpi=250, bbox_inches='tight',
            facecolor=bg, edgecolor='none')
plt.close()
print("Saved 3mt_v5_threepanel.png")


# =====================================================
# VERSION C: Single combined UMAP, color by category
# with density contours showing the "neighborhoods"
# =====================================================
from scipy.ndimage import gaussian_filter

fig, ax = plt.subplots(figsize=(16, 9), facecolor=bg)
ax.set_facecolor(bg)

# All points, very subtle
all_correct = plot_df[plot_df["is_hallucinated"] == 0]
all_hall = plot_df[plot_df["is_hallucinated"] == 1]

# Draw all correct as subtle blue
ax.scatter(all_correct["x"], all_correct["y"],
           c='#5DADE2', alpha=0.25, s=10, edgecolors='none', zorder=2)

# Draw all hallucinated with glow
for gs_m, ga in [(8, 0.03), (4, 0.06)]:
    ax.scatter(all_hall["x"], all_hall["y"],
               c='#E74C3C', alpha=ga, s=30 * gs_m,
               edgecolors='none', zorder=3)
ax.scatter(all_hall["x"], all_hall["y"],
           c='#FF6B6B', alpha=0.85, s=25,
           edgecolors='#E74C3C', linewidths=0.3, zorder=4)

# Add density contours for correct answers (shows the "dense neighborhoods")
grid_n = 100
xi = np.linspace(xmin - xpad, xmax + xpad, grid_n)
yi = np.linspace(ymin - ypad, ymax + ypad, grid_n)
density = np.zeros((grid_n, grid_n))
for _, row in all_correct.iterrows():
    ix = np.searchsorted(xi, row["x"]) - 1
    iy = np.searchsorted(yi, row["y"]) - 1
    if 0 <= ix < grid_n and 0 <= iy < grid_n:
        density[iy, ix] += 1
density = gaussian_filter(density, sigma=4)

# Subtle blue contour lines showing knowledge density
levels = np.percentile(density[density > 0], [50, 75, 90])
ax.contour(xi, yi, density, levels=levels,
           colors='#5DADE2', alpha=0.15, linewidths=1.0, zorder=1)

ax.set_xlim(xmin - xpad * 1.5, xmax + xpad * 1.5)
ax.set_ylim(ymin - ypad * 1.5, ymax + ypad * 2.5)
ax.axis('off')

# Find cleanest blue and red regions for labels
blue_median = all_correct[["x", "y"]].median()
red_median = all_hall[["x", "y"]].median()

# Labels in corners
ax.text(0.08, 0.92, "Dense = reliable",
        transform=ax.transAxes, fontsize=18, fontweight='bold',
        color='#7EC8E3', fontfamily='sans-serif', va='top')
ax.text(0.08, 0.85, "Blue dots cluster tightly —\nthe AI has lots of knowledge here",
        transform=ax.transAxes, fontsize=11, color='#5DADE288',
        fontfamily='sans-serif', va='top')

ax.text(0.92, 0.92, "Sparse = fabrication",
        transform=ax.transAxes, fontsize=18, fontweight='bold',
        color='#FF9999', fontfamily='sans-serif', va='top', ha='right')
ax.text(0.92, 0.85, "Red dots are isolated —\nthe AI is guessing",
        transform=ax.transAxes, fontsize=11, color='#FF999988',
        fontfamily='sans-serif', va='top', ha='right')

fig.text(0.5, 0.96, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=34, fontweight='bold',
         color='white', fontfamily='sans-serif')
fig.text(0.5, 0.92,
         "2,364 questions in the AI's internal space  —  contour lines show knowledge density",
         ha='center', va='center', fontsize=12, color='#666677',
         fontfamily='sans-serif')

fig.legend(handles=legend_elements, loc='lower center',
           fontsize=12, frameon=False, labelcolor='white',
           ncol=2, bbox_to_anchor=(0.5, 0.03))

fig.text(0.5, 0.01,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#444455',
         fontfamily='sans-serif')

plt.tight_layout(pad=0.5)
plt.savefig("3mt_v5_contour.png", dpi=250, bbox_inches='tight',
            facecolor=bg, edgecolor='none')
plt.close()
print("Saved 3mt_v5_contour.png")

print("\nDone! Three versions:")
print("  1. 3mt_v5_twopanel.png   — factual vs nonexistent side-by-side")
print("  2. 3mt_v5_threepanel.png — factual vs plausible vs nonexistent")
print("  3. 3mt_v5_contour.png    — single map with density contours")
