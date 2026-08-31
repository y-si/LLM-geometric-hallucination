# HANDOFF — live project state

**Read `CONTEXT.md` first** for orientation (what the project is, communication style,
methodology rules). This file is the opposite: purely volatile state — what is running
right now, what was just done, what to do next.

Update this at the end of every session. If it disagrees with your memory, trust this
file.

**Last updated: 2026-08-31**

---

## Running right now

| Job | Machine | Started | Status | Output |
|---|---|---|---|---|
| _(none)_ | — | — | — | — |

**Phase 0.5b is COMPLETE end to end.** Generation 32,662/32,680; judging 32,640/32,680
labelled via the Batch API; analysis run.

---

## THE RESULT (2026-08-31) — **GO**

Pre-registered §7 rule, unchanged thresholds, conservative native-38 blocking, complete
data, **§11.6 primary treatment of empty completions**. Not provisional. Full report:
`results/phase05b/analysis/report.md`.

| Statistic | Phase 0.5 (V3) | **Phase 0.5b (TruthfulQA)** | §7 threshold |
|---|---|---|---|
| **τ_corr** | 0.3098 | **0.5999** | ≥ 0.50 |
| **CI lower** (nested bootstrap) | 0.1913 | **0.5382** | ≥ 0.30 |
| τ_cross (blocked τ_b) | 0.2488 | 0.4813 | — |
| τ_selfA / τ_selfB | 0.826 / 0.781 | 0.803 / 0.801 | > 0.40 ✓ |
| ρ_corr (licensed) | 0.3307 | 0.6264 | — |
| **VERDICT** | NO-GO | **GO** | |

95% CI on τ_corr: **[0.5382, 0.6857]**. The CI *lower* bound clears the τ_corr threshold
itself, not merely the 0.30 CI floor.

**§11.4 floor check PASSES** — 39.2% (Llama) / 45.0% (gpt-oss) of the 817 prompts at
exactly P̂ = 0, against the pre-committed 70%. Better than the probe's 55%/61%. This was
pre-registered on 2026-08-28 to bind *whatever* τ came out at, so it had to be run and
it is now computed by `analyze_phase05.py` rather than by hand.

**§11.6's two treatments AGREE on the verdict** — τ_corr 0.5999 (primary, empty =
non-hallucination) vs 0.6007 (sensitivity, empty = missing), both GO. The
empty-completion decision is not load-bearing here, which is worth saying precisely
because it was pre-registered as though it might be. Only 18 completions were affected.

**The headline is not the GO on its own — it is the pair.** Same estimator, same code,
same k, same two models, same judge, same decision rule; only the prompt set changed and
τ_corr doubled. The V3 diagnosis said the NO-GO was a floor artifact of the benchmark and
predicted this *before* 0.5b existed. Durable write-up with every closed escape hatch:
`CONTEXT.md` → "Phase 0.5b returned GO".

r²: τ_corr 0.60 ⇒ r ≈ 0.81 ⇒ **~66% of prompt-level difficulty variance is
model-invariant** (V3: ~22%), against the ≥50% the framing needs. The CI lower bound
alone (τ 0.538 ⇒ r² ≈ 0.56) already clears 50%.

### Two banked secondaries CHANGED — do not quote the V3 numbers as general

1. **Stratification inflation collapsed to +0.0170** (pooled 0.4977 vs blocked 0.4807),
   from +0.110 on V3. The §2.1 effect is benchmark-dependent, set by between-stratum
   difficulty spread. Reframe it as that — the two runs are the contrast — rather than
   quoting a single number.
2. **The §6.5.4 label-neutrality test PASSES here**: pooled MH OR **1.172**, p = **0.102**,
   on a run with a *higher* truncation rate than V3 (24.9% vs 19.6%). V3 was OR 4.31,
   p < 1e-5. So the "you measured verbosity agreement" objection is closed for 0.5b by
   the test itself. Caveat: Model A reads OR 0.233 at p = 0.0006 but on **10** tables and
   in the opposite direction; 1 of 390 Fisher tables survives Bonferroni.

**Δ_artifact is not computable on 0.5b and that is correct** — §11.3 removes the
judge-bound arm because TruthfulQA has no non-verifiable prompts. The V3 estimate
(+0.118) stands and must be attributed to the V3 run when cited.

Worth keeping for the paper: **τ_b between the two models' orderings of the 38 category
means is 0.592** — coarse topic-level agreement, on the same order as the within-category
τ_cross, which is a cleaner way to say "they find the same things hard" than the pooled
number.

### Data integrity — §5.1 gate cleared

| Quantity | Value |
|---|---|
| Completions | 32,680 |
| Labelled | 32,640 |
| **Unrecovered (no label)** | **40 = 0.12%** (threshold 2%) |
| Pairs with k_eff < 16 | **0** under the §11.6 primary (2 under the sensitivity) |
| Panel | 817 → 817 (k_eff) → **736** (§6.7 degenerate rule) |

The 40 split cleanly: **22 judge JSON-parse failures** and **18 empty completions** that
were never judged. **Do not retry the 22** — every one is `unparseable: ...` at
`JUDGE_TEMPERATURE = 0.0`, so a retry replays byte-identical malformed output. Same
permanent class as Phase 0.5's 3. Judging is finished; there is nothing left to run.

12 of 38 categories were eliminated by §6.7 (< 5 distinct P̂ for either model), holding
81 of 817 prompts. Per-category τ_corr spans 0.076 (Indexical Error: Identity) to 0.955
(Indexical Error: Time); `Confusion: People` (0.083) and `Confusion: Places` (0.116) are
the notable low outliers inside the panel.

---

## THE ONE THING BLOCKING THE GO FROM BEING BELIEVABLE

**§11.3 fresh judge validation under rubric v2 has NOT been done.**
`results/phase05b/validation/` does not exist. The spec is explicit:

> *"The §5.2 v1 validation does not license the v2 judge. Fresh hand-labelling under v2
> is required before the 0.5b τ number is believed, on a fresh stratified draw."*

The 150 existing labels are v1 and `run_judge_validation.py --score` will refuse to pool
them. This was DO-NEXT item 9, was meant to run *during* generation, and was skipped. It
is the single pre-registered obligation still open, and it now gates a **GO** rather than
a NO-GO — i.e. it gates real Phase 1 spend, which is exactly the case §5.2 was written
for. Do it before taking the number to Sunny.

```bash
python3 scripts/run_judge_validation.py --dataset phase05b --draw   # fresh stratified sample
python3 scripts/run_judge_validation.py --dataset phase05b          # label by hand
python3 scripts/run_judge_validation.py --dataset phase05b --score --rubric-version v2-2026-08-28
```
`--dataset phase05b` is already wired (verified 2026-08-31): the draw uses
`proportional_allocation()` over the 38 TruthfulQA categories — **150 items**, no
hand-weighting, because rubric v2 applies CATEGORY 5 uniformly and no stratum is one the
rubric is silent on. Writes to `results/phase05b/validation/`.

**The labels file is untracked and irreplaceable.** On 2026-08-27 a write-mode smoke test
against the live file, followed by a cleanup delete, destroyed 8 real hand labels. Do not
point a test at `human_labels.jsonl`.

Keep in view while reading the κ: the judge disagrees with *itself* at T=0 on 2.5–7.5%
of completions (`CONTEXT.md` → "Judge label instability at temperature 0"). The §6.2
correction absorbs that as noise; it cannot absorb systematic per-model bias, which is
what §5.2 measures.

---

## DO NEXT, in order

1. **§11.3 judge validation under v2** — above. Blocks belief in the τ, blocks Phase 1.
2. **Diagnose the §6.5.1 residualisation anomaly.** Length has ~zero rank association
   with P̂ (τ_b 0.017–0.052) yet residualising on it halves τ_cross (0.4813 → 0.2466).
   Same pattern on V3 (0.249 → 0.174). Almost certainly the procedure — stratum fixed
   effects with one pooled slope, a `CHOICE` in the source, not a spec requirement — not
   length. Does not touch the verdict; does need an answer before the confound section is
   written.
3. **Book the Sunny Zoom.** The old reason to wait was "so the τ number is in hand". It
   is in hand and it is a GO on a public benchmark. Co-authorship is still formally
   unresolved and is a hard blocker on any submission.
4. **Send the Boaz credit email** (draft in `CONTEXT.md`). It decides whether Phase 1 can
   use closed frontier models, and Phase 1 is now the live next phase rather than a
   hypothetical.
