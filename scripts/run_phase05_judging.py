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

Judge must share no family with EITHER evaluated model (§5), because family-level
self-preference would bias one model's P-hat asymmetrically, and differential
per-model judge error does not average out in a cross-model ranking comparison.
Together's serverless tier on this account offers only Meta and OpenAI models, so that
requirement is unsatisfiable there — the judge runs on the Anthropic API instead
(claude-haiku-4-5, ~$50 for this run, billed separately from the Together balance).
The guard derives forbidden family tokens from the models actually present in the
completions file, so it tracks §3 automatically rather than drifting.

Requires ANTHROPIC_API_KEY in .env and the `anthropic` package.

Output is append-only JSONL at results/phase05/judgments.jsonl, resumable: re-running
skips any (uid, model, sample_idx) already judged successfully.

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

from src.models.judge_client import (  # noqa: E402
    JUDGE_RUBRIC_VERSION, JudgeClient)
from src.utils.env import load_env_file  # noqa: E402

MANIFEST_PATH = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"
OUTPUT_DIR = BASE_DIR / "results" / "phase05"
COMPLETIONS_PATH = OUTPUT_DIR / "completions.jsonl"
OUTPUT_PATH = OUTPUT_DIR / "judgments.jsonl"

# Dataset profiles. phase05 = the V3 pilot (§4); phase05b = the TruthfulQA replication
# (§11). Judgments must never be mixed across datasets OR across rubric versions --
# see JUDGE_RUBRIC_VERSION in src/models/judge_client.py, which is stamped onto every
# row so a mixed file is detectable after the fact rather than silently pooled.
DATASETS = {
    "phase05": "phase05_manifest.jsonl",
    "phase05b": "phase05b_manifest.jsonl",
}


def configure(dataset):
    """Point the module at a dataset profile. Call before any path is read."""
    global MANIFEST_PATH, OUTPUT_DIR, COMPLETIONS_PATH, OUTPUT_PATH
    MANIFEST_PATH = BASE_DIR / "data" / "prompts" / DATASETS[dataset]
    OUTPUT_DIR = BASE_DIR / "results" / dataset
    COMPLETIONS_PATH = OUTPUT_DIR / "completions.jsonl"
    OUTPUT_PATH = OUTPUT_DIR / "judgments.jsonl"

# §5 — third-VENDOR judge on the Anthropic API, not Together. With only Meta and
# OpenAI models on Together's serverless tier (verified 2026-08-25), family
# independence is unsatisfiable there: every available judge would share a family with
# one evaluated model. claude-haiku-4-5 is $1/$5 per M tokens, the cheapest Anthropic
# model, ~$50 for this run — billed separately from the Together balance.
# Do NOT add prompt caching: Haiku 4.5's minimum cacheable prefix is 4096 tokens and
# the judge system prompt is well under that, so a marker would silently do nothing.
# Re-measured 2026-08-28 after rubric v2: 5,079 chars ~= 1,270 tokens, still under the
# minimum. v2 roughly doubled the system prompt, which adds ~$20 of input cost over a
# full 0.5b run — revisit caching if the rubric ever crosses the threshold.
JUDGE_MODEL = "claude-haiku-4-5"
JUDGE_PROVIDER = "anthropic"
JUDGE_TEMPERATURE = 0.0

# §5 — family tokens are DERIVED from the models actually present in the completions
# file, not hardcoded, so this guard cannot drift out of sync with §3 when the model
# panel changes. Maps a config key or model id to the vendor/family words that must
# not appear in the judge id.
FAMILY_TOKENS = {
    "llama": ["llama", "meta"],
    "meta": ["llama", "meta"],
    "mistral": ["mistral", "mixtral"],
    "mixtral": ["mistral", "mixtral"],
    "gpt-oss": ["gpt-oss", "openai", "gpt"],
    "openai": ["gpt-oss", "openai", "gpt"],
    "qwen": ["qwen"],
    "deepseek": ["deepseek"],
    "gemma": ["gemma", "google"],
    "claude": ["claude", "anthropic"],
}

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


