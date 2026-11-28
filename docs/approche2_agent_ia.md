# Approche 2 : outil / agent IA (énoncé, point 2)

L'approche 1 est le code Python du dépôt. L'approche 2 consiste à confier tout ou partie de la
collecte à un outil ou à un agent IA. Cette page compare les deux.

## Essai réalisé (2026-11-24, assistant IA avec outil de lecture web)

| Tâche | Résultat observé |
| --- | --- |
| Lire `demande.json` | Réussi. L'assistant a décrit la structure : 5 clés de métadonnées, une liste `details` d'environ 190 entrées toutes les 15 minutes, champ `valeurs.demandeTotal`, créneaux futurs vides |
| Proposer un collecteur Python | Réussi : le code a ensuite été intégré et testé (`collecte/demande_hq_collecteur.py`) |
| Lire `robots.txt` du site | **Refusé par l'outil** : le contrôle de politique du site n'a pas pu être fait par l'agent |
| Lire l'API `donnees.hydroquebec.com` (2026-11-28) | **Refusé par l'outil** (domaine hors liste autorisée) |
| Collecter régulièrement pour bâtir un historique | Impossible : l'agent ne tourne pas en continu |

## Comparaison

| Critère | Approche 1 : Python | Approche 2 : outil / agent IA |
| --- | --- | --- |
| Mise en route | Écrire et tester du code | Une consigne suffit |
| Reproductibilité | Script rejouable, tests automatisés | Dépend de l'outil, de la session et de la formulation |
| Politique `robots.txt` | Appliquée par le code avant chaque requête | Non garantie : l'outil peut la refuser ou l'ignorer |
| Volume et pagination | Pagination, nouvel essai sur 429, export CSV complet | Limité à ce que l'outil lit en une fois |
| Fiabilité | Vérifiée par des tests | À contrôler : un résumé peut tronquer ou se tromper |
| Meilleur usage | Collecte régulière et pipeline | Explorer vite une source inconnue, générer un squelette de code |

## Conclusion

Les deux approches se complètent : l'agent IA a servi à **explorer** `demande.json` et à
rédiger un premier collecteur ; le code Python l'exécute, applique `robots.txt` et peut être
relancé. La vérification de la politique du site reste une étape humaine ou programmée,
jamais déléguée à un résumé d'agent.

## À compléter avec tes propres essais

| Outil | Date | Consigne donnée | Résultat | Limite rencontrée |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
