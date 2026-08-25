"""
3MT Combined Slide: Embedding explainer + contour map.

Layout:
- Top strip: "Question" → [vector of numbers] → "point on the map" (3b1b style)
- Main area: The contour map with all 2,364 questions

The audience sees HOW a question becomes a dot, then sees WHERE those dots land.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.gridspec import GridSpec
from scipy.ndimage import gaussian_filter
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

all_ids = geo["id"].tolist()
valid_ids = [pid for pid in all_ids if pid in id_mapping]
all_indices = [id_mapping[pid] for pid in valid_ids]

print(f"Running 2D UMAP on {len(valid_ids)} embeddings...")
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords = reducer.fit_transform(embeddings[all_indices])

coord_df = pd.DataFrame({"id": valid_ids, "x": coords[:, 0], "y": coords[:, 1]})
plot_df = df.merge(coord_df, on="id", how="inner")

all_correct = plot_df[plot_df["is_hallucinated"] == 0]
all_hall = plot_df[plot_df["is_hallucinated"] == 1]

# Get one real embedding to show actual numbers
example_id = "factual_001"
if example_id in id_mapping:
    example_vec = embeddings[id_mapping[example_id]]
else:
    example_vec = embeddings[0]

# --- Build the combined slide ---
bg = '#08080f'

fig = plt.figure(figsize=(16, 9), facecolor=bg)

# GridSpec: top row for explainer (25% height), bottom for map (75%)
gs = GridSpec(2, 1, figure=fig, height_ratios=[0.28, 0.72],
             hspace=0.02, left=0.03, right=0.97, top=0.92, bottom=0.06)

# =====================================================
# TOP: Embedding explainer strip
# =====================================================
ax_top = fig.add_subplot(gs[0])
ax_top.set_facecolor(bg)
ax_top.set_xlim(0, 10)
ax_top.set_ylim(0, 2)
ax_top.axis('off')

# Step 1: The question (left)
question_text = '"Who wrote\n  Don Quixote?"'
ax_top.text(1.0, 1.15, question_text, fontsize=14, color='white',
            fontfamily='monospace', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#1a1a2e',
                      edgecolor='#5DADE2', linewidth=1.5, alpha=0.9))

# Label
ax_top.text(1.0, 0.2, 'Question', fontsize=10, color='#888899',
            ha='center', va='center', fontfamily='sans-serif')

# Arrow 1: question → vector
ax_top.annotate('', xy=(2.7, 1.15), xytext=(1.9, 1.15),
                arrowprops=dict(arrowstyle='->', color='#5DADE266',
                                lw=2.5, connectionstyle='arc3,rad=0'))

ax_top.text(2.3, 0.7, 'embed', fontsize=9, color='#5DADE2', alpha=0.5,
            ha='center', va='center', fontfamily='sans-serif', style='italic')

# Step 2: Vector of numbers (middle)
# Draw a column of numbers like 3b1b
vec_x = 3.5
numbers = [f'{example_vec[i]:+.1f}' for i in range(6)]
numbers.append('⋮')
numbers.append(f'{example_vec[-1]:+.1f}')

# Background bracket
ax_top.text(vec_x - 0.35, 1.15, '[', fontsize=28, color='#5DADE2', alpha=0.4,
            ha='center', va='center', fontfamily='monospace', fontweight='light')
ax_top.text(vec_x + 0.35, 1.15, ']', fontsize=28, color='#5DADE2', alpha=0.4,
            ha='center', va='center', fontfamily='monospace', fontweight='light')

# Numbers in column
y_positions = np.linspace(1.75, 0.55, len(numbers))
for num_str, yp in zip(numbers, y_positions):
    color = '#5DADE2' if num_str != '⋮' else '#5DADE244'
    ax_top.text(vec_x, yp, num_str, fontsize=7.5, color=color,
                ha='center', va='center', fontfamily='monospace', alpha=0.8)

ax_top.text(vec_x, 0.15, '3,072 numbers', fontsize=9, color='#888899',
            ha='center', va='center', fontfamily='sans-serif')

# Arrow 2: vector → point
ax_top.annotate('', xy=(5.0, 1.15), xytext=(4.2, 1.15),
                arrowprops=dict(arrowstyle='->', color='#5DADE266',
                                lw=2.5, connectionstyle='arc3,rad=0'))

# Step 3: Small 3D-ish coordinate space with a single dot
# Draw simple axes
ax_x, ax_y_center = 5.8, 1.1
axis_len = 0.7

# X axis
ax_top.plot([ax_x - axis_len, ax_x + axis_len], [ax_y_center, ax_y_center],
            color='#444466', lw=1, alpha=0.5)
# Y axis
ax_top.plot([ax_x, ax_x], [ax_y_center - axis_len*0.8, ax_y_center + axis_len*0.8],
            color='#444466', lw=1, alpha=0.5)
# Z axis (diagonal for 3D effect)
ax_top.plot([ax_x - axis_len*0.5, ax_x + axis_len*0.5],
            [ax_y_center - axis_len*0.4, ax_y_center + axis_len*0.4],
            color='#444466', lw=1, alpha=0.3)

# The point
ax_top.plot(ax_x + 0.25, ax_y_center + 0.2, 'o', color='#5DADE2',
            markersize=10, markeredgecolor='white', markeredgewidth=1, zorder=5)

# Subtle glow
ax_top.plot(ax_x + 0.25, ax_y_center + 0.2, 'o', color='#5DADE2',
            markersize=20, alpha=0.15, zorder=4)

ax_top.text(5.8, 0.15, 'A point in space', fontsize=9, color='#888899',
            ha='center', va='center', fontfamily='sans-serif')

# Arrow 3: point → map (bigger, pointing down-right)
ax_top.annotate('', xy=(8.2, 0.6), xytext=(6.8, 1.0),
                arrowprops=dict(arrowstyle='->', color='#5DADE233',
                                lw=3, connectionstyle='arc3,rad=-0.15'))

# Step 4: Thumbnail preview of the map
ax_top.text(8.8, 1.4, 'Do this for\nevery question...', fontsize=11, color='#AAAABB',
            ha='center', va='center', fontfamily='sans-serif', style='italic')

ax_top.text(8.8, 0.15, '↓', fontsize=18, color='#5DADE244',
            ha='center', va='center', fontfamily='sans-serif')


# =====================================================
# BOTTOM: Contour map (from v5_contour)
# =====================================================
ax_map = fig.add_subplot(gs[1])
ax_map.set_facecolor(bg)

xmin, xmax = plot_df["x"].min(), plot_df["x"].max()
ymin, ymax = plot_df["y"].min(), plot_df["y"].max()
xpad = (xmax - xmin) * 0.08
ypad = (ymax - ymin) * 0.08

# Density contours
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

levels = np.percentile(density[density > 0], [30, 50, 70, 85, 95])
ax_map.contour(xi, yi, density, levels=levels,
               colors='#5DADE2', alpha=0.12, linewidths=0.8, zorder=1)

# Blue correct dots
ax_map.scatter(all_correct["x"], all_correct["y"],
               c='#5DADE2', alpha=0.25, s=10, edgecolors='none', zorder=2)

# Red hallucinated with glow
for gs_m, ga in [(8, 0.03), (4, 0.06)]:
    ax_map.scatter(all_hall["x"], all_hall["y"],
                   c='#E74C3C', alpha=ga, s=30 * gs_m,
                   edgecolors='none', zorder=3)
ax_map.scatter(all_hall["x"], all_hall["y"],
               c='#FF6B6B', alpha=0.85, s=25,
               edgecolors='#E74C3C', linewidths=0.3, zorder=4)

ax_map.set_xlim(xmin - xpad * 1.5, xmax + xpad * 1.5)
ax_map.set_ylim(ymin - ypad * 1.5, ymax + ypad * 2)
ax_map.axis('off')

# Labels in clear space
ax_map.text(0.05, 0.95, "Dense = reliable",
            transform=ax_map.transAxes, fontsize=18, fontweight='bold',
            color='#7EC8E3', fontfamily='sans-serif', va='top')
ax_map.text(0.05, 0.87, "Blue dots cluster tightly —\nthe AI has lots of knowledge here",
            transform=ax_map.transAxes, fontsize=10, color='#5DADE266',
            fontfamily='sans-serif', va='top')

ax_map.text(0.95, 0.95, "Sparse = fabrication",
            transform=ax_map.transAxes, fontsize=18, fontweight='bold',
            color='#FF9999', fontfamily='sans-serif', va='top', ha='right')
ax_map.text(0.95, 0.87, "Red dots are isolated —\nthe AI is guessing",
            transform=ax_map.transAxes, fontsize=10, color='#FF999966',
            fontfamily='sans-serif', va='top', ha='right')

# Legend
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
           markersize=10, label='Correct answer', linestyle='None'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
           markeredgecolor='#E74C3C', markersize=10, label='Fabricated answer',
           linestyle='None'),
]
ax_map.legend(handles=legend_elements, loc='lower right',
              fontsize=11, frameon=False, labelcolor='white')

# Title
fig.text(0.5, 0.97, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=32, fontweight='bold',
         color='white', fontfamily='sans-serif')

# Footer
fig.text(0.5, 0.015,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#444455',
         fontfamily='sans-serif')

plt.savefig("3mt_combined_slide.png", dpi=250, bbox_inches='tight',
            facecolor=bg, edgecolor='none')
plt.close()
print("Saved 3mt_combined_slide.png")
