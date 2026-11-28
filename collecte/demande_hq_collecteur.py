from typing import List

import requests

from collecte.base_collecteur import BaseCollecteur
from collecte.robots import url_autorisee
from modele.evenement_energie import EvenementEnergie


class DemandeHQCollecteur(BaseCollecteur):
    """Demande électrique du Québec : données ouvertes d'Hydro-Québec (pas de 15 min).

    Le fichier est une fenêtre glissante d'environ 2 jours : une série utile se
    construit en relançant le pipeline (la déduplication SHA-256 sur la date et
    la valeur évite les doublons). Les créneaux futurs, sans mesure, sont ignorés.
    La demande est celle de tout le Québec : région « Quebec », catégorie
    distincte (`demande_quebec`) pour ne pas se mélanger aux régions
    Montréal / Lanaudière.
    """

    URL = "https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/json/demande.json"
    USER_AGENT = "ObservatoireEnergieQC-Bot/1.0 (usage pedagogique, 420-C71-BB)"

    def __init__(self, nom_source: str, respecter_robots: bool = True, timeout: int = 15):
        super().__init__(nom_source)
        self._respecter_robots = respecter_robots
        self._timeout = timeout

    def extraire(self) -> List[EvenementEnergie]:
        if self._respecter_robots and not url_autorisee(self.URL, self.USER_AGENT, self._timeout):
            raise PermissionError(f"Accès refusé par robots.txt pour : {self.URL}")

        try:
            reponse = requests.get(
                self.URL, timeout=self._timeout, headers={"User-Agent": self.USER_AGENT}
            )
            reponse.raise_for_status()
            details = reponse.json()["details"]
        except (requests.RequestException, KeyError, ValueError) as exc:
            raise RuntimeError(f"Erreur collecte demande HQ ({self._nom_source}): {exc}") from exc

        evenements: List[EvenementEnergie] = []
        for detail in details:
            valeur = detail.get("valeurs", {}).get("demandeTotal")
            if valeur is None:
                continue  # créneau futur sans mesure
            evenements.append(
                EvenementEnergie(
                    source=self._nom_source,
                    format_origine="JSON",
                    categorie="demande_quebec",
                    donnees={
                        "region": "Quebec",
                        "date": detail["date"],
                        "demande_mw": valeur,
                    },
                )
            )
        return evenements
