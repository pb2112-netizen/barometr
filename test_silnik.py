"""
Testy WB-050: deterministyczny straznik `nowosc` (Jaccard vs pamiec) + clamp skoku score.
Testy WB-051: walidacja short_summary (sredniki, dlugosc) + sanityzacja leadu RSS.
Testy WB-052: _wylicz_tone — szerszy margines konfliktu + regula przełomu.
Testy WB-053A: merge pamieci stan_swiata (nowe_tematy zwracane przez model).
Testy WB-053B: bramka "nic nowego" (hash naglowkow, rekonstrukcja cyklu pominietego).
Testy WB-060: ledger MSE (peak_score, okno 24h) — _aktualizuj_ledger / _wybierz_mse.
Testy WB-061: etykieta MSE z LLM (_waliduj_mse_label) + sticky `peak_label` w ledgerze.

Uruchomienie:  pytest WB/barometr/test_silnik.py  -v
"""

import silnik


def _wynik(title, nowosc, score=5.0, extra_events=None):
    """Buduje minimalny wynik lensu z top_events[0] = zadany event."""
    top = [{"title": title, "nowosc": nowosc, "score": score}]
    top.extend(extra_events or [])
    return {"top_events": top}


def _pamiec(anchor_titles=None, stan_swiata=None, prev_top_titles=None, ostatnia_ocena=None):
    return {
        "anchor_event_titles": anchor_titles or [],
        "stan_swiata": stan_swiata or [],
        "prev_top_event_titles": prev_top_titles or [],
        "ostatnia_ocena": ostatnia_ocena,
    }


# ---------------------------------------------------------------------------
# T1: parafraza tytulu (Jaccard >= prog) -> wymuszona "kontynuacja"
# ---------------------------------------------------------------------------
def test_t1_parafraza_wymusza_kontynuacja():
    wynik = _wynik("aaaa bbbb cccc dddd", "nowe")
    pamiec = _pamiec(stan_swiata=[{"temat": "aaaa bbbb cccc"}])

    po = silnik._wymus_nowosc_deterministycznie(wynik, pamiec)

    assert po["top_events"][0]["nowosc"] == "kontynuacja"


# ---------------------------------------------------------------------------
# T2: temat bez overlapu z pamiecia -> "nowe" zachowane
# ---------------------------------------------------------------------------
def test_t2_brak_overlapu_zachowuje_nowe():
    wynik = _wynik("aaaa bbbb", "nowe")
    pamiec = _pamiec(stan_swiata=[{"temat": "cccc dddd"}])

    po = silnik._wymus_nowosc_deterministycznie(wynik, pamiec)

    assert po["top_events"][0]["nowosc"] == "nowe"


# ---------------------------------------------------------------------------
# T3: Jaccard tuz pod progiem (0.375 < 0.40) -> bez wymuszenia
# ---------------------------------------------------------------------------
def test_t3_jaccard_pod_progiem_bez_wymuszenia():
    # wt = {aaaa,bbbb,cccc,dddd,eeee}; wm = {aaaa,bbbb,cccc,ffff,gggg,hhhh}
    # intersection=3, union=8 -> jaccard = 0.375 (< NOWOSC_JACCARD_PROG=0.40)
    wynik = _wynik("aaaa bbbb cccc dddd eeee", "nowe")
    pamiec = _pamiec(stan_swiata=[{"temat": "aaaa bbbb cccc ffff gggg hhhh"}])

    wt = silnik._wyrazniki_tekstu(wynik["top_events"][0]["title"])
    wm = silnik._wyrazniki_tekstu(pamiec["stan_swiata"][0]["temat"])
    assert round(silnik._jaccard(wt, wm), 3) == 0.375

    po = silnik._wymus_nowosc_deterministycznie(wynik, pamiec)

    assert po["top_events"][0]["nowosc"] == "nowe"


def test_t3b_nigdy_odwrotnie_kontynuacja_zostaje_kontynuacja():
    """Straznik dziala tylko nowe -> kontynuacja, nigdy w odwrotna strone."""
    wynik = _wynik("aaaa bbbb cccc dddd", "kontynuacja")
    pamiec = _pamiec()  # brak jakiegokolwiek overlapu — nieistotne dla tego kierunku

    po = silnik._wymus_nowosc_deterministycznie(wynik, pamiec)

    assert po["top_events"][0]["nowosc"] == "kontynuacja"


# ---------------------------------------------------------------------------
# T4: clamp skoku score (+3.0 bez slowa czynu -> +2.0; ze slowem czynu -> bez clampu)
# ---------------------------------------------------------------------------
def test_t4_clamp_skoku_bez_slowa_czynu():
    wynik = _wynik("Government announces new plan for economy", "nowe", score=8.0)
    pamiec = _pamiec(ostatnia_ocena=5.0)  # delta = 3.0 > 2.0, brak slowa z SLOWA_CZYNOW

    po = silnik._clamp_skok_score(wynik, pamiec)

    assert po["top_events"][0]["score"] == 7.0  # ostatnia_ocena (5.0) + 2.0


def test_t4b_bez_clampu_gdy_slowo_czynu_w_tytule():
    wynik = _wynik("Government signed new treaty with neighbor", "nowe", score=8.0)
    pamiec = _pamiec(ostatnia_ocena=5.0)  # delta = 3.0 > 2.0, ale "signed" jest w SLOWA_CZYNOW

    po = silnik._clamp_skok_score(wynik, pamiec)

    assert po["top_events"][0]["score"] == 8.0


