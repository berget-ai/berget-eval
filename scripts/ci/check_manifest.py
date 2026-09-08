#!/usr/bin/env python3
"""CI gate: datasets/ integrity against datasets/manifest.json.

Checks:
  1. Every versioned file registered in the manifest exists and matches
     its sha256 (and question/document count where recorded).
  2. Every unversioned stimulus file (prompts, judge prompts) matches its
     registered sha256 — changing one requires a manifest update in the
     same PR, so the registry never silently desyncs.
  3. Every tracked file under datasets/ is registered in the manifest
     (documentation files excluded: manifest.json, README.md, DESIGN.md).
  4. With --base <ref>: any MODIFIED or DELETED path under datasets/*/v<N>/
     fails — versioned datasets are never mutated in place; add a new
     version directory instead.

Usage:
  python3 scripts/ci/check_manifest.py [--base <git-ref>]
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO / "datasets" / "manifest.json"

# Documentation files under datasets/ that are not stimulus material.
DOC_FILES = {"manifest.json", "README.md", "DESIGN.md"}

VERSIONED_RE = re.compile(r"^datasets/[^/]+/v\d+/")


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True
    ).stdout.strip()


def load_manifest():
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"ERROR: could not read {MANIFEST_PATH}: {e}")


def registered_paths(manifest):
    """All dataset-relative paths registered in the manifest."""
    paths = {}
    for ds_name, ds in manifest.get("datasets", {}).items():
        for ver, entry in ds.get("versions", {}).items():
            paths[entry["path"]] = ("versioned", ds_name, ver, entry)
    for rel, entry in manifest.get("unversioned_files", {}).items():
        paths[rel] = ("unversioned", None, None, entry)
    return paths


def check_hashes(manifest, failures):
    registered = registered_paths(manifest)
    for rel, (kind, ds_name, ver, entry) in sorted(registered.items()):
        path = REPO / "datasets" / rel
        label = f"{ds_name} {ver}" if kind == "versioned" else rel
        if not path.exists():
            failures.append(f"{label}: registered file missing: datasets/{rel}")
            continue
        actual = sha256_file(path)
        if actual != entry.get("sha256"):
            failures.append(
                f"{label}: sha256 mismatch for datasets/{rel}\n"
                f"    manifest: {entry.get('sha256')}\n"
                f"    on disk:  {actual}\n"
                "    Versioned datasets must never be mutated in place — add a new "
                "version directory. Unversioned prompt files require a manifest "
                "update in the same PR."
            )
            continue
        # count check where the manifest records one
        count_key = next(
            (k for k in ("questions", "documents", "notes") if k in entry), None
        )
        if count_key:
            n = count_entries(path)
            if n is None:
                failures.append(f"{label}: could not count entries in {path}")
                continue
            if n != entry[count_key]:
                failures.append(
                    f"{label}: {count_key} count {n} != manifest's {entry[count_key]}"
                )
        print(f"  ok {label} ({rel})")


def count_entries(path):
    """Line count (jsonl) or array length (json); None on read/parse error."""
    try:
        with open(path, encoding="utf-8") as fh:
            if path.name.endswith(".jsonl"):
                return sum(1 for line in fh if line.strip())
            return len(json.load(fh))
    except (OSError, json.JSONDecodeError):
        return None


def check_unregistered(manifest, failures):
    registered = set(registered_paths(manifest))
    tracked = git("ls-files", "datasets/").splitlines()
    for rel in tracked:
        rel = rel.removeprefix("datasets/")
        if Path(rel).name in DOC_FILES or rel in registered:
            continue
        failures.append(
            f"datasets/{rel}: tracked file not registered in manifest.json "
            "(add it, or it does not belong under datasets/)"
        )


def check_no_in_place_mutation(base, failures):
    out = git("diff", "--name-status", f"{base}...HEAD", "--", "datasets/")
    for line in out.splitlines():
        if not line.strip():
            continue
        status, _, path = line.partition("\t")
        if status.startswith(("M", "D")) and VERSIONED_RE.match(path):
            failures.append(
                f"{path}: versioned dataset file {status} relative to {base} — "
                "never mutate in place; create a new version directory "
                "(e.g. v4/) and register it in manifest.json"
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        default=None,
        help="git ref to diff against for in-place-mutation check",
    )
    args = ap.parse_args()

    manifest = load_manifest()
    failures = []

    print("Check 1+2: sha256 of every registered file")
    check_hashes(manifest, failures)

    print("\nCheck 3: no unregistered files under datasets/")
    check_unregistered(manifest, failures)

    if args.base:
        print(f"\nCheck 4: no in-place mutation of versioned files vs {args.base}")
        check_no_in_place_mutation(args.base, failures)

    if failures:
        print(f"\nFAIL — {len(failures)} problem(s):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)
    print("\nPASS — datasets/ is in sync with manifest.json")


if __name__ == "__main__":
    main()
