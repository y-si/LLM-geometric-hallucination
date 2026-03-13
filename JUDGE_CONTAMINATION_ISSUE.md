# Judge Contamination Issue — Discovered March 11, 2026

## Summary

The consensus judging pipeline has a silent failure mode: when a judge API call fails (rate limit, expired key, quota exceeded), it defaults to `label=3 (Refused), confidence=0.0` and this fake vote participates in the majority vote as if it were a real judgment.

**Root cause** (two code locations):
1. `src/models/judge_client.py` lines 174-178: After all retries, returns `{"label": 3, "confidence": 0.0, "justification": "Error: ..."}`
2. `src/models/consensus_judge.py` lines 52-53: If the future itself raises, injects the same default

**Two distinct API failure modes encountered:**
1. **GPT-5.1**: HTTP 429 "exceeded current quota" (OpenAI billing limit hit mid-run)
2. **Claude Opus 4.5**: "Could not resolve authentication method" (API key missing/expired in some sessions)

---

## How It Works (the mechanics)

The 3-judge panel votes on each response. Majority (2 of 3) wins.

**When 1 judge fails:** 2 real votes + 1 fake vote (label=3).
- If the 2 real judges agree → they outvote the fake → **label is correct** (91-93% of cases)
- If the 2 real judges disagree → the fake label=3 breaks the tie → **label may be wrong**

**When 2 judges fail (CoT only):** 1 real vote + 2 fake votes (both label=3). Consensus is always "Refused" regardless of what the real judge said.

---

## Actual Damage (revised after deep analysis)

### Initial scare vs. reality

The initial scan found 14,607 entries (34.9%) with at least one failed judge. This sounded catastrophic. But deeper analysis shows that in **91-93% of those cases, the 2 real judges agreed**, so the fake vote was outvoted and the label is correct.

### Labels changed by fix script

*Note: early estimate said "151 definitively wrong" using a narrow definition (consensus=3 and neither real judge said 3). Full recomputation changed **325 labels** — including cases where the fake vote reinforced one real judge's minority opinion. See "Why 325 instead of 151?" below.*

| Data | Labels changed | Total entries | % changed | Fix cost |
|---|---|---|---|---|
| V5 non-CoT (baselines + 4 prefixes) | 199 | 24,299 | 0.82% | $0 (script) |
| V5 finetuned + ablation (10 files) | 126 | 4,490 | 2.81% | $0 (script) |
| **Subtotal (non-CoT)** | **325** | **28,789** | **1.13%** | **$0** |
| V5 CoT verification | unfixable | 4,860 | 65.3% garbage | excluded from thesis |

### What this means
- **325 labels** across all non-CoT V5 data changed after recomputation. Fixed with a script (no API calls).
- **~3,172 CoT labels** are garbage (2 judges failed). Excluded from thesis entirely.
- **V3, TruthfulQA, cross-cat ablation: completely clean.** Zero failures.

---

## Contamination Scope by Dataset

### Completely clean (0 failures)
- **V3 cross-model benchmark** (449 entries)
- **TruthfulQA evaluation** (3,268 entries)
- **Cross-category ablation** (2,694 entries)

### Partially contaminated (1 judge failed, mostly safe)
- **V5 baselines** (4,860 entries): 442 affected (9.1%), ~40 labels actually wrong
- **V5 entity_aware prefix**: 16-25% Claude failures, ~91% safe (2 real judges agree)
- **V5 structured_caution prefix**: 16-25% Claude failures, ~91% safe
- **V5 epistemic_humility prefix**: essentially clean
- **V5 fact_grounded prefix**: essentially clean
- **V5 finetuned** (4,490 entries): 100% have GPT-5.1 failure, but 93.3% safe (Claude + Llama agree). Only 53 labels definitively wrong.

### Severely contaminated (2 judges failed, labels are garbage)
- **V5 CoT verification** (4,860 entries): 3,172 entries (65.3%) have 2+ failed judges. Both GPT-5.1 AND Claude failed simultaneously — only Llama 4 Maverick actually ran.

---

## Invalidated Finding: "CoT Catastrophic Refusal"

**Previously reported:**
> "CoT over-refusal: negative finding with RLHF alignment implications. CoT catastrophic (62-68% refusal)"

