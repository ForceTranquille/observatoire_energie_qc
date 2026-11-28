from pathlib import Path
from typing import Dict, List
import pandas as pd


class ExporteurEnergie:
    """Nettoie, déduplique et exporte les événements normalisés.

    Les catégories de CATEGORIES_HORS_GLOBAL ont leur propre fichier mais ne sont
    pas mêlées à `dataset_energie_normalise.csv`, qui reste le jeu régional
    (Montréal / Lanaudière) lu par le tableau de bord Power BI.
    """

    CATEGORIES_HORS_GLOBAL = ("demande_quebec",)

    def __init__(self, dossier_sortie: Path):
        self._dossier_sortie = Path(dossier_sortie)
        self._dossier_sortie.mkdir(parents=True, exist_ok=True)

    def exporter(self, evenements: List[dict]) -> Dict[str, Path]:
        if not evenements:
            return {}

        lignes: List[dict] = []
        for evt in evenements:
            ligne = {
                "event_id": evt.get("event_id"),
                "horodatage_utc": evt.get("horodatage_utc"),
                "source": evt.get("source"),
                "format_origine": evt.get("format_origine"),
                "categorie": evt.get("categorie"),
                **evt.get("donnees", {}),
            }
            lignes.append(ligne)

        df = pd.DataFrame(lignes)
        if "event_id" in df.columns and df["event_id"].notna().any():
            df = df.drop_duplicates(subset=["event_id"], keep="first")

        fichiers_generes: Dict[str, Path] = {}

        chemin_global = self._dossier_sortie / "dataset_energie_normalise.csv"
        df_global = df[~df["categorie"].isin(self.CATEGORIES_HORS_GLOBAL)]
        df_global.to_csv(chemin_global, index=False, encoding="utf-8")
        fichiers_generes["global"] = chemin_global

        if "categorie" in df.columns:
            for categorie, sous_df in df.groupby("categorie"):
                sous_df_propre = sous_df.dropna(axis=1, how="all")
                chemin_cat = self._dossier_sortie / f"{categorie}_propre.csv"
                sous_df_propre.to_csv(chemin_cat, index=False, encoding="utf-8")
                fichiers_generes[str(categorie)] = chemin_cat

        return fichiers_generes