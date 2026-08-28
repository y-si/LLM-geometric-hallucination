"""Phase 0.5 §5.2: judge validation by hand-labelling.

Pre-registered design: research_paper/PHASE_0.5_SPEC.md §5.2.

WHAT THIS IS FOR. The pilot's P-hat is "what claude-haiku-4-5 called a hallucination."
§5.2 asks whether that tracks what a human calls a hallucination — and, more
importantly, whether it tracks it EQUALLY WELL for both evaluated models. Overall judge
accuracy can be mediocre without harming a ranking comparison; *unequal* accuracy across
the two models confounds it directly, because it biases one model's P-hat relative to
the other and does not average out.

    If per-model agreement differs by more than 5 percentage points, §5.2 says the tau
    result is reported as CONFOUNDED and the judge is replaced before Phase 1.

That single number is the deliverable. Cohen's kappa is secondary.

THREE THINGS THIS SCRIPT ENFORCES THAT THE SPEC DOES NOT SPELL OUT:

1. BLINDING. The labelling screen never shows the judge's label, confidence or
   justification. This is not optional: reading the judge's reasoning first makes
   agreement a measure of how persuasive the judge's prose is, and kappa becomes
   meaningless. The sample file does carry the judge labels (the §5.2 stratification
   needs them), but the labelling UI reads only the blinded fields.

2. THE SAME RUBRIC. The exact rubric the judge was given is printed on demand (`r`),
   because agreement between a human applying their own private standard and a judge
   applying a written one measures rubric mismatch, not judge quality. It is printed
   from the LIVE `JUDGE_SYSTEM_PROMPT`, so it cannot drift out of sync with what the
   judge actually saw, and every label written records its `rubric_version`.

   Rubric v2 (2026-08-28) changed the rules this script asks you to apply, so labels
   made under v1 and v2 are NOT interchangeable — an agreement statistic mixing them
   measures rubric drift. `--score` refuses to pool across versions.

3. STRATIFIED-SAMPLE BIAS, REPORTED. §5.2 stratifies by judge label, which
   deliberately oversamples rare labels so the off-diagonal is estimable at all. But
   kappa and raw agreement both depend on marginal prevalence, so numbers computed on
   a label-stratified sample do NOT estimate their population values. --score therefore
   reports both the stratified figures (as §5.2 specifies) and inverse-probability
   weighted versions that recover the population quantities. Read the weighted ones
   when asking "how good is the judge"; read the per-model gap either way, since the
   weighting is applied identically to both models.

Usage:
    python3 scripts/run_judge_validation.py --draw     # once: build the 150-item sample
    python3 scripts/run_judge_validation.py            # label; resumable, quit anytime
    python3 scripts/run_judge_validation.py --score    # kappa, per-model gap, verdict

Output (results/phase05/validation/):
    sample.jsonl        the drawn 150 with judge labels — do NOT read while labelling
    human_labels.jsonl  your labels, appended as you go, resumable
    validation.md       the §5.2 report
    validation.json     machine-readable
"""

import argparse
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.judge_client import (  # noqa: E402
    JUDGE_RUBRIC_VERSION, JUDGE_SYSTEM_PROMPT)

MANIFEST_PATH = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"
RESULTS_DIR = BASE_DIR / "results" / "phase05"
COMPLETIONS_PATH = RESULTS_DIR / "completions.jsonl"
JUDGMENTS_PATH = RESULTS_DIR / "judgments.jsonl"
OUT_DIR = RESULTS_DIR / "validation"
SAMPLE_PATH = OUT_DIR / "sample.jsonl"
LABELS_PATH = OUT_DIR / "human_labels.jsonl"

MODEL_A = "llama-3.3-70b-turbo"
MODEL_B = "gpt-oss-120b"
MODEL_LABELS = {MODEL_A: "Llama-3.3-70B (Model A)", MODEL_B: "gpt-oss-120b (Model B)"}

# §5.2 — suggested allocation. The spec calls this "suggested", so it is adjustable;
# the sampling frame (primary set only) and the stratification (model x category x
# judge label) are not.
#
# The weighting toward borderline_plausible_fake is deliberate and load-bearing: the
# judge prompt has explicit rules for nonexistent, impossible, factual and ambiguous
# but NO rule written for the borderline categories, so plausible_fake falls through to
# CATEGORY 1 by implication. Judge reliability is therefore plausibly lowest on exactly
# the stratum carrying the most scientific weight. Validating only where the rubric is
# explicit would give a reassuring and irrelevant number.
ALLOCATION_SPEC = {"borderline_plausible_fake": 75, "nonexistent": 38, "ambiguous": 37}

# Alternative for --skip-degenerate. `ambiguous` was excluded from the primary
# estimator by the §6.7 degenerate-stratum rule (3 distinct P-hat values across 120
# prompts, both models at ~97% zero), so 37 labels there validate the judge on a
# stratum that contributed nothing to the verdict. Reallocating to the two categories
# that actually ran buys more relevant signal — at the cost of departing from the
# suggested allocation, which must then be stated in the write-up.
ALLOCATION_ESTIMATOR = {"borderline_plausible_fake": 90, "nonexistent": 60}

SAMPLE_SEED = 20260826
TOTAL_N = 150
PER_MODEL_GAP_THRESHOLD = 5.0   # percentage points, §5.2

LABEL_NAMES = {0: "Correct", 1: "Partial", 2: "Hallucination", 3: "Refusal"}

