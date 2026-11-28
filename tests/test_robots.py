import requests

from collecte.robots import charger_robots, url_autorisee
from tests.conftest import FauxResponse

UA = "TP-test/1.0"


def test_robots_200_applique_les_regles(simuler_http):
    simuler_http({"/robots.txt": FauxResponse(200, "User-agent: *\nDisallow: /prive/\n")})
    assert url_autorisee("https://exemple.test/public/page", UA) is True
    assert url_autorisee("https://exemple.test/prive/page", UA) is False


def test_robots_403_refuse_tout(simuler_http):
    simuler_http({"/robots.txt": FauxResponse(403)})
    rp, code = charger_robots("https://exemple.test", UA)
    assert code == 403
    assert rp.can_fetch(UA, "https://exemple.test/n-importe-quoi") is False


def test_robots_404_permet_tout(simuler_http):
    simuler_http({"/robots.txt": FauxResponse(404)})
    assert url_autorisee("https://exemple.test/page", UA) is True


def test_robots_5xx_et_reseau_refusent_par_prudence(simuler_http):
    simuler_http({"/robots.txt": FauxResponse(503)})
    assert url_autorisee("https://exemple.test/page", UA) is False
    simuler_http({"/robots.txt": requests.ConnectionError("réseau coupé")})
    assert url_autorisee("https://autre.test/page", UA) is False


def test_robots_lu_une_seule_fois_par_hote_avec_cache(simuler_http):
    appels = simuler_http({"/robots.txt": FauxResponse(200, "User-agent: *\nAllow: /\n")})
    cache = {}
    url_autorisee("https://exemple.test/a", UA, cache=cache)
    url_autorisee("https://exemple.test/b", UA, cache=cache)
    assert appels.count("https://exemple.test/robots.txt") == 1


def test_url_invalide_refusee():
    assert url_autorisee("pas-une-url", UA) is False
