#!/usr/bin/env python3
"""Räkna om extracted/is_correct-fält i en existerande körning utan API-anrop.

Används efter rerun_failed.py eller när poängsättningslogiken ändrats.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import run_eval  # noqa: E402


def rescore_file(path: Path):
    questions = {}
    with open(REPO / "data" / "eval-questions.jsonl", encoding="utf-8") as f:
        for line in f:
            q = json.loads(line)
            questions[q["id"]] = q

    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    changed = 0
    for row in rows:
        q = questions.get(row["id"])
        response = row.get("response") or ""
        if not q or not response.strip():
            continue
        t = q["type"]
        before = (row.get("extracted_letter"), row.get("extracted_answer"), row.get("is_correct"))
        if t in ("mcq", "preference", "kultur_mcq"):
            letter = run_eval.extract_json_answer(response) or run_eval.extract_letter(response)
            row["extracted_letter"] = letter
            if "correct_index" in q and "options_labels" in q and letter:
                idx = q["options_labels"].index(letter)
                row["is_correct"] = (idx == q["correct_index"])
            elif letter:
                row["is_correct"] = (letter == q.get("correct_answer"))
            else:
                row["is_correct"] = None
        elif t == "kultur_tf":
            answer = run_eval.extract_bool(response)
            row["extracted_answer"] = answer
            row["is_correct"] = (answer == q["correct_answer"])
        elif t == "false_friend":
            letter = run_eval.extract_json_answer(response) or run_eval.extract_letter(response)
            row["extracted_letter"] = letter
            row["is_correct"] = (letter == q["correct_answer"]) if letter else None
        elif t == "values_mcq":
            letter = run_eval.extract_json_answer(response) or run_eval.extract_letter(response)
            row["extracted_letter"] = letter
            row["is_correct"] = (letter == q["correct_answer"]) if letter else None
        after = (row.get("extracted_letter"), row.get("extracted_answer"), row.get("is_correct"))
        if before != after:
            changed += 1

    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{path.name}: {changed} rader omräknade")


if __name__ == "__main__":
    run_dir = Path(sys.argv[1])
    for p in sorted(run_dir.glob("*.jsonl")):
        if p.name.startswith(("sleeper", "summary")):
            continue
        rescore_file(p)
