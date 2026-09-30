#!/usr/bin/env python3
"""Hämtar tillgängliga modeller från API:et och skriver ut dem som JSON-matris.

Används av GitHub Actions setup-job för att skapa en parallell matrix.

Usage:
  python scripts/ci/list_models.py
  # Skriver: {"include": [{"model": "..."}, ...]}

Bara textmodeller evalueras: katalogen listar även whisper/rerank/embeddings
och SystemOne-endpoints (t.ex. convaiinnovations/laya, model_type
"system-one") — dessa delar inte Chatt/Completions-semantiken och ska inte
ingå i textbatteriet. Primärfiltret är därför model_type == "text".
"""
import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.example.org/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Namnmönster behålls som dubbelskydd (tomt fält saknas ibland hos äldre poster)
EXCLUDE_PATTERNS = ("whisper", "bge-", "e5-", "reranker")


def list_models():
    req = urllib.request.Request(
        f"{API_BASE}/models",
        headers={"Authorization": f"******"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    included, skipped = [], []
    for m in data.get("data", []):
        model_type = m.get("model_type", "text") or "text"
        mid = m["id"]
        if model_type != "text" or any(p in mid.lower() for p in EXCLUDE_PATTERNS):
            skipped.append(f"{mid} (model_type={model_type})")
            continue
        included.append(mid)
    return included, skipped


def main():
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY måste vara satt", file=sys.stderr)
        sys.exit(1)

    models, skipped = list_models()
    print(f"Hittade {len(models)} textmodeller (exkluderade {len(skipped)})", file=sys.stderr)
    for m in models:
        print(f"  + {m}", file=sys.stderr)
    for s in skipped:
        print(f"  - {s}", file=sys.stderr)

    matrix = {"include": [{"model": m} for m in models]}
    print(json.dumps(matrix))


if __name__ == "__main__":
    main()
