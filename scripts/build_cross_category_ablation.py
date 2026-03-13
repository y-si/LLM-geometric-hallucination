"""Phase 10A: Cross-Category Generalization Ablation — Data Preparation

Creates 5 ablation conditions per model (+ Full as existing control):
  entity_dep       — Only entity-dependent categories (nonexistent, plausible_fake, obscure_real)
  R_entity_dep     — Random sample from all 7 categories, matched to entity_dep's N (size control)
  entity_indep     — Only entity-independent categories (factual, ambiguous, impossible, edge_factual)
  leave_out_nonex  — All categories except nonexistent
  leave_out_fact   — All categories except factual

Design rationale:
  - entity_dep / entity_indep test the conceptual boundary between uncertainty types
  - R_entity_dep isolates category coverage from dataset size (same approach as Phase 9's R{N})
  - leave_out_nonexistent / leave_out_factual are single-category holdouts with best statistical
    power (largest test categories: nonexistent n=120, factual n=98)
  - Full (existing T-all) is the control — no new fine-tuning needed

Input:
  data/training/v5_training_{model}.jsonl — best-per-prompt data (Step 9 output)

Output:
  data/training/ablation_cross_cat/{condition}_{model}.jsonl — best-per-prompt format
  data/training/ablation_cross_cat/{condition}_together_{model}.jsonl — Together AI format
  data/training/ablation_cross_cat/cross_cat_ablation_report.json — generation report
"""

import json
import random
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TRAINING_DIR = BASE_DIR / "data" / "training"
OUTPUT_DIR = TRAINING_DIR / "ablation_cross_cat"

MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]
SEED = 2026  # Different seed from Phase 9 (2025) to avoid any correlation

ENTITY_DEP_CATS = {"nonexistent", "borderline_plausible_fake", "borderline_obscure_real"}
ENTITY_INDEP_CATS = {"factual", "ambiguous", "impossible", "borderline_edge_factual"}

# Condition definitions: name → set of categories to INCLUDE
CONDITIONS = {
    "entity_dep": ENTITY_DEP_CATS,
    "entity_indep": ENTITY_INDEP_CATS,
    "leave_out_nonex": (ENTITY_DEP_CATS | ENTITY_INDEP_CATS) - {"nonexistent"},
    "leave_out_fact": (ENTITY_DEP_CATS | ENTITY_INDEP_CATS) - {"factual"},
}


