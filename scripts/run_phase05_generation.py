"""Phase 0.5 step 1: generate completions for the Kendall's tau pilot.

Pre-registered design: research_paper/PHASE_0.5_SPEC.md §3 (models), §6.1 (k and
decoding config). Reads data/prompts/phase05_manifest.jsonl (704 unique prompts,
built by scripts/build_phase05_manifest.py) and produces k=20 completions per
(prompt, model) for both funded Together AI models.

    704 prompts x 20 samples x 2 models = 28,160 completions

Decoding config is pre-registered and must not drift: temperature 0.7, top_p 1.0,
max_tokens 2048, no system prompt. P-hat is defined relative to this config, so a
change invalidates comparison with any earlier partial run.

sample_idx is recorded and stable because the split-half noise ceiling (§6.2) splits
each prompt's completions by odd/even index. It must be a real per-sample index, not
a re-derived ordering.

Output is append-only JSONL at results/phase05/completions.jsonl. The script is
resumable: re-running skips any (uid, model, sample_idx) triple already
present, so a rate-limit crash costs only the in-flight batch. Generation failures
are recorded as rows with generation_failed=true rather than dropped silently, so a
later pass can retry exactly the gaps.

Usage:
    python3 scripts/run_phase05_generation.py --preflight   # verify models respond
    python3 scripts/run_phase05_generation.py               # full run (resumable)
    python3 scripts/run_phase05_generation.py --limit 10    # smoke test, 10 prompts
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

from src.models.multi_model_client import get_model_client  # noqa: E402
from src.utils.env import load_env_file  # noqa: E402

MANIFEST_PATH = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"
OUTPUT_DIR = BASE_DIR / "results" / "phase05"
OUTPUT_PATH = OUTPUT_DIR / "completions.jsonl"
CONFIG_PATH = OUTPUT_DIR / "decoding_config.json"

# §3 — the two evaluated models. Keys resolve via experiments/multi_model_config.yaml.
# Availability verified 2026-08-25 by probing with real 1-token requests: Together's
# serverless tier on this account serves exactly three chat models (these two plus
# openai/gpt-oss-20b). Both thesis models — Mixtral-8x7B and every Llama-4-Maverick
# build — are dedicated-endpoint-only, so NEITHER of these is a thesis model and no
# thesis-era rate is comparable to this pilot's. Upside: Meta-dense vs OpenAI-MoE is
# far more separated than the original Mixtral/Maverick pair, which weakens the
# shared-pretraining critique. See PHASE_0.5_SPEC.md §3.1 and §9.
MODELS = ["llama-3.3-70b-turbo", "gpt-oss-120b"]

# §6.1 / §3 — pre-registered decoding config. Do not change mid-run; the fingerprint
# check below refuses to resume across a change.
#
# max_tokens=2048 is set from measurement, not intuition. Probing both models at a
# 1536-token cap (2026-08-25) found natural completion lengths differ ~7x at the
# median: Llama p50=96 / max=595, gpt-oss p50=699 / p90=1536 with 3/15 still hitting
# the cap. At the original 256 that truncated gpt-oss mid-sentence on most prompts,
# and the judge scores a truncated answer as the model's answer — an error that lands
# asymmetrically across the two models and therefore corrupts the ranking comparison.
# A single shared value keeps the decoding config identical across models, which is
# what makes the two P-hat estimates comparable.
K_SAMPLES = 20
TEMPERATURE = 0.7
TOP_P = 1.0
MAX_TOKENS = 2048

MAX_WORKERS = 8
MAX_ATTEMPTS = 3

write_lock = threading.Lock()


def decoding_config():
    return {"k_samples": K_SAMPLES, "temperature": TEMPERATURE, "top_p": TOP_P,
            "max_tokens": MAX_TOKENS, "models": sorted(MODELS)}


def check_decoding_config():
    """Refuse to resume across a decoding-config change (§3).

    P-hat is defined relative to one decoding config. Appending completions generated
    under different settings to the same file would silently mix two populations, and
    the resume logic would skip the old rows rather than flag them.
    """
    current = decoding_config()
    if not CONFIG_PATH.exists():
        if OUTPUT_PATH.exists() and OUTPUT_PATH.stat().st_size > 0:
            sys.exit(
                f"REFUSING TO RUN: {OUTPUT_PATH.name} has data but no "
                f"{CONFIG_PATH.name} recording the decoding config it was generated "
                "under. It predates this check and may not match the current config. "
                f"Delete both files and regenerate:\n  rm {OUTPUT_PATH} "
                f"{OUTPUT_DIR / 'judgments.jsonl'}"
            )
        with open(CONFIG_PATH, "w") as f:
            json.dump(current, f, indent=1, sort_keys=True)
        return

    with open(CONFIG_PATH) as f:
        stored = json.load(f)
    if stored != current:
        diffs = [f"{k}: file={stored.get(k)!r} now={current[k]!r}"
                 for k in current if stored.get(k) != current[k]]
        sys.exit(
            "REFUSING TO RUN: the decoding config changed since these completions "
            "were generated.\n  " + "\n  ".join(diffs)
            + "\n\nP-hat is defined relative to one decoding config (§3). Either "
            "restore the old settings, or delete the results and regenerate:\n"
            f"  rm {OUTPUT_PATH} {CONFIG_PATH} {OUTPUT_DIR / 'judgments.jsonl'}"
        )


def read_jsonl(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_manifest(limit=None):
    prompts = read_jsonl(MANIFEST_PATH)
    if not prompts:
        sys.exit(f"No manifest at {MANIFEST_PATH}. "
                 "Run scripts/build_phase05_manifest.py first.")
    prompts.sort(key=lambda r: (r["category"], r["uid"]))
    if limit:
        prompts = stratified_sample(prompts, limit)
    return prompts


def stratified_sample(prompts, limit):
    """Round-robin across categories, deterministically.

    A plain prompts[:limit] takes the first N of a (category, id)-sorted manifest,
    which means a 10-prompt smoke test draws entirely from `ambiguous` (the first
    category, 120 entries). That produced a smoke test that validated one of seven
    categories and made a model-specific truncation problem look symmetric.
    """
    by_cat = defaultdict(list)
    for r in prompts:
        by_cat[r["category"]].append(r)
    cats = sorted(by_cat)
    picked, depth = [], 0
    while len(picked) < limit and depth < max(len(v) for v in by_cat.values()):
        for cat in cats:
            if depth < len(by_cat[cat]) and len(picked) < limit:
                picked.append(by_cat[cat][depth])
        depth += 1
    picked.sort(key=lambda r: (r["category"], r["uid"]))
    return picked


def existing_keys(path):
    """Set of (uid, model, sample_idx) already generated successfully."""
    done = set()
    failed = Counter()
    for row in read_jsonl(path):
        key = (row["uid"], row["model"], row["sample_idx"])
        if row.get("generation_failed"):
            failed[key] += 1
        else:
            done.add(key)
    return done, failed


def append_rows(path, rows):
    with write_lock:
        with open(path, "a") as f:
            for row in rows:
                f.write(json.dumps(row, sort_keys=True) + "\n")


def generate_one(client, prompt_row, model_key, sample_idx):
    """One completion. Returns a result row; never raises."""
    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            result = client.generate_with_meta(
                prompt_row["question"],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            if not result.get("text"):
                raise ValueError(f"empty completion "
                                 f"(finish_reason={result.get('finish_reason')})")
            return {
                "uid": prompt_row["uid"],
        "prompt_id": prompt_row["id"],
                "category": prompt_row["category"],
                "model": model_key,
                "sample_idx": sample_idx,
                "question": prompt_row["question"],
                "completion": result["text"],
                # Recorded so truncation is MEASURED, not inferred from punctuation.
                # "length" means the completion hit max_tokens and is cut mid-answer;
                # the judge would score a truncated answer as the model's answer.
                "finish_reason": result.get("finish_reason"),
                "output_tokens": result.get("output_tokens"),
            }
        except Exception as e:  # noqa: BLE001 — record, do not crash the run
            last_error = str(e)
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 ** attempt)

    return {
        "uid": prompt_row["uid"],
        "prompt_id": prompt_row["id"],
        "category": prompt_row["category"],
        "model": model_key,
        "sample_idx": sample_idx,
        "question": prompt_row["question"],
        "completion": None,
        "generation_failed": True,
        "error": last_error,
    }


def preflight(clients):
    """Confirm every model responds before committing to a long run."""
    print("Preflight: one call per model\n")
    ok = True
    for model_key, client in clients.items():
        try:
            text = client.generate("What is the capital of France?",
                                   max_tokens=32, temperature=0.0, top_p=1.0)
            preview = (text or "").strip().replace("\n", " ")[:70]
            print(f"  OK    {model_key:24s} {preview}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {model_key:24s} {e}")
            ok = False
    print()
    return ok


def main():
    parser = argparse.ArgumentParser(
        description="Phase 0.5: generate pilot completions (resumable)")
    parser.add_argument("--preflight", action="store_true",
                        help="Verify each model responds, then exit")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only use the first N manifest prompts (smoke test)")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Also retry triples previously recorded as failed")
    args = parser.parse_args()

    # Both models are Together-hosted, so that is the only credential needed.
    load_env_file(required=["TOGETHER_API_KEY"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    check_decoding_config()

    clients = {key: get_model_client(key, str(BASE_DIR / "experiments" / "multi_model_config.yaml"))
               for key in MODELS}

    if args.preflight:
        sys.exit(0 if preflight(clients) else 1)

    prompts = load_manifest(args.limit)
    done, previously_failed = existing_keys(OUTPUT_PATH)

    tasks = []
    for prompt_row in prompts:
        for model_key in MODELS:
            for sample_idx in range(K_SAMPLES):
                key = (prompt_row["uid"], model_key, sample_idx)
                if key in done:
                    continue
                if key in previously_failed and not args.retry_failed:
                    continue
                tasks.append((prompt_row, model_key, sample_idx))

    total_target = len(prompts) * len(MODELS) * K_SAMPLES
    print(f"manifest prompts : {len(prompts)}")
    print(f"models           : {', '.join(MODELS)}")
    print(f"k                : {K_SAMPLES}  (T={TEMPERATURE}, top_p={TOP_P}, "
          f"max_tokens={MAX_TOKENS})")
    print(f"target completions: {total_target}")
    print(f"already done      : {len(done)}")
    if previously_failed:
        state = "will retry" if args.retry_failed else "skipping (use --retry-failed)"
        print(f"previously failed : {len(previously_failed)}  ({state})")
    print(f"to generate       : {len(tasks)}\n")

    if not tasks:
        print("Nothing to do.")
        return

    completed, failed = 0, 0
    buffer = []
    start = time.time()
    # Report often enough that a short run shows progress and a slow run is
    # distinguishable from a wedged one.
    report_every = max(20, min(500, len(tasks) // 20))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(generate_one, clients[model_key], prompt_row,
                            model_key, sample_idx): (prompt_row["uid"], model_key, sample_idx)
            for prompt_row, model_key, sample_idx in tasks
        }
        for future in as_completed(futures):
            row = future.result()
            buffer.append(row)
            completed += 1
            if row.get("generation_failed"):
                failed += 1

            if len(buffer) >= 50:
                append_rows(OUTPUT_PATH, buffer)
                buffer = []

            if completed % report_every == 0 or completed == len(tasks):
                elapsed = time.time() - start
                rate = completed / elapsed if elapsed else 0
                remaining = (len(tasks) - completed) / rate if rate else 0
                eta = f"{remaining / 3600:.1f}h" if remaining > 5400 else f"{remaining / 60:.0f}m"
                print(f"  {completed}/{len(tasks)}  failed={failed}  "
                      f"{rate:.1f}/s  eta={eta}", flush=True)

    if buffer:
        append_rows(OUTPUT_PATH, buffer)

    print(f"\nwrote -> {OUTPUT_PATH.relative_to(BASE_DIR)}")
    print(f"generated {completed - failed}, failed {failed}")

    if failed:
        rate = failed / completed
        print(f"generation failure rate: {rate:.2%}")
        if rate > 0.02:
            print("WARNING: >2% failure rate. Re-run with --retry-failed before "
                  "judging; a high failure rate means uneven k_eff across prompts "
                  "(PHASE_0.5_SPEC.md §5.1).")

    rows = read_jsonl(OUTPUT_PATH)
    per_model = Counter(r["model"] for r in rows if not r.get("generation_failed"))
    k_eff = defaultdict(int)
    for r in rows:
        if not r.get("generation_failed"):
            k_eff[(r["uid"], r["model"])] += 1
    short = sum(1 for v in k_eff.values() if v < K_SAMPLES)
    print("\ncumulative in file:")
    for model_key in MODELS:
        print(f"  {model_key:24s} {per_model[model_key]}")
    print(f"  (prompt, model) pairs below k={K_SAMPLES}: {short}")

    # Truncation report (§6.5.4). A completion cut off at max_tokens is judged as if
    # it were the model's answer, so an asymmetric truncation rate between models
    # produces asymmetric judge error — which does not average out in a ranking
    # comparison. Measured from finish_reason, not inferred.
    print("\ntruncation (finish_reason == 'length'):")
    rates = {}
    for model_key in MODELS:
        ok = [r for r in rows if r["model"] == model_key and not r.get("generation_failed")]
        if not ok:
            continue
        cut = sum(1 for r in ok if r.get("finish_reason") == "length")
        toks = [r["output_tokens"] for r in ok if r.get("output_tokens") is not None]
        rates[model_key] = cut / len(ok)
        median = sorted(toks)[len(toks) // 2] if toks else None
        print(f"  {model_key:24s} {cut:6d}/{len(ok):<6d} = {cut / len(ok):6.1%}"
              + (f"   median {median} output tokens" if median else ""))
    if len(rates) == 2:
        gap = abs(list(rates.values())[0] - list(rates.values())[1])
        print(f"  asymmetry between models: {gap:.1%}")
        if gap > 0.05:
            print("  NOTE: >5 point truncation gap. This is expected — a model that is"
                  " still generating at max_tokens is confabulating at length, which"
                  " is the behaviour being measured, not noise.\n"
                  "  Do NOT raise MAX_TOKENS to chase it and do NOT residualize P-hat"
                  " on length (that controls a mediator and destroys real signal).\n"
                  "  The check that matters is the label-neutrality test in"
                  " PHASE_0.5_SPEC.md §6.5.4, run after judging.")


if __name__ == "__main__":
    main()
