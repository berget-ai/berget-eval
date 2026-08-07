#!/usr/bin/env python3
"""Generera svårare testfrågor v3.

Principer:
  - Språk-MCQ: distraktorer är liknande ord (böjningar, synonymer) - inte uppenbart fel
  - Preference: bägge alternativ innehåller viss frengelska, ett bara något bättre
  - Kulturfrågor: välj frågor med 4 liknande alternativ (inte uppenbara fel)
  - Ta bort självklara frågor ("Pljeskavica", "Ulf Kristersson")
"""
import json
import random
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
KULTUR_DIR = Path(__file__).resolve().parent.parent / "data" / "kulturkanon"
OUT = DATA / "eval-questions.jsonl"
random.seed(42)

# ── 1. Svårare språk-MCQ med närmare distraktorer ──
# Alla ord är från vår finetuning-data (påhittade), men distraktorer är SVÅRA - liknande ordformer
HARD_LANGUAGE_MCQ = [
    {
        "invented": "deploybart",
        "correct": "utrullningsbart",
        "distractors": ["distribuerbart", "utrymningsbart", "delegeringsbart"],
        "rationale": "'deploybart' = eng deploy + sv -bart. Distraktorer liknar i formen.",
    },
    {
        "invented": "routningen",
        "question_word": "routningen",
        # Vi blev överens om att routing är etablerat - men routningen (sv böjning) oetablerad
        "correct": "dirigeringen",
        "distractors": ["rutningen", "rotationen", "redigeringen"],
        "rationale": "'routningen' är hybridform. 'dirigeringen' är svensk etablerad.",
    },
    {
        "invented": "buildet",
        "correct": "bygget",
        "distractors": ["budet", "bålget", "baguetten"],  # liknar i bokstäver
        "rationale": "'buildet' hybrid; 'bygget' svensk etablerad.",
    },
    {
        "invented": "merget",
        "correct": "sammanslagningen",
        "distractors": ["sammanfogningen", "sammanställningen", "sammanhanget"],
        "rationale": "'merget' = eng merge + sv -et. 'sammanslagningen' svensk etablerad. Distraktorer börjar alla med 'samman-'.",
    },
    {
        "invented": "mockningen",
        "correct": "skeendesimuleringen",
        "distractors": ["skenhandlingarna", "skeendet", "simuleringen"],
        "rationale": "Mock-metoden = simulering av skeenden. Svårt pga nästan rätt ord i distraktorer.",
    },
    {
        "invented": "annotationerna",
        "correct": "annoteringarna",
        "distractors": ["annotationerna", "noteringarna", "anteckningarna"],
        "rationale": "(annotationerna ~ annoteringarna) subtil: 'annotationer' anglicism, 'annoteringar' svensk form.",
    },
    {
        "invented": "flashningen",
        "correct": "fast programmatiseringen",
        "distractors": ["blixtladdningen", "firmwareuppdateringen", "fast Programmeringen"],
        "rationale": "Subtil: flashning är en specifik typ av uppdatering.",
    },
    {
        "invented": "hooket",
        "correct": "kroken",
        "distractors": ["kopplingen", "harket", "höken"],
        "rationale": "Subtila fonetiska likheter i distraktorer.",
    },
    {
        "invented": "workloadet",
        "correct": "arbetsbelastningen",
        "distractors": ["arbetslaget", "arbetsläget", "arbetsschemat"],
        "rationale": "Subtilt: alla fyra börjar med 'arbets-'.",
    },
    {
        "invented": "indenteringen",
        "correct": "indraget",
        "distractors": ["indelningen", "individueringen", "indexeringen"],
        "rationale": "Subtilt: fyra ord som alla börjar med 'ind-'.",
    },
]

def make_hard_language_mcq():
    qs = []
    for i, item in enumerate(HARD_LANGUAGE_MCQ, 1):
        options = item["distractors"] + [item["correct"]]
        random.shuffle(options)
        labels = ["A", "B", "C", "D"]
        correct_idx = options.index(item["correct"])
        qs.append({
            "id": f"mcq_{i:03d}",
            "type": "mcq",
            "category": "A: svår hybridform + nära distraktorer",
            "question": f"Vilket är det korrekta svenska ordet för det påhittade ordet '{item['invented']}'? Svara med bara bokstaven.",
            "options_labels": labels,
            "options": options,
            "correct_index": correct_idx,
            "correct_answer": item["correct"],
            "rationale": item["rationale"],
        })
    return qs

