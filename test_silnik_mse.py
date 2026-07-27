"""
Testy poprawek MSE z audytu 2026-07-27 (plan: WB/PLAN_NAPRAWCZY_MSE_2026-07-27.md).

WB-063: twarde dopasowanie tematow — koniec sklejania po jednym wspolnym slowie >= 4 znaki.
WB-064: MSE ma wlasna tresc (summary/title/peak_at w kontrakcie).
WB-065: budzet etykiety MSE na DWIE linie UI (slowa + znaki + szerokosc em).
WB-066: wygasanie peaku MSE, cap tla vs potwierdzony czyn, koniec deprecated utcnow().

Fixtury oznaczone "produkcyjne" to prawdziwe tytuly z pamiec_ua.json / pamiec_pl.json
(cykl 2026-07-16), na ktorych stara regula skleila rozne wydarzenia.

Uruchomienie:  pytest WB/barometr/test_silnik_mse.py -v
"""

import silnik


# ---------------------------------------------------------------------------
# WB-063: dopasowanie tematow
# ---------------------------------------------------------------------------
KOLIZJE_PRODUKCYJNE = [
    # (tytul A, tytul B, slowo ktore dawniej wystarczalo do sklejenia)
    ("Five arrested after Hong Kong police raid independent bookshop",
     "French MPs approve assisted dying law with strict rules after debate", "after"),
    ("Protests in Ukraine's cities against Zelensky's removal of defence minister",
     "Protests in Paris, Gaza for release of Hussam Abu Safia", "protests"),
    ("Iran targets military bases as US launches wave of strikes",
     "Palestinian homes sealed off by israeli military restrictions", "military"),
]

KONTYNUACJE_PRODUKCYJNE = [
    # (tytul biezacy, temat/tytul z pamieci) — to SA te same historie, musza sie laczyc
    ("Protests in Ukraine's cities against Zelensky's removal of defence minister",
     "Zelensky removes defense minister - Ukraine command crisis"),
    ("Chip giant TSMC pledges another $100bn to expand US production",
     "TSMC $100bn US expansion - tech supply chain shift"),
    ("Iran targets military bases as US launches wave of strikes",
     "US-Iran military escalation - Strait of Hormuz strikes"),
    ("Naval blockade of Iranian ports escalates",
     "Naval blockade of Iranian ports"),
]


def test_wb063_kolizje_produkcyjne_nie_sa_juz_dopasowywane():
    for a, b, slowo in KOLIZJE_PRODUKCYJNE:
        wspolne = silnik._wyrazniki_tekstu(a) & silnik._wyrazniki_tekstu(b)
        assert slowo in wspolne, f"fixtura nieaktualna: {slowo!r} nie jest juz wspolne"
        assert not silnik._tematy_pasuja(a, b), (
            f"nadal sklejone przez {slowo!r}: {a[:40]} / {b[:40]}")


def test_wb063_prawdziwe_kontynuacje_nadal_sie_lacza():
    """Prog nie moze byc tak ostry, zeby kontynuacje stawaly sie nowymi tematami (decay)."""
    for biezacy, w_pamieci in KONTYNUACJE_PRODUKCYJNE:
        assert silnik._tematy_pasuja(biezacy, w_pamieci), f"zgubiona kontynuacja: {biezacy[:50]}"


def test_wb063_stopwords_nie_niosa_tematu():
    assert not silnik._tematy_pasuja("Flood warnings after heavy rain",
                                     "Election result after recount")
    assert silnik._wyrazniki_tematu("Flood warnings after heavy rain") == {
        "flood", "warnings", "heavy", "rain"}


def test_wb063_krotki_tytul_ratowany_przez_jaccard():
    """Przy krotkich tytulach 1 wspolne slowo z 2-3 to mocny sygnal (Jaccard >= 0.30)."""
    assert silnik._tematy_pasuja("Hormuz blockade", "Hormuz crisis")


