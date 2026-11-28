import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


class FauxResponse:
    """Réponse HTTP simulée (aucun accès réseau dans les tests)."""

    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text if json_data is None else json.dumps(json_data)
        self._json = json_data

    def json(self):
        if self._json is None:
            return json.loads(self.text)
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def demande_json():
    return json.loads((FIXTURES / "demande_sample.json").read_text(encoding="utf-8"))


@pytest.fixture
def simuler_http(monkeypatch):
    """simuler_http({url_ou_suffixe: FauxResponse}) remplace requests.get ; journalise les appels."""
    appels = []

    def installer(routes):
        def faux_get(url, *args, **kwargs):
            appels.append(url)
            for cle, reponse in routes.items():
                if url == cle or url.endswith(cle):
                    if isinstance(reponse, Exception):
                        raise reponse
                    return reponse
            return FauxResponse(404)
        monkeypatch.setattr("requests.get", faux_get)
        return appels

    return installer
