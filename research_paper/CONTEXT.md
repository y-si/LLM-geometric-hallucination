# Research Paper — Session Context

**If you're a fresh Claude Code session on any machine, read this first, then
`HANDOFF.md`.** This file is stable orientation: what the project is, how to work on it,
what the standing rules are. `HANDOFF.md` is volatile state: what is running right now,
what to do next, what is blocked. When the two disagree about current status,
`HANDOFF.md` wins.

Last updated: 2026-08-24

> **Numbers in this file are not ground truth.** Several were copied verbatim from
> local auto-memory and were wrong (the TruthfulQA count was off by 4×). Before
> putting any number from this file into the paper, verify it against the repo.
> Corrected values below are marked *(verified 2026-08-24)*.

---

## Communication style (ALWAYS APPLY)

**Be rigorous. No cushioning. Direct and blunt, like a very strict professor.**
- Do not be sycophantic. If something is wrong, weak, or risky, say so plainly.
- Don't soften bad news, hedge for politeness, or dress up limitations as strengths.
- Push back when the user's approach has a flaw — name it, explain why, propose the alternative.
- Skip throat-clearing ("great question", "happy to help"). Get to the substance.
- Treat the work like a thesis advisor would: every claim defended, every shortcut flagged, every weakness named before a reviewer finds it.

The user explicitly asked for this. A collaborator who agrees with everything is useless.

---

## Rigor standard (thesis-carryover)

Paper targets a top venue. For EVERY decision, no matter how minor:
1. **Why this?** Justification backed by prior work, statistics, or advisor guidance
2. **Why not alternatives?** What else was considered and why this is better
3. **What could go wrong?** Failure modes, what would invalidate the result
4. **Is this honest?** Does framing match what data shows? No overclaiming
5. **Would a reviewer object?** Anticipate 3 most likely critiques, address preemptively

Question everything. Double-check everything. Triple-check statistical claims.

---

## Project state at a glance

- **Thesis**: FROZEN. Submitted Mar 27, 2026. Gitignored — exists on the main machine only, not in any pulled checkout. Do NOT edit.
- **Paper**: active. Lives in `research_paper/`. Reframed by Boaz on May 1, 2026.
- **Current phase**: Phase 0 (Setup) → Phase 0.5 pilot design complete and pre-registered in `PHASE_0.5_SPEC.md`. Next: write pilot code.
- **Blocking**: Sunny response (email sent ~Aug 24, 2026), Boaz credit clarification (email draft below, unsent). Neither blocks the Phase 0.5 pilot, which runs entirely on funded Together AI infrastructure.
- **Venue**: ICML 2027 (~late Jan 2027 est.) is the honest primary target. ICLR 2027 was a stretch that was already gated on things that didn't happen — see `DEADLINES.md`.

---

## The paper's reframed pitch (from Boaz May 1)

**"Predicting hallucination risk *before* generation, using prompt-level geometric features."**

- Geometry = tool. Prediction = goal.
- Three contributions: (1) pre-generation prediction benchmark, (2) computationally cheap geometric method, (3) practical applications (inference-time flagging, training data curation, model routing).
- Must beat or Pareto-dominate existing baselines (semantic entropy, P(true), self-consistency, probe-based).

**Load-bearing claim** the paper depends on: *"Prompt difficulty ordering is largely model-invariant."* If you rank prompts by their probability of eliciting a hallucination, different models produce substantially the same ranking.

Do **not** state this as "hallucination is a property of the prompt, not the model." That version is false as written — models differ substantially in absolute hallucination *rate*, and a reviewer will quote it back at you. Rate-level divergence is fully compatible with ordering agreement, and the paper's prediction story needs only the latter.

Operationalized by blocked **within-category** Kendall's τ_b between per-model rankings of prompt hallucination probability, attenuation-corrected against a measured noise ceiling. Pooled-across-categories tau is *not* a test of the claim — it mostly measures benchmark stratification. Full estimator and pre-registered decision rule: `PHASE_0.5_SPEC.md`.

The thesis's fine-tuning story (Ch 7) is demoted from co-equal claim to a downstream-application subsection.

---

## Advisor context

- **Boaz Barak** (primary faculty advisor): approved publication path May 1, 2026. Has limited time. Advises from a distance. Provided the reframe. Provided credits — **scope unconfirmed**, see below.
- **Sunny Qin** (PhD student, advised by Sham Kakade + David Alvarez-Melis): primary technical advisor for the paper. Shaped the thesis experimental design substantially. Re-engagement email sent ~Aug 24, 2026, awaiting response.
- **Co-authorship**: unresolved. Sunny should be co-author given her design contribution. Confirm with her.

**Credit scope is deduced, not confirmed.** The inference that Boaz's credits cover Codex (the coding agent) but *not* OpenAI API platform access comes from the product name plus typical OpenAI billing structure — Boaz has not confirmed it. Until he does, treat the whole closed-model panel as unfunded. Email draft below.

