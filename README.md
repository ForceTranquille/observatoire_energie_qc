# Observatoire Énergétique QC (`observatoire_energie_qc`)

Projet de session réalisé dans le cadre du cours **420-C71-BB — Programmation de pipelines de données** (AEC *Spécialiste en solutions d'intelligence artificielle*, Collège de Bois-de-Boulogne, Automne 2026), supervisé par **Hafed Benteftifa**.

## Objectif du pipeline

Concevoir et exécuter un pipeline bout-en-bout d'acquisition, de validation, de diffusion événementielle, de stockage hybride et d'analyse croisée des données énergétiques et météorologiques entre **Montréal** et **Lanaudière** à partir de **5 formats hétérogènes** :

1. **API REST** (`collecte/api_collecteur.py`)
2. **Fichier CSV** (`collecte/fichier_collecteur.py` — `donnees/entree/historique_consommation.csv`)
3. **Fichier JSON** (`collecte/fichier_collecteur.py` — `donnees/entree/pannes_reseau.json`)
4. **Fichier XML** (`collecte/xml_collecteur.py` — `donnees/entree/alertes_meteo.xml`)
5. **Web Scraping éthique** (`collecte/web_scraping_collecteur.py` — vérification `robots.txt` via `RobotFileParser`, délais aléatoires de `13 s`, `15 s` ou `18 s` et en-tête `User-Agent` dédié)

## Architecture du projet

```text
observatoire_energie_qc/
├── analyse/
│   └── analyse_energie.py
├── base_de_donnees/
│   ├── __init__.py
│   ├── mongo_repo.py
│   └── postgres_repo.py
├── collecte/
│   ├── __init__.py
│   ├── api_collecteur.py
│   ├── base_collecteur.py
│   ├── fichier_collecteur.py
│   ├── web_scraping_collecteur.py
│   └── xml_collecteur.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── donnees/
│   ├── entree/
│   │   ├── alertes_meteo.xml
│   │   ├── historique_consommation.csv
│   │   └── pannes_reseau.json
│   └── sortie/
│       ├── figures/
│       │   ├── clients_par_panne.png
│       │   └── demande_par_region.png
│       ├── alerte_propre.csv
│       ├── consommation_propre.csv
│       ├── croisement_conso_meteo.csv
│       ├── dataset_energie_normalise.csv
│       ├── meteo_propre.csv
│       ├── pannes_propre.csv
│       └── web_scraping_propre.csv
├── io_fichiers/
│   ├── __init__.py
│   └── export_ia.py
├── modele/
│   ├── __init__.py
│   └── evenement_energie.py
├── streaming/
│   ├── __init__.py
│   ├── consommateur_kafka.py
│   └── producteur_kafka.py
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── mod_analyse.py
├── mod_main.py
└── requirements.txt