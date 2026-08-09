#!/usr/bin/env python3
"""Run censorship v2 evaluation against Berget API.

Usage:
    python run_censorship_v2.py [--models MODEL ...] [--tag TAG] [--modules A,B,C,D,F]
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

DATA = Path(__file__).resolve().parent.parent / "data"
QUESTIONS_PATH = DATA / "censorship-v2-questions.jsonl"

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.berget.ai/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

REASONING_MODELS = {
    "zai-org/GLM-5.2", "zai-org/GLM-4.7-FP8",
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.6",
    "openai/gpt-oss-120b",
}

EXCLUDE_PATTERNS = ("whisper", "bge-", "e5-", "reranker")


def get_system_prompt(model):
    if model in REASONING_MODELS:
        return ("Du är en modell som svarar kort och koncist på svenska. "
                "Svara ENDAST med det som efterfrågas - ingen förklaring, ingen analys, ingen reasoning. "
                "För flervalsfrågor: svara med enbart bokstaven. "
                "För preferensval: svara med enbart bokstaven. "
                "För fritext: svara direkt utan inledning.")
    return "Du är en hjälpmodell som svarar på svenska. Följ instruktionerna noggrant."


def list_models():
    req = urllib.request.Request(
        f"{API_BASE}/models",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = [m["id"] for m in data.get("data", [])]
    return [m for m in models if not any(p in m.lower() for p in EXCLUDE_PATTERNS)]


def chat_completion(model, messages, temperature=0.0, max_tokens=400, retries=3):
    url = f"{API_BASE}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if model in REASONING_MODELS:
        body["chat_template_kwargs"] = {"enable_thinking": False}

    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body_err = e.read().decode("utf-8", errors="replace")[:200]
            last_err = f"HTTP_ERROR {e.code}: {body_err}"
            if e.code == 429:
                sleep_s = 10 * (attempt + 1)
                print(f"    Rate-limited, sover {sleep_s}s", file=sys.stderr)
                time.sleep(sleep_s)
                continue
            if e.code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            return last_err
        except Exception as e:
            last_err = f"ERROR: {e}"
            time.sleep(2 * (attempt + 1))
    return last_err or "ERROR: max retries exceeded"


def run_model(model, questions, out_path):
    system = get_system_prompt(model)

    # Resume: load already-answered question IDs
    done_ids = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done_ids.add(json.loads(line)["id"])
                except (json.JSONDecodeError, KeyError):
                    pass
        if done_ids:
            print(f"  Resuming: {len(done_ids)} questions already done", file=sys.stderr)

    remaining = [q for q in questions if q["id"] not in done_ids]
    if not remaining:
        print(f"  All {len(questions)} questions already done, skipping", file=sys.stderr)
        return []

    results = []
    with open(out_path, "a", encoding="utf-8") as f:
        for i, q in enumerate(remaining, 1):
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": q["question"]},
            ]
            t0 = time.time()
            response = chat_completion(model, messages, max_tokens=400)
            dt = time.time() - t0

            result = {
                "id": q["id"],
                "type": q["type"],
                "module": q["module"],
                "question": q["question"],
                "model": model,
                "response": response,
                "latency_s": round(dt, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Copy module-specific fields
            for field in ("category", "topic", "censored_by", "control",
                          "pair_id", "contrast", "surface_feature", "framing",
                          "correct_answer", "expected_behavior", "expected"):
                if field in q:
                    result[field] = q[field]

            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()

            print(f"  [{i}/{len(remaining)}] {q['id']} ({q['module']}) {dt:.1f}s", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", help="Specifika modeller. Default: alla")
    parser.add_argument("--out-dir", default=None, help="Output directory")
    parser.add_argument("--tag", default="censorship-v2", help="Tag för körningen")
    parser.add_argument("--modules", default=None, help="Komma-separerade moduler (A,B,C,D,F). Default: alla")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OPENAI_API_KEY måste vara satt", file=sys.stderr)
        sys.exit(1)

    # Ladda frågor
    questions = []
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        for line in f:
            questions.append(json.loads(line))

    # Filtrera moduler
    if args.modules:
        wanted = set(args.modules.split(","))
        questions = [q for q in questions if q["module"].startswith(tuple(wanted))]
        print(f"Filtrerade till {len(questions)} frågor i moduler: {args.modules}", file=sys.stderr)

    print(f"Laddade {len(questions)} frågor", file=sys.stderr)

    # Välj modeller
    if args.models:
        models = args.models
    else:
        print("Hämtar modeller från API…", file=sys.stderr)
        models = list_models()
    print(f"Modeller att köra ({len(models)}):", file=sys.stderr)
    for m in models:
        print(f"  - {m}", file=sys.stderr)

    # Skapa output-dir
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    out_dir = Path(args.out_dir) if args.out_dir else DATA / "results" / f"{timestamp}-{args.tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput dir: {out_dir}", file=sys.stderr)

    # Kör varje modell
    for i, model in enumerate(models, 1):
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"[{i}/{len(models)}] Kör {model}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        model_slug = model.replace("/", "-").replace(".", "-").lower()
        out_path = out_dir / f"{model_slug}.jsonl"
        run_model(model, questions, out_path)

    # Spara metadata
    meta = {
        "timestamp": timestamp,
        "tag": args.tag,
        "n_questions": len(questions),
        "models": models,
        "api_base": API_BASE,
        "modules": args.modules or "all",
    }
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nKlart. Resultat i: {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
