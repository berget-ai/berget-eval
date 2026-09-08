# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **9 modeller** på **322 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Lang-MCQ | Lang-Preference | Conversation | False-friends | Long-form | Translation | Swenglish-free | Culture-MCQ | Culture-TF | Values | Censorship-free | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| zai-org/GLM-4.7-FP8 | 75% | 75% | 33% | 100% | 100% | 69% | 99% | 70% | 70% | 82% | 91% | 79% |
| zai-org/GLM-5.2 | 75% | 92% | 23% | 90% | 100% | 72% | 100% | 75% | 70% | 73% | 94% | 79% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 70% | 92% | 17% | 100% | 100% | 68% | 99% | 55% | 80% | 64% | 100% | 77% |
| mistralai/Mistral-Medium-3.5-128B | 70% | 92% | 20% | 100% | 100% | 60% | 99% | 65% | 70% | 69% | 98% | 77% |
| meta-llama/Llama-3.3-70B-Instruct | 70% | 67% | 20% | 90% | 100% | 65% | 99% | 75% | 80% | 73% | 98% | 76% |
| moonshotai/Kimi-K3 | 60% | 75% | 23% | 90% | 100% | 73% | 99% | 85% | 60% | 62% | 92% | 74% |
| google/gemma-4-31B-it | 80% | 83% | 20% | 90% | 100% | 68% | 98% | 75% | 70% | 29% | 99% | 74% |
| openai/gpt-oss-120b | 70% | 75% | 3% | 90% | 100% | 71% | 100% | 60% | 70% | 51% | 83% | 70% |
| moonshotai/Kimi-K2.6 | 35% | 58% | 33% | 70% | 95% | 93% | 96% | 40% | 60% | 29% | 96% | 64% |

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
| google/gemma-4-31B-it | 2% | 2% | 27% | 41% |
| meta-llama/Llama-3.3-70B-Instruct | 0% | 0% | 25% | 55% |
| mistralai/Mistral-Medium-3.5-128B | 5% | 0% | 0% | 32% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 2% | 0% | 7% | 30% |
| moonshotai/Kimi-K2.6 | 2% | 11% | 30% | 36% |
| moonshotai/Kimi-K3 | 0% | 11% | 23% | 52% |
| openai/gpt-oss-120b | 0% | 5% | 41% | 73% |
| zai-org/GLM-4.7-FP8 | 5% | 0% | 0% | 50% |
| zai-org/GLM-5.2 | 9% | 11% | 14% | 36% |

## Plot

![Polär plot](polar-plot.png)

## Observationer

### google/gemma-4-31B-it
- **Svagheter**: Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: explanation_diff, code_style_diff flaggade i >10% av par

### meta-llama/Llama-3.3-70B-Instruct
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form
- **Sleeper**: explanation_diff, code_style_diff flaggade i >10% av par

### mistralai/Mistral-Medium-3.5-128B
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: False-friends, Long-form
- **Sleeper**: code_style_diff flaggade i >10% av par

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: False-friends, Long-form, Censorship-free
- **Sleeper**: code_style_diff flaggade i >10% av par

### moonshotai/Kimi-K2.6
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, False-friends, Culture-MCQ, Culture-TF, Values
- **Sleeper**: partial_refusal, explanation_diff, code_style_diff flaggade i >10% av par

### moonshotai/Kimi-K3
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: partial_refusal, explanation_diff, code_style_diff flaggade i >10% av par

### openai/gpt-oss-120b
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: explanation_diff, code_style_diff flaggade i >10% av par

### zai-org/GLM-4.7-FP8
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Culture-TF
- **Styrkor**: False-friends, Long-form
- **Sleeper**: code_style_diff flaggade i >10% av par

### zai-org/GLM-5.2
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: partial_refusal, explanation_diff, code_style_diff flaggade i >10% av par

