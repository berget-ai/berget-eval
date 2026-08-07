#!/usr/bin/env python3
"""Provtesta frågorna mot en modell. Bygger test-prompter, skickar till API, sparar råsvar."""
import json
import os
import re
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error

DATA = Path(__file__).resolve().parent.parent / "data"
QUESTIONS = DATA / "eval-questions.jsonl"

MODEL_ARG = sys.argv[1] if len(sys.argv) > 1 else "mistralai/Mistral-Small-3.2-24B-Instruct-2506"
#Filnamn-säker slugify av modelnamn
MODEL_SLUG = MODEL_ARG.replace("/", "-").replace(".", "-").replace(" ", "-").lower()
OUT = DATA / f"eval-pilot-responses-{MODEL_SLUG}.jsonl"

# För reasoning-modeller: tvinga direkt svar utan chain-of-thought
REASONING_MODELS = {"zai-org/GLM-5.2", "zai-org/GLM-4.7-FP8", "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.6", "openai/gpt-oss-120b"}

def get_system_prompt(model):
    if model in REASONING_MODELS:
        return ("Du är en modell som svarar kort och koncist på svenska. "
                "Svara ENDAST med det som efterfrågas - ingen förklaring, ingen analys, ingen reasoning. "
                "För flervalsfrågor: svara med enbart bokstaven. "
                "För preferensval: svara med enbart bokstaven. "
                "För fritext: svara direkt utan inledning.")
    return "Du är en hjälpmodell som svarar på svenska. Följ instruktionerna noggrant."

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.example.org/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

MODEL = MODEL_ARG

def chat_completion(model, messages, temperature=0.0, max_tokens=300, retries=2):
    url = f"{API_BASE}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    # För reasoning-modeller: försök stänga av thinking via chat_template_kwargs
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
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body_err = e.read().decode("utf-8", errors="replace")
            last_err = f"HTTP_ERROR {e.code}: {body_err[:200]}"
            if e.code < 500:
                return last_err
        except Exception as e:
            last_err = f"ERROR: {e}"
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    return last_err or "ERROR: unknown"

def build_prompt(q):
    """Bygg user-meddelandet för en fråga."""
    if q["type"] in ("mcq", "kultur_mcq"):
        opts = "\n".join(f"{label}. {o}" for label, o in zip(q["options_labels"], q["options"]))
        return f"{q['question']}\n\n{opts}"
    elif q["type"] == "preference":
        opts = "\n".join(f"{label}. {o}" for label, o in zip(q["options_labels"], q["options"]))
        return f"{q['question']}\n\n{opts}"
    elif q["type"] == "long_form":
        return f"{q['question']} Svara kort (max {q.get('max_words', 80)} ord)."
    elif q["type"] == "translation":
        return q["question"]
    elif q["type"] == "kultur_tf":
        return q["question"]
    return q["question"]

def extract_letter_answer(text):
    """Extrahera A/B/C/D från modellens svar."""
    if not text:
        return None
    text = text.strip()
    m = re.match(r"^\s*([ABCD])\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"(?:svaret är|svaret:\s*)\s*([ABCD])\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return None

def extract_bool_answer(text):
    """Extrahera Sant/Falskt från modellens svar."""
    if not text: return None
    text = text.strip().lower()
    # Direkt "sant" eller "falskt" först
    m = re.match(r"^\s*(sant|falskt|true|false|ja|nej)\b", text)
    if m:
        v = m.group(1)
        if v in ("sant", "true", "ja"): return "Sant"
        if v in ("falskt", "false", "nej"): return "Falskt"
    # "svaret är sant/falskt"
    m = re.search(r"(?:svaret är|svaret:?)\s*(sant|falskt|true|false|ja|nej)", text)
    if m:
        v = m.group(1)
        if v in ("sant", "true", "ja"): return "Sant"
        if v in ("falskt", "false", "nej"): return "Falskt"
    # Första förekomst
    if "sant" in text[:50]: return "Sant"
    if "falskt" in text[:50]: return "Falskt"
    return None

def main():
    if not API_KEY:
        print("ERROR: BERGET_API_KEY eller OPENAI_API_KEY måste vara satt", file=sys.stderr)
        sys.exit(1)

    questions = []
    with open(QUESTIONS, encoding="utf-8") as f:
        for line in f:
            questions.append(json.loads(line))

    # Pilot: ta första 5 av varje typ
    by_type = {}
    for q in questions:
        by_type.setdefault(q["type"], []).append(q)
    pilot = []
    for t, qs in by_type.items():
        pilot.extend(qs[:5])

    print(f"Pilot: {len(pilot)} frågor mot {MODEL}", file=sys.stderr)

    system = get_system_prompt(MODEL)
    print(f"System-prompt: {system[:100]}...", file=sys.stderr)

    results = []
    with open(OUT, "w", encoding="utf-8") as f:
        for i, q in enumerate(pilot):
            prompt = build_prompt(q)
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
            t0 = time.time()
            response = chat_completion(MODEL, messages)
            dt = time.time() - t0

            result = {
                "id": q["id"],
                "type": q["type"],
                "question": q["question"],
                "expected": q.get("correct_answer") or q.get("expected_keywords"),
                "model": MODEL,
                "response": response,
                "latency_s": round(dt, 2),
            }
            if q["type"] in ("mcq", "preference", "kultur_mcq"):
                letter = extract_letter_answer(response)
                result["extracted_letter"] = letter
                if letter:
                    labels = q["options_labels"]
                    idx = labels.index(letter)
                    result["is_correct"] = (idx == q["correct_index"])
                else:
                    result["is_correct"] = None
            elif q["type"] == "kultur_tf":
                answer = extract_bool_answer(response)
                result["extracted_answer"] = answer
                result["is_correct"] = (answer == q["correct_answer"])

            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()

            correct_mark = ""
            if "is_correct" in result:
                correct_mark = "✓" if result["is_correct"] else "✗"
            print(f"[{i+1}/{len(pilot)}] {q['id']} ({q['type']}) {dt:.1f}s {correct_mark}", file=sys.stderr)

    print(f"\nWrote {OUT}", file=sys.stderr)

    # Summering
    correct = sum(1 for r in [json.loads(l) for l in open(OUT)] if r.get("is_correct"))
    total_obj = sum(1 for r in [json.loads(l) for l in open(OUT)] if "is_correct" in r)
    print(f"\nObjektiva frågor: {correct}/{total_obj} rätt", file=sys.stderr)

if __name__ == "__main__":
    main()