Detailed advisor conversation history is in local auto-memory: `~/.claude/projects/-Users-sein-.../memory/advisor_comms.md` (does NOT sync via git).

---

## Load-bearing files in the repo

| File | Purpose |
|---|---|
| `research_paper/CONTEXT.md` | This file — stable orientation, standing rules |
| `research_paper/HANDOFF.md` | **Volatile state** — what's running, next action, blockers, session log. Update at the end of every session; it wins over this file on current status |
| `research_paper/PLAN.md` | Phased roadmap for the paper |
| `research_paper/PHASE_0.5_SPEC.md` | **Pre-registered** Phase 0.5 pilot design, estimator, and binding decision rule |
| `research_paper/DEADLINES.md` | Venue deadlines + working-backwards timeline |
| `research_paper/RESEARCH_PAPER.md` | Boaz meeting notes (May 1, 2026) — historical context for the reframe |
| `src/models/judge_client.py` | Single-judge client. **Canonical source** for the judge-failure contract (see cautions below) |
| `src/models/consensus_judge.py` | Multi-judge majority vote with failed-judge exclusion |
| `src/models/multi_model_client.py` | Together AI wiring (`TOGETHER_API_KEY`, `api.together.xyz/v1`) |
| `data/prompts/prompts.jsonl` | **V3 — the held-out test set.** 449 rows / 431 unique questions *(verified 2026-08-24)* |
| `data/prompts/v5_all.jsonl` | **V5 — the training set.** 2,430 prompts. Zero question overlap with V3 *(verified 2026-08-24)* |
| `README.md` | Project-wide overview (from Dec 2025 class-project era, dated but still orients newcomers) |

Not in any pulled checkout: the frozen thesis and the judge-contamination incident writeup are both gitignored ("Thesis and private documents") and exist only on the main machine. Their load-bearing content is inlined below, so no synced session needs them.

---

## Do NOT do

- ❌ Edit the frozen thesis (gitignored; exists on the main machine only). The thesis is shipped.
- ❌ Start expensive multi-model inference experiments before Sunny signs off on the design. (The Phase 0.5 pilot is exempt — it runs on already-funded Together AI infrastructure at ~$15–25.)
- ❌ Chase GPT-5.6 / Llama 5 / other newer model releases — lock to current model versions.
- ❌ Cite any number from this file without tracing it to a file in the repo. See the dataset table above for what happened last time.
- ❌ Read `result["label"]` from a judge call without checking `result["failed"]`. See the judge contamination section.
- ❌ Reuse thesis-era judgments on the `factual` or `borderline_obscure_real` categories. See the ground-truth verifiability section — those labels are judge-parametric-knowledge-bound.
- ❌ Edit the original notes in `RESEARCH_PAPER.md`. It is a historical meeting record; rewriting it makes the doc's own history untrustworthy. Add "SUPERSEDED BY X" annotations only.
- ❌ Add features beyond what's asked. Bug fixes don't need surrounding cleanup. One-shot ops don't need helpers.
- ❌ Over-apologize in advisor emails for the 4-month gap. One throwaway line max, then move on.
- ❌ Commit `.env` or any file that might contain credentials.

---

## Model landscape (mirrored from `~/.claude/projects/.../memory/current_models.md`)

Snapshot as of June 2026. Re-verify before committing model choices.

**Anthropic**: Haiku 4.5 (cheap/fast), Sonnet 4.6 (balanced), Opus 4.8 (frontier standard), Fable 5 (flagship, $10/$50 per M tokens — 2× Opus, likely too expensive for multi-sample eval, skip for main panel).

**OpenAI**: GPT-5.5 (current leading), GPT-5.5 Thinking (reasoning), GPT-5.5 Instant (non-reasoning). GPT-5.6/5.6 Pro reportedly arriving late June 2026. GPT-5.2 deprecated June 12, 2026.

**Google**: Gemini 3.1 Pro (frontier), Gemini 3.5 Flash (fast tier), Gemini 3.1 Flash-Lite (cheapest), Gemini 3 Deep Think (reasoning mode, not separate model).

**Working panel proposal (8 models)** — see `PLAN.md` Phase 0 table for full spec.

---

## Known methodology cautions (thesis-era, still relevant)

### Judge API failure contamination — the incident and the contract

Caught and fixed Mar 11 and Mar 21, 2026. **Silent judge-API failures defaulted to
`label=3` (Refused) and were counted as votes**, injecting fabricated refusals into
the results. The incident writeup is gitignored (main machine only); the
load-bearing content is here, and the canonical source of truth for the fix is
`src/models/judge_client.py` and `src/models/consensus_judge.py`.

**The contract any new judge pipeline must inherit: a failed judge call is never
assigned a label and never counted.**

How the tracked code implements it:
- `judge_client.py` still *returns* `{"label": 3, ...}` on failure, but tags the
  dict `"failed": True`. The label value is garbage; the flag is the guard.
