import logging
import random
import time
from typing import Callable, Dict, List, Optional, Tuple
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from collecte.base_collecteur import BaseCollecteur
from collecte.robots import url_autorisee
from modele.evenement_energie import EvenementEnergie

logger = logging.getLogger(__name__)


class WebScrapingCollecteur(BaseCollecteur):
    """Collecteur Web Scraping HTML conforme à robots.txt avec pauses aléatoires.

    - robots.txt est lu pour chaque hôte (une seule fois) et interprété selon
      son code HTTP : 200 -> règles lues, 401/403 -> tout refusé, autre 4xx ->
      tout permis, erreur réseau ou 5xx -> refus par prudence.
    - Entre deux requêtes successives, une pause aléatoire de 13 s, 15 s ou
      18 s est appliquée (exigence du TP : « scraping aléatoire »).
    - Les pages sont des instantanés : leur contenu change dans le temps, ces
      événements ne sont donc pas strictement idempotents d'une exécution à
      l'autre (contrairement aux sources fichier).
    """

    DELAIS_AUTORISES = (13, 15, 18)

    def __init__(
        self,
        nom_source: str,
        urls: List[str],
        region: str,
        user_agent: str = "ObservatoireEnergieQC-Bot/1.0 (+https://github.com/ForceTranquille)",
        timeout: int = 15,
        regions_par_url: Optional[Dict[str, str]] = None,
        sleeper: Callable[[float], None] = time.sleep,
        choisir_delai: Callable[[Tuple[int, ...]], int] = random.choice,
    ) -> None:
        super().__init__(nom_source)
        self._urls = urls
        self._region = region
        self._regions_par_url = regions_par_url or {}
        self._user_agent = user_agent
        self._timeout = timeout
        self._sleeper = sleeper
        self._choisir_delai = choisir_delai
        self._robots_cache: Dict[str, RobotFileParser] = {}
        self.delais_appliques: List[int] = []
        self.urls_refusees: List[str] = []

    # ---------- robots.txt ----------
    def _est_autorise_robots(self, url: str) -> bool:
        """Vérifie si l'URL est autorisée pour le User-Agent selon robots.txt."""
        return url_autorisee(url, self._user_agent, self._timeout, self._robots_cache)

    # ---------- pause aléatoire ----------
    def _attendre_delai_aleatoire(self, index: int) -> Optional[int]:
        """Pause aléatoire (13 s, 15 s ou 18 s) avant chaque requête successive."""
        if index == 0:
            return None
        delai = self._choisir_delai(self.DELAIS_AUTORISES)
        self._sleeper(delai)
        self.delais_appliques.append(delai)
        return delai

    # ---------- extraction ----------
    def extraire(self) -> List[EvenementEnergie]:
        """Récupère le contenu HTML des URLs autorisées et retourne des EvenementEnergie."""
        evenements: List[EvenementEnergie] = []
        self.delais_appliques = []
        self.urls_refusees = []
        headers = {
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8",
        }

        requete_faite = False
        for url in self._urls:
            if not self._est_autorise_robots(url):
                self.urls_refusees.append(url)
                logger.warning("Accès refusé par robots.txt : %s", url)
                continue

            delai_applique = self._attendre_delai_aleatoire(1 if requete_faite else 0)
            requete_faite = True

            reponse = requests.get(url, headers=headers, timeout=self._timeout)
            reponse.raise_for_status()

            soup = BeautifulSoup(reponse.text, "html.parser")
            titre = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else "Sans titre"
            )
            paragraphes = [
                p.get_text(" ", strip=True)
                for p in soup.find_all("p")
                if p.get_text(" ", strip=True)
            ]
            extrait = paragraphes[0][:200] if paragraphes else ""

            evenements.append(
                EvenementEnergie(
                    source=self.nom_source,
                    format_origine="HTML",
                    categorie="web_scraping",
                    donnees={
                        "region": self._regions_par_url.get(url, self._region),
                        "url_source": url,
                        "titre_page": titre,
                        "extrait_contenu": extrait,
                        "nb_paragraphes": len(paragraphes),
                        "delai_precedent_s": delai_applique if delai_applique is not None else 0,
                    },
                )
            )

        if not evenements and self.urls_refusees:
            raise PermissionError(
                "Accès refusé par robots.txt pour : " + ", ".join(self.urls_refusees)
            )
        return evenements
