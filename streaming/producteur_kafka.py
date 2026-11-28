from typing import Iterable, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from kafka.serializer import Serializer
from config.settings import KAFKA_SERVERS, TOPICS
from modele.evenement_energie import EvenementEnergie


class _Utf8TextSerializer(Serializer):
    """Sérialiseur UTF-8 conforme à l'interface Serializer de kafka-python-ng."""

    def serialize(self, topic: str, value: Optional[str]) -> Optional[bytes]:
        if value is None:
            return None
        return value.encode("utf-8")


class ProducteurEnergieKafka:
    """Publie chaque EvenementEnergie vers le topic Kafka associé."""

    def __init__(self, bootstrap_servers: str = KAFKA_SERVERS):
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=_Utf8TextSerializer(),
            key_serializer=_Utf8TextSerializer(),
            acks="all",
            retries=3,
        )

    def _topic_pour_categorie(self, categorie: str) -> str:
        mapping = {
            "meteo": TOPICS["meteo"],
            "consommation": TOPICS["consommation"],
            "demande_quebec": TOPICS["demande_quebec"],
            "pannes": TOPICS["pannes"],
            "alerte": TOPICS["alertes"],
        }
        return mapping.get(categorie, TOPICS["meteo"])

    def publier_evenements(self, evenements: Iterable[EvenementEnergie]) -> int:
        compteur = 0
        for evt in evenements:
            topic = self._topic_pour_categorie(evt.categorie)
            cle = str(evt.donnees.get("region", evt.categorie))
            try:
                futur = self._producer.send(topic, key=cle, value=evt.to_json())
                futur.get(timeout=10)
                compteur += 1
            except KafkaError as exc:
                raise RuntimeError(f"Échec publication Kafka ({topic}): {exc}") from exc
        self._producer.flush()
        return compteur

    def fermer(self) -> None:
        self._producer.flush()
        self._producer.close()