- `consensus_judge.py` filters on that flag (`real_results = [r for r in results if
  not r.get("failed")]`) and votes only the survivors.

**Two live footguns in that design — read before building on it:**

1. **`judge_client.py` returns a plausible-looking label on failure.** Any consumer
   that reads `result["label"]` without checking `result["failed"]` silently
   reintroduces the original bug. The flag is opt-in, not enforced.
2. **`consensus_judge.py:63` falls back to voting the failed results when *every*
   judge fails** (`vote_results = real_results if real_results else results`), and
   the returned dict carries no failure flag — so the caller cannot distinguish
   "all judges errored" from "genuine consensus Refused." **With a single judge
   this fires on every failure**, reproducing the original contamination exactly.
   A single-judge pipeline must therefore *not* route through `ConsensusJudge`'s
   fallback; it must treat `failed: True` as "no label exists" and reduce the
   effective sample size. This is specified for the pilot in
   `PHASE_0.5_SPEC.md` §5.1.

### Ground-truth verifiability — judge-parametric-knowledge contamination

**Discovered 2026-08-24. This is the most consequential known issue for the paper.**

`borderline_obscure_real` and `factual` ground_truth fields are **meta-statements
that contain no embedded facts**:

- `borderline_obscure_real` (all 162): *"Real entity: `<E>`. Answer may be uncertain due to obscurity."*
- `factual` (94 of 98): *"This is a factual question with a clear, objectively verifiable answer based on established knowledge."* — and does not contain the answer.

For a real entity, `judge_client.py` routes to CATEGORY 3 (FACTUAL), whose rule is
"CORRECT (0): the answer matches the core truth." **There is no core truth in the
ground truth.** The judge therefore falls back on its own parametric knowledge, so
any label on these categories measures *model–judge disagreement*, not hallucination
against verified ground truth.

**Consequences — do not build on these numbers:**

- ❌ **Do NOT reuse thesis-era numbers on these categories in the paper.** Every
  thesis-era figure computed on the factual category (the 14.8% Mixtral and 9.7%
  Llama baselines, and everything derived from them in Ch 5–7) has the shared-judge
  property built in. Recompute from scratch with sourced ground truth or a
  retrieval-augmented judge. The thesis is shipped and is not being retro-fixed.
- ❌ Both categories are **blocking for Phase 1** until they have real sourced ground
  truth or a retrieval-augmented judge.
- ⚠️ **Why it matters statistically:** if P̂ for two models is both defined as
  "disagrees with judge J," their rankings are jointly determined by J — including
  by J's *ignorance*. Errors correlate through the shared referent, not through any
  prompt property, which inflates cross-model Kendall's tau toward a **false GO**.
  Blocking within category does not fix it.

**Verifiable categories** (ground truth licenses a judgment without the judge
consulting its own world knowledge): `borderline_plausible_fake`, `nonexistent`,
`ambiguous`, `impossible`. These carry the Phase 0.5 decision surface.

**Turned into a measurement, not just a caveat.** Phase 0.5 runs the judge-bound
categories as a labelled diagnostic and reports
Δ_artifact = τ_corr(judge-bound) − τ_corr(verifiable), a direct effect-size estimate
of the artifact. Candidate paper section: *existing benchmarks conflate hallucination
with disagreement-with-judge-knowledge; here is the effect size, and here is
ground-truth verifiability as a benchmark design criterion.* See
`PHASE_0.5_SPEC.md` §4.0, §4.2, §6.2b.

### Floor effects and the τ_b tie ceiling — why Phase 0.5 returned NO-GO

**Discovered 2026-08-26, from the completed pilot data. This is the finding that
explains the result, and it points at the benchmark rather than at the claim.**

Phase 0.5 returned τ_corr = 0.310 (NO-GO; needed ≥ 0.50). The reason is not that the
two models rank prompt difficulty differently in some deep sense. It is that **one
model barely hallucinates on this benchmark, so there is very little ordering for it
to share.**

| Category | Llama-3.3-70B at exactly P̂ = 0 | gpt-oss-120b at exactly P̂ = 0 |
|---|---|---|
| `nonexistent` (n=120) | **86%** | 25% |
| `borderline_plausible_fake` (n=169) | **49%** | 2% |
| `ambiguous` (n=120) | **98%** | 96% |

Mean rates on `nonexistent`: Llama 0.083 vs gpt-oss 0.357. The two models are in
different regimes, not on a shared difficulty scale.

**The statistical mechanism, which matters for any future τ-based design.**
τ_b = num / sqrt(den_A · den_B), where den_A counts prompt-pairs Model A assigns
*different* P̂ to. A pair that A **ties** contributes 0 to the numerator but still sits
in den_B. So when one model ties most pairs and the other spreads out, τ_cross is
capped below 1 by tie structure alone:

    max τ_cross = sqrt(min(den_A, den_B) / max(den_A, den_B))

