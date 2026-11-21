# Observatoire de l'énergie du Québec

Prototype Python permettant de collecter des relevés énergétiques, de les
publier dans Apache Kafka, de les conserver dans MongoDB puis PostgreSQL, et
d'en produire des indicateurs simples.

## Architecture

```text
Sources HTTP/JSON/CSV
        |
        v
Collecteur HTTP -> sujet Kafka -> consommateur
                         |              |
                         |              +-> MongoDB (données brutes)
                         v
                 agrégation analysable -> PostgreSQL (série normalisée)
```

Le code est organisé comme une bibliothèque réutilisable. Les pilotes
MongoDB, PostgreSQL et Kafka sont chargés uniquement lorsqu'ils sont utilisés;
les couches applicatives restent testables sans Docker.

## Démarrage

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .

# Services locaux
docker compose up -d

# Exemple de collecte locale
python -m observatoire_energie_qc.main collect \
  --url https://example.org/energy.json \
  --kafka-bootstrap localhost:9092
```

Un mode sans Kafka est disponible pour traiter un fichier directement:

```bash
python -m observatoire_energie_qc.main ingest \
  --input releves.json
```

## Format des relevés

Chaque relevé accepte au minimum `timestamp`, `region`, `consumption_mwh` et
`production_mwh`:

```json
{
  "timestamp": "2026-11-21T12:00:00Z",
  "region": "Québec",
  "consumption_mwh": 12500,
  "production_mwh": 13100,
  "source": "example"
}
```

Les champs `timestamp`, `consumption_mwh`, `production_mwh` et `region` sont
validés avant publication ou persistance.