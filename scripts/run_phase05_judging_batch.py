"""Phase 0.5b judging via the Anthropic Message Batches API — same labels, half the cost.

WHY THIS EXISTS. Judging 32,680 completions synchronously costs ~$125 (calibrated
against the real ~$80 Phase 0.5 Anthropic bill, not a recalled rate). The Batch API
gives 50% off both input and output, taking it to ~$63.

THIS IS A COST OPTIMISATION, NOT A METHODOLOGICAL CHANGE, and that claim has to be
structural rather than asserted. Every field that could affect a label is taken from the
same constants the synchronous path uses:

    model            JUDGE_MODEL          (claude-haiku-4-5)
    system           JUDGE_SYSTEM_PROMPT  (rubric v2, plain string form)
    user content     JUDGE_USER_TEMPLATE  + the same "\\n\\nRespond in JSON." suffix
    temperature      JUDGE_TEMPERATURE    (0.0)
    max_tokens       JUDGE_MAX_TOKENS     (1000)
    response parsing parse_judge_response()  -- the SAME function, not a copy

ONE REQUEST PER COMPLETION. This is the part that matters most and the reason batching
is safe here. Packing several completions into one prompt would let the judge compare
answers and anchor across them, inducing within-prompt correlation; tau_self is a
SPLIT-HALF reliability, so that would corrupt it directly, and P-hat's k_eff denominator
assumes independent labels. The Batch API does nothing of the kind -- it is the same
32,680 independent requests, submitted as a list instead of one at a time.

§5.1 FAILURE CONTRACT, PRESERVED. A request that errors, expires or is cancelled gets a
row with judge_failed=true and NO label. Never coerce a failure into a label; the March
2026 contamination incident happened exactly that way. Batch actually makes this easier
than the sync path: every request comes back with an explicit result.type, so there is
no ambiguity about whether a label exists.

THE REAL RISK IS THE custom_id ROUND-TRIP. Results come back keyed by a custom_id we
assign, and a wrong mapping would attach labels to the wrong completions -- silently,
with plausible-looking numbers. That is not hypothetical for this project: the same
class of bug produced the prompt_id collision that forced re-keying Phase 0.5 on uid,
and the k_eff undercount that reported 11 when the truth was 87. So:

  * custom_id is SELF-DESCRIBING (prompt_id-A|B-sampleidx), not an index into a
    side file that could be lost or fall out of sync;
  * a request manifest is persisted anyway, and --retrieve cross-checks every returned
    custom_id against it;
  * --verify re-judges completions that ALREADY have synchronous labels and asserts the
    batch labels match. That is a real regression test against an independent source,
    not a self-consistency check.

Usage (each step is separate so a closed terminal loses nothing -- batch IDs are on disk):
    python3 scripts/run_phase05_judging_batch.py --verify        # 40 rows vs sync labels
    python3 scripts/run_phase05_judging_batch.py --submit        # submit all unjudged
    python3 scripts/run_phase05_judging_batch.py --status        # poll
    python3 scripts/run_phase05_judging_batch.py --retrieve      # write judgments.jsonl

Runs server-side, so unlike the sync path it does not care whether your laptop stays
awake -- which matters, given a closed lid cost this project 1,527 generation rows.
"""

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.judge_client import (  # noqa: E402
    JUDGE_RUBRIC_VERSION, JUDGE_SYSTEM_PROMPT, JUDGE_USER_TEMPLATE,
    parse_judge_response)
from src.utils.env import load_env_file  # noqa: E402

# Kept identical to run_phase05_judging.py. If these drift, the two routes stop being
# interchangeable and the batch run is no longer a pure cost optimisation.
JUDGE_MODEL = "claude-haiku-4-5"
JUDGE_TEMPERATURE = 0.0
JUDGE_MAX_TOKENS = 1000

DATASETS = {
    "phase05": "phase05_manifest.jsonl",
    "phase05b": "phase05b_manifest.jsonl",
}
MODEL_CODES = {"llama-3.3-70b-turbo": "A", "gpt-oss-120b": "B"}
CODE_TO_MODEL = {v: k for k, v in MODEL_CODES.items()}