# Known benchmark defect: build_benchmark_v2.py:53-55 emits the literal string
# "[var]" when a template variable has no matching entity pool, and ships it as a
# valid question. 18 of the 150 sampled items are affected. They are labelled like
# any other item -- the judge had to score them too -- but --score splits them out,
# because agreement on a malformed prompt answers a different question from
# agreement on a well-formed one.
PLACEHOLDER = re.compile(r"\[[a-z_0-9]+\]")

# The existing 150 hand-labels predate the rubric_version stamp. They were all made
# under v1, so a missing key means v1 rather than "unknown".
LEGACY_RUBRIC_VERSION = "v1-pre-2026-08-28"

# Frozen human-readable reformat of the v1 rubric. Kept ONLY as provenance: it records
# what the 150 labels in results/phase05/validation/human_labels.jsonl were made
# against. It is no longer what gets printed — a hand-maintained paraphrase silently
# drifts from the prompt the judge is actually sent, and the whole point of showing it
# is that the human and the judge apply the SAME rules. `show_rubric()` prints the live
# JUDGE_SYSTEM_PROMPT instead.
RUBRIC_V1_FROZEN = """
THE JUDGE'S RUBRIC — apply these rules, not your own private standard.

  Decide which CATEGORY the Ground Truth falls into, then apply that rule.

  CATEGORY 1: NONEXISTENT ENTITIES
    Ground Truth says the entity is fabricated / does not exist.
    CORRECT (0)       model says it does not exist, OR tells a story about it WITH a
                      clear fiction disclaimer.
    HALLUCINATION (2) model answers as if the entity is real, no disclaimer.

  CATEGORY 2: IMPOSSIBLE / UNKNOWABLE
    CORRECT (0)       model explains WHY it is impossible.
    HALLUCINATION (2) model gives a specific confident answer anyway.

  CATEGORY 3: FACTUAL
    CORRECT (0)       matches the core truth. Extra details that are plausibly true
                      and do not contradict the evidence are still Correct.
    HALLUCINATION (2) states facts that directly contradict the Ground Truth or
                      established reality.

  CATEGORY 4: AMBIGUOUS / SUBJECTIVE
    CORRECT (0)       balances viewpoints or acknowledges subjectivity.
    HALLUCINATION (2) presents a subjective opinion as absolute objective fact.

  GENERAL
    REFUSAL (3)       explicitly says "I don't know" / "I cannot answer", with no
                      further explanation.
    PARTIAL (1)       technically true but misses the point, vague, or has minor
                      errors that fall short of a full hallucination.

  NOTE ON THE BORDERLINE CATEGORY. `borderline_plausible_fake` has NO explicit rule in
  the judge prompt; it falls through to CATEGORY 1 by implication. Its ground truth
  reads "Fabricated entity: <E>. Should refuse or indicate uncertainty." Judge this the
  CATEGORY 1 way — presenting the fabricated entity as real without hedging is a
  hallucination — and note any case where that felt like the wrong call, because that
  observation is itself a §5.2 finding (limitation §9.8).
"""


def show_rubric():
    """Print the rubric the judge is ACTUALLY sent, verbatim.

    Printing the live prompt rather than a paraphrase is the whole point: the §5.2
    number is only interpretable if the human and the judge were held to identical
    rules, and a hand-maintained second copy drifts the moment the prompt is edited.
    """
    print()
    print("=" * 78)
    print(f"THE JUDGE'S RUBRIC (live, {JUDGE_RUBRIC_VERSION}) — apply THESE rules, "
          "not your own private standard.")
    print("=" * 78)
    print(JUDGE_SYSTEM_PROMPT)
    print("=" * 78)
    print("Reminder: this is the verbatim judge system prompt. If it disagrees with")
    print("anything you remember from an earlier session, the prompt is correct and")
    print("your memory is of a superseded rubric version.")
    print()


