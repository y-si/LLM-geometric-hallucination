"""Generate thesis-quality category × prefix hallucination heatmap for Chapter 6."""

import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Style (matching existing thesis figures) ─────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Read data
data = {}
with open(PROJECT_ROOT / 'results' / 'v5_prefixes' / 'analysis' / 'v5_category_metrics.csv') as f:
    for row in csv.DictReader(f):
        key = (row['model_name'], row['prefix_key'], row['category'])
        data[key] = float(row['hallucination_rate']) * 100

# Configuration
categories = [
    ('ambiguous', 'Ambiguous'),
    ('borderline_edge_factual', 'Edge\nfactual'),
    ('borderline_obscure_real', 'Obscure\nreal'),
    ('borderline_plausible_fake', 'Plausible\nfake'),
    ('factual', 'Factual'),
    ('impossible', 'Impossible'),
    ('nonexistent', 'Nonexistent'),
]

prefixes = [
    ('no_prefix', 'Baseline'),
    ('epistemic_humility', 'Epist. Humility'),
    ('fact_grounded', 'Fact-Grounded'),
    ('entity_aware', 'Entity-Aware'),
    ('structured_caution', 'Struct. Caution'),
]

models = [
    ('mixtral-8x7b', 'Mixtral 8x7B'),
    ('llama-4-maverick-17b', 'Llama 4 Maverick'),
]

# Build matrices
fig, axes = plt.subplots(1, 2, figsize=(18, 6), sharey=True,
                         gridspec_kw={'wspace': 0.15})

# Custom colormap: green (low) -> yellow (mid) -> red (high)
cmap = mcolors.LinearSegmentedColormap.from_list(
    'halluc', ['#1a9641', '#a6d96a', '#ffffbf', '#fdae61', '#d73027'], N=256
)

for ax_idx, (model_key, model_name) in enumerate(models):
    ax = axes[ax_idx]

    matrix = np.zeros((len(prefixes), len(categories)))
    for i, (pkey, _) in enumerate(prefixes):
        for j, (ckey, _) in enumerate(categories):
            matrix[i, j] = data.get((model_key, pkey, ckey), 0)

    # Plot
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=45)

    # Annotate cells
    for i in range(len(prefixes)):
        for j in range(len(categories)):
            val = matrix[i, j]
            # White text on dark/red cells, black on light/green
            color = 'white' if val > 35 else 'black'
            fontweight = 'bold' if i == 0 else 'normal'  # Bold baseline
            text = f'{val:.1f}'
            ax.text(j, i, text, ha='center', va='center', fontsize=11,
                    color=color, fontweight=fontweight)

    # Labels
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels([label for _, label in categories], fontsize=10, ha='center')
    ax.set_yticks(range(len(prefixes)))
    ax.set_yticklabels([label for _, label in prefixes], fontsize=11)

    ax.set_title(model_name, fontsize=13, fontweight='bold', pad=10)

    # Add horizontal line separating baseline from prefixes
    ax.axhline(y=0.5, color='white', linewidth=2)

# Colorbar — position manually to avoid overlap
cbar_ax = fig.add_axes([0.93, 0.2, 0.015, 0.6])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label('Hallucination rate (%)', fontsize=12)

plt.subplots_adjust(left=0.09, right=0.9, top=0.88, bottom=0.18)

# Save
out_path = PROJECT_ROOT / 'thesis' / 'Dissertate-Harvard-LaTeX' / 'figures' / 'ch6_category_heatmap.png'
plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f'Saved to {out_path}')

# Also save to results for reference
plt.savefig(PROJECT_ROOT / 'results' / 'v5_prefixes' / 'analysis' / 'ch6_category_heatmap_thesis.png',
            dpi=300, bbox_inches='tight', facecolor='white')
print('Also saved to results/v5_prefixes/analysis/')