def test_wb063_obcy_event_nie_dziedziczy_cudzego_wpisu_ledgera():
    """Regresja end-to-end z audytu: slaby paryski protest przejmowal wpis ukrainski."""
    pamiec = {"event_detected_at": {
        "protests in ukraine's cities against zelensky's removal of defence minister": {
            "detected_at": "2026-07-15T04:00:00Z",
            "peak_at": "2026-07-15T04:00:00Z",
            "peak_score": 7.9,
            "peak_sentiment": "negative",
            "title": "Protests in Ukraine's cities against Zelensky's removal of defence minister",
            "peak_label": "Mass protests over Ukraine defence minister sacking",
            "peak_summary": "Kyiv protests deepen Ukraine command crisis.",
        },
    }}
    top = [{
        "title": "Protests in Paris, Gaza for release of Hussam Abu Safia",
        "score": 1.8,
        "sentiment": "neutral",
        "label": "Paris rallies demand release of detained doctor",
        "summary": "Solidarity rallies in Paris and Gaza.",
    }]

    wynik, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-15T21:00:00Z")

    klucz = "protests in paris, gaza for release of hussam abu safia"
    assert wynik[0]["detected_at"] == "2026-07-15T21:00:00Z"   # wlasny czas, nie ukrainski
    assert ledger[klucz]["peak_score"] == 1.8                   # wlasny score, nie 7.9
    assert ledger[klucz]["peak_label"] == "Paris rallies demand release of detained doctor"
    # wpis zrodlowy przetrwal osobno (retencja < 24h), nie zostal przeklejony
    assert any("ukraine" in k for k in ledger), "wpis zrodlowy zniknal z ledgera"


def test_wb063_wpis_ledgera_zuzywalny_tylko_raz_na_cykl():
    """Dwa rozne eventy nie moga odziedziczyc tego samego peak_score/detected_at."""
    pamiec = {"event_detected_at": {
        "us launches wave of strikes on iranian military bases": {
            "detected_at": "2026-07-14T18:00:00Z",
            "peak_at": "2026-07-15T20:00:00Z",
            "peak_score": 6.0,
            "peak_sentiment": "negative",
            "title": "US launches wave of strikes on Iranian military bases",
            "peak_label": "US strikes Iranian military bases overnight",
        },
    }}
    top = [
        {"title": "US launches new wave of strikes on Iranian bases", "score": 5.0,
         "sentiment": "negative", "label": "US strikes more Iranian bases overnight"},
        {"title": "US military strikes drug boats off Venezuela coast", "score": 4.0,
         "sentiment": "negative", "label": "US strikes alleged drug boats near Venezuela"},
    ]

    _, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-15T21:00:00Z")

    dziedzicza = [w for w in ledger.values() if w.get("detected_at") == "2026-07-14T18:00:00Z"]
    assert len(dziedzicza) == 1, "wpis ledgera odziedziczony przez wiecej niz jeden event"


def test_wb063_wybierane_jest_najlepsze_dopasowanie_nie_pierwsze():
    """Kolejnosc w dict nie moze decydowac, ktory temat przejmie historie."""
    pamiec = {"event_detected_at": {
        "naval convoy escorts grain ships through corridor": {
            "detected_at": "2026-07-01T00:00:00Z", "peak_at": "2026-07-15T20:00:00Z",
            "peak_score": 9.0, "peak_sentiment": "negative",
            "title": "Naval convoy escorts grain ships through corridor",
            "peak_label": "Slaby kandydat",
        },
        "naval blockade of iranian ports": {
            "detected_at": "2026-07-10T00:00:00Z", "peak_at": "2026-07-15T20:00:00Z",
            "peak_score": 5.0, "peak_sentiment": "negative",
            "title": "Naval blockade of Iranian ports",
            "peak_label": "Wlasciwy kandydat",
        },
    }}
    top = [{"title": "Naval blockade of Iranian ports escalates", "score": 4.0,
            "sentiment": "negative", "label": "Iran tightens naval blockade of its ports"}]

    _, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-15T21:00:00Z")

    wpis = ledger["naval blockade of iranian ports escalates"]
    assert wpis["detected_at"] == "2026-07-10T00:00:00Z"
    assert wpis["peak_label"] == "Wlasciwy kandydat"


def test_wb063_rationale_o_innym_wydarzeniu_nie_trafia_do_summary():
    """`_rationale_matches_title` na tym samym progu — koniec wklejania cudzego opisu."""
    rationale = "Kyiv protests over defence minister dismissal escalate Ukraine command crisis."
    events = [{"title": "Chip giant TSMC pledges another $100bn to expand US production",
               "score": 2.8, "summary": ""}]

    wynik = silnik._ensure_event_summaries(events, "pl", "Poland", rationale)

    assert "Kyiv" not in wynik[0]["summary"]


