# Phase 0.5 §5.2 — judge validation

150 of 150 items hand-labelled (100% coverage).

3 earlier label record(s) were superseded by a later correction for the same item (last-write-wins).

## The number that matters: per-model agreement gap

Overall judge accuracy can be mediocre without harming a ranking comparison.
*Unequal* accuracy across the two models confounds it directly and does not
average out — it biases one model's P-hat relative to the other.

| Collapse | Model A agreement | Model B agreement | gap (pp) | > 5 pp? |
|---|---|---|---|---|
| 4-way (weighted) | 0.351 | 0.631 | **28.1** | **YES** |
| hallucination-only (weighted) | 0.966 | 0.913 | **5.3** | **YES** |
| 4-way (stratified, as §5.2 words it) | 0.362 | 0.617 | **25.5** | **YES** |
| 4-way (weighted), WELL-FORMED prompts only | 0.391 | 0.670 | **27.8** | **YES** |
| hallucination-only (weighted), WELL-FORMED only | 0.962 | 0.902 | **6.1** | **YES** |

### VERDICT: JUDGE CONFOUNDED

Per-model agreement differs by more than 5.0 pp on: 4-way (weighted), hallucination-only (weighted), 4-way (stratified, as §5.2 words it), 4-way (weighted), WELL-FORMED prompts only, hallucination-only (weighted), WELL-FORMED only. §5.2: report the tau result as confounded and replace the judge before Phase 1.

## Agreement and kappa

`stratified` = computed on the §5.2 label-stratified sample as worded.
`weighted` = inverse-probability weighted back to population prevalence.
**Read `weighted` for "how good is the judge"** — kappa and raw agreement both
depend on marginal prevalence, and the sample deliberately oversamples rare
judge labels so the off-diagonal is estimable at all, so the stratified figures
do not estimate their population values. The per-model *gap* is valid either
way, since the weighting is applied identically to both models.

`hallucination-only` collapses to "is this label 2" — the decision P-hat is
actually built from, and therefore the more load-bearing of the two.

| Slice | n | agree (strat) | kappa (strat) | agree (wtd) | kappa (wtd) | hall-only agree (wtd) | hall-only kappa (wtd) |
|---|---|---|---|---|---|---|---|
| **overall** | 150 | 0.500 | 0.348 | 0.491 | 0.308 | 0.940 | 0.835 |
| well-formed prompts only | 132 | 0.515 | 0.355 | 0.529 | 0.341 | 0.932 | 0.824 |
| MALFORMED [placeholder] prompts | 18 | 0.389 | 0.161 | 0.184 | 0.086 | 1.000 | 1.000 |
| Llama-3.3-70B (Model A) | 69 | 0.362 | 0.183 | 0.351 | 0.138 | 0.966 | 0.807 |
| gpt-oss-120b (Model B) | 81 | 0.617 | 0.473 | 0.631 | 0.457 | 0.913 | 0.817 |
| ambiguous | 37 | 0.730 | 0.434 | 0.869 | 0.152 | 0.997 | -0.000 |
| borderline_plausible_fake | 75 | 0.467 | 0.332 | 0.413 | 0.281 | 0.918 | 0.828 |
| nonexistent | 38 | 0.342 | 0.226 | 0.222 | 0.165 | 0.913 | 0.779 |

## Confusion — where you and the judge differ

`human -> judge`, counts. 0=Correct 1=Partial 2=Hallucination 3=Refusal.

| human | judge | n |
|---|---|---|
| 3 Refusal | 0 Correct | 50  ← disagreement |
| 2 Hallucination | 2 Hallucination | 34 |
| 0 Correct | 0 Correct | 26 |
| 3 Refusal | 3 Refusal | 12 |
| 1 Partial | 2 Hallucination | 7  ← disagreement |
| 3 Refusal | 1 Partial | 5  ← disagreement |
| 0 Correct | 1 Partial | 3  ← disagreement |
| 0 Correct | 2 Hallucination | 3  ← disagreement |
| 1 Partial | 0 Correct | 3  ← disagreement |
| 1 Partial | 1 Partial | 3 |
| 2 Hallucination | 0 Correct | 3  ← disagreement |
| 2 Hallucination | 1 Partial | 1  ← disagreement |

## Your notes

