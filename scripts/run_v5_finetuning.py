"""Step 10: Launch LoRA fine-tuning jobs on Together AI.

Usage:
  # Convert data first (if not already done):
  python3 scripts/convert_training_to_together.py

  # Launch all jobs (3 configs × 2 models = 6 jobs):
  python3 scripts/run_v5_finetuning.py

  # Launch single model + config:
  python3 scripts/run_v5_finetuning.py --model mixtral-8x7b --config A

  # Check status of running jobs:
  python3 scripts/run_v5_finetuning.py --status

  # Dry run (validate data, estimate cost, don't launch):
  python3 scripts/run_v5_finetuning.py --dry-run

Requires: pip install together
Requires: TOGETHER_API_KEY environment variable
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
TRAINING_DIR = BASE_DIR / "data" / "training"
RESULTS_FILE = TRAINING_DIR / "v5_finetuned_models.json"

# Together AI model IDs for the instruct variants we fine-tune
TOGETHER_MODELS = {
    "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "llama-4-maverick-17b": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
}

# Hyperparameter configurations for ablation
CONFIGS = {
    "A": {
        "description": "Primary — literature-standard LoRA",
        "learning_rate": 2e-4,
        "n_epochs": 3,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "batch_size": 8,
        "warmup_ratio": 0.05,
    },
    "B": {
        "description": "Lower LR — more conservative",
        "learning_rate": 1e-4,
        "n_epochs": 3,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "batch_size": 8,
        "warmup_ratio": 0.05,
    },
    "C": {
        "description": "More epochs — tests convergence",
        "learning_rate": 2e-4,
        "n_epochs": 5,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "batch_size": 8,
        "warmup_ratio": 0.05,
    },
}


def load_results():
    """Load existing results file (tracks all jobs across runs)."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return {"jobs": [], "completed_models": {}}


def save_results(results):
    """Save results file."""
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)


def upload_file(client, model):
    """Upload training data file to Together AI."""
    filepath = TRAINING_DIR / f"v5_together_{model}.jsonl"
    if not filepath.exists():
        print(f"  ERROR: {filepath} not found. Run convert_training_to_together.py first.")
        sys.exit(1)

    # Count records
    with open(filepath) as f:
        n_records = sum(1 for _ in f)
    print(f"  Uploading {filepath.name} ({n_records} records)...")

    response = client.files.upload(file=str(filepath), purpose="fine-tune")
    file_id = response.id
    print(f"  Uploaded: file_id={file_id}")
    return file_id


def launch_job(client, model, config_name, file_id, suffix_tag=""):
    """Launch a single fine-tuning job."""
    config = CONFIGS[config_name]
    together_model = TOGETHER_MODELS[model]
    suffix = f"v5-{model.split('-')[0]}-cfg{config_name}"
    if suffix_tag:
        suffix += f"-{suffix_tag}"

    print(f"\n  Launching: {model} / config {config_name} ({config['description']})")
    print(f"    Model: {together_model}")
    print(f"    lr={config['learning_rate']}, epochs={config['n_epochs']}, "
          f"lora_r={config['lora_r']}, lora_alpha={config['lora_alpha']}")

    # Llama 4 Maverick requires min batch_size=16 per Together AI docs
    batch_size = config["batch_size"]
    if "maverick" in model.lower() and batch_size < 16:
        batch_size = 16
        print(f"    (batch_size raised to 16 — Llama 4 Maverick minimum)")

    response = client.fine_tuning.create(
        training_file=file_id,
        model=together_model,
        n_epochs=config["n_epochs"],
        learning_rate=config["learning_rate"],
        batch_size=batch_size,
        lora_r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        warmup_ratio=config["warmup_ratio"],
        suffix=suffix,
    )

    job_id = response.id
    print(f"    Job ID: {job_id}")
    return job_id


def check_status(client, results):
    """Check status of all tracked jobs."""
    if not results["jobs"]:
        print("No jobs tracked yet.")
        return

    print(f"\n{'='*70}")
    print(f"{'Model':<30} {'Config':>6} {'Status':>12} {'Job ID':>20}")
    print(f"{'-'*70}")

    for job in results["jobs"]:
        try:
            response = client.fine_tuning.retrieve(job["job_id"])
            status = response.status
            job["status"] = status
            if status == "completed" and hasattr(response, "output_name"):
                job["output_name"] = response.output_name
        except Exception as e:
            status = f"error: {e}"

        print(f"{job['model']:<30} {job['config']:>6} {status:>12} {job['job_id']:>20}")

        if job.get("output_name"):
            print(f"  → Fine-tuned model: {job['output_name']}")

    save_results(results)


def poll_until_complete(client, results, poll_interval=60):
    """Poll all pending jobs until completion."""
    pending = [j for j in results["jobs"] if j.get("status") not in ("completed", "failed", "cancelled")]

    if not pending:
        print("No pending jobs to poll.")
        return

    print(f"\nPolling {len(pending)} pending jobs (every {poll_interval}s)...")

    while pending:
        time.sleep(poll_interval)
        still_pending = []

        for job in pending:
            try:
                response = client.fine_tuning.retrieve(job["job_id"])
                status = response.status
                job["status"] = status

                if status == "completed":
                    output_name = getattr(response, "output_name", "unknown")
                    job["output_name"] = output_name
                    job["completed_at"] = datetime.now().isoformat()
                    print(f"  COMPLETED: {job['model']}/{job['config']} → {output_name}")

                    # Track in completed_models for easy lookup
                    key = f"{job['model']}_config{job['config']}"
                    results["completed_models"][key] = output_name
                elif status == "failed":
                    print(f"  FAILED: {job['model']}/{job['config']}")
                elif status == "cancelled":
                    print(f"  CANCELLED: {job['model']}/{job['config']}")
                else:
                    still_pending.append(job)
                    print(f"  {job['model']}/{job['config']}: {status}")
            except Exception as e:
                print(f"  Error checking {job['job_id']}: {e}")
                still_pending.append(job)

        pending = still_pending
        save_results(results)

    print("\nAll jobs finished.")
    save_results(results)