# ---------------------------------------------------------------------------
# WB-064: MSE ma wlasna tresc
# ---------------------------------------------------------------------------
def test_wb064_mse_publikuje_wlasne_summary_title_i_peak_at():
    top = [{"title": "Naval blockade of Iranian ports escalates", "score": 7.3,
            "sentiment": "negative", "label": "Iran tightens naval blockade of its ports",
            "summary": "Blockade lifts EU energy prices and raises shipping costs for Poland."}]

    _, ledger = silnik._aktualizuj_ledger(top, {"event_detected_at": {}}, "2026-07-15T08:00:00Z")
    mse = silnik._wybierz_mse(ledger, "2026-07-15T08:00:00Z")

    assert mse["title"] == "Naval blockade of Iranian ports escalates"
    assert mse["summary"].startswith("Blockade lifts EU energy prices")
    assert mse["peak_at"] == "2026-07-15T08:00:00Z"


def test_wb064_peak_summary_sticky_jak_peak_label():
    """Champion spoza top-3 pokazuje SWOJ opis, nie opis biezacego dominanta."""
    pamiec = {"event_detected_at": {
        "naval blockade of iranian ports": {
            "detected_at": "2026-07-15T00:00:00Z", "peak_at": "2026-07-15T06:00:00Z",
            "peak_score": 7.3, "peak_sentiment": "negative",
            "title": "Naval blockade of Iranian ports",
            "peak_label": "Iran tightens naval blockade of its ports",
            "peak_summary": "Blockade lifts EU energy prices.",
        },
    }}
    # inny, slabszy temat w top_events tego cyklu
    top = [{"title": "Regional election result confirmed in Bavaria", "score": 2.0,
            "sentiment": "neutral", "label": "Bavaria confirms regional election result",
            "summary": "Routine regional vote with no cross-border effect."}]

    _, ledger = silnik._aktualizuj_ledger(top, pamiec, "2026-07-15T08:00:00Z")
    mse = silnik._wybierz_mse(ledger, "2026-07-15T08:00:00Z")

    assert mse["label"] == "Iran tightens naval blockade of its ports"
    assert mse["summary"] == "Blockade lifts EU energy prices."


def test_wb064_peak_summary_przycinany_do_preferowanego_limitu():
    top = [{"title": "Some headline about a long summary", "score": 5.0, "sentiment": "neutral",
            "label": "Headline about a very long summary", "summary": "A" * 400}]

    _, ledger = silnik._aktualizuj_ledger(top, {"event_detected_at": {}}, "2026-07-15T08:00:00Z")

    peak_summary = ledger["some headline about a long summary"]["peak_summary"]
    assert len(peak_summary) <= silnik.PREFERRED_EVENT_SUMMARY + 1


def test_wb064_brak_summary_nie_wywala_mse():
    """Stary ledger bez peak_summary -> MSE z pustym summary, bez wyjatku."""
    pamiec = {"event_detected_at": {
        "old entry without summary": {
            "detected_at": "2026-07-15T00:00:00Z", "peak_at": "2026-07-15T06:00:00Z",
            "peak_score": 5.0, "peak_sentiment": "negative",
            "title": "Old entry without summary", "peak_label": "Old entry without summary",
        },
    }}
    mse = silnik._wybierz_mse(pamiec["event_detected_at"], "2026-07-15T08:00:00Z")
    assert mse["summary"] == ""
    assert mse["title"] == "Old entry without summary"


# ---------------------------------------------------------------------------
# WB-065: budzet etykiety na DWIE linie UI
# ---------------------------------------------------------------------------
def test_wb065_etykieta_z_produkcji_ponad_budzetem_odrzucona():
    """Realne etykiety z produkcji 2026-07-16 (65-82 znaki) lamia nowy budzet."""
    za_dlugie = [
        "TSMC commits additional $100 billion to expand US chip production",
        "Hundreds protest in Kyiv over Zelensky's dismissal of defense minister",
        "Zelensky dismisses Ukraine defense minister without explanation, sparking protests",
    ]
    for label in za_dlugie:
        _, accepted = silnik._waliduj_mse_label(label, "Some fallback headline here")
        assert accepted is False, f"przeszlo mimo {len(label)} znakow: {label}"