def load_training_data(model):
    """Load best-per-prompt training data for a model."""
    path = TRAINING_DIR / f"v5_training_{model}.jsonl"
    records = []
    with open(path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def to_together_format(record):
    """Convert a training record to Together AI messages format (no system prompt)."""
    question = record.get("question", "").strip()
    answer = str(record.get("selected_answer", "")).strip()
    if not question or not answer:
        return None
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


def estimate_tokens(text):
    """Rough token estimate: ~4 chars per token."""
    return len(text) / 4


def filter_by_categories(records, include_cats):
    """Return indices of records whose category is in include_cats."""
    return [i for i, r in enumerate(records) if r.get("category") in include_cats]


def stratified_random_sample(records, target_n, seed):
    """Stratified random sample from all categories, preserving Full's category proportions.

    Samples target_n records total, with each category contributing proportionally
    to its share in the full dataset.
    """
    rng = random.Random(seed)

    # Group by category
    cat_indices = defaultdict(list)
    for i, r in enumerate(records):
        cat_indices[r.get("category", "unknown")].append(i)

    total = len(records)
    sampled = []

    # Compute proportional counts
    cats_sorted = sorted(cat_indices.keys())
    proportional_counts = {}
    allocated = 0
    for j, cat in enumerate(cats_sorted):
        if j == len(cats_sorted) - 1:
            # Last category gets remainder to ensure exact total
            proportional_counts[cat] = target_n - allocated
        else:
            n = round(len(cat_indices[cat]) / total * target_n)
            proportional_counts[cat] = n
            allocated += n

    # Sample
    for cat in cats_sorted:
        n_cat = proportional_counts[cat]
        pool = cat_indices[cat][:]
        rng.shuffle(pool)
        if n_cat > len(pool):
            print(f"  WARNING: {cat} has {len(pool)} records but need {n_cat}, taking all")
            n_cat = len(pool)
        sampled.extend(pool[:n_cat])

    return sampled


def write_condition(records, indices, condition, model):
    """Write ablation files for a condition. Returns stats dict."""
    subset = [records[i] for i in sorted(indices)]

    # Per-category breakdown
    cat_counts = defaultdict(int)
    for r in subset:
        cat_counts[r.get("category", "unknown")] += 1

    # Write best-per-prompt format
    bpp_path = OUTPUT_DIR / f"{condition}_{model}.jsonl"
    with open(bpp_path, "w") as f:
        for r in subset:
            f.write(json.dumps(r) + "\n")

    # Write Together AI format
    together_path = OUTPUT_DIR / f"{condition}_together_{model}.jsonl"
    total_tokens = 0
    converted = 0
    skipped = 0
    with open(together_path, "w") as f:
        for r in subset:
            rec = to_together_format(r)
            if rec is None:
                skipped += 1
                continue
            f.write(json.dumps(rec) + "\n")
            converted += 1
            total_tokens += estimate_tokens(
                rec["messages"][0]["content"] + rec["messages"][1]["content"]
            )

    if skipped:
        print(f"  WARNING: {skipped} records skipped (empty question/answer)")

    return {
        "total": len(subset),
        "converted": converted,
        "skipped": skipped,
        "token_estimate": int(total_tokens),
        "per_category": dict(sorted(cat_counts.items())),
    }


def main():
    print("=" * 60)
    print("Phase 10A: Cross-Category Generalization — Data Preparation")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "experiment": "Phase 10: Cross-Category Generalization Ablation",
        "seed": SEED,
        "conditions": {},
        "entity_dep_categories": sorted(ENTITY_DEP_CATS),
        "entity_indep_categories": sorted(ENTITY_INDEP_CATS),
    }

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        records = load_training_data(model)
        print(f"  {len(records)} training records loaded")

        # Show per-category counts
        cat_counts_full = defaultdict(int)
        for r in records:
            cat_counts_full[r.get("category", "unknown")] += 1
        for cat in sorted(cat_counts_full):
            print(f"    {cat}: {cat_counts_full[cat]}")

        # === Category-filtered conditions ===
        for cond_name, include_cats in CONDITIONS.items():
            print(f"\n--- {cond_name}: {sorted(include_cats)} ---")
            indices = filter_by_categories(records, include_cats)
            print(f"  {len(indices)} records selected")
            stats = write_condition(records, indices, cond_name, model)
            report["conditions"].setdefault(cond_name, {})[model] = stats

            for cat in sorted(stats["per_category"]):
                print(f"    {cat}: {stats['per_category'][cat]}")

        # === R_entity_dep: size-matched random control ===
        entity_dep_indices = filter_by_categories(records, ENTITY_DEP_CATS)
        target_n = len(entity_dep_indices)
        cond_name = "R_entity_dep"
        print(f"\n--- {cond_name}: stratified random sample, N={target_n} ---")

        r_indices = stratified_random_sample(records, target_n, SEED)
        print(f"  {len(r_indices)} records selected")
        stats = write_condition(records, r_indices, cond_name, model)
        report["conditions"].setdefault(cond_name, {})[model] = stats

        for cat in sorted(stats["per_category"]):
            print(f"    {cat}: {stats['per_category'][cat]}")

        # === Full (existing, just log stats) ===
        report["conditions"].setdefault("Full", {})[model] = {
            "total": len(records),
            "per_category": dict(sorted(cat_counts_full.items())),
            "note": "Existing T-all from Phase 9, not regenerated",
        }

        # === Validation ===
        print(f"\n--- Validation ---")

        # 1. Verify category filtering is correct
        for cond_name, include_cats in CONDITIONS.items():
            cond_stats = report["conditions"][cond_name][model]
            actual_cats = set(cond_stats["per_category"].keys())
            expected_cats = include_cats & set(cat_counts_full.keys())
            if actual_cats != expected_cats:
                print(f"  FAIL: {cond_name} has categories {actual_cats}, expected {expected_cats}")
            else:
                print(f"  OK: {cond_name} — {len(actual_cats)} categories, {cond_stats['total']} records")

        # 2. Verify R_entity_dep has correct N
        r_stats = report["conditions"]["R_entity_dep"][model]
        dep_stats = report["conditions"]["entity_dep"][model]
        if r_stats["total"] == dep_stats["total"]:
            print(f"  OK: R_entity_dep N ({r_stats['total']}) matches entity_dep N ({dep_stats['total']})")
        else:
            print(f"  FAIL: R_entity_dep N ({r_stats['total']}) != entity_dep N ({dep_stats['total']})")

        # 3. Verify R_entity_dep has all 7 categories
        r_cats = set(r_stats["per_category"].keys())
        if len(r_cats) == 7:
            print(f"  OK: R_entity_dep has all 7 categories")
        else:
            print(f"  FAIL: R_entity_dep has {len(r_cats)} categories: {r_cats}")

        # 4. Verify all conditions have >200 records (LoRA minimum)
        for cond_name in list(CONDITIONS.keys()) + ["R_entity_dep"]:
            n = report["conditions"][cond_name][model]["total"]
            status = "OK" if n >= 200 else "FAIL"
            print(f"  {status}: {cond_name} has {n} records (minimum 200)")

    # Write report
    report_path = OUTPUT_DIR / "cross_cat_ablation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n{'='*60}")
    print(f"Report written to {report_path}")

    # Summary
    print(f"\nFiles generated in {OUTPUT_DIR}:")
    for p in sorted(OUTPUT_DIR.iterdir()):
        if p.suffix == ".jsonl":
            with open(p) as f:
                n = sum(1 for _ in f)
            print(f"  {p.name}: {n} records")

    print("\nDone.")


if __name__ == "__main__":
    main()
