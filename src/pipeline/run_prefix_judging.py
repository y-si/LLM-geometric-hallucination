"""Run consensus judging on prefix experiment results.

Walks the v4_prefix_experiment directory tree and judges all answers.jsonl
files using the same 3-judge consensus panel as V3.
"""

import sys
import argparse
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.consensus_judge import ConsensusJudge
from src.utils.io import read_jsonl, write_jsonl

# Same judge panel as V3 for comparability
JUDGES_CONFIG = [
    {'provider': 'openai', 'model': 'gpt-5.1'},
    {'provider': 'anthropic', 'model': 'claude-opus-4-5-20251101'},
    {'provider': 'together', 'model': 'meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8'},
]


def run_prefix_judging(base_dir, model_filter=None, prefix_filter=None):
    """Judge all prefix experiment results."""

    base_path = Path(base_dir)

    # Find all answers.jsonl files
    answer_files = sorted(base_path.glob("*/*/answers.jsonl"))

    if model_filter:
        answer_files = [f for f in answer_files if f.parent.parent.name == model_filter]
    if prefix_filter:
        answer_files = [f for f in answer_files if f.parent.name == prefix_filter]

    if not answer_files:
        print(f"No answer files found in {base_dir}")
        return

    print(f"Found {len(answer_files)} answer files to judge")
    print("\nInitializing Consensus Judge Panel:")
    for j in JUDGES_CONFIG:
        print(f"  - {j['provider']}/{j['model']}")

    judge_system = ConsensusJudge(JUDGES_CONFIG)

    for file in answer_files:
        model_key = file.parent.parent.name
        prefix_key = file.parent.name
        output_file = file.parent / "judged_answers.jsonl"

        print(f"\nJudging: {model_key}/{prefix_key}")

        answers = read_jsonl(file)
        results = []

        # Resume capability
        existing_ids = set()
        if output_file.exists():
            print("  Resuming from existing file...")
            existing = read_jsonl(output_file)
            existing_ids = {r['id'] for r in existing}
            results = existing
            print(f"  {len(existing_ids)} already judged, "
                  f"{len(answers) - len(existing_ids)} remaining")

        for answer_data in tqdm(answers, desc=f"{model_key}/{prefix_key}"):
            if answer_data['id'] in existing_ids:
                continue

            try:
                judgment = judge_system.judge(
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

                # Save periodically
                if len(results) % 10 == 0:
                    write_jsonl(output_file, results)

            except Exception as e:
                print(f"  Error judging {answer_data.get('id', 'unknown')}: {e}")

        write_jsonl(output_file, results)
        print(f"  Saved {len(results)} judgments to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Judge prefix experiment results")
    parser.add_argument("--base-dir", type=str,
                        default="results/v4_prefix_experiment")
    parser.add_argument("--model", type=str, default=None,
                        help="Filter to a specific model key")
    parser.add_argument("--prefix", type=str, default=None,
                        help="Filter to a specific prefix key")
    args = parser.parse_args()

    run_prefix_judging(args.base_dir, args.model, args.prefix)


if __name__ == "__main__":
    main()