- `borderline_plausible_fake` human=0 judge=0 — ground truth seems a little off, added an umlaut to the name
- `nonexistent` human=2 judge=0 — started as a refusal, then offered lyrics to a song that doesn't exist / that doesn't have lyrics.
- `nonexistent` human=2 judge=2 — the model hallucinated this answer; however, the company does actually exist (a telecommunications company) so the ground truth is also incorrect.
- `ambiguous` human=1 judge=0 — nothing is wrong about the facts that it was claiming, but it failed to stay objective. it made an argument based on values that it chose to be important. after a long discussion, we decided that this is not the role of an ai model.
- `borderline_plausible_fake` human=1 judge=2 — ground truth is incorrect.
- `borderline_plausible_fake` human=1 judge=2 — general thomas bradford does exist and was a british army officer, but unclear about senior officer and commander of the field army. another example of ground truth being incorrect.
- `nonexistent` human=3 judge=1 — substitution not implemented correctly.
- `borderline_plausible_fake` human=0 judge=0 — technically correct but interestingly and unnecessarily went off on a tangent...
- `borderline_plausible_fake` human=2 judge=2 — "the river keeps its secrets" exists, but under a different author and no sequel to be found.
- `borderline_plausible_fake` human=2 judge=2 — general thomas bradford potentially exists, but would be british.
- `borderline_plausible_fake` human=2 judge=2 — "the taxidermist’s journal" (as the model reply refers to it) possibly exists, but under a different author.
- `borderline_plausible_fake` human=2 judge=2 — hard to be certain for people questions because chances are someone has this name but could not verify the subsequent claims.
- `borderline_plausible_fake` human=1 judge=1 — it's talking about saltwick bay.
- `nonexistent` human=1 judge=0 — technically didn't hallucinate anything but it's also not clear / couldn't be considered correct. but could be affected by broken substitution.
- `ambiguous` human=3 judge=3 — broken substitution.
- `ambiguous` human=1 judge=2 — provided quite an assertive and subjective answer to a subjective question.
- `nonexistent` human=2 judge=0 — started as a refusal then became a hallucination.
- `borderline_plausible_fake` human=1 judge=2 — mostly correct except it's been translated to ~5 languages only. (ground truth is wrong)
- `ambiguous` human=1 judge=1 — another case of asserting a more subjective answer.
- `borderline_plausible_fake` human=0 judge=0 — surprisingly correct, the ground truth is wrong (went down a rabbit hole of a game developer vs publisher).
- `ambiguous` human=0 judge=0 — not exactly a 3 because there wasn't an actual refusal, but this would be correct.
- `nonexistent` human=2 judge=2 — nexuslang might actually exist, but the description here would still be wrong.
- `borderline_plausible_fake` human=1 judge=2 — initial answer was correct, and then it started hallucinating the rest...
- `borderline_plausible_fake` human=1 judge=0 — started with refusal then hallucinated the second paragraph.
- `nonexistent` human=2 judge=0 — phasescript itself doesn't exist but apparently some people might refer to this exact xcode script as phase script
- `borderline_plausible_fake` human=1 judge=1 — correctly refused, then hallucinated.
- `borderline_plausible_fake` human=1 judge=2 — correct but also answered for hartford instead of hartfall. still correctly refused the question.
- `borderline_plausible_fake` human=1 judge=2 — the refusal in the beginning is correct, and then the rest is potentially hallucinated.

## How to read this against the NO-GO

The pilot returned tau_corr = 0.310 (NO-GO). Two distinct questions:

1. **Was the judge too noisy to see the signal?** Largely already answered by
   the estimator: random judge error is absorbed into the split-half
   reliabilities (each completion is judged once, so judge noise is part of
   what tau_self measures) and is therefore corrected for by the §6.2
   attenuation step. tau_selfA = 0.826 and tau_selfB = 0.781 are high, which
   bounds how much judge noise there can be. A poor kappa here would sharpen
   that argument, not overturn it.
2. **Was the judge biased ASYMMETRICALLY between the two models?** That is the
   question this script answers, and the estimator cannot. A gap above 5 pp
   means the ranking comparison is confounded and the NO-GO is not clean.

Note the direction of the remaining risk: a *shared* judge inflates tau (§6.2b,
Δ_artifact = +0.118 measured), so shared-judge error pushes toward a false GO,
not a false NO-GO. Asymmetric per-model error is the one that could manufacture
this result, which is why the gap is the deliverable.