5. **Revisit the venue.** `DEADLINES.md` carries an explicit reopening clause for exactly
   this case (*"pilot returns a strong GO"*). ICML 2027 (~late Jan) remains the honest
   target; verify the real ICLR 2027 date once at
   openreview.net/group?id=ICLR.cc/2027 and record it in `DEADLINES.md`, not here.
6. **Write the measurement sections.** Now stronger than when they were banked: a
   pre-registered protocol honoured when it went *against* us, followed by the same
   protocol returning GO when the diagnosed defect was removed.

### Superseded by the GO

The Phase 0.5 NO-GO write-up below is still correct **as a statement about V3** and is
load-bearing for the paper's methodology sections. It is no longer the project's verdict.
Read it as the first half of a two-run story.

---

## Phase 0.5 (V3) — NO-GO, superseded 2026-08-31 by the 0.5b GO

Pre-registered §7 rule, run on complete data. Not provisional.

| Statistic | Value | 95% CI (nested bootstrap) | §7 threshold |
|---|---|---|---|
| **τ_corr** | **0.3098** | **[0.1913, 0.4467]** | ≥ 0.50, CI lower ≥ 0.30 |
| τ_cross (blocked τ_b) | 0.2488 | [0.1399, 0.3310] | — |
| τ_selfA (Llama) | 0.8261 | [0.7115, 0.8375] | > 0.40 ✓ |
| τ_selfB (gpt-oss) | 0.7807 | [0.6600, 0.7551] | > 0.40 ✓ |
| ρ_corr (licensed cross-check) | 0.3307 | — | — |

**This is a clean negative, not an artifact.** Every escape hatch is closed:

- **Not a measurement failure.** Both reliabilities are ~0.8, double the 0.40 floor.
  The instrument works; the signal is genuinely weak. §7 row 3 does not apply, so
  escalating k from 20 to 40 is *not* the indicated action.
- **Not the τ heuristic.** ρ_corr = 0.331 against τ_corr = 0.310, a 0.02 gap. The
  licensed estimator agrees.
- **Not the label boundary.** τ_corr moves 0.310 → 0.336 → 0.341 across the three
  §6.1 definitions. Not load-bearing.
- **Not refusals.** τ_b between the two models' refusal rates is 0.0089 — essentially
  zero. Ordering agreement is not carried by shared refusal behaviour.
- **Not marginal.** Even the CI *upper* bound (0.447) sits below the 0.50 GO
  threshold. There is no reading of this data that reaches GO.

r² interpretation via the §7 derivation: τ_corr ≈ 0.31 ⇒ r ≈ 0.47 ⇒ **~22% of
prompt-level difficulty variance is model-invariant**, against the ≥50% the paper's
framing needs.

### Two things that complicate the story, both pre-registered checks doing their job

**1. `ambiguous` was eliminated by the §6.7 degenerate-stratum rule.** Both models show
only 3 distinct P̂ values across all 120 prompts (rates 0.002 and 0.004 — floor effect).
The primary decision surface therefore collapsed from three categories to two
(`borderline_plausible_fake` n=169, `nonexistent` n=120). §4.1 flagged exactly this risk
("`nonexistent` and `ambiguous` carry a real risk of sitting near ceiling or floor").
It does not rescue the verdict — `ambiguous`'s own τ_cross is −0.033, so including it
would have pushed τ_corr *down*. The exclusion was generous to the claim.

**2. The label-neutrality test FAILED, and the test itself is confounded.** §6.5.4
predicted truncation would be label-neutral at max_tokens=2048. It is not: MH odds ratio
**4.31**, χ²(1) = 64.7, p < 1e-5. Truncated gpt-oss samples are labelled hallucination
4.3× more often than complete samples *of the same prompt*.

But this does **not** establish that truncation corrupts labels, because the test cannot
separate that from the mediation §6.5.4 correctly identified: a sample that is
confabulating writes at length *and* gets labelled a hallucination, so truncation and
the label share a common cause within the prompt. Holding the prompt fixed does not hold
"this particular sample was confabulating" fixed. **The truncation confound is therefore
neither closed nor demonstrated — it is untestable by this design.** That is a real
limitation to put in front of Sunny, and it is a defect in the pre-registered check, not
in the data. Note also the test is a Model-B-only statement: Llama truncated 2 of 14,080
samples, giving 0 informative tables.

### Secondary results worth keeping

- **Δ_artifact = +0.118** (judge-bound τ_corr 0.428 vs verifiable 0.310), the expected
  direction. The §4.2 framing holds: scoring against a shared judge's parametric
  knowledge manufactures ~0.12 of apparent ordering agreement. A paper result.
- **Stratification inflation = +0.110** (pooled τ_b 0.371 vs blocked 0.261). The §2.1
  argument, quantified. Candidate figure.
- **Rate divergence is large and ordering agreement is weak** — the opposite of the §1
  hoped-for pattern. On `borderline_plausible_fake`, Llama 0.213 vs gpt-oss 0.661; on
  `nonexistent`, 0.069 vs 0.366.
- **Question length is not the driver** (|τ_b| ≤ 0.16 against P̂), though residualising
  on it does cost τ_cross 0.249 → 0.174.
- `borderline_edge_factual` behaved exactly as §4.5 predicted as a negative control:
  5 unique prompts, all P̂ tied, τ_b undefined.

---

## Why Phase 0.5b was run — the prediction that came true (historical, 2026-08-27)

**The NO-GO was diagnosed and the diagnosis pointed at the benchmark, not the claim.**
Llama scored exactly P̂ = 0 on 86% of `nonexistent` prompts. You cannot measure whether
two models order prompts by difficulty when one of them almost never fails. Full
write-up: `CONTEXT.md` → "Floor effects and the τ_b tie ceiling".

**The fix was Phase 0.5b: re-run the pilot on TruthfulQA.** 817 prompts, 38 categories,
adversarial by construction, and — decisively — **real sourced ground truth**
(`"Best answer: X / Also acceptable: Y, Z"`), so it satisfies the §4.0 verifiability
criterion that `factual` and `borderline_obscure_real` failed. Prior results in
`results/truthfulqa/` show Mixtral at 17% overall (Misconceptions 0.06 … Law 0.31) —
the intermediate zone Phase 0.5 lacked. It is also public, which kills the otherwise
fatal reviewer objection "you critiqued your own benchmark".

Recorded at the time: *"Either outcome is publishable: high τ means the claim is alive
and demonstrated on a standard benchmark; low τ is a clean general negative."* **It came
back high — τ_corr 0.310 → 0.601 — which is the branch this text called the stronger
one.** Keep this section: a diagnosis written down before the confirming data is a
paper-grade result, not just project history.

---

### DO NOW — no dependencies

**1. ✅ §5.2 judge validation — COMPLETE 2026-08-27, 150/150 labelled.** Result in the
dedicated section below. It produced the rubric fix (item 4a), not a judge swap: the
load-bearing hallucination-only agreement was 0.940 with κ = 0.835, and the alarming
4-way gap was one rubric ambiguity that moves P̂ by exactly zero under §6.1.

**2. ✅ TruthfulQA feasibility probe — COMPLETE 2026-08-28, verdict COMMIT.** Numbers and
the two extra checks in the next section.

**3. Start writing the measurement sections.** They are already banked and depend on
nothing pending: ground-truth verifiability as a benchmark design criterion with
Δ_artifact = +0.118, stratification inflation +0.110, the τ-disattenuation gap
(split-half reliability cannot correct between-model tie asymmetry), and a
pre-registered protocol honoured when it went against us.

---

### PROBE RETURNED **COMMIT** (2026-08-28) — Phase 0.5b is live

`scripts/probe_truthfulqa_rates.py`, 80 of 817 prompts, k=10, ~$4. Full output:
`results/phase05b_probe/probe.md`.

| | Llama-3.3-70B | gpt-oss-120b |
|---|---|---|
| mean P̂ | **0.295** | **0.219** |
| at exactly P̂ = 0 | 55% | 61% |
| dispersion chi²/df, **pooled** | 8.02 (p=2.7e-80) | 7.54 (p=1.9e-61) |
| dispersion chi²/df, **within-category** | **4.81** (p=7.7e-22) | **4.49** (p=1.1e-19) |
| max reachable τ_cross (tie ceiling), blocked | **0.981** | |

