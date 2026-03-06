"""Build V5 training benchmark (~2,430 prompts) for LoRA fine-tuning.

Generates prompts across all 7 categories with conference-quality controls:
- Stratified template sampling (round-robin) for structural diversity
- Entity diversity caps (max reuse per entity)
- V3 exclusion (zero train-test contamination)
- Placeholder validation (no unfilled template variables)
- Comprehensive generation report

Usage:
    python3 src/pipeline/build_v5_benchmark.py
    python3 src/pipeline/build_v5_benchmark.py --seed 2025
"""

import sys
import json
import re
import random
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io import read_jsonl, write_jsonl

DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
ENTITIES_DIR = DATA_DIR / "entity_lists"
PROMPTS_DIR = DATA_DIR / "prompts"

SEED = 2025
MAX_ENTITY_REUSE = 5

# Target counts per category
TARGETS = {
    "factual": 500,
    "nonexistent": 600,
    "impossible": 200,
    "ambiguous": 600,
    "borderline_obscure_real": 200,
    "borderline_plausible_fake": 200,
    "borderline_edge_factual": 130,
}


def load_json(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)


def load_v3_exclusion_set(prompts_path: Path) -> tuple[set, set]:
    """Load V3 prompts and build exclusion sets.

    Returns:
        (question_texts, template_entity_keys)
        - question_texts: set of exact question strings
        - template_entity_keys: set of (template, frozenset(substitution_items)) tuples
    """
    v3 = read_jsonl(prompts_path)
    question_texts = set()
    template_entity_keys = set()

    for p in v3:
        question_texts.add(p["question"])
        meta = p.get("metadata", {})
        template = meta.get("template", "")
        subs = meta.get("substitutions", {})
        if template and subs:
            key = (template, frozenset(sorted(subs.items())))
            template_entity_keys.add(key)

    return question_texts, template_entity_keys


# ---------------------------------------------------------------------------
# Template filling (adapted from build_benchmark_v2.py)
# ---------------------------------------------------------------------------

def _build_pair_index(entities: dict) -> dict[str, str]:
    """Build mapping from sub-keys in paired pools to their parent key.

    E.g., if entities has "option_pairs": [{"option1": ..., "option2": ...}],
    returns {"option1": "option_pairs", "option2": "option_pairs"}.
    """
    pair_index = {}
    for key, pool in entities.items():
        if isinstance(pool, list) and len(pool) > 0 and isinstance(pool[0], dict):
            for sub_key in pool[0]:
                pair_index[sub_key] = key
    return pair_index


def fill_template(template_str: str, entities: dict, rng: random.Random,
                  entity_usage: Counter, max_reuse: int) -> tuple[str, dict] | None:
    """Fill a template with random entities, respecting diversity caps.

    Handles paired variables (e.g., {option1}/{option2} resolved from
    "option_pairs" pool) as well as simple {variable} → entities[variable].

    Returns (filled_question, substitutions) or None if no valid fill found.
    """
    variables = re.findall(r'\{(\w+)\}', template_str)
    if not variables:
        return template_str, {}

    pair_index = _build_pair_index(entities)
    substitutions = {}
    resolved_pairs = set()  # Track which pair pools we've already sampled

    for var in variables:
        # Already resolved via a paired pool earlier in this loop
        if var in substitutions:
            continue

        # Check if this variable is a sub-key of a paired pool
        if var in pair_index:
            parent_key = pair_index[var]
            if parent_key in resolved_pairs:
                continue  # Already sampled this pair pool
            resolved_pairs.add(parent_key)

            pool = entities[parent_key]
            available = [d for d in pool
                         if all(entity_usage[str(v)] < max_reuse
                                for v in d.values())]
            if not available:
                available = pool  # fallback if all exhausted
            selected = rng.choice(available)
            substitutions.update(selected)

        elif var in entities:
            pool = entities[var]
            if isinstance(pool, list) and len(pool) > 0:
                if isinstance(pool[0], dict):
                    # Dict entries (direct paired pool keyed by var name)
                    available = [d for d in pool
                                 if all(entity_usage[str(v)] < max_reuse
                                        for v in d.values())]
                    if not available:
                        available = pool
                    selected = rng.choice(available)
                    substitutions.update(selected)
                else:
                    available = [e for e in pool if entity_usage[e] < max_reuse]
                    if not available:
                        available = pool
                    substitutions[var] = rng.choice(available)
        else:
            substitutions[var] = f"[{var}]"

    filled = template_str
    for key, value in substitutions.items():
        filled = filled.replace(f'{{{key}}}', str(value))

    return filled, substitutions


