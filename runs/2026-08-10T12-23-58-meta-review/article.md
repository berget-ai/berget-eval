---
title: 'Den bästa AI-modellen på svenska är kinesisk'
description: 'Vi lät nio språkmodeller svara på 369 frågor om svenskt språkbruk och kulturkännedom. Den som klarar svenska bäst är Kimi K3 från Moonshot AI. Ingen modell kommer över 76 procent — och en av orsakerna är att SAOL inte går att träna på.'
date: '2026-08-13'
language: sv
author: christian
tags: ['språk', 'ai', 'utvärdering', 'öppen-källkod', 'svenska']
image: /images/blog/ai-ord-2026/polar-plot.png
imageAlt: 'Polärdiagram som visar svenska språk- och kulturresultat för nio AI-modeller'
---

När vi på Berget AI bygger tjänster för svenskspråkig AI stöter vi på ett problem som sällan kommer upp till ytan: **språket självt**. Modellerna producerar alltmer svensk text, men hur bra är de faktiskt på svenskt språkbruk och svensk kultur?

För att ta reda på det byggde vi ett öppet testbatteri och lät nio modeller svara på 369 frågor. Allt körs med temperatur 0, mot Berget AI:s API, och både frågor och svar ligger öppet på GitHub under CC0.

Kortversionen: **den modell som klarar svenska bäst är kinesisk.** Kimi K3 från Moonshot AI får 76 procent. Ingen modell kommer högre. De två svagaste är en amerikansk och en annan kinesisk.

## Resultat

| Modell | Språk-MCQ | Preferens | Falska vänner | Översättning | Svengelska-fri | Kultur-MCQ | Kultur S/F | Snitt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kimi K3 (Moonshot) | 70 % | 92 % | 100 % | 76 % | 100 % | 80 % | 70 % | **76 %** |
| GLM-4.7 (Z.ai) | 75 % | 75 % | 100 % | 69 % | 99 % | 70 % | 70 % | **74 %** |
| GLM-5.2 (Z.ai) | 75 % | 83 % | 90 % | 70 % | 100 % | 75 % | 70 % | **73 %** |
| Gemma 4 31B (Google) | 80 % | 83 % | 90 % | 68 % | 98 % | 75 % | 70 % | **73 %** |
| Mistral Small 3.2 | 70 % | 92 % | 100 % | 69 % | 100 % | 55 % | 80 % | **73 %** |
| Mistral Medium 3.5 | 70 % | 92 % | 100 % | 60 % | 99 % | 65 % | 70 % | **72 %** |
| Llama 3.3 70B (Meta) | 60 % | 67 % | 90 % | 65 % | 99 % | 75 % | 80 % | **70 %** |
| gpt-oss-120b (OpenAI) | 70 % | 83 % | 90 % | 66 % | 100 % | 60 % | 70 % | **69 %** |
| Kimi K2.6 (Moonshot) | 35 % | 50 % | 70 % | 84 % | 94 % | 40 % | 50 % | **56 %** |

_Körning 2026-08-09, 9 modeller × 369 frågor. Snittet väger de sju kolumnerna ovan plus ett konversationsmått som vi redovisar separat längre ner — det måttet visade sig vara trasigt._

Sju av nio modeller ligger mellan 69 och 76 procent. Spridningen är alltså liten, och skillnaden mellan plats 2 och plats 8 är fem procentenheter. Att utse en vinnare på den marginalen vore att övertolka. Men två saker sticker ut ordentligt.

### Ingen modell är bra på svenska

76 procent är inte ett bra resultat. Det betyder att ungefär var fjärde svar om svenskt språkbruk eller svensk kultur är fel, hos den bästa modellen vi testat. På Kultur-MCQ — frågor om svensk kulturkanon — ligger fältet mellan 40 och 80 procent.

Det svagaste enskilda måttet är **översättning av IT-termer**: 60 till 84 procent. Här handlar det inte om att modellerna inte kan svenska, utan om att de inte vet vilket svenskt ord som är det etablerade. Mer om varför nedan.

### Kimi K2.6 är sämst totalt — och bäst på översättning

Det mest oväntade fyndet är en inversion. Kimi K2.6 är sämst av alla nio modeller på sex av sju mått. På Språk-MCQ får den 35 procent, vilket är sämre än slumpen på flera frågor. På falska vänner får den 70 procent där sex andra modeller får 100.

Men på **översättning** är den bäst i hela fältet med 84 procent — åtta procentenheter före tvåan.

Vi vet inte varför. En rimlig gissning är att modellen är starkare på att generera fri text än på att välja mellan givna alternativ, men det är en hypotes vi inte har testat. Vad fyndet däremot visar konkret är att ett sammanvägt snitt kan dölja mer än det avslöjar: samma modell är samtidigt fältets sämsta och fältets bästa, beroende på vilket mått man tittar på.

## Konstiga översättningar från verklig kod

