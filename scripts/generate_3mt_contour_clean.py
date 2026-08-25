"""
Export clean contour map — no title, no labels, no legend, no footer.
Just the map itself on a dark background, ready to layer in Keynote.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

xmin, xmax = plot_df["x"].min(), plot_df["x"].max()
ymin, ymax = plot_df["y"].min(), plot_df["y"].max()
xpad = (xmax - xmin) * 0.08
ypad = (ymax - ymin) * 0.08

# --- Clean map (no annotations) ---
bg = '#08080f'
# Shared rendering function
def render_contour_map(fig, ax):
    grid_n = 100
    xi = np.linspace(xmin - xpad * 1.5, xmax + xpad * 1.5, grid_n)
    yi = np.linspace(ymin - ypad * 1.5, ymax + ypad * 1.5, grid_n)
    density = np.zeros((grid_n, grid_n))
    for _, row in all_correct.iterrows():
        ix = np.searchsorted(xi, row["x"]) - 1
        iy = np.searchsorted(yi, row["y"]) - 1
        if 0 <= ix < grid_n and 0 <= iy < grid_n:
            density[iy, ix] += 1
    density_smooth = gaussian_filter(density, sigma=4)

    levels = np.percentile(density_smooth[density_smooth > 0], [25, 45, 60, 75, 88, 95])
    ax.contour(xi, yi, density_smooth, levels=levels,
               colors='#5DADE2', alpha=0.35, linewidths=1.2, zorder=1)

    ax.scatter(all_correct["x"], all_correct["y"],
               c='#5DADE2', alpha=0.25, s=10, edgecolors='none', zorder=2)

    for gs_m, ga in [(8, 0.03), (4, 0.06)]:
        ax.scatter(all_hall["x"], all_hall["y"],
                   c='#E74C3C', alpha=ga, s=30 * gs_m,
                   edgecolors='none', zorder=3)
    ax.scatter(all_hall["x"], all_hall["y"],
               c='#FF6B6B', alpha=0.85, s=25,
               edgecolors='#E74C3C', linewidths=0.3, zorder=4)

    ax.set_xlim(xmin - xpad * 1.5, xmax + xpad * 1.5)
    ax.set_ylim(ymin - ypad * 1.5, ymax + ypad * 1.5)
    ax.axis('off')


# --- 16:9 version ---
fig, ax = plt.subplots(figsize=(16, 9), facecolor=bg)
ax.set_facecolor(bg)
render_contour_map(fig, ax)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_contour_clean.png", dpi=300, bbox_inches='tight',
            facecolor=bg, edgecolor='none', pad_inches=0.1)
plt.close()
print("Saved 3mt_contour_clean.png")

# --- Wide/flat version (for placing below explainer strip) ---
fig, ax = plt.subplots(figsize=(16, 6), facecolor=bg)
ax.set_facecolor(bg)
render_contour_map(fig, ax)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_contour_clean_wide.png", dpi=300, bbox_inches='tight',
            facecolor=bg, edgecolor='none', pad_inches=0.1)
plt.close()
print("Saved 3mt_contour_clean_wide.png")

# --- Transparent 16:9 ---
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_alpha(0)
ax.set_facecolor('none')
render_contour_map(fig, ax)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_contour_transparent.png", dpi=300, bbox_inches='tight',
            transparent=True, pad_inches=0.1)
plt.close()
print("Saved 3mt_contour_transparent.png")

# --- Transparent wide/flat ---
fig, ax = plt.subplots(figsize=(16, 6))
fig.patch.set_alpha(0)
ax.set_facecolor('none')
render_contour_map(fig, ax)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_contour_transparent_wide.png", dpi=300, bbox_inches='tight',
            transparent=True, pad_inches=0.1)
plt.close()
print("Saved 3mt_contour_transparent_wide.png")

print("\nAll files in project root:")
print("  3mt_contour_clean.png              — dark bg, 16:9")
print("  3mt_contour_clean_wide.png         — dark bg, wide/flat")
print("  3mt_contour_transparent.png        — transparent, 16:9")
print("  3mt_contour_transparent_wide.png   — transparent, wide/flat")
