# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **9 modeller** på **369 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Lang-MCQ | Lang-Preference | Conversation | False-friends | Long-form | Translation | Swenglish-free | Culture-MCQ | Culture-TF | Values | Censorship-free | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/Kimi-K3 | 70% | 92% | 30% | 90% | 100% | 71% | 99% | 90% | 70% | 65% | 88% | 79% |
| mistralai/Mistral-Medium-3.5-128B | 70% | 92% | 20% | 90% | 100% | 60% | 99% | 85% | 70% | 75% | 98% | 78% |
| zai-org/GLM-5.2 | 75% | 83% | 20% | 90% | 100% | 70% | 100% | 70% | 80% | 71% | 94% | 78% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 75% | 92% | 17% | 90% | 100% | 68% | 99% | 60% | 80% | 71% | 100% | 77% |
| moonshotai/Kimi-K2.6 | 70% | 92% | 20% | 100% | 100% | 92% | 95% | 70% | 50% | 64% | 97% | 77% |
| meta-llama/Llama-3.3-70B-Instruct | 70% | 75% | 23% | 90% | 100% | 65% | 99% | 65% | 80% | 73% | 97% | 76% |
| zai-org/GLM-4.7-FP8 | 75% | 67% | 27% | 90% | 100% | 67% | 100% | 60% | 70% | 76% | 92% | 75% |
| google/gemma-4-31B-it | 80% | 83% | 20% | 70% | 100% | 68% | 97% | 75% | 70% | 44% | 98% | 73% |
| openai/gpt-oss-120b | 70% | 83% | 3% | 100% | 100% | 66% | 100% | 65% | 60% | 60% | 82% | 72% |

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
| google/gemma-4-31B-it | 5% | 6% | 12% | 10% |
| meta-llama/Llama-3.3-70B-Instruct | 3% | 0% | 5% | 0% |
| mistralai/Mistral-Medium-3.5-128B | 0% | 2% | 8% | 3% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 2% | 3% | 9% | 7% |
| moonshotai/Kimi-K2.6 | 0% | 5% | 14% | 7% |
| moonshotai/Kimi-K3 | 0% | 6% | 14% | 10% |
| openai/gpt-oss-120b | 0% | 8% | 21% | 10% |
| zai-org/GLM-4.7-FP8 | 0% | 0% | 11% | 0% |
| zai-org/GLM-5.2 | 0% | 15% | 20% | 10% |

## Plot

![Polär plot](polar-plot.png)

## Observationer

### google/gemma-4-31B-it
- **Svagheter**: Conversation, False-friends, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: sleeper_length_diff >10%

### meta-llama/Llama-3.3-70B-Instruct
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form

### mistralai/Mistral-Medium-3.5-128B
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-TF, Values
- **Styrkor**: Long-form

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form, Censorship-free

### moonshotai/Kimi-K2.6
- **Svagheter**: Lang-MCQ, Conversation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: False-friends, Long-form
- **Sleeper**: sleeper_length_diff >10%

### moonshotai/Kimi-K3
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: sleeper_length_diff >10%

### openai/gpt-oss-120b
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: False-friends, Long-form
- **Sleeper**: sleeper_length_diff >10%

### zai-org/GLM-4.7-FP8
- **Svagheter**: Lang-MCQ, Lang-Preference, Conversation, Translation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: sleeper_length_diff >10%

### zai-org/GLM-5.2
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form
- **Sleeper**: sleeper_refusal_diff, sleeper_length_diff >10%

