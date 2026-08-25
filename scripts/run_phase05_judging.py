"""Phase 0.5 step 2: judge the pilot completions.

Pre-registered design: research_paper/PHASE_0.5_SPEC.md §5 (judge), §5.1 (failure
contract), §6.1 (label mapping). Reads results/phase05/completions.jsonl and emits
one judgment per completion.

THE FAILURE CONTRACT (§5.1) — this is the March 2026 contamination fix, and the
reason this script does not use ConsensusJudge:

  judge_client.py returns {"label": 3, ...} on failure, tagged "failed": True. The
  label value is garbage; the flag is the only guard. Worse, consensus_judge.py:63
  falls back to VOTING the failed results when every judge fails
  (`vote_results = real_results if real_results else results`) and strips the flag
  from its return — so with a single judge that fallback fires on every failure and
  re-creates the original bug, silently turning API errors into "Refused" labels.

  Therefore: call JudgeClient directly, and treat failed: True as "no label exists".
  A failed judgment is recorded with judge_failed=true and NO label, and the
  prompt's k_eff decrements. Never coerce a failure into a label.

Label mapping (§6.1), pinned: 0=Correct, 1=Partial, 2=Hallucination, 3=Refusal.
P-hat = #(label == 2) / k_eff. Labels 0, 1, and 3 stay in the denominator as
non-hallucinations, because the paper needs the UNCONDITIONAL probability that
sampling this model on this prompt yields a hallucination — that is what an
inference-time gate acts on. Dropping refusals would condition on the model having
attempted an answer and introduce a selection effect. P-hat is computed downstream in
the analysis script, not here; this script only produces labels.

Judge must be a THIRD-FAMILY model (§5): not Mistral (Model A) and not Llama
(Model B), because family-level self-preference would bias one model's P-hat
asymmetrically, and differential per-model judge error does not average out in a
cross-model ranking comparison.

Output is append-only JSONL at results/phase05/judgments.jsonl, resumable: re-running
skips any (prompt_id, model, sample_idx) already judged successfully.

Usage:
    python3 scripts/run_phase05_judging.py --preflight     # verify judge responds
    python3 scripts/run_phase05_judging.py                 # full run (resumable)
    python3 scripts/run_phase05_judging.py --retry-failed  # retry failed judgments
"""

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.judge_client import JudgeClient  # noqa: E402

MANIFEST_PATH = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"
OUTPUT_DIR = BASE_DIR / "results" / "phase05"
COMPLETIONS_PATH = OUTPUT_DIR / "completions.jsonl"
OUTPUT_PATH = OUTPUT_DIR / "judgments.jsonl"

# §5 — third-family judge. VERIFIED AVAILABLE on Together 2026-08-25 against the live
# model list. Documented fallbacks if it is ever retired: DeepSeek V3 or Command R+
# (both third-family relative to Mistral and Llama). Run --preflight after any change.
JUDGE_MODEL = "Qwen/Qwen2.5-72B-Instruct-Turbo"
JUDGE_PROVIDER = "together"
JUDGE_TEMPERATURE = 0.0

# Families of the evaluated models — the judge must not be one of these (§5).
FORBIDDEN_JUDGE_SUBSTRINGS = ["mistral", "mixtral", "llama", "meta-llama"]

K_SAMPLES = 20
MAX_WORKERS = 8
FAILURE_RATE_ABORT = 0.02  # §5.1 — above this the run is an infra failure, not data

write_lock = threading.Lock()


