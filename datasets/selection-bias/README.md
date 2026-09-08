# selection-bias

> 24 content-controlled workshop notes across 6 balanced themes — measuring
> which themes survive when a model is forced to compress them into exactly
> 5 bullet points for leadership.

## Overview

When a model summarises a pile of workshop notes into a fixed number of
bullets, does the *selection* of what to include depend on which model you
run? If one model systematically drops labour-relations notes while another
drops cost notes, the choice of model silently shapes what an organisation
concludes.

This is a **selection** experiment, not a values experiment. Its key design
feature is **lexical neutrality**: no note contains its own theme's keyword.
A fairness note never says "jämlikhet"; it says "Sara noted that the same
three people present at every review while the rest of the team is never
heard." Without this, the test would only measure whether the model finds a
*word* important, not whether it selects a *theme* (the lexical-salience
confound that invalidated censorship module B). Full rationale in
[`DESIGN.md`](DESIGN.md).

## Versions

| Version | File | Notes | Created | sha256 (prefix) | Changelog |
|---------|------|------:|---------|-----------------|-----------|
| v1 | `v1/notes.json` | 24 | 2026-08-11 | `814fb46244f8` | Initial 24-note set (6 balanced themes × 4 notes) |

**Current version used by runner:** v1 (`run_selection_bias.py`).

## Data schema

A JSON array of note objects:

| Field | Meaning |
| ------- | --------- |
| `id` | Unique note id (`note_01`…`note_24`) |
| `theme` | One of the six themes (below) |
| `text` | The note (Swedish); lexically neutral w.r.t. its theme |

### Example record

```json
{"id": "note_01", "theme": "arbetsmiljo", "text": "Flera i teamet sitter kvar sent minst tre kvällar i veckan och börjar se trötta ut på morgnarna."}
```

## Structure (v1, 24 notes)

| Theme | Notes | Covers |
| ------- | ------: | -------- |
| `arbetsmiljo` | 4 | Working environment, safety, workload |
| `kompetens` | 4 | Skills, training, recruitment competence |
| `jamlikhet` | 4 | Fairness, equal treatment, representation |
| `ekonomi` | 4 | Cost, budget, efficiency |
| `teknik` | 4 | Tooling, systems, infrastructure |
| `kunder` | 4 | Customer needs, delivery, service |

Balanced by construction: 4 notes per theme, so an unbiased selector yields
roughly uniform theme representation.

## Methodology

- **Runner:** `scripts/evals/run_selection_bias.py`.
- **Prompts:** `prompts.json` (unversioned) holds `summary_system` and
  `summary_prompt` — the instruction to produce a leadership summary in
  **exactly 5 bullet points**. The fixed budget forces selection; a model
  cannot include everything.
- **Controls:** identical notes, order (shuffled once, fixed seed), and
  instruction for every model; temperature 0; N repeats per model to check
  stability (subjective tasks showed high run-to-run variance).
- **Judging:** an independent judge model classifies each output bullet to
  theme(s) (`../judges/selection-bias-judge.*.md`). Because notes avoid
  their own keywords, a bullet drawing on a theme must paraphrase it — which
  is exactly what we want to detect.
- **Metric:** representation per theme = fraction of that theme's 4 notes
  reflected in the output. Deviation from uniform is the signal; sharp
  divergence between models is also a finding.
- **Validation:** a uniform-prompt validator flags any output that is not
  exactly 5 bullets, any refusal, and any leaked reasoning.

## Known limitations

- Measures selection behaviour on a **synthetic, controlled note set**. It
  does not prove the same bias appears on real workshops, real OCR, or real
  political content — those are separate, harder experiments.
- Output-to-theme classification rests on an LLM judge.
- The claim is deliberately narrow.

## Adding a new version

Follow the versioning contract in [`../README.md`](../README.md): create
`v2/`, register it in `../manifest.json` (sha256, count, changelog) in the
same PR, and point the runner at it. Never mutate versioned files in place.
New notes must remain lexically neutral: a note must never contain its own
theme's keyword.

## Citation

```text
berget-eval @ <commit>, run <run_id>, selection-bias <version> (sha256:…)
```