**Reality:**
- Llama CoT: 1,654 entries labeled Refused. **1,652 (99.9%) are API failure artifacts.** Only 2 genuine refusals.
- Mixtral CoT: 1,520 entries labeled Refused. **100% are API failure artifacts.** Zero genuine refusals.
- Corrected refusal rates: **under 1%** for both models.

**The "CoT causes catastrophic over-refusal" narrative was entirely wrong.** It was API rate-limiting, not model behavior.

---

## Impact on Thesis Results

### Unchanged
- V3 cross-model benchmark (all of Chapter 5 geometric analysis)
- All geometric/embedding analysis (independent of judge labels)
- TruthfulQA evaluation
- Cross-category ablation
- Template ablation finding
- The pipeline design and methodology

### Slightly affected (325 labels changed, 1.13%)
- V5 baseline hallucination rates: will shift by fractions of a percent
- V5 prefix hallucination rates (Entity-Aware, Structured Caution): will shift by fractions of a percent
- Best prefixes are still the best prefixes
- Step 9 training data: may gain/lose a handful of examples
- Bridge analysis: minimal impact

### Finetuned evaluation (53 wrong labels)
- Correct rates go UP ~3-6% (models were better than reported)
- Refusal rates drop to near-zero (the "refusals" were fake)
- Hallucination rates barely change

### CoT (invalidated — excluded from thesis)
- 65% of entries had 2+ failed judges, unfixable from stored data (would need ~$50 re-judging)
- Decision: **exclude entirely**. The "catastrophic refusal" finding was a bug, not a result. Corrected CoT would likely show similar accuracy to other prefixes — a boring result not worth $50 and an afternoon with 15 days to deadline. No thesis section depends on CoT. The core contributions (geometry predicts hallucination, geometry guides fixability, best-per-prompt fine-tuning, template ablation) are all intact without it.

---

## Fix Plan (Revised)

### Step 1: Fix the bug in the code ($0, 10 minutes)
Before anything else, fix the silent failure so it doesn't happen again.

### Step 2: Recompute non-CoT labels from existing data ($0, minutes)
Write a script that:
1. Scans all V5 JSONL files (non-CoT)
2. Identifies entries with failed judges (confidence=0.0, "Error" in justification)
3. Recomputes consensus using only the real judges
4. Writes corrected JSONL files (backup originals first)

Full recomputation changed 325 labels + corrected confidence scores on thousands more.

### Step 3: Re-run downstream analysis ($0, minutes)
- Re-run Step 9 best-per-prompt selection with corrected labels
- Re-run any analysis scripts that compute hallucination rates
- Update figures if numbers change

### Step 4 (optional): Re-judge CoT (~$50, 4-6 hours)
Only if you want to report CoT results in the thesis.

### Step 5 (if needed): Re-run fine-tuning (~$22)
Only if Step 9 produces materially different training data.

---

## Before Re-judging (for CoT or any future runs): Fix the Bug

**Option A (minimal):** Add logging/alerting when a judge fails
**Option B (better):** Raise an exception instead of silently returning label=3
**Option C (best):** Mark entries as "needs re-judging" rather than injecting a fake label

At minimum: verify API keys and billing are active before starting any run.

---

## Verification

All claims independently verified on March 11, 2026 by:
1. Scanning all JSONL files for entries with confidence=0.0 and "Error" in justification
2. Printing verbatim error messages from failed judges
3. Cross-checking that V3 and TruthfulQA have 0 failures
4. Confirming that CoT label=3 entries almost exclusively have 2+ failed judges
5. Checking that 91-93% of 1-failure entries have 2 real judges that agree (label unaffected)

The error messages are unambiguous:
- GPT-5.1: `"Error: Error code: 429 - ... You exceeded your current quota..."`
- Claude: `"Error: Could not resolve authentication method..."`

---

## Files Affected

### Contaminated data files:
- `results/v5_finetuned/*/judged_answers.jsonl` (all 10 files — 1 judge failed per entry)
- `results/v5_prefix_experiment/cot_verification/judged_*.jsonl` (2 judges failed on 65%)
- `results/v5_prefix_experiment/baselines/judged_*.jsonl` (9% affected)
- `results/v5_prefix_experiment/entity_aware/judged_*.jsonl` (16-25% affected)
- `results/v5_prefix_experiment/structured_caution/judged_*.jsonl` (16-25% affected)

