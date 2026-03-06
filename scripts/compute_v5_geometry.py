"""Compute geometric features for the combined V3+V5 corpus.

Loads pre-computed embeddings (2,879 x 3072) and computes 5 geometric
features per prompt: local_id, curvature, oppositeness, density, centrality.

Uses self-reference (the combined corpus is its own reference distribution),
matching V3 methodology. All hyperparameters match V3: k=20 for ID/curvature/
density, PCA(10) with 3-flip for oppositeness, cosine distance throughout.

Usage:
    python3 scripts/compute_v5_geometry.py

Output:
    data/processed/v5_geometry_features.csv
"""

import sys
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.geometry.intrinsic_dimension import compute_local_id_for_all
from src.geometry.curvature import compute_curvature_proxy
from src.geometry.oppositeness import fit_global_pca, compute_oppositeness_scores
from src.geometry.density import compute_local_density
from src.geometry.centrality import compute_distance_to_center
from src.utils.io import read_jsonl

# Hyperparameters (matching V3 config_v2.yaml)
K_NEIGHBORS = 20        # For local_id, curvature, density
N_PCA_COMPONENTS = 10   # For oppositeness global PCA
N_FLIP_COMPONENTS = 3   # For oppositeness sign-flip
METRIC = 'cosine'

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
PROMPTS_DIR = DATA_DIR / "prompts"


