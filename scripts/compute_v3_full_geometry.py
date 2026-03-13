"""Step 12A.0: Compute geometric features for ALL 449 V3 held-out prompts.

The original geometry_features.csv only has 368 prompts (4 main categories).
The 81 borderline prompts (obscure_real: 30, plausible_fake: 31, edge_factual: 20)
were never embedded or processed through the geometry pipeline.

This script re-embeds all 449 V3 prompts and computes geometry features for the
complete set, enabling the fine-tuning bridge analysis (Step 12A.1-3) to cover
all categories including the borderline prompts where the most interesting
fine-tuning behavior occurs (regressions).

Uses the same embedding model (text-embedding-3-large) and reference corpus
as the original V3 pipeline. Verifies consistency with existing 368-prompt
geometry by checking correlation.

Usage:
    export OPENAI_API_KEY=...
    python3 scripts/compute_v3_full_geometry.py

Output:
    data/processed/v3_all_geometry_features.csv  (449 rows)
    data/processed/v3_all_question_embeddings.npy
    data/processed/v3_all_embedding_id_mapping.json

Cost: <$0.01 (449 short texts via OpenAI embeddings API)
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.embedding_client import EmbeddingClient
from src.geometry.intrinsic_dimension import compute_local_id_for_all
from src.geometry.curvature import compute_curvature_proxy
from src.geometry.oppositeness import fit_global_pca, compute_oppositeness_scores
from src.geometry.reference_corpus import load_reference_corpus
from src.geometry.density import compute_local_density
from src.geometry.centrality import compute_distance_to_center
from src.utils.io import read_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

V3_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "prompts.jsonl"
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference_corpus"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OLD_GEOMETRY_PATH = PROCESSED_DIR / "geometry_features.csv"

OUTPUT_GEOMETRY = PROCESSED_DIR / "v3_all_geometry_features.csv"
OUTPUT_EMBEDDINGS = PROCESSED_DIR / "v3_all_question_embeddings.npy"
OUTPUT_MAPPING = PROCESSED_DIR / "v3_all_embedding_id_mapping.json"

EMBEDDING_MODEL = "text-embedding-3-large"
N_NEIGHBORS_ID = 20
N_NEIGHBORS_CURVATURE = 30
N_PCA_COMPONENTS = 50
N_FLIP_COMPONENTS = 5


def main():
    # ── Load V3 prompts ──
    prompts = read_jsonl(V3_PROMPTS_PATH)
    print(f"Loaded {len(prompts)} V3 prompts")

    cats = {}
    for p in prompts:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
    for c in sorted(cats.keys()):
        print(f"  {c}: {cats[c]}")

    question_ids = [p["id"] for p in prompts]
    questions = [p["question"] for p in prompts]
    categories = [p["category"] for p in prompts]

    # ── Embed all 449 questions (or load cached) ──
    if OUTPUT_EMBEDDINGS.exists():
        print(f"\nLoading cached embeddings from {OUTPUT_EMBEDDINGS}...")
        embeddings = np.load(OUTPUT_EMBEDDINGS)
        print(f"Embeddings shape: {embeddings.shape}")
    else:
        print(f"\nEmbedding {len(questions)} questions with {EMBEDDING_MODEL}...")
        embed_client = EmbeddingClient(
            model_name=EMBEDDING_MODEL,
            batch_size=100,
            max_retries=3,
            timeout=60,
        )
        embeddings = embed_client.embed_texts(questions)
        print(f"Embeddings shape: {embeddings.shape}")

        # Save embeddings
        np.save(OUTPUT_EMBEDDINGS, embeddings)
        id_mapping = {qid: i for i, qid in enumerate(question_ids)}
        with open(OUTPUT_MAPPING, "w") as f:
            json.dump(id_mapping, f, indent=2)
        print(f"Saved embeddings to {OUTPUT_EMBEDDINGS}")

    # ── Reference for density/centrality ──
    # V3 used self-reference (decision log: "build_from_benchmark: true").
    # The reference_corpus/ dir only has metadata.json — embedding files were
    # cleaned up. Use self-reference to match V3 methodology.
    ref_embeddings_path = REFERENCE_DIR / "reference_embeddings.npy"
    if ref_embeddings_path.exists():
        print("\nLoading reference corpus...")
        ref_corpus = load_reference_corpus(REFERENCE_DIR)
        ref_embeddings = ref_corpus["embeddings"]
        ref_mean = ref_corpus["mean"]
        print(f"Reference corpus: {ref_embeddings.shape[0]} samples, dim={ref_embeddings.shape[1]}")
    else:
        print("\nUsing self-reference for density/centrality (matches V3 methodology)")
        ref_embeddings = embeddings
        ref_mean = np.mean(embeddings, axis=0)

    # ── Compute geometric features ──

    print("\nComputing local intrinsic dimension...")
    local_ids = compute_local_id_for_all(
        embeddings, n_neighbors=N_NEIGHBORS_ID, metric="cosine"
    )
    print(f"  Range: {np.nanmin(local_ids):.2f} to {np.nanmax(local_ids):.2f}")

    print("Computing curvature scores (449 local PCAs, ~1-2 min)...")
    curvature_scores = compute_curvature_proxy(
        embeddings, local_ids, n_neighbors=N_NEIGHBORS_CURVATURE, metric="cosine"
    )
    print(f"  Range: {np.nanmin(curvature_scores):.4f} to {np.nanmax(curvature_scores):.4f}")

    print("Computing oppositeness scores...")
    global_pca = fit_global_pca(embeddings, n_components=N_PCA_COMPONENTS)
    print(f"  PCA explained variance: {global_pca.explained_variance_ratio_.sum():.3f}")
    oppositeness_scores = compute_oppositeness_scores(
        embeddings, global_pca, n_flip=N_FLIP_COMPONENTS
    )
    print(f"  Range: {np.nanmin(oppositeness_scores):.4f} to {np.nanmax(oppositeness_scores):.4f}")

    print("Computing local density...")
    density_scores = compute_local_density(
        embeddings, ref_embeddings, k=N_NEIGHBORS_ID, metric="cosine"
    )
    print(f"  Range: {np.nanmin(density_scores):.4f} to {np.nanmax(density_scores):.4f}")

    print("Computing centrality...")
    centrality_scores = compute_distance_to_center(
        embeddings, ref_mean, metric="cosine"
    )
    print(f"  Range: {np.nanmin(centrality_scores):.4f} to {np.nanmax(centrality_scores):.4f}")

    # ── Build output DataFrame ──
    features_df = pd.DataFrame({
        "id": question_ids,
        "category": categories,
        "local_id": local_ids,
        "curvature_score": curvature_scores,
        "oppositeness_score": oppositeness_scores,
        "density": density_scores,
        "centrality": centrality_scores,
    })

    features_df.to_csv(OUTPUT_GEOMETRY, index=False)
    print(f"\nSaved {len(features_df)} rows to {OUTPUT_GEOMETRY}")

    # ── Summary by category ──
    print("\nGeometry features by category:")
    print(f"  {'Category':<30s} {'N':>4s} {'Curvature':>10s} {'Opposit':>10s} {'Density':>10s} {'Central':>10s}")
    print(f"  {'-'*30} {'-'*4} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for cat in sorted(features_df["category"].unique()):
        cd = features_df[features_df["category"] == cat]
        print(
            f"  {cat:<30s} {len(cd):>4d} "
            f"{cd['curvature_score'].mean():>10.4f} "
            f"{cd['oppositeness_score'].mean():>10.4f} "
            f"{cd['density'].mean():>10.4f} "
            f"{cd['centrality'].mean():>10.4f}"
        )

    # ── Verify against original 368 ──
    if OLD_GEOMETRY_PATH.exists():
        print("\n── Verification against original geometry_features.csv ──")
        old_df = pd.read_csv(OLD_GEOMETRY_PATH)
        print(f"Original: {len(old_df)} rows")

        merged = old_df.merge(features_df, on="id", suffixes=("_old", "_new"))
        print(f"Matched: {len(merged)} rows")

        for feat in ["curvature_score", "oppositeness_score", "density", "centrality"]:
            old_col = f"{feat}_old"
            new_col = f"{feat}_new"
            if old_col in merged.columns and new_col in merged.columns:
                corr = merged[old_col].corr(merged[new_col])
                max_diff = (merged[old_col] - merged[new_col]).abs().max()
                mean_diff = (merged[old_col] - merged[new_col]).abs().mean()
                print(f"  {feat}: corr={corr:.6f}, max_diff={max_diff:.6f}, mean_diff={mean_diff:.6f}")

        # Check new categories
        new_cats = set(features_df["category"].unique()) - set(old_df["category"].unique())
        if new_cats:
            print(f"\n  NEW categories (not in original): {sorted(new_cats)}")
            for cat in sorted(new_cats):
                n = len(features_df[features_df["category"] == cat])
                print(f"    {cat}: {n} prompts")
    else:
        print("\nOriginal geometry_features.csv not found — skipping verification")

    print(f"\n{'='*60}")
    print(f"  DONE — {len(features_df)} prompts with geometry features")
    print(f"  Output: {OUTPUT_GEOMETRY}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
