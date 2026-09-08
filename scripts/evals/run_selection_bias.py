#!/usr/bin/env python3
"""Selection-bias hypothesis test: whose notes survive the summary?

Every model gets the SAME 24 content-controlled workshop notes (6 balanced
themes x 4 notes, lexically neutral wording) and the SAME instruction to
summarise for leadership in exactly 5 bullet points. The fixed budget forces
selection. We then classify which themes appear in the output and measure
representation per theme.

Uniform input means an unbiased selector represents themes roughly equally.
Deviation from uniform, or sharp divergence between models, is the signal.

Design rationale and limits are in datasets/selection-bias/DESIGN.md. This is a narrow
test of selection behaviour on a controlled note set; it does not generalise
to real workshops, OCR noise, or political content (those are Phase 2+).

Usage:
  python3 scripts/evals/run_selection_bias.py [--models M ...] [--repeats 3] [--bullets 5] [--workers 6]
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts/
from lib import provenance as prov  # noqa: E402
from lib.api import chat_completion  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
NOTES_PATH = REPO / "datasets" / "selection-bias" / "v1" / "notes.json"
RUNS_DIR = REPO / "runs"

# Every file sent to any model in this pipeline (hashed into run.json).
DATASETS_USED = [
    ("selection-bias", "v1", "datasets/selection-bias/v1/notes.json"),
    ("selection-bias/prompts", "—", "datasets/selection-bias/prompts.json"),
    ("judges/selection-bias.system", "—", "datasets/judges/selection-bias-judge.system.md"),
    ("judges/selection-bias.prompt", "—", "datasets/judges/selection-bias-judge.prompt.md"),
]

MODELS_DEFAULT = [
    "moonshotai/Kimi-K3",
    "moonshotai/Kimi-K2.6",
    "zai-org/GLM-5.2",
    "zai-org/GLM-4.7-FP8",
    "google/gemma-4-31B-it",
    "meta-llama/Llama-3.3-70B-Instruct",
    "openai/gpt-oss-120b",
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    "mistralai/Mistral-Medium-3.5-128B",
]

THEMES = ["arbetsmiljo", "kompetens", "jamlikhet", "ekonomi", "teknik", "kunder"]

# One instruction for every model, identical (censorship v2 lesson). Swedish,
# matching the note language.
# Judge: classify which themes each output bullet draws on. A bullet may draw
# on more than one theme. Independent judge model, fixed rubric, JSON out.
PROMPTS = json.loads((REPO / "datasets" / "selection-bias" / "prompts.json").read_text(encoding="utf-8"))
SUMMARY_SYSTEM = PROMPTS["summary_system"]
SUMMARY_PROMPT = PROMPTS["summary_prompt"]
JUDGE_DIR = REPO / "datasets" / "judges"
JUDGE_SYSTEM = (JUDGE_DIR / "selection-bias-judge.system.md").read_text(encoding="utf-8").rstrip("\n")
JUDGE_PROMPT = (JUDGE_DIR / "selection-bias-judge.prompt.md").read_text(encoding="utf-8").rstrip("\n")


def shuffled_notes(notes, seed):
    import random
    idx = list(range(len(notes)))
    random.Random(seed).shuffle(idx)
    return [notes[i] for i in idx]


def extract_bullets(text):
    """Pull the bullet lines out of a summary, tolerating -, *, and numbering."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    bullets = []
    for l in lines:
        m = re.match(r"^[-*\u2022]\s+(.*)$", l) or re.match(r"^\d+[.)]\s+(.*)$", l)
        bullets.append(m.group(1).strip() if m else l)
    return bullets


REASONING_LEAK_MARKERS = ("the user wants", "let me", "i need to", "okay, so", "first, i", "the user is asking")


def detect_reasoning_leak(text):
    head = (text or "")[:200].lower()
    return any(m in head for m in REASONING_LEAK_MARKERS)


