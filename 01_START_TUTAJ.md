> ============================================================
> ## ETAP 1 z 2 — BACKEND (silnik) GOTOWY ✅ + plan aplikacji
> Ten plik opisuje GOTOWY backend i kontrakt danych. **NIE buduj backendu od nowa.**
> Aplikacja Android jest **JUŻ ZBUDOWANA** w kolejnym etapie.
> 👉 Najnowszy stan i punkt startu dla nowej sesji: **`../WorldBarometer/02_HANDOVER.md`** (ETAP 2).
> Lokalnie oba projekty w `WB/` (`E:\AI\Agenci_SEO\WB\`).
> ============================================================

# START TUTAJ — handoff do budowy aplikacji Android v1

Ten plik to „twarda prawda" projektu. Nowy czat (czyste okno kontekstu) ma to przeczytać
na starcie, zanim zacznie cokolwiek kodować. Backend (silnik oceny) jest **gotowy i działa**.
Kolejny etap to **aplikacja na Androida**, która tylko czyta gotowy wynik.

---

## 1. Co już działa (NIE ruszać tego bez powodu)

Silnik oceny wydarzeń działa w pełni automatycznie w chmurze:

```
GitHub Actions (co 30 min)  →  silnik.py: pobiera RSS + ocenia modelem AI  →  barometer.json (publiczny URL)
```

- Repozytorium: `https://github.com/pb2112-netizen/barometr`
- Silnik: `silnik.py` (Python), uruchamiany przez `.github/workflows/barometr.yml` (cron `*/30 * * * *` + ręcznie).
- Model AI: `anthropic/claude-sonnet-4.6` przez OpenRouter (klucz w GitHub Secrets jako `OPENROUTER_API_KEY`).
- Źródła RSS: BBC World, Al Jazeera, The Guardian World.
- Logika: ocena dziesiętna 1.0–10.0, polski kontekst (profil użytkownika), „domyślnie nisko",
  ocena ZMIANY a nie istnienia wydarzenia, decay dla ciągnących się tematów, pamięć stanu świata.

**Aplikacja NIE zna żadnego klucza API.** Pobiera wyłącznie publiczny plik JSON.

---

## 2. Adres danych dla aplikacji (multi-lens, WB-008)

Baza URL (bez zmian):

```
https://raw.githubusercontent.com/pb2112-netizen/barometr/main/
```

| Plik | Rola |
|------|------|
| `barometer_{lens}.json` | Wynik per kraj: `pl`, `ro`, `pt`, `ua`, `us` |
| `barometer.json` | **Alias kompatybilności** — zawsze kopia `barometer_pl.json` |
| `manifest.json` | Indeks lensów + względne URL-e plików wynikowych |
| `lenses.json` | Katalog profili lensów (konfiguracja silnika, commitowana) |

Przykład: `.../main/barometer_pl.json` (domyślny lens aplikacji).

- Publiczny, HTTPS, ~1–2 KB per plik, HTTP 200, bez autoryzacji.
- Pamięć (`pamiec_{lens}.json`) — osobna per kraj; nie publikowana do apki.
- Wspiera `ETag` / `If-Modified-Since` → odpowiedź 304 (oszczędność transferu).

---

## 3. Schemat `barometer.json` (kontrakt danych)

```json
{
  "global_score": 4.2,
  "short_summary": "Regional tensions, no direct EU threat",
  "rationale": "Tekst uzasadnienia (EN).",
  "top_events": [
    {
      "title": "Ukraine strikes military plant 900 km inside Russia",
      "summary": "Krótki opis wydarzenia (EN).",
      "score": 4.2,
      "nowosc": "nowe",
      "category": "geopolityka",
      "sources": ["BBC", "Al Jazeera"]
    }
  ],
  "tryb": "AI (anthropic/claude-sonnet-4.6)",
  "level_label": "Low",
  "trend": "stable",
  "updated_at": "2026-06-10T16:05:45.579337Z",
  "liczba_naglowkow": 45,
  "lens_id": "pl",
  "lens_name_en": "Poland"
}
```

Pola opcjonalne (WB-008): `lens_id`, `lens_name_en`.

Pola kluczowe dla UI:
- `global_score` (float 1.0–10.0) — wielka liczba na ekranie i podstawa koloru.
- `level_label` — `Stable` / `Low` / `Elevated` / `High` / `Critical` (steruje kolorem/gradientem).
- `trend` — `rising` / `falling` / `stable` (kolor strzałki, niezależny od poziomu).
- `short_summary` — jednolinijkowe podsumowanie pod liczbą.
- `top_events[]` — lista TOP 3 (`title`, `summary`, `score`, `sources`).
- `updated_at` — ISO UTC, do „ostatnia aktualizacja".

Język treści: **angielski** (polski w przyszłości).

---

## 4. Kolory → poziomy (źródło: `makiety/paleta.json`)

Tylko kolory/gradienty, **żadnych ikon** (decyzja MVP).

| level_label | zakres score | kolor      | gradient (2 stopnie)   |
|-------------|--------------|------------|------------------------|
| Stable      | 1.0–2.9      | `#15803D`  | `#064E3B` → `#16A34A`  |
| Low         | 3.0–4.9      | `#65A30D`  | `#3F6212` → `#84CC16`  |
| Elevated    | 5.0–6.9      | `#D97706`  | `#92400E` → `#F59E0B`  |
| High        | 7.0–8.9      | `#EA580C`  | `#9A3412` → `#FB923C`  |
| Critical    | 9.0–10.0     | `#B91C1C`  | `#7F1D1D` → `#EF4444`  |

Trend: `rising #DC2626`, `falling #16A34A`, `stable #94A3B8`.
Neutralne (tło/tekst/karta, light+dark) — patrz `makiety/paleta.json`.

Zastosowanie:
- **Widget pulpitu**: tło = gradient poziomu (2 stopnie), tekst biały, bez ikon.
- **Ekran główny**: wielka cyfra w kolorze poziomu, tło neutralne; pasek 0–10 wypełniony kolorem poziomu.
- **Etykieta poziomu**: kropka/tekst w kolorze poziomu.
- **Badge przy evencie**: kolor liczony z `score` danego eventu.

---

## 5. Decyzje techniczne (uzgodnione)

- Język: **Kotlin**, UI: **Jetpack Compose**.
- Widget pulpitu: **Glance**.
- Cykliczne odświeżanie w tle: **WorkManager** (15–30 min; tylko gdy sieć + bateria OK).
- Lokalne dane/ustawienia: **DataStore**.
- Sieć: HTTPS + cache (ETag/If-Modified-Since), walidacja certyfikatu (bez wyłączania).
- Min. uprawnienia: **sieć** + **POST_NOTIFICATIONS** (Android 13+). Bez lokalizacji/kontaktów.

Wymagania niefunkcjonalne (bezpieczeństwo, bateria, dane, odświeżanie) — pełny opis w `SPEC_MVP.md`. Przeczytać.

---

## 6. Zakres MVP aplikacji

1. **Ekran główny**: wielka liczba `global_score` (kolor wg poziomu), `level_label`, `short_summary`,
   strzałka trendu, pasek 0–10, lista TOP 3 (`title` + `summary` + badge ze `score`), czas `updated_at`.
2. **Widget na pulpit** (Glance): tło = gradient poziomu, liczba `global_score`, bez ikon.
   Tap = jednorazowe odświeżenie.
3. **Odświeżanie**: WorkManager co ~15–30 min + **pull-to-refresh** (throttling min. ~60 s).
   Offline = ostatni znany wynik + znacznik „nieaktualne".
4. **Powiadomienia (lokalnie na telefonie)**: wyślij gdy `score ≥ próg` ORAZ wzrost względem
   poprzedniego ORAZ minęło ≥ 3 h od ostatniego powiadomienia. Próg ustawialny suwakiem.
5. **Ustawienia**: suwak progu powiadomień (domyślnie 5.0), przełącznik powiadomień, info o ostatniej aktualizacji.

Poza MVP (NIE robić teraz): historia/wykresy trendu, archiwum, konta, wiele profili, personalizacja źródeł w appce.

---

## 7. Prompt startowy do nowej rozmowy (skopiuj i wklej)

> ⚠️ UWAGA: ten prompt został JUŻ WYKONANY — aplikacja jest zbudowana (ETAP 2).
> NIE uruchamiaj go ponownie. To zapis historyczny. Aktualny punkt startu: `../WorldBarometer/02_HANDOVER.md`.

> Buduję natywną aplikację Android (Kotlin + Jetpack Compose) o nazwie „World Barometer".
> Backend już istnieje i działa — aplikacja TYLKO pobiera gotowy plik JSON z publicznego URL:
> `https://raw.githubusercontent.com/pb2112-netizen/barometr/main/barometer.json`
>
> Najpierw przeczytaj w repo pliki: `START_TUTAJ.md`, `SPEC_MVP.md` i `makiety/paleta.json` —
> zawierają kontrakt danych, kolory→poziomy, decyzje techniczne i zakres MVP. Trzymaj się ich.
>
> Stos: Kotlin, Jetpack Compose, Glance (widget), WorkManager (odświeżanie w tle), DataStore (ustawienia).
> Zacznij od zaproponowania struktury projektu i listy zadań, a potem zbuduj szkielet:
> (1) warstwa sieci + model danych z JSON, (2) ekran główny, (3) widget, (4) WorkManager + powiadomienia, (5) ustawienia.
> Pracuj małymi krokami, po kolei. Najpierw plan, potem kod.

---

## 8. Praca z repo (przypomnienie)

- Klucz API: tylko w GitHub Secrets (`OPENROUTER_API_KEY`) i lokalnym `.env`. Nigdy w kodzie/appce.
- `barometer.json` i `pamiec.json` są generowane przez workflow (ignorowane lokalnie, wymuszane na push przez CI).
- Ręczne uruchomienie silnika: zakładka **Actions** → „Barometr update" → **Run workflow**.
