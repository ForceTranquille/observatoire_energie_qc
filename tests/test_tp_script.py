import pandas as pd
import pytest

import tp_collecte_hydroquebec as tp
from tests.conftest import FauxResponse


def test_get_json_reessaie_sur_429_avec_attente_exponentielle(monkeypatch):
    reponses = iter([FauxResponse(429), FauxResponse(429), FauxResponse(200, json_data={"ok": 1})])
    attentes = []
    monkeypatch.setattr("requests.get", lambda url, *a, **k: next(reponses))
    assert tp.get_json("https://x.test/api", sleeper=attentes.append) == {"ok": 1}
    assert attentes == [1, 2]


def test_get_json_abandonne_apres_trois_429(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **k: FauxResponse(429))
    with pytest.raises(RuntimeError):
        tp.get_json("https://x.test/api", sleeper=lambda s: None)


def test_fetch_records_pagine_jusqu_au_total(monkeypatch):
    appels = []

    def faux_get(url, params=None, **k):
        appels.append(params["offset"])
        lot = [{"n": params["offset"] + i} for i in range(params["limit"])]
        return FauxResponse(200, json_data={"results": lot, "total_count": 250})
    monkeypatch.setattr("requests.get", faux_get)
    df = tp.fetch_records("jeu", max_rows=1000, sleeper=lambda s: None)
    assert appels == [0, 100, 200]          # s'arrête quand offset >= total_count
    assert len(df) == 300


def test_extraire_liens_par_section():
    html = ("<h2>Données</h2><a href='/a'>A</a><a href='/a'>A</a>"
            "<h3>Autres</h3><a href='https://autre.test/b'>B</a>")
    df = tp.extraire_liens(html, "https://hq.test/page/")
    assert list(df["section"]) == ["Données", "Autres"]      # doublon retiré
    assert list(df["url"]) == ["https://hq.test/a", "https://autre.test/b"]


def test_to_lonlat():
    assert tp.to_lonlat("[-73.5, 45.5]") == (-73.5, 45.5)
    assert tp.to_lonlat([1, 2, 3]) == (1, 2)
    assert tp.to_lonlat("pas du json") == (None, None)


def test_verifier_robots_signale_les_refus(simuler_http):
    simuler_http({"https://pannes.test/robots.txt": FauxResponse(403),
                  "https://donnees.test/robots.txt": FauxResponse(200, "User-agent: *\nAllow: /\n")})
    verdicts = tp.verifier_robots(["https://pannes.test/x.json", "https://donnees.test/api"])
    assert verdicts == {"https://pannes.test/x.json": False, "https://donnees.test/api": True}


def test_pause_aleatoire_choisit_parmi_13_15_18():
    attentes = []
    assert tp.pause_aleatoire(attentes.append, lambda delais: delais[2]) == 18
    assert attentes == [18]


def test_exporter_ignore_les_dataframes_vides(tmp_path):
    fichiers = tp.exporter(tmp_path, plein=pd.DataFrame({"a": [1]}), vide=pd.DataFrame())
    assert [f.name for f in fichiers] == ["hq_plein.csv"]
