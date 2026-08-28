"""Probe TruthfulQA hallucination rates before committing to a full Phase 0.5b run.

WHY THIS EXISTS. The Phase 0.5 pilot returned NO-GO (tau_corr = 0.310 against a 0.50
threshold) and the diagnosis was a FLOOR EFFECT, not model disagreement: Llama-3.3-70B
scored exactly P-hat = 0 on 86% of `nonexistent` prompts and 49% of
`borderline_plausible_fake`. You cannot measure whether two models order prompts by
difficulty the same way when one of them almost never fails. See CONTEXT.md ->
"Floor effects and the tau_b tie ceiling".

TruthfulQA is the natural fix: adversarial by construction, real sourced ground truth
("Best answer: X / Also acceptable: Y, Z" — so it satisfies the §4.0 verifiability
criterion, unlike this project's own `factual` category), public, and 817 prompts across
38 categories.

BUT the existing TruthfulQA rate data in results/truthfulqa/ is for **Mixtral-8x7B and
Llama-4-Maverick** — neither of which is in the current panel. Mixtral hallucinated on
17% of TruthfulQA overall (Misconceptions 0.06 ... Law 0.31), which is exactly the
intermediate zone needed. Llama-3.3-70B is a stronger, later model and may be far more
truthful, which would put us straight back in the floor regime with $70 spent.

    THE DECISION THIS PROBE MAKES:
      Llama hallucination rate roughly 0.10 - 0.60, with within-category spread
        -> commit to the full run
      under ~0.05
        -> TruthfulQA is saturated for this panel too; harder prompts needed
      no within-category variance even at a workable mean rate
        -> the floor problem has moved, not gone

Cost: 40 prompts x k=5 x 2 models = 400 completions plus 400 judge calls. Roughly
$0.10 generation + $0.60 judging, a few minutes. Compare with ~$70 for the full run.

k=5 is deliberately small. This probe estimates a RATE and looks for SPREAD; it is not
trying to estimate per-prompt P-hat precisely (the full run uses k=20 for that). With
k=5, P-hat takes values in {0, .2, .4, .6, .8, 1}, which is enough to distinguish "every
prompt pinned at zero" from "prompts spread across the range" — the only question that
matters here.

Reuses the same clients, decoding config and failure contract as the real pipeline, so
the numbers are comparable to the Phase 0.5 run rather than merely indicative.

Usage:
    python3 scripts/probe_truthfulqa_rates.py                 # 40 prompts, k=5
    python3 scripts/probe_truthfulqa_rates.py --n 60 --k 5    # wider
    python3 scripts/probe_truthfulqa_rates.py --no-judge      # generation only, free-ish

Output:
    results/phase05b_probe/probe.jsonl     raw completions + labels
    results/phase05b_probe/probe.md        the verdict
"""

import argparse
import json
import math
import random
import sys
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.multi_model_client import get_model_client  # noqa: E402
from src.models.judge_client import JudgeClient  # noqa: E402
from src.utils.env import load_env_file  # noqa: E402

TRUTHFULQA_PATH = BASE_DIR / "data" / "prompts" / "truthfulqa.jsonl"
OUT_DIR = BASE_DIR / "results" / "phase05b_probe"

# §3 — same panel as Phase 0.5, so the probe is comparable to the pilot.
MODELS = ["llama-3.3-70b-turbo", "gpt-oss-120b"]
MODEL_A, MODEL_B = MODELS

# §3 decoding config, held identical to the pilot. P-hat is defined relative to it.
TEMPERATURE = 0.7
TOP_P = 1.0
MAX_TOKENS = 2048

# §5 — third-vendor judge, no family shared with either evaluated model.
JUDGE_MODEL = "claude-haiku-4-5"
JUDGE_PROVIDER = "anthropic"
JUDGE_TEMPERATURE = 0.0

LABEL_HALLUCINATION = 2
MAX_WORKERS = 8
SEED = 20260827

# Decision thresholds for this probe. Not pre-registered — this is a feasibility
# screen for a future run, not a test of any claim.
RATE_FLOOR = 0.05      # below this, the panel is saturated on TruthfulQA
RATE_USEFUL_LO = 0.10  # comfortable lower edge of the measurable zone
RATE_USEFUL_HI = 0.60  # above this we would be approaching a ceiling instead

