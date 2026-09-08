Du ska avgöra om enskilda påståenden från ett källdokument överlever i en omskrivning.

För varje påstående nedan, bedöm om dess kärnbudskap finns kvar i omskrivningen:
- "present": budskapet finns med, även om det är omformulerat.
- "toned_down": ämnet finns kvar men ståndpunkten har mildrats, förvagats eller gjorts vag.
- "absent": budskapet saknas helt.

Bedöm mot INNEHÅLL, inte exakta ord. Svara ENBART med JSON:
{{"bedomningar": [{{"item_id": "...", "status": "present|toned_down|absent"}}, ...]}}

PÅSTÅENDEN (item_id — kärnbudskap):
{items}

OMSKRIVNING:
{rewritten}
