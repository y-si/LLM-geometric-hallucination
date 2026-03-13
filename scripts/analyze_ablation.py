"""Step 9F Analysis: Template diversity ablation results.

Mirrors analyze_v5_finetuned.py structure. Compares ablation conditions
(T5/T10/R{N}/T-all) against V3 baseline, best prefix, and each other.

Key comparisons:
  - Each condition vs V3 baseline (does every condition still beat no-FT?)
  - Each condition vs T-all (does reducing templates hurt?)
  - T5 vs R{N} (template diversity vs dataset size)
  - Per-category breakdown
  - Template-overlap split (seen vs novel template accuracy on test set)

Usage:
    python3 scripts/analyze_ablation.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl

# ── Paths ──────────────────────────────────────────────────────────────────

V3_BASELINE_DIR = PROJECT_ROOT / "results" / "v3" / "multi_model" / "judged_recalibrated"
V4_PREFIX_DIR = PROJECT_ROOT / "results" / "v4_prefix_experiment"
V5_FINETUNED_DIR = PROJECT_ROOT / "results" / "v5_finetuned"
ABLATION_DIR = V5_FINETUNED_DIR / "ablation"
V3_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "prompts.jsonl"
ABLATION_REPORT_PATH = PROJECT_ROOT / "data" / "training" / "ablation" / "ablation_report.json"

OUTPUT_PATH = ABLATION_DIR / "ablation_analysis.json"

# Model short names → T-all config dirs (the existing best configs from Step 10/11)
TALL_CONFIGS = {
    "mixtral-8x7b": "configC",
    "llama-4-maverick-17b": "configA",
}

# Ablation condition labels per model
ABLATION_CONDITIONS = {
    "mixtral-8x7b": ["T5_mixtral", "T10_mixtral", "R397_mixtral"],
    "llama-4-maverick-17b": ["T5_llama", "T10_llama", "R402_llama"],
}

NON_COT_PREFIXES = ["entity_aware", "structured_caution", "epistemic_humility", "fact_grounded"]


# ── Helpers (same as analyze_v5_finetuned.py) ─────────────────────────────

def load_v3_prompts():
    """Load V3 prompts with metadata."""
    return read_jsonl(V3_PROMPTS_PATH)


def load_v3_ids():
    """Load the set of V3 prompt IDs."""
    return {p["id"] for p in load_v3_prompts()}


def deduplicate_results(results):
    """Remove duplicate entries (keep first occurrence per ID)."""
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

    map_a = {r["id"]: r["judge_label"] for r in results_a}
    map_b = {r["id"]: r["judge_label"] for r in results_b}

    common_ids = set(map_a.keys()) & set(map_b.keys())
    if id_filter:
        common_ids &= id_filter

    b_better = 0
    a_better = 0
    for pid in common_ids:
        a_correct = (map_a[pid] == 0)
        b_correct = (map_b[pid] == 0)
        if a_correct and not b_correct:
            a_better += 1
        elif b_correct and not a_correct:
            b_better += 1

    n = b_better + a_better
    if n == 0:
        return b_better, a_better, 0.0, 1.0

    chi2 = (abs(b_better - a_better) - 1) ** 2 / n
    p_value = 1 - chi2_dist.cdf(chi2, df=1)
    return b_better, a_better, chi2, p_value


# ── Template overlap ──────────────────────────────────────────────────────

def load_training_templates():
    """Load template lists per condition from ablation_report.json."""
    with open(ABLATION_REPORT_PATH) as f:
        report = json.load(f)

    templates = {}
    for cond_name, cond_data in report["conditions"].items():
        for model_key, model_data in cond_data.items():
            if isinstance(model_data, str):
                continue
            tpg = model_data.get("templates_per_group", {})
            if tpg:
                all_templates = set()
                for group_templates in tpg.values():
                    all_templates.update(group_templates)
                templates[f"{cond_name}_{model_key}"] = all_templates
    return templates


def compute_template_overlap(v3_prompts, training_templates):
    """Split V3 test prompts into seen/novel template groups.

    Returns {condition: {"seen_ids": set, "novel_ids": set, "no_template_ids": set}}
    """
    overlap = {}
    for cond_key, cond_templates in training_templates.items():
        seen_ids = set()
        novel_ids = set()
        no_template_ids = set()
        for p in v3_prompts:
            template = p.get("metadata", {}).get("template")
            if not template:
                no_template_ids.add(p["id"])
            elif template in cond_templates:
                seen_ids.add(p["id"])
            else:
                novel_ids.add(p["id"])
        overlap[cond_key] = {
            "seen_ids": seen_ids,
            "novel_ids": novel_ids,
            "no_template_ids": no_template_ids,
        }
    return overlap


# ── Main Analysis ──────────────────────────────────────────────────────────

def main():
    v3_prompts = load_v3_prompts()
    v3_ids = {p["id"] for p in v3_prompts}
    print(f"V3 held-out test set: {len(v3_ids)} prompts\n")

    # Load template overlap info
    training_templates = load_training_templates()
    template_overlap = compute_template_overlap(v3_prompts, training_templates)

    report = {}

    for model in ["mixtral-8x7b", "llama-4-maverick-17b"]:
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
            print(f"\n  Best Single Prefix ({best_prefix_name}):")
            print(f"    {best_prefix_stats['correct']}/{best_prefix_stats['total']} correct "
                  f"({best_prefix_stats['accuracy']*100:.1f}%), "
                  f"{best_prefix_stats['hallucination']} halluc "
                  f"({best_prefix_stats['hallucination_rate']*100:.1f}%)")

        # ── Load T-all (existing best FT config) ──
        tall_config = TALL_CONFIGS[model]
        tall_path = V5_FINETUNED_DIR / model / tall_config / "judged_answers.jsonl"
        if not tall_path.exists():
            print(f"  T-all ({tall_config}) not found at {tall_path}, skipping")
            continue
        tall_results = read_jsonl(tall_path)
        tall_stats = label_stats(tall_results, v3_ids)
        print(f"\n  T-all ({tall_config}, all templates):")
        print(f"    {tall_stats['correct']}/{tall_stats['total']} correct "
              f"({tall_stats['accuracy']*100:.1f}%), "
              f"{tall_stats['hallucination']} halluc ({tall_stats['hallucination_rate']*100:.1f}%)")

        # ── Load ablation conditions ──
        model_report = {
            "baseline": bl_stats,
            "best_prefix": {"name": best_prefix_name, **best_prefix_stats} if best_prefix_stats else None,
            "t_all": {"config": tall_config, **tall_stats},
            "ablation": {},
        }

        conditions = ABLATION_CONDITIONS[model]
        all_condition_results = {}  # label -> results list, for cross-condition McNemar

        for cond_label in conditions:
            judged_path = ABLATION_DIR / cond_label / "judged_answers.jsonl"
            if not judged_path.exists():
                print(f"\n  {cond_label}: judged_answers.jsonl not found, skipping")
                continue

            cond_results = read_jsonl(judged_path)
            all_condition_results[cond_label] = cond_results
            cond_stats = label_stats(cond_results, v3_ids)

            print(f"\n  {cond_label}:")
            print(f"    {cond_stats['correct']}/{cond_stats['total']} correct "
                  f"({cond_stats['accuracy']*100:.1f}%), "
                  f"{cond_stats['hallucination']} halluc "
                  f"({cond_stats['hallucination_rate']*100:.1f}%)")

            # McNemar vs baseline
            ft_better, bl_better, chi2, p = mcnemar_test(v3_baseline, cond_results, v3_ids)
            print(f"    vs Baseline: FT fixes {ft_better}, FT breaks {bl_better}, "
                  f"chi2={chi2:.2f}, p={p:.4f}")

            # McNemar vs T-all
            tall_better, cond_better, chi2_tall, p_tall = mcnemar_test(
                cond_results, tall_results, v3_ids)
            print(f"    vs T-all: T-all fixes {tall_better}, {cond_label} fixes {cond_better}, "
                  f"chi2={chi2_tall:.2f}, p={p_tall:.4f}")

            # McNemar vs best prefix
            mcnemar_prefix = {}
            if best_prefix_results:
                ft_better_pf, pf_better, chi2_pf, p_pf = mcnemar_test(
                    best_prefix_results, cond_results, v3_ids)
                print(f"    vs Best Prefix ({best_prefix_name}): FT fixes {ft_better_pf}, "
                      f"Prefix fixes {pf_better}, chi2={chi2_pf:.2f}, p={p_pf:.4f}")
                mcnemar_prefix = {
                    "ft_fixes": ft_better_pf, "prefix_fixes": pf_better,
                    "chi2": chi2_pf, "p_value": p_pf,
                }

            # Per-category
            cond_cats = per_category_stats(cond_results, v3_ids)
            bl_cats = per_category_stats(v3_baseline, v3_ids)

            print(f"\n    {'Category':<30s} {'BL Acc':>7s} {'FT Acc':>7s} {'Diff':>7s} "
                  f"{'BL Hal':>7s} {'FT Hal':>7s}")
            print(f"    {'-'*30} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
            for cat in sorted(cond_cats.keys()):
                bl_cat = bl_cats.get(cat, {"accuracy": 0, "hallucination_rate": 0})
                ft_cat = cond_cats[cat]
                diff = ft_cat["accuracy"] - bl_cat.get("accuracy", 0)
                print(f"    {cat:<30s} "
                      f"{bl_cat.get('accuracy', 0)*100:>6.1f}% "
                      f"{ft_cat['accuracy']*100:>6.1f}% "
                      f"{diff*100:>+6.1f}% "
                      f"{bl_cat.get('hallucination_rate', 0)*100:>6.1f}% "
                      f"{ft_cat['hallucination_rate']*100:>6.1f}%")

            # Template overlap split
            template_split = {}
            # Map condition label to template key (e.g. T5_mixtral -> T5_mixtral-8x7b)
            cond_prefix = cond_label.split("_")[0]  # T5, T10, R397, R402
            template_key = f"{cond_prefix}_{model}"
            if template_key in template_overlap:
                overlap_info = template_overlap[template_key]
                seen_stats = label_stats(cond_results, overlap_info["seen_ids"])
                novel_stats = label_stats(cond_results, overlap_info["novel_ids"])
                no_tmpl_stats = label_stats(cond_results, overlap_info["no_template_ids"])

                print(f"\n    Template overlap split:")
                print(f"      Seen templates:    {seen_stats.get('total', 0):>3d} prompts, "
                      f"acc={seen_stats.get('accuracy', 0)*100:.1f}%, "
                      f"hal={seen_stats.get('hallucination_rate', 0)*100:.1f}%")
                print(f"      Novel templates:   {novel_stats.get('total', 0):>3d} prompts, "
                      f"acc={novel_stats.get('accuracy', 0)*100:.1f}%, "
                      f"hal={novel_stats.get('hallucination_rate', 0)*100:.1f}%")
                print(f"      No template (borderline): {no_tmpl_stats.get('total', 0):>3d} prompts, "
                      f"acc={no_tmpl_stats.get('accuracy', 0)*100:.1f}%, "
                      f"hal={no_tmpl_stats.get('hallucination_rate', 0)*100:.1f}%")

                template_split = {
                    "seen": {**seen_stats, "n_prompts": len(overlap_info["seen_ids"])},
                    "novel": {**novel_stats, "n_prompts": len(overlap_info["novel_ids"])},
                    "no_template": {**no_tmpl_stats, "n_prompts": len(overlap_info["no_template_ids"])},
                }
            else:
                # R{N} uses all templates — all 368 with-template prompts are "seen"
                print(f"\n    Template overlap: R{{N}} uses full template pool (all seen)")

            model_report["ablation"][cond_label] = {
                "aggregate": cond_stats,
                "per_category": cond_cats,
                "mcnemar_vs_baseline": {
                    "ft_fixes": ft_better, "ft_breaks": bl_better,
                    "chi2": chi2, "p_value": p,
                },
                "mcnemar_vs_tall": {
                    "tall_fixes": tall_better, "cond_fixes": cond_better,
                    "chi2": chi2_tall, "p_value": p_tall,
                },
                "mcnemar_vs_best_prefix": mcnemar_prefix,
                "template_split": template_split,
            }

        # ── T5 vs R{N} (the key diversity-vs-size comparison) ──
        # Identify which conditions are T5 and R{N} for this model
        t5_label = f"T5_{model.split('-')[0]}"  # T5_mixtral or T5_llama
        rn_label = [c for c in conditions if c.startswith("R")][0] if any(c.startswith("R") for c in conditions) else None

        if t5_label in all_condition_results and rn_label and rn_label in all_condition_results:
            t5_results = all_condition_results[t5_label]
            rn_results = all_condition_results[rn_label]
            rn_better, t5_better, chi2_tr, p_tr = mcnemar_test(t5_results, rn_results, v3_ids)

            print(f"\n  ── KEY TEST: {t5_label} vs {rn_label} (diversity vs size) ──")
            print(f"    Same N (~{label_stats(t5_results, v3_ids)['total']}), "
                  f"different template count (50 vs ~194)")
            t5_s = label_stats(t5_results, v3_ids)
            rn_s = label_stats(rn_results, v3_ids)
            print(f"    {t5_label}: {t5_s['accuracy']*100:.1f}% acc, "
                  f"{t5_s['hallucination_rate']*100:.1f}% hal")
            print(f"    {rn_label}: {rn_s['accuracy']*100:.1f}% acc, "
                  f"{rn_s['hallucination_rate']*100:.1f}% hal")
            print(f"    McNemar: {rn_label} fixes {rn_better}, {t5_label} fixes {t5_better}, "
                  f"chi2={chi2_tr:.2f}, p={p_tr:.4f}")

            model_report["t5_vs_rn"] = {
                "t5_label": t5_label,
                "rn_label": rn_label,
                "t5_stats": t5_s,
                "rn_stats": rn_s,
                "mcnemar": {
                    "rn_fixes": rn_better, "t5_fixes": t5_better,
                    "chi2": chi2_tr, "p_value": p_tr,
                },
            }

        report[model] = model_report

    # ── Summary table ──
    print(f"\n\n{'='*70}")
    print(f"  SUMMARY COMPARISON")
    print(f"{'='*70}")

    header = f"  {'Condition':<35s} {'Mixtral Acc':>12s} {'Llama Acc':>12s}"
    print(f"\n{header}")
    print(f"  {'-'*35} {'-'*12} {'-'*12}")

    def get_acc(model_key, path_fn):
        mr = report.get(model_key, {})
        return path_fn(mr)

    # Baseline
    m_bl = report.get("mixtral-8x7b", {}).get("baseline", {}).get("accuracy")
    l_bl = report.get("llama-4-maverick-17b", {}).get("baseline", {}).get("accuracy")
    print(f"  {'Baseline (no prefix)':<35s} "
          f"{m_bl*100:>11.1f}% {l_bl*100:>11.1f}%")

    # Best prefix
    m_bp = report.get("mixtral-8x7b", {}).get("best_prefix", {}).get("accuracy")
    l_bp = report.get("llama-4-maverick-17b", {}).get("best_prefix", {}).get("accuracy")
    m_bp_name = report.get("mixtral-8x7b", {}).get("best_prefix", {}).get("name", "?")
    l_bp_name = report.get("llama-4-maverick-17b", {}).get("best_prefix", {}).get("name", "?")
    print(f"  {'Best prefix (' + m_bp_name + '/' + l_bp_name + ')':<35s} "
          f"{m_bp*100:>11.1f}% {l_bp*100:>11.1f}%")

    # Ablation conditions (ordered by template count)
    for t5, t10, rn in [
        ("T5_mixtral", "T10_mixtral", "R397_mixtral"),
        ("T5_llama", "T10_llama", "R402_llama"),
    ]:
        pass  # handled below

    # Print each condition row
    condition_order = [
        ("FT: T5 (5 templates)", "T5_mixtral", "T5_llama"),
        ("FT: R{N} (all tmpl, T5 size)", "R397_mixtral", "R402_llama"),
        ("FT: T10 (10 templates)", "T10_mixtral", "T10_llama"),
        ("FT: T-all (all templates)", None, None),  # from t_all
    ]

    for row_label, m_cond, l_cond in condition_order:
        if m_cond is None:
            # T-all
            m_acc = report.get("mixtral-8x7b", {}).get("t_all", {}).get("accuracy")
            l_acc = report.get("llama-4-maverick-17b", {}).get("t_all", {}).get("accuracy")
        else:
            m_acc = report.get("mixtral-8x7b", {}).get("ablation", {}).get(m_cond, {}).get("aggregate", {}).get("accuracy")
            l_acc = report.get("llama-4-maverick-17b", {}).get("ablation", {}).get(l_cond, {}).get("aggregate", {}).get("accuracy")
        m_str = f"{m_acc*100:.1f}%" if m_acc is not None else "N/A"
        l_str = f"{l_acc*100:.1f}%" if l_acc is not None else "N/A"
        print(f"  {row_label:<35s} {m_str:>12s} {l_str:>12s}")

    # Save report
    with open(OUTPUT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Full report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
