"""Convert Step 9 best-per-prompt training data to Together AI fine-tuning format.

Input:  data/training/v5_training_{model}.jsonl  (Step 9 output)
Output: data/training/v5_together_{model}.jsonl  (Together AI messages format)

Together AI format:
  {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

No system message included — the fine-tuned model should produce careful
responses as its default behavior, without needing a system prompt at inference.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TRAINING_DIR = BASE_DIR / "data" / "training"

MODELS = ["mixtral-8x7b", "llama-4-maverick-17b"]


def estimate_tokens(text):
    """Rough token estimate: ~4 chars per token for English."""
    return len(text) / 4


def convert_model(model):
    """Convert one model's training data to Together AI format."""
    input_path = TRAINING_DIR / f"v5_training_{model}.jsonl"
    output_path = TRAINING_DIR / f"v5_together_{model}.jsonl"

    records = []
    with open(input_path) as f:
        for line in f:
            records.append(json.loads(line))

    print(f"\n{'='*60}")
    print(f"Model: {model}")
    print(f"Input: {input_path} ({len(records)} records)")

    # Validate and convert
    converted = []
    skipped = 0
    total_tokens = 0

    for r in records:
        question = r.get("question", "").strip()
        answer = str(r.get("selected_answer", "")).strip()

        if not question:
            print(f"  WARNING: Empty question in {r.get('id', 'unknown')}, skipping")
            skipped += 1
            continue

        if not answer:
            print(f"  WARNING: Empty answer in {r.get('id', 'unknown')}, skipping")
            skipped += 1
            continue

        together_record = {
            "messages": [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ]
        }
        converted.append(together_record)

        total_tokens += estimate_tokens(question) + estimate_tokens(answer)

    # Write output
    with open(output_path, "w") as f:
        for rec in converted:
            f.write(json.dumps(rec) + "\n")

    print(f"Output: {output_path} ({len(converted)} records)")
    if skipped:
        print(f"  Skipped: {skipped} (empty question or answer)")

    # Token stats
    avg_tokens = total_tokens / len(converted) if converted else 0
    print(f"\nToken estimates:")
    print(f"  Total: {total_tokens:,.0f}")
    print(f"  Per example (avg): {avg_tokens:.0f}")
    print(f"  Per epoch: {total_tokens:,.0f}")
    print(f"  3 epochs: {total_tokens * 3:,.0f}")

    # Cost estimates (Together AI LoRA SFT pricing by TOTAL parameters)
    # Mixtral 8x7B = 46.7B total params → $1.50/1M tokens (17B-69B tier)
    # Llama 4 Maverick = ~400B total params (128 experts) → $3.00/1M tokens (70B+ tier)
    if "mixtral" in model:
        cost_per_1m = 1.50
    else:
        cost_per_1m = 3.00
    cost_3ep = (total_tokens * 3 / 1_000_000) * cost_per_1m
    print(f"  Estimated cost (3 epochs, LoRA SFT): ${cost_3ep:.2f}")

    # Answer length distribution
    answer_lens = [len(str(r.get("selected_answer", ""))) for r in records if r.get("selected_answer")]
    if answer_lens:
        answer_lens.sort()
        print(f"\nAnswer length (chars):")
        print(f"  Mean: {sum(answer_lens)/len(answer_lens):.0f}")
        print(f"  Median: {answer_lens[len(answer_lens)//2]}")
        print(f"  Min: {min(answer_lens)}, Max: {max(answer_lens)}")
        print(f"  P10: {answer_lens[len(answer_lens)//10]}, P90: {answer_lens[9*len(answer_lens)//10]}")

    return len(converted), total_tokens


def main():
    print("Converting Step 9 training data to Together AI format")
    print("No system message — model learns careful behavior as default")

    total_records = 0
    total_tokens = 0

    for model in MODELS:
        n, t = convert_model(model)
        total_records += n
        total_tokens += t

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_records} records, ~{total_tokens:,.0f} tokens")
    print(f"Files ready for upload to Together AI fine-tuning API")


if __name__ == "__main__":
    main()
