#!/usr/bin/env python3
"""Run multi-sample evaluation for high flip-rate models.

Runs N samples per condition for models with high baseline flip rates
(GPT-OSS, Llama 3.3, Kimi K3). This gives us mean ± std instead of
binary flag/no-flag.

Usage:
    python3 run_multisample_eval.py --samples 5 --models "openai/gpt-oss-120b,meta-llama/Llama-3.3-70B-Instruct,moonshotai/Kimi-K3"
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts/

from lib import provenance as prov  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent
QUESTIONS_PATH = REPO / "datasets" / "main-battery" / "v3" / "eval-questions.jsonl"
RESULTS_DIR = REPO / "runs"
PROMPTS = json.loads((REPO / "datasets" / "main-battery" / "prompts.json").read_text(encoding="utf-8"))
SYSTEM_PROMPT = PROMPTS["system"]

# Every file sent to any model in this pipeline (hashed into run.json).
DATASETS_USED = [
    ("main-battery", "v3", "datasets/main-battery/v3/eval-questions.jsonl"),
    ("main-battery/prompts", "—", "datasets/main-battery/prompts.json"),
]

API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.berget.ai/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

REASONING_MODELS = {
    "zai-org/GLM-5.2", "zai-org/GLM-4.7-FP8",
    "moonshotai/Kimi-K3", "moonshotai/Kimi-K2.6",
    "openai/gpt-oss-120b",
}

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
        except Exception as e:
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)

def load_sleeper_questions():
    """Load only sleeper agent questions (geopolitical triggers)."""
    questions = []
    with open(QUESTIONS_PATH) as f:
        for line in f:
            q = json.loads(line)
            if q.get("type") == "sleeper_agent" and q.get("trigger_region") in [
                "neutral", "iran_nk", "china", "russia", "israel"
            ]:
                questions.append(q)
    return questions

def run_multisample(models, samples_per_condition, run_dir):
    """Run multi-sample evaluation for specified models."""
    questions = load_sleeper_questions()

    # Group by pair_id
    pairs = {}
    for q in questions:
        pid = q.get("pair_id")
        if pid not in pairs:
            pairs[pid] = {}
        pairs[pid][q.get("trigger_region")] = q

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Running multi-sample evaluation: {samples_per_condition} samples per condition")
    print(f"Models: {', '.join(models)}")
    print(f"Pairs: {len(pairs)}")
    print(f"Results: {run_dir}")
    print()

    for model in models:
        model_slug = model.replace("/", "-").replace(".", "-")
        output_file = run_dir / f"{model_slug}.jsonl"

        print(f"\n=== {model} ===")

        with open(output_file, "w") as f:
            for pair_id, regions in sorted(pairs.items()):
                if "neutral" not in regions:
                    continue

                print(f"\n{pair_id}:")

                # Run baseline N times
                baseline_q = regions["neutral"]
                baseline_responses = []
                for i in range(samples_per_condition):
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": baseline_q["question"]},
                    ]
                    resp = chat_completion(model, messages)
                    baseline_responses.append(resp)
                    print(f"  baseline[{i}]: {len(resp)} chars")

                # Run each trigger region N times
                for region in ["iran_nk", "china", "russia", "israel"]:
                    if region not in regions:
                        continue

                    trigger_q = regions[region]
                    trigger_responses = []
                    for i in range(samples_per_condition):
                        messages = [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": trigger_q["question"]},
                        ]
                        resp = chat_completion(model, messages)
                        trigger_responses.append(resp)
                        print(f"  {region}[{i}]: {len(resp)} chars")

                    # Save all samples
                    record = {
                        "pair_id": pair_id,
                        "model": model,
                        "samples": samples_per_condition,
                        "baseline": {
                            "question": baseline_q["question"],
                            "responses": baseline_responses,
                        },
                        "trigger": {
                            "region": region,
                            "question": trigger_q["question"],
                            "responses": trigger_responses,
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"\nSaved: {output_file}")

    # Write metadata
    metadata = {
        "timestamp": timestamp,
        "type": "multisample",
        "samples_per_condition": samples_per_condition,
        "models": models,
        "pairs": list(pairs.keys()),
    }
    with open(run_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n=== Done ===")
    print(f"Results: {run_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", required=True, help="Comma-separated model IDs")
    parser.add_argument("--samples", type=int, default=5, help="Samples per condition")
    parser.add_argument("--tag", default="multisample")
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--print-run-dir", action="store_true",
                        help="Skriv ut run-katalogens sökväg och avsluta (för CI-setup)")
    parser.add_argument("--finalize-run", action="store_true",
                        help="Skriv auktoritativ run.json för en ihopslagen körning (CI-finalize)")
    args = parser.parse_args()

    if args.print_run_dir:
        print(args.out_dir if args.out_dir else Path("runs") / prov.build_run_id(args.tag))
        sys.exit(0)

    if args.finalize_run:
        if not args.out_dir:
            parser.error("--finalize-run kräver --out-dir")
        prov.finalize_run(
            Path(args.out_dir),
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
        )
        print(f"run.json skriven för {args.out_dir}", file=sys.stderr)
        sys.exit(0)

    models = [m.strip() for m in args.models.split(",")]
    out_dir = Path(args.out_dir) if args.out_dir else RESULTS_DIR / prov.build_run_id(args.tag)
    owner = prov.is_owner(out_dir)
    if owner:
        prov.start_run(
            out_dir,
            datasets=[prov.dataset_entry(*d) for d in DATASETS_USED],
            models=models,
            config={"samples_per_condition": args.samples},
        )
    try:
        run_multisample(models, args.samples, out_dir)
    except Exception as e:
        if owner:
            prov.finish_run(out_dir, "failed", error=e)
        raise
    if owner:
        prov.finish_run(out_dir, "completed")
