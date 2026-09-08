# Scripts restructure plan: make the evaluation entry points obvious

**Status:** Proposed
**Goal:** A reader (or reviewer, or new contributor) must be able to answer within
seconds: *which scripts run the actual evaluations?* Today all 31 scripts sit flat
in `scripts/`, and the `run_*.py` prefix — the closest thing to a marker for "this
is an evaluation" — is shared by 7 eval runners, a shared provenance library
(`run_provenance.py`), and a repair tool (`rerun_failed.py`).

## Problem statement

An audit of `scripts/` (imports, API usage, workflow references) shows five
distinct roles currently indistinguishable by name or location:

| Role | Scripts | Calls model APIs? | Invoked by CI? |
| --- | --- | --- | --- |
| **Eval runners** (query models → produce `runs/<run_id>/`) | `run_eval.py` (main battery), `run_censorship_v2.py`, `run_wvs_swe.py`, `run_selection_bias.py`, `run_self_criticism.py`, `run_multisample_eval.py` | Yes | weekly-eval, wvs-swe, pre-publication |
| **Judging/scoring** (score an existing run; LLM judges) | `judge_sleeper.py`, `validate_wvs_swe.py` (re-judges with extra judges), `rescore_run.py` (offline), `run_judge_calibration.py` (see cross-reference §B — not a runner) | 2 of 4 | `judge_sleeper.py` in weekly-eval |
| **Analysis/reporting** (aggregate over runs) | `summarize_eval.py`, `analyze_censorship_v2.py`, `meta_review.py` | `meta_review.py` only | `summarize_eval.py` in weekly-eval |
| **Dataset generators** (write `datasets/`; frozen per version) | 9× `generate_*.py` | `generate_censorship_v2_questions.py` only | No |
| **Maintenance/infra** | `rerun_failed.py`, `rerun_empty_claude.py`, `backfill_run_json.py` (one-off, done), `eval_pilot.py` (superseded by `run_eval.py` per its own docstring), `list_models.py`, `check_manifest.py`, `validate_run.py` | Some | `list_models.py`, `check_manifest.py` |

Three structural findings make this worse than "just a lot of files":

1. **`run_provenance.py` is a library, not a script.** It is imported by all six
   provenance-writing runners but its `run_` prefix makes it look like the seventh
   evaluation. It has no meaningful `__main__` behavior.
2. **`run_censorship_v2.py` doubles as the repo's API client.** Its
   `chat_completion` function is imported by `run_wvs_swe.py`,
   `run_selection_bias.py`, `validate_wvs_swe.py`, and `meta_review.py` — so an
   evaluation runner is load-bearing infrastructure for four other scripts.
3. **Superseded scripts are indistinguishable from live ones.**
   `eval_pilot.py`, `generate_eval_questions.py` (v2 generator — v3 exists),
   `generate_new_eval_questions.py`, and `generate_sleeper_agent_questions.py`
   (still writes to the pre-restructure `data/` path) are historical artifacts
   mixed in with the generators of the current frozen dataset versions.

## Target structure

```text
scripts/
├── README.md                     # one line per script; "how to run an eval" up top
├── evals/                        # ★ THE EVALUATIONS — each produces runs/<run_id>/
│   ├── run_main_battery.py       # was run_eval.py (weekly CI; 369-question battery)
│   ├── run_censorship.py         # was run_censorship_v2.py
│   ├── run_wvs_swe.py
│   ├── run_selection_bias.py
│   ├── run_self_criticism.py
│   └── run_multisample.py        # was run_multisample_eval.py
├── judging/                      # score an existing run (LLM judges, no new run folder)
│   ├── judge_sleeper.py
│   ├── validate_wvs_swe.py
│   ├── rescore_run.py
│   └── judge_calibration.py      # was run_judge_calibration.py — samples pairs for
│                                 #   inter-judge agreement; not a runner (see §B)
├── analysis/                     # offline aggregation/reporting over runs/
│   ├── summarize_eval.py
│   ├── analyze_censorship_v2.py
│   └── meta_review.py
├── datasets/                     # generators for the frozen dataset versions
│   └── (9× generate_*.py, live ones only)
├── maintenance/                  # run repair, one-offs
│   ├── rerun_failed.py
│   ├── rerun_empty_claude.py
│   └── backfill_run_json.py      # docstring already says ONE-OFF
├── lib/                          # shared code — NOT runnable scripts
│   ├── __init__.py
│   ├── provenance.py             # was run_provenance.py
│   └── api.py                    # chat_completion extracted from run_censorship_v2.py
├── ci/                           # CI helpers, never run manually
│   ├── list_models.py
│   ├── check_manifest.py
│   └── validate_run.py
└── archive/                      # superseded, kept for provenance (CC0, cheap to keep)
    ├── eval_pilot.py
    ├── generate_eval_questions.py        # v2 generator; v3 is live
    ├── generate_new_eval_questions.py
    └── generate_sleeper_agent_questions.py  # writes pre-restructure data/ path
```

