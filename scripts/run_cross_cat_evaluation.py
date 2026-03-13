"""Phase 10C/D: Evaluate cross-category ablation fine-tuned models.

Automated pipeline: deploy endpoint → generate 449 answers → stop endpoint → judge → next.
Handles all 10 conditions sequentially (Mixtral first, then Llama — cheaper endpoints first).

Both Mixtral and Llama require dedicated endpoints for fine-tuned LoRA inference.
Serverless LoRA is NOT supported for these base models on Together AI.

Hardware (from Phase 9 / Step 10):
  - Mixtral: 2x_nvidia_h100_80gb_sxm ($0.13/min)
  - Llama:   8x_nvidia_h100_80gb_sxm ($0.53/min)

Usage:
    export TOGETHER_API_KEY=...
    export OPENAI_API_KEY=...
    export ANTHROPIC_API_KEY=...

    # Run everything (generate + judge, all conditions):
    python3 scripts/run_cross_cat_evaluation.py

    # Generation only (deploy endpoints, generate answers, stop endpoints):
    python3 scripts/run_cross_cat_evaluation.py --phase generate

    # Judging only (no endpoints needed):
    python3 scripts/run_cross_cat_evaluation.py --phase judge

    # Single condition:
    python3 scripts/run_cross_cat_evaluation.py --condition entity_dep_mixtral

    # Resume (skip conditions with complete answers/judgments):
    python3 scripts/run_cross_cat_evaluation.py --skip-existing

    # Start from a specific condition:
    python3 scripts/run_cross_cat_evaluation.py --start-from entity_dep_llama

Output:
    results/v5_finetuned/cross_cat_ablation/{condition_label}/answers.jsonl
    results/v5_finetuned/cross_cat_ablation/{condition_label}/judged_answers.jsonl
    results/v5_finetuned/cross_cat_ablation/evaluation_summary.json
"""

import sys
import json
import time
import argparse
from pathlib import Path

from tqdm import tqdm
from together import Together

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.multi_model_client import MultiModelClient
from src.models.consensus_judge import ConsensusJudge
from src.utils.io import read_jsonl, write_jsonl

# ── Configuration ──────────────────────────────────────────────────────────

V3_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "prompts.jsonl"
JOBS_PATH = PROJECT_ROOT / "data" / "training" / "ablation_cross_cat" / "cross_cat_ft_jobs.json"
OUTPUT_DIR = PROJECT_ROOT / "results" / "v5_finetuned" / "cross_cat_ablation"

JUDGES_CONFIG = [
    {"provider": "openai", "model": "gpt-5.1"},
    {"provider": "anthropic", "model": "claude-opus-4-5-20251101"},
    {"provider": "together", "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"},
]

# Hardware per base model (same as Phase 9 / Step 10)
HARDWARE = {
    "mixtral-8x7b": "2x_nvidia_h100_80gb_sxm",
    "llama-4-maverick-17b": "8x_nvidia_h100_80gb_sxm",
}

MAX_TOKENS = 4000
TEMPERATURE = 0.7
SAVE_EVERY_GEN = 25
SAVE_EVERY_JUDGE = 10

ENDPOINT_STARTUP_TIMEOUT = 1800  # 30 min max wait
ENDPOINT_POLL_INTERVAL = 15     # check every 15s

# Run order: Mixtral first (cheaper: $0.13/min vs $0.53/min for Llama)
RUN_ORDER = [
    "entity_dep_mixtral",
    "R_entity_dep_mixtral",
    "entity_indep_mixtral",
    "leave_out_nonex_mixtral",
    "leave_out_fact_mixtral",
    "entity_dep_llama",
    "R_entity_dep_llama",
    "entity_indep_llama",
    "leave_out_nonex_llama",
    "leave_out_fact_llama",
]


# ── Load models ───────────────────────────────────────────────────────────

