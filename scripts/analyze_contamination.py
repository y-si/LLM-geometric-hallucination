"""
Step 11C: Entity-level train-test contamination analysis.

Re-scores fine-tuning evaluation on decontaminated subset (test prompts
whose entities do NOT appear in V5 training data).

Outputs:
  - Per-category accuracy: full test set vs clean subset
  - Overall accuracy comparison
  - Determines if contamination inflated fine-tuning results
"""

import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

# --- Load data ---

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

def load_json(path):
    with open(path) as f:
        return json.load(f)

# V5 training prompts
v5_files = list(ROOT.glob("data/prompts/v5_*.jsonl"))
v5_prompts = []
for f in v5_files:
    if f.name == "v5_all.jsonl" or f.name == "v5_generation_report.json":
        continue
    v5_prompts.extend(load_jsonl(f))

print(f"Loaded {len(v5_prompts)} V5 training prompts from {len(v5_files)-1} files")

# Entity lists (to know what entities exist per category)
entity_dir = ROOT / "data" / "entity_lists"

# Load entity pools
entity_pools = {}
for f in entity_dir.glob("*.json"):
    entity_pools[f.stem] = load_json(f)

# --- Extract entities from prompts ---

def extract_entities_from_prompt(prompt):
    """Extract entity names from prompt metadata or text."""
    entities = set()
    meta = prompt.get("metadata", {})
    subs = meta.get("substitutions", {})

    # From substitutions metadata
    for key, val in subs.items():
        if isinstance(val, str) and val.strip() and val not in ("[profession]", "[topic]"):
            entities.add(val.lower().strip())

    return entities

def extract_entities_from_text(text, entity_pool_values):
    """Check if any known entity names appear in the prompt text."""
    text_lower = text.lower()
    found = set()
    for entity in entity_pool_values:
        if isinstance(entity, str) and entity.lower() in text_lower:
            found.add(entity.lower())
        elif isinstance(entity, dict):
            # Edge factual has {question, answer} dicts
            q = entity.get("question", "")
            if q.lower() in text_lower:
                found.add(q.lower())
    return found

# Build V5 entity set per category
v5_entities_by_cat = defaultdict(set)
v5_entities_all = set()

for p in v5_prompts:
    cat = p.get("category", "")
    ents = extract_entities_from_prompt(p)
    v5_entities_by_cat[cat].update(ents)
    v5_entities_all.update(ents)

    # Also extract from question text using entity pools
    question = p.get("question", "")
    for pool_name, pool_data in entity_pools.items():
        if isinstance(pool_data, list):
            for item in pool_data:
                if isinstance(item, str) and len(item) > 3 and item.lower() in question.lower():
                    v5_entities_by_cat[cat].add(item.lower())
                    v5_entities_all.add(item.lower())
        elif isinstance(pool_data, dict):
            for subkey, sublist in pool_data.items():
                if isinstance(sublist, list):
                    for item in sublist:
                        if isinstance(item, str) and len(item) > 3 and item.lower() in question.lower():
                            v5_entities_by_cat[cat].add(item.lower())
                            v5_entities_all.add(item.lower())

print(f"\nV5 entities by category:")
for cat, ents in sorted(v5_entities_by_cat.items()):
    print(f"  {cat}: {len(ents)} unique entities")

# --- Load fine-tuned evaluation results ---

ft_results = {}

# Mixtral configC
mixtral_path = ROOT / "results/v5_finetuned/mixtral-8x7b/configC/judged_answers.jsonl"
if mixtral_path.exists():
    ft_results["Mixtral configC"] = load_jsonl(mixtral_path)
    print(f"\nLoaded Mixtral configC: {len(ft_results['Mixtral configC'])} judged answers")

# Llama configA
llama_path = ROOT / "results/v5_finetuned/llama-4-maverick-17b/configA/judged_answers.jsonl"
if llama_path.exists():
    ft_results["Llama configA"] = load_jsonl(llama_path)
    print(f"Loaded Llama configA: {len(ft_results['Llama configA'])} judged answers")

# --- Classify each test prompt as clean or contaminated ---

def classify_prompt(prompt, v5_entity_set):
    """Check if any entity in this prompt also appears in V5 training."""
    # Check substitutions
    ents = extract_entities_from_prompt(prompt)
    for e in ents:
        if e in v5_entity_set:
            return "contaminated", e

    # Check question text against all known entity pool values
    question = prompt.get("question", "").lower()
    for pool_name, pool_data in entity_pools.items():
        if isinstance(pool_data, list):
            for item in pool_data:
                if isinstance(item, str) and len(item) > 3:
                    if item.lower() in question and item.lower() in v5_entity_set:
                        return "contaminated", item
        elif isinstance(pool_data, dict):
            for subkey, sublist in pool_data.items():
                if isinstance(sublist, list):
                    for item in sublist:
                        if isinstance(item, str) and len(item) > 3:
                            if item.lower() in question and item.lower() in v5_entity_set:
                                return "contaminated", item

    return "clean", None

# --- Analyze ---

print("\n" + "="*80)
print("DECONTAMINATION ANALYSIS")
print("="*80)

