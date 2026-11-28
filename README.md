# Observatoire Énergétique QC (`observatoire_energie_qc`) — Branche `feat/powerbi`

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-KRaft-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Normalized%20Series-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Raw%20Archive-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose%20%7C%20CI%2FCD-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

Pipeline de données bout-en-bout : acquisition multi-source, validation et idempotence,
diffusion événementielle (**Apache Kafka** en mode **KRaft**), double persistance
(**MongoDB** / **PostgreSQL**), analyse comparative **Montréal vs Lanaudière** et
visualisation (**Power BI**).

> **Cette branche = `main` + le tableau de bord Power BI.** Le code Python est identique à `main` ; seul le dossier
> `powerbi/` et ce README sont propres à la branche. Pour le pipeline seul, voir la branche `main`.

Réalisé dans le cadre du cours **420-C71-BB** (AEC *Spécialiste en solutions d'intelligence
artificielle*, Collège de Bois-de-Boulogne, Automne 2026), supervisé par **Hafed Benteftifa**.

---

## Sources de données

| # | Source | Format | Collecteur |
| --- | --- | --- | --- |
| 1 | Open-Meteo (Montréal, Lanaudière) | API REST | `collecte/api_collecteur.py` |
| 2 | Demande du Québec, pas de 15 min (données ouvertes Hydro-Québec) | JSON | `collecte/demande_hq_collecteur.py` |
| 3 | Historique de consommation (exemple fictif) | CSV | `collecte/fichier_collecteur.py` |
| 4 | Pannes en cours, Québec entier (données réelles) | JSON | `collecte/pannes_hq_collecteur.py` |
| 4b | Pannes réseau (exemple fictif) | JSON | `collecte/fichier_collecteur.py` |
| 5 | Alertes météo (exemple fictif) | XML | `collecte/xml_collecteur.py` |
| 6 | Pages Météo Canada (Montréal, Lanaudière) | HTML | `collecte/web_scraping_collecteur.py` |

**Scraping conforme :** `robots.txt` est lu avant chaque requête (`collecte/robots.py`) et
interprété selon son code HTTP ; une pause aléatoire de **13 s, 15 s ou 18 s** sépare les
requêtes successives ; l'en-tête `User-Agent` identifie le projet.

**Idempotence :** chaque événement porte un `event_id` SHA-256 (`modele/evenement_energie.py`) :
les relances ne créent pas de doublons.

---

## Architecture

```text
Sources HTTP / JSON / CSV / XML
        |
        v
Collecteurs (BaseCollecteur.extraire) -> EvenementEnergie (SHA-256)
        |
        v
sujet Kafka -> consommateur
                    |-> MongoDB (données brutes)
                    |-> PostgreSQL (série normalisée)
                    |-> exports CSV -> analyse et graphiques
```

Le workflow détaillé, avec sa notation, est dans [`docs/workflow.md`](docs/workflow.md). Les règles d'éthique de collecte (`robots.txt`, pauses de 13/15/18 s) sont dans [`docs/ethique_scraping.md`](docs/ethique_scraping.md).

---

## Démarrage rapide

```bash
python -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # Windows : copy .env.example .env
docker compose up -d                                  # Kafka (KRaft), PostgreSQL, MongoDB

python mod_main.py                  # collecte -> Kafka -> bases -> CSV (donnees/sortie/)
python mod_analyse.py               # statistiques, croisement régional, figures
python tp_collecte_hydroquebec.py   # script du TP, numéroté comme l'énoncé
pytest                              # tests (aucun accès réseau requis)
```

`tp_collecte_hydroquebec.py --sans-pause` saute les pauses de 13/15/18 s : à réserver au
développement.

---

## Structure du dépôt

