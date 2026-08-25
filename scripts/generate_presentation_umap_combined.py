"""Dark-mode single UMAP plot with all categories colored, for presentation."""

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

# ── Dark theme ──
DARK_BG = "#1a1a1a"
AXES_BG = "#2d2d2d"
TEXT_COLOR = "#ffffff"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 12,
    "figure.facecolor": DARK_BG,
    "axes.facecolor": AXES_BG,
    "axes.edgecolor": "#555555",
    "text.color": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "legend.facecolor": "#333333",
    "legend.edgecolor": "#555555",
    "legend.labelcolor": TEXT_COLOR,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

# Category colors — bright for dark background
CAT_COLORS = {
    "ambiguous": "#5bc0eb",          # cyan
    "borderline_edge_factual": "#00e5ff",  # bright teal
    "factual": "#2ecc71",            # green
    "impossible": "#ff9f43",         # orange
    "borderline_obscure_real": "#ff6bcb",  # pink
    "nonexistent": "#b19cd9",        # lavender/purple
    "borderline_plausible_fake": "#ff6b6b",  # red
}

CAT_LABELS = {
    "ambiguous": "Ambiguous",
    "borderline_edge_factual": "Edge Factual",
    "factual": "Factual",
    "impossible": "Impossible",
    "borderline_obscure_real": "Obscure Real",
    "nonexistent": "Nonexistent",
    "borderline_plausible_fake": "Plausible Fake",
}

# ── Load data ──
embeddings = np.load("data/processed/v5_question_embeddings.npy")
with open("data/processed/v5_embedding_id_mapping.json") as f:
    id_mapping = json.load(f)

geo = pd.read_csv("data/processed/v5_geometry_features.csv")

# Load Mixtral baselines for hallucination rates
mixtral_results = []
with open("results/v5_baselines/mixtral-8x7b/no_prefix/judged_answers.jsonl") as f:
    for line in f:
        mixtral_results.append(json.loads(line))
mixtral_df = pd.DataFrame(mixtral_results)

# Compute per-category hallucination rates
cat_rates = {}
for cat in CAT_LABELS:
    cat_data = mixtral_df[mixtral_df["category"] == cat]
    hall = (cat_data["judge_label"] == 2).sum()
    total = len(cat_data[cat_data["judge_label"].isin([0, 2])])
    if total > 0:
        cat_rates[cat] = hall / total * 100

# Run UMAP
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

# Merge with category info
cat_df = geo[["id", "category"]].copy()
plot_df = cat_df.merge(coord_df, on="id", how="inner")
print(f"Plotting {len(plot_df)} prompts")

# ── Plot ──
fig, ax = plt.subplots(figsize=(10, 7))

# Plot order: low hallucination rate first (background), high last (foreground)
sorted_cats = sorted(CAT_LABELS.keys(), key=lambda c: cat_rates.get(c, 0))

for cat in sorted_cats:
    cat_data = plot_df[plot_df["category"] == cat]
    rate = cat_rates.get(cat, 0)
    label = f"{CAT_LABELS[cat]} ({rate:.1f}%)"
    ax.scatter(cat_data["umap1"], cat_data["umap2"],
               c=CAT_COLORS[cat], s=35, alpha=0.7, label=label, edgecolors="none")

ax.set_xlabel("UMAP 1", fontsize=13)
ax.set_ylabel("UMAP 2", fontsize=13)
ax.legend(loc="upper right", fontsize=9, framealpha=0.8, title="Category (hall. rate)",
          title_fontsize=9)
ax.grid(alpha=0.1, color="#444444")

plt.tight_layout()

out_dir = Path("thesis/Dissertate-Harvard-LaTeX/figures/presentation")
fig.savefig(out_dir / "dark_umap_single_combined.png", dpi=300,
            bbox_inches="tight", facecolor=DARK_BG, edgecolor=DARK_BG)
fig.savefig(out_dir / "dark_umap_single_combined.pdf",
            bbox_inches="tight", facecolor=DARK_BG, edgecolor=DARK_BG)
plt.close(fig)
print("Saved: dark_umap_single_combined.png/pdf")