for model_name, results in ft_results.items():
    print(f"\n{'='*60}")
    print(f"MODEL: {model_name}")
    print(f"{'='*60}")

    # Classify each prompt
    clean_results = []
    contaminated_results = []
    clean_by_cat = defaultdict(list)
    contam_by_cat = defaultdict(list)
    all_by_cat = defaultdict(list)

    for r in results:
        cat = r.get("category", "unknown")
        status, entity = classify_prompt(r, v5_entities_all)
        all_by_cat[cat].append(r)

        if status == "clean":
            clean_results.append(r)
            clean_by_cat[cat].append(r)
        else:
            contaminated_results.append(r)
            contam_by_cat[cat].append(r)

    # Overall comparison
    def accuracy(results_list):
        if not results_list:
            return 0, 0, 0, 0
        correct = sum(1 for r in results_list if r.get("judge_label") == 0)
        halluc = sum(1 for r in results_list if r.get("judge_label") == 2)
        refused = sum(1 for r in results_list if r.get("judge_label") == 3)
        n = len(results_list)
        return correct/n*100, halluc/n*100, refused/n*100, n

    full_acc, full_hal, full_ref, full_n = accuracy(results)
    clean_acc, clean_hal, clean_ref, clean_n = accuracy(clean_results)
    contam_acc, contam_hal, contam_ref, contam_n = accuracy(contaminated_results)

    print(f"\n--- OVERALL ---")
    print(f"{'Subset':<25} {'N':>5} {'Accuracy':>10} {'Halluc':>10} {'Refused':>10}")
    print(f"{'-'*60}")
    print(f"{'Full test set':<25} {full_n:>5} {full_acc:>9.1f}% {full_hal:>9.1f}% {full_ref:>9.1f}%")
    print(f"{'Clean (no overlap)':<25} {clean_n:>5} {clean_acc:>9.1f}% {clean_hal:>9.1f}% {clean_ref:>9.1f}%")
    print(f"{'Contaminated':<25} {contam_n:>5} {contam_acc:>9.1f}% {contam_hal:>9.1f}% {contam_ref:>9.1f}%")
    print(f"{'Gap (full - clean)':<25} {'':>5} {full_acc - clean_acc:>+9.1f}pp {full_hal - clean_hal:>+9.1f}pp")

    # Per-category comparison
    print(f"\n--- PER CATEGORY ---")
    print(f"{'Category':<30} {'Full N':>6} {'Full Acc':>9} {'Clean N':>8} {'Clean Acc':>10} {'Gap':>8}")
    print(f"{'-'*75}")

    categories = sorted(set(r.get("category") for r in results))
    for cat in categories:
        all_acc, all_hal, _, all_n = accuracy(all_by_cat[cat])
        cl_acc, cl_hal, _, cl_n = accuracy(clean_by_cat.get(cat, []))
        gap = all_acc - cl_acc if cl_n > 0 else float('nan')

        power = "GOOD" if cl_n >= 30 else ("OK" if cl_n >= 20 else ("POOR" if cl_n >= 5 else "N/A"))

        gap_str = f"{gap:>+7.1f}pp" if cl_n > 0 else "    N/A"
        cl_acc_str = f"{cl_acc:>9.1f}%" if cl_n > 0 else "      N/A"

        print(f"{cat:<30} {all_n:>6} {all_acc:>8.1f}% {cl_n:>8} {cl_acc_str} {gap_str}  ({power})")

    # Entity-dependent vs entity-independent split
    entity_dep_cats = {"nonexistent", "borderline_plausible_fake", "borderline_obscure_real"}
    entity_indep_cats = {"factual", "ambiguous", "impossible", "borderline_edge_factual"}

    dep_all = [r for r in results if r.get("category") in entity_dep_cats]
    dep_clean = [r for r in clean_results if r.get("category") in entity_dep_cats]
    indep_all = [r for r in results if r.get("category") in entity_indep_cats]
    indep_clean = [r for r in clean_results if r.get("category") in entity_indep_cats]

    print(f"\n--- ENTITY-DEPENDENT vs ENTITY-INDEPENDENT ---")
    dep_all_acc, dep_all_hal, _, dep_all_n = accuracy(dep_all)
    dep_cl_acc, dep_cl_hal, _, dep_cl_n = accuracy(dep_clean)
    indep_all_acc, indep_all_hal, _, indep_all_n = accuracy(indep_all)
    indep_cl_acc, indep_cl_hal, _, indep_cl_n = accuracy(indep_clean)

    print(f"{'Group':<30} {'Full N':>6} {'Full Acc':>9} {'Clean N':>8} {'Clean Acc':>10} {'Gap':>8}")
    print(f"{'-'*75}")
    print(f"{'Entity-dependent':<30} {dep_all_n:>6} {dep_all_acc:>8.1f}% {dep_cl_n:>8} {dep_cl_acc:>9.1f}% {dep_all_acc - dep_cl_acc:>+7.1f}pp")
    print(f"{'Entity-independent':<30} {indep_all_n:>6} {indep_all_acc:>8.1f}% {indep_cl_n:>8} {indep_cl_acc:>9.1f}% {indep_all_acc - indep_cl_acc:>+7.1f}pp")

print("\n" + "="*80)
print("INTERPRETATION GUIDE")
print("="*80)
print("""
If full accuracy ≈ clean accuracy (gap < 3pp):
  → Contamination didn't inflate results. Model learned behavior, not entity names.
  → Report both numbers, note contamination, no further action needed.

If full accuracy > clean accuracy by 3-10pp:
  → Moderate inflation. Entity memorization helped on some prompts.
  → Report decontaminated numbers as primary. Consider Option B (new test prompts).

If full accuracy > clean accuracy by >10pp:
  → Serious inflation. Fine-tuning results need re-evaluation.
  → Option B required: generate new test prompts with novel entities.
""")
