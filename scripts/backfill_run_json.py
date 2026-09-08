#!/usr/bin/env python3
"""ONE-OFF backfill (PR 4 of the restructure): write run.json for the
historical runs in runs/ and rename folders with recovered GHA run ids.

For each run folder:
- dataset version/hash: resolve the git commit at the run's timestamp,
  hash the dataset file at that commit. Every entry is marked
  "resolution": "inferred-from-git" — this tells you what *existed* at
  that commit, not what the script *read* (the v2→v3 transition window
  and dirty local working trees can misattribute).
- GHA run id: match the folder timestamp against `gh api
  .../actions/workflows/<wf>/runs?created=<date>` (head_sha lookup is
  unreliable here — the finalize jobs rebase before pushing, so the
  results commit's parent is not the run's head_sha).
- models: enumerated from the result files present.
- status: "completed" only where per-model JSONL line counts match the
  dataset's question count (or the runs.jsonl row count matches
  models x docs/personas/repeats from config.json); otherwise "failed"
  with a note.

Runs with a recovered gh<id> are renamed to <old-name>-gh<id>; the rest
keep their name and get "provenance": {"trigger": "unknown",
"recovered": false}.

Usage: python3 scripts/backfill_run_json.py [--dry-run]
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = REPO / "runs"


def _load_manifest():
    with open(REPO / "datasets" / "manifest.json", encoding="utf-8") as fh:
        return json.load(fh)


MANIFEST = _load_manifest()

# dataset file (pre-restructure path in git history) per run family
DATASET_AT_COMMIT = {
    "main": ("main-battery", "data/eval-questions.jsonl", "jsonl"),
    "censorship": ("censorship", "data/censorship-v2-questions.jsonl", "jsonl"),
    "wvs": ("wvs-swe", "data/wvs-swe/documents.json", "json"),
    "selection": ("selection-bias", "data/selection-notes.json", "json"),
}

# judge model recorded for runs that contain sleeper-judgments.jsonl
# (judge_sleeper.py default at the time; validate_wvs_swe config.json carries its own)
SLEEPER_JUDGE_DEFAULT = "mistralai/Mistral-Medium-3.5-128B"


def _read_json(path, default=None):
    """json.loads of a file, tolerating missing/corrupt files (one-off backfill:
    warn and continue rather than aborting the batch)."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"  WARNING: could not read {path}: {e}", file=sys.stderr)
        return default


