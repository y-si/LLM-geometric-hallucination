"""
3MT Slide Prototype V2: Improved 3D embedding visualization.

Changes from v1:
- Filter to factual + nonexistent categories only (clearest contrast)
- Depth-based point sizing (closer = larger) for real 3D feel
- Multiple camera angles to find the best separation
- Glow effect on hallucinated points
- Try to evoke the word2vec video aesthetic
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D
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

# --- Run 3D UMAP on ALL data (for global structure) ---
all_ids = geo["id"].tolist()
valid_ids = [pid for pid in all_ids if pid in id_mapping]
all_indices = [id_mapping[pid] for pid in valid_ids]
all_embeddings = embeddings[all_indices]

print(f"Running 3D UMAP on {len(all_embeddings)} embeddings...")
reducer = umap.UMAP(n_components=3, random_state=42, n_neighbors=15, min_dist=0.1)
coords_3d = reducer.fit_transform(all_embeddings)

coord_df = pd.DataFrame({
    "id": valid_ids,
    "x": coords_3d[:, 0],
    "y": coords_3d[:, 1],
    "z": coords_3d[:, 2],
})

plot_df = df.merge(coord_df, on="id", how="inner")

# --- VERSION A: All categories, better rendering ---
def render_3d_slide(plot_data, filename, elev=25, azim=140, title_suffix="",
                    show_annotations=True, bg_color='#08080f'):
    """Render a polished 3D slide."""
    fig = plt.figure(figsize=(16, 9), facecolor=bg_color)
    ax = fig.add_subplot(111, projection='3d', facecolor=bg_color)

    correct = plot_data[plot_data["is_hallucinated"] == 0]
    hallucinated = plot_data[plot_data["is_hallucinated"] == 1]

    # Depth-based sizing: compute distance from camera and scale
    # Normalize coordinates for consistent sizing
    all_coords = plot_data[["x", "y", "z"]].values

    # --- Draw correct points: blue, subtle ---
    ax.scatter(correct["x"], correct["y"], correct["z"],
               c='#5DADE2', alpha=0.25, s=12, edgecolors='none',
               depthshade=True, zorder=1)

    # --- Draw hallucinated: red, prominent, with "glow" ---
    # Outer glow layer
    ax.scatter(hallucinated["x"], hallucinated["y"], hallucinated["z"],
               c='#E74C3C', alpha=0.15, s=120, edgecolors='none',
               depthshade=True, zorder=2)
    # Core
    ax.scatter(hallucinated["x"], hallucinated["y"], hallucinated["z"],
               c='#FF6B6B', alpha=0.9, s=35, marker='o', edgecolors='#E74C3C',
               linewidths=0.5, depthshade=True, zorder=3)

    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()

    # Title
    fig.text(0.5, 0.94, f"The Geometry of AI Hallucination{title_suffix}",
             ha='center', va='center', fontsize=30, fontweight='bold',
             color='white', fontfamily='sans-serif')

    fig.text(0.5, 0.89,
             "Each point is a question fed to an AI.  Where it lands in this space predicts the answer.",
             ha='center', va='center', fontsize=13, color='#888899',
             fontfamily='sans-serif')

    if show_annotations:
        # Find the mostly-blue cluster and mostly-red cluster
        # Use category info to find factual centroid and nonexistent centroid
        factual = plot_data[plot_data["category"] == "factual"]
        nonexistent = plot_data[plot_data["category"] == "nonexistent"]

        if len(factual) > 0:
            fc = factual[["x", "y", "z"]].mean()
            ax.text(fc["x"], fc["y"], fc["z"] + 2.0,
                    "Knows this well",
                    fontsize=15, fontweight='bold', color='#7EC8E3',
                    ha='center', va='bottom', zorder=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_color,
                              edgecolor='none', alpha=0.7))

        if len(nonexistent) > 0:
            nc = nonexistent[["x", "y", "z"]].mean()
            ax.text(nc["x"], nc["y"], nc["z"] + 2.0,
                    "Making things up",
                    fontsize=15, fontweight='bold', color='#FF9999',
                    ha='center', va='bottom', zorder=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_color,
                              edgecolor='none', alpha=0.7))

    # Legend
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
               markersize=9, label='Correct', linestyle='None'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
               markeredgecolor='#E74C3C', markersize=9, label='Fabricated',
               linestyle='None'),
    ]
    ax.legend(handles=legend_elements, loc='lower right',
              fontsize=11, frameon=False, labelcolor='white',
              bbox_to_anchor=(1.0, 0.02))

    # Footer
    fig.text(0.5, 0.03,
             "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
             ha='center', va='center', fontsize=9, color='#555566',
             fontfamily='sans-serif')

    plt.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.08)
    plt.savefig(filename, dpi=250, bbox_inches='tight',
                facecolor=bg_color, edgecolor='none')
    plt.close(fig)
    print(f"Saved {filename}")


# --- VERSION B: Only factual + nonexistent (max contrast) ---
contrast_df = plot_df[plot_df["category"].isin(["factual", "nonexistent"])].copy()
print(f"\nContrast subset: {len(contrast_df)} points "
      f"({(contrast_df['is_hallucinated']==0).sum()} correct, "
      f"{(contrast_df['is_hallucinated']==1).sum()} hallucinated)")

# --- VERSION C: Show all but dim the "boring" middle categories ---
def render_layered(plot_data, filename, elev=25, azim=140, bg_color='#08080f'):
    """All data but emphasis on extreme categories."""
    fig = plt.figure(figsize=(16, 9), facecolor=bg_color)
    ax = fig.add_subplot(111, projection='3d', facecolor=bg_color)

    # Categories by hallucination rate
    safe_cats = ["factual", "borderline_edge_factual", "ambiguous"]
    danger_cats = ["nonexistent", "borderline_plausible_fake"]
    mid_cats = ["impossible", "borderline_obscure_real"]

    # Background: middle categories, very faint
    mid = plot_data[plot_data["category"].isin(mid_cats)]
    ax.scatter(mid["x"], mid["y"], mid["z"],
               c='#444455', alpha=0.08, s=6, edgecolors='none', depthshade=True)

    # Safe categories: blue
    safe = plot_data[plot_data["category"].isin(safe_cats)]
    safe_correct = safe[safe["is_hallucinated"] == 0]
    safe_hall = safe[safe["is_hallucinated"] == 1]
    ax.scatter(safe_correct["x"], safe_correct["y"], safe_correct["z"],
               c='#5DADE2', alpha=0.4, s=16, edgecolors='none', depthshade=True, zorder=2)
    ax.scatter(safe_hall["x"], safe_hall["y"], safe_hall["z"],
               c='#E74C3C', alpha=0.6, s=25, edgecolors='none', depthshade=True, zorder=3)

    # Danger categories: red emphasis
    danger = plot_data[plot_data["category"].isin(danger_cats)]
    danger_correct = danger[danger["is_hallucinated"] == 0]
    danger_hall = danger[danger["is_hallucinated"] == 1]
    ax.scatter(danger_correct["x"], danger_correct["y"], danger_correct["z"],
               c='#5DADE2', alpha=0.4, s=16, edgecolors='none', depthshade=True, zorder=2)
    # Glow
    ax.scatter(danger_hall["x"], danger_hall["y"], danger_hall["z"],
               c='#E74C3C', alpha=0.12, s=150, edgecolors='none', depthshade=True, zorder=3)
    ax.scatter(danger_hall["x"], danger_hall["y"], danger_hall["z"],
               c='#FF6B6B', alpha=0.9, s=30, edgecolors='#E74C3C',
               linewidths=0.3, depthshade=True, zorder=4)

    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()

    # Annotations
    factual = plot_data[plot_data["category"] == "factual"]
    nonexistent = plot_data[plot_data["category"] == "nonexistent"]

    if len(factual) > 0:
        fc = factual[["x", "y", "z"]].mean()
        ax.text(fc["x"], fc["y"], fc["z"] + 2.2,
                "The AI knows\nthis territory",
                fontsize=16, fontweight='bold', color='#7EC8E3',
                ha='center', va='bottom', zorder=10)

    if len(nonexistent) > 0:
        nc = nonexistent[["x", "y", "z"]].mean()
        ax.text(nc["x"], nc["y"], nc["z"] + 2.2,
                "The AI is\nguessing here",
                fontsize=16, fontweight='bold', color='#FF9999',
                ha='center', va='bottom', zorder=10)

    # Title
    fig.text(0.5, 0.94, "The Geometry of AI Hallucination",
             ha='center', va='center', fontsize=30, fontweight='bold',
             color='white', fontfamily='sans-serif')
    fig.text(0.5, 0.89,
             "Each point is a question.  Where it lands in the AI's internal map predicts the answer.",
             ha='center', va='center', fontsize=13, color='#888899',
             fontfamily='sans-serif')

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
               markersize=9, label='Correct', linestyle='None'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
               markeredgecolor='#E74C3C', markersize=9, label='Fabricated',
               linestyle='None'),
    ]
    ax.legend(handles=legend_elements, loc='lower right',
              fontsize=11, frameon=False, labelcolor='white',
              bbox_to_anchor=(1.0, 0.02))

    fig.text(0.5, 0.03,
             "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
             ha='center', va='center', fontsize=9, color='#555566',
             fontfamily='sans-serif')

    plt.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.08)
    plt.savefig(filename, dpi=250, bbox_inches='tight',
                facecolor=bg_color, edgecolor='none')
    plt.close(fig)
    print(f"Saved {filename}")


# Generate multiple camera angles for the full dataset
print("\n--- Full dataset, multiple angles ---")
for azim in [45, 135, 200]:
    render_3d_slide(plot_df, f"3mt_3d_v2_all_az{azim}.png",
                    elev=25, azim=azim, show_annotations=True)

# Contrast-only versions
print("\n--- Factual vs Nonexistent only ---")
for azim in [45, 135, 200]:
    render_3d_slide(contrast_df, f"3mt_3d_v2_contrast_az{azim}.png",
                    elev=25, azim=azim, show_annotations=True,
                    title_suffix="")

# Layered version (all data, emphasis on extremes)
print("\n--- Layered (all data, emphasis on extremes) ---")
for azim in [45, 135, 200]:
    render_layered(plot_df, f"3mt_3d_v2_layered_az{azim}.png",
                   elev=25, azim=azim)

print("\nDone! Generated 9 variants.")