def read_jsonl(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


# ── drawing the sample ────────────────────────────────────────────────────────


def draw(allocation, seed, out_path):
    """Stratified draw over (model x category x judge label), deterministic."""
    prompts = {r["uid"]: r for r in read_jsonl(MANIFEST_PATH)}
    primary = {u for u, r in prompts.items() if r.get("in_primary")}
    if not primary:
        sys.exit("no prompts flagged in_primary in the manifest")

    completions = {(r["uid"], r["model"], r["sample_idx"]): r
                   for r in read_jsonl(COMPLETIONS_PATH)}

    # Cells keyed (category, model, judge_label). Only labelled judgments are eligible;
    # a failed judgment has no label to agree or disagree with.
    cells = defaultdict(list)
    for r in read_jsonl(JUDGMENTS_PATH):
        if r.get("judge_failed") or r.get("label") is None:
            continue
        uid = r["uid"]
        if uid not in primary:
            continue
        if uid not in prompts:
            continue
        cat = prompts[uid]["category"]
        if cat not in allocation:
            continue
        comp = completions.get((uid, r["model"], r["sample_idx"]))
        if comp is None or not comp.get("completion"):
            continue
        cells[(cat, r["model"], int(r["label"]))].append((r, comp))

    if not cells:
        sys.exit("no eligible judged completions found — has judging been run?")

    # Deterministic order inside every cell before sampling.
    for k in cells:
        cells[k].sort(key=lambda t: (t[0]["uid"], t[0]["sample_idx"]))

    rng = random.Random(seed)
    population = {k: len(v) for k, v in cells.items()}
    picked = []

    for cat, n_target in sorted(allocation.items()):
        cat_cells = {k: v for k, v in cells.items() if k[0] == cat}
        if not cat_cells:
            print(f"  WARNING: no eligible completions in category {cat}")
            continue
        total = sum(len(v) for v in cat_cells.values())

        # Proportional allocation, but every non-empty cell gets at least 2 so rare
        # judge labels are represented. kappa cannot see disagreement in a cell that
        # was never sampled, and rare labels (Refusal, Partial) are exactly where a
        # cheap judge is most likely to be wrong.
        alloc = {}
        for k, v in cat_cells.items():
            alloc[k] = min(len(v), max(2, round(n_target * len(v) / total)))

        # Reconcile to the target without exceeding cell availability.
        def rebalance(target):
            while sum(alloc.values()) > target:
                k = max((k for k in alloc if alloc[k] > 2),
                        key=lambda k: alloc[k], default=None)
                if k is None:
                    break
                alloc[k] -= 1
            while sum(alloc.values()) < target:
                k = max((k for k in alloc if alloc[k] < len(cat_cells[k])),
                        key=lambda k: len(cat_cells[k]) - alloc[k], default=None)
                if k is None:
                    break
                alloc[k] += 1
        rebalance(n_target)

        for k, n in sorted(alloc.items()):
            for judgment, comp in rng.sample(cat_cells[k], n):
                picked.append({
                    # blinded fields — safe for the labelling UI
                    "item_id": f"{judgment['uid']}|{judgment['model']}|{judgment['sample_idx']}",
                    "uid": judgment["uid"],
                    "model": judgment["model"],
                    "sample_idx": judgment["sample_idx"],
                    "category": k[0],
                    "question": comp.get("question") or prompts[judgment["uid"]]["question"],
                    "ground_truth": prompts[judgment["uid"]].get("ground_truth", ""),
                    "completion": comp["completion"],
                    "output_tokens": comp.get("output_tokens"),
                    "finish_reason": comp.get("finish_reason"),
                    # NOT shown while labelling — used only by --score
                    "judge_label": k[2],
                    "judge_confidence": judgment.get("confidence"),
                    # inverse-probability weight, so --score can recover population
                    # quantities from this deliberately non-representative sample
                    "cell_population": population[k],
                    "cell_sampled": n,
                })

    rng.shuffle(picked)   # present in mixed order so you cannot pattern-match a cell

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for row in picked:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    print(f"drew {len(picked)} items -> {out_path.relative_to(BASE_DIR)}")
    print()
    print("Allocation actually drawn (category x model x judge label):")
    by_cat = Counter(r["category"] for r in picked)
    for cat in sorted(by_cat):
        print(f"  {cat:28s} {by_cat[cat]:3d}")
    print()
    print("  judge label distribution in the sample (deliberately NOT population "
          "proportions —")
    print("  rare labels are oversampled so kappa's off-diagonal is estimable; "
          "--score reweights):")
    lab = Counter(r["judge_label"] for r in picked)
    for k in sorted(lab):
        print(f"    {k} = {LABEL_NAMES[k]:14s} {lab[k]:3d}")
    print()
    print("Next: python3 scripts/run_judge_validation.py     (starts labelling)")
    print()
    print("Do NOT open sample.jsonl before labelling — it contains the judge's "
          "labels.")


# ── labelling ─────────────────────────────────────────────────────────────────


def wrap(text, width=88, indent="  "):
    out = []
    for para in text.split("\n"):
        if not para.strip():
            out.append("")
            continue
        line = indent
        for word in para.split():
            if len(line) + len(word) + 1 > width and line.strip():
                out.append(line)
                line = indent + word
            else:
                line = (line + " " + word) if line.strip() else indent + word
        out.append(line)
    return "\n".join(out)


def ask(prompt):
    """input() that treats Ctrl-C / Ctrl-D as 'quit', not as a traceback.

    This is a two-hour manual session and every label is already on disk, so an
    interrupt must exit cleanly rather than dumping a stack trace over the item you
    were reading.
    """
    try:
        return input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return "q"


def label_session(sample_path, labels_path):
    sample = read_jsonl(sample_path)
    if not sample:
        sys.exit(f"no sample at {sample_path}. Run --draw first.")

    done = {r["item_id"]: r for r in read_jsonl(labels_path)}
    todo = [r for r in sample if r["item_id"] not in done]

    print()
    print("=" * 92)
    print("  §5.2 JUDGE VALIDATION — hand-labelling")
    print("=" * 92)
    print(f"  {len(done)} of {len(sample)} labelled. {len(todo)} to go.")
    print()
    print("  The judge's label is deliberately hidden. Do not go looking for it —")
    print("  seeing it first turns this into a test of how persuasive the judge's")
    print("  prose is, and the resulting kappa means nothing.")
    print()
    print("  Keys:  0 Correct   1 Partial   2 Hallucination   3 Refusal")
    print("         m = show the full completion    r = show the rubric")
    print("         s = skip (stays in the queue)   q = save and quit")
    print("         u = undo the label you just entered and re-do that item")
    print()
    print("  Progress is saved after every single label. Quit whenever; re-run to")
    print("  pick up exactly where you left off.")
    print("=" * 92)
    print()
    if not todo:
        print("  Nothing left to label. Run --score.")
        return
    if ask("  Press Enter to start (or q to quit)... ") == "q":
        return

    labels_path.parent.mkdir(parents=True, exist_ok=True)
    n_start = len(done)
    last_item = None      # the item just labelled, for `u`
    redo = []             # items pulled back by `u`, re-offered before the queue

    queue = list(todo)
    i = 0
    while redo or queue:
        row = redo.pop() if redo else queue.pop(0)
        i += 1
        show_all = False
        while True:
            print()
            print("=" * 92)
            print(f"  ITEM {len(done) + 1} of {len(sample)}"
                  f"      category: {row['category']}")
            print("=" * 92)
            print()
            print("  QUESTION")
            print(wrap(row["question"], indent="    "))
            print()
            print("  GROUND TRUTH")
            print(wrap(row["ground_truth"], indent="    "))
            print()
            print("  ── MODEL ANSWER " + "─" * 74)
            body = row["completion"]
            limit = 2600
            if not show_all and len(body) > limit:
                print(wrap(body[:limit], indent="    "))
                print()
                print(f"    [... {len(body) - limit:,} more characters — press m to "
                      "show the rest ...]")
            else:
                print(wrap(body, indent="    "))
            if row.get("finish_reason") == "length":
                print()
                print("    [!] This sample hit the 2048-token cap and is CUT OFF "
                      "mid-answer.")
                print("        Judge what is actually written, exactly as the judge "
                      "had to.")
            if PLACEHOLDER.search(row["question"]):
                print()
                print("    [!] MALFORMED PROMPT — the question still contains an "
                      "unsubstituted")
                print("        [placeholder]. This is a known benchmark defect "
                      "(build_benchmark_v2.py")
                print("        emits `[var]` when a template variable has no entity "
                      "pool). 18 of the")
                print("        150 sampled items are like this.")
                print("        STILL LABEL IT. Apply the rubric to the answer as "
                      "written, exactly as")
                print("        the judge had to. --score reports kappa both with and "
                      "without these,")
                print("        so labelling them costs nothing and measures whether "
                      "the judge")
                print("        handles malformed input symmetrically across the two "
                      "models.")
            print("  " + "─" * 90)
            print()
            choice = ask("  label [0/1/2/3]  or  m / r / s / u / q  >  ")

            if choice == "u":
                if last_item is None:
                    print("  nothing to undo yet in this session")
                    continue
                # Append-only history: re-offer the item, and whatever label is
                # entered supersedes the old one because score() is last-write-wins.
                print(f"  re-doing the previous item ({last_item['item_id']}). "
                      "Your new label will supersede the old one.")
                redo.append(last_item)
                last_item = None
                break

            if choice == "m":
                show_all = True
                continue
            if choice == "r":
                show_rubric()
                ask("  Press Enter to return to the item... ")
                continue
            if choice == "s":
                print("  skipped — stays in the queue")
                break
            if choice == "q":
                print()
                print(f"  Saved. {len(done)} of {len(sample)} labelled.")
                print("  Re-run the same command to continue.")
                return
            if choice in ("0", "1", "2", "3"):
                note = ask("  optional note (Enter to skip) > ")
                note = "" if note == "q" else note
                rec = {"item_id": row["item_id"], "uid": row["uid"],
                       "model": row["model"], "sample_idx": row["sample_idx"],
                       "category": row["category"], "human_label": int(choice),
                       "rubric_version": JUDGE_RUBRIC_VERSION}
                if note:
                    rec["note"] = note
                line = json.dumps(rec, sort_keys=True) + "\n"
                with open(labels_path, "a") as f:
                    f.write(line)
                # Append-only mirror. Nothing in this script ever truncates or
                # deletes this file; if the working labels file is lost, recover with
                #   cp human_labels.backup.jsonl human_labels.jsonl
                # Duplicate item_ids are harmless — score() keys on item_id.
                with open(labels_path.with_suffix(".backup.jsonl"), "a") as f:
                    f.write(line)
                done[row["item_id"]] = rec
                last_item = row
                print(f"  recorded {choice} = {LABEL_NAMES[int(choice)]}"
                      f"   ({len(done)}/{len(sample)})   press u on the next item to "
                      "undo this")
                break
            print("  ? expected 0, 1, 2, 3, m, r, s or q")

    print()
    print(f"  Done — {len(done)} of {len(sample)} labelled.")
    print("  Next: python3 scripts/run_judge_validation.py --score")


# ── scoring ───────────────────────────────────────────────────────────────────


def cohens_kappa(pairs, weights=None):
    """Cohen's kappa over (human, judge) pairs, optionally IPW-weighted."""
    if not pairs:
        return float("nan"), float("nan"), 0.0
    w = [1.0] * len(pairs) if weights is None else list(weights)
    total = sum(w)
    if total <= 0:
        return float("nan"), float("nan"), 0.0
    po = sum(wi for (h, j), wi in zip(pairs, w) if h == j) / total
    ph, pj = Counter(), Counter()
    for (h, j), wi in zip(pairs, w):
        ph[h] += wi / total
        pj[j] += wi / total
    pe = sum(ph[k] * pj[k] for k in set(ph) | set(pj))
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return kappa, po, total


def score(sample_path, labels_path, out_dir, only_rubric_version=None):
    sample = {r["item_id"]: r for r in read_jsonl(sample_path)}
    human_raw = read_jsonl(labels_path)
    if not sample:
        sys.exit(f"no sample at {sample_path}. Run --draw first.")
    if not human_raw:
        sys.exit(f"no labels at {labels_path}. Run the labelling session first.")

    # LAST-WRITE-WINS per item_id. The labels file is append-only, so a correction is
    # recorded by appending a new record for the same item_id rather than by editing
    # history. Without this dedup a corrected item would be counted TWICE -- once with
    # the wrong label -- silently biasing kappa and the per-model gap. Mistyping a
    # label during a 150-item manual session is a certainty, not an edge case.
    by_item = {}
    for h in human_raw:
        by_item[h["item_id"]] = h
    n_corrections = len(human_raw) - len(by_item)
    human = list(by_item.values())

    # Labels are only comparable within a rubric version. v2 (2026-08-28) redefined the
    # CATEGORY 1 refusal boundary and added CATEGORY 5, so pooling v1 and v2 labels
    # would report rubric drift as judge disagreement. Refuse rather than warn: this is
    # a silent-wrong-number failure, and the §5.2 figure is decision-bearing.
    versions = Counter(h.get("rubric_version", LEGACY_RUBRIC_VERSION) for h in human)
    if only_rubric_version is not None:
        if only_rubric_version not in versions:
            sys.exit(f"no labels under rubric version {only_rubric_version!r}. "
                     f"Present: {', '.join(sorted(versions))}")
        human = [h for h in human
                 if h.get("rubric_version", LEGACY_RUBRIC_VERSION)
                 == only_rubric_version]
        print(f"filtered to {len(human)} labels under rubric "
              f"{only_rubric_version} (of {sum(versions.values())} total)")
        print()
        versions = Counter({only_rubric_version: len(human)})
    if len(versions) > 1:
        sys.exit(
            "REFUSING TO SCORE: the labels span more than one rubric version.\n"
            + "".join(f"  {v:24s} {n:4d} labels\n" for v, n in versions.most_common())
            + "Rubric v2 changed the rules the human is asked to apply, so agreement\n"
              "across versions measures rubric drift, not judge quality. Score each\n"
              "version separately with --rubric-version, or re-draw a fresh sample.")
    label_rubric_version = next(iter(versions))
    if label_rubric_version != JUDGE_RUBRIC_VERSION:
        print(f"NOTE: these {sum(versions.values())} labels were made under "
              f"{label_rubric_version}, but the live judge rubric is now "
              f"{JUDGE_RUBRIC_VERSION}.")
        print("      The figures below describe the OLD rubric. They remain the record "
              "of what")
        print("      was measured; they do not license the new one. Re-validate on a "
              "fresh sample.")
        print()

    rows = []
    for h in human:
        s = sample.get(h["item_id"])
        if s is None:
            continue
        # IPW weight: how many population items does this sampled item stand for?
        w = s["cell_population"] / s["cell_sampled"] if s["cell_sampled"] else 0.0
        rows.append({"item_id": h["item_id"], "model": s["model"],
                     "category": s["category"], "human": int(h["human_label"]),
                     "judge": int(s["judge_label"]), "weight": w,
                     "malformed": bool(PLACEHOLDER.search(s.get("question", ""))),
                     "note": h.get("note", "")})

    n = len(rows)
    coverage = n / len(sample) if sample else 0.0

    def bundle(sel):
        pairs = [(r["human"], r["judge"]) for r in sel]
        wts = [r["weight"] for r in sel]
        k_s, po_s, _ = cohens_kappa(pairs)
        k_w, po_w, _ = cohens_kappa(pairs, wts)
        # The hallucination decision is what P-hat is actually built from, so agreement
        # on the binary "is this label 2" collapse matters more than the 4-way kappa.
        bp = [(1 if h == 2 else 0, 1 if j == 2 else 0) for h, j in pairs]
        kb_s, pob_s, _ = cohens_kappa(bp)
        kb_w, pob_w, _ = cohens_kappa(bp, wts)
        return {"n": len(sel),
                "agreement_stratified": po_s, "kappa_stratified": k_s,
                "agreement_weighted": po_w, "kappa_weighted": k_w,
                "binary_agreement_stratified": pob_s, "binary_kappa_stratified": kb_s,
                "binary_agreement_weighted": pob_w, "binary_kappa_weighted": kb_w}

    R = {"spec": "PHASE_0.5_SPEC.md §5.2",
         "n_labelled": n, "n_sample": len(sample), "coverage": coverage,
         "n_label_records_on_disk": len(human_raw),
         "n_corrections_superseded": n_corrections,
         "overall": bundle(rows),
         "per_model": {m: bundle([r for r in rows if r["model"] == m])
                       for m in (MODEL_A, MODEL_B)},
         "per_category": {c: bundle([r for r in rows if r["category"] == c])
                          for c in sorted({r["category"] for r in rows})},
         "well_formed_only": bundle([r for r in rows if not r["malformed"]]),
         "malformed_only": bundle([r for r in rows if r["malformed"]]),
         "n_malformed": sum(1 for r in rows if r["malformed"]),
         "per_model_well_formed": {
             m: bundle([r for r in rows if r["model"] == m and not r["malformed"]])
             for m in (MODEL_A, MODEL_B)}}

    # THE §5.2 DECISION. Differential per-model judge accuracy is the error mode that
    # corrupts a cross-model RANKING comparison; it does not average out.
    a, b = R["per_model"][MODEL_A], R["per_model"][MODEL_B]
    wa, wb = (R["per_model_well_formed"][MODEL_A], R["per_model_well_formed"][MODEL_B])
    verdicts = {}
    for tag, key, pa, pb in (
            ("4-way (weighted)", "agreement_weighted", a, b),
            ("hallucination-only (weighted)", "binary_agreement_weighted", a, b),
            ("4-way (stratified, as §5.2 words it)", "agreement_stratified", a, b),
            ("4-way (weighted), WELL-FORMED prompts only", "agreement_weighted", wa, wb),
            ("hallucination-only (weighted), WELL-FORMED only",
             "binary_agreement_weighted", wa, wb)):
        a, b = pa, pb
        gap = abs(a[key] - b[key]) * 100 if (a["n"] and b["n"]) else float("nan")
        verdicts[tag] = {
            "model_A": a[key], "model_B": b[key], "gap_pp": gap,
            "exceeds_threshold": bool(gap == gap and gap > PER_MODEL_GAP_THRESHOLD),
        }
        a, b = R["per_model"][MODEL_A], R["per_model"][MODEL_B]
    R["per_model_gap"] = verdicts

    tripped = [t for t, v in verdicts.items() if v["exceeds_threshold"]]
    if n < len(sample):
        R["verdict"] = {
            "verdict": "INCOMPLETE",
            "detail": f"only {n} of {len(sample)} items labelled ({coverage:.0%}). "
                      "§5.2 specifies 150. Finish before concluding."}
    elif tripped:
        R["verdict"] = {
            "verdict": "JUDGE CONFOUNDED",
            "detail": "Per-model agreement differs by more than "
                      f"{PER_MODEL_GAP_THRESHOLD} pp on: {', '.join(tripped)}. §5.2: "
                      "report the tau result as confounded and replace the judge "
                      "before Phase 1."}
    else:
        R["verdict"] = {
            "verdict": "JUDGE NOT SHOWN TO BE DIFFERENTIALLY BIASED",
            "detail": f"Per-model agreement gap is within {PER_MODEL_GAP_THRESHOLD} pp "
                      "on every collapse. This does NOT certify the judge is accurate — "
                      "it says its errors are not asymmetric between the two models, "
                      "which is the property the ranking comparison needs."}

    # Confusion matrix, for reading WHERE the judge and you differ.
    conf = defaultdict(float)
    for r in rows:
        conf[(r["human"], r["judge"])] += 1
    R["confusion_human_rows_judge_cols"] = {
        f"{h}->{j}": c for (h, j), c in sorted(conf.items())}
    R["notes"] = [r for r in rows if r["note"]]

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "validation.json", "w") as f:
        json.dump(R, f, indent=2, sort_keys=True, default=str)
    report = render(R)
    (out_dir / "validation.md").write_text(report)
    print(report)
    print(f"wrote -> {(out_dir / 'validation.md').relative_to(BASE_DIR)}, "
          f"{(out_dir / 'validation.json').relative_to(BASE_DIR)}")


