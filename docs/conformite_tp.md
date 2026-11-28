# Conformité à l'énoncé du TP 420-C71-BB

| Exigence de l'énoncé | Où c'est couvert | Vérification |
| --- | --- | --- |
| 1. Format individuel ou équipe | Travail individuel | |
| 2. Web scraping et appels d'API | `collecte/web_scraping_collecteur.py`, `collecte/api_collecteur.py`, `tp_collecte_hydroquebec.py` | `tests/test_scraping.py`, `tests/test_tp_script.py` |
| 2. Approche 1 : programmation Python | Tout le dépôt | `pytest` |
| 2. Approche 2 : outil / agent IA | `docs/approche2_agent_ia.md` | Comparaison documentée |
| 3. Notation et workflow, décrits en premier | `docs/workflow.md` et `docs/workflow.png` | |
| 4.a.i Domaine d'intérêt | Énergie et pannes au Québec (`docs/besoins_donnees.md`) | |
| 4.a.ii Besoin en données | `docs/besoins_donnees.md` | |
| 4.a.iii Collecte avec des modules appropriés | `requests`, `BeautifulSoup`, `pandas`, `urllib.robotparser` | |
| 4.a.iv Accès par une API | Open-Meteo, API Explore v2.1 d'Hydro-Québec, `demande.json` | `tests/test_demande_hq.py` |
| 4.a.v Représentation en DataFrame | `io_fichiers/export_ia.py`, `analyse/analyse_energie.py`, section 8 de `tp_collecte_hydroquebec.py` | `tests/test_evenement_export.py` |
| 4.b Code Python, modules dédiés | Architecture modulaire (`collecte/`, `streaming/`, `base_de_donnees/`, `analyse/`) | |
| Scraping aléatoire (13, 15, 18 s) | `WebScrapingCollecteur.DELAIS_AUTORISES`, `pause_aleatoire()` | `test_pause_aleatoire_appliquee_entre_deux_requetes` |
| `robots.txt` : politique du site | `collecte/robots.py` (lecture selon le code HTTP, refus par prudence) | `tests/test_robots.py` |

## Ce qui n'a pas pu être vérifié depuis l'environnement de développement

- L'accès réseau réel à `donnees.hydroquebec.com` et le contenu de son `robots.txt`.
- Le verdict de `robots.txt` pour `www.hydroquebec.com` et `pannes.hydroquebec.com`.

À contrôler avant la remise : lancer `python tp_collecte_hydroquebec.py` et noter, dans le
rapport, le code HTTP et le verdict affichés à la section 3.