def dry_run(model_filter=None, config_filter=None):
    """Validate data and estimate costs without launching."""
    print("DRY RUN — validating data and estimating costs\n")

    models = [model_filter] if model_filter else list(TOGETHER_MODELS.keys())
    configs = [config_filter] if config_filter else list(CONFIGS.keys())

    total_cost = 0
    for model in models:
        filepath = TRAINING_DIR / f"v5_together_{model}.jsonl"
        if not filepath.exists():
            print(f"  {model}: {filepath.name} NOT FOUND — run convert script first")
            continue

        # Count records and estimate tokens
        n_records = 0
        total_chars = 0
        with open(filepath) as f:
            for line in f:
                r = json.loads(line)
                for msg in r["messages"]:
                    total_chars += len(msg["content"])
                n_records += 1

        est_tokens = total_chars / 4

        # Validate format
        with open(filepath) as f:
            first = json.loads(f.readline())
        assert "messages" in first, "Missing 'messages' key"
        assert first["messages"][0]["role"] == "user", "First message should be 'user'"
        assert first["messages"][1]["role"] == "assistant", "Second message should be 'assistant'"

        # Together AI LoRA SFT pricing is by TOTAL parameters, not active:
        # Mixtral 8x7B = 46.7B total → $1.50/1M tokens (17B-69B tier)
        # Llama 4 Maverick = ~400B total (128 experts) → $3.00/1M tokens (70B+ tier)
        cost_per_1m = 1.50 if "mixtral" in model else 3.00

        print(f"\n{model}:")
        print(f"  File: {filepath.name}")
        print(f"  Records: {n_records}")
        print(f"  Est. tokens: {est_tokens:,.0f}")
        print(f"  Format: VALID")

        for cfg_name in configs:
            cfg = CONFIGS[cfg_name]
            epoch_cost = (est_tokens / 1_000_000) * cost_per_1m
            run_cost = epoch_cost * cfg["n_epochs"]
            total_cost += run_cost
            print(f"  Config {cfg_name} ({cfg['description']}): "
                  f"{cfg['n_epochs']} epochs × {est_tokens:,.0f} tokens = "
                  f"~${run_cost:.2f}")

    print(f"\n{'='*40}")
    print(f"Total estimated cost: ${total_cost:.2f}")
    print(f"Total jobs: {len(models) * len(configs)}")


def main():
    parser = argparse.ArgumentParser(description="Launch V5 LoRA fine-tuning on Together AI")
    parser.add_argument("--model", choices=list(TOGETHER_MODELS.keys()),
                        help="Fine-tune only this model (default: both)")
    parser.add_argument("--config", choices=list(CONFIGS.keys()),
                        help="Use only this config (default: all 3)")
    parser.add_argument("--status", action="store_true",
                        help="Check status of tracked jobs")
    parser.add_argument("--poll", action="store_true",
                        help="Poll until all pending jobs complete")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate data and estimate costs without launching")
    args = parser.parse_args()

    if args.dry_run:
        dry_run(args.model, args.config)
        return

    # Import together SDK
    try:
        from together import Together
    except ImportError:
        print("ERROR: together SDK not installed. Run: pip3 install together")
        sys.exit(1)

    if not os.environ.get("TOGETHER_API_KEY"):
        print("ERROR: TOGETHER_API_KEY environment variable not set")
        sys.exit(1)

    client = Together()
    results = load_results()

    if args.status:
        check_status(client, results)
        return

    if args.poll:
        poll_until_complete(client, results)
        return

    # Determine which models and configs to run
    models = [args.model] if args.model else list(TOGETHER_MODELS.keys())
    configs = [args.config] if args.config else list(CONFIGS.keys())

    print(f"Launching fine-tuning: {len(models)} models × {len(configs)} configs = {len(models)*len(configs)} jobs")

    for model in models:
        print(f"\n{'='*60}")
        print(f"Model: {model}")

        # Upload file (once per model)
        file_id = upload_file(client, model)

        for cfg_name in configs:
            # Check if already launched
            existing = [j for j in results["jobs"]
                        if j["model"] == model and j["config"] == cfg_name
                        and j.get("status") not in ("failed", "cancelled")]
            if existing:
                print(f"\n  Config {cfg_name} already launched (job {existing[0]['job_id']}), skipping")
                continue

            job_id = launch_job(client, model, cfg_name, file_id)

            results["jobs"].append({
                "model": model,
                "config": cfg_name,
                "job_id": job_id,
                "file_id": file_id,
                "together_model": TOGETHER_MODELS[model],
                "hyperparameters": CONFIGS[cfg_name],
                "launched_at": datetime.now().isoformat(),
                "status": "pending",
            })
            save_results(results)

    print(f"\n{'='*60}")
    print(f"All jobs launched. Track progress with:")
    print(f"  python3 scripts/run_v5_finetuning.py --status")
    print(f"  python3 scripts/run_v5_finetuning.py --poll")
    print(f"\nResults saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
