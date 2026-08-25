# Research Paper — Session Context

**If you're a fresh Claude Code session on any machine, read this first.** This file exists so that a clean session can catch up on the project without needing access to the local `~/.claude/` auto-memory (which does not sync via git).

Last updated: 2026-08-24

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

- **Thesis**: FROZEN. Submitted Mar 27, 2026. Lives in `thesis/`. Do NOT edit unless explicitly asked.
- **Paper**: active. Lives in `research_paper/`. Reframed by Boaz on May 1, 2026.
- **Current phase**: Phase 0 (Setup). See `PLAN.md` for the phased roadmap.
- **Blocking**: Sunny response (email sent ~Aug 24, 2026), Boaz credit clarification (email draft below, unsent).
- **Realistic primary venue target**: ICML 2027 (~late Jan 2027 deadline). ICLR 2027 is a stretch sprint.

---

## The paper's reframed pitch (from Boaz May 1)

**"Predicting hallucination risk *before* generation, using prompt-level geometric features."**

- Geometry = tool. Prediction = goal.
- Three contributions: (1) pre-generation prediction benchmark, (2) computationally cheap geometric method, (3) practical applications (inference-time flagging, training data curation, model routing).
- Must beat or Pareto-dominate existing baselines (semantic entropy, P(true), self-consistency, probe-based).

**Load-bearing claim** the paper depends on: *"Hallucination is a property of the prompt, not the model."* Operationalized by computing pairwise Kendall's tau between per-model rankings of prompt hallucination probability. High tau ⇒ prompt-driven. Low tau ⇒ paper's framing collapses.

The thesis's fine-tuning story (Ch 7) is demoted from co-equal claim to a downstream-application subsection.

---

## Advisor context

- **Boaz Barak** (primary faculty advisor): approved publication path May 1, 2026. Has limited time. Advises from a distance. Provided the reframe. Provided Codex credits.
- **Sunny Qin** (PhD student, advised by Sham Kakade + David Alvarez-Melis): primary technical advisor for the paper. Shaped the thesis experimental design substantially. Re-engagement email sent ~Aug 24, 2026, awaiting response.
- **Co-authorship**: unresolved. Sunny should be co-author given her design contribution. Confirm with her.

Detailed advisor conversation history is in local auto-memory: `~/.claude/projects/-Users-sein-.../memory/advisor_comms.md` (does NOT sync via git).

---

## Load-bearing files in the repo

| File | Purpose |
|---|---|
| `research_paper/CONTEXT.md` | This file — session entry point |
| `research_paper/PLAN.md` | Phased roadmap for the paper |
| `research_paper/DEADLINES.md` | Venue deadlines + working-backwards timelines |
| `research_paper/RESEARCH_PAPER.md` | Boaz meeting notes (May 1, 2026) — historical context for the reframe |
| `JUDGE_CONTAMINATION_ISSUE.md` | Methodology bug caught + fixed in thesis; paper inherits clean data |
| `thesis/` | FROZEN — do not edit |
| `README.md` | Project-wide overview (from Dec 2025 class-project era, dated but still orients newcomers) |

---

## Do NOT do

- ❌ Edit any file in `thesis/` unless explicitly asked. The thesis is shipped.
- ❌ Start expensive multi-model inference experiments before Sunny signs off on the design.
- ❌ Chase GPT-5.6 / Llama 5 / other newer model releases — lock to current model versions.
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

**Judge API failure contamination** — Fixed Mar 11 and Mar 21, 2026. Silent judge failures used to inject fake "Refused" votes. Fixed in `judge_client.py` and `consensus_judge.py`. Full details in `JUDGE_CONTAMINATION_ISSUE.md`. Any new judge pipeline for the paper must exclude failed judges from the vote.

**CoT contamination** — CoT Verification was excluded from the thesis (API failure artifact) but is STILL PRESENT in several scripts and CSVs. Before adding any number/figure/table: trace to source → verify it excludes `cot_verification`. Known contaminated: `scripts/analyze_v5_prefixes.py`, `src/evaluation/prefix_analysis.py`, `v5_prefix_metrics.csv`, `v5_category_metrics.csv`.

**Clean data**: V3 (449 prompts), TruthfulQA (3,268), cross-cat ablation (2,694) — verified 0 failures.

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
