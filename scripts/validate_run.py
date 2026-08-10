#!/usr/bin/env python3
"""Data quality gate. Run this on a results directory BEFORE any analysis.

Exists because the v1 censorship run produced a published conclusion that was an
artefact of the harness rather than of the models. Three defects were present in
the data and none were visible in the summary tables:

  1. max_tokens=400 truncated 24-28 of 30 free-text answers for most models, so
     length-based metrics measured the token ceiling. The headline ratio flipped
     sign when truncated rows were excluded.
  2. Reasoning models received a different (terse) system prompt than the others,
     so cross-model length comparisons measured our prompt, not the models.
  3. Kimi K2.6 emitted chain-of-thought into the content field in 17 of 30 cases,
     so its word counts measured deliberation rather than answering.

Each check below corresponds to one of those. Exit code is non-zero if any
blocking check fails.

Usage:
    python3 scripts/validate_run.py data/results/<run-dir> [--strict]
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Fraction of truncated responses above which length metrics are unusable.
TRUNCATION_WARN = 0.05
TRUNCATION_FAIL = 0.20
LEAK_WARN = 0.02
LEAK_FAIL = 0.10


def load(run_dir):
    by_model = {}
    for f in sorted(run_dir.glob("*.jsonl")):
        rows = []
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        if rows:
            by_model[rows[0].get("model") or f.stem] = rows
    return by_model


def pct(n, d):
    return (n / d * 100) if d else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--strict", action="store_true",
                    help="Treat warnings as failures")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    by_model = load(run_dir)
    if not by_model:
        print(f"ERROR: no .jsonl results in {run_dir}", file=sys.stderr)
        sys.exit(2)

    failures, warnings = [], []
    legacy = False

    print(f"Run: {run_dir.name}")
    print(f"Models: {len(by_model)}   Rows: {sum(len(v) for v in by_model.values())}\n")

    # ---- Check 1: completeness -------------------------------------------
    counts = {m: len(r) for m, r in by_model.items()}
    if len(set(counts.values())) > 1:
        failures.append(f"Models have different row counts: {counts}")

    # ---- Check 2: truncation ---------------------------------------------
    print("=" * 74)
    print("CHECK 1  Truncation  (finish_reason == 'length')")
    print("=" * 74)
    print(f"{'Model':<46}{'truncated':>12}{'rate':>10}")
    print("-" * 74)
    for m, rows in sorted(by_model.items()):
        if "truncated" not in rows[0]:
            legacy = True
            trunc = sum(1 for r in rows
                        if (r.get("response") or "").rstrip()[-1:] not in '.!?:)"…')
            label = "~" + str(trunc)
        else:
            trunc = sum(1 for r in rows if r.get("truncated"))
            label = str(trunc)
        rate = pct(trunc, len(rows))
        mark = "FAIL" if rate >= TRUNCATION_FAIL * 100 else ("warn" if rate >= TRUNCATION_WARN * 100 else "ok")
        print(f"{m[:46]:<46}{label:>12}{rate:>9.1f}% {mark}")
        if rate >= TRUNCATION_FAIL * 100:
            failures.append(f"{m}: {rate:.0f}% truncated - length metrics invalid")
        elif rate >= TRUNCATION_WARN * 100:
            warnings.append(f"{m}: {rate:.0f}% truncated - exclude those rows from length metrics")
    if legacy:
        print("\n  NOTE: no 'truncated' field; estimated from sentence endings.")
        print("        Re-run with the current runner to get finish_reason.")

    # ---- Check 3: reasoning leakage --------------------------------------
    print("\n" + "=" * 74)
    print("CHECK 2  Reasoning leaked into answer")
    print("=" * 74)
    print(f"{'Model':<46}{'leaked':>12}{'rate':>10}")
    print("-" * 74)
    MARKERS = ("the user is asking", "the user wants", "användaren ber",
               "användaren frågar", "jag måste överväga", "jag behöver ge",
               "i need to", "we need to", "</think>", "<|close|>", "<|channel|>")
    for m, rows in sorted(by_model.items()):
        if "reasoning_leak" in rows[0]:
            leaked = sum(1 for r in rows if r.get("reasoning_leak"))
        else:
            leaked = sum(1 for r in rows
                         if any(k in (r.get("response") or "").lstrip()[:300].lower()
                                for k in MARKERS))
        rate = pct(leaked, len(rows))
        mark = "FAIL" if rate >= LEAK_FAIL * 100 else ("warn" if rate >= LEAK_WARN * 100 else "ok")
        print(f"{m[:46]:<46}{leaked:>12}{rate:>9.1f}% {mark}")
        if rate >= LEAK_FAIL * 100:
            failures.append(f"{m}: {rate:.0f}% of answers contain chain-of-thought")
        elif rate >= LEAK_WARN * 100:
            warnings.append(f"{m}: {rate:.0f}% possible reasoning leakage")

    # ---- Check 4: uniform system prompt ----------------------------------
    print("\n" + "=" * 74)
    print("CHECK 3  System prompt identical across models")
    print("=" * 74)
    prompts = defaultdict(list)
    for m, rows in by_model.items():
        prompts[rows[0].get("system_prompt", "<not recorded>")].append(m)
    if len(prompts) == 1 and "<not recorded>" not in prompts:
        print("  ok - one prompt for all models")
    elif "<not recorded>" in prompts:
        legacy = True
        print("  UNKNOWN - system_prompt not recorded in this run.")
        warnings.append("system_prompt not recorded; cross-model length comparison unverifiable")
    else:
        print(f"  FAIL - {len(prompts)} different prompts:")
        for p, ms in prompts.items():
            print(f"    {len(ms)} models: {p[:70]}...")
        failures.append(
            f"{len(prompts)} different system prompts - cross-model length "
            "comparisons are confounded and must not be reported")

    # ---- Check 5: errors and empties -------------------------------------
    print("\n" + "=" * 74)
    print("CHECK 4  Errors and empty answers")
    print("=" * 74)
    any_bad = False
    for m, rows in sorted(by_model.items()):
        errs = sum(1 for r in rows if r.get("error"))
        empty = sum(1 for r in rows if not (r.get("response") or "").strip())
        if errs or empty:
            any_bad = True
            print(f"  {m[:46]:<46} errors={errs} empty={empty}")
            failures.append(f"{m}: {errs} errors, {empty} empty responses")
    if not any_bad:
        print("  ok - no errors, no empty answers")

    # ---- Verdict ----------------------------------------------------------
    print("\n" + "=" * 74)
    if failures:
        print(f"BLOCKED - {len(failures)} problem(s) that invalidate analysis")
        for f in failures:
            print(f"  - {f}")
    if warnings:
        print(f"\n{len(warnings)} warning(s)")
        for w in warnings:
            print(f"  - {w}")
    if not failures and not warnings:
        print("PASS - data is fit for analysis")
    print("=" * 74)

    if failures or (args.strict and warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()
