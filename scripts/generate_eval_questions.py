#!/usr/bin/env python3
"""Generera testfrågor för modellutvärdering — v2 med kvalitetsfilter.

Förbättringar jämfört med v1:
  - Exkluderar MCQ där rätt svar är identiskt med påhittat ord (t.ex. cronjobbet)
  - Exkluderar MCQ där distraktorn dupliceras
  - Exkluderar preference-par där bägge alternativ är etablerade (pod/podd)
  - Bättre handplockade preference-par
  - Kontrollerar att rätt svar inte innehåller påhittat ord
  - Lägger till "rationale" förklaring
"""
import json
import random
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "eval-questions.jsonl"
random.seed(42)

# ── 1. MCQ-frågor från finetuning-datan ──

# Svartlista: ord vi inte ska ha med eftersom de faktiskt är etablerade
# inom IT-svenska (bekräftat via CS IT-ordlistan) eller har flera acceptabla former
MCQ_BLACKLIST = {
    "cronjobbet",   # cronjob etablerat
    "podarna",      # pod/podd bägge acceptabla
    "ingressarna",  # ingress etablerat inom K8s
    "clustret",     # kluster etablerat, clustret är felstavning - för trivialt
    "volumet",      # volym etablerat, "volumet" är bara felstavning
    "imaget",       # bild/avbild - bägge används
    "tokenet",      # tecken/token - token etablerat inom IT
    "secretet",     # hemlighet/secret - secret etablerat inom K8s
    "statefulset",  # K8s-term, etablerad
    "interfacet",   # gränssnitt etablerat, men interfacet används入库
    "namespacet",   # namnrymd/namespace - bägge används
    "endpointet",   # ändpunkt/endpoint - bägge används
    "deploymentet", # utrullning/deployment - bägge används inom K8s-svenska
    "chartet",      # Helm-chart etablerat
    "configet",     # konfig etablerat
    "regexet",      # regex etablerat inom IT
    "workflowet",   # arbetsflöde/workflow - bägge används
    "buildet",      # bygge/build - bägge
    "patternet",    # mönster/pattern - bägge
    "recordet",     # post/record - bägge
    "commitet",     # incheckning/commit - bägge
    "fixet",        # fix/programfix - bägge
    "addonet",      # tillägg/addon - bägge
    "statementet",  # sats/statement - bägge
    "merget",       # sammanslagning/merge - bägge
    "pullbar",      # för niche
    "subscribar",   # för niche
    "subnät",       # subnät etablerat enligt CS IT-ord
    "subnätet",     # dto
    "subdomäner",   # underdomäner/subdomäner - bägge acceptabla
    "routningen",   # routing etablerat enligt CS IT-ord
    "routbar",      # routbar etablerat via routing
    "routbart",     # dto
    "routbara",     # dto
    "routningen",   # dto
    "flashningen",  # flash etablerat enligt CS
    "webhooket",    # webhook etablerat enligt CS
    "webhookarna",  # dto
    "mockningen",   # mock/skenobjekt - "skeenden" för svagt
    "mockarna",     # dto
    "daemonsetet",  # daemonset är K8s-term
    "följande",     # allmänt svenskt ord
    "accountet",    # konto/account - bägge
}

def is_valid_mcq(word, correct, distractors):
    """Kontrollera att MCQ är giltig."""
    # Rätt svar får inte vara identiskt med påhittat
    if word.lower() == correct.lower():
        return False
    # Rätt svar får inte innehålla påhittat ord eller vice versa
    if word.lower() in correct.lower() or correct.lower() in word.lower():
        return False
    # Distraktorer får inte duplicera rätt svar
    if correct.lower() in [d.lower() for d in distractors]:
        return False
    # Inga dubletter bland distraktorer
    if len(set(d.lower() for d in distractors)) != len(distractors):
        return False
    # Rätt svar får inte vara enstaka bokstav eller för kort
    if len(correct) < 3:
        return False
    # Rätt svar får inte innehålla parentes eller snedstreck
    if any(c in correct for c in "()/"):
        return False
    # Rätt svar får inte vara flertydigt/sammansatt
    if " " in correct:
        return False
    return True

