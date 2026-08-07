# berget-eval

Utvärderingsramverk för AI-modellers svenska språkkompetens, värderingar och censurbeteende.

## Vad är det här?

Ett komplett utvärderingsramverk som testar AI-modeller på tre dimensioner:

1. **Språkkompetens** — använder modellen korrekta svenska IT-termer istället för svengelska hybridformer ("deploybar" → "driftsättningsbar")?
2. **Värderingar** — återspeglar modellen svenska värderingar (jämställdhet, sekularism, jämställdhet, jämställdhet, tillit, HBTQ-rättigheter) enligt World Values Survey?
3. **Censur** — svarar modellen på känsliga frågor utan att felaktigt vägra? Testas i tre censurtraditioner (kinesisk, europeisk, amerikansk) plus asymmetrisk partiskhetstest.

## Frågor

267 eval-frågor fördelade på:

| Typ | Antal | Vad det testar |
|---|---:|---|
| Censur | 90 | Svarar modellen utan att felaktigt vägra? |
| Värderingar | 55 | Återspeglar modellen svenska värderingar (WVS)? |
| Språk-MCQ | 20 | Korrekt svenskt ord för påhittat ord? |
| Kultur-MCQ | 20 | Svensk kultur- och kulturkanonkunskap? |
| Long-form | 20 | Begreppsförklaringar på svenska |
| Översättning | 15 | EN→SV-översättning utan frengelska |
| Konversation | 15 | Rätt svenska ord i tekniska samtal |
| Preference | 12 | Vilken mening är mest korrekt skriven? |
| Kultur-Sant/Falskt | 10 | Sant/falskt om svensk kultur |
| False friends | 10 | Kognatfel (ras-konditioner, gift, kondition) |

### Censurkategorier

| Kategori | Antal | Exempel |
|---|---:|---|
| Kinesisk | 15 | Tiananmen, Taiwan, Tibet, Falun Gong, Xinjiang |
| Europeisk | 15 | Förintelseförnekande, hatbrott, GDPR, upphovsrätt |
| Amerikansk | 20 | Abort, ras, vapen, vaccination, cancel culture |
| Asymmetrisk | 20 | Par-test: kapitalism/kommunism, Biden/Trump, feminism, EU |
| Falsk positiv | 20 | Säkra frågor som felaktigt censureras (inkl. Falun som svensk ort) |

## Träningsdata

- `data/svenska-it-ordval-finetuning.jsonl` — 350 SFT-par (påhittat ord → korrekt svensk form)
- `data/svenska-it-ordval-konversationer.jsonl` — 32 konversationer där svenska IT-termer används i tekniska sammanhang

## Köra utvärdering

```bash
export OPENAI_API_KEY="din-nyckel"
export OPENAI_API_BASE="https://api.example.org/v1"
python scripts/run_eval.py --tag $(date +%Y-%m-%d)
```

GitHub Actions kör automatiskt varje söndag 23:00 UTC via `.github/workflows/weekly-eval.yml`.

## Rapporter

- [Saknade ord i ordlistor — del 1](docs/100-2026-08-07-saknade-ord-del1-pahittade.md)
- [Saknade ord i ordlistor — del 2](docs/100-2026-08-07-saknade-ord-del2-kognat-moderna.md)
- [Översättningsförslag](docs/101-2026-08-07-oversattningsforkslag.md)
- [Förslag till SAOL](docs/102-2026-08-07-saol-forklag-termer.md)

## Licens

CC0 1.0 Universal (Public Domain)
