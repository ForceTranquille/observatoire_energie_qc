from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import EnergyReading


class MongoPersistence:
    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        database: str = "energy_observatory",
        collection: str = "raw_readings",
    ) -> None:
        try:
            from pymongo import MongoClient
        except ImportError as exc:
            raise RuntimeError("MongoDB support requires the 'all' optional dependencies") from exc
        self.client = MongoClient(uri)
        self.collection = self.client[database][collection]

    def insert(self, readings: Iterable[EnergyReading]) -> int:
        documents = [reading.to_dict() for reading in readings]
        if not documents:
            return 0
        result = self.collection.insert_many(documents)
        return len(result.inserted_ids)


class PostgreSQLPersistence:
    def __init__(self, dsn: str) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL support requires the 'all' optional dependencies"
            ) from exc
        self.connection = psycopg.connect(dsn)
        self._create_schema()

    def _create_schema(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS energy_readings (
                    timestamp TIMESTAMPTZ NOT NULL,
                    region TEXT NOT NULL,
                    consumption_mwh DOUBLE PRECISION NOT NULL,
                    production_mwh DOUBLE PRECISION NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY (timestamp, region)
                )
                """
            )
        self.connection.commit()

    def insert(self, readings: Iterable[EnergyReading]) -> int:
        values = [
            (
                reading.timestamp,
                reading.region,
                reading.consumption_mwh,
                reading.production_mwh,
                reading.source,
            )
            for reading in readings
        ]
        if not values:
            return 0
        with self.connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO energy_readings
                    (timestamp, region, consumption_mwh, production_mwh, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, region) DO UPDATE SET
                    consumption_mwh = EXCLUDED.consumption_mwh,
                    production_mwh = EXCLUDED.production_mwh,
                    source = EXCLUDED.source
                """,
                values,
            )
        self.connection.commit()
        return len(values)