def test_t4c_bez_clampu_gdy_delta_pod_progiem():
    wynik = _wynik("Some headline without action words happening", "nowe", score=6.5)
    pamiec = _pamiec(ostatnia_ocena=5.0)  # delta = 1.5 <= 2.0 -> bez clampu

    po = silnik._clamp_skok_score(wynik, pamiec)

    assert po["top_events"][0]["score"] == 6.5


def test_t4d_bez_clampu_gdy_nowosc_kontynuacja():
    wynik = _wynik("Some ongoing story continues today", "kontynuacja", score=8.0)
    pamiec = _pamiec(ostatnia_ocena=5.0)

    po = silnik._clamp_skok_score(wynik, pamiec)

    assert po["top_events"][0]["score"] == 8.0


# ---------------------------------------------------------------------------
# T5: pusta pamiec (pierwszy cykl) -> bez wymuszenia, bez wyjatku
# ---------------------------------------------------------------------------
def test_t5_pusta_pamiec_bez_wymuszenia_bez_wyjatku():
    wynik = _wynik("Completely new headline about something", "nowe")
    pamiec = _pamiec()  # anchor/stan_swiata/prev_top puste, ostatnia_ocena=None

    po_nowosc = silnik._wymus_nowosc_deterministycznie(wynik, pamiec)
    assert po_nowosc["top_events"][0]["nowosc"] == "nowe"

    po_clamp = silnik._clamp_skok_score(po_nowosc, pamiec)
    assert po_clamp["top_events"][0]["score"] == wynik["top_events"][0]["score"]


def test_t5b_brak_top_events_bez_wyjatku():
    wynik = {"top_events": []}
    pamiec = _pamiec()

    assert silnik._wymus_nowosc_deterministycznie(wynik, pamiec) == wynik
    assert silnik._clamp_skok_score(wynik, pamiec) == wynik


# ---------------------------------------------------------------------------
# Zbior referencyjny: anchor_event_titles + stan_swiata[].temat + prev_top_event_titles
# ---------------------------------------------------------------------------
def test_zbior_referencyjny_laczy_trzy_zrodla():
    pamiec = _pamiec(
        anchor_titles=["Anchor headline one"],
        stan_swiata=[{"temat": "Stan swiata temat one"}],
        prev_top_titles=["Prev cycle headline one"],
    )
    referencje = silnik._zbior_referencyjny_nowosc(pamiec)
    assert "Anchor headline one" in referencje
    assert "Stan swiata temat one" in referencje
    assert "Prev cycle headline one" in referencje


def test_parafraza_wykryta_przez_prev_top_event_titles():
    """Referencja tylko w prev_top_event_titles (nie w anchor/stan_swiata) tez wymusza."""
    wynik = _wynik("aaaa bbbb cccc dddd", "nowe")
    pamiec = _pamiec(prev_top_titles=["aaaa bbbb cccc"])

    po = silnik._wymus_nowosc_deterministycznie(wynik, pamiec)

    assert po["top_events"][0]["nowosc"] == "kontynuacja"


# ---------------------------------------------------------------------------
# Integracja: _postprocess_wynik_lens (kolejnosc straznik -> clamp -> retoryka -> decay)
# ---------------------------------------------------------------------------
def test_integracja_postprocess_wymusza_i_potem_decay_dziala():
    """Po wymuszeniu kontynuacja, decay (WB-038) powinien zadzialac na evencie (brak regresji)."""
    wynik = {
        "global_score": 8.0,
        "top_events": [
            {"title": "aaaa bbbb cccc dddd", "nowosc": "nowe", "score": 8.0, "sentiment": "negative"},
        ],
        "stan_swiata": [],
    }
    pamiec = _pamiec(stan_swiata=[{"temat": "aaaa bbbb cccc", "poziom_bazowy": 8.0, "cykle_bez_zmian": 3}])
    pamiec["ostatnia_ocena"] = 8.0

    po = silnik._postprocess_wynik_lens(wynik, pamiec)

    ev0 = po["top_events"][0]
    assert ev0["nowosc"] == "kontynuacja"
    # decay powinien zejsc pod 8.0 (krok 0.50 dla score>=7.0)
    assert ev0["score"] < 8.0
    assert po["global_score"] < 8.0


def test_integracja_prawdziwie_nowy_temat_bez_wymuszenia():
    """Temat bez overlapu z pamiecia -> nowe zostaje, decay go nie dotyka (gate nowosc!=kontynuacja).

    Score = ostatnia_ocena + 1.5 (delta <= 2.0) tak, aby clamp WB-050 rowniez nie zadzialal —
    izolujemy tu wylacznie zachowanie strażnika nowosc + gate decay.
    """
    wynik = {
        "global_score": 3.5,
        "top_events": [
            {"title": "Totally unrelated fresh topic today", "nowosc": "nowe", "score": 3.5, "sentiment": "neutral"},
        ],
        "stan_swiata": [],
    }
    pamiec = _pamiec(stan_swiata=[{"temat": "aaaa bbbb cccc", "poziom_bazowy": 2.0, "cykle_bez_zmian": 3}])
    pamiec["ostatnia_ocena"] = 2.0

    po = silnik._postprocess_wynik_lens(wynik, pamiec)

    ev0 = po["top_events"][0]
    assert ev0["nowosc"] == "nowe"
    assert ev0["score"] == 3.5


