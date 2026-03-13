"""Pre-registered sensitivity/robustness checks for the consensus judging pipeline.

Implements three checks from Section 4.3.7 of setup.tex:
  1. Unanimous-only aggregation: re-compute headline metrics using only prompts
     where all 3 judges agree.
  2. Judge removal analysis: re-compute majority vote from each 2-of-3 subset.
  3. Self-evaluation bias check: compare Llama judge labels (index 2) on
     Llama-generated vs Mixtral-generated responses.

Judge ordering (all scripts): [GPT-5.1, Claude Opus 4.5, Llama 4 Maverick]
  - Index 0: GPT-5.1
  - Index 1: Claude Opus 4.5
  - Index 2: Llama 4 Maverick

Usage:
    python3 scripts/sensitivity_analysis.py
    python3 scripts/sensitivity_analysis.py --dataset v5_baselines
    python3 scripts/sensitivity_analysis.py --dataset v5_finetuned
    python3 scripts/sensitivity_analysis.py --dataset all

Output:
    results/sensitivity_analysis.json
"""

import json
import sys
from collections import Counter
from pathlib import Path
from itertools import combinations

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl

# ── Configuration ─────────────────────────────────────────────────────────

JUDGE_NAMES = ["gpt-5.1", "claude-opus-4.5", "llama-4-maverick"]

DATASETS = {
    "v5_baselines": {
        "mixtral": PROJECT_ROOT / "results" / "v5_baselines" / "mixtral-8x7b" / "no_prefix" / "judged_answers.jsonl",
        "llama": PROJECT_ROOT / "results" / "v5_baselines" / "llama-4-maverick-17b" / "no_prefix" / "judged_answers.jsonl",
    },
    "v5_prefixes": {
        f"{model}_{prefix}": PROJECT_ROOT / "results" / "v5_prefixes" / model_dir / prefix / "judged_answers.jsonl"
        for model, model_dir in [("mixtral", "mixtral-8x7b"), ("llama", "llama-4-maverick-17b")]
        # CoT excluded from thesis — 65% of entries had 2+ failed judges (see JUDGE_CONTAMINATION_ISSUE.md)
        for prefix in ["entity_aware", "structured_caution", "epistemic_humility", "fact_grounded"]
    },
    "v5_finetuned": {
        f"{model}_{config}": path
        for model, model_dir in [("mixtral", "mixtral-8x7b"), ("llama", "llama-4-maverick-17b")]
        for config in ["configA", "configB", "configC"]
        if (path := PROJECT_ROOT / "results" / "v5_finetuned" / model_dir / config / "judged_answers.jsonl").exists()
    },
    "ablation": {
        label: PROJECT_ROOT / "results" / "v5_finetuned" / "ablation" / label / "judged_answers.jsonl"
        for label in ["T5_mixtral", "T10_mixtral", "R397_mixtral", "T5_llama", "T10_llama", "R402_llama"]
    },
}


def label_stats(labels):
    """Compute accuracy, hallucination rate, and counts from a list of labels."""
    total = len(labels)
    if total == 0:
        return {"total": 0}
    counts = Counter(labels)
    return {
        "total": total,
        "correct": counts[0],
        "partial": counts[1],
        "hallucination": counts[2],
        "refusal": counts[3],
        "accuracy": counts[0] / total,
        "hallucination_rate": counts[2] / total,
    }


def is_failed_judge(judgment):
    """Detect a failed judge: confidence=0.0 AND error in justification."""
    if judgment.get("confidence") != 0.0:
        return False
    justification = str(judgment.get("justification", ""))
    return "Error" in justification or "error" in justification


def majority_vote_2of3(judgments, exclude_idx):
    """Compute majority vote from 2 judges (excluding one).

    Filters out failed judges from the remaining pair. If only one real
    judge remains, returns that judge's label. If both are failed, returns None.
    """
    remaining = [j for i, j in enumerate(judgments) if i != exclude_idx]
    if len(remaining) != 2:
        return None
    # Filter out failed judges from the remaining pair
    real = [j for j in remaining if not is_failed_judge(j)]
    if len(real) == 0:
        return None  # Both remaining judges failed
    if len(real) == 1:
        return real[0]["label"]  # Only one real judge left
    # Both real: standard 2-judge vote
    if real[0]["label"] == real[1]["label"]:
        return real[0]["label"]
    # Tie: use higher confidence, then panel order
    if real[0]["confidence"] > real[1]["confidence"]:
        return real[0]["label"]
    elif real[1]["confidence"] > real[0]["confidence"]:
        return real[1]["label"]
    return real[0]["label"]  # Equal confidence: first in panel order


def load_dataset(name):
    """Load all judged answers for a dataset group. Returns flat list."""
    if name not in DATASETS:
        return []
    all_data = []
    for label, path in DATASETS[name].items():
        if path.exists():
            data = read_jsonl(path)
            for d in data:
                d["_source"] = label
            all_data.extend(data)
    return all_data


# ── Check 1: Unanimous-only aggregation ──────────────────────────────────