Design decisions:

- **`evals/` is the whole point.** One directory, six files, uniform `run_*.py`
  naming. Everything else is explicitly *not* an evaluation entry point.
- **Rename `run_eval.py` → `run_main_battery.py`.** The dataset is already called
  `main-battery`; the script should match. `run_eval.py` as a name claims a
  generality it doesn't have (it doesn't run censorship, WVS, …). Similarly
  `run_censorship_v2.py` → `run_censorship.py`: the `v2` belongs to the dataset
  version (`datasets/censorship/v2/`), not the runner — the runner will also run
  a future v3. **Open decision:** if the rename is considered too noisy, keep
  filenames and rely on directory placement alone. Recommendation: rename, the
  repo already absorbed a larger rename in the datasets restructure and `git mv`
  preserves history.
- **Extract `lib/api.py`.** `chat_completion` (plus `API_BASE`/`API_KEY` env
  handling) moves out of `run_censorship.py`; the four importers switch to
  `from lib.api import chat_completion`. This removes the worst coupling: today
  editing the censorship runner can silently break the WVS runner.
- **`run_provenance.py` → `lib/provenance.py`.** Name stops lying about what it is.
- **Archive, don't delete.** Consistent with the previous restructure's
  "explicitly out of scope: archiving or deleting generate scripts" — but the
  flat dump was the problem; `archive/` keeps provenance without implying
  liveness. `backfill_run_json.py` goes to `maintenance/` rather than `archive/`
  because it documents the run.json backfill methodology and is re-runnable.
- **Generators stay under `scripts/`**, not next to `datasets/`. The previous
  restructure deliberately kept them here; moving them into `datasets/` would
  blur the "datasets are inputs, never mutated" contract.
- **No new abstraction.** The runners already share a de-facto CLI convention
  (`--tag`, `--print-run-dir`, `--finalize-run`, `--out-dir`) that the workflows
  depend on. This plan does not add a unified dispatcher or base class — seven
  files with a shared `lib/` is simple enough.

## Import rewiring

