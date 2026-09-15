# Benchmark data flow

How prompts become raw data and raw data becomes published findings.
Each pipeline below is independently runnable; all write to `runs/<run_id>/`,
self-describing via `run.json` (dataset versions + sha256, models, judge, origin).

```mermaid
flowchart LR
    subgraph INPUTS["INPUTS (prompts & configuration)"]
        Q1["datasets/main-battery/v3/eval-questions.jsonl<br/><i>369 prompts, 12 types<br/>(literal user messages)</i>"]
        Q2["datasets/censorship/v2/questions.jsonl<br/><i>210 prompts<br/>(literal user messages)</i>"]
        Q3["datasets/wvs-swe/v2/documents.json<br/><i>stimulus documents + claims<br/>(NOT full prompts)</i>"]
        Q4["datasets/selection-bias/v1/notes.json<br/><i>24 workshop notes<br/>(NOT full prompts)</i>"]
        P["prompts on disk<br/><i>datasets/*/prompts.json<br/>+ datasets/judges/*.md<br/>(system / persona / summary /<br/>ALL judge prompts)</i>"]
        MODELS["Model list<br/><i>fetched live from API /models<br/>(recorded in run.json)</i>"]
    end

    subgraph RUN["1 · RUN (model under test) — scripts/evals/"]
        R1["run_main_battery.py<br/><i>369 questions × N models<br/>temp 0</i>"]
        R2["run_censorship.py"]
        R3["run_wvs_swe.py<br/><i>docs × personas (sv/us)<br/>× long/short rewrite</i>"]
        R4["run_selection_bias.py<br/><i>notes → fixed-bullet summary</i>"]
    end

    subgraph RAW["RAW OUTPUTS (per run directory)"]
        O0["run.json<br/><i>provenance: datasets + sha256,<br/>models, judge, git commit, origin</i>"]
        O1["&lt;model&gt;.jsonl<br/><i>raw response per question<br/>+ latency + timestamp</i>"]
        O2["runs.jsonl + config.json<br/><i>raw rewrites + system prompts</i>"]
    end

    subgraph JUDGE["2 · JUDGE (LLM-as-judge: Gemma 4 31B) — scripts/judging/"]
        J1["judge_sleeper.py<br/><i>paired-context comparison:<br/>subtle vuln / partial refusal /<br/>explanation diff / style diff<br/>(Gemma 4; Mistral Small 3.2 som<br/>anti-självbedömnings-fallback)</i>"]
        J2["claim-survival judge<br/><i>present / toned_down / absent<br/>(inside run_wvs_swe.py)</i>"]
        J3["theme-survival judge<br/><i>(inside run_selection_bias.py)</i>"]
    end

    subgraph AGG["3 · AGGREGATE & PUBLISH — scripts/analysis/"]
        A1["summarize_eval.py<br/>→ summary.json / summary.md<br/>/ polar-plot.png"]
        A2["judge_sleeper.py<br/>→ sleeper-judgments.jsonl<br/>→ sleeper-summary.json"]
        A3["survival-rate tables<br/><i>(stdout + runs.jsonl)</i>"]
        V["validate_run.py /<br/>validate_wvs_swe.py<br/><i>integrity gates (ci/, judging/)</i>"]
    end

    Q1 & P --> R1
    Q2 & P --> R2
    Q3 & P --> R3
    Q4 & P --> R4
    MODELS --> R1 & R2 & R3 & R4

    R1 & R2 & R3 & R4 --> O0
    R1 --> O1
    R2 --> O1
    R3 --> O2
    R4 --> O2

    O1 --> J1
    O2 --> J2 & J3

    O1 --> A1
    J1 --> A2
    J2 & J3 --> A3
    A1 & A2 & A3 --> V

    style RAW fill:#e8f4e8
    style INPUTS fill:#eef
```

## Auxiliary flows (not shown above)

| Flow | Script | Input | Output |
| --- | --- | --- | --- |
| Flip-rate (non-determinism) | `evals/run_multisample.py` | Same prompt × N samples | String-consistency metrics |
| Judge calibration | `judging/judge_calibration.py` | 50 judged pairs | Small-vs-Medium judge agreement |
| Repair failed responses | `maintenance/rerun_failed.py`, `maintenance/rerun_empty_claude.py` | Existing run dir | Patched `<model>.jsonl` |
| Re-score a run | `judging/rescore_run.py` | Existing run dir | Updated `summary.json` |
| Meta review | `analysis/meta_review.py` | Judgments | Judge-quality critique |

## Verifiability (post-restructure)

1. **All prompts live in `datasets/`.** System, persona, summary and judge prompts
   are data files (`datasets/*/prompts.json`, `datasets/judges/*.md`), hashed into
   every run's `run.json` — the full stimulus is auditable without reading code.
2. **Every run is self-describing.** `runs/<run_id>/run.json` records each stimulus
   file's sha256, models, judge, config, git commit and origin (GitHub Actions run id
   or local), plus a `status` lifecycle — `ci/validate_run.py` blocks runs that didn't
   complete from entering aggregates. Runners write it via `scripts/lib/provenance.py`
   (single writer).
3. **Datasets are versioned and immutable.** `datasets/manifest.json` is enforced by
   CI (`.github/workflows/datasets-manifest.yml`): no in-place mutation, no
   unregistered files. See `datasets/README.md` for the versioning contract.
4. **Remaining gap:** the served model list is dynamic (fetched from the API at run
   time) and the gateway serves unversioned models — which exact weights answered is
   knowable only per model id, not per version. Accepted ambiguity.
