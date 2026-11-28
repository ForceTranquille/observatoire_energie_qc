import json
from typing import List, Optional, Tuple

import requests

from collecte.base_collecteur import BaseCollecteur
from collecte.robots import url_autorisee
from modele.evenement_energie import EvenementEnergie

COLONNES = [
    "clients_touches", "debut", "fin_estimee", "type", "localisation",
    "statut_equipe", "inutilise", "code_cause", "id_municipalite", "id_message",
]


def vers_lon_lat(valeur) -> Tuple[Optional[float], Optional[float]]:
    if isinstance(valeur, str):
        try:
            valeur = json.loads(valeur)
        except ValueError:
            return (None, None)
    if isinstance(valeur, (list, tuple)) and len(valeur) >= 2:
        return (valeur[0], valeur[1])
    return (None, None)


class PannesHQCollecteur(BaseCollecteur):
    """Pannes en cours d'Hydro-Québec (JSON public de pannes.hydroquebec.com).

    Données réelles, pour tout le Québec : aucune région Montréal / Lanaudière
    n'est fournie (seulement un identifiant de municipalité et des coordonnées).
    Elles forment donc une catégorie distincte, `pannes_en_cours`, séparée des
    pannes d'exemple (`pannes`) que le tableau de bord Power BI filtre par région.
    """

    BASE = "https://pannes.hydroquebec.com/pannes/donnees/v3_0"
    USER_AGENT = "ObservatoireEnergieQC-Bot/1.0 (usage pedagogique, 420-C71-BB)"

    def __init__(self, nom_source: str, respecter_robots: bool = True, timeout: int = 20):
        super().__init__(nom_source)
        self._respecter_robots = respecter_robots
        self._timeout = timeout

    def extraire(self) -> List[EvenementEnergie]:
        url_version = f"{self.BASE}/bisversion.json"
        if self._respecter_robots and not url_autorisee(url_version, self.USER_AGENT, self._timeout):
            raise PermissionError(f"Accès refusé par robots.txt pour : {url_version}")

        entetes = {"User-Agent": self.USER_AGENT}
        try:
            rep_version = requests.get(url_version, timeout=self._timeout, headers=entetes)
            rep_version.raise_for_status()
            version = rep_version.text.strip().strip('"')
            rep = requests.get(f"{self.BASE}/bismarkers{version}.json", timeout=self._timeout, headers=entetes)
            rep.raise_for_status()
            pannes = rep.json()["pannes"]
        except (requests.RequestException, KeyError, ValueError) as exc:
            raise RuntimeError(f"Erreur collecte pannes HQ ({self._nom_source}): {exc}") from exc

        evenements: List[EvenementEnergie] = []
        for ligne in pannes:
            champs = dict(zip(COLONNES, ligne))
            lon, lat = vers_lon_lat(champs.get("localisation"))
            try:
                clients = int(champs.get("clients_touches"))
            except (TypeError, ValueError):
                clients = None
            evenements.append(
                EvenementEnergie(
                    source=self._nom_source,
                    format_origine="JSON",
                    categorie="pannes_en_cours",
                    donnees={
                        "region": "Quebec",
                        "id_panne": f"{champs.get('id_municipalite')}@{champs.get('debut')}",
                        "clients_touches": clients,
                        "debut": champs.get("debut"),
                        "fin_estimee": champs.get("fin_estimee"),
                        "code_cause": champs.get("code_cause"),
                        "statut_equipe": champs.get("statut_equipe"),
                        "id_municipalite": champs.get("id_municipalite"),
                        "lon": lon,
                        "lat": lat,
                    },
                )
            )
        return evenements
