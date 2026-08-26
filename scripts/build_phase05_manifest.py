"""Phase 0.5: build the frozen prompt manifest for the Kendall's tau pilot.

Design is pre-registered in research_paper/PHASE_0.5_SPEC.md. This script implements
§4.1–§4.4. It is fully deterministic — no RNG, no network. Re-running it must
reproduce byte-identical output.

Three analysis sets are emitted as ONE deduplicated file with per-row boolean flags,
because the sets overlap and we generate completions once per unique prompt rather
than once per set membership (§4.4):

  PRIMARY (the decision surface, §4.1) — the three categories whose ground_truth
  licenses a judgment without the judge consulting its own world knowledge:
      borderline_plausible_fake (169), nonexistent (120), ambiguous (120) = 409

  JUDGE-BOUND (the artifact diagnostic, §4.2) — the two categories whose ground_truth
  is a meta-statement containing no facts, so the judge falls back on its own
  parametric knowledge and both models' scores correlate through the shared judge:
      borderline_obscure_real (162), factual (98) = 260
  Reported as Delta_artifact = tau_corr(judge-bound) - tau_corr(verifiable).
  NOT part of the go/no-go rule.

  SECONDARY (the stratification contrast, §4.3) — all 431 unique V3 prompts across
  all 7 categories, for reporting pooled tau next to blocked tau. Also NOT part of
  the go/no-go rule. Includes borderline_edge_factual as a documented
  degenerate-variance negative control (20 rows collapse to 5 unique questions).

Deduplication is load-bearing, not hygiene: duplicate prompts share an expected
P(hallucinate) under every model, so each duplicate pair contributes a
near-guaranteed concordance and inflates rank correlation.
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "data" / "prompts"

V3_PATH = PROMPTS_DIR / "prompts.jsonl"
V5_TRAIN_PATH = PROMPTS_DIR / "v5_all.jsonl"
MANIFEST_OUT = PROMPTS_DIR / "phase05_manifest.jsonl"

# §4.1 — verifiable ground truth, adequate n. Carries the decision.
PRIMARY_CATEGORIES = ["borderline_plausible_fake", "nonexistent", "ambiguous"]

# §4.2 — ground_truth is a meta-statement with no embedded facts. Diagnostic only.
JUDGE_BOUND_CATEGORIES = ["borderline_obscure_real", "factual"]

# Expected counts from the pre-registration (§4.1, §4.2, §4.3). A mismatch means the
# underlying data changed since the spec was frozen, which invalidates the
# pre-registration until the amendment log is updated — so it is a hard failure.
EXPECTED = {
    "borderline_plausible_fake": 169,
    "nonexistent": 120,
    "ambiguous": 120,
    "borderline_obscure_real": 162,
    "factual": 98,
}
EXPECTED_PRIMARY_TOTAL = 409
EXPECTED_JUDGE_BOUND_TOTAL = 260
EXPECTED_SECONDARY_TOTAL = 431
EXPECTED_MANIFEST_TOTAL = 704


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def norm(question):
    return question.strip()


def dedup_by_question(rows):
    """Keep the lowest-id row per unique question. Returns (kept, dropped)."""
    by_question = defaultdict(list)
    for r in rows:
        by_question[norm(r["question"])].append(r)

    kept, dropped = [], []
    for question in sorted(by_question):
        group = sorted(by_question[question], key=lambda r: str(r["id"]))
        kept.append(group[0])
        dropped.extend(group[1:])
    return kept, dropped


def build_category(category, v3_rows, v5_questions):
    """V3 rows for a category, deduped, plus V5-clean pool top-up if a pool exists.

    IDs are namespaced by source. V3 and the standalone pool files reuse the same id
    space (both contain e.g. `borderline_obscure_0`) while naming DIFFERENT questions.
    Everything downstream keys on (prompt_id, model, sample_idx), so an un-namespaced
    id silently collides: the resume logic treats the second prompt as already
    generated and skips it. That is exactly what happened on the first full run —
    54 colliding ids produced 2,160 duplicate keys. `uid` is the real key; `id` is
    retained as provenance.
    """
    v3_cat = [r for r in v3_rows if r["category"] == category]
    v3_kept, v3_dropped = dedup_by_question(v3_cat)

    print(f"\n{category}")
    print(f"  V3: {len(v3_cat)} rows -> {len(v3_kept)} unique "
          f"({len(v3_dropped)} duplicates dropped)")
    for r in v3_dropped:
        print(f"    dropped dup id={r['id']}: {norm(r['question'])[:70]}")

    rows = [{**r, "source": "v3", "uid": f"v3:{r['id']}"} for r in v3_kept]
    taken = {norm(r["question"]) for r in v3_kept}

    pool_path = PROMPTS_DIR / f"{category}.jsonl"
    if not pool_path.exists():
        print(f"  pool: none ({pool_path.name} does not exist) — V3 only")
        print(f"  category total: {len(rows)}")
        return rows

    pool_rows = load_jsonl(pool_path)
    pool_kept, pool_dedup_dropped = dedup_by_question(pool_rows)

    in_v5, already_taken, added = 0, 0, 0
    for r in pool_kept:
        q = norm(r["question"])
        if q in v5_questions:
            in_v5 += 1
            continue
        if q in taken:
            already_taken += 1
            continue
        taken.add(q)
        rows.append({**r, "source": "pool", "uid": f"pool:{r['id']}"})
        added += 1

    print(f"  pool ({pool_path.name}): {len(pool_rows)} rows -> {len(pool_kept)} unique; "
          f"{in_v5} in V5 train, {already_taken} already in V3, {added} added")
    if pool_dedup_dropped:
        print(f"    note: {len(pool_dedup_dropped)} intra-pool duplicates dropped")
    print(f"  category total: {len(rows)}")
    return rows


def main():
    v3_rows = load_jsonl(V3_PATH)
    v5_questions = {norm(r["question"]) for r in load_jsonl(V5_TRAIN_PATH)}
    print(f"V3: {len(v3_rows)} rows | V5 train: {len(v5_questions)} unique questions")

    overlap = {norm(r["question"]) for r in v3_rows} & v5_questions
    if overlap:
        sys.exit(f"FAIL: V3 overlaps V5 train on {len(overlap)} questions. "
                 "V3 is supposed to be held out — investigate before proceeding.")
    print("V3 x V5 train overlap: 0 (as expected)")

    print("\n--- PRIMARY (decision surface, verifiable ground truth) ---")
    primary = []
    for category in PRIMARY_CATEGORIES:
        primary.extend(build_category(category, v3_rows, v5_questions))

    print("\n--- JUDGE-BOUND (artifact diagnostic, not part of the decision) ---")
    judge_bound = []
    for category in JUDGE_BOUND_CATEGORIES:
        judge_bound.extend(build_category(category, v3_rows, v5_questions))

    print("\n--- SECONDARY (stratification contrast, all unique V3) ---")
    secondary, secondary_dropped = dedup_by_question(v3_rows)
    print(f"  {len(v3_rows)} V3 rows -> {len(secondary)} unique "
          f"({len(secondary_dropped)} duplicates dropped)")
    raw_counts = Counter(r["category"] for r in v3_rows)
    kept_counts = Counter(r["category"] for r in secondary)
    for category in sorted(kept_counts):
        note = ""
        if kept_counts[category] < raw_counts[category]:
            note = f"  <-- {raw_counts[category]} rows collapsed to {kept_counts[category]}"
        print(f"    {category:32s} {kept_counts[category]:4d}{note}")

    # Merge into one row per unique question, flagged by set membership.
    merged = {}
    for rows, flag in ((primary, "in_primary"),
                       (judge_bound, "in_judgebound"),
                       (secondary, "in_secondary")):
        for r in rows:
            q = norm(r["question"])
            if q not in merged:
                merged[q] = {**r, "source": r.get("source", "v3"),
                             "uid": r.get("uid", f"v3:{r['id']}"),
                             "in_primary": False, "in_judgebound": False,
                             "in_secondary": False}
            merged[q][flag] = True

    manifest = sorted(merged.values(), key=lambda r: (r["category"], r["uid"]))

    # `uid` is the key everything downstream joins on. A collision here silently
    # corrupts the run: the resume logic skips the second prompt as already done.
    uids = Counter(r["uid"] for r in manifest)
    collisions = {u: n for u, n in uids.items() if n > 1}
    if collisions:
        sys.exit(f"FAIL: {len(collisions)} duplicate uid(s) — downstream keys would "
                 f"collide: {sorted(collisions)[:5]}")
    if len(uids) != len(manifest):
        sys.exit("FAIL: uid count does not match manifest length")

    counts = Counter(r["category"] for r in manifest
                     if r["in_primary"] or r["in_judgebound"])
    problems = []
    for category, expected in EXPECTED.items():
        if counts[category] != expected:
            problems.append(f"{category}: expected {expected}, got {counts[category]}")
    totals = [
        ("primary", sum(r["in_primary"] for r in manifest), EXPECTED_PRIMARY_TOTAL),
        ("judge-bound", sum(r["in_judgebound"] for r in manifest), EXPECTED_JUDGE_BOUND_TOTAL),
        ("secondary", sum(r["in_secondary"] for r in manifest), EXPECTED_SECONDARY_TOTAL),
        ("manifest", len(manifest), EXPECTED_MANIFEST_TOTAL),
    ]
    for name, actual, expected in totals:
        if actual != expected:
            problems.append(f"{name} total: expected {expected}, got {actual}")
    if problems:
        sys.exit("FAIL: counts differ from the pre-registration (PHASE_0.5_SPEC.md §4):\n  "
                 + "\n  ".join(problems)
                 + "\nUpdate the spec's amendment log before regenerating.")

    with open(MANIFEST_OUT, "w") as f:
        for r in manifest:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    print(f"\nwrote {len(manifest)} unique prompts -> {MANIFEST_OUT.relative_to(BASE_DIR)}")
    for name, actual, _ in totals[:3]:
        print(f"  {name:12s} {actual}")
    print(f"  {'v3 / pool':12s} {sum(r['source'] == 'v3' for r in manifest)} / "
          f"{sum(r['source'] == 'pool' for r in manifest)}")
    print("\nManifest is frozen once generation starts. Commit it.")


if __name__ == "__main__":
    main()