# Between-prompt spread test. Counting DISTINCT P-hat values does not work and the
# first version of this script got it wrong: at k=5, a constant true rate of 0.25
# produces P-hat in {0, .2, .4, .6} from binomial noise alone, so a distinct-value
# count cannot tell real between-prompt variance from sampling noise. (Same class of
# error as confusing tau_cross with tau_self.)
#
# The correct test compares observed variance against the variance binomial noise
# alone would produce if every prompt shared the mean rate:
#
#     V_noise = p_bar * (1 - p_bar) / k          (all prompts identical)
#     excess  = Var(P-hat across prompts) / V_noise
#
# excess ~ 1.0 means no detectable between-prompt difficulty variance — nothing to
# rank, which is the Phase 0.5 failure. Meaningfully above 1 means real spread.
# At k=5 this test has low power, so the bar is set modestly and a borderline result
# means "probe wider", not "commit".
MIN_DISPERSION_RATIO = 1.5   # chi2/df; 1.0 = prompts interchangeable
DISPERSION_ALPHA = 0.05      # p-value for rejecting "all prompts equally hard"

write_lock = threading.Lock()


def stratified_sample(rows, n, seed):
    """Round-robin across TruthfulQA categories, deterministically.

    NOT rows[:n]. The Phase 0.5 generation and judging scripts both shipped a bug
    where --limit took a prefix of a category-sorted file and silently sampled a
    single category; that made a model-specific truncation problem look symmetric and
    produced a wrong reading. Same fix here.
    """
    buckets = defaultdict(list)
    for r in rows:
        buckets[r.get("category", "?")].append(r)
    rng = random.Random(seed)
    for k in buckets:
        buckets[k].sort(key=lambda r: r["id"])
        rng.shuffle(buckets[k])
    keys = sorted(buckets)
    picked, depth = [], 0
    longest = max(len(v) for v in buckets.values())
    while len(picked) < n and depth < longest:
        for k in keys:
            if depth < len(buckets[k]) and len(picked) < n:
                picked.append(buckets[k][depth])
        depth += 1
    return picked


def generate_one(client, row, model_key, idx):
    try:
        res = client.generate_with_meta(
            row["question"], max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE, top_p=TOP_P)
        return {"id": row["id"], "category": row.get("category"),
                "question": row["question"], "ground_truth": row.get("ground_truth", ""),
                "model": model_key, "sample_idx": idx,
                "completion": res["text"], "finish_reason": res.get("finish_reason"),
                "output_tokens": res.get("output_tokens")}
    except Exception as e:
        return {"id": row["id"], "category": row.get("category"),
                "question": row["question"], "ground_truth": row.get("ground_truth", ""),
                "model": model_key, "sample_idx": idx,
                "completion": None, "gen_error": str(e)[:200]}


def judge_one(judge, row):
    """§5.1 failure contract: a failed judge call gets NO label, ever."""
    if not row.get("completion"):
        return {**row, "judge_failed": True, "error": "no completion to judge"}
    try:
        res = judge.judge(question=row["question"], answer=row["completion"],
                          ground_truth=row["ground_truth"])
        if res.get("failed"):
            # judge_client.py returns {"label": 3, "failed": True} on failure. The
            # label is garbage and the flag is the only guard — never read the label
            # without checking the flag, or the March 2026 contamination returns.
            return {**row, "judge_failed": True,
                    "error": str(res.get("error", "judge reported failure"))[:200]}
        return {**row, "label": int(res["label"]),
                "confidence": res.get("confidence")}
    except Exception as e:
        return {**row, "judge_failed": True, "error": str(e)[:200]}


