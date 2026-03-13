"""Build template diversity ablation datasets from existing V5 best-per-prompt training data.

Phase 9A: Template Diversity Ablation — Data Preparation

Creates 4 ablation conditions per model:
  T5   — Only prompts using first 5 templates per category/sub-type (seeded shuffle)
  R{N} — Random sample matching T5's N, stratified by category (controls for quantity)
  T10  — Only prompts using first 10 templates per category/sub-type
  T-all — Full training set (already exists, not regenerated)

Design rationale:
  - T1 excluded a priori: only 179 prompts achievable (3-15 per category), insufficient
    for fine-tuning. Some category-template combinations produce <5 prompts.
  - T5 ⊂ T10 ⊂ T-all nesting guaranteed by seeded shuffle.
  - R{N} matched to T5's count with stratified sampling to isolate template diversity
    from training set size.
  - borderline_edge_factual has no templates — always included in full.

Design notes (document in thesis):
  - edge_factual dilution: 130 no-template records = ~33% of T5/R{N}. These are
    identical between T5 and R{N}, diluting the template-diversity signal. Report
    per-category metrics excluding edge_factual to show the effect on templated
    categories.
  - R{N} labels differ per model (R397 Mixtral, R402 Llama) because unfixable
    counts differ (28 vs 24). Downstream scripts should read ablation_report.json
    to resolve filenames.

Input:
  data/prompts/v5_all.jsonl — ID→template lookup (2,430 records)
  data/training/v5_training_{model}.jsonl — best-per-prompt data

Output:
  data/training/ablation/{condition}_{model}.jsonl — best-per-prompt format
  data/training/ablation/{condition}_together_{model}.jsonl — Together AI format
  data/training/ablation/ablation_report.json — generation report
"""

import json
import math
import random
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
PROMPTS_PATH = BASE_DIR / "data" / "prompts" / "v5_all.jsonl"
TRAINING_DIR = BASE_DIR / "data" / "training"
OUTPUT_DIR = TRAINING_DIR / "ablation"

MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]
SEED = 2025

# Categories that use templates (borderline_edge_factual does not)
MAIN_CATEGORIES = ["factual", "nonexistent", "impossible", "ambiguous"]
BORDERLINE_CATEGORIES = ["borderline_obscure_real", "borderline_plausible_fake"]
NO_TEMPLATE_CATEGORY = "borderline_edge_factual"


def load_prompt_lookup():
    """Load v5_all.jsonl and build ID → {template, category, sub-type key} lookup."""
    lookup = {}
    with open(PROMPTS_PATH) as f:
        for line in f:
            r = json.loads(line)
            pid = r["id"]
            cat = r["category"]
            template = r.get("metadata", {}).get("template")
            # For borderline categories, the sub-type key combines category + entity_subtype
            # e.g. "borderline_obscure_real__people"
            entity_subtype = r.get("metadata", {}).get("entity_subtype")
            if cat in BORDERLINE_CATEGORIES and entity_subtype:
                subtype_key = f"{cat}__{entity_subtype}"
            else:
                subtype_key = None
            lookup[pid] = {
                "template": template,
                "category": cat,
                "subtype_key": subtype_key,
            }
    return lookup


def load_training_data(model):
    """Load best-per-prompt training data for a model."""
    path = TRAINING_DIR / f"v5_training_{model}.jsonl"
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records


def get_template_groups(records, lookup):
    """Group training record IDs by their template selection key.

    Returns:
      groups: dict mapping group_key → {template → [record_indices]}
      no_template_indices: list of indices for records without templates
    """
    groups = defaultdict(lambda: defaultdict(list))
    no_template_indices = []

    for i, r in enumerate(records):
        pid = r["id"]
        info = lookup.get(pid)
        if info is None:
            # ID not in v5_all — shouldn't happen
            print(f"  WARNING: {pid} not found in v5_all.jsonl")
            no_template_indices.append(i)
            continue

        cat = info["category"]
        template = info["template"]

        if cat == NO_TEMPLATE_CATEGORY:
            no_template_indices.append(i)
            continue

        if template is None:
            # Has a category but no template — treat like edge_factual
            no_template_indices.append(i)
            continue

        # For borderline categories, group by sub-type; for main categories, by category
        if info["subtype_key"]:
            group_key = info["subtype_key"]
        else:
            group_key = cat

        groups[group_key][template].append(i)

    return groups, no_template_indices


