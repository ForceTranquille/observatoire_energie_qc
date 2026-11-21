import json
from typing import Callable, List
from kafka import KafkaConsumer
from kafka.structs import TopicPartition
from config.settings import KAFKA_SERVERS


class ConsommateurEnergieKafka:
    """Lit les messages des topics Kafka sans coordination de groupe (compatible Python 3.15 / Windows)."""

    def __init__(
        self,
        topics: List[str],
        bootstrap_servers: str = KAFKA_SERVERS,
    ):
        self._topics = topics
        self._consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            consumer_timeout_ms=5000,
        )
        self._assigner_partitions()

    def _assigner_partitions(self) -> None:
        partitions: List[TopicPartition] = []
        for topic in self._topics:
            partition_ids = self._consumer.partitions_for_topic(topic) or {0}
            for pid in partition_ids:
                partitions.append(TopicPartition(topic, pid))
        if partitions:
            self._consumer.assign(partitions)
            self._consumer.seek_to_beginning(*partitions)

    def consommer_lot(self, callback: Callable[[dict], None]) -> int:
        traites = 0
        for message in self._consumer:
            callback(message.value)
            traites += 1
        return traites

    def fermer(self) -> None:
        try:
            self._consumer.close(autocommit=False)
        except Exception:
            pass