# ── 2. Svårare preference-frågor: bägge alternativ innehåller fel, ett bara något bättre ──
HARD_PREFERENCE = [
    {
        # Bägge innehåller hybridord - en "B" är bättre pga komplett omskrivning
        "a": "Klustret är deploybart till produktion nu.",
        "b": "Klustret går att rulla ut till produktion nu.",
        "correct_idx": 1,
        "rationale": "Bagra alternativ innehåller frengelska men B har svensk omskrivning. A har 'deploybart'.",
    },
    {
        # A har 2 frengelska ord, B har bara 1
        "a": "Buildet misslyckades under CI-pipelinen, vi måste refaktorera koden.",
        "b": "Bygget misslyckades under CI-pipelinen, vi måste refaktorera koden.",
        "correct_idx": 1,
        "rationale": "Båda har 'refaktorera' men B har rätt 'bygget' istället för 'buildet'.",
    },
    {
        # A har 'mockningen' som är oetablerad, B har 'mockningen' också - ingen vinnare
        # -> B har bättre ordval i resten
        "a": "Mockningen av API:et fungerar inte, vi får testa om.",
        "b": "Skenobjekten i testet fungerar, vi får testa om.",
        "correct_idx": 1,
        "rationale": "A har 'mockningen' (påhittat), B har 'skenobjekten' (svensk). Båda har resten likvärdig.",
    },
    {
        # A har två fel ('annotationer' + 'namespacet'), B har ett ('annotationer')
        "a": "Annotationerna saknas på namespacet, det måste åtgärdas.",
        "b": "Annoteringarna saknas på namespacet, det måste åtgärdas.",
        "correct_idx": 1,
        "rationale": "Båda har 'namespacet' (accepterat lån). A har 'annotationerna' (anglicism). B har svensk form.",
    },
    {
        # A har 'workloadet' (mer påhittat) och 'controller' (accepterat), B har bara 'controller'
        "a": "Workloadet har kraschat och startas om av controller.",
        "b": "Arbetsbelastningen har kraschat och startas om av controller.",
        "correct_idx": 1,
        "rationale": "A har 'workloadet' (sv stam + et), B har svensk etablerad form.",
    },
    {
        # A har 'fb-cap:a' (helt påhittat) vs B 'begränsa'
        "a": "Vi tvingades fb-cap:a loggningen så disken inte fylls.",
        "b": "Vi tvingades begränsa loggningen så disken inte fylls.",
        "correct_idx": 1,
        "rationale": "A 'fb-cap:a' är helt påhittat. B 'begränsa' är svensk etablerad.",
    },
    {
        # A: 'commitet' + 'brancharna' (2 fel), B: 'incheckningen' + 'brancharna' (1 fel)
        "a": "Commitet blockerades av pre-commit-kroken på brancharna.",
        "b": "Incheckningen blockerades av pre-commit-kroken på brancharna.",
        "correct_idx": 1,
        "rationale": "A har två påhittade ('commitet', 'brancharna'); B har en ('brancharna' accepterat).",
    },
    {
        # A har 't.ex. parsningen fel' med 'parsning' (accepterat), B har 'tolkningen' (svensk)
        # Subtilt: bägge accepteras av många, men B är mer svensk
        "a": "Felet ligger i parsningen av JSON-svaret, inte nätverket.",
        "b": "Felet ligger i tolkningen av JSON-svaret, inte nätverket.",
        "correct_idx": 1,
        "rationale": "Bägge accepteras av svensk IT-praxis. B ('tolkningen') är mer svensk etablerad; A ('parsningen') hybridform fast accepterad enligt CS.",
    },
    {
        # Subtil: både 'failande tester' (A) och 'misslyckade tester' (B) - men A har ett till fel
        "a": "Vi har tre failande tester som behöver åtgärdas akut.",
        "b": "Vi har tre misslyckade tester som behöver åtgärdas akut.",
        "correct_idx": 1,
        "rationale": "A har 'failande' (påhittat hybrid). B har svensk etablerad form.",
    },
    {
        # A: 'workloadet kraschar', B: 'arbetsbelastningen kraschar'  
        "a": "Arbetsbelastningen på klustret är för hög, vi måste skala.",
        "b": "Arbetsbelastningen på klustret är för hög, vi måste skalera.",
        "correct_idx": 0,
        "rationale": "Subtilt: A 'skala' (korrekt svenskt), B 'skalera' (anglicism av scale+era).",
    },
    {
        # A: deploymentet (accepterat), B: utrullningen (svensk) - subtilt
        "a": "Deploymentet lyckades utan problem på stage.",
        "b": "Utrullningen lyckades utan problem på stage.",
        "correct_idx": 1,
        "rationale": "Bägge formerna accepteras. B är svensk etablerad; A anglicism.",
    },
    {
        # Svårt: A har 'flaska' = fel ('flaska' är inte ord), B har 'flashning' (etablerat)
        "a": "Flaskan av BIOS-brädan tog 10 minuter.",
        "b": "Flashningen av BIOS-brädan tog 10 minuter.",
        "correct_idx": 1,
        "rationale": "A 'Flaskan' = helt fel ord. B 'Flashningen' = teknisk anglicism men accepterad i svensk IT-praxis.",
    },
]