def check_unanimous(data, source_label="all"):
    """Filter to unanimous-only, re-compute headline metrics."""
    unanimous = [d for d in data if d.get("agreement_rate", 0) == 1.0]
    all_labels = [d["judge_label"] for d in data]
    unan_labels = [d["judge_label"] for d in unanimous]

    result = {
        "source": source_label,
        "total_all": len(data),
        "total_unanimous": len(unanimous),
        "fraction_unanimous": len(unanimous) / len(data) if data else 0,
        "all_data": label_stats(all_labels),
        "unanimous_only": label_stats(unan_labels),
    }

    # Per-category
    categories = sorted(set(d["category"] for d in data))
    result["per_category"] = {}
    for cat in categories:
        cat_all = [d for d in data if d["category"] == cat]
        cat_unan = [d for d in unanimous if d["category"] == cat]
        result["per_category"][cat] = {
            "total_all": len(cat_all),
            "total_unanimous": len(cat_unan),
            "fraction_unanimous": len(cat_unan) / len(cat_all) if cat_all else 0,
            "all_accuracy": label_stats([d["judge_label"] for d in cat_all])["accuracy"] if cat_all else None,
            "unanimous_accuracy": label_stats([d["judge_label"] for d in cat_unan])["accuracy"] if cat_unan else None,
        }

    return result


# ── Check 2: Judge removal analysis ──────────────────────────────────────

def check_judge_removal(data, source_label="all"):
    """Recompute consensus from each 2-of-3 judge subset."""
    result = {
        "source": source_label,
        "total": len(data),
        "original": label_stats([d["judge_label"] for d in data]),
        "subsets": {},
    }

    for exclude_idx in range(3):
        excluded_name = JUDGE_NAMES[exclude_idx]
        kept = [JUDGE_NAMES[i] for i in range(3) if i != exclude_idx]
        subset_key = f"without_{excluded_name}"

        new_labels = []
        changed = 0
        for d in data:
            judgments = d.get("individual_judgments", [])
            if len(judgments) < 3:
                new_labels.append(d["judge_label"])
                continue
            new_label = majority_vote_2of3(judgments, exclude_idx)
            if new_label is None:
                new_labels.append(d["judge_label"])
            else:
                if new_label != d["judge_label"]:
                    changed += 1
                new_labels.append(new_label)

        result["subsets"][subset_key] = {
            "kept_judges": kept,
            "excluded_judge": excluded_name,
            "labels_changed": changed,
            "fraction_changed": changed / len(data) if data else 0,
            **label_stats(new_labels),
        }

    return result


# ── Check 3: Self-evaluation bias ────────────────────────────────────────

