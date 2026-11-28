import pandas as pd

from analyse.analyse_energie import AnalyseurEnergie


def test_graphique_demande_quebec_genere(tmp_path):
    df = pd.DataFrame({"date": ["2026-11-24T20:45:00", "2026-11-24T21:00:00", "2026-11-24T21:00:00"],
                       "demande_mw": [26463.0, 26291.0, 26291.0]})
    analyseur = AnalyseurEnergie(tmp_path, tmp_path / "figures")
    figures = analyseur.generer_graphiques({"demande_quebec": df})
    assert figures["demande_quebec"].exists()


def test_charge_demande_quebec_depuis_csv(tmp_path):
    pd.DataFrame({"date": ["2026-11-24T21:00:00"], "demande_mw": [1.0]}).to_csv(
        tmp_path / "demande_quebec_propre.csv", index=False)
    assert "demande_quebec" in AnalyseurEnergie(tmp_path, tmp_path / "f").charger_datasets()


def test_demande_quebec_ne_pollue_pas_la_comparaison_regionale(tmp_path):
    conso = pd.DataFrame({"region": ["Montreal"], "demande_mw": [15000.0]})
    meteo = pd.DataFrame({"region": ["Montreal"], "temperature_c": [8.0]})
    qc = pd.DataFrame({"region": ["Quebec"], "date": ["2026-11-24T21:00:00"], "demande_mw": [26291.0]})
    croise = AnalyseurEnergie(tmp_path, tmp_path / "f").croiser_conso_meteo(
        {"consommation": conso, "meteo": meteo, "demande_quebec": qc}, sauvegarder_csv=False)
    assert list(croise["region"]) == ["Montreal"]
