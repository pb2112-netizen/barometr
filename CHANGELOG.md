# CHANGELOG — barometr (silnik)

Historia projektu (append-only). Najnowsze na górze.

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
