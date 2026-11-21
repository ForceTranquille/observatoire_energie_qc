# Observatoire Énergétique QC (`observatoire_energie_qc`)

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-KRaft-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Normalized%20Series-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Raw%20Archive-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose%20%7C%20CI%2FCD-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

Pipeline d'ingénierie de données bout-en-bout conçu pour l'acquisition multi-source, la validation schématique et d'idempotence, la diffusion événementielle asynchrone (**Apache Kafka** en mode **KRaft**), la double persistance (**MongoDB** / **PostgreSQL**), l'analyse comparative **Montréal vs Lanaudière** et la visualisation analytique (**Power BI**).

Réalisé dans le cadre du cours **420-C71-BB — Programmation de pipelines de données** (AEC *Spécialiste en solutions d'intelligence artificielle*, Collège de Bois-de-Boulogne, Automne 2026), supervisé par **Hafed Benteftifa**.

---

## 🎯 Objectifs & Périmètre fonctionnel

- **Ingestion de 5 sources hétérogènes** couvrant la demande électrique, les pannes réseau, les alertes météorologiques et les conditions météo entre **Montréal** et **Lanaudière** :
  1. **API REST** (`collecte/api_collecteur.py`)
  2. **Fichier CSV** (`collecte/fichier_collecteur.py` — `donnees/entree/historique_consommation.csv`)
  3. **Fichier JSON** (`collecte/fichier_collecteur.py` — `donnees/entree/pannes_reseau.json`)
  4. **Fichier XML** (`collecte/xml_collecteur.py` — `donnees/entree/alertes_meteo.xml`)
  5. **Web Scraping conforme** (`collecte/web_scraping_collecteur.py` — évaluation `robots.txt` via `RobotFileParser`, délais aléatoires bornés de `13 s`, `15 s` ou `18 s`, en-tête `User-Agent` dédié)
- **Fiabilité & rejouabilité :** contrôle d'idempotence via empreinte **SHA-256** (`modele/evenement_energie.py`) afin d'éviter la duplication lors des réexécutions ou des reprises sur incident.
- **Découplage & auditabilité :** séparation stricte entre l'archive brute non altérée (**MongoDB**) et la série temporelle normalisée prête pour l'analytique et l'IA (**PostgreSQL** + exports CSV/PNG).

---

## 🏗️ Architecture du pipeline

```text
Sources HTTP / JSON / CSV / XML
        |
        v
Collecteur HTTP -> sujet Kafka -> consommateur
                         |              |
                         |              +-> MongoDB (données brutes)
                         v
                 agrégation analysable -> PostgreSQL (série normalisée)