def select_templates(groups, n_templates):
    """Select first n_templates per group using seeded shuffle.

    Returns set of selected template strings and set of included record indices.
    """
    selected_templates = {}  # group_key → list of selected templates
    included_indices = set()

    for group_key in sorted(groups.keys()):
        templates_in_group = groups[group_key]
        rng = random.Random(SEED)
        templates_sorted = sorted(templates_in_group.keys())
        rng.shuffle(templates_sorted)
        chosen = templates_sorted[:n_templates]
        selected_templates[group_key] = chosen

        for tmpl in chosen:
            for idx in templates_in_group[tmpl]:
                included_indices.add(idx)

    return selected_templates, included_indices


def stratified_sample(records, lookup, target_cat_counts):
    """Stratified random sample matching target category counts exactly.

    target_cat_counts: dict of category → count (from T5's distribution).
    This ensures R{N} has the same category distribution as T5,
    isolating template diversity as the only variable.
    """
    rng = random.Random(SEED)

    # Group indices by category
    cat_indices = defaultdict(list)
    for i, r in enumerate(records):
        pid = r["id"]
        info = lookup.get(pid)
        cat = info["category"] if info else "unknown"
        cat_indices[cat].append(i)

    # Sample from each category to match target counts
    sampled_indices = set()
    for cat in sorted(target_cat_counts.keys()):
        n_cat = target_cat_counts[cat]
        pool = cat_indices.get(cat, [])[:]
        if len(pool) < n_cat:
            print(f"  WARNING: {cat} has {len(pool)} records but need {n_cat}")
            n_cat = len(pool)
        rng.shuffle(pool)
        sampled_indices.update(pool[:n_cat])

    return sampled_indices


def estimate_tokens(text):
    """Rough token estimate: ~4 chars per token."""
    return len(text) / 4


def to_together_format(record):
    """Convert a training record to Together AI messages format."""
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


def write_condition(records, indices, condition, model):
    """Write ablation files for a condition. Returns stats dict."""
    subset = [records[i] for i in sorted(indices)]

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
        "token_estimate": int(total_tokens),
    }


