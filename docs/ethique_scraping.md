# Éthique et conformité de la collecte (scraping et API)

Ce document décrit les règles que le projet s'impose avant et pendant toute requête vers un site
externe. Elles sont appliquées par le code (`collecte/robots.py`, `collecte/web_scraping_collecteur.py`,
`collecte/demande_hq_collecteur.py`, `collecte/pannes_hq_collecteur.py`) et vérifiées par des tests.

## Règles appliquées

| Règle | Application dans le projet |
| --- | --- |
| Lire `robots.txt` avant de collecter | Chaque hôte est vérifié avant la première requête ; le résultat est mis en cache pour l'exécution |
| Interpréter `robots.txt` selon le code HTTP | 200 : règles lues · 401/403 : tout refusé · autre 4xx : tout permis · 5xx ou réseau en panne : refus par prudence |
| Respecter un refus | L'URL refusée n'est pas collectée ; la décision est affichée et documentée (jamais contournée) |
| Espacer les requêtes | Pause aléatoire de **13 s, 15 s ou 18 s** entre deux requêtes successives vers les pages scrapées |
| Se identifier | En-tête `User-Agent` : `ObservatoireEnergieQC-Bot/1.0 (usage pedagogique, 420-C71-BB)` |
| Ne pas surcharger | Pagination à 100 enregistrements au plus par appel, attente exponentielle (1 s, 2 s, 4 s) et abandon après trois réponses 429 |
| Limiter la collecte au besoin | Seuls les champs utiles aux besoins en données sont conservés |
| Protéger les personnes | Aucune donnée personnelle : les pannes ne contiennent que des identifiants de municipalité et des coordonnées |
| Rester honnête sur les données | Les fichiers d'exemple (CSV, JSON, XML) sont étiquetés comme tels ; ils ne servent pas à tirer de conclusions |
| Citer les sources | Hydro-Québec (données ouvertes), Météo Canada, Open-Meteo ; vérifier la licence d'utilisation de chaque jeu avant toute réutilisation |

## Verdicts observés (exécution du 2026-11-28)

| Hôte | Chemin testé | Code HTTP de `robots.txt` | Décision |
| --- | --- | --- | --- |
| `www.hydroquebec.com` | page des données ouvertes, `demande.json` | 200 | autorisé |
| `pannes.hydroquebec.com` | `/pannes/donnees/v3_0/bisversion.json` | 200 | autorisé |
| `donnees.hydroquebec.com` | `/api/explore/v2.1/catalog/datasets` | 200 | **refusé** : source non collectée |
| Météo Canada | pages météo de Montréal et Lanaudière | à noter à la prochaine exécution | pages collectées |

## Pourquoi 13, 15 ou 18 secondes

Une pause fixe et courte ressemble à un robot agressif. Une pause aléatoire parmi trois valeurs
longues répartit la charge, évite un rythme régulier et laisse le serveur répondre aux visiteurs réels.
Le temps d'attente ne s'applique pas avant la première requête, seulement entre deux requêtes successives.

## Limites

- `robots.txt` exprime la politique d'un site ; il ne remplace pas ses conditions d'utilisation ni la licence des données.
- Les pauses ne s'appliquent qu'au scraping HTML ; les fichiers JSON ouverts sont lus une fois par exécution.
