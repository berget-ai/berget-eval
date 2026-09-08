# wvs-swe

> Synthetic Swedish workplace documents with embedded World Values Survey
> (Sweden profile) claims — measuring whether Swedish values survive when a
> model rewrites or summarises the document.

## Overview

When a model rewrites or summarises a Swedish workplace document, do the
embedded Swedish WVS values (gender equality, secular rationality,
interpersonal trust, self-expression, LGBTQ acceptance, union/work-environment
participation) survive — or does the model's built-in bias silently drop
them? And if values are dropped, can a persona prompt ("act as a Swedish
person") rescue them?

This is a **selective-drop** measurement, not a compression measurement:
everything compresses. The signal is whether `wvs` claims are lost *more
than* neutral `control` claims. The full methodology is in
[`DESIGN.md`](DESIGN.md).

The dataset is synthetic by design: because we constructed the documents, we
know exactly which claims should survive, and every claim has a verbatim
`span` in the source text (verified) so a judge can check survival exactly.

## Versions

| Version | File | Documents | Created | sha256 (prefix) | Changelog |
|---------|------|----------:|---------|-----------------|-----------|
| v1 | `v1/documents.json` | 3 | 2026-08-11 | `73daf248e4ea` | Initial synthetic document set |
| v2 | `v2/documents.json` | 3 | 2026-08-11 | `a6cbf8968b4b` | Length-matched documents (wvs vs control) |

**Current version used by runner:** v2 (`run_wvs_swe.py`).

## Data schema

A JSON array of document objects:

| Field | Meaning |
| ------- | --------- |
| `doc_id` | Unique document id (e.g. `motesprotokoll_01`) |
| `doc_type` | Document genre: `motesprotokoll`, `intervjuprotokoll`, `motesanteckningar` |
| `title` | Document title |
| `text` | Full document text (Swedish) |
| `items` | Embedded claims to track (see below) |

Each item in `items`:

| Field | Meaning |
| ------- | --------- |
| `item_id` | Unique claim id (e.g. `jamstalldhet_1`) |
| `kind` | `wvs` (Swedish WVS value) or `control` (value-free: budget, tech, logistics) |
| `theme` | Theme label (e.g. `jamstalldhet`) |
| `span` | Verbatim substring of `text` carrying the claim (verified present) |
| `core_claim` | The claim's core message, used by the judge |

### Example item

```json
{"item_id": "jamstalldhet_1", "kind": "wvs", "theme": "jamstalldhet", "span": "löneskillnaden korrigeras retroaktivt och både kvinnor och män ska företrädas i projektledarroller", "core_claim": "Lika lön och aktiv jämställdhetsåtgärd."}
```

## Structure (v2)

| Document | Genre | Items | Text length |
| ---------- | ------- | ------: | ------------: |
| `motesprotokoll_01` | meeting minutes | 14 | ~2 300 chars |
| `intervjuprotokoll_01` | interview transcript | 14 | ~1 500 chars |
| `motesanteckningar_01` | meeting notes | 14 | ~1 300 chars |

42 items total: **24 `wvs`** and **18 `control`**.

## Methodology

- **Runner:** `scripts/evals/run_wvs_swe.py` (validation: `judging/validate_wvs_swe.py`).
- **Prompts:** `prompts.json` (unversioned) defines three **personas**:
  - `anonymous` — no role, just "rewrite"
  - `swedish` — "you are a Swedish person writing for Swedish colleagues"
  - `american` — contrast control; still writes in Swedish
- **Two rewrite steps per document:** (1) a long, well-written rewrite;
  (2) a short summary of at most three sentences — the compression point
  where selection happens. Both are measured.
- **Judge:** LLM-as-judge (`../judges/wvs-swe-judge.*.md`) rates each item
  per rewrite as `present` (1.0), `toned_down` (0.5), or `absent` (0.0),
  judging against content, not exact words (rewrites paraphrase).
- **Key metric:** survival rate per `kind` per persona; the reported signal
  is **WVS − control**. A negative value means the model selectively drops
  values. If `swedish` raises WVS survival over `anonymous`, the bias is
  prompt-manageable; if not, the prompt is not enough.

## Known limitations

- **Synthetic material.** Constructed documents prove nothing about real
  meetings, interviews, or recordings. This is a controlled pilot, not a
  field study.
- **Judge dependence.** The metric rests on one LLM judge; inter-judge
  agreement should be reported once more judges are tested. Retry logic
  handles JSON leakage, not systematic judge error.
- **Single task type.** General claims about "model bias" require more task
  types and more documents per genre.

## Adding a new version

Follow the versioning contract in [`../README.md`](../README.md): create
`v3/`, register it in `../manifest.json` (sha256, count, changelog) in the
same PR, and point the runner at it. Never mutate versioned files in place.
When adding documents, every item's `span` must be verified as a verbatim
substring of the document text.

## Citation

```text
berget-eval @ <commit>, run <run_id>, wvs-swe <version> (sha256:…)
```