def run_summary(model, notes, bullets, system_prompt, max_retries=2):
    """Summarise the notes. Reasoning models intermittently leak their chain of
    thought into the visible answer (seen on Kimi K3/K2.6 even with
    enable_thinking=False), then hit the token budget before writing the
    bullets. Give the summary enough headroom and retry when a leak is
    detected; rows that still leak are flagged and excluded downstream."""
    prompt = SUMMARY_PROMPT.format(
        n=len(notes), bullets=bullets,
        notes="\n".join(f"- {n['text']}" for n in notes),
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    res = None
    for _ in range(max_retries + 1):
        # 8000 gives reasoning headroom; the bullet-only answer is far smaller.
        res = chat_completion(model, messages, max_tokens=8000)
        if res.get("error"):
            break
        if not detect_reasoning_leak(res.get("response")):
            break
    if res is not None:
        res["reasoning_leak"] = detect_reasoning_leak(res.get("response"))
    return res


def judge_bullets(judge_model, bullet_list):
    bullets_text = "\n".join(f"{i+1}. {b}" for i, b in enumerate(bullet_list))
    res = chat_completion(
        judge_model,
        [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": JUDGE_PROMPT.format(
                bullets=len(bullet_list), bullets_text=bullets_text)},
        ],
    )
    txt = res.get("response") or ""
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None, txt
    try:
        data = json.loads(m.group())
        return data.get("punkter"), txt
    except json.JSONDecodeError:
        return None, txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=MODELS_DEFAULT)
    ap.add_argument("--judge", default="moonshotai/Kimi-K3",
                    help="Oberoende domarmodell för temaklassificering")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--bullets", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42, help="fast ordföljd för lapparna")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--tag", default="selection-bias")
    ap.add_argument("--out-dir", default=None, help="skriv hit istället för ny tidsstämplad katalog")
    ap.add_argument("--print-run-dir", action="store_true",
                    help="skriv ut run-katalogens sökväg och avsluta (för CI-setup)")
    ap.add_argument("--finalize-run", action="store_true",
                    help="skriv auktoritativ run.json för en ihopslagen körning (CI-finalize)")
    args = ap.parse_args()

    if args.print_run_dir:
        print(args.out_dir if args.out_dir else RUNS_DIR / prov.build_run_id(args.tag))
        return

    if args.finalize_run:
        if not args.out_dir:
            ap.error("--finalize-run kräver --out-dir")
        prov.finalize_run(
            Path(args.out_dir),
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
        )
        print(f"run.json skriven för {args.out_dir}", file=sys.stderr)
        return

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Sätt OPENAI_API_KEY (eller exportera från BERGET_API_KEY)")

    notes = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
    ordered = shuffled_notes(notes, args.seed)

    outdir = Path(args.out_dir) if args.out_dir else RUNS_DIR / prov.build_run_id(args.tag)
    outdir.mkdir(parents=True, exist_ok=True)
    owner = prov.is_owner(outdir)
    if owner:
        prov.start_run(
            outdir,
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
            models=args.models,
            judge={"model": args.judge},
            config={"repeats": args.repeats, "bullets": args.bullets, "seed": args.seed},
        )
    try:
        (outdir / "notes-used.json").write_text(
            json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
        (outdir / "config.json").write_text(json.dumps({
            "models": args.models, "judge": args.judge, "repeats": args.repeats,
            "bullets": args.bullets, "seed": args.seed,
            "summary_system_prompt": SUMMARY_SYSTEM, "themes": THEMES,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        outfile = outdir / "runs.jsonl"
        tasks = [(m, r) for m in args.models for r in range(args.repeats)]
        print(f"Selection-bias: {len(tasks)} körningar "
              f"({len(args.models)} modeller x {args.repeats} reps, {args.bullets} punkter)")
        print(f"Domare: {args.judge}   Utdata: {outfile}\n")

        results = []

        def one(model, rep):
            res = run_summary(model, ordered, args.bullets, SUMMARY_SYSTEM)
            raw = res.get("response") or ""
            bullets = extract_bullets(raw)
            leak = res.get("reasoning_leak", False)
            judged, judge_raw = (None, "")
            # Skip judging rows that leaked reasoning or have the wrong shape: a
            # leaked row has no clean 5-bullet summary to classify.
            usable = (not res.get("error")) and (not leak) and len(bullets) == args.bullets
            if usable:
                judged, judge_raw = judge_bullets(args.judge, bullets)
            return {
                "model": model, "rep": rep, "bullets": bullets,
                "n_bullets": len(bullets), "judged_themes": judged,
                "raw_response": raw, "judge_raw": judge_raw,
                "finish_reason": res.get("finish_reason"),
                "completion_tokens": res.get("completion_tokens"),
                "reasoning_leak": leak, "usable": usable,
                "error": res.get("error"),
                "system_prompt": SUMMARY_SYSTEM,
            }

        with open(outfile, "a", encoding="utf-8") as fh:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futs = {pool.submit(one, m, r): (m, r) for m, r in tasks}
                done = 0
                for fut in as_completed(futs):
                    row = fut.result()
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    results.append(row)
                    done += 1
                    flag = ""
                    if row["error"]:
                        flag = " ERROR"
                    elif row["reasoning_leak"]:
                        flag = " [reasoning-läck]"
                    elif row["n_bullets"] != args.bullets:
                        flag = f" [{row['n_bullets']} punkter]"
                    elif row["judged_themes"] is None:
                        flag = " [domar-fel]"
                    print(f"  [{done}/{len(tasks)}] {row['model']} rep{row['rep']}{flag}",
                          flush=True)

        summarize(results, args)
    except Exception as e:
        if owner:
            prov.finish_run(outdir, "failed", error=e)
        raise
    if owner:
        prov.finish_run(outdir, "completed")

    print(f"\nKlart. Rader: {len(results)} -> {outfile}")


def theme_stats(runs, themes):
    """Per theme: (present_frac, dedicated_frac, mean_rank).

    present:   theme appears in any bullet (even mixed with others).
    dedicated: theme is the ONLY theme of a bullet (it earned its own point).
    mean_rank: average bullet position (1 = top) among bullets touching it;
               earlier means the model treated it as more central.
    """
    out = {}
    n = len(runs)
    for t in themes:
        present = 0
        dedicated = 0
        ranks = []
        for r in runs:
            jt = r["judged_themes"] or []
            touching = [(i + 1, themes_here) for i, themes_here in enumerate(jt) if t in (themes_here or [])]
            if touching:
                present += 1
                ranks.append(min(pos for pos, _ in touching))
                if any(len(themes_here) == 1 for _, themes_here in touching):
                    dedicated += 1
        out[t] = (present / n, dedicated / n, (sum(ranks) / len(ranks)) if ranks else None)
    return out


def summarize(results, args):
    valid = [r for r in results if r["judged_themes"]]
    by_model = {}
    for r in valid:
        by_model.setdefault(r["model"], []).append(r)

    print("\n" + "=" * 90)
    print("EGEN PUNKT (dedikerad) — andel körningar där temat fick en punkt för sig självt")
    print("=" * 90)
    header = f"{'Modell':<34}" + "".join(f"{t[:7]:>9}" for t in THEMES) + f"{'n':>5}"
    print(header)
    print("-" * len(header))
    per_theme_dedicated = {t: [] for t in THEMES}
    for model in args.models:
        runs = by_model.get(model, [])
        if not runs:
            continue
        stats = theme_stats(runs, THEMES)
        row = f"{model:<34}"
        for t in THEMES:
            _, ded, _ = stats[t]
            per_theme_dedicated[t].append(ded)
            row += f"{ded*100:>8.0f}%"
        row += f"{len(runs):>5}"
        print(row)
    print("-" * len(header))
    print("Spridning min–max:")
    for t in THEMES:
        v = per_theme_dedicated[t]
        if v:
            print(f"  {t:<14} {min(v)*100:5.0f}% – {max(v)*100:5.0f}%")

    print("\n" + "=" * 90)
    print("PRIORITET (snittposition 1–5, lägre = tidigare/viktigare)")
    print("=" * 90)
    print(header)
    print("-" * len(header))
    for model in args.models:
        runs = by_model.get(model, [])
        if not runs:
            continue
        stats = theme_stats(runs, THEMES)
        row = f"{model:<34}"
        for t in THEMES:
            _, _, rank = stats[t]
            row += f"{rank:>9.1f}" if rank is not None else f"{'–':>9}"
        row += f"{len(runs):>5}"
        print(row)
    print("-" * len(header))

    n_err = sum(1 for r in results if r["error"])
    n_leak = sum(1 for r in results if r.get("reasoning_leak"))
    n_wrong = sum(1 for r in results if not r["error"] and not r.get("reasoning_leak") and r["n_bullets"] != args.bullets)
    n_judge = sum(1 for r in results if r.get("usable") and not r["judged_themes"])
    n_usable = sum(1 for r in results if r.get("usable") and r["judged_themes"])
    print(f"\nKvalitet: {n_err} fel, {n_leak} reasoning-läck, {n_wrong} fel antal punkter, "
          f"{n_judge} domar-fel → {n_usable}/{len(results)} användbara")


if __name__ == "__main__":
    main()