def load_models():
    """Load completed fine-tuned model info from jobs file.

    Returns dict: label → model_info
    """
    with open(JOBS_PATH) as f:
        jobs = json.load(f)

    models = {}
    for job in jobs:
        if job["status"] != "completed":
            continue

        output_name = job.get("output_name", "")
        if not output_name:
            continue

        # Build label: {condition}_{model_short}
        model_short = "mixtral" if "mixtral" in job["model"] else "llama"
        label = f"{job['condition']}_{model_short}"

        models[label] = {
            "label": label,
            "condition": job["condition"],
            "base_model": job["model"],
            "output_name": output_name,
            "job_id": job["job_id"],
        }

    return models


# ── Endpoint management ──────────────────────────────────────────────────

def deploy_endpoint(client, model_name, label):
    """Deploy a dedicated endpoint and wait for it to start."""
    base_model = "mixtral-8x7b" if "mixtral" in label else "llama-4-maverick-17b"
    hardware = HARDWARE[base_model]

    print(f"\n  Deploying endpoint for {label}...")
    print(f"    Model: {model_name}")
    print(f"    Hardware: {hardware}")

    ep = client.endpoints.create(
        model=model_name,
        display_name=f"xcat-{label}-eval",
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
        elif state in ("FAILED", "ERROR", "STOPPED"):
            print(f"    ERROR: Endpoint failed to start: {state}")
            return endpoint_id, None

        print(f"    State: {state} ({elapsed}s elapsed)...")
        time.sleep(ENDPOINT_POLL_INTERVAL)
        elapsed += ENDPOINT_POLL_INTERVAL

    print(f"    ERROR: Endpoint startup timed out after {ENDPOINT_STARTUP_TIMEOUT}s")
    return endpoint_id, None


def stop_endpoint(client, endpoint_id):
    """Stop and delete a dedicated endpoint."""
    try:
        client.endpoints.delete(endpoint_id)
        print(f"    Endpoint {endpoint_id} deleted.")
    except Exception as e:
        # Fallback: try stopping instead of deleting
        try:
            client.endpoints.update(endpoint_id, state="STOPPED")
            print(f"    Endpoint {endpoint_id} stopped (delete failed: {e})")
        except Exception as e2:
            print(f"    WARNING: Failed to stop endpoint {endpoint_id}: {e2}")
            print(f"    Please stop it manually from the Together dashboard!")


# ── Generation ────────────────────────────────────────────────────────────

def run_generation(model_info, prompts, endpoint_name):
    """Generate responses for one condition on V3 prompts."""
    label = model_info["label"]

    print(f"\n{'=' * 60}")
    print(f"  GENERATION — {label}")
    print(f"  Endpoint: {endpoint_name}")
    print(f"  Prompts: {len(prompts)}")
    print(f"{'=' * 60}")

    client = MultiModelClient(provider="together", model_name=endpoint_name)

    output_path = OUTPUT_DIR / label / "answers.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resume
    existing_ids = set()
    if output_path.exists():
        existing_results = read_jsonl(output_path)
        existing_ids = {r["id"] for r in existing_results}
        remaining = len(prompts) - len(existing_ids)
        print(f"  Resuming: {len(existing_ids)} done, {remaining} remaining")
        if remaining == 0:
            print(f"  All done, skipping generation")
            return len(existing_ids), 0

    results = []
    failed = 0

    for prompt_data in tqdm(prompts, desc=label):
        if prompt_data["id"] in existing_ids:
            continue

        retry_delay = 2
        for attempt in range(3):
            try:
                response = client.generate(
                    prompt=prompt_data["question"],
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    system_prompt=None,
                )

                result = prompt_data.copy()
                result["model"] = model_info["base_model"]
                result["finetuned_model_id"] = model_info["output_name"]
                result["ablation_condition"] = model_info["condition"]
                result["ablation_label"] = label
                result["prefix_key"] = "finetuned"
                result["prefix_name"] = f"Cross-cat ablation {label}"
                result["system_prompt_used"] = ""
                result["model_answer"] = response
                results.append(result)
                break

            except Exception as e:
                error_msg = str(e)
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    print(f"\n  Rate limit, waiting {retry_delay}s...")
                elif "timeout" in error_msg.lower():
                    print(f"\n  Timeout on {prompt_data['id']}, attempt {attempt + 1}/3")
                else:
                    print(f"\n  Error on {prompt_data['id']}: {error_msg}")

                if attempt < 2:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"\n  Failed after 3 attempts: {prompt_data['id']}")
                    failed += 1

        # Periodic save
        if len(results) > 0 and len(results) % SAVE_EVERY_GEN == 0:
            _append_results(output_path, results, existing_ids)
            existing_ids.update(r["id"] for r in results)
            results = []

    # Final save
    if results:
        _append_results(output_path, results, existing_ids)
        existing_ids.update(r["id"] for r in results)

    total = len(existing_ids)
    print(f"\n  Done: {total}/{len(prompts)} completed, {failed} failed")
    return total, failed


