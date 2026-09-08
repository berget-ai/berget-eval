# archive/

Superseded scripts, kept for provenance (they document how the current frozen
dataset versions were produced). Nothing here is maintained; paths inside these
files may reference pre-restructure locations. Do not run these to regenerate
a frozen dataset — versions are immutable; create a new generator in
`scripts/datasets/` for a new version instead.

| Script | Superseded by | Why archived |
| --- | --- | --- |
| `eval_pilot.py` | `evals/run_main_battery.py` | Its own docstring describes run_eval as the full version of it; writes to a pre-restructure `data/` path |
| `generate_eval_questions.py` | `datasets/generate_eval_questions_v3.py` | v2 question generator; the live dataset is v3 |
| `generate_new_eval_questions.py` | `datasets/generate_eval_questions_v3.py` | Experimental additions, folded into v3 |
| `generate_sleeper_agent_questions.py` | `datasets/generate_eval_questions_v3.py` | Writes the pre-restructure `data/eval-questions-sleeper.jsonl` path; sleeper questions live in main-battery v3 |
