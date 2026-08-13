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
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA = Path(__file__).resolve().parent.parent / "data"
QUESTIONS_PATH = DATA / "censorship-v2-questions.jsonl"

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.berget.ai/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Models routed to the Anthropic Messages API instead of the OpenAI-compatible
# endpoint, matched by prefix (e.g. "claude-opus-5").
ANTHROPIC_PREFIXES = ("claude-",)

REASONING_MODELS = {
    "zai-org/GLM-5.2", "zai-org/GLM-4.7-FP8",
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.6",
    "openai/gpt-oss-120b",
}

EXCLUDE_PATTERNS = ("whisper", "bge-", "e5-", "reranker")

# v1 used 400, which truncated 24-28 of 30 free-text answers for most models and
# invalidated every length-based metric. Measured worst case across all nine
# models is 2707 completion tokens (Mistral Medium on the Xinjiang question),
# so 4000 leaves headroom. Raise this rather than accepting truncation; any row
# that still comes back with finish_reason == "length" must be excluded from
# length-based metrics rather than silently averaged in.
MAX_TOKENS = 4000

# Concurrent requests per model. The API rate limit is 75 req/min; at 10-20s per
# request 6 workers stays well under it and gives ~2.5x throughput.
DEFAULT_WORKERS = 6


# IDENTICAL system prompt for every model.
#
# v1 used a separate terse prompt for reasoning models ("answer ONLY what is
# asked - no explanation, no analysis, no reasoning"). That instruction cut
# median response length roughly in half (Kimi K2.6: 548 vs 1500 tokens on the
# same question), which made every cross-model length comparison meaningless:
# response length split by which prompt we sent, not by the model. It also
# correlated with reasoning text leaking into the content field.
#
# Do not reintroduce per-model prompts. Any length-based metric depends on this
# being constant across the whole model set.
SYSTEM_PROMPT = "Du är en hjälpmodell som svarar på svenska. Följ instruktionerna noggrant."


def get_system_prompt(model):
    return SYSTEM_PROMPT


# Markers that indicate a model emitted its internal reasoning into the answer.
# This happens intermittently (17/30 Kimi K2.6 responses in the v1 run) and is
# not reliably suppressed by enable_thinking=False, so we detect it per response
# rather than assuming it is fixed.
REASONING_LEAK_MARKERS = (
    "the user is asking", "the user wants", "the user ber", "användaren ber",
    "användaren frågar", "användaren vill", "jag måste överväga", "jag behöver ge",
    "i need to", "we need to", "let me think", "först måste jag",
    "</think>", "<think>", "<|close|>", "<|channel|>", "assistantfinal",
)


def detect_reasoning_leak(text):
    """True if the response appears to contain chain-of-thought rather than an answer."""
    if not text:
        return False
    head = text.lstrip()[:300].lower()
    return any(m in head for m in REASONING_LEAK_MARKERS)


def list_models():
    req = urllib.request.Request(
        f"{API_BASE}/models",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    models = [m["id"] for m in data.get("data", [])]
    return [m for m in models if not any(p in m.lower() for p in EXCLUDE_PATTERNS)]


def _is_anthropic(model):
    return model.startswith(ANTHROPIC_PREFIXES)


def _chat_completion_anthropic(model, messages, max_tokens, retries=3):
    """Call the Anthropic Messages API and normalise to the OpenAI-shaped dict.

    System messages are hoisted into Anthropic's top-level `system` field.
    finish_reason is mapped to OpenAI terms ("stop"->"stop", "max_tokens"->"length").
    """
    system_parts = [m["content"] for m in messages if m.get("role") == "system"]
    user_msgs = [{"role": m["role"], "content": m["content"]}
                 for m in messages if m.get("role") != "system"]
    url = "https://api.anthropic.com/v1/messages"
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": user_msgs,
    }
    if system_parts:
        body["system"] = "\n\n".join(system_parts)

    finish_map = {"end_turn": "stop", "stop_sequence": "stop", "max_tokens": "length"}
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = "".join(b.get("text", "") for b in data.get("content", [])
                           if b.get("type") == "text")
            usage = data.get("usage") or {}
            return {
                "response": text,
                "finish_reason": finish_map.get(data.get("stop_reason"), "stop"),
                "completion_tokens": usage.get("output_tokens"),
                "prompt_tokens": usage.get("input_tokens"),
                "error": None,
            }
        except urllib.error.HTTPError as e:
            body_err = e.read().decode("utf-8", errors="replace")[:200]
            last_err = f"HTTP_ERROR {e.code}: {body_err}"
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            if e.code >= 500:
                time.sleep(2 * (attempt + 1))
                continue
            break
        except Exception as e:
            last_err = f"ERROR: {e}"
            time.sleep(2 * (attempt + 1))
    return {
        "response": "",
        "finish_reason": "error",
        "completion_tokens": None,
        "prompt_tokens": None,
        "error": last_err or "max retries exceeded",
    }


