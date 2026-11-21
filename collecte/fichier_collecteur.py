from pathlib import Path
from typing import List
import json
import pandas as pd
from collecte.base_collecteur import BaseCollecteur
from modele.evenement_energie import EvenementEnergie


class CsvConsommationCollecteur(BaseCollecteur):
    """Collecteur CSV pour l'historique de consommation."""

    def __init__(self, nom_source: str, chemin_fichier: Path):
        super().__init__(nom_source)
        self._chemin_fichier = Path(chemin_fichier)

    def extraire(self) -> List[EvenementEnergie]:
        if not self._chemin_fichier.exists():
            raise FileNotFoundError(f"Fichier CSV introuvable : {self._chemin_fichier}")

        df = pd.read_csv(self._chemin_fichier)
        return [
            EvenementEnergie(
                source=self._nom_source,
                format_origine="CSV",
                categorie="consommation",
                donnees=ligne,
            )
            for ligne in df.to_dict(orient="records")
        ]


class JsonPanneCollecteur(BaseCollecteur):
    """Collecteur JSON pour les pannes reseau."""

    def __init__(self, nom_source: str, chemin_fichier: Path):
        super().__init__(nom_source)
        self._chemin_fichier = Path(chemin_fichier)

    def extraire(self) -> List[EvenementEnergie]:
        if not self._chemin_fichier.exists():
            raise FileNotFoundError(f"Fichier JSON introuvable : {self._chemin_fichier}")

        contenu = json.loads(self._chemin_fichier.read_text(encoding="utf-8"))
        enregistrements = contenu if isinstance(contenu, list) else [contenu]

        return [
            EvenementEnergie(
                source=self._nom_source,
                format_origine="JSON",
                categorie="pannes",
                donnees=item,
            )
            for item in enregistrements
        ]