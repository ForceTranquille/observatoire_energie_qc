from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from .models import EnergyReading


class KafkaClientUnavailable(RuntimeError):
    pass


def _kafka_module():
    try:
        from kafka import KafkaConsumer, KafkaProducer
    except ImportError as exc:
        raise KafkaClientUnavailable(
            "Kafka support requires the 'all' optional dependencies"
        ) from exc
    return KafkaConsumer, KafkaProducer


class KafkaPublisher:
    def __init__(self, bootstrap_servers: str = "localhost:9092", topic: str = "energy-readings"):
        _, KafkaProducer = _kafka_module()
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    def publish(self, readings: Iterable[EnergyReading]) -> int:
        count = 0
        for reading in readings:
            self.producer.send(self.topic, reading.to_dict())
            count += 1
        self.producer.flush()
        return count

    def close(self) -> None:
        self.producer.close()


def consume_readings(
    *,
    bootstrap_servers: str = "localhost:9092",
    topic: str = "energy-readings",
    group_id: str = "energy-observatory",
    limit: int | None = None,
) -> list[EnergyReading]:
    KafkaConsumer, _ = _kafka_module()
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    readings: list[EnergyReading] = []
    try:
        for message in consumer:
            readings.append(EnergyReading.from_mapping(message.value))
            if limit is not None and len(readings) >= limit:
                break
    finally:
        consumer.close()
    return readings