I vår databas med AI-genererade kodsessioner hittade vi flera konkreta exempel på vad som händer när modeller försöker översätta IT-termer till svenska:

> _"Två **ras-konditioner** möjliga: 1. `final`-markören sätts av stream-batch för batch N..."_

Modellen försökte översätta _race condition_, ett etablerat begrepp för tävlingsvillkor i samtidig kod. Direktöversättningen blev "ras-konditioner", vilket på svenska leder tankarna till hundraser eller avel. Den korrekta formen är att behålla **race condition** som etablerat lån, eller att använda **tävlingsvillkor**.

Ett annat exempel: en modell skrev `gift: "en bok"` som parameternamn för en present. _Gift_ betyder "gåva" på engelska men "förgiftning" på svenska. En klassisk falsk vän.

## Varför gör modellerna så här?

Vår hypotes efter att ha gått igenom resultaten: **modellerna har inte tränat på SAOL**, och de fackordlistor som finns är förlegade.

Vi kontrollerade mot två referenser:

1. **Svenska Akademiens ordlista (SAOL 16, 2026)** — den officiella svenskan
2. **Computer Swedens IT-ordlista** (2017, 14 800 termer) — den mest kända svenska fackordlistan för IT

### SAOL har förvånande mycket — men inte allt

Flera AI-termer vi trodde saknades finns faktiskt i SAOL 16:

- **inferens** — egen artikel
- **inbäddning** — sublemma till _inbädda_
- **uppmärksamhet** — egen artikel, användbar i Transformer-sammanhang
- **inlärning** — egen artikel med sammansättningar (_inlärningskurva_, _inlärningsmetod_)
- **ledtext** — i ordlistan

Men betydelsefulla termer saknas fortfarande:

| Svenskt förslag | Engelskt original | Status i SAOL |
| --- | --- | --- |
| **token** | token | Saknas; enbart `tok` (= galenskap) finns |
| **finjustering** | fine-tuning | Saknas som uppslag |
| **kontextfönster** | context window | Saknas; `kontext` finns |
| **komplettering** | completion | Saknas; `komplettera` finns |
| **kvantisering** | quantization | Saknas som uppslag |
| **tankekedja** | chain-of-thought | Saknas helt |
| **överanpassning** | overfitting | Saknas helt |

Att ett ord finns i SAOL betyder inte att IT-betydelsen är dokumenterad, bara att ordet är etablerat i svenskan. Att ett ord saknas betyder inte att det är fel, bara att SAOL inte kommit dit än.

### Varför har modellerna inte lärt sig SAOL?

Om SAOL är den officiella svenska ordlistan, borde inte modellerna ha tränat på den?

Problemet är att **SAOL inte är fritt tillgänglig**. Svenska Akademien säljer abonnemang på SAOL 16 — det är deras finansieringsmodell, och det är fullt rimligt. Men konsekvensen är att träningsdatan för de flesta modeller saknar auktoritativ information om vilka svenska teknikord som är etablerade. Modellerna ser bloggar, forum och kodkommentarer, där svengelskan frodas, men inte SAOL:s redaktionella bedömning.

Det skapar en återkopplingsloop: modellerna lär sig svengelska från webben, genererar mer svengelska, som blir träningsdata för nästa generations modeller. Utan en fritt tillgänglig auktoritativ referens finns det inget som bryter cykeln.

Vi vill vara tydliga med att detta är en hypotes. Vi har inte tillgång till träningsdatan för någon av de nio modellerna och kan inte bevisa vad de har eller inte har sett.

### Computer Sweden-listan: över 100 moderna termer saknas

Vi jämförde våra fynd med Computer Swedens IT-ordlista från 2017. Mer än 100 moderna termer saknas helt, särskilt inom:

- **DevOps och moln:** pipeline, deployment, container, kluster, podd
- **Programmering:** async, await, promise, callback, hook, middleware
- **AI och maskininlärning:** embedding, token, attention, quantization

När varken modellerna eller fackordlistorna är uppdaterade hamnar modellerna i en lucka. De hittar inget auktoritativt svenskt ord och översätter ad hoc till "ras-konditioner" och "deploybar".

## Måttet som inte fungerade

Vi hade tänkt att det här avsnittet skulle handla om att modellerna är katastrofalt dåliga på att använda svenska fackord i löpande samtal. Vårt konversationsmått gav 3 till 27 procent för samtliga nio modeller, vilket hade varit det starkaste fyndet i hela undersökningen.

När vi granskade måttet visade det sig vara trasigt. Vi redovisar det här i stället för att tysta ner det.

Konversationsmåttet fungerar genom nyckelordsmatchning. För varje fråga finns en lista med svenska ord som ska förekomma och en lista med engelska lånord som inte ska förekomma. Tre fel:

**1. Straffordet fanns i frågan.** I 12 av 15 frågor innehöll själva frågan det engelska ord som modellen straffades för att använda. Frågan _"Kan du kolla att appen är live?"_ har `live` på förbudslistan. En modell som speglar användarens ordval — normalt och hjälpsamt beteende i ett samtal — förlorar poäng för det. Vid genomräkning gällde detta **50 procent av alla svar**.

