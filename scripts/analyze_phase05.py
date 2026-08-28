"""Phase 0.5 step 3: the analysis (spec §6) and the go/no-go verdict (spec §7).

Pre-registered design: research_paper/PHASE_0.5_SPEC.md. Reads
results/phase05/completions.jsonl (for finish_reason / output_tokens) and
results/phase05/judgments.jsonl (for labels), joined on (uid, model, sample_idx).

Nothing in here is a modelling choice made after seeing the data. Every estimator,
threshold, exclusion rule, and confound check below is fixed by the spec sections
named in the section headers. Where the spec left a detail open (which pooled
Spearman analogue, which length tokenizer, whether the k_eff filter also applies to
the non-primary sets) the choice is stated inline as a CHOICE comment, so a reviewer
can see the seam.

THE FAILURE CONTRACT (§5.1) — inherited from the March 2026 contamination fix:

  A judgment row with judge_failed=true has NO label. It is never counted, never
  imputed, and never coerced to 3=Refusal. It decrements that (uid, model) pair's
  k_eff. Pairs with k_eff < 16 of 20 for EITHER model leave the primary estimator.

  k_eff is computed over the FULL manifest x models cross-product, not over the
  keys observed in judgments.jsonl. A pair whose every sample failed has k_eff = 0
  and no key at all in a success-keyed dict, so counting that way silently omits
  exactly the worst-damaged pairs. (run_phase05_judging.py's end-of-run summary has
  this defect: it reported 13 pairs below threshold on a run whose true count was
  464, because 451 pairs had zero successes.)

  If the overall judge failure rate exceeds 2%, §5.1 says the run is an
  infrastructure failure and is not analysed. This script therefore WITHHOLDS the §7
  verdict in that case. --ignore-failure-gate computes it anyway, stamped
  provisional and NOT pre-registered; use it to preview numbers, never to decide.

  The rate that gates §5.1 is the UNRECOVERED rate — completions that ended up with
  no label — NOT failed rows over total rows. run_phase05_judging.py appends rather
  than rewrites, so --retry-failed leaves every stale failure row in the file beside
  its replacement success. A row-based rate would therefore never fall back under 2%
  however completely the run is recovered (9,213 / 37,373 = 24.7% after a full
  retry) and would wedge this gate permanently shut. The gross call-failure rate is
  still reported, because a high value means the API was unreliable during the run
  even when every sample was eventually labelled.

Label mapping (§6.1), pinned: 0=Correct, 1=Partial, 2=Hallucination, 3=Refusal.

    P-hat(prompt, model) = #(label == 2) / k_eff

Labels 0, 1 and 3 stay in the DENOMINATOR as non-hallucinations, because the paper
needs the unconditional probability that sampling this model on this prompt yields a
hallucination — that is what an inference-time gate acts on. Dropping refusals would
condition on the model having attempted an answer and introduce a selection effect.

Dependencies: numpy and pandas only. scipy is deliberately not used — Kendall tau-b,
the stratified Spearman, Fisher exact, Cochran-Mantel-Haenszel and the Wilson
interval are all implemented here against numpy 1.19 / Python 3.9, which is what this
machine has.

Usage:
    python3 scripts/analyze_phase05.py
    python3 scripts/analyze_phase05.py --bootstrap 200        # fast preview
    python3 scripts/analyze_phase05.py --ignore-failure-gate  # provisional numbers

Output (results/phase05/analysis/):
    report.md                  the whole §6-§7 report, also printed to stdout
    phase05_results.json       every number, machine-readable
    per_prompt.csv             P-hat, k_eff, refusal and length per (uid, model)
    category_rates.csv         §6.4 marginal rates with CIs
    keff_exclusions.csv        every (uid, model) pair dropped, with its k_eff
"""

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# ── dataset profiles ────────────────────────────────────────────────────────────
# The estimator is dataset-independent; the paths and the expected strata are not.
# Rather than generalise every function's signature, `configure()` rebinds the module
# globals below, so `--dataset phase05b` reuses §6-§7 verbatim on TruthfulQA. The
# module-level defaults remain Phase 0.5, which is what audit_ground_truth.py imports
# this module for -- it never calls configure(), so it is unaffected.
#
# `primary_categories: None` means "accept whatever the manifest's in_primary flag
# selects, and do not assert a category list". That is correct for 0.5b: the strata are
# TruthfulQA's own 38 categories, externally defined, and hardcoding them here would
# only re-encode the source file. The drift guard that matters is still enforced --
# build_phase05b_manifest.py verifies the count and the partition at build time, and
# `expected_n` below catches a manifest swapped underneath the analysis.
DATASETS = {
    "phase05": {
        "spec": "research_paper/PHASE_0.5_SPEC.md §6-§7",
        "manifest": "phase05_manifest.jsonl",
        "results": "phase05",
        # §4.1 — the decision surface: verifiable ground truth (§4.0) and adequate n.
        "primary_categories": ("borderline_plausible_fake", "nonexistent", "ambiguous"),
        # §4.2 — retained deliberately and labelled; NOT part of the decision rule.
        "judgebound_categories": ("borderline_obscure_real", "factual"),
        "expected_n": 704,
        "coarse_strata": False,
    },
    "phase05b": {
        "spec": "research_paper/PHASE_0.5_SPEC.md §11 (estimator §6-§7 unchanged)",
        "manifest": "phase05b_manifest.jsonl",
        "results": "phase05b",
        "primary_categories": None,      # §11.2 — TruthfulQA's own 38 categories
        "judgebound_categories": (),     # §11.3 — no non-verifiable arm exists
        "expected_n": 817,
        # §11.2 — the pre-registered coarse-13 merge is reported as a THIRD rung on
        # the §6.3 stratification ladder (pooled -> coarse -> native). Secondary only.
        "coarse_strata": True,
    },
}
DATASET = "phase05"

MANIFEST_PATH = BASE_DIR / "data" / "prompts" / "phase05_manifest.jsonl"
RESULTS_DIR = BASE_DIR / "results" / "phase05"
COMPLETIONS_PATH = RESULTS_DIR / "completions.jsonl"
JUDGMENTS_PATH = RESULTS_DIR / "judgments.jsonl"
DECODING_CONFIG_PATH = RESULTS_DIR / "decoding_config.json"
OUT_DIR = RESULTS_DIR / "analysis"

# §3 — Model A is the Meta dense model, Model B the OpenAI open-weight MoE. The
# A/B assignment is fixed here so that tau_selfA and tau_selfB are never silently
# swapped between runs by dict ordering.
MODEL_A = "llama-3.3-70b-turbo"
MODEL_B = "gpt-oss-120b"
MODEL_LABELS = {MODEL_A: "Llama-3.3-70B (Model A)", MODEL_B: "gpt-oss-120b (Model B)"}

# §4.1 — the decision surface: verifiable ground truth (§4.0) and adequate n.
PRIMARY_CATEGORIES = ("borderline_plausible_fake", "nonexistent", "ambiguous")
# §4.2 — retained deliberately and labelled; NOT part of the decision rule.
JUDGEBOUND_CATEGORIES = ("borderline_obscure_real", "factual")
EXPECTED_N_PROMPTS = 704
COARSE_STRATA = False
SPEC_REF = "research_paper/PHASE_0.5_SPEC.md §6-§7"


def configure(dataset):
    """Point the module at a dataset profile. Call before anything reads a path."""
    if dataset not in DATASETS:
        sys.exit(f"unknown dataset {dataset!r}. Choose from: {', '.join(DATASETS)}")
    cfg = DATASETS[dataset]
    global DATASET, MANIFEST_PATH, RESULTS_DIR, COMPLETIONS_PATH, JUDGMENTS_PATH
    global DECODING_CONFIG_PATH, OUT_DIR, PRIMARY_CATEGORIES, JUDGEBOUND_CATEGORIES
    global EXPECTED_N_PROMPTS, COARSE_STRATA, SPEC_REF
    DATASET = dataset
    MANIFEST_PATH = BASE_DIR / "data" / "prompts" / cfg["manifest"]
    RESULTS_DIR = BASE_DIR / "results" / cfg["results"]
    COMPLETIONS_PATH = RESULTS_DIR / "completions.jsonl"
    JUDGMENTS_PATH = RESULTS_DIR / "judgments.jsonl"
    DECODING_CONFIG_PATH = RESULTS_DIR / "decoding_config.json"
    OUT_DIR = RESULTS_DIR / "analysis"
    PRIMARY_CATEGORIES = cfg["primary_categories"]
    JUDGEBOUND_CATEGORIES = cfg["judgebound_categories"]
    EXPECTED_N_PROMPTS = cfg["expected_n"]
    COARSE_STRATA = cfg["coarse_strata"]
    SPEC_REF = cfg["spec"]
    return cfg

K_SAMPLES = 20                    # §6.1
K_EFF_MIN = 16                    # §5.1 — below this the pair leaves the primary
FAILURE_RATE_ABORT = 0.02         # §5.1 — above this the run is infra failure
DEGENERATE_MIN_DISTINCT = 5       # §6.7
BOOTSTRAP_ITERS = 1000            # §6.6
BOOTSTRAP_SEED = 20260826         # fixed so the CI is reproducible
BOOTSTRAP_BATCH = 250             # iterations per vectorised batch (memory knob)

# §7 — binding thresholds. Do not edit without a dated §10 amendment.
GO_TAU_CORR = 0.50
GO_CI_LOWER = 0.30
MEASUREMENT_FAILURE_TAU_SELF = 0.40

LABEL_CORRECT, LABEL_PARTIAL, LABEL_HALLUCINATION, LABEL_REFUSAL = 0, 1, 2, 3


# ── statistics, numpy-only ────────────────────────────────────────────────────


def _tau_parts(x, y):
    """Kendall tau-b numerator and the two tie-corrected denominators.

    Accepts (n,) or (B, n) — batched over the leading axis so the bootstrap does not
    pay Python loop overhead per iteration.

    Returns (num, den_x, den_y) where num = n_concordant - n_discordant,
    den_x = n0 - n1 (pairs not tied in x) and den_y = n0 - n2 (pairs not tied in y).
    tau_b = num / sqrt(den_x * den_y).

    Computed over the full n x n sign matrix and halved rather than over an explicit
    upper triangle: the triu fancy-index copy costs more than the redundant half of
    an int8 matrix. Zeros in the full sign matrix are n (the diagonal) + 2 * n_ties,
    which is where the (zeros - n) / 2 below comes from.
    """
    x = np.atleast_2d(np.asarray(x, dtype=np.float64))
    y = np.atleast_2d(np.asarray(y, dtype=np.float64))
    n = x.shape[-1]
    if n < 2:
        z = np.zeros(x.shape[0])
        return z, z, z.copy()

    sx = np.sign(x[..., :, None] - x[..., None, :]).astype(np.int8)
    sy = np.sign(y[..., :, None] - y[..., None, :]).astype(np.int8)

    num = (sx.astype(np.int16) * sy).sum(axis=(-2, -1)) / 2.0
    nz_x = np.count_nonzero(sx, axis=(-2, -1))
    nz_y = np.count_nonzero(sy, axis=(-2, -1))
    # pairs not tied in x = nonzero off-diagonal entries / 2
    den_x = nz_x / 2.0
    den_y = nz_y / 2.0
    return num, den_x.astype(np.float64), den_y.astype(np.float64)


def tau_b_blocked(x, y, strata):
    """Blocked within-stratum Kendall tau-b (§6.2).

    ONE estimator over concordant/discordant pairs, counting only pairs of prompts
    that share a category. Numerator and both tie-corrected denominators are summed
    across strata before the ratio is taken — not a median of per-stratum taus,
    which would be a statistic over 2-3 noisy numbers and would discard the
    unequal-n weighting.

    Between-category pairs are structurally absent, which is the point: any two
    models agree that impossible prompts are harder than factual ones, so pooled tau
    measures benchmark stratification rather than model agreement (§2.1).
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    strata = np.asarray(strata)
    num = den_x = den_y = 0.0
    n_pairs = 0
    for s in np.unique(strata):
        m = strata == s
        if m.sum() < 2:
            continue
        a, bx, by = _tau_parts(x[m], y[m])
        num += float(a[0])
        den_x += float(bx[0])
        den_y += float(by[0])
        n_pairs += int(m.sum() * (m.sum() - 1) // 2)
    den = math.sqrt(den_x * den_y)
    tau = float(num / den) if den > 0 else float("nan")
    return {"tau_b": tau, "n_pairs": n_pairs, "num": num,
            "den_x": den_x, "den_y": den_y}


def _rank_avg(v):
    """Average ranks, ties shared. numpy-only rankdata."""
    v = np.asarray(v, dtype=np.float64)
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v), dtype=np.float64)
    sv = v[order]
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman_blocked(x, y, strata):
    """Stratified Spearman rho — the licensed cross-check for §6.2's tau heuristic.

    CHOICE: the spec asks for "Spearman rho with the standard disattenuation" as the
    formally licensed counterpart to the tau correction, but does not say how to
    block it. Implemented as the partial Spearman controlling for a stratum
    indicator: rank within stratum, centre the ranks within stratum, then take the
    Pearson correlation of the pooled centred ranks. This is the direct rho analogue
    of tau_b_blocked — one estimator, within-stratum pairs only, no between-category
    contribution.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    strata = np.asarray(strata)
    rx = np.zeros(len(x))
    ry = np.zeros(len(y))
    for s in np.unique(strata):
        m = strata == s
        if m.sum() < 2:
            continue
        a, b = _rank_avg(x[m]), _rank_avg(y[m])
        rx[m] = a - a.mean()
        ry[m] = b - b.mean()
    denom = math.sqrt(float((rx ** 2).sum()) * float((ry ** 2).sum()))
    if denom == 0:
        return float("nan")
    return float((rx * ry).sum() / denom)


