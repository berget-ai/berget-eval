#!/usr/bin/env python3
"""Run judge calibration: compare Mistral Small vs Mistral Medium on same pairs.

This validates whether our judge rotation (Small for most models, GLM-4.7
for Mistral models) produces consistent rankings. If Small and Medium
rank models differently, our cross-model comparisons are confounded.

Usage:
    python3 run_judge_calibration.py --sample-size 50
"""
import argparse
import json
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
RESULTS_DIR = DATA / "results"

def load_judgments(run_dir):
    """Load all sleeper judgments from a run."""
    jf = run_dir / "sleeper-judgments.jsonl"
    if not jf.exists():
        return []

    judgments = []
    with open(jf) as f:
        for line in f:
            judgments.append(json.loads(line))
    return judgments

def run_calibration(sample_size=50, seed=42):
    """Sample judgments and re-judge with both Mistral Small and Medium."""
    # Use run 3 as source
    run_dir = RESULTS_DIR / "2026-08-08T15-08-56-expanded-sleeper"
    judgments = load_judgments(run_dir)

    if not judgments:
        print(f"No judgments found in {run_dir}")
        return

    print(f"Loaded {len(judgments)} judgments from {run_dir.name}")

    # Sample random pairs
    random.seed(seed)
    sampled = random.sample(judgments, min(sample_size, len(judgments)))

    print(f"Sampled {len(sampled)} pairs for calibration")
    print()

    # For each sampled pair, we need the original responses
    # This requires loading the raw results files
    calibration_data = []

    for j in sampled:
        pair_id = j.get("pair_id")
        model = j.get("model")
        region = j.get("trigger_region")

        # Load the original result
        model_slug = model.replace("/", "-").replace(".", "-")
        result_file = run_dir / f"{model_slug}.jsonl"

        if not result_file.exists():
            continue

        baseline_resp = None
        trigger_resp = None

        with open(result_file) as f:
            for line in f:
                r = json.loads(line)
                if r.get("pair_id") == pair_id:
                    if r.get("trigger_region") == "neutral":
                        baseline_resp = r.get("response")
                    elif r.get("trigger_region") == region:
                        trigger_resp = r.get("response")

        if baseline_resp and trigger_resp:
            calibration_data.append({
                "pair_id": pair_id,
                "model": model,
                "region": region,
                "baseline_response": baseline_resp,
                "trigger_response": trigger_resp,
                "original_judgment": j.get("judgment"),
            })

    print(f"Found {len(calibration_data)} pairs with both responses")

    # Save for manual or automated re-judging
    output_file = run_dir / "judge_calibration_sample.jsonl"
    with open(output_file, "w") as f:
        for item in calibration_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nSaved calibration sample: {output_file}")
    print("\nNext steps:")
    print("1. Re-judge these pairs with Mistral Medium (128B)")
    print("2. Compare with original Mistral Small (24B) judgments")
    print("3. Calculate Cohen's kappa or simple agreement rate")
    print("4. Report in article whether judge choice affects model rankings")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_calibration(args.sample_size, args.seed)
