# Observatoire Énergétique QC (`observatoire_energie_qc`) — Branche `feat/powerbi`

Branche dédiée à la couche **Business Intelligence (Power BI Desktop)** du projet **`observatoire_energie_qc`** réalisé dans le cadre du cours **420-C71-BB — Programmation de pipelines de données** (Collège de Bois-de-Boulogne, Automne 2026), supervisé par **Hafed Benteftifa**.

---

## 📊 Tableau de bord Power BI (`powerbi/observatoire_energie_qc.pbix`)

Ce tableau de bord exploite les sorties nettoyées générées par le pipeline Python (`donnees/sortie/`) pour comparer la demande électrique, les pannes réseau et les conditions météorologiques entre **Montréal** et **Lanaudière** :

* **Sources alimentant le modèle :**
  * `dataset_energie_normalise.csv`
  * `croisement_conso_meteo.csv`
  * `pannes_propre.csv`
  * `web_scraping_propre.csv`
* **Visuels clés de la page :**
  * **Segment (`Slicer`) `region`** (`Lanaudiere` / `Montreal`) pilotant l'ensemble des visuels.
  * **KPI `Demande moyenne (MW)`** (`Average of demande_mw`) et **`Total clients touchés`** (`Sum of clients_touches`).
  * **Graphiques comparatifs :** *Demande (MW) par région*, *Total clients touchés* par région et *Croisement demande (MW) et température (°C)*.

---

## 🔀 Stratégie de branches

* **`main` :** branche principale du pipeline de collecte, Kafka (KRaft), MongoDB, PostgreSQL et analyse (`mod_main.py`, `mod_analyse.py`).
* **`feat/powerbi` :** branche isolée contenant les artefacts **Power BI** (`powerbi/observatoire_energie_qc.pbix`) et la documentation BI associée.