"""Shared OpenAI-compatible API client for the eval scripts.

Extracted from scripts/evals/run_censorship.py (PR 2 of the scripts
restructure) — it had become the de-facto API client for four other scripts
(run_wvs_swe, run_selection_bias, validate_wvs_swe, meta_review). Other
runners still carry their own chat_completion variants with different
signatures; consolidating those is deliberately out of scope.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.berget.ai/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

REASONING_MODELS = {
    "zai-org/GLM-5.2", "zai-org/GLM-4.7-FP8",
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.6",
    "openai/gpt-oss-120b",
}

# v1 used 400, which truncated 24-28 of 30 free-text answers for most models and
# invalidated every length-based metric. Measured worst case across all nine
# models is 2707 completion tokens (Mistral Medium on the Xinjiang question),
# so 4000 leaves headroom. Raise this rather than accepting truncation; any row
# that still comes back with finish_reason == "length" must be excluded from
# length-based metrics rather than silently averaged in.
MAX_TOKENS = 4000


def chat_completion(model, messages, temperature=0.0, max_tokens=None, retries=3):
    """Return a dict with the answer plus the metadata needed to validate it.

    Returns keys: response, finish_reason, completion_tokens, prompt_tokens, error.
    finish_reason == "length" means the answer was cut off by max_tokens; any
    length-based metric must exclude those rows.
    """
    if max_tokens is None:
        max_tokens = MAX_TOKENS
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