Scripts already manipulate `sys.path` (`sys.path.insert(0, str(REPO / "scripts"))`),
so from any new subdirectory the pattern becomes:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # scripts/
from lib.api import chat_completion
from lib import provenance as prov
```

Import edges to rewire (found by grep, not guessed):

| Importer | Today imports | After |
| --- | --- | --- |
| `evals/run_censorship.py` | `run_provenance` | `lib.provenance` |
| `evals/run_main_battery.py` | `run_provenance`, lazy `judge_sleeper` | `lib.provenance`, `judging.judge_sleeper` |
| `evals/run_wvs_swe.py`, `evals/run_selection_bias.py` | `run_censorship_v2.chat_completion`, `run_provenance` | `lib.api`, `lib.provenance` |
| `evals/run_self_criticism.py`, `evals/run_multisample.py` | `run_provenance` | `lib.provenance` |
| `judging/validate_wvs_swe.py` | `run_censorship_v2.chat_completion` | `lib.api` |
| `analysis/meta_review.py` | `run_censorship_v2.chat_completion` | `lib.api` |
| `maintenance/rerun_failed.py`, `judging/rescore_run.py` | `run_eval` | `evals.run_main_battery` |

(An `__init__.py` in `evals/`, `judging/`, `lib/` makes these plain package
imports; no per-file path hacks beyond the single `sys.path` line.)

## Pull requests

Four PRs, each leaving the tree green. Merge in order — 1 and 2 touch the same
runner files and must not run concurrently.

### PR 1 — Create `evals/` and move the 6 runners (mechanical)

- `git mv` the 6 eval runners into `scripts/evals/` (with the two renames if
  approved).
- Fix their internal `sys.path` lines and provenance imports.
- Update **workflows**: `weekly-eval.yml`, `wvs-swe.yml`, `pre-publication.yml`
  (all reference `scripts/run_eval.py`, `scripts/run_wvs_swe.py`,
  `scripts/run_judge_calibration.py`, `scripts/run_multisample_eval.py`).
- Update **README.md** quickstart commands.

Verify:

- `grep -rn "scripts/run_eval\|scripts/run_wvs_swe\|scripts/run_multisample\|scripts/run_judge_cal\|scripts/run_censorship" .github/ README.md docs/` returns nothing.
- `python scripts/evals/run_main_battery.py --print-run-dir --tag test` prints a
  valid path (no API calls needed).
- `python scripts/evals/run_wvs_swe.py --print-run-dir --tag test` likewise.
- Smoke-run one eval with `--filter placebo` (81 calls, ~cheap) end-to-end.

### PR 2 — Extract `lib/` (api.py + provenance.py)

- Create `scripts/lib/`; move `run_provenance.py` → `lib/provenance.py`;
  extract `chat_completion` + env config from `run_censorship.py` into
  `lib/api.py` (leaving a thin re-export in the runner for one PR is acceptable
  to keep the diff reviewable, but remove it before merge).
- Rewire the 9 importer edges from the table above.

Verify:

- `python -c "import ast,sys; [ast.parse(open(f).read()) for f in ...]"` — or
  simply `python scripts/evals/run_censorship.py --help` and every other touched
  script's `--help` exits 0 (imports resolve).
- Byte-check: extracted `chat_completion` body identical to the original
  (`git show HEAD~1:scripts/run_censorship_v2.py | sed -n …` diff).

### PR 3 — Move judging/analysis/maintenance/ci + archive the superseded

- `git mv` the remaining live scripts into `judging/`, `analysis/`,
  `maintenance/`, `ci/`, `datasets/`.
- `git mv` the 4 superseded scripts into `archive/` with a one-line
  `archive/README.md` (why each is archived and what replaced it).
- Update workflow references: `weekly-eval.yml` (`judge_sleeper.py`,
  `summarize_eval.py`, `list_models.py`), `datasets-manifest.yml`
  (`check_manifest.py`, including its `paths:` trigger filter on line 13!).

Verify:

- Full-repo grep for every moved filename: `grep -rn "scripts/" .github/ README.md docs/ *.md` — only new paths appear.
- `python scripts/ci/check_manifest.py` passes locally (it is path-sensitive).
- The `datasets-manifest.yml` trigger path updated to `scripts/ci/check_manifest.py`
  — easy to miss because it's not a run step.

### PR 4 — `scripts/README.md` + docs

- `scripts/README.md`: table of every script, one line each, with the lead
  section "Run an evaluation" listing only `evals/`. State the naming
  convention: *an evaluation runner is a script in `evals/` that creates
  `runs/<run_id>/` with a `run.json` via `lib/provenance.py`.*
- Update `docs/BENCHMARK_PIPELINE.md` and the root README's script references.
- Note the convention for *future* evals: new benchmark → new file in `evals/`,
  new dataset version → generator in `datasets/`, never retroactively edit a
  frozen generator (create `generate_*_vN.py`).

Verify: a colleague test — ask someone unfamiliar with the repo to find "how do
I run the censorship eval" using only `scripts/README.md`; success = under 30 s.

## Cross-reference: what the workflows and `runs/` actually show

Checked every workflow against all 24 run folders and their `run.json`
provenance. This evidence base changes three placements in the plan.

### A. Runs per script (24 runs, as of 2026-09-08)

| Script | Runs | Which |
| --- | ---: | --- |
| `run_eval.py` (main battery) | 13 | 6× weekly CI (`weekly-gh*`) + 7 manual (`manual*`, `shuffled-*`, `expanded-sleeper`, `claude-frontier-v2`, `flash-rerun-*`) |
| `run_wvs_swe.py` | 6 | 4× weekly CI (`wvs-swe-weekly-gh*`) + 2 manual pilots |
| `run_censorship_v2.py` | 3 | all manual; one `status: failed` (crash mid-run — the try/finally lifecycle works) |
| `run_selection_bias.py` | 2 | both manual, same evening (iteration) |
| `meta_review.py` | 1 | see §C |
| `run_self_criticism.py` | **0** | dataset + provenance wiring exist; never produced a committed run |
| `run_multisample_eval.py` | **0** | CI-wired via pre-publication.yml but never persisted (see §D) |
| `run_judge_calibration.py` | **0** | cannot produce a run — not a runner (see §B) |

Only **two of four workflows** ever produced a committed run: `weekly-eval.yml`
and `wvs-swe.yml`, both on Sunday-night schedules plus manual dispatch.

### B. `run_judge_calibration.py` is not a runner — **plan corrected**

The first draft placed it in `evals/` on the strength of its name. Evidence
against:

- The run directory is **hardcoded** (`run_dir = RESULTS_DIR /
  "2026-08-08T15-08-56-expanded-sleeper"`) — it analyzes one frozen historical
  run, it doesn't create new ones.
- It writes `judge_calibration_sample.jsonl` *into an existing run folder* and
  prints manual next steps ("re-judge these pairs… calculate Cohen's kappa").
- Its pre-publication.yml job contains an explicit `# TODO: … requires
  extending run_judge_calibration.py to actually call the API` — the CI job is
  a stub that samples but never re-judges.

→ Moved to `judging/` as `judge_calibration.py` in the target structure.

### C. `meta_review.py` creates run folders but bypasses provenance — open question resolved

The first draft assumed it "produces no run.json run folder". Wrong: it created
`runs/2026-08-10T12-23-58-meta-review/` — but with **its own hardcoded naming**
(`f"{timestamp}-meta-review"`, plus a second `-meta-swap` scheme), no
`run_provenance` import, and no `run.json` at runtime. The `run.json` now
present was backfilled (`datasets: []`, `trigger: "unknown"`,
`recovered: false`) — precisely the provenance hole the run.json contract
exists to close.

→ Stays in `analysis/` (it studies our eval, not model behavior), but PR 3 adds
one behavior fix: route its folder creation through `lib/provenance.py` so
future meta-reviews are self-describing. Flagged in the diff as a deliberate
behavior change, not a mechanical move.

### D. pre-publication.yml has run — and persisted nothing

`gh run list` shows two dispatches on 2026-08-09 (one success after a 1h17m
cancellation). Yet **no placebo/multisample/calibration folder exists in
`runs/`, and none ever existed in git history** — the finalize job's
`git add runs/` evidently found nothing new. Contributing causes: the
calibration job is a stub (§B), and multisample results were uploaded as
artifacts but never landed in a committed run folder.

→ Consequences for this plan: `run_multisample_eval.py` and
`run_self_criticism.py` remain in `evals/` (both are correctly wired
provenance runners), but `scripts/README.md` (PR 4) must mark them
**unexercised** so a reader doesn't cite infrastructure that has never produced
data. Fixing the pre-publication persistence path is out of scope here but
should be a follow-up issue before the next pre-publication data collection.

### E. Workflow reference surface (what PRs 1–3 must update)

| Workflow | Script references |
| --- | --- |
| `weekly-eval.yml` | `list_models.py`, `run_eval.py` (×3: `--print-run-dir`, run, `--finalize-run`), `judge_sleeper.py`, `summarize_eval.py` |
| `wvs-swe.yml` | `list_models.py`, `run_wvs_swe.py` (×3, same pattern) |
| `pre-publication.yml` | `run_eval.py` (×2), `run_judge_calibration.py`, `run_multisample_eval.py` |
| `datasets-manifest.yml` | `check_manifest.py` — **including the `on.pull_request.paths:` trigger filter**, which is not a run step and is easy to miss |

## Explicitly out of scope

- Unifying the runner CLIs into a single `run` command or shared base class.
  The convention is already consistent where CI needs it; a dispatcher adds a
  layer without removing one.
- Changing what any evaluation *measures* (question sets, judges, scoring).
- Deleting archived scripts.
- Touching `datasets/`, `runs/`, or `data/` (previous restructure's domain).

## Decisions log

| Decision | Choice | Rationale |
| --- | --- | --- |
| Marker for "this is an eval" | `evals/` directory, not naming prefix | Prefixes already collided (`run_provenance`); a directory is unmissable in `ls` and in CI logs |
| `run_provenance.py` | Move to `lib/provenance.py` | It is imported by 6 runners and runs nothing itself; the `run_` name was actively misleading |
| `chat_completion` home | New `lib/api.py` | 4 scripts import it from an eval runner; runner edits currently risk breaking unrelated evals |
| Superseded scripts | `archive/`, not deletion | Keeps provenance of how current frozen datasets were produced; zero cost |
| `run_judge_calibration.py` placement | `judging/judge_calibration.py`, not `evals/` | Cross-reference §B: hardcoded input run, no provenance, workflow TODO says it never calls the API |
| `meta_review.py` provenance | Keep in `analysis/` + adopt `lib/provenance.py` in PR 3 | Cross-reference §C: it already creates run folders with ad-hoc naming; closing the hole is one small behavior change |
| Generators under `scripts/datasets/` | Keep out of `datasets/` | Preserves "datasets are versioned inputs, never mutated" boundary |
| Filenames inside `evals/` | Rename to match dataset names | `run_eval.py` overclaims; `run_censorship_v2.py` couples runner name to dataset version — **pending approval** |

## Open questions

1. Approve the two renames (`run_eval.py` → `run_main_battery.py`,
   `run_censorship_v2.py` → `run_censorship.py`), or directory-only moves?
2. ~~`meta_review.py` placement~~ — **resolved by evidence** (cross-reference
   §C): it creates run folders but bypasses provenance; placed in `analysis/`
   with a provenance fix in PR 3.
3. `eval_pilot.py` — archive as proposed, or does anyone still use it for
   smoke-testing new questions before a dataset version is cut? (If yes, it
   belongs in `maintenance/` instead.)
4. Should PR 3's `meta_review.py` provenance fix also record the *reviewed run*
   as a dataset entry (sha256 of the judgments file it reads)? That would make
   meta-review findings citable under the same convention as everything else,
   at the cost of a slightly larger behavior change.
