# svenska-ai-ordval

Svenskt finetuning-data och utvärderingsramverk för AI-modellers språk- och kulturkompetens.

## Vad är det här?

Projektet identifierar och åtgärdar svenska AI-modellers tendens att producera svengelska hybridformer — ord som "deploybar", "routningen", "parsningen" — istället för etablerade svenska IT-termer som "driftsättningsbar", "dirigeringen", "tolkningen".

## Innehåll

### Träningsdata

- `data/svenska-it-ordval-finetuning.jsonl` — 350 SFT-par med påhittade ord och deras korrekta svenska former
- `data/svenska-it-ordval-konversationer.jsonl` — 32 konversationer där korrekta svenska termer används i tekniska sammanhang

### Referensdata

- `data/false-friends-ordlista.jsonl` — 100 false friends och kognatfel (ord där direktöversättning ger fel betydelse)
- `data/it-termer-moderna.jsonl` — 192 moderna IT- och AI-termer med svenska former
- `data/cs-it-ord-raw.txt` — CS IT-ordlista (14 810 ord) som referens

### Utvärdering

- `data/eval-questions.jsonl` — 87 testfrågor (språk-MCQ, preference, long-form, översättning, kultur-MCQ, kultur sant/falskt)
- `scripts/run_eval.py` — kör alla frågor motalla modeller via OpenAI-kompatibelt API
- `scripts/eval_pilot.py` — pilot-runner för snabba test
- `scripts/summarize_eval.py` — sammanställer resultat med polär plot och Markdown-rapport

### Rapporter

- [Saknade ord i ordlistor — del 1](docs/100-2026-08-07-saknade-ord-del1-pahittade.md)
- [Saknade ord i ordlistor — del 2](docs/100-2026-08-07-saknade-ord-del2-kognat-moderna.md)
- [Översättningsförslag](docs/101-2026-08-07-oversattningsforkslag.md)
- [Förslag till SAOL](docs/102-2026-08-07-saol-forklag-termer.md)

## Licens

CC0 1.0 Universal (Public Domain)