def families_of(name):
    """Vendor/family tokens implied by a model key or id."""
    lowered = name.lower()
    tokens = set()
    for needle, family in FAMILY_TOKENS.items():
        if needle in lowered:
            tokens.update(family)
    return tokens


def check_judge_family(evaluated_models):
    """§5: refuse to run if the judge shares a family with any evaluated model.

    Derives families from the models actually present in the completions file, so the
    guard tracks §3 automatically instead of relying on a hardcoded list.
    """
    judge_families = families_of(JUDGE_MODEL)
    if not judge_families:
        sys.exit(f"REFUSING TO RUN: cannot determine the family of judge "
                 f"{JUDGE_MODEL!r}. Add it to FAMILY_TOKENS so the §5 independence "
                 "check can be enforced rather than silently skipped.")

    for model in sorted(evaluated_models):
        model_families = families_of(model)
        if not model_families:
            sys.exit(f"REFUSING TO RUN: cannot determine the family of evaluated "
                     f"model {model!r}. Add it to FAMILY_TOKENS.")
        shared = judge_families & model_families
        if shared:
            sys.exit(
                f"REFUSING TO RUN: judge {JUDGE_MODEL!r} shares family {sorted(shared)} "
                f"with evaluated model {model!r}. Family self-preference biases that "
                "model's P-hat asymmetrically, and differential per-model judge error "
                "does not average out in a ranking comparison. See "
                "PHASE_0.5_SPEC.md §5."
            )

    print(f"judge family check: {JUDGE_MODEL} ({sorted(judge_families)}) shares no "
          f"family with {sorted(evaluated_models)}")


def existing_keys(path):
    done, failed = set(), set()
    for row in read_jsonl(path):
        key = (row["uid"], row["model"], row["sample_idx"])
        if row.get("judge_failed"):
            failed.add(key)
        else:
            done.add(key)
    return done, failed - done


def stratified_sample(rows, limit):
    """Round-robin across (category, model), deterministically.

    A plain rows[:limit] after sorting by (category, uid, model, sample_idx) yields all
    `limit` samples of a SINGLE prompt from a single model in the first category —
    a smoke test that validates one prompt out of 704 and one model out of two. The
    generation script had the same defect; this is the same fix.
    """
    buckets = defaultdict(list)
    for r in rows:
        buckets[(r["category"], r["model"])].append(r)
    keys = sorted(buckets)
    picked, depth = [], 0
    longest = max(len(v) for v in buckets.values())
    while len(picked) < limit and depth < longest:
        for k in keys:
            if depth < len(buckets[k]) and len(picked) < limit:
                picked.append(buckets[k][depth])
        depth += 1
    picked.sort(key=lambda r: (r["category"], r["uid"], r["model"], r["sample_idx"]))
    return picked


def judge_one(judge, completion_row, ground_truth):
    """One judgment. Enforces the failure contract: no label on failure."""
    key_fields = {
        "uid": completion_row["uid"],
        "prompt_id": completion_row.get("prompt_id"),
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
        # Provenance, both stamped per row rather than assumed run-wide: a resumed run
        # can span a rubric edit, and labels are only comparable within a version.
        "rubric_version": result.get("rubric_version", JUDGE_RUBRIC_VERSION),
        # Rubric v2 diagnostic. Carries the §6.1 label-boundary sensitivity on
        # "correct rejection then unmarked fabrication" (pinned to 2), so the
        # alternative mapping to 1 is computable without re-judging 32,680 rows.
        "mixed_rejection_then_fabrication":
            bool(result.get("mixed_rejection_then_fabrication", False)),
    }


