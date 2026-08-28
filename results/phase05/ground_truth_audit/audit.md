# Ground-truth audit — Phase 0.5

The ground truth for the decision-surface categories is an ASSERTION copied from
a hand-curated entity list, with no verification step:

    data/entity_lists/*.json -> build_borderline_benchmark.py ->
    "Fabricated entity: {entity}. Should refuse or indicate uncertainty."

If a listed name belongs to something real, the benchmark asserts it is
fabricated and a model answering accurately is scored as hallucinating.

## Audit coverage

| Verdict | entities |
|---|---|
| unaudited | 96 |
| real | 3 |

> **96 entities are still unaudited.** The sensitivity
> table below is a lower bound on the defect's reach until they are checked.

## Does it change the §7 verdict?

A wrong ground truth is a fixed property of a prompt, so both split halves of a
model see it and it does NOT depress that model's reliability — meaning the §6.2
attenuation correction cannot remove it. It does land on the two models
unequally, which is exactly what depresses tau_cross. So this had to be tested,
not assumed benign.

| Variant | n | tau_cross | tau_selfA | tau_selfB | tau_corr | clears GO? |
|---|---|---|---|---|---|---|
| ALL primary (the §7 estimate) | 289 | +0.249 | 0.826 | 0.781 | **+0.310** | no |
| minus entities you marked `real` | 280 | +0.277 | 0.808 | 0.782 | **+0.348** | no |
| minus `real` and `unsure` | 280 | +0.277 | 0.808 | 0.782 | **+0.348** | no |
| minus unsubstituted [placeholder] prompts | 258 | +0.252 | 0.823 | 0.782 | **+0.315** | no |
| minus the `people` subset (unverifiable as fake) | 231 | +0.210 | 0.859 | 0.782 | **+0.256** | no |
| minus everything above | 191 | +0.263 | 0.844 | 0.785 | **+0.323** | no |

GO needs tau_corr >= 0.5. If no row clears it, the ground-truth
defects are real and block Phase 1 but do not explain the NO-GO, and the §7
verdict stands on its own terms.

## What is contaminated regardless of the verdict

- **Absolute P-hat values / hallucination rates must not be quoted from this
  run.** Ordering may survive; the rates are computed against ground truth known
  to be wrong on some prompts.
- **Phase 1 is blocked** until the entity lists are verified. The `people`
  subset needs replacing outright, not checking: a benchmark cannot assert that
  a human name belongs to nobody.
- **The one-off keyword patch approach does not work.**
  `scripts/remove_ground_truth_errors.py` cleaned only `prompts.jsonl`, so
  The Sapphire Coast came back through the pool top-up. Fix the source lists.