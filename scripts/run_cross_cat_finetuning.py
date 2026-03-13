"""Phase 10B: Launch cross-category generalization ablation fine-tuning jobs.

Uploads training data and launches LoRA fine-tuning on Together AI for
5 conditions × 2 models = 10 jobs.

LoRA config per model (same as main experiment + Phase 9):
  - Mixtral: configC (lr=2e-4, 5 epochs, batch_size=8)
  - Llama:   configA (lr=2e-4, 3 epochs, batch_size=16)
  Together AI overrides: lora_r=64, alpha=128, no dropout (same for all jobs)

Usage:
  # Dry run (validate data, estimate cost):
  python3 scripts/run_cross_cat_finetuning.py --dry-run

  # Launch all 10 jobs:
  python3 scripts/run_cross_cat_finetuning.py

  # Launch single condition:
  python3 scripts/run_cross_cat_finetuning.py --condition entity_dep --model mixtral-8x7b

  # Check status:
  python3 scripts/run_cross_cat_finetuning.py --status

  # Poll until all complete:
  python3 scripts/run_cross_cat_finetuning.py --poll

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
DATA_DIR = BASE_DIR / "data" / "training" / "ablation_cross_cat"
JOBS_FILE = DATA_DIR / "cross_cat_ft_jobs.json"

# Together AI base model IDs
TOGETHER_MODELS = {
    "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "llama-4-maverick-17b": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
}

# Per-model LoRA config (configC for Mixtral, configA for Llama)
# Together AI overrides lora_r/alpha/dropout, but we pass them for documentation
MODEL_CONFIGS = {
    "mixtral-8x7b": {
        "config_name": "C",
        "description": "configC — 5 epochs (same as main FT experiment)",
        "learning_rate": 2e-4,
        "n_epochs": 5,
        "lora_r": 16,      # Together overrides to 64
        "lora_alpha": 32,   # Together overrides to 128
        "lora_dropout": 0.05,  # Together overrides to 0
        "batch_size": 8,
        "warmup_ratio": 0.05,
    },
    "llama-4-maverick-17b": {
        "config_name": "A",
        "description": "configA — 3 epochs (same as main FT experiment)",
        "learning_rate": 2e-4,
        "n_epochs": 3,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "batch_size": 16,   # Llama 4 Maverick minimum
        "warmup_ratio": 0.05,
    },
}

# All 5 conditions (Full is existing, not re-fine-tuned)
CONDITIONS = [
    "entity_dep",
    "R_entity_dep",
    "entity_indep",
    "leave_out_nonex",
    "leave_out_fact",
]


def load_jobs():
    """Load existing jobs file."""
    if JOBS_FILE.exists():
        with open(JOBS_FILE) as f:
            return json.load(f)
    return []


def save_jobs(jobs):
    """Save jobs file."""
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


def get_training_file(condition, model):
    """Get path to Together AI format training file."""
    return DATA_DIR / f"{condition}_together_{model}.jsonl"


def make_suffix(condition, model):
    """Generate unique suffix for Together AI model name."""
    model_short = model.split("-")[0]  # mixtral or llama
    return f"xcat-{condition}-{model_short}"


def upload_file(client, filepath):
    """Upload training data file to Together AI."""
    with open(filepath) as f:
        n_records = sum(1 for _ in f)
    print(f"    Uploading {filepath.name} ({n_records} records)...")

    response = client.files.upload(file=str(filepath), purpose="fine-tune")
    file_id = response.id
    print(f"    Uploaded: file_id={file_id}")
    return file_id


def launch_job(client, condition, model, file_id):
    """Launch a single fine-tuning job."""
    config = MODEL_CONFIGS[model]
    together_model = TOGETHER_MODELS[model]
    suffix = make_suffix(condition, model)

    print(f"\n  Launching: {condition} / {model} (config{config['config_name']})")
    print(f"    Base model: {together_model}")
    print(f"    lr={config['learning_rate']}, epochs={config['n_epochs']}, "
          f"batch_size={config['batch_size']}")

    response = client.fine_tuning.create(
        training_file=file_id,
        model=together_model,
        n_epochs=config["n_epochs"],
        learning_rate=config["learning_rate"],
        batch_size=config["batch_size"],
        lora_r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        warmup_ratio=config["warmup_ratio"],
        suffix=suffix,
    )

    job_id = response.id
    print(f"    Job ID: {job_id}")
    return job_id


def check_status(client, jobs):
    """Check status of all tracked jobs."""
    if not jobs:
        print("No jobs tracked yet.")
        return

    print(f"\n{'='*80}")
    print(f"{'Condition':<20} {'Model':<25} {'Status':>12} {'Job ID':>20}")
    print(f"{'-'*80}")

    for job in jobs:
        try:
            response = client.fine_tuning.retrieve(job["job_id"])
            status = response.status
            job["status"] = status

            if status == "completed" and hasattr(response, "model_output_name"):
                job["output_name"] = response.model_output_name
        except Exception as e:
            status = f"error: {e}"

        print(f"{job['condition']:<20} {job['model']:<25} {status:>12} {job['job_id']:>20}")
        if job.get("output_name"):
            print(f"  -> {job['output_name']}")

    save_jobs(jobs)


def poll_until_complete(client, jobs, poll_interval=60):
    """Poll all pending jobs until completion."""
    pending = [j for j in jobs if j.get("status") not in ("completed", "failed", "cancelled")]

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
                    output_name = getattr(response, "model_output_name", "unknown")
                    job["output_name"] = output_name
                    job["completed_at"] = datetime.now().isoformat()
                    print(f"  COMPLETED: {job['condition']}/{job['model']} -> {output_name}")
                elif status == "failed":
                    print(f"  FAILED: {job['condition']}/{job['model']}")
                elif status == "cancelled":
                    print(f"  CANCELLED: {job['condition']}/{job['model']}")
                else:
                    still_pending.append(job)
                    print(f"  {job['condition']}/{job['model']}: {status}")
            except Exception as e:
                print(f"  Error checking {job['job_id']}: {e}")
                still_pending.append(job)

        pending = still_pending
        save_jobs(jobs)

    print("\nAll jobs finished.")
    save_jobs(jobs)


def dry_run(condition_filter=None, model_filter=None):
    """Validate data and estimate costs without launching."""
    print("DRY RUN — validating data and estimating costs\n")

    conditions = [condition_filter] if condition_filter else CONDITIONS
    models = [model_filter] if model_filter else list(TOGETHER_MODELS.keys())

    total_cost = 0
    total_jobs = 0

    for model in models:
        config = MODEL_CONFIGS[model]
        cost_per_1m = 1.50 if "mixtral" in model else 3.00

        print(f"\n{model} (config{config['config_name']}: {config['n_epochs']} epochs):")

        for condition in conditions:
            filepath = get_training_file(condition, model)
            if not filepath.exists():
                print(f"  {condition}: FILE NOT FOUND ({filepath.name})")
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

            # Validate format
            with open(filepath) as f:
                first = json.loads(f.readline())
            assert "messages" in first, f"Missing 'messages' in {filepath.name}"
            assert len(first["messages"]) == 2, f"Expected 2 messages in {filepath.name}"
            assert first["messages"][0]["role"] == "user"
            assert first["messages"][1]["role"] == "assistant"

            est_tokens = total_chars / 4
            cost = (est_tokens / 1_000_000) * cost_per_1m * config["n_epochs"]
            total_cost += cost
            total_jobs += 1

            suffix = make_suffix(condition, model)
            print(f"  {condition}: {n_records} records, ~{est_tokens:,.0f} tokens, "
                  f"${cost:.2f}, suffix={suffix}")

    print(f"\n{'='*40}")
    print(f"Total jobs: {total_jobs}")
    print(f"Total estimated FT cost: ${total_cost:.2f}")
    print(f"(Does not include Mixtral endpoint cost for evaluation)")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 10B: Launch cross-category ablation fine-tuning"
    )
    parser.add_argument("--condition", choices=CONDITIONS,
                        help="Fine-tune only this condition (default: all 5)")
    parser.add_argument("--model", choices=list(TOGETHER_MODELS.keys()),
                        help="Fine-tune only this model (default: both)")
    parser.add_argument("--status", action="store_true",
                        help="Check status of tracked jobs")
    parser.add_argument("--poll", action="store_true",
                        help="Poll until all pending jobs complete")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate data and estimate costs without launching")
    args = parser.parse_args()

    if args.dry_run:
        dry_run(args.condition, args.model)
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
    jobs = load_jobs()

    if args.status:
        check_status(client, jobs)
        return

    if args.poll:
        poll_until_complete(client, jobs)
        return

    # Determine what to launch
    conditions = [args.condition] if args.condition else CONDITIONS
    models = [args.model] if args.model else list(TOGETHER_MODELS.keys())

    n_jobs = len(conditions) * len(models)
    print(f"Launching fine-tuning: {len(conditions)} conditions × {len(models)} models = {n_jobs} jobs")

    for model in models:
        config = MODEL_CONFIGS[model]
        print(f"\n{'='*60}")
        print(f"Model: {model} (config{config['config_name']})")

        for condition in conditions:
            # Duplicate launch protection
            existing = [j for j in jobs
                        if j["condition"] == condition and j["model"] == model
                        and j.get("status") not in ("failed", "cancelled")]
            if existing:
                print(f"\n  {condition} already launched (job {existing[0]['job_id']}), skipping")
                continue

            filepath = get_training_file(condition, model)
            if not filepath.exists():
                print(f"\n  ERROR: {filepath} not found. Run build_cross_category_ablation.py first.")
                continue

            # Upload file
            print(f"\n  Condition: {condition}")
            file_id = upload_file(client, filepath)

            # Launch job
            job_id = launch_job(client, condition, model, file_id)

            jobs.append({
                "condition": condition,
                "model": model,
                "config": config["config_name"],
                "job_id": job_id,
                "file_id": file_id,
                "together_model": TOGETHER_MODELS[model],
                "suffix": make_suffix(condition, model),
                "n_records": sum(1 for _ in open(filepath)),
                "launched_at": datetime.now().isoformat(),
                "status": "pending",
            })
            save_jobs(jobs)

    print(f"\n{'='*60}")
    print(f"All jobs launched. Track progress with:")
    print(f"  python3 scripts/run_cross_cat_finetuning.py --status")
    print(f"  python3 scripts/run_cross_cat_finetuning.py --poll")
    print(f"\nJobs tracked in: {JOBS_FILE}")


if __name__ == "__main__":
    main()