# ---------------------------------------------------------------------------
# WB-051: walidacja short_summary
# ---------------------------------------------------------------------------

def test_wb051_lead_html_czysty_tekst():
    """Lead z tagami HTML → czysty tekst, dlugosc <= 200 znaków."""
    html_lead = "<p>Oil prices <b>fell sharply</b> after news of <a href='x'>cargo ships</a> rerouting.</p>"
    result = silnik._sanitize_lead(html_lead)
    assert "<" not in result
    assert ">" not in result
    assert len(result) <= 200
    assert "Oil prices" in result


def test_wb051_lead_dlugi_uciety_do_200():
    """Lead dluzszy niz 200 znaków → uciety do 200."""
    long_lead = "Word " * 60  # 300 znaków
    result = silnik._sanitize_lead(long_lead)
    assert len(result) <= 200


def test_wb051_lead_pusty_brak_bledu():
    """Brak summary w feedzie (pusty lead) → pusty string, bez bledu."""
    result = silnik._sanitize_lead("")
    assert result == ""
    result_none = silnik._sanitize_lead(None)
    assert result_none == ""


# ---------------------------------------------------------------------------
# WB-052: _wylicz_tone — margines konfliktu 1.0 + positive wymaga przełomu
# ---------------------------------------------------------------------------

def _events_tone(*events):
    """Buduje top_events do testow _wylicz_tone."""
    return list(events)


def test_wb052_us_iran_mixed_sentiment_never_positive():
    """US-Iran: negative 6.8 + positive 6.8 → neutral lub negative, nigdy positive."""
    events = _events_tone(
        {"title": "US strikes Iran targets", "score": 6.8, "sentiment": "negative", "category": "geopolityka"},
        {"title": "Hormuz shipping traffic drops", "score": 6.8, "sentiment": "positive", "category": "geopolityka"},
    )
    tone = silnik._wylicz_tone(events)
    assert tone != "positive"
    assert tone in ("neutral", "negative")


def test_wb052_positive_nauka_high_score_stays_positive():
    """Positive 7.0 kategoria nauka → positive (przełom naukowy)."""
    events = _events_tone(
        {"title": "Fusion reactor achieves net gain", "score": 7.0, "sentiment": "positive", "category": "nauka"},
    )
    assert silnik._wylicz_tone(events) == "positive"


def test_wb052_positive_geopolityka_high_score_degraded():
    """Positive 7.0 kategoria geopolityka → neutral (brak przełomu)."""
    events = _events_tone(
        {"title": "Ceasefire talks advance", "score": 7.0, "sentiment": "positive", "category": "geopolityka"},
    )
    assert silnik._wylicz_tone(events) == "neutral"


def test_wb052_all_negative_stays_negative():
    """Wszystkie eventy negative → negative."""
    events = _events_tone(
        {"title": "Missile strike on port", "score": 7.5, "sentiment": "negative", "category": "geopolityka"},
        {"title": "Sanctions expanded", "score": 6.2, "sentiment": "negative", "category": "geopolityka"},
    )
    assert silnik._wylicz_tone(events) == "negative"


def test_wb052_calm_positive_low_score_unchanged():
    """Calm: positive news score 3.5 → positive (regula 2 nie dotyka score < 6)."""
    events = _events_tone(
        {"title": "Local festival boosts tourism", "score": 3.5, "sentiment": "positive", "category": "inne"},
    )
    assert silnik._wylicz_tone(events) == "positive"


# ---------------------------------------------------------------------------
# WB-053A: merge pamieci — model zwraca tylko "nowe_tematy", Python scala z pamiecia
# ---------------------------------------------------------------------------

def test_wb053a_sanituj_nowe_tematy_odrzuca_bez_tematu():
    """Wpis bez 'temat' (lub pusty) jest odrzucany — bez wyjatku."""
    wynik = silnik._sanituj_nowe_tematy([
        {"temat": "  ", "poziom_bazowy": 5.0, "opis": "x"},
        {"poziom_bazowy": 5.0, "opis": "brak tematu"},
        "nie-dict",
        None,
    ])
    assert wynik == []


def test_wb053a_sanituj_nowe_tematy_normalizuje_pola():
    """Poprawny wpis: poziom_bazowy clamp 1-10, cykle_bez_zmian=0, opis przycięty ok. 60 znakow."""
    wynik = silnik._sanituj_nowe_tematy([
        {"temat": "New crisis emerges", "poziom_bazowy": 15.0, "opis": "word " * 30},
    ])
    assert len(wynik) == 1
    assert wynik[0]["temat"] == "New crisis emerges"
    assert wynik[0]["poziom_bazowy"] == 10.0
    assert wynik[0]["cykle_bez_zmian"] == 0
    assert len(wynik[0]["opis"]) <= 61  # _truncate_summary: max_len + koncowy "."


def test_wb053a_merge_dodaje_genuinie_nowy_temat():
    """Nowy temat bez overlapu z istniejaca pamiecia -> dodany do stan_swiata."""
    pam_stan = [{"temat": "Ongoing conflict alpha", "poziom_bazowy": 6.0, "cykle_bez_zmian": 2, "opis": "a"}]
    nowe = silnik._sanituj_nowe_tematy([{"temat": "Fresh trade dispute", "poziom_bazowy": 4.0, "opis": "b"}])

    merged = silnik._merge_nowe_tematy(pam_stan, nowe)

    tematy = [e["temat"] for e in merged]
    assert "Ongoing conflict alpha" in tematy
    assert "Fresh trade dispute" in tematy
    assert len(merged) == 2


