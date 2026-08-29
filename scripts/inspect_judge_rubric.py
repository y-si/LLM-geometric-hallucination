"""Read the judge's reasoning on a handful of rows to confirm rubric v2 is working.

WHY THIS EXISTS. Rubric v2 was written 2026-08-28 and, at the time this script was
added, had never judged a single real completion. Its most consequential change is a new
**CATEGORY 5** for TruthfulQA's three-part ground truth
(`Best answer: / Also acceptable: / Known incorrect answers:`), which v1 had no rule for
at all -- v1 fell through to CATEGORY 3 and instructed the judge to consult "established
reality", i.e. to ignore the authoritative known-incorrect list, the single most valuable
signal in the dataset. Judging Phase 0.5b costs ~$125. Finding out afterwards that the
judge never used the list would waste all of it.

A label alone cannot tell you whether the rubric routed correctly -- a wrong rule
produces confident, well-formed labels too. The JUSTIFICATION can, because the judge is
instructed to reference the specific category rule it applied. So this script prints the
reasoning next to the ground truth and greps for the tells:

    "CATEGORY 5" / "Known incorrect" / "Also acceptable"   -> routed correctly
    "CATEGORY 3" / "established reality"                   -> fell through, v2 not working
    label 3 on an item whose ground truth lists "I have no comment"
                                                           -> the v1 trap, not fixed

It also reports how often `mixed_rejection_then_fabrication` fires, since that flag
exists to make the §6.1 label-boundary sensitivity computable later; a flag that never
fires is indistinguishable from a flag that is broken.

This is READ-ONLY. It judges nothing and writes nothing. Judge some rows first:

    python3 scripts/run_phase05_judging.py --dataset phase05b --limit 20   # ~$0.05
    python3 scripts/inspect_judge_rubric.py --dataset phase05b

Usage:
    python3 scripts/inspect_judge_rubric.py [--dataset phase05b] [-n 8]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

DATASETS = {
    "phase05": "phase05_manifest.jsonl",
    "phase05b": "phase05b_manifest.jsonl",
}
LABEL_NAMES = {0: "Correct", 1: "Partial", 2: "HALLUCINATION", 3: "Refusal"}

ROUTED_RIGHT = re.compile(r"CATEGORY 5|known incorrect|also acceptable|best answer",
                          re.I)
ROUTED_WRONG = re.compile(r"CATEGORY 3|established reality", re.I)
NO_COMMENT = re.compile(r"I have no comment", re.I)


def read_jsonl(path):
    if not path.exists():
        sys.exit(f"missing: {path}\nJudge some rows first:\n"
                 f"  python3 scripts/run_phase05_judging.py --dataset phase05b --limit 20")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser(description="Inspect judge reasoning for rubric routing")
    ap.add_argument("--dataset", choices=sorted(DATASETS), default="phase05b")
    ap.add_argument("-n", type=int, default=8, help="how many rows to print in full")
    args = ap.parse_args()

    res = BASE_DIR / "results" / args.dataset
    man = {r["uid"]: r for r in read_jsonl(BASE_DIR / "data" / "prompts"
                                          / DATASETS[args.dataset])}
    comp = {(r["uid"], r["model"], r["sample_idx"]): r
            for r in read_jsonl(res / "completions.jsonl")}
    judg = [j for j in read_jsonl(res / "judgments.jsonl")
            if not j.get("judge_failed")]

    if not judg:
        sys.exit("no successful judgments yet.")

    versions = Counter(j.get("rubric_version", "(unstamped)") for j in judg)
    print(f"{len(judg)} judged rows   rubric versions: {dict(versions)}")
    print()

    right = wrong = 0
    trap = []
    for j in judg:
        js = j.get("justification", "")
        if ROUTED_RIGHT.search(js):
            right += 1
        if ROUTED_WRONG.search(js):
            wrong += 1
        gt = man[j["uid"]].get("ground_truth", "")
        if NO_COMMENT.search(gt) and j["label"] == 3:
            trap.append(j)

    print("=" * 78)
    print("ROUTING CHECK — is the judge actually using the three-part reference?")
    print("=" * 78)
    print(f"  justifications citing CATEGORY 5 / the answer lists : {right}/{len(judg)}"
          f"  ({right/len(judg):.0%})")
    print(f"  justifications citing CATEGORY 3 / 'established reality': {wrong}/{len(judg)}"
          f"  ({wrong/len(judg):.0%})   <- want ~0")
    print()
    print(f"  v1 TRAP: label=3 Refusal where the ground truth lists 'I have no comment'")
    print(f"    {len(trap)} case(s)   <- want 0; CATEGORY 5 says a listed non-answer is "
          f"CORRECT (0)")
    for t in trap[:3]:
        print(f"      {t['uid']} / {t['model']}")
    print()
    flag = sum(1 for j in judg if j.get("mixed_rejection_then_fabrication"))
    print(f"  mixed_rejection_then_fabrication fired: {flag}/{len(judg)}")
    print(f"    (field present on {sum(1 for j in judg if 'mixed_rejection_then_fabrication' in j)}"
          f"/{len(judg)} rows — absent means the judge omitted it)")
    print()
    print("  label distribution:", dict(sorted(Counter(j["label"] for j in judg).items())))
    print()

    print("=" * 78)
    print(f"FULL REASONING ON {min(args.n, len(judg))} ROWS — read these yourself")
    print("=" * 78)
    for j in judg[:args.n]:
        c = comp.get((j["uid"], j["model"], j["sample_idx"]), {})
        gt = man[j["uid"]].get("ground_truth", "")
        print()
        print(f"--- {j['uid']}  {j['model']}  sample {j['sample_idx']} "
              f"[{j['category']}] ---")
        print(f"Q  {c.get('question','')}")
        print(f"GROUND TRUTH")
        # NEVER truncate the ground truth. It is the authoritative reference the whole
        # check is against, and TruthfulQA's known-incorrect line routinely exceeds 150
        # chars. Truncating it produced a false alarm on 2026-08-28: the display cut
        # "; The happiest place on Earth is Denmark" off truthfulqa_0144's 191-char list,
        # which made the judge look like it was inventing entries when it was quoting
        # correctly. Wrap instead of clip.
        for line in gt.split("\n"):
            head = line
            while len(head) > 110:
                cut = head.rfind("; ", 0, 110)
                cut = cut + 1 if cut > 40 else 110
                print(f"   {head[:cut]}")
                head = head[cut:].lstrip()
            print(f"   {head}")
        ans = (c.get("completion") or "(EMPTY — gpt-oss spent the budget on reasoning)")
        print(f"MODEL ANSWER ({c.get('output_tokens','?')} tok)")
        print(f"   {ans[:400].replace(chr(10), ' ')}")
        print(f"JUDGE -> {j['label']} = {LABEL_NAMES[j['label']]}  "
              f"(conf {j.get('confidence')})")
        print(f"   {j.get('justification','')[:600]}")
    print()
    print("What you are looking for: does the reasoning quote the Best answer / Also")
    print("acceptable / Known incorrect lists, or does it argue from its own knowledge?")
    print("The former is CATEGORY 5 working. The latter means v2 is not routing and the")
    print("~$125 judging run would measure model-vs-judge-knowledge instead.")


if __name__ == "__main__":
    main()
