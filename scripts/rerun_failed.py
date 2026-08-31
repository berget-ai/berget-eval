#!/usr/bin/env python3
"""Rerun failed (HTTP_ERROR) questions for a model and merge into existing run file.

Usage:
    OPENAI_API_KEY=<key> OPENAI_API_BASE=<base> python scripts/rerun_failed.py \
        --run-dir data/results/2026-08-31T13-11-51-flash-rerun-2026-08-31 \
        --model zai-org/GLM-5.3-Flash
"""

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

# Import from run_eval (chat_completion, build_prompt, get_system_prompt)
import run_eval  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--delay", type=float, default=1.0,
                    help="Delay between requests in seconds (be nice to the server)")
    ap.add_argument("--retries", type=int, default=6)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    model = args.model
    model_slug = model.replace("/", "-").replace(".", "-").lower()
    out_path = run_dir / f"{model_slug}.jsonl"

    with open(out_path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    # Läs questions-filen för att få prompts
    questions = {}
    with open(REPO / "data" / "eval-questions.jsonl", encoding="utf-8") as f:
        for line in f:
            q = json.loads(line)
            questions[q["id"]] = q

    failed = [r for r in rows if not (r.get("response") or "").strip()
              or (r.get("response") or "").startswith("HTTP_ERROR")
              or (r.get("response") or "").startswith("ERROR:")]
    print(f"{len(failed)} misslyckade/tomma av {len(rows)} rader")

    fixed = 0
    for i, row in enumerate(failed, 1):
        q = questions.get(row["id"])
        if not q:
            print(f"  [{i}/{len(failed)}] {row['id']}: fråga saknas i eval-questions.jsonl, hoppar över")
            continue

        prompt = run_eval.build_prompt(q)
        system = run_eval.get_system_prompt(model)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        is_mcq = q["type"] in ("mcq", "preference", "kultur_mcq",
                               "values_mcq", "false_friend")
        if q["type"] == "sleeper_agent":
            max_tokens = 3000
        elif is_mcq:
            max_tokens = run_eval.MCQ_MAX_TOKENS
        else:
            # GLM-5.3-Flash tänker alltid (reasoning äter token-budget) —
            # ge fri-text-frågor ett rejält tak så svaret hinner fram.
            max_tokens = 3000

        t0 = time.time()
        response = run_eval.chat_completion(
            model, messages, max_tokens=max_tokens, retries=args.retries,
            response_format=run_eval.MCQ_RESPONSE_FORMAT if is_mcq else None,
        )
        dt = round(time.time() - t0, 2)

        if response.startswith("HTTP_ERROR") or response.startswith("ERROR:"):
            print(f"  [{i}/{len(failed)}] {row['id']}: STILL FAILING: {response[:80]}")
        else:
            fixed += 1
            print(f"  [{i}/{len(failed)}] {row['id']}: OK ({dt}s)")

        row["response"] = response
        row["latency_s"] = dt
        row["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "+00:00"
        row["rerun"] = True

        # Räkna om härledda fält (extracted/is_correct) med samma logik som run_eval
        if q["type"] in ("mcq", "preference", "kultur_mcq"):
            letter = run_eval.extract_json_answer(response) or run_eval.extract_letter(response)
            row["extracted_letter"] = letter
            if "correct_index" in q and "options_labels" in q and letter:
                idx = q["options_labels"].index(letter)
                row["is_correct"] = (idx == q["correct_index"])
            elif letter:
                row["is_correct"] = (letter == q.get("correct_answer"))
            else:
                row["is_correct"] = None
        elif q["type"] == "kultur_tf":
            answer = run_eval.extract_bool(response)
            row["extracted_answer"] = answer
            row["is_correct"] = (answer == q["correct_answer"])
        elif q["type"] == "false_friend":
            letter = run_eval.extract_json_answer(response) or run_eval.extract_letter(response)
            row["extracted_letter"] = letter
            row["is_correct"] = (letter == q["correct_answer"]) if letter else None
        elif q["type"] == "values_mcq":
            letter = run_eval.extract_json_answer(response) or run_eval.extract_letter(response)
            row["extracted_letter"] = letter
            row["is_correct"] = (letter == q["correct_answer"]) if letter else None

        time.sleep(args.delay)

    # Skriv tillbaka alla rader i originalordning
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nKlart: {fixed}/{len(failed)} fixade. Sparat till {out_path}")

    # Summera kvarvarande fel
    still = sum(1 for r in rows if (r.get("response") or "").startswith(("HTTP_ERROR", "ERROR:")))
    print(f"Kvarvarande fel: {still}")


if __name__ == "__main__":
    main()
