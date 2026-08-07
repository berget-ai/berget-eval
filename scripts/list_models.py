#!/usr/bin/env python3
"""Hämtar tillgängliga modeller från API:et och skriver ut dem som JSON-matris.

Används av GitHub Actions setup-job för att skapa en parallell matrix.

Usage:
  python scripts/list_models.py
  # Skriver: {"include": [{"model": "..."}, ...]}
"""
import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.example.org/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

EXCLUDE_PATTERNS = ("whisper", "bge-", "e5-", "reranker")


def list_models():
    req = urllib.request.Request(
        f"{API_BASE}/models",
        headers={"Authorization": f"******"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = [m["id"] for m in data.get("data", [])]
    return [m for m in models if not any(p in m.lower() for p in EXCLUDE_PATTERNS)]


def main():
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY måste vara satt", file=sys.stderr)
        sys.exit(1)

    models = list_models()
    print(f"Hittade {len(models)} modeller", file=sys.stderr)
    for m in models:
        print(f"  - {m}", file=sys.stderr)

    matrix = {"include": [{"model": m} for m in models]}
    print(json.dumps(matrix))


if __name__ == "__main__":
    main()
