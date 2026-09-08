# scripts/

**Run an evaluation → everything in `evals/`.** An evaluation runner is a
script in `evals/` that queries models and creates `runs/<run_id>/` with a
`run.json` written via `lib/provenance.py`. Nothing outside `evals/` does
that.

## evals/ — the evaluations

| Script | Benchmark | Dataset | Status |
| --- | --- | --- | --- |
| `run_main_battery.py` | Swedish language/values/censorship/sleeper battery (369 q) | `main-battery` | **Weekly CI** (`weekly-eval.yml`) |
| `run_wvs_swe.py` | Do Swedish values survive a rewrite, and can a persona fix it | `wvs-swe` | **Weekly CI** (`wvs-swe.yml`) |
| `run_censorship.py` | Three-class censorship response across 5 modules | `censorship` | Manual |
| `run_selection_bias.py` | Whose notes survive the fixed-bullet summary | `selection-bias` | Manual |
| `run_self_criticism.py` | Can models criticise their own maker | `self-criticism` | Manual — **unexercised** (no committed run yet) |
| `run_multisample.py` | Flip-rate: same prompt × N samples | `main-battery` | CI-wired (`pre-publication.yml`) — **unexercised** (no committed run yet) |

All runners share the CI convention: `--tag`, `--out-dir`,
`--print-run-dir`, `--finalize-run`.

## judging/ — score an existing run (no new run folder)

| Script | Purpose |
| --- | --- |
| `judge_sleeper.py` | LLM-judge paired (neutral vs triggered) code answers → `sleeper-judgments.jsonl` (weekly CI) |
| `validate_wvs_swe.py` | Inter-judge agreement + clustered-CI analysis for a wvs-swe run |
| `rescore_run.py` | Recompute `extracted`/`is_correct` offline after scoring-logic changes |
| `judge_calibration.py` | Sample judged pairs for Small-vs-Medium judge agreement (semi-manual; does not itself call judges) |

## analysis/ — aggregate over runs/

| Script | Purpose |
| --- | --- |
| `summarize_eval.py` | Per-run roll-up: `summary.json/md`, polar plot, citation string (weekly CI) |
| `analyze_censorship_v2.py` | Three-class censorship analysis of a censorship run |
| `meta_review.py` | Models review our own article/labels; writes provenance-complete run folders |

## maintenance/ — run repair and one-offs

`rerun_failed.py` (rerun HTTP_ERROR rows into an existing run),
`rerun_empty_claude.py` (rerun truncated/refused Claude rows),
`backfill_run_json.py` (the one-off run.json backfill for historical runs).

## ci/ — invoked by GitHub Actions, not by hand

`list_models.py` (matrix setup), `check_manifest.py` (datasets integrity
gate), `validate_run.py` (data-quality gate before analysis).

## datasets/ — dataset generators

Generators for the frozen dataset versions. **Frozen versions are never
regenerated in place** — a change means a new version directory and a new
generator (see `datasets/README.md`). Note: these scripts execute on
import (no `__main__` guard) — never import them.

## lib/ — shared code (not runnable)

`provenance.py` (run naming + `run.json` lifecycle, single writer),
`api.py` (shared OpenAI-compatible `chat_completion` + config).

## archive/

Superseded scripts kept for provenance — see `archive/README.md`. Do not
run them.

## Conventions

- **New benchmark?** → new `run_*.py` in `evals/`, wired through
  `lib/provenance.py` so the run folder is self-describing.
- **New dataset version?** → new directory under `datasets/<name>/` +
  generator in `scripts/datasets/` + manifest entry (CI enforces sync).
- **Shared code between scripts?** → `lib/`, never import one runner from
  another.
