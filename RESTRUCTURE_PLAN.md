# Restructure plan: versioned datasets + self-describing runs

**Status:** Implemented (PRs #11–#15 + docs PR)
**Goal:** Make the repository independently verifiable. A researcher must be able to
answer, for any published finding: *which exact dataset version produced this run,
which models were queried, which code ran, and which automation triggered it* —
without reading Python source.

## Principles

1. **`datasets/`** holds all versioned inputs (prompts + stimulus material). Nothing here
   is ever mutated in place; a change creates a new version directory.
2. **`runs/`** holds only outputs. One folder per run, self-describing via `run.json`.
3. Version directories (`v1/`, `v2/`) are for humans; **sha256 hashes are the integrity
   layer** recorded in the dataset manifest and in every `run.json`.
4. Prompt fragments currently hardcoded in scripts (system prompts, persona prompts,
   judge prompts) are extracted into the dataset directories so `datasets/` alone
   specifies everything sent to any model.

## Target structure

```text
berget-eval/
├── datasets/                        # versioned inputs — the source of truth
│   ├── manifest.json                # registry: dataset → versions → sha256 + changelog
│   ├── README.md                    # the versioning contract
│   ├── main-battery/
│   │   ├── v1/eval-questions.jsonl  # was data/eval-questions-v1-lang.jsonl (69 q)
│   │   ├── v2/eval-questions.jsonl  # was data/eval-questions-v2.jsonl (99 q)
│   │   └── v3/eval-questions.jsonl  # was data/eval-questions.jsonl (369 q)
│   ├── censorship/
│   │   └── v2/questions.jsonl       # was data/censorship-v2-questions.jsonl (210 q)
│   ├── wvs-swe/
│   │   ├── v1/documents.json        # was data/wvs-swe/documents.v1.json
│   │   ├── v2/documents.json        # was data/wvs-swe/documents.json (length-matched)
│   │   ├── prompts.json             # ← extracted from run_wvs_swe.py (personas, templates, judge prompt)
│   │   └── DESIGN.md                # was data/wvs-swe/DESIGN.md (methodology stays with the dataset)
│   ├── selection-bias/
│   │   ├── v1/notes.json            # was data/selection-notes.json
│   │   └── prompts.json             # ← extracted from run_selection_bias.py
│   ├── self-criticism/
│   │   └── v1/questions.jsonl       # was data/self-criticism-questions.jsonl
│   └── judges/
│       └── sleeper-judge.md         # ← extracted from judge_sleeper.py
├── runs/                            # outputs only (was data/results/)
│   ├── _summary/                    # cross-run roll-ups (eval-summary.json/png/md from summarize_eval.py)
│   └── <run_id>/                    # e.g. 2026-09-06T23-14-27-weekly-gh12345678901
│       ├── run.json                 # provenance metadata (see below)
│       ├── <model>.jsonl
│       └── summary.json / runs.jsonl / …
├── data/                            # non-eval material (unchanged this round)
│   └── (fine-tuning JSONL, wordlists, raw corpora)
└── scripts/
```

## Run folder naming

`<UTC timestamp>-<tag>-<origin suffix>` — date-first for sorting, tag for humans,
origin for provenance:

- GitHub Actions: `2026-09-14T23-14-27-weekly-gh12345678901`
  (`github.run_id`, deep-links to `…/actions/runs/12345678901`)
- Local/manual: `2026-09-14T10-00-00-manual-local-a1b2c3d` (git short SHA)

The **runner script is the single writer**: it builds the run folder name and writes
`run.json`, reading `GITHUB_RUN_ID`/workflow name from env vars when present and
falling back to `local-<git short sha>` otherwise. Workflows contain no naming logic
of their own — they just run the script (two implementations of the scheme would
drift).

## `datasets/manifest.json`

```json
{
  "main-battery": {
    "description": "Swedish language/values/censorship/sleeper battery",
    "versions": {
      "v3": {
        "path": "main-battery/v3/eval-questions.jsonl",
        "sha256": "…",
        "questions": 369,
        "created": "2026-08-16",
        "changelog": "Added placebo controls (9 questions)"
      }
    }
  }
}
```

## `runs/<run_id>/run.json`

Written by the runner script at run start, updated at run end:

```json
{
  "run_id": "2026-09-06T23-14-27-weekly-gh12345678901",
  "started_at": "2026-09-06T23:14:27Z",
  "status": "completed",
  "completed_at": "2026-09-06T23:51:02Z",
  "git_commit": "557e7ca…",
  "datasets": [
    { "name": "main-battery", "version": "v3",
      "path": "datasets/main-battery/v3/eval-questions.jsonl", "sha256": "…",
      "resolution": "recorded" },
    { "name": "main-battery/prompts", "version": "—",
      "path": "datasets/main-battery/prompts.json", "sha256": "…",
      "resolution": "recorded" },
    { "name": "judges/sleeper", "version": "—",
      "path": "datasets/judges/sleeper-judge.md", "sha256": "…",
      "resolution": "recorded" }
  ],
  "models": ["google/gemma-4-31B-it", "…"],
  "judge": { "model": "mistralai/mistral-small-3-2-24b-instruct-2506" },
  "config": { "temperature": 0 },
  "provenance": {
    "github_run_id": "12345678901",
    "github_run_url": "https://github.com/berget-ai/berget-eval/actions/runs/12345678901",
    "workflow": "weekly-eval.yml",
    "trigger": "schedule"
  }
}
```

Field semantics:

- **`datasets[]` lists every file sent to any model** — questions, persona/template
  prompts, judge prompts — each with its own sha256. The judge prompt and persona
  prompts are part of the stimulus (in bias evals they often *are* the
  manipulation), so an unhashed prompt would leave the provenance chain with a hole
  exactly where it matters most.
- **`resolution`**: `"recorded"` when the runner hashed the file it actually opened
  (all new runs); `"inferred-from-git"` for backfilled historical runs where the
  dataset version was reconstructed from git history and may be wrong.
- **`status`**: `"running"` at start, flipped to `"completed"` (with `completed_at`)
  or `"failed"` (with `error`) at exit — the runner's main body is wrapped in
  try/finally so even crashes flip it. A run folder without `status: "completed"`
  is partial and must not enter aggregates.

## Pull requests

The work lands as **six PRs**, each leaving the tree fully working — every runner
always points at paths that exist — so each is independently reviewable and
revertable. (The earlier "steps 1–6 in a single PR" constraint only requires the
*file moves and the path-reference updates* to be atomic, not the new behavior;
PR 1 below is exactly that atomic unit.)

**Merge order:** PR 1 first. PRs 2, 3, 5 may start once PR 1 merges, but PRs 2 and 3
both edit the runner scripts and must be sequenced (2 before 3) to avoid conflicts.
PR 4 requires PR 3 (the `run.json` schema and the extended validator must exist).
PR 6 last, so docs describe the final state.

### PR 1 — Layout migration: `data/` → `datasets/` + `runs/` (mechanical, no behavior change)

- Reorganize via `git mv` (preserves history): `data/` prompts → `datasets/<name>/vX/`,
  `data/results/` → `runs/`.
- Update **every** script and workflow reference to the new paths so all runners keep
  working unchanged: `summarize_eval.py` (roll-up outputs move from `data/` to
  `runs/_summary/`), `rescore_run.py`, `rerun_failed.py`, `rerun_empty_claude.py`,
  `run_multisample_eval.py`, `run_judge_calibration.py`, `validate_run.py`,
  `validate_wvs_swe.py`, `meta_review.py`, `eval_pilot.py`, `run_self_criticism.py`,
  `analyze_censorship_v2.py`, the runners, and the generate scripts.
- Write `datasets/manifest.json` with sha256 for every version.

Verify:

- `git log --follow datasets/main-battery/v3/eval-questions.jsonl` shows full history.
- `shasum -a 256` spot-checks match the manifest.
- The literal-path grep is **insufficient** — most scripts build paths via a `DATA`
  constant (e.g. `DATA / "eval-questions.jsonl"`), which a literal grep misses (it
  currently finds 17 hits in 9 files while ~13 more references slip through,
  including `run_self_criticism.py`). Verify with both:

  ```bash
  grep -rn "data/results\|data/eval-questions\|data/censorship\|data/wvs-swe\|data/selection-notes\|data/self-criticism" scripts/ .github/
  grep -rn 'parent\.parent / "data"\|DATA / "' scripts/
  ```

- Smoke-run each runner (`run_eval.py`, `run_wvs_swe.py`, `run_censorship_v2.py`,
  `run_self_criticism.py`, `run_selection_bias.py`, `run_multisample_eval.py`) with
  a 1-question filter.

### PR 2 — Extract prompt fragments from code

- Extract system/persona/judge prompts into `datasets/*/prompts.json` and
  `datasets/judges/`; update `run_wvs_swe.py`, `run_selection_bias.py`,
  `judge_sleeper.py`, `run_eval.py`, `run_censorship_v2.py` to load them from disk.

Verify: prompts on disk byte-match what the scripts previously sent (diff extracted
text against the old constants).

### PR 3 — Self-describing runs: naming + `run.json`

- Update runner scripts to resolve the origin suffix (`gh$GITHUB_RUN_ID` else
  `local-<sha>`), build the run folder name, and write `run.json` — including the
  `status` lifecycle (`running` → `completed`/`failed` via try/finally) and hashing
  every prompt/judge file loaded into `datasets[]`. The runner script is the single
  writer; workflows just pass env.
- Extend `validate_run.py` to flag any run folder where `status != "completed"` or
  per-model JSONL line counts don't match the dataset's question count.

Verify: `python scripts/run_eval.py --filter placebo --tag restructure-test` locally
produces a correctly named folder with valid `run.json`; smoke-run the other runners
with a 1-question filter; `validate_run.py` flags a doctored partial run.

### PR 4 — Backfill + rename the 24 historical runs

- One-off backfill script writing `run.json` for each existing run:
  - dataset version/hash: resolve the git commit at the run's timestamp, hash the
    dataset file at that commit — and mark every entry
    `"resolution": "inferred-from-git"` (this tells you what *existed* at that
    commit, not what the script *read*; runs from the v2→v3 transition window and
    local runs with dirty working trees can be misattributed, so backfilled hashes
    must never be presented with recorded authority);
  - GHA run id: find the commit that added the run folder, then
    `gh api "repos/berget-ai/berget-eval/actions/runs?head_sha=<sha>"`;
  - models: enumerate the `<model>.jsonl` files present;
  - status: set `"status": "completed"` only where per-model JSONL line counts
    match the dataset's question count; otherwise `"failed"` / partial with a note.
- Rename existing run folders to the new scheme where a `gh<id>` was recovered:
  `<old-name>-gh<run_id>`; runs without a recoverable id keep their name and get
  `"provenance": {"trigger": "unknown", "recovered": false}` in `run.json`.

Review strategy: review the backfill script in full; the 24 `run.json` files are
generated output — spot-check 3 against `git log` and the Actions UI, then require
`validate_run.py` (from PR 3) to pass on all 24.

### PR 5 — CI enforcement of the manifest

- Add a workflow that, on PRs touching `datasets/`, verifies every file's sha256
  against `manifest.json` and fails if a tracked dataset file changed without a new
  version directory. This turns "never mutate in place" from a social rule into a
  checked one — without it the manifest will silently desync.
- Independent of PRs 2–4; can land any time after PR 1.

Verify: open a test PR flipping a byte in a dataset file; CI must go red.

### PR 6 — Docs + citation convention

- Update `README.md`, `docs/BENCHMARK_PIPELINE.md` (the ⚠ "prompt fragments in code"
  box should disappear), add `datasets/README.md` describing the versioning contract
  (how to add a new version, never mutate in place). The contract must also:
  - note that censorship starts at `v2` (no v1 was ever versioned as a dataset), so
    external readers don't hunt for a nonexistent `censorship/v1/`;
  - define the **citation convention** that closes the loop from publication to
    provenance (the actual deliverable of this restructure):

    ```text
    berget-eval @ <commit>, run <run_id>, <dataset> <version> (sha256:…)
    ```

    e.g. `berget-eval @ 557e7ca, run 2026-09-06T23-14-27-weekly-gh12345678901,
    main-battery v3 (sha256:9f2c…)`. Have `summarize_eval.py` emit this string per
    run so the correct citation is copy-pasteable rather than hand-assembled.

## Explicitly out of scope (this round)

- English translation of README/docs (separate task).
- `data/` fine-tuning files and wordlists (training/reference material, not eval inputs).
- Archiving or deleting `generate_*.py` scripts.

## Decisions log

| Decision | Choice | Rationale |
| --- | --- | --- |
| Version scheme | `v1/v2/v3` dirs + sha256 in manifest | Researchers cite "main-battery v3"; hashes are the integrity layer |
| `data/results/` → `runs/` | Rename | All references touched anyway (14 literal + more via the `DATA` path constant); clearer semantics |
| GHA identifier | `run_id`, not `run_number` | Globally unique; deep-links to the Actions run |
| Existing 24 runs | Rename with recovered `gh<id>` | Nothing external references these paths yet; uniformity wins |
| Prompts/judge files in `run.json` | Per-file sha256 in `datasets[]` | Prompts are part of the stimulus; manifest-hash alone can desync from what ran |
| Backfilled dataset hashes | `"resolution": "inferred-from-git"` | Git-at-timestamp tells what existed, not what ran; never present inferred hashes as recorded |
| Run lifecycle | `status` + `completed_at`, enforced by `validate_run.py` | This repo's history (rerun_failed, rerun_empty_claude) shows runs die mid-way; partial runs must not enter aggregates |
| `run.json` writer | Runner script only, workflows pass env | Two implementations of the naming scheme would drift |
| Manifest integrity | CI check on PRs touching `datasets/` | A social "never mutate" rule will desync; make it mechanical |
| Cross-run summaries | `runs/_summary/` | `data/` holds inputs; roll-ups are outputs (principle 2) |
| PR split | 6 PRs; only move + path updates are atomic (PR 1) | Keeps the tree green at every merge while isolating rename noise from behavior changes; each PR is reviewable on its own terms (mechanical / byte-verifiable / behavioral / generated / CI / docs) |
| Served-model versioning | Not recorded | The gateway serves unversioned models; the drift ambiguity is accepted |