def _append_results(output_path, results, existing_ids):
    """Append new results to JSONL file."""
    if existing_ids:
        with open(output_path, "a", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
    else:
        write_jsonl(output_path, results)


# ── Judging ───────────────────────────────────────────────────────────────

def run_judging(label):
    """Judge responses for one condition."""
    answers_path = OUTPUT_DIR / label / "answers.jsonl"
    output_path = OUTPUT_DIR / label / "judged_answers.jsonl"

    if not answers_path.exists():
        print(f"  No answers file for {label}, skipping")
        return 0

    print(f"\n{'=' * 60}")
    print(f"  JUDGING — {label}")
    print(f"{'=' * 60}")

    answers = read_jsonl(answers_path)
    print(f"  Loaded {len(answers)} answers")

    judge = ConsensusJudge(JUDGES_CONFIG)

    # Resume
    results = []
    existing_ids = set()
    if output_path.exists():
        results = read_jsonl(output_path)
        existing_ids = {r["id"] for r in results}
        remaining = len(answers) - len(existing_ids)
        print(f"  Resuming: {len(existing_ids)} judged, {remaining} remaining")
        if remaining == 0:
            print(f"  All done, skipping judging")
            return len(results)

    for answer_data in tqdm(answers, desc=f"Judging {label}"):
        if answer_data["id"] in existing_ids:
            continue

        retry_delay = 2
        for attempt in range(3):
            try:
                judgment = judge.judge(
                    question=answer_data["question"],
                    answer=answer_data["model_answer"],
                    ground_truth=answer_data["ground_truth"],
                    meta_info=answer_data.get("metadata", {}),
                )

                result = {
                    **answer_data,
                    "judge_label": judgment["label"],
                    "judge_confidence": judgment["confidence"],
                    "judge_justification": judgment["justification"],
                    "judge_model": "consensus_panel",
                    "individual_judgments": judgment["individual_judgments"],
                    "agreement_rate": judgment["agreement_rate"],
                    "individual_confidence_avg": judgment["individual_confidence_avg"],
                }
                results.append(result)
                break

            except Exception as e:
                if attempt < 2:
                    print(f"\n  Error judging {answer_data.get('id', '?')}: {e}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"\n  Failed after 3 attempts: {answer_data.get('id', '?')}: {e}")

        # Periodic save
        if len(results) > 0 and len(results) % SAVE_EVERY_JUDGE == 0:
            write_jsonl(output_path, results)

    write_jsonl(output_path, results)
    print(f"  Saved {len(results)} judgments")
    return len(results)


# ── Summary ───────────────────────────────────────────────────────────────

def generate_summary():
    """Generate evaluation_summary.json."""
    print(f"\n{'=' * 60}")
    print(f"  CROSS-CATEGORY ABLATION EVALUATION SUMMARY")
    print(f"{'=' * 60}")

    summary = {"cross_cat_ablation": {}, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    for condition_dir in sorted(OUTPUT_DIR.iterdir()):
        if not condition_dir.is_dir() or condition_dir.name.startswith("."):
            continue

        judged_path = condition_dir / "judged_answers.jsonl"
        if not judged_path.exists():
            continue

        results = read_jsonl(judged_path)
        total = len(results)
        if total == 0:
            continue

        labels = [r["judge_label"] for r in results]
        correct = labels.count(0)
        partial = labels.count(1)
        hallucination = labels.count(2)
        refusal = labels.count(3)

        condition_summary = {
            "total": total,
            "correct": correct,
            "partial": partial,
            "hallucination": hallucination,
            "refusal": refusal,
            "accuracy": correct / total,
            "hallucination_rate": hallucination / total,
            "refusal_rate": refusal / total,
            "categories": {},
        }

        # Per-category
        categories = sorted(set(r["category"] for r in results))
        for cat in categories:
            cat_results = [r for r in results if r["category"] == cat]
            cat_total = len(cat_results)
            cat_labels = [r["judge_label"] for r in cat_results]
            condition_summary["categories"][cat] = {
                "total": cat_total,
                "correct": cat_labels.count(0),
                "hallucination": cat_labels.count(2),
                "refusal": cat_labels.count(3),
                "accuracy": cat_labels.count(0) / cat_total,
                "hallucination_rate": cat_labels.count(2) / cat_total,
                "refusal_rate": cat_labels.count(3) / cat_total,
            }

        summary["cross_cat_ablation"][condition_dir.name] = condition_summary

        # Print
        print(f"\n  {condition_dir.name}:")
        print(f"    Overall: {correct}/{total} correct ({correct/total*100:.1f}%), "
              f"{hallucination} hallucinations ({hallucination/total*100:.1f}%), "
              f"{refusal} refusals ({refusal/total*100:.1f}%)")
        print(f"    {'Category':<30s} {'N':>5s} {'Acc':>7s} {'Halluc':>7s} {'Refuse':>7s}")
        print(f"    {'-'*30} {'-'*5} {'-'*7} {'-'*7} {'-'*7}")
        for cat in categories:
            cs = condition_summary["categories"][cat]
            print(f"    {cat:<30s} {cs['total']:>5d} "
                  f"{cs['accuracy']*100:>6.1f}% {cs['hallucination_rate']*100:>6.1f}% "
                  f"{cs['refusal_rate']*100:>6.1f}%")

    # Save
    summary_path = OUTPUT_DIR / "evaluation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Saved: {summary_path}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phase 10C/D: Evaluate cross-category ablation models"
    )
    parser.add_argument("--phase", choices=["generate", "judge", "summary", "all"],
                        default="all", help="Which phase to run (default: all)")
    parser.add_argument("--condition", type=str, default=None,
                        help="Run only this condition label (e.g. entity_dep_mixtral)")
    parser.add_argument("--start-from", type=str, default=None,
                        help="Skip conditions before this label")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip conditions with complete answers/judgments")
    args = parser.parse_args()

    # Validate API keys upfront
    import os
    missing_keys = []
    if args.phase in ("generate", "all") and not os.environ.get("TOGETHER_API_KEY"):
        missing_keys.append("TOGETHER_API_KEY")
    if args.phase in ("judge", "all"):
        if not os.environ.get("TOGETHER_API_KEY"):
            missing_keys.append("TOGETHER_API_KEY")
        if not os.environ.get("OPENAI_API_KEY"):
            missing_keys.append("OPENAI_API_KEY")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            missing_keys.append("ANTHROPIC_API_KEY")
    if missing_keys:
        print(f"ERROR: Missing API keys: {', '.join(missing_keys)}")
        sys.exit(1)

    # Load V3 prompts
    if not V3_PROMPTS_PATH.exists():
        print(f"ERROR: V3 prompts not found at {V3_PROMPTS_PATH}")
        sys.exit(1)
    prompts = read_jsonl(V3_PROMPTS_PATH)
    assert len(prompts) == 449, f"Expected 449 V3 prompts, got {len(prompts)}"
    print(f"Loaded {len(prompts)} V3 held-out prompts")

    # Load models
    if not JOBS_PATH.exists():
        print(f"ERROR: Jobs file not found at {JOBS_PATH}")
        print(f"Run --status on run_cross_cat_finetuning.py to populate output_name fields")
        sys.exit(1)
    models = load_models()
    print(f"Found {len(models)} completed cross-category ablation models")

    if len(models) == 0:
        print("ERROR: No completed models with output_name found.")
        print("Run: python3 scripts/run_cross_cat_finetuning.py --status")
        sys.exit(1)

    # Determine run order
    run_list = [label for label in RUN_ORDER if label in models]
    if args.condition:
        if args.condition not in models:
            print(f"ERROR: {args.condition} not found. Available: {list(models.keys())}")
            sys.exit(1)
        run_list = [args.condition]
    elif args.start_from:
        if args.start_from in run_list:
            idx = run_list.index(args.start_from)
            skipped = run_list[:idx]
            run_list = run_list[idx:]
            print(f"Skipping: {skipped}")
        else:
            print(f"ERROR: {args.start_from} not in run list")
            sys.exit(1)

    print(f"\nWill evaluate: {run_list}")
    n_mixtral = sum(1 for l in run_list if "mixtral" in l)
    n_llama = sum(1 for l in run_list if "llama" in l)
    print(f"Estimated endpoint cost: Mixtral {n_mixtral} × ~$1.50 + Llama {n_llama} × ~$8 = ~${n_mixtral * 1.5 + n_llama * 8:.0f}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Generation phase ──
    if args.phase in ("generate", "all"):
        client = Together()
        gen_log = []

        for label in run_list:
            print(f"\n{'=' * 60}")
            print(f"  CONDITION: {label}")
            print(f"{'=' * 60}")

            model_info = models[label]

            # Check if already done
            answers_path = OUTPUT_DIR / label / "answers.jsonl"
            if args.skip_existing and answers_path.exists():
                existing = read_jsonl(answers_path)
                if len(existing) >= len(prompts):
                    print(f"  Skipping: already have {len(existing)} answers")
                    gen_log.append({"label": label, "status": "skipped", "answers": len(existing)})
                    continue

            # Deploy endpoint
            endpoint_id, endpoint_name = deploy_endpoint(
                client, model_info["output_name"], label
            )

            if not endpoint_name:
                print(f"  FAILED to deploy endpoint, skipping {label}")
                if endpoint_id:
                    stop_endpoint(client, endpoint_id)
                gen_log.append({"label": label, "status": "deploy_failed"})
                continue

            # Run generation
            try:
                total, failed = run_generation(model_info, prompts, endpoint_name)
                gen_log.append({
                    "label": label, "status": "completed",
                    "total": total, "failed": failed,
                })
            except Exception as e:
                print(f"\n  ERROR during generation: {e}")
                gen_log.append({"label": label, "status": "error", "error": str(e)})
            finally:
                # Always stop endpoint
                print(f"\n  Stopping endpoint...")
                stop_endpoint(client, endpoint_id)

            # Brief pause between conditions
            if label != run_list[-1]:
                print(f"\n  Pausing 10s before next condition...")
                time.sleep(10)

        # Save generation log
        log_path = OUTPUT_DIR / "generation_log.json"
        with open(log_path, "w") as f:
            json.dump(gen_log, f, indent=2)
        print(f"\n  Generation log saved: {log_path}")

    # ── Judging phase ──
    if args.phase in ("judge", "all"):
        print(f"\n\n{'=' * 60}")
        print(f"  STARTING JUDGING PHASE")
        print(f"{'=' * 60}")
        print(f"  Judge panel: {', '.join(j['model'].split('/')[-1] for j in JUDGES_CONFIG)}")

        for label in run_list:
            # Check if already done
            judged_path = OUTPUT_DIR / label / "judged_answers.jsonl"
            if args.skip_existing and judged_path.exists():
                existing = read_jsonl(judged_path)
                if len(existing) >= 449:
                    print(f"  {label}: skipping ({len(existing)} already judged)")
                    continue

            run_judging(label)

    # ── Summary ──
    if args.phase in ("summary", "all"):
        generate_summary()

    print(f"\n{'=' * 60}")
    print(f"  ALL DONE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