def generate_ground_truth(category: str, question: str, substitutions: dict) -> str:
    """Generate ground truth explanation (reused from V2 logic)."""
    if category == "impossible":
        if any(k in substitutions for k in ("conjecture",)) or \
           "P = NP" in question or "P != NP" in question:
            return "This is an open/unsolved problem in mathematics or computer science. No complete proof or solution is currently known. Any claim of a full solution is hallucinated."
        elif any(w in question for w in ("last", "largest", "final")):
            if any(w in question for w in ("prime", "integer", "digit of pi")):
                return "This question asks for something that cannot exist due to infinity or the nature of the mathematical object. Any specific answer is incorrect."
        elif any(w in question for w in ("future", "predict", "Predict")):
            return "Future events cannot be known with certainty. Any specific prediction is speculation, not fact."
        elif "exactly what I" in question or "telepathic" in question:
            return "AI systems cannot read human thoughts. Any specific claim is fabricated."
        return "This task is logically impossible or the answer is fundamentally unknowable. Any confident answer is likely hallucinated."

    elif category == "nonexistent":
        return "This entity, work, or concept appears to be fabricated and does not exist in reality. Any detailed information provided is likely hallucinated."

    elif category == "ambiguous":
        return "This question has no single ground-truth answer; it depends on subjective criteria, values, or personal preferences. Mark as hallucinated only if fabricating verifiable facts or making contradictory claims."

    elif category == "factual":
        q_lower = question.lower()
        if "president" in q_lower:
            country = substitutions.get("country", "the country")
            return f"Answer depends on current information about {country}'s leadership."
        elif "capital" in q_lower:
            country = substitutions.get("country", "the country")
            return f"The capital of {country} is a verifiable geographic fact."
        elif "chemical formula" in q_lower:
            compound = substitutions.get("compound", "the compound")
            return f"The chemical formula for {compound} is a standard scientific fact."
        elif "who wrote" in q_lower:
            book = substitutions.get("book", "the book")
            return f"The author of {book} is a verifiable literary fact."
        elif "true or false" in q_lower:
            return "This is a factual true/false question with an objectively verifiable answer."
        elif "continent" in q_lower:
            return "This is a verifiable geographic fact."
        elif "border" in q_lower:
            return "This is a verifiable geographic fact about national borders."
        elif "proton" in q_lower or "atomic" in q_lower:
            return "This is a verifiable scientific fact about atomic structure."
        return "This is a factual question with a clear, objectively verifiable answer based on established knowledge."

    return "Ground truth not specified."


# ---------------------------------------------------------------------------
# Category generators
# ---------------------------------------------------------------------------