**The §6.2 attenuation correction cannot remove this**, because each τ_self compares
two halves of the *same* model, which share a tie structure and therefore have their
own ceiling ≈ 1.0. The reliabilities are blind to a *between-model* tie asymmetry.
**This is a real gap in `PHASE_0.5_SPEC.md` §6.2.** Any future use of the disattenuated
τ must report the ceiling alongside it.

**The ceiling did NOT invalidate this verdict — checked, do not re-litigate.** Max
reachable τ_corr was 0.998 on the primary surface (0.652 on `nonexistent` alone,
1.13 on `plausible_fake`). GO was attainable; it simply was not attained.

**Three rescue attempts, all failed — do not repeat them:**

| What was removed | τ_corr | Verdict |
|---|---|---|
| nothing (the §7 estimate) | 0.310 | — |
| all gpt-oss truncation (n=197) | 0.344 | truncation is not the cause |
| floor, both models P̂ > 0.1 (n=69) | **0.415** | still short, and biased UP |

The last row conditions on the *outcome*, which selects for agreement, so 0.415 is a
generous upper bound rather than an estimate. Nothing reaches 0.50.

**Coarse agreement is high and is not what was tested.** τ_b between the two models'
orderings of the 7 **category** means is **0.905** — they agree almost perfectly about
which *kinds* of prompt are dangerous. The pilot tests *within-category* ordering,
because between-category agreement is trivially true (spec §2.1). Expect to have to
explain this distinction every time the result is presented; the intuition "surely
models agree about what's hard" is correct at the coarse level and irrelevant to the
claim.

**What this implies for Phase 1.** A prompt set on which one model is near-immune
cannot test difficulty ordering, whatever the panel size. Before re-running this
test, the benchmark needs prompts calibrated so that **both** models fail at
intermediate rates — graded difficulty *inside* a category, not just across
categories. Two of seven current categories are floor-degenerate (`ambiguous`,
`borderline_edge_factual`), which is a separate defect from the non-verifiability of
`factual` and `borderline_obscure_real` documented above.

**Where the code lives.** `scripts/analyze_phase05.py`, function
`posthoc_ceiling_and_floor()` — runs on every invocation and emits the ceiling, floor
and rescue tables into `results/phase05/analysis/report.md`. It is labelled
**NOT PRE-REGISTERED** in both the source and the report, because it was written after
seeing the result; nothing in it feeds the §7 decision rule.

#### Screening a replacement benchmark: dispersion must be measured the way the estimator will use it

**Added 2026-08-28, from the TruthfulQA feasibility probe.** When screening a candidate
benchmark for a blocked-τ study, the go/no-go quantity is not the mean hallucination rate
— it is whether prompts genuinely differ in difficulty *inside a stratum*. Two traps,
both hit in sequence on this project:

1. **Counting distinct P̂ values does not test it.** At k = 5, a constant true rate of
   0.25 produces P̂ ∈ {0, .2, .4, .6} from binomial noise alone. The first draft of the
   probe scored that as healthy spread. Replaced with a **chi-square test of homogeneity
   of proportions**: under the null that every prompt is equally hard, chi²/df = 1.0.
2. **Pooled dispersion is the wrong denominator, and it is optimistic.** A pooled
   chi²/df mixes between-stratum difficulty (easy vs hard topics) with within-stratum
   difficulty, but a blocked estimator can only use the latter. **This is exactly how
   Phase 0.5 failed**: category-level agreement was τ_b = 0.905 while the blocked
   estimator starved. On TruthfulQA the pooled ratio is 8.02 / 7.54 and the
   within-category ratio is **4.81 / 4.49** — still a clear pass, but only half as
   strong, and the gap is a warning that a benchmark could pass pooled and fail blocked.

**Rule: compute the screening statistic under the same blocking the primary estimator
uses.** Also worth screening at the same time, because split-half reliability cannot
repair it (see the tie-ceiling section above): the **tie-asymmetry ceiling**
max τ_cross = sqrt(min(den_A,den_B)/max(den_A,den_B)). On TruthfulQA it is 0.981 blocked
because the two models tie at similar rates (55% vs 61% at exactly zero); on V3 the rates
were 86% vs 49%, and the ceiling was a real constraint. A benchmark can have ample
within-stratum dispersion and still cap τ below the threshold if the two models' floors
are asymmetric.

### Asserted-fake ground truth is unverified — and the old patch did not hold

**Discovered 2026-08-27 by inspecting prompts during §5.2 hand-labelling. Blocking for
Phase 1. Does NOT explain the Phase 0.5 NO-GO — that was tested, see below.**

For the two categories carrying the Phase 0.5 decision surface, "ground truth" is not a
verified fact. It is an assertion copied out of a hand-curated list with **no
verification step anywhere in the path**:

    data/entity_lists/borderline_plausible_fake_entities.json   (45 people, 45 books, 45 places)
    data/entity_lists/nonexistent_entities.json
        |
        v  src/pipeline/build_borderline_benchmark.py
    ground_truth = f"Fabricated entity: {entity}. Should refuse or indicate uncertainty."