def make_hard_preference():
    qs = []
    for i, p in enumerate(HARD_PREFERENCE, 1):
        options = [p["a"], p["b"]]
        qs.append({
            "id": f"pref_{i:03d}",
            "type": "preference",
            "category": "subtil preference",
            "question": "Vilken av följande två meningar är mest korrekt skriven på svenska? Svara med bara A eller B.",
            "options_labels": ["A", "B"],
            "options": options,
            "correct_index": p["correct_idx"],
            "correct_answer": options[p["correct_idx"]],
            "rationale": p["rationale"],
        })
    return qs

# ── 3. Long-form frågor - samma som innan ──
LONG_FORM_CONCEPTS = [
    ("användargränssnitt", "Förklara vad ett användargränssnitt är och ge ett exempel."),
    ("refaktorisering", "Vad betyder refaktorisering inom programmering? Beskriv kort."),
    ("regressionstest", "Vad är ett regressionstest och varför är det viktigt?"),
    ("annotering", "Förklara vad en annotering är inom programmering."),
    ("realtid", "Vad menas med realtid i datasystemsammanhang?"),
    ("användningsfall", "Förklara vad ett användningsfall (use case) är."),
    ("åtkomstkontroll", "Vad är åtkomstkontroll och varför behövs det?"),
    ("rullgardinsmeny", "Beskriv vad en rullgardinsmeny är."),
    ("pålitlighet", "Vad betyder pålitlighet (reliability) för ett IT-system?"),
    ("tillgänglighet", "Förklara skillnaden mellan tillgänglighet och användbarhet."),
    ("återställning", "Beskriv vad en återställning av ett system innebär."),
    ("behörighet", "Vad är skillnaden mellan autentisering och behörighet?"),
    ("kryptering", "Förklara kryptering kort."),
    ("signering", "Vad innebär digital signering?"),
    ("redundans", "Förklara redundans och varför det används."),
    ("reguljärt uttryck", "Vad är ett reguljärt uttryck och när används det?"),
    ("tjänst", "Inom mikrotjänst-arkitektur, vad är en tjänst?"),
    ("referens", "Inom programmering, vad är en referens?"),
    ("radering", "Vad betyder radering i ett databassammanhang?"),
    ("orsakskod", "Vad är en orsakskod i en felrapport?"),
]

def make_long_form():
    qs = []
    for i, (ord, fraga) in enumerate(LONG_FORM_CONCEPTS, 1):
        qs.append({
            "id": f"lf_{i:03d}",
            "type": "long_form",
            "concept": ord,
            "question": fraga,
            "evaluation_criteria": [
                f"Svaret ska förklara '{ord}' korrekt på svenska",
                "Svaret ska undvika frengelska",
                "Svaret ska vara begripligt",
            ],
            "max_words": 80,
        })
    return qs

