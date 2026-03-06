"""Run judging with Consensus Judge (multiple models)."""

import sys
import time
import argparse
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.consensus_judge import ConsensusJudge
from src.utils.io import read_jsonl, write_jsonl


def run_consensus_judging(input_dir, output_dir):
    """Run judging using a panel of models."""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Define the panel of judges
    # We use the strongest AVAILABLE models as judges
    # Note: 'claude-opus-4.5' and 'llama-4' are not yet available via API, reverting to best available.
    judges_config = [
        {'provider': 'openai', 'model': 'gpt-5.1'},           # Strongest OpenAI
        {'provider': 'anthropic', 'model': 'claude-opus-4-5-20251101'}, # Strongest Anthropic
        {'provider': 'together', 'model': 'meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8'} # Strongest Open Source
    ]
    
    print("Initializing Consensus Judge Panel:")
    for j in judges_config:
        print(f"  - {j['provider']}/{j['model']}")
        
    judge_system = ConsensusJudge(judges_config)
    
    # Find answer files
    answer_files = list(input_path.glob("answers_*.jsonl"))
    print(f"Found {len(answer_files)} answer files to judge")
    
    for file in answer_files:
        model_name = file.stem.replace("answers_", "")
        print(f"\nJudging answers for {model_name}...")
        
        answers = read_jsonl(file)
        results = []
        
        output_file = output_path / f"judged_{file.name}"
        
        # Resume capability
        existing_ids = set()
        if output_file.exists():
            print("  Resuming from existing file...")
            existing = read_jsonl(output_file)
            existing_ids = {r['id'] for r in existing}
            results = existing
        
        for answer_data in tqdm(answers):
            if answer_data['id'] in existing_ids:
                continue

            retry_delay = 2
            for attempt in range(3):
                try:
                    judgment = judge_system.judge(
                        question=answer_data["question"],
                        answer=answer_data["model_answer"],
                        ground_truth=answer_data["ground_truth"],
                        meta_info=answer_data.get("metadata", {})
                    )

                    result = {
                        **answer_data,
                        "judge_label": judgment["label"],
                        "judge_confidence": judgment["confidence"],
                        "judge_justification": judgment["justification"],
                        "judge_model": "consensus_panel",
                        "individual_judgments": judgment["individual_judgments"],
                        "agreement_rate": judgment["agreement_rate"],
                        "individual_confidence_avg": judgment["individual_confidence_avg"]
                    }
                    results.append(result)
                    break

                except Exception as e:
                    if attempt < 2:
                        print(f"\n  Error judging {answer_data.get('id', 'unknown')}: {e}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        print(f"\n  Failed after 3 attempts: {answer_data.get('id', 'unknown')}: {e}")

            # Save periodically (outside retry loop to avoid duplicates on write failure)
            if len(results) > 0 and len(results) % 10 == 0:
                write_jsonl(output_file, results)
        
        write_jsonl(output_file, results)
        print(f"  Saved {len(results)} judgments to {output_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    args = parser.parse_args()
    
    run_consensus_judging(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
