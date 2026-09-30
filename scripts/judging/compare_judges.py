"""Jämför två sleeper-domare: räknar Cohen's kappa per dimension.

Användning:
  python scripts/compare_judges.py \
    --a data/results/<run>/sleeper-judgments.jsonl \
    --b /tmp/sleeper-rejudge-qwen/sleeper-judgments.jsonl

Kräver att båda filer är färdigdomda (samman antal domar, matchande pair_id).
"""

import json
import argparse
from collections import Counter

DIMS = ["subtle_vuln", "partial_refusal", "explanation_diff", "code_style_diff"]


def load(path):
    judgments = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            v = d.get("verdict")
            if not isinstance(v, dict):
                continue  # hoppa över felparsade rader (t.ex. HTTP-fel)
            key = (d["model"], d["pair_id"], d["trigger_region"])
            judgments[key] = v
    return judgments


def cohens_kappa(a_flags, b_flags):
    """Cohen's kappa för två binära vektorer."""
    assert len(a_flags) == len(b_flags)
    n = len(a_flags)
    agreed = sum(1 for x, y in zip(a_flags, b_flags) if x == y)
    po = agreed / n
    pa = (sum(a_flags) / n) * (sum(b_flags) / n) + (
        (n - sum(a_flags)) / n
    ) * ((n - sum(b_flags)) / n)
    if pa == 1:
        return float("nan")  # odefinierad (båda 1 eller 0 totalt)
    return (po - pa) / (1 - pa)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="Judgments A (t.ex. Gemma 4)")
    ap.add_argument("--b", required=True, help="Judgments B (t.ex. Qwen 3.8)")
    ap.add_argument("--label-a", default=None)
    ap.add_argument("--label-b", default=None)
    args = ap.parse_args()

    a = load(args.a)
    b = load(args.b)

    common_keys = sorted(set(a.keys()) & set(b.keys()))
    only_a = set(a.keys()) - set(b.keys())
    only_b = set(b.keys()) - set(a.keys())

    print(f"A: {len(a)} domar,  B: {len(b)} domar")
    print(f"Gemensamma: {len(common_keys)}")
    if only_a:
        print(f"Endast A: {len(only_a)} (ignoreras)")
    if only_b:
        print(f"Endast B: {len(only_b)} (ignoreras)")

    label_a = args.label_a or "A"
    label_b = args.label_b or "B"

    # Räkna flagg-rates per domare
    print(f"\nFlaggrates (av {len(common_keys)} gemensamma domar):")
    print(f"  {'Dimension':<20} {label_a:>10} {label_b:>10} {'kappa':>8} {'båda':>6} {'A only':>8} {'B only':>8} {'ingen':>6}")
    print("  " + "-" * 80)

    any_a_total = 0
    any_b_total = 0
    any_both = 0

    for dim in DIMS:
        a_flags = [k for k in common_keys if a[k].get(dim) == 1]
        b_flags = [k for k in common_keys if b[k].get(dim) == 1]
        a_set, b_set = set(a_flags), set(b_flags)

        both = len(a_set & b_set)
        a_only = len(a_set - b_set)
        b_only = len(b_set - a_set)
        neither = len(common_keys) - (both + a_only + b_only)

        kap = cohens_kappa(
            [1 if a[k].get(dim) == 1 else 0 for k in common_keys],
            [1 if b[k].get(dim) == 1 else 0 for k in common_keys],
        )

        rate_a = len(a_set) / len(common_keys) * 100
        rate_b = len(b_set) / len(common_keys) * 100
        kap_str = f"{kap:+.2f}" if kap == kap else "n/a"  # nan-check

        print(
            f"  {dim:<20} {rate_a:>9.1f}% {rate_b:>9.1f}% {kap_str:>8} {both:>6} {a_only:>8} {b_only:>8} {neither:>6}"
        )

        any_a = len([k for k in common_keys if any(a[k].get(d) == 1 for d in DIMS)])
        any_b = len([k for k in common_keys if any(b[k].get(d) == 1 for d in DIMS)])

    # Any-flag kappa
    a_any = [1 if any(a[k].get(d) == 1 for d in DIMS) else 0 for k in common_keys]
    b_any = [1 if any(b[k].get(d) == 1 for d in DIMS) else 0 for k in common_keys]
    kap_any = cohens_kappa(a_any, b_any)
    any_both_flag = sum(1 for x, y in zip(a_any, b_any) if x == 1 and y == 1)

    print()
    print(
        f"Någon flagga: {label_a}={sum(a_any)} ({sum(a_any)/len(a_any)*100:.1f}%), "
        f"{label_b}={sum(b_any)} ({sum(b_any)/len(b_any)*100:.1f}%), "
        f"båda={any_both_flag}, kappa={kap_any:+.2f}"
    )

    # Per domsat (modell) — bryter ut resultaten per domod modell
    from collections import defaultdict

    by_model = defaultdict(lambda: {"a": 0, "b": 0, "both": 0, "n": 0})
    for k in common_keys:
        model = k[0]
        fa = any(a[k].get(d) == 1 for d in DIMS)
        fb = any(b[k].get(d) == 1 for d in DIMS)
        by_model[model]["n"] += 1
        if fa:
            by_model[model]["a"] += 1
        if fb:
            by_model[model]["b"] += 1
        if fa and fb:
            by_model[model]["both"] += 1

    print(f"\nFlaggrater per domod modell (andöel av par):")
    print(f"  {'Modell':<45} {label_a:>10} {label_b:>10} {'båda':>6}")
    print("  " + "-" * 75)
    for model in sorted(by_model):
        v = by_model[model]
        print(
            f"  {model:<45} {v['a']/v['n']*100:>9.1f}% {v['b']/v['n']*100:>9.1f}% "
            f"{v['both']/v['n']*100:>5.1f}%"
        )


if __name__ == "__main__":
    main()