### Clean data files:
- `results/v3/` (all files)
- `results/truthfulqa/` (all files)
- `results/v5_finetuned/cross_cat_ablation/` (all files)
- `results/v5_prefix_experiment/epistemic_humility/` (essentially clean)
- `results/v5_prefix_experiment/fact_grounded/` (essentially clean)

### Code with the bug:
- `src/models/judge_client.py` lines 174-178
- `src/models/consensus_judge.py` lines 52-53

---

## Fix Implementation (March 11, 2026)

### Script: `scripts/fix_judge_contamination.py`

**What it does:**
- Scans 20 non-CoT V5 JSONL files (baselines, 4 prefixes, finetuned main configs, finetuned ablations)
- For each entry, identifies failed judges (confidence=0.0 AND "Error" in justification)
- Recomputes consensus using only real (non-failed) judges
- Adds `_correction` metadata to every affected entry (audit trail)
- Backs up originals to `.backup_pre_contamination_fix` before overwriting

**What it does NOT do:**
- No API calls (recomputes from stored individual judgments only)
- Does NOT touch CoT files (those need actual re-judging — 2 judges failed, only 1 real vote)
- Does NOT touch V3, TruthfulQA, cross-cat ablation (all clean, 0 failures)
- Does NOT touch V4 files (initial benchmark, separate analysis)
- Does NOT modify individual_judgments (preserves the failure record)
- Does NOT modify any code files

**Tiebreaking logic when 2 real judges disagree:**
- Use the judge with higher confidence score
- Rationale: more principled than the current tiebreaker (fake label=3 vote). Both judges are real — we pick the one that's more certain.
- If equal confidence: use first judge (deterministic fallback, rare edge case)

**Safety features:**
- Default mode is DRY RUN (no file writes). Must pass `--apply` to make changes.
- Backs up every file before overwriting. Backup suffix: `.backup_pre_contamination_fix`
- Asserts entry count matches before and after (no entries lost or gained)
- NEVER_TOUCH list prevents accidental modification of clean data
- Every changed entry gets a `_correction` dict with: old_label, new_label, method, failed_judge_index, timestamp
- Writes `results/contamination_fix_summary.json` audit file on apply

### Dry-Run Results (March 11, 2026)

```
Total entries scanned:    28,789
Labels changed:           325 (1.13%)
Labels unchanged:         28,464
Unfixable (2+ failures):  0

Label transitions:
  Refused -> Correct:       125
  Partial -> Correct:        86
  Hallucinated -> Correct:   80
  Refused -> Hallucinated:   23
  Refused -> Partial:         6
  Correct -> Hallucinated:    2
  Partial -> Hallucinated:    2
  Hallucinated -> Partial:    1
```

**Interpretation:**
- 325 labels change, overwhelmingly in the "getting better" direction (291 → Correct)
- Only 4 changes go toward worse labels (2 Correct→Hallucinated, 2 Partial→Hallucinated)
- The fake label=3 votes were systematically inflating Refused and Hallucinated counts
- Net effect: correct rates go up, refusal rates drop, hallucination rates barely change
- This is consistent with the earlier finding that GPT-5.1 (the failed judge) was the strictest

**Why 325 instead of 151?** The earlier "151 definitively wrong" count only included entries where consensus=3 and neither real judge said 3. The 325 includes ALL label changes — including cases where the fake vote reinforced one real judge's minority opinion to create a 2-1 majority. For example: Claude says Partial(1), Llama says Correct(0), fake GPT says Refused(3). Current consensus = no majority, Counter.most_common picks the first (Partial from Claude? Actually the fake vote creates a 3-way split). The full recomputation catches all these cases.

### Per-file breakdown (actual applied counts from `contamination_fix_summary.json`)

