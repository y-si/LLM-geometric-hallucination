"""Automated ablation evaluation: deploy endpoint → generate → stop → next.

Handles all 6 ablation models sequentially, deploying and stopping dedicated
endpoints to minimize cost.

Usage:
    export TOGETHER_API_KEY=...
    python3 scripts/run_ablation_generation_all.py

    # Resume from a specific condition (skips earlier ones):
    python3 scripts/run_ablation_generation_all.py --start-from R397_mixtral

    # Skip conditions that already have answers.jsonl:
    python3 scripts/run_ablation_generation_all.py --skip-existing
"""

import sys
import json
import time
import argparse
from pathlib import Path

from together import Together

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_ablation_evaluation import run_generation, OUTPUT_DIR
from src.utils.io import read_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

ABLATION_JOBS_PATH = PROJECT_ROOT / "data" / "training" / "ablation" / "ablation_ft_jobs.json"
V3_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "prompts.jsonl"

# Hardware per base model (from previous Step 10 endpoints)
HARDWARE = {
    "mixtral": "2x_nvidia_h100_80gb_sxm",
    "llama": "8x_nvidia_h100_80gb_sxm",
}

# Run Mixtral first (cheaper: ~$0.13/min vs ~$0.53/min for Llama)
RUN_ORDER = [
    "T5_mixtral",
    "R397_mixtral",
    "T10_mixtral",
    "T5_llama",
    "R402_llama",
    "T10_llama",
]

ENDPOINT_STARTUP_TIMEOUT = 1800  # 30 min max wait for endpoint
ENDPOINT_POLL_INTERVAL = 15     # check every 15s


# ── Helpers ────────────────────────────────────────────────────────────────

def load_ablation_models():
    """Load ablation models keyed by label."""
    with open(ABLATION_JOBS_PATH) as f:
        jobs = json.load(f)
    return {j["label"]: j for j in jobs}


def deploy_endpoint(client, model_name, label):
    """Deploy a dedicated endpoint and wait for it to start."""
    hw_key = "mixtral" if "mixtral" in label.lower() else "llama"
    hardware = HARDWARE[hw_key]

    print(f"\n  Deploying endpoint for {label}...")
    print(f"    Model: {model_name}")
    print(f"    Hardware: {hardware}")

    ep = client.endpoints.create(
        model=model_name,
        display_name=f"abl-{label}-eval",
        hardware=hardware,
        autoscaling={"min_replicas": 1, "max_replicas": 1},
        inactive_timeout=900,  # auto-stop after 15 min idle (safety net)
    )

    endpoint_id = ep.id
    endpoint_name = ep.name
    print(f"    Endpoint ID: {endpoint_id}")
    print(f"    Endpoint name: {endpoint_name}")

    # Wait for STARTED
    elapsed = 0
    while elapsed < ENDPOINT_STARTUP_TIMEOUT:
        ep_status = client.endpoints.retrieve(endpoint_id)
        state = ep_status.state
        if state == "STARTED":
            print(f"    Endpoint ready! (took {elapsed}s)")
            return endpoint_id, endpoint_name
        elif state in ("FAILED", "ERROR"):
            print(f"    ERROR: Endpoint failed to start: {state}")
            return None, None

        print(f"    State: {state} ({elapsed}s elapsed)...")
        time.sleep(ENDPOINT_POLL_INTERVAL)
        elapsed += ENDPOINT_POLL_INTERVAL

    print(f"    ERROR: Endpoint startup timed out after {ENDPOINT_STARTUP_TIMEOUT}s")
    return endpoint_id, None  # return ID so we can stop it


