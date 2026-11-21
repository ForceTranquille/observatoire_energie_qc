from abc import ABC, abstractmethod
from typing import List
from modele.evenement_energie import EvenementEnergie


class BaseCollecteur(ABC):
    """Classe abstraite definissant l'interface de collecte (POO)."""

    def __init__(self, nom_source: str):
        self._nom_source = nom_source

    @property
    def nom_source(self) -> str:
        return self._nom_source

    @abstractmethod
    def extraire(self) -> List[EvenementEnergie]:
        pass