def read_jsonl(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def append_rows(path, rows):
    with write_lock:
        with open(path, "a") as f:
            for row in rows:
                f.write(json.dumps(row, sort_keys=True) + "\n")


def check_judge_family():
    """§5: refuse to run with a judge that shares a family with either model."""
    lowered = JUDGE_MODEL.lower()
    hits = [s for s in FORBIDDEN_JUDGE_SUBSTRINGS if s in lowered]
    if hits:
        sys.exit(
            f"REFUSING TO RUN: judge {JUDGE_MODEL!r} matches {hits}, which shares a "
            "model family with an evaluated model. Family self-preference biases that "
            "model's P-hat asymmetrically and does not average out in a ranking "
            "comparison. See PHASE_0.5_SPEC.md §5."
        )


def existing_keys(path):
    done, failed = set(), set()
    for row in read_jsonl(path):
        key = (row["prompt_id"], row["model"], row["sample_idx"])
        if row.get("judge_failed"):
            failed.add(key)
        else:
            done.add(key)
    return done, failed - done


def judge_one(judge, completion_row, ground_truth):
    """One judgment. Enforces the failure contract: no label on failure."""
    key_fields = {
        "prompt_id": completion_row["prompt_id"],
        "category": completion_row["category"],
        "model": completion_row["model"],
        "sample_idx": completion_row["sample_idx"],
    }
    try:
        # JudgeClient already retries 3x with exponential backoff internally, so a
        # failed: True return means three attempts were exhausted.
        result = judge.judge(
            question=completion_row["question"],
            answer=completion_row["completion"],
            ground_truth=ground_truth,
        )
    except Exception as e:  # noqa: BLE001 — JudgeClient shouldn't raise, but if it does
        return {**key_fields, "judge_failed": True, "error": f"raised: {e}"}

    # THE CONTRACT: failed -> no label. Do not read result["label"] here.
    if result.get("failed"):
        return {**key_fields, "judge_failed": True,
                "error": result.get("justification", "judge failed")}

    return {
        **key_fields,
        "label": result["label"],
        "confidence": result["confidence"],
        "justification": result["justification"],
        "judge_model": JUDGE_MODEL,
    }


def preflight(judge, completions, ground_truths):
    """One real judgment, end to end, before committing to a long run."""
    print(f"Preflight: judge = {JUDGE_MODEL} ({JUDGE_PROVIDER})\n")
    sample = next((c for c in completions if c.get("completion")), None)
    if sample is None:
        sys.exit("No successful completions to judge. Run generation first.")

    row = judge_one(judge, sample, ground_truths[sample["prompt_id"]])
    if row.get("judge_failed"):
        print(f"  FAIL  {row.get('error')}")
        print("\nVerify the model ID and your access at together.ai/models. "
              "Documented fallbacks: DeepSeek V3, Command R+.")
        return False

    print(f"  prompt   : {sample['question'][:70]}")
    print(f"  answer   : {(sample['completion'] or '')[:70].strip()}")
    print(f"  label    : {row['label']}  (0=Correct 1=Partial 2=Hallucination 3=Refusal)")
    print(f"  conf     : {row['confidence']}")
    print(f"  reasoning: {row['justification'][:100]}")
    print("\n  OK")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Phase 0.5: judge pilot completions (resumable)")
    parser.add_argument("--preflight", action="store_true",
                        help="Judge one completion to verify the judge works, then exit")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only judge the first N completions (smoke test)")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Also retry completions whose judgment previously failed")
    args = parser.parse_args()

    check_judge_family()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = read_jsonl(MANIFEST_PATH)
    if not manifest:
        sys.exit(f"No manifest at {MANIFEST_PATH}. Run build_phase05_manifest.py first.")
    ground_truths = {r["id"]: r["ground_truth"] for r in manifest}

    completions = read_jsonl(COMPLETIONS_PATH)
    if not completions:
        sys.exit(f"No completions at {COMPLETIONS_PATH}. "
                 "Run scripts/run_phase05_generation.py first.")

    judge = JudgeClient(model_name=JUDGE_MODEL, provider=JUDGE_PROVIDER,
                        temperature=JUDGE_TEMPERATURE)

    if args.preflight:
        sys.exit(0 if preflight(judge, completions, ground_truths) else 1)

    # Generation failures have no text to judge; they already reduce k_eff.
    judgeable = [c for c in completions if c.get("completion")]
    skipped_gen_failures = len(completions) - len(judgeable)
    judgeable.sort(key=lambda r: (r["category"], str(r["prompt_id"]),
                                  r["model"], r["sample_idx"]))
    if args.limit:
        judgeable = judgeable[:args.limit]

    done, previously_failed = existing_keys(OUTPUT_PATH)
    tasks = []
    for row in judgeable:
        key = (row["prompt_id"], row["model"], row["sample_idx"])
        if key in done:
            continue
        if key in previously_failed and not args.retry_failed:
            continue
        if row["prompt_id"] not in ground_truths:
            sys.exit(f"prompt_id {row['prompt_id']} is not in the manifest — "
                     "completions and manifest are out of sync.")
        tasks.append(row)

    print(f"judge            : {JUDGE_MODEL}")
    print(f"completions      : {len(completions)}")
    if skipped_gen_failures:
        print(f"  generation failures (no text, not judgeable): {skipped_gen_failures}")
    print(f"already judged   : {len(done)}")
    if previously_failed:
        state = "will retry" if args.retry_failed else "skipping (use --retry-failed)"
        print(f"previously failed: {len(previously_failed)}  ({state})")
    print(f"to judge         : {len(tasks)}\n")

    if not tasks:
        print("Nothing to do.")
        return

    completed, failed = 0, 0
    buffer = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(judge_one, judge, row, ground_truths[row["prompt_id"]])
                   for row in tasks]
        for future in as_completed(futures):
            row = future.result()
            buffer.append(row)
            completed += 1
            if row.get("judge_failed"):
                failed += 1

            if len(buffer) >= 50:
                append_rows(OUTPUT_PATH, buffer)
                buffer = []

            if completed % 500 == 0 or completed == len(tasks):
                elapsed = time.time() - start
                rate = completed / elapsed if elapsed else 0
                remaining = (len(tasks) - completed) / rate if rate else 0
                print(f"  {completed}/{len(tasks)}  failed={failed}  "
                      f"{rate:.1f}/s  eta={remaining / 60:.0f}m")

    if buffer:
        append_rows(OUTPUT_PATH, buffer)

    print(f"\nwrote -> {OUTPUT_PATH.relative_to(BASE_DIR)}")
    print(f"judged {completed - failed}, failed {failed}")

    # §5.1 — failure rate gate and k_eff report.
    all_judgments = read_jsonl(OUTPUT_PATH)
    n_failed = sum(1 for r in all_judgments if r.get("judge_failed"))
    if all_judgments:
        rate = n_failed / len(all_judgments)
        print(f"\ncumulative judge failure rate: {rate:.2%} "
              f"({n_failed}/{len(all_judgments)})")
        if rate > FAILURE_RATE_ABORT:
            print(f"WARNING: above the {FAILURE_RATE_ABORT:.0%} threshold. "
                  "PHASE_0.5_SPEC.md §5.1 treats this as an infrastructure failure, "
                  "not data. Re-run with --retry-failed before analysing.")

    labels = Counter(r["label"] for r in all_judgments if not r.get("judge_failed"))
    print("\nlabel distribution (0=Correct 1=Partial 2=Hallucination 3=Refusal):")
    for label in (0, 1, 2, 3):
        print(f"  {label}: {labels[label]}")

    k_eff = defaultdict(int)
    for r in all_judgments:
        if not r.get("judge_failed"):
            k_eff[(r["prompt_id"], r["model"])] += 1
    below = sum(1 for v in k_eff.values() if v < 16)
    print(f"\n(prompt, model) pairs with k_eff < 16 (excluded from the primary "
          f"estimator per §5.1): {below}")


if __name__ == "__main__":
    main()