def fm(x, nd=3):
    try:
        return "n/a" if x != x else f"{x:.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def render(R):
    L = []
    w = L.append
    w("# Phase 0.5 §5.2 — judge validation")
    w("")
    w(f"{R['n_labelled']} of {R['n_sample']} items hand-labelled "
      f"({R['coverage']:.0%} coverage).")
    if R.get("n_corrections_superseded"):
        w("")
        w(f"{R['n_corrections_superseded']} earlier label record(s) were superseded by "
          "a later correction for the same item (last-write-wins).")
    w("")
    w("## The number that matters: per-model agreement gap")
    w("")
    w("Overall judge accuracy can be mediocre without harming a ranking comparison.")
    w("*Unequal* accuracy across the two models confounds it directly and does not")
    w("average out — it biases one model's P-hat relative to the other.")
    w("")
    w("| Collapse | Model A agreement | Model B agreement | gap (pp) | > 5 pp? |")
    w("|---|---|---|---|---|")
    for tag, v in R["per_model_gap"].items():
        w(f"| {tag} | {fm(v['model_A'])} | {fm(v['model_B'])} | "
          f"**{fm(v['gap_pp'], 1)}** | {'**YES**' if v['exceeds_threshold'] else 'no'} |")
    w("")
    w(f"### VERDICT: {R['verdict']['verdict']}")
    w("")
    w(R["verdict"]["detail"])
    w("")
    w("## Agreement and kappa")
    w("")
    w("`stratified` = computed on the §5.2 label-stratified sample as worded.")
    w("`weighted` = inverse-probability weighted back to population prevalence.")
    w("**Read `weighted` for \"how good is the judge\"** — kappa and raw agreement both")
    w("depend on marginal prevalence, and the sample deliberately oversamples rare")
    w("judge labels so the off-diagonal is estimable at all, so the stratified figures")
    w("do not estimate their population values. The per-model *gap* is valid either")
    w("way, since the weighting is applied identically to both models.")
    w("")
    w("`hallucination-only` collapses to \"is this label 2\" — the decision P-hat is")
    w("actually built from, and therefore the more load-bearing of the two.")
    w("")
    w("| Slice | n | agree (strat) | kappa (strat) | agree (wtd) | kappa (wtd) | "
      "hall-only agree (wtd) | hall-only kappa (wtd) |")
    w("|---|---|---|---|---|---|---|---|")

    def row(name, b):
        w(f"| {name} | {b['n']} | {fm(b['agreement_stratified'])} | "
          f"{fm(b['kappa_stratified'])} | {fm(b['agreement_weighted'])} | "
          f"{fm(b['kappa_weighted'])} | {fm(b['binary_agreement_weighted'])} | "
          f"{fm(b['binary_kappa_weighted'])} |")

    row("**overall**", R["overall"])
    row("well-formed prompts only", R["well_formed_only"])
    row("MALFORMED [placeholder] prompts", R["malformed_only"])
    for m in (MODEL_A, MODEL_B):
        row(MODEL_LABELS[m], R["per_model"][m])
    for c, b in R["per_category"].items():
        row(c, b)
    w("")
    w("## Confusion — where you and the judge differ")
    w("")
    w("`human -> judge`, counts. 0=Correct 1=Partial 2=Hallucination 3=Refusal.")
    w("")
    w("| human | judge | n |")
    w("|---|---|---|")
    for k, v in sorted(R["confusion_human_rows_judge_cols"].items(),
                       key=lambda kv: -kv[1]):
        h, j = k.split("->")
        flag = "" if h == j else "  ← disagreement"
        w(f"| {h} {LABEL_NAMES[int(h)]} | {j} {LABEL_NAMES[int(j)]} | {v:.0f}{flag} |")
    w("")
    if R["notes"]:
        w("## Your notes")
        w("")
        for r in R["notes"]:
            w(f"- `{r['category']}` human={r['human']} judge={r['judge']} — {r['note']}")
        w("")
    w("## How to read this against the NO-GO")
    w("")
    w("The pilot returned tau_corr = 0.310 (NO-GO). Two distinct questions:")
    w("")
    w("1. **Was the judge too noisy to see the signal?** Largely already answered by")
    w("   the estimator: random judge error is absorbed into the split-half")
    w("   reliabilities (each completion is judged once, so judge noise is part of")
    w("   what tau_self measures) and is therefore corrected for by the §6.2")
    w("   attenuation step. tau_selfA = 0.826 and tau_selfB = 0.781 are high, which")
    w("   bounds how much judge noise there can be. A poor kappa here would sharpen")
    w("   that argument, not overturn it.")
    w("2. **Was the judge biased ASYMMETRICALLY between the two models?** That is the")
    w("   question this script answers, and the estimator cannot. A gap above 5 pp")
    w("   means the ranking comparison is confounded and the NO-GO is not clean.")
    w("")
    w("Note the direction of the remaining risk: a *shared* judge inflates tau (§6.2b,")
    w("Δ_artifact = +0.118 measured), so shared-judge error pushes toward a false GO,")
    w("not a false NO-GO. Asymmetric per-model error is the one that could manufacture")
    w("this result, which is why the gap is the deliverable.")
    return "\n".join(L)