def make_mcq_from_finetuning():
    items = []
    with open(DATA / "2026-08-04-ai-pahittade-ord-finetuning.jsonl") as f:
        for line in f:
            obj = json.loads(line)
            if "instruction" in obj and "input" in obj and "output" in obj:
                if obj["instruction"].startswith("Ange det korrekta"):
                    items.append(obj)
    items_a = [i for i in items if i.get("metadata", {}).get("category", "").startswith("A")]
    items = items_a

    all_outputs = []
    for i in items:
        out = i["output"].split("/")[0].split("(")[0].strip()
        if out and len(out) > 2 and " " not in out and not any(c in out for c in "()/"):
            all_outputs.append(out)

    mcqs = []
    used_correct = set()
    used_inputs = set()
    for item in items:
        word = item["input"]
        if word in MCQ_BLACKLIST:
            continue
        if word in used_inputs:
            continue
        correct = item["output"].split("/")[0].split("(")[0].strip()
        if not is_valid_mcq(word, correct, []):
            continue
        if correct in used_correct:
            continue

        # Distraktorer: ord som inte är "för nära" rätt svar
        pool = []
        for o in all_outputs:
            if o == correct:
                continue
            if o in used_correct:
                continue
            # Undvik distraktorer som liknar rätt svar (kan göra frågan otydlig)
            if correct[:3] == o[:3]:
                continue
            pool.append(o)
        if len(pool) < 3:
            continue
        distractors = random.sample(pool, 3)
        if not is_valid_mcq(word, correct, distractors):
            continue

        used_correct.add(correct)
        used_inputs.add(word)
        options = distractors + [correct]
        random.shuffle(options)
        correct_idx = options.index(correct)

        # Generera en kort förklaring av rätt val
        rationale = f"'{word}' är påhittat (engelsk stam + svensk böjning). Korrekt svenska: '{correct}'."

        mcqs.append({
            "id": f"mcq_{len(mcqs)+1:03d}",
            "type": "mcq",
            "category": item.get("metadata", {}).get("category", ""),
            "question": f"Vilket är det korrekta svenska ordet för det påhittade ordet '{word}'? Svara med bara bokstaven (A, B, C eller D).",
            "options_labels": ["A", "B", "C", "D"],
            "options": options,
            "correct_index": correct_idx,
            "correct_answer": correct,
            "rationale": rationale,
        })
    return mcqs

