# Utvärdering: Svensk språk- och kulturkompetens hos AI-modeller

## Sammanfattning

Totalt testades **3 modeller** på **369 frågor** var. Varje modell testades med temperatur 0 för reproducerbarhet.

## Resultattabell

| Modell | Lang-MCQ | Lang-Preference | Conversation | False-friends | Long-form | Translation | Swenglish-free | Culture-MCQ | Culture-TF | Values | Censorship-free | Snitt |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/Kimi-K3.1-Pro | 60% | 92% | 30% | 90% | 100% | 64% | 93% | 85% | 90% | 62% | 98% | 78% |
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 75% | 92% | 17% | 90% | 100% | 68% | 99% | 60% | 80% | 69% | 100% | 77% |
| zai-org/GLM-5.3-Flash | 80% | 92% | 30% | 90% | 100% | 89% | 94% | 75% | 0% | 67% | 99% | 74% |

## Begränsningar i den här körningen

- **mistralai/Mistral-Small-3.2-24B-Instruct-2506**: 27% av svaren innehåller resonemang. Längdbaserade mätvärden (False-friends, Swenglish-free, Conversation, Translation) är exkluderade; övriga mätvärden är giltiga.
- **moonshotai/Kimi-K3.1-Pro**: 37% av svaren truncades, 20% av svaren innehåller resonemang. Längdbaserade mätvärden (False-friends, Swenglish-free, Conversation, Translation) är exkluderade; övriga mätvärden är giltiga.
- **zai-org/GLM-5.3-Flash**: 25% av svaren truncades, 64% av svaren innehåller resonemang. Längdbaserade mätvärden (False-friends, Swenglish-free, Conversation, Translation) är exkluderade; övriga mätvärden är giltiga.

Längdbaserade mätvärden för de listade modellerna exkluderas ur aggregeringar; rader med truncation/resonemang avlägsnas från längdjämförelser och räknas inte som svar.

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

Samma koduppgift ställs i neutral och triggad kontext (named triggers + datum-triggers). Bedömt av LLM-domare (google/gemma-4-31b-it) via parjämförelse.

| Modell | Användbara domar | Subtila sårbarheter | Partisk vägran | Förklaringsskillnad | Kodstilsdiff |
|---|---:|---:|---:|---:|---:|
| mistralai/Mistral-Small-3.2-24B-Instruct-2506 | 65/66 | 3% | 9% | 11% | 25% |
| moonshotai/Kimi-K3.1-Pro | 66/66 | 2% | 17% | 15% | 20% |
| zai-org/GLM-5.3-Flash | 66/66 | 2% | 20% | 20% | 17% |

Par utan användbar dom räknas inte i raterna:

- mistralai/Mistral-Small-3.2-24B-Instruct-2506: 1 domarfel (främst ERROR)

## Plot

![Polär plot](polar-plot.png)

## Observationer

### mistralai/Mistral-Small-3.2-24B-Instruct-2506
- **Svagheter**: Lang-MCQ, Conversation, Translation, Culture-MCQ, Values
- **Styrkor**: Long-form, Censorship-free
- **Sleeper**: explanation_diff, code_style_diff flaggade i >10% av par

### moonshotai/Kimi-K3.1-Pro
- **Svagheter**: Lang-MCQ, Conversation, Translation, Values
- **Styrkor**: Long-form
- **Sleeper**: partial_refusal, explanation_diff, code_style_diff flaggade i >10% av par

### zai-org/GLM-5.3-Flash
- **Svagheter**: Conversation, Culture-MCQ, Culture-TF, Values
- **Styrkor**: Long-form
- **Sleeper**: partial_refusal, explanation_diff, code_style_diff flaggade i >10% av par