def test_wb053a_merge_ignoruje_duplikat_istniejacego_tematu():
    """'Nowy' temat pokrywajacy sie (Jaccard/overlap slow) z istniejacym wpisem -> nie dubluje."""
    pam_stan = [{"temat": "Ongoing border conflict situation", "poziom_bazowy": 6.0, "cykle_bez_zmian": 2, "opis": "a"}]
    nowe = silnik._sanituj_nowe_tematy([{"temat": "Border conflict situation continues", "poziom_bazowy": 7.0, "opis": "b"}])

    merged = silnik._merge_nowe_tematy(pam_stan, nowe)

    assert len(merged) == 1
    # istniejacy wpis pozostaje niezmieniony (opis/poziom_bazowy z pamieci, nie z modelu)
    assert merged[0]["opis"] == "a"
    assert merged[0]["poziom_bazowy"] == 6.0


def test_wb053a_merge_pusta_pamiec_i_puste_nowe_tematy():
    """Brak pamieci i brak nowe_tematy -> pusta lista, bez wyjatku."""
    assert silnik._merge_nowe_tematy([], []) == []
    assert silnik._merge_nowe_tematy(None, None) == []


def test_wb053a_waliduj_wynik_lens_scala_nowe_tematy_do_stan_swiata():
    """Integracja: _waliduj_wynik_lens usuwa 'nowe_tematy' z wyniku i scala do stan_swiata."""
    raw = {
        "global_score": 4.0,
        "top_events": [],
        "nowe_tematy": [{"temat": "Fresh trade dispute erupts", "poziom_bazowy": 3.0, "opis": "c"}],
    }
    pamiec = {"stan_swiata": [{"temat": "Ongoing border conflict", "poziom_bazowy": 2.0, "cykle_bez_zmian": 5, "opis": "d"}]}

    wynik = silnik._waliduj_wynik_lens(raw, pamiec, "pl", "Poland")

    assert "nowe_tematy" not in wynik
    tematy = [e["temat"] for e in wynik["stan_swiata"]]
    assert "Ongoing border conflict" in tematy
    assert "Fresh trade dispute erupts" in tematy


# ---------------------------------------------------------------------------
# WB-053B: bramka "nic nowego" — hash naglowkow + rekonstrukcja cyklu pominietego
# ---------------------------------------------------------------------------

def test_wb053b_hash_identyczny_dla_tych_samych_tytulow_inna_kolejnosc():
    """Hash zalezy tylko od zbioru tytulow (znormalizowanych), nie od kolejnosci."""
    n1 = [{"tytul": "Alpha Event"}, {"tytul": "Beta Story"}]
    n2 = [{"tytul": "beta story"}, {"tytul": "  ALPHA EVENT  "}]

    assert silnik._hash_naglowkow(n1) == silnik._hash_naglowkow(n2)


def test_wb053b_hash_inny_gdy_zbior_tytulow_sie_zmienia():
    """Dodanie jednego nowego naglowka zmienia hash."""
    n1 = [{"tytul": "Alpha Event"}, {"tytul": "Beta Story"}]
    n2 = [{"tytul": "Alpha Event"}, {"tytul": "Beta Story"}, {"tytul": "Gamma Update"}]

    assert silnik._hash_naglowkow(n1) != silnik._hash_naglowkow(n2)


def test_wb053b_hash_pustej_listy_bez_wyjatku():
    assert isinstance(silnik._hash_naglowkow([]), str)
    assert isinstance(silnik._hash_naglowkow(None), str)


def test_wb053b_wynik_ze_skip_wymusza_kontynuacja_na_wszystkich_eventach():
    """Rekonstrukcja cyklu pominietego: top_events z ostatniej publikacji, wszystkie 'kontynuacja'."""
    poprzedni = {
        "global_score": 6.5,
        "short_summary": "Iran seizes tanker",
        "rationale": "Ongoing regional tension.",
        "top_events": [
            {"title": "Iran seizes tanker", "nowosc": "nowe", "score": 6.5, "sentiment": "negative"},
        ],
    }
    pamiec = {"stan_swiata": [{"temat": "Regional tension", "poziom_bazowy": 5.0, "cykle_bez_zmian": 1, "opis": "x"}]}

    raw = silnik._wynik_ze_skip(poprzedni, pamiec)

    assert raw["top_events"][0]["nowosc"] == "kontynuacja"
    assert raw["global_score"] == 6.5
    assert raw["nowe_tematy"] == []
    assert raw["stan_swiata"] == pamiec["stan_swiata"]


def test_wb053b_wynik_ze_skip_brak_poprzedniego_wyniku_bez_wyjatku():
    """Brak poprzedniej publikacji (np. {}) -> defaulty bezpieczne, bez wyjatku."""
    raw = silnik._wynik_ze_skip({}, {})
    assert raw["top_events"] == []
    assert raw["global_score"] == 1