# Anthropic batch limits: 100,000 requests and 256 MB per batch. Each request here is
# roughly 8 KB (the 5 KB rubric plus question, answer and ground truth), so 32,680
# requests is ~250 MB -- right at the ceiling. Split well under both limits rather than
# discovering the boundary in production.
MAX_REQUESTS_PER_BATCH = 8000
POLL_SECONDS = 60


def read_jsonl(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def append_rows(path, rows):
    with open(path, "a") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def custom_id_for(prompt_id, model, sample_idx):
    """Self-describing key. Alphanumerics, hyphens and underscores only; <=64 chars."""
    return f"{prompt_id}-{MODEL_CODES[model]}-{sample_idx:02d}"


def parse_custom_id(cid):
    prompt_id, code, idx = cid.rsplit("-", 2)
    return prompt_id, CODE_TO_MODEL[code], int(idx)


class Paths:
    def __init__(self, dataset):
        self.dataset = dataset
        self.manifest = BASE_DIR / "data" / "prompts" / DATASETS[dataset]
        self.results = BASE_DIR / "results" / dataset
        self.completions = self.results / "completions.jsonl"
        self.judgments = self.results / "judgments.jsonl"
        self.state = self.results / "batch_state.json"


def load_work(P, limit=None, only_already_judged=False):
    """Completions needing a label, with their ground truth. Resumable and deduplicated."""
    manifest = read_jsonl(P.manifest)
    if not manifest:
        sys.exit(f"no manifest at {P.manifest}")
    ground_truths = {r["uid"]: r["ground_truth"] for r in manifest}
    prompt_ids = {r["uid"]: r["id"] for r in manifest}

    # Dedupe on (uid, model, sample_idx), preferring the successful row. The completions
    # file is append-only, so after --retry-failed a key can appear as a failure row AND
    # a later success row; judging the failure row would send an empty answer.
    best = {}
    for r in read_jsonl(P.completions):
        key = (r["uid"], r["model"], r["sample_idx"])
        if r.get("completion"):
            best[key] = r
        else:
            best.setdefault(key, r)
    if not best:
        sys.exit(f"no completions at {P.completions}")

    judged = {(r["uid"], r["model"], r["sample_idx"])
              for r in read_jsonl(P.judgments) if not r.get("judge_failed")}

    work = []
    for key, r in sorted(best.items()):
        if not r.get("completion"):
            continue                      # §11.6 empty completions: nothing to judge
        already = key in judged
        if only_already_judged and not already:
            continue
        if not only_already_judged and already:
            continue
        if r["model"] not in MODEL_CODES:
            sys.exit(f"unknown model {r['model']!r}; add it to MODEL_CODES")
        work.append((r, ground_truths[r["uid"]], prompt_ids[r["uid"]]))
    if limit:
        # Round-robin over (category, model) so a small batch is not all one prompt.
        buckets = defaultdict(list)
        for item in work:
            buckets[(item[0]["category"], item[0]["model"])].append(item)
        keys = sorted(buckets)
        out, depth = [], 0
        longest = max((len(v) for v in buckets.values()), default=0)
        while len(out) < limit and depth < longest:
            for k in keys:
                if depth < len(buckets[k]) and len(out) < limit:
                    out.append(buckets[k][depth])
            depth += 1
        work = out
    return work


def build_request(comp, ground_truth, prompt_id):
    """One batch request, field-for-field identical to the synchronous call."""
    user_content = JUDGE_USER_TEMPLATE.format(
        question=comp["question"],
        answer=comp["completion"],
        ground_truth=ground_truth,
    )
    return {
        "custom_id": custom_id_for(prompt_id, comp["model"], comp["sample_idx"]),
        "params": {
            "model": JUDGE_MODEL,
            # Plain string, matching JudgeClient's anthropic branch. NOT the
            # cache_control list form -- caching was measured not to fire at this
            # prompt length (scripts/check_prompt_caching.py).
            "system": JUDGE_SYSTEM_PROMPT,
            "messages": [{"role": "user",
                          "content": user_content + "\n\nRespond in JSON."}],
            "temperature": JUDGE_TEMPERATURE,
            "max_tokens": JUDGE_MAX_TOKENS,
        },
    }


def load_state(P):
    if P.state.exists():
        return json.loads(P.state.read_text())
    return {"batches": []}


def save_state(P, state):
    P.state.write_text(json.dumps(state, indent=2, sort_keys=True))


def submit(P, client, limit=None, tag="main"):
    work = load_work(P, limit=limit)
    if not work:
        print("nothing to judge — every completion already has a label.")
        return
    print(f"completions needing a label: {len(work):,}")

    state = load_state(P)
    submitted = 0
    for start in range(0, len(work), MAX_REQUESTS_PER_BATCH):
        chunk = work[start:start + MAX_REQUESTS_PER_BATCH]
        requests = [build_request(c, gt, pid) for c, gt, pid in chunk]
        ids = [r["custom_id"] for r in requests]
        if len(set(ids)) != len(ids):
            dupes = [k for k, n in Counter(ids).items() if n > 1][:5]
            sys.exit(f"duplicate custom_ids, refusing to submit: {dupes}")
        approx_mb = sum(len(json.dumps(r)) for r in requests) / 1e6
        batch = client.messages.batches.create(requests=requests)
        state["batches"].append({
            "id": batch.id,
            "tag": tag,
            "n_requests": len(requests),
            "custom_ids": ids,
            "retrieved": False,
        })
        save_state(P, state)
        submitted += len(requests)
        print(f"  submitted {batch.id}  {len(requests):,} requests  ~{approx_mb:.0f} MB")

    print()
    print(f"submitted {submitted:,} requests across "
          f"{len([b for b in state['batches'] if not b['retrieved']])} pending batch(es).")
    print(f"state -> {P.state.relative_to(BASE_DIR)}   (batch IDs are on disk; a closed")
    print("terminal loses nothing)")
    print("\nNext: --status to poll, then --retrieve when ended.")


def status(P, client):
    state = load_state(P)
    if not state["batches"]:
        print("no batches submitted yet.")
        return
    print(f"{'batch id':<40} {'tag':<8} {'requests':>9} {'status':<12} retrieved")
    all_ended = True
    for b in state["batches"]:
        try:
            live = client.messages.batches.retrieve(b["id"])
            st = live.processing_status
            counts = live.request_counts
            extra = (f"  ok={counts.succeeded} err={counts.errored} "
                     f"exp={counts.expired} cancel={counts.canceled}")
        except Exception as e:  # noqa: BLE001
            st, extra = f"ERROR", f"  {e}"
        if st != "ended":
            all_ended = False
        print(f"{b['id']:<40} {b['tag']:<8} {b['n_requests']:>9,} {st:<12} "
              f"{b['retrieved']}{extra}")
    print()
    if all_ended:
        print("all batches ended — run --retrieve")
    else:
        print("still processing. Anthropic's ceiling is 24h; usually much faster.")


def retrieve(P, client, verify=False):
    state = load_state(P)
    pending = [b for b in state["batches"] if not b["retrieved"]]
    if not pending:
        print("nothing pending to retrieve.")
        return

    # For --verify we compare against labels that already exist rather than writing.
    existing = {}
    if verify:
        for r in read_jsonl(P.judgments):
            if not r.get("judge_failed"):
                existing[(r["uid"], r["model"], r["sample_idx"])] = r

    manifest = read_jsonl(P.manifest)
    uid_of_prompt = {r["id"]: r["uid"] for r in manifest}
    cat_of_uid = {r["uid"]: r["category"] for r in manifest}

    for b in pending:
        live = client.messages.batches.retrieve(b["id"])
        if live.processing_status != "ended":
            print(f"{b['id']}: still {live.processing_status}, skipping")
            continue

        expected = set(b["custom_ids"])
        seen = set()
        rows, n_ok, n_fail = [], 0, 0
        mismatches = []

        for entry in client.messages.batches.results(b["id"]):
            cid = entry.custom_id
            if cid not in expected:
                sys.exit(f"REFUSING TO WRITE: batch {b['id']} returned custom_id "
                         f"{cid!r} that was never submitted. The id mapping is wrong.")
            seen.add(cid)
            prompt_id, model, sample_idx = parse_custom_id(cid)
            uid = uid_of_prompt.get(prompt_id)
            if uid is None:
                sys.exit(f"REFUSING TO WRITE: custom_id {cid!r} has no prompt in the "
                         "manifest.")
            key_fields = {
                "uid": uid,
                "prompt_id": prompt_id,
                "category": cat_of_uid[uid],
                "model": model,
                "sample_idx": sample_idx,
            }

            # §5.1: anything that is not a clean success gets NO label.
            if entry.result.type != "succeeded":
                n_fail += 1
                rows.append({**key_fields, "judge_failed": True,
                             "error": f"batch result type: {entry.result.type}"})
                continue
            try:
                text = entry.result.message.content[0].text
                parsed = parse_judge_response(text)
            except Exception as e:  # noqa: BLE001
                n_fail += 1
                rows.append({**key_fields, "judge_failed": True,
                             "error": f"unparseable: {e}"})
                continue

            n_ok += 1
            row = {
                **key_fields,
                "label": parsed["label"],
                "confidence": parsed["confidence"],
                "justification": parsed["justification"],
                "judge_model": JUDGE_MODEL,
                "rubric_version": parsed["rubric_version"],
                "mixed_rejection_then_fabrication":
                    parsed["mixed_rejection_then_fabrication"],
                "via": "batch",
            }
            rows.append(row)

            if verify:
                prev = existing.get((uid, model, sample_idx))
                if prev is not None and prev["label"] != row["label"]:
                    mismatches.append((cid, prev["label"], row["label"],
                                       prev.get("confidence")))

        missing = expected - seen
        print(f"{b['id']}: {n_ok:,} labelled, {n_fail:,} failed, "
              f"{len(missing):,} never returned")

        if verify:
            print()
            print("=" * 74)
            print("VERIFY — batch labels vs labels the SYNCHRONOUS path already produced")
            print("=" * 74)
            compared = sum(1 for r in rows if "label" in r
                           and (r["uid"], r["model"], r["sample_idx"]) in existing)
            print(f"  compared            : {compared}")
            print(f"  label mismatches    : {len(mismatches)}")
            for cid, a, bl, conf in mismatches[:8]:
                print(f"      {cid}: sync={a} batch={bl}  sync_conf={conf}")

            # DIAGNOSTIC THAT SEPARATES THE TWO HYPOTHESES. A custom_id mapping bug
            # attaches labels to the wrong completions, so its mismatches are drawn at
            # random from the population and their confidences look like the population's.
            # Judge non-determinism at T=0 only flips items the judge was unsure about,
            # so its mismatches concentrate at the bottom of the confidence distribution.
            # Reporting the two distributions makes the distinction visible instead of
            # leaving it to be argued.
            if mismatches:
                mc = [c for *_, c in mismatches if c is not None]
                allc = [r.get("confidence") for r in existing.values()
                        if r.get("confidence") is not None]
                if mc and allc:
                    allc_sorted = sorted(allc)
                    def pct(x):
                        return 100 * sum(1 for v in allc_sorted if v < x) / len(allc_sorted)
                    print()
                    print(f"  mean sync confidence, MISMATCHED items : "
                          f"{sum(mc)/len(mc):.3f}")
                    print(f"  mean sync confidence, all judged items : "
                          f"{sum(allc)/len(allc):.3f}")
                    print(f"  confidence percentiles of the mismatches: "
                          f"{[f'{pct(c):.0f}th' for c in mc]}")
                    print()
                    if sum(mc)/len(mc) < sum(allc)/len(allc) - 0.05:
                        print("  -> mismatches concentrate on LOW-confidence items. That is")
                        print("     the signature of judge non-determinism at T=0, not of a")
                        print("     mapping bug (which would draw mismatches at random and")
                        print("     look like the population). CONFIRM with:")
                        print("       python3 scripts/check_judge_determinism.py")
                        print("     which re-judges via the SYNC path only and measures")
                        print("     whether it agrees with itself. If sync-vs-sync")
                        print("     instability is comparable, the batch route is fine.")
                    else:
                        print("  -> mismatches do NOT concentrate on low-confidence items.")
                        print("     That is consistent with a MAPPING BUG. Do not submit.")
            if compared == 0:
                print("  NOTHING COMPARED — run --verify only after some rows have been")
                print("  judged synchronously, otherwise this proves nothing.")
            elif not mismatches:
                print("  -> the custom_id round-trip is exact and the two routes agree.")
                print("     Safe to --submit the full run.")
            else:
                print("  -> MISMATCHES. Read the confidence diagnostic above before acting:")
                print("     temperature 0.0 is greedy decoding but NOT a determinism")
                print("     guarantee -- floating-point non-associativity means identical")
                print("     requests can yield different tokens. So a few mismatches on")
                print("     LOW-confidence items are expected and harmless; mismatches on")
                print("     confident items are not.")
            print("=" * 74)
            print("\n--verify does not write to judgments.jsonl.")
            b["retrieved"] = True
            save_state(P, state)
            continue

        if missing:
            print(f"  WARNING: {len(missing)} submitted requests had no result at all. "
                  "They keep no label and stay unjudged; re-run --submit to pick them up.")
        append_rows(P.judgments, rows)
        b["retrieved"] = True
        save_state(P, state)
        print(f"  appended -> {P.judgments.relative_to(BASE_DIR)}")


def main():
    ap = argparse.ArgumentParser(
        description="Phase 0.5b judging via the Anthropic Batch API (50% cheaper)")
    ap.add_argument("--dataset", choices=sorted(DATASETS), default="phase05b")
    ap.add_argument("--submit", action="store_true", help="submit all unjudged completions")
    ap.add_argument("--status", action="store_true", help="poll submitted batches")
    ap.add_argument("--retrieve", action="store_true", help="write results to judgments.jsonl")
    ap.add_argument("--verify", action="store_true",
                    help="submit a small batch of ALREADY-judged completions and assert "
                         "the batch labels match the synchronous ones. Run this first.")
    ap.add_argument("--verify-n", type=int, default=40)
    ap.add_argument("--limit", type=int, default=None,
                    help="submit only the first N (round-robin over category x model)")
    ap.add_argument("--wait", action="store_true",
                    help="with --verify: poll until the batch ends, then check")
    args = ap.parse_args()

    load_env_file(required=["ANTHROPIC_API_KEY"])
    from anthropic import Anthropic
    client = Anthropic(timeout=120)
    P = Paths(args.dataset)
    P.results.mkdir(parents=True, exist_ok=True)

    print(f"dataset: {args.dataset}   judge: {JUDGE_MODEL} rubric {JUDGE_RUBRIC_VERSION}")
    print()

    if args.verify:
        work = load_work(P, limit=args.verify_n, only_already_judged=True)
        if not work:
            sys.exit("no already-judged completions to verify against. Judge a few "
                     "synchronously first:\n  python3 scripts/run_phase05_judging.py "
                     f"--dataset {args.dataset} --limit 40")
        print(f"verifying on {len(work)} completions that ALREADY have sync labels")
        requests = [build_request(c, gt, pid) for c, gt, pid in work]
        batch = client.messages.batches.create(requests=requests)
        state = load_state(P)
        state["batches"].append({"id": batch.id, "tag": "verify",
                                 "n_requests": len(requests),
                                 "custom_ids": [r["custom_id"] for r in requests],
                                 "retrieved": False})
        save_state(P, state)
        print(f"submitted verify batch {batch.id}")
        if args.wait:
            while True:
                live = client.messages.batches.retrieve(batch.id)
                print(f"  {live.processing_status}  ok={live.request_counts.succeeded} "
                      f"err={live.request_counts.errored}", flush=True)
                if live.processing_status == "ended":
                    break
                time.sleep(POLL_SECONDS)
            retrieve(P, client, verify=True)
        else:
            print("Poll with --status, then: --retrieve --verify")
    elif args.submit:
        submit(P, client, limit=args.limit)
    elif args.status:
        status(P, client)
    elif args.retrieve:
        retrieve(P, client, verify=False)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
