"""
3MT Slide V4: Fix label placement by finding actual blue/red regions.
Also try: just factual vs nonexistent (cleanest contrast).
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import umap

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.seed import set_seed

set_seed(42)

# --- Load data ---
print("Loading embeddings...")
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

# Run UMAP on just factual + nonexistent for cleaner separation
subset_cats = ["factual", "nonexistent"]
subset_ids = geo[geo["category"].isin(subset_cats)]["id"].tolist()
subset_valid = [pid for pid in subset_ids if pid in id_mapping]
subset_indices = [id_mapping[pid] for pid in subset_valid]
subset_embeddings = embeddings[subset_indices]

print(f"Running 2D UMAP on {len(subset_embeddings)} embeddings (factual + nonexistent only)...")
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords = reducer.fit_transform(subset_embeddings)

coord_df = pd.DataFrame({
    "id": subset_valid,
    "x": coords[:, 0],
    "y": coords[:, 1],
})

plot_df = df[df["category"].isin(subset_cats)].merge(coord_df, on="id", how="inner")
correct = plot_df[plot_df["is_hallucinated"] == 0]
hallucinated = plot_df[plot_df["is_hallucinated"] == 1]

print(f"Points: {len(correct)} correct, {len(hallucinated)} hallucinated")
print(f"  Factual: {len(plot_df[plot_df['category']=='factual'])} "
      f"({(plot_df[plot_df['category']=='factual']['is_hallucinated']).mean()*100:.0f}% hall)")
print(f"  Nonexistent: {len(plot_df[plot_df['category']=='nonexistent'])} "
      f"({(plot_df[plot_df['category']=='nonexistent']['is_hallucinated']).mean()*100:.0f}% hall)")

# Find the actual blue-heavy and red-heavy regions
# Use grid-based density
from scipy.ndimage import gaussian_filter

xmin, xmax = plot_df["x"].min(), plot_df["x"].max()
ymin, ymax = plot_df["y"].min(), plot_df["y"].max()
xpad = (xmax - xmin) * 0.1
ypad = (ymax - ymin) * 0.1

# Compute blue-centric and red-centric centroids using only points
# far from the other color
blue_centroid = correct[["x", "y"]].median()  # median is more robust
red_centroid = hallucinated[["x", "y"]].median()

print(f"\nBlue centroid: ({blue_centroid['x']:.1f}, {blue_centroid['y']:.1f})")
print(f"Red centroid:  ({red_centroid['x']:.1f}, {red_centroid['y']:.1f})")


# =====================================================
# VERSION A: Dark, clean, factual vs nonexistent only
# =====================================================
bg = '#08080f'
fig, ax = plt.subplots(figsize=(16, 9), facecolor=bg)
ax.set_facecolor(bg)

np.random.seed(42)

# Blue correct points with slight size variation
ax.scatter(correct["x"], correct["y"],
           c='#5DADE2', alpha=0.4, s=np.random.uniform(12, 30, len(correct)),
           edgecolors='none', zorder=2)

# Red hallucinated with glow
for glow_s, glow_a in [(250, 0.04), (120, 0.08)]:
    ax.scatter(hallucinated["x"], hallucinated["y"],
               c='#E74C3C', alpha=glow_a, s=glow_s,
               edgecolors='none', zorder=3)
ax.scatter(hallucinated["x"], hallucinated["y"],
           c='#FF6B6B', alpha=0.9, s=35,
           edgecolors='#E74C3C', linewidths=0.4, zorder=4)

# Smart label placement: put labels in empty space
# Find direction from data center to each centroid, extend outward
data_center = plot_df[["x", "y"]].mean()

# Blue label: extend from blue centroid away from center
blue_dir = blue_centroid - data_center
blue_dir_norm = blue_dir / np.sqrt((blue_dir**2).sum())
blue_label_pos = blue_centroid + blue_dir_norm * (xmax - xmin) * 0.4

# Red label: extend from red centroid away from center
red_dir = red_centroid - data_center
red_dir_norm = red_dir / np.sqrt((red_dir**2).sum())
red_label_pos = red_centroid + red_dir_norm * (xmax - xmin) * 0.4

ax.annotate("The AI knows\nthis well",
            xy=(blue_centroid["x"], blue_centroid["y"]),
            xytext=(blue_label_pos["x"], blue_label_pos["y"]),
            fontsize=20, fontweight='bold', color='#7EC8E3',
            ha='center', va='center',
            arrowprops=dict(arrowstyle='->', color='#7EC8E355',
                            lw=2, connectionstyle='arc3,rad=0.15'),
            fontfamily='sans-serif')

ax.annotate("The AI is\nmaking things up",
            xy=(red_centroid["x"], red_centroid["y"]),
            xytext=(red_label_pos["x"], red_label_pos["y"]),
            fontsize=20, fontweight='bold', color='#FF9999',
            ha='center', va='center',
            arrowprops=dict(arrowstyle='->', color='#FF999955',
                            lw=2, connectionstyle='arc3,rad=-0.15'),
            fontfamily='sans-serif')

# Expand axes to fit labels
ax.set_xlim(xmin - xpad * 4, xmax + xpad * 4)
ax.set_ylim(ymin - ypad * 3, ymax + ypad * 4)
ax.axis('off')

fig.text(0.5, 0.95, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=34, fontweight='bold',
         color='white', fontfamily='sans-serif')
fig.text(0.5, 0.905,
         "Each point is a question fed to an AI  —  where it lands predicts the answer",
         ha='center', va='center', fontsize=13, color='#777788',
         fontfamily='sans-serif')

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
           markersize=10, label='Correct answer', linestyle='None'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
           markeredgecolor='#E74C3C', markersize=10, label='Fabricated answer',
           linestyle='None'),
]
ax.legend(handles=legend_elements, loc='lower right',
          fontsize=13, frameon=False, labelcolor='white')

fig.text(0.5, 0.025,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#444455',
         fontfamily='sans-serif')

plt.tight_layout(pad=0.5)
plt.savefig("3mt_v4_contrast.png", dpi=250, bbox_inches='tight',
            facecolor=bg, edgecolor='none')
plt.close()
print("\nSaved 3mt_v4_contrast.png")


# =====================================================
# VERSION B: All categories, smarter annotations
# =====================================================
print("\n--- All categories version ---")

# Full UMAP
all_ids_full = geo["id"].tolist()
valid_full = [pid for pid in all_ids_full if pid in id_mapping]
all_indices_full = [id_mapping[pid] for pid in valid_full]

print(f"Running 2D UMAP on all {len(valid_full)} embeddings...")
reducer_full = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords_full = reducer_full.fit_transform(embeddings[all_indices_full])

coord_full_df = pd.DataFrame({
    "id": valid_full,
    "x": coords_full[:, 0],
    "y": coords_full[:, 1],
})

full_plot = df.merge(coord_full_df, on="id", how="inner")
full_correct = full_plot[full_plot["is_hallucinated"] == 0]
full_hall = full_plot[full_plot["is_hallucinated"] == 1]

# Find blue-dominated and red-dominated regions using grid
from scipy.ndimage import gaussian_filter as gf

grid_res = 50
xr = np.linspace(full_plot["x"].min(), full_plot["x"].max(), grid_res)
yr = np.linspace(full_plot["y"].min(), full_plot["y"].max(), grid_res)

# Count blue and red in each grid cell
blue_density = np.zeros((grid_res, grid_res))
red_density = np.zeros((grid_res, grid_res))

for _, row in full_correct.iterrows():
    xi = np.searchsorted(xr, row["x"]) - 1
    yi = np.searchsorted(yr, row["y"]) - 1
    xi, yi = max(0, min(xi, grid_res-1)), max(0, min(yi, grid_res-1))
    blue_density[yi, xi] += 1

for _, row in full_hall.iterrows():
    xi = np.searchsorted(xr, row["x"]) - 1
    yi = np.searchsorted(yr, row["y"]) - 1
    xi, yi = max(0, min(xi, grid_res-1)), max(0, min(yi, grid_res-1))
    red_density[yi, xi] += 1

blue_smooth = gf(blue_density, 3)
red_smooth = gf(red_density, 3)

# Find peak blue region and peak red region
blue_peak = np.unravel_index(blue_smooth.argmax(), blue_smooth.shape)
red_peak = np.unravel_index(red_smooth.argmax(), red_smooth.shape)

blue_peak_xy = (xr[blue_peak[1]], yr[blue_peak[0]])
red_peak_xy = (xr[red_peak[1]], yr[red_peak[0]])
print(f"Blue peak: {blue_peak_xy}")
print(f"Red peak: {red_peak_xy}")

bg = '#08080f'
fig, ax = plt.subplots(figsize=(16, 9), facecolor=bg)
ax.set_facecolor(bg)

safe_cats = ["factual", "borderline_edge_factual", "ambiguous"]
danger_cats = ["nonexistent", "borderline_plausible_fake"]

# All correct: blue
ax.scatter(full_correct["x"], full_correct["y"],
           c='#5DADE2', alpha=0.3, s=12, edgecolors='none', zorder=2)

# Hallucinated in danger categories: glowing red
danger_hall = full_hall[full_hall["category"].isin(danger_cats)]
other_hall = full_hall[~full_hall["category"].isin(danger_cats)]

ax.scatter(other_hall["x"], other_hall["y"],
           c='#E74C3C', alpha=0.35, s=18, edgecolors='none', zorder=3)

for gs, ga in [(250, 0.04), (120, 0.08)]:
    ax.scatter(danger_hall["x"], danger_hall["y"],
               c='#E74C3C', alpha=ga, s=gs, edgecolors='none', zorder=3)
ax.scatter(danger_hall["x"], danger_hall["y"],
           c='#FF6B6B', alpha=0.9, s=30, edgecolors='#E74C3C',
           linewidths=0.3, zorder=4)

# Labels pointing at the actual peak-density regions
xfull_range = full_plot["x"].max() - full_plot["x"].min()
yfull_range = full_plot["y"].max() - full_plot["y"].min()

# Blue label above and to the side of blue peak
blue_lx = blue_peak_xy[0] - xfull_range * 0.2
blue_ly = blue_peak_xy[1] + yfull_range * 0.25

ax.annotate("The AI knows\nthis well",
            xy=blue_peak_xy,
            xytext=(blue_lx, blue_ly),
            fontsize=20, fontweight='bold', color='#7EC8E3',
            ha='center', va='center',
            arrowprops=dict(arrowstyle='->', color='#7EC8E355',
                            lw=2, connectionstyle='arc3,rad=0.2'),
            fontfamily='sans-serif')

# Red label above and to the side of red peak
red_lx = red_peak_xy[0] + xfull_range * 0.2
red_ly = red_peak_xy[1] + yfull_range * 0.25

ax.annotate("The AI is\nmaking things up",
            xy=red_peak_xy,
            xytext=(red_lx, red_ly),
            fontsize=20, fontweight='bold', color='#FF9999',
            ha='center', va='center',
            arrowprops=dict(arrowstyle='->', color='#FF999955',
                            lw=2, connectionstyle='arc3,rad=-0.2'),
            fontfamily='sans-serif')

xmin_f, xmax_f = full_plot["x"].min(), full_plot["x"].max()
ymin_f, ymax_f = full_plot["y"].min(), full_plot["y"].max()
xp = xfull_range * 0.15
yp = yfull_range * 0.15
ax.set_xlim(xmin_f - xp * 3, xmax_f + xp * 3)
ax.set_ylim(ymin_f - yp * 2, ymax_f + yp * 4)
ax.axis('off')

fig.text(0.5, 0.95, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=34, fontweight='bold',
         color='white', fontfamily='sans-serif')
fig.text(0.5, 0.905,
         "2,364 questions mapped in the AI's internal space  —  each dot is one question",
         ha='center', va='center', fontsize=13, color='#777788',
         fontfamily='sans-serif')

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
           markersize=10, label='Correct answer', linestyle='None'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
           markeredgecolor='#E74C3C', markersize=10, label='Fabricated answer',
           linestyle='None'),
]
ax.legend(handles=legend_elements, loc='lower right',
          fontsize=13, frameon=False, labelcolor='white')

fig.text(0.5, 0.025,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#444455',
         fontfamily='sans-serif')

plt.tight_layout(pad=0.5)
plt.savefig("3mt_v4_all.png", dpi=250, bbox_inches='tight',
            facecolor=bg, edgecolor='none')
plt.close()
print("Saved 3mt_v4_all.png")

print("\nDone!")
