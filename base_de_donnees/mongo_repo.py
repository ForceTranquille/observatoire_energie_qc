from typing import Dict, Any
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from config.settings import MONGO_URI, MONGO_DB


class MongoBrutRepository:
    """Archive les payloads bruts dans MongoDB avec déduplication sur event_id."""

    def __init__(self, uri: str = MONGO_URI, db_name: str = MONGO_DB):
        self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self._db = self._client[db_name]
        self._index_crees = set()

    def _assurer_index(self, collection_name: str) -> None:
        if collection_name not in self._index_crees:
            self._db[collection_name].create_index(
                [("event_id", ASCENDING)], unique=True, sparse=True
            )
            self._index_crees.add(collection_name)

    def inserer_evenement(self, evenement: Dict[str, Any]) -> bool:
        collection_name = f"brut_{evenement.get('categorie', 'general')}"
        self._assurer_index(collection_name)
        try:
            self._db[collection_name].insert_one(dict(evenement))
            return True
        except DuplicateKeyError:
            return False

    def fermer(self) -> None:
        self._client.close()