def spearman_brown(r_half):
    """Upgrade a split-half reliability to full test length (§6.2)."""
    if not np.isfinite(r_half) or r_half <= -1:
        return float("nan")
    return float(2.0 * r_half / (1.0 + r_half))


def disattenuate(r_cross, rel_a, rel_b):
    """r_cross / sqrt(rel_a * rel_b); NaN when either reliability is non-positive.

    A non-positive reliability is a MEASUREMENT FAILURE (§7 row 3), not evidence
    against the claim — returning NaN here rather than a clipped number keeps that
    distinction visible downstream.
    """
    if not (np.isfinite(rel_a) and np.isfinite(rel_b)) or rel_a <= 0 or rel_b <= 0:
        return float("nan")
    return float(r_cross / math.sqrt(rel_a * rel_b))


def wilson_interval(successes, n, z=1.959963984540054):
    """Wilson score interval. Behaves at 0 and n successes, unlike Wald."""
    if n == 0:
        return float("nan"), float("nan")
    p = successes / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher exact p for [[a, b], [c, d]] by exact enumeration."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    if n == 0 or r1 == 0 or r2 == 0 or c1 == 0 or c1 == n:
        return 1.0
    total = math.comb(n, c1)

    def pmf(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / total

    p_obs = pmf(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return float(min(1.0, sum(pmf(x) for x in range(lo, hi + 1)
                              if pmf(x) <= p_obs * (1 + 1e-9))))


def chi2_sf_1df(x):
    """P(chi-square with 1 df > x) = erfc(sqrt(x / 2))."""
    if not np.isfinite(x) or x <= 0:
        return 1.0
    return float(math.erfc(math.sqrt(x / 2.0)))


def cochran_mantel_haenszel(tables):
    """CMH test over 2x2 tables [(a, b, c, d), ...], with MH common odds ratio.

    Row 1 is the exposed group (here: truncated samples), column 1 the event (here:
    label == 2). Continuity-corrected, 1 df.
    """
    sum_a = sum_e = sum_v = 0.0
    num_or = den_or = 0.0
    used = 0
    for a, b, c, d in tables:
        n = a + b + c + d
        if n < 2:
            continue
        r1, r2, c1, c2 = a + b, c + d, a + c, b + d
        if r1 == 0 or r2 == 0 or c1 == 0 or c2 == 0:
            continue          # no contrast in this table; contributes nothing
        used += 1
        sum_a += a
        sum_e += r1 * c1 / n
        sum_v += r1 * r2 * c1 * c2 / (n * n * (n - 1))
        num_or += a * d / n
        den_or += b * c / n
    if used == 0 or sum_v <= 0:
        return {"n_tables_informative": used, "chi2": float("nan"),
                "p_value": float("nan"), "mh_odds_ratio": float("nan"),
                "sum_a": sum_a, "sum_expected": sum_e}
    chi2 = (abs(sum_a - sum_e) - 0.5) ** 2 / sum_v
    return {"n_tables_informative": used,
            "chi2": float(chi2),
            "p_value": chi2_sf_1df(chi2),
            "mh_odds_ratio": float(num_or / den_or) if den_or > 0 else float("inf"),
            "sum_a": sum_a, "sum_expected": sum_e}


def rank_auc(pos, neg):
    """P(random positive > random negative), ties at 0.5. Mann-Whitney U / (n*m)."""
    pos, neg = np.asarray(pos, dtype=np.float64), np.asarray(neg, dtype=np.float64)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    both = np.concatenate([pos, neg])
    r = _rank_avg(both)
    u = r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2.0
    return float(u / (len(pos) * len(neg)))


def residualise_within_stratum(y, z, strata):
    """Residual of y on z with stratum fixed effects and one pooled slope.

    CHOICE: stratum fixed effects plus a single global slope, rather than a separate
    slope per stratum. With 2-3 strata of n=120-169 either is estimable, but a
    pooled slope is the more stable estimate of "the part of P-hat that this
    nuisance variable explains" and it keeps the residualised estimator comparable
    across the primary, judge-bound and secondary sets, whose stratum counts differ.
    """
    y = np.asarray(y, dtype=np.float64)
    z = np.asarray(z, dtype=np.float64)
    strata = np.asarray(strata)
    yc, zc = np.zeros(len(y)), np.zeros(len(z))
    for s in np.unique(strata):
        m = strata == s
        yc[m] = y[m] - y[m].mean()
        zc[m] = z[m] - z[m].mean()
    var = float((zc ** 2).sum())
    if var == 0:
        return yc
    slope = float((zc * yc).sum() / var)
    return yc - slope * zc


# ── loading ───────────────────────────────────────────────────────────────────


def read_jsonl(path):
    if not path.exists():
        sys.exit(f"missing input: {path}")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def rel(path):
    """Repo-relative path for display, falling back to absolute when outside it."""
    try:
        return str(Path(path).relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def load_prompt_table():
    """Manifest rows keyed by uid, with the set-membership flags and length proxies."""
    rows = read_jsonl(MANIFEST_PATH)
    prompts = {}
    for r in rows:
        uid = r["uid"]
        if uid in prompts:
            sys.exit(f"duplicate uid in manifest: {uid}. The manifest is supposed to "
                     "be deduplicated and frozen (§4.4).")
        q = r["question"]
        prompts[uid] = {
            "uid": uid,
            "prompt_id": r.get("id"),
            "category": r["category"],
            # §11.2 — the pre-registered coarse merge, used ONLY as the middle rung of
            # the §6.3 stratification ladder. Falls back to the native category so that
            # a manifest without the field behaves exactly as before (pooled -> blocked,
            # no third rung), rather than erroring.
            "coarse_category": r.get("coarse_category", r["category"]),
            "source": r.get("source"),
            "question": q,
            # CHOICE: §6.5.1 asks for "question token length". Neither tiktoken nor
            # transformers is installed and neither evaluated model's tokenizer is
            # available offline, so length is proxied by whitespace word count (and
            # character count is carried alongside as a robustness check). Both are
            # monotone in true token count for prompts of this shape; since the test
            # is rank-based, a monotone reparameterisation of the predictor does not
            # change tau_b at all — it only affects the residualisation.
            "question_words": len(q.split()),
            "question_chars": len(q),
            "in_primary": bool(r.get("in_primary")),
            "in_judgebound": bool(r.get("in_judgebound")),
            "in_secondary": bool(r.get("in_secondary")),
        }
    return prompts


def load_judged(prompts):
    """Join judgments onto completions and fold into per-(uid, model) records.

    Every judgment row must match a completion row on (uid, model, sample_idx);
    output_tokens and finish_reason live only on the completion side and §6.5.4
    needs them alongside the label.
    """
    completions = {}
    for r in read_jsonl(COMPLETIONS_PATH):
        completions[(r["uid"], r["model"], r["sample_idx"])] = r

    judgments = read_jsonl(JUDGMENTS_PATH)
    n_rows = len(judgments)
    n_failed_rows = 0
    orphans = 0
    unknown_uid = set()
    dupes = 0

    # per (uid, model): parallel lists of successfully-labelled samples
    recs = defaultdict(lambda: {"idx": [], "label": [], "tokens": [], "trunc": []})
    models = set()
    errors = Counter()
    labelled_keys = set()
    for r in judgments:
        uid, model, idx = r["uid"], r["model"], r["sample_idx"]
        models.add(model)
        if uid not in prompts:
            unknown_uid.add(uid)
            continue
        if r.get("judge_failed") or r.get("label") is None:
            # §5.1 — a failed row, or a row without judge_failed but also without a
            # label, is still NOT a label. Never impute, never coerce to 3=Refusal.
            n_failed_rows += 1
            errors[str(r.get("error", "unspecified (no error field)"))[:120]] += 1
            continue
        comp = completions.get((uid, model, idx))
        if comp is None:
            orphans += 1
            continue
        key = (uid, model, idx)
        if key in labelled_keys:
            # run_phase05_judging.py is append-only, so --retry-failed leaves the
            # stale failure row in place next to the new success. That is handled
            # below. A second SUCCESS for the same key would instead be genuine
            # double-judging, which would push k_eff above 20 and silently reweight
            # that prompt — so it is dropped and counted, not accumulated.
            dupes += 1
            continue
        labelled_keys.add(key)
        rec = recs[(uid, model)]
        rec["idx"].append(idx)
        rec["label"].append(int(r["label"]))
        rec["tokens"].append(comp.get("output_tokens"))
        rec["trunc"].append(comp.get("finish_reason") == "length")

    if unknown_uid:
        sys.exit(f"{len(unknown_uid)} judged uids are absent from the manifest "
                 f"(e.g. {sorted(unknown_uid)[:3]}). The manifest must be the frozen "
                 "one that generation ran against (§4.4).")

    return {
        "records": recs,
        "models": sorted(models),
        "n_judgment_rows": n_rows,
        "n_failed_rows": n_failed_rows,
        "n_labelled_keys": len(labelled_keys),
        "n_duplicate_successes": dupes,
        "n_orphan_judgments": orphans,
        "n_completion_rows": len(completions),
        "completions": completions,
        "error_counter": errors,
    }


def build_per_pair(prompts, recs):
    """P-hat and its companions for every (uid, model) in the manifest cross-product.

    Iterates the manifest x models cross-product deliberately: a pair whose every
    sample failed has no key in `recs`, so iterating `recs` would make exactly the
    worst-damaged pairs invisible and report k_eff coverage as far better than it is.
    """
    out = {}
    for uid, p in prompts.items():
        for model in (MODEL_A, MODEL_B):
            rec = recs.get((uid, model))
            idx = np.array(rec["idx"], dtype=int) if rec else np.zeros(0, dtype=int)
            lab = np.array(rec["label"], dtype=int) if rec else np.zeros(0, dtype=int)
            k_eff = len(lab)

            hall = (lab == LABEL_HALLUCINATION)
            partial = (lab == LABEL_PARTIAL)
            refusal = (lab == LABEL_REFUSAL)

            # §6.2 noise ceiling: odd/even sample_idx. Deterministic, not random, so
            # the ceiling is reproducible and cannot be reshuffled into a better one.
            even = (idx % 2 == 0)
            odd = ~even

            tokens = ([t for t in rec["tokens"] if t is not None] if rec else [])
            out[(uid, model)] = {
                "uid": uid,
                "model": model,
                "category": p["category"],
                "source": p["source"],
                "k_eff": k_eff,
                "n_hallucination": int(hall.sum()),
                "n_partial": int(partial.sum()),
                "n_refusal": int(refusal.sum()),
                "n_correct": int((lab == LABEL_CORRECT).sum()),
                "p_hat": float(hall.mean()) if k_eff else float("nan"),
                # §6.1 label-boundary sensitivity: relabelling only, no new API calls.
                "p_hat_partial_half": (float((hall.sum() + 0.5 * partial.sum()) / k_eff)
                                       if k_eff else float("nan")),
                "p_hat_partial_full": (float((hall.sum() + partial.sum()) / k_eff)
                                       if k_eff else float("nan")),
                "refusal_rate": float(refusal.mean()) if k_eff else float("nan"),
                "k_half_even": int(even.sum()),
                "k_half_odd": int(odd.sum()),
                "n_hall_even": int(hall[even].sum()) if k_eff else 0,
                "n_hall_odd": int(hall[odd].sum()) if k_eff else 0,
                "p_hat_even": (float(hall[even].mean()) if even.sum() else float("nan")),
                "p_hat_odd": (float(hall[odd].mean()) if odd.sum() else float("nan")),
                # Per-half partial counts exist so the §6.1 label-boundary variants can
                # recompute the RELIABILITIES under the variant definition too. Dividing
                # a variant tau_cross by the label-2-only reliabilities would mix two
                # definitions inside one ratio.
                "n_partial_even": int(partial[even].sum()) if k_eff else 0,
                "n_partial_odd": int(partial[odd].sum()) if k_eff else 0,
                "n_truncated": int(sum(rec["trunc"])) if rec else 0,
                "mean_output_tokens": float(np.mean(tokens)) if tokens else float("nan"),
                "median_output_tokens": (float(np.median(tokens)) if tokens
                                         else float("nan")),
            }
    return out


# ── the estimator bundle (§6.2) ───────────────────────────────────────────────


class Panel:
    """A prompt set reduced to the arrays every §6.2 estimator needs.

    Holds only prompts that survived the §5.1 k_eff filter and the §6.7 degenerate-
    stratum rule, so tau_cross, tau_selfA and tau_selfB are computed on exactly the
    same prompt set. Computing the cross tau and the reliabilities on different sets
    would make the ratio in `disattenuate` meaningless.
    """

    def __init__(self, name, uids, prompts, per_pair):
        self.name = name
        self.uids = list(uids)
        self.prompts = prompts
        self.per_pair = per_pair
        self.strata = np.array([prompts[u]["category"] for u in self.uids])

        def col(model, key):
            return np.array([per_pair[(u, model)][key] for u in self.uids],
                            dtype=np.float64)

        def icol(model, key):
            return np.array([per_pair[(u, model)][key] for u in self.uids], dtype=int)

        self.pA, self.pB = col(MODEL_A, "p_hat"), col(MODEL_B, "p_hat")
        self.kA, self.kB = icol(MODEL_A, "k_eff"), icol(MODEL_B, "k_eff")
        self.nhA = icol(MODEL_A, "n_hallucination")
        self.nhB = icol(MODEL_B, "n_hallucination")
        self.npA = icol(MODEL_A, "n_partial")
        self.npB = icol(MODEL_B, "n_partial")
        self.refA = col(MODEL_A, "refusal_rate")
        self.refB = col(MODEL_B, "refusal_rate")
        self.lenA = col(MODEL_A, "mean_output_tokens")
        self.lenB = col(MODEL_B, "mean_output_tokens")
        self.qlen = np.array([prompts[u]["question_words"] for u in self.uids],
                             dtype=np.float64)
        self.qchars = np.array([prompts[u]["question_chars"] for u in self.uids],
                               dtype=np.float64)
        self.source = np.array([prompts[u]["source"] for u in self.uids])

        # split halves, for the noise ceiling
        for tag, model in (("A", MODEL_A), ("B", MODEL_B)):
            for half in ("even", "odd"):
                setattr(self, "p%s_%s" % (tag, half), col(model, "p_hat_" + half))
                setattr(self, "k%s_%s" % (tag, half), icol(model, "k_half_" + half))
                setattr(self, "nh%s_%s" % (tag, half), icol(model, "n_hall_" + half))
                setattr(self, "np%s_%s" % (tag, half),
                        icol(model, "n_partial_" + half))
        assert (self.kA_even > 0).all() and (self.kA_odd > 0).all(), \
            "an empty split half survived the k_eff filter — impossible at k_eff>=16"
        assert (self.kB_even > 0).all() and (self.kB_odd > 0).all()

    def __len__(self):
        return len(self.uids)

    def point_estimates(self, partial_weight=0.0):
        """tau_cross, tau_selfA/B, tau_corr and the rho cross-check (§6.2).

        partial_weight is the §6.1 label-boundary knob: 0.0 is the pre-registered
        primary (label 2 only is a hallucination), 0.5 counts a Partial as half a
        hallucination, 1.0 counts it in full. It is applied to the full-sample P-hats
        AND to both split halves, so a variant tau_cross is divided by reliabilities
        measured under the same definition rather than by the primary's.
        """
        def ph(nh, npart, k):
            return (nh + partial_weight * npart) / k

        pA = ph(self.nhA, self.npA, self.kA)
        pB = ph(self.nhB, self.npB, self.kB)
        pA_even = ph(self.nhA_even, self.npA_even, self.kA_even)
        pA_odd = ph(self.nhA_odd, self.npA_odd, self.kA_odd)
        pB_even = ph(self.nhB_even, self.npB_even, self.kB_even)
        pB_odd = ph(self.nhB_odd, self.npB_odd, self.kB_odd)

        cross = tau_b_blocked(pA, pB, self.strata)
        selfA = tau_b_blocked(pA_even, pA_odd, self.strata)
        selfB = tau_b_blocked(pB_even, pB_odd, self.strata)

        rho_cross = spearman_blocked(pA, pB, self.strata)
        rho_selfA_half = spearman_blocked(pA_even, pA_odd, self.strata)
        rho_selfB_half = spearman_blocked(pB_even, pB_odd, self.strata)
        relA, relB = spearman_brown(rho_selfA_half), spearman_brown(rho_selfB_half)

        return {
            "n_prompts": len(self),
            "n_within_stratum_pairs": cross["n_pairs"],
            "tau_cross": cross["tau_b"],
            "tau_selfA": selfA["tau_b"],
            "tau_selfB": selfB["tau_b"],
            # §6.2 — Spearman's attenuation correction adapted to tau. The formula is
            # derived under classical test theory for Pearson r, so applying it to
            # tau is a HEURISTIC; the rho block below is the licensed version.
            "tau_corr": disattenuate(cross["tau_b"], selfA["tau_b"], selfB["tau_b"]),
            "rho_cross": rho_cross,
            "rho_selfA_halflength": rho_selfA_half,
            "rho_selfB_halflength": rho_selfB_half,
            "rho_selfA_spearman_brown": relA,
            "rho_selfB_spearman_brown": relB,
            "rho_corr": disattenuate(rho_cross, relA, relB),
        }

    def bootstrap(self, iters, seed, batch=BOOTSTRAP_BATCH):
        """Nested bootstrap (§6.6) — prompts within category, then completions.

        Level 1: resample prompts with replacement WITHIN category, preserving each
        stratum's size, so the blocked structure and the stratum weights are held
        fixed across iterations.

        Level 2: resample each prompt's completions with replacement and recompute
        P-hat. Resampling prompts alone would ignore completion-level noise and give
        a CI that is too narrow.

        Two implementation notes that are exact, not approximations:

        1. Drawing k_eff times with replacement from a 0/1 vector with m ones is,
           per draw, a Bernoulli(m / k_eff). So the resampled hallucination count is
           exactly Binomial(k_eff, P-hat) and no completion-level array is needed.
           This is an identity, not a normal approximation.
        2. The completion resample is done WITHIN each odd/even half and the full
           P-hat is reconstructed from the two half-counts. That is one resample per
           prompt (as §6.6 specifies) from which tau_cross and both reliabilities all
           derive, while keeping the two halves the same size and independent. A
           single unstratified resample of all k_eff would destroy the odd/even
           membership the noise ceiling is defined on.
        """
        rng = np.random.default_rng(seed)
        uniq = list(np.unique(self.strata))
        groups = [np.flatnonzero(self.strata == s) for s in uniq]

        out = {k: [] for k in ("tau_cross", "tau_selfA", "tau_selfB", "tau_corr")}
        done = 0
        while done < iters:
            b = min(batch, iters - done)
            acc = {k: np.zeros(b) for k in ("cn", "cdx", "cdy",
                                            "an", "adx", "ady",
                                            "bn", "bdx", "bdy")}
            for g in groups:
                n = len(g)
                if n < 2:
                    continue
                pick = rng.integers(0, n, size=(b, n))
                sel = g[pick]                                   # (b, n) prompt indices

                def half_draw(k_arr, p_arr):
                    k = k_arr[sel]
                    return rng.binomial(k, np.clip(p_arr[sel], 0.0, 1.0)), k

                a_ev, ka_ev = half_draw(self.kA_even, self.pA_even)
                a_od, ka_od = half_draw(self.kA_odd, self.pA_odd)
                b_ev, kb_ev = half_draw(self.kB_even, self.pB_even)
                b_od, kb_od = half_draw(self.kB_odd, self.pB_odd)

                pA = (a_ev + a_od) / (ka_ev + ka_od)
                pB = (b_ev + b_od) / (kb_ev + kb_od)

                for prefix, (x, y) in (
                    ("c", (pA, pB)),
                    ("a", (a_ev / ka_ev, a_od / ka_od)),
                    ("b", (b_ev / kb_ev, b_od / kb_od)),
                ):
                    num, dx, dy = _tau_parts(x, y)
                    acc[prefix + "n"] += num
                    acc[prefix + "dx"] += dx
                    acc[prefix + "dy"] += dy

            def ratio(prefix):
                den = np.sqrt(acc[prefix + "dx"] * acc[prefix + "dy"])
                with np.errstate(divide="ignore", invalid="ignore"):
                    return np.where(den > 0, acc[prefix + "n"] / den, np.nan)

            tc, ta, tb = ratio("c"), ratio("a"), ratio("b")
            with np.errstate(divide="ignore", invalid="ignore"):
                corr = np.where((ta > 0) & (tb > 0), tc / np.sqrt(ta * tb), np.nan)

            out["tau_cross"].extend(tc.tolist())
            out["tau_selfA"].extend(ta.tolist())
            out["tau_selfB"].extend(tb.tolist())
            out["tau_corr"].extend(corr.tolist())
            done += b

        summary = {"iters": iters, "seed": seed}
        for k, v in out.items():
            v = np.asarray(v, dtype=np.float64)
            finite = v[np.isfinite(v)]
            summary[k] = {
                "mean": float(finite.mean()) if len(finite) else float("nan"),
                "ci_lower": (float(np.percentile(finite, 2.5)) if len(finite)
                             else float("nan")),
                "ci_upper": (float(np.percentile(finite, 97.5)) if len(finite)
                             else float("nan")),
                "n_finite": int(len(finite)),
                "n_undefined": int(len(v) - len(finite)),
            }
        return summary


# ── §6.7 degenerate strata and §5.1 exclusions ────────────────────────────────


def keff_filter(uids, per_pair):
    """§5.1 — drop a prompt if EITHER model's k_eff < 16 of 20."""
    kept, dropped = [], []
    for u in uids:
        ka = per_pair[(u, MODEL_A)]["k_eff"]
        kb = per_pair[(u, MODEL_B)]["k_eff"]
        (kept if min(ka, kb) >= K_EFF_MIN else dropped).append(u)
    return kept, dropped


def degenerate_filter(uids, prompts, per_pair):
    """§6.7 — a stratum where EITHER model shows < 5 distinct P-hat values is unstable.

    Reported as degenerate - insufficient variance, excluded from the blocked
    estimator, and the observed distinct-value counts are logged rather than the
    exclusion happening silently.
    """
    by_cat = defaultdict(list)
    for u in uids:
        by_cat[prompts[u]["category"]].append(u)

    kept, report = [], []
    for cat in sorted(by_cat):
        us = by_cat[cat]
        dA = len({per_pair[(u, MODEL_A)]["p_hat"] for u in us})
        dB = len({per_pair[(u, MODEL_B)]["p_hat"] for u in us})
        degenerate = (len(us) < 2 or dA < DEGENERATE_MIN_DISTINCT
                      or dB < DEGENERATE_MIN_DISTINCT)
        report.append({"category": cat, "n_prompts": len(us),
                       "distinct_p_hat_A": dA, "distinct_p_hat_B": dB,
                       "degenerate": degenerate})
        if not degenerate:
            kept.extend(us)
    return kept, report


def make_panel(name, uids, prompts, per_pair, apply_degenerate=True):
    kept, dropped_keff = keff_filter(uids, per_pair)
    if apply_degenerate:
        kept, degen = degenerate_filter(kept, prompts, per_pair)
    else:
        degen = []

    # Per-category k_eff attrition, reported so that a category deleted ENTIRELY by
    # the §5.1 filter is visible. The degenerate-stratum table only lists categories
    # that survived to that stage, so a category wiped out at the k_eff step would
    # otherwise vanish from the report without a line explaining where it went.
    kept_set = set(kept)
    dropped_set = set(dropped_keff)
    attrition = []
    for cat in sorted({prompts[u]["category"] for u in uids}):
        us = [u for u in uids if prompts[u]["category"] == cat]
        attrition.append({
            "category": cat,
            "n_requested": len(us),
            "n_dropped_keff": sum(1 for u in us if u in dropped_set),
            "n_final": sum(1 for u in us if u in kept_set),
        })

    panel = Panel(name, kept, prompts, per_pair) if len(kept) >= 2 else None
    return panel, {"n_requested": len(uids),
                   "n_after_keff": len(uids) - len(dropped_keff),
                   "n_final": len(kept), "dropped_keff": dropped_keff,
                   "keff_attrition_by_category": attrition,
                   "degenerate_report": degen}


# ── confound checks (§6.5) ────────────────────────────────────────────────────


def confound_checks(panel):
    """§6.5.1 surface length, §6.5.2 provenance, §6.5.3 refusal propensity."""
    out = {}

    # 6.5.1 — if the shared ordering is driven by question token length, the
    # geometric-feature story is trivial. Report the raw association AND the
    # residualised tau_cross. A large drop is a finding, not something to suppress.
    out["surface_length"] = {
        "tau_pA_vs_question_words": tau_b_blocked(panel.pA, panel.qlen,
                                                  panel.strata)["tau_b"],
        "tau_pB_vs_question_words": tau_b_blocked(panel.pB, panel.qlen,
                                                  panel.strata)["tau_b"],
        "tau_pA_vs_question_chars": tau_b_blocked(panel.pA, panel.qchars,
                                                  panel.strata)["tau_b"],
        "tau_pB_vs_question_chars": tau_b_blocked(panel.pB, panel.qchars,
                                                  panel.strata)["tau_b"],
        "tau_cross_residualised_on_question_words": tau_b_blocked(
            residualise_within_stratum(panel.pA, panel.qlen, panel.strata),
            residualise_within_stratum(panel.pB, panel.qlen, panel.strata),
            panel.strata)["tau_b"],
    }

    # 6.5.2 — the pool files are a different generation than V3's borderline prompts
    # (§4.1). If the two provenances disagree materially, §4.1 says the primary
    # estimate is recomputed V3-only and reported as such.
    prov = {}
    for src in ("v3", "pool"):
        m = panel.source == src
        n = int(m.sum())
        entry = {"n_prompts": n}
        if n >= 2:
            # Strata are re-derived on the subset, so a provenance slice that leaves
            # a category with one prompt simply drops that category's pairs.
            entry["tau_cross"] = tau_b_blocked(panel.pA[m], panel.pB[m],
                                               panel.strata[m])["tau_b"]
            entry["n_within_stratum_pairs"] = tau_b_blocked(
                panel.pA[m], panel.pB[m], panel.strata[m])["n_pairs"]
            entry["categories"] = dict(Counter(panel.strata[m].tolist()))
        else:
            entry["tau_cross"] = float("nan")
        prov[src] = entry
    prov["difference_v3_minus_pool"] = (
        prov["v3"].get("tau_cross", float("nan"))
        - prov["pool"].get("tau_cross", float("nan")))
    out["provenance"] = prov

    # 6.5.3 — a model that refuses more has structurally lower P-hat. If ordering
    # agreement is carried by shared REFUSAL behaviour rather than shared
    # hallucination behaviour, that is a different and weaker claim.
    out["refusal_propensity"] = {
        "tau_refusalA_vs_refusalB": tau_b_blocked(panel.refA, panel.refB,
                                                 panel.strata)["tau_b"],
        "tau_cross_residualised_on_own_refusal": tau_b_blocked(
            residualise_within_stratum(panel.pA, panel.refA, panel.strata),
            residualise_within_stratum(panel.pB, panel.refB, panel.strata),
            panel.strata)["tau_b"],
        "mean_refusal_rate_A": float(np.nanmean(panel.refA)),
        "mean_refusal_rate_B": float(np.nanmean(panel.refB)),
    }
    return out


def truncation_checks(prompts, recs, per_pair, panel_uids):
    """§6.5.4 — truncation as MEASUREMENT ERROR, not as a confounder.

    Deliberately does NOT residualise P-hat on completion length. An earlier draft of
    the spec specified exactly that and it was wrong: length here is a CONSEQUENCE of
    hallucinating, not a nuisance sitting beside it — the model writes at length
    because it is confabulating. Residualising on a mediator strips real signal and
    would have manufactured a false NO-GO. The question is whether truncation changes
    the LABEL, which the judged data answers directly.
    """
    out = {}
    panel_set = set(panel_uids)

    # truncation rate per model, overall and by category
    rate = {}
    for model in (MODEL_A, MODEL_B):
        n_t = n = 0
        by_cat = defaultdict(lambda: [0, 0])
        for uid, p in prompts.items():
            rec = recs.get((uid, model))
            if not rec:
                continue
            t, k = int(sum(rec["trunc"])), len(rec["trunc"])
            n_t += t
            n += k
            by_cat[p["category"]][0] += t
            by_cat[p["category"]][1] += k
        rate[model] = {
            "n_truncated": n_t, "n_judged": n,
            "rate": (n_t / n) if n else float("nan"),
            "by_category": {c: {"n_truncated": v[0], "n_judged": v[1],
                                "rate": v[0] / v[1] if v[1] else float("nan")}
                            for c, v in sorted(by_cat.items())},
        }
    out["truncation_rate"] = rate

    # Label-neutrality (PRIMARY test). Truncation is model-specific, so the table is
    # per (uid, model): rows = truncated / complete, cols = label 2 / not.
    tables, per_table, coverage = [], [], Counter()
    for uid in sorted(panel_set):
        for model in (MODEL_A, MODEL_B):
            rec = recs.get((uid, model))
            if not rec:
                coverage["no_judged_samples"] += 1
                continue
            trunc = np.array(rec["trunc"], dtype=bool)
            hall = np.array(rec["label"], dtype=int) == LABEL_HALLUCINATION
            if trunc.all():
                # Coverage caveat: no within-prompt contrast exists. Untestable by
                # this method and must be named, not quietly dropped.
                coverage["all_samples_truncated"] += 1
                continue
            if not trunc.any():
                coverage["no_samples_truncated"] += 1
                continue
            coverage["mixed_testable"] += 1
            a = int((trunc & hall).sum())
            b = int((trunc & ~hall).sum())
            c = int((~trunc & hall).sum())
            d = int((~trunc & ~hall).sum())
            tables.append((a, b, c, d))
            per_table.append({
                "uid": uid, "model": model,
                "trunc_hall": a, "trunc_not": b,
                "complete_hall": c, "complete_not": d,
                "fisher_p": fisher_exact_2x2(a, b, c, d),
            })
    ps = [t["fisher_p"] for t in per_table]
    out["label_neutrality"] = {
        "coverage": dict(coverage),
        "n_tables": len(tables),
        "cmh_pooled": cochran_mantel_haenszel(tables),
        "cmh_by_model": {
            m: cochran_mantel_haenszel(
                [(t["trunc_hall"], t["trunc_not"], t["complete_hall"],
                  t["complete_not"]) for t in per_table if t["model"] == m])
            for m in (MODEL_A, MODEL_B)},
        "fisher_n_significant_p05_uncorrected": int(sum(p < 0.05 for p in ps)),
        "fisher_bonferroni_alpha": (0.05 / len(ps)) if ps else float("nan"),
        "fisher_n_significant_bonferroni": int(sum(p < 0.05 / len(ps) for p in ps)) if ps else 0,
        "per_table": per_table,
    }

    # DESCRIPTIVE ONLY (§6.5.4): output_tokens vs label, per model within category.
    # Reported as a finding about confabulation behaviour. Explicitly NOT a control.
    assoc = {}
    for model in (MODEL_A, MODEL_B):
        per_cat = {}
        bucket = defaultdict(lambda: ([], []))
        for uid in panel_set:
            rec = recs.get((uid, model))
            if not rec:
                continue
            cat = prompts[uid]["category"]
            for lab, tok in zip(rec["label"], rec["tokens"]):
                if tok is None:
                    continue
                bucket[cat][0 if lab == LABEL_HALLUCINATION else 1].append(tok)
        for cat, (h, nh) in sorted(bucket.items()):
            per_cat[cat] = {
                "n_hallucination": len(h), "n_other": len(nh),
                "median_tokens_hallucination": float(np.median(h)) if h else float("nan"),
                "median_tokens_other": float(np.median(nh)) if nh else float("nan"),
                "auc_tokens_predict_hallucination": rank_auc(h, nh),
            }
        assoc[model] = per_cat
    out["output_tokens_vs_label_descriptive"] = assoc
    return out


# ── POST-HOC diagnostics (NOT pre-registered) ─────────────────────────────────


def posthoc_ceiling_and_floor(panel, prompts, per_pair):
    """Why is tau_cross low? Separates "models disagree" from "nothing to rank".

    ================== NOT PRE-REGISTERED. READ THIS BEFORE CITING. ==============
    Added 2026-08-26, AFTER seeing the primary result. It is a diagnostic that
    explains the §7 verdict; it does not modify, soften or override it. No number
    below feeds the decision rule. Anything reported from here is post-hoc and must
    be labelled as such in the paper.
    ==============================================================================

    THE PROBLEM IT MEASURES. tau_b's denominator is
    sqrt(den_A * den_B), where den_A counts prompt-pairs Model A gives DIFFERENT
    P-hats to and den_B likewise for Model B. A pair that A ties contributes 0 to the
    numerator but still sits in den_B. So when one model is pinned near the floor and
    ties most pairs while the other spreads out, tau_cross is capped below 1 by the
    TIE STRUCTURE ALONE, before any question of whether the models agree:

        max tau_cross = sqrt(min(den_A, den_B) / max(den_A, den_B))

    WHY THE PRE-REGISTERED CORRECTION CANNOT FIX IT. The §6.2 attenuation correction
    divides by sqrt(tau_selfA * tau_selfB), and each tau_self compares two halves of
    the SAME model — which share a tie structure, so their own ceiling is ~1.0. The
    reliabilities are blind to a between-model tie asymmetry, so tau_corr inherits it
    uncorrected. This is a real gap in §6.2 and is why the ceiling is computed
    explicitly rather than assumed benign.

    The ceiling is also expressed on the tau_corr scale, because that is the scale §7
    thresholds. If max reachable tau_corr had come in below 0.50, the GO outcome
    would have been unreachable by construction and the NO-GO would be
    uninterpretable. Verified 2026-08-26: it did not (0.998 on the primary), so the
    verdict stands. That check is the point of this function — run it every time.
    """
    A, Bm = MODEL_A, MODEL_B
    out = {"NOT_PRE_REGISTERED": True,
           "added": "2026-08-26, after seeing the primary result",
           "feeds_decision_rule": False}

    def blocked_parts(x, y, strata):
        num = dx = dy = 0.0
        for s in np.unique(strata):
            k = strata == s
            a, bx, by = _tau_parts(x[k], y[k])
            num += float(a[0]); dx += float(bx[0]); dy += float(by[0])
        return num, dx, dy

    groups = [("PRIMARY (decision surface)", panel.uids)]
    for cat in sorted(set(panel.strata.tolist())):
        groups.append((cat, [u for u in panel.uids if prompts[u]["category"] == cat]))

    rows = []
    for label, us in groups:
        if len(us) < 2:
            continue
        st = np.array([prompts[u]["category"] for u in us])
        a = np.array([per_pair[(u, A)]["p_hat"] for u in us])
        b = np.array([per_pair[(u, Bm)]["p_hat"] for u in us])
        _, dA, dB = blocked_parts(a, b, st)
        est = Panel("ph", us, prompts, per_pair).point_estimates()
        ceil_cross = (math.sqrt(min(dA, dB) / max(dA, dB)) if max(dA, dB) > 0
                      else float("nan"))
        rel = math.sqrt(max(est["tau_selfA"], 0) * max(est["tau_selfB"], 0))
        ceil_corr = ceil_cross / rel if rel > 0 else float("nan")
        rows.append({
            "group": label, "n_prompts": len(us),
            "pairs_A_distinguishes": dA, "pairs_B_distinguishes": dB,
            "tau_cross": est["tau_cross"], "tau_corr": est["tau_corr"],
            "max_reachable_tau_cross": ceil_cross,
            "max_reachable_tau_corr": ceil_corr,
            "pct_of_reachable_maximum": (100 * est["tau_cross"] / ceil_cross
                                         if ceil_cross and np.isfinite(ceil_cross)
                                         and ceil_cross > 0 else float("nan")),
            "go_reachable": bool(np.isfinite(ceil_corr) and ceil_corr >= GO_TAU_CORR),
        })
    out["ceiling"] = rows

    # Floor effects: the SOURCE of the tie asymmetry. A model that scores exactly 0 on
    # most prompts of a category cannot contribute a difficulty ordering over them —
    # "which prompts are hard for this model" becomes a question about its rare
    # failures. Reported per (category, model) so the asymmetry is visible directly.
    floor = []
    for cat in sorted({prompts[u]["category"] for u in panel.uids}):
        us = [u for u in panel.uids if prompts[u]["category"] == cat]
        for model in (A, Bm):
            v = np.array([per_pair[(u, model)]["p_hat"] for u in us])
            floor.append({
                "category": cat, "model": model, "n_prompts": len(us),
                "pct_exactly_zero": float(100 * (v == 0).mean()),
                "median_p_hat": float(np.median(v)),
                "p90_p_hat": float(np.percentile(v, 90)),
                "distinct_p_hat": int(len(set(v.tolist()))),
            })
    out["floor_effects"] = floor

    # Rescue attempts. Each removes a candidate cause of the low tau; if the verdict
    # were an artifact of that cause, tau_corr would climb past 0.50 here.
    #
    # The both-models-off-the-floor rows condition on the OUTCOME, which selects for
    # agreement and biases tau UPWARD. They are therefore a generous upper bound on
    # what a floor-free prompt set could give, not an estimate of anything.
    rescues = []

    def add_rescue(label, keep, note):
        if len(keep) < 40:
            rescues.append({"variant": label, "n_prompts": len(keep),
                            "note": note + " — too few prompts to estimate"})
            return
        st = np.array([prompts[u]["category"] for u in keep])
        a = np.array([per_pair[(u, A)]["p_hat"] for u in keep])
        b = np.array([per_pair[(u, Bm)]["p_hat"] for u in keep])
        _, dA, dB = blocked_parts(a, b, st)
        est = Panel("rescue", keep, prompts, per_pair).point_estimates()
        ceil = (math.sqrt(min(dA, dB) / max(dA, dB)) if max(dA, dB) > 0
                else float("nan"))
        rescues.append({
            "variant": label, "n_prompts": len(keep),
            "tau_cross": est["tau_cross"], "tau_corr": est["tau_corr"],
            "max_reachable_tau_cross": ceil,
            "clears_go": bool(np.isfinite(est["tau_corr"])
                              and est["tau_corr"] >= GO_TAU_CORR),
            "note": note,
        })

    add_rescue("all primary prompts (reference)", list(panel.uids),
               "the §7 estimate itself")

    # Truncation: gpt-oss truncates ~20% of samples and the §6.5.4 label-neutrality
    # test failed, so truncation-induced label error is a live candidate. It is a
    # PER-PROMPT property, stable across split halves, so it does not lower tau_self
    # and is NOT removed by the attenuation correction — exactly the shape that could
    # manufacture a false NO-GO. Dropping the affected prompts tests it directly.
    for thr, lab in ((0.5, "gpt-oss truncation <= 50% of samples"),
                     (0.2, "gpt-oss truncation <= 20% of samples"),
                     (1e-9, "gpt-oss truncation == 0 (no truncation at all)")):
        keep = [u for u in panel.uids
                if (per_pair[(u, Bm)]["n_truncated"]
                    / max(per_pair[(u, Bm)]["k_eff"], 1)) < thr]
        add_rescue(lab, keep, "tests whether truncation error drives the low tau")

    for thr in (0.0, 0.05, 0.10):
        keep = [u for u in panel.uids
                if per_pair[(u, A)]["p_hat"] > thr
                and per_pair[(u, Bm)]["p_hat"] > thr]
        add_rescue(f"both models P-hat > {thr}", keep,
                   "removes the floor AND the tie ceiling, but conditions on the "
                   "outcome so it is biased UPWARD — a generous upper bound")
    out["rescue_attempts"] = rescues

    # Coarse-vs-fine contrast. The intuition "surely models agree about what is hard"
    # is about CATEGORY-level difficulty, and it is correct. The claim under test is
    # WITHIN-category ordering. Reporting both side by side is what makes the result
    # legible instead of counter-intuitive.
    cat_means = []
    for cat in sorted({prompts[u]["category"] for u in prompts}):
        us = [u for u in prompts
              if prompts[u]["category"] == cat
              and min(per_pair[(u, A)]["k_eff"], per_pair[(u, Bm)]["k_eff"]) >= K_EFF_MIN]
        if not us:
            continue
        cat_means.append({
            "category": cat, "n_prompts": len(us),
            "mean_p_hat_A": float(np.mean([per_pair[(u, A)]["p_hat"] for u in us])),
            "mean_p_hat_B": float(np.mean([per_pair[(u, Bm)]["p_hat"] for u in us])),
        })
    ra = _rank_avg([c["mean_p_hat_A"] for c in cat_means])
    rb = _rank_avg([c["mean_p_hat_B"] for c in cat_means])
    n_cat = len(cat_means)
    out["coarse_vs_fine"] = {
        "category_means": cat_means,
        "tau_b_between_category_orderings": (
            tau_b_blocked(ra, rb, np.zeros(n_cat))["tau_b"] if n_cat >= 2
            else float("nan")),
        "note": "Category-level agreement is high and is NOT what §7 tests. The "
                "decision surface is within-category ordering, because between-"
                "category agreement is trivially true (§2.1).",
    }
    return out


# ── §6.4 rate-level divergence ────────────────────────────────────────────────


def marginal_rates(prompts, per_pair, uids):
    """Per model, per category: marginal hallucination rate with CIs (§6.4).

    Purpose is to show explicitly that the two models can differ substantially in
    RATE while agreeing in ORDERING — the evidence for the §1 rephrasing.

    Two intervals are reported. The completion-level Wilson interval is the
    "binomial CI" §6.4 asks for; it treats the 20 samples of a prompt as independent,
    which they are not, so it is anticonservative. The prompt-mean interval with a
    bootstrap over prompts is added alongside because that is the one a reviewer
    should read for a between-model rate comparison.
    """
    rows = []
    rng = np.random.default_rng(BOOTSTRAP_SEED + 1)
    by_cat = defaultdict(list)
    for u in uids:
        by_cat[prompts[u]["category"]].append(u)
    for cat in sorted(by_cat):
        for model in (MODEL_A, MODEL_B):
            us = by_cat[cat]
            n_h = sum(per_pair[(u, model)]["n_hallucination"] for u in us)
            n_k = sum(per_pair[(u, model)]["k_eff"] for u in us)
            lo, hi = wilson_interval(n_h, n_k)
            ph = np.array([per_pair[(u, model)]["p_hat"] for u in us])
            ph = ph[np.isfinite(ph)]
            if len(ph) >= 2:
                draws = ph[rng.integers(0, len(ph), size=(2000, len(ph)))].mean(axis=1)
                plo, phi = np.percentile(draws, [2.5, 97.5])
            else:
                plo = phi = float("nan")
            rows.append({
                "category": cat, "model": model, "n_prompts": len(us),
                "n_completions": n_k, "n_hallucination": n_h,
                "rate_completion_level": (n_h / n_k) if n_k else float("nan"),
                "wilson_lo": lo, "wilson_hi": hi,
                "mean_p_hat_over_prompts": float(ph.mean()) if len(ph) else float("nan"),
                "prompt_bootstrap_lo": float(plo), "prompt_bootstrap_hi": float(phi),
                "mean_refusal_rate": float(np.nanmean(
                    [per_pair[(u, model)]["refusal_rate"] for u in us])),
            })
    return rows


# ── §6.3 the stratification contrast ──────────────────────────────────────────


def secondary_contrast(prompts, per_pair, uids, iters, seed):
    """§6.3 — pooled tau next to blocked tau, plus per-category tau with CIs.

    The gap between pooled and blocked is the quantitative version of §2.1: pooled
    tau over heterogeneous categories measures benchmark stratification, not model
    agreement, and this is the figure that shows it.
    """
    kept, dropped = keff_filter(uids, per_pair)
    if len(kept) < 2:
        return {"error": "too few prompts survive the k_eff filter", "n_final": len(kept)}

    strata = np.array([prompts[u]["category"] for u in kept])
    pA = np.array([per_pair[(u, MODEL_A)]["p_hat"] for u in kept])
    pB = np.array([per_pair[(u, MODEL_B)]["p_hat"] for u in kept])

    pooled = tau_b_blocked(pA, pB, np.zeros(len(kept)))   # one stratum = pooled
    blocked = tau_b_blocked(pA, pB, strata)

    # §11.2 — third rung. With 38 externally-defined strata, the ladder
    # pooled -> coarse-13 -> native-38 separates the inflation into "between broad
    # topic" and "between related category", which one gap cannot. Only computed when
    # the manifest actually carries a distinct coarse field, so Phase 0.5 is untouched.
    coarse = None
    coarse_strata = np.array([prompts[u]["coarse_category"] for u in kept])
    if len({s for s in coarse_strata.tolist()}) != len({s for s in strata.tolist()}):
        coarse = tau_b_blocked(pA, pB, coarse_strata)

    per_cat = []
    for cat_i, cat in enumerate(sorted(set(strata.tolist()))):
        us = [u for u in kept if prompts[u]["category"] == cat]
        # The degenerate rule is REPORTED here rather than applied: §4.5 keeps
        # borderline_edge_factual in the secondary set precisely as a documented
        # negative control, so its failure mode has to stay visible.
        _, degen = degenerate_filter(us, prompts, per_pair)
        panel = Panel("secondary:" + cat, us, prompts, per_pair) if len(us) >= 2 else None
        entry = {"category": cat, "n_prompts": len(us),
                 "degenerate_report": degen}
        if panel is not None:
            entry.update(panel.point_estimates())
            # Fewer iterations per category than the primary: these are secondary
            # descriptives, not the decision surface, and there are up to 7 of them.
            # Seed offset is the sorted-position index, NOT hash(cat) — Python string
            # hashing is salted per process, so a hash-derived seed would make these
            # CIs silently irreproducible between runs.
            entry["bootstrap"] = panel.bootstrap(max(200, iters // 5),
                                                 seed + 1000 + cat_i)
        per_cat.append(entry)

    return {
        "n_requested": len(uids), "n_final": len(kept),
        "n_dropped_keff": len(dropped),
        "pooled_tau_b": pooled["tau_b"],
        "pooled_n_pairs": pooled["n_pairs"],
        "blocked_tau_b": blocked["tau_b"],
        "blocked_n_pairs": blocked["n_pairs"],
        "stratification_inflation": pooled["tau_b"] - blocked["tau_b"],
        "coarse_tau_b": None if coarse is None else coarse["tau_b"],
        "coarse_n_pairs": None if coarse is None else coarse["n_pairs"],
        "coarse_n_strata": (None if coarse is None
                            else len(set(coarse_strata.tolist()))),
        "n_strata": len(set(strata.tolist())),
        "per_category": per_cat,
    }


# ── §7 verdict ────────────────────────────────────────────────────────────────


def verdict(point, boot):
    """The pre-registered decision rule (§7). Order of evaluation matters.

    MEASUREMENT FAILURE is checked FIRST and returns inconclusive, not negative. Low
    reliability means we cannot see the signal at this k, which is a different fact
    from the signal being absent; conflating them would kill the paper on an artifact.
    """
    tsa, tsb = point["tau_selfA"], point["tau_selfB"]
    tc, ci_lo = point["tau_corr"], boot["tau_corr"]["ci_lower"]

    if not np.isfinite(tsa) or not np.isfinite(tsb) \
            or tsa <= MEASUREMENT_FAILURE_TAU_SELF or tsb <= MEASUREMENT_FAILURE_TAU_SELF:
        return {
            "verdict": "MEASUREMENT FAILURE",
            "reason": (f"tau_selfA={tsa:.4f}, tau_selfB={tsb:.4f}; §7 requires both "
                       f"> {MEASUREMENT_FAILURE_TAU_SELF}"),
            "action": ("Inconclusive, NOT negative. Escalate k from 20 to 40 and "
                       "re-run before drawing any conclusion about the claim."),
        }
    if not np.isfinite(tc):
        return {"verdict": "MEASUREMENT FAILURE",
                "reason": "tau_corr is undefined",
                "action": "Escalate k from 20 to 40 and re-run."}
    if tc >= GO_TAU_CORR and np.isfinite(ci_lo) and ci_lo >= GO_CI_LOWER:
        return {
            "verdict": "GO",
            "reason": (f"tau_corr={tc:.4f} >= {GO_TAU_CORR} and bootstrap 95% CI "
                       f"lower bound={ci_lo:.4f} >= {GO_CI_LOWER}"),
            "action": "Proceed to Phase 1 panel scale-up.",
        }
    return {
        "verdict": "NO-GO",
        "reason": (f"tau_corr={tc:.4f} (need >= {GO_TAU_CORR}), bootstrap 95% CI "
                   f"lower bound={ci_lo:.4f} (need >= {GO_CI_LOWER})"),
        "action": ("Do NOT scale. Take the result to Sunny and reframe before "
                   "spending on the panel."),
    }


# ── report ────────────────────────────────────────────────────────────────────


def f(x, nd=4):
    if x is None:
        return "—"
    try:
        return "n/a" if not np.isfinite(x) else f"{x:.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def render_report(R):
    L = []
    w = L.append
    w("# Phase 0.5 analysis — Kendall's tau pilot")
    w("")
    w("Generated by `scripts/analyze_phase05.py`. Every estimator, threshold and")
    w("exclusion rule below is pre-registered in `research_paper/PHASE_0.5_SPEC.md`;")
    w("the section numbers are the audit trail.")
    w("")
    cfg = R["inputs"]["decoding_config"]
    w(f"Decoding config (§3): {json.dumps(cfg, sort_keys=True)}")
    w(f"P-hat is defined relative to this config — a scope statement for the paper.")
    w("")

    # ── integrity ──
    ig = R["integrity"]
    w("## Data integrity (§5.1)")
    w("")
    w(f"| Quantity | Value |")
    w(f"|---|---|")
    w(f"| Completion rows | {ig['n_completion_rows']:,} |")
    w(f"| Judgment rows (append-only; includes retried failures) | "
      f"{ig['n_judgment_rows']:,} |")
    w(f"| Completions with a label | {ig['n_labelled']:,} |")
    w(f"| **Completions with NO label (unrecovered)** | "
      f"**{ig['n_unrecovered_completions']:,}** |")
    w(f"| **Unrecovered rate — this is what gates §5.1** | "
      f"**{ig['unrecovered_rate']*100:.2f}%** (threshold "
      f"{FAILURE_RATE_ABORT*100:.0f}%) |")
    w(f"| Gross judge call-failure rate (diagnostic, does NOT gate) | "
      f"{ig['gross_call_failure_rate']*100:.2f}% ({ig['n_failed_rows']:,} rows) |")
    w(f"| Duplicate successful judgments dropped | "
      f"{ig['n_duplicate_successes_dropped']:,} |")
    w(f"| Orphan judgments (no matching completion) | {ig['n_orphan_judgments']:,} |")
    w(f"| (uid, model) pairs in manifest x models | {ig['n_pairs_expected']:,} |")
    w(f"| Pairs with k_eff = 0 | {ig['n_pairs_keff_zero']:,} |")
    w(f"| Pairs with k_eff < {K_EFF_MIN} | {ig['n_pairs_below_keff']:,} |")
    w("")
    w("The gate is driven by the UNRECOVERED rate, not by failed rows over total")
    w("rows. `run_phase05_judging.py` appends rather than rewrites, so a retried")
    w("failure leaves its old failure row in the file; a row-based rate would never")
    w("fall back under 2% however completely the run is recovered, and would wedge")
    w("this gate permanently shut.")
    w("")
    w("k_eff distribution over the full manifest x models cross-product:")
    w("")
    w("| k_eff | pairs |")
    w("|---|---|")
    for k in sorted(ig["keff_histogram"], key=int):
        w(f"| {k} | {ig['keff_histogram'][k]:,} |")
    w("")
    if ig["gate_tripped"]:
        w("> **§5.1 INFRASTRUCTURE FAILURE.** The unrecovered rate exceeds the 2%")
        w("> threshold, so this run is not data and the §7 verdict is not licensed.")
        if ig["error_summary"]:
            w("> Dominant judge errors:")
            for msg, n in ig["error_summary"]:
                w(f"> - {n:,} x `{msg}`")
        w(">")
        w("> Recover with `python3 scripts/run_phase05_judging.py --retry-failed`,")
        w("> then re-run this script. Everything below is computed on the labelled")
        w("> subset and is **provisional**: the missing judgments are not missing at")
        w("> random — they arrived in a contiguous block, so whole prompts are absent")
        w("> rather than scattered samples, and the surviving set is not a random")
        w("> sample of the primary surface.")
        w("")

    # ── panels ──
    for key, title, sec in (("primary", "Primary set — the decision surface", "§4.1"),
                            ("judgebound", "Judge-bound set — artifact diagnostic", "§4.2")):
        P = R[key]
        w(f"## {title} ({sec})")
        w("")
        if P.get("error"):
            w(f"**Not computable:** {P['error']}")
            w("")
            continue
        sel = P["selection"]
        w(f"Prompts requested {sel['n_requested']} → after §5.1 k_eff filter "
          f"{sel['n_after_keff']} → after §6.7 degenerate rule **{sel['n_final']}**.")
        w("")
        w("| Category | requested | dropped by §5.1 k_eff < 16 | in panel |")
        w("|---|---|---|---|")
        for a in sel["keff_attrition_by_category"]:
            note = " — **category eliminated**" if a["n_final"] == 0 else ""
            w(f"| {a['category']}{note} | {a['n_requested']} | "
              f"{a['n_dropped_keff']} | {a['n_final']} |")
        w("")
        if sel["degenerate_report"]:
            w("| Category | n | distinct P-hat A | distinct P-hat B | §6.7 degenerate |")
            w("|---|---|---|---|---|")
            for d in sel["degenerate_report"]:
                w(f"| {d['category']} | {d['n_prompts']} | {d['distinct_p_hat_A']} | "
                  f"{d['distinct_p_hat_B']} | {'YES — excluded' if d['degenerate'] else 'no'} |")
            w("")
        pt, bt = P["point"], P["bootstrap"]
        w(f"Within-stratum pairs: **{pt['n_within_stratum_pairs']:,}**")
        w("")
        w("| Statistic | Value | bootstrap mean | 95% CI (nested bootstrap, §6.6) |")
        w("|---|---|---|---|")
        for name, k in (("tau_cross (blocked tau_b)", "tau_cross"),
                        ("tau_selfA (split-half, Model A)", "tau_selfA"),
                        ("tau_selfB (split-half, Model B)", "tau_selfB"),
                        ("**tau_corr (attenuation-corrected)**", "tau_corr")):
            ci = bt[k]
            w(f"| {name} | {f(pt[k])} | {f(ci['mean'])} | "
              f"[{f(ci['ci_lower'])}, {f(ci['ci_upper'])}] |")
        w("")
        if bt["tau_corr"]["n_undefined"]:
            w(f"{bt['tau_corr']['n_undefined']} of {bt['iters']} bootstrap iterations "
              "left tau_corr undefined (a non-positive resampled reliability) and are "
              "excluded from the percentiles. A large count is itself a reliability "
              "warning.")
            w("")
        # The direction of this bias is knowable a priori and is not a bug, but it
        # lands on the §7 test, so it is reported rather than absorbed.
        bias_self = min(bt["tau_selfA"]["mean"] - pt["tau_selfA"],
                        bt["tau_selfB"]["mean"] - pt["tau_selfB"])
        if np.isfinite(bias_self) and bias_self < -0.005:
            w("**Direction of the nested-bootstrap bias, and it points the wrong way for")
            w("§7.** The bootstrap means of tau_selfA and tau_selfB sit BELOW their point")
            w("estimates. That is expected, not a defect: level 2 of §6.6 resamples")
            w("completions, which adds a second layer of sampling noise on top of an")
            w("already-noisy P-hat, and extra noise attenuates a reliability coefficient")
            w("systematically downward. Because tau_corr divides by sqrt(tau_selfA *")
            w("tau_selfB), a downward bias in the denominator produces an UPWARD bias in")
            w("resampled tau_corr — visible above as a bootstrap mean above the point")
            w("estimate. §7 tests the CI LOWER bound, so this bias is")
            w("**anti-conservative**: it makes GO marginally easier to reach than the")
            w("nominal 0.30 threshold implies. The procedure is pre-registered and is")
            w("not changed here; the direction is stated so a reviewer can weigh a")
            w("borderline lower bound correctly.")
            w("")
        w("Licensed cross-check (§6.2) — Spearman rho with Spearman-Brown reliability:")
        w("")
        w("| Statistic | Value |")
        w("|---|---|")
        w(f"| rho_cross (stratified) | {f(pt['rho_cross'])} |")
        w(f"| reliability A (half {f(pt['rho_selfA_halflength'])} → "
          f"full {f(pt['rho_selfA_spearman_brown'])}) | "
          f"{f(pt['rho_selfA_spearman_brown'])} |")
        w(f"| reliability B (half {f(pt['rho_selfB_halflength'])} → "
          f"full {f(pt['rho_selfB_spearman_brown'])}) | "
          f"{f(pt['rho_selfB_spearman_brown'])} |")
        w(f"| **rho_corr** | **{f(pt['rho_corr'])}** |")
        w(f"| tau_corr − rho_corr | {f(pt['tau_corr'] - pt['rho_corr'])} |")
        w("")
        w("The tau disattenuation is a heuristic: Spearman's correction is derived for")
        w("Pearson r under classical test theory. rho_corr is the formally licensed")
        w("version. A material disagreement between the two is itself a finding (§9.4).")
        w("")
        w("The split-half ceiling is the reliability of a k=10 estimate, but tau_cross")
        w("uses k=20, so the ceiling is a CONSERVATIVE (low) estimate of the true k=20")
        w("ceiling and tau_corr is therefore slightly OVER-corrected (§6.2, §9.3).")
        w("")
        if P.get("label_boundary"):
            w("Label-boundary sensitivity (§6.1) — relabelling only, no new API calls.")
            w("The reliabilities are recomputed under each definition, so every row's")
            w("tau_corr is internally consistent:")
            w("")
            w("| P-hat definition | tau_cross | tau_selfA | tau_selfB | tau_corr |")
            w("|---|---|---|---|---|")
            for row in P["label_boundary"]:
                w(f"| {row['definition']} | {f(row['tau_cross'])} | "
                  f"{f(row['tau_selfA'])} | {f(row['tau_selfB'])} | "
                  f"{f(row['tau_corr'])} |")
            w("")
            w("If tau_corr moves materially across these rows the label boundary is")
            w("load-bearing and must be discussed in the paper (§6.1, §9.9).")
            w("")

    # ── Δ_artifact ──
    w("## Shared-judge artifact (§6.2b)")
    w("")
    da = R["delta_artifact"]
    if da.get("value") is None:
        w(f"Not computable: {da.get('error')}")
    else:
        w(f"    Δ_artifact = tau_corr(judge-bound) − tau_corr(verifiable)")
        w(f"               = {f(da['tau_corr_judgebound'])} − {f(da['tau_corr_primary'])}"
          f" = **{f(da['value'])}**")
        w("")
        w("Δ > 0 is the expected direction and is the measurement of interest: it")
        w("estimates how much apparent cross-model ordering agreement is manufactured")
        w("by scoring both models against a shared judge's parametric knowledge rather")
        w("than against verified ground truth. **Excluded from the §7 decision rule** —")
        w("the decision runs on the verifiable strata alone.")
    w("")

    # ── 6.3 ──
    w("## Stratification contrast (§6.3, secondary set)")
    w("")
    S = R["secondary"]
    if S.get("error"):
        w(f"Not computable: {S['error']}")
    else:
        w(f"{S['n_final']} prompts across {S.get('n_strata', 7)} categories "
          f"({S['n_dropped_keff']} dropped by the k_eff filter).")
        w("")
        w("| Estimator | tau_b | pairs |")
        w("|---|---|---|")
        w(f"| **pooled** — *stratification-inflated, NOT a test of the claim* | "
          f"{f(S['pooled_tau_b'])} | {S['pooled_n_pairs']:,} |")
        if S.get("coarse_tau_b") is not None:
            w(f"| coarse ({S['coarse_n_strata']} merged strata, §11.2 — "
              f"**secondary only, never the decision statistic**) | "
              f"{f(S['coarse_tau_b'])} | {S['coarse_n_pairs']:,} |")
        w(f"| blocked (within-category) | {f(S['blocked_tau_b'])} | "
          f"{S['blocked_n_pairs']:,} |")
        w(f"| **inflation (pooled − blocked)** | **{f(S['stratification_inflation'])}** | |")
        if S.get("coarse_tau_b") is not None:
            w("")
            w("The three-rung ladder separates the inflation into its two parts, which a")
            w("single pooled−blocked gap cannot: **pooled → coarse** is inflation from")
            w("mixing broad topics, **coarse → blocked** is inflation from mixing related")
            w("categories inside one topic. Per §11.2 the *finer* blocking is the")
            w("pre-registered primary, because coarsening strata can only raise tau.")
        w("")
        w("Per category (`borderline_edge_factual` is the §4.5 documented negative")
        w("control — degenerate variance is the expected result, reported not hidden):")
        w("")
        w("| Category | n | tau_cross | tau_selfA | tau_selfB | tau_corr | "
          "tau_corr 95% CI | §6.7 |")
        w("|---|---|---|---|---|---|---|---|")
        for c in S["per_category"]:
            if "tau_cross" not in c:
                w(f"| {c['category']} | {c['n_prompts']} | — | — | — | — | — | n<2 |")
                continue
            ci = c["bootstrap"]["tau_corr"]
            deg = "degenerate" if (c["degenerate_report"]
                                  and c["degenerate_report"][0]["degenerate"]) else "ok"
            w(f"| {c['category']} | {c['n_prompts']} | {f(c['tau_cross'])} | "
              f"{f(c['tau_selfA'])} | {f(c['tau_selfB'])} | {f(c['tau_corr'])} | "
              f"[{f(ci['ci_lower'])}, {f(ci['ci_upper'])}] | {deg} |")
    w("")

    # ── 6.4 ──
    w("## Rate-level divergence (§6.4)")
    w("")
    w("Models may differ substantially in RATE while agreeing in ORDERING — that")
    w("compatibility is the whole point of the §1 rephrasing.")
    w("")
    w("| Category | Model | n prompts | rate (completion-level) | Wilson 95% | "
      "mean P-hat over prompts | prompt-bootstrap 95% | refusal rate |")
    w("|---|---|---|---|---|---|---|---|")
    for r in R["marginal_rates"]:
        w(f"| {r['category']} | {MODEL_LABELS[r['model']]} | {r['n_prompts']} | "
          f"{f(r['rate_completion_level'], 4)} | [{f(r['wilson_lo'])}, {f(r['wilson_hi'])}] | "
          f"{f(r['mean_p_hat_over_prompts'])} | [{f(r['prompt_bootstrap_lo'])}, "
          f"{f(r['prompt_bootstrap_hi'])}] | {f(r['mean_refusal_rate'])} |")
    w("")
    w("The Wilson interval treats a prompt's 20 samples as independent, which they are")
    w("not, so it is anticonservative. Read the prompt-bootstrap interval for any")
    w("between-model rate comparison.")
    w("")

    # ── 6.5 ──
    w("## Pre-registered confound checks (§6.5)")
    w("")
    C = R.get("confounds")
    if not C:
        w("Not computable — no primary panel.")
    else:
        sl = C["surface_length"]
        w("### §6.5.1 Surface length")
        w("")
        w("If the shared ordering is driven by question length, the geometric-feature")
        w("story is trivial.")
        w("")
        w("| Quantity | tau_b |")
        w("|---|---|")
        w(f"| P-hat_A vs question words | {f(sl['tau_pA_vs_question_words'])} |")
        w(f"| P-hat_B vs question words | {f(sl['tau_pB_vs_question_words'])} |")
        w(f"| P-hat_A vs question chars | {f(sl['tau_pA_vs_question_chars'])} |")
        w(f"| P-hat_B vs question chars | {f(sl['tau_pB_vs_question_chars'])} |")
        w(f"| tau_cross, both residualised on length | "
          f"{f(sl['tau_cross_residualised_on_question_words'])} |")
        w(f"| drop vs raw tau_cross | "
          f"{f(R['primary']['point']['tau_cross'] - sl['tau_cross_residualised_on_question_words'])} |")
        w("")
        w("Length is proxied by whitespace word count — no tokenizer is installed and")
        w("neither evaluated model's tokenizer is available offline. Because tau_b is")
        w("rank-based, a monotone reparameterisation of the predictor leaves the two")
        w("association rows unchanged; only the residualised row is proxy-dependent.")
        w("")
        pv = C["provenance"]
        w("### §6.5.2 Provenance homogeneity")
        w("")
        w("| Provenance | n | tau_cross |")
        w("|---|---|---|")
        for src in ("v3", "pool"):
            w(f"| `{src}` | {pv[src]['n_prompts']} | {f(pv[src]['tau_cross'])} |")
        w(f"| difference (v3 − pool) | | {f(pv['difference_v3_minus_pool'])} |")
        w("")
        w("§4.1: if these differ materially the primary estimate is recomputed V3-only")
        w("and reported as such. Pool prompts are a different generation than V3's")
        w("borderline prompts (§9.6).")
        w("")
        rf = C["refusal_propensity"]
        w("### §6.5.3 Refusal propensity")
        w("")
        w("| Quantity | Value |")
        w("|---|---|")
        w(f"| tau_b between the two models' refusal rates | "
          f"{f(rf['tau_refusalA_vs_refusalB'])} |")
        w(f"| tau_cross with each P-hat residualised on its own refusal rate | "
          f"{f(rf['tau_cross_residualised_on_own_refusal'])} |")
        w(f"| mean refusal rate, Model A | {f(rf['mean_refusal_rate_A'])} |")
        w(f"| mean refusal rate, Model B | {f(rf['mean_refusal_rate_B'])} |")
        w("")
        w("If ordering agreement is substantially carried by shared refusal behaviour")
        w("rather than shared hallucination behaviour, that is a different and weaker")
        w("claim and must be reported as such.")
        w("")

    T = R.get("truncation")
    if T:
        w("### §6.5.4 Completion length and truncation")
        w("")
        w("**P-hat is deliberately NOT residualised on completion length.** Length here")
        w("is a consequence of hallucinating, not a nuisance beside it: the model writes")
        w("at length *because* it is confabulating. Residualising on a mediator strips")
        w("real signal and would manufacture a false NO-GO. The question is whether")
        w("truncation changes the LABEL.")
        w("")
        w("| Model | truncation rate | n truncated / n judged |")
        w("|---|---|---|")
        for m in (MODEL_A, MODEL_B):
            tr = T["truncation_rate"][m]
            w(f"| {MODEL_LABELS[m]} | {f(tr['rate'])} | "
              f"{tr['n_truncated']:,} / {tr['n_judged']:,} |")
        w("")
        w("| Category | " + " | ".join(MODEL_LABELS[m] for m in (MODEL_A, MODEL_B)) + " |")
        w("|---|---|---|")
        cats = sorted(set(T["truncation_rate"][MODEL_A]["by_category"]) |
                      set(T["truncation_rate"][MODEL_B]["by_category"]))
        for c in cats:
            cells = []
            for m in (MODEL_A, MODEL_B):
                e = T["truncation_rate"][m]["by_category"].get(c)
                cells.append(f(e["rate"]) if e else "—")
            w(f"| {c} | " + " | ".join(cells) + " |")
        w("")
        ln = T["label_neutrality"]
        w("**Label-neutrality test (primary), on the primary panel.** Per (prompt, model)")
        w("2x2 table: truncated/complete x hallucination/not, Fisher exact per table,")
        w("pooled with Cochran-Mantel-Haenszel.")
        w("")
        w("| Coverage class | (prompt, model) pairs |")
        w("|---|---|")
        for k, v in sorted(ln["coverage"].items()):
            w(f"| {k} | {v:,} |")
        w("")
        w("`all_samples_truncated` and `no_samples_truncated` admit no within-prompt")
        w("contrast and are **untestable by this method** — named here rather than")
        w("silently dropped (§6.5.4 coverage caveat).")
        w("")
        w("| Pooled test | informative tables | chi2 (1 df) | p | MH odds ratio |")
        w("|---|---|---|---|---|")
        cm = ln["cmh_pooled"]
        w(f"| all models | {cm['n_tables_informative']} | {f(cm['chi2'])} | "
          f"{f(cm['p_value'], 5)} | {f(cm['mh_odds_ratio'])} |")
        for m in (MODEL_A, MODEL_B):
            cm = ln["cmh_by_model"][m]
            w(f"| {MODEL_LABELS[m]} | {cm['n_tables_informative']} | {f(cm['chi2'])} | "
              f"{f(cm['p_value'], 5)} | {f(cm['mh_odds_ratio'])} |")
        w("")
        w(f"Fisher tables significant at uncorrected p<0.05: "
          f"{ln['fisher_n_significant_p05_uncorrected']} of {ln['n_tables']}; "
          f"at Bonferroni alpha={f(ln['fisher_bonferroni_alpha'], 6)}: "
          f"{ln['fisher_n_significant_bonferroni']}.")
        w("")
        w("No difference ⇒ truncation is label-neutral and the confound is closed.")
        w("An MH odds ratio above 1 means truncated samples are labelled hallucination")
        w("*more* often than complete samples of the same prompt.")
        w("")
        w("**Descriptive only** (§6.5.4) — output_tokens vs label, per model within")
        w("category. A finding about confabulation behaviour, explicitly NOT a control.")
        w("")
        w("| Model | Category | median tokens (hall.) | median tokens (other) | "
          "AUC tokens→hallucination |")
        w("|---|---|---|---|---|")
        for m in (MODEL_A, MODEL_B):
            for c, e in sorted(T["output_tokens_vs_label_descriptive"][m].items()):
                w(f"| {MODEL_LABELS[m]} | {c} | {f(e['median_tokens_hallucination'], 1)} | "
                  f"{f(e['median_tokens_other'], 1)} | "
                  f"{f(e['auc_tokens_predict_hallucination'])} |")
        w("")

    # ── verdict ──
    w("## §7 Pre-registered decision rule (binding)")
    w("")
    V = R["verdict"]
    w(f"| Outcome | Condition |")
    w(f"|---|---|")
    w(f"| GO | tau_corr ≥ {GO_TAU_CORR} **and** CI lower bound ≥ {GO_CI_LOWER} |")
    w(f"| NO-GO | tau_corr < {GO_TAU_CORR}, or CI lower bound < {GO_CI_LOWER} |")
    w(f"| MEASUREMENT FAILURE | tau_selfA ≤ {MEASUREMENT_FAILURE_TAU_SELF} or "
      f"tau_selfB ≤ {MEASUREMENT_FAILURE_TAU_SELF} |")
    w("")
    w(f"### VERDICT: {V['verdict']}")
    w("")
    w(f"- **Basis:** {V.get('reason', '—')}")
    w(f"- **Action:** {V.get('action', '—')}")
    if V.get("provisional"):
        w("")
        w("> **PROVISIONAL — NOT the pre-registered verdict.** §5.1's 2% judge-failure")
        w("> gate is tripped, so this run is an infrastructure failure and no verdict is")
        w("> licensed from it. The number above was computed only because")
        w("> `--ignore-failure-gate` was passed. Do not put it in the paper, do not")
        w("> take it to an advisor, and do not treat it as evidence either way.")
    w("")

    # ── post-hoc diagnostics ──
    D = R.get("posthoc_diagnostics")
    if D:
        w("---")
        w("")
        w("# Post-hoc diagnostics — WHY the tau is low")
        w("")
        w("> **NOT PRE-REGISTERED.** Added 2026-08-26, after seeing the primary")
        w("> result. Nothing in this part feeds the §7 decision rule. It exists to")
        w("> distinguish *the models order prompts differently* from *there was no")
        w("> ordering to share*. Anything cited from here must be labelled post-hoc.")
        w("")
        w("## The tau_b tie ceiling")
        w("")
        w("`tau_b = num / sqrt(den_A * den_B)`, where `den_A` counts prompt-pairs")
        w("Model A gives different P-hats to. A pair that A **ties** contributes 0 to")
        w("the numerator but still sits in `den_B`. So when one model is pinned near")
        w("the floor and ties most pairs while the other spreads out, tau_cross is")
        w("capped below 1 by tie structure alone — before any question of agreement:")
        w("")
        w("    max tau_cross = sqrt(min(den_A, den_B) / max(den_A, den_B))")
        w("")
        w("**The §6.2 attenuation correction cannot remove this.** Each tau_self")
        w("compares two halves of the *same* model, which share a tie structure, so")
        w("their own ceiling is ~1.0. The reliabilities are blind to a *between-model*")
        w("tie asymmetry, and tau_corr inherits it uncorrected. This is a genuine gap")
        w("in §6.2, which is why the ceiling is computed rather than assumed benign.")
        w("")
        w("| Group | n | pairs A splits | pairs B splits | tau_cross | max tau_cross | "
          "% of max | max tau_corr | GO reachable? |")
        w("|---|---|---|---|---|---|---|---|---|")
        for r in D["ceiling"]:
            w(f"| {r['group']} | {r['n_prompts']} | {r['pairs_A_distinguishes']:.0f} | "
              f"{r['pairs_B_distinguishes']:.0f} | {f(r['tau_cross'], 3)} | "
              f"{f(r['max_reachable_tau_cross'], 3)} | "
              f"{f(r['pct_of_reachable_maximum'], 0)}% | "
              f"{f(r['max_reachable_tau_corr'], 3)} | "
              f"{'YES' if r['go_reachable'] else '**NO — verdict uninterpretable**'} |")
        w("")
        w("**Read the last column first.** If max reachable tau_corr were below "
          f"{GO_TAU_CORR}, GO would have been unreachable by construction and the §7")
        w("verdict would be meaningless rather than negative. Where it reads YES, the")
        w("ceiling is real but left room, and the verdict stands on its own terms.")
        w("")
        w("## Floor effects — the source of the tie asymmetry")
        w("")
        w("A model scoring exactly 0 on most prompts of a category cannot contribute a")
        w("difficulty ordering over them: *which prompts are hard for this model*")
        w("collapses into a question about its rare failures.")
        w("")
        w("| Category | Model | n | % at exactly P-hat = 0 | median | p90 | distinct |")
        w("|---|---|---|---|---|---|---|")
        for r in D["floor_effects"]:
            w(f"| {r['category']} | {MODEL_LABELS[r['model']]} | {r['n_prompts']} | "
              f"**{r['pct_exactly_zero']:.0f}%** | {f(r['median_p_hat'], 2)} | "
              f"{f(r['p90_p_hat'], 2)} | {r['distinct_p_hat']} |")
        w("")
        w("## Rescue attempts — could the low tau be an artifact?")
        w("")
        w("Each row removes a candidate cause. If the verdict were an artifact of that")
        w(f"cause, tau_corr would climb past {GO_TAU_CORR} here.")
        w("")
        w("| Variant | n | tau_cross | tau_corr | max tau_cross | clears GO? |")
        w("|---|---|---|---|---|---|")
        for r in D["rescue_attempts"]:
            if "tau_corr" not in r:
                w(f"| {r['variant']} | {r['n_prompts']} | — | — | — | {r['note']} |")
                continue
            w(f"| {r['variant']} | {r['n_prompts']} | {f(r['tau_cross'], 3)} | "
              f"**{f(r['tau_corr'], 3)}** | {f(r['max_reachable_tau_cross'], 3)} | "
              f"{'**YES**' if r['clears_go'] else 'no'} |")
        w("")
        w("The `both models P-hat > x` rows condition on the OUTCOME, which selects")
        w("for agreement and biases tau **upward**. Treat them as a generous upper")
        w("bound on what a floor-free prompt set might give, not as an estimate.")
        w("")
        w("## Coarse vs fine agreement — why the result feels counter-intuitive")
        w("")
        cv = D["coarse_vs_fine"]
        w("The intuition *surely two models agree about what is hard* is about")
        w("**category-level** difficulty, and it is correct. §7 tests **within-")
        w("category** ordering, which is a different and much harder claim — and the")
        w("only one the paper can use, since between-category agreement is trivially")
        w("true (§2.1).")
        w("")
        w(f"tau_b between the two models' orderings of the {len(cv['category_means'])} "
          f"category means: **{f(cv['tau_b_between_category_orderings'], 3)}**")
        w("")
        w("| Category | mean P-hat A | mean P-hat B |")
        w("|---|---|---|")
        for c in cv["category_means"]:
            w(f"| {c['category']} | {f(c['mean_p_hat_A'], 3)} | "
              f"{f(c['mean_p_hat_B'], 3)} |")
        w("")
    return "\n".join(L)


# ── main ──────────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(description="Phase 0.5 / 0.5b analysis (spec §6-§7)")
    ap.add_argument("--dataset", choices=sorted(DATASETS), default="phase05",
                    help="which dataset profile to analyse. phase05 = the V3 pilot "
                         "(§4); phase05b = the TruthfulQA replication (§11). The "
                         "estimator and the §7 thresholds are identical for both.")
    ap.add_argument("--bootstrap", type=int, default=BOOTSTRAP_ITERS,
                    help=f"nested bootstrap iterations (§6.6 specifies "
                         f"{BOOTSTRAP_ITERS}; lower only for a preview)")
    ap.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    ap.add_argument("--ignore-failure-gate", action="store_true",
                    help="compute the §7 verdict even when the §5.1 2%% judge-failure "
                         "gate is tripped. Output is stamped provisional and is NOT "
                         "the pre-registered verdict.")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="defaults to results/<dataset>/analysis")
    args = ap.parse_args()

    # Must happen before any path or category constant is read.
    configure(args.dataset)
    if args.out_dir is None:
        args.out_dir = OUT_DIR
    print(f"dataset: {args.dataset}   manifest: {rel(MANIFEST_PATH)}   "
          f"spec: {SPEC_REF}")

    if args.bootstrap != BOOTSTRAP_ITERS:
        print(f"NOTE: bootstrap iterations {args.bootstrap} != the pre-registered "
              f"{BOOTSTRAP_ITERS}. Preview only.\n")

    prompts = load_prompt_table()
    loaded = load_judged(prompts)
    recs = loaded["records"]

    if set(loaded["models"]) != {MODEL_A, MODEL_B}:
        sys.exit(f"models in judgments {loaded['models']} != the §3 pair "
                 f"{[MODEL_A, MODEL_B]}. Fix MODEL_A/MODEL_B or the input, do not "
                 "let the A/B assignment drift.")

    per_pair = build_per_pair(prompts, recs)

    # ── §5.1 integrity ──
    keff_vals = [v["k_eff"] for v in per_pair.values()]
    n_rows = loaded["n_judgment_rows"]
    n_completions = loaded["n_completion_rows"]

    # §5.1's gate is about how much data was LOST, so the rate that gates it counts
    # completions that ended up with no label at all — NOT failed rows.
    #
    # This distinction is load-bearing because run_phase05_judging.py is append-only:
    # --retry-failed leaves every stale failure row in the file next to the new
    # success. failed_rows / total_rows therefore never falls back below 2% no matter
    # how completely the run is recovered (9,213 / 37,373 = 24.7% after a full
    # retry), which would wedge the gate permanently shut. The judging script's own
    # end-of-run summary has exactly this defect.
    #
    # The gross call-failure rate is still reported, because a high value means the
    # API was unreliable during the run even if every sample was eventually labelled.
    n_unrecovered = n_completions - loaded["n_labelled_keys"]
    unrecovered_rate = n_unrecovered / n_completions if n_completions else float("nan")
    gross_rate = loaded["n_failed_rows"] / n_rows if n_rows else float("nan")

    err = loaded["error_counter"]

    integrity = {
        "n_completion_rows": n_completions,
        "n_judgment_rows": n_rows,
        "n_labelled": loaded["n_labelled_keys"],
        "n_failed_rows": loaded["n_failed_rows"],
        "n_unrecovered_completions": n_unrecovered,
        "unrecovered_rate": unrecovered_rate,
        "gross_call_failure_rate": gross_rate,
        "n_duplicate_successes_dropped": loaded["n_duplicate_successes"],
        "n_orphan_judgments": loaded["n_orphan_judgments"],
        "n_pairs_expected": len(per_pair),
        "n_pairs_keff_zero": sum(1 for v in keff_vals if v == 0),
        "n_pairs_below_keff": sum(1 for v in keff_vals if v < K_EFF_MIN),
        "keff_histogram": {str(k): v for k, v in sorted(Counter(keff_vals).items())},
        "gate_tripped": bool(np.isfinite(unrecovered_rate)
                             and unrecovered_rate > FAILURE_RATE_ABORT),
        "error_summary": err.most_common(5),
        "label_distribution": dict(Counter(
            lab for rec in recs.values() for lab in rec["label"])),
    }
    if max(keff_vals) > K_SAMPLES:
        sys.exit(f"a (uid, model) pair has k_eff = {max(keff_vals)} > k = {K_SAMPLES}. "
                 "Duplicate successful judgments would reweight that prompt; "
                 "deduplication in load_judged should have prevented this.")

    if integrity["gate_tripped"]:
        print("=" * 78)
        print("§5.1 INFRASTRUCTURE FAILURE")
        print(f"  {n_unrecovered:,} of {n_completions:,} completions carry no label "
              f"({unrecovered_rate*100:.2f}% > {FAILURE_RATE_ABORT*100:.0f}% threshold)")
        print(f"  gross judge call-failure rate: {gross_rate*100:.2f}% "
              f"({loaded['n_failed_rows']:,} of {n_rows:,} rows)")
        print(f"  {integrity['n_pairs_keff_zero']:,} of {len(per_pair):,} "
              f"(uid, model) pairs have k_eff = 0")
        for msg, n in integrity["error_summary"]:
            print(f"  {n:,} x {msg}")
        print()
        print("  §5.1: this is not data. Recover with")
        print("    python3 scripts/run_phase05_judging.py --retry-failed")
        print("  then re-run this script.")
        if args.ignore_failure_gate:
            print()
            print("  --ignore-failure-gate: computing anyway. Every number below is")
            print("  PROVISIONAL and is NOT the pre-registered result. The missing")
            print("  judgments are not missing at random.")
        print("=" * 78)
        print()

    # ── panels ──
    primary_uids = sorted(u for u, p in prompts.items() if p["in_primary"])
    judgebound_uids = sorted(u for u, p in prompts.items() if p["in_judgebound"])
    secondary_uids = sorted(u for u, p in prompts.items() if p["in_secondary"])

    # Sanity: the flags and the §4.1/§4.2 category lists must agree. A drifted
    # manifest would silently move the decision surface.
    #
    # `primary_categories: None` (0.5b) means the strata are the source benchmark's own
    # and are not restated here, so there is no list to compare against. The manifest is
    # still guarded, by prompt count rather than by category names — that is what
    # catches the failure this check exists for, a manifest swapped underneath the
    # analysis. Only the count check is skipped when a profile declares its categories.
    if EXPECTED_N_PROMPTS is not None and len(prompts) != EXPECTED_N_PROMPTS:
        sys.exit(f"manifest has {len(prompts)} prompts, expected "
                 f"{EXPECTED_N_PROMPTS} for dataset {DATASET!r}. The manifest is not "
                 "the frozen one this analysis is written against.")
    for uids, cats, name in ((primary_uids, PRIMARY_CATEGORIES, "primary"),
                             (judgebound_uids, JUDGEBOUND_CATEGORIES, "judge-bound")):
        if cats is None:
            continue
        got = sorted({prompts[u]["category"] for u in uids})
        if got != sorted(cats):
            sys.exit(f"{name} set categories {got} != spec {sorted(cats)}. The "
                     "manifest is not the frozen one this analysis is written against.")

    R = {
        "spec": SPEC_REF,
        "dataset": DATASET,
        "inputs": {
            "manifest": rel(MANIFEST_PATH),
            "completions": rel(COMPLETIONS_PATH),
            "judgments": rel(JUDGMENTS_PATH),
            "decoding_config": (json.loads(DECODING_CONFIG_PATH.read_text())
                                if DECODING_CONFIG_PATH.exists() else None),
            "model_A": MODEL_A, "model_B": MODEL_B,
            "bootstrap_iters": args.bootstrap, "bootstrap_seed": args.seed,
        },
        "integrity": integrity,
    }

    panels = {}
    for key, uids in (("primary", primary_uids), ("judgebound", judgebound_uids)):
        panel, sel = make_panel(key, uids, prompts, per_pair)
        panels[key] = panel
        if panel is None:
            R[key] = {"error": "fewer than 2 prompts survive the §5.1 and §6.7 "
                               "filters", "selection": sel}
            continue
        print(f"[{key}] {len(panel)} prompts, computing point estimates ...")
        point = panel.point_estimates()
        print(f"[{key}] nested bootstrap, {args.bootstrap} iterations ...")
        boot = panel.bootstrap(args.bootstrap, args.seed)

        lb = []
        for label, weight in (("label 2 only (PRE-REGISTERED PRIMARY)", 0.0),
                              ("partial = 0.5 hallucination", 0.5),
                              ("partial = full hallucination", 1.0)):
            e = panel.point_estimates(partial_weight=weight)
            lb.append({"definition": label, "partial_weight": weight,
                       "tau_cross": e["tau_cross"], "tau_selfA": e["tau_selfA"],
                       "tau_selfB": e["tau_selfB"], "tau_corr": e["tau_corr"]})

        R[key] = {"selection": {k: v for k, v in sel.items() if k != "dropped_keff"},
                  "n_dropped_keff": len(sel["dropped_keff"]),
                  "point": point, "bootstrap": boot, "label_boundary": lb}
        R[key]["selection"]["degenerate_report"] = sel["degenerate_report"]

    # ── §6.2b Δ_artifact ──
    if panels["primary"] is not None and panels["judgebound"] is not None:
        tp = R["primary"]["point"]["tau_corr"]
        tj = R["judgebound"]["point"]["tau_corr"]
        R["delta_artifact"] = {
            "tau_corr_primary": tp, "tau_corr_judgebound": tj,
            "value": (tj - tp) if (np.isfinite(tp) and np.isfinite(tj)) else None,
            "note": "Excluded from the §7 decision rule. Δ > 0 is the expected "
                    "direction and is the measurement of interest (§4.2, §6.2b).",
        }
        if R["delta_artifact"]["value"] is None:
            R["delta_artifact"]["error"] = "a tau_corr is undefined"
    else:
        R["delta_artifact"] = {"value": None,
                               "error": "one of the two panels is not computable"}

    # ── §6.3, §6.4, §6.5 ──
    print("[secondary] pooled vs blocked contrast ...")
    R["secondary"] = secondary_contrast(prompts, per_pair, secondary_uids,
                                        args.bootstrap, args.seed)

    rate_uids, _ = keff_filter(sorted(prompts), per_pair)
    R["marginal_rates"] = marginal_rates(prompts, per_pair, rate_uids)

    if panels["primary"] is not None:
        print("[confounds] §6.5.1-3 ...")
        R["confounds"] = confound_checks(panels["primary"])
        print("[truncation] §6.5.4 label-neutrality ...")
        R["truncation"] = truncation_checks(prompts, recs, per_pair,
                                            panels["primary"].uids)
        print("[post-hoc] tie ceiling, floor effects, rescue attempts ...")
        R["posthoc_diagnostics"] = posthoc_ceiling_and_floor(
            panels["primary"], prompts, per_pair)

    # ── §7 ──
    if panels["primary"] is None:
        R["verdict"] = {"verdict": "NOT COMPUTABLE",
                        "reason": "the primary panel is empty after the §5.1 and "
                                  "§6.7 filters",
                        "action": "Fix the judging run, then re-run."}
    elif integrity["gate_tripped"] and not args.ignore_failure_gate:
        R["verdict"] = {
            "verdict": "WITHHELD — §5.1 infrastructure failure",
            "reason": (f"{integrity['n_unrecovered_completions']:,} of "
                       f"{integrity['n_completion_rows']:,} completions carry no label "
                       f"({unrecovered_rate*100:.2f}%), exceeding the 2% threshold; "
                       f"§5.1 says such a run is re-run, not analysed"),
            "action": ("Run `python3 scripts/run_phase05_judging.py --retry-failed` "
                       "to recover the unlabelled completions, then re-run this "
                       "script. `--ignore-failure-gate` previews the number but the "
                       "result is not pre-registered."),
        }
    else:
        R["verdict"] = verdict(R["primary"]["point"], R["primary"]["bootstrap"])
        if integrity["gate_tripped"]:
            R["verdict"]["provisional"] = True

    # ── write ──
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(sorted(per_pair.values(),
                        key=lambda r: (r["category"], r["uid"], r["model"]))) \
        .to_csv(out / "per_prompt.csv", index=False)
    pd.DataFrame(R["marginal_rates"]).to_csv(out / "category_rates.csv", index=False)
    pd.DataFrame([v for v in per_pair.values() if v["k_eff"] < K_EFF_MIN]) \
        .to_csv(out / "keff_exclusions.csv", index=False)

    report = render_report(R)
    (out / "report.md").write_text(report)
    results_name = f"{DATASET}_results.json"
    with open(out / results_name, "w") as fh:
        json.dump(R, fh, indent=2, sort_keys=True, default=str)

    print()
    print(report)
    print()
    print(f"wrote -> {rel(out)}/"
          "{report.md, " + results_name + ", per_prompt.csv, category_rates.csv, "
          "keff_exclusions.csv}")


if __name__ == "__main__":
    main()
