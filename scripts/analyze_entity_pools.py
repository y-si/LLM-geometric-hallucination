"""Analyze entity pool sizes vs template usage to identify expansion targets."""

import json
import re
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
ENTITIES_DIR = DATA_DIR / "entity_lists"

TARGET_PROMPTS_PER_CATEGORY = 500
MIN_POOL_SIZE = 15  # minimum entities per pool for good diversity


def resolve_var_to_pool(var: str, entities: dict):
    """Match a template variable to an entity pool key, handling singular/plural."""
    # Direct match
    if var in entities:
        return var, len(entities[var])

    # Try adding 's' (country -> countries)
    if var + 's' in entities:
        return var + 's', len(entities[var + 's'])

    # Try adding 'es' (compound -> compounds... wait that's just +s)
    if var + 'es' in entities:
        return var + 'es', len(entities[var + 'es'])

    # Try removing trailing 's'
    if var.endswith('s') and var[:-1] in entities:
        return var[:-1], len(entities[var[:-1]])

    # Special mappings for known mismatches
    special = {
        'conjecture': 'conjectures',
        'impossible_value': 'impossible_values',
        'unsolvable_problem': 'unsolvable_problems',
        'future_value': 'future_values',
        'future_date': 'future_dates',
        'nonexistent_property': 'nonexistent_properties',
        'mathematical_object': 'mathematical_objects',
        'infinite_set': 'infinite_sets',
        'ancient_event': 'ancient_events',
        'unpredictable_event': 'unpredictable_events',
        'impossible_measurement': 'impossible_measurements',
        'topic': 'topics',
        'physical_quantity': 'physical_quantities',
        'historical_event': 'historical_events',
        'geographic_feature': 'geographic_features',
        'event': 'events',
        'country': 'countries',
        'compound': 'compounds',
        'element': 'elements',
        'book': 'books',
        'invention': 'inventions',
    }
    if var in special and special[var] in entities:
        return special[var], len(entities[special[var]])

    # Check dict-based pools (option_pairs, concept_pairs)
    for pool_name, pool in entities.items():
        if pool and isinstance(pool[0], dict) and var in pool[0]:
            return f"{pool_name} (via {var})", len(pool)

    return None, 0


def analyze_category(category: str):
    """Analyze a single category's template variable usage vs entity pool sizes."""
    with open(TEMPLATES_DIR / f"{category}_templates.json") as f:
        templates = json.load(f)

    with open(ENTITIES_DIR / f"{category}_entities.json") as f:
        entities = json.load(f)

    # Count variable usage across templates
    var_usage = Counter()
    template_vars = []
    for t in templates:
        vars_in_t = re.findall(r'\{(\w+)\}', t)
        template_vars.append(vars_in_t)
        for v in vars_in_t:
            var_usage[v] += 1

    static_templates = sum(1 for tv in template_vars if len(tv) == 0)

    # Map each template variable to its entity pool
    var_to_pool = {}  # template_var -> (pool_key, pool_size)
    for tv_list in template_vars:
        for v in tv_list:
            if v not in var_to_pool:
                var_to_pool[v] = resolve_var_to_pool(v, entities)

    # Calculate combinatorial capacity per template
    template_capacities = []
    for i, (t, vars_in_t) in enumerate(zip(templates, template_vars)):
        if not vars_in_t:
            template_capacities.append((i, t[:60], 1, []))
            continue
        capacity = 1
        pool_info = []
        seen_pools = set()
        for v in vars_in_t:
            pool_key, pool_size = var_to_pool.get(v, (None, 0))
            # If two vars map to the same pool (e.g., two {country} references),
            # the second pick has one fewer option
            if pool_key in seen_pools:
                capacity *= max(pool_size - 1, 1)
            else:
                capacity *= max(pool_size, 1)
                seen_pools.add(pool_key)
            pool_info.append((v, pool_size))
        template_capacities.append((i, t[:60], capacity, pool_info))

    total_capacity = sum(cap for _, _, cap, _ in template_capacities)

    # Build pool analysis (deduplicate by pool key)
    pool_analysis = []
    seen_pools = {}  # pool_key -> analysis entry
    all_vars = set()
    for tv_list in template_vars:
        all_vars.update(tv_list)

    for var in sorted(all_vars):
        pool_key, pool_size = var_to_pool.get(var, (None, 0))
        display_name = f"{var} -> {pool_key}" if pool_key and pool_key != var else var
        if pool_key is None:
            display_name = f"{var} (UNMATCHED!)"

        times_used = var_usage[var]
        needs_expansion = pool_size < MIN_POOL_SIZE
        expand_to = MIN_POOL_SIZE if needs_expansion else pool_size
        new_needed = expand_to - pool_size if needs_expansion else 0

        pool_analysis.append({
            'variable': var,
            'pool_key': pool_key,
            'display': display_name,
            'current_size': pool_size,
            'templates_using': times_used,
            'needs_expansion': needs_expansion,
            'target_size': expand_to,
            'new_needed': new_needed,
        })

    pool_analysis.sort(key=lambda x: x['current_size'])

    # Also note entity pools that exist but aren't used by any template
    used_pool_keys = set(p['pool_key'] for p in pool_analysis if p['pool_key'])
    unused_pools = []
    for key in entities:
        # Check if this key is used (directly or via plural mapping)
        if key not in used_pool_keys:
            # Check if any var maps to this key
            mapped = any(pk == key for pk, _ in var_to_pool.values())
            if not mapped:
                unused_pools.append((key, len(entities[key])))

    return {
        'category': category,
        'n_templates': len(templates),
        'static_templates': static_templates,
        'total_capacity': total_capacity,
        'pool_analysis': pool_analysis,
        'template_capacities': template_capacities,
        'unused_pools': unused_pools,
        'naming_mismatches': [(v, pk) for v, (pk, _) in var_to_pool.items() if pk and pk != v and '(via' not in pk],
    }


