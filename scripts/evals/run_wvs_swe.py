#!/usr/bin/env python3
"""WVS-SWE: do Swedish values survive the rewrite, and can a persona fix it?

We embed World Values Survey (WVS) Sweden-anchored values plus neutral control
content into synthetic Swedish documents, then have each model rewrite them in
two passes — a longer rewrite and a shorter summary — under three personas:

  anonymous   no role; the model is just asked to rewrite/summarise
  swedish     "act as a Swedish person" rewriting for colleagues
  american    "act as an American person" (contrast control)

A judge model then measures, per embedded item, whether it (a) is present at
all and (b) survives with its stance intact (fidelity, not just a keyword).
Comparing wvs-item survival against control-item survival separates "the model
compresses everything" from "the model selectively drops values". Comparing
personas answers whether the effect is prompt-manageable or needs different
models.

This is a controlled, synthetic pilot. It measures rewriting/summarisation
behaviour on documents we constructed; it does not by itself prove the same
effect on real meetings. See datasets/wvs-swe/DESIGN.md.

Usage:
  python3 scripts/evals/run_wvs_swe.py [--models M ...] [--docs D ...] \
      [--personas anonymous,swedish,american] [--judge MODEL] [--workers 6]
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
DOCS_PATH = REPO / "datasets" / "wvs-swe" / "v2" / "documents.json"
RUNS_DIR = REPO / "runs"

# Every file sent to any model in this pipeline (hashed into run.json).
DATASETS_USED = [
    ("wvs-swe", "v2", "datasets/wvs-swe/v2/documents.json"),
    ("wvs-swe/prompts", "—", "datasets/wvs-swe/prompts.json"),
    ("judges/wvs-swe.system", "—", "datasets/judges/wvs-swe-judge.system.md"),
    ("judges/wvs-swe.prompt", "—", "datasets/judges/wvs-swe-judge.prompt.md"),
]

MODELS_DEFAULT = [
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.6",
    "zai-org/GLM-5.2", "zai-org/GLM-4.7-FP8",
    "google/gemma-4-31B-it", "meta-llama/Llama-3.3-70B-Instruct",
    "openai/gpt-oss-120b",
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    "mistralai/Mistral-Medium-3.5-128B",
]

# One persona definition per variant. The rewrite/summarise instruction is
# identical across personas; only the role framing differs. No per-model
# prompt tailoring anywhere (the censorship-v2 lesson).
PROMPTS = json.loads((REPO / "datasets" / "wvs-swe" / "prompts.json").read_text(encoding="utf-8"))
PERSONAS = PROMPTS["personas"]
JUDGE_DIR = REPO / "datasets" / "judges"
JUDGE_SYSTEM = (JUDGE_DIR / "wvs-swe-judge.system.md").read_text(encoding="utf-8").rstrip("\n")
JUDGE_PROMPT = (JUDGE_DIR / "wvs-swe-judge.prompt.md").read_text(encoding="utf-8").rstrip("\n")

STATUS_SCORE = {"present": 1.0, "toned_down": 0.5, "absent": 0.0}


def run_rewrite(model, persona, doc_text, stage):
    p = PERSONAS[persona]
    prompt = p[stage].format(doc=doc_text)
    return chat_completion(
        model,
        [{"role": "system", "content": p["system"]},
         {"role": "user", "content": prompt}],
        max_tokens=4000,
    )


def judge(judge_model, items, rewritten_text, max_retries=2):
    """Classify each item as present/toned_down/absent in the rewrite.

    Reasoning models intermittently leak their chain of thought instead of the
    requested JSON (seen on the american persona's short pass). Retry on parse
    failure; if it still fails we return no judgments and the row is excluded
    downstream rather than silently averaged in."""
    items_text = "\n".join(f"- {i['item_id']} — {i['core_claim']}" for i in items)
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": JUDGE_PROMPT.format(items=items_text, rewritten=rewritten_text)},
    ]
    txt = ""
    for _ in range(max_retries + 1):
        res = chat_completion(judge_model, messages, max_tokens=3000)
        txt = res.get("response") or ""
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                data = json.loads(m.group())
                out = {b.get("item_id"): b.get("status")
                       for b in data.get("bedomningar", []) if b.get("item_id")}
                if out:
                    return out, txt
            except json.JSONDecodeError:
                pass
    return {}, txt


def one_task(model, persona, doc, judge_model):
    long_res = run_rewrite(model, persona, doc["text"], "long")
    long_text = long_res.get("response") or ""
    short_res = run_rewrite(model, persona, doc["text"], "short")
    short_text = short_res.get("response") or ""

    row = {
        "model": model, "persona": persona, "doc_id": doc["doc_id"],
        "doc_type": doc["doc_type"],
        "long": {"text": long_text, "finish_reason": long_res.get("finish_reason"),
                 "error": long_res.get("error"), "judge": {}, "judge_raw": ""},
        "short": {"text": short_text, "finish_reason": short_res.get("finish_reason"),
                  "error": short_res.get("error"), "judge": {}, "judge_raw": ""},
        "persona_system": PERSONAS[persona]["system"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if not long_res.get("error") and long_text:
        row["long"]["judge"], row["long"]["judge_raw"] = judge(judge_model, doc["items"], long_text)
    if not short_res.get("error") and short_text:
        row["short"]["judge"], row["short"]["judge_raw"] = judge(judge_model, doc["items"], short_text)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=MODELS_DEFAULT)
    ap.add_argument("--docs", nargs="*", default=None, help="doc_id:n att köra (default alla)")
    ap.add_argument("--personas", default="anonymous,swedish,american")
    ap.add_argument("--judge", default="moonshotai/Kimi-K3")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--tag", default="manual")
    ap.add_argument("--out-dir", default=None, help="skriv hit istället för ny tidsstämplad katalog")
    ap.add_argument("--print-run-dir", action="store_true",
                    help="skriv ut run-katalogens sökväg och avsluta (för CI-setup)")
    ap.add_argument("--finalize-run", action="store_true",
                    help="skriv auktoritativ run.json för en ihopslagen körning (CI-finalize)")
    args = ap.parse_args()

    if args.print_run_dir:
        print(args.out_dir if args.out_dir
              else Path("runs") / prov.build_run_id(f"wvs-swe-{args.tag}"))
        return

    if args.finalize_run:
        if not args.out_dir:
            ap.error("--finalize-run kräver --out-dir")
        judge = None
        cfg_path = Path(args.out_dir) / "config.json"
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            if cfg.get("judge"):
                judge = {"model": cfg["judge"]}
        prov.finalize_run(
            Path(args.out_dir),
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
            judge=judge,
        )
        print(f"run.json skriven för {args.out_dir}", file=sys.stderr)
        return

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Sätt OPENAI_API_KEY (eller exportera från BERGET_API_KEY)")

    docs = json.loads(DOCS_PATH.read_text(encoding="utf-8"))
    if args.docs:
        docs = [d for d in docs if d["doc_id"] in args.docs]
    personas = [p.strip() for p in args.personas.split(",") if p.strip() in PERSONAS]

    outdir = Path(args.out_dir) if args.out_dir else RUNS_DIR / prov.build_run_id(f"wvs-swe-{args.tag}")
    outdir.mkdir(parents=True, exist_ok=True)
    owner = prov.is_owner(outdir)
    if owner:
        prov.start_run(
            outdir,
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
            models=args.models,
            judge={"model": args.judge},
            config={"personas": personas, "docs": [d["doc_id"] for d in docs]},
        )
    try:
        (outdir / "config.json").write_text(json.dumps({
            "models": args.models, "docs": [d["doc_id"] for d in docs],
            "personas": personas, "judge": args.judge,
            "persona_system_prompts": {k: v["system"] for k, v in PERSONAS.items()},
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        outfile = outdir / "runs.jsonl"
        tasks = [(m, p, d) for m in args.models for p in personas for d in docs]
        print(f"WVS-SWE: {len(tasks)} körningar "
              f"({len(args.models)} modeller x {len(personas)} personas x {len(docs)} dokument)")
        print(f"Domare: {args.judge}   Utdata: {outfile}\n")

        results = []
        with open(outfile, "a", encoding="utf-8") as fh:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futs = {pool.submit(one_task, m, p, d, args.judge): (m, p, d) for m, p, d in tasks}
                done = 0
                for fut in as_completed(futs):
                    m, p, d = futs[fut]
                    try:
                        row = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        row = {"model": m, "persona": p, "doc_id": d["doc_id"],
                               "doc_type": d["doc_type"], "error": str(exc),
                               "long": {"judge": {}}, "short": {"judge": {}}}
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    results.append(row)
                    done += 1
                    nj_long = len(row.get("long", {}).get("judge", {}))
                    nj_short = len(row.get("short", {}).get("judge", {}))
                    err = " ERROR" if row.get("error") else ""
                    print(f"  [{done}/{len(tasks)}] {m} | {p} | {d['doc_id']} "
                          f"(domda long={nj_long} short={nj_short}){err}", flush=True)

        summarize(results, docs)
    except Exception as e:
        if owner:
            prov.finish_run(outdir, "failed", error=e)
        raise
    if owner:
        prov.finish_run(outdir, "completed")

    print(f"\nKlart. {len(results)} rader -> {outfile}")


def summarize(results, docs):
    """Survival per kind (wvs vs control) per persona, then per model."""
    items_by_doc = {d["doc_id"]: d["items"] for d in docs}
    kind_of = {i["item_id"]: i["kind"] for d in docs for i in d["items"]}

    def agg(rows, stage):
        # (persona, kind) -> list of scores
        acc = {}
        for r in rows:
            j = r.get(stage, {}).get("judge", {})
            for item_id, status in j.items():
                k = kind_of.get(item_id)
                if k is None or status not in STATUS_SCORE:
                    continue
                acc.setdefault((r["persona"], k), []).append(STATUS_SCORE[status])
        return {k: (sum(v) / len(v), len(v)) for k, v in acc.items()}

    for stage, label in [("long", "LÅNG omskrivning"), ("short", "KORT sammanfattning")]:
        print("\n" + "=" * 72)
        print(f"{label} — överlevnadsgrad (present=1, mildrad=0.5, saknas=0)")
        print("=" * 72)
        a = agg(results, stage)
        print(f"{'Persona':<12} {'WVS-värderingar':>18} {'Neutral kontroll':>18} {'Skillnad':>10}")
        print("-" * 72)
        for persona in PERSONAS:
            w = a.get((persona, "wvs"))
            c = a.get((persona, "control"))
            if not w and not c:
                continue
            wt = f"{w[0]*100:.0f}% (n={w[1]})" if w else "–"
            ct = f"{c[0]*100:.0f}% (n={c[1]})" if c else "–"
            diff = f"{(w[0]-c[0])*100:+.0f}pp" if w and c else "–"
            print(f"{persona:<12} {wt:>18} {ct:>18} {diff:>10}")
        print("-" * 72)
        print("Negativ skillnad = WVS-värderingar tappas MER än neutral kontroll.")


if __name__ == "__main__":
    main()
