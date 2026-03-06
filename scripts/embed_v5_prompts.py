"""Embed V5 + V3 prompts using OpenAI text-embedding-3-large.

Embeds the combined corpus (449 V3 + 2,430 V5 = 2,879 prompts) into a single
embedding matrix for geometry computation. V3 prompts come first so their
indices are stable.

Usage:
    export OPENAI_API_KEY=sk-...
    python3 scripts/embed_v5_prompts.py

Output:
    data/processed/v5_question_embeddings.npy        (2879, 3072) float32
    data/processed/v5_embedding_id_mapping.json       {id: index}
"""

import sys
import json
import time
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl
from src.models.embedding_client import EmbeddingClient

PROMPTS_DIR = PROJECT_ROOT / "data" / "prompts"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


def main():
    print("=" * 60)
    print("  EMBEDDING V5 + V3 PROMPTS")
    print("=" * 60)

    # 1. Load prompts: V3 first, then V5
    v3_prompts = read_jsonl(PROMPTS_DIR / "prompts.jsonl")
    v5_prompts = read_jsonl(PROMPTS_DIR / "v5_all.jsonl")

    all_prompts = v3_prompts + v5_prompts
    print(f"\n  V3 prompts: {len(v3_prompts)}")
    print(f"  V5 prompts: {len(v5_prompts)}")
    print(f"  Combined:   {len(all_prompts)}")

    # 2. Extract question texts
    questions = [p["question"] for p in all_prompts]
    ids = [p["id"] for p in all_prompts]

    # Check for duplicate IDs
    if len(set(ids)) != len(ids):
        print(f"\n  WARNING: {len(ids) - len(set(ids))} duplicate IDs found!")

    # 3. Build ID mapping
    id_mapping = {pid: idx for idx, pid in enumerate(ids)}

    # 4. Embed
    print(f"\n  Model: text-embedding-3-large (3072-dim)")
    print(f"  Batches: {(len(questions) + 99) // 100} x 100 texts")
    print(f"  Estimated time: ~30-60 seconds\n")

    client = EmbeddingClient(
        model_name="text-embedding-3-large",
        batch_size=100,
        max_retries=3,
        timeout=60,
    )

    start_time = time.time()

    # Embed with progress reporting
    all_embeddings = []
    batch_size = 100
    n_batches = (len(questions) + batch_size - 1) // batch_size

    for i in range(0, len(questions), batch_size):
        batch_num = i // batch_size + 1
        batch = questions[i : i + batch_size]
        print(f"  Batch {batch_num}/{n_batches} ({len(batch)} texts)...", end=" ")

        batch_start = time.time()
        embeddings = client._embed_batch(batch)
        all_embeddings.extend(embeddings)
        batch_elapsed = time.time() - batch_start
        print(f"done ({batch_elapsed:.1f}s)")

    elapsed = time.time() - start_time
    print(f"\n  Total embedding time: {elapsed:.1f}s")

    # 5. Convert to numpy
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    print(f"  Embedding shape: {embeddings_array.shape}")
    print(f"  Memory: {embeddings_array.nbytes / 1024 / 1024:.1f} MB")

    # 6. Validate
    assert embeddings_array.shape[0] == len(all_prompts), \
        f"Mismatch: {embeddings_array.shape[0]} embeddings vs {len(all_prompts)} prompts"
    assert embeddings_array.shape[1] == 3072, \
        f"Expected 3072 dims, got {embeddings_array.shape[1]}"

    # Check for NaN/Inf
    n_nan = np.isnan(embeddings_array).sum()
    n_inf = np.isinf(embeddings_array).sum()
    print(f"  NaN values: {n_nan} {'[PASS]' if n_nan == 0 else '[FAIL!]'}")
    print(f"  Inf values: {n_inf} {'[PASS]' if n_inf == 0 else '[FAIL!]'}")

    # Check norms are reasonable (embeddings should be unit-normalized by OpenAI)
    norms = np.linalg.norm(embeddings_array, axis=1)
    print(f"  Norm range: [{norms.min():.4f}, {norms.max():.4f}] (expect ~1.0)")

    # 7. Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    embeddings_path = OUTPUT_DIR / "v5_question_embeddings.npy"
    mapping_path = OUTPUT_DIR / "v5_embedding_id_mapping.json"

    np.save(embeddings_path, embeddings_array)
    print(f"\n  Saved embeddings: {embeddings_path}")
    print(f"    Shape: {embeddings_array.shape}, dtype: {embeddings_array.dtype}")

    with open(mapping_path, "w") as f:
        json.dump(id_mapping, f, indent=2)
    print(f"  Saved ID mapping: {mapping_path}")
    print(f"    {len(id_mapping)} entries (V3: indices 0-{len(v3_prompts)-1}, V5: {len(v3_prompts)}-{len(all_prompts)-1})")

    print(f"\n{'=' * 60}")
    print(f"  DONE — {len(all_prompts)} prompts embedded in {elapsed:.1f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
