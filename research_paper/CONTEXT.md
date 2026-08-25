# Research Paper — Session Context

**If you're a fresh Claude Code session on any machine, read this first.** This file exists so that a clean session can catch up on the project without needing access to the local `~/.claude/` auto-memory (which does not sync via git).

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
| `research_paper/CONTEXT.md` | This file — session entry point |
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

- Auto-memory at `~/.claude/projects/.../memory/` does NOT sync via git. That content is mirrored here in CONTEXT.md and in the other repo docs. If you edit CONTEXT.md, also update `~/.claude/projects/.../memory/MEMORY.md` on this machine so the local auto-memory stays in sync.
- Local `.env` with API keys must be reconfigured per machine (never committed).
- Together AI is used for open-model inference (Mixtral, Llama). API key required.
- `python3` not `python` on the main machine — verify on any new machine.