def print_report(analysis):
    cat = analysis['category']
    print(f"\n{'='*70}")
    print(f"  {cat.upper()}")
    print(f"{'='*70}")
    print(f"  Templates: {analysis['n_templates']} ({analysis['static_templates']} static/hardcoded)")
    print(f"  Total combinatorial capacity: {analysis['total_capacity']:,} unique prompts")
    print(f"  Target: {TARGET_PROMPTS_PER_CATEGORY} prompts")
    ok = "YES" if analysis['total_capacity'] >= TARGET_PROMPTS_PER_CATEGORY else "NO"
    print(f"  Can reach target? {ok}")

    if analysis['naming_mismatches']:
        print(f"\n  NOTE: Template-to-pool naming mismatches (need to standardize):")
        for var, pool_key in analysis['naming_mismatches']:
            print(f"    template uses {{{var}}} -> pool key is '{pool_key}'")

    print(f"\n  {'Variable':<30s} {'Pool Key':<25s} {'Size':>5s}  {'Used':>4s}  {'Tgt':>4s}  {'Add':>4s}")
    print(f"  {'-'*30} {'-'*25} {'-'*5}  {'-'*4}  {'-'*4}  {'-'*4}")
    for p in analysis['pool_analysis']:
        marker = " ***" if p['needs_expansion'] else ""
        pk = str(p['pool_key'] or 'NONE')[:25]
        print(f"  {p['variable']:<30s} {pk:<25s} {p['current_size']:>5d}  {p['templates_using']:>4d}  {p['target_size']:>4d}  {p['new_needed']:>4d}{marker}")

    if analysis['unused_pools']:
        print(f"\n  Unused entity pools (exist in JSON but no template references them):")
        for key, size in analysis['unused_pools']:
            print(f"    '{key}' ({size} entities)")

    print(f"\n  Lowest-capacity templates:")
    bottlenecks = sorted(analysis['template_capacities'], key=lambda x: x[2])[:5]
    for idx, text, cap, pools in bottlenecks:
        pool_str = ", ".join(f"{v}({s})" for v, s in pools) if pools else "static"
        print(f"    [{cap:>5d}] {text}  | {pool_str}")

    total_new = sum(p['new_needed'] for p in analysis['pool_analysis'])
    n_expand = sum(1 for p in analysis['pool_analysis'] if p['needs_expansion'])
    print(f"\n  Pools needing expansion: {n_expand}")
    print(f"  Total new entities needed: {total_new}")


def main():
    print("ENTITY POOL EXPANSION ANALYSIS")
    print(f"Target: {TARGET_PROMPTS_PER_CATEGORY} prompts per category")
    print(f"Minimum pool size: {MIN_POOL_SIZE}")

    categories = ['factual', 'nonexistent', 'impossible', 'ambiguous']
    grand_total = 0

    for cat in categories:
        analysis = analyze_category(cat)
        print_report(analysis)
        grand_total += sum(p['new_needed'] for p in analysis['pool_analysis'])

    print(f"\n{'='*70}")
    print(f"GRAND TOTAL: {grand_total} new entities needed across all categories")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
