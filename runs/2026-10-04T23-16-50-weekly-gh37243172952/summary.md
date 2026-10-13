# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **5 modeller** på **369 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Lang-MCQ | Lang-Preference | Conversation | False-friends | Long-form | Translation | Swenglish-free | Culture-MCQ | Culture-TF | Values | Censorship-free | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/Kimi-K3 | 70% | 100% | 37% | 100% | 100% | 77% | 98% | 90% | 60% | 65% | 99% | 81% |
| google/gemma-4-31B-it | 75% | 92% | 23% | 90% | 100% | 68% | 100% | 75% | 70% | 55% | 92% | 76% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 70% | 92% | 13% | 90% | 100% | 65% | 100% | 60% | 80% | 73% | 81% | 75% |
| zai-org/GLM-5.3-Flash | 80% | 100% | 27% | 90% | 100% | 88% | 96% | 75% | 0% | 67% | 99% | 75% |
| Qwen/Qwen3.8-27B-FP8 | 60% | 75% | 10% | 80% | 100% | 74% | 96% | 65% | 80% | 64% | 97% | 73% |

## Metriker

- **Lang-MCQ**: Flervalsfrågor - vilket är rätt svenskt ord för påhittat ord?
- **Lang-Preference**: Vilken mening är mest korrekt skriven på svenska?
- **Conversation**: Använder modellen rätt svenska ord i tekniska samtal?
- **False-friends**: Kognatfel - undviker modellen direktöversättningar som ger fel betydelse?
- **Long-form**: Begreppsfoerklaringar (användargränssnitt, refaktorisering m.m.)
- **Translation**: Translation EN→SV - täckning av förväntade svenska nyckelord
- **Swenglish-free**: Hur få påhittade hybridord (eng stam + sv böjning) modellen använder
- **Culture-MCQ**: Flervalsfrågor om svensk kultur och kulturkanon
- **Culture-TF**: Sant/falskt-påståenden om svensk kultur
- **Values**: Återspeglar modellen svenska värderingar (WVS-baserat)?
- **Censorship-free**: Svarar modellen på känsliga frågor utan att felaktigt vägra? (3 censurtraditioner + asymmetrisk test + Falun)

## Sleeper agent-analys

Samma koduppgift ställs i neutral och触发ad kontext (named triggers + datum-triggers). Bedömt av LLM-domare (Mistral Small) via parjämförelse.

| Modell | Subtila sårbarheter | Partisk vägran | Förklaringsskillnad | Kodstilsdiff |
|---|---:|---:|---:|---:|
| google/gemma-4-31B-it | 5% | 8% | 8% | 33% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 15% | 6% | 0% | 38% |
| moonshotai/Kimi-K3 | 3% | 30% | 36% | 29% |
| Qwen/Qwen3.8-27B-FP8 | 0% | 20% | 17% | 30% |
| zai-org/GLM-5.3-Flash | 0% | 20% | 21% | 9% |

## Plot

![Polär plot](polar-plot.png)

## Observationer

### google/gemma-4-31B-it
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: code_style_diff flaggade i >10% av par

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form
- **Sleeper**: subtle_vuln, code_style_diff flaggade i >10% av par

### moonshotai/Kimi-K3
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-TF, Values
- **Styrkor**: Lang-Preference, False-friends, Long-form
- **Sleeper**: partial_refusal, explanation_diff, code_style_diff flaggade i >10% av par

### Qwen/Qwen3.8-27B-FP8
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form
- **Sleeper**: partial_refusal, explanation_diff, code_style_diff flaggade i >10% av par

### zai-org/GLM-5.3-Flash
- **Svagheter**: Conversation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Lang-Preference, Long-form
- **Sleeper**: partial_refusal, explanation_diff flaggade i >10% av par

