import pandas as pd

from io_fichiers.export_ia import ExporteurEnergie
from modele.evenement_energie import EvenementEnergie


def evt(categorie, region, **donnees):
    return EvenementEnergie("S", "JSON", categorie, {"region": region, **donnees})


def test_event_id_deterministe_et_sensible_aux_donnees():
    a = evt("pannes", "Montreal", clients=85)
    assert a.event_id == evt("pannes", "Montreal", clients=85).event_id
    assert a.event_id != evt("pannes", "Montreal", clients=86).event_id


def test_export_garde_demande_quebec_hors_du_fichier_global(tmp_path):
    evenements = [
        evt("consommation", "Montreal", demande_mw=15000.0).__dict__,
        evt("demande_quebec", "Quebec", date="2026-11-24T21:00:00", demande_mw=26291.0).__dict__,
    ]
    fichiers = ExporteurEnergie(tmp_path).exporter(evenements)
    global_df = pd.read_csv(fichiers["global"])
    assert list(global_df["region"]) == ["Montreal"]       # compatible tableau de bord Power BI
    assert list(pd.read_csv(fichiers["demande_quebec"])["region"]) == ["Quebec"]


def test_export_deduplique_sur_event_id(tmp_path):
    e = evt("pannes", "Montreal", clients=85).__dict__
    fichiers = ExporteurEnergie(tmp_path).exporter([e, e])
    assert len(pd.read_csv(fichiers["global"])) == 1