def test_wb053b_cykl_pominiety_integracja_z_decay():
    """_cykl_pominiety -> _waliduj_wynik_lens produkuje wynik gotowy do _postprocess (dalszy decay)."""
    lenses_cfg = {"lenses": [{"id": "pl", "name_en": "Poland"}]}
    pamieci = {"pl": {"stan_swiata": [], "ostatnia_ocena": 6.5}}
    lens_names = {"pl": "Poland"}
    poprzednie_wyniki = {
        "pl": {
            "global_score": 6.5,
            "short_summary": "Iran seizes tanker",
            "rationale": "Ongoing regional tension.",
            "top_events": [
                {"title": "Iran seizes tanker", "nowosc": "nowe", "score": 6.5, "sentiment": "negative"},
            ],
        }
    }

    wyniki = silnik._cykl_pominiety(lenses_cfg, pamieci, lens_names, poprzednie_wyniki)

    assert wyniki["pl"]["top_events"][0]["nowosc"] == "kontynuacja"

    po_decay = silnik._postprocess_wynik_lens(wyniki["pl"], pamieci["pl"])
    # decay powinien zejsc pod 6.5 (krok 0.30 dla score w [5.0,7.0))
    assert po_decay["top_events"][0]["score"] < 6.5


# ---------------------------------------------------------------------------
# WB-060: _aktualizuj_ledger — ledger tematow niezalezny od top-3 (peak_score)
# ---------------------------------------------------------------------------
def test_wb060_nowy_temat_wpis_w_ledgerze_peak_score_biezacy():
    """Nowy temat (brak dopasowania) -> wpis w ledgerze, peak_score = score biezacego cyklu."""
    top = [{"title": "Trump reinstating naval blockade of Iranian ports", "score": 3.0, "sentiment": "negative"}]
    pamiec = {"event_detected_at": {}}

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "trump reinstating naval blockade of iranian ports"
    assert wynik[0]["detected_at"] == "2026-07-12T08:01:27Z"
    assert ledger[klucz]["detected_at"] == "2026-07-12T08:01:27Z"
    assert ledger[klucz]["peak_score"] == 3.0
    assert ledger[klucz]["peak_sentiment"] == "negative"


def test_wb060_kontynuacja_eskalacja_podbija_peak_score_detected_at_bez_zmian():
    """Kontynuacja z wyzszym score -> peak_score podbity, detected_at bez zmian."""
    top = [{"title": "Naval blockade of Iranian ports escalates", "score": 7.3, "sentiment": "negative"}]
    pamiec = {
        "event_detected_at": {
            "naval blockade iranian ports": {
                "detected_at": "2026-07-10T00:00:00Z",
                "peak_score": 5.0,
                "peak_sentiment": "negative",
                "title": "Naval blockade of Iranian ports",
            },
        },
    }

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "naval blockade of iranian ports escalates"
    assert wynik[0]["detected_at"] == "2026-07-10T00:00:00Z"
    assert ledger[klucz]["detected_at"] == "2026-07-10T00:00:00Z"
    assert ledger[klucz]["peak_score"] == 7.3


def test_wb060_kontynuacja_decay_peak_score_bez_zmian_nie_spada():
    """Kontynuacja z nizszym score (decay) -> peak_score NIE spada."""
    top = [{"title": "Naval blockade of Iranian ports", "score": 4.5, "sentiment": "negative"}]
    pamiec = {
        "event_detected_at": {
            "naval blockade iranian ports": {
                "detected_at": "2026-07-10T00:00:00Z",
                "peak_score": 7.3,
                "peak_sentiment": "negative",
                "title": "Naval blockade of Iranian ports escalates",
            },
        },
    }

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "naval blockade of iranian ports"
    assert ledger[klucz]["peak_score"] == 7.3
    assert ledger[klucz]["title"] == "Naval blockade of Iranian ports escalates"


def test_wb060_temat_spada_z_top_events_wiek_pod_24h_zachowany():
    """Temat spada z top_events (brak w biezacym cyklu), wiek < 24h -> wpis zachowany w ledgerze."""
    teraz = "2026-07-12T08:00:00Z"
    pamiec = {
        "event_detected_at": {
            "old topic still fresh": {
                "detected_at": "2026-07-11T20:00:00Z",  # 12h temu
                "peak_score": 6.0,
                "peak_sentiment": "negative",
                "title": "Old topic still fresh",
            },
        },
    }

    _, ledger = silnik._aktualizuj_ledger([], pamiec, teraz)

    assert "old topic still fresh" in ledger
    assert ledger["old topic still fresh"]["peak_score"] == 6.0


def test_wb060_temat_wiek_24h_plus_wykluczony_z_wybierz_mse():
    """Temat wiek >= 24h -> wykluczony z kandydatow _wybierz_mse, niezaleznie od top_events."""
    teraz = "2026-07-12T08:00:00Z"
    ledger = {
        "old topic": {
            "detected_at": "2026-07-11T07:00:00Z",  # 25h temu
            "peak_score": 9.0,
            "peak_sentiment": "negative",
            "title": "Old topic",
        },
        "fresh topic": {
            "detected_at": "2026-07-12T00:00:00Z",  # 8h temu
            "peak_score": 3.0,
            "peak_sentiment": "neutral",
            "title": "Fresh topic",
        },
    }

    mse = silnik._wybierz_mse(ledger, teraz)

    assert mse["label"].lower().startswith("fresh topic")
    assert mse["score"] == 3.0