def normal_sf(z):
    """P(Z > z) for a standard normal, via erfc."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def chi2_sf(x, df):
    """P(chi-square_df > x), Wilson-Hilferty approximation (accurate for df >= 30)."""
    if df <= 0 or x <= 0:
        return 1.0
    if df == 1:
        return math.erfc(math.sqrt(x / 2.0))
    t = (x / df) ** (1.0 / 3.0)
    mean = 1.0 - 2.0 / (9.0 * df)
    sd = math.sqrt(2.0 / (9.0 * df))
    return normal_sf((t - mean) / sd)


def dispersion_test(counts, k):
    """Do prompts differ in true difficulty, or is all the spread sampling noise?

    THE QUESTION THIS ANSWERS. tau measures whether two models ORDER prompts the same
    way. That is only meaningful if the prompts actually differ in difficulty. Phase 0.5
    failed because they largely did not, for Llama: 86% of `nonexistent` prompts sat at
    exactly P-hat = 0, so there was no ordering to agree about.

    WHY A NAIVE CHECK FAILS. Counting distinct P-hat values does not work — at k=5, a
    CONSTANT true rate of 0.25 yields P-hat in {0, .2, .4, .6} from binomial noise alone.
    Comparing observed variance to the noise floor p(1-p)/k is the right idea, but the
    raw ratio has huge sampling error at small n and gave ~1.4x for both a
    genuinely-spread and a perfectly-uniform synthetic set.

    THE PROPER TEST. Standard chi-square test of homogeneity of proportions. Under the
    null that every prompt shares one true rate p_bar:

        chi2 = sum_i (x_i - k*p_bar)^2 / (k*p_bar*(1-p_bar)) ~ chi2(n-1)

    where x_i is prompt i's hallucination count out of k. Reported as the DISPERSION
    RATIO chi2/df, which is 1.0 under the null and rises with real between-prompt
    difficulty variance, plus a p-value. A ratio near 1 with a large p-value means
    "these prompts are interchangeable" — fatal for a tau study however good the mean
    rate looks.

    Returns (ratio, p_value, n_prompts, mean_rate).
    """
    counts = [c for c in counts if c is not None]
    n = len(counts)
    if n < 2 or k < 1:
        return float("nan"), float("nan"), n, float("nan")
    p_bar = sum(counts) / (n * k)
    if p_bar <= 0 or p_bar >= 1:
        # Every sample identical: no dispersion is even expressible. This is the
        # degenerate case Phase 0.5 hit, and it must not be reported as "no evidence
        # of difference" — it is the strongest possible evidence of no variance.
        return 0.0, 1.0, n, p_bar
    denom = k * p_bar * (1 - p_bar)
    chi2 = sum((c - k * p_bar) ** 2 for c in counts) / denom
    df = n - 1
    return chi2 / df, chi2_sf(chi2, df), n, p_bar


def summarise(rows, do_judge):
    L = []
    w = L.append
    w("# TruthfulQA rate probe")
    w("")
    w("Feasibility screen for a Phase 0.5b re-run on TruthfulQA. **Not pre-registered**")
    w("and not a test of any claim — it decides only whether the panel shows measurable")
    w("hallucination variance on this benchmark before ~$70 is committed.")
    w("")
    w(f"Panel: {MODEL_A} / {MODEL_B}. Decoding: T={TEMPERATURE}, top_p={TOP_P}, "
      f"max_tokens={MAX_TOKENS} (identical to Phase 0.5).")
    w("")

    gen_fail = sum(1 for r in rows if not r.get("completion"))
    w(f"Completions: {len(rows)}  (generation failures: {gen_fail})")
    if do_judge:
        jf = sum(1 for r in rows if r.get("judge_failed"))
        w(f"Judge failures (no label, never counted): {jf}")
    w("")

    if not do_judge:
        w("Ran with --no-judge, so no rates. Completion lengths only:")
        w("")
        w("| Model | n | median output tokens | truncated at cap |")
        w("|---|---|---|---|")
        for m in MODELS:
            toks = sorted(r["output_tokens"] for r in rows
                          if r["model"] == m and r.get("output_tokens"))
            tr = sum(1 for r in rows
                     if r["model"] == m and r.get("finish_reason") == "length")
            med = toks[len(toks) // 2] if toks else "n/a"
            w(f"| {m} | {len(toks)} | {med} | {tr} |")
        return "\n".join(L), None

    # per (id, model) P-hat
    per_pair = defaultdict(lambda: {"n": 0, "hall": 0})
    for r in rows:
        if r.get("judge_failed") or r.get("label") is None:
            continue
        k = (r["id"], r["model"])
        per_pair[k]["n"] += 1
        per_pair[k]["hall"] += int(r["label"] == LABEL_HALLUCINATION)

    rates, phats, counts = {}, defaultdict(list), defaultdict(list)
    k_by_model = defaultdict(list)
    for (pid, model), v in per_pair.items():
        if v["n"] == 0:
            continue
        phats[model].append(v["hall"] / v["n"])
        counts[model].append(v["hall"])
        k_by_model[model].append(v["n"])
    for m in MODELS:
        vals = phats[m]
        rates[m] = sum(vals) / len(vals) if vals else float("nan")

    w("## The number this probe exists for")
    w("")
    disp = {}
    for m in MODELS:
        ks = k_by_model[m]
        k_m = min(ks) if ks else 1
        # Restrict to pairs at full k so the chi-square has a single, valid k.
        cs = [c for c, kk in zip(counts[m], k_by_model[m]) if kk == max(ks, default=0)]
        disp[m] = dispersion_test(cs, max(ks, default=1))
    w("| Model | prompts | mean P-hat | % at exactly 0 | dispersion chi2/df | p |")
    w("|---|---|---|---|---|---|")
    for m in MODELS:
        vals = phats[m]
        zero = 100 * sum(1 for v in vals if v == 0) / len(vals) if vals else float("nan")
        ratio, pv, npr, _ = disp[m]
        w(f"| {m} | {len(vals)} | **{rates[m]:.3f}** | {zero:.0f}% | "
          f"**{ratio:.2f}** | {pv:.4g} |")
    w("")
    w("**The dispersion column matters as much as the rate.** tau asks whether two")
    w("models ORDER prompts the same way, which is only meaningful if the prompts")
    w("actually differ in difficulty. This is a chi-square test of homogeneity of")
    w("proportions: under the null that every prompt is equally hard, chi2/df = 1.0.")
    w("A ratio near 1 with a large p means the prompts are effectively interchangeable —")
    w("fatal for a tau study however healthy the mean rate looks. That is precisely what")
    w("killed Phase 0.5.")
    w("")
    w("Phase 0.5 comparison — the regime that killed the pilot:")
    w("")
    w("| | Llama mean P-hat | Llama % at exactly 0 |")
    w("|---|---|---|")
    w("| V3 `nonexistent` | 0.083 | **86%** |")
    w("| V3 `borderline_plausible_fake` | 0.213 | **49%** |")
    w(f"| TruthfulQA (this probe) | {rates[MODEL_A]:.3f} | "
      f"{100 * sum(1 for v in phats[MODEL_A] if v == 0) / max(len(phats[MODEL_A]), 1):.0f}% |")
    w("")

    # within-category spread — a workable mean rate with no spread is still unusable
    by_cat = defaultdict(lambda: defaultdict(list))
    for (pid, model), v in per_pair.items():
        if v["n"] == 0:
            continue
        cat = next((r["category"] for r in rows if r["id"] == pid), "?")
        by_cat[cat][model].append(v["hall"] / v["n"])
    w("## Within-category spread")
    w("")
    w("A workable mean rate with every prompt tied is still unusable — that is exactly")
    w("what the tie ceiling in CONTEXT.md describes. Per-category n is tiny in a probe,")
    w("so read these as orientation only; the overall excess-variance figure above is")
    w("the decision-relevant number.")
    w("")
    w("| Category | n | Llama mean / distinct | gpt-oss mean / distinct |")
    w("|---|---|---|---|")
    for cat in sorted(by_cat):
        a, b = by_cat[cat].get(MODEL_A, []), by_cat[cat].get(MODEL_B, [])
        ma = f"{sum(a)/len(a):.2f} / {len(set(a))}" if a else "-"
        mb = f"{sum(b)/len(b):.2f} / {len(set(b))}" if b else "-"
        w(f"| {cat} | {max(len(a), len(b))} | {ma} | {mb} |")
    w("")

    ra = rates[MODEL_A]
    verdict, detail = "", ""
    if ra != ra:
        verdict = "INCONCLUSIVE"
        detail = "no labelled completions for Model A — check the judge and API keys."
    elif ra < RATE_FLOOR:
        verdict = "DO NOT COMMIT"
        detail = (f"Llama hallucinates on {ra:.1%} of TruthfulQA, below the {RATE_FLOOR:.0%} "
                  "floor. TruthfulQA is saturated for this panel, so a full run would "
                  "reproduce the Phase 0.5 floor effect and the same uninterpretable "
                  "NO-GO. Options: a harder benchmark, a weaker Model A so the pair "
                  "spans a usable range, or accept that ordering is only measurable "
                  "where both models genuinely fail.")
    elif ra > RATE_USEFUL_HI:
        verdict = "CAUTION"
        detail = (f"Llama hallucinates on {ra:.1%}, above {RATE_USEFUL_HI:.0%}. Not a "
                  "floor problem but possibly a ceiling one — check the distinct-P-hat "
                  "counts above before committing.")
    else:
        ra_ratio, ra_p, _, _ = disp[MODEL_A]
        rb_ratio, rb_p, _, _ = disp[MODEL_B]
        ex_a, ex_b = ra_ratio, rb_ratio
        spread_ok = (ra_ratio == ra_ratio and rb_ratio == rb_ratio
                     and ra_ratio >= MIN_DISPERSION_RATIO
                     and rb_ratio >= MIN_DISPERSION_RATIO
                     and ra_p < DISPERSION_ALPHA and rb_p < DISPERSION_ALPHA)
        if spread_ok:
            verdict = "COMMIT"
            detail = (f"Llama hallucinates on {ra:.1%} of TruthfulQA — inside the "
                      f"{RATE_USEFUL_LO:.0%}-{RATE_USEFUL_HI:.0%} measurable zone — and "
                      f"prompt-difficulty dispersion is {ex_a:.2f} / {ex_b:.2f} (chi2/df, "
                      f"p={ra_p:.3g} / {rb_p:.3g}), so real difficulty differences exist "
                      "to rank. This "
                      "is the regime Phase 0.5 lacked. Proceed to the full run: 817 "
                      "prompts x k=20 x 2 models.")
        else:
            verdict = "CAUTION"
            detail = (f"Mean rate {ra:.1%} is workable, but prompt-difficulty dispersion "
                      f"is only {ex_a:.2f} / {ex_b:.2f} (chi2/df, p={ra_p:.3g} / "
                      f"{rb_p:.3g}; need >= {MIN_DISPERSION_RATIO} and p < "
                      f"{DISPERSION_ALPHA}). The prompts are close to interchangeable, so "
                      "there is little difficulty ordering to share — the Phase 0.5 "
                      "problem has moved, not gone. Re-probe wider (--n 120 --k 10) "
                      "before concluding; do not commit the full run on this.")

    w("## Verdict")
    w("")
    w(f"### {verdict}")
    w("")
    w(detail)
    w("")
    w(f"Thresholds used (not pre-registered): rate floor {RATE_FLOOR}, useful zone "
      f"{RATE_USEFUL_LO}-{RATE_USEFUL_HI}, minimum dispersion {MIN_DISPERSION_RATIO} "
      f"at p < {DISPERSION_ALPHA}.")
    return "\n".join(L), verdict


def main():
    ap = argparse.ArgumentParser(description="TruthfulQA rate probe (Phase 0.5b screen)")
    ap.add_argument("--n", type=int, default=80,
                    help="prompts to sample (80 x k=10 gives the dispersion test "
                         "usable power; 40 x k=5 does not)")
    ap.add_argument("--k", type=int, default=10, help="samples per (prompt, model)")
    ap.add_argument("--no-judge", action="store_true",
                    help="generate only; report lengths, no rates")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    load_env_file(required=("TOGETHER_API_KEY",) if args.no_judge
                  else ("TOGETHER_API_KEY", "ANTHROPIC_API_KEY"))

    rows = [json.loads(l) for l in open(TRUTHFULQA_PATH) if l.strip()]
    sample = stratified_sample(rows, args.n, args.seed)
    print(f"TruthfulQA: {len(rows)} prompts, sampled {len(sample)} across "
          f"{len({r.get('category') for r in sample})} categories")
    print(f"panel: {MODELS}   k={args.k}   "
          f"total completions: {len(sample) * args.k * len(MODELS)}")
    print()

    clients = {m: get_model_client(m) for m in MODELS}

    tasks = [(r, m, i) for r in sample for m in MODELS for i in range(args.k)]
    out = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(generate_one, clients[m], r, m, i) for r, m, i in tasks]
        for n, f in enumerate(as_completed(futs), 1):
            out.append(f.result())
            if n % 50 == 0 or n == len(futs):
                print(f"  generated {n}/{len(futs)}")

    if not args.no_judge:
        print()
        judge = JudgeClient(model_name=JUDGE_MODEL, provider=JUDGE_PROVIDER,
                            temperature=JUDGE_TEMPERATURE)
        judged = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futs = [ex.submit(judge_one, judge, r) for r in out]
            for n, f in enumerate(as_completed(futs), 1):
                judged.append(f.result())
                if n % 50 == 0 or n == len(futs):
                    print(f"  judged {n}/{len(futs)}")
        out = judged

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "probe.jsonl", "w") as f:
        for r in out:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    report, verdict = summarise(out, not args.no_judge)
    (args.out_dir / "probe.md").write_text(report)
    print()
    print(report)
    print()
    print(f"wrote -> {(args.out_dir / 'probe.md').relative_to(BASE_DIR)}, "
          f"{(args.out_dir / 'probe.jsonl').relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
