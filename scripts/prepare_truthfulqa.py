"""Step 13A: Download and prepare TruthfulQA for generalization testing.

Downloads TruthfulQA (Lin et al., 2022) from HuggingFace and converts
to our JSONL format for the generate→judge pipeline.

Ground truth is constructed as an enriched string containing best_answer,
all correct_answers, and incorrect_answers — because our judge prompt
template only injects the ground_truth field (meta_info is not shown
to the judge).

Usage:
    pip install datasets  # if not already installed
    python3 scripts/prepare_truthfulqa.py

Output:
    data/prompts/truthfulqa.jsonl  (817 questions)
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_PATH = PROJECT_ROOT / "data" / "prompts" / "truthfulqa.jsonl"


def build_ground_truth(entry):
    """Construct enriched ground truth string for our judge.

    The judge sees only the ground_truth field, not meta_info.
    Include best answer, all correct answers, and known incorrect
    answers so the judge has full context for evaluation.
    """
    parts = [f"Best answer: {entry['best_answer']}"]

    correct = entry.get("correct_answers", [])
    if correct:
        # Skip if identical to best_answer
        other_correct = [a for a in correct if a.strip() != entry["best_answer"].strip()]
        if other_correct:
            parts.append(f"Also acceptable: {'; '.join(other_correct)}")

    incorrect = entry.get("incorrect_answers", [])
    if incorrect:
        parts.append(f"Known incorrect answers: {'; '.join(incorrect)}")

    return "\n".join(parts)


def main():
    # Try to import datasets
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: 'datasets' package not installed.")
        print("  Run: pip install datasets")
        sys.exit(1)

    print("Downloading TruthfulQA from HuggingFace...")
    ds = load_dataset("truthfulqa/truthful_qa", name="generation", split="validation")
    print(f"  Downloaded {len(ds)} questions")

    # Convert to our format
    prompts = []
    categories = {}

    for i, entry in enumerate(ds):
        cat = entry.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

        ground_truth = build_ground_truth(entry)

        prompt = {
            "id": f"truthfulqa_{i:04d}",
            "question": entry["question"],
            "ground_truth": ground_truth,
            "category": cat,
            "metadata": {
                "source": "truthfulqa",
                "type": entry.get("type", ""),
                "best_answer": entry["best_answer"],
                "correct_answers": entry.get("correct_answers", []),
                "incorrect_answers": entry.get("incorrect_answers", []),
                "truthfulqa_source": entry.get("source", ""),
            },
        }
        prompts.append(prompt)

    # Write JSONL
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for p in prompts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(prompts)} prompts to {OUTPUT_PATH}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  TruthfulQA Summary")
    print(f"{'=' * 60}")
    print(f"  Total questions: {len(prompts)}")
    print(f"  Categories: {len(categories)}")
    print(f"\n  {'Category':<35s} {'Count':>5s}")
    print(f"  {'-' * 35} {'-' * 5}")
    for cat in sorted(categories.keys()):
        print(f"  {cat:<35s} {categories[cat]:>5d}")

    # Spot-check: show 3 examples
    print(f"\n{'=' * 60}")
    print(f"  Sample prompts (first 3)")
    print(f"{'=' * 60}")
    for p in prompts[:3]:
        print(f"\n  ID: {p['id']}")
        print(f"  Category: {p['category']}")
        print(f"  Question: {p['question']}")
        gt_preview = p["ground_truth"][:150]
        if len(p["ground_truth"]) > 150:
            gt_preview += "..."
        print(f"  Ground truth: {gt_preview}")

    # Verify no issues
    issues = []
    for p in prompts:
        if not p["question"].strip():
            issues.append(f"{p['id']}: empty question")
        if not p["ground_truth"].strip():
            issues.append(f"{p['id']}: empty ground_truth")
        if "[" in p["question"]:
            issues.append(f"{p['id']}: possible unfilled placeholder in question")

    if issues:
        print(f"\n  ISSUES FOUND ({len(issues)}):")
        for issue in issues[:10]:
            print(f"    - {issue}")
    else:
        print(f"\n  Validation: all {len(prompts)} prompts pass (no empty fields, no placeholders)")

    print(f"\n{'=' * 60}")
    print(f"  DONE — ready for Step 13B (baseline inference)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