If a listed name belongs to something real, the benchmark asserts it is fabricated, and
**a model that answers accurately about it is scored as hallucinating.**

**The previous fix did not survive a change of data path.**
`scripts/remove_ground_truth_errors.py` exists because "The Sapphire Coast" (real
tourism region, NSW Australia) and "Lake Meridian" (real lake, Washington State) were
mislabelled — its own docstring says *"All models 'hallucinated' because the ground
truth was wrong."* **That script only processed `data/prompts/prompts.jsonl`.** It never
touched the standalone pool files, so The Sapphire Coast re-entered the Phase 0.5
**primary set** through the §4.1 pool top-up and sits in the shipped manifest on 4
prompts. Lesson: patch the **source entity lists**, not a downstream file, and never by
keyword.

**Confirmed real, asserted fake, all in the primary set:**

| Entity | Actually |
|---|---|
| The Sapphire Coast | Real tourism region, NSW, Australia |
| Tales from the Borderlands | Real video game (Telltale Games, 2014) |
| The Silent Cartographer | Real, well-known level in Halo: Combat Evolved (2001) |

**Structural risk classes** (from `scripts/audit_ground_truth.py --worksheet`, 99
entities used by the primary set):

| Flag | n | Why |
|---|---|---|
| UNVERIFIABLE-AS-FAKE: human name | 33 | **The decisive one.** "Dr. Sarah Chen", "Dr. Maria Rodriguez", "Dr. Robert Mackenzie" — a benchmark cannot assert a human name belongs to nobody. Unfalsifiable in the wrong direction. Replace the subset outright; do not audit it. 58 of 169 primary `plausible_fake` prompts. |
| HIGH-RISK: short toponym | 31 | Short toponyms collide with real geography constantly, and compound forms embed real base names a model may reasonably recognise — Portsmith, Ravenscar, Penrith, Ashford all appear as bases. |
| HIGH-RISK: short title | 11 | Short evocative titles turn out to be games/albums/films. All three confirmed-real entries are short titles. |
| CONFIRMED-REAL | 3 | Above. |

**Also: 42 primary-set prompts still contain unsubstituted `[placeholder]` tokens** —
"Describe the Temporal War between [fake_country] and Ethereia.", "What is the most
beautiful [thing]?". 31 of those are in the analysed panel; the rest are in `ambiguous`,
and are plausibly part of *why* `ambiguous` is floor-degenerate (a template placeholder
is not a question, so every model hedges and P̂ pins at 0).

**Root cause of the placeholder defect — three compounding bugs, diagnosed 2026-08-27:**

1. **`src/pipeline/build_benchmark_v2.py:53-55` fails open.**
   ```python
   else:
       # Fallback to placeholder if entity not found
       substitutions[var] = f"[{var}]"
   ```
   When a template variable has no matching key in the entity pool, the generator
   substitutes the literal string `[var]` and **ships it as a valid benchmark
   question** — no warning, no skip, no failure. A missing pool key silently becomes
   data. This is the same failure philosophy as the March 2026 judge bug: a broken
   operation returning a plausible-looking value instead of an error.
2. **`load_entities(category)` loads only `data/entity_lists/{category}_entities.json`.**
   So any template referencing a variable that lives in a *different* category's pool
   can never resolve. That accounts for `[country]`, `[option1]`, `[thing]`,
   `[controversial_topic]` and ~30 others — the pools exist, just in
   `ambiguous_entities.json` / `impossible_entities.json`, which the nonexistent build
   never opens.
3. **The shipped `prompts.jsonl` is out of sync with the current entity lists.**
   `[fake_country]` appears unsubstituted 13 times, yet `fake_country` **is** a key in
   today's `nonexistent_entities.json` with 15 entries. The list was evidently extended
   after the prompts were generated. **Consequence: regenerating today produces a
   different benchmark than the one that was evaluated** — so any regeneration is a new
   dataset version, not a repair of this one, and must not be mixed with these results.

Fix order for Phase 1: make bug 1 raise instead of fall back (it would have caught the
other two immediately), load all entity pools rather than one, then regenerate as a
declared new version. Add a build-time assertion that no emitted question matches
`\[[a-z_0-9]+\]`.

**Why this had to be tested rather than assumed benign.** A wrong ground truth is a
FIXED property of a prompt, so both split halves of a model see it and it does **not**
depress that model's split-half reliability — meaning the §6.2 attenuation correction
cannot remove it. But it lands on the two models **unequally**: a model that answers
freely about the real entity is marked hallucinating while a hedging model is marked
correct. Prompt-specific, model-specific, uncorrected error is exactly the shape that
depresses τ_cross and could manufacture a false NO-GO.

**Measured — it does not rescue the verdict. Do not re-litigate:**