def main():
    print("=" * 60)
    print("Phase 9A: Template Diversity Ablation — Data Preparation")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load prompt lookup
    print("\nLoading prompt lookup from v5_all.jsonl...")
    lookup = load_prompt_lookup()
    print(f"  {len(lookup)} prompts loaded")

    report = {
        "conditions": {},
        "nesting_verified": True,
        "t1_exclusion_rationale": (
            "Only 179 prompts achievable (3-15 per category). "
            "Insufficient for fine-tuning."
        ),
        "seed": SEED,
    }

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        records = load_training_data(model)
        print(f"  {len(records)} training records loaded")

        # Build template groups
        groups, no_template_indices = get_template_groups(records, lookup)
        print(f"  {len(groups)} template groups, {len(no_template_indices)} no-template records")
        for gk in sorted(groups.keys()):
            print(f"    {gk}: {len(groups[gk])} templates, "
                  f"{sum(len(v) for v in groups[gk].values())} records")

        # === T5 ===
        print("\n--- T5: first 5 templates per group ---")
        t5_templates, t5_indices = select_templates(groups, 5)
        # Always include no-template records (edge_factual)
        t5_indices.update(no_template_indices)
        print(f"  {len(t5_indices)} records selected")
        stats = write_condition(records, t5_indices, "T5", model)

        # Per-category breakdown
        cat_counts = defaultdict(int)
        for i in t5_indices:
            pid = records[i]["id"]
            info = lookup.get(pid)
            cat_counts[info["category"] if info else "unknown"] += 1

        templates_used = sum(len(v) for v in t5_templates.values())
        t5_report = {
            **stats,
            "per_category": dict(sorted(cat_counts.items())),
            "templates_used": templates_used,
            "templates_per_group": {
                gk: tmpls for gk, tmpls in sorted(t5_templates.items())
            },
        }
        report["conditions"].setdefault("T5", {})[model] = t5_report

        for cat in sorted(cat_counts):
            print(f"    {cat}: {cat_counts[cat]}")

        # === R{N} (matched random control) ===
        t5_n = len(t5_indices)
        rn_label = f"R{t5_n}"
        print(f"\n--- {rn_label}: stratified random sample matching T5 category distribution ---")
        rn_indices = stratified_sample(records, lookup, dict(cat_counts))
        print(f"  {len(rn_indices)} records selected")
        stats = write_condition(records, rn_indices, rn_label, model)

        rn_cat_counts = defaultdict(int)
        for i in rn_indices:
            pid = records[i]["id"]
            info = lookup.get(pid)
            rn_cat_counts[info["category"] if info else "unknown"] += 1

        # Count unique templates in RN
        rn_templates = set()
        for i in rn_indices:
            pid = records[i]["id"]
            info = lookup.get(pid)
            if info and info["template"]:
                rn_templates.add(info["template"])

        rn_report = {
            **stats,
            "per_category": dict(sorted(rn_cat_counts.items())),
            "templates_used": len(rn_templates),
        }
        report["conditions"].setdefault(rn_label, {})[model] = rn_report

        for cat in sorted(rn_cat_counts):
            print(f"    {cat}: {rn_cat_counts[cat]}")

        # === T10 ===
        print("\n--- T10: first 10 templates per group ---")
        t10_templates, t10_indices = select_templates(groups, 10)
        t10_indices.update(no_template_indices)
        print(f"  {len(t10_indices)} records selected")
        stats = write_condition(records, t10_indices, "T10", model)

        t10_cat_counts = defaultdict(int)
        for i in t10_indices:
            pid = records[i]["id"]
            info = lookup.get(pid)
            t10_cat_counts[info["category"] if info else "unknown"] += 1

        t10_templates_used = sum(len(v) for v in t10_templates.values())
        t10_report = {
            **stats,
            "per_category": dict(sorted(t10_cat_counts.items())),
            "templates_used": t10_templates_used,
            "templates_per_group": {
                gk: tmpls for gk, tmpls in sorted(t10_templates.items())
            },
        }
        report["conditions"].setdefault("T10", {})[model] = t10_report

        for cat in sorted(t10_cat_counts):
            print(f"    {cat}: {t10_cat_counts[cat]}")

        # === T-all ===
        report["conditions"].setdefault("T-all", {})["note"] = (
            "existing v5_together files, not regenerated"
        )
        tall_cats = defaultdict(int)
        for r in records:
            info = lookup.get(r["id"])
            tall_cats[info["category"] if info else "unknown"] += 1
        report["conditions"]["T-all"][model] = {
            "total": len(records),
            "per_category": dict(sorted(tall_cats.items())),
        }

        # === Verify nesting: T5 ⊂ T10 ⊂ T-all ===
        t5_ids = {records[i]["id"] for i in t5_indices}
        t10_ids = {records[i]["id"] for i in t10_indices}
        all_ids = {r["id"] for r in records}

        nesting_ok = t5_ids.issubset(t10_ids) and t10_ids.issubset(all_ids)
        if nesting_ok:
            print(f"\n  Nesting verified: T5({len(t5_ids)}) ⊂ T10({len(t10_ids)}) ⊂ T-all({len(all_ids)})")
        else:
            print(f"\n  WARNING: Nesting FAILED!")
            if not t5_ids.issubset(t10_ids):
                diff = t5_ids - t10_ids
                print(f"    T5 has {len(diff)} IDs not in T10")
            if not t10_ids.issubset(all_ids):
                diff = t10_ids - all_ids
                print(f"    T10 has {len(diff)} IDs not in T-all")

        report["nesting_verified"] = report.get("nesting_verified", True) and nesting_ok

        # === Verify R{N} category proportions match T5 ===
        print(f"\n  Category proportion comparison (T5 vs {rn_label}):")
        for cat in sorted(set(list(cat_counts.keys()) + list(rn_cat_counts.keys()))):
            t5_frac = cat_counts.get(cat, 0) / t5_n if t5_n else 0
            rn_frac = rn_cat_counts.get(cat, 0) / len(rn_indices) if rn_indices else 0
            print(f"    {cat}: T5={cat_counts.get(cat, 0)} ({t5_frac:.3f}) "
                  f"{rn_label}={rn_cat_counts.get(cat, 0)} ({rn_frac:.3f})")

    # Write report
    report_path = OUTPUT_DIR / "ablation_report.json"
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