def stop_endpoint(client, endpoint_id):
    """Stop a dedicated endpoint."""
    try:
        client.endpoints.update(endpoint_id, state="STOPPED")
        print(f"    Endpoint {endpoint_id} stopped.")
    except Exception as e:
        print(f"    WARNING: Failed to stop endpoint {endpoint_id}: {e}")
        print(f"    Please stop it manually from the Together dashboard!")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run all ablation generations with auto endpoint management")
    parser.add_argument("--start-from", type=str, default=None,
                        help="Skip conditions before this label (e.g. R397_mixtral)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip conditions that already have complete answers.jsonl")
    args = parser.parse_args()

    # Load prompts
    prompts = read_jsonl(V3_PROMPTS_PATH)
    print(f"Loaded {len(prompts)} V3 held-out prompts")

    # Load models
    models = load_ablation_models()
    print(f"Loaded {len(models)} ablation models")

    client = Together()

    # Determine which conditions to run
    run_list = RUN_ORDER[:]
    if args.start_from:
        if args.start_from in run_list:
            idx = run_list.index(args.start_from)
            skipped = run_list[:idx]
            run_list = run_list[idx:]
            print(f"Skipping: {skipped}")
        else:
            print(f"ERROR: {args.start_from} not in {run_list}")
            sys.exit(1)

    print(f"\nWill run: {run_list}")
    print(f"Estimated cost: Mixtral ~$2-3 each, Llama ~$8-10 each")

    results_log = []

    for label in run_list:
        print(f"\n{'=' * 60}")
        print(f"  CONDITION: {label}")
        print(f"{'=' * 60}")

        job = models.get(label)
        if not job or job["status"] != "completed":
            print(f"  Skipping: job not completed")
            continue

        output_name = job.get("output_name", "")
        if not output_name:
            print(f"  Skipping: no output_name")
            continue

        # Check if already done
        answers_path = OUTPUT_DIR / label / "answers.jsonl"
        if args.skip_existing and answers_path.exists():
            existing = read_jsonl(answers_path)
            if len(existing) >= len(prompts):
                print(f"  Skipping: already have {len(existing)} answers")
                results_log.append({"label": label, "status": "skipped", "answers": len(existing)})
                continue

        # Determine base model
        if "mixtral" in label.lower():
            base_model = "mixtral-8x7b"
        else:
            base_model = "llama-4-maverick-17b"

        # Deploy endpoint
        endpoint_id, endpoint_name = deploy_endpoint(client, output_name, label)

        if not endpoint_name:
            print(f"  FAILED to deploy endpoint, skipping {label}")
            if endpoint_id:
                stop_endpoint(client, endpoint_id)
            results_log.append({"label": label, "status": "deploy_failed"})
            continue

        # Run generation
        model_info = {
            "label": label,
            "base_model": base_model,
            "output_name": output_name,
            "endpoint": endpoint_name,
            "job_id": job["job_id"],
        }

        try:
            total, failed = run_generation(model_info, prompts)
            results_log.append({
                "label": label,
                "status": "completed",
                "total": total,
                "failed": failed,
                "endpoint_id": endpoint_id,
            })
        except Exception as e:
            print(f"\n  ERROR during generation: {e}")
            results_log.append({"label": label, "status": "error", "error": str(e)})
        finally:
            # Always stop endpoint
            print(f"\n  Stopping endpoint...")
            stop_endpoint(client, endpoint_id)

        # Brief pause between conditions
        print(f"\n  Pausing 10s before next condition...")
        time.sleep(10)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  GENERATION SUMMARY")
    print(f"{'=' * 60}")
    for entry in results_log:
        status = entry["status"]
        label = entry["label"]
        if status == "completed":
            print(f"  {label}: {entry['total']} answers, {entry['failed']} failed")
        elif status == "skipped":
            print(f"  {label}: skipped ({entry['answers']} existing)")
        else:
            print(f"  {label}: {status}")

    # Save log
    log_path = OUTPUT_DIR / "generation_log.json"
    with open(log_path, "w") as f:
        json.dump(results_log, f, indent=2)
    print(f"\n  Log saved: {log_path}")

    print(f"\nNext: python3 scripts/run_ablation_evaluation.py --phase judge")


if __name__ == "__main__":
    main()
