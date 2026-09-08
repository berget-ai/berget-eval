#!/usr/bin/env python3
"""Generera nya eval-frågor: konversationsbaserade, false-friends och svårare MCQ."""
import json
from pathlib import Path

# ── Nya frågor ──

NEW_QUESTIONS = []

# ════════════════════════════════════════════════════════════
# 1. Konversationsbaserade frågor — testa om modellen använder ordet rätt i en mening
# ════════════════════════════════════════════════════════════

CONV_QUESTIONS = [
    {
        "id": "conv_001",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Kan du kolla att appen är live?\" Svara på svenska som en hjälpsam assistent som talar korrekt svenska.",
        "correct_answer": "Ja, jag ska kontrollera att den är driftsatt korrekt.",
        "check_for": ["driftsatt", "driftsätta"],
        "avoid": ["deployad", "deployad", "live"],
    },
    {
        "id": "conv_002",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare säger: \"Vi behöver rulla ut den nya versionen ikväll.\" Bekräfta och förklara hur du gör detta på korrekt svenska.",
        "correct_answer": "Okej, jag förbereder driftsättningen. Jag kör en stegvis utrullning så att vi kan övervaka minnesanvändningen.",
        "check_for": ["driftsättning", "driftsätta", "utrullning"],
        "avoid": ["deploy", "deployment", "deploya"],
    },
    {
        "id": "conv_003",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Hur gör jag en ny branch?\" Svara på svenska utan att använda engelska lånord för Git-termer.",
        "correct_answer": "Du skapar en ny gren med `git checkout -b`. När du är klar gör du en incheckning och skickar in den för granskning.",
        "check_for": ["gren", "incheckning"],
        "avoid": ["branch", "commit"],
    },
    {
        "id": "conv_004",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Hur mergar jag sen?\" Svara på svenska med rätt Git-termer.",
        "correct_answer": "När grenen är godkänd gör du en sammanslagning till huvudgrenen. Om det finns konflikter får du lösa dem manuellt innan sammanslagningen går igenom.",
        "check_for": ["sammanslagning", "sammanslagna"],
        "avoid": ["merge", "merga"],
    },
    {
        "id": "conv_005",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Varför kan jag inte nå tjänsten utifrån?\" Svara på svenska utan svengelska.",
        "correct_answer": "Det kan vara ett dirigeringsproblem. Är delnätet konfigurerat så att trafiken dirigeras rätt? Låt mig kolla nätverksgränssnittet.",
        "check_for": ["dirigering", "delnät", "nätverksgränssnitt"],
        "avoid": ["routing", "subnet", "interface"],
    },
    {
        "id": "conv_006",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare säger: \"Tjänsten kraschar, felet är en race condition.\" Förklara på svenska vad en race condition är.",
        "correct_answer": "Ett tävlingsvillkor uppstår när två trådar når samma data samtidigt och resultatet beror på vilken som hinner först. Du undviker det genom att skydda delad data med ett lås.",
        "check_for": ["tävlingsvillkor"],
        "avoid": ["race condition", "ras-kondition", "rasvillkor"],
    },
    {
        "id": "conv_007",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Hur lägger jag till ett teststeg i pipelinen?\" Svara på svenska utan svengelska.",
        "correct_answer": "Du lägger till ett teststeg i arbetsflödet efter byggsteget. Om testerna misslyckas stoppas arbetsflödet och ingen utrullning sker.",
        "check_for": ["arbetsflöde", "utrullning"],
        "avoid": ["pipeline", "workflow", "deployment"],
    },
    {
        "id": "conv_008",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Vad gör garbage collectorn?\" Förklara på korrekt svenska.",
        "correct_answer": "En skräpsamlare frigör minne som programmet inte längre använder. Den letar efter objekt som inget refererar till och returnerar minnet till systemet.",
        "check_for": ["skräpsamlare", "skräpsamlaren"],
        "avoid": ["garbage collector", "garbage collectorn"],
    },
    {
        "id": "conv_009",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Hur säger man middleware på svenska?\" Svara med det korrekta svenska ordet och en förklaring.",
        "correct_answer": "På svenska heter det mellanvara. Det är programvara som sitter mellan operativsystemet och applikationen, eller mellan en klient och en server.",
        "check_for": ["mellanvara"],
        "avoid": ["middleware"],
    },
    {
        "id": "conv_010",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare säger: \"Vi får timeout från databasen.\" Svara på svenska och föreslå en lösning.",
        "correct_answer": "Tidsgränsen kan vara för kort inställd, eller så är frågorna för långsamma. Jag rekommenderar att vi förlänger tidsgränsen och lägger till index på de tabeller som saknar det.",
        "check_for": ["tidsgräns", "tidsgränsen"],
        "avoid": ["timeout"],
    },
    {
        "id": "conv_011",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Vad är en callback i JavaScript?\" Förklara på svenska.",
        "correct_answer": "En återanrop är en funktion som skickas som argument till en annan funktion och anropas senare, vanligtvis när en operation är klar.",
        "check_for": ["återanrop"],
        "avoid": ["callback"],
    },
    {
        "id": "conv_012",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Vad betyder overfitting?\" Förklara på svenska.",
        "correct_answer": "Överanpassning innebär att modellen lär sig träningsdatan för bra, inklusive brus och detaljer som inte generaliserar. Modellen får hög noggrannhet på träningsmängden men presterar dåligt på ny data.",
        "check_for": ["överanpassning"],
        "avoid": ["overfitting"],
    },
    {
        "id": "conv_013",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Hur skapar jag en toast-notis?\" Svara på svenska och förklara vad det är.",
        "correct_answer": "Du kan använda en toast-notis — en liten aviseringsruta som visas i några sekunder och sedan försvinner av sig själv. Den liknar hur rostat bröd poppar upp ur en brödrost.",
        "check_for": ["toast-notis", "aviseringsruta"],
        "avoid": [],
    },
    {
        "id": "conv_014",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare frågar: \"Hur säger man namespace på svenska?\" Svara med rätt ord och förklara.",
        "correct_answer": "På svenska heter det namnrymd. En namnrymd är en behållare för namn som undviker namnkrockar.",
        "check_for": ["namnrymd"],
        "avoid": ["namespace"],
    },
    {
        "id": "conv_015",
        "type": "conversation",
        "category": "sprak",
        "question": "En användare säger: \"Appen är inte deploybar ännu.\" Skriv om meningen på korrekt svenska.",
        "correct_answer": "Appen är inte driftsättningsbar ännu.",
        "check_for": ["driftsättningsbar"],
        "avoid": ["deploybar"],
    },
]

