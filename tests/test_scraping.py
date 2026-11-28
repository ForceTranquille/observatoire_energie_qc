import pytest

from collecte.web_scraping_collecteur import WebScrapingCollecteur
from tests.conftest import FauxResponse

PAGE = "<html><head><title>Météo</title></head><body><p>Ensoleillé</p><p>Vent</p></body></html>"
URL_A = "https://meteo.test/a"
URL_B = "https://meteo.test/b"


def fabriquer(urls, pauses, **kw):
    return WebScrapingCollecteur(
        "Test", urls=urls, region="Montreal",
        sleeper=pauses.append, choisir_delai=lambda delais: 15, **kw,
    )


def test_pause_aleatoire_appliquee_entre_deux_requetes(simuler_http):
    simuler_http({"/robots.txt": FauxResponse(200, "User-agent: *\nAllow: /\n"),
                  URL_A: FauxResponse(200, PAGE), URL_B: FauxResponse(200, PAGE)})
    pauses = []
    evenements = fabriquer([URL_A, URL_B], pauses,
                           regions_par_url={URL_A: "Montreal", URL_B: "Lanaudiere"}).extraire()
    assert pauses == [15]                      # une seule pause : entre la 1re et la 2e URL
    assert [e.donnees["region"] for e in evenements] == ["Montreal", "Lanaudiere"]
    assert [e.donnees["delai_precedent_s"] for e in evenements] == [0, 15]
    assert evenements[0].donnees["nb_paragraphes"] == 2


def test_delais_possibles_sont_13_15_18():
    assert WebScrapingCollecteur.DELAIS_AUTORISES == (13, 15, 18)


def test_url_refusee_est_ignoree_mais_les_autres_sont_collectees(simuler_http):
    simuler_http({"/robots.txt": FauxResponse(200, "User-agent: *\nDisallow: /b\n"),
                  URL_A: FauxResponse(200, PAGE), URL_B: FauxResponse(200, PAGE)})
    collecteur = fabriquer([URL_A, URL_B], [])
    assert len(collecteur.extraire()) == 1
    assert collecteur.urls_refusees == [URL_B]


def test_tout_refuse_leve_permission_error(simuler_http):
    simuler_http({"/robots.txt": FauxResponse(403)})
    with pytest.raises(PermissionError):
        fabriquer([URL_A], []).extraire()