def _count_lines(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    except OSError as e:
        print(f"  WARNING: could not read {path}: {e}", file=sys.stderr)
        return 0


def _models_in(path):
    """Yield model ids from a result file; tolerate unreadable/partial rows."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    row = {}
                model = row.get("model")
                if model:
                    yield model
    except OSError as e:
        print(f"  WARNING: could not read {path}: {e}", file=sys.stderr)


def git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True
    ).stdout.strip()


def gh_api(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if out.returncode != 0:
        print(
            f"  WARNING: gh api {path} failed: {out.stderr.strip()[:120]}",
            file=sys.stderr,
        )
        return {}
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        print(f"  WARNING: gh api {path} returned non-JSON", file=sys.stderr)
        return {}


def _read_config(cfg_path):
    """Read config.json; repair shard-merged files (concatenated JSON objects)."""
    try:
        text = Path(cfg_path).read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            cfg, _ = json.JSONDecoder().raw_decode(text)
            print(
                f"  NOTE: {cfg_path} held concatenated JSON; used first object",
                file=sys.stderr,
            )
            return cfg
        except json.JSONDecodeError:
            return {}


def family(tag):
    if "wvs-swe" in tag:
        return "wvs"
    if "selection-bias" in tag:
        return "selection"
    if "censorship" in tag:
        return "censorship"
    if "meta-review" in tag:
        return "meta"
    return "main"


def dataset_at_commit(fam, commit):
    """(datasets[] entry, question/doc count) for the dataset at `commit`."""
    name, old_path, kind = DATASET_AT_COMMIT[fam]
    content = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{commit}:{old_path}"], capture_output=True
    ).stdout
    if not content:
        return None, None
    sha = hashlib.sha256(content).hexdigest()
    if kind == "jsonl":
        count = content.count(b"\n")
    else:
        try:
            count = len(json.loads(content))
        except json.JSONDecodeError:
            return None, None
    version, new_path = "unknown", old_path
    for v, e in MANIFEST[name]["versions"].items():
        if e["sha256"] == sha:
            version, new_path = v, f"datasets/{e['path']}"
            break
    entry = {
        "name": name,
        "version": version,
        "path": new_path,
        "sha256": sha,
        "resolution": "inferred-from-git",
    }
    return entry, count


def models_in(folder):
    models = []
    for f in sorted(folder.glob("*.jsonl")):
        if f.name.startswith(("sleeper", "summary")):
            continue
        for m in _models_in(f):
            if m not in models:
                models.append(m)
    return models


def per_model_counts(folder):
    """{filename: row_count} for per-model result files."""
    counts = {}
    for f in sorted(folder.glob("*.jsonl")):
        if f.name.startswith(("sleeper", "summary", "runs", "review")):
            continue
        counts[f.name] = _count_lines(f)
    return counts


def assess_status(fam, folder, n_questions):
    """(status, note) — completed only when line counts match expectations."""
    notes = []
    if fam in ("main", "censorship"):
        counts = per_model_counts(folder)
        if not counts:
            return "failed", "no per-model result files"
        bad = {f: n for f, n in counts.items() if n != n_questions}
        if bad:
            return "failed", f"row counts != {n_questions} questions: {bad}"
        meta = folder / "metadata.json"
        if meta.exists():
            listed = (_read_json(meta) or {}).get("models", [])
            present = set(models_in(folder))
            missing = [m for m in listed if m not in present]
            if missing:
                return (
                    "failed",
                    f"models in metadata.json missing from results: {missing}",
                )
        if len(counts) < 3:
            notes.append(
                f"only {len(counts)} model file(s) present; possibly a partial/superseded run"
            )
        return "completed", "; ".join(notes) or None

    if fam == "meta":
        review = folder / "review.jsonl"
        if review.exists() and review.stat().st_size > 0:
            return "completed", "meta-review article review; no question dataset"
        return "failed", "no review.jsonl"

    cfg_path = folder / "config.json"
    runs_file = folder / "runs.jsonl"
    if not runs_file.exists():
        return "failed", "no runs.jsonl"
    rows = _count_lines(runs_file)
    models = models_in(folder)
    cfg = _read_config(cfg_path)
    if fam == "wvs":
        expected = len(models) * len(cfg.get("docs", [])) * len(cfg.get("personas", []))
        if rows != expected:
            return (
                "failed",
                f"runs.jsonl has {rows} rows, expected {expected} (models x docs x personas)",
            )
        return "completed", None
    # selection
    expected = len(models) * cfg.get("repeats", 0)
    if rows != expected:
        return (
            "failed",
            f"runs.jsonl has {rows} rows, expected {expected} (models x repeats)",
        )
    return "completed", None


def recover_gha_run(folder_name, ts, tag):
    """Match folder timestamp against workflow runs of that day."""
    wf = (
        "wvs-swe.yml"
        if "wvs-swe" in tag
        else ("weekly-eval.yml" if "weekly" in tag else None)
    )
    if not wf:
        return None
    data = gh_api(
        f"repos/berget-ai/berget-eval/actions/workflows/{wf}/runs?created={ts:%Y-%m-%d}"
    )
    best, best_dt = None, None
    for r in data.get("workflow_runs", []):
        created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        delta = (ts - created).total_seconds()
        if -60 <= delta <= 15 * 60 and (best_dt is None or abs(delta) < abs(best_dt)):
            best, best_dt = r, delta
    if best:
        return {
            "id": best["id"],
            "workflow": wf,
            "event": best["event"],
            "conclusion": best.get("conclusion"),
        }
    return None


def backfill(folder, dry_run):
    name = folder.name
    ts = datetime.strptime(name[:19], "%Y-%m-%dT%H-%M-%S").replace(tzinfo=timezone.utc)
    tag = name[20:]
    fam = family(tag)

    commit = git("rev-list", "-1", f"--before={ts.isoformat()}", "origin/main")
    entry, n_questions = (
        (None, None) if fam == "meta" else dataset_at_commit(fam, commit)
    )
    if entry is None and fam != "meta":
        # Dataset file absent in git at the run's timestamp (ran from a dirty
        # local tree, committed later). Fall back to the tree at the commit
        # that added the run folder — still git-derived, still inferred.
        adding = git(
            "log", "--diff-filter=A", "--format=%H", "-1", "--", f"data/results/{name}"
        )
        if adding:
            c2 = git(
                "rev-list",
                "-1",
                f"--before={git('show', '-s', '--format=%cI', adding)}",
                "origin/main",
            )
            entry, n_questions = dataset_at_commit(fam, c2)
            if entry:
                entry["note"] = (
                    "absent in git at run timestamp; "
                    f"resolved at results-commit {adding[:7]}"
                )
    datasets = [entry] if entry else []
    if n_questions is None and fam in ("main", "censorship"):
        meta = _read_json(folder / "metadata.json")
        if meta and meta.get("n_questions"):
            n_questions = meta["n_questions"]

    models = models_in(folder)
    status, note = assess_status(fam, folder, n_questions)

    judge = None
    cfg_path = folder / "config.json"
    if cfg_path.exists():
        cfg_judge = _read_config(cfg_path).get("judge")
        if cfg_judge:
            judge = {"model": cfg_judge}
    elif (folder / "sleeper-judgments.jsonl").exists():
        judge = {"model": SLEEPER_JUDGE_DEFAULT}

    gha = recover_gha_run(name, ts, tag)
    if gha:
        provenance = {
            "github_run_id": str(gha["id"]),
            "github_run_url": f"https://github.com/berget-ai/berget-eval/actions/runs/{gha['id']}",
            "workflow": gha["workflow"],
            "trigger": gha["event"],
            "conclusion": gha["conclusion"],
            "recovered": True,
        }
        new_name = f"{name}-gh{gha['id']}"
    else:
        provenance = {"trigger": "unknown", "recovered": False}
        new_name = name

    run = {
        "run_id": new_name,
        "started_at": f"{name[:10]}T{name[11:19].replace('-', ':')}+00:00",
        "status": status,
        "git_commit": commit,
        "datasets": datasets,
        "models": models,
        "judge": judge,
        "config": {},
        "n_questions": n_questions if fam in ("main", "censorship") else None,
        "provenance": provenance,
        "backfill": {
            "at": datetime.now(timezone.utc).isoformat(),
            "script": "scripts/backfill_run_json.py",
        },
    }
    if note:
        run["note"] = note

    print(f"{name}")
    print(f"  family={fam} status={status}" + (f" NOTE: {note}" if note else ""))
    print(
        f"  dataset: {(entry or {}).get('name')}/{(entry or {}).get('version')} "
        f"n={n_questions} models={len(models)}"
    )
    print(f"  provenance: {'gh' + str(gha['id']) if gha else 'unknown'} -> {new_name}")
    if not dry_run:
        try:
            (folder / "run.json").write_text(
                json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except OSError as e:
            print(f"  ERROR: could not write run.json: {e}", file=sys.stderr)
            return name, "error"
        if new_name != name:
            subprocess.run(
                ["git", "-C", str(REPO), "mv", f"runs/{name}", f"runs/{new_name}"],
                check=True,
            )
    return new_name, status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    folders = sorted(
        d for d in RUNS.iterdir() if d.is_dir() and not d.name.startswith("_")
    )
    print(f"{len(folders)} historical runs\n")
    statuses = {}
    for folder in folders:
        try:
            _, status = backfill(folder, args.dry_run)
        except Exception as e:  # noqa: BLE001 — one bad folder must not abort the batch
            print(f"  ERROR: {folder.name}: {e}", file=sys.stderr)
            status = "error"
        statuses[status] = statuses.get(status, 0) + 1
    print(f"\n{statuses}")
    if args.dry_run:
        print("DRY RUN — nothing written")


if __name__ == "__main__":
    main()