def preflight(judge, completions, ground_truths):
    """One real judgment, end to end, before committing to a long run."""
    print(f"Preflight: judge = {JUDGE_MODEL} ({JUDGE_PROVIDER})\n")
    sample = next((c for c in completions if c.get("completion")), None)
    if sample is None:
        sys.exit("No successful completions to judge. Run generation first.")

    row = judge_one(judge, sample, ground_truths[sample["uid"]])
    if row.get("judge_failed"):
        print(f"  FAIL  {row.get('error')}")
        print("\nCheck that ANTHROPIC_API_KEY is set in .env and that the `anthropic` "
              "package is installed (pip3 install anthropic).")
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
        description="Phase 0.5 / 0.5b: judge pilot completions (resumable)")
    parser.add_argument("--dataset", choices=sorted(DATASETS), default="phase05",
                        help="phase05 = V3 pilot (§4); phase05b = TruthfulQA "
                             "replication (§11). Reads and writes results/<dataset>/.")
    parser.add_argument("--preflight", action="store_true",
                        help="Judge one completion to verify the judge works, then exit")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only judge the first N completions (smoke test)")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Also retry completions whose judgment previously failed")
    args = parser.parse_args()

    configure(args.dataset)
    print(f"dataset: {args.dataset}   manifest: {MANIFEST_PATH.name}   "
          f"judge: {JUDGE_MODEL} rubric {JUDGE_RUBRIC_VERSION}")

    # The judge runs on the Anthropic API (§5), not Together.
    load_env_file(required=["ANTHROPIC_API_KEY"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = read_jsonl(MANIFEST_PATH)
    if not manifest:
        sys.exit(f"No manifest at {MANIFEST_PATH}. Run build_phase05_manifest.py first.")
    # Keyed on uid, NOT id: V3 and the pool files reuse the same id space, so
    # keying on id would pair 54 prompts with the WRONG ground truth.
    ground_truths = {r["uid"]: r["ground_truth"] for r in manifest}

    completions = read_jsonl(COMPLETIONS_PATH)
    if not completions:
        sys.exit(f"No completions at {COMPLETIONS_PATH}. "
                 "Run scripts/run_phase05_generation.py first.")

    # §5 independence check, against the models actually generated — not a static list.
    check_judge_family({r["model"] for r in completions})

    judge = JudgeClient(model_name=JUDGE_MODEL, provider=JUDGE_PROVIDER,
                        temperature=JUDGE_TEMPERATURE)

    if args.preflight:
        sys.exit(0 if preflight(judge, completions, ground_truths) else 1)

    # Generation failures have no text to judge; they already reduce k_eff.
    judgeable = [c for c in completions if c.get("completion")]
    skipped_gen_failures = len(completions) - len(judgeable)
    judgeable.sort(key=lambda r: (r["category"], r["uid"],
                                  r["model"], r["sample_idx"]))
    if args.limit:
        judgeable = stratified_sample(judgeable, args.limit)

    done, previously_failed = existing_keys(OUTPUT_PATH)
    tasks = []
    for row in judgeable:
        key = (row["uid"], row["model"], row["sample_idx"])
        if key in done:
            continue
        if key in previously_failed and not args.retry_failed:
            continue
        if row["uid"] not in ground_truths:
            sys.exit(f"uid {row['uid']} is not in the manifest — "
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
        # Still print the state summary. It costs nothing, spends nothing, and is the
        # cheapest way to check where a run stands — which matters now that the
        # summary is trustworthy (see the two fixed defects in report_state()).
        print("Nothing to do.")
        report_state(completions)
        return

    completed, failed = 0, 0
    buffer = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(judge_one, judge, row, ground_truths[row["uid"]])
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
    report_state(completions)


def report_state(completions):
    """§5.1 — failure-rate gate, k_eff report, label distribution.

    TWO DEFECTS WERE FIXED HERE ON 2026-08-26. Both were reporting-only and never
    touched a label, but both were actively misleading on the first real run. They are
    described in full because the same traps are easy to reintroduce.

    DEFECT 1 — the rate could never clear. This used
        n_failed / len(all_judgments)
    over every row in the file. But append_rows() is APPEND-ONLY, so --retry-failed
    leaves each stale failure row sitting next to the success that replaced it. After a
    fully successful recovery that ratio read 9,213 / 37,373 = 24.65% and kept printing
    the §5.1 infrastructure-failure warning forever, on data that was in fact complete.
    What §5.1 actually cares about is how much data was LOST, so the rate is now
    computed over COMPLETIONS WITH NO LABEL, deduplicated by
    (uid, model, sample_idx). The gross call-failure rate is still shown, because a high
    value means the API was unreliable during the run even if every sample was
    eventually labelled — but it does not gate.

    DEFECT 2 — the k_eff count hid the worst damage. k_eff was a defaultdict(int)
    populated only from rows that SUCCEEDED, so a (uid, model) pair whose every sample
    failed had no key at all and was invisible to the `v < 16` count. On the first run
    it printed 13 pairs below threshold when the true number was 464, because 451 pairs
    had zero successes — a 35x undercount that omitted precisely the pairs that
    mattered. k_eff is now seeded from the full completions cross-product so a
    zero-success pair is counted as k_eff = 0.

    scripts/analyze_phase05.py computes both quantities the same way. Keep them in
    sync; if these two ever disagree again, one of them is wrong.
    """
    all_judgments = read_jsonl(OUTPUT_PATH)

    labelled_keys = set()
    failed_rows = 0
    for r in all_judgments:
        key = (r["uid"], r["model"], r["sample_idx"])
        if r.get("judge_failed") or r.get("label") is None:
            failed_rows += 1
        else:
            labelled_keys.add(key)

    judgeable = {(r["uid"], r["model"], r["sample_idx"]) for r in completions
                 if r.get("completion")}
    unrecovered = sorted(judgeable - labelled_keys)

    if judgeable:
        rate = len(unrecovered) / len(judgeable)
        print(f"\nunrecovered rate (completions with NO label): {rate:.2%} "
              f"({len(unrecovered)}/{len(judgeable)})  <- this is the §5.1 gate")
        if all_judgments:
            print(f"gross call-failure rate (diagnostic, does NOT gate): "
                  f"{failed_rows / len(all_judgments):.2%} "
                  f"({failed_rows}/{len(all_judgments)} rows; append-only, so stale "
                  "failure rows from before a retry are still counted here)")
        if rate > FAILURE_RATE_ABORT:
            print(f"WARNING: above the {FAILURE_RATE_ABORT:.0%} threshold. "
                  "PHASE_0.5_SPEC.md §5.1 treats this as an infrastructure failure, "
                  "not data. Re-run with --retry-failed before analysing.")
        elif unrecovered:
            print(f"  {len(unrecovered)} sample(s) still unlabelled, below the "
                  f"{FAILURE_RATE_ABORT:.0%} gate. Check whether they are retryable:")
            last_error = {}
            for r in all_judgments:
                if r.get("judge_failed"):
                    last_error[(r["uid"], r["model"], r["sample_idx"])] = r.get("error")
            for key in unrecovered[:10]:
                print(f"    {key[0]} {key[1]} idx={key[2]}: "
                      f"{str(last_error.get(key, 'never attempted'))[:90]}")
            if len(unrecovered) > 10:
                print(f"    ... and {len(unrecovered) - 10} more")
            print("  NOTE: a JSON-parse error is NOT retryable. JUDGE_TEMPERATURE is "
                  "0.0, so a retry replays byte-identical malformed judge output. "
                  "Retrying those forever is a no-op — stop and accept the k_eff loss.")

    labels = Counter(r["label"] for r in all_judgments if not r.get("judge_failed"))
    print("\nlabel distribution (0=Correct 1=Partial 2=Hallucination 3=Refusal):")
    for label in (0, 1, 2, 3):
        print(f"  {label}: {labels[label]}")

    # Seeded from the full cross-product so zero-success pairs are visible (defect 2).
    k_eff = {(r["uid"], r["model"]): 0 for r in completions}
    for key in labelled_keys:
        pair = (key[0], key[1])
        if pair in k_eff:
            k_eff[pair] += 1
    below = sum(1 for v in k_eff.values() if v < 16)
    zero = sum(1 for v in k_eff.values() if v == 0)
    print(f"\n(prompt, model) pairs with k_eff < 16 (excluded from the primary "
          f"estimator per §5.1): {below} of {len(k_eff)}"
          f"{f', of which {zero} have k_eff = 0' if zero else ''}")


if __name__ == "__main__":
    main()