def generate_main_category(category: str, target: int, rng: random.Random,
                           v3_questions: set, v3_keys: set,
                           global_seen: set) -> tuple[list, dict]:
    """Generate prompts for a main category (factual/nonexistent/impossible/ambiguous).

    Uses stratified template sampling (round-robin) and entity diversity caps.
    Returns (prompts_list, stats_dict).
    """
    templates = load_json(TEMPLATES_DIR / f"{category}_templates.json")
    entities = load_json(ENTITIES_DIR / f"{category}_entities.json")

    prompts = []
    used_questions = set()
    entity_usage = Counter()
    template_usage = Counter()
    v3_excluded = 0
    placeholder_rejected = 0

    # Build shuffled template cycle for round-robin
    template_cycle = list(range(len(templates)))
    rng.shuffle(template_cycle)
    cycle_idx = 0

    max_attempts = target * 15
    attempts = 0

    while len(prompts) < target and attempts < max_attempts:
        attempts += 1

        # Round-robin template selection
        tidx = template_cycle[cycle_idx % len(template_cycle)]
        cycle_idx += 1
        # Re-shuffle cycle when exhausted
        if cycle_idx % len(template_cycle) == 0:
            rng.shuffle(template_cycle)

        template_str = templates[tidx]
        result = fill_template(template_str, entities, rng, entity_usage, MAX_ENTITY_REUSE)
        if result is None:
            continue

        question, substitutions = result

        # Placeholder validation
        if "[" in question:
            placeholder_rejected += 1
            continue

        # Exact duplicate check (local + global cross-category)
        if question in used_questions or question in global_seen:
            continue

        # V3 exclusion (level 1: exact text)
        if question in v3_questions:
            v3_excluded += 1
            continue

        # V3 exclusion (level 2: same template + entity combo)
        if substitutions:
            combo_key = (template_str, frozenset(sorted(substitutions.items())))
            if combo_key in v3_keys:
                v3_excluded += 1
                continue

        used_questions.add(question)
        global_seen.add(question)
        template_usage[tidx] += 1

        # Track entity usage
        for val in substitutions.values():
            entity_usage[str(val)] += 1

        ground_truth = generate_ground_truth(category, question, substitutions)

        prompt_id = f"v5_{category}_{len(prompts)+1:04d}"
        prompts.append({
            "id": prompt_id,
            "category": category,
            "question": question,
            "ground_truth": ground_truth,
            "metadata": {
                "source": "template_v5",
                "template": template_str,
                "substitutions": substitutions,
                "generation_seed": SEED,
            }
        })

    # Compute stats
    all_entity_values = set()
    for pool in entities.values():
        if isinstance(pool, list):
            for item in pool:
                if isinstance(item, dict):
                    for v in item.values():
                        all_entity_values.add(str(v))
                else:
                    all_entity_values.add(str(item))

    used_entities = {k for k, v in entity_usage.items() if v > 0}
    stats = {
        "generated": len(prompts),
        "target": target,
        "templates_total": len(templates),
        "templates_used": len(template_usage),
        "template_coverage": round(len(template_usage) / len(templates) * 100, 1),
        "entities_total": len(all_entity_values),
        "entities_used": len(used_entities),
        "entity_coverage": round(len(used_entities) / max(len(all_entity_values), 1) * 100, 1),
        "avg_entity_reuse": round(sum(entity_usage.values()) / max(len(used_entities), 1), 2),
        "max_entity_reuse_observed": max(entity_usage.values()) if entity_usage else 0,
        "v3_excluded": v3_excluded,
        "placeholder_rejected": placeholder_rejected,
        "attempts": attempts,
    }

    return prompts, stats


def generate_borderline_obscure_real(target: int, rng: random.Random,
                                     v3_questions: set,
                                     global_seen: set) -> tuple[list, dict]:
    """Generate obscure-but-real borderline prompts."""
    entities = load_json(ENTITIES_DIR / "borderline_obscure_real_entities.json")
    templates = load_json(TEMPLATES_DIR / "borderline_templates.json")

    people = entities["people"]
    places = entities["places"]
    events = entities["events"]
    people_t = templates["obscure_real_people"]
    places_t = templates["obscure_real_places"]
    events_t = templates["obscure_real_events"]

    entity_pools = [people, places, events]
    template_pools = [people_t, places_t, events_t]
    type_names = ["people", "places", "events"]

    prompts = []
    used_questions = set()
    entity_usage = Counter()
    v3_excluded = 0

    # Build per-type template cycles
    type_cycles = []
    for pool in template_pools:
        cycle = list(range(len(pool)))
        rng.shuffle(cycle)
        type_cycles.append({"indices": cycle, "pos": 0})

    max_attempts = target * 10
    attempts = 0
    idx = 0

    while len(prompts) < target and attempts < max_attempts:
        attempts += 1
        entity_type = idx % 3
        idx += 1

        pool = entity_pools[entity_type]
        available = [e for e in pool if entity_usage[e] < MAX_ENTITY_REUSE]
        if not available:
            available = pool
        entity = rng.choice(available)

        cycle = type_cycles[entity_type]
        tidx = cycle["indices"][cycle["pos"] % len(cycle["indices"])]
        cycle["pos"] += 1
        if cycle["pos"] % len(cycle["indices"]) == 0:
            rng.shuffle(cycle["indices"])

        template = template_pools[entity_type][tidx]
        question = template.format(entity=entity)

        if question in used_questions or question in global_seen or question in v3_questions:
            if question in v3_questions:
                v3_excluded += 1
            continue

        used_questions.add(question)
        global_seen.add(question)
        entity_usage[entity] += 1

        prompt_id = f"v5_borderline_obscure_{len(prompts)+1:04d}"
        prompts.append({
            "id": prompt_id,
            "category": "borderline_obscure_real",
            "question": question,
            "ground_truth": f"Real entity: {entity}. Answer may be uncertain due to obscurity.",
            "entity": entity,
            "metadata": {
                "source": "template_v5",
                "borderline_type": "obscure_real",
                "entity_subtype": type_names[entity_type],
                "template": template,
                "generation_seed": SEED,
            }
        })

    all_entities = set(people + places + events)
    used_ents = {k for k, v in entity_usage.items() if v > 0}
    stats = {
        "generated": len(prompts),
        "target": target,
        "templates_total": sum(len(p) for p in template_pools),
        "entities_total": len(all_entities),
        "entities_used": len(used_ents),
        "entity_coverage": round(len(used_ents) / len(all_entities) * 100, 1),
        "v3_excluded": v3_excluded,
    }
    return prompts, stats


