# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **9 modeller** på **369 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Lang-MCQ | Lang-Preference | Conversation | False-friends | Long-form | Translation | Swenglish-free | Culture-MCQ | Culture-TF | Values | Censorship-free | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/Kimi-K3 | 70% | 100% | 37% | 90% | 100% | 66% | 99% | 85% | 70% | 67% | 99% | 80% |
| zai-org/GLM-5.3 | 80% | 92% | 33% | 90% | 100% | 88% | 97% | 75% | 50% | 58% | 99% | 78% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 75% | 92% | 17% | 90% | 100% | 68% | 99% | 60% | 80% | 69% | 100% | 77% |
| meta-llama/Llama-3.3-70B-Instruct | 65% | 75% | 20% | 90% | 100% | 65% | 99% | 65% | 80% | 73% | 97% | 75% |
| zai-org/GLM-4.7-FP8 | 75% | 67% | 27% | 90% | 100% | 67% | 100% | 60% | 70% | 76% | 92% | 75% |
| google/gemma-4-31B-it | 80% | 83% | 20% | 80% | 100% | 68% | 98% | 70% | 70% | 45% | 99% | 74% |
| zai-org/GLM-5.3-Flash | 80% | 100% | 23% | 90% | 100% | 78% | 99% | 85% | 10% | 49% | 98% | 74% |
| zai-org/GLM-5.2 | 70% | 92% | 10% | 80% | 90% | 68% | 100% | 70% | 70% | 69% | 92% | 74% |
| openai/gpt-oss-120b | 65% | 75% | 3% | 90% | 100% | 67% | 100% | 65% | 70% | 49% | 88% | 70% |

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
| google/gemma-4-31B-it | 0% | 0% | 0% | 0% |
| meta-llama/Llama-3.3-70B-Instruct | 0% | 0% | 0% | 0% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 0% | 0% | 0% | 0% |
| moonshotai/Kimi-K3 | 0% | 0% | 0% | 0% |
| openai/gpt-oss-120b | 0% | 0% | 0% | 0% |
| zai-org/GLM-4.7-FP8 | 0% | 0% | 0% | 0% |
| zai-org/GLM-5.2 | 0% | 0% | 0% | 0% |
| zai-org/GLM-5.3-Flash | 0% | 0% | 0% | 0% |
| zai-org/GLM-5.3 | 0% | 0% | 0% | 0% |

## Plot

![Polär plot](polar-plot.png)

## Observationer

### google/gemma-4-31B-it
- **Svagheter**: Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form

### meta-llama/Llama-3.3-70B-Instruct
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form, Censorship-free

### moonshotai/Kimi-K3
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-TF, Values
- **Styrkor**: Lang-Preference, Long-form

### openai/gpt-oss-120b
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form

### zai-org/GLM-4.7-FP8
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form

### zai-org/GLM-5.2
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values

### zai-org/GLM-5.3-Flash
- **Svagheter**: Conversation, Translation, Culture-TF, Values
- **Styrkor**: Lang-Preference, Long-form

### zai-org/GLM-5.3
- **Svagheter**: Conversation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form