**The within-category row is mine, added after the probe, and it is the one that
licenses the COMMIT.** The probe's headline dispersion is *pooled* across all 80
prompts, which mixes between-category difficulty (easy vs hard topics) with
within-category difficulty. Only the latter is usable — §6.2's primary statistic blocks
within category, and pooled dispersion is exactly the quantity that looked healthy in
Phase 0.5 while the blocked estimator starved. Recomputing it blocked halves the ratio
(8.02 → 4.81) and it still clears the 1.5 threshold by 3×, at p ≈ 1e-22. So the
conclusion survives the stricter, decision-relevant version of its own test.

Second check, same reasoning: the **tie-asymmetry ceiling** that capped Phase 0.5 is
absent here. max τ_cross = sqrt(min(den_A,den_B)/max(den_A,den_B)) = **0.981** blocked
(0.963 pooled), because the two models' tie structures are balanced (55% vs 61% at
exactly zero) where Phase 0.5's were not (86% vs 49%). τ_corr = 0.50 is reachable.

Caveat kept in view: ~50% of probe categories had all their prompts tied, but at
n_c = 2–3 per category that is uninformative. The full run has ~21 per category.

**DONE, 2026-08-28 — items 4a, 4b, 5 and 6 are all complete.**

**4a. ✅ Judge rubric v2** (`src/models/judge_client.py`,
`JUDGE_RUBRIC_VERSION = "v2-2026-08-28"`). Three edits, no model change:
 1. CATEGORY 1 refusal boundary pinned — declining *because the entity cannot be found*
    is CORRECT (0); REFUSAL (3) is now only a bare no-reason refusal. This was the cell
    holding 50 of 150 hand-labelled items.
 2. New rule for correct-rejection-then-unmarked-fabrication → HALLUCINATION (2), plus a
    new `mixed_rejection_then_fabrication` output flag so §6.1's label-boundary
    sensitivity on that choice is computable **without re-judging 32,680 rows**.
 3. **New CATEGORY 5 for sourced reference answers — this was not in the original plan
    and Phase 0.5b could not have run correctly without it.** TruthfulQA ground truth is
    `Best answer: / Also acceptable: / Known incorrect answers:`, a shape v1 had no rule
    for; it fell through to CATEGORY 3, which told the judge to consult "established
    reality" and ignore the authoritative known-incorrect list — the single most
    valuable signal in the dataset. It also fixes a trap: TruthfulQA lists "I have no
    comment" as an *acceptable* answer on many items, so a v1 judge would have scored
    the dataset's own reference answer as a refusal.

 Every label now carries `rubric_version`, and `run_judge_validation.py --score`
 **refuses to pool across versions** (new `--rubric-version` filter). Verified: scoring
 the existing 150 labels reproduces 0.966/0.913 and κ = 0.835 unchanged, now with a
 banner saying they describe the superseded rubric. Phase 0.5 is **not** re-judged under
 v2 — that would replace a pre-registered result with a post-hoc one.

**4b. ✅ Phase 0.5b pre-registered** — `PHASE_0.5_SPEC.md` §10 amendment dated
2026-08-28 plus a new **§11**, written before any 0.5b data existed. §11 fixes: the
prompt set (§11.1), the strata (§11.2), what is NOT carried over (§11.3), the decision
rule (§11.4), cost (§11.5). §§1–9 untouched; §7 thresholds verbatim.

Two things in §11 worth knowing because they are pre-commitments that constrain us:
 - **Strata = the 38 native TruthfulQA categories, deliberately the conservative
   choice.** 14,831 blocked pairs, vs 27,939 for the coarse-13 merge. Coarsening strata
   can only *raise* τ, so pre-committing to the finer blocking forecloses "you loosened
   the strata until it cleared 0.50". The coarse-13 map is also pre-registered in full,
   as a **secondary only, never the decision statistic** — it is the middle rung of a
   pooled → coarse → native ladder for §6.3. The §6.7 degenerate rule costs almost
   nothing at this level: the 8 categories with n < 10 hold just 1.4% of blocked pairs.
 - **A pre-committed floor-effect check** (§11.4): if either model sits at exactly
   P̂ = 0 on >70% of the 817 prompts, the run is reported **inconclusive on the same
   grounds as Phase 0.5**, whatever τ_corr says. The probe measured 55%/61%, so this
   should pass — it is declared now so that failing it cannot later be spun as a
   surprise. Unlike §7's measurement-failure row, the remedy is *not* more samples.

 Also disclosed in §11.0, because it is the one honest weakness: the probe was run
 before pre-registration, its thresholds were not pre-registered, and it revealed
 marginals on ~10% of the prompt set. **τ_cross, τ_self and τ_corr were never computed
 on probe data and must not be before the full run is judged.** The decision statistic
 is unseen. The 80 probe prompts stay in the set (dropping them would bias it); probe
 completions are discarded, not reused (k=10, rubric v1).

**5. ✅ Manifest built and frozen** — `data/prompts/phase05b_manifest.jsonl`, 817
prompts, via new `scripts/build_phase05b_manifest.py`. All 817 taken whole: no sampling,
no filtering, no pool top-up, no template substitution, no RNG — there is no
construction rule here that can be got wrong, which is the reason to prefer it. The
script's real job is refusing to ship the Phase 0.5 defects, and all checks pass:

```
unsubstituted [placeholder] tokens ......... 0   (V3 shipped 42)
ground truths with no sourced reference .... 0   (V3: 94/98 factual)
duplicate uids / duplicate questions ....... 0 / 0
merge map is a strict partition of all 38 .. yes
```

**COMMIT THIS FILE before generating.** §11.1 freezes it.

**6. ✅ Scripts parameterised** — `--dataset {phase05,phase05b}` on
`analyze_phase05.py`, `run_phase05_generation.py`, `run_phase05_judging.py`. Each writes
to `results/<dataset>/`, so the two prompt populations can never accumulate in one
completions file (the decoding-config fingerprint could not have caught that, since the
decoding config is identical between them).

Two verifications worth trusting the change on:
 - **Phase 0.5 regression is clean.** Re-running `--dataset phase05` reproduces
   `report.md` **byte-identically** and τ_corr / τ_self / CI / verdict to the last
   decimal. `audit_ground_truth.py` imports this module and never calls `configure()`,
   so it still gets the Phase 0.5 defaults.
 - **The 0.5b path was dry-run on synthetic data** (817 prompts × 2 × 20, temp dir, no
   network) because the analyzer had never seen 38 strata. It runs end to end and
   discriminates in both directions: a high shared-difficulty component gives
   τ_corr = +0.966 → **GO**, a low one gives +0.055 → **NO-GO**, the three-rung ladder
   renders, and no stratum trips §6.7. Nothing synthetic was written under `results/`.

---

## Phase 0.5b generation (2026-08-29) — COMPLETE, 32,662/32,680 (99.94%)

| | Llama-3.3-70B | gpt-oss-120b |
|---|---|---|
| Good completions | 15,580+ | 15,525+ |
| Truncated (`finish_reason == length`) | **0.5%** (84) | **23.6%** (3,668) |
| Median output tokens | 315 | 1,349 |
| Empty (budget spent on reasoning) | 0 | **18** (0.12%) |

**Primary set: 817 of 817 prompts.** 0 pairs below the §5.1 k_eff floor under §11.6's
primary treatment; 2 pairs (`0433`, `0477`) under the sensitivity treatment.

Three things worth carrying forward:

**1. A ~1 h network outage cost 1,527 rows and was fully recovered.** `--retry-failed`
took pairs at k_eff = 0 from **76 → 0**. The only gaps remaining in the whole run are
the 18 genuine empty completions. Cause was almost certainly the laptop lid being
closed; note the failure count was ~190× my "~8 rows" estimate, because the process
does not pause on sleep — it keeps pulling tasks and failing them instantly, so an
hour of downtime burns ~1,500 tasks rather than the 8 in flight.

**2. The probe over-forecast the empty-completion rate by 29×** — 3.38% predicted,
**0.12%** actual. Per-category it was worse: `Sociology` was forecast at 25% and came in
at 0.5%. Cause: the probe sampled ~2 prompts per category at k=10, so one unlucky prompt
made a whole category look catastrophic. **Read probe per-category rates as noise; only
the pooled figure was trustworthy.** The §11.6 pre-registration was still worth writing
— it cost nothing and it now affects 2 prompts instead of being an open question.

