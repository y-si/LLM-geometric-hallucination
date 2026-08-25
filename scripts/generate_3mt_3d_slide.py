"""
3MT Slide Prototype: 3D embedding space visualization.

Idea: Render the actual UMAP embeddings as a 3D point cloud (like the
word2vec visualization videos), colored by correct/hallucinated. The audience
sees "the inside of an AI" — a cloud of floating points where red clusters
reveal where fabrication happens.

Generates a static image with a carefully chosen camera angle that shows:
- Dense clusters of blue (correct) points
- Sparse/isolated red (hallucinated) points
- The 3D depth that makes it feel like a real space you could fly through
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

# Load Mixtral baselines
mixtral_results = []
with open("results/v5_baselines/mixtral-8x7b/no_prefix/judged_answers.jsonl") as f:
    for line in f:
        mixtral_results.append(json.loads(line))
mixtral_df = pd.DataFrame(mixtral_results)

# Merge — keep correct (0) and hallucinated (2)
df = mixtral_df[["id", "category", "judge_label"]].copy()
df = df[df["judge_label"].isin([0, 2])].copy()
df["is_hallucinated"] = (df["judge_label"] == 2).astype(int)

# Get embeddings for UMAP
all_ids = geo["id"].tolist()
valid_ids = [pid for pid in all_ids if pid in id_mapping]
all_indices = [id_mapping[pid] for pid in valid_ids]
all_embeddings = embeddings[all_indices]

# --- 3D UMAP ---
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
correct = plot_df[plot_df["is_hallucinated"] == 0]
hallucinated = plot_df[plot_df["is_hallucinated"] == 1]

print(f"Plotting: {len(correct)} correct, {len(hallucinated)} hallucinated")

# --- Style 1: Dark background (like the word2vec video) ---
fig = plt.figure(figsize=(16, 9), facecolor='#0a0a12')
ax = fig.add_subplot(111, projection='3d', facecolor='#0a0a12')

# Correct answers: blue, semi-transparent, smaller
ax.scatter(correct["x"], correct["y"], correct["z"],
           c='#4A90D9', alpha=0.35, s=18, edgecolors='none',
           label='Correct', depthshade=True, zorder=1)

# Hallucinated: red, more opaque, slightly larger with glow effect
ax.scatter(hallucinated["x"], hallucinated["y"], hallucinated["z"],
           c='#E74C3C', alpha=0.85, s=45, marker='x', linewidths=1.2,
           label='Hallucinated', depthshade=True, zorder=2)

# Camera angle — chosen to show depth and separation
ax.view_init(elev=20, azim=135)

# Remove all axes/grid for clean look
ax.set_axis_off()
ax.grid(False)
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False

# Title and labels (large, for reading from distance)
fig.text(0.5, 0.93, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=28, fontweight='bold',
         color='white', fontfamily='sans-serif')

fig.text(0.5, 0.88, "Every dot is a question. Where it lands determines whether the AI fabricates.",
         ha='center', va='center', fontsize=13, color='#999999',
         fontfamily='sans-serif')

# Legend in bottom-right
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#4A90D9',
           markersize=10, label='Correct answer', linestyle='None'),
    Line2D([0], [0], marker='X', color='w', markerfacecolor='#E74C3C',
           markeredgecolor='#E74C3C', markersize=10, label='Fabricated answer',
           linestyle='None'),
]
legend = ax.legend(handles=legend_elements, loc='lower right',
                   fontsize=11, frameon=False, labelcolor='white',
                   bbox_to_anchor=(1.0, 0.02))

# Footer
fig.text(0.5, 0.03,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#666677',
         fontfamily='sans-serif')

plt.tight_layout(pad=1.5)
plt.savefig("3mt_3d_dark.png", dpi=250, bbox_inches='tight',
            facecolor='#0a0a12', edgecolor='none')
print("Saved 3mt_3d_dark.png")


# --- Style 2: Light background (cleaner, more academic) ---
fig2 = plt.figure(figsize=(16, 9), facecolor='#FAFAFA')
ax2 = fig2.add_subplot(111, projection='3d', facecolor='#FAFAFA')

ax2.scatter(correct["x"], correct["y"], correct["z"],
            c='#4A90D9', alpha=0.3, s=18, edgecolors='none',
            depthshade=True, zorder=1)

ax2.scatter(hallucinated["x"], hallucinated["y"], hallucinated["z"],
            c='#E74C3C', alpha=0.85, s=50, marker='x', linewidths=1.2,
            depthshade=True, zorder=2)

ax2.view_init(elev=20, azim=135)
ax2.set_axis_off()
ax2.grid(False)
ax2.xaxis.pane.fill = False
ax2.yaxis.pane.fill = False
ax2.zaxis.pane.fill = False

fig2.text(0.5, 0.93, "The Geometry of AI Hallucination",
          ha='center', va='center', fontsize=28, fontweight='bold',
          color='#1A1A2E', fontfamily='sans-serif')

fig2.text(0.5, 0.88, "Every dot is a question. Where it lands determines whether the AI fabricates.",
          ha='center', va='center', fontsize=13, color='#666677',
          fontfamily='sans-serif')

legend_elements2 = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#4A90D9',
           markersize=10, label='Correct answer', linestyle='None'),
    Line2D([0], [0], marker='X', color='w', markerfacecolor='#E74C3C',
           markeredgecolor='#E74C3C', markersize=10, label='Fabricated answer',
           linestyle='None'),
]
legend2 = ax2.legend(handles=legend_elements2, loc='lower right',
                     fontsize=11, frameon=False, labelcolor='#333333',
                     bbox_to_anchor=(1.0, 0.02))

fig2.text(0.5, 0.03,
          "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
          ha='center', va='center', fontsize=9, color='#888899',
          fontfamily='sans-serif')

plt.tight_layout(pad=1.5)
plt.savefig("3mt_3d_light.png", dpi=250, bbox_inches='tight',
            facecolor='#FAFAFA', edgecolor='none')
print("Saved 3mt_3d_light.png")


# --- Style 3: Dark with region annotations ---
fig3 = plt.figure(figsize=(16, 9), facecolor='#0a0a12')
ax3 = fig3.add_subplot(111, projection='3d', facecolor='#0a0a12')

ax3.scatter(correct["x"], correct["y"], correct["z"],
            c='#4A90D9', alpha=0.35, s=18, edgecolors='none',
            depthshade=True, zorder=1)

ax3.scatter(hallucinated["x"], hallucinated["y"], hallucinated["z"],
            c='#E74C3C', alpha=0.85, s=45, marker='x', linewidths=1.2,
            depthshade=True, zorder=2)

ax3.view_init(elev=20, azim=135)
ax3.set_axis_off()
ax3.grid(False)
ax3.xaxis.pane.fill = False
ax3.yaxis.pane.fill = False
ax3.zaxis.pane.fill = False

# Add 2D text annotations pointing to dense/sparse regions
# We'll find the centroid of correct-heavy and hallucination-heavy regions
correct_centroid = correct[["x", "y", "z"]].mean()
hall_centroid = hallucinated[["x", "y", "z"]].mean()

ax3.text(correct_centroid["x"], correct_centroid["y"], correct_centroid["z"] + 1.5,
         "The AI knows\nthis well",
         fontsize=16, fontweight='bold', color='#7FBFFF',
         ha='center', va='bottom', zorder=10)

ax3.text(hall_centroid["x"], hall_centroid["y"], hall_centroid["z"] + 1.5,
         "The AI is\nguessing",
         fontsize=16, fontweight='bold', color='#FF8888',
         ha='center', va='bottom', zorder=10)

fig3.text(0.5, 0.93, "The Geometry of AI Hallucination",
          ha='center', va='center', fontsize=28, fontweight='bold',
          color='white', fontfamily='sans-serif')

fig3.text(0.5, 0.88, "Every dot is a question. Where it lands determines whether the AI fabricates.",
          ha='center', va='center', fontsize=13, color='#999999',
          fontfamily='sans-serif')

legend3 = ax3.legend(handles=legend_elements, loc='lower right',
                     fontsize=11, frameon=False, labelcolor='white',
                     bbox_to_anchor=(1.0, 0.02))

fig3.text(0.5, 0.03,
          "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
          ha='center', va='center', fontsize=9, color='#666677',
          fontfamily='sans-serif')

plt.tight_layout(pad=1.5)
plt.savefig("3mt_3d_annotated.png", dpi=250, bbox_inches='tight',
            facecolor='#0a0a12', edgecolor='none')
print("Saved 3mt_3d_annotated.png")

plt.close('all')
print("\nDone! Check the three outputs:")
print("  1. 3mt_3d_dark.png      — dark bg, clean (like word2vec video)")
print("  2. 3mt_3d_light.png     — light bg, more academic")
print("  3. 3mt_3d_annotated.png — dark bg with region labels")
