"""Fix judge contamination in V4 prefix experiment data.

Same logic as fix_judge_contamination.py but targets V4 files specifically.
The original fix script had V4 in its NEVER_TOUCH list because V4 was
considered a separate analysis. We now need corrected V4 numbers for the thesis.

Processes all 10 V4 prefix files (5 prefixes x 2 models), including CoT
(for completeness, though CoT is excluded from thesis analysis).

Usage:
    python3 scripts/fix_v4_judge_contamination.py              # Dry run
    python3 scripts/fix_v4_judge_contamination.py --apply       # Apply corrections
    python3 scripts/fix_v4_judge_contamination.py --verbose     # Show every change
"""

import json
import shutil
import argparse
from pathlib import Path
from collections import Counter
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# V4 prefix experiment files
FILES_TO_PROCESS = []
for model in ["mixtral-8x7b", "llama-4-maverick-17b"]:
    for prefix in ["entity_aware", "structured_caution", "epistemic_humility",
                    "fact_grounded", "cot_verification"]:
        FILES_TO_PROCESS.append(
            PROJECT_ROOT / "results" / "v4_prefix_experiment" / model / prefix / "judged_answers.jsonl"
        )

LABEL_NAMES = {0: "Correct", 1: "Partial", 2: "Hallucinated", 3: "Refused"}


def is_failed_judge(judgment: dict) -> bool:
    """Detect a failed judge: confidence=0.0 AND error in justification."""
    if judgment.get("confidence") != 0.0:
        return False
    justification = str(judgment.get("justification", ""))
    return "Error" in justification or "error" in justification


def recompute_consensus(real_judgments: list) -> dict:
    """Recompute consensus from real (non-failed) judges only."""
    if len(real_judgments) == 0:
        return {"label": None, "confidence": 0.0, "agreement_rate": 0.0,
                "method": "no_real_judges"}

    if len(real_judgments) == 1:
        return {"label": None, "confidence": 0.0, "agreement_rate": 0.0,
                "method": "single_judge_insufficient"}

    labels = [j["label"] for j in real_judgments]
    confidences = [j["confidence"] for j in real_judgments]

    if len(real_judgments) == 2:
        if labels[0] == labels[1]:
            return {
                "label": labels[0],
                "confidence": 1.0 * sum(confidences) / len(confidences),
                "agreement_rate": 1.0,
                "method": "two_judges_agree",
            }
        else:
            if confidences[0] > confidences[1]:
                winner = 0
            elif confidences[1] > confidences[0]:
                winner = 1
            else:
                winner = 0
            return {
                "label": labels[winner],
                "confidence": 0.5 * sum(confidences) / len(confidences),
                "agreement_rate": 0.5,
                "method": f"two_judges_disagree_confidence_tiebreak_judge{winner}",
            }

    if len(real_judgments) == 3:
        counts = Counter(labels)
        majority_label, majority_count = counts.most_common(1)[0]
        agreement_rate = majority_count / 3
        avg_conf = sum(confidences) / 3
        return {
            "label": majority_label,
            "confidence": agreement_rate * avg_conf,
            "agreement_rate": agreement_rate,
            "method": "three_judges_majority",
        }

    raise ValueError(f"Unexpected number of real judgments: {len(real_judgments)}")


