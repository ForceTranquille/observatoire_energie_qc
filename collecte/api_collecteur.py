from typing import List
import requests
from collecte.base_collecteur import BaseCollecteur
from modele.evenement_energie import EvenementEnergie


class ApiMeteoCollecteur(BaseCollecteur):
    """Collecteur API REST Open-Meteo pour une region du Quebec."""

    URL_API = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, nom_source: str, latitude: float, longitude: float, region: str):
        super().__init__(nom_source)
        self._latitude = latitude
        self._longitude = longitude
        self._region = region

    def extraire(self) -> List[EvenementEnergie]:
        params = {
            "latitude": self._latitude,
            "longitude": self._longitude,
            "current": "temperature_2m,wind_speed_10m,precipitation",
            "timezone": "America/Toronto",
        }
        try:
            response = requests.get(self.URL_API, params=params, timeout=10)
            response.raise_for_status()
            payload = response.json().get("current", {})

            return [
                EvenementEnergie(
                    source=self._nom_source,
                    format_origine="API",
                    categorie="meteo",
                    donnees={
                        "region": self._region,
                        "temperature_c": payload.get("temperature_2m"),
                        "vent_kmh": payload.get("wind_speed_10m"),
                        "precipitations_mm": payload.get("precipitation"),
                        "horodatage_source": payload.get("time"),
                    },
                )
            ]
        except requests.RequestException as exc:
            raise RuntimeError(f"Erreur collecte API ({self._nom_source}): {exc}") from exc