# ── 4. Översättning - samma som innan ──
TRANSLATION_SENTENCES = [
    {"en": "The server failed to start due to insufficient memory.",
     "expected_sv_keywords": ["servern", "misslyckades", "starta", "minne"]},
    {"en": "The request was rejected because the token had expired.",
     "expected_sv_keywords": ["begäran", "förfrågan", "avvisad", "löpt ut"]},
    {"en": "We need to refactor the authentication logic.",
     "expected_sv_keywords": ["refaktorera", "omstrukturera", "autentiserings"]},
    {"en": "The deployment was rolled back to the previous version.",
     "expected_sv_keywords": ["utrullning", "distribution", "återställd", "föregående"]},
    {"en": "Please configure the default values for the new environment.",
     "expected_sv_keywords": ["konfigurera", "standardvärden", "miljö"]},
    {"en": "The endpoint returns a 404 error when the resource is not found.",
     "expected_sv_keywords": ["ändpunkt", "resurs", "hittas"]},
    {"en": "The container crashed and was restarted automatically.",
     "expected_sv_keywords": ["behållare", "kraschade", "startades om"]},
    {"en": "We are investigating the root cause of the outage.",
     "expected_sv_keywords": ["undersöker", "rotorsak", "avbrott"]},
    {"en": "The backup completed successfully and was verified.",
     "expected_sv_keywords": ["säkerhetskopiering", "slutfördes", "verifierad"]},
    {"en": "The interface allows users to reset their passwords.",
     "expected_sv_keywords": ["gränssnitt", "användare", "lösenord"]},
    {"en": "Annotations were added to the Kubernetes resources.",
     "expected_sv_keywords": ["annoteringar", "resurser"]},
    {"en": "The routing table needs to be updated.",
     "expected_sv_keywords": ["dirigeringstabell", "routningstabell", "uppdateras"]},
    {"en": "Default timeout is 30 seconds.",
     "expected_sv_keywords": ["standard", "tidsgräns", "sekunder"]},
    {"en": "The request body was validated by the middleware.",
     "expected_sv_keywords": ["begäran", "kropp", "validerad", "mellanvara"]},
    {"en": "The branch was merged after code review.",
     "expected_sv_keywords": ["gren", "sammanslagen", "kodgranskning"]},
]

def make_translation():
    qs = []
    for i, s in enumerate(TRANSLATION_SENTENCES, 1):
        qs.append({
            "id": f"trans_{i:03d}",
            "type": "translation",
            "question": f"Översätt följande mening till korrekt svenska. Undvik frengelska (engelska ord med svensk böjning). Svara med bara översättningen:\n\n{s['en']}",
            "source": s["en"],
            "expected_keywords": s["expected_sv_keywords"],
            "evaluation_note": "Bedöm om översättningen använder korrekta svenska ord istället för engelska ord med svensk böjning.",
        })
    return qs

# ── 5. Kulturfrågor - välj SVÅRA med lika alternativ ──

# Svartlista för uppenbara frågor
KULTUR_BLACKLIST_QUESTIONS = {
    # Uppenbara - tas bort
    "Vem har varit Sveriges statsminister sedan 2022?",
    "Pljeskavica är en maträtt som ursprungligen kommer från Sverige.",
    "Vilket band tillhör den 'första vågen' av black metal och var ett svenskt black/viking metal-band från Stockholm?",
    "Vilken svensk bergsbestigare är känd för sina resor i Mellanöstern och Asien?",
}

def is_hard_kultur_mcq(q):
    if q["question"] in KULTUR_BLACKLIST_QUESTIONS:
        return False
    if "options" not in q or "correctAnswer" not in q:
        return False
    opts = [str(o) for o in q["options"]]
    if len(opts) != 4:
        return False
    if q["correctAnswer"] not in opts:
        return False
    # Kräv att alla 4 alternativ är av ungefär samma längd (mer lika = svårare)
    lengths = [len(o) for o in opts]
    if max(lengths) - min(lengths) > 40:
        return False
    # Kräv att alternativen är korta (långa ger bort svar)
    if max(lengths) > 100:
        return False
    # Kräv att frågan är rimlig
    if len(q["question"]) > 400 or len(q["question"]) < 20:
        return False
    # Kräv att rätt svar inte är en uppenbar "alla andra är fel"
    # Hoppa över om rätt svar stavas väldigt annorlunda än distraktorer
    correct = q["correctAnswer"]
    for opt in opts:
        if opt != correct and len(opt) > 3 and len(correct) > 3:
            # Räkna gemensamma prefix
            common = 0
            for c1, c2 in zip(opt.lower(), correct.lower()):
                if c1 == c2: common += 1
                else: break
            # Minst en distraktor ska ha >= 3 tecken gemensamt prefix med rätt
    return True

