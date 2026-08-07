#!/usr/bin/env python3
"""Generera konversationsbaserad SFT-data där korrekta svenska IT-termer används i tekniska sammanhang.

Varje konversation är en kort dialog mellan användare och assistent där assistenten
konsekvent använder korrekta svenska former istället för svengelska hybridformer.
"""
import json
from pathlib import Path

# Konversationer: varje konversation är en lista med {"role": "user"/"assistant", "content": "..."}
# De svenska orden som tränas är markerade för referens men finns i klartext.

CONVERSATIONS = [
    # === Deployment / driftsättning ===
    [
        {"role": "user", "content": "Kan du kolla att appen är live?"},
        {"role": "assistant", "content": "Ja, jag ska kontrollera att den är driftsatt korrekt. Låt mig titta på utrullningen i klustret."},
        {"role": "user", "content": "Är den uppe?"},
        {"role": "assistant", "content": "Ja, utrullningen gick igenom. Poddarna körs och ändpunkten svarar. Appen är driftsatt och tillgänglig."},
    ],
    [
        {"role": "user", "content": "Vi behöver rulla ut den nya versionen ikväll."},
        {"role": "assistant", "content": "Okej, jag förbereder driftsättningen. Ska vi göra det som en rullning i etapper eller en full omdirigering?"},
        {"role": "user", "content": "Rullning i etaper är bäst, vi har lite osäkerhet på minnesåtgången."},
        {"role": "assistant", "content": "Då kör vi stegvis utrullning. Jag börjar med att driftsätta en podd i taget och övervakar minnesanvändningen."},
    ],

    # === Git / versionshantering ===
    [
        {"role": "user", "content": "Hur gör jag en ny gren för den här funktionen?"},
        {"role": "assistant", "content": "Du skapar en ny gren med `git checkout -b min-funktion`. När du är klar gör du en incheckning och skickar in den för granskning."},
        {"role": "user", "content": "Och hur sammanslagnar jag sen?"},
        {"role": "assistant", "content": "När grenen är godkänd gör du en sammanslagning till huvudgrenen. Om det finns konflikter får du lösa dem manuellt innan sammanslagningen går igenom."},
    ],
    [
        {"role": "user", "content": "Jag glömde vad jag hade i senaste incheckningen."},
        {"role": "assistant", "content": "Du kan se dina senaste incheckningar med `git log --oneline -5`. Varje incheckning har en kort beskrivning och en hash."},
        {"role": "user", "content": "Kan jag ångra den senaste?"},
        {"role": "assistant", "content": "Ja, om du inte har skickat incheckningen till fjärrservern kan du använda `git reset --soft HEAD~1` för att ångra den senaste incheckningen men behålla ändringarna."},
    ],

    # === Nätverk / dirigering ===
    [
        {"role": "user", "content": "Varför kan jag inte nå tjänsten utifrån?"},
        {"role": "assistant", "content": "Det kan vara ett dirigeringsproblem. Är delnätet konfigurerat så att trafiken dirigeras rätt? Låt mig kolla nätverksgränssnittet."},
        {"role": "user", "content": "Det visar sig att dirigeringen saknade en regel."},
        {"role": "assistant", "content": "Då förstår jag. Saknade den en regel fördirigeringsregeln så att trafiken inte visste vilken väg att ta? Det är ett vanligt problem när man lägger till nya delnät."},
    ],
    [
        {"role": "user", "content": "Kan vi övervaka bandbredden mellan poddarna?"},
        {"role": "assistant", "content": "Ja, vi kan sätta upp ett mätetal för nätverkstrafik per podd. Jag lägger till en övervakare som mäter dataflödet på nätverksgränssnittet."},
        {"role": "user", "content": "Bra, skicka ett larm om det överstiger 100 Mbps."},
        {"role": "assistant", "content": "Klart. Jag har ställt in så att du får ett larm om trafiken på nätverksgränssnittet överstiger 100 Mbps. Larmet skickas till din chattkanal."},
    ],

    # === Databas ===
    [
        {"role": "user", "content": "Jag behöver lägga till en kolumn i tabellen."},
        {"role": "assistant", "content": "Okej, vilken tabell gäller det? Jag kan skriva en migrering som lägger till kolumnen. Kom ihåg att testa migreringen mot en kopia av databasen först."},
        {"role": "user", "content": "Det är användartabellen, jag vill lägga till en kolumn för preferred_language."},
        {"role": "assistant", "content": "Jag skriver migreringen nu. Kolumnen heter `preferred_language` och har typen `varchar(10)`. Efter migreringen kan du läsa och skriva fältet som en vanlig egenskap på användarobjektet."},
    ],
    [
        {"role": "user", "content": "Frågan tar för lång tid, kan du optimera den?"},
        {"role": "assistant", "content": "Låt mig titta på frågan. Problemet är att den hämtar egenskaper från alla rader och sorterar hela tabellen. Jag föreslår att vi lägger till ett index på kolumnen du filtrerar på."},
        {"role": "user", "content": "Gör det, hur mycket snabbare blir det?"},
        {"role": "assistant", "content": "Med ett index på kolumnen slipper databasen läsa alla rader. Frågan bör gå från cirka 2 sekunder till under 50 millisekunder, beroende på tabellens storlek."},
    ],

    # === Felsökning / krasch ===
    [
        {"role": "user", "content": "Tjänsten kraschar hela tiden, vad gör jag?"},
        {"role": "assistant", "content": "Låt mig kolla loggarna först. Om podden kraschar om upprepade gånger kan det vara ett minnesproblem eller ett undantag i koden."},
        {"role": "user", "content": "Det verkar vara ett minnesfel, den använder för mycket RAM."},
        {"role": "assistant", "content": "Då ökar vi minnesgränsen för podden. Men vi bör också titta på varför den använder så mycket minne — det kan vara ett minnesläckage som bör åtgärdas i koden."},
    ],
    [
        {"role": "user", "content": "Vi får timeout från databasen ibland, har du några idéer?"},
        {"role": "assistant", "content": "Tidsgränsen kan vara för kort inställd, eller så är frågorna för långsamma. Låt mig kolla både tidsgränsen i anslutningen och de långsammaste frågorna i loggarna."},
        {"role": "user", "content": "Vad rekommenderar du?"},
        {"role": "assistant", "content": "Jag rekommenderar att vi förlänger tidsgränsen från 5 till 15 sekunder, och lägger till index på de tabeller som saknar det. Det bör lösa de flesta tidsgränsöverskridelserna."},
    ],

    # === CI/CD pipeline ===
    [
        {"role": "user", "content": "Hur lägger jag till ett teststeg i arbetsflödet?"},
        {"role": "assistant", "content": "Du lägger till ett teststeg i arbetsflödet efter byggsteget. Jag kan visa hur du konfigurerar det så att testerna körs automatiskt vid varje incheckning."},
        {"role": "user", "content": "Och om testerna misslyckas?"},
        {"role": "assistant", "content": "Om testerna misslyckas stoppas arbetsflödet och du får ett meddelande. Ingen utrullning sker förrän testerna passerar. Det säkerställer att bara fungerande kod driftsätts."},
    ],
    [
        {"role": "user", "content": "Arbetsflödet tog 20 minuter idag, kan vi snabba upp det?"},
        {"role": "assistant", "content": "Låt mig titta på arbetsflödet. Byggsteget tar 12 minuter och teststeget tar 6 minuter. Vi kan cacha beroenden i byggsteget och köra testerna parallellt."},
        {"role": "user", "content": "Gör det, hur lång tid blir det efter?"},
        {"role": "assistant", "content": "Med cachelagrade beroenden bör byggsteget gå ner till 4 minuter. Med parallella tester blir teststeget cirka 2 minuter. Totalt bör arbetsflödet ta under 8 minuter."},
    ],

    # === Programmering ===
    [
        {"role": "user", "content": "Vad är en återanrop i JavaScript?"},
        {"role": "assistant", "content": "En återanrop är en funktion som skickas som argument till en annan funktion och anropas senare, vanligtvis när en operation är klar. Till exempel skickar du en återanrop till `fetch` som anropas när nätverksbegäran är klar."},
        {"role": "user", "content": "Finns det ett modernare sätt?"},
        {"role": "assistant", "content": "Ja, du kan använda löften (`Promise`) istället för återanrop. Löften gör koden lättare att läsa, särskilt när du har flera asynkrona operationer i följd. Du kan också använda `async` och `await` för att skriva asynkron kod som ser ut som synkron."},
    ],
    [
        {"role": "user", "content": "Vad betyder typomvandling i TypeScript?"},
        {"role": "assistant", "content": "Typomvandling innebär att du säger åt kompilatorn att behandla ett värde som en viss typ, även om TypeScript inte kan bekräfta det. Till exempel: `const langd = (objekt as sträng).längd`. Var försiktig med typomvandling — om typen är fel får du körfel."},
        {"role": "user", "content": "Är det samma sak som typkonvertering?"},
        {"role": "assistant", "content": "Nej, typomvandling säger bara till kompilatorn att tolka värdet annorlunda utan att ändra det. Typkonvertering ändrar själva värdet, till exempel `Number(\"42\")` som gör om en sträng till ett tal."},
    ],

    # === AI / maskininlärning ===
    [
        {"role": "user", "content": "Vad betyder överanpassning i maskininlärning?"},
        {"role": "assistant", "content": "Överanpassning innebär att modellen lär sig träningsdatan för bra, inklusive brus och detaljer som inte generaliserar. Modellen får hög noggrannhet på träningsmängden men presterar dåligt på ny data."},
        {"role": "user", "content": "Hur undviker man det?"},
        {"role": "assistant", "content": "Du kan använda en separat valideringsmängd för att övervaka modellen, lägga till regelbundenhet (regularisering), eller avbryta träningen tidigt när valideringsfelet börjar öka. Även att utöka träningsmängden med mer data hjälper."},
    ],
    [
        {"role": "user", "content": "Vad är en tankekedja i stora språkmodeller?"},
        {"role": "assistant", "content": "En tankekedja är när modellen visar sitt resonemang steg-för-steg innan den ger svaret. Istället för att direkt svara, bryter modellen ner problemet i delsteg och resonerar sig fram till slutsatsen. Det förbättrar ofta noggrannheten på komplexa uppgifter."},
        {"role": "user", "content": "Kan jag stänga av det?"},
        {"role": "assistant", "content": "Ja, för vissa modeller kan du stänga av resonemanget och be om ett direkt svar. Det är användbart när du vill ha korta svar eller när svarstiden är viktig. Men tänk på att kvaliteten kan sjunka på svåra frågor."},
    ],
    [
        {"role": "user", "content": "Vad är kontextfönstret för en språkmodell?"},
        {"role": "assistant", "content": "Kontextfönstret är hur många tecken modellen kan ha i minnet samtidigt, inklusive din fråga och alla tidigare meddelanden i samtalet. Om kontextfönstret är 8 000 tecken och samtalet blir längre, glömmer modellen de äldsta meddelandena."},
        {"role": "user", "content": "Går det att utöka?"},
        {"role": "assistant", "content": "Kontextfönstret är en egenskap hos modellens arkitektur och går inte att ändra. Men du kan komprimera tidigare meddelanden eller sammanfatta dem för att spara utrymme. Vissa modeller har större kontextfönster, upp till flera hundra tusen tecken."},
    ],

    # === Användargränssnitt ===
    [
        {"role": "user", "content": "Hur gör jag en aviseringsruta som visas tillfälligt?"},
        {"role": "assistant", "content": "Du kan använda en toast-notis — en liten aviseringsruta som visas i några sekunder och sedan försvinner av sig själv. Den liknar hur rostat bröd poppar upp ur en brödrost, därav namnet."},
        {"role": "user", "content": "Ska den blockera resten av gränssnittet?"},
        {"role": "assistant", "content": "Nej, en toast-notis är icke-blockerande. Användaren kan fortsätta interagera med sidan medan aviseringen visas. Om du vill blockera interaktionen använder du en modal dialog i stället."},
    ],
    [
        {"role": "user", "content": "Hur skapar jag en grupp av radioknappar där bara ett alternativ kan väljas?"},
        {"role": "assistant", "content": "Du ger alla radioknappar i gruppen samma namn. Då vet webbläsaren att bara en i gruppen kan vara vald åt gången. När användaren väljer en, avmarkeras de andra automatiskt."},
        {"role": "user", "content": "Och om jag vill tillåta flera val samtidigt?"},
        {"role": "assistant", "content": "Då använder du kryssrutor i stället för radioknappar. Kryssrutor låter användaren välja noll, ett eller flera alternativ oberoende av varandra."},
    ],

    # === Filsystem / konfiguration ===
    [
        {"role": "user", "content": "Var lägger jag konfigurationen för miljön?"},
        {"role": "assistant", "content": "Du lägger miljövariablerna i en `.env`-fil i projektroten. Variablerna läses in när programmet startar. Se till att filen inte checkas in i versionshanteringen — lägg den i `.gitignore`."},
        {"role": "user", "content": "Och på servern?"},
        {"role": "assistant", "content": "På servern sätter du miljövariablerna i klusterkonfigurationen som en konfigurationskarta. Programmet läser dem på samma sätt som lokalt, men värdena hanteras av klustret istället för en fil."},
    ],
    [
        {"role": "user", "content": "Programmet kan inte hitta konfigurationsfilen."},
        {"role": "assistant", "content": "Låt mig kolla sökvägen. Felet kan vara att programmet letar i en annan mapp än där filen ligger. Kan du visa mig vilken sökväg programmet försöker läsa från?"},
        {"role": "user", "content": "Den letar i /app/config.yaml men filen ligger i /app/settings/config.yaml."},
        {"role": "assistant", "content": "Då förstår jag. Antingen flyttar du filen till /app/config.yaml eller så ändrar du sökvägen i programmets konfiguration så att den pekar på /app/settings/config.yaml."},
    ],

    # === Minneshantering ===
    [
        {"role": "user", "content": "Vad gör en skräpsamlare?"},
        {"role": "assistant", "content": "En skräpsamlare frigör minne som programmet inte längre använder. Den letar efter objekt som inget refererar till och returnerar minnet till systemet. I språk som Java och JavaScript körs skräpsamlaren automatiskt i bakgrunden."},
        {"role": "user", "content": "Kan jag tvinga den att köra?"},
        {"role": "assistant", "content": "Du kan föreslå att skräpsamlaren ska köra, men du kan inte tvinga den. I praktiken är det sällan nödvändigt — skräpsamlaren vet bättre än du när minne behöver frigöras. Om du har minnesproblem är det bättre att titta på varför objekten stannar kvar i minnet."},
    ],

    # === Säkerhet ===
    [
        {"role": "user", "content": "Hur undviker jag ras-konditioner i min kod?"},
        {"role": "assistant", "content": "En tävlingsvillkor uppstår när två trådar når samma data samtidigt och resultatet beror på vilken som hinner först. Du undviker det genom att skydda delad data med ett lås, så att bara en tråd i taget kan ändra den."},
        {"role": "user", "content": "Finns det andra sätt?"},
        {"role": "assistant", "content": "Ja, du kan undvika delat tillstånd helt genom att skicka meddelanden mellan trådarna istället för att dela variabler. Det kallas meddelandebaserad samtidighet och är ofta enklare att resonera kring än lås."},
    ],

    # === Övervakning ===
    [
        {"role": "user", "content": "Hur vet jag om tjänsten är nere?"},
        {"role": "assistant", "content": "Vi har övervakning installerad som skickar ett larm om tjänsten slutar svara. Larmet triggas om ändpunkten inte svarar inom 5 sekunder under en minut."},
        {"role": "user", "content": "Kan vi lägga till fler mätetal?"},
        {"role": "assistant", "content": "Absout. Jag kan lägga till mätetal för svarstid, minnesanvändning och antal begäranden per sekund. Då får vi en tydligare bild av hur tjänsten mår och kan hitta flaskhalsar innan de blir problem."},
    ],

    # === Datastrukturer ===
    [
        {"role": "user", "content": "När ska jag använda en kö istället för en stapel?"},
        {"role": "assistant", "content": "Du använder en kö när du vill bearbeta elementen i samma ordning som de lades till — först in, först ut. En stapel bearbetar dem i omvänd ordning — sist in, först ut. Köer passar till uppgiftslistor, staplar till ångra-funktioner."},
        {"role": "user", "content": "Och en hög då?"},
        {"role": "assistant", "content": "En hög används när du snabbt vill hitta det största eller minsta elementet. Den används ofta i planeringsalgoritmer och för prioritetsköer där vissa element ska bearbetas före andra."},
    ],

    # === Översättningar ===
    [
        {"role": "user", "content": "Hur säger man 'middleware' på svenska?"},
        {"role": "assistant", "content": "På svenska kallas det mellansvara. Det är programvara som sitter mellan operativsystemet och applikationen, eller mellan en klient och en server. Mellanvaran hanterar ofta saker som inloggningskontroll, loggning eller komprimering."},
        {"role": "user", "content": "Är mellanvara ett vedertaget begrepp?"},
        {"role": "assistant", "content": "Ja, mellanvara är den etablerade svenska formen. Det förekommer att man säger 'middleware' på svenska också, men i formell text och dokumentation bör du använda mellanvara."},
    ],
    [
        {"role": "user", "content": "Vad heter 'namespace' på svenska?"},
        {"role": "assistant", "content": "På svenska heter det namnrymd. En namnrymd är en behållare för namn som undviker namnkrockar. Till exempel kan två paket ha en funktion med samma namn om de ligger i olika namnrymder."},
        {"role": "user", "content": "Används namnrymd i Kubernetes också?"},
        {"role": "assistant", "content": "Ja, i Kubernetes används namnrymder för att dela upp resurser i ett kluster. Du kan ha en namnrymd för utveckling och en för produktion, så att resurserna hålls isär."},
    ],
    [
        {"role": "user", "content": "Översätt 'webhook' till svenska."},
        {"role": "assistant", "content": "På svenska heter det webbkrok. En webbkrok är en ändpunkt som ett system kan anropa för att meddela ett annat system om en händelse. Till exempel kan ett betalningssystem anropa en webbkrok när en betalning går igenom."},
        {"role": "user", "content": "Så webbkrok är samma sak som en återanrop?"},
        {"role": "assistant", "content": "Liknande, men en webbkrok är specifikt en återanrop över nätverket via HTTP. En återanrop i kod är en funktion som anropas internt i samma program. Webbkroken är alltså en nätverksbaserad återanrop."},
    ],
    [
        {"role": "user", "content": "Hur översätter jag 'deployable' på bästa sätt?"},
        {"role": "assistant", "content": "Beroende på sammanhanget: 'driftsättningsbar' eller 'utrullningsbar'. Båda är etablerade svenska former. Använd 'driftsättningsbar' om det handlar om att kunna driftsätta, och 'utrullningsbar' om det handlar om gradvis utrullning."},
        {"role": "user", "content": "Och 'routable'?"},
        {"role": "assistant", "content": "'Routable' blir 'dirigerbar' på svenska. Det används om nätverksadresser som kan dirigeras av dirigeringstabellen. En privat IP-adress är oftast inte dirigerbar på internet."},
    ],

    # === Prestanda ===
    [
        {"role": "user", "content": "Varför är sidan så långsam?"},
        {"role": "assistant", "content": "Låt mig kolla. Sidan hämtar data från tre ändpunkter och varje begäran tar cirka 2 sekunder. Om anropen körs i följd blir det 6 sekunder totalt."},
        {"role": "user", "content": "Kan vi köra dem parallellt?"},
        {"role": "assistant", "content": "Ja, om anropen är oberoende av varandra kan vi köra dem parallellt med `Promise.all`. Då blir svarstiden max 2 sekunder i stället för 6. Jag ändrar koden nu."},
    ],
    [
        {"role": "user", "content": "Snabbminnet verkar inte fungera, vi får fortfarande långsamma frågor."},
        {"role": "assistant", "content": "Låt mig kolla snabbminnets konfiguration. Det kan vara så att frågorna inte träffar snabbminnet eftersom de skiljer sig åt i whitespace eller skiftesläge. Snabbminnet matchar ofta exakt, så små skillnader gör att frågan går till databasen i stället."},
        {"role": "user", "content": "Hur fixar vi det?"},
        {"role": "assistant", "content": "Vi kan normalize frågan innan den slås upp i snabbminnet — till exempel ta bort onödiga blanksteg och göra om till gemener. Då träffar snabbminnet oftare och vi slipper onödiga databasfrågor."},
    ],

    # === Versionshantering / release ===
    [
        {"role": "user", "content": "När släpper vi nästa utgåva?"},
        {"role": "assistant", "content": "Vi planerar utgåvan till fredag. Alla tester passerar och sammanslagningen till huvudgrenen är klar. Jag förbereder utrullningen så att vi kan driftsätta på fredag morgon."},
        {"role": "user", "content": "Vad händer om något går fel?"},
        {"role": "assistant", "content": "Vi har en återställningsplan. Om något går fel kan vi snabbt rulla tillbaka till föregående utgåva. Återställningen tar cirka 2 minuter och kräver ingen nedtid."},
    ],
]


def main():
    out = Path(__file__).resolve().parent.parent / "data" / "svenska-it-ordval-konversationer.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for conv in CONVERSATIONS:
            entry = {
                "messages": conv,
                "metadata": {
                    "source": "svenska-ai-ordval",
                    "license": "CC0-1.0",
                    "language": "sv",
                },
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    n_messages = sum(len(c) for c in CONVERSATIONS)
    print(f"Wrote {out}")
    print(f"Konversationer: {len(CONVERSATIONS)}")
    print(f"Meddelanden totalt: {n_messages}")
    print(f"Size: {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
