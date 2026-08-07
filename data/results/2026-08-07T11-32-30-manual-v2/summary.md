# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **9 modeller** på **122 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Språk-MCQ | Språk-Preference | Konversation | False friends | Long-form | Översättning | Frengelska-fri | Kultur-MCQ | Kultur-Sant/Falskt | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/Kimi-K3 | 65% | 92% | 30% | 100% | 100% | 73% | 99% | 85% | 70% | 79% |
| zai-org/GLM-5.2 | 75% | 83% | 23% | 100% | 100% | 64% | 100% | 80% | 70% | 77% |
| zai-org/GLM-4.7-FP8 | 75% | 75% | 33% | 100% | 100% | 69% | 99% | 70% | 70% | 77% |
| google/gemma-4-31B-it | 80% | 83% | 20% | 90% | 100% | 68% | 99% | 75% | 70% | 76% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 70% | 92% | 17% | 100% | 100% | 68% | 100% | 55% | 80% | 76% |
| mistralai/Mistral-Medium-3.5-128B | 70% | 92% | 20% | 100% | 100% | 60% | 100% | 65% | 70% | 75% |
| meta-llama/Llama-3.3-70B-Instruct | 60% | 75% | 23% | 90% | 100% | 65% | 100% | 75% | 80% | 74% |
| openai/gpt-oss-120b | 70% | 75% | 17% | 90% | 100% | 67% | 100% | 60% | 70% | 72% |
| moonshotai/Kimi-K2.6 | 35% | 50% | 23% | 50% | 100% | 92% | 93% | 45% | 50% | 60% |

## Metriker

- **Språk-MCQ**: Flervalsfrågor - vilket är rätt svenskt ord för påhittat ord?
- **Språk-Preference**: Vilken mening är mest korrekt skriven på svenska?
- **Konversation**: Använder modellen rätt svenska ord i tekniska samtal?
- **False friends**: Kognatfel - undviker modellen direktöversättningar som ger fel betydelse?
- **Long-form**: Begreppsförklaringar (användargränssnitt, refaktorisering m.m.)
- **Översättning**: Översättning EN→SV - täckning av förväntade svenska nyckelord
- **Frengelska-fri**: Hur få påhittade hybridord (eng stam + sv böjning) modellen använder
- **Kultur-MCQ**: Flervalsfrågor om svensk kultur och kulturkanon
- **Kultur-Sant/Falskt**: Sant/falskt-påståenden om svensk kultur

## Plot

![Polär plot](polar-plot.png)

## Observationer

### google/gemma-4-31B-it
- **Svagheter**: Konversation, Översättning, Kultur-MCQ, Kultur-Sant/Falskt
- **Styrkor**: Long-form

### meta-llama/Llama-3.3-70B-Instruct
- **Svagheter**: Språk-MCQ, Språk-Preference, Konversation, Översättning, Kultur-MCQ
- **Styrkor**: Long-form, Frengelska-fri

### mistralai/Mistral-Medium-3.5-128B
- **Svagheter**: Språk-MCQ, Konversation, Översättning, Kultur-MCQ, Kultur-Sant/Falskt
- **Styrkor**: False friends, Long-form

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Språk-MCQ, Konversation, Översättning, Kultur-MCQ
- **Styrkor**: False friends, Long-form

### moonshotai/Kimi-K2.6
- **Svagheter**: Språk-MCQ, Språk-Preference, Konversation, False friends, Kultur-MCQ, Kultur-Sant/Falskt
- **Styrkor**: Long-form

### moonshotai/Kimi-K3
- **Svagheter**: Språk-MCQ, Konversation, Översättning, Kultur-Sant/Falskt
- **Styrkor**: False friends, Long-form

### openai/gpt-oss-120b
- **Svagheter**: Språk-MCQ, Språk-Preference, Konversation, Översättning, Kultur-MCQ, Kultur-Sant/Falskt
- **Styrkor**: Long-form

### zai-org/GLM-4.7-FP8
- **Svagheter**: Språk-MCQ, Språk-Preference, Konversation, Översättning, Kultur-MCQ, Kultur-Sant/Falskt
- **Styrkor**: False friends, Long-form

### zai-org/GLM-5.2
- **Svagheter**: Språk-MCQ, Konversation, Översättning, Kultur-Sant/Falskt
- **Styrkor**: False friends, Long-form, Frengelska-fri