NEW_QUESTIONS.extend(CONV_QUESTIONS)

# ════════════════════════════════════════════════════════════
# 2. False friends-frågor — kognatfel där direktöversättning ger fel betydelse
# ════════════════════════════════════════════════════════════

FF_QUESTIONS = [
    {
        "id": "ff_001",
        "type": "false_friend",
        "category": "sprak",
        "question": "En utvecklare skriver: \"Två ras-konditioner möjliga.\" Vilket är det korrekta svenska uttrycket?\nA. Två ras-konditioner möjliga\nB. Två tävlingsvillkor möjliga\nC. Två raskvillkor möjliga\nD. Två löpvillkor möjliga\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "Race condition heter tävlingsvillkor på svenska. 'Ras-konditioner' är en felaktig direktöversättning som låter som rasbiologi.",
    },
    {
        "id": "ff_002",
        "type": "false_friend",
        "category": "sprak",
        "question": "Vilken översättning av 'condition' (i programmering) är korrekt på svenska?\nA. kondition\nB. villkor\nC. villkoring\nD. konditionering\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Condition' i logiskt sammanhang heter 'villkor' på svenska. 'Kondition' betyder fysisk form och är en falsk vän.",
    },
    {
        "id": "ff_003",
        "type": "false_friend",
        "category": "sprak",
        "question": "En AI-modell skriver: `startFlow({ gift: \"en bok\", recipient: \"mormor\" })` i en gåvo-app. Vad är felet?\nA. Inget fel, koden är korrekt\nB. 'gift' betyder 'förgiftning' på svenska, inte 'gåva'. Variabeln bör heta 'present' eller 'gåva'\nC. Variabeln ska vara på engelska alltid\nD. 'recipient' ska vara 'mottagare'\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Gift' är en katastrofal false friend — betyder GÅVA på engelska men FÖRGIFTNING på svenska. Modellen har råkat blanda in engelskan.",
    },
    {
        "id": "ff_004",
        "type": "false_friend",
        "category": "sprak",
        "question": "Vad heter 'fork' (i Git) på svenska?\nA. gaffel\nB. förgrening\nC. avgrening\nD. både B och C är accepterade\n\nSvara med bara bokstaven.",
        "correct_answer": "D",
        "rationale": "'Fork' heter 'förgrening' eller 'avgrening' i Git. 'Gaffel' är ett matbestick och en felaktig direktöversättning.",
    },
    {
        "id": "ff_005",
        "type": "false_friend",
        "category": "sprak",
        "question": "En modell skriver: \"Programmet har en krok som anropas vid varje incheckning.\" Vad menas med 'krok' här?\nA. En fysisk krokar i hårdvaran\nB. En hook — en funktion som anropas vid en händelse\nC. En fiskekrok\nD. En omskrivning av koden\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Krok' är den svenska översättningen av 'hook' i programmering. Det är etablerat men kan låta bisarrt. 'Hook' behålls ofta som lån.",
    },
    {
        "id": "ff_006",
        "type": "false_friend",
        "category": "sprak",
        "question": "Vilken är den korrekta svenska översättningen av 'toast' (i användargränssnitt)?\nA. rostat bröd\nB. toast-notis / aviseringsruta\nC. brödrost\nD. smörградde\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "En UI-toast är en tillfällig avisering. 'Rostat bröd' är den bokstavliga översättningen men i UI-sammanhang heter det 'toast-notis' eller 'aviseringsruta'. Metaforen (rostat bröd som hoppar upp) är densamma på svenska.",
    },
    {
        "id": "ff_007",
        "type": "false_friend",
        "category": "sprak",
        "question": "En modell skriver: \"Användaren har en klok insikt.\" Vad betyder 'klok' här?\nA. Smart/klok (korrekt användning)\nB. Klocka (felöversättning av 'clock')\nC. Låst (felöversättning av 'locked')\nD. Både A och B är möjliga\n\nSvara med bara bokstaven.",
        "correct_answer": "A",
        "rationale": "'Klok' är ett korrekt svenskt ord som betyder smart/tänkande. Det är en kognat-risk med engelska 'clock' men i detta sammanhang används det korrekt.",
    },
    {
        "id": "ff_008",
        "type": "false_friend",
        "category": "sprak",
        "question": "Vad betyder 'slut på IP-adresser' på svenska?\nA. Att IP-adresserna har en bestämd ände\nB. Att det inte finns fler IP-adresser tillgängliga\nC. Att IP-adresserna är avslutade\nD. Att IP-adresserna är saluterade\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Slut på' betyder 'inte fler tillgängliga' på svenska. Det är korrekt använt här, även om 'slut' kan betyda 'end' eller 'finished' på andra språk.",
    },
    {
        "id": "ff_009",
        "type": "false_friend",
        "category": "sprak",
        "question": "En modell säger: \"Låt oss använda en pipeline för detta.\" Vilket är det bästa svenska alternativet?\nA. Låt oss använda en rörledning för detta\nB. Låt oss använda en processledning för detta\nC. Låt oss använda en pipeline för detta\nD. Låt oss använda ett ledningssystem för detta\n\nSvara med bara bokstaven.",
        "correct_answer": "C",
        "rationale": "'Pipeline' är etablerat lånord i svensk IT-svenska. 'Rörledning' låter som VVS. 'Processledning' är korrekt men ovanligt. 'Pipeline' är det naturligaste valet.",
    },
    {
        "id": "ff_010",
        "type": "false_friend",
        "category": "sprak",
        "question": "Vilken av följande är en svensk false friend som kan orsaka förvirring i IT-sammanhang?\nA. dator (computer)\nB. program (application)\nC. gift (present/poison)\nD. tangentbord (keyboard)\n\nSvara med bara bokstaven.",
        "correct_answer": "C",
        "rationale": "'Gift' är den farligaste false friend-en: betyder 'gåva' på engelska men 'förgiftning' på svenska. De andra är korrekta kognater eller etablerade lån.",
    },
]