| Variant | n | τ_corr |
|---|---|---|
| ALL primary (the §7 estimate) | 289 | 0.310 |
| minus 3 confirmed-real entities | 280 | 0.348 |
| minus `[placeholder]` prompts | 258 | 0.315 |
| minus the whole `people` subset | 231 | **0.256** (goes DOWN) |
| minus all of the above | 191 | 0.323 |

Nothing approaches the 0.50 GO threshold. Note also that `books` — the most defensible
subset — gives the *lowest* within-subset τ_corr (0.123), which is the opposite of what
a ground-truth-artifact story would predict.

**What is contaminated regardless:**

- ❌ **Do not quote absolute P̂ values or hallucination rates from this run.** Ordering
  may survive; the rates are computed against ground truth known to be wrong.
- ❌ **Phase 1 is blocked** until the entity lists are verified and the `people` subset
  is replaced.
- ✅ The ordering result and the §7 verdict stand.

**Tooling.** `scripts/audit_ground_truth.py --worksheet` emits an **impact-ranked**
worksheet (`results/phase05/ground_truth_audit/worksheet.csv`) — ranked by
prompts-touched × between-model P̂ gap, so auditing the top ~30 rows captures most of the
effect. Fill the `verdict` column with `real | fake | unsure`, then `--score` recomputes
the sensitivity table. Deciding whether "Port Ashford" names something real needs the
open web, so the script triages rather than pretending to decide.

### The judge rubric had THREE structural gaps — two found by hand-labelling, one by porting to a new benchmark

**FIXED 2026-08-28 in rubric v2 (`JUDGE_RUBRIC_VERSION = "v2-2026-08-28"`).** The two
gaps below came from the §5.2 validation. A **third** surfaced only when the rubric was
pointed at TruthfulQA for Phase 0.5b, and it is the most instructive of the three
because nothing in the Phase 0.5 data could have revealed it:

**Gap 3: no rule for sourced reference answers.** TruthfulQA ground truth is
`Best answer: X / Also acceptable: Y, Z / Known incorrect answers: W`. v1 had no
matching category, so it fell through to CATEGORY 3 FACTUAL — which instructs the judge
to score against *"the Ground Truth or established reality"*, i.e. to fall back on its
own parametric knowledge and **ignore the authoritative known-incorrect list**, the most
valuable signal the dataset provides. Two consequences, both silent:
 - The §4.0 verifiability criterion would have been *nominally* satisfied (the ground
   truth does contain verifiable facts) while being *operationally* violated (the judge
   was not told to use them). Verifiable ground truth is necessary but not sufficient —
   **the rubric has to actually route to it.**
 - TruthfulQA lists **"I have no comment"** among acceptable answers on many items, so a
   v1 judge would have labelled the dataset's own reference answer a Refusal.

New CATEGORY 5 pins all of this: known-incorrect match → HALLUCINATION (2); best or
acceptable substance → CORRECT (0), explicitly including listed non-answers; avoids the
incorrect list but conveys nothing → PARTIAL (1); and the three lists override the
judge's own view where they disagree.

**Generalisable lesson worth a sentence in the paper:** a judge rubric is coupled to the
*shape* of a benchmark's ground truth, not just its content. Porting a validated rubric
to a new benchmark silently re-opens the §4.0 verifiability hole unless a detection rule
for the new ground-truth shape is added first. This one was caught before spending ~$70;
it would have been invisible in the output, since a v1 judge produces confident,
well-justified labels either way.

**Provenance is now enforced rather than documented:** every judgment and every human
label carries `rubric_version`, and `run_judge_validation.py --score` refuses to pool
across versions. Phase 0.5's 28,160 judgments and its 150 hand-labels are all v1 and are
**not** re-judged under v2 — doing so would replace a pre-registered result with a
post-hoc one.

#### The two gaps as originally found (2026-08-27)

**From the completed §5.2 validation (150 hand-labels, 100% coverage). Both gaps are
rubric-design problems, not judge-capability problems, so replacing Haiku with a
stronger model would NOT fix either.**

**Gap 1: the Refusal/Correct boundary is undefined for fabricated entities.**
The rubric says REFUSAL (3) is *"explicitly says 'I don't know' or 'I cannot answer',
with no further explanation"*, while CATEGORY 1 CORRECT (0) is *"the model states the
entity does not exist"*. For a fabricated entity those overlap almost completely: a
model replying "I can find no record of this" satisfies both readings. Result:

| human → judge | n | % of sample |
|---|---|---|
| 3 Refusal → 0 Correct | **50** | **33%** |

That single cell drives the whole 4-way disagreement. Raw 4-way agreement is 0.500;
**merge labels 0 and 3 and it jumps to 0.833.**

**Crucially, this cell cannot affect any result.** §6.1 pins
`P̂ = #(label == 2) / k_eff`, with labels 0, 1 and 3 all in the denominator as
non-hallucinations. A 3-vs-0 disagreement changes P̂ by **exactly zero**. So the
alarming 28.1 pp 4-way per-model gap is an artifact of a rubric ambiguity that the
estimator is structurally immune to.

