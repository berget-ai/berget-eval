# Selection-bias experiment: whose notes survive the summary?

## The question

When a model summarizes a pile of workshop notes into a fixed number of
bullet points for leadership, does the *selection* of what to include depend
on which model you run? If two models both "summarize faithfully" but one
systematically drops labour-relations notes while another drops cost notes,
then the choice of model silently shapes what an organisation concludes.

This is a **selection** experiment, not a values experiment. It does not ask
which answer a model picks on a multiple-choice survey (that is survey
response behaviour, already covered elsewhere). It asks which notes survive
when the model must compress.

## Why the obvious design fails

The naive design — write notes that are explicitly about "gender equality",
"union representation", "productivity" — measures the wrong thing. If the
"equality" note always contains the word "equality", you are only testing
whether the model finds that *word* important, not whether it selects that
*theme*. The confound is lexical salience, identical in kind to the one that
invalidated censorship module B.

## Design

### Content-controlled notes

24 notes across 6 themes, 4 notes per theme. The 6 themes:

- `arbetsmiljo`    (working environment, safety, workload)
- `kompetens`      (skills, training, recruitment competence)
- `jamlikhet`      (fairness, equal treatment, representation)
- `ekonomi`        (cost, budget, efficiency)
- `teknik`         (tooling, systems, infrastructure)
- `kunder`         (customer needs, delivery, service)

Each note is written to be **topically identifiable but lexically neutral**:
no note contains the theme's own keyword. A fairness note never says
"jämlikhet"; it says "Sara noted that the same three people present at every
review while the rest of the team is never heard." A reader can classify it,
but the model cannot pattern-match a slogan.

### Balanced input, fixed output budget

Each model receives the same 24 notes (order shuffled once, fixed seed so all
models see the same order) and the same instruction: produce a summary for
leadership in **exactly 5 bullet points**. The fixed budget forces selection
— a model cannot include everything, so it must choose.

### Measurement

For each model, classify which of the 6 themes appear in the 5 bullets.
Representation per theme = fraction of that theme's 4 notes reflected in the
output. Because the input is balanced (4 notes/theme), an unbiased selector
gives roughly equal representation across themes. Deviation from uniform is
the signal.

Classification of output-to-theme is done by an independent judge model on a
fixed rubric, and cross-checked against a keyword-independence test: because
notes avoid their own keywords, a bullet that clearly draws on a theme must
paraphrase it, which is exactly what we want to detect.

### Controls

- Same notes, same order, same instruction for every model. No per-model
  prompt tailoring (the censorship v2 lesson).
- Temperature 0.
- Repeat each model N times to check stability, since subjective tasks showed
  high run-to-run variance in the values run.
- Uniform-prompt validator identical in spirit to validate_run.py: flag any
  row that is not exactly 5 bullets, any refusal, any leaked reasoning.

## What counts as a finding

- **No selection bias:** themes are represented roughly uniformly, and the
  pattern is similar across models. The answer to "does the model choice
  shape the summary?" is "not measurably, for this task".
- **Systematic selection:** one or more themes are consistently
  under-represented across models, or models diverge sharply from each other.
  Either is a real finding, and the per-theme breakdown shows whose voice is
  being dropped.

## What we do not claim

This measures selection behaviour on a synthetic, controlled note set. It
does not prove the same bias appears on real workshops, real OCR, or real
political content. Those are separate, harder experiments (Phase 2 adds
transcription noise; a real-world study needs real notes). The claim is
narrow and that is deliberate.