def test_wb060_wyzszy_peak_score_wygrywa_niezaleznie_od_pozycji_w_top_events():
    """Dwa tematy w oknie 24h -> wyzszy peak_score wygrywa (nie kolejnosc w ledgerze/top_events)."""
    teraz = "2026-07-12T08:00:00Z"
    ledger = {
        "topic a": {
            "detected_at": "2026-07-12T06:00:00Z",
            "peak_score": 4.0,
            "peak_sentiment": "neutral",
            "title": "Topic A",
        },
        "topic b": {
            "detected_at": "2026-07-12T02:00:00Z",
            "peak_score": 8.5,
            "peak_sentiment": "negative",
            "title": "Topic B",
        },
    }

    mse = silnik._wybierz_mse(ledger, teraz)

    assert mse["score"] == 8.5
    assert mse["label"].lower().startswith("topic b")


def test_wb060_remis_peak_score_starszy_detected_at_wygrywa():
    """Remis peak_score -> starszy (wczesniejszy) detected_at wygrywa."""
    teraz = "2026-07-12T08:00:00Z"
    ledger = {
        "topic newer": {
            "detected_at": "2026-07-12T05:00:00Z",
            "peak_score": 6.0,
            "peak_sentiment": "negative",
            "title": "Topic newer",
        },
        "topic older": {
            "detected_at": "2026-07-12T01:00:00Z",
            "peak_score": 6.0,
            "peak_sentiment": "negative",
            "title": "Topic older",
        },
    }

    mse = silnik._wybierz_mse(ledger, teraz)

    assert mse["label"].lower().startswith("topic older")
    assert mse["detected_at"] == "2026-07-12T01:00:00Z"


def test_wb060_ledger_pusty_i_top_events_puste_wybierz_mse_none():
    """Ledger pusty + top_events puste -> _wybierz_mse zwraca None."""
    assert silnik._wybierz_mse({}, "2026-07-12T08:00:00Z") is None
    assert silnik._wybierz_mse(None, "2026-07-12T08:00:00Z") is None


def test_wb060_migracja_starego_formatu_str_bez_wyjatku():
    """Migracja starego formatu WB-059 (str ISO) -> dict; nie wywala wyjatku, peak_score z biezacego eventu."""
    top = [{"title": "Legacy topic continues", "score": 5.5, "sentiment": "positive"}]
    pamiec = {"event_detected_at": {"legacy topic continues": "2026-07-11T10:00:00Z"}}

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "legacy topic continues"
    assert wynik[0]["detected_at"] == "2026-07-11T10:00:00Z"
    assert ledger[klucz]["peak_score"] == 5.5
    assert ledger[klucz]["detected_at"] == "2026-07-11T10:00:00Z"


def test_wb060_ledger_pusta_lista_top_events_bez_wyjatku():
    wynik, ledger = silnik._aktualizuj_ledger([], {"event_detected_at": {}}, "2026-07-12T08:01:27Z")
    assert wynik == []
    assert ledger == {}


def test_wb060_finalizuj_wynik_ustawia_detected_at_i_mutuje_pamiec():
    """Integracja: finalizuj_wynik() dopisuje detected_at i mutuje pamiec['event_detected_at']."""
    raw = {
        "global_score": 3.0,
        "top_events": [{"title": "Some fresh headline about a topic", "score": 3.0, "nowosc": "nowe"}],
    }
    pamiec = {"ostatnia_ocena": None, "event_detected_at": {}}

    wynik = silnik.finalizuj_wynik(raw, "pl", "Poland", pamiec, 10)

    assert wynik["top_events"][0]["detected_at"] == wynik["updated_at"]
    assert pamiec["event_detected_at"]


def test_wb060_finalizuj_wynik_kontynuacja_zachowuje_detected_at_z_pamieci():
    pamiec = {
        "ostatnia_ocena": 3.0,
        "event_detected_at": {
            "some fresh headline": {
                "detected_at": "2026-07-01T00:00:00Z",
                "peak_score": 3.0,
                "peak_sentiment": "neutral",
                "title": "Some fresh headline",
            },
        },
    }
    raw = {
        "global_score": 3.0,
        "top_events": [{"title": "Some fresh headline about a topic", "score": 3.0, "nowosc": "kontynuacja"}],
    }

    wynik = silnik.finalizuj_wynik(raw, "pl", "Poland", pamiec, 10)

    assert wynik["top_events"][0]["detected_at"] == "2026-07-01T00:00:00Z"


# ---------------------------------------------------------------------------
# WB-061: _waliduj_mse_label — walidacja etykiety LLM (budzet 2 linii)
# ---------------------------------------------------------------------------

def test_wb061_waliduj_label_poprawny_akceptowany_bez_zmian():
    """Poprawny label (8-14 slow, <=110 znakow, bez sredniku/meta) -> accepted=True, tekst bez zmian."""
    title = "Rebel forces attack government positions in north"
    label = "Government forces launch major offensive against rebel strongholds in the northern region"
    text, accepted = silnik._waliduj_mse_label(label, title)
    assert accepted is True
    assert text == label


def test_wb061_waliduj_label_srednik_odrzucony_fallback_bez_elipsy():
    """Srednik w labelu -> reject; fallback = _skrot_z_tytulu(title, 12, bez elipsy)."""
    title = "Central bank raises interest rates sharply amid inflation surge nationwide"
    text, accepted = silnik._waliduj_mse_label("Rates rise; markets react sharply", title)
    assert accepted is False
    assert text == silnik._skrot_z_tytulu(title, max_words=12, ellipsis=False)
    assert "…" not in text and "..." not in text