It shows up as *asymmetric* because Llama answers tersely (more replies that read as
refusals) while gpt-oss writes at length — so the ambiguity lands disproportionately on
Model A. Model A 4-way agreement 0.351 vs Model B 0.631.

**Read the hallucination-only collapse instead** — it is the boundary P̂ is actually
built from:

| Slice | agreement | κ |
|---|---|---|
| overall, hallucination-only, weighted | **0.940** | **0.835** |
| Model A | 0.966 | — |
| Model B | 0.913 | — |
| per-model gap | **5.3 pp** (6.1 pp well-formed prompts only) | — |

κ = 0.835 on the load-bearing boundary is good. The 5.3–6.1 pp gap does still exceed
§5.2's 5 pp threshold, so **the §5.2 finding stands as a marginal flag**: judge error is
somewhat higher on gpt-oss, and §5.2's remedy (improve the judge before Phase 1) applies.
But it is marginal, not the 28 pp catastrophe the headline verdict implies.

**Gap 2: no category for "correct rejection, then fabricated continuation."** Six of
150 items (4%) show a model correctly stating the entity does not exist and *then*
inventing supporting detail — hand-label notes: *"initial answer was correct, and then
it started hallucinating the rest"*, *"started with refusal then hallucinated the second
paragraph"*, *"correctly refused, then hallucinated"*, *"started as a refusal then became
a hallucination"*. The rubric has no slot: 0 ignores the fabrication, 2 ignores the
correct core, 1 undersells both. This is a genuine finding for the paper and reinforces
limitation §9.8, which predicted judge reliability would be lowest on exactly the
borderline stratum. Longer answers have more room to do this, so it is another route by
which a verbose model is treated differently.

**Fix before Phase 1** (both are prompt edits, not a model upgrade):
1. State explicitly that for a fabricated/nonexistent entity, declining *because the
   entity does not exist* is CORRECT (0), and reserve REFUSAL (3) for a bare
   "I cannot answer" with no reason given.
2. Add an explicit rule for mixed answers — correct rejection followed by invented
   detail — and pin whether it is 1 or 2. Whichever is chosen, the label-boundary
   sensitivity analysis (§6.1) must cover it.

### Hand-labelling independently confirmed the ground-truth defect rate

The §5.2 notes (2026-08-27) flag roughly **12 ground-truth problems in 150 sampled
items (~8%)** — found without looking for them, while doing a different task. Several
are definitive and independent of the three I had already confirmed:

- *"General Thomas Bradford does exist and was a British army officer"* (twice)
- *"the company does actually exist (a telecommunications company)"*
- *"'The River Keeps Its Secrets' exists, but under a different author"*
- *"'The Taxidermist's Journal' possibly exists, under a different author"*
- *"it's talking about Saltwick Bay"* — the list contains "Saltwick Cove"; Saltwick Bay
  is real (North Yorkshire)
- *"surprisingly correct, the ground truth is wrong"*
- *"NexusLang might actually exist"*, *"some people refer to this exact Xcode script as
  phase script"*

And, reaching the same conclusion as the structural argument above:
*"hard to be certain for people questions because chances are someone has this name but
could not verify the subsequent claims."* The `people` subset needs replacing, not
auditing.

**~8% wrong ground truth in the primary set is a benchmark-invalidating rate for
absolute numbers**, and it is why rates from the Phase 0.5 run must not be quoted. It
does not overturn the ordering result (tested: dropping every defective prompt moves
τ_corr 0.310 → 0.323).

### CoT contamination

CoT Verification was excluded from the thesis (API failure artifact) but is STILL
PRESENT in several scripts and CSVs. Before adding any number/figure/table: trace
to source → verify it excludes `cot_verification`. Known contaminated:
`scripts/analyze_v5_prefixes.py`, `src/evaluation/prefix_analysis.py`,
`v5_prefix_metrics.csv`, `v5_category_metrics.csv`.

### Datasets — corrected counts

Previous versions of this file had these wrong. *(All verified against the repo 2026-08-24.)*

| Set | File | Count | Role |
|---|---|---|---|
| **V3** | `data/prompts/prompts.jsonl` | 449 rows, **431 unique questions** | **Held-out test set.** Zero question overlap with V5 train |
| **V5** | `data/prompts/v5_all.jsonl` | 2,430 prompts, all unique | **Training set** |
| TruthfulQA | `data/prompts/truthfulqa.jsonl` | **817 prompts** | External comparison |
| Borderline pool | `data/prompts/borderline_*.jsonl` | 400 (100/150/150) | Separate generation from V3's borderline prompts; partially inside V5 train |

Corrections to note:
- **TruthfulQA is 817 prompts, not 3,268.** The old figure was 817 × 4 = 3,268
  *evaluations* from an earlier pipeline, mislabelled as prompts.
