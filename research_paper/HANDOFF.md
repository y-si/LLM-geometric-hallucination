# HANDOFF — live project state

**Read `CONTEXT.md` first** for orientation (what the project is, communication style,
methodology rules). This file is the opposite: purely volatile state — what is running
right now, what was just done, what to do next.

Update this at the end of every session. If it disagrees with your memory, trust this
file.

**Last updated: 2026-08-25**

---

## Running right now

| Job | Machine | Status | Output |
|---|---|---|---|
| _(none)_ | — | — | — |

> When you start a long job, add a row: what, which machine, when started, where the
> log is. When it finishes, move it to the session log below and clear the row.
> **Never run generation or judging on two machines at once** — they write to separate
> files and you pay twice for the same completions.

---

## Next action

**Run the full Phase 0.5 generation.** Everything upstream is verified: manifest frozen,
models probe-confirmed serverless, preflight passed, smoke test clean at n=14.

```bash
# rotate keys FIRST if they were exposed — the process holds the key in memory
nohup python3 scripts/run_phase05_generation.py > results/phase05/gen.log 2>&1 &
tail -f results/phase05/gen.log
```

- ~28,160 completions, **~10 hours**, fully resumable (a crash or closed laptop costs
  only the in-flight batch — just re-run the same command).
- Costs ~$5–9 on Together. **Zero Claude Code quota** — it is plain Python hitting
  provider APIs.

Then, in order:

```bash
python3 scripts/run_phase05_judging.py --preflight   # 1 real judgment, read the reasoning
python3 scripts/run_phase05_judging.py --limit 20    # smoke test
python3 scripts/run_phase05_judging.py               # full, ~$50 on Anthropic
```

---

## Blocked / waiting

| Item | On whom | Since | Notes |
|---|---|---|---|
| Boaz credit clarification | Boaz | email drafted, **not sent** | Decides whether Phase 1 can use closed frontier models. Draft in `CONTEXT.md`. Urgent if ICLR is live. |
| Sunny Zoom | Sunny | she offered "next week" | Propose **late** in the week so the τ number is in hand. Send her `PHASE_0.5_SPEC.md` beforehand. Co-authorship still formally unresolved. |
| ICLR 2027 deadline | verification | Sunny says **Sept 24** | Unverified. Check iclr.cc / OpenReview. 30 vs 37 days changes the plan. |

---

## Main remaining build

**The analysis script (spec §6 and §7).** Nothing else stands between pilot data and a
GO/NO-GO verdict. Needs: blocked within-category τ_b, split-half noise ceiling,
attenuation correction, nested bootstrap, Δ_artifact, the §6.5 confound checks
(including the label-neutrality test), and the §7 decision rule.

This is the piece where a subtle error silently produces a confidently wrong verdict —
two pre-registered checks have already had to be corrected before seeing data. Write it
carefully and against the real data shapes in `results/phase05/*.jsonl`.

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

Newest first. One entry per working session: what changed, what it cost, what broke.

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
