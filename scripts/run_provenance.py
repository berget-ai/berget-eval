#!/usr/bin/env python3
"""Shared run-folder naming and run.json provenance for all runners.

Single-writer principle: runner scripts (via this module) build run folder
names and write run.json. Workflows pass env and flags only — GitHub context
(GITHUB_RUN_ID, GITHUB_WORKFLOW, ...) is ambient in Actions — and contain no
naming logic of their own, so the scheme cannot drift between two
implementations.

Run folder naming:  <UTC timestamp>-<tag>-<origin suffix>
  GitHub Actions:   2026-09-14T23-14-27-weekly-gh12345678901
  Local/manual:     2026-09-14T10-00-00-manual-local-a1b2c3d

run.json lifecycle: written with status "running" at run start, flipped to
"completed" (with completed_at) or "failed" (with error) at exit. A run
folder without status "completed" is partial and must not enter aggregates
(enforced by validate_run.py).
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True
    ).stdout.strip()


def git_commit():
    return _git("rev-parse", "HEAD")


def git_dirty():
    return bool(_git("status", "--porcelain"))


def origin_suffix():
    """gh<run_id> in GitHub Actions, else local-<git short sha>."""
    run_id = os.environ.get("GITHUB_RUN_ID")
    if run_id:
        return f"gh{run_id}"
    return f"local-{ _git('rev-parse', '--short', 'HEAD') }".replace(" ", "")


def build_run_id(tag, now=None):
    now = now or datetime.now(timezone.utc)
    return f"{now.strftime('%Y-%m-%dT%H-%M-%S')}-{tag}-{origin_suffix()}"


def provenance():
    """GitHub context when run in Actions, local context otherwise."""
    run_id = os.environ.get("GITHUB_RUN_ID")
    if run_id:
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        return {
            "github_run_id": run_id,
            "github_run_url": f"{server}/{repo}/actions/runs/{run_id}",
            "workflow": os.environ.get("GITHUB_WORKFLOW"),
            "trigger": os.environ.get("GITHUB_EVENT_NAME"),
        }
    return {"trigger": "local", "git_dirty": git_dirty()}


def dataset_entry(name, version, rel_path):
    """One datasets[] entry: a file sent to a model, hashed as read."""
    return {
        "name": name,
        "version": version,
        "path": rel_path,
        "sha256": sha256_file(REPO / rel_path),
        "resolution": "recorded",
    }


def start_run(out_dir, *, datasets, models, judge=None, config=None, n_questions=None):
    """Write run.json with status 'running'. Returns the run dict."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run = {
        "run_id": out_dir.name,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "git_commit": git_commit(),
        "datasets": datasets,
        "models": models,
        "judge": judge,
        "config": config or {},
        "n_questions": n_questions,
        "provenance": provenance(),
    }
    _write(out_dir, run)
    return run


def finish_run(out_dir, status, error=None):
    """Flip run.json to completed/failed. Called in try/finally by runners."""
    out_dir = Path(out_dir)
    path = out_dir / "run.json"
    if not path.exists():
        return
    try:
        run = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        # Called from finally blocks; never mask the original exception.
        print(f"warning: could not update {path}: {e}", file=sys.stderr)
        return
    run["status"] = status
    if status == "completed":
        run["completed_at"] = datetime.now(timezone.utc).isoformat()
    if error is not None:
        run["error"] = str(error)
    _write(out_dir, run)


def is_owner(out_dir):
    """True if this process owns the run lifecycle (no run.json yet).

    CI matrix shards run with --out-dir into a folder that has no run.json on
    their fresh checkout — each shard writes a local run.json that never
    reaches the repo (the artifact merge only copies *.jsonl); the finalize
    job then calls --finalize-run to write the authoritative one.
    """
    return not (Path(out_dir) / "run.json").exists()


def models_from_jsonl(out_dir):
    """Model ids found in a run folder, from the first row of each result file."""
    models = []
    for f in sorted(Path(out_dir).glob("*.jsonl")):
        if f.name.startswith(("sleeper", "runs")):
            continue
        for model in _models_in_file(f):
            if model not in models:
                models.append(model)
    # runs.jsonl (wvs-swe / selection-bias) holds all models in one file
    runs_file = Path(out_dir) / "runs.jsonl"
    if runs_file.exists():
        for model in _models_in_file(runs_file):
            if model not in models:
                models.append(model)
    return models


def _models_in_file(path):
    """Yield model ids from a result file; tolerate unreadable/partial rows."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    row = {}  # partial/corrupt row (crashed run)
                model = row.get("model")
                if model:
                    yield model
    except OSError:
        return


def finalize_run(out_dir, *, datasets, judge=None, config=None):
    """Write the authoritative run.json for a CI-merged run folder.

    Used in workflow finalize jobs after per-model artifacts are merged:
    run_id and started_at come from the folder name, models from the result
    files present, provenance from ambient GitHub env vars.
    """
    out_dir = Path(out_dir)
    run_id = out_dir.name
    started_at = None
    ts = run_id[:19]  # "2026-09-08T08-00-00"
    if "T" in ts:
        date, time_part = ts.split("T", 1)
        started_at = f"{date}T{time_part.replace('-', ':')}+00:00"
    run = {
        "run_id": run_id,
        "started_at": started_at,
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "datasets": datasets,
        "models": models_from_jsonl(out_dir),
        "judge": judge,
        "config": config or {},
        "provenance": provenance(),
    }
    _write(out_dir, run)
    return run


def _write(out_dir, run):
    (Path(out_dir) / "run.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
