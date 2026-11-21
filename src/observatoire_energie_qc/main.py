from __future__ import annotations

import argparse
import json
import sys

from .collector import collect_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Observatoire énergétique du Québec")
    sub = parser.add_subparsers(dest="command", required=True)

    collect = sub.add_parser("collect", help="Collecter depuis une URL ou un fichier")
    collect.add_argument("--url", required=True)
    collect.add_argument("--kafka-bootstrap", default="localhost:9092")
    collect.add_argument("--topic", default="energy-readings")

    ingest = sub.add_parser("ingest", help="Analyser un fichier local")
    ingest.add_argument("--input", required=True)
    ingest.add_argument("--mongo-uri")
    ingest.add_argument("--postgres-dsn")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    readings = collect_records(args.url if args.command == "collect" else args.input)

    if args.command == "collect":
        from .kafka import KafkaPublisher

        publisher = KafkaPublisher(args.kafka_bootstrap, args.topic)
        try:
            print(json.dumps({"published": publisher.publish(readings)}))
        finally:
            publisher.close()
    else:
        from .analysis import daily_summary

        print(json.dumps(daily_summary(readings), ensure_ascii=False, indent=2))
        if args.mongo_uri:
            from .persistence import MongoPersistence

            print(json.dumps({"mongo_inserted": MongoPersistence(args.mongo_uri).insert(readings)}))
        if args.postgres_dsn:
            from .persistence import PostgreSQLPersistence

            print(json.dumps({"postgres_upserted": PostgreSQLPersistence(args.postgres_dsn).insert(readings)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
