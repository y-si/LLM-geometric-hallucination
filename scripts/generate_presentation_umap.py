"""Regenerate V5 category manifold UMAP figures with dark theme for presentation."""

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

# --- Dark theme ---
DARK_BG = "#1a1a1a"
AXES_BG = "#2d2d2d"
TEXT_COLOR = "#ffffff"
GRID_COLOR = "#444444"

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor": AXES_BG,
    "axes.edgecolor": "#555555",
    "text.color": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "figure.edgecolor": DARK_BG,
    "legend.facecolor": "#333333",
    "legend.edgecolor": "#555555",
    "legend.labelcolor": TEXT_COLOR,
})

# --- Load data ---
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
all_indices = [id_mapping[pid] for pid in all_ids if pid in id_mapping]
all_embeddings = embeddings[all_indices]

print(f"Running UMAP on {len(all_embeddings)} embeddings...")
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords_2d = reducer.fit_transform(all_embeddings)

valid_ids = [pid for pid in all_ids if pid in id_mapping]
coord_df = pd.DataFrame({
    "id": valid_ids,
    "umap1": coords_2d[:, 0],
    "umap2": coords_2d[:, 1],
})

plot_df = df.merge(coord_df, on="id", how="inner")
print(f"Plotting {len(plot_df)} prompts ({plot_df['is_hallucinated'].sum()} hallucinated)")

cat_order = [
    ("ambiguous", "Ambiguous"),
    ("borderline_edge_factual", "Edge Factual"),
    ("factual", "Factual"),
    ("impossible", "Impossible"),
    ("borderline_obscure_real", "Obscure Real"),
    ("nonexistent", "Nonexistent"),
    ("borderline_plausible_fake", "Plausible Fake"),
]

cat_rates = {}
for cat_key, cat_label in cat_order:
    cat_data = plot_df[plot_df["category"] == cat_key]
    if len(cat_data) > 0:
        rate = cat_data["is_hallucinated"].mean() * 100
        cat_rates[cat_key] = rate

out_dir = Path("thesis/Dissertate-Harvard-LaTeX/figures/presentation")
out_dir.mkdir(parents=True, exist_ok=True)

# Dark-mode colors
CORRECT_COLOR = "#5bc0eb"    # bright cyan
HALL_COLOR = "#ff6b6b"       # bright red
TITLE_COLOR = "#ffffff"

def plot_category_panel_dark(ax, cat_key, cat_label, data):
    cat_data = data[data["category"] == cat_key]
    if len(cat_data) == 0:
        ax.set_visible(False)
        return

    correct = cat_data[cat_data["is_hallucinated"] == 0]
    hallucinated = cat_data[cat_data["is_hallucinated"] == 1]
    rate = cat_rates.get(cat_key, 0)

    ax.scatter(correct["umap1"], correct["umap2"],
               c=CORRECT_COLOR, alpha=0.5, s=30, label="Correct", zorder=1)
    if len(hallucinated) > 0:
        ax.scatter(hallucinated["umap1"], hallucinated["umap2"],
                   c=HALL_COLOR, alpha=0.9, s=50, marker="x", linewidths=1.5,
                   label="Hallucinated", zorder=2)

    ax.set_title(f"{cat_label}\n({rate:.0f}% hallucinated)",
                 fontsize=13, fontweight="bold", color=TITLE_COLOR)
    ax.set_xlabel("UMAP 1", fontsize=10)
    ax.set_ylabel("UMAP 2", fontsize=10)
    ax.legend(loc="best", fontsize=8, framealpha=0.7)
    ax.grid(alpha=0.15, color=GRID_COLOR)
    ax.tick_params(colors=TEXT_COLOR)


# Image A: first 3 categories (low hallucination)
fig_a, axes_a = plt.subplots(1, 3, figsize=(18, 5.5))
for ax, (cat_key, cat_label) in zip(axes_a, cat_order[:3]):
    plot_category_panel_dark(ax, cat_key, cat_label, plot_df)
for ax in axes_a[1:]:
    ax.set_ylabel("")
plt.tight_layout()
fig_a.savefig(out_dir / "dark_umap_manifolds_a.png", dpi=300, bbox_inches="tight",
              facecolor=DARK_BG, edgecolor=DARK_BG)
fig_a.savefig(out_dir / "dark_umap_manifolds_a.pdf", bbox_inches="tight",
              facecolor=DARK_BG, edgecolor=DARK_BG)
plt.close(fig_a)
print("Saved: dark_umap_manifolds_a")

# Image B: next 4 categories (high hallucination), 2x2 grid
fig_b, axes_b = plt.subplots(2, 2, figsize=(12, 11))
for ax, (cat_key, cat_label) in zip(axes_b.flat, cat_order[3:]):
    plot_category_panel_dark(ax, cat_key, cat_label, plot_df)
axes_b[0, 1].set_ylabel("")
axes_b[1, 1].set_ylabel("")
plt.tight_layout()
fig_b.savefig(out_dir / "dark_umap_manifolds_b.png", dpi=300, bbox_inches="tight",
              facecolor=DARK_BG, edgecolor=DARK_BG)
fig_b.savefig(out_dir / "dark_umap_manifolds_b.pdf", bbox_inches="tight",
              facecolor=DARK_BG, edgecolor=DARK_BG)
plt.close(fig_b)
print("Saved: dark_umap_manifolds_b")

# Combined 3x3
fig_c, axes_c = plt.subplots(3, 3, figsize=(18, 16))
for i, (cat_key, cat_label) in enumerate(cat_order):
    row, col = divmod(i, 3)
    plot_category_panel_dark(axes_c[row, col], cat_key, cat_label, plot_df)
for i in range(len(cat_order), 9):
    row, col = divmod(i, 3)
    axes_c[row, col].set_visible(False)
plt.tight_layout()
fig_c.savefig(out_dir / "dark_umap_manifolds_combined.png", dpi=300, bbox_inches="tight",
              facecolor=DARK_BG, edgecolor=DARK_BG)
fig_c.savefig(out_dir / "dark_umap_manifolds_combined.pdf", bbox_inches="tight",
              facecolor=DARK_BG, edgecolor=DARK_BG)
plt.close(fig_c)
print("Saved: dark_umap_manifolds_combined")

print("Done!")