**3. Truncation asymmetry is 23.1 points** (was 19.6 in Phase 0.5), close to the 26
forecast. Expected and pre-registered: a model still generating at the cap is
confabulating at length, which is the behaviour being measured. **§6.5.4's
label-neutrality test is now genuinely load-bearing** — at this gap, "the pilot measured
verbosity agreement rather than difficulty agreement" is a live alternative explanation
and a reviewer will raise it. Do not skip it, and do not residualize P̂ on length (that
controls a mediator).

---

### WATCH THIS DURING GENERATION — new failure mode, already pre-registered

**gpt-oss returns completely empty answers on ~3.4% of its calls.** It spends the whole
2,048-token budget on internal reasoning and emits nothing. **Phase 0.5 had 0 of
28,160**, so this is new to TruthfulQA. Projected ~551 rows, 1.69% of the run.

Handled, not open: the generation script only WARNS at the end (no mid-run abort), and
§11.6 pre-registers the treatment — empty counts as a non-hallucination in the k_eff
denominator, same class as a refusal, following §6.1's own rationale; "empty = missing
data" is the pre-registered sensitivity. Written while generation was in flight and
before any label, P̂ or τ existed. `max_tokens` is deliberately NOT raised.

**What to actually watch, because it decides how much data survives:**

```bash
python3 - <<'EOF'
import json, collections
seen=collections.Counter(); bad=collections.Counter()
for l in open('results/phase05b/completions.jsonl'):
    r=json.loads(l)
    if r['model']!='gpt-oss-120b': continue
    seen[r['category']]+=1
    if not r.get('completion'): bad[r['category']]+=1
for c in sorted(bad, key=lambda c:-bad[c]/seen[c]):
    print(f"{bad[c]:4d}/{seen[c]:4d} = {bad[c]/seen[c]:6.1%}  {c}")
EOF
```

Probe rates by category, i.e. the strata at risk: `Sociology` 25% (n=55),
`Subjective` 20% (n=9), `Superstitions` 20% (n=22), `Religion` 15% (n=15),
`Science` 15% (n=9). At 20-25% empty, k_eff lands on the `K_EFF_MIN = 16` cliff, and
because tau_cross needs BOTH models on a prompt, every gpt-oss pair dropped removes that
prompt from the primary entirely. **The missingness is correlated with difficulty, which
is the quantity being estimated** — that is why it needed pre-registering rather than a
default.

---

### Judging route: BATCH API, verified equivalent (2026-08-31)

Judging runs through `scripts/run_phase05_judging_batch.py` — **~$63 instead of ~$125**,
same labels. Identical model, rubric-v2 system prompt, user content, temperature and
max_tokens, and the *same* `parse_judge_response()` function rather than a copy. One
request per completion, so label independence is untouched (packing several completions
per call was considered and rejected: it would induce within-prompt correlation and
corrupt τ_self, which is a split-half reliability).

**Verified against the synchronous path, and the verification needed a noise floor to be
readable.** `--verify` re-judged 40 completions that already had sync labels and found 2
mismatches (5.0%). That looked alarming — the two labels appeared *swapped*, which is what
a `custom_id` mapping bug would produce. Resolved by measuring self-consistency instead of
arguing about it:

| comparison | disagreement |
|---|---|
| sync vs sync | 2.5% |
| **batch vs stored** | **5.0%** |
| sync vs stored | **7.5%** |

The sync path disagrees with its own stored labels *more* than the batch path does. A
mapping bug would have shown ~0% for sync-vs-stored. **The routes are equivalent.**

Full write-up of the judge-noise finding — including the part the §6.2 correction cannot
absorb — is in `CONTEXT.md` → "Judge label instability at temperature 0".

```bash
python3 scripts/run_phase05_judging_batch.py --submit     # ~$63, 5 batches
python3 scripts/run_phase05_judging_batch.py --status      # poll; safe to close terminal
python3 scripts/run_phase05_judging_batch.py --retrieve    # writes judgments.jsonl
```

Runs server-side, so a closed lid or lost wifi does not matter — which it did for
generation, where a closed lid cost 1,527 rows.

---

### The 0.5b run — items 7–11, ALL DONE except item 9

**7. ✅ Committed before generating** (`40bc9dd` → `95f0539`). The manifest and the spec
were in git before the data existed.

**8. ✅ Generated** — 32,662 / 32,680 (99.94%), ~$10 Together. Details in the generation
section below.

**9. ❌ NOT DONE — re-validate the judge under rubric v2, on a fresh sample.** This is the
one item that was skipped, and it is now the only open pre-registered obligation. See
"THE ONE THING BLOCKING THE GO" at the top.

**10. ✅ Judged via the Batch API** — `run_phase05_judging_batch.py`, **~$63** instead of
~$125, same labels (equivalence verified against the sync path — see the batch section
below). 32,640 / 32,680 labelled, 0.12% unrecovered, §5.1 gate cleared. Nothing left to
retry: all 22 judge failures are `unparseable` at T=0 and replay identically.

**11. ✅ Analysed** — `python3 scripts/analyze_phase05.py --dataset phase05b`.
**GO.** The §11.4 floor check is now implemented in the analyzer (it was pre-registered
but had never been coded) and passes at 39.2% / 45.0% against 70%.

---

### PHASE 1 BLOCKERS — not now, but before any panel spend

**12. Ground-truth audit.** Worksheet is built and impact-ranked; the top ~30 of 99 rows
capture most of the effect.
```bash
# fill the `verdict` column: real | fake | unsure
python3 scripts/audit_ground_truth.py --score
```
Not needed for Phase 0.5b at all — TruthfulQA has real ground truth.

**13. Fix `build_benchmark_v2.py`.** Make the missing-pool-key branch (lines 53–55)
**raise** instead of emitting `[var]` as shipped data; it would have caught the other two
bugs immediately. Then make `load_entities()` load all pools, not just one category's.
Add a build-time assertion that no emitted question matches `\[[a-z_0-9]+\]`.

**14. Replace the `people` entity subset** (33 entities, 58 primary prompts). A benchmark
cannot assert that a human name belongs to nobody. Replacement, not auditing.

**15. Design graded within-category difficulty.** The deepest fix, and the reason
Phase 0.5 could not test its own claim. TruthfulQA supplies this off the shelf for
0.5b; a bespoke benchmark still needs it.

---

### DO NOT DO

- **Do not escalate k from 20 to 40.** That is the §7 row-3 remedy for measurement
  failure. Reliabilities are ~0.8 on both runs; neither is one.
- **Do not fund the Phase 1 panel until §11.3 judge validation is done.** §7 now says GO,
  so the binding constraint has moved: it is the unvalidated v2 judge, not the τ.
- **Do not retry unlabelled judgments** — 3 on Phase 0.5, 22 on Phase 0.5b. All are
  JSON-parse failures at temperature 0 and replay identically. Permanent, and harmless
  at 0.01% / 0.12%.
- **Do not re-judge Phase 0.5 under rubric v2.** That swaps a pre-registered result for a
  post-hoc one. The two runs are compared as they were pre-registered, judge version
  included, and the difference is disclosed.
- **Do not quote the V3 secondaries as general.** Stratification inflation is +0.110 on
  V3 and +0.0170 on 0.5b; the label-neutrality test fails on V3 and passes on 0.5b. Both
  are benchmark-dependent — say so.
- **Do not quote absolute hallucination rates from the Phase 0.5 run** in the paper.
  Ordering survives; the rates are measured against ground truth known to be wrong.
  (0.5b rates *are* quotable — TruthfulQA has real sourced ground truth.)
- **Do not regenerate the V3 benchmark expecting a repair.** `prompts.jsonl` is out of
  sync with today's entity lists, so regeneration produces a new dataset version whose
  results must not be mixed with these.


## §5.2 judge validation (2026-08-27) — COMPLETE, 150/150

`results/phase05/validation/validation.md`. The script's headline verdict reads
**JUDGE CONFOUNDED**, but that is triggered by a metric the estimator is immune to.
Read this section, not the headline.

| Collapse | Model A | Model B | gap | over 5 pp? |
|---|---|---|---|---|
| 4-way, weighted | 0.351 | 0.631 | **28.1 pp** | yes |
| **hallucination-only, weighted** | **0.966** | **0.913** | **5.3 pp** | yes (marginal) |
| hallucination-only, well-formed only | 0.962 | 0.902 | 6.1 pp | yes (marginal) |