```text
collecte/            collecteurs (API, fichiers, XML, scraping, demande.json) et robots.txt
streaming/           producteur et consommateur Kafka
base_de_donnees/     dépôts MongoDB et PostgreSQL
modele/              EvenementEnergie (modèle normalisé, SHA-256)
io_fichiers/         export des CSV propres
analyse/             statistiques, croisements, graphiques
config/              paramètres (topics, bases)
donnees/             entrées d'exemple et sorties
docs/                workflow, besoins en données, approche 2, conformité à l'énoncé
tests/               pytest (réponses HTTP simulées)
tp_collecte_hydroquebec.py   script du TP (méthode en 10 sections)
```

---

## Énoncé du TP

La correspondance exigence par exigence est dans
[`docs/conformite_tp.md`](docs/conformite_tp.md). Les besoins en données sont décrits dans
[`docs/besoins_donnees.md`](docs/besoins_donnees.md) et la comparaison avec l'approche
« outil / agent IA » dans [`docs/approche2_agent_ia.md`](docs/approche2_agent_ia.md).

---

## Tableau de bord Power BI

Fichier : `powerbi/observatoire_energie_qc.pbix` (Power BI Desktop). Il lit les CSV nettoyés de `donnees/sortie/`
pour comparer la demande, les pannes et la météo entre **Montréal** et **Lanaudière**.

**Utiliser le tableau de bord**

1. Générer les CSV : `python mod_main.py` (Docker Compose démarré, voir *Démarrage rapide*).
2. Ouvrir `powerbi/observatoire_energie_qc.pbix`, puis *Accueil > Actualiser*.
3. Si Power BI ne trouve plus les fichiers : *Transformer les données > Paramètres de la source de données* et
   pointer vers le dossier `donnees/sortie/` de ton poste.

**Sources du modèle**

| Fichier | Contenu | Origine des données |
| --- | --- | --- |
| `dataset_energie_normalise.csv` | événements normalisés (Montréal, Lanaudière) | mixte |
| `croisement_conso_meteo.csv` | demande et météo par région | demande : **exemple**, météo : réelle |
| `pannes_propre.csv` | pannes par région | **exemple** (2 lignes) |
| `web_scraping_propre.csv` | pages Météo Canada scrapées | réelle |

**Visuels** : segment `region` (`Lanaudiere` / `Montreal`) qui pilote la page, KPI *Demande moyenne (MW)* et
*Total clients touchés*, graphiques *Demande (MW) par région*, *Clients touchés* et *Demande et température*.

**À lire avant d'interpréter les chiffres.** Les KPI de demande et de pannes viennent de fichiers d'exemple de quelques
lignes : ils démontrent le modèle, ils ne mesurent pas Hydro-Québec. Les données réelles (demande du Québec,
`demande_quebec_propre.csv`, et pannes en cours, `pannes_en_cours_propre.csv`) couvrent tout le Québec, sans région
Montréal ou Lanaudière ; elles sont exportées à part et **ne sont pas** dans le modèle actuel, pour ne pas fausser les
KPI régionaux. Pour les afficher, ajouter ces deux CSV comme sources dans Power BI.

---

## Stratégie de branches

Le dépôt n'a que **deux branches** :

* **`main` :** tout le code Python (collecte, Kafka KRaft, MongoDB, PostgreSQL, analyse), les tests et la documentation.
* **`feat/powerbi` :** `main` plus le tableau de bord **Power BI** (`powerbi/observatoire_energie_qc.pbix`).

Flux de travail : on modifie et on teste le Python sur `main`, puis on fusionne `main` dans `feat/powerbi`
(`git checkout feat/powerbi` puis `git merge main`) pour que le tableau de bord suive le code.

---

## Limites connues

* Les entrées CSV, JSON et XML sont des jeux d'exemple de quelques lignes : elles montrent les
  formats mais ne permettent pas de conclusions statistiques.
* `demande.json` est une fenêtre glissante d'environ 2 jours : l'historique se construit en
  relançant la collecte.
* Les pages scrapées sont des instantanés : leurs événements ne sont pas strictement
  idempotents d'une exécution à l'autre.
