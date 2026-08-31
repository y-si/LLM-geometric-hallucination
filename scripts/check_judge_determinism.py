"""Measure the judge's label instability at temperature 0 — the noise floor.

WHY THIS EXISTS. The Batch API verification (run_phase05_judging_batch.py --verify)
found 2 label mismatches in 40 against previously-recorded synchronous labels. That is
either (a) a custom_id mapping bug, which would be fatal and silent, or (b) the judge
simply not being deterministic at temperature 0.0.

The two hypotheses cannot be separated by staring at the mismatches, and the difference
matters enormously: (a) means labels are attached to the wrong completions, (b) means
labels carry ordinary measurement noise that the k=20 design already averages over.

A comfortable-sounding argument for (b) is available -- both mismatches were on
truthfulqa_0144, a prompt whose sync labels are already spread {2:14, 1:4, 0:2}, and
both had the lowest confidences in the set (0.72, 0.75). But that is circumstantial.

THE ACTUAL TEST: re-judge the SAME completions through the SAME synchronous path and
see whether it agrees with its own earlier labels. This isolates the variable. The batch
route is not involved at all, so any disagreement here is pure judge non-determinism and
establishes the noise floor that the batch comparison must be read against.

    sync-vs-sync disagreement ~= batch-vs-sync disagreement  ->  batch path is fine
    sync-vs-sync disagreement ~= 0 but batch disagrees        ->  mapping bug, stop

Temperature 0.0 is greedy decoding but NOT a determinism guarantee: floating-point
non-associativity means results depend on kernel scheduling and server-side batching,
so identical requests can yield different tokens. This script measures how much that
matters for this rubric on this data, which is worth knowing regardless of the batch
question -- it is a lower bound on the judge noise in every P-hat in the study.

Cost: ~$0.01 per repeat per item. Defaults to 40 items x 2 repeats, ~$1.

Usage:
    python3 scripts/check_judge_determinism.py                    # 40 items, 2 repeats
    python3 scripts/check_judge_determinism.py --n 60 --repeats 3
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.judge_client import JUDGE_RUBRIC_VERSION, JudgeClient  # noqa: E402
from src.utils.env import load_env_file  # noqa: E402

JUDGE_MODEL = "claude-haiku-4-5"
JUDGE_PROVIDER = "anthropic"
JUDGE_TEMPERATURE = 0.0

DATASETS = {"phase05": "phase05_manifest.jsonl", "phase05b": "phase05b_manifest.jsonl"}


def read_jsonl(path):
    if not path.exists():
        sys.exit(f"missing: {path}")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser(description="Measure judge label instability at T=0")
    ap.add_argument("--dataset", choices=sorted(DATASETS), default="phase05b")
    ap.add_argument("--n", type=int, default=40, help="completions to re-judge")
    ap.add_argument("--repeats", type=int, default=2, help="times to re-judge each")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    load_env_file(required=["ANTHROPIC_API_KEY"])
    res = BASE_DIR / "results" / args.dataset
    manifest = {r["uid"]: r for r in read_jsonl(BASE_DIR / "data" / "prompts"
                                               / DATASETS[args.dataset])}
    comp = {}
    for r in read_jsonl(res / "completions.jsonl"):
        if r.get("completion"):
            comp[(r["uid"], r["model"], r["sample_idx"])] = r
    prior = {}
    for r in read_jsonl(res / "judgments.jsonl"):
        if not r.get("judge_failed"):
            prior[(r["uid"], r["model"], r["sample_idx"])] = r

    keys = [k for k in sorted(prior) if k in comp][:args.n]
    if not keys:
        sys.exit("no previously-judged completions to re-judge.")

    print(f"judge: {JUDGE_MODEL}  rubric {JUDGE_RUBRIC_VERSION}  T={JUDGE_TEMPERATURE}")
    print(f"re-judging {len(keys)} completions x {args.repeats} repeats, "
          f"through the SYNCHRONOUS path only")
    print()

    judge = JudgeClient(model_name=JUDGE_MODEL, provider=JUDGE_PROVIDER,
                        temperature=JUDGE_TEMPERATURE)

    def one(task):
        k, rep = task
        c = comp[k]
        r = judge.judge(question=c["question"], answer=c["completion"],
                        ground_truth=manifest[k[0]]["ground_truth"])
        return k, rep, (None if r.get("failed") else r["label"])

    tasks = [(k, rep) for k in keys for rep in range(args.repeats)]
    got = defaultdict(list)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, (k, rep, lab) in enumerate(ex.map(one, tasks), 1):
            got[k].append(lab)
            if i % 20 == 0:
                print(f"  {i}/{len(tasks)}", flush=True)

    print()
    print("=" * 74)
    print("NOISE FLOOR — does the synchronous judge agree with ITSELF?")
    print("=" * 74)
    unstable_repeats = 0      # disagreement among this run's own repeats
    differs_from_prior = 0    # disagreement with the stored label
    n_ok = 0
    detail = []
    for k in keys:
        labs = [x for x in got[k] if x is not None]
        if len(labs) < 2:
            continue
        n_ok += 1
        same_run = len(set(labs)) == 1
        vs_prior = prior[k]["label"] not in set(labs)
        if not same_run:
            unstable_repeats += 1
        if prior[k]["label"] != labs[0]:
            differs_from_prior += 1
        if not same_run or prior[k]["label"] != labs[0]:
            detail.append((k, prior[k]["label"], labs,
                           prior[k].get("confidence")))

    print(f"  completions re-judged {args.repeats}x : {n_ok}")
    print(f"  repeats disagreed with each other  : {unstable_repeats} "
          f"({unstable_repeats/n_ok:.1%})")
    print(f"  differed from the stored label     : {differs_from_prior} "
          f"({differs_from_prior/n_ok:.1%})")
    print()
    if detail:
        print("  unstable items (stored -> this run's repeats), with stored confidence:")
        for k, p, labs, conf in detail[:15]:
            print(f"    {k[0][-4:]} {k[1][:11]} s{k[2]:02d}: {p} -> {labs}  conf={conf}")
        print()
        confs = [c for _, _, _, c in detail if c is not None]
        allc = [prior[k].get("confidence") for k in keys
                if prior[k].get("confidence") is not None]
        if confs and allc:
            print(f"  mean stored confidence, UNSTABLE items : "
                  f"{sum(confs)/len(confs):.3f}")
            print(f"  mean stored confidence, all items      : "
                  f"{sum(allc)/len(allc):.3f}")
            print()
            print("  If instability concentrates on LOW-confidence items, the judge is")
            print("  simply uncertain there and k=20 averages over it. If it is spread")
            print("  across high-confidence items too, something structural is wrong.")
    else:
        print("  the synchronous judge is perfectly self-consistent on this sample.")
        print()
        print("  IF the batch run disagreed with stored labels while sync does not,")
        print("  the batch path is NOT equivalent -- investigate the custom_id mapping")
        print("  before submitting the full run.")
    print("=" * 74)
    print()
    print("HOW TO READ THIS against the batch verification (2 mismatches in 40 = 5.0%):")
    print(f"  sync-vs-sync instability here      : {unstable_repeats/n_ok:.1%}")
    print(f"  sync-vs-stored instability here    : {differs_from_prior/n_ok:.1%}")
    print("  If those are comparable to 5%, the batch mismatches are ordinary judge")
    print("  noise at T=0 and the batch route is equivalent. If they are ~0%, they are")
    print("  not, and the mapping needs fixing.")


if __name__ == "__main__":
    main()
