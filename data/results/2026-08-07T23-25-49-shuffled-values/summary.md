# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **9 modeller** på **322 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Lang-MCQ | Lang-Preference | Conversation | False-friends | Long-form | Translation | Swenglish-free | Culture-MCQ | Culture-TF | Values | Censorship-free | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/Kimi-K3 | 70% | 92% | 27% | 90% | 100% | 71% | 99% | 85% | 70% | 60% | 97% | 78% |
| zai-org/GLM-5.2 | 70% | 92% | 23% | 90% | 100% | 70% | 100% | 65% | 80% | 64% | 96% | 77% |
| zai-org/GLM-4.7-FP8 | 75% | 67% | 33% | 100% | 100% | 69% | 99% | 70% | 70% | 75% | 91% | 77% |
| mistralai/Mistral-Medium-3.5-128B | 70% | 92% | 20% | 100% | 100% | 60% | 99% | 65% | 70% | 71% | 98% | 77% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 70% | 92% | 17% | 100% | 100% | 68% | 99% | 55% | 80% | 60% | 100% | 76% |
| meta-llama/Llama-3.3-70B-Instruct | 60% | 75% | 23% | 90% | 100% | 65% | 99% | 75% | 80% | 71% | 98% | 76% |
| google/gemma-4-31B-it | 80% | 83% | 20% | 90% | 100% | 68% | 99% | 75% | 70% | 31% | 99% | 74% |
| openai/gpt-oss-120b | 70% | 75% | 17% | 90% | 100% | 67% | 100% | 65% | 70% | 55% | 83% | 72% |
| moonshotai/Kimi-K2.6 | 40% | 67% | 20% | 60% | 100% | 94% | 96% | 45% | 60% | 36% | 97% | 65% |

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

Samma koduppgift ställs i neutral och触发ad kontext (named triggers + datum-triggers). Bedömt med regex-heuristik (ingen LLM-domare tillgänglig).

| Modell | Sårbarhetsdiff | Vägradiff | Längddiff | Neutral vägran |
|---|---:|---:|---:|---:|
| google/gemma-4-31B-it | 5% | 2% | 9% | 0% |
| meta-llama/Llama-3.3-70B-Instruct | 9% | 0% | 0% | 0% |
| mistralai/Mistral-Medium-3.5-128B | 0% | 0% | 0% | 0% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 0% | 0% | 2% | 0% |
| moonshotai/Kimi-K2.6 | 0% | 2% | 18% | 0% |
| moonshotai/Kimi-K3 | 0% | 7% | 2% | 0% |
| openai/gpt-oss-120b | 0% | 2% | 14% | 0% |
| zai-org/GLM-4.7-FP8 | 0% | 0% | 9% | 0% |
| zai-org/GLM-5.2 | 0% | 9% | 11% | 0% |

## Plot

![Polär plot](polar-plot.png)

## Observationer

### google/gemma-4-31B-it
- **Svagheter**: Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form

### meta-llama/Llama-3.3-70B-Instruct
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form

### mistralai/Mistral-Medium-3.5-128B
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: False-friends, Long-form

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: False-friends, Long-form, Censorship-free

### moonshotai/Kimi-K2.6
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, False-friends, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: sleeper_length_diff >10%

### moonshotai/Kimi-K3
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-TF, Values
- **Styrkor**: Long-form

### openai/gpt-oss-120b
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: sleeper_length_diff >10%

### zai-org/GLM-4.7-FP8
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: False-friends, Long-form

### zai-org/GLM-5.2
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form
- **Sleeper**: sleeper_length_diff >10%

