"""Generate poster-scale figures (36x48 inch poster, ~2x font sizes).

Regenerates the three hero figures for the poster at larger font sizes
and dimensions so they remain legible when printed at poster scale.

Usage:
    python3 scripts/generate_poster_figures.py

Output:
    thesis/figures/poster_*.png
"""

import json
import csv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "thesis" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Poster-scale style (roughly 2x thesis font sizes) ────────────────────

POSTER_STYLE = {
    "font.family": "serif",
    "font.size": 22,
    "axes.titlesize": 26,
    "axes.labelsize": 24,
    "xtick.labelsize": 20,
    "ytick.labelsize": 20,
    "legend.fontsize": 18,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
}

COLORS = {
    "correct": "#accd91",
    "hallucinated": "#bd6565",
    "baseline": "#e74c3c",
    "best_prefix": "#3498db",
    "finetuned": "#2ecc71",
    "oracle": "#95a5a6",
}


# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 1: Within-category density box plot (Phase 1 hero)
# ═══════════════════════════════════════════════════════════════════════════

def poster_density_boxplot():
    """Within-category density: hallucinated vs correct in nonexistent category."""
    plt.rcParams.update(POSTER_STYLE)

    geo_df = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "v5_geometry_features.csv")

    models = {
        "mixtral-8x7b": "Mixtral 8x7B",
        "llama-4-maverick-17b": "Llama 4 Maverick",
    }

    model_data = {}
    for model_id, model_label in models.items():
        fpath = (PROJECT_ROOT / "results" / "v5_baselines" / model_id /
                 "no_prefix" / "judged_answers.jsonl")
        records = []
        with open(fpath) as f:
            for line in f:
                obj = json.loads(line)
                records.append({
                    "id": obj["id"],
                    "category": obj["category"],
                    "judge_label": obj["judge_label"],
                })
        labels_df = pd.DataFrame(records)
        merged = geo_df.merge(labels_df[["id", "judge_label"]], on="id", how="inner")
        nonexistent = merged[merged["category"] == "nonexistent"].copy()
        hall = nonexistent[nonexistent["judge_label"] == 2]["density"].values
        correct = nonexistent[nonexistent["judge_label"] == 0]["density"].values
        model_data[model_id] = {
            "label": model_label,
            "hall": hall,
            "correct": correct,
            "n_hall": len(hall),
            "n_correct": len(correct),
        }

    fig, axes = plt.subplots(1, 2, figsize=(16, 8), sharey=True)

    p_values = {
        "mixtral-8x7b": "$p = 5.7 \\times 10^{-7}$",
        "llama-4-maverick-17b": "$p = 3.4 \\times 10^{-5}$",
    }

    for ax, (model_id, data) in zip(axes, model_data.items()):
        bp = ax.boxplot(
            [data["correct"], data["hall"]],
            labels=[
                f"Correct\n(n={data['n_correct']})",
                f"Hallucinated\n(n={data['n_hall']})",
            ],
            patch_artist=True,
            widths=0.5,
            medianprops=dict(color="black", linewidth=2.5),
            whiskerprops=dict(linewidth=1.5),
            capprops=dict(linewidth=1.5),
            flierprops=dict(marker="o", markersize=6, alpha=0.5),
        )

        colors = [COLORS["correct"], COLORS["hallucinated"]]
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
            patch.set_edgecolor("black")
            patch.set_linewidth(1.0)

        ax.set_title(data["label"], fontweight="bold", fontsize=28)
        ax.set_ylabel("Density" if ax == axes[0] else "", fontsize=24)

        # Add mean values on the plot
        for i, (vals, label) in enumerate([(data["correct"], "correct"), (data["hall"], "hall")]):
            mean_val = np.mean(vals)
            ax.text(i + 1, mean_val, f"{mean_val:.2f}", ha="center", va="bottom",
                    fontsize=18, fontweight="bold", color="black")

        # P-value annotation
        ymax = max(data["correct"].max(), data["hall"].max())
        ymin = min(data["correct"].min(), data["hall"].min())
        y_range = ymax - ymin
        ax.set_ylim(ymin - 0.05 * y_range, ymax + 0.22 * y_range)

        bracket_y = ymax + 0.07 * y_range
        ax.text(1.5, bracket_y + 0.04 * y_range, p_values[model_id],
                ha="center", va="bottom", fontsize=20, fontstyle="italic")
        ax.plot([1, 2], [bracket_y, bracket_y], color="black", linewidth=1.2)
        ax.plot([1, 1], [bracket_y - 0.02 * y_range, bracket_y],
                color="black", linewidth=1.2)
        ax.plot([2, 2], [bracket_y - 0.02 * y_range, bracket_y],
                color="black", linewidth=1.2)

    fig.suptitle("Within Nonexistent Category: Density by Outcome",
                 fontsize=30, fontweight="bold", y=1.02)
    plt.tight_layout()

    outpath = OUTPUT_DIR / "poster_density_boxplot.png"
    fig.savefig(outpath, bbox_inches="tight")
    plt.close()
    print(f"Saved: {outpath}")


# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 2: Category × prefix hallucination heatmap (Phase 2 hero)
# ═══════════════════════════════════════════════════════════════════════════

def poster_category_heatmap():
    """Category × prefix hallucination rate heatmap for both models."""
    plt.rcParams.update(POSTER_STYLE)

    data = {}
    csv_path = PROJECT_ROOT / 'results' / 'v5_prefixes' / 'analysis' / 'v5_category_metrics.csv'
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            key = (row['model_name'], row['prefix_key'], row['category'])
            data[key] = float(row['hallucination_rate']) * 100

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

    model_configs = [
        ('mixtral-8x7b', 'Mixtral 8x7B'),
        ('llama-4-maverick-17b', 'Llama 4 Maverick'),
    ]

    import matplotlib.colors as mcolors
    cmap = mcolors.LinearSegmentedColormap.from_list(
        'green_red', ['#2d6a2e', '#7cb342', '#c8e6c9', '#ffcc80', '#ef5350', '#b71c1c']
    )

    fig, axes = plt.subplots(1, 2, figsize=(28, 9))

    for ax, (model_id, model_label) in zip(axes, model_configs):
        matrix = np.zeros((len(prefixes), len(categories)))
        for i, (pk, _) in enumerate(prefixes):
            for j, (ck, _) in enumerate(categories):
                matrix[i, j] = data.get((model_id, pk, ck), 0)

        im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=45)

        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels([cl for _, cl in categories], fontsize=18)
        ax.set_yticks(range(len(prefixes)))
        ax.set_yticklabels([pl for _, pl in prefixes], fontsize=18)
        ax.set_title(model_label, fontsize=28, fontweight='bold', pad=15)

        # Add baseline separator
        ax.axhline(y=0.5, color='white', linewidth=3)

        # Add values in cells
        for i in range(len(prefixes)):
            for j in range(len(categories)):
                val = matrix[i, j]
                color = 'white' if val > 20 else 'black'
                ax.text(j, i, f'{val:.1f}', ha='center', va='center',
                        fontsize=16, fontweight='bold', color=color)

    # Colorbar — place below the figure horizontally
    cbar_ax = fig.add_axes([0.15, -0.06, 0.7, 0.03])  # [left, bottom, width, height]
    cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Hallucination rate (%)', fontsize=22)
    cbar.ax.tick_params(labelsize=18)

    plt.subplots_adjust(wspace=0.4)

    outpath = OUTPUT_DIR / "poster_category_heatmap.png"
    fig.savefig(outpath, bbox_inches="tight")
    plt.close()
    print(f"Saved: {outpath}")


# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 3: Baseline vs Best Prefix vs Fine-Tuned comparison (Phase 3 hero)
# ═══════════════════════════════════════════════════════════════════════════