def process_file(filepath: Path, apply: bool, verbose: bool) -> dict:
    """Process a single JSONL file. Returns stats dict."""
    stats = {
        "file": str(filepath.relative_to(PROJECT_ROOT)),
        "total": 0,
        "no_individual_judgments": 0,
        "clean": 0,
        "one_failure_agree": 0,
        "one_failure_disagree": 0,
        "two_plus_failures": 0,
        "labels_changed": 0,
        "labels_unchanged": 0,
        "changes": [],
    }

    if not filepath.exists():
        print(f"  SKIPPED (file not found)")
        return stats

    entries = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    stats["total"] = len(entries)
    corrected_entries = []

    for entry in entries:
        individual = entry.get("individual_judgments")

        if not individual or len(individual) != 3:
            stats["no_individual_judgments"] += 1
            corrected_entries.append(entry)
            continue

        failed_indices = [i for i, j in enumerate(individual) if is_failed_judge(j)]
        real_judgments = [j for i, j in enumerate(individual) if i not in failed_indices]

        if len(failed_indices) == 0:
            stats["clean"] += 1
            corrected_entries.append(entry)
            continue

        if len(failed_indices) >= 2:
            stats["two_plus_failures"] += 1
            entry_copy = dict(entry)
            entry_copy["_contamination_flag"] = {
                "status": "unfixable_needs_rejudging",
                "failed_judge_count": len(failed_indices),
                "failed_judge_indices": failed_indices,
                "timestamp": datetime.now().isoformat(),
            }
            corrected_entries.append(entry_copy)
            continue

        # Exactly 1 failure — recompute from 2 real judges
        assert len(failed_indices) == 1
        assert len(real_judgments) == 2

        result = recompute_consensus(real_judgments)
        old_label = entry.get("judge_label")
        new_label = result["label"]

        if new_label is None:
            stats["two_plus_failures"] += 1
            corrected_entries.append(entry)
            continue

        if old_label == new_label:
            if real_judgments[0]["label"] == real_judgments[1]["label"]:
                stats["one_failure_agree"] += 1
            else:
                stats["one_failure_disagree"] += 1
            stats["labels_unchanged"] += 1
            entry_copy = dict(entry)
            entry_copy["_correction"] = {
                "applied": True,
                "reason": "judge_failure_recomputed",
                "failed_judge_index": failed_indices[0],
                "old_label": old_label,
                "new_label": new_label,
                "label_changed": False,
                "method": result["method"],
                "old_confidence": entry.get("judge_confidence"),
                "new_confidence": result["confidence"],
                "timestamp": datetime.now().isoformat(),
            }
            entry_copy["judge_confidence"] = result["confidence"]
            entry_copy["agreement_rate"] = result["agreement_rate"]
            entry_copy["individual_confidence_avg"] = sum(
                j["confidence"] for j in real_judgments
            ) / len(real_judgments)
            corrected_entries.append(entry_copy)
        else:
            if real_judgments[0]["label"] == real_judgments[1]["label"]:
                stats["one_failure_agree"] += 1
            else:
                stats["one_failure_disagree"] += 1
            stats["labels_changed"] += 1
            stats["changes"].append((
                entry.get("id", "unknown"),
                old_label,
                new_label,
                entry.get("category", "unknown"),
            ))

            if verbose:
                print(f"    CHANGE: {entry.get('id')} [{entry.get('category')}] "
                      f"{old_label}({LABEL_NAMES.get(old_label, '?')}) -> "
                      f"{new_label}({LABEL_NAMES.get(new_label, '?')}) "
                      f"[{result['method']}]")

            entry_copy = dict(entry)
            entry_copy["_correction"] = {
                "applied": True,
                "reason": "judge_failure_recomputed",
                "failed_judge_index": failed_indices[0],
                "old_label": old_label,
                "new_label": new_label,
                "label_changed": True,
                "method": result["method"],
                "old_confidence": entry.get("judge_confidence"),
                "new_confidence": result["confidence"],
                "timestamp": datetime.now().isoformat(),
            }
            entry_copy["judge_label"] = new_label
            entry_copy["judge_confidence"] = result["confidence"]
            entry_copy["agreement_rate"] = result["agreement_rate"]
            entry_copy["individual_confidence_avg"] = sum(
                j["confidence"] for j in real_judgments
            ) / len(real_judgments)
            corrected_entries.append(entry_copy)

    assert len(corrected_entries) == len(entries), (
        f"Entry count mismatch: {len(corrected_entries)} vs {len(entries)}"
    )

    if apply and (stats["labels_changed"] > 0 or stats["one_failure_agree"] > 0
                  or stats["one_failure_disagree"] > 0):
        backup_path = filepath.with_suffix(".jsonl.backup_pre_v4_fix")
        if not backup_path.exists():
            shutil.copy2(filepath, backup_path)
            print(f"    Backed up to: {backup_path.name}")
        else:
            print(f"    Backup already exists: {backup_path.name}")

        with open(filepath, "w") as f:
            for entry in corrected_entries:
                f.write(json.dumps(entry) + "\n")
        print(f"    Written: {len(corrected_entries)} entries")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Fix judge contamination in V4 prefix experiment JSONL files")
    parser.add_argument("--apply", action="store_true",
                        help="Actually write corrected files (default: dry run)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show every label change")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"=== V4 Judge Contamination Fix ({mode}) ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    existing_files = [f for f in FILES_TO_PROCESS if f.exists()]
    missing_files = [f for f in FILES_TO_PROCESS if not f.exists()]

    print(f"Files to process: {len(existing_files)}")
    if missing_files:
        print(f"Files not found (skipping): {len(missing_files)}")
        for f in missing_files:
            print(f"  - {f.relative_to(PROJECT_ROOT)}")
    print()

    all_stats = []
    total_changed = 0
    total_entries = 0
    total_unfixable = 0
    transition_counts = Counter()

    for filepath in existing_files:
        rel_path = filepath.relative_to(PROJECT_ROOT)
        print(f"Processing: {rel_path}")

        stats = process_file(filepath, apply=args.apply, verbose=args.verbose)
        all_stats.append(stats)

        total_entries += stats["total"]
        total_changed += stats["labels_changed"]
        total_unfixable += stats["two_plus_failures"]

        for (entry_id, old_label, new_label, category) in stats["changes"]:
            transition_counts[(old_label, new_label)] += 1

        affected = stats["one_failure_agree"] + stats["one_failure_disagree"]
        print(f"  Total: {stats['total']}, Clean: {stats['clean']}, "
              f"Affected: {affected}, Changed: {stats['labels_changed']}, "
              f"Unfixable: {stats['two_plus_failures']}")
        print()

    print("=" * 60)
    print("V4 FIX SUMMARY")
    print("=" * 60)
    print(f"Total entries scanned:    {total_entries}")
    print(f"Labels changed:           {total_changed}")
    print(f"Labels unchanged:         {total_entries - total_changed - total_unfixable}")
    print(f"Unfixable (2+ failures):  {total_unfixable}")
    print(f"Change rate:              {total_changed / max(total_entries, 1) * 100:.2f}%")
    print()

    if transition_counts:
        print("Label transitions:")
        for (old, new), count in sorted(transition_counts.items(), key=lambda x: -x[1]):
            print(f"  {LABEL_NAMES.get(old, old)} -> {LABEL_NAMES.get(new, new)}: {count}")
        print()

    if not args.apply:
        print("This was a DRY RUN. No files were modified.")
        print("To apply corrections, run with --apply")
    else:
        print("Corrections APPLIED. Originals backed up with .backup_pre_v4_fix suffix.")

    # Write V4-specific summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "scope": "v4_prefix_experiment",
        "total_entries": total_entries,
        "labels_changed": total_changed,
        "unfixable": total_unfixable,
        "transitions": {f"{LABEL_NAMES.get(old, old)}->{LABEL_NAMES.get(new, new)}": count
                        for (old, new), count in transition_counts.items()},
        "per_file": [{
            "file": s["file"],
            "total": s["total"],
            "clean": s["clean"],
            "labels_changed": s["labels_changed"],
            "unfixable": s["two_plus_failures"],
        } for s in all_stats],
    }

    summary_path = PROJECT_ROOT / "results" / "v4_contamination_fix_summary.json"
    if args.apply:
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nAudit summary written to: {summary_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
