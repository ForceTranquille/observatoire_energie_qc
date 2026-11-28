import pandas as pd

import tp_collecte_hydroquebec as tp
from tests.conftest import FauxResponse

ALLOW = FauxResponse(200, "User-agent: *\nAllow: /\n")


def test_main_complet_hors_ligne(simuler_http, demande_json, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tp, "DOSSIER_SORTIE", tmp_path)
    appels = simuler_http({
        "https://www.hydroquebec.com/robots.txt": ALLOW,
        "https://donnees.hydroquebec.com/robots.txt": ALLOW,
        "https://pannes.hydroquebec.com/robots.txt": FauxResponse(403),
        tp.PAGE: FauxResponse(200, "<h2>Données</h2><a href='/x'>Jeu</a>"),
        tp.API + "/catalog/datasets": FauxResponse(200, json_data={
            "total_count": 1,
            "results": [{"dataset_id": "d1", "metas": {"default": {
                "title": "Jeu 1", "modified": "2026-11-01", "records_count": 10}}}]}),
        tp.API + "/catalog/datasets/" + tp.DATASET: FauxResponse(200, json_data={
            "fields": [{"name": "date", "type": "datetime", "label": "Date"},
                       {"name": "prod", "type": "double", "label": "Production"}]}),
        tp.API + "/catalog/datasets/" + tp.DATASET + "/records": FauxResponse(200, json_data={
            "total_count": 2,
            "results": [{"date": "2026-11-24T10:00:00+00:00", "prod": 100.5},
                        {"date": "2026-11-24T11:00:00+00:00", "prod": 101.0}]}),
        "https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/json/demande.json":
            FauxResponse(200, json_data=demande_json),
    })

    assert tp.main(["--sans-pause"]) == 0

    sortie = capsys.readouterr().out
    assert "[SAUTÉ] pannes_en_cours" in sortie                  # robots.txt 403 : jamais collecté
    assert not any("pannes.hydroquebec.com/pannes/donnees" in u for u in appels)
    for nom in ("page_donnees_ouvertes", "catalogue", "production_consommation_horaire", "demande_quebec"):
        assert (tmp_path / f"hq_{nom}.csv").exists(), nom
    assert not (tmp_path / "hq_pannes_en_cours.csv").exists()
    assert (tmp_path / "figures" / "demande_quebec.png").exists()
    assert len(pd.read_csv(tmp_path / "hq_demande_quebec.csv")) == 5
