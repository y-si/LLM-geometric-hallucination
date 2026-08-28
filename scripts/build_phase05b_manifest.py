"""Build the frozen Phase 0.5b prompt manifest from TruthfulQA (spec §11.1).

WHY THIS IS SHORT, AND WHY THAT IS THE POINT. The Phase 0.5 manifest was assembled by
`build_borderline_benchmark.py` / `build_benchmark_v2.py` out of template files and
entity pools, and three compounding bugs in that path shipped 42 primary prompts still
containing literal `[placeholder]` tokens, plus asserted-fake ground truth that is wrong
on roughly 8% of items (`CONTEXT.md`, and the audit in `audit_ground_truth.py`).

§11.1 takes all 817 TruthfulQA prompts whole: no sampling, no filtering, no pool
top-up, no template substitution, no RNG. There is no construction rule here that can
be got wrong, which is the reason to prefer it. This script's real job is therefore not
construction but VERIFICATION — it refuses to emit a manifest that repeats any of the
known Phase 0.5 defects, and it fails loudly rather than shipping suspect data:

  * no unsubstituted `[placeholder]` token in any question   (the V3 bug, 42 prompts)
  * no duplicate uid                                        (the Phase 0.5 collision)
  * no duplicate question text
  * every ground truth carries a "Best answer:" reference    (the §4.0 verifiability
    criterion that `factual` and `borderline_obscure_real` failed)
  * the coarse-13 merge map is a strict partition of the 38 native categories
  * exactly 817 prompts across exactly 38 categories

Strata (§11.2): `category` is the native TruthfulQA category and is the PRIMARY
blocking level (38 strata, 14,831 blocked pairs). `coarse_category` is the
pre-registered 13-stratum merge, reported as a secondary only and never as the
decision statistic — coarsening strata can only raise tau, so the primary is
deliberately the finer, more conservative blocking.

Usage:
    python3 scripts/build_phase05b_manifest.py            # verify, then write
    python3 scripts/build_phase05b_manifest.py --check    # verify only, write nothing

Output: data/prompts/phase05b_manifest.jsonl  -- FREEZE AND COMMIT before generating.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SOURCE_PATH = BASE_DIR / "data" / "prompts" / "truthfulqa.jsonl"
MANIFEST_PATH = BASE_DIR / "data" / "prompts" / "phase05b_manifest.jsonl"

EXPECTED_N = 817
EXPECTED_CATEGORIES = 38
PLACEHOLDER = re.compile(r"\[[a-z_0-9]+\]")

# §11.2 — pre-registered coarse merge. Fixed in the spec BEFORE data exists so it
# cannot be retuned after seeing results. Verified below to be a strict partition.
COARSE_STRATA = {
    "Misconceptions": ["Misconceptions", "Misconceptions: Topical", "Misinformation"],
    "Sociology & Stereotypes": ["Sociology", "Stereotypes"],
    "Law & Politics": ["Law", "Politics"],
    "Paranormal & Conspiracies": ["Paranormal", "Conspiracies", "Superstitions"],
    "Health & Nutrition": ["Health", "Nutrition"],
    "Fiction & Folklore": ["Fiction", "Myths and Fairytales", "Proverbs"],
    "Indexical Error": ["Indexical Error: Other", "Indexical Error: Time",
                        "Indexical Error: Location", "Indexical Error: Identity"],
    "Science & Psychology": ["Science", "Education", "Weather", "Psychology"],
    "Reasoning & Subjectivity": ["Logical Falsehood", "Distraction", "Subjective",
                                 "Religion"],
    "Confusion": ["Confusion: People", "Confusion: Places", "Confusion: Other"],
    "History & Quotation": ["History", "Misquotations", "Mandela Effect"],
    "Economics & Finance": ["Economics", "Finance", "Statistics"],
    "Language & Advertising": ["Language", "Advertising"],
}


def read_jsonl(path):
    if not path.exists():
        sys.exit(f"missing input: {path}")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def coarse_map():
    """native category -> coarse stratum, verified to be a strict partition."""
    out = {}
    for coarse, natives in COARSE_STRATA.items():
        for n in natives:
            if n in out:
                sys.exit(f"merge map is not a partition: {n!r} appears in both "
                         f"{out[n]!r} and {coarse!r}")
            out[n] = coarse
    return out


def blocked_pairs(sizes):
    return sum(n * (n - 1) // 2 for n in sizes)


def build(rows):
    cmap = coarse_map()
    cats = Counter(r["category"] for r in rows)

    problems = []
    if len(rows) != EXPECTED_N:
        problems.append(f"expected {EXPECTED_N} prompts, got {len(rows)}")
    if len(cats) != EXPECTED_CATEGORIES:
        problems.append(f"expected {EXPECTED_CATEGORIES} categories, got {len(cats)}")

    # The merge map must cover the data exactly, in both directions. A category present
    # in the data but absent from the map would silently fall out of the coarse
    # secondary; a category in the map but absent from the data means the map was
    # written against a different snapshot of TruthfulQA.
    missing = set(cats) - set(cmap)
    extra = set(cmap) - set(cats)
    if missing:
        problems.append(f"categories in data but not in the §11.2 merge map: "
                        f"{sorted(missing)}")
    if extra:
        problems.append(f"categories in the §11.2 merge map but not in data: "
                        f"{sorted(extra)}")

    seen_uid, seen_q = {}, {}
    out = []
    n_placeholder = n_no_reference = 0
    for r in rows:
        uid = f"truthfulqa:{r['id']}"
        q = r["question"]
        gt = r.get("ground_truth") or ""

        if uid in seen_uid:
            problems.append(f"duplicate uid {uid}")
        seen_uid[uid] = True
        qk = q.strip()
        if qk in seen_q:
            problems.append(f"duplicate question text: {qk[:70]!r} "
                            f"({seen_q[qk]} and {r['id']})")
        seen_q[qk] = r["id"]

        if PLACEHOLDER.search(q):
            n_placeholder += 1
            problems.append(f"unsubstituted placeholder in {r['id']}: {q[:70]!r}")
        # §4.0 verifiability: the judge must be handed a sourced answer, not asked to
        # consult its own parametric knowledge. Rubric v2 CATEGORY 5 keys off exactly
        # this prefix, so a row without it would be judged under the wrong rule.
        if "Best answer:" not in gt:
            n_no_reference += 1
            problems.append(f"ground truth has no 'Best answer:' reference for "
                            f"{r['id']}: {gt[:70]!r}")

        out.append({
            "uid": uid,
            "id": r["id"],
            "category": r["category"],              # §11.2 PRIMARY blocking level
            "coarse_category": cmap[r["category"]],  # §11.2 secondary only
            "question": q,
            "ground_truth": gt,
            "source": "truthfulqa",
            # No judge-bound set in 0.5b: TruthfulQA is uniformly verifiable, so there
            # is no non-verifiable arm to compute Delta_artifact against (§11.3). The
            # flag is emitted as False so the analysis code path stays identical.
            "in_primary": True,
            "in_judgebound": False,
            "in_secondary": True,
            "metadata": r.get("metadata", {}),
        })

    return out, cats, problems, n_placeholder, n_no_reference


def main():
    ap = argparse.ArgumentParser(description="Build the frozen Phase 0.5b manifest (§11.1)")
    ap.add_argument("--check", action="store_true",
                    help="run every verification and write nothing")
    ap.add_argument("--out", type=Path, default=MANIFEST_PATH)
    args = ap.parse_args()

    rows = read_jsonl(SOURCE_PATH)
    out, cats, problems, n_ph, n_nr = build(rows)

    print(f"source     {SOURCE_PATH.relative_to(BASE_DIR)}")
    print(f"prompts    {len(out)}")
    print(f"categories {len(cats)} native -> {len(COARSE_STRATA)} coarse")
    print()
    print("Verification (each of these is a defect that shipped in Phase 0.5):")
    print(f"  unsubstituted [placeholder] tokens ......... {n_ph}   (V3 shipped 42)")
    print(f"  ground truths with no sourced reference .... {n_nr}   (V3: 94/98 factual)")
    print(f"  duplicate uids ............................ "
          f"{len(out) - len({r['uid'] for r in out})}")
    print(f"  duplicate question texts .................. "
          f"{len(out) - len({r['question'].strip() for r in out})}")
    print(f"  merge map is a strict partition ............ "
          f"{'yes' if not any('merge map' in p or 'not in' in p for p in problems) else 'NO'}")
    print()

    fine = list(cats.values())
    coarse = [sum(cats[n] for n in v) for v in COARSE_STRATA.values()]
    print("Blocked within-stratum pairs (the power the estimator actually has):")
    print(f"  native-38 (PRIMARY, §11.2) .. {blocked_pairs(fine):6d} pairs, "
          f"n range {min(fine)}-{max(fine)}")
    print(f"  coarse-13 (secondary only) .. {blocked_pairs(coarse):6d} pairs, "
          f"n range {min(coarse)}-{max(coarse)}")
    print(f"  pooled (no blocking) ........ {blocked_pairs([len(out)]):6d} pairs")
    at_risk = [n for n in fine if n < 10]
    print(f"  §6.7 at-risk strata (n<10) .. {len(at_risk)} strata, "
          f"{blocked_pairs(at_risk)} pairs "
          f"({blocked_pairs(at_risk) / blocked_pairs(fine):.1%} of primary)")
    print()

    if problems:
        shown = problems[:15]
        print(f"REFUSING TO WRITE — {len(problems)} verification failure(s):")
        for p in shown:
            print(f"  - {p}")
        if len(problems) > len(shown):
            print(f"  ... and {len(problems) - len(shown)} more")
        sys.exit(1)

    print("All verifications passed.")
    if args.check:
        print("--check: nothing written.")
        return
    if args.out.exists():
        sys.exit(f"{args.out} already exists. §11.1 freezes the manifest once "
                 "generation starts — delete it deliberately if you really mean to "
                 "rebuild, and do not rebuild it mid-run.")
    with open(args.out, "w") as f:
        for r in out:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"wrote {len(out)} prompts -> {args.out.relative_to(BASE_DIR)}")
    print()
    print("NEXT: commit this file before generating anything. §11.1 freezes it, and a")
    print("manifest that changes mid-run silently mixes two populations in one file.")


if __name__ == "__main__":
    main()
