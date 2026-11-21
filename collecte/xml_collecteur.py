from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET
from collecte.base_collecteur import BaseCollecteur
from modele.evenement_energie import EvenementEnergie


class XmlAlerteCollecteur(BaseCollecteur):
    """Collecteur pour les fichiers XML d'alertes."""

    def __init__(self, nom_source: str, chemin_fichier: Path):
        super().__init__(nom_source)
        self._chemin_fichier = Path(chemin_fichier)

    def extraire(self) -> List[EvenementEnergie]:
        if not self._chemin_fichier.exists():
            raise FileNotFoundError(f"Fichier XML introuvable : {self._chemin_fichier}")

        racine = ET.parse(self._chemin_fichier).getroot()
        evenements: List[EvenementEnergie] = []

        for elem in racine.findall("alerte"):
            evenements.append(
                EvenementEnergie(
                    source=self._nom_source,
                    format_origine="XML",
                    categorie="alerte",
                    donnees={
                        "id_alerte": elem.attrib.get("id", ""),
                        "region": elem.findtext("region", default="Inconnue").strip(),
                        "type_alerte": elem.findtext("type", default="Inconnu").strip(),
                        "severite": elem.findtext("severite", default="Inconnue").strip(),
                    },
                )
            )
        return evenements