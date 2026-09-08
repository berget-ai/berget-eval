# Datasets — the versioning contract

`datasets/` holds every versioned input to the evaluation: question batteries,
stimulus documents/notes, and all prompts sent to any model (system, persona,
summary, and judge prompts). Together with `runs/<run_id>/run.json`, this
directory lets anyone answer, for any published finding: *which exact dataset
version produced this run, which models were queried, and which code ran* —
without reading Python source.

## Layout

```text
datasets/
├── manifest.json             # registry: every stimulus file + sha256
├── main-battery/
│   ├── v1/eval-questions.jsonl   (69 questions)
│   ├── v2/eval-questions.jsonl   (99 questions)
│   ├── v3/eval-questions.jsonl   (369 questions)
│   └── prompts.json              # system prompts (unversioned)
├── censorship/
│   ├── v2/questions.jsonl        (210 questions — see note below)
│   └── prompts.json
├── wvs-swe/
│   ├── v1/documents.json
│   ├── v2/documents.json         (length-matched)
│   ├── prompts.json              # personas + rewrite/summary templates
│   └── DESIGN.md                 # methodology (documentation, not stimulus)
├── selection-bias/
│   ├── v1/notes.json
│   └── prompts.json
├── self-criticism/
│   ├── v1/questions.jsonl
│   └── prompts.json
└── judges/                     # all LLM-judge prompts (unversioned)
    ├── sleeper-judge.{system,prompt}.md
    ├── wvs-swe-judge.{system,prompt}.md
    └── selection-bias-judge.{system,prompt}.md
```

## Dataset cards

Each dataset directory has its own README card with purpose, schema, version
history, methodology, and known limitations:

- [main-battery](main-battery/README.md) — the 369-question main battery
- [censorship](censorship/README.md) — the 210-question censorship battery
- [wvs-swe](wvs-swe/README.md) — WVS values-survival stimulus documents
- [selection-bias](selection-bias/README.md) — theme-selection workshop notes
- [self-criticism](self-criticism/README.md) — vendor self-criticism battery
- [judges](judges/README.md) — all LLM-judge prompts

> **Note:** the censorship battery starts at **v2**. No v1 was ever versioned
> as a dataset (the v1 run's length-truncation flaw was discovered before
> versioning existed), so there is no `censorship/v1/` to look for.

## The rules

1. **Versioned files (`<name>/v<N>/…`) are never mutated in place.** Changing
   questions or stimulus material means creating a **new version directory**
   (`v4/`), registering it in `manifest.json` (sha256, count, created date,
   changelog), and pointing the runner at it.
2. **Unversioned stimulus files** (`prompts.json`, `judges/*.md`) may evolve,
   but every change must update the file's sha256 in `manifest.json`
   **in the same PR**.
3. **CI enforces both rules** (`.github/workflows/datasets-manifest.yml` →
   `scripts/check_manifest.py`): any PR touching `datasets/` fails if a
   registered file's hash doesn't match, if a file is unregistered, or if a
   versioned file is modified/deleted in place.
4. Version directories (`v1/`, `v2/`) are for humans; **sha256 is the
   integrity layer**, recorded in the manifest and in every run's `run.json`.

## How to add a new dataset version

```bash
mkdir datasets/main-battery/v4
# write the new file, then register it in manifest.json:
#   path, sha256 (shasum -a 256), questions count, created date, changelog
# point the runner's QUESTIONS_PATH at v4
# open the PR — .github/workflows/datasets-manifest.yml must go green
```

## Citation convention

Every finding should be citable back to its exact inputs:

```text
berget-eval @ <commit>, run <run_id>, <dataset> <version> (sha256:…)
```

e.g. `berget-eval @ 70294c8, run 2026-09-06T23-14-27-weekly-gh34066312037,
main-battery v3 (sha256:2325e32e2b32…)`.

`summarize_eval.py` prints this string per run and embeds it in `summary.md`,
so the correct citation is copy-pasteable rather than hand-assembled. Each
run's `run.json` carries the full provenance: every stimulus file with its
sha256, models, judge, config, git commit, and how the run was triggered
(GitHub Actions run id or local).