def test_wb061_waliduj_label_za_dlugi_slowami_odrzucony():
    """Label > 14 slow -> reject."""
    title = "Central bank raises interest rates sharply amid inflation surge nationwide"
    dlugi_label = " ".join(["word"] * 20)
    text, accepted = silnik._waliduj_mse_label(dlugi_label, title)
    assert accepted is False


def test_wb061_waliduj_label_za_dlugi_znakami_odrzucony():
    """Label > 110 znakow -> reject, mimo <=14 slow."""
    title = "Central bank raises interest rates sharply amid inflation surge nationwide"
    dlugi_label = " ".join(["a" * 15] * 8)  # 8 slow, ale > 110 znakow
    assert len(dlugi_label) > 110
    text, accepted = silnik._waliduj_mse_label(dlugi_label, title)
    assert accepted is False


def test_wb061_waliduj_label_meta_fraza_odrzucona():
    """Meta-fraza cyklu ciszy (blocklista) -> reject, niezaleznie od dlugosci."""
    title = "Central bank raises interest rates sharply amid inflation surge nationwide"
    text, accepted = silnik._waliduj_mse_label("Quiet period with no new shocks reported", title)
    assert accepted is False


def test_wb061_waliduj_label_puste_odrzucone():
    """Puste / brak label -> reject, bez wyjatku."""
    title = "Central bank raises interest rates sharply amid inflation surge nationwide"
    text, accepted = silnik._waliduj_mse_label("", title)
    assert accepted is False
    text2, accepted2 = silnik._waliduj_mse_label(None, title)
    assert accepted2 is False


def test_wb061_waliduj_label_strip_koncowej_elipsy_przed_walidacja():
    """Koncowa elipsa (…/...) jest zdejmowana przed walidacja — nie rstrip('.') (psuje 'U.S.')."""
    title = "Some headline about a topic"
    text, accepted = silnik._waliduj_mse_label("A reasonably short valid headline phrase here…", title)
    assert "…" not in text
    text2, accepted2 = silnik._waliduj_mse_label("A reasonably short valid headline phrase...", title)
    assert "..." not in text2


def test_wb061_skrot_z_tytulu_domyslnie_bez_elipsy():
    """WB-061: _skrot_z_tytulu domyslnie (ellipsis=False) nie dokleja wielokropka."""
    long_title = "Government forces launch major offensive against rebel strongholds across the entire northern border region today"
    text = silnik._skrot_z_tytulu(long_title)
    assert "…" not in text
    assert len(text.split()) <= 12


def test_wb061_skrot_z_tytulu_ellipsis_true_dokleja_wielokropek():
    """Z ellipsis=True (opt-in) wielokropek nadal dostepny gdy ktos tego potrzebuje."""
    long_title = "Government forces launch major offensive against rebel strongholds across the entire northern border region today"
    text = silnik._skrot_z_tytulu(long_title, max_words=5, ellipsis=True)
    assert text.endswith("…")


# ---------------------------------------------------------------------------
# WB-061: T1-T7 ze specyfikacji — sticky `peak_label` w ledgerze + _wybierz_mse
# ---------------------------------------------------------------------------

def test_wb061_t1_nowy_event_poprawny_label_ledger_i_mse():
    """T1: nowy event z poprawnym labelem (12 slow) -> peak_label w ledgerze = label; MSE.label = ten tekst."""
    label = "Government forces launch major offensive against rebel strongholds in the northern region"
    top = [{"title": "Rebel forces attack government positions in north", "score": 5.0,
            "sentiment": "negative", "label": label}]
    pamiec = {"event_detected_at": {}}

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-15T08:00:00Z")

    klucz = "rebel forces attack government positions in north"
    assert wynik[0]["label"] == label
    assert ledger[klucz]["peak_label"] == label

    mse = silnik._wybierz_mse(ledger, "2026-07-15T08:00:00Z")
    assert mse["label"] == label


def test_wb061_t2_label_niepoprawny_fallback_skrot_bez_elipsy():
    """T2: label ze srednikiem / 20 slow / meta -> fallback skrot; bez '…'."""
    title = "Massive earthquake strikes coastal region causing widespread damage overnight"
    top = [{"title": title, "score": 4.0, "sentiment": "negative",
            "label": "Earthquake hits; damage widespread across region"}]
    pamiec = {"event_detected_at": {}}

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-15T08:00:00Z")

    klucz = title.lower()
    oczekiwany_fallback = silnik._skrot_z_tytulu(title, max_words=12, ellipsis=False)
    assert wynik[0]["label"] == oczekiwany_fallback
    assert ledger[klucz]["peak_label"] == oczekiwany_fallback
    assert "…" not in oczekiwany_fallback and "..." not in oczekiwany_fallback


def test_wb061_t3_kontynuacja_score_dol_peak_label_niezmienione():
    """T3: kontynuacja, score w dol -> peak_label niezmienione mimo nowego (innego) ev.label."""
    sticky_label = "Iran imposes naval blockade escalating regional tensions across Gulf shipping lanes"
    pamiec = {
        "event_detected_at": {
            "naval blockade iranian ports": {
                "detected_at": "2026-07-10T00:00:00Z",
                "peak_score": 7.3,
                "peak_sentiment": "negative",
                "title": "Naval blockade of Iranian ports escalates",
                "peak_label": sticky_label,
            },
        },
    }
    top = [{"title": "Naval blockade of Iranian ports", "score": 4.5, "sentiment": "negative",
            "label": "Blockade situation continues with reduced tensions this week"}]

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "naval blockade of iranian ports"
    assert ledger[klucz]["peak_label"] == sticky_label
    assert ledger[klucz]["peak_score"] == 7.3


