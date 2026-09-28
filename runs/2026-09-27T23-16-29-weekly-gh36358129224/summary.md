# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **8 modeller** på **369 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Lang-MCQ | Lang-Preference | Conversation | False-friends | Long-form | Translation | Swenglish-free | Culture-MCQ | Culture-TF | Values | Censorship-free | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/Kimi-K3 | 65% | 92% | 27% | 90% | 100% | 76% | 98% | 90% | 50% | 62% | 99% | 77% |
| google/gemma-4-31B-it | 75% | 92% | 23% | 90% | 100% | 68% | 100% | 75% | 70% | 56% | 92% | 77% |
| zai-org/GLM-5.3-Flash | 80% | 100% | 27% | 90% | 100% | 88% | 96% | 75% | 0% | 67% | 99% | 75% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 70% | 92% | 13% | 80% | 100% | 65% | 100% | 60% | 80% | 73% | 81% | 74% |
| Qwen/Qwen3.8-27B-FP8 | 60% | 83% | 20% | 80% | 85% | 72% | 97% | 70% | 70% | 62% | 97% | 72% |
| convaiinnovations/laya | 0% | 0% | 0% | 0% | 0% | 0% | 100% | 0% | 0% | 0% | 99% | 18% |
| klang/pianissimo | 0% | 0% | 0% | 0% | 0% | 0% | 100% | 0% | 0% | 0% | 99% | 18% |
| Qwen/Qwen3.5-2B | 0% | 0% | 0% | 0% | 0% | 0% | 100% | 0% | 0% | 0% | 99% | 18% |

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
| convaiinnovations/laya | 0% | 0% | 0% | 0% |
| google/gemma-4-31B-it | 0% | 0% | 0% | 0% |
| klang/pianissimo | 0% | 0% | 0% | 0% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 0% | 0% | 0% | 0% |
| moonshotai/Kimi-K3 | 0% | 0% | 0% | 0% |
| Qwen/Qwen3.5-2B | 0% | 0% | 0% | 0% |
| Qwen/Qwen3.8-27B-FP8 | 0% | 0% | 0% | 0% |
| zai-org/GLM-5.3-Flash | 0% | 0% | 0% | 0% |

## Plot

![Polär plot](polar-plot.png)

## Observationer

### convaiinnovations/laya
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, False-friends, Long-form, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Swenglish-free

### google/gemma-4-31B-it
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form

### klang/pianissimo
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, False-friends, Long-form, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Swenglish-free

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form

### moonshotai/Kimi-K3
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-TF, Values
- **Styrkor**: Long-form

### Qwen/Qwen3.5-2B
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, False-friends, Long-form, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Swenglish-free

### Qwen/Qwen3.8-27B-FP8
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values

### zai-org/GLM-5.3-Flash
- **Svagheter**: Conversation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Lang-Preference, Long-form