| File | Total | Clean | Changed | Notes |
|---|---|---|---|---|
| v5_baselines/mixtral | 2,430 | 2,212 | 31 | GPT-5.1 failures |
| v5_baselines/llama | 2,430 | 2,206 | 24 | GPT-5.1 failures |
| v5_prefixes/mixtral/entity_aware | 2,430 | 1,927 | 31 | Claude failures |
| v5_prefixes/mixtral/structured_caution | 2,430 | 1,936 | 55 | Claude failures |
| v5_prefixes/mixtral/epistemic_humility | 2,430 | 2,429 | 0 | Nearly clean |
| v5_prefixes/mixtral/fact_grounded | 2,430 | 2,430 | 0 | Fully clean |
| v5_prefixes/llama/entity_aware | 2,430 | 1,816 | 27 | Claude failures |
| v5_prefixes/llama/structured_caution | 2,430 | 2,034 | 31 | Claude failures |
| v5_prefixes/llama/epistemic_humility | 2,430 | 2,429 | 0 | Nearly clean |
| v5_prefixes/llama/fact_grounded | 2,429 | 2,429 | 0 | Fully clean |
| v5_finetuned/mixtral/configA | 449 | 0 | 22 | GPT-5.1 failed on ALL |
| v5_finetuned/mixtral/configB | 449 | 0 | 16 | GPT-5.1 failed on ALL |
| v5_finetuned/mixtral/configC | 449 | 0 | 16 | GPT-5.1 failed on ALL |
| v5_finetuned/llama/configA | 449 | 0 | 10 | GPT-5.1 failed on ALL |
| v5_finetuned/ablation/T5_mixtral | 449 | 0 | 9 | GPT-5.1 failed on ALL |
| v5_finetuned/ablation/T10_mixtral | 449 | 0 | 10 | GPT-5.1 failed on ALL |
| v5_finetuned/ablation/R397_mixtral | 449 | 0 | 13 | GPT-5.1 failed on ALL |
| v5_finetuned/ablation/T5_llama | 449 | 0 | 13 | GPT-5.1 failed on ALL |
| v5_finetuned/ablation/T10_llama | 449 | 0 | 11 | GPT-5.1 failed on ALL |
| v5_finetuned/ablation/R402_llama | 449 | 0 | 6 | GPT-5.1 failed on ALL |

### Applied: March 11, 2026 at 23:16 UTC

```bash
python3 scripts/fix_judge_contamination.py --apply
```

**Result**: 325 labels corrected across 20 files. 0 unfixable. All originals backed up.
Audit trail: `results/contamination_fix_summary.json`
Backups: `*.jsonl.backup_pre_contamination_fix` alongside each corrected file

### Step 9 Re-run Results (March 11, 2026)

Re-ran best-per-prompt training data selection with corrected labels. Changes are minimal:

**Mixtral:** 2,402 → 2,403 training (+1), 28 → 27 unfixable (-1). Correct: 2,374 → 2,381 (+7), Partial: 26 → 22 (-4), Refusal: 2 → 0 (-2).

**Llama:** 2,406 → 2,406 (unchanged), 24 → 24 (unchanged). Correct: 2,387 → 2,394 (+7), Partial: 16 → 11 (-5), Refusal: 3 → 1 (-2).

Source distribution shifted (entity_aware gained share as corrected labels revealed more correct responses). Old results backed up with `.pre_contamination_fix` suffix.

**Conclusion: Re-training NOT needed.** Training sets are nearly identical. The corrected labels improved quality (more correct, fewer partial/refusal artifacts) but the actual training examples barely changed.

### Bug Fix (March 11, 2026)

Fixed the silent failure default in two files:

1. **`src/models/judge_client.py`**: Failed judges now include `"failed": True` flag in their return dict
2. **`src/models/consensus_judge.py`**:
   - Failed judges now include `"failed": True` flag
   - Consensus logic now **excludes failed judges from the majority vote** — only real judges participate
   - Warning printed when any judge fails
   - Falls back to all results only if ALL judges failed (edge case)

### All steps complete (March 12, 2026):
- ✅ Analysis scripts re-run with corrected data. Numbers shifted <1pp. No conclusions changed.
- ✅ All figures regenerated.
- ✅ CoT excluded from thesis (decision finalized — not worth re-judging).

### NOT applying (decided against):
- **Re-running fine-tuning**: Training sets barely changed (+1 for Mixtral, +0 for Llama). Not worth $22.
- **Re-judging CoT**: $50 cost, 4-6 hours runtime. Corrected CoT would likely show similar accuracy to other prefixes — a boring result. No thesis section depends on CoT. Core contributions intact without it.
