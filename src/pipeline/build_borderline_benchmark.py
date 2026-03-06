"""Build borderline benchmark with edge cases.

Creates high-value prompts that sit between obvious safety and danger:
- Obscure but real entities
- Plausible-looking fake entities
- Edge-case factual questions (real but tricky)

Entity pools and templates are loaded from external JSON files:
- data/entity_lists/borderline_obscure_real_entities.json
- data/entity_lists/borderline_plausible_fake_entities.json
- data/entity_lists/borderline_edge_factual_entities.json
- data/templates/borderline_templates.json
"""

import sys
from pathlib import Path
import json
import random

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.io import write_jsonl
from src.utils.seed import set_seed

# Resolve project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_DIR = PROJECT_ROOT / "data" / "entity_lists"
TEMPLATES_DIR = PROJECT_ROOT / "data" / "templates"


def load_json(path):
    """Load a JSON file."""
    with open(path) as f:
        return json.load(f)


def load_entities():
    """Load all borderline entity pools from external JSON files."""
    obscure_real = load_json(ENTITIES_DIR / "borderline_obscure_real_entities.json")
    plausible_fake = load_json(ENTITIES_DIR / "borderline_plausible_fake_entities.json")
    edge_factual = load_json(ENTITIES_DIR / "borderline_edge_factual_entities.json")
    return obscure_real, plausible_fake, edge_factual


def load_templates():
    """Load borderline templates from external JSON file."""
    return load_json(TEMPLATES_DIR / "borderline_templates.json")


def generate_obscure_real_questions(entities, templates, n=150, seed=42):
    """Generate questions about obscure but real entities."""
    random.seed(seed)

    people = entities["people"]
    places = entities["places"]
    events = entities["events"]

    people_templates = templates["obscure_real_people"]
    place_templates = templates["obscure_real_places"]
    event_templates = templates["obscure_real_events"]

    questions = []
    idx = 0

    while len(questions) < n:
        # Rotate through entity types for balance
        entity_type = idx % 3

        if entity_type == 0:
            entity = random.choice(people)
            template = random.choice(people_templates)
        elif entity_type == 1:
            entity = random.choice(places)
            template = random.choice(place_templates)
        else:
            entity = random.choice(events)
            template = random.choice(event_templates)

        question = template.format(entity=entity)

        # Avoid duplicate questions
        if question not in {q['question'] for q in questions}:
            questions.append({
                'id': f'borderline_obscure_{len(questions)}',
                'category': 'borderline_obscure_real',
                'question': question,
                'ground_truth': f'Real entity: {entity}. Answer may be uncertain due to obscurity.',
                'entity': entity,
                'metadata': {'borderline_type': 'obscure_real'}
            })

        idx += 1
        if idx > n * 5:  # safety valve
            break

    return questions[:n]


def generate_plausible_fake_questions(entities, templates, n=150, seed=42):
    """Generate questions about plausible-looking fake entities."""
    random.seed(seed)

    people = entities["people"]
    books = entities["books"]
    places = entities["places"]

    person_templates = templates["plausible_fake_people"]
    book_templates = templates["plausible_fake_books"]
    place_templates = templates["plausible_fake_places"]

    questions = []
    idx = 0

    while len(questions) < n:
        entity_type = idx % 3

        if entity_type == 0:
            entity = random.choice(people)
            template = random.choice(person_templates)
            question = template.format(person=entity)
        elif entity_type == 1:
            entity = random.choice(books)
            template = random.choice(book_templates)
            question = template.format(book=entity)
        else:
            entity = random.choice(places)
            template = random.choice(place_templates)
            question = template.format(place=entity)

        # Avoid duplicate questions
        if question not in {q['question'] for q in questions}:
            questions.append({
                'id': f'borderline_fake_{len(questions)}',
                'category': 'borderline_plausible_fake',
                'question': question,
                'ground_truth': f'Fabricated entity: {entity}. Should refuse or indicate uncertainty.',
                'entity': entity,
                'metadata': {'borderline_type': 'plausible_fake'}
            })

        idx += 1
        if idx > n * 5:
            break

    return questions[:n]


def generate_edge_case_factual(edge_factual, n=100, seed=42):
    """Generate factual questions with unusual phrasing or rare knowledge."""
    random.seed(seed)

    questions = []
    shuffled = edge_factual.copy()
    random.shuffle(shuffled)

    for i, item in enumerate(shuffled[:n]):
        questions.append({
            'id': f'borderline_edge_{i}',
            'category': 'borderline_edge_factual',
            'question': item['question'],
            'ground_truth': item['ground_truth'],
            'entity': item['entity'],
            'metadata': {'borderline_type': 'edge_factual', 'note': item['note']}
        })

    return questions


def main():
    """Generate borderline benchmark."""

    set_seed(42)

    print("=" * 60)
    print("BUILDING BORDERLINE BENCHMARK")
    print("=" * 60)

    # Load data from external JSON files
    obscure_real_entities, plausible_fake_entities, edge_factual_entities = load_entities()
    templates = load_templates()

    print(f"\nEntity pool sizes (loaded from data/entity_lists/):")
    print(f"  Obscure real people:     {len(obscure_real_entities['people'])}")
    print(f"  Obscure real places:     {len(obscure_real_entities['places'])}")
    print(f"  Obscure real events:     {len(obscure_real_entities['events'])}")
    print(f"  Plausible fake people:   {len(plausible_fake_entities['people'])}")
    print(f"  Plausible fake books:    {len(plausible_fake_entities['books'])}")
    print(f"  Plausible fake places:   {len(plausible_fake_entities['places'])}")
    print(f"  Edge case factual Qs:    {len(edge_factual_entities)}")

    print(f"\nTemplate counts (loaded from data/templates/):")
    for key, tmpl_list in templates.items():
        print(f"  {key}: {len(tmpl_list)}")

    # Generate all question types
    obscure_real = generate_obscure_real_questions(
        obscure_real_entities, templates, n=150, seed=42
    )
    plausible_fake = generate_plausible_fake_questions(
        plausible_fake_entities, templates, n=150, seed=42
    )
    edge_factual = generate_edge_case_factual(
        edge_factual_entities, n=100, seed=42
    )

    print(f"\nGenerated:")
    print(f"  Obscure real: {len(obscure_real)}")
    print(f"  Plausible fake: {len(plausible_fake)}")
    print(f"  Edge factual: {len(edge_factual)}")
    print(f"  TOTAL: {len(obscure_real) + len(plausible_fake) + len(edge_factual)}")

    # Save to files
    output_dir = Path("data/prompts")
    output_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(output_dir / "borderline_obscure_real.jsonl", obscure_real)
    write_jsonl(output_dir / "borderline_plausible_fake.jsonl", plausible_fake)
    write_jsonl(output_dir / "borderline_edge_factual.jsonl", edge_factual)

    # Combined file
    all_borderline = obscure_real + plausible_fake + edge_factual
    write_jsonl(output_dir / "borderline_all.jsonl", all_borderline)

    print(f"\nSaved to {output_dir}")

    # Show examples
    print("\n" + "=" * 60)
    print("EXAMPLES")
    print("=" * 60)

    print("\n1. Obscure Real:")
    for q in obscure_real[:3]:
        print(f"   {q['question']}")

    print("\n2. Plausible Fake:")
    for q in plausible_fake[:3]:
        print(f"   {q['question']}")

    print("\n3. Edge Factual:")
    for q in edge_factual[:3]:
        print(f"   {q['question']}")

    print("\n" + "=" * 60)
    print("Borderline benchmark complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
