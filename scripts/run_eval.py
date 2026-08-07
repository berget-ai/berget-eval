#!/usr/bin/env python3
"""Full runner - kör alla frågor mot alla (eller valda) modeller.

Skillnad mot eval_pilot.py:
  - Kör ALLA frågor i data/eval-questions.jsonl (inte bara första 5 per typ)
  - Sparar resultat i data/results/<metadata-timestamp>/<model-slug>.jsonl
  - Stöd för rate-limit retries
  - Kan välja modeller via --models eller kör alla via API:et
  - Genererar sammanställning (summarize_eval) per körning
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

DATA = Path(__file__).resolve().parent.parent / "data"
QUESTIONS_PATH = DATA / "eval-questions.jsonl"

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.example.org/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Modeller som utför reasoning (behär tvingas till direkt svar)
REASONING_MODELS = {
    "zai-org/GLM-5.2", "zai-org/GLM-4.7-FP8",
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.6",
    "openai/gpt-oss-120b",
}

# Modeller som ska uteslutas (icke-chatt: embedding, whisper, etc.)
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
            # 429 rate limit -> lång retry
            if e.code == 429:
                sleep_s = 10 * (attempt + 1)
                print(f"    Rate-limited, sover {sleep_s}s", file=sys.stderr)
                time.sleep(sleep_s)
                continue
            # 5xx -> kort retry
            if e.code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            # 4xx -> ge upp
            return last_err
        except Exception as e:
            last_err = f"ERROR: {e}"
            time.sleep(2 * (attempt + 1))
    return last_err or "ERROR: max retries exceeded"


def build_prompt(q):
    if q["type"] in ("mcq", "kultur_mcq"):
        opts = "\n".join(f"{l}. {o}" for l, o in zip(q["options_labels"], q["options"]))
        return f"{q['question']}\n\n{opts}"
    elif q["type"] == "preference":
        opts = "\n".join(f"{l}. {o}" for l, o in zip(q["options_labels"], q["options"]))
        return f"{q['question']}\n\n{opts}"
    elif q["type"] == "long_form":
        return f"{q['question']} Svara kort (max {q.get('max_words', 80)} ord)."
    elif q["type"] == "translation":
        return q["question"]
    elif q["type"] == "kultur_tf":
        return q["question"]
    return q["question"]


def extract_letter(text):
    if not text: return None
    text = text.strip()
    m = re.match(r"^\s*([ABCD])\b", text, re.IGNORECASE)
    if m: return m.group(1).upper()
    m = re.search(r"(?:svaret är|svaret:\s*)\s*([ABCD])\b", text, re.IGNORECASE)
    if m: return m.group(1).upper()
    return None


def extract_bool(text):
    if not text: return None
    t = text.strip().lower()
    m = re.match(r"^\s*(sant|falskt|true|false|ja|nej)\b", t)
    if m:
        v = m.group(1)
        if v in ("sant", "true", "ja"): return "Sant"
        if v in ("falskt", "false", "nej"): return "Falskt"
    m = re.search(r"(?:svaret är|svaret:?)\s*(sant|falskt|true|false|ja|nej)", t)
    if m:
        v = m.group(1)
        if v in ("sant", "true", "ja"): return "Sant"
        if v in ("falskt", "false", "nej"): return "Falskt"
    if "sant" in t[:50]: return "Sant"
    if "falskt" in t[:50]: return "Falskt"
    return None


def run_model(model, questions, out_path, max_tokens_map=None):
    """Kör alla frågor mot en modell. Sparar löpande till out_path."""
    system = get_system_prompt(model)
    results = []
    with open(out_path, "w", encoding="utf-8") as f:
        for i, q in enumerate(questions, 1):
            prompt = build_prompt(q)
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
            t0 = time.time()
            response = chat_completion(model, messages)
            dt = time.time() - t0

            result = {
                "id": q["id"],
                "type": q["type"],
                "question": q["question"],
                "model": model,
                "response": response,
                "latency_s": round(dt, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Sätt expected och is_correct
            if q["type"] in ("mcq", "preference", "kultur_mcq"):
                result["expected"] = q.get("correct_answer")
                letter = extract_letter(response)
                result["extracted_letter"] = letter
                if letter:
                    idx = q["options_labels"].index(letter)
                    result["is_correct"] = (idx == q["correct_index"])
                else:
                    result["is_correct"] = None
            elif q["type"] == "kultur_tf":
                result["expected"] = q.get("correct_answer")
                answer = extract_bool(response)
                result["extracted_answer"] = answer
                result["is_correct"] = (answer == q["correct_answer"])
            elif q["type"] == "translation":
                result["expected"] = q.get("expected_keywords")
            elif q["type"] == "long_form":
                result["expected"] = q.get("concept")

            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()

            mark = ""
            if "is_correct" in result:
                mark = "✓" if result["is_correct"] else "✗"
            print(f"  [{i}/{len(questions)}] {q['id']} ({q['type']}) {dt:.1f}s {mark}", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", help="Specifika modeller. Default: alla")
    parser.add_argument("--out-dir", default=None, help="Output directory")
    parser.add_argument("--tag", default=None, help="Tag för körningen (används i sökväg)")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: BERGET_API_KEY eller OPENAI_API_KEY måste vara satt", file=sys.stderr)
        sys.exit(1)

    # Ladda frågor
    questions = []
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        for line in f:
            questions.append(json.loads(line))
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
    tag = args.tag or "run"
    out_dir = Path(args.out_dir) if args.out_dir else DATA / "results" / f"{timestamp}-{tag}"
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
        "tag": tag,
        "n_questions": len(questions),
        "models": models,
        "api_base": API_BASE,
    }
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nKlart. Resultat i: {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
