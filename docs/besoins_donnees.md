# Besoins en données (énoncé, point 4.a.ii)

**Domaine :** énergie électrique au Québec : demande, pannes réseau, météo et alertes.

**Questions auxquelles les données doivent répondre**

1. Comment la demande d'électricité varie-t-elle dans la journée (pas de 15 minutes) ?
2. Comment se compare-t-elle entre Montréal et Lanaudière, et quel est le lien avec la météo ?
3. Où et pourquoi surviennent les pannes, et combien de clients touchent-elles ?

| Besoin | Champs utiles | Source | Granularité | Accès | Sortie |
| --- | --- | --- | --- | --- | --- |
| Demande du Québec | date, demande totale (MW) | `demande.json`, données ouvertes Hydro-Québec | 15 min, fenêtre glissante d'environ 2 jours | JSON ouvert | `demande_quebec_propre.csv` |
| Production et consommation horaires | champs découverts par les métadonnées | API Explore v2.1 (`donnees.hydroquebec.com`) | horaire | API REST paginée | `hq_production_consommation_horaire.csv` |
| Catalogue des jeux ouverts | id, titre, date de modification, nombre de lignes | API Explore v2.1 | instantané | API REST | `hq_catalogue.csv` |
| Météo | température, vent, précipitations | Open-Meteo | courant | API REST | `meteo_propre.csv` |
| Demande par région | région, demande (MW), température | `historique_consommation.csv` | quelques lignes d'exemple | fichier CSV | `consommation_propre.csv` |
| Pannes | id, région, clients touchés, cause | `pannes_reseau.json` (exemple) ; pannes en cours sous réserve de `robots.txt` | ponctuel | fichier JSON / API | `pannes_propre.csv` |
| Alertes météo | id, région, type, sévérité | `alertes_meteo.xml` | ponctuel | fichier XML | `alerte_propre.csv` |
| Veille HTML | titre, nombre de paragraphes, URL | pages `meteo.gc.ca` | instantané | web scraping | `web_scraping_propre.csv` |

## Limites connues

- `demande.json` ne couvre qu'une fenêtre glissante : l'historique se construit en relançant
  la collecte (la déduplication SHA-256 évite les doublons).
- La demande de `demande.json` est celle de **tout le Québec** : elle n'est pas découpée par
  région, d'où sa catégorie séparée (`demande_quebec`).
- Les fichiers CSV, JSON et XML d'entrée contiennent quelques lignes d'exemple : ils servent
  à démontrer les formats, pas à tirer des conclusions statistiques.
- Le JSON des pannes en cours n'est collecté que si son `robots.txt` le permet ; sinon la
  décision est documentée et la source n'est pas utilisée.
