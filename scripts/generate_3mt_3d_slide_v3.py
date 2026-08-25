"""
3MT Slide Prototype V3: Final polished versions.

Two approaches:
1. Matplotlib: polished layered view with offset labels
2. Plotly: proper 3D rendering exported as static image
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

# =====================================================
# APPROACH 1: Polished matplotlib with 2D projection
# (fake the 3D by using 2D UMAP + size/alpha variation)
# =====================================================
print("\n--- Approach 1: Styled 2D with depth cues ---")

# Also run 2D UMAP for a cleaner base
reducer_2d = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords_2d = reducer_2d.fit_transform(all_embeddings)

coord_2d_df = pd.DataFrame({
    "id": valid_ids,
    "x": coords_2d[:, 0],
    "y": coords_2d[:, 1],
})

plot_2d = df.merge(coord_2d_df, on="id", how="inner")

# Category groupings
safe_cats = ["factual", "borderline_edge_factual", "ambiguous"]
danger_cats = ["nonexistent", "borderline_plausible_fake"]

bg = '#08080f'
fig, ax = plt.subplots(figsize=(16, 9), facecolor=bg)
ax.set_facecolor(bg)

correct = plot_2d[plot_2d["is_hallucinated"] == 0]
hallucinated = plot_2d[plot_2d["is_hallucinated"] == 1]

# Add subtle random size variation for depth illusion
np.random.seed(42)
correct_sizes = np.random.uniform(8, 25, len(correct))
hall_sizes = np.random.uniform(20, 50, len(hallucinated))

# Correct: blue, semi-transparent
ax.scatter(correct["x"], correct["y"],
           c='#5DADE2', alpha=0.3, s=correct_sizes,
           edgecolors='none', zorder=1)

# Hallucinated: glow layer
ax.scatter(hallucinated["x"], hallucinated["y"],
           c='#E74C3C', alpha=0.08, s=hall_sizes * 8,
           edgecolors='none', zorder=2)
# Core
ax.scatter(hallucinated["x"], hallucinated["y"],
           c='#FF6B6B', alpha=0.85, s=hall_sizes,
           edgecolors='#E74C3C', linewidths=0.3, zorder=3)

# Find label positions — use category centroids but offset into clear space
factual = plot_2d[plot_2d["category"] == "factual"]
nonexistent = plot_2d[plot_2d["category"] == "nonexistent"]

if len(factual) > 0 and len(nonexistent) > 0:
    fc = factual[["x", "y"]].mean()
    nc = nonexistent[["x", "y"]].mean()

    # Get plot bounds
    xmin, xmax = plot_2d["x"].min(), plot_2d["x"].max()
    ymin, ymax = plot_2d["y"].min(), plot_2d["y"].max()
    xpad = (xmax - xmin) * 0.15
    ypad = (ymax - ymin) * 0.15

    # Place labels away from data, with arrows
    # Factual label: offset to the left/above
    fx_label = fc["x"] - xpad * 1.5
    fy_label = fc["y"] + ypad * 2.0

    ax.annotate("The AI knows\nthis well",
                xy=(fc["x"], fc["y"]),
                xytext=(fx_label, fy_label),
                fontsize=18, fontweight='bold', color='#7EC8E3',
                ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#7EC8E3',
                                lw=1.5, connectionstyle='arc3,rad=0.2'),
                fontfamily='sans-serif')

    # Nonexistent label: offset to the right/above
    nx_label = nc["x"] + xpad * 1.5
    ny_label = nc["y"] + ypad * 2.0

    ax.annotate("The AI is\nmaking things up",
                xy=(nc["x"], nc["y"]),
                xytext=(nx_label, ny_label),
                fontsize=18, fontweight='bold', color='#FF9999',
                ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#FF9999',
                                lw=1.5, connectionstyle='arc3,rad=-0.2'),
                fontfamily='sans-serif')

ax.set_xlim(xmin - xpad, xmax + xpad * 2)
ax.set_ylim(ymin - ypad, ymax + ypad * 3)
ax.axis('off')

# Title
fig.text(0.5, 0.95, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=32, fontweight='bold',
         color='white', fontfamily='sans-serif')
fig.text(0.5, 0.91,
         "Each point is a question.  Where it lands in the AI's internal map predicts the answer.",
         ha='center', va='center', fontsize=12.5, color='#888899',
         fontfamily='sans-serif')

# Legend
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
           markersize=9, label='Correct', linestyle='None'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
           markeredgecolor='#E74C3C', markersize=9, label='Fabricated',
           linestyle='None'),
]
ax.legend(handles=legend_elements, loc='lower right',
          fontsize=12, frameon=False, labelcolor='white')

# Footer
fig.text(0.5, 0.02,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#555566',
         fontfamily='sans-serif')

plt.tight_layout(pad=1.0)
plt.savefig("3mt_v3_styled2d.png", dpi=250, bbox_inches='tight',
            facecolor=bg, edgecolor='none')
plt.close()
print("Saved 3mt_v3_styled2d.png")


# =====================================================
# APPROACH 2: Plotly 3D (proper rendering)
# =====================================================
print("\n--- Approach 2: Plotly 3D ---")
try:
    import plotly.graph_objects as go

    correct_3d = plot_df[plot_df["is_hallucinated"] == 0]
    hall_3d = plot_df[plot_df["is_hallucinated"] == 1]

    fig3d = go.Figure()

    # Correct points
    fig3d.add_trace(go.Scatter3d(
        x=correct_3d["x"], y=correct_3d["y"], z=correct_3d["z"],
        mode='markers',
        marker=dict(size=2.5, color='#5DADE2', opacity=0.3),
        name='Correct',
    ))

    # Hallucinated points
    fig3d.add_trace(go.Scatter3d(
        x=hall_3d["x"], y=hall_3d["y"], z=hall_3d["z"],
        mode='markers',
        marker=dict(size=4.5, color='#FF6B6B', opacity=0.85,
                    line=dict(color='#E74C3C', width=0.5)),
        name='Fabricated',
    ))

    fig3d.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor='#08080f',
            camera=dict(
                eye=dict(x=1.5, y=0.8, z=0.6),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        paper_bgcolor='#08080f',
        plot_bgcolor='#08080f',
        title=dict(
            text="<b>The Geometry of AI Hallucination</b><br>"
                 "<span style='font-size:13px;color:#888899'>"
                 "Each point is a question. Where it lands predicts the answer.</span>",
            font=dict(size=24, color='white', family='Helvetica Neue'),
            x=0.5,
        ),
        legend=dict(
            font=dict(color='white', size=13),
            bgcolor='rgba(0,0,0,0)',
            x=0.85, y=0.15,
        ),
        margin=dict(l=0, r=0, t=80, b=40),
        width=1600,
        height=900,
        annotations=[
            dict(
                text="Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
                xref="paper", yref="paper",
                x=0.5, y=0.01,
                showarrow=False,
                font=dict(size=10, color='#555566'),
            )
        ],
    )

    # Save as static image
    fig3d.write_image("3mt_v3_plotly3d.png", scale=2)
    print("Saved 3mt_v3_plotly3d.png")

    # Also save interactive HTML for exploration
    fig3d.write_html("3mt_v3_plotly3d.html")
    print("Saved 3mt_v3_plotly3d.html (interactive — open in browser to explore angles)")

except ImportError:
    print("plotly not installed — skipping 3D plotly render")
    print("Install with: pip install plotly kaleido")
except Exception as e:
    print(f"Plotly export failed: {e}")
    print("Try: pip install kaleido")


# =====================================================
# APPROACH 3: Pure 2D, maximum clarity, "constellation" style
# =====================================================
print("\n--- Approach 3: Constellation style ---")

fig, ax = plt.subplots(figsize=(16, 9), facecolor='#06060c')
ax.set_facecolor('#06060c')

# All correct points as very subtle background "stars"
ax.scatter(correct["x"], correct["y"],
           c='#3A7BD5', alpha=0.15, s=5, edgecolors='none', zorder=1)

# Correct in safe categories: brighter blue
safe_correct = correct[correct["category"].isin(safe_cats)]
ax.scatter(safe_correct["x"], safe_correct["y"],
           c='#5DADE2', alpha=0.5, s=20, edgecolors='none', zorder=2)

# Hallucinated in danger categories: bright red with glow
danger_hall = hallucinated[hallucinated["category"].isin(danger_cats)]
# Multiple glow layers
for glow_size, glow_alpha in [(300, 0.03), (150, 0.06), (80, 0.1)]:
    ax.scatter(danger_hall["x"], danger_hall["y"],
               c='#E74C3C', alpha=glow_alpha, s=glow_size,
               edgecolors='none', zorder=3)
ax.scatter(danger_hall["x"], danger_hall["y"],
           c='#FF6B6B', alpha=0.9, s=30,
           edgecolors='#FF4444', linewidths=0.5, zorder=4)

# Other hallucinated (not in danger cats): dimmer red
other_hall = hallucinated[~hallucinated["category"].isin(danger_cats)]
ax.scatter(other_hall["x"], other_hall["y"],
           c='#E74C3C', alpha=0.4, s=15, edgecolors='none', zorder=3)

# Labels with arrows
if len(factual) > 0 and len(nonexistent) > 0:
    fc = safe_correct[["x", "y"]].mean()
    nc = danger_hall[["x", "y"]].mean()

    xmin, xmax = plot_2d["x"].min(), plot_2d["x"].max()
    ymin, ymax = plot_2d["y"].min(), plot_2d["y"].max()
    xpad = (xmax - xmin) * 0.15
    ypad = (ymax - ymin) * 0.15

    # Blue label
    ax.annotate("Dense neighborhood\nThe AI knows this well",
                xy=(fc["x"], fc["y"]),
                xytext=(fc["x"] - xpad * 2, fc["y"] + ypad * 2.5),
                fontsize=15, fontweight='bold', color='#7EC8E3',
                ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#7EC8E344',
                                lw=2, connectionstyle='arc3,rad=0.15'),
                fontfamily='sans-serif')

    # Red label
    ax.annotate("Sparse neighborhood\nThe AI is guessing",
                xy=(nc["x"], nc["y"]),
                xytext=(nc["x"] + xpad * 2, nc["y"] + ypad * 2.5),
                fontsize=15, fontweight='bold', color='#FF9999',
                ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#FF999944',
                                lw=2, connectionstyle='arc3,rad=-0.15'),
                fontfamily='sans-serif')

ax.set_xlim(xmin - xpad * 2.5, xmax + xpad * 3)
ax.set_ylim(ymin - ypad, ymax + ypad * 4)
ax.axis('off')

fig.text(0.5, 0.96, "The Geometry of AI Hallucination",
         ha='center', va='center', fontsize=32, fontweight='bold',
         color='white', fontfamily='sans-serif')
fig.text(0.5, 0.925,
         "2,364 questions mapped in the AI's internal space  —  each dot is one question",
         ha='center', va='center', fontsize=12, color='#666677',
         fontfamily='sans-serif')

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#5DADE2',
           markersize=9, label='Correct', linestyle='None'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B',
           markeredgecolor='#E74C3C', markersize=9, label='Fabricated',
           linestyle='None'),
]
ax.legend(handles=legend_elements, loc='lower right',
          fontsize=12, frameon=False, labelcolor='white')

fig.text(0.5, 0.02,
         "Sein Coray  |  Computer Science  |  Advisor: Boaz Barak",
         ha='center', va='center', fontsize=9, color='#444455',
         fontfamily='sans-serif')

plt.tight_layout(pad=0.5)
plt.savefig("3mt_v3_constellation.png", dpi=250, bbox_inches='tight',
            facecolor='#06060c', edgecolor='none')
plt.close()
print("Saved 3mt_v3_constellation.png")

print("\nDone! Three approaches:")
print("  1. 3mt_v3_styled2d.png     — 2D UMAP with glow + arrows")
print("  2. 3mt_v3_plotly3d.png     — proper 3D rendering")
print("     3mt_v3_plotly3d.html    — interactive (explore camera angles)")
print("  3. 3mt_v3_constellation.png — 'constellation' style, max drama")