def test_wb065_etykieta_w_budzecie_akceptowana():
    for label in ["Iran tightens naval blockade of its ports",
                  "Kyiv protests over defence minister sacking",
                  "TSMC adds $100bn to US chip plants"]:
        text, accepted = silnik._waliduj_mse_label(label, "Some fallback headline here")
        assert accepted is True, f"odrzucone mimo {len(label)} znakow: {label}"
        assert text == label


def test_wb065_szerokosc_em_odroznia_waskie_od_szerokich_znakow():
    waskie = "i" * 40
    szerokie = "W" * 40
    assert silnik._szerokosc_em(waskie) < silnik._szerokosc_em(szerokie)
    assert silnik._szerokosc_em(waskie) <= silnik.MSE_LABEL_MAX_EM
    assert silnik._szerokosc_em(szerokie) > silnik.MSE_LABEL_MAX_EM


def test_wb065_fallback_ze_skrotu_tez_miesci_sie_w_budzecie():
    """Fallback nie moze byc szerszy niz etykieta, ktora odrzucil — inaczej '...' wraca."""
    dlugie_tytuly = [
        "Zelensky dismisses Ukraine defense minister without explanation as protests spread",
        "WWWWWWWW WWWWWWWW WWWWWWWW WWWWWWWW WWWWWWWW WWWWWWWW",
        "More than 800 Canadian wildfires burning as air quality alerts extend to US cities",
    ]
    for title in dlugie_tytuly:
        skrot = silnik._skrot_z_tytulu(title)
        assert silnik._miesci_sie_w_budzecie(skrot), f"fallback poza budzetem: {skrot}"
        assert "…" not in skrot and "..." not in skrot


def test_wb065_zaden_publikowany_label_nie_ma_elipsy():
    top = [{"title": "A very long headline that will certainly not fit the two line budget",
            "score": 5.0, "sentiment": "neutral",
            "label": "An equally long label from the model that blows the two line budget"}]

    wynik, ledger = silnik._aktualizuj_ledger(top, {"event_detected_at": {}}, "2026-07-15T08:00:00Z")
    mse = silnik._wybierz_mse(ledger, "2026-07-15T08:00:00Z")

    for tekst in (wynik[0]["label"], mse["label"]):
        assert "…" not in tekst and not tekst.endswith("...")
        assert silnik._miesci_sie_w_budzecie(tekst)


# ---------------------------------------------------------------------------
# WB-066: cap tla nie dusi potwierdzonego czynu
# ---------------------------------------------------------------------------
def test_wb066_nowy_potwierdzony_czyn_przebija_cap_tla():
    wynik = {
        "global_score": 8.0,
        "rationale": "",
        "top_events": [{"title": "Alliance signed defence treaty with neighbouring state",
                        "nowosc": "nowe", "score": 8.0, "sentiment": "negative"}],
        "stan_swiata": [{"temat": "Old background topic", "poziom_bazowy": 3.0,
                         "cykle_bez_zmian": 5, "opis": "tlo"}],
    }
    po = silnik._zastosuj_decay_lens(wynik, {"stan_swiata": [], "ostatnia_ocena": 3.0})
    assert po["global_score"] == 8.0


def test_wb066_sama_retoryka_nie_przebija_capu_tla():
    """WB-018 zostaje: slowa bez czynu nie winduja score ponad tlo."""
    wynik = {
        "global_score": 8.0,
        "rationale": "",
        "top_events": [{"title": "Leader warns of possible response to alliance moves",
                        "nowosc": "nowe", "score": 8.0, "sentiment": "negative"}],
        "stan_swiata": [{"temat": "Old background topic", "poziom_bazowy": 3.0,
                         "cykle_bez_zmian": 5, "opis": "tlo"}],
    }
    po = silnik._zastosuj_decay_lens(wynik, {"stan_swiata": [], "ostatnia_ocena": 3.0})
    assert po["global_score"] <= 3.0


# ---------------------------------------------------------------------------
# WB-066: znacznik czasu bez deprecated utcnow()
# ---------------------------------------------------------------------------
def test_wb066_teraz_iso_ma_format_kontraktu():
    ts = silnik._teraz_iso()
    assert ts.endswith("Z") and "+00:00" not in ts
    silnik._parse_iso_utc(ts)  # nie moze rzucic