def is_hard_kultur_tf(q):
    if q["question"] in KULTUR_BLACKLIST_QUESTIONS:
        return False
    if "correctAnswer" not in q:
        return False
    if len(q["question"]) < 30 or len(q["question"]) > 400:
        return False
    # Undvik uppenbara "Sverige" eller "ej Sverige" typer
    text = q["question"].lower()
    if "ursprungligen kommer från sverige" in text or "från sverige" in text:
        return False
    return True

def load_kultur_hard():
    mcqs, tfs = [], []
    for fname in ("genererade-fragor.json", "wiki-fragor.json"):
        path = KULTUR_DIR / fname
        if not path.exists(): continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for q in data["questions"]:
            if q.get("type") == "multiple-choice":
                if is_hard_kultur_mcq(q):
                    mcqs.append({"question": q["question"], "options": [str(o) for o in q["options"]],
                                 "correctAnswer": q["correctAnswer"], "source": fname})
            elif q.get("type") in ("true-false","true-or-false","sant-falskt","sant-or-falskt","truefalse","boolean"):
                correct = q.get("correctAnswer")
                if isinstance(correct, str):
                    correct = correct.lower().strip()
                    if correct in ("true","sant","ja"): correct = True
                    elif correct in ("false","falskt","nej"): correct = False
                    else: continue
                if not isinstance(correct, bool): continue
                if is_hard_kultur_tf({"question": q["question"], "correctAnswer": q["correctAnswer"]}):
                    tfs.append({"question": q["question"], "correctAnswer": correct, "source": fname})
    return mcqs, tfs

def make_kultur_questions(mcqs, tfs, n_mcq=20, n_tf=10):
    random.shuffle(mcqs)
    random.shuffle(tfs)
    qs = []
    for i, q in enumerate(mcqs[:n_mcq]):
        opts = list(q["options"])
        correct = q["correctAnswer"]
        random.shuffle(opts)
        labels = [chr(65 + j) for j in range(len(opts))]
        correct_idx = opts.index(correct)
        qs.append({
            "id": f"kultur_mcq_{i+1:03d}",
            "type": "kultur_mcq",
            "category": "kulturkanon_mc_hard",
            "question": f"{q['question']}\nSvara med bara bokstaven.",
            "options_labels": labels,
            "options": opts,
            "correct_index": correct_idx,
            "correct_answer": correct,
            "rationale": f"Från {q['source']}.",
        })
    for i, q in enumerate(tfs[:n_tf]):
        qs.append({
            "id": f"kultur_tf_{i+1:03d}",
            "type": "kultur_tf",
            "category": "kulturkanon_tf_hard",
            "question": f"{q['question']}\nSvara med 'Sant' eller 'Falskt'.",
            "correct_answer": "Sant" if q["correctAnswer"] else "Falskt",
            "rationale": f"Från {q['source']}.",
        })
    return qs

def main():
    print("Genererar svårare testfrågor v3...", file=sys.stderr)
    mcq_lang = make_hard_language_mcq()
    prefs = make_hard_preference()
    long_forms = make_long_form()
    translations = make_translation()

    mcqs, tfs = load_kultur_hard()
    print(f"Filtrerade kulturfrågor: {len(mcqs)} MC, {len(tfs)} TF", file=sys.stderr)
    kultur_qs = make_kultur_questions(mcqs, tfs, n_mcq=20, n_tf=10)

    all_q = mcq_lang + prefs + long_forms + translations + kultur_qs
    from collections import Counter
    types = Counter(q["type"] for q in all_q)
    print(f"\nTotal: {len(all_q)} frågor", file=sys.stderr)
    for t, n in types.most_common():
        print(f"  {t}: {n}", file=sys.stderr)

    # Skriv till en ny fil först - vi vill backa upp den gamla
    backup = DATA / "eval-questions-v2.jsonl"
    with open(OUT, "r", encoding="utf-8") as f:
        old = f.read()
    with open(backup, "w", encoding="utf-8") as f:
        f.write(old)
    print(f"Backup till {backup}", file=sys.stderr)

    with open(OUT, "w", encoding="utf-8") as f:
        for q in all_q:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
