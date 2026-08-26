"""Probe each model's NATURAL completion length, to set max_tokens from data.

PHASE_0.5_SPEC.md §3.2 sets max_tokens=2048 from this measurement rather than
intuition. Re-run it if the model panel changes — a cap chosen without knowing where
completions naturally stop truncates one model far more than the other, and the judge
scores a truncated answer AS the model's answer, which biases that model's P-hat.

Uses finish_reason from the API, so truncation is measured rather than inferred from
punctuation (inferring it is how an earlier reading got the direction wrong).

Cost: ~30 calls, a few cents.

Usage:
    cd <repo root>
    python3 scripts/diagnostics/probe_completion_lengths.py

Result recorded 2026-08-25 at a 1536-token cap, 15 prompts spread across categories:
  llama-3.3-70b-turbo  p50=96   p90=555   max=595    hit cap 0/15
  gpt-oss-120b         p50=699  p90=1536  max=1536   hit cap 3/15
A ~7x median gap. At max_tokens=2048 the residual truncation is concentrated almost
entirely on runaway-elaboration prompts (see §6.5.4).
"""

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.multi_model_client import get_model_client  # noqa: E402
from src.utils.env import load_env_file  # noqa: E402

CONFIG = str(BASE_DIR / "experiments" / "multi_model_config.yaml")
MANIFEST = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"

MODELS = ["llama-3.3-70b-turbo", "gpt-oss-120b"]
PROBE_CAP = 1536        # generous — we want natural stops, not another wall
SAMPLES = 15
TEMPERATURE = 0.7       # pre-registered decoding config, except max_tokens
TOP_P = 1.0


def stratified(prompts, n):
    by_cat = defaultdict(list)
    for r in prompts:
        by_cat[r["category"]].append(r)
    cats = sorted(by_cat)
    picked, depth = [], 0
    while len(picked) < n and depth < max(len(v) for v in by_cat.values()):
        for cat in cats:
            if depth < len(by_cat[cat]) and len(picked) < n:
                picked.append(by_cat[cat][depth])
        depth += 1
    return picked


def main():
    load_env_file(required=["TOGETHER_API_KEY"])
    prompts = [json.loads(l) for l in open(MANIFEST) if l.strip()]
    prompts.sort(key=lambda r: (r["category"], str(r["id"])))
    probe_set = stratified(prompts, SAMPLES)
    print(f"probing {len(probe_set)} prompts x {len(MODELS)} models "
          f"at max_tokens={PROBE_CAP}\n")

    results = {}
    for key in MODELS:
        client = get_model_client(key, CONFIG)
        print(f"=== {key} ===", flush=True)
        toks, capped = [], 0
        for p in probe_set:
            try:
                r = client.generate_with_meta(p["question"], max_tokens=PROBE_CAP,
                                              temperature=TEMPERATURE, top_p=TOP_P)
                n = r.get("output_tokens")
                fin = r.get("finish_reason")
                if n is not None:
                    toks.append(n)
                capped += (fin == "length")
                print(f"  {str(n):>5} tok  finish={str(fin):12s} {p['category'][:24]}",
                      flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"  ERROR {e}", flush=True)
        if toks:
            s = sorted(toks)
            results[key] = (s, capped)
            print(f"\n  p50={int(statistics.median(s))} "
                  f"p90={s[min(len(s) - 1, 9 * len(s) // 10)]} max={s[-1]}  "
                  f"hit the {PROBE_CAP} cap: {capped}/{len(s)}\n")

    if len(results) == len(MODELS):
        pooled = sorted(t for s, _ in results.values() for t in s)
        p95 = pooled[min(len(pooled) - 1, int(0.95 * len(pooled)))]
        print("=" * 62)
        for key, (s, capped) in results.items():
            print(f"  {key:22s} p50={int(statistics.median(s)):5d}  "
                  f"p90={s[min(len(s) - 1, 9 * len(s) // 10)]:5d}  "
                  f"max={s[-1]:5d}  hit_cap={capped}/{len(s)}")
        print(f"\n  pooled p95 = {p95} -> max_tokens ~ {((p95 // 128) + 1) * 128}")
        print("\n  Use ONE shared value across models: an identical decoding config is"
              "\n  what makes the two P-hat estimates comparable (§3).")


if __name__ == "__main__":
    main()