def check_self_eval_bias(data, source_label="all"):
    """Compare Llama judge (index 2) labels on Llama vs Mixtral responses."""
    # Split by target model
    llama_gen = [d for d in data if "llama" in d.get("model", "").lower()]
    mixtral_gen = [d for d in data if "mixtral" in d.get("model", "").lower()]

    def llama_judge_stats(subset):
        labels = []
        for d in subset:
            judgments = d.get("individual_judgments", [])
            if len(judgments) >= 3:
                labels.append(judgments[2]["label"])
        return label_stats(labels)

    def consensus_stats(subset):
        return label_stats([d["judge_label"] for d in subset])

    llama_on_llama = llama_judge_stats(llama_gen)
    llama_on_mixtral = llama_judge_stats(mixtral_gen)

    # Also compare consensus (all 3 judges) for reference
    consensus_on_llama = consensus_stats(llama_gen)
    consensus_on_mixtral = consensus_stats(mixtral_gen)

    result = {
        "source": source_label,
        "llama_generated_n": len(llama_gen),
        "mixtral_generated_n": len(mixtral_gen),
        "llama_judge_on_llama_responses": llama_on_llama,
        "llama_judge_on_mixtral_responses": llama_on_mixtral,
        "consensus_on_llama_responses": consensus_on_llama,
        "consensus_on_mixtral_responses": consensus_on_mixtral,
    }

    # Compute bias metrics if both have data
    if llama_on_llama.get("total", 0) > 0 and llama_on_mixtral.get("total", 0) > 0:
        # Positive = more lenient on Llama (higher accuracy on Llama responses)
        result["llama_judge_accuracy_diff"] = (
            llama_on_llama["accuracy"] - llama_on_mixtral["accuracy"]
        )
        result["llama_judge_halluc_rate_diff"] = (
            llama_on_llama["hallucination_rate"] - llama_on_mixtral["hallucination_rate"]
        )
        result["consensus_accuracy_diff"] = (
            consensus_on_llama["accuracy"] - consensus_on_mixtral["accuracy"]
        )
        # If Llama judge shows a bigger accuracy gap than consensus, that's bias
        result["excess_llama_judge_leniency"] = (
            result["llama_judge_accuracy_diff"] - result["consensus_accuracy_diff"]
        )

    return result


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pre-registered sensitivity analysis")
    parser.add_argument("--dataset", default="all",
                        choices=["v5_baselines", "v5_prefixes", "v5_finetuned", "ablation", "all"])
    args = parser.parse_args()

    datasets_to_run = (
        ["v5_baselines", "v5_prefixes", "v5_finetuned", "ablation"]
        if args.dataset == "all"
        else [args.dataset]
    )

    output = {
        "description": "Pre-registered sensitivity analysis (setup.tex Section 4.3.7)",
        "judge_ordering": JUDGE_NAMES,
        "checks": {},
    }

    for ds_name in datasets_to_run:
        data = load_dataset(ds_name)
        if not data:
            print(f"  Skipping {ds_name}: no data found")
            continue

        print(f"\n{'=' * 60}")
        print(f"  Dataset: {ds_name} ({len(data)} records)")
        print(f"{'=' * 60}")

        # Check 1: Unanimous
        unan = check_unanimous(data, ds_name)
        print(f"\n  [1] Unanimous-only aggregation:")
        print(f"      Total: {unan['total_all']}, Unanimous: {unan['total_unanimous']} "
              f"({unan['fraction_unanimous']*100:.1f}%)")
        print(f"      All data — Acc: {unan['all_data']['accuracy']*100:.1f}%, "
              f"Halluc: {unan['all_data']['hallucination_rate']*100:.1f}%")
        print(f"      Unanimous — Acc: {unan['unanimous_only']['accuracy']*100:.1f}%, "
              f"Halluc: {unan['unanimous_only']['hallucination_rate']*100:.1f}%")

        # Check 2: Judge removal
        removal = check_judge_removal(data, ds_name)
        print(f"\n  [2] Judge removal analysis:")
        print(f"      Original — Acc: {removal['original']['accuracy']*100:.1f}%, "
              f"Halluc: {removal['original']['hallucination_rate']*100:.1f}%")
        for key, sub in removal["subsets"].items():
            print(f"      {key}: Acc {sub['accuracy']*100:.1f}%, "
                  f"Halluc {sub['hallucination_rate']*100:.1f}%, "
                  f"Changed: {sub['labels_changed']} ({sub['fraction_changed']*100:.1f}%)")

        # Check 3: Self-eval bias
        bias = check_self_eval_bias(data, ds_name)
        print(f"\n  [3] Self-evaluation bias (Llama judge):")
        print(f"      Llama-generated: n={bias['llama_generated_n']}")
        print(f"      Mixtral-generated: n={bias['mixtral_generated_n']}")
        if bias.get("llama_judge_accuracy_diff") is not None:
            print(f"      Llama judge acc on Llama resp: "
                  f"{bias['llama_judge_on_llama_responses']['accuracy']*100:.1f}%")
            print(f"      Llama judge acc on Mixtral resp: "
                  f"{bias['llama_judge_on_mixtral_responses']['accuracy']*100:.1f}%")
            print(f"      Accuracy diff (positive=lenient on Llama): "
                  f"{bias['llama_judge_accuracy_diff']*100:+.1f}pp")
            print(f"      Excess leniency vs consensus: "
                  f"{bias['excess_llama_judge_leniency']*100:+.1f}pp")
        else:
            print(f"      (insufficient data for comparison)")

        output["checks"][ds_name] = {
            "unanimous_only": unan,
            "judge_removal": removal,
            "self_eval_bias": bias,
        }

    # Combined analysis across all datasets
    if len(datasets_to_run) > 1:
        all_data = []
        for ds_name in datasets_to_run:
            all_data.extend(load_dataset(ds_name))
        if all_data:
            print(f"\n{'=' * 60}")
            print(f"  COMBINED ({len(all_data)} records)")
            print(f"{'=' * 60}")

            unan = check_unanimous(all_data, "combined")
            removal = check_judge_removal(all_data, "combined")
            bias = check_self_eval_bias(all_data, "combined")

            print(f"\n  [1] Unanimous: {unan['total_unanimous']}/{unan['total_all']} "
                  f"({unan['fraction_unanimous']*100:.1f}%)")
            print(f"      All — Acc: {unan['all_data']['accuracy']*100:.1f}%, "
                  f"Unanimous — Acc: {unan['unanimous_only']['accuracy']*100:.1f}%")
            print(f"\n  [2] Judge removal:")
            for key, sub in removal["subsets"].items():
                print(f"      {key}: Acc {sub['accuracy']*100:.1f}%, "
                      f"Changed: {sub['labels_changed']} ({sub['fraction_changed']*100:.1f}%)")
            print(f"\n  [3] Self-eval bias:")
            if bias.get("excess_llama_judge_leniency") is not None:
                print(f"      Excess leniency: {bias['excess_llama_judge_leniency']*100:+.1f}pp")

            output["checks"]["combined"] = {
                "unanimous_only": unan,
                "judge_removal": removal,
                "self_eval_bias": bias,
            }

    # Save
    output_path = PROJECT_ROOT / "results" / "sensitivity_analysis.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved: {output_path}")


if __name__ == "__main__":
    main()
