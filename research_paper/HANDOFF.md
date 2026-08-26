# HANDOFF — live project state

**Read `CONTEXT.md` first** for orientation (what the project is, communication style,
methodology rules). This file is the opposite: purely volatile state — what is running
right now, what was just done, what to do next.

Update this at the end of every session. If it disagrees with your memory, trust this
file.

**Last updated: 2026-08-25**

---

## Running right now

| Job | Machine | Started | Status | Output |
|---|---|---|---|---|
| _(none)_ | — | — | — | — |

**Generation is COMPLETE** — 28,160 / 28,160 completions, 1,408 / 1,408 (uid, model)
pairs at exactly k=20, zero pairs short, zero absent. Packed and pushed (`fdab540`).

---

## Next action

**Judge the completions.** Preflight already passed — `claude-haiku-4-5` correctly
routed an `ambiguous` prompt to CATEGORY 4 and cited the rule, so it is following the
taxonomy rather than guessing.

```bash
python3 scripts/run_phase05_judging.py --limit 20    # smoke test, read the labels
python3 scripts/run_phase05_judging.py               # full, ~$50, resumable, ~several hours
```

Judging is resumable exactly like generation. Watch progress with
`wc -l results/phase05/judgments.jsonl` (target 28,160), not the log.

**Then** the analysis script (spec §6–§7) — still unwritten, and the only thing between
this data and a GO/NO-GO verdict.

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