def test_wb061_t4_peak_bump_label_accepted_aktualizuje_peak_label():
    """T4: kontynuacja, score > peak, label accepted -> peak_label = nowy label."""
    new_label = "Iran expands naval blockade striking multiple tankers near Strait of Hormuz"
    pamiec = {
        "event_detected_at": {
            "naval blockade iranian ports": {
                "detected_at": "2026-07-10T00:00:00Z",
                "peak_score": 5.0,
                "peak_sentiment": "negative",
                "title": "Naval blockade of Iranian ports",
                "peak_label": "Iran imposes naval blockade of key Gulf ports amid tensions",
            },
        },
    }
    top = [{"title": "Naval blockade of Iranian ports escalates", "score": 7.3, "sentiment": "negative",
            "label": new_label}]

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "naval blockade of iranian ports escalates"
    assert ledger[klucz]["peak_label"] == new_label
    assert ledger[klucz]["peak_score"] == 7.3


def test_wb061_t4b_peak_bump_label_rejected_zachowuje_stary_peak_label():
    """T4b: peak bump, label rejected (';') gdy stary peak_label istnieje -> stary zachowany."""
    old_label = "Iran imposes naval blockade of key Gulf ports amid tensions"
    pamiec = {
        "event_detected_at": {
            "naval blockade iranian ports": {
                "detected_at": "2026-07-10T00:00:00Z",
                "peak_score": 5.0,
                "peak_sentiment": "negative",
                "title": "Naval blockade of Iranian ports",
                "peak_label": old_label,
            },
        },
    }
    top = [{"title": "Naval blockade of Iranian ports escalates", "score": 7.3, "sentiment": "negative",
            "label": "Blockade widens; tankers hit"}]

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "naval blockade of iranian ports escalates"
    assert ledger[klucz]["peak_label"] == old_label
    assert ledger[klucz]["peak_score"] == 7.3  # peak_score i tak podbity, tylko label sticky


def test_wb061_t5_champion_tylko_w_retencji_mse_label_sticky():
    """T5: champion tylko w retencji (poza biezacym top) -> MSE.label = sticky peak_label z ledgera."""
    sticky_label = "Old topic escalates dramatically affecting regional stability across border areas"
    ledger = {
        "old topic": {
            "detected_at": "2026-07-12T00:00:00Z",
            "peak_score": 8.0,
            "peak_sentiment": "negative",
            "title": "Old topic escalates",
            "peak_label": sticky_label,
        },
    }
    mse = silnik._wybierz_mse(ledger, "2026-07-12T08:00:00Z")
    assert mse["label"] == sticky_label


def test_wb061_t6_brak_peak_label_stary_ledger_fallback_skrot():
    """T6: brak peak_label (stary ledger WB-060) -> MSE.label = _skrot_z_tytulu 12 slow bez elipsy."""
    long_title = "Government forces launch major offensive against rebel strongholds across the entire northern border region today"
    ledger = {
        "topic": {
            "detected_at": "2026-07-12T00:00:00Z",
            "peak_score": 6.0,
            "peak_sentiment": "negative",
            "title": long_title,
            # brak "peak_label" — wpis z przed WB-061
        },
    }
    mse = silnik._wybierz_mse(ledger, "2026-07-12T08:00:00Z")
    assert mse["label"] == silnik._skrot_z_tytulu(long_title, max_words=12, ellipsis=False)
    assert "…" not in mse["label"]


def test_wb061_t7_wb060_fixtures_bez_peak_label_uzywaja_fallbacku():
    """T7: fixtures WB-060 bez `peak_label` -> _wybierz_mse zwraca fallback skrot tytulu (bez
    elipsy); asercje `label.lower().startswith(...)` w testach WB-060 pozostaja poprawne, bo
    tytuly uzyte tam sa krotsze niz 12 slow (skrot = caly tytul, bez zmian)."""
    ledger = {
        "fresh topic": {
            "detected_at": "2026-07-12T00:00:00Z",
            "peak_score": 3.0,
            "peak_sentiment": "neutral",
            "title": "Fresh topic",
        },
    }
    mse = silnik._wybierz_mse(ledger, "2026-07-12T08:00:00Z")
    assert mse["label"] == "Fresh topic"
    assert mse["label"].lower().startswith("fresh topic")


def test_wb061_ac7_skip_gate_nie_kasuje_peak_label():
    """AC-7: cykl bez AI (skip gate) — score identyczny jak peak, brak nowego label -> peak_label sticky."""
    old_label = "Iran imposes naval blockade of key Gulf ports amid rising regional tensions"
    pamiec = {
        "event_detected_at": {
            "naval blockade iranian ports": {
                "detected_at": "2026-07-10T00:00:00Z",
                "peak_score": 5.0,
                "peak_sentiment": "negative",
                "title": "Naval blockade of Iranian ports",
                "peak_label": old_label,
            },
        },
    }
    # skip-gate: ev bez "label" (rekonstrukcja z poprzedniego cyklu), score identyczny jak peak
    top = [{"title": "Naval blockade of Iranian ports", "score": 5.0, "sentiment": "negative",
            "nowosc": "kontynuacja"}]

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-12T08:01:27Z")

    klucz = "naval blockade of iranian ports"
    assert ledger[klucz]["peak_label"] == old_label
