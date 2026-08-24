#!/usr/bin/env python3
"""Kör om Claude-svar som blev tomma (finish_reason='length' / refusal).

Läser en resultatfil, hittar rader med tomt response, kör om dem mot Anthropic
med högre max_tokens och längre timeout, loggar finish_reason, och skriver
tillbaka de ifyllda svaren in-place. Bevarar alla övriga rader orörda.

Usage:
  OPENAI_API_KEY=sk-ant-... OPENAI_API_BASE=https://api.anthropic.com/v1 \
  python3 scripts/rerun_empty_claude.py <model.jsonl> [--max-tokens 16000]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.anthropic.com/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

SYSTEM = "Du är en hjälpsam assistent."


def chat_completion(model, messages, max_tokens, timeout=180, retries=3):
    """Returnerar (content, finish_reason)."""
    url = f"{API_BASE}/chat/completions"
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {API_KEY}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]
                return choice["message"].get("content") or "", choice.get("finish_reason")
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
    ap.add_argument("jsonl", help="Resultatfil att reparera (in-place)")
    ap.add_argument("--max-tokens", type=int, default=16000)
    args = ap.parse_args()

    path = Path(args.jsonl)
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    model = rows[0]["model"] if rows else None
    if not model:
        print("Ingen modell i filen", file=sys.stderr)
        sys.exit(1)

    empty_idx = [i for i, r in enumerate(rows)
                 if not (r.get("response") or "").strip()]
    print(f"{path.name}: {len(empty_idx)} tomma av {len(rows)} (modell {model})",
          file=sys.stderr)
    if not empty_idx:
        print("Inget att köra om.", file=sys.stderr)
        return

    filled = 0
    still_empty = 0
    for n, i in enumerate(empty_idx, 1):
        r = rows[i]
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": r["question"]},
        ]
        t0 = time.time()
        content, finish = chat_completion(model, messages, args.max_tokens)
        dt = time.time() - t0
        ok = bool(content.strip()) and not content.startswith("ERROR")
        if ok:
            rows[i]["response"] = content
            rows[i]["latency_s"] = round(dt, 2)
            rows[i]["timestamp"] = datetime.now(timezone.utc).isoformat()
            filled += 1
        else:
            still_empty += 1
        rows[i]["finish_reason"] = finish
        rows[i]["rerun"] = True
        status = "✓" if ok else "✗"
        print(f"  [{n}/{len(empty_idx)}] {r['id']} finish={finish} {status} "
              f"({len(content)} tkn, {dt:.1f}s)", file=sys.stderr)

    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nKlart: {filled} ifyllda, {still_empty} fortfarande tomma.", file=sys.stderr)


if __name__ == "__main__":
    main()