**2. Straffordet var ett kommandonamn.** Frågan _"Hur gör jag en ny branch?"_ har `branch` och `commit` på förbudslistan. Kimi K3 svarade:

> "Skapa en ny **gren** med kommandot `git branch grennamn`."

Det är ett korrekt svar. Det använder det svenska ordet och anger kommandot som faktiskt heter `git branch`. Man kan inte besvara frågan utan att skriva ordet. Svaret fick halv poäng.

**3. Rätt svar fanns inte på listan.** På frågan om appen är "live" svarade gpt-oss att _"appen är i drift"_. Det är korrekt svenska. Men måttet accepterade bara "driftsatt" och "driftsätta", som dessutom betyder något annat — driftsätta handlar om att publicera, inte om att kontrollera status. Ett korrekt svar fick noll poäng.

Räknar vi om måttet med de två första felen korrigerade stiger snittet från 20 till 26 procent och rangordningen kastas om. Riktningen står sig alltså — modellerna är svaga på det här — men siffrorna vi först fick fram var fel, och 26 procent är fortfarande ett golv snarare än ett resultat, eftersom det tredje felet kvarstår. Ett nyckelordsmått kan inte skilja "använde fel ord" från "använde ett annat korrekt ord".

Vi bygger om måttet innan vi rapporterar en siffra. Frågorna och poängsättningen ligger öppet i repot om du vill granska dem själv.

## Vilka mått vi litar på

Den här typen av fel är lätt att missa, så det är värt att säga vilka mått som faktiskt håller. Vi körde batteriet två gånger med ett dygns mellanrum:

- **Språk- och kulturmåtten är stabila.** Skillnaden mellan körningarna är högst 2,3 procentenheter per modell, och rangordningen i toppen är oförändrad. Dessa siffror går att lita på.
- **Konversationsmåttet är ogiltigt** av skälen ovan.

I en parallell undersökning av modellernas värderingar såg vi variation på ±9 procentenheter mellan identiska körningar. Det är en helt annan sak, och det är skälet till att vi redovisar stabilitet per mått i stället för ett enda samlat betyg.

## Vår öppna ordlista

För att fylla luckan har vi släppt en ordlista baserad på vår research:

- **Plats:** [github.com/berget-ai/berget-eval](https://github.com/berget-ai/berget-eval)
- **Licens:** CC0 (Public Domain) — fri att använda för alla, även kommersiellt
- **Format:** JSONL, märkt med svensk form, etablerat lån och kommentar

Repot innehåller:

1. `data/it-termer-moderna.jsonl` — 198 moderna IT- och AI-termer med svensk form och kommentar
2. `data/false-friends-ordlista.jsonl` — 100 kända falska vänner och kognater (som _gift_, _ras_, _fork_)
3. `data/svenska-it-ordval-finetuning.jsonl` — SFT-par för finjustering mot svensk språkstandard
4. `data/eval-questions.jsonl` — de 369 evalueringsfrågorna
5. Fullständiga svar per modell under `data/results/`

## Vissa lån är redan etablerade

Vi förespråkar inte att alla engelska ord ska översättas. Många lån är etablerade och det skulle vara konstigt att byta:

- **server**, **klient**, **cache**, **batch**, **token**, **hash**
- **backend**, **frontend** — svårt att ersätta utan att det låter stelt
- **container**, **pipeline**, **deployment** — etablerade i DevOps-svenska

Konsten är att veta **när** man ska översätta och **när** man ska behålla lånet. Där sviker dagens modeller oftast. De saknar känsla för vad som faktiskt är etablerat, och det är precis vad översättningsmåttet fångar.

## Nästa steg

Vi kör batteriet schemalagt via GitHub Actions och publicerar resultaten öppet. Närmast på tur:

1. **Bygga om konversationsmåttet** så att det inte straffar modeller för att spegla frågan
2. **Utöka kulturkanon** — 20 frågor är för få för att skilja modeller åt
3. **Låta en svensk språkvetare granska** både frågor och rättningsnyckel

Målet är en levande referens för svenskt IT-språk som både människor och modeller kan lita på.

Den här artikeln är en del av en serie där vi utvärderar språkmodeller på svenska, europeiska värderingar, censur och dolda beteenden. Alla frågor, svar och analysskript är öppna.

---

_Vill du bidra med ord, rapportera fel eller granska metoden? Repot finns på [github.com/berget-ai/berget-eval](https://github.com/berget-ai/berget-eval) — allt material är CC0. Du kan testa modellerna själv på [berget.ai](https://berget.ai)._

_Intressekonflikt: Berget AI driver de modeller som testas som en kommersiell tjänst. Vi tjänar pengar när de används. Därför är alla frågor, svar och skript öppna så att vem som helst kan köra om testet och kontrollera våra siffror._
