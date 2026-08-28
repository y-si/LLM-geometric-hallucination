"""Does prompt caching actually fire on OUR judge system prompt? (~$0.01, ~10 seconds)

WHY EMPIRICALLY RATHER THAN FROM THE DOCS. Judging Phase 0.5b costs ~$125, and the
judge system prompt is **60% of the input bill** -- 1,270 tokens re-sent on all 32,680
calls, $41.50 of it. Caching drops a cache READ to 0.1x, so if it fires this saves ~$37.

Whether it fires depends on the model's minimum cacheable prefix, which is a number
this repo has recorded as 4,096 tokens (see run_phase05_judging.py) without ever
testing it. Claude models have used 1,024 and 2,048 minimums depending on tier. If the
real minimum is 1,024, the v2 rubric already qualifies at 1,270 tokens and caching is
free money -- no padding, no spec amendment, no change to what the judge is asked.

The docs would answer "what is the minimum". This answers the question that actually
matters: "does caching fire on the exact prompt we are going to send." Those differ
whenever the minimum is stated per-tier, or the prompt is near the boundary.

HOW IT READS OUT. Two identical calls. The API reports, in `usage`:
    cache_creation_input_tokens  > 0 on call 1  -> the prefix WAS cacheable, cache written
    cache_read_input_tokens      > 0 on call 2  -> the cache was HIT
Both zero means the prompt is under the minimum and caching is unavailable. There is no
error and no warning in that case -- a cache_control marker on a too-short prompt is
silently ignored, which is exactly why this needs testing rather than assuming.

This script does NOT write to results/, does not touch the running generation, and does
not judge any real completion. It sends a throwaway question twice.

Usage:
    python3 scripts/check_prompt_caching.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.models.judge_client import (  # noqa: E402
    JUDGE_RUBRIC_VERSION, JUDGE_SYSTEM_PROMPT)
from src.utils.env import load_env_file  # noqa: E402

JUDGE_MODEL = "claude-haiku-4-5"

# Costs of the Phase 0.5b judging run, from measured token volumes calibrated against
# the real Phase 0.5 Anthropic bill (~$80 actual vs $75 modelled).
SYS_TOKENS_TOTAL = 41_503_600      # 1,270 tok x 32,680 calls
RATE_IN = 1.0                      # $/M input
CACHE_READ_MULTIPLIER = 0.1
CACHE_WRITE_MULTIPLIER = 1.25


def main():
    load_env_file(required=["ANTHROPIC_API_KEY"])
    from anthropic import Anthropic

    client = Anthropic(timeout=60)

    print(f"judge model : {JUDGE_MODEL}")
    print(f"rubric      : {JUDGE_RUBRIC_VERSION}")
    print(f"system chars: {len(JUDGE_SYSTEM_PROMPT):,}  (~{len(JUDGE_SYSTEM_PROMPT)//4:,} tokens)")
    print()

    def call(n):
        r = client.messages.create(
            model=JUDGE_MODEL,
            # The marker goes on the SYSTEM block, as a list with cache_control. This is
            # the only structural change judging would need.
            system=[{
                "type": "text",
                "text": JUDGE_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": "Reply with the single word: ok"}],
            max_tokens=8,
            temperature=0.0,
        )
        u = r.usage
        created = getattr(u, "cache_creation_input_tokens", None) or 0
        read = getattr(u, "cache_read_input_tokens", None) or 0
        print(f"  call {n}:  input={u.input_tokens:6,}   "
              f"cache_created={created:6,}   cache_read={read:6,}")
        return created, read

    print("Two identical calls (the second should HIT the cache the first wrote):")
    created1, read1 = call(1)
    created2, read2 = call(2)
    print()

    cacheable = (created1 > 0) or (read2 > 0)
    print("=" * 74)
    if cacheable:
        cached_tokens = max(created1, read2)
        full = SYS_TOKENS_TOTAL / 1e6 * RATE_IN
        # One cache write per ~5-minute TTL window, then reads. Over a ~3.5 h run the
        # write cost is negligible; the honest bound is "reads for essentially all calls".
        cached = SYS_TOKENS_TOTAL / 1e6 * RATE_IN * CACHE_READ_MULTIPLIER
        print(f"CACHING WORKS — {cached_tokens:,} tokens cached on the system prompt.")
        print()
        print(f"  judge system prompt over the full 0.5b run:")
        print(f"    uncached  ${full:6.2f}")
        print(f"    cached    ${cached:6.2f}   (0.1x read)")
        print(f"    SAVING   ~${full - cached:6.2f}  on a ~$125 judging bill "
              f"({(full - cached) / 125:.0%})")
        print()
        print("  ACTION: add the cache_control marker to the system block in")
        print("  src/models/judge_client.py (anthropic branch). This does NOT change")
        print("  the rubric text, so it needs no §10 amendment — the judge is asked")
        print("  exactly the same question, it is only billed differently.")
        print("  Also: order judging so calls sharing a prefix run close together, and")
        print("  drop the 'Do NOT add prompt caching' comment in run_phase05_judging.py.")
    else:
        print("CACHING DOES NOT FIRE — the system prompt is under the minimum cacheable")
        print("prefix for this model. Note there was no error: a cache_control marker on")
        print("a too-short prompt is silently ignored, which is why this had to be tested.")
        print()
        print(f"  Leave it alone. The only way to reach the minimum is to pad the rubric,")
        print(f"  and padding a pre-registered rubric to cross a billing threshold is not")
        print(f"  something to put in a methods section. Judging stays ~$125.")
        print()
        print("  The existing comment in run_phase05_judging.py is correct; this run")
        print("  confirmed it empirically rather than by assumption.")
    print("=" * 74)


if __name__ == "__main__":
    main()
