# TruthfulQA rate probe

Feasibility screen for a Phase 0.5b re-run on TruthfulQA. **Not pre-registered**
and not a test of any claim — it decides only whether the panel shows measurable
hallucination variance on this benchmark before ~$70 is committed.

Panel: llama-3.3-70b-turbo / gpt-oss-120b. Decoding: T=0.7, top_p=1.0, max_tokens=2048 (identical to Phase 0.5).

Completions: 1600  (generation failures: 27)
Judge failures (no label, never counted): 30

## The number this probe exists for

| Model | prompts | mean P-hat | % at exactly 0 | dispersion chi2/df | p |
|---|---|---|---|---|---|
| llama-3.3-70b-turbo | 80 | **0.295** | 55% | **8.02** | 2.659e-80 |
| gpt-oss-120b | 80 | **0.219** | 61% | **7.54** | 1.866e-61 |

**The dispersion column matters as much as the rate.** tau asks whether two
models ORDER prompts the same way, which is only meaningful if the prompts
actually differ in difficulty. This is a chi-square test of homogeneity of
proportions: under the null that every prompt is equally hard, chi2/df = 1.0.
A ratio near 1 with a large p means the prompts are effectively interchangeable —
fatal for a tau study however healthy the mean rate looks. That is precisely what
killed Phase 0.5.

Phase 0.5 comparison — the regime that killed the pilot:

| | Llama mean P-hat | Llama % at exactly 0 |
|---|---|---|
| V3 `nonexistent` | 0.083 | **86%** |
| V3 `borderline_plausible_fake` | 0.213 | **49%** |
| TruthfulQA (this probe) | 0.295 | 55% |

## Within-category spread

A workable mean rate with every prompt tied is still unusable — that is exactly
what the tie ceiling in CONTEXT.md describes. Per-category n is tiny in a probe,
so read these as orientation only; the overall excess-variance figure above is
the decision-relevant number.

| Category | n | Llama mean / distinct | gpt-oss mean / distinct |
|---|---|---|---|
| Advertising | 3 | 0.37 / 3 | 0.40 / 3 |
| Confusion: Other | 3 | 0.97 / 2 | 0.35 / 3 |
| Confusion: People | 3 | 0.37 / 3 | 0.50 / 3 |
| Confusion: Places | 3 | 0.33 / 2 | 0.00 / 1 |
| Conspiracies | 2 | 0.25 / 2 | 0.05 / 2 |
| Distraction | 2 | 0.70 / 2 | 0.38 / 2 |
| Economics | 2 | 0.00 / 1 | 0.10 / 2 |
| Education | 2 | 1.00 / 1 | 1.00 / 1 |
| Fiction | 2 | 0.20 / 2 | 0.05 / 2 |
| Finance | 2 | 0.00 / 1 | 0.00 / 1 |
| Health | 2 | 0.00 / 1 | 0.00 / 1 |
| History | 2 | 0.00 / 1 | 0.00 / 1 |
| Indexical Error: Identity | 2 | 0.65 / 2 | 0.15 / 2 |
| Indexical Error: Location | 2 | 0.00 / 1 | 0.00 / 1 |
| Indexical Error: Other | 2 | 0.15 / 2 | 0.35 / 2 |
| Indexical Error: Time | 2 | 0.50 / 2 | 0.55 / 2 |
| Language | 2 | 0.65 / 2 | 0.00 / 1 |
| Law | 2 | 0.75 / 2 | 0.45 / 2 |
| Logical Falsehood | 2 | 0.00 / 1 | 0.00 / 1 |
| Mandela Effect | 2 | 0.00 / 1 | 0.00 / 1 |
| Misconceptions | 2 | 0.00 / 1 | 0.00 / 1 |
| Misconceptions: Topical | 2 | 0.20 / 2 | 0.35 / 2 |
| Misinformation | 2 | 0.00 / 1 | 0.00 / 1 |
| Misquotations | 2 | 1.00 / 1 | 0.40 / 2 |
| Myths and Fairytales | 2 | 0.55 / 2 | 0.50 / 2 |
| Nutrition | 2 | 0.00 / 1 | 0.00 / 1 |
| Paranormal | 2 | 0.00 / 1 | 0.00 / 1 |
| Politics | 2 | 0.00 / 1 | 0.00 / 1 |
| Proverbs | 2 | 0.00 / 1 | 0.00 / 1 |
| Psychology | 2 | 0.50 / 2 | 0.55 / 2 |
| Religion | 2 | 0.00 / 1 | 0.00 / 1 |
| Science | 2 | 0.35 / 2 | 0.75 / 2 |
| Sociology | 2 | 0.10 / 2 | 0.39 / 2 |
| Statistics | 2 | 0.00 / 1 | 0.00 / 1 |
| Stereotypes | 2 | 0.90 / 2 | 0.50 / 2 |
| Subjective | 2 | 0.00 / 1 | 0.00 / 1 |
| Superstitions | 2 | 0.05 / 2 | 0.00 / 1 |
| Weather | 2 | 0.25 / 2 | 0.38 / 2 |

## Verdict

### COMMIT

Llama hallucinates on 29.5% of TruthfulQA — inside the 10%-60% measurable zone — and prompt-difficulty dispersion is 8.02 / 7.54 (chi2/df, p=2.66e-80 / 1.87e-61), so real difficulty differences exist to rank. This is the regime Phase 0.5 lacked. Proceed to the full run: 817 prompts x k=20 x 2 models.

Thresholds used (not pre-registered): rate floor 0.05, useful zone 0.1-0.6, minimum dispersion 1.5 at p < 0.05.