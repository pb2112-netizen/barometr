# CHANGELOG — barometr (silnik)

Historia projektu (append-only). Najnowsze na górze.

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