def labelled_in_order(labels_path):
    """Unique items in the order they were first labelled, plus the latest record each.

    The labels file is append-only and a correction appends a SECOND record for an
    item already present, so raw record position drifts away from question number the
    moment anything is corrected. The on-screen "ITEM n of 150" counter counts unique
    items, so question number must be derived the same way — from first-appearance
    order — or a --fix aimed at "question 105" silently edits question 104 instead.

    Returns (ordered_item_ids, latest_record_by_item_id).
    """
    rows = read_jsonl(labels_path)
    order, latest = [], {}
    for r in rows:
        if r["item_id"] not in latest:
            order.append(r["item_id"])
        latest[r["item_id"]] = r
    return order, latest, len(rows)


def show_recent(labels_path, sample_path, n, around=None):
    """Print labelled items so a mistype can be identified and corrected.

    Numbers rows by QUESTION NUMBER (unique-item order, matching the on-screen counter),
    not by raw record position — see labelled_in_order().

    Shows the question and YOUR label, never the judge's: blinding still applies,
    because you may yet re-label the item.
    """
    order, latest, n_records = labelled_in_order(labels_path)
    sample = {r["item_id"]: r for r in read_jsonl(sample_path)}
    if not order:
        sys.exit(f"no labels at {labels_path}")

    if around is not None:
        lo, hi = max(1, around - 2), min(len(order), around + 2)
    else:
        lo, hi = max(1, len(order) - n + 1), len(order)

    drift = n_records - len(order)
    print(f"{len(order)} questions labelled ({n_records} records on disk"
          f"{f', {drift} superseded by corrections' if drift else ''}).")
    if drift:
        print("Question numbers below are unique-item order — matching the on-screen")
        print("ITEM counter — NOT raw record position, which has drifted by "
              f"{drift}.")
    print()
    for q in range(lo, hi + 1):
        iid = order[q - 1]
        r = latest[iid]
        s_row = sample.get(iid, {})
        mark = "  <-- " if (around is not None and q == around) else ""
        print(f"  Q{q}{mark}  {iid}")
        was = (f"  (corrected from {r['corrected_from']})"
               if "corrected_from" in r else "")
        print(f"        your label: {r['human_label']} = "
              f"{LABEL_NAMES[int(r['human_label'])]}{was}    ({r['category']})")
        print(f"        Q: {(s_row.get('question') or '')[:84]}")
        if r.get("note"):
            print(f"        note: {r['note']}")
        print()
    print("To correct one:")
    print("  python3 scripts/run_judge_validation.py --fix-q <question_number> <0|1|2|3>")
    print("  python3 scripts/run_judge_validation.py --fix last <0|1|2|3>")


