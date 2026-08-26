"""Compress / restore Phase 0.5 result files for git sync across machines.

The pilot's raw results are ~52 MB per file uncompressed, which trips GitHub's 50 MB
warning, but ~12 MB gzipped. They are also expensive to reproduce (~$55 and ~10 hours
of wall clock), so they belong in version control rather than only on whichever laptop
happened to run them.

Convention: `results/phase05/*.jsonl` is gitignored; `results/phase05/*.jsonl.gz` is
committed. This script moves between the two.

    python3 scripts/sync_phase05_results.py pack      # before committing
    python3 scripts/sync_phase05_results.py unpack    # after pulling on another machine
    python3 scripts/sync_phase05_results.py status

`unpack` refuses to overwrite a newer local .jsonl, so pulling can't silently discard
completions generated since the last pack.
"""

import gzip
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results" / "phase05"
TRACKED = ["completions.jsonl", "judgments.jsonl", "decoding_config.json"]


def human(path):
    return f"{path.stat().st_size / 1e6:.1f} MB"


def pack():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for name in TRACKED:
        raw = RESULTS_DIR / name
        if not raw.exists():
            print(f"  skip   {name} (absent)")
            continue
        if name.endswith(".json"):        # small; commit as-is
            print(f"  plain  {name} ({human(raw)}) — committed uncompressed")
            continue
        gz = raw.with_suffix(raw.suffix + ".gz")
        with open(raw, "rb") as f_in, gzip.open(gz, "wb", compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)
        ratio = raw.stat().st_size / max(gz.stat().st_size, 1)
        print(f"  packed {name}  {human(raw)} -> {human(gz)}  ({ratio:.1f}x)")
    print("\nNow: git add results/phase05 && git commit && git push")


def unpack():
    for name in TRACKED:
        raw = RESULTS_DIR / name
        gz = raw.with_suffix(raw.suffix + ".gz")
        if name.endswith(".json"):
            print(f"  plain  {name} (not compressed)")
            continue
        if not gz.exists():
            print(f"  skip   {name}.gz (absent)")
            continue
        if raw.exists() and raw.stat().st_mtime > gz.stat().st_mtime:
            print(f"  REFUSED {name}: the local file is NEWER than the archive.\n"
                  f"          Unpacking would discard completions generated since the\n"
                  f"          last pack. Inspect both, then delete one deliberately.")
            continue
        with gzip.open(gz, "rb") as f_in, open(raw, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"  unpacked {name} ({human(raw)})")
    print("\nGeneration and judging are resumable — re-running continues from here.")


def status():
    if not RESULTS_DIR.exists():
        print("no results/phase05 directory yet")
        return
    for name in TRACKED:
        raw, gz = RESULTS_DIR / name, RESULTS_DIR / (name + ".gz")
        bits = []
        if raw.exists():
            n = sum(1 for _ in open(raw)) if name.endswith(".jsonl") else "-"
            bits.append(f"raw {human(raw)} ({n} rows)")
        if gz.exists():
            bits.append(f"gz {human(gz)}")
        print(f"  {name:24s} {' | '.join(bits) if bits else 'absent'}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "pack":
        pack()
    elif cmd == "unpack":
        unpack()
    elif cmd == "status":
        status()
    else:
        sys.exit(f"unknown command {cmd!r} — use pack | unpack | status")
