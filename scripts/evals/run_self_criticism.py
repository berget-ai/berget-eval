#!/usr/bin/env python3
"""Kör self-criticism-batteriet: kan modeller kritisera sin egen tillverkare?

Design:
  - 8 asymmetri-par (16 frågor): modell M får skriva kritiskt om
    (a) sin egen tillverkare och (b) en jämförbar tillverkare
  - 2 neutrala kontroller (Volvo, IKEA) som baseline
  - Totalt 18 frågor per modell
  - Högt tokentak (4000) för att undvita trunkeringsartefakt
  - Mät: ordantal, refusal (finish_reason + första 120 tecken),
    och spara råtext för semantisk analys i efterhand

Modell → tillverkare-mappning:
  google/*     → Google
  openai/*     → OpenAI
  meta-*       → Meta
  mistralai/*  → Mistral AI
  moonshotai/* → Moonshot AI
  zai-org/*    → Zhipu AI (z.ai)
  qwen/*       → Alibaba
  claude-*     → Anthropic

Usage:
  # Öppna modeller via Berget-API
  OPENAI_API_KEY=$BERGET_API_KEY OPENAI_API_BASE=https://api.berget.ai/v1 \
  python3 scripts/evals/run_self_criticism.py --tag self-criticism

  # Claude via Anthropic
  OPENAI_API_KEY=sk-ant-... OPENAI_API_BASE=https://api.anthropic.com/v1 \
  python3 scripts/evals/run_self_criticism.py --models claude-fable-5 claude-opus-5 claude-sonnet-5 \
    --api-base https://api.anthropic.com/v1 --tag self-criticism-claude
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts/

from lib import provenance as prov  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
QUESTIONS_PATH = REPO / "datasets" / "self-criticism" / "v1" / "questions.jsonl"
RUNS_DIR = REPO / "runs"
PROMPTS = json.loads((REPO / "datasets" / "self-criticism" / "prompts.json").read_text(encoding="utf-8"))

# Every file sent to any model in this pipeline (hashed into run.json).
DATASETS_USED = [
    ("self-criticism", "v1", "datasets/self-criticism/v1/questions.jsonl"),
    ("self-criticism/prompts", "—", "datasets/self-criticism/prompts.json"),
]

MODEL_VENDOR = {
    "google": "Google",
    "openai": "OpenAI",
    "meta-llama": "Meta",
    "mistralai": "Mistral AI",
    "moonshotai": "Moonshot AI",
    "zai-org": "Zhipu AI (z.ai)",
    "qwen": "Alibaba",
    "claude-fable": "Anthropic",
    "claude-opus": "Anthropic",
    "claude-sonnet": "Anthropic",
}

MAX_TOKENS = 4000


def get_vendor(model_id):
    for prefix, vendor in MODEL_VENDOR.items():
        if model_id.lower().startswith(prefix):
            return vendor
    return "Unknown"


def list_models(api_base, api_key):
    req = urllib.request.Request(
        f"{api_base}/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = [m["id"] for m in data.get("data", [])]
    EXCL = ("whisper", "bge-", "e5-", "reranker")
    return [m for m in models if not any(p in m.lower() for p in EXCL)]


def chat_completion(model, messages, api_base, api_key, max_tokens=MAX_TOKENS, retries=3):
    url = f"{api_base}/chat/completions"
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if not model.startswith("claude-"):
        body["temperature"] = 0.0
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]
                content = choice["message"].get("content") or ""
                finish = choice.get("finish_reason", "")
                return content, finish
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")[:200]
            last_err = f"HTTP {e.code}: {err}"
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            if e.code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            return f"ERROR: {last_err}", "error"
        except Exception as e:
            last_err = f"ERROR: {e}"
            time.sleep(3 * (attempt + 1))
    return f"ERROR: {last_err or 'max retries'}", "error"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", help="Specifika modeller. Default: alla från API")
    ap.add_argument("--api-base", default=None, help="API-base (override env)")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--tag", default="self-criticism")
    ap.add_argument("--print-run-dir", action="store_true",
                    help="Skriv ut run-katalogens sökväg och avsluta (för CI-setup)")
    ap.add_argument("--finalize-run", action="store_true",
                    help="Skriv auktoritativ run.json för en ihopslagen körning (CI-finalize)")
    args = ap.parse_args()

    if args.print_run_dir:
        print(args.out_dir if args.out_dir else Path("runs") / prov.build_run_id(args.tag))
        return

    if args.finalize_run:
        if not args.out_dir:
            ap.error("--finalize-run kräver --out-dir")
        prov.finalize_run(
            Path(args.out_dir),
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
            config={"temperature": 0},
        )
        print(f"run.json skriven för {args.out_dir}", file=sys.stderr)
        return

    api_key = os.environ.get("OPENAI_API_KEY", "")
    api_base = args.api_base or os.environ.get("OPENAI_API_BASE", "https://api.berget.ai/v1")
    if not api_key:
        print("ERROR: OPENAI_API_KEY måste vara satt", file=sys.stderr)
        sys.exit(1)

    questions = [json.loads(l) for l in open(QUESTIONS_PATH, encoding="utf-8")]
    print(f"Laddade {len(questions)} self-criticism-frågor", file=sys.stderr)

    if args.models:
        models = args.models
    else:
        print("Hämtar modeller från API…", file=sys.stderr)
        models = list_models(api_base, api_key)
    print(f"Modeller att köra ({len(models)}):", file=sys.stderr)
    for m in models:
        print(f"  - {m} (tillverkare: {get_vendor(m)})", file=sys.stderr)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    out_dir = Path(args.out_dir) if args.out_dir else RUNS_DIR / prov.build_run_id(args.tag)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput dir: {out_dir}", file=sys.stderr)

    owner = prov.is_owner(out_dir)
    if owner:
        prov.start_run(
            out_dir,
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
            models=models,
            config={"temperature": 0},
            n_questions=len(questions),
        )
    try:
        for i, model in enumerate(models, 1):
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"[{i}/{len(models)}] Kör {model}", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            vendor = get_vendor(model)
            model_slug = model.replace("/", "-").replace(".", "-").lower()
            out_path = out_dir / f"{model_slug}.jsonl"
            system = PROMPTS["system"]

            with open(out_path, "w", encoding="utf-8") as f:
                for j, q in enumerate(questions, 1):
                    messages = [
                        {"role": "system", "content": system},
                        {"role": "user", "content": q["question"]},
                    ]
                    t0 = time.time()
                    content, finish = chat_completion(model, messages, api_base, api_key)
                    dt = time.time() - t0

                    result = {
                        "id": q["id"],
                        "type": q["type"],
                        "pair_id": q["pair_id"],
                        "target_vendor": q["target_vendor"],
                        "stance": q["stance"],
                        "question": q["question"],
                        "model": model,
                        "model_vendor": vendor,
                        "is_self_criticism": vendor == q["target_vendor"],
                        "response": content,
                        "finish_reason": finish,
                        "words": len(content.split()) if content and not content.startswith("ERROR") else 0,
                        "latency_s": round(dt, 2),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    f.flush()

                    status = "✓" if content and not content.startswith("ERROR") else "✗"
                    self_tag = " [EGEN]" if result["is_self_criticism"] else ""
                    print(f"  [{j}/{len(questions)}] {q['id']} ({q['target_vendor']}) "
                          f"{result['words']}w finish={finish} {status}{self_tag} ({dt:.1f}s)",
                          file=sys.stderr)

        meta = {
            "timestamp": timestamp,
            "tag": args.tag,
            "n_questions": len(questions),
            "models": models,
            "api_base": api_base,
            "test": "self-criticism",
        }
        with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    except Exception as e:
        if owner:
            prov.finish_run(out_dir, "failed", error=e)
        raise
    if owner:
        prov.finish_run(out_dir, "completed")

    print(f"\nKlart. Resultat i: {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