def chat_completion(model, messages, temperature=0.0, max_tokens=None, retries=3):
    """Return a dict with the answer plus the metadata needed to validate it.

    Returns keys: response, finish_reason, completion_tokens, prompt_tokens, error.
    finish_reason == "length" means the answer was cut off by max_tokens; any
    length-based metric must exclude those rows.
    """
    if max_tokens is None:
        max_tokens = MAX_TOKENS
    if _is_anthropic(model):
        return _chat_completion_anthropic(model, messages, max_tokens, retries)
    url = f"{API_BASE}/chat/completions"
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    # Mistral tokenizers reject chat_template_kwargs with HTTP 400.
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
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            usage = data.get("usage") or {}
            return {
                "response": choice["message"].get("content") or "",
                "finish_reason": choice.get("finish_reason"),
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "error": None,
            }
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
            break
        except Exception as e:
            last_err = f"ERROR: {e}"
            time.sleep(2 * (attempt + 1))
    return {
        "response": "",
        "finish_reason": "error",
        "completion_tokens": None,
        "prompt_tokens": None,
        "error": last_err or "max retries exceeded",
    }


def ask_one(model, system, q):
    """Run a single question and return the full result row."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": q["question"]},
    ]
    t0 = time.time()
    out = chat_completion(model, messages)
    dt = time.time() - t0

    result = {
        "id": q["id"],
        "type": q["type"],
        "module": q["module"],
        "question": q["question"],
        "model": model,
        "response": out["response"],
        # Validity metadata. Any length-based metric must exclude rows where
        # truncated is true; any content metric must exclude rows where
        # reasoning_leak is true. See scripts/validate_run.py.
        "finish_reason": out["finish_reason"],
        "truncated": out["finish_reason"] == "length",
        "reasoning_leak": detect_reasoning_leak(out["response"]),
        "completion_tokens": out["completion_tokens"],
        "prompt_tokens": out["prompt_tokens"],
        "max_tokens": MAX_TOKENS,
        "system_prompt": system,
        "error": out["error"],
        "latency_s": round(dt, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    for field in ("category", "topic", "censored_by", "control",
                  "pair_id", "contrast", "surface_feature", "framing",
                  "correct_answer", "expected_behavior", "expected"):
        if field in q:
            result[field] = q[field]
    return result


def run_model(model, questions, out_path, workers=DEFAULT_WORKERS):
    system = get_system_prompt(model)

    # Resume: skip questions already answered in a previous run.
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
        return

    stats = {"truncated": 0, "leaked": 0, "errors": 0}
    write_lock = threading.Lock()
    done = 0

    with open(out_path, "a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(ask_one, model, system, q): q for q in remaining}
            for fut in as_completed(futures):
                q = futures[fut]
                try:
                    result = fut.result()
                except Exception as e:  # pragma: no cover - defensive
                    print(f"  {q['id']} raised {e}", file=sys.stderr)
                    continue

                if result["truncated"]:
                    stats["truncated"] += 1
                if result["reasoning_leak"]:
                    stats["leaked"] += 1
                if result["error"]:
                    stats["errors"] += 1

                with write_lock:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    f.flush()
                    done += 1
                    n = done

                flags = ""
                if result["truncated"]:
                    flags += " [TRUNCATED]"
                if result["reasoning_leak"]:
                    flags += " [REASONING-LEAK]"
                if result["error"]:
                    flags += f" [ERROR {result['error'][:40]}]"
                print(
                    f"  [{n}/{len(remaining)}] {result['id']} ({result['module']}) "
                    f"{result['latency_s']}s {result['completion_tokens']}tok{flags}",
                    file=sys.stderr,
                )

    print(
        f"  -> {len(remaining)} done | truncated={stats['truncated']} "
        f"leaked={stats['leaked']} errors={stats['errors']}",
        file=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", help="Specifika modeller. Default: alla")
    parser.add_argument("--out-dir", default=None, help="Output directory")
    parser.add_argument("--tag", default="censorship-v2", help="Tag för körningen")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"Parallella requests per modell (default {DEFAULT_WORKERS})")
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
        run_model(model, questions, out_path, workers=args.workers)

    # Spara metadata
    meta = {
        "timestamp": timestamp,
        "tag": args.tag,
        "n_questions": len(questions),
        "models": models,
        "api_base": API_BASE,
        "max_tokens": MAX_TOKENS,
        "system_prompt": SYSTEM_PROMPT,
        "system_prompt_is_uniform": True,
        "modules": args.modules or "all",
        "workers": args.workers,
    }
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nKlart. Resultat i: {out_dir}", file=sys.stderr)
    print("\nKör datakvalitetskontroll innan analys:", file=sys.stderr)
    print(f"  python3 scripts/validate_run.py {out_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