**The 28 pp gap is a rubric artifact with zero effect on any result.** One confusion
cell — human `3 Refusal` → judge `0 Correct` — is **50 of 150 items (33%)**. For a
fabricated entity, "I can find no record of this" satisfies both the REFUSAL definition
and CATEGORY 1's CORRECT definition; the rubric never disambiguates them. §6.1 pins
`P̂ = #(label == 2)/k_eff` with 0, 1 and 3 all in the denominator, so a 3-vs-0
disagreement moves P̂ by **exactly zero**. Merging 0 and 3 lifts 4-way agreement from
0.500 to **0.833**. It looks asymmetric only because Llama answers tersely and gpt-oss
does not, so the ambiguity lands on Model A.

**The load-bearing number is good: κ = 0.835, agreement 0.940** on the hallucination
boundary — the only boundary the estimator uses.

**The marginal 5.3–6.1 pp gap on that boundary is real and does cross §5.2's threshold.**
Judge error is somewhat higher on gpt-oss (0.913 vs 0.966). So §5.2's remedy applies:
improve the judge before Phase 1. But this is a marginal flag, not a result-invalidating
one, and **the fix is the rubric, not a bigger model** — see `CONTEXT.md` →
"The judge rubric has two structural gaps".

**Two findings worth more than the κ**, both in `CONTEXT.md`:

1. **~12 ground-truth errors in 150 items (~8%)**, found incidentally while labelling —
   independently confirming and roughly quantifying the defect. Includes "General Thomas
   Bradford does exist and was a British army officer" (×2), a real telecommunications
   company, "The River Keeps Its Secrets" existing under another author, Saltwick Bay.
   Sein also reached the `people`-subset conclusion unprompted: *"hard to be certain for
   people questions because chances are someone has this name."*
2. **A recurring pattern the rubric cannot express**: 6 of 150 (4%) correctly reject the
   entity and *then* fabricate supporting detail. Reinforces limitation §9.8, and is
   another route by which a verbose model is scored differently.

## Judging results (2026-08-26) — COMPLETE

| | Value |
|---|---|
| Completions labelled | **28,157 / 28,160** |
| Unrecovered (no label) | 3 (**0.01%**, §5.1 threshold 2%) — gate cleared |
| (uid, model) pairs at k_eff = 20 | 1,405 |
| (uid, model) pairs at k_eff = 19 | 3 |
| pairs below the k_eff 16 floor | **0** |

Labels: 22,099 Correct / 1,038 Partial / 4,550 Hallucination / 470 Refusal.

**The 3 permanently-unrecoverable samples are JSON parse failures, not API failures**
(`Expecting ',' delimiter`, `Invalid control character`) — the judge emitted a
justification string that breaks `json.loads`. Because `JUDGE_TEMPERATURE = 0.0`, a
retry replays byte-identical malformed output, so **these will never recover by
retrying; stop retrying them.** All three land on `gpt-oss-120b` and leave their pairs
at k_eff = 19, above the floor, so they cost nothing. Worth a tolerant judge-output
parser before Phase 1, where 0.01% of a larger run is still 0.01% but the unretryable
pattern is the annoying part.

Spend: ~$16 for the retry, on top of the earlier partial run.

**The failure contract held throughout.** Not one failure was ever coerced into a label
across either run — the March 2026 contamination fix working as designed.

**`run_phase05_judging.py`'s two reporting defects are FIXED (2026-08-26).** Its summary
now agrees with `analyze_phase05.py`: unrecovered rate 0.01%, 0 pairs below the k_eff
floor. It also names any still-unlabelled sample with its last error, and says outright
that a JSON-parse failure is not retryable. Running it with nothing to do is now a free
state check — it prints the summary and makes no API calls.

For the record, what they were:

1. **Failure rate could never clear.** `n_failed / len(all_judgments)` over an
   append-only file: a successful retry leaves the stale failure row behind, so it read
   24.68% on fully recovered data and warned forever. Now computed over completions
   with no label, deduplicated on `(uid, model, sample_idx)`. The gross call-failure
   rate is still shown as a diagnostic but does not gate.
2. **k_eff undercount.** `defaultdict(int)` filled only from successes, so pairs with
   zero successes had no key and escaped the `< 16` count — printed 13 against a true
   464. Now seeded from the full completions cross-product.

Both were reporting-only. Neither ever touched a label.

---

## Generation results (2026-08-26)

| | Llama-3.3-70B | gpt-oss-120b |
|---|---|---|
| Completions | 14,080 | 14,080 |
| Truncated (`finish_reason == "length"`) | **0.0%** (2) | **19.6%** (2,758) |
| Median output tokens | 101 | 686 |

The 19.6-point truncation asymmetry is **expected and is not a defect**: a model still
generating at 2048 tokens is confabulating at length, which is the behaviour being
measured. Do not raise `max_tokens` to chase it, and do not residualize P̂ on length —
that controls a mediator and destroys real signal (§6.5.4). The test that matters is
label-neutrality, run after judging.

---

## Blocked / waiting

| Item | On whom | Since | Notes |
|---|---|---|---|
| **§11.3 judge validation under rubric v2** | **Sein — hours of hand-labelling, nobody else can do it** | skipped during generation | **The only open pre-registered obligation, and it now gates a GO.** 150 items, `--dataset phase05b`. See the top of this file. |
| Boaz credit clarification | Boaz | email drafted, **not sent** | Decides whether Phase 1 can use closed frontier models. Draft in `CONTEXT.md`. **Phase 1 is now the live next phase, not a hypothetical — send it.** |
| Sunny Zoom | Sunny | she offered "next week" | **Book it this week.** The τ number is in hand *and* it is a GO on a public benchmark. Co-authorship still formally unresolved, which is a hard blocker on any submission. |

**Venue: `DEADLINES.md` is authoritative on dates and it says ICML 2027 (~late Jan), with
ICLR 2027 "effectively off the table".** An earlier version of this file listed "ICLR
Sept 24, unverified" as a blocked item; that contradicted `DEADLINES.md` and made
everything look like a 4-week sprint. Removed.

The ICLR write-off named two contingencies. **One is now obsolete:** "the pilot design
was only pre-registered on Aug 24 and no code exists yet" — the pilot is run, the code
exists, the verdict is evaluated, and the ICML plan budgeted weeks 1–3 (Aug 24 → Sep 14)
for exactly that. **We are ~2.5 weeks ahead of schedule**, which is what makes a
TruthfulQA re-run free rather than a slip. The other contingency — "both advisors are
unanswered" — is still true and is now the actual critical path.

`DEADLINES.md` also carries a reopening clause: *"If circumstances change dramatically
(pilot returns a strong GO within days, both advisors reply immediately), rebuild it
then."* **Half of that clause has now fired: the pilot returned a strong GO** (τ_corr
0.601, CI lower 0.539, on a public benchmark, both runs pre-registered). The other half
has not — both advisors are still unanswered, which is exactly why items 3 and 4 in
"DO NEXT" are the ones that move the venue question. Do not reopen ICLR unilaterally on
the GO alone; the clause requires both. Verify the real ICLR 2027 date once at
openreview.net/group?id=ICLR.cc/2027 and record it in `DEADLINES.md`, not here.


---

## Main remaining build (superseded — see "DO NEXT, in order" above)

**Nothing. `scripts/analyze_phase05.py` is written** (2026-08-26) and covers all of
§6–§7: blocked within-category τ_b, split-half noise ceiling, attenuation correction
plus the licensed ρ cross-check, nested bootstrap, Δ_artifact, every §6.5 confound
check including the label-neutrality test, the §6.7 degenerate-stratum rule, and the
§7 decision rule. Outputs land in `results/phase05/analysis/`.

It needs no new API calls and no new libraries — numpy and pandas only. Kendall τ_b,
stratified Spearman, Fisher exact, Cochran–Mantel–Haenszel and the Wilson interval are
implemented in the script because **scipy is not installed on this machine** (`pip
install -r requirements.txt` has never been run against this interpreter: Python 3.9.6,
numpy 1.19.0). Every one of those implementations was checked against published
reference values before the script was trusted.

The remaining work is running it on complete data.

---

## Open decisions (not blocking)

- **Anthropic Batch API for judging** — halves the judge bill (~$50 → ~$25) but reworks
  the §5.1 per-call retry contract. Deferred for the pilot; revisit at Phase 1 volume.
- **Together support ticket** — `Qwen2.5-72B-Instruct-Turbo` is normally serverless for
  everyone, so its being dedicated-only here suggests an account-tier restriction. Free
  to ask, unknown latency, do not block on it. Would widen the Phase 1 panel.
