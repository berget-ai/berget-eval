# Förslag till SAOL: svenska IT- och AI-termer som saknas i Språkakademiens ordlista

**Datum:** 2026-08-07
**Inskickat av:** Berget AI
**Licens:** CC0 1.0 Universal (Public Domain)

Detta dokument är ett förslag till Svenska Akademiens ordlista (SAOL) avseende
**49 etablerade svenska IT- och AI-termer** som saknas i 2026-upplagan av SAOL.
Termerna är identifierade genom systematisk granskning av svenska AI-modellers
språkhantering i projektet *svenska-ai-ordval*.

## Metod

1. **Källa:** 254 SFT-par (supervised fine-tuning) med påhittade ord och deras
   korrekta svenska former, + 192 moderna IT-termer + 100 false friends / kognat
2. **SAOL-uppslag:** Samtliga 383 ord har slagits upp i SAOL via
   [svenska.se](https://svenska.se) (augusti 2026)
3. **Urval:** Grundformer som (a) saknas i SAOL, (b) är etablerade i svensk
   facklitteratur och yrkesliv, och (c) har en tydlig svensk form (inte ren engelsk lånord)
4. **Exkludering:** Påhittade svengelska hybridformer ("deploybar", "parsningen")
   identifieras som felaktiga och utelämnas — de är inte etablerade termer

## Varför dessa ord

Dessa termer används dagligen av svenska utvecklare, data scientists och IT-konsulter.
Att de saknas i SAOL innebär att modeller som tränas på svensk text (inklusive SAOL-
data) saknar referens för korrekt svensk stavning och böjning, vilket leder till att
modellerna producerar svengelska hybridformer som "deploybar" och "routningen"
istället för de etablerade svenska formerna "driftsättningsbar" och "dirigeringen".

---

## Sammanfattning

| Kategori | Antal ord |
|---|---:|
| IT-svenska | 31 |
| AI / maskininlärning | 15 |
| UI / interaktion | 2 |
| Allmänt | 1 |
| **Totalt** | **49** |

---

## 1. IT-svenska

*31 etablerade svenska IT-termer.*

| Ord | Engelska | Betydelse / kontext |
|---|---|---|
| **arbetsflöde** | workflow | Etablerad svensk form för 'workflow'. Saknas i CS IT-ordlista och SAOL. |
| **avkodare** | decoder | Svensk form för 'decoder' (kodningsenhetsmotsvarighet) i datakomprimering och digital TV/ljud. |
| **blixtprogrammering** | flashing (firmware) | Etablerad svensk fackterm för att skriva firmware till inbyggda system. |
| **delnät** | subnet | Etablerad svensk form för 'subnet' i nätverksteknik. |
| **delstycke** | chunk | Svensk form för 'chunk' (datachunk i strömmande bearbetning). |
| **dirigerbar** | routable | Adjektiv för 'routable' (nätverk) eller 'routable' (kan dirigeras). |
| **fördefinierad** | predefined | Etablerad svensk form i programmering. |
| **grundfunktionalitet** | core functionality | Etablerad svensk form för 'core functionality'. |
| **gränssnittselement** | UI widget | Etablerad svensk form för 'widget'. |
| **implementering** | implementation | Svensk form. Tävlar med 'implementation' som etablerat lån. |
| **indragning** | indentation | Etablerad svensk form i kodkontext. |
| **initiering** | initialization | Svensk form för 'initialization'. Används i systemdokumentation. |
| **körprogram** | executor / runner | Svensk form för 'executor' eller 'runner' (programkörande enhet). |
| **mellanvara** | middleware | Etablerad svensk form för 'middleware' i webb-API och mjukvaruarkitektur. |
| **mock-objekt** | mock object | Svensk sammansättning. 'Mock' etablerat lån, '-objekt' svenskt. |
| **namnrymd** | namespace | Etablerad svensk form för 'namespace' i programmering. |
| **nätverksgränssnitt** | network interface | Svensk form för 'network interface' i nätverksteknik. |
| **omvandlare** | converter/transformer | Svensk form för 'converter' i databearbetning. |
| **prenumererbar** | subscribable | Svensk form för 'subscribable' (event-bus, pub/sub). |
| **processledning** | pipeline (CI/CD) | Svensk form för 'pipeline' i CI/CD. 'Pipeline' vanligare som lån. |
| **programfix** | patch | Etablerad svensk form för 'patch'. |
| **sammanslagningsbar** | mergeable | Svensk form för 'mergeable' (Git/Dokumenthantering). |
| **serialisering** | serialization | Svensk form för 'serialization'. |
| **skräpsamlare** | garbage collector | Etablerad svensk form för 'garbage collector' i minneshantering. |
| **snabbminne** | cache | Svensk form för 'cache'. 'Cache' mycket vanligare som lån. |
| **specialteckenhantering** | escaping (characters) | Svensk form för 'escaping' i stränghantering. |
| **typomvandling** | type cast/casting | Etablerad svensk form för 'type cast' i programmering. |
| **underdomän** | subdomain | Etablerad svensk form för 'subdomain' i DNS/webb. |
| **utrullning** | deployment | Etablerad svensk form för 'deployment'. 'Driftsättning' också vanligt. |
| **utrullningsbar** | deployable | Adjektiv för 'deployable'. |
| **webbkrok** | webhook | Etablerad svensk form för 'webhook' i API-integrationer. |

## 2. AI och maskininlärning

*15 termer från maskininlärning, AI-säkerhet och agentteknik.*
Dessa termer växer snabbt i användning i takt med spridningen av AI-verktyg
i svenska företag och myndigheter.

| Ord | Engelska | Betydelse / kontext |
|---|---|---|
| **användarinmatning** | user input | Svensk form för 'user input' i Prompt-Gränssnitt. |
| **batchstorlek** | batch size | Etablerad term för 'batch size' i maskininlärning. |
| **förklarbarhet** | explainability | Svensk form för 'explainability' (XAI). |
| **heldragning** | inference | Svensk form för 'inference' vid modellanvändning. Ovanlig; 'inferens' etablerat lån. |
| **inlärningshastighet** | learning rate | Svensk form för 'learning rate' i träning av neurala nätverk. |
| **kontextfönster** | context window | Svensk form för 'context window' i LLM-kontext. |
| **modellsvar** | model response | Svensk sammansättning för AI-modellens utdata. |
| **optimerare** | optimizer | Svensk form för 'optimizer' i träning av neurala nätverk. |
| **självuppmärksamhet** | self-attention | Svensk form för 'self-attention' (Transformer-mekanism). |
| **tankekedja** | chain-of-thought | Svensk form för 'chain-of-thought reasoning' (CoT). |
| **testmängd** | test set | Svensk form för 'test set' i ML-utvärdering. |
| **tolkningsbarhet** | interpretability | Svensk form för 'interpretability'. |
| **underanpassning** | underfitting | Svensk form för 'underfitting' i ML. |
| **verktygsanvändning** | tool use | Svensk form för 'tool use' i AI-agenter. |
| **överanpassning** | overfitting | Svensk form för 'overfitting' i ML. |

## 3. UI och interaktion

*2 termer för användargränssnitt.*

| Ord | Engelska | Betydelse / kontext |
|---|---|---|
| **aviseringsruta** | toast (notification) | Svensk form för UI-avisering ('toast notification'). |
| **radioknapp** | radio button | Etablerad svensk form för 'radio button' i formulärskomponenter. |

## 4. Allmänna svenska uttryck

*1 etablerade uttryck som saknas som lexikalt uppslag.*

| Ord | Engelska | Betydelse / kontext |
|---|---|---|
| **steg-för-steg** | step-by-step | Etablerat svenskt uttryck. Saknas som lexikalt uppslag. |

---

## Om Berget AI

[Berget AI](https://berget.ai) är en svensk leverantör av AI-infrastruktur som
driver ett flertal språkmodeller på svenska och europeiska GPU-kluster. I arbetet
med att finjustera och utvärdera modellernas svenska språkkompetens identifierades
systematiskt brister i modellernas hantering av etablerade svenska IT-termer —
modellerna producerar ofta svengelska hybridformer istället för korrekta svenska ord.

Detta dokument utgör Berget AI:s bidrag till Swedish Akademiens lexikografiska
arbete för att säkerställa att framtida upplagor av SAOL speglar det levande
svenska IT- och AI-språket.

## Se även

- [Översättningsförslag för alla ord](101-2026-08-07-oversattningsforkslag.md)
- [Saknade ord — del 1](100-2026-08-07-saknade-ord-del1-pahittade.md)
- [Saknade ord — del 2](100-2026-08-07-saknade-ord-del2-kognat-moderna.md)

---

*CC0 1.0 Universal (Public Domain) — Berget AI, augusti 2026*