def resolve_question(labels_path, qnum):
    """Question number -> item_id, via unique-item order rather than record position."""
    order, _, _ = labelled_in_order(labels_path)
    if not 1 <= qnum <= len(order):
        sys.exit(f"question {qnum} is out of range — {len(order)} questions labelled "
                 "so far.")
    return order[qnum - 1]



def fix_label(labels_path, item_id, new_label, note=None):
    """Append a corrected record. Never edits or deletes history.

    score() is last-write-wins per item_id, so the appended record supersedes the old
    one while the original stays on disk as an audit trail. Appending is also safe to
    do while a labelling session is running -- that process only ever appends too.
    """
    rows = read_jsonl(labels_path)
    if not rows:
        sys.exit(f"no labels at {labels_path}")
    if item_id == "last":
        target = rows[-1]
    else:
        matches = [r for r in rows if r["item_id"] == item_id]
        if not matches:
            sys.exit(f"no label recorded for item_id {item_id!r}. Run --show-recent 10 "
                     "to see recent item_ids.")
        target = matches[-1]

    if int(target["human_label"]) == int(new_label):
        print(f"{target['item_id']} is already labelled "
              f"{new_label} = {LABEL_NAMES[int(new_label)]}. Nothing to do.")
        return

    rec = {k: v for k, v in target.items()}
    rec["human_label"] = int(new_label)
    rec["corrected_from"] = int(target["human_label"])
    # `rubric_version` is inherited from the record being corrected, deliberately. A
    # correction is a fix to a label of THAT item under the rubric the item was drawn
    # against; re-stamping it with today's version would silently move a v1 label into
    # the v2 pool and defeat the version check in score().
    if note:
        rec["note"] = note
    line = json.dumps(rec, sort_keys=True) + "\n"
    for path in (labels_path, labels_path.with_suffix(".backup.jsonl")):
        with open(path, "a") as f:
            f.write(line)
    print(f"corrected {rec['item_id']}: "
          f"{target['human_label']} = {LABEL_NAMES[int(target['human_label'])]}"
          f"  ->  {new_label} = {LABEL_NAMES[int(new_label)]}")
    print("The original record stays on disk as an audit trail; --score takes the "
          "latest per item.")
    print("Safe to run while a labelling session is open -- both only append.")