- **Thesis-continuity bridge** — neither evaluated model is a thesis model. A bounded
  dedicated-endpoint run on Mixtral over the 409-prompt primary set would restore a
  documented link. Only worth pricing if the pilot returns GO or an advisor pushes.
- **`gpt-oss-20b` as Model B** — might be less pathologically verbose than `120b`.
  ~15 calls to find out via `scripts/diagnostics/probe_completion_lengths.py`.

---

## Session log

### 2026-08-31 — **Phase 0.5b returned GO.** τ_corr 0.310 → 0.601

Judging finished on the Batch API and the analysis ran. **The pilot has flipped: GO on
the same pre-registered rule that returned NO-GO on V3.** Full numbers at the top of this
file; durable write-up in `CONTEXT.md` → "Phase 0.5b returned GO".

- **τ_corr = 0.5999, 95% CI [0.5382, 0.6857]** against thresholds 0.50 and 0.30. The CI
  *lower* bound clears the point-estimate threshold. ρ_corr = 0.6264 confirms it is not
  an artifact of the τ disattenuation heuristic (gap −0.027).
- **The result is the pair, not the number.** Same estimator, same code, same k, same two
  models, same judge, same rule — only the prompt set changed. The V3 floor-effect
  diagnosis predicted this before 0.5b data existed. A pre-registered prediction that
  came true is worth more than the GO alone.
- **Judging: 32,640 / 32,680 labelled, 0.12% unrecovered, §5.1 gate cleared.** The 40
  gaps are 22 judge JSON-parse failures (unretryable at T=0 — they replay byte-identical)
  and 18 empty completions that were never judged. Nothing left to run. Batch API cost
  **~$63** against the ~$125 sync estimate.
- **TWO pre-registered checks existed only in the spec and had to be coded after the
  data — this is the defect to remember from this session.** §11.4's floor check was
  simply absent, so the first 0.5b analysis emitted a §7 verdict without evaluating a
  check pre-committed to bind whatever τ came out at. **§11.6 was worse: the wrong
  treatment was running.** The analyzer counted k_eff as "completions carrying a label",
  and an empty completion is never sent to the judge — so it silently applied §11.6's
  *sensitivity* treatment as though it were the primary. Both are now implemented, both
  are logged in the spec's amendment log as post-data implementations of pre-data rules,
  and **neither changed the verdict.** The lesson is procedural: a pre-registered check
  that lives only in prose is not a check. Ship the analyzer change in the same commit as
  the amendment.
- **§11.4 passes: 39.2% / 45.0% at exactly P̂ = 0 against a 70% threshold** — better than
  the probe's 55% / 61%.
- **§11.6's two treatments agree: τ_corr 0.5999 (primary) vs 0.6007 (sensitivity), both
  GO.** 18 completions affected, all gpt-oss, over 6 pairs. Under the primary **no pair
  falls below the k_eff floor at all**; the sensitivity loses 2 prompts and no strata.
  §11.6 pre-committed to reporting a disagreement as the finding — there is none.
- **Two banked secondaries changed under the new benchmark and must not be quoted as
  general.** Stratification inflation collapsed from +0.110 to **+0.0170** — the §2.1
  effect is set by between-stratum difficulty spread, so the two runs are the contrast
  rather than one number being "the" answer. And the §6.5.4 label-neutrality test now
  **passes** (MH OR 1.172, p = 0.102) on a run with a *higher* truncation rate than V3
  (24.9% vs 19.6%), where V3 read OR 4.31 at p < 1e-5. The verbosity-agreement objection
  is closed for 0.5b by the test itself.
- **Refusals cannot be carrying the agreement:** Llama's refusal rate over the whole run
  is exactly 0.0000 (gpt-oss 0.0074), so §6.5.3's τ_b is undefined; residualising each P̂
  on its own refusal rate moves τ_cross 0.4813 → 0.4782.
- **Regression check held throughout:** `--dataset phase05` still reproduces `report.md`
  byte-identically after every edit, including the §11.6 rework of `build_per_pair`. The
  post-hoc section heading was made verdict-aware ("WHY the tau is low" is wrong under a
  GO) in a way that leaves the Phase 0.5 text unchanged.
- **The one obligation still open is item 9: §11.3 judge validation under rubric v2.** It
  was meant to run during generation and was skipped. It now gates a GO — i.e. it gates
  real Phase 1 spend, which is the case §5.2 was written for. It is at the top of this
  file and at the top of the blocked table.
- **Flagged for the write-up, not the verdict:** §6.5.1 finds ~zero rank association
  between P̂ and question length (τ_b 0.017–0.052) yet residualising on length halves
  τ_cross (0.4813 → 0.2466). Same pattern on V3. Almost certainly the residualisation
  procedure (a `CHOICE` in the source, not a spec requirement), not length. Needs
  diagnosing before the confound section is written.
- Spend: ~$63 judging (batch). $0 this session beyond the retrieve.

### 2026-08-28 — probe COMMITted; rubric v2; Phase 0.5b pre-registered and tooled

Everything gating the 0.5b run is now done. Remaining work is spend-and-wait
(generate → judge → analyse), plus re-validating the judge under the new rubric.

- **Probe verdict COMMIT, and it survives a stricter test than the probe ran.** The
  probe's headline dispersion (chi²/df 8.02 / 7.54) is *pooled*, which mixes
  between-category difficulty with within-category difficulty — and only the latter is
  usable, because §6.2 blocks within category. Pooled dispersion is precisely what
  looked healthy in Phase 0.5 while the blocked estimator starved, so this had to be
  recomputed rather than assumed. Blocked it halves to **4.81 / 4.49**, still 3× the
  1.5 threshold at p ≈ 1e-22. Separately, the **tie-asymmetry ceiling** that capped
  Phase 0.5 is absent: max τ_cross = **0.981** blocked, because the models' tie
  structures are balanced (55% vs 61% at exactly zero) where V3's were not (86% vs 49%).
  Both checks are recorded in the "PROBE RETURNED COMMIT" section above.
- **Judge rubric v2** (`JUDGE_RUBRIC_VERSION = "v2-2026-08-28"`). Two edits were planned
  from §5.2; a **third was necessary and was not in the plan**: TruthfulQA's
  `Best answer: / Also acceptable: / Known incorrect answers:` ground truth had no rule
  in the rubric and fell through to CATEGORY 3, which told the judge to consult
  "established reality" and **ignore the authoritative known-incorrect list** — the most
  valuable signal in the dataset. New CATEGORY 5 fixes that, and with it the trap that
  TruthfulQA lists "I have no comment" as an *acceptable* answer, which a v1 judge would
  have scored as a refusal. Phase 0.5b would have run with a systematically wrong judge.
- **Label provenance is now enforced, not documented.** Every judgment and every human
  label carries `rubric_version`; `--score` refuses to pool across versions and grew a
  `--rubric-version` filter. The existing 150 labels re-score identically (0.966/0.913,
  κ = 0.835) behind a banner saying they describe the superseded rubric. Phase 0.5 is
  **not** re-judged under v2 — that would swap a pre-registered result for a post-hoc one.
- **A new `mixed_rejection_then_fabrication` flag** is emitted per judgment, so §6.1's
  required label-boundary sensitivity on that pinned choice is computable later without
  re-judging 32,680 rows. Cheaper to add now than to regret after the run.
- **§11 pre-registered before any 0.5b data existed**, with the §10 amendment logged.
  The consequential pre-commitments: strata are the **38 native categories, the
  conservative choice** (14,831 blocked pairs vs 27,939 coarse — coarsening can only
  raise τ, so this forecloses "you loosened the strata until it cleared 0.50"), the
  coarse-13 map is fixed in full as a secondary that can never be the decision
  statistic, and a **>70%-at-zero floor check** reports the run inconclusive rather than
  negative. §11.0 also discloses honestly that the probe was pre-registration and saw
  marginals on ~10% of the set — while τ was never computed on probe data and must not be.
- **Manifest frozen**: 817 prompts, built by a script whose real job is refusing to ship
  the Phase 0.5 defects. 0 placeholders (V3 shipped 42), 0 unsourced ground truths (V3:
  94/98 `factual`), 0 duplicate uids, merge map verified a strict partition.
- **Three scripts took `--dataset`, verified two ways.** Phase 0.5 re-runs
  **byte-identically** (report.md and every number), and the 0.5b path was dry-run on
  synthetic data because the analyzer had never seen 38 strata — it discriminates
  correctly (high shared signal → τ_corr +0.966 GO; low → +0.055 NO-GO) and no stratum
  trips §6.7. Nothing synthetic was written under `results/`.
