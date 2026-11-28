import pytest

from collecte.demande_hq_collecteur import DemandeHQCollecteur
from tests.conftest import FauxResponse

URL = DemandeHQCollecteur.URL
ROBOTS_OK = FauxResponse(200, "User-agent: *\nAllow: /\n")


def test_ignore_les_creneaux_futurs_vides(simuler_http, demande_json):
    simuler_http({"/robots.txt": ROBOTS_OK, URL: FauxResponse(200, json_data=demande_json)})
    evenements = DemandeHQCollecteur("HQ").extraire()
    assert len(evenements) == 5            # 7 créneaux dont 2 vides
    assert {e.categorie for e in evenements} == {"demande_quebec"}
    assert {e.donnees["region"] for e in evenements} == {"Quebec"}
    assert evenements[-1].donnees == {"region": "Quebec", "date": "2026-11-24T21:00:00",
                                      "demande_mw": 26291.0}


def test_relance_donne_les_memes_event_id(simuler_http, demande_json):
    simuler_http({"/robots.txt": ROBOTS_OK, URL: FauxResponse(200, json_data=demande_json)})
    premiere = [e.event_id for e in DemandeHQCollecteur("HQ").extraire()]
    seconde = [e.event_id for e in DemandeHQCollecteur("HQ").extraire()]
    assert premiere == seconde and len(set(premiere)) == len(premiere)


def test_robots_refuse_bloque_la_collecte(simuler_http, demande_json):
    appels = simuler_http({"/robots.txt": FauxResponse(403),
                           URL: FauxResponse(200, json_data=demande_json)})
    with pytest.raises(PermissionError):
        DemandeHQCollecteur("HQ").extraire()
    assert URL not in appels               # le JSON n'est jamais demandé


def test_robots_ignorable_explicitement(simuler_http, demande_json):
    simuler_http({"/robots.txt": FauxResponse(403), URL: FauxResponse(200, json_data=demande_json)})
    assert len(DemandeHQCollecteur("HQ", respecter_robots=False).extraire()) == 5


def test_json_invalide_leve_runtime_error(simuler_http):
    simuler_http({"/robots.txt": ROBOTS_OK, URL: FauxResponse(200, json_data={"pas": "details"})})
    with pytest.raises(RuntimeError):
        DemandeHQCollecteur("HQ").extraire()
