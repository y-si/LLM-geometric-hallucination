"""Phase 0.5 step 1: generate completions for the Kendall's tau pilot.

Pre-registered design: research_paper/PHASE_0.5_SPEC.md §3 (models), §6.1 (k and
decoding config). Reads data/prompts/phase05_manifest.jsonl (704 unique prompts,
built by scripts/build_phase05_manifest.py) and produces k=20 completions per
(prompt, model) for both funded Together AI models.

    704 prompts x 20 samples x 2 models = 28,160 completions

Decoding config is pre-registered and must not drift: temperature 0.7, top_p 1.0,
max_tokens 256, no system prompt. P-hat is defined relative to this config, so a
change invalidates comparison with any earlier partial run.

sample_idx is recorded and stable because the split-half noise ceiling (§6.2) splits
each prompt's completions by odd/even index. It must be a real per-sample index, not
a re-derived ordering.

Output is append-only JSONL at results/phase05/completions.jsonl. The script is
resumable: re-running skips any (prompt_id, model, sample_idx) triple already
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

# §3 — the two funded models. Keys resolve via experiments/multi_model_config.yaml.
# Maverick is the FP4 build: Together retired the FP8 serverless endpoint (verified
# 2026-08-25, only -FP4 is served). The thesis ran FP8, so absolute hallucination
# rates here are NOT comparable to thesis-era Maverick numbers. Tolerable because the
# pilot's claim is about prompt-difficulty ORDERING, not rates — but logged in
# PHASE_0.5_SPEC.md §9 as a limitation.
MODELS = ["mixtral-8x7b", "llama-4-maverick-17b-fp4"]

# §6.1 / §3 — pre-registered decoding config. Do not change mid-run.
K_SAMPLES = 20
TEMPERATURE = 0.7
TOP_P = 1.0
MAX_TOKENS = 256

MAX_WORKERS = 8
MAX_ATTEMPTS = 3

write_lock = threading.Lock()


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
    prompts.sort(key=lambda r: (r["category"], str(r["id"])))
    if limit:
        prompts = prompts[:limit]
    return prompts


def existing_keys(path):
    """Set of (prompt_id, model, sample_idx) already generated successfully."""
    done = set()
    failed = Counter()
    for row in read_jsonl(path):
        key = (row["prompt_id"], row["model"], row["sample_idx"])
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
            text = client.generate(
                prompt_row["question"],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            if text is None:
                raise ValueError("provider returned None")
            return {
                "prompt_id": prompt_row["id"],
                "category": prompt_row["category"],
                "model": model_key,
                "sample_idx": sample_idx,
                "question": prompt_row["question"],
                "completion": text,
            }
        except Exception as e:  # noqa: BLE001 — record, do not crash the run
            last_error = str(e)
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(2 ** attempt)

    return {
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
                key = (prompt_row["id"], model_key, sample_idx)
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

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(generate_one, clients[model_key], prompt_row,
                            model_key, sample_idx): (prompt_row["id"], model_key, sample_idx)
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

            if completed % 500 == 0 or completed == len(tasks):
                elapsed = time.time() - start
                rate = completed / elapsed if elapsed else 0
                remaining = (len(tasks) - completed) / rate if rate else 0
                print(f"  {completed}/{len(tasks)}  failed={failed}  "
                      f"{rate:.1f}/s  eta={remaining / 60:.0f}m")

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
            k_eff[(r["prompt_id"], r["model"])] += 1
    short = sum(1 for v in k_eff.values() if v < K_SAMPLES)
    print("\ncumulative in file:")
    for model_key in MODELS:
        print(f"  {model_key:24s} {per_model[model_key]}")
    print(f"  (prompt, model) pairs below k={K_SAMPLES}: {short}")


if __name__ == "__main__":
    main()