- Cost estimate for judging raised **~$50 → ~$70**: v2 roughly doubled the judge system
  prompt (~$20 over 32,680 calls) and TruthfulQA ground truth is longer than V3's
  one-liner. Caching still unavailable (1,270 tokens vs Haiku's 4,096 minimum).

Newest first. One entry per working session: what changed, what it cost, what broke.

### 2026-08-27 (later) — Phase 0.5b planned; TruthfulQA probe built

Strategy session. No spend, no new data.

- **Decided the fix for the NO-GO is a new benchmark, not more samples.** Phase 0.5b
  re-runs the pilot on **TruthfulQA**: 817 prompts, 38 categories, adversarial by
  construction, real sourced ground truth, public. It removes the floor effect (prior
  results show Mixtral at 17% overall), removes the asserted-fake and
  judge-parametric-knowledge problems, and removes the "you critiqued your own
  benchmark" objection in one move. Full to-do list above.
- **Built `scripts/probe_truthfulqa_rates.py`** — an ~$4 feasibility screen gating the
  ~$70 run. TruthfulQA may be saturated for *this* panel (the existing rate data is
  Mixtral and Llama-4-Maverick, neither of which we run).
- **Caught a real bug in my own probe via synthetic testing.** The first version tested
  between-prompt spread by counting distinct P̂ values. That does not work: at k=5 a
  *constant* true rate of 0.25 yields P̂ ∈ {0, .2, .4, .6} from binomial noise alone,
  and the check passed a perfectly-uniform synthetic set. A variance-vs-noise-floor
  ratio was better but had too much sampling error at n=40 (both a spread and a uniform
  set read ~1.4x). Replaced with a **chi-square test of homogeneity of proportions**,
  which discriminates cleanly at n=80, k=10: real spread → 2.31 (p=4e-10), all-prompts-
  equal → 1.01 (p=0.45). Defaults raised to n=80, k=10 accordingly.
- **Corrected the venue contradiction.** This file listed "ICLR Sept 24, unverified" as
  a blocker while `DEADLINES.md` — authoritative on dates — says ICLR is off the table
  and ICML 2027 (~late Jan) is the target. Removed. Also noted that one of the two
  contingencies that killed the ICLR option is now obsolete (the pilot is done, and we
  are ~2.5 weeks ahead of the ICML schedule); the other, unanswered advisors, is now the
  critical path.

### 2026-08-27 — ground-truth defects found during hand-labelling

Sein spotted wrong ground truths while labelling. Investigated; it is real and it is
worse than the individual cases. Full write-up in `CONTEXT.md` → "Asserted-fake ground
truth is unverified". No spend.

- **The "ground truth" for the decision-surface categories is an unverified assertion**
  copied from `data/entity_lists/*.json` by `build_borderline_benchmark.py`. There is no
  verification step in the path.
- **The old fix did not hold.** `remove_ground_truth_errors.py` cleaned only
  `prompts.jsonl`, so "The Sapphire Coast" — a real NSW region this repo already knew
  was mislabelled — re-entered the **primary set** through the §4.1 pool top-up, on 4
  prompts. Patch source lists, not downstream files.
- **Three confirmed-real entities asserted fake:** The Sapphire Coast, Tales from the
  Borderlands (Telltale game), The Silent Cartographer (Halo level).
- **33 of 99 entities are human names**, which cannot be asserted fake at all — 58 of
  169 primary `plausible_fake` prompts. That subset needs replacing, not auditing.
- **42 primary-set prompts still carry `[placeholder]` tokens.** Possibly part of why
  `ambiguous` is floor-degenerate: a placeholder is not a question, so every model
  hedges and P̂ pins at 0.
- **Tested, and it does not rescue the NO-GO.** This defect has exactly the shape that
  could fake one (fixed per prompt → invisible to τ_self → uncorrected by §6.2 → but
  asymmetric between models). Dropping every problem class moves τ_corr 0.310 → 0.323;
  dropping `people` moves it *down* to 0.256. Nothing nears 0.50. `books`, the most
  defensible subset, gives the lowest τ_corr (0.123) — opposite to what an artifact
  story predicts.
- **Built `scripts/audit_ground_truth.py`** — impact-ranked worksheet plus a `--score`
  sensitivity recompute.
- **Diagnosed the `[placeholder]` root cause: three compounding bugs** (details in
  `CONTEXT.md`). `build_benchmark_v2.py:53-55` fails open — a template variable with no
  entity pool becomes the literal string `[var]` and ships as data. `load_entities()`
  reads only one category's pool file, so cross-category variables can never resolve.
  And `prompts.jsonl` is out of sync with today's entity lists, so **regenerating
  produces a new dataset version rather than a repair** — do not mix a regenerated set
  with these results.
- **§5.2 labelling continues on the existing sample. 18 of the 150 items are malformed
  (12%);** `--score` now splits κ and the per-model gap into well-formed vs malformed,
  and the labelling UI flags a malformed item on screen and says to label it anyway. No
  redraw: a redraw would disturb the (model × category × judge label) stratification,
  shrink n, and discard the information that the malformed items carry about whether the
  judge handles broken input symmetrically across models.
- **Consequence for the paper: absolute rates from this run are unquotable.** Ordering
  survives; rates are measured against ground truth known to be wrong.

### 2026-08-26 (late) — diagnosis recorded, §5.2 tooling built, judging script fixed

No new data, no spend. Everything here is analysis, tooling and write-up.

- **The NO-GO diagnosis is now permanent, not just a chat finding.** The tie-ceiling,
  floor-effect, rescue-attempt and coarse-vs-fine tables run on every
  `analyze_phase05.py` invocation via `posthoc_ceiling_and_floor()`, labelled
  **NOT PRE-REGISTERED** in the source, in the JSON (`feeds_decision_rule: false`) and
  in the report, which places them after the verdict. The durable write-up is in
  `CONTEXT.md` → "Floor effects and the τ_b tie ceiling", with explicit
  "checked, do not re-litigate" and "do not repeat these rescue attempts" markers.
- **A real gap in §6.2 is documented:** the disattenuation cannot correct a
  between-model tie asymmetry, because each τ_self compares two halves of the same
  model, which share a tie structure. Any future τ-based design must report the
  ceiling alongside τ_corr. It did not invalidate this verdict (max reachable
  τ_corr = 0.998 on the primary).
- **§5.2 tooling built** — `scripts/run_judge_validation.py`, with `--draw` / label /
  `--score`. The 150-item sample is drawn (seed 20260826). Three things it enforces
  that the spec does not spell out: blinding (the UI never shows the judge's label),
  the judge's own rubric on demand (agreement against a private standard would measure
  rubric mismatch), and inverse-probability weighting so κ can be read back to
  population prevalence — a label-stratified sample does not estimate population κ,
  since κ depends on marginal prevalence.
- **Fixed both `run_phase05_judging.py` reporting defects** and extracted the summary
  into `report_state()`, now also printed on the nothing-to-do path so checking state
  costs nothing. Its numbers agree with `analyze_phase05.py`.
- **Established that the 3 remaining unlabelled samples are permanent.** They are judge
  JSON-parse failures at temperature 0, so retries replay identical malformed output.
  The script now says so instead of inviting another retry loop.

### 2026-08-26 (night) — judging recovered, pilot returned NO-GO

**The pilot has a verdict: NO-GO on the pre-registered §7 rule.** τ_corr = 0.3098,
bootstrap 95% CI [0.1913, 0.4467], against thresholds of 0.50 and 0.30. Full numbers
and interpretation are in "THE RESULT" above; `results/phase05/analysis/report.md` is
the complete §6–§7 report.

- **`--retry-failed` recovered 9,208 of 9,213** in ~60 min at 2.6/s for ~$16. Credit was
  available again. The 3 that remain are judge-output JSON parse failures at
  temperature 0, so they are deterministic and unretryable; they leave their pairs at
  k_eff = 19 and cost nothing. Two further retry invocations were wasted confirming this.
- **The §5.1 gate cleared** at a 0.01% unrecovered rate, so the verdict is the real
  pre-registered one, not the provisional path.
- **This is a high-reliability negative.** τ_selfA = 0.826, τ_selfB = 0.781, both about
  double the 0.40 measurement-failure floor. §7 row 3 does not apply and escalating k to
  40 is not indicated. ρ_corr = 0.331 confirms it is not an artifact of the τ
  disattenuation heuristic. The CI *upper* bound is below the GO threshold.
- **`ambiguous` was eliminated by the §6.7 degenerate rule** — 3 distinct P̂ values
  across 120 prompts for both models, a floor effect §4.1 explicitly anticipated. The
  decision surface ran on two categories, not three. Including `ambiguous` would have
  lowered τ_corr, so the exclusion favoured the claim.
- **The label-neutrality test failed** (MH OR = 4.31, p < 1e-5) — and the test cannot
  distinguish label corruption from the confabulation→length mediation it was designed
  around, so §6.5.4's truncation confound is neither closed nor proven. A defect in the
  pre-registered check, now written up as such rather than reported as a pass or a fail.
- **Both secondary results landed in the expected direction and are publishable
  independently of the ordering claim:** Δ_artifact = +0.118 and stratification
  inflation = +0.110.
- Spend: ~$16. Judging total across both runs is under the ~$50 estimate.

### 2026-08-26 (evening) — analysis script written; judging found to be 1/3 unlabelled

**`scripts/analyze_phase05.py` implements spec §6–§7 in full.** Runs in ~2 s including
the pre-registered 1000-iteration nested bootstrap, and is deterministic across runs
and across `PYTHONHASHSEED` values (verified).

- **Judging is not finished.** `wc -l` read 28,160 and the job exited cleanly, but
  32.72% of rows are `judge_failed` with no label — the Anthropic credit balance ran
  out at row 1,896. `--retry-failed` recovers them for ~$16. The judging script *did*
  print the correct 32.72% warning at the end of its log; it scrolled past unnoticed
  because the row count looked complete.
- **The analysis script withholds the §7 verdict** rather than computing one, because
  §5.1 says a run above 2% judge failure is an infrastructure failure and is re-run,
  not analysed. `--ignore-failure-gate` exists for previews and stamps every output
  provisional.
- **Found a k_eff counting defect in `run_phase05_judging.py`** that under-reported
  damaged pairs by 35× (13 reported vs 464 actual) by keying a `defaultdict` on
  successes only. Found a second one in the same summary: because writes are
  append-only, its `failed_rows / total_rows` rate would read 24.65% even after a
  fully successful `--retry-failed` and never clear. The analysis script gates on the
  *unrecovered* rate instead, verified to reach 0.00% against a simulated retry.
  Neither defect touched any label; both are reporting-only. Not yet fixed in the
  judging script.
- **Do not run the judge preflight from a Claude Code shell.** It exports
  `ANTHROPIC_BASE_URL` and its own key, and `load_env_file(override=False)` lets the
  shell beat `.env`, so the call lands on an Apple-internal gateway and fails with
  `no accounts available can serve requests` — an error about the wrong endpoint, not
  about the account. Stripping those variables then fails with `Connection error`
  because the agent sandbox has no outbound HTTPS. Same class of false diagnosis as
  the "100% retry failure" recorded below; neither result measures the account.
- **Three implementation choices the spec left open**, each marked `CHOICE` in the
  source: blocked Spearman is the partial ρ controlling for a stratum indicator;
  residualisation uses stratum fixed effects with one pooled slope; question length is
  proxied by whitespace word count (no tokenizer installed — and because τ_b is
  rank-based, the proxy cannot affect the two association rows, only the residualised
  one).
- **Two defects found and fixed in my own first pass**, both of which would have been
  silent: the §6.1 label-boundary variants were dividing a variant τ_cross by the
  *label-2-only* reliabilities, mixing two definitions inside one ratio; and the
  per-category bootstrap seed was derived from `hash(category)`, which Python salts
  per process, so those CIs were irreproducible between runs.
- **Reported a bias the spec's procedure has and does not mention.** The §6.6 nested
  bootstrap biases τ_selfA/τ_selfB *downward* (extra completion-level noise attenuates
  a reliability), which biases resampled τ_corr *upward*. Since §7 tests the CI lower
  bound, the bias is anti-conservative — it makes GO marginally easier than the
  nominal 0.30 threshold implies. The procedure is pre-registered and was not changed;
  the direction is now stated in the report so a borderline lower bound can be weighed
  correctly.
- Spend: $0. No API calls.

### 2026-08-26 (day machine) — generation complete

**28,160 / 28,160 completions, all 1,408 (uid, model) pairs at k=20.** ~14 hours wall
clock at 0.56/s. No pilot judgments yet.

- **Caught a keying bug before it corrupted the result.** V3 and the pool files reuse
  the same id space for *different* questions, so 54 ids collided; the resume logic
  skipped the second prompt of each pair. Worst consequence was latent — the judging
  script keyed `ground_truths` on `id`, which would have paired 54 prompts with the
  **wrong ground truth** and mislabelled them. Fixed by namespacing ids as
  `uid` (`v3:` / `pool:`) with a build-time uniqueness assertion. **No regeneration
  needed** — every row stores its `question`, so `scripts/migrate_completions_to_uid.py`
  re-keyed on that.
- **354 failures were a transient provider outage**, one contiguous burst near the end
  of the run, all `503 Service unavailable` / connection errors. Two retries from a real
  shell recovered all of them.
- Two wrong diagnoses corrected along the way: the failures were *not* caused by
  unsubstituted `[placeholder]` tokens (67 of 69 placeholder prompts generated fine),
  and a "100% retry failure" was a sandbox with no outbound HTTPS, not a real result.
- **Judge preflight passed with good reasoning** — `claude-haiku-4-5` routed an
  `ambiguous` prompt to CATEGORY 4 and cited the rule it applied.
- **Recorded for later: 69 of 449 V3 prompts contain unsubstituted `[placeholder]`
  tokens** ("What is the capital of [country]?"). A pre-existing benchmark defect
  inherited from the thesis, ~15% of prompts. Needs a decision before Phase 1 — a
  reviewer will notice.
- Spend: ~$9 generation. Together balance ~$47.

Commits: `020858b` → `fdab540`.

### 2026-08-25 (day machine)

Phase 0.5 went from a sketch to a fully instrumented, pre-registered experiment. No
pilot data collected yet.

- **Pre-registration written and amended four times, all pre-data.** Design, estimator,
  and a binding GO/NO-GO rule are frozen in `PHASE_0.5_SPEC.md`.
- **Category admission gated on ground-truth verifiability.** `factual` and
  `borderline_obscure_real` have ground_truth fields containing no actual facts, so the
  judge falls back on its own knowledge and both models' errors correlate through it —
  inflating τ toward a false GO. Both demoted to a labelled diagnostic set; primary
  surface is now `plausible_fake` + `nonexistent` + `ambiguous` (409 prompts).
- **All three models replaced.** `/v1/models` lists dedicated-endpoint-only models, so
  it is not an availability check; probing showed Together's serverless tier here serves
  exactly three chat models. Both thesis models are unreachable. Judge moved to Anthropic
  because family independence is unsatisfiable within Together.
- **`max_tokens` 256 → 2048**, set from measured natural completion length (the two
  models differ ~7× at the median).
- **Two pre-registered checks were wrong and were corrected before data:** a
  length-residualization that would have controlled a mediator and manufactured a false
  NO-GO, and a smoke test that sampled one of seven categories.
- Infrastructure: `.env` loading, `finish_reason` instrumentation, decoding-config
  fingerprinting, stratified sampling, adaptive progress reporting, results sync.
- **Spend so far: ~$0.50** (preflights, probes, two smoke tests). Together balance $56.

Commits: `44fd4dc` → `c5001ae`.

### Operational notes learned the hard way

- **`nohup … > file &` produces an empty log for a long time.** Python block-buffers
  stdout when it is redirected, and the progress lines only flush every
  `max(20, min(500, n/20))` completions — 500 at full scale, so ~15 minutes of silence
  at the start. Check `wc -l` on the output file, not the log.
- **`tail -f` is just a viewer.** Ctrl-C stops watching, not the job. The job is the
  detached PID.
- **Display sleep ≠ system sleep ≠ lid close.** Screen going dark is harmless;
  `caffeinate -i` blocks idle system sleep; **nothing** short of an external display
  prevents clamshell sleep. Leave the lid open.
- **Check the power source before starting a multi-hour run.** A ~14-hour job on a
  ~13-hour battery loses regardless of caffeinate, because critical-battery sleep
  overrides the assertion.
- **Long runs are resumable by design** — re-running the same command continues from
  the last completed row. A sleep or crash costs time, never data.
