import json
from typing import Dict, Any, Optional
import psycopg2
from config.settings import PG_CONFIG


class PostgresEnergieRepository:
    """Persiste les données normalisées dans PostgreSQL avec déduplication."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or PG_CONFIG
        self._conn = psycopg2.connect(**self._config)
        self._creer_tables()

    def _creer_tables(self) -> None:
        with self._conn:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS evenements_normalises (
                        id SERIAL PRIMARY KEY,
                        event_id VARCHAR(64) UNIQUE,
                        source VARCHAR(100) NOT NULL,
                        format_origine VARCHAR(20) NOT NULL,
                        categorie VARCHAR(50) NOT NULL,
                        region VARCHAR(100),
                        horodatage_utc TIMESTAMPTZ NOT NULL,
                        payload_json TEXT NOT NULL
                    );
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE evenements_normalises
                    ADD COLUMN IF NOT EXISTS event_id VARCHAR(64) UNIQUE;
                    """
                )

    def inserer_evenement(self, evenement: Dict[str, Any]) -> bool:
        donnees = evenement.get("donnees", {})
        region = donnees.get("region", "Non specifiee")
        with self._conn:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO evenements_normalises
                        (event_id, source, format_origine, categorie, region, horodatage_utc, payload_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING;
                    """,
                    (
                        evenement.get("event_id"),
                        evenement.get("source"),
                        evenement.get("format_origine"),
                        evenement.get("categorie"),
                        region,
                        evenement.get("horodatage_utc"),
                        json.dumps(donnees, ensure_ascii=False),
                    ),
                )
                return cur.rowcount > 0

    def fermer(self) -> None:
        if self._conn and not self._conn.closed:
            self._conn.close()