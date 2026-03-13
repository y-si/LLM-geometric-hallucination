#!/usr/bin/env python3
"""
Comprehensive data integrity audit for all result files.
Checks entry counts, schema, label validity, confidence ranges,
individual judgments, backups, correction metadata, ID uniqueness,
and cross-file consistency.
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path("/Users/sein/Desktop/homebase/harvard/classes/cs2881/LLM-geometric-hallucination/results")

# Track all issues
issues = []
warnings = []
stats = defaultdict(dict)


def load_jsonl(path):
    """Load a JSONL file, return list of dicts and any parse errors."""
    entries = []
    parse_errors = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                parse_errors.append((i, str(e)))
    return entries, parse_errors


def audit_judged_file(path, expected_count=None, label="", check_corrections=False):
    """Audit a judged JSONL file for all integrity checks."""
    rel = str(path.relative_to(BASE))
    entries, parse_errors = load_jsonl(path)

    if parse_errors:
        for line_num, err in parse_errors:
            issues.append(f"[PARSE ERROR] {rel}: line {line_num}: {err}")

    # 1. Entry count
    count = len(entries)
    stats[rel]["count"] = count
    if expected_count is not None and count != expected_count:
        issues.append(f"[COUNT] {rel}: expected {expected_count}, got {count}")

    if not entries:
        issues.append(f"[EMPTY] {rel}: file is empty")
        return set()

    # 2. Schema consistency
    required_judged = {"id", "judge_label", "judge_confidence", "individual_judgments",
                       "model_answer", "question", "ground_truth", "category"}
    for i, entry in enumerate(entries):
        missing = required_judged - set(entry.keys())
        if missing:
            issues.append(f"[SCHEMA] {rel}: entry {i} (id={entry.get('id','?')}) missing fields: {missing}")
            if i >= 5:
                issues.append(f"[SCHEMA] {rel}: ... (stopping after 5 schema errors)")
                break

    # 3. Label validity
    null_labels = 0
    invalid_labels = 0
    label_dist = defaultdict(int)
    for entry in entries:
        lbl = entry.get("judge_label")
        if lbl is None:
            null_labels += 1
        elif lbl not in (0, 1, 2, 3):
            invalid_labels += 1
        else:
            label_dist[lbl] += 1
    if null_labels:
        issues.append(f"[LABEL] {rel}: {null_labels} null judge_label values")
    if invalid_labels:
        issues.append(f"[LABEL] {rel}: {invalid_labels} invalid judge_label values (not in {{0,1,2,3}})")
    stats[rel]["label_dist"] = dict(label_dist)

    # 4. Confidence ranges
    bad_conf = 0
    null_conf = 0
    for entry in entries:
        conf = entry.get("judge_confidence")
        if conf is None:
            null_conf += 1
        elif not (0 <= conf <= 1):
            bad_conf += 1
    if null_conf:
        issues.append(f"[CONFIDENCE] {rel}: {null_conf} null judge_confidence values")
    if bad_conf:
        issues.append(f"[CONFIDENCE] {rel}: {bad_conf} judge_confidence values outside [0,1]")

    # 5. Individual judgments
    bad_judgments = 0
    wrong_count_judgments = 0
    for entry in entries:
        ij = entry.get("individual_judgments")
        if ij is None:
            bad_judgments += 1
        elif not isinstance(ij, list):
            bad_judgments += 1
        elif len(ij) != 3:
            wrong_count_judgments += 1
    if bad_judgments:
        issues.append(f"[JUDGMENTS] {rel}: {bad_judgments} entries with missing/invalid individual_judgments")
    if wrong_count_judgments:
        issues.append(f"[JUDGMENTS] {rel}: {wrong_count_judgments} entries without exactly 3 individual judgments")

    # 7. Correction metadata
    if check_corrections:
        corrected = sum(1 for e in entries if "_correction" in e)
        stats[rel]["corrected_entries"] = corrected

    # 8. ID uniqueness
    ids = [e.get("id") for e in entries]
    id_set = set(ids)
    if len(ids) != len(id_set):
        dupes = len(ids) - len(id_set)
        issues.append(f"[ID_UNIQUE] {rel}: {dupes} duplicate IDs")

    return id_set


def audit_answers_file(path, expected_count=None):
    """Audit an answers-only file (no judge fields required)."""
    rel = str(path.relative_to(BASE))
    entries, parse_errors = load_jsonl(path)

    if parse_errors:
        for line_num, err in parse_errors:
            issues.append(f"[PARSE ERROR] {rel}: line {line_num}: {err}")

    count = len(entries)
    stats[rel]["count"] = count
    if expected_count is not None and count != expected_count:
        issues.append(f"[COUNT] {rel}: expected {expected_count}, got {count}")

    # Minimal schema for answers files
    required = {"id", "question", "model_answer", "category"}
    for i, entry in enumerate(entries):
        missing = required - set(entry.keys())
        if missing:
            issues.append(f"[SCHEMA] {rel}: entry {i} (id={entry.get('id','?')}) missing fields: {missing}")
            if i >= 5:
                break

    # ID uniqueness
    ids = [e.get("id") for e in entries]
    if len(ids) != len(set(ids)):
        dupes = len(ids) - len(set(ids))
        issues.append(f"[ID_UNIQUE] {rel}: {dupes} duplicate IDs")

    return set(ids)


def check_backup(judged_path):
    """Check if backup file exists for a judged file."""
    backup = Path(str(judged_path) + ".backup_pre_contamination_fix")
    rel = str(judged_path.relative_to(BASE))
    if backup.exists():
        stats[rel]["has_backup"] = True
        # Compare line counts
        with open(backup) as f:
            backup_count = sum(1 for line in f if line.strip())
        with open(judged_path) as f:
            current_count = sum(1 for line in f if line.strip())
        if backup_count != current_count:
            issues.append(f"[BACKUP] {rel}: backup has {backup_count} entries vs current {current_count}")
    else:
        stats[rel]["has_backup"] = False


print("=" * 80)
print("DATA INTEGRITY AUDIT")
print("=" * 80)

# ============================================================================
# V5 BASELINES
# ============================================================================
print("\n--- V5 BASELINES ---")
v5_baseline_ids = {}
for model in ["mixtral-8x7b", "llama-4-maverick-17b"]:
    judged = BASE / "v5_baselines" / model / "no_prefix" / "judged_answers.jsonl"
    answers = BASE / "v5_baselines" / model / "no_prefix" / "answers.jsonl"
    if judged.exists():
        ids = audit_judged_file(judged, expected_count=2430, label=f"v5_baseline_{model}",
                                check_corrections=True)
        v5_baseline_ids[model] = ids
        check_backup(judged)
        print(f"  {model}: {len(ids)} entries")
    if answers.exists():
        audit_answers_file(answers, expected_count=2430)

# ============================================================================
# V5 PREFIXES (skip cot_verification)
# ============================================================================
print("\n--- V5 PREFIXES ---")
v5_prefix_ids = {}
prefixes = ["entity_aware", "epistemic_humility", "fact_grounded", "structured_caution"]
for model in ["mixtral-8x7b", "llama-4-maverick-17b"]:
    for prefix in prefixes:
        judged = BASE / "v5_prefixes" / model / prefix / "judged_answers.jsonl"
        answers = BASE / "v5_prefixes" / model / prefix / "answers.jsonl"
        # Allow 2429 or 2430
        if judged.exists():
            ids = audit_judged_file(judged, expected_count=None,
                                    label=f"v5_prefix_{model}_{prefix}",
                                    check_corrections=True)
            key = f"{model}/{prefix}"
            v5_prefix_ids[key] = ids
            check_backup(judged)
            count = stats[str(judged.relative_to(BASE))]["count"]
            if count not in (2429, 2430):
                issues.append(f"[COUNT] v5_prefixes/{key}/judged_answers.jsonl: expected 2429-2430, got {count}")
            print(f"  {model}/{prefix}: {count} entries")
        if answers.exists():
            audit_answers_file(answers, expected_count=None)

# ============================================================================
# V5 FINETUNED (main configs)
# ============================================================================
print("\n--- V5 FINETUNED ---")
v5_ft_ids = {}
for model_dir in ["mixtral-8x7b", "llama-4-maverick-17b"]:
    model_path = BASE / "v5_finetuned" / model_dir
    if not model_path.exists():
        continue
    for config in sorted(os.listdir(model_path)):
        config_path = model_path / config
        if not config_path.is_dir():
            continue
        judged = config_path / "judged_answers.jsonl"
        answers = config_path / "answers.jsonl"
        if judged.exists():
            ids = audit_judged_file(judged, expected_count=449,
                                    label=f"v5_ft_{model_dir}_{config}",
                                    check_corrections=True)
            v5_ft_ids[f"{model_dir}/{config}"] = ids
            check_backup(judged)
            print(f"  {model_dir}/{config}: {len(ids)} entries")
        elif answers.exists():
            audit_answers_file(answers, expected_count=449)
            print(f"  {model_dir}/{config}: answers only (no judged)")

# ============================================================================
# V5 FINETUNED ABLATION
# ============================================================================
print("\n--- V5 FINETUNED ABLATION ---")
ablation_path = BASE / "v5_finetuned" / "ablation"
if ablation_path.exists():
    for sub in sorted(os.listdir(ablation_path)):
        sub_path = ablation_path / sub
        if not sub_path.is_dir():
            continue
        judged = sub_path / "judged_answers.jsonl"
        answers = sub_path / "answers.jsonl"
        if judged.exists():
            ids = audit_judged_file(judged, expected_count=449,
                                    label=f"ablation_{sub}",
                                    check_corrections=True)
            check_backup(judged)
            print(f"  {sub}: {len(ids)} entries")
        if answers.exists():
            audit_answers_file(answers, expected_count=449)

# ============================================================================
# V5 FINETUNED CROSS-CAT ABLATION
# ============================================================================
print("\n--- V5 CROSS-CAT ABLATION ---")
cross_cat_path = BASE / "v5_finetuned" / "cross_cat_ablation"
if cross_cat_path.exists():
    for sub in sorted(os.listdir(cross_cat_path)):
        sub_path = cross_cat_path / sub
        if not sub_path.is_dir():
            continue
        # These are answers-only files (judged inline or separate)
        answers = sub_path / "answers.jsonl"
        judged = sub_path / "judged_answers.jsonl"
        if judged.exists():
            ids = audit_judged_file(judged, expected_count=449,
                                    label=f"crosscat_{sub}",
                                    check_corrections=True)
            print(f"  {sub}: {len(ids)} judged entries")
        elif answers.exists():
            # Check if answers have judge fields embedded
            entries, _ = load_jsonl(answers)
            has_judge = all("judge_label" in e for e in entries[:5]) if entries else False
            if has_judge:
                ids = audit_judged_file(answers, expected_count=449,
                                        label=f"crosscat_{sub}")
                print(f"  {sub}: {len(ids)} entries (judged in answers file)")
            else:
                ids = audit_answers_file(answers, expected_count=449)
                print(f"  {sub}: {len(ids)} entries (answers only, NO judge labels)")
                warnings.append(f"[NO_JUDGE] cross_cat_ablation/{sub}: no judged file and answers lack judge fields")

# ============================================================================
# V3 (multi-model judged_recalibrated is the canonical set)
# ============================================================================
print("\n--- V3 ---")
v3_ids = {}
v3_judged_dir = BASE / "v3" / "multi_model" / "judged_recalibrated"
if v3_judged_dir.exists():
    for f in sorted(os.listdir(v3_judged_dir)):
        if not f.endswith(".jsonl"):
            continue
        path = v3_judged_dir / f
        model_name = f.replace("judged_answers_", "").replace(".jsonl", "")
        ids = audit_judged_file(path, expected_count=449, label=f"v3_{model_name}")
        v3_ids[model_name] = ids
        print(f"  {model_name}: {len(ids)} entries")

# Also check the judged/ and judged_backup/ dirs
for subdir in ["judged", "judged_backup"]:
    d = BASE / "v3" / "multi_model" / subdir
    if d.exists():
        for f in sorted(os.listdir(d)):
            if not f.endswith(".jsonl"):
                continue
            path = d / f
            audit_judged_file(path, expected_count=449, label=f"v3_{subdir}_{f}")

# V3 answers files
v3_answers_dir = BASE / "v3" / "multi_model"
for f in sorted(os.listdir(v3_answers_dir)):
    if f.startswith("answers_") and f.endswith(".jsonl"):
        path = v3_answers_dir / f
        model_name = f.replace("answers_", "").replace(".jsonl", "")
        # Answers files may not have all fields
        entries, _ = load_jsonl(path)
        stats[str(path.relative_to(BASE))]["count"] = len(entries)
        if len(entries) != 449:
            issues.append(f"[COUNT] v3/multi_model/{f}: expected 449, got {len(entries)}")

# ============================================================================
# TRUTHFULQA
# ============================================================================
print("\n--- TRUTHFULQA ---")
for model in ["mixtral-8x7b", "llama-4-maverick-17b"]:
    for condition in ["baseline", "finetuned"]:
        judged = BASE / "truthfulqa" / model / f"{condition}_judged.jsonl"
        answers = BASE / "truthfulqa" / model / f"{condition}_answers.jsonl"
        if judged.exists():
            # TruthfulQA has different schema - category comes from TruthfulQA
            ids = audit_judged_file(judged, expected_count=None,
                                    label=f"truthfulqa_{model}_{condition}")
            count = stats[str(judged.relative_to(BASE))]["count"]
            print(f"  {model}/{condition}: {count} entries")
        if answers.exists():
            entries, _ = load_jsonl(answers)
            stats[str(answers.relative_to(BASE))]["count"] = len(entries)

# ============================================================================
# CROSS-FILE CONSISTENCY
# ============================================================================
print("\n--- CROSS-FILE CONSISTENCY ---")

# V5 baselines vs prefixes: same prompt IDs per model
for model in ["mixtral-8x7b", "llama-4-maverick-17b"]:
    if model not in v5_baseline_ids:
        continue
    baseline_ids = v5_baseline_ids[model]
    for prefix in prefixes:
        key = f"{model}/{prefix}"
        if key not in v5_prefix_ids:
            continue
        prefix_ids = v5_prefix_ids[key]
        only_baseline = baseline_ids - prefix_ids
        only_prefix = prefix_ids - baseline_ids
        if only_baseline:
            issues.append(f"[CROSS-FILE] {model}: {len(only_baseline)} IDs in baseline but not in {prefix}")
        if only_prefix:
            issues.append(f"[CROSS-FILE] {model}: {len(only_prefix)} IDs in {prefix} but not in baseline")
    print(f"  {model}: baseline vs prefix ID consistency checked")

# V3 models should all share the same IDs
if v3_ids:
    ref_model = list(v3_ids.keys())[0]
    ref_ids = v3_ids[ref_model]
    for m, ids in v3_ids.items():
        if m == ref_model:
            continue
        diff = ref_ids.symmetric_difference(ids)
        if diff:
            issues.append(f"[CROSS-FILE] V3: {ref_model} vs {m} differ by {len(diff)} IDs")
    print(f"  V3: cross-model ID consistency checked ({len(v3_ids)} models)")

# V5 finetuned should match V3 IDs (449 test set)
if v3_ids and v5_ft_ids:
    ref_v3 = list(v3_ids.values())[0]
    for key, ids in v5_ft_ids.items():
        diff = ref_v3.symmetric_difference(ids)
        if diff:
            # Check if it's just prefix differences
            sample_diff = list(diff)[:3]
            issues.append(f"[CROSS-FILE] V5 finetuned {key} vs V3: {len(diff)} ID differences (sample: {sample_diff})")
    print(f"  V5 finetuned vs V3 ID consistency checked")

# ============================================================================
# BACKUP FILES CHECK
# ============================================================================
print("\n--- BACKUP FILES ---")
# List all files that have backups
backup_files = list(BASE.rglob("*.backup_pre_contamination_fix"))
print(f"  Found {len(backup_files)} backup files:")
for bf in sorted(backup_files):
    original = Path(str(bf).replace(".backup_pre_contamination_fix", ""))
    if not original.exists():
        issues.append(f"[BACKUP] {bf.relative_to(BASE)}: backup exists but original is missing!")
    print(f"    {bf.relative_to(BASE)}")

# Files that were corrected should have backups
corrected_files = []
for rel_path, st in stats.items():
    if st.get("corrected_entries", 0) > 0:
        corrected_files.append(rel_path)
        if not st.get("has_backup", False):
            issues.append(f"[BACKUP] {rel_path}: has {st['corrected_entries']} corrected entries but NO backup file")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

# File counts
total_files = len(stats)
print(f"\nTotal files audited: {total_files}")

# Entry count summary
print("\nEntry counts by section:")
for rel_path in sorted(stats.keys()):
    count = stats[rel_path].get("count", "?")
    extras = []
    if stats[rel_path].get("corrected_entries", 0) > 0:
        extras.append(f"{stats[rel_path]['corrected_entries']} corrected")
    if stats[rel_path].get("has_backup"):
        extras.append("has backup")
    extra_str = f" ({', '.join(extras)})" if extras else ""
    label_info = stats[rel_path].get("label_dist", {})
    if label_info:
        label_str = " | labels: " + ", ".join(f"{k}:{v}" for k, v in sorted(label_info.items()))
    else:
        label_str = ""
    print(f"  {rel_path}: {count}{extra_str}{label_str}")

print(f"\n{'=' * 80}")
print(f"ISSUES FOUND: {len(issues)}")
print(f"WARNINGS: {len(warnings)}")
print(f"{'=' * 80}")

if issues:
    print("\n--- ISSUES ---")
    for issue in issues:
        print(f"  {issue}")

if warnings:
    print("\n--- WARNINGS ---")
    for w in warnings:
        print(f"  {w}")

if not issues and not warnings:
    print("\n  ALL CHECKS PASSED - No issues found.")

print()
