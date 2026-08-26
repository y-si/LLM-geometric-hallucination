"""Probe which Together models are actually SERVERLESS-accessible.

/v1/models lists every model Together knows about, including ones that require a paid
dedicated endpoint. It is therefore NOT an availability check — trusting it is what led
PHASE_0.5_SPEC.md to pin two models that turned out to be unreachable. This makes a
real 1-token chat request against each candidate and reports what actually works.

Cost: negligible (a token or two per model).

Reads TOGETHER_API_KEY from .env. Never prints the key.

Usage:
    cd <repo root>
    python3 scripts/diagnostics/probe_together_serverless.py

Result recorded 2026-08-25: exactly three chat models are serverless on this account —
meta-llama/Llama-3.3-70B-Instruct-Turbo, openai/gpt-oss-120b, openai/gpt-oss-20b.
Every Mistral/Mixtral, every Qwen, Gemma, GLM, DeepSeek, Llama-4-Maverick-FP4 and
Llama-4-Scout build returned 400 model_not_available.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.utils.env import load_env_file  # noqa: E402

MODEL_CANDIDATES = [
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP4",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "mistralai/Mistral-Small-24B-Instruct-2501",
    "google/gemma-3-27b-it",
    "zai-org/GLM-4.6",
    "deepseek-ai/DeepSeek-V3.1",
]

JUDGE_CANDIDATES = [
    "Qwen/Qwen2.5-72B-Instruct-Turbo",
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen3-Next-80B-A3B-Instruct",
]


def probe(key, model_id):
    payload = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(
        "https://api.together.xyz/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 # Cloudflare 403s the default Python-urllib User-Agent.
                 "User-Agent": "curl/8.4.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            json.loads(resp.read())
        return "SERVERLESS OK", ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            msg = json.loads(body).get("error", {}).get("message", body)
        except Exception:  # noqa: BLE001
            msg = body
        if "non-serverless" in msg or "dedicated endpoint" in msg:
            return "dedicated only", ""
        if e.code == 401:
            return "AUTH FAIL", msg[:80]
        if e.code == 429:
            return "RATE LIMITED", "retry — inconclusive"
        return f"HTTP {e.code}", msg[:90]
    except Exception as e:  # noqa: BLE001
        return "ERROR", str(e)[:90]


def main():
    load_env_file(required=["TOGETHER_API_KEY"])
    key = os.environ["TOGETHER_API_KEY"]
    print(f"key_length = {len(key)} (not printing the key)\n")

    usable = {}
    for title, candidates in (("EVALUATED MODEL CANDIDATES", MODEL_CANDIDATES),
                              ("JUDGE CANDIDATES", JUDGE_CANDIDATES)):
        print(f"=== {title} ===")
        ok = []
        for model_id in candidates:
            verdict, detail = probe(key, model_id)
            print(f"  {verdict:15s} {model_id}" + (f"   [{detail}]" if detail else ""),
                  flush=True)
            if verdict == "SERVERLESS OK":
                ok.append(model_id)
        usable[title] = ok
        print()

    print("=" * 62)
    for title, ok in usable.items():
        print(f"{title}: {len(ok)} usable")
        for m in ok:
            print(f"  {m}")


if __name__ == "__main__":
    main()
