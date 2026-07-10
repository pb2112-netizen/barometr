"""
Testy WB-050: deterministyczny straznik `nowosc` (Jaccard vs pamiec) + clamp skoku score.
Testy WB-051: walidacja short_summary (sredniki, dlugosc) + sanityzacja leadu RSS.

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

def _wynik_ss(title, short_summary, nowosc="nowe"):
    """Buduje minimalny wynik lensu do testow _ustaw_short_summary."""
    return {
        "top_events": [{"title": title, "nowosc": nowosc, "score": 5.0}],
        "short_summary": short_summary,
    }


def _pamiec_ss(sticky=""):
    return {"sticky_short_summary": sticky}


def test_wb051_srednik_w_short_summary_fallback():
    """Sklejka ze srednikiem → fallback z tytulu."""
    wynik = _wynik_ss("Cargo ships reroute Hormuz straits", "oil plunges; ships reroute Hormuz")
    po, _ = silnik._ustaw_short_summary(wynik, _pamiec_ss())
    assert ";" not in po["short_summary"]
    assert len(po["short_summary"].split()) <= 6


def test_wb051_7_slow_short_summary_fallback():
    """7 slow w short_summary → fallback z tytulu."""
    wynik = _wynik_ss("Iran closes Hormuz to tankers", "Iran closes strait tankers oil cargo ships blocked")
    po, _ = silnik._ustaw_short_summary(wynik, _pamiec_ss())
    assert len(po["short_summary"].split()) <= 6


def test_wb051_poprawne_4_slowa_bez_zmian():
    """Poprawne 4 slowa → short_summary bez zmian."""
    wynik = _wynik_ss("Iran seizes British tanker", "Iran seizes tanker")
    po, _ = silnik._ustaw_short_summary(wynik, _pamiec_ss())
    assert po["short_summary"] == "Iran seizes tanker"


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
