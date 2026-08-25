# Paper Deadlines

Working document. **All dates below are estimates until verified against official sources.** Check the official pages before locking any date in your calendar.

Official sources to check:
- **NeurIPS 2026**: https://neurips.cc/Conferences/2026 (main + workshops)
- **ICLR 2027**: https://openreview.net/group?id=ICLR.cc/2027 (deadlines drop late summer 2026)
- **ICML 2027**: https://icml.cc/Conferences/2027

---

## Boaz's April 2026 venue guidance
- NeurIPS 2026 main: **too soon** (deadline was May 2026, missed)
- ICML / ICLR 2026 main: **deadlines already passed**
- Realistic targets: **ICLR 2027 main** (Sep/Oct 2026 deadline) or **NeurIPS 2026 workshop** (Aug/Sep 2026 deadline)
- Relevant workshops named: **TrustML**, **Reliable & Responsible Foundation Models**, **Geometry in ML** (must verify these are running in 2026)

## Boaz May 1 meeting: venue decision deferred
Boaz did NOT re-litigate the venue in the May 1 reframe meeting. His position was that the decision waits on the Phase 1 tau result: strong tau across the panel with clean baselines → ICLR/ICML main defensible; noisier signal or a panel cut for credit reasons → NeurIPS workshop is the honest target.

**Current status (Aug 24, 2026): ICML 2027 is the honest primary target.** The deferral above still governs *quality* framing — a weak tau result would push us to a workshop — but the calendar has already decided the venue question. ICLR 2027 required a sprint whose week-1 milestone (pilot done, both advisors replied) did not happen. `CONTEXT.md` and this file agree on this; if they ever disagree again, this file wins on dates and CONTEXT.md wins on project state.

---

## Deadline table (verify before committing)

| Venue | Full paper deadline (est.) | Format | Status |
|---|---|---|---|
| NeurIPS 2026 main | ~mid-May 2026 | 9pp | **PASSED** |
| NeurIPS 2026 workshops | ~mid-Aug to mid-Sep 2026 | 4–6pp | Most passed or imminent — check for late ones |
| ICLR 2027 main | ~late-Sep to early-Oct 2026 | 8pp | Effectively off the table — see below |
| ICML 2027 main | ~late-Jan 2027 | 8pp | ~22 weeks out (**primary target**) |

Workshop CFPs are announced 2–3 months before their deadline.

---

## Primary vs. fallback strategy (revised end-of-August 2026)

**Primary target: ICML 2027 main (~late-Jan 2027 est.)**
- ~22 weeks from Aug 24, 2026
- Full experimental program: Phases 0–5
- Comfortable, no compression
- **This is the target. Plan against it.**

**ICLR 2027 main (~early Oct 2026 est.) — effectively off the table**
- The sprint was contingent on the Phase 0.5 pilot landing clean in the first 1–2 weeks of September AND Sunny + Boaz both replying in that window, with Phases 3–5 compressed hard. Neither contingency held: the pilot design was only pre-registered on Aug 24 and no code exists yet, and both advisors are unanswered.
- The working-backwards table for this sprint has been removed rather than left to rot. If circumstances change dramatically (pilot returns a strong GO within days, both advisors reply immediately), rebuild it then.
- Standing judgment: submitting a rushed paper here risks a rejection that hurts at ICML. Not worth it.

**Opt-in tertiary: any still-open NeurIPS 2026 workshop**
- Check weekly for late CFPs
- Only submit a compressed workshop version if a relevant one lands with 6+ weeks lead time
- Do NOT let workshop preparation displace ICML work

---

## Working-backwards timeline

### ICML 2027 — assume ~late-Jan 2027 deadline, 22 weeks from Aug 24
Comfortable pace. Full program, no compression.

| Weeks | Phase | Milestone |
|---|---|---|
| 1–3 (Aug 24 → Sep 14) | Phase 0 + 0.5 | Boaz credits clarified, panel locked, **Phase 0.5 pilot run and its pre-registered GO/NO-GO evaluated** (`PHASE_0.5_SPEC.md`). Sunny sign-off if she replies — the pilot does not block on her. |
| 4–8 (Sep 14 → Oct 19) | Phase 1 | Full 5–10 model panel tau result (funding-gated). Go/no-go decision. |
| 9–14 (Oct 19 → Nov 30) | Phases 2, 3, 4 (parallel) | Geometric prediction + baselines + PopQA transfer |
| 15–18 (Nov 30 → Dec 28) | Phase 5 | Downstream applications |
| 19–22 (Dec 28 → Jan 25) | Phase 6 | Draft, Sunny review, Boaz review, submit |

Note the dependency risk: weeks 4–8 assume a funded panel. If the Boaz reply and institutional access both come back negative, Phase 1 is a 2-model experiment and the paper's panel-breadth claim has to be rewritten. That contingency is not yet planned for.

---

## Critical dates to check weekly

- [ ] NeurIPS 2026 workshop list — anything still open with a workable deadline?
- [ ] ICLR 2027 openreview — official deadline posted?
- [ ] ICML 2027 icml.cc — official deadline posted?

---

## Update log
- 2026-06-22: Initial version. Working with estimated dates only — none verified yet.
- 2026-08-24: Revised primary target to ICML 2027 given end-of-August start (4 months post-Boaz-meeting). ICLR 2027 downgraded to stretch. NeurIPS workshops largely past. Verified deadlines still TBD.
- 2026-08-24 (later): ICLR 2027 moved from stretch to effectively off the table — its week-1 gating milestones did not happen. Removed the ICLR working-backwards table (it had internally overlapping week ranges: rows "2–3: Aug 31→Sep 14" and "3–4: Sep 7→Sep 21"). Unified venue status with `CONTEXT.md`. Added the unfunded-panel dependency risk to the ICML timeline. **All deadline dates in this file remain unverified estimates.**
