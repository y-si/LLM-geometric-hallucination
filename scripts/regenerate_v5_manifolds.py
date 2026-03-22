"""Regenerate V5 category manifold UMAP figures with better layout for thesis.

Layout: split into two images (a: 3 panels, b: 4 panels in 2x2) for LaTeX stacking.
Categories ordered by increasing Mixtral hallucination rate.
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import umap

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.seed import set_seed

set_seed(42)

# --- Load data ---
embeddings = np.load("data/processed/v5_question_embeddings.npy")
with open("data/processed/v5_embedding_id_mapping.json") as f:
    id_mapping = json.load(f)

geo = pd.read_csv("data/processed/v5_geometry_features.csv")

# Load Mixtral baselines
mixtral_results = []
with open("results/v5_baselines/mixtral-8x7b/no_prefix/judged_answers.jsonl") as f:
    for line in f:
        mixtral_results.append(json.loads(line))
mixtral_df = pd.DataFrame(mixtral_results)

# Merge
df = mixtral_df[["id", "category", "judge_label"]].copy()
# Only keep correct (0) and hallucinated (2) for visualization
df = df[df["judge_label"].isin([0, 2])].copy()
df["is_hallucinated"] = (df["judge_label"] == 2).astype(int)

# Get embedding indices for all prompts in the geometry features (for UMAP)
all_ids = geo["id"].tolist()
all_indices = [id_mapping[pid] for pid in all_ids if pid in id_mapping]
all_embeddings = embeddings[all_indices]

print(f"Running UMAP on {len(all_embeddings)} embeddings...")
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords_2d = reducer.fit_transform(all_embeddings)

# Build coordinate lookup
valid_ids = [pid for pid in all_ids if pid in id_mapping]
coord_df = pd.DataFrame({
    "id": valid_ids,
    "umap1": coords_2d[:, 0],
    "umap2": coords_2d[:, 1],
})

# Merge coordinates with results
plot_df = df.merge(coord_df, on="id", how="inner")
print(f"Plotting {len(plot_df)} prompts ({plot_df['is_hallucinated'].sum()} hallucinated)")

# Category order by increasing Mixtral hallucination rate
cat_order = [
    ("ambiguous", "Ambiguous"),
    ("borderline_edge_factual", "Edge Factual"),
    ("factual", "Factual"),
    ("impossible", "Impossible"),
    ("borderline_obscure_real", "Obscure Real"),
    ("nonexistent", "Nonexistent"),
    ("borderline_plausible_fake", "Plausible Fake"),
]

# Compute per-category hallucination rates
cat_rates = {}
for cat_key, cat_label in cat_order:
    cat_data = plot_df[plot_df["category"] == cat_key]
    if len(cat_data) > 0:
        rate = cat_data["is_hallucinated"].mean() * 100
        cat_rates[cat_key] = rate

# --- Generate split figures ---
out_dir = Path("thesis/Dissertate-Harvard-LaTeX/figures")

def plot_category_panel(ax, cat_key, cat_label, data):
    """Plot a single category panel."""
    cat_data = data[data["category"] == cat_key]
    if len(cat_data) == 0:
        ax.set_visible(False)
        return

    correct = cat_data[cat_data["is_hallucinated"] == 0]
    hallucinated = cat_data[cat_data["is_hallucinated"] == 1]
    rate = cat_rates.get(cat_key, 0)

    ax.scatter(correct["umap1"], correct["umap2"],
               c="lightblue", alpha=0.5, s=30, label="Correct", zorder=1)
    if len(hallucinated) > 0:
        ax.scatter(hallucinated["umap1"], hallucinated["umap2"],
                   c="red", alpha=0.8, s=50, marker="x", linewidths=1.5,
                   label="Hallucinated", zorder=2)

    ax.set_title(f"{cat_label}\n({rate:.0f}% hallucinated)", fontsize=13, fontweight="bold")
    ax.set_xlabel("UMAP 1", fontsize=10)
    ax.set_ylabel("UMAP 2", fontsize=10)
    ax.legend(loc="best", fontsize=8, framealpha=0.8)
    ax.grid(alpha=0.2)

# Image A: first 3 categories (low hallucination)
fig_a, axes_a = plt.subplots(1, 3, figsize=(18, 5.5))
for ax, (cat_key, cat_label) in zip(axes_a, cat_order[:3]):
    plot_category_panel(ax, cat_key, cat_label, plot_df)
# Only first panel gets y-label
for ax in axes_a[1:]:
    ax.set_ylabel("")
plt.tight_layout()
fig_a.savefig(out_dir / "v5_category_manifolds_umap_mixtral_a.png", dpi=300, bbox_inches="tight")
plt.close(fig_a)
print(f"Saved: v5_category_manifolds_umap_mixtral_a.png")

# Image B: next 4 categories (high hallucination), 2x2 grid
fig_b, axes_b = plt.subplots(2, 2, figsize=(12, 11))
for ax, (cat_key, cat_label) in zip(axes_b.flat, cat_order[3:]):
    plot_category_panel(ax, cat_key, cat_label, plot_df)
# Clean up y-labels
axes_b[0, 1].set_ylabel("")
axes_b[1, 1].set_ylabel("")
plt.tight_layout()
fig_b.savefig(out_dir / "v5_category_manifolds_umap_mixtral_b.png", dpi=300, bbox_inches="tight")
plt.close(fig_b)
print(f"Saved: v5_category_manifolds_umap_mixtral_b.png")

# Also save a single combined figure for reference
fig_c, axes_c = plt.subplots(3, 3, figsize=(18, 16))
for i, (cat_key, cat_label) in enumerate(cat_order):
    row, col = divmod(i, 3)
    plot_category_panel(axes_c[row, col], cat_key, cat_label, plot_df)
# Hide empty panels
for i in range(len(cat_order), 9):
    row, col = divmod(i, 3)
    axes_c[row, col].set_visible(False)
plt.tight_layout()
fig_c.savefig(out_dir / "v5_category_manifolds_umap_mixtral_combined.png", dpi=300, bbox_inches="tight")
plt.close(fig_c)
print(f"Saved: v5_category_manifolds_umap_mixtral_combined.png")

# Also overwrite the analysis directory version
fig_c2, axes_c2 = plt.subplots(3, 3, figsize=(18, 16))
for i, (cat_key, cat_label) in enumerate(cat_order):
    row, col = divmod(i, 3)
    plot_category_panel(axes_c2[row, col], cat_key, cat_label, plot_df)
for i in range(len(cat_order), 9):
    row, col = divmod(i, 3)
    axes_c2[row, col].set_visible(False)
plt.tight_layout()
fig_c2.savefig(Path("results/v5_baselines/analysis/v5_category_manifolds_umap_mixtral.png"), dpi=300, bbox_inches="tight")
plt.close(fig_c2)
print("Done!")
