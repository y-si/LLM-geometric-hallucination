"""Audit the asserted-fake entity lists that Phase 0.5's ground truth rests on.

WHY THIS EXISTS. For the two categories carrying the Phase 0.5 decision surface, the
"ground truth" is not a verified fact. It is an assertion copied straight out of a
hand-curated list:

    data/entity_lists/borderline_plausible_fake_entities.json
    data/entity_lists/nonexistent_entities.json
        |
        v  src/pipeline/build_borderline_benchmark.py
    ground_truth = f"Fabricated entity: {entity}. Should refuse or indicate uncertainty."

There is NO verification step anywhere in that path. If a name on the list happens to
belong to something real, the benchmark asserts it is fabricated, and a model that
answers accurately about it is scored as HALLUCINATING.

THE PROJECT HAS ALREADY BEEN BURNED BY THIS. scripts/remove_ground_truth_errors.py
exists because "The Sapphire Coast" (a real tourism region in NSW, Australia) and
"Lake Meridian" (a real lake in Washington State) were mislabelled — its own docstring
says "All models 'hallucinated' because the ground truth was wrong." **That cleanup only
processed data/prompts/prompts.jsonl.** It never touched the standalone pool files, so
The Sapphire Coast re-entered the Phase 0.5 primary set through the §4.1 pool top-up and
is in the shipped manifest on 4 prompts. A one-off keyword patch does not survive a
change of data path; an audit of the source list does.

WHY THE ERROR IS EXACTLY THE SHAPE THAT CAN FAKE A NO-GO. A wrong ground truth is a
FIXED property of a prompt. Both odd and even split halves of a model see the same wrong
ground truth, so it does NOT depress that model's split-half reliability, so the §6.2
attenuation correction cannot remove it. But it lands on the two models UNEQUALLY: a
model that answers freely about the real entity is marked hallucinating, while a model
that hedges is marked correct. Prompt-specific, model-specific, uncorrected error is
precisely what depresses tau_cross.

Measured 2026-08-26, so this is settled rather than feared: dropping every problem class
found so far moves tau_corr from 0.310 to 0.323, and dropping the `people` subset moves
it DOWN to 0.256. **The ground-truth defects are real and block Phase 1, but they do not
explain the NO-GO.** Re-run --score after auditing to confirm that still holds.

WHAT CANNOT BE AUTOMATED. Deciding whether "Port Ashford" or "Cairn Loch" names
something real needs the open web, so this script does not pretend to decide. It
produces a PRIORITISED WORKSHEET — entities ranked by how much they actually affect the
estimate — and then recomputes the sensitivity once you have filled in verdicts.

Usage:
    python3 scripts/audit_ground_truth.py --worksheet   # build the audit worksheet
    # ... fill in the `verdict` column: real | fake | unsure
    python3 scripts/audit_ground_truth.py --score       # recompute tau without `real`

Output (results/phase05/ground_truth_audit/):
    worksheet.csv    one row per asserted-fake entity, ranked by impact
    audit.md         the risk triage and the sensitivity table
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "analyze_phase05", BASE_DIR / "scripts" / "analyze_phase05.py")
AP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AP)

MANIFEST_PATH = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"
ENTITIES_DIR = BASE_DIR / "data" / "entity_lists"
OUT_DIR = BASE_DIR / "results" / "phase05" / "ground_truth_audit"
WORKSHEET = OUT_DIR / "worksheet.csv"

FAKE_GT_PATTERNS = [
    re.compile(r"Fabricated entity: (.+?)\. Should refuse"),
]
PLACEHOLDER = re.compile(r"\[[a-z_0-9]+\]")

# Confirmed real by inspection 2026-08-26. Kept in the source so the finding is not
# lost, and so --score has a defensible default before any manual auditing happens.
CONFIRMED_REAL = {
    "The Sapphire Coast":
        "Real tourism region, New South Wales, Australia. Already known to this repo "
        "via scripts/remove_ground_truth_errors.py; that fix only cleaned "
        "prompts.jsonl, so it re-entered through the pool top-up.",
    "Tales from the Borderlands":
        "Real episodic video game (Telltale Games, 2014), set in the Borderlands "
        "franchise.",
    "The Silent Cartographer":
        "Real and well-known level in Halo: Combat Evolved (2001).",
}

# Structural risk classes. These are not verdicts — they are reasons an entity is
# unsafe to ASSERT fake, which is a different and lower bar than being real.
GENERIC_PERSON_TITLES = ("Dr.", "Professor", "Ambassador", "General", "Sir", "Colonel")


def read_jsonl(path):
    if not path.exists():
        sys.exit(f"missing input: {path}")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def entity_of(ground_truth):
    for pat in FAKE_GT_PATTERNS:
        m = pat.search(ground_truth or "")
        if m:
            return m.group(1)
    return None


def load_entity_types():
    """entity -> subset name, from the curated list the ground truth is copied from."""
    path = ENTITIES_DIR / "borderline_plausible_fake_entities.json"
    if not path.exists():
        return {}
    data = json.load(open(path))
    return {e: subset for subset, lst in data.items() for e in lst}


def risk_flags(entity, subset):
    """Why this entity is unsafe to assert fake. Not a claim that it IS real."""
    flags = []
    if entity in CONFIRMED_REAL:
        flags.append("CONFIRMED-REAL")
    if subset == "people":
        # The decisive one. A benchmark cannot assert that a human name belongs to
        # nobody: "Dr. Sarah Chen" and "Dr. Maria Rodriguez" certainly name real
        # people. The claim is unfalsifiable in the wrong direction, so a model that
        # answers about a plausible namesake cannot be scored wrong on this basis.
        flags.append("UNVERIFIABLE-AS-FAKE: human name")
    words = entity.replace("The ", "").split()
    if subset == "places" and len(words) <= 2:
        # Short toponyms collide with real geography constantly, and compound forms
        # ("Portsmith Narrows", "Mount Penrith") embed real base names that a model may
        # reasonably recognise.
        flags.append("HIGH-RISK: short toponym")
    if subset == "books" and len(words) <= 4:
        # Short evocative titles are the ones that turn out to be games, albums or
        # films — all three confirmed-real book entries are short.
        flags.append("HIGH-RISK: short title")
    return flags


def build_worksheet(out_path):
    manifest = read_jsonl(MANIFEST_PATH)
    prompts = AP.load_prompt_table()
    loaded = AP.load_judged(prompts)
    per_pair = AP.build_per_pair(prompts, loaded["records"])
    etypes = load_entity_types()

    by_entity = defaultdict(lambda: {"uids": [], "categories": Counter()})
    placeholder_rows = []
    for r in manifest:
        if not r.get("in_primary"):
            continue
        if PLACEHOLDER.search(r["question"]):
            placeholder_rows.append(r)
        ent = entity_of(r.get("ground_truth"))
        if ent is None:
            continue
        rec = by_entity[ent]
        rec["uids"].append(r["uid"])
        rec["categories"][r["category"]] += 1

    rows = []
    for ent, rec in by_entity.items():
        subset = etypes.get(ent, "unknown")
        pa, pb = [], []
        for u in rec["uids"]:
            for model, acc in ((AP.MODEL_A, pa), (AP.MODEL_B, pb)):
                v = per_pair.get((u, model), {}).get("p_hat")
                if v is not None and v == v:
                    acc.append(v)
        mean_a = sum(pa) / len(pa) if pa else float("nan")
        mean_b = sum(pb) / len(pb) if pb else float("nan")
        flags = risk_flags(ent, subset)
        rows.append({
            "entity": ent,
            "subset": subset,
            "n_primary_prompts": len(rec["uids"]),
            "mean_p_hat_llama": round(mean_a, 3) if mean_a == mean_a else "",
            "mean_p_hat_gptoss": round(mean_b, 3) if mean_b == mean_b else "",
            "model_gap": (round(mean_b - mean_a, 3)
                          if mean_a == mean_a and mean_b == mean_b else ""),
            "risk_flags": "; ".join(flags),
            # Impact ranking: a wrong ground truth matters in proportion to how many
            # prompts it touches AND how differently the two models behaved on it,
            # since a between-model gap is what actually moves tau_cross.
            "impact": round(len(rec["uids"]) * abs(mean_b - mean_a), 3)
                      if mean_a == mean_a and mean_b == mean_b else 0,
            "verdict": "real" if ent in CONFIRMED_REAL else "",
            "note": CONFIRMED_REAL.get(ent, ""),
            "uids": " ".join(sorted(rec["uids"])),
        })

    rows.sort(key=lambda r: (-r["impact"], r["entity"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)

    print(f"wrote {len(rows)} entities -> {out_path.relative_to(BASE_DIR)}")
    print()
    print("Risk triage:")
    tri = Counter()
    for r in rows:
        for fl in (r["risk_flags"].split("; ") if r["risk_flags"] else ["(no flag)"]):
            tri[fl] += 1
    for k, v in tri.most_common():
        print(f"  {v:4d}  {k}")
    print()
    print(f"Unsubstituted [placeholder] prompts in the primary set: "
          f"{len(placeholder_rows)}")
    for r in placeholder_rows[:5]:
        print(f"    {r['uid']}: {r['question']}")
    if len(placeholder_rows) > 5:
        print(f"    ... and {len(placeholder_rows) - 5} more")
    print()
    print("Next: open worksheet.csv, fill the `verdict` column with real | fake | "
          "unsure.")
    print("It is ranked by impact, so auditing the top ~30 rows captures most of the")
    print("effect. Then: python3 scripts/audit_ground_truth.py --score")
    return rows, placeholder_rows


def score(worksheet_path):
    if not worksheet_path.exists():
        sys.exit(f"no worksheet at {worksheet_path}. Run --worksheet first.")
    with open(worksheet_path) as f:
        rows = list(csv.DictReader(f))

    verdicts = Counter(r["verdict"].strip().lower() or "unaudited" for r in rows)
    real_ents = {r["entity"] for r in rows
                 if r["verdict"].strip().lower() == "real"}
    unsure_ents = {r["entity"] for r in rows
                   if r["verdict"].strip().lower() == "unsure"}

    prompts = AP.load_prompt_table()
    loaded = AP.load_judged(prompts)
    per_pair = AP.build_per_pair(prompts, loaded["records"])
    primary = sorted(u for u, p in prompts.items() if p["in_primary"])
    panel, _ = AP.make_panel("primary", primary, prompts, per_pair)

    manifest = {r["uid"]: r for r in read_jsonl(MANIFEST_PATH)}
    etypes = load_entity_types()

    def ent(u):
        return entity_of(manifest[u].get("ground_truth"))

    bad_placeholder = {u for u in panel.uids
                       if PLACEHOLDER.search(prompts[u]["question"])}
    people = {u for u in panel.uids
              if prompts[u]["category"] == "borderline_plausible_fake"
              and etypes.get(ent(u)) == "people"}

    variants = [
        ("ALL primary (the §7 estimate)", list(panel.uids)),
        ("minus entities you marked `real`",
         [u for u in panel.uids if ent(u) not in real_ents]),
        ("minus `real` and `unsure`",
         [u for u in panel.uids if ent(u) not in real_ents | unsure_ents]),
        ("minus unsubstituted [placeholder] prompts",
         [u for u in panel.uids if u not in bad_placeholder]),
        ("minus the `people` subset (unverifiable as fake)",
         [u for u in panel.uids if u not in people]),
        ("minus everything above",
         [u for u in panel.uids
          if ent(u) not in real_ents | unsure_ents
          and u not in bad_placeholder and u not in people]),
    ]

    L = []
    w = L.append
    w("# Ground-truth audit — Phase 0.5")
    w("")
    w("The ground truth for the decision-surface categories is an ASSERTION copied from")
    w("a hand-curated entity list, with no verification step:")
    w("")
    w("    data/entity_lists/*.json -> build_borderline_benchmark.py ->")
    w("    \"Fabricated entity: {entity}. Should refuse or indicate uncertainty.\"")
    w("")
    w("If a listed name belongs to something real, the benchmark asserts it is")
    w("fabricated and a model answering accurately is scored as hallucinating.")
    w("")
    w("## Audit coverage")
    w("")
    w("| Verdict | entities |")
    w("|---|---|")
    for k, v in verdicts.most_common():
        w(f"| {k} | {v} |")
    w("")
    if verdicts.get("unaudited"):
        w(f"> **{verdicts['unaudited']} entities are still unaudited.** The sensitivity")
        w("> table below is a lower bound on the defect's reach until they are checked.")
        w("")
    w("## Does it change the §7 verdict?")
    w("")
    w("A wrong ground truth is a fixed property of a prompt, so both split halves of a")
    w("model see it and it does NOT depress that model's reliability — meaning the §6.2")
    w("attenuation correction cannot remove it. It does land on the two models")
    w("unequally, which is exactly what depresses tau_cross. So this had to be tested,")
    w("not assumed benign.")
    w("")
    w("| Variant | n | tau_cross | tau_selfA | tau_selfB | tau_corr | clears GO? |")
    w("|---|---|---|---|---|---|---|")
    for label, uids in variants:
        if len(uids) < 40:
            w(f"| {label} | {len(uids)} | — | — | — | — | too few prompts |")
            continue
        e = AP.Panel("v", uids, prompts, per_pair).point_estimates()
        clears = (e["tau_corr"] == e["tau_corr"]
                  and e["tau_corr"] >= AP.GO_TAU_CORR)
        w(f"| {label} | {len(uids)} | {e['tau_cross']:+.3f} | {e['tau_selfA']:.3f} | "
          f"{e['tau_selfB']:.3f} | **{e['tau_corr']:+.3f}** | "
          f"{'**YES**' if clears else 'no'} |")
    w("")
    w(f"GO needs tau_corr >= {AP.GO_TAU_CORR}. If no row clears it, the ground-truth")
    w("defects are real and block Phase 1 but do not explain the NO-GO, and the §7")
    w("verdict stands on its own terms.")
    w("")
    w("## What is contaminated regardless of the verdict")
    w("")
    w("- **Absolute P-hat values / hallucination rates must not be quoted from this")
    w("  run.** Ordering may survive; the rates are computed against ground truth known")
    w("  to be wrong on some prompts.")
    w("- **Phase 1 is blocked** until the entity lists are verified. The `people`")
    w("  subset needs replacing outright, not checking: a benchmark cannot assert that")
    w("  a human name belongs to nobody.")
    w("- **The one-off keyword patch approach does not work.**")
    w("  `scripts/remove_ground_truth_errors.py` cleaned only `prompts.jsonl`, so")
    w("  The Sapphire Coast came back through the pool top-up. Fix the source lists.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = "\n".join(L)
    (OUT_DIR / "audit.md").write_text(report)
    print(report)
    print()
    print(f"wrote -> {(OUT_DIR / 'audit.md').relative_to(BASE_DIR)}")


def main():
    ap = argparse.ArgumentParser(description="Audit Phase 0.5 asserted-fake ground truth")
    ap.add_argument("--worksheet", action="store_true",
                    help="build the impact-ranked audit worksheet")
    ap.add_argument("--score", action="store_true",
                    help="recompute tau with audited entities excluded")
    ap.add_argument("--worksheet-path", type=Path, default=WORKSHEET)
    args = ap.parse_args()

    if args.worksheet:
        if args.worksheet_path.exists():
            sys.exit(f"{args.worksheet_path} already exists — rebuilding would discard "
                     "verdicts you have already filled in. Delete it deliberately if "
                     "that is what you want.")
        build_worksheet(args.worksheet_path)
    elif args.score:
        score(args.worksheet_path)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