# ── 2. Long-form frågor ──

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
    for ord, fraga in LONG_FORM_CONCEPTS:
        qs.append({
            "id": f"lf_{len(qs)+1:03d}",
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

# ── 3. Preference-par (handplockade) ──

PREFERENCE_PAIRS = [
    # Alla dessa använder ord ur kategori A från finetuning-datan som är oetablerade hybridord.
    # "Rätt" alternativ är en svensk etablerad form som ingen svenskspråkig källa strider mot.
    {
        "invented": "Vi har tre failande tester som behöver åtgärdas.",
        "correct": "Vi har tre misslyckade tester som behöver åtgärdas.",
        "rationale": "'failande' är oetablerad hybridform (eng fail + sv -ande). 'misslyckade' är etablerad svensk form.",
    },
    {
        "invented": "Systemet är obootbart efter uppdateringen.",
        "correct": "Systemet går inte att starta efter uppdateringen.",
        "rationale": "'obootbart' är oetablerat hybridord. Omskrivning är svensk etablerad form.",
    },
    {
        "invented": "Klustret är deploybart till produktion nu.",
        "correct": "Klustret går att rulla ut till produktion nu.",
        "rationale": "'deploybart' är oetablerad hybridform. Omskrivning är svensk etablerad form.",
    },
    {
        "invented": "Buildet misslyckades under CI-pipelinen.",
        "correct": "Bygget misslyckades under CI-pipelinen.",
        "rationale": "'buildet' är oetablerad hybridform. 'bygget' är svensk etablerad form.",
    },
    {
        "invented": "Merget blockerades av konflikter.",
        "correct": "Sammanslagningen blockerades av konflikter.",
        "rationale": "'merget' är oetablerad hybridform. 'sammanslagningen' är svensk etablerad form.",
    },
    {
        "invented": "Annotationerna saknas på resurserna.",
        "correct": "Annoteringarna saknas på resurserna.",
        "rationale": "'annotationer' är anglicism. 'annoteringar' är svensk etablerad form.",
    },
    {
        "invented": "Workloadet har kraschat och startas om av controller.",
        "correct": "Arbetsbelastningen har kraschat och startas om av styrenheten.",
        "rationale": "'workloadet' är oetablerad hybridform. 'arbetsbelastning' är svensk etablerad form.",
    },
    {
        "invented": "Vi tvingades fb-cap:a loggningen så disken inte fylls.",
        "correct": "Vi tvingades begränsa loggningen så disken inte fylls.",
        "rationale": "'fb-cap:a' är helt påhittat. 'begränsa' är svensk etablerad form.",
    },
    {
        "invented": "Modellen dräpade några rader vid översättningen.",
        "correct": "Modellen tog bort några rader vid översättningen.",
        "rationale": "'dräpade' är felaktigt tempus av dräpa (normativt: dräpte) och därtill ontologiskt fel i kontext.",
    },
    {
        "invented": "Det förexisterande värdet används som standard.",
        "correct": "Det förut existerande värdet används som standard.",
        "rationale": "'förexisterande' är oetablerad hybrid (sv för + eng existing). 'förut existerande' är svensk form.",
    },
    {
        "invented": "Jaghör vad du menar med den frågan.",
        "correct": "Jag hör vad du menar med den frågan.",
        "rationale": "'jaghör' är felaktig sammansmältning av 'jag hör'.",
    },
    {
        "invented": "De dispergerande färgerna skapar en varm känsla.",
        "correct": "De spridande färgerna skapar en varm känsla.",
        "rationale": "'dispergerande' är oetablerad hybrid (eng dispersing). 'spridande' är svensk etablerad form.",
    },
]

def make_preference():
    qs = []
    for i, p in enumerate(PREFERENCE_PAIRS):
        # Slumpa ordning på alternativen
        if random.random() > 0.5:
            options = [p["invented"], p["correct"]]
            correct_idx = 1
        else:
            options = [p["correct"], p["invented"]]
            correct_idx = 0
        qs.append({
            "id": f"pref_{i+1:03d}",
            "type": "preference",
            "question": "Vilken av följande två meningar är mest korrekt skriven på svenska? Svara med bara A eller B.",
            "options_labels": ["A", "B"],
            "options": options,
            "correct_index": correct_idx,
            "correct_answer": p["correct"],
            "rationale": p["rationale"],
        })
    return qs

# ── 4. Översättning ──

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
    for i, s in enumerate(TRANSLATION_SENTENCES):
        qs.append({
            "id": f"trans_{i+1:03d}",
            "type": "translation",
            "question": f"Översätt följande mening till korrekt svenska. Undvik frengelska (engelska ord med svensk böjning). Svara med bara översättningen:\n\n{s['en']}",
            "source": s["en"],
            "expected_keywords": s["expected_sv_keywords"],
            "evaluation_note": "Bedöm om översättningen använder korrekta svenska ord istället för engelska ord med svensk böjning.",
        })
    return qs

# ── Huvudfunktion ──
def main():
    print("Genererar testfrågor v2...", file=sys.stderr)
    mcqs = make_mcq_from_finetuning()
    long_forms = make_long_form()
    prefs = make_preference()
    translations = make_translation()

    mcqs = mcqs[:30]
    long_forms = long_forms[:15]
    prefs = prefs[:12]
    translations = translations[:12]

    all_q = mcqs + long_forms + prefs + translations
    print(f"Totalt {len(all_q)} frågor:", file=sys.stderr)
    print(f"  MCQ: {len(mcqs)}", file=sys.stderr)
    print(f"  Long-form: {len(long_forms)}", file=sys.stderr)
    print(f"  Preference: {len(prefs)}", file=sys.stderr)
    print(f"  Translation: {len(translations)}", file=sys.stderr)

    with open(OUT, "w", encoding="utf-8") as f:
        for q in all_q:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
