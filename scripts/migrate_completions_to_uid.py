"""One-off repair: re-key Phase 0.5 completions from `prompt_id` to `uid`.

The first full generation run keyed on (prompt_id, model, sample_idx). V3 and the
standalone pool files reuse the same id space while naming DIFFERENT questions, so 54
ids collided and the resume logic skipped the second prompt of each pair as "already
done", producing 2,160 duplicate keys and 108 (prompt_id, model) pairs with more than
k=20 samples.

The completions themselves are sound — every row stores its `question`, which is the
true identity. This joins on question text, writes `uid`, and renumbers `sample_idx`
per (uid, model) so the odd/even split-half in spec §6.2 operates on a clean index.

No API calls. Idempotent: re-running on an already-migrated file is a no-op.

    python3 scripts/migrate_completions_to_uid.py --dry-run
    python3 scripts/migrate_completions_to_uid.py
"""

import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"
COMPLETIONS = BASE_DIR / "results" / "phase05" / "completions.jsonl"


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser(description="Re-key completions on uid")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    manifest = read_jsonl(MANIFEST)
    if "uid" not in manifest[0]:
        sys.exit("Manifest has no `uid` column. Re-run build_phase05_manifest.py first.")
    by_question = {r["question"].strip(): r for r in manifest}
    if len(by_question) != len(manifest):
        sys.exit("Manifest questions are not unique — cannot join on question text.")

    rows = read_jsonl(COMPLETIONS)
    print(f"completions: {len(rows)}")
    if rows and "uid" in rows[0]:
        print("Already migrated (rows carry `uid`). Nothing to do.")
        return

    matched, unmatched = [], []
    for r in rows:
        m = by_question.get(r["question"].strip())
        if m is None:
            unmatched.append(r)
        else:
            matched.append({**r, "uid": m["uid"], "category": m["category"],
                            "source": m["source"]})

    print(f"  matched to a manifest prompt : {len(matched)}")
    print(f"  UNMATCHED (dropped)          : {len(unmatched)}")
    if unmatched:
        for r in unmatched[:3]:
            print(f"    {r.get('prompt_id')} {r['question'][:60]!r}")

    # Renumber sample_idx per (uid, model). The original indices are unreliable after
    # the collision, and §6.2's split-half ceiling splits on odd/even index.
    ok = [r for r in matched if not r.get("generation_failed")]
    failed = [r for r in matched if r.get("generation_failed")]
    grouped = defaultdict(list)
    for r in ok:
        grouped[(r["uid"], r["model"])].append(r)

    renumbered = []
    for (uid, model), group in sorted(grouped.items()):
        group.sort(key=lambda r: (r.get("sample_idx", 0), r["completion"] or ""))
        for i, r in enumerate(group):
            renumbered.append({**r, "sample_idx": i})

    counts = {k: len(v) for k, v in grouped.items()}
    over = {k: n for k, n in counts.items() if n > 20}
    under = {k: n for k, n in counts.items() if n < 20}
    print(f"\n(uid, model) pairs: {len(counts)} / {len(manifest) * 2} expected")
    print(f"  at k=20      : {sum(1 for n in counts.values() if n == 20)}")
    print(f"  k_eff < 20   : {len(under)}")
    print(f"  k_eff > 20   : {len(over)}   (must be 0 after re-keying)")
    missing = [(m["uid"], mo) for m in manifest
               for mo in {r["model"] for r in ok} if (m["uid"], mo) not in counts]
    print(f"  missing pairs: {len(missing)}")
    for uid, model in missing[:8]:
        print(f"    {uid:26s} {model}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return
    if over:
        sys.exit("\nRefusing to write: some pairs still exceed k=20 after re-keying.")

    backup = COMPLETIONS.with_suffix(".jsonl.prekey-backup")
    shutil.copy2(COMPLETIONS, backup)
    out = renumbered + failed
    out.sort(key=lambda r: (r["category"], r["uid"], r["model"], r.get("sample_idx", 0)))
    with open(COMPLETIONS, "w") as f:
        for r in out:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"\nbackup -> {backup.name}")
    print(f"wrote {len(out)} rows ({len(renumbered)} ok + {len(failed)} failed)")


if __name__ == "__main__":
    main()