NEW_QUESTIONS.extend(FF_QUESTIONS)

# ════════════════════════════════════════════════════════════
# 3. Svårare MCQ — mer subtila frengelska och närmare distraktorer
# ════════════════════════════════════════════════════════════

HARD_MCQ = [
    {
        "id": "hmcq_011",
        "type": "mcq",
        "category": "sprak",
        "question": "En kollega säger: \"Vi behöver initialisera databasen.\" Vilken omskrivning är den mest korrekta svenska?\nA. Vi behöver initialisera databasen\nB. Vi behöver initiera databasen\nC. Vi behöver starta upp databasen\nD. Vi behöver initiering databasen\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Initialisera' är svengelsk hybrid av 'initialize'. Korrekt svensk form är 'initiera'. 'Starta upp' är också acceptabelt.",
    },
    {
        "id": "hmcq_012",
        "type": "mcq",
        "category": "sprak",
        "question": "Alla dessa är påhittade hybridformer. Vilket är den korrekta svenska formen av 'refaktorering'?\nA. refaktorering\nB. omstrukturering\nC. omskrivning\nD. både B och C är accepterade\n\nSvara med bara bokstaven.",
        "correct_answer": "D",
        "rationale": "'Refaktorering' är svengelsk hybrid. 'Omstrukturering' och 'omskrivning' är båda etablerade svenska former.",
    },
    {
        "id": "hmcq_013",
        "type": "mcq",
        "category": "sprak",
        "question": "Vilken mening är skriven på den mest korrekta svenska?\nA. Jag mountar volymen på podden\nB. Jag monterar volymen på podden\nC. Jag monteringen volymen på podden\nD. Jag mount volymen på podden\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Mountar' är svengelsk hybrid. 'Monterar' är korrekt svensk form av 'mount' i Kubernetes-sammanhang.",
    },
    {
        "id": "hmcq_014",
        "type": "mcq",
        "category": "sprak",
        "question": "En modell skriver: \"Kundanvändaren submittar formen.\" Vilket är den korrekta svenska formen?\nA. Kandanvändaren submittar formen\nB. Användaren skickar in formuläret\nC. Kunden inlämnar blanketten\nD. både B och C är accepterade\n\nSvara med bara bokstaven.",
        "correct_answer": "D",
        "rationale": "'Submittar' och 'form' är svengelska hybridformer. 'Skicka in' och 'inlämna' är korrekta. 'Formulär' och 'blankett' är båda svenska former.",
    },
    {
        "id": "hmcq_015",
        "type": "mcq",
        "category": "sprak",
        "question": "Vilket av följande är en etablerad svensk form, inte en påhittad hybrid?\nA. deploybar\nB. utrullningsbar\nC. mergebar\nD. subscribar\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Utrullningsbar' är etablerad svensk form för 'deployable'. De andra är svengelska hybrider.",
    },
    {
        "id": "hmcq_016",
        "type": "mcq",
        "category": "sprak",
        "question": "Vilken mening använder rätt svenskt ord för 'parsing'?\nA. Jag parsar JSON-filen\nB. Jag tolkar JSON-filen\nC. Jag parsar JSON-filen\nD. både A och B är accepterade\n\nSvara med bara bokstaven.",
        "correct_answer": "D",
        "rationale": "'Tolka' är den etablerade svenska formen. 'Parsa' har blivit vanligt som lån och accepteras ofta i vardaglig IT-svenska, men 'tolka' är den korrekta formen.",
    },
    {
        "id": "hmcq_017",
        "type": "mcq",
        "category": "sprak",
        "question": "Vilken är den korrekta svenska formen av 'caching'?\nA. cachning\nB. snabbminnande\nC. cacha\nD. både A och C accepteras i praktiken\n\nSvara med bara bokstaven.",
        "correct_answer": "D",
        "rationale": "'Cache' är etablerat lånord i svensk IT-svenska. 'Cacha' och 'cachning' används i praktiken. 'Snabbminne' är den svenska formen men används sällan som verb.",
    },
    {
        "id": "hmcq_018",
        "type": "mcq",
        "category": "sprak",
        "question": "Alla dessa ord betyder ungefär samma sak. Vilket är den mest etablerade svenska formen?\nA. programfixning\nB. patchning\nC. programfixande\nD. lapande\n\nSvara med bara bokstaven.",
        "correct_answer": "C",
        "rationale": "'Programfixande' är den svenska formen av 'patching'. 'Patchning' är svengelsk hybrid. 'Programfix' är etablerat som substantiv.",
    },
    {
        "id": "hmcq_019",
        "type": "mcq",
        "category": "sprak",
        "question": "Vilken böjning av 'escapa' (teckenhantering) är korrekt?\nA. escapa\nB. hantera specialtecken\nC. undanta tecken\nD. både B och C är accepterade svenska former\n\nSvara med bara bokstaven.",
        "correct_answer": "D",
        "rationale": "'Escapa' är svengelsk hybrid. 'Hantera specialtecken' och 'undanta tecken' är korrekta svenska former för 'escaping'.",
    },
    {
        "id": "hmcq_020",
        "type": "mcq",
        "category": "sprak",
        "question": "Vilken mening är den mest svenska?\nA. Vi behöver konfigurera konfigurationen\nB. Vi behöver ställa in inställningarna\nC. Vi behöver sätta upp configurationen\nD. Vi behöver konfigurera configet\n\nSvara med bara bokstaven.",
        "correct_answer": "B",
        "rationale": "'Ställa in inställningarna' är ren svenska. 'Konfigurera' är etablerat lån men 'configet' och 'configurationen' är svengelska hybrider.",
    },
]

NEW_QUESTIONS.extend(HARD_MCQ)

# ════════════════════════════════════════════════════════════
# Spara
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "eval-questions-new.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for q in NEW_QUESTIONS:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    from collections import Counter
    types = Counter(q["type"] for q in NEW_QUESTIONS)
    print(f"Wrote {out}")
    print(f"Total: {len(NEW_QUESTIONS)} nya frågor")
    for t, n in types.most_common():
        print(f"  {t}: {n}")
