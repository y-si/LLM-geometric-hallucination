"""Step 9: Best-per-prompt selection for V5 fine-tuning training data.

For each V5 prompt, selects the single best response across:
  - baseline (no-prefix)
  - 4 non-CoT prefixes: entity_aware, structured_caution, epistemic_humility, fact_grounded

Selection priority: correct (0) > partial (1) > refusal (3) > hallucination (2)
Tiebreaker within same label: highest judge_confidence.

CoT Verification excluded (original 62-68% refusal rate was API failure artifact — see
JUDGE_CONTAMINATION_ISSUE.md — but CoT still excluded because non-CoT prefixes already
achieve 98-99% correct, and CoT's verbose reasoning-chain format is unsuitable for training).
Baseline included as candidate (prevents 6 regression cases where baseline correct but all prefixes hallucinate).
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_DIR = BASE_DIR / "data" / "training"

MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]
NON_COT_PREFIXES = ["entity_aware", "structured_caution", "epistemic_humility", "fact_grounded"]
SOURCES = ["baseline"] + NON_COT_PREFIXES

# Priority: lower = better. Label 0 (correct) > 1 (partial) > 3 (refusal) > 2 (hallucination)
LABEL_PRIORITY = {0: 0, 1: 1, 3: 2, 2: 3}


def load_jsonl(path):
    records = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            records[r["id"]] = r
    return records


def write_jsonl(path, records):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def select_best(sources_data):
    """Select the best response across all sources for a single prompt.

    Args:
        sources_data: dict of {source_name: record} for one prompt

    Returns:
        (best_record, best_source, alternatives_dict) or None if all hallucinate
    """
    candidates = []
    alternatives = {}

    for source, record in sources_data.items():
        label = record.get("judge_label")
        confidence = record.get("judge_confidence", 0.0)
        if label is None:
            continue
        alternatives[source] = label
        priority = LABEL_PRIORITY.get(label, 99)
        # Sort key: (priority, -confidence) — lower priority first, higher confidence first
        candidates.append((priority, -confidence, source, record))

    if not candidates:
        return None

    candidates.sort()
    best_priority, neg_conf, best_source, best_record = candidates[0]

    # If best is hallucination (priority 3), this prompt is unfixable
    if best_priority == 3:  # label == 2
        return None

    return best_record, best_source, alternatives


def build_training_data(model):
    """Build best-per-prompt training data for one model."""

    # Load baseline
    bl_path = RESULTS_DIR / "v5_baselines" / model / "no_prefix" / "judged_answers.jsonl"
    baseline = load_jsonl(bl_path)
    print(f"  Loaded {len(baseline)} baseline responses")

    # Load prefix responses
    prefix_data = {}
    for prefix in NON_COT_PREFIXES:
        pf_path = RESULTS_DIR / "v5_prefixes" / model / prefix / "judged_answers.jsonl"
        prefix_data[prefix] = load_jsonl(pf_path)
        print(f"  Loaded {len(prefix_data[prefix])} {prefix} responses")

    # Get all prompt IDs (union across all sources)
    all_ids = set(baseline.keys())
    for prefix in NON_COT_PREFIXES:
        all_ids |= set(prefix_data[prefix].keys())
    all_ids = sorted(all_ids)
    print(f"  Total unique prompt IDs: {len(all_ids)}")

    # Select best per prompt
    training = []
    unfixable = []
    stats = Counter()
    source_counts = Counter()
    label_counts = Counter()
    category_stats = defaultdict(lambda: Counter())

    for pid in all_ids:
        sources = {}
        if pid in baseline:
            sources["baseline"] = baseline[pid]
        for prefix in NON_COT_PREFIXES:
            if pid in prefix_data[prefix]:
                sources[prefix] = prefix_data[prefix][pid]

        result = select_best(sources)

        # Get category from any available source
        category = None
        for s in sources.values():
            category = s.get("category")
            if category:
                break

        if result is None:
            # Unfixable — all sources hallucinate
            stats["excluded_unfixable"] += 1
            category_stats[category]["unfixable"] += 1
            unfixable_record = {
                "id": pid,
                "category": category,
                "question": sources.get("baseline", next(iter(sources.values()))).get("question"),
                "ground_truth": sources.get("baseline", next(iter(sources.values()))).get("ground_truth"),
                "source_labels": {s: r.get("judge_label") for s, r in sources.items()},
            }
            unfixable.append(unfixable_record)
            continue

        best_record, best_source, alternatives = result
        selected_label = best_record.get("judge_label")

        label_name = {0: "correct", 1: "partial", 3: "refusal"}.get(selected_label, "unknown")
        stats[f"selected_{label_name}"] += 1
        source_counts[best_source] += 1
        label_counts[selected_label] += 1
        category_stats[category][label_name] += 1

        training_record = {
            "id": pid,
            "category": category,
            "question": best_record.get("question"),
            "ground_truth": best_record.get("ground_truth"),
            "selected_answer": best_record.get("model_answer"),
            "selected_source": best_source,
            "selected_label": selected_label,
            "selected_confidence": best_record.get("judge_confidence"),
            "selection_reason": label_name,
            "alternatives": alternatives,
        }
        training.append(training_record)

    return training, unfixable, stats, source_counts, label_counts, category_stats


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {}

    for model in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {model}")
        print(f"{'='*60}")

        training, unfixable, stats, source_counts, label_counts, category_stats = build_training_data(model)

        # Write training data
        train_path = OUTPUT_DIR / f"v5_training_{model}.jsonl"
        write_jsonl(train_path, training)
        print(f"\n  Training data: {len(training)} prompts → {train_path}")

        # Write unfixable
        unfix_path = OUTPUT_DIR / f"v5_unfixable_{model}.jsonl"
        write_jsonl(unfix_path, unfixable)
        print(f"  Unfixable: {len(unfixable)} prompts → {unfix_path}")

        # Print summary
        total = len(training) + len(unfixable)
        print(f"\n  Selection summary ({total} total):")
        for label_name in ["correct", "partial", "refusal"]:
            ct = stats.get(f"selected_{label_name}", 0)
            print(f"    {label_name}: {ct} ({100*ct/total:.1f}%)")
        print(f"    excluded (unfixable): {len(unfixable)} ({100*len(unfixable)/total:.1f}%)")

        print(f"\n  Source distribution (for {len(training)} selected):")
        for source in SOURCES:
            ct = source_counts.get(source, 0)
            print(f"    {source}: {ct} ({100*ct/len(training):.1f}%)")

        print(f"\n  Category breakdown:")
        for cat in sorted(category_stats.keys()):
            cs = category_stats[cat]
            cat_total = sum(cs.values())
            parts = ", ".join(f"{k}={v}" for k, v in sorted(cs.items()))
            print(f"    {cat} ({cat_total}): {parts}")

        # Unique saves per prefix (prompts where only that source gives correct)
        print(f"\n  Unique correct saves (only this source gives label=0):")
        for source in SOURCES:
            unique = 0
            for rec in training:
                if rec["selected_label"] == 0 and rec["selected_source"] == source:
                    # Check if no other source also gave correct
                    other_correct = any(
                        v == 0 for k, v in rec["alternatives"].items() if k != source
                    )
                    if not other_correct:
                        unique += 1
            print(f"    {source}: {unique}")

        # Build report section
        report[model] = {
            "training_size": len(training),
            "unfixable_size": len(unfixable),
            "selection_counts": dict(stats),
            "source_distribution": dict(source_counts),
            "label_distribution": {str(k): v for k, v in label_counts.items()},
            "category_breakdown": {k: dict(v) for k, v in category_stats.items()},
            "training_file": str(train_path),
            "unfixable_file": str(unfix_path),
        }

    # Write combined report
    report_path = OUTPUT_DIR / "v5_selection_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n\nSelection report → {report_path}")


if __name__ == "__main__":
    main()
