# Workflow du processus de collecte (énoncé, point 3)

**Notation :** organigramme (*flowchart*) en Mermaid, avec les symboles de la notation
BPMN simplifiée : ovale = début / fin, rectangle = tâche, losange = décision,
cylindre = stockage, cadre = sous-processus.

```mermaid
flowchart TD
    A([Début : besoin de données<br/>énergie et pannes au Québec]) --> B[Identifier les besoins en données<br/>docs/besoins_donnees.md]
    B --> C{robots.txt autorise<br/>la collecte ?}
    C -- non --> D[Documenter le refus<br/>NE PAS collecter]
    C -- oui --> E1

    subgraph COL [Collecte en Python]
        E1[Web scraping<br/>requests + BeautifulSoup<br/>pause aléatoire 13 / 15 / 18 s]
        E2[API REST<br/>Open-Meteo, Explore v2.1]
        E3[JSON ouvert<br/>demande.json, pas de 15 min]
        E4[Fichiers CSV / JSON / XML]
    end

    E1 --> F
    E2 --> F
    E3 --> F
    E4 --> F
    F[Événement normalisé<br/>identifiant SHA-256] --> G[(Kafka)]
    G --> H[(MongoDB<br/>données brutes)]
    G --> I[(PostgreSQL<br/>série normalisée)]
    F --> J[DataFrame pandas]
    J --> K[Exploration<br/>info, describe, graphiques]
    K --> L[Export CSV et figures]
    L --> M([Fin])
    D --> M
```

![Workflow du processus de collecte](workflow.png)

## Lecture

1. **Besoin** : le domaine est l'énergie et les pannes au Québec (voir `besoins_donnees.md`).
2. **Politique du site** : `robots.txt` est lu avant toute requête. 200 : les règles sont
   appliquées ; 401 ou 403 : tout est refusé ; autre 4xx : tout est permis ; 5xx ou réseau
   en panne : refus par prudence.
3. **Collecte** : quatre familles de sources, toutes derrière la même classe abstraite
   `BaseCollecteur` (méthode `extraire()`).
4. **Normalisation** : chaque enregistrement devient un `EvenementEnergie` ; son `event_id`
   SHA-256 permet d'ignorer les doublons à chaque relance.
5. **Représentation** : DataFrame pandas, exploration, puis export CSV et figures.

Les deux scripts d'entrée correspondent à ce schéma :
`mod_main.py` (pipeline complet avec Kafka et bases) et `tp_collecte_hydroquebec.py`
(script numéroté section par section, comme l'énoncé).
