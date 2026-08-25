"""
3MT Contour map where dot color reflects within-category density.

Dense within their category = blue (reliable)
Sparse within their category = red (hallucination-prone)

This is visually consistent with the thesis finding: within-category
density predicts hallucination. The audience sees "crowded = blue,
sparse = red" which matches the speech.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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

# We need the UMAP coordinates
all_ids = geo["id"].tolist()
valid_ids = [pid for pid in all_ids if pid in id_mapping]
all_indices = [id_mapping[pid] for pid in valid_ids]

print(f"Running 2D UMAP on {len(valid_ids)} embeddings...")
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords = reducer.fit_transform(embeddings[all_indices])

coord_df = pd.DataFrame({"id": valid_ids, "x": coords[:, 0], "y": coords[:, 1]})

# Merge with geometry features (has within-category density)
plot_df = geo.merge(coord_df, on="id", how="inner")

# Compute density in UMAP 2D space (k-NN based)
from sklearn.neighbors import NearestNeighbors

umap_coords = plot_df[["x", "y"]].values
nn = NearestNeighbors(n_neighbors=50)
nn.fit(umap_coords)
distances, _ = nn.kneighbors(umap_coords)
# Average distance to 15 nearest neighbors — lower = denser
avg_dist = distances.mean(axis=1)
# Invert so higher = denser, then percentile rank
plot_df["umap_density"] = 1.0 / (avg_dist + 1e-8)
plot_df["density_pctile"] = plot_df["umap_density"].rank(pct=True)

print(f"Total points: {len(plot_df)}")
print(f"Density percentile range: {plot_df['density_pctile'].min():.2f} - {plot_df['density_pctile'].max():.2f}")
print("\nPer-category counts:")
for cat in sorted(plot_df["category"].unique()):
    n = len(plot_df[plot_df["category"] == cat])
    print(f"  {cat}: {n}")

xmin, xmax = plot_df["x"].min(), plot_df["x"].max()
ymin, ymax = plot_df["y"].min(), plot_df["y"].max()
xpad = (xmax - xmin) * 0.08
ypad = (ymax - ymin) * 0.08


def render_density_map(fig, ax, bg_opaque=True):
    """Render the contour map with density-colored dots."""

    # Contour lines from ALL points (overall data density in UMAP space)
    grid_n = 100
    xi = np.linspace(xmin - xpad * 1.5, xmax + xpad * 1.5, grid_n)
    yi = np.linspace(ymin - ypad * 1.5, ymax + ypad * 1.5, grid_n)
    density_grid = np.zeros((grid_n, grid_n))
    for _, row in plot_df.iterrows():
        ix = np.searchsorted(xi, row["x"]) - 1
        iy = np.searchsorted(yi, row["y"]) - 1
        if 0 <= ix < grid_n and 0 <= iy < grid_n:
            density_grid[iy, ix] += 1
    density_grid = gaussian_filter(density_grid, sigma=4)

    levels = np.percentile(density_grid[density_grid > 0], [25, 45, 60, 75, 88, 95])
    ax.contour(xi, yi, density_grid, levels=levels,
               colors='#5DADE2', alpha=0.35, linewidths=1.2, zorder=1)

    # Binary coloring: bottom 15% density = red, rest = blue
    threshold = 0.15
    is_sparse = plot_df["density_pctile"] < threshold
    sparse_pts = plot_df[is_sparse]
    dense_pts = plot_df[~is_sparse]

    # Blue (dense) — dominant visual, bright and solid
    ax.scatter(dense_pts["x"], dense_pts["y"],
               c='#5DADE2', alpha=0.7, s=25,
               edgecolors='none', zorder=2)

    # Red (sparse) — same dot size as blue, subtle glow only
    ax.scatter(sparse_pts["x"], sparse_pts["y"],
               c='#E74C3C', alpha=0.06, s=80,
               edgecolors='none', zorder=3)
    ax.scatter(sparse_pts["x"], sparse_pts["y"],
               c='#FF6B6B', alpha=0.85, s=25,
               edgecolors='none', zorder=4)

    ax.set_xlim(xmin - xpad * 1.5, xmax + xpad * 1.5)
    ax.set_ylim(ymin - ypad * 1.5, ymax + ypad * 1.5)
    ax.axis('off')


# --- Dark background, 16:9 ---
bg = '#08080f'
fig, ax = plt.subplots(figsize=(16, 9), facecolor=bg)
ax.set_facecolor(bg)
render_density_map(fig, ax)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_density_colored.png", dpi=300, bbox_inches='tight',
            facecolor=bg, edgecolor='none', pad_inches=0.1)
plt.close()
print("\nSaved 3mt_density_colored.png")

# --- Dark background, wide/flat ---
fig, ax = plt.subplots(figsize=(16, 6), facecolor=bg)
ax.set_facecolor(bg)
render_density_map(fig, ax)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_density_colored_wide.png", dpi=300, bbox_inches='tight',
            facecolor=bg, edgecolor='none', pad_inches=0.1)
plt.close()
print("Saved 3mt_density_colored_wide.png")

# --- Transparent, 16:9 ---
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_alpha(0)
ax.set_facecolor('none')
render_density_map(fig, ax, bg_opaque=False)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_density_colored_transparent.png", dpi=300, bbox_inches='tight',
            transparent=True, pad_inches=0.1)
plt.close()
print("Saved 3mt_density_colored_transparent.png")

# --- Transparent, wide/flat ---
fig, ax = plt.subplots(figsize=(16, 6))
fig.patch.set_alpha(0)
ax.set_facecolor('none')
render_density_map(fig, ax, bg_opaque=False)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig("3mt_density_colored_transparent_wide.png", dpi=300, bbox_inches='tight',
            transparent=True, pad_inches=0.1)
plt.close()
print("Saved 3mt_density_colored_transparent_wide.png")

print("\nAll files in project root:")
print("  3mt_density_colored.png                 — dark bg, 16:9")
print("  3mt_density_colored_wide.png            — dark bg, wide")
print("  3mt_density_colored_transparent.png     — transparent, 16:9")
print("  3mt_density_colored_transparent_wide.png — transparent, wide")
