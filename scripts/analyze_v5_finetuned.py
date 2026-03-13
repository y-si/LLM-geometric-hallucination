"""Step 11 Analysis: Compare fine-tuned models to all baselines on V3 held-out set.

Loads V3 baseline, V4 prefix, and V5 fine-tuned results, then produces:
  - Aggregate hallucination rate comparison across all conditions
  - Per-category breakdown
  - McNemar's test (fine-tuned vs baseline, fine-tuned vs best-prefix)
  - Hyperparameter sensitivity (A vs B vs C for Mixtral)

Usage:
    python3 scripts/analyze_v5_finetuned.py

Requires Step 11 judged results in results/v5_finetuned/.
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl

# ── Paths ──────────────────────────────────────────────────────────────────

V3_BASELINE_DIR = PROJECT_ROOT / "results" / "v3" / "multi_model" / "judged_recalibrated"
V4_PREFIX_DIR = PROJECT_ROOT / "results" / "v4_prefix_experiment"
V5_FINETUNED_DIR = PROJECT_ROOT / "results" / "v5_finetuned"
V3_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "prompts.jsonl"

MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]
NON_COT_PREFIXES = ["entity_aware", "structured_caution", "epistemic_humility", "fact_grounded"]

OUTPUT_PATH = V5_FINETUNED_DIR / "comparison_analysis.json"


# ── Helpers ────────────────────────────────────────────────────────────────

def load_v3_ids():
    """Load the set of V3 prompt IDs."""
    prompts = read_jsonl(V3_PROMPTS_PATH)
    return {p["id"] for p in prompts}


def deduplicate_results(results):
    """Remove duplicate entries (keep first occurrence per ID).

    The V3 baseline files have 538 entries with 453 unique IDs — borderline
    prompts are duplicated (some with inconsistent labels).  Deduplicating
    to first-occurrence ensures each prompt is counted exactly once.
    """
    seen = set()
    deduped = []
    for r in results:
        if r["id"] not in seen:
            deduped.append(r)
            seen.add(r["id"])
    return deduped


def label_stats(results, id_filter=None):
    """Compute label distribution from judged results."""
    if id_filter:
        results = [r for r in results if r["id"] in id_filter]
    total = len(results)
    if total == 0:
        return {"total": 0}
    labels = [r["judge_label"] for r in results]
    correct = labels.count(0)
    halluc = labels.count(2)
    return {
        "total": total,
        "correct": correct,
        "partial": labels.count(1),
        "hallucination": halluc,
        "refusal": labels.count(3),
        "accuracy": correct / total,
        "hallucination_rate": halluc / total,
    }


def per_category_stats(results, id_filter=None):
    """Compute per-category label distribution."""
    if id_filter:
        results = [r for r in results if r["id"] in id_filter]
    cats = sorted(set(r["category"] for r in results))
    out = {}
    for cat in cats:
        cat_results = [r for r in results if r["category"] == cat]
        out[cat] = label_stats(cat_results)
    return out


def mcnemar_test(results_a, results_b, id_filter=None):
    """McNemar's test comparing two conditions on paired prompts.

    Returns (b_better, a_better, chi2, p_value).
    b_better = prompts where B is correct but A is not.
    a_better = prompts where A is correct but B is not.
    """
    from scipy.stats import chi2 as chi2_dist

    # Build per-ID label maps
    map_a = {r["id"]: r["judge_label"] for r in results_a}
    map_b = {r["id"]: r["judge_label"] for r in results_b}

    common_ids = set(map_a.keys()) & set(map_b.keys())
    if id_filter:
        common_ids &= id_filter

    # Count discordant pairs (correct = label 0, incorrect = anything else)
    b_better = 0  # A wrong, B correct
    a_better = 0  # A correct, B wrong
    for pid in common_ids:
        a_correct = (map_a[pid] == 0)
        b_correct = (map_b[pid] == 0)
        if a_correct and not b_correct:
            a_better += 1
        elif b_correct and not a_correct:
            b_better += 1

    # McNemar's chi-squared (with continuity correction)
    n = b_better + a_better
    if n == 0:
        return b_better, a_better, 0.0, 1.0

    chi2 = (abs(b_better - a_better) - 1) ** 2 / n
    p_value = 1 - chi2_dist.cdf(chi2, df=1)
    return b_better, a_better, chi2, p_value


# ── Main Analysis ──────────────────────────────────────────────────────────

def main():
    v3_ids = load_v3_ids()
    print(f"V3 held-out test set: {len(v3_ids)} prompts\n")

    report = {}

    for model in MODELS:
        print(f"\n{'='*70}")
        print(f"  MODEL: {model}")
        print(f"{'='*70}")

        # ── Load V3 baseline ──
        v3_path = V3_BASELINE_DIR / f"judged_answers_{model}.jsonl"
        if not v3_path.exists():
            print(f"  V3 baseline not found at {v3_path}, skipping")
            continue
        v3_baseline = deduplicate_results(read_jsonl(v3_path))
        bl_stats = label_stats(v3_baseline, v3_ids)
        print(f"\n  V3 Baseline (no prefix):")
        print(f"    {bl_stats['correct']}/{bl_stats['total']} correct "
              f"({bl_stats['accuracy']*100:.1f}%), "
              f"{bl_stats['hallucination']} halluc ({bl_stats['hallucination_rate']*100:.1f}%)")

        # ── Load V4 best single prefix ──
        best_prefix_name = None
        best_prefix_stats = None
        best_prefix_results = None
        for prefix in NON_COT_PREFIXES:
            pf_path = V4_PREFIX_DIR / model / prefix / "judged_answers.jsonl"
            if not pf_path.exists():
                continue
            pf_results = deduplicate_results(read_jsonl(pf_path))
            pf_stats = label_stats(pf_results, v3_ids)
            if best_prefix_stats is None or pf_stats["accuracy"] > best_prefix_stats["accuracy"]:
                best_prefix_name = prefix
                best_prefix_stats = pf_stats
                best_prefix_results = pf_results

        if best_prefix_stats:
            print(f"\n  V4 Best Single Prefix ({best_prefix_name}):")
            print(f"    {best_prefix_stats['correct']}/{best_prefix_stats['total']} correct "
                  f"({best_prefix_stats['accuracy']*100:.1f}%), "
                  f"{best_prefix_stats['hallucination']} halluc "
                  f"({best_prefix_stats['hallucination_rate']*100:.1f}%)")

        # ── Load V4 best-per-prompt oracle ──
        # For each prompt, pick the best label across all non-CoT prefixes + baseline
        oracle_labels = {}
        all_v4_sources = {"baseline": v3_baseline}
        for prefix in NON_COT_PREFIXES:
            pf_path = V4_PREFIX_DIR / model / prefix / "judged_answers.jsonl"
            if pf_path.exists():
                all_v4_sources[prefix] = deduplicate_results(read_jsonl(pf_path))

        for pid in v3_ids:
            best_label = None
            label_priority = {0: 0, 1: 1, 3: 2, 2: 3}
            for source_name, source_results in all_v4_sources.items():
                for r in source_results:
                    if r["id"] == pid:
                        label = r["judge_label"]
                        priority = label_priority.get(label, 99)
                        if best_label is None or priority < label_priority.get(best_label, 99):
                            best_label = label
                        break
            if best_label is not None:
                oracle_labels[pid] = best_label

        oracle_correct = sum(1 for l in oracle_labels.values() if l == 0)
        oracle_total = len(oracle_labels)
        oracle_halluc = sum(1 for l in oracle_labels.values() if l == 2)
        if oracle_total > 0:
            print(f"\n  V4 Best-per-prompt Oracle:")
            print(f"    {oracle_correct}/{oracle_total} correct "
                  f"({oracle_correct/oracle_total*100:.1f}%), "
                  f"{oracle_halluc} halluc ({oracle_halluc/oracle_total*100:.1f}%)")

        # ── Load fine-tuned results ──
        model_report = {
            "baseline": bl_stats,
            "best_prefix": {"name": best_prefix_name, **best_prefix_stats} if best_prefix_stats else None,
            "oracle": {
                "total": oracle_total, "correct": oracle_correct,
                "hallucination": oracle_halluc,
                "accuracy": oracle_correct / oracle_total if oracle_total > 0 else 0,
            },
            "finetuned": {},
        }

        ft_configs = []
        for config_dir in sorted((V5_FINETUNED_DIR / model).iterdir()) if (V5_FINETUNED_DIR / model).exists() else []:
            if not config_dir.is_dir():
                continue
            judged_path = config_dir / "judged_answers.jsonl"
            if not judged_path.exists():
                continue
            ft_configs.append((config_dir.name, read_jsonl(judged_path)))

        if not ft_configs:
            print(f"\n  No fine-tuned results found for {model}")
            report[model] = model_report
            continue

        for config_name, ft_results in ft_configs:
            ft_stats = label_stats(ft_results, v3_ids)
            print(f"\n  Fine-tuned {config_name}:")
            print(f"    {ft_stats['correct']}/{ft_stats['total']} correct "
                  f"({ft_stats['accuracy']*100:.1f}%), "
                  f"{ft_stats['hallucination']} halluc "
                  f"({ft_stats['hallucination_rate']*100:.1f}%)")

            # McNemar vs baseline
            ft_better, bl_better, chi2, p = mcnemar_test(v3_baseline, ft_results, v3_ids)
            print(f"    vs Baseline: FT fixes {ft_better}, FT breaks {bl_better}, "
                  f"chi2={chi2:.2f}, p={p:.4f}")

            # McNemar vs best prefix
            if best_prefix_results:
                ft_better_pf, pf_better, chi2_pf, p_pf = mcnemar_test(
                    best_prefix_results, ft_results, v3_ids)
                print(f"    vs Best Prefix ({best_prefix_name}): FT fixes {ft_better_pf}, "
                      f"Prefix fixes {pf_better}, chi2={chi2_pf:.2f}, p={p_pf:.4f}")
            else:
                chi2_pf, p_pf, ft_better_pf, pf_better = 0, 1, 0, 0

            # Per-category
            ft_cats = per_category_stats(ft_results, v3_ids)
            bl_cats = per_category_stats(v3_baseline, v3_ids)

            print(f"\n    {'Category':<30s} {'BL Acc':>7s} {'FT Acc':>7s} {'Diff':>7s} "
                  f"{'BL Hal':>7s} {'FT Hal':>7s}")
            print(f"    {'-'*30} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
            for cat in sorted(ft_cats.keys()):
                bl_cat = bl_cats.get(cat, {"accuracy": 0, "hallucination_rate": 0})
                ft_cat = ft_cats[cat]
                diff = ft_cat["accuracy"] - bl_cat.get("accuracy", 0)
                print(f"    {cat:<30s} "
                      f"{bl_cat.get('accuracy', 0)*100:>6.1f}% "
                      f"{ft_cat['accuracy']*100:>6.1f}% "
                      f"{diff*100:>+6.1f}% "
                      f"{bl_cat.get('hallucination_rate', 0)*100:>6.1f}% "
                      f"{ft_cat['hallucination_rate']*100:>6.1f}%")

            model_report["finetuned"][config_name] = {
                "aggregate": ft_stats,
                "per_category": ft_cats,
                "mcnemar_vs_baseline": {
                    "ft_fixes": ft_better, "ft_breaks": bl_better,
                    "chi2": chi2, "p_value": p,
                },
                "mcnemar_vs_best_prefix": {
                    "ft_fixes": ft_better_pf, "prefix_fixes": pf_better,
                    "chi2": chi2_pf, "p_value": p_pf,
                },
            }

        report[model] = model_report

    # ── Hyperparameter sensitivity (Mixtral A vs B vs C) ──
    mixtral_configs = report.get("mixtral-8x7b", {}).get("finetuned", {})
    if len(mixtral_configs) > 1:
        print(f"\n\n{'='*70}")
        print(f"  HYPERPARAMETER SENSITIVITY (Mixtral)")
        print(f"{'='*70}")
        print(f"\n  {'Config':<12s} {'Accuracy':>10s} {'Halluc Rate':>12s} {'Correct':>8s}")
        print(f"  {'-'*12} {'-'*10} {'-'*12} {'-'*8}")
        for cfg_name in sorted(mixtral_configs.keys()):
            s = mixtral_configs[cfg_name]["aggregate"]
            print(f"  {cfg_name:<12s} {s['accuracy']*100:>9.1f}% "
                  f"{s['hallucination_rate']*100:>11.1f}% {s['correct']:>8d}")

    # ── Summary table ──
    print(f"\n\n{'='*70}")
    print(f"  SUMMARY COMPARISON")
    print(f"{'='*70}")
    print(f"\n  {'Condition':<35s} {'Mixtral Acc':>12s} {'Llama Acc':>12s}")
    print(f"  {'-'*35} {'-'*12} {'-'*12}")

    for model in MODELS:
        mr = report.get(model, {})
        bl = mr.get("baseline", {})
        if model == "mixtral-8x7b":
            mixtral_bl = f"{bl.get('accuracy', 0)*100:.1f}%" if bl else "N/A"
        else:
            llama_bl = f"{bl.get('accuracy', 0)*100:.1f}%" if bl else "N/A"
    print(f"  {'Baseline (no prefix)':<35s} {mixtral_bl:>12s} {llama_bl:>12s}")

    for model in MODELS:
        mr = report.get(model, {})
        bp = mr.get("best_prefix", {})
        if model == "mixtral-8x7b":
            mixtral_bp = f"{bp.get('accuracy', 0)*100:.1f}%" if bp else "N/A"
        else:
            llama_bp = f"{bp.get('accuracy', 0)*100:.1f}%" if bp else "N/A"
    print(f"  {'Best single prefix (V4)':<35s} {mixtral_bp:>12s} {llama_bp:>12s}")

    for model in MODELS:
        mr = report.get(model, {})
        orc = mr.get("oracle", {})
        if model == "mixtral-8x7b":
            mixtral_orc = f"{orc.get('accuracy', 0)*100:.1f}%" if orc else "N/A"
        else:
            llama_orc = f"{orc.get('accuracy', 0)*100:.1f}%" if orc else "N/A"
    print(f"  {'Best-per-prompt oracle (V4)':<35s} {mixtral_orc:>12s} {llama_orc:>12s}")

    # Fine-tuned (primary config = A)
    for model in MODELS:
        mr = report.get(model, {})
        ft = mr.get("finetuned", {})
        cfg_a = ft.get("configA", {}).get("aggregate", {})
        if model == "mixtral-8x7b":
            mixtral_ft = f"{cfg_a.get('accuracy', 0)*100:.1f}%" if cfg_a else "N/A"
        else:
            llama_ft = f"{cfg_a.get('accuracy', 0)*100:.1f}%" if cfg_a else "N/A"
    print(f"  {'Fine-tuned configA (no prefix)':<35s} {mixtral_ft:>12s} {llama_ft:>12s}")

    # Save report
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Full report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