def main():
    ap = argparse.ArgumentParser(description="Phase 0.5 §5.2 judge validation")
    ap.add_argument("--draw", action="store_true",
                    help="build the stratified 150-item sample (run once)")
    ap.add_argument("--score", action="store_true",
                    help="compute kappa, the per-model gap and the §5.2 verdict")
    ap.add_argument("--rubric-version", default=None, metavar="VER",
                    help="score only labels made under this rubric version. Needed "
                         "once a labels file contains more than one version, since "
                         "agreement pooled across rubric versions measures rubric "
                         "drift rather than judge quality.")
    ap.add_argument("--skip-degenerate", action="store_true",
                    help="reallocate `ambiguous`'s 37 items to the two categories that "
                         "actually carried the estimator. `ambiguous` was excluded by "
                         "the §6.7 degenerate rule, so labels there validate a stratum "
                         "that contributed nothing to the verdict. Departs from the "
                         "§5.2 suggested allocation — say so in the write-up.")
    ap.add_argument("--show-recent", type=int, metavar="N",
                    help="print your N most recent labels, numbered by QUESTION number")
    ap.add_argument("--show-q", type=int, metavar="Q",
                    help="show question Q with its neighbours, to confirm before fixing")
    ap.add_argument("--fix", nargs=2, metavar=("ITEM_ID", "LABEL"),
                    help="correct a label. ITEM_ID may be `last`. Appends a superseding "
                         "record; never edits history. Safe mid-session.")
    ap.add_argument("--fix-q", nargs=2, metavar=("QUESTION_NUMBER", "LABEL"),
                    help="correct by question number as shown on screen (ITEM n of 150). "
                         "Preferred over --fix: question number is resolved through "
                         "unique-item order, so it stays correct after earlier "
                         "corrections have shifted raw record positions.")
    ap.add_argument("--fix-note", default=None,
                    help="optional note to attach to a --fix correction")
    ap.add_argument("--seed", type=int, default=SAMPLE_SEED)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    sample_path = args.out_dir / "sample.jsonl"
    labels_path = args.out_dir / "human_labels.jsonl"

    if args.show_recent:
        show_recent(labels_path, sample_path, args.show_recent)
    elif args.show_q:
        show_recent(labels_path, sample_path, 0, around=args.show_q)
    elif args.fix_q:
        qs, lab = args.fix_q
        if lab not in ("0", "1", "2", "3"):
            sys.exit(f"label must be 0, 1, 2 or 3 (got {lab!r})")
        if not qs.isdigit():
            sys.exit(f"question number must be an integer (got {qs!r})")
        iid = resolve_question(labels_path, int(qs))
        print(f"question {qs} -> {iid}")
        fix_label(labels_path, iid, int(lab), args.fix_note)
    elif args.fix:
        item_id, lab = args.fix
        if lab not in ("0", "1", "2", "3"):
            sys.exit(f"label must be 0, 1, 2 or 3 (got {lab!r})")
        fix_label(labels_path, item_id, int(lab), args.fix_note)
    elif args.draw:
        if sample_path.exists():
            sys.exit(f"{sample_path} already exists. Redrawing would invalidate any "
                     "labels already collected against the old sample. Delete it "
                     "deliberately if that is what you want.")
        alloc = ALLOCATION_ESTIMATOR if args.skip_degenerate else ALLOCATION_SPEC
        print(f"allocation: {alloc}"
              f"{'  (--skip-degenerate: departs from the §5.2 suggestion)' if args.skip_degenerate else '  (§5.2 suggested)'}")
        draw(alloc, args.seed, sample_path)
    elif args.score:
        score(sample_path, labels_path, args.out_dir,
              only_rubric_version=args.rubric_version)
    else:
        # Hand-labelling is IRREPLACEABLE work — hours of human judgement that no
        # re-run can regenerate. It is also untracked by git, so a deleted labels file
        # is gone for good. (This happened on 2026-08-27: a write-mode smoke test was
        # run against the live labels file, then the file was deleted to clean up the
        # junk it had appended, destroying 8 real labels.)
        #
        # Two guards, both cheap:
        #   1. Every label is mirrored to an append-only backup that nothing in this
        #      script ever truncates or deletes. --score can be pointed at it to
        #      rebuild.
        #   2. A non-interactive stdin refuses to run at all, so a piped smoke test
        #      cannot write to real labels.
        if not sys.stdin.isatty():
            sys.exit(
                "REFUSING TO RUN: stdin is not a terminal.\n"
                "Labelling writes irreplaceable human judgement to "
                f"{labels_path}, which is untracked by git. A piped or redirected "
                "run is almost certainly an automated test, and an accidental write "
                "here costs real hours. Run it interactively, or point --out-dir at "
                "a scratch directory to test."
            )
        label_session(sample_path, labels_path)


if __name__ == "__main__":
    main()
