"""
Generate the "Knowledge Landscape" conceptual diagram for the 3MT slide.
V2: More dramatic contrast, stronger terrain, clearer dot distribution.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

np.random.seed(42)

fig, ax = plt.subplots(1, 1, figsize=(14, 7))

# ── Create the terrain/density field ──
x_grid = np.linspace(0, 10, 600)
y_grid = np.linspace(0, 5, 300)
X, Y = np.meshgrid(x_grid, y_grid)

Z = np.zeros_like(X)

# Dense region (left) — big overlapping knowledge clusters
dense_centers = [
    (2.2, 2.5, 1.4, 1.2, 5.0),
    (3.2, 3.0, 1.0, 0.9, 6.0),
    (2.5, 1.8, 1.1, 1.0, 4.5),
    (3.5, 2.2, 1.0, 1.2, 4.0),
    (1.8, 3.5, 0.8, 0.7, 3.0),
    (3.8, 3.5, 0.7, 0.9, 2.5),
    (2.8, 1.2, 0.9, 0.7, 3.0),
    (1.5, 2.0, 0.6, 0.8, 2.5),
    (4.2, 2.8, 0.6, 0.7, 2.0),
]

# Sparse region — very weak, isolated
sparse_centers = [
    (7.8, 1.8, 0.35, 0.35, 0.5),
    (8.8, 3.2, 0.3, 0.3, 0.3),
]

for cx, cy, sx, sy, amp in dense_centers + sparse_centers:
    Z += amp * np.exp(-((X - cx)**2 / (2 * sx**2) + (Y - cy)**2 / (2 * sy**2)))

Z = gaussian_filter(Z, sigma=6)

# ── Colormap: rich teal (dense) → almost white (sparse) ──
colors_terrain = [
    (0.95, 0.95, 0.97, 1.0),    # near-white (empty)
    (0.88, 0.91, 0.95, 1.0),    # very light blue
    (0.72, 0.82, 0.90, 1.0),    # light steel
    (0.50, 0.72, 0.82, 1.0),    # medium teal
    (0.30, 0.60, 0.72, 1.0),    # teal
    (0.18, 0.50, 0.65, 1.0),    # deep teal
    (0.12, 0.42, 0.58, 1.0),    # rich teal
    (0.08, 0.35, 0.52, 1.0),    # deepest
]
cmap_terrain = LinearSegmentedColormap.from_list('terrain_knowledge', colors_terrain, N=256)

# Plot terrain
ax.contourf(X, Y, Z, levels=60, cmap=cmap_terrain, alpha=0.95)

# Subtle contour lines
contour_levels = np.linspace(Z.max() * 0.1, Z.max() * 0.8, 6)
ax.contour(X, Y, Z, levels=contour_levels, colors='white', alpha=0.2, linewidths=0.6)

# ── Place dots ──
# Dense region: mostly green, very few red
dense_dots = [
    # (x, y, correct)
    (1.5, 2.8, True), (1.8, 1.6, True), (2.0, 3.5, True),
    (2.2, 2.0, True), (2.5, 3.2, True), (2.8, 1.5, True),
    (2.3, 2.8, True), (3.0, 3.4, True), (3.2, 2.0, True),
    (3.5, 2.8, True), (3.0, 1.8, True), (3.8, 3.2, True),
    (2.6, 2.3, True), (4.0, 2.5, True), (1.6, 3.2, True),
    (3.3, 2.5, True),
    (2.0, 2.3, False),  # rare miss in dense region
]

# Transition: mixed
trans_dots = [
    (5.2, 2.8, True), (5.5, 1.8, True),
    (5.8, 3.2, False), (5.3, 2.2, False),
]

# Sparse region: mostly red, rare green
sparse_dots = [
    (7.2, 3.5, False), (7.5, 1.5, False), (7.8, 2.8, False),
    (8.2, 3.8, False), (8.5, 2.0, False), (8.8, 3.2, False),
    (8.0, 1.2, False), (9.0, 2.5, False),
    (7.8, 3.8, True),  # rare hit in sparse region
]

all_dots = dense_dots + trans_dots + sparse_dots

# Draw dots
for x, y, correct in all_dots:
    if correct:
        ax.plot(x, y, 'o', color='#27AE60', markersize=11, markeredgecolor='white',
                markeredgewidth=1.8, zorder=5, alpha=0.95)
    else:
        ax.plot(x, y, 'X', color='#E74C3C', markersize=13, markeredgecolor='white',
                markeredgewidth=1.2, zorder=5, alpha=0.95)

# ── Labels ──
ax.text(2.8, 4.7, 'The AI knows this well', fontsize=18, fontweight='bold',
        color='#0D3B4F', ha='center', va='center', fontfamily='sans-serif')

ax.text(8.0, 4.7, 'The AI is guessing', fontsize=18, fontweight='bold',
        color='#8B8B9E', ha='center', va='center', fontfamily='sans-serif')

# ── Legend (bottom-right, subtle) ──
legend_x, legend_y = 8.8, 0.55
ax.plot(legend_x - 0.15, legend_y + 0.15, 'o', color='#27AE60', markersize=7,
        markeredgecolor='white', markeredgewidth=1.2, zorder=5)
ax.text(legend_x + 0.05, legend_y + 0.15, 'Correct', fontsize=9,
        color='#555566', va='center', fontfamily='sans-serif')
ax.plot(legend_x + 1.0 - 0.15, legend_y + 0.15, 'X', color='#E74C3C', markersize=8,
        markeredgecolor='white', markeredgewidth=0.8, zorder=5)
ax.text(legend_x + 1.2, legend_y + 0.15, 'Fabricated', fontsize=9,
        color='#555566', va='center', fontfamily='sans-serif')

# ── Clean up ──
ax.set_xlim(0.3, 9.7)
ax.set_ylim(0.2, 5.0)
ax.axis('off')

fig.patch.set_facecolor('#FAFAFA')

plt.tight_layout(pad=0.3)
plt.savefig('3mt_landscape.png', dpi=250, bbox_inches='tight',
            facecolor='#FAFAFA', edgecolor='none')
plt.savefig('3mt_landscape.pdf', bbox_inches='tight',
            facecolor='#FAFAFA', edgecolor='none')
print("Saved 3mt_landscape.png and .pdf")
