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
Boaz did NOT re-litigate the venue in the May 1 reframe meeting. Decision is punted until Phase 1 (Kendall's tau) result lands. If tau is strong across the panel with clean baselines → ICLR main defensible. If signal is noisier or panel is cut for credit reasons → NeurIPS workshop is the honest target.

---

## Deadline table (verify before committing)

| Venue | Full paper deadline (est.) | Format | Status |
|---|---|---|---|
| NeurIPS 2026 main | ~mid-May 2026 | 9pp | **PASSED** |
| NeurIPS 2026 workshops | ~mid-Aug to mid-Sep 2026 | 4–6pp | Most passed or imminent — check for late ones |
| ICLR 2027 main | ~late-Sep to early-Oct 2026 | 8pp | ~5–6 weeks out (stretch target) |
| ICML 2027 main | ~late-Jan 2027 | 8pp | ~22 weeks out (realistic primary) |

Workshop CFPs are announced 2–3 months before their deadline.

---

## Primary vs. fallback strategy (revised end-of-August 2026)

**Primary target: ICML 2027 main (~late-Jan 2027 est.)**
- ~22 weeks from Aug 24, 2026
- Full experimental program: Phases 0–5
- Comfortable, no compression
- **This is the realistic target given the 4-month post-thesis lull.**

**Stretch target: ICLR 2027 main (~early Oct 2026 est.)**
- ~5–6 weeks from Aug 24, 2026
- Only viable if:
  - Phase 0.5 pilot lands clean in the next 1–2 weeks
  - Sunny + Boaz respond within 2 weeks
  - Phases 3, 4, 5 get compressed hard
- Not worth compromising the paper's quality to hit. If the sprint isn't clean, fall back to ICML.

**Opt-in tertiary: any still-open NeurIPS 2026 workshop**
- Check weekly for late CFPs
- Only submit compressed workshop version if a relevant one lands with 6+ weeks lead time
- Do NOT let workshop preparation displace ICLR/ICML work

---

## Working-backwards timelines

### ICML 2027 — assume ~late-Jan 2027 deadline, 22 weeks from Aug 24
Comfortable pace. Full program, no compression.

| Weeks | Phase | Milestone |
|---|---|---|
| 1–3 (Aug 24 → Sep 14) | Phase 0 + 0.5 | Sunny signed off, Boaz credits clarified, panel locked, Kendall's tau pilot done |
| 4–8 (Sep 14 → Oct 19) | Phase 1 | Full 5–10 model panel Kendall's tau result. Go/no-go decision. |
| 9–14 (Oct 19 → Nov 30) | Phases 2, 3, 4 (parallel) | Geometric prediction + baselines + PopQA transfer |
| 15–18 (Nov 30 → Dec 28) | Phase 5 | Downstream applications |
| 19–22 (Dec 28 → Jan 25) | Phase 6 | Draft, Sunny review, Boaz review, submit |

### ICLR 2027 stretch — assume ~Oct 1 deadline, ~5–6 weeks from Aug 24
Aggressive sprint. Only viable if everything breaks right.

| Weeks | Phase | Milestone |
|---|---|---|
| 1 (Aug 24 → Aug 31) | Phase 0 + 0.5 (compressed) | Sunny + Boaz respond fast, panel locked, pilot done |
| 2–3 (Aug 31 → Sep 14) | Phase 1 (compressed) | Full panel Kendall's tau. Go/no-go. |
| 3–4 (Sep 7 → Sep 21) | Phases 2 + 3 (parallel) | Geometric prediction + semantic entropy only baseline |
| 5 (Sep 21 → Sep 28) | Phase 6 | Draft, minimal review |
| 6 (Sep 28 → Oct 1) | Submit | |

Skip Phases 4 and 5 entirely; note as future work. Submitting this rushed to ICLR risks a rejection that hurts you at ICML.

---

## Critical dates to check weekly

- [ ] NeurIPS 2026 workshop list — anything still open with a workable deadline?
- [ ] ICLR 2027 openreview — official deadline posted?
- [ ] ICML 2027 icml.cc — official deadline posted?

---

## Update log
- 2026-06-22: Initial version. Working with estimated dates only — none verified yet.
- 2026-08-24: Revised primary target to ICML 2027 given end-of-August start (4 months post-Boaz-meeting). ICLR 2027 downgraded to stretch. NeurIPS workshops largely past. Verified deadlines still TBD.