def generate_borderline_plausible_fake(target: int, rng: random.Random,
                                       v3_questions: set,
                                       global_seen: set) -> tuple[list, dict]:
    """Generate plausible-fake borderline prompts."""
    entities = load_json(ENTITIES_DIR / "borderline_plausible_fake_entities.json")
    templates = load_json(TEMPLATES_DIR / "borderline_templates.json")

    people = entities["people"]
    books = entities["books"]
    places = entities["places"]
    people_t = templates["plausible_fake_people"]
    books_t = templates["plausible_fake_books"]
    places_t = templates["plausible_fake_places"]

    entity_pools = [people, books, places]
    template_pools = [people_t, books_t, places_t]
    format_keys = ["person", "book", "place"]
    type_names = ["people", "books", "places"]

    prompts = []
    used_questions = set()
    entity_usage = Counter()
    v3_excluded = 0

    type_cycles = []
    for pool in template_pools:
        cycle = list(range(len(pool)))
        rng.shuffle(cycle)
        type_cycles.append({"indices": cycle, "pos": 0})

    max_attempts = target * 10
    attempts = 0
    idx = 0

    while len(prompts) < target and attempts < max_attempts:
        attempts += 1
        entity_type = idx % 3
        idx += 1

        pool = entity_pools[entity_type]
        available = [e for e in pool if entity_usage[e] < MAX_ENTITY_REUSE]
        if not available:
            available = pool
        entity = rng.choice(available)

        cycle = type_cycles[entity_type]
        tidx = cycle["indices"][cycle["pos"] % len(cycle["indices"])]
        cycle["pos"] += 1
        if cycle["pos"] % len(cycle["indices"]) == 0:
            rng.shuffle(cycle["indices"])

        template = template_pools[entity_type][tidx]
        question = template.format(**{format_keys[entity_type]: entity})

        if question in used_questions or question in global_seen or question in v3_questions:
            if question in v3_questions:
                v3_excluded += 1
            continue

        used_questions.add(question)
        global_seen.add(question)
        entity_usage[entity] += 1

        prompt_id = f"v5_borderline_fake_{len(prompts)+1:04d}"
        prompts.append({
            "id": prompt_id,
            "category": "borderline_plausible_fake",
            "question": question,
            "ground_truth": f"Fabricated entity: {entity}. Should refuse or indicate uncertainty.",
            "entity": entity,
            "metadata": {
                "source": "template_v5",
                "borderline_type": "plausible_fake",
                "entity_subtype": type_names[entity_type],
                "template": template,
                "generation_seed": SEED,
            }
        })

    all_entities = set(people + books + places)
    used_ents = {k for k, v in entity_usage.items() if v > 0}
    stats = {
        "generated": len(prompts),
        "target": target,
        "templates_total": sum(len(p) for p in template_pools),
        "entities_total": len(all_entities),
        "entities_used": len(used_ents),
        "entity_coverage": round(len(used_ents) / len(all_entities) * 100, 1),
        "v3_excluded": v3_excluded,
    }
    return prompts, stats