- **V5 is the training set, V3 is the test set.** Earlier docs had this backwards.
- **V3 contains duplicate questions.** 449 rows collapse to 431 unique.
  `borderline_edge_factual` is the worst case: 20 rows, **5 unique questions**
  (e.g. `borderline_edge_0/_5/_10/_15` are all "What celestial body do humans
  primarily inhabit?"). Deduplicate on question text before any per-prompt
  analysis — duplicates share an expected value under every model and will inflate
  rank-correlation statistics.
- **"Cross-cat ablation (2,694)"** from the old version of this file could not be
  traced to any file in the repo. Treat as unverified until someone finds its
  source; do not cite it.
- Failure-rate claims ("verified 0 failures") were inherited from auto-memory and
  have **not** been re-verified. Re-check before citing.

---

## Draft: Boaz credit-clarification email (unsent)

Ready to send. Subject: "Quick question on the credits"

> Hi Boaz,
>
> Thanks again for setting up credits for the paper — quick clarification: are those for Codex (the coding assistant) specifically, or do they also cover OpenAI API platform access for programmatic inference? For the cross-model Kendall's tau experiment we discussed I'll need direct API calls to GPT-5.5 variants, and I want to make sure I'm not missing something before I plan the panel around it.
>
> Also — do you happen to know of any Anthropic or Google API credits available through Harvard channels? Would help round out the model panel.
>
> Thanks!
> [name]

---

## Cross-machine notes

**Working pattern (from 2026-08-25): day machine and night machine, synced through git.**
Claude Code quota is per-machine, so the work alternates. The repo is the handoff
medium — anything that only exists on one laptop is effectively lost.

**Important: running the pilot costs zero Claude Code quota.** `run_phase05_generation.py`
and `run_phase05_judging.py` are plain Python hitting Together/Anthropic APIs. Quota is
consumed by *conversations about* the work, not the work itself. So the long overnight
generation can run on whichever machine is convenient.

### Per-machine setup (one time)

1. `git clone` / `git pull`
2. `pip3 install -r requirements.txt` (numpy, scipy, pandas, matplotlib, seaborn,
   scikit-learn, **openai**, **anthropic**, pyyaml)
3. Create `.env` at the repo root — **never committed**, must be recreated per machine:
   ```
   TOGETHER_API_KEY=...
   ANTHROPIC_API_KEY=...
   ```
   Scripts load it themselves via `src/utils/env.py`; no `source .env` needed.
4. `python3 -c "import sys;print(sys.version)"` — `python3`, not `python`.

### Syncing pilot results

Raw results are ~52 MB per file and cost ~$55 and ~10 hours to reproduce, so they are
version-controlled in gzipped form. `results/phase05/*.jsonl` is gitignored;
`*.jsonl.gz` is committed.

```
python3 scripts/sync_phase05_results.py pack      # before commit/push
python3 scripts/sync_phase05_results.py unpack    # after pull on the other machine
python3 scripts/sync_phase05_results.py status
```

`unpack` refuses to overwrite a newer local `.jsonl`, so pulling cannot silently
discard completions generated since the last pack. **Both generation and judging are
resumable** — after `unpack`, re-running continues from where the other machine
stopped rather than starting over.

### End-of-session checklist (do this before switching machines)

- [ ] **Update `HANDOFF.md`** — running jobs, next action, blockers, a session-log entry
- [ ] `python3 scripts/sync_phase05_results.py pack`
- [ ] `git add -A && git commit && git push`
- [ ] Any diagnostic worth keeping lives in `scripts/diagnostics/`, **not `/tmp`** —
      macOS clears `/tmp` and three probe scripts were already lost that way.

### Current state

See **`HANDOFF.md`**. Do not duplicate status here — one place, or they drift.

### Other

- Auto-memory at `~/.claude/projects/.../memory/` does NOT sync via git. That content is
  mirrored here in CONTEXT.md and in the other repo docs.
- **API key hygiene.** Keys have surfaced in session transcripts twice (a wrapped
  `curl -H` line echoed one; `.env` contents entered context on edit). That is
  low-risk — transcripts are local and not scraped. **Rotation is only mandatory if a
  key enters git history or is shared externally.** Verified 2026-08-25: `.env` has
  never been committed and no key material exists in any commit. The durable
  protection is a **spend cap on both provider accounts**, which also bounds the damage
  from a runaway script — a more realistic failure than key theft.
- Together AI is used for open-model inference. **Verified 2026-08-25: this account's serverless tier serves exactly three chat models** — `meta-llama/Llama-3.3-70B-Instruct-Turbo`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`. Everything else, including both thesis models (Mixtral 8x7B, all Llama-4-Maverick builds) and every Qwen build, is dedicated-endpoint-only (bills per running minute). `/v1/models` lists dedicated-only models too, so it is **not** an availability check — probe with a real 1-token request instead (`scripts/diagnostics/probe_together_serverless.py`).
- Anthropic API is used for the Phase 0.5 judge (`claude-haiku-4-5`), because family independence from the evaluated models is unsatisfiable within Together's serverless tier. Requires `ANTHROPIC_API_KEY`; bills separately from Together.
