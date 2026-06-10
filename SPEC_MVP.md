# Barometr – specyfikacja niefunkcjonalna (MVP)

Uzupełnienie do silnika i makiet. Wymagania dot. bezpieczeństwa, zużycia zasobów i odświeżania.

## 1. Bezpieczeństwo

### Klucze i sekrety
- Klucz LLM (OpenRouter) **tylko po stronie silnika** (serwer/CI). NIGDY w aplikacji mobilnej.
- Aplikacja telefonu pobiera wyłącznie publiczny `barometer.json` – nie zna żadnego klucza.
- Sekrety w `.env` / GitHub Secrets, pliki objęte `.gitignore`, uprawnienia `600`.
- Limit wydatków ustawiony w panelu OpenRouter (ochrona przed kosztem przy wycieku).
- Rotacja kluczy, które kiedykolwiek pojawiły się poza `.env` (np. w czacie).

### Odporność na ataki (specyfika tej aplikacji)
- **Prompt injection przez nagłówki** (główne ryzyko): nagłówki są niezaufane; silnik
  traktuje je jako dane, ignoruje instrukcje w treści; ocena jest walidowana i przycinana
  do zakresu 1.0–10.0 (model nie może wymusić wartości spoza skali ani innego formatu).
- **Parsowanie RSS/XML**: korzystać z bibliotek odpornych na XXE/„billion laughs”;
  limit rozmiaru pobieranych danych, timeouty.
- **TLS/MITM**: wszystkie połączenia po HTTPS; w aplikacji walidacja certyfikatu (bez
  wyłączania weryfikacji), brak czystego HTTP.
- **Integralność danych**: `barometer.json` serwowany z zaufanego hosta po HTTPS.
- **Łańcuch dostaw**: pinowanie wersji zależności, regularny audyt (`pip-audit`).
- **Uprawnienia aplikacji**: minimum (sieć + powiadomienia). Brak lokalizacji, kontaktów itp.

## 2. Optymalizacja zasobów (jak aplikacja pogody)

Cel: aplikacja nie drenuje baterii, internetu ani CPU.

- **Brak ciągłej pracy w tle.** Żadnej usługi działającej non-stop, żadnych wakelocków.
- **Aktualizacja cykliczna przez WorkManager**, interwał ~15–30 min (minimum systemowe 15 min),
  z ograniczeniami: tylko gdy jest sieć i bateria nie jest niska.
- **Jedno pobranie zasila aplikację i widget** (brak podwójnych zapytań).
- **Mały transfer**: `barometer.json` to ~1–2 KB. Używać cache HTTP (ETag / If-Modified-Since);
  gdy brak zmian → odpowiedź 304, zero pobierania treści.
- **Cache lokalny**: ostatni wynik trzymany lokalnie; offline pokazuje ostatni znany stan
  + znacznik „nieaktualne”.
- **Backoff przy błędach**: wykładnicze ponawianie, bez agresywnego odpytywania.
- **Szacunek dzienny**: przy 15-min cyklu < ~1 MB/dobę i pomijalne zużycie baterii.

## 3. Odświeżanie na życzenie użytkownika

- **Pull-to-refresh** na ekranie głównym (gest pociągnięcia w dół).
- **Tap na widgrecie** wyzwala jednorazowe odświeżenie (one-off WorkManager).
- **Throttling**: ręczne odświeżenie nie częściej niż raz na ~60 s (ochrona przed spamem
  i nadmiernym ruchem); w międzyczasie pokazujemy ostatni wynik.
- Widoczny stan: „aktualizacja…”, czas ostatniej aktualizacji, obsługa błędu/offline.

## 4. Powiadomienia (przypomnienie z logiki MVP)
- Decyzja lokalnie na telefonie: `score ≥ próg` ORAZ wzrost względem poprzedniego ORAZ
  minęło ≥ 3 h od ostatniego powiadomienia (limit częstotliwości).
- Uprawnienie `POST_NOTIFICATIONS` (Android 13+).
