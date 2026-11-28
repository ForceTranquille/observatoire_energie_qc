import pytest

from collecte.pannes_hq_collecteur import PannesHQCollecteur, vers_lon_lat
from tests.conftest import FauxResponse

BASE = PannesHQCollecteur.BASE
ROBOTS_OK = FauxResponse(200, "User-agent: *\nAllow: /\n")


def _routes(pannes):
    return {
        "https://pannes.hydroquebec.com/robots.txt": ROBOTS_OK,
        f"{BASE}/bisversion.json": FauxResponse(200, '"20261128"'),
        f"{BASE}/bismarkers20261128.json": FauxResponse(200, json_data={"pannes": pannes}),
    }


def test_pannes_reelles_deviennent_des_evenements(simuler_http):
    simuler_http(_routes([
        [489, "2026-11-28 01:00:00", "2026-11-28 05:15:00", "P", "[-73.5, 45.5]", "L", "", "8", "4395", "13"],
        [2, "2026-11-28 02:00:00", "2026-11-28 04:00:00", "P", "pas du json", "A", "", "7", "5001", "13"],
    ]))
    evts = PannesHQCollecteur("HQ_Pannes_Reelles").extraire()
    assert [e.categorie for e in evts] == ["pannes_en_cours"] * 2
    premier = evts[0].donnees
    assert premier["clients_touches"] == 489
    assert (premier["lon"], premier["lat"]) == (-73.5, 45.5)
    assert premier["region"] == "Quebec"
    assert evts[1].donnees["lon"] is None


def test_pannes_refusees_par_robots(simuler_http):
    simuler_http({"https://pannes.hydroquebec.com/robots.txt": FauxResponse(403)})
    with pytest.raises(PermissionError):
        PannesHQCollecteur("HQ_Pannes_Reelles").extraire()


def test_pannes_reponse_invalide(simuler_http):
    routes = _routes([])
    routes[f"{BASE}/bismarkers20261128.json"] = FauxResponse(200, json_data={"autre": 1})
    simuler_http(routes)
    with pytest.raises(RuntimeError):
        PannesHQCollecteur("HQ_Pannes_Reelles").extraire()


def test_vers_lon_lat():
    assert vers_lon_lat([1, 2, 3]) == (1, 2)
    assert vers_lon_lat("x") == (None, None)
