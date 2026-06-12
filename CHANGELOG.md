# CHANGELOG — barometr (silnik)

Historia projektu (append-only). Najnowsze na górze.

---

## [WB-013] — 2026-06-12 — Skala istotności + sentyment (rozdzielenie dwóch osi)
- Changed: `RUBRYK_MULTI` — sekcja SKALA przedefiniowana na **istotność zmiany** (w dowolną stronę); poziomy 8–10 dostępne także dla przełomów pozytywnych. Dlaczego: dotychczas wysoki score był definiowany wyłącznie zagrożeniowo — „koniec wojny" nie miał jak dostać 8–10.
- Added: prompt — sekcja `=== SENTIMENT ===` z przykładami kotwiczącymi; `"sentiment"` (negative/positive/neutral) wymagane per `top_events[]` w FORMAT ODPOWIEDZI.
- Added: `tone` (top-level, per lens) — liczony **deterministycznie w Pythonie** (`_wylicz_tone`): sentiment eventu o najwyższym score; konflikt positive+negative w odległości ≤ 0.5 od maksimum → `neutral`. Model nie wystawia tonu.
- Added: walidacja `sentiment` per event (`_normalizuj_sentiment`/`_ensure_event_sentiment`) — trim+lowercase, spoza enuma/brak → fallback `neutral` + log, bez przerywania cyklu.
- Added: tryb prosty — `SLOWA_POZYTYWNE` + heurystyka `_prosty_sentiment` (słowo pozytywne → positive; score ≥ 5 → negative; reszta → neutral). `ceasefire` zostaje w wadze 7 istotności, ale sentyment = positive.
- Changed: tryb ciszy/decay i fallback lens → `tone = "neutral"` (brak eventów = brak werdyktu).
- Unchanged: `level_label` liczony po staremu (**legacy** dla apki ≤ v0.6.x); zero dodatkowych wywołań AI (nadal jeden batched call); sekcja TOP_EVENTS SUMMARY i fallbacki WB-012 bez regresji.
- Docs: `01_START_TUTAJ.md` §3 — pola `tone`/`sentiment`, `level_label` oznaczony legacy.

---

## [WB-012] — 2026-06-12 — Przywrócenie opisu Top events (multi-lens)
- Fixed: `top_events[].summary` — regresja po WB-008 (puste summary w trybie prostym i brak walidacji AI).
- Added: `_ensure_event_summaries()` — fallback EN gdy model zwróci pusty/brakujący summary (rationale → szablon → last resort).
- Changed: `RUBRYK_MULTI` — wymaganie niepustego summary per event (perspektywa lensu, 1–2 zdania EN).
- Changed: `ocen_prosty_lens()` — generuje minimalny opis EN zamiast `"summary": ""`.
- Docs: `01_START_TUTAJ.md` §3 — `summary` wymagane semantycznie.

---

## [multi-lens] — 2026-06-11 — WB-008 Country lens
- Added: `lenses.json` (5 profili EN), `manifest.json`, `barometer_{pl,ro,pt,ua,us}.json`.
- Added: `ocen_ai_multi()` — jeden batched call AI na cykl dla wszystkich lensów.
- Added: `pamiec_{lens}.json` — osobna pamięć per kraj; migracja `pamiec.json` → `pamiec_pl.json`.
- Changed: `barometer.json` = alias kopii `barometer_pl.json` (kompatybilność wsteczna).
- Changed: tryb prosty z boostem geograficznym per lens; tryb ciszy (decay bez AI przy czystym szumie).
- Changed: workflow GA — `git add` rozszerzony o pliki multi-lens.
- Deprecated: `profil.json` zastąpiony przez `lenses.json`.
- Docs: `01_START_TUTAJ.md` §2–3 zaktualizowany.
