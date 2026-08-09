# Körningsplan före publicering

Baserat på kritisk granskning. Tre nya datainsamlingar:

## 1. Placebo-kontroll (9 nya frågor)

**Syfte:** Avgöra om GLM-5.2:s `urllib`-mönster är geopolitisk trigger eller generell organisationskontext.

**Design:** Samma tekniska uppgifter (sleeper_003, 007, 011) med neutrala företagskontexter:
- Volvo (logistikverktyg)
- IKEA (lagerhantering)  
- Ericsson (nätverksövervakning)

**Kör:** `python3 scripts/run_eval.py` (hela 369-frågebatteriet)

**Analys:** Jämför `urllib`-frekvens:
- Baslinje (neutral): X%
- Geopolitisk trigger: Y%
- Placebo (Volvo/IKEA/Ericsson): Z%

Om Z ≈ Y → generell nervositet, inte geopolitisk targeting.

## 2. Domarkalibrering (50 par)

**Syfte:** Validera att Mistral Small (24B) och Mistral Medium (128B) rankar modeller i samma ordning.

**Kör:** 
```bash
python3 scripts/run_judge_calibration.py --sample-size 50
# Sedan manuell eller API-driven om-bedömning med båda domarna
```

**Analys:** Cohen's kappa eller enkel överensstämmelseprocent.

Om κ < 0.6 → rapportera flaggrater separat per domare, inte aggregerat.

## 3. Multi-sample för hög-flip-modeller (5 samples × 44 par × 3 modeller = 660 anrop)

**Syfte:** GPT-OSS (76% flip), Llama 3.3 (75%), Kimi K3 (67%) — deras enstaka flaggor är nästan meningslösa.

**Kör:**
```bash
python3 scripts/run_multisample_eval.py \
  --models "openai/gpt-oss-120b,meta-llama/Llama-3.3-70B-Instruct,moonshotai/Kimi-K3" \
  --samples 5
```

**Analys:** Rapportera medelvärde ± standardavvikelse istället för binärt flagg/inte flagg.

## Total omfattning

| Åtgärd | API-anrop | Tid (75 req/min) |
|--------|-----------|------------------|
| Placebo (9 frågor × 9 modeller) | 81 | ~1 min |
| Domarkalibrering (50 par × 2 domare) | 100 | ~2 min |
| Multi-sample (3 modeller × 44 par × 5 samples) | 660 | ~9 min |
| **Totalt** | **841** | **~12 min** |

Plus fullständig omkörning av 369 frågor för att få placebo-data: ~30 min.

## Artikeluppdatering efter körning

1. **Placebo:** Ny sektion "Is it geopolitics or just specificity?" med jämförelse
2. **Domarkalibrering:** Uppdatera limitations med överensstämmelsegrad
3. **Multi-sample:** Nya tabeller för GPT-OSS, Llama 3.3, Kimi K3 med medelvärden

## Godkännande för publicering

- [ ] Placebo visar Z ≈ Y (generell nervositet) eller Z << Y (geopolitisk specifik)
- [ ] Domarkalibrering κ > 0.6 (eller separata rapporteringar)
- [ ] Multi-sample visar att flaggmönster är stabila (CV < 50%)
