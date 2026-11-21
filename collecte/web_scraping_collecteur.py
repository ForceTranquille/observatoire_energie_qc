import random
import time
from typing import List, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from collecte.base_collecteur import BaseCollecteur
from modele.evenement_energie import EvenementEnergie


class WebScrapingCollecteur(BaseCollecteur):
    """Collecteur Web Scraping HTML conforme à robots.txt avec pauses aléatoires."""

    DELAIS_AUTORISES = (13, 15, 18)

    def __init__(
        self,
        nom_source: str,
        urls: List[str],
        region: str,
        user_agent: str = "ObservatoireEnergieQC-Bot/1.0 (+https://github.com/ForceTranquille)",
        timeout: int = 15,
    ) -> None:
        super().__init__(nom_source)
        self._urls = urls
        self._region = region
        self._user_agent = user_agent
        self._timeout = timeout

    def _est_autorise_robots(self, url: str) -> bool:
        """Vérifie si l'URL est autorisée pour le User-Agent selon le fichier robots.txt."""
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)

        try:
            rp.read()
            return rp.can_fetch(self._user_agent, url)
        except Exception:
            return False

    def _attendre_delai_aleatoire(self, index: int) -> Optional[int]:
        """Applique une pause aléatoire (13 s, 15 s ou 18 s) entre les requêtes successives."""
        if index == 0:
            return None
        delai = random.choice(self.DELAIS_AUTORISES)
        time.sleep(delai)
        return delai

    def extraire(self) -> List[EvenementEnergie]:
        """Récupère le contenu HTML des URLs autorisées et retourne des EvenementEnergie."""
        evenements: List[EvenementEnergie] = []
        headers = {
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-CA,fr;q=0.9,en;q=0.8",
        }

        for index, url in enumerate(self._urls):
            if not self._est_autorise_robots(url):
                raise PermissionError(f"Accès refusé par robots.txt pour : {url}")

            delai_applique = self._attendre_delai_aleatoire(index)

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
                        "region": self._region,
                        "url_source": url,
                        "titre_page": titre,
                        "extrait_contenu": extrait,
                        "nb_paragraphes": len(paragraphes),
                        "delai_precedent_s": delai_applique if delai_applique is not None else 0,
                    },
                )
            )

        return evenements