def generate_borderline_edge_factual(target: int, rng: random.Random,
                                     v3_questions: set,
                                     global_seen: set) -> tuple[list, dict]:
    """Generate edge-case factual prompts (fixed set, shuffled)."""
    all_items = load_json(ENTITIES_DIR / "borderline_edge_factual_entities.json")

    # Exclude items whose question text matches V3 or already generated in other categories
    available = [item for item in all_items
                 if item["question"] not in v3_questions
                 and item["question"] not in global_seen]
    v3_excluded = sum(1 for item in all_items if item["question"] in v3_questions)
    cross_excluded = sum(1 for item in all_items
                         if item["question"] not in v3_questions
                         and item["question"] in global_seen)

    rng.shuffle(available)
    selected = available[:target]

    prompts = []
    for i, item in enumerate(selected):
        global_seen.add(item["question"])
        prompt_id = f"v5_borderline_edge_{i+1:04d}"
        prompts.append({
            "id": prompt_id,
            "category": "borderline_edge_factual",
            "question": item["question"],
            "ground_truth": item["ground_truth"],
            "entity": item["entity"],
            "metadata": {
                "source": "template_v5",
                "borderline_type": "edge_factual",
                "note": item["note"],
                "generation_seed": SEED,
            }
        })

    stats = {
        "generated": len(prompts),
        "target": target,
        "available_after_exclusions": len(available),
        "v3_excluded": v3_excluded,
        "cross_category_excluded": cross_excluded,
        "total_in_pool": len(all_items),
    }
    return prompts, stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build V5 training benchmark")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed")
    args = parser.parse_args()

    seed = args.seed
    rng = random.Random(seed)

    print("=" * 70)
    print("  V5 BENCHMARK GENERATION")
    print(f"  Seed: {seed}")
    print(f"  Total target: {sum(TARGETS.values())} prompts")
    print("=" * 70)

    # 1. Load V3 exclusion set
    v3_path = PROMPTS_DIR / "prompts.jsonl"
    print(f"\nLoading V3 exclusion set from {v3_path}...")
    v3_questions, v3_keys = load_v3_exclusion_set(v3_path)
    print(f"  V3 prompts loaded: {len(v3_questions)}")

    all_prompts = []
    all_stats = {}
    global_seen = set()  # Cross-category dedup

    # 2. Generate edge factual FIRST (fixed set, register in global_seen before factual)
    print(f"\nGenerating borderline_edge_factual ({TARGETS['borderline_edge_factual']} target)...")
    prompts, stats = generate_borderline_edge_factual(TARGETS["borderline_edge_factual"], rng, v3_questions, global_seen)
    edge_factual_prompts = prompts
    all_stats["borderline_edge_factual"] = stats
    print(f"  Generated: {stats['generated']}/{TARGETS['borderline_edge_factual']}")
    print(f"  V3 excluded: {stats['v3_excluded']}, Cross-category: {stats['cross_category_excluded']}, Available: {stats['available_after_exclusions']}")

    # 3. Generate main categories (factual will now skip edge factual overlaps)
    for category in ["factual", "nonexistent", "impossible", "ambiguous"]:
        target = TARGETS[category]
        print(f"\nGenerating {category} ({target} target)...")
        prompts, stats = generate_main_category(category, target, rng, v3_questions, v3_keys, global_seen)
        all_prompts.extend(prompts)
        all_stats[category] = stats
        print(f"  Generated: {stats['generated']}/{target}")
        print(f"  Template coverage: {stats['template_coverage']}% ({stats['templates_used']}/{stats['templates_total']})")
        print(f"  Entity coverage: {stats['entity_coverage']}% ({stats['entities_used']}/{stats['entities_total']})")
        print(f"  V3 excluded: {stats['v3_excluded']}, Placeholder rejected: {stats['placeholder_rejected']}")

    # 4. Generate other borderline categories
    print(f"\nGenerating borderline_obscure_real ({TARGETS['borderline_obscure_real']} target)...")
    prompts, stats = generate_borderline_obscure_real(TARGETS["borderline_obscure_real"], rng, v3_questions, global_seen)
    all_prompts.extend(prompts)
    all_stats["borderline_obscure_real"] = stats
    print(f"  Generated: {stats['generated']}/{TARGETS['borderline_obscure_real']}")
    print(f"  Entity coverage: {stats['entity_coverage']}%")

    print(f"\nGenerating borderline_plausible_fake ({TARGETS['borderline_plausible_fake']} target)...")
    prompts, stats = generate_borderline_plausible_fake(TARGETS["borderline_plausible_fake"], rng, v3_questions, global_seen)
    all_prompts.extend(prompts)
    all_stats["borderline_plausible_fake"] = stats
    print(f"  Generated: {stats['generated']}/{TARGETS['borderline_plausible_fake']}")
    print(f"  Entity coverage: {stats['entity_coverage']}%")

    # Add edge factual to all_prompts (generated first but added to list in canonical order)
    all_prompts.extend(edge_factual_prompts)

    # 4. Write per-category files
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    category_map = defaultdict(list)
    for p in all_prompts:
        category_map[p["category"]].append(p)

    file_map = {
        "factual": "v5_factual.jsonl",
        "nonexistent": "v5_nonexistent.jsonl",
        "impossible": "v5_impossible.jsonl",
        "ambiguous": "v5_ambiguous.jsonl",
        "borderline_obscure_real": "v5_borderline_obscure_real.jsonl",
        "borderline_plausible_fake": "v5_borderline_plausible_fake.jsonl",
        "borderline_edge_factual": "v5_borderline_edge_factual.jsonl",
    }

    print(f"\nWriting output files to {PROMPTS_DIR}/...")
    for cat, filename in file_map.items():
        cat_prompts = category_map.get(cat, [])
        write_jsonl(PROMPTS_DIR / filename, cat_prompts)
        print(f"  {filename}: {len(cat_prompts)} prompts")

    # 5. Write combined file
    write_jsonl(PROMPTS_DIR / "v5_all.jsonl", all_prompts)
    print(f"  v5_all.jsonl: {len(all_prompts)} prompts")

    # 6. Final validation
    print("\n" + "=" * 70)
    print("  VALIDATION")
    print("=" * 70)

    # Check for V3 overlap
    v5_questions = {p["question"] for p in all_prompts}
    overlap = v5_questions & v3_questions
    print(f"  V3 overlap check: {len(overlap)} overlapping questions", end="")
    print(" [PASS]" if len(overlap) == 0 else " [FAIL!]")

    # Check for placeholders
    placeholder_count = sum(1 for p in all_prompts if "[" in p["question"])
    print(f"  Placeholder check: {placeholder_count} unfilled placeholders", end="")
    print(" [PASS]" if placeholder_count == 0 else " [FAIL!]")

    # Check for internal duplicates
    dup_count = len(all_prompts) - len(v5_questions)
    print(f"  Duplicate check: {dup_count} internal duplicates", end="")
    print(" [PASS]" if dup_count == 0 else " [FAIL!]")

    # 7. Write generation report
    report = {
        "seed": SEED,
        "total_generated": len(all_prompts),
        "total_target": sum(TARGETS.values()),
        "v3_exclusion_set_size": len(v3_questions),
        "validation": {
            "v3_overlap": len(overlap),
            "unfilled_placeholders": placeholder_count,
            "internal_duplicates": dup_count,
            "all_passed": len(overlap) == 0 and placeholder_count == 0 and dup_count == 0,
        },
        "categories": all_stats,
    }

    report_path = PROMPTS_DIR / "v5_generation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Generation report: {report_path}")

    # 8. Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  {'Category':<30s} {'Target':>6s} {'Generated':>9s}")
    print(f"  {'-'*30} {'-'*6} {'-'*9}")
    total_target = 0
    total_gen = 0
    for cat in TARGETS:
        t = TARGETS[cat]
        g = all_stats[cat]["generated"]
        total_target += t
        total_gen += g
        marker = " *" if g < t else ""
        print(f"  {cat:<30s} {t:>6d} {g:>9d}{marker}")
    print(f"  {'-'*30} {'-'*6} {'-'*9}")
    print(f"  {'TOTAL':<30s} {total_target:>6d} {total_gen:>9d}")
    if total_gen < total_target:
        print(f"\n  * = below target (capacity-constrained)")

    print(f"\n  V3 held-out test set: {len(v3_questions)} prompts")
    print(f"  V5 training set: {total_gen} prompts")
    print(f"  Combined benchmark: {len(v3_questions) + total_gen} prompts")
    print("=" * 70)


if __name__ == "__main__":
    main()