def main():
    print("=" * 70)
    print("  GEOMETRY COMPUTATION — V5 COMBINED CORPUS")
    print("=" * 70)

    # 1. Load pre-computed embeddings
    embeddings_path = PROCESSED_DIR / "v5_question_embeddings.npy"
    mapping_path = PROCESSED_DIR / "v5_embedding_id_mapping.json"

    print(f"\n  Loading embeddings from {embeddings_path}...")
    embeddings = np.load(embeddings_path)
    print(f"  Shape: {embeddings.shape}, dtype: {embeddings.dtype}")

    with open(mapping_path) as f:
        id_mapping = json.load(f)  # {prompt_id: index}

    # Invert mapping: index -> prompt_id
    index_to_id = {v: k for k, v in id_mapping.items()}
    n_points = embeddings.shape[0]
    assert n_points == len(id_mapping), \
        f"Mismatch: {n_points} embeddings vs {len(id_mapping)} IDs"

    # Build ordered ID and category lists
    prompt_ids = [index_to_id[i] for i in range(n_points)]

    # Load prompt metadata for categories
    v3_prompts = read_jsonl(PROMPTS_DIR / "prompts.jsonl")
    v5_prompts = read_jsonl(PROMPTS_DIR / "v5_all.jsonl")

    id_to_category = {}
    for p in v3_prompts + v5_prompts:
        id_to_category[p["id"]] = p["category"]

    categories = [id_to_category.get(pid, "unknown") for pid in prompt_ids]
    unknown_count = sum(1 for c in categories if c == "unknown")
    if unknown_count > 0:
        print(f"  WARNING: {unknown_count} prompts with unknown category!")

    print(f"  Prompts: {n_points} (V3: {len(v3_prompts)}, V5: {len(v5_prompts)})")

    # Self-reference: the corpus is its own reference distribution
    ref_embeddings = embeddings
    ref_mean = np.mean(embeddings, axis=0)
    print(f"\n  Reference: self-reference ({n_points} prompts)")

    # 2. Compute features
    total_start = time.time()

    # 2a. Local intrinsic dimension (TwoNN)
    print(f"\n  [1/5] Local intrinsic dimension (TwoNN, k={K_NEIGHBORS})...")
    t0 = time.time()
    local_ids = compute_local_id_for_all(
        embeddings, n_neighbors=K_NEIGHBORS, metric=METRIC
    )
    nan_count = np.isnan(local_ids).sum()
    print(f"    Range: [{np.nanmin(local_ids):.2f}, {np.nanmax(local_ids):.2f}]")
    print(f"    NaN: {nan_count}/{n_points} ({nan_count/n_points*100:.1f}%)")
    print(f"    Time: {time.time() - t0:.1f}s")

    # 2b. Curvature (PCA residual variance)
    print(f"\n  [2/5] Curvature proxy (PCA residual, k={K_NEIGHBORS})...")
    t0 = time.time()
    curvature_scores = compute_curvature_proxy(
        embeddings, local_ids, n_neighbors=K_NEIGHBORS, metric=METRIC
    )
    nan_count = np.isnan(curvature_scores).sum()
    print(f"    Range: [{np.nanmin(curvature_scores):.4f}, {np.nanmax(curvature_scores):.4f}]")
    print(f"    NaN: {nan_count}/{n_points}")
    print(f"    Time: {time.time() - t0:.1f}s")

    # 2c. Oppositeness (PCA sign-flip)
    print(f"\n  [3/5] Oppositeness (PCA={N_PCA_COMPONENTS}, flip={N_FLIP_COMPONENTS})...")
    t0 = time.time()
    global_pca = fit_global_pca(embeddings, n_components=N_PCA_COMPONENTS)
    print(f"    PCA explained variance: {global_pca.explained_variance_ratio_.sum():.4f}")
    oppositeness_scores = compute_oppositeness_scores(
        embeddings, global_pca, n_flip=N_FLIP_COMPONENTS
    )
    print(f"    Range: [{np.nanmin(oppositeness_scores):.4f}, {np.nanmax(oppositeness_scores):.4f}]")
    print(f"    Time: {time.time() - t0:.1f}s")

    # 2d. Density (inverse mean k-NN distance to reference)
    print(f"\n  [4/5] Local density (k={K_NEIGHBORS}, self-reference)...")
    t0 = time.time()
    density_scores = compute_local_density(
        embeddings, ref_embeddings, k=K_NEIGHBORS, metric=METRIC
    )
    print(f"    Range: [{np.nanmin(density_scores):.4f}, {np.nanmax(density_scores):.4f}]")
    print(f"    Time: {time.time() - t0:.1f}s")

    # 2e. Centrality (cosine distance to corpus mean)
    print(f"\n  [5/5] Centrality (distance to corpus mean)...")
    t0 = time.time()
    centrality_scores = compute_distance_to_center(
        embeddings, ref_mean, metric=METRIC
    )
    print(f"    Range: [{np.nanmin(centrality_scores):.4f}, {np.nanmax(centrality_scores):.4f}]")
    print(f"    Time: {time.time() - t0:.1f}s")

    total_elapsed = time.time() - total_start
    print(f"\n  Total computation time: {total_elapsed:.1f}s")

    # 3. Build output dataframe
    features_df = pd.DataFrame({
        'id': prompt_ids,
        'category': categories,
        'local_id': local_ids,
        'curvature_score': curvature_scores,
        'oppositeness_score': oppositeness_scores,
        'density': density_scores,
        'centrality': centrality_scores,
    })

    # 4. Summary by category
    print("\n" + "=" * 70)
    print("  SUMMARY BY CATEGORY")
    print("=" * 70)
    print(f"  {'Category':<30s} {'N':>5s} {'LocalID':>8s} {'Curv':>8s} {'Oppos':>8s} {'Dens':>8s} {'Centr':>8s}")
    print(f"  {'-'*30} {'-'*5} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for cat in sorted(features_df['category'].unique()):
        cat_data = features_df[features_df['category'] == cat]
        n = len(cat_data)
        print(f"  {cat:<30s} {n:>5d} "
              f"{cat_data['local_id'].mean():>8.2f} "
              f"{cat_data['curvature_score'].mean():>8.4f} "
              f"{cat_data['oppositeness_score'].mean():>8.4f} "
              f"{cat_data['density'].mean():>8.4f} "
              f"{cat_data['centrality'].mean():>8.4f}")

    # 5. Validation
    print("\n" + "=" * 70)
    print("  VALIDATION")
    print("=" * 70)

    total_nan = features_df[['local_id', 'curvature_score', 'oppositeness_score',
                              'density', 'centrality']].isna().sum()
    for col, count in total_nan.items():
        status = "[PASS]" if count == 0 else f"[{count} NaN]"
        print(f"  {col}: {status}")

    # Check for infinities
    total_inf = np.isinf(features_df[['local_id', 'curvature_score', 'oppositeness_score',
                                       'density', 'centrality']].values).sum()
    print(f"  Inf values: {total_inf} {'[PASS]' if total_inf == 0 else '[FAIL]'}")

    # Row count check
    print(f"  Row count: {len(features_df)} {'[PASS]' if len(features_df) == n_points else '[FAIL]'}")

    # 6. Save
    output_path = PROCESSED_DIR / "v5_geometry_features.csv"
    features_df.to_csv(output_path, index=False)
    print(f"\n  Saved: {output_path}")
    print(f"  Shape: {features_df.shape}")

    print(f"\n{'=' * 70}")
    print(f"  DONE — {n_points} prompts, 5 features, {total_elapsed:.1f}s")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