def poster_ft_comparison():
    """Bar chart: baseline vs best-prefix vs fine-tuned, hallucination + refusal."""
    plt.rcParams.update(POSTER_STYLE)

    json_path = PROJECT_ROOT / "results" / "v5_finetuned" / "comparison_analysis.json"
    with open(json_path) as f:
        comp_data = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(20, 9))

    configs = {"mixtral-8x7b": "C", "llama-4-maverick-17b": "A"}
    model_labels = {"mixtral-8x7b": "Mixtral 8x7B", "llama-4-maverick-17b": "Llama 4 Maverick"}

    for idx, (model, config) in enumerate(configs.items()):
        ax = axes[idx]
        md = comp_data[model]

        best_prefix_name = md['best_prefix'].get('prefix_name', md['best_prefix'].get('name', 'Best Prefix'))
        conditions = ["Baseline", f"Best Prefix\n({best_prefix_name})", "Fine-Tuned"]

        hall_rates = [
            md["baseline"]["hallucination_rate"] * 100,
            md["best_prefix"]["hallucination_rate"] * 100,
            md["finetuned"][f"config{config}"]["aggregate"]["hallucination_rate"] * 100,
        ]

        def get_refusal(d):
            if "refusal_rate" in d:
                return d["refusal_rate"] * 100
            elif "refusal" in d and "total" in d:
                return d["refusal"] / d["total"] * 100
            return 0

        refusal_rates = [
            get_refusal(md["baseline"]),
            get_refusal(md["best_prefix"]),
            get_refusal(md["finetuned"][f"config{config}"]["aggregate"]),
        ]

        x = np.arange(len(conditions))
        width = 0.35

        bars1 = ax.bar(x - width/2, hall_rates, width, label='Hallucination rate',
                       color=COLORS["hallucinated"], edgecolor="black", linewidth=1.0, alpha=0.85)
        bars2 = ax.bar(x + width/2, refusal_rates, width, label='Refusal rate',
                       color='#95a5a6', edgecolor="black", linewidth=1.0, alpha=0.85)

        # Add value labels
        for bar, val in zip(bars1, hall_rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=18, fontweight='bold')
        for bar, val in zip(bars2, refusal_rates):
            if val > 0.1:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                        f'{val:.1f}%', ha='center', va='bottom', fontsize=18, fontweight='bold')

        ax.set_xticks(x)
        ax.set_xticklabels(conditions, fontsize=20)
        ax.set_ylabel('Rate (%)', fontsize=24)
        ax.set_title(model_labels[model], fontsize=28, fontweight='bold')
        ax.legend(fontsize=18, loc='upper right')
        ax.set_ylim(0, max(hall_rates) * 1.3)
        ax.grid(axis='y', alpha=0.3)

        # Add McNemar p-value annotation
        if model == "mixtral-8x7b":
            ax.text(1.5, max(hall_rates) * 0.9, "$p = 0.82$\n(FT vs Best Prefix)",
                    ha="center", fontsize=16, fontstyle="italic",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

    fig.suptitle("Hallucination and Refusal Rates by Intervention",
                 fontsize=32, fontweight="bold", y=1.02)
    plt.tight_layout()

    outpath = OUTPUT_DIR / "poster_ft_comparison.png"
    fig.savefig(outpath, bbox_inches="tight")
    plt.close()
    print(f"Saved: {outpath}")


# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 4: Combined UMAP colored by category (Motivation/Key Question)
# ═══════════════════════════════════════════════════════════════════════════

def poster_umap():
    """Single UMAP with all prompts colored by category, poster-scale."""
    import umap as umap_lib
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.seed import set_seed
    set_seed(42)

    plt.rcParams.update(POSTER_STYLE)

    # Load data
    embeddings = np.load(PROJECT_ROOT / "data" / "processed" / "v5_question_embeddings.npy")
    with open(PROJECT_ROOT / "data" / "processed" / "v5_embedding_id_mapping.json") as f:
        id_mapping = json.load(f)

    geo = pd.read_csv(PROJECT_ROOT / "data" / "processed" / "v5_geometry_features.csv")

    # Load Mixtral baselines for hallucination labels
    mixtral_results = []
    with open(PROJECT_ROOT / "results" / "v5_baselines" / "mixtral-8x7b" / "no_prefix" / "judged_answers.jsonl") as f:
        for line in f:
            mixtral_results.append(json.loads(line))
    mixtral_df = pd.DataFrame(mixtral_results)

    df = mixtral_df[["id", "category", "judge_label"]].copy()
    df = df[df["judge_label"].isin([0, 2])].copy()

    # Get embeddings for all prompts in geometry features
    all_ids = geo["id"].tolist()
    all_indices = [id_mapping[pid] for pid in all_ids if pid in id_mapping]
    all_embeddings = embeddings[all_indices]

    print("  Running UMAP...")
    reducer = umap_lib.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
    coords_2d = reducer.fit_transform(all_embeddings)

    valid_ids = [pid for pid in all_ids if pid in id_mapping]
    coord_df = pd.DataFrame({
        "id": valid_ids,
        "umap1": coords_2d[:, 0],
        "umap2": coords_2d[:, 1],
    })

    # Merge with category and hallucination info
    plot_df = df.merge(coord_df, on="id", how="inner")

    # Category colors and labels with hallucination rates
    cat_config = [
        ("ambiguous", "Ambiguous", "#1f77b4"),
        ("borderline_edge_factual", "Edge Factual", "#17becf"),
        ("factual", "Factual", "#2ca02c"),
        ("impossible", "Impossible", "#ff7f0e"),
        ("borderline_obscure_real", "Obscure Real", "#e377c2"),
        ("nonexistent", "Nonexistent", "#9467bd"),
        ("borderline_plausible_fake", "Plausible Fake", "#d62728"),
    ]

    # Compute rates for legend
    cat_rates = {}
    for cat_key, _, _ in cat_config:
        cat_data = plot_df[plot_df["category"] == cat_key]
        if len(cat_data) > 0:
            cat_rates[cat_key] = cat_data[cat_data["judge_label"] == 2].shape[0] / len(cat_data) * 100

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))

    for cat_key, cat_label, color in cat_config:
        cat_data = plot_df[plot_df["category"] == cat_key]
        rate = cat_rates.get(cat_key, 0)
        ax.scatter(cat_data["umap1"], cat_data["umap2"],
                   c=color, alpha=0.6, s=60, label=f"{cat_label} ({rate:.1f}%)",
                   edgecolors='white', linewidths=0.3, zorder=2)

    ax.set_xlabel("UMAP 1", fontsize=26)
    ax.set_ylabel("UMAP 2", fontsize=26)
    ax.legend(fontsize=20, loc="upper right", framealpha=0.9,
              title="Category (halluc. rate)", title_fontsize=20,
              markerscale=2.0)
    ax.grid(alpha=0.15)
    ax.tick_params(labelsize=20)

    plt.tight_layout()

    outpath = OUTPUT_DIR / "poster_umap_categories.png"
    fig.savefig(outpath, bbox_inches="tight")
    plt.close()
    print(f"Saved: {outpath}")

    # Also save UMAP without legend + separate legend image
    fig2, ax2 = plt.subplots(1, 1, figsize=(16, 12))
    for cat_key, cat_label, color in cat_config:
        cat_data = plot_df[plot_df["category"] == cat_key]
        ax2.scatter(cat_data["umap1"], cat_data["umap2"],
                    c=color, alpha=0.6, s=60, edgecolors='white', linewidths=0.3, zorder=2)
    ax2.set_xlabel("UMAP 1", fontsize=26)
    ax2.set_ylabel("UMAP 2", fontsize=26)
    ax2.grid(alpha=0.15)
    ax2.tick_params(labelsize=20)
    plt.tight_layout()
    fig2.savefig(OUTPUT_DIR / "poster_umap_nolegend.png", bbox_inches="tight")
    plt.close()
    print(f"Saved: {OUTPUT_DIR / 'poster_umap_nolegend.png'}")

    # Standalone legend image
    fig_leg, ax_leg = plt.subplots(1, 1, figsize=(8, 5))
    ax_leg.axis('off')
    handles = []
    for cat_key, cat_label, color in cat_config:
        rate = cat_rates.get(cat_key, 0)
        h = ax_leg.scatter([], [], c=color, s=200, edgecolors='white', linewidths=0.3,
                           label=f"{cat_label} ({rate:.1f}%)")
        handles.append(h)
    ax_leg.legend(handles=handles, fontsize=22, loc='center', framealpha=0.9,
                  title="Category (halluc. rate)", title_fontsize=24,
                  markerscale=1.5, handletextpad=1.0, borderpad=1.2)
    plt.tight_layout()
    fig_leg.savefig(OUTPUT_DIR / "poster_umap_legend.png", bbox_inches="tight",
                    transparent=True)
    plt.close()
    print(f"Saved: {OUTPUT_DIR / 'poster_umap_legend.png'}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generating poster-scale figures...")
    print()

    print("[1/3] Density box plot (Phase 1)...")
    poster_density_boxplot()

    print("[2/3] Category heatmap (Phase 2)...")
    poster_category_heatmap()

    print("[3/4] FT comparison bar chart (Phase 3)...")
    poster_ft_comparison()

    print("[4/4] UMAP colored by category (Motivation)...")
    poster_umap()

    print()
    print("All poster figures saved to thesis/figures/poster_*.png")
