from pathlib import Path
from typing import List, Optional
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from base_de_donnees.mongo_repo import MongoBrutRepository
from base_de_donnees.postgres_repo import PostgresEnergieRepository
from collecte.api_collecteur import ApiMeteoCollecteur
from collecte.base_collecteur import BaseCollecteur
from collecte.fichier_collecteur import CsvConsommationCollecteur, JsonPanneCollecteur
from collecte.web_scraping_collecteur import WebScrapingCollecteur
from collecte.xml_collecteur import XmlAlerteCollecteur
from config.settings import TOPICS
from io_fichiers.export_ia import ExporteurEnergie
from modele.evenement_energie import EvenementEnergie
from streaming.consommateur_kafka import ConsommateurEnergieKafka
from streaming.producteur_kafka import ProducteurEnergieKafka

console = Console()


def _fermer_ressources(*ressources: Optional[object]) -> None:
    for res in ressources:
        if res is not None and hasattr(res, "fermer"):
            try:
                res.fermer()  # type: ignore[attr-defined]
            except Exception as exc:
                console.print(f"  [yellow]WARN[/yellow] Fermeture ressource : {exc}")


def executer_pipeline() -> None:
    console.print(
        Panel.fit(
            "[bold white]OBSERVATOIRE ÉNERGÉTIQUE QC[/bold white]\n"
            "[cyan]Pipeline d'ingestion, streaming Kafka & persistance hybride (420-C71-BB)[/cyan]",
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )

    racine_projet = Path(__file__).resolve().parent
    base_entree = racine_projet / "donnees" / "entree"
    base_sortie = racine_projet / "donnees" / "sortie"
    base_sortie.mkdir(parents=True, exist_ok=True)

    collecteurs: List[BaseCollecteur] = [
        ApiMeteoCollecteur("OpenMeteo_Montreal", 45.5017, -73.5673, "Montreal"),
        ApiMeteoCollecteur("OpenMeteo_Lanaudiere", 46.0167, -73.4333, "Lanaudiere"),
        CsvConsommationCollecteur("HQ_Historique_CSV", base_entree / "historique_consommation.csv"),
        JsonPanneCollecteur("HQ_Pannes_JSON", base_entree / "pannes_reseau.json"),
        XmlAlerteCollecteur("Alertes_XML", base_entree / "alertes_meteo.xml"),
        WebScrapingCollecteur(
            "Meteo_MTL_Scraping",
            urls=["https://meteo.gc.ca/fr/location/index.html?coords=45.509,-73.554"],
            region="Montreal",
        ),
    ]

    # --- Étape 1 : Collecte ---
    console.print("\n[bold cyan][1/4] Collecte multi-sources[/bold cyan]")
    evenements_collectes: List[EvenementEnergie] = []
    erreurs_collecte = 0

    for collecteur in collecteurs:
        try:
            lots = collecteur.extraire()
            evenements_collectes.extend(lots)
            console.print(
                f"  [bold green]OK[/bold green]  {collecteur.nom_source:<22} "
                f"[dim]|[/dim] [bold]{len(lots)}[/bold] événement(s)"
            )
        except Exception as exc:
            erreurs_collecte += 1
            console.print(
                f"  [bold red]ERR[/bold red] {collecteur.nom_source:<22} "
                f"[dim]|[/dim] [red]{exc}[/red]"
            )

    # --- Étape 2 : Publication Kafka ---
    console.print("\n[bold cyan][2/4] Publication streaming Kafka[/bold cyan]")
    publies = 0
    producteur: Optional[ProducteurEnergieKafka] = None
    try:
        producteur = ProducteurEnergieKafka()
        publies = producteur.publier_evenements(evenements_collectes)
        console.print(f"  [bold green]OK[/bold green]  Messages publiés : [bold]{publies}[/bold]")
    finally:
        _fermer_ressources(producteur)

    # --- Étape 3 : Consommation & Persistance dédupliquée ---
    console.print("\n[bold cyan][3/4] Consommation & persistance (MongoDB + PostgreSQL)[/bold cyan]")
    consommateur: Optional[ConsommateurEnergieKafka] = None
    mongo_repo: Optional[MongoBrutRepository] = None
    pg_repo: Optional[PostgresEnergieRepository] = None
    enregistrements_export: List[dict] = []
    stats = {"consommes": 0, "inseres": 0, "doublons": 0}

    def traiter_message(evt: dict) -> None:
        stats["consommes"] += 1
        ins_mongo = mongo_repo.inserer_evenement(evt) if mongo_repo is not None else False
        ins_pg = pg_repo.inserer_evenement(evt) if pg_repo is not None else False
        if ins_mongo or ins_pg:
            stats["inseres"] += 1
        else:
            stats["doublons"] += 1
        enregistrements_export.append(evt)

    try:
        consommateur = ConsommateurEnergieKafka(list(TOPICS.values()))
        mongo_repo = MongoBrutRepository()
        pg_repo = PostgresEnergieRepository()
        consommateur.consommer_lot(traiter_message)
        console.print(
            f"  [bold green]OK[/bold green]  Lus : [bold]{stats['consommes']}[/bold]  "
            f"[dim]|[/dim]  Nouveaux : [bold green]{stats['inseres']}[/bold green]  "
            f"[dim]|[/dim]  Doublons ignorés : [bold yellow]{stats['doublons']}[/bold yellow]"
        )
    finally:
        _fermer_ressources(consommateur, mongo_repo, pg_repo)

    # --- Étape 4 : Exports ---
    console.print("\n[bold cyan][4/4] Génération des fichiers CSV[/bold cyan]")
    fichiers_export = {}
    if enregistrements_export:
        exporteur = ExporteurEnergie(base_sortie)
        fichiers_export = exporteur.exporter(enregistrements_export)
        for cle, chemin in fichiers_export.items():
            nb_lignes = max(
                sum(1 for _ in open(chemin, encoding="utf-8")) - 1,
                0,
            )
            console.print(
                f"  [bold green]OK[/bold green]  {cle:<14} "
                f"[dim]|[/dim] [bold]{nb_lignes:>3}[/bold] ligne(s) "
                f"[dim]|[/dim] {chemin.name}"
            )
    else:
        console.print("  [yellow]WARN[/yellow] Aucun enregistrement à exporter.")

    # --- Tableau récapitulatif ---
    console.print()
    tableau = Table(
        title="Événements collectés lors de l'exécution",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold cyan",
        expand=False,
        pad_edge=True,
    )
    tableau.add_column("#", justify="right", style="dim", width=3, no_wrap=True)
    tableau.add_column("Source", style="bold white", no_wrap=True)
    tableau.add_column("Format", justify="center", style="magenta", width=6, no_wrap=True)
    tableau.add_column("Catégorie", style="green", no_wrap=True)
    tableau.add_column("Région", style="yellow", no_wrap=True)
    tableau.add_column("ID", style="dim", width=8, no_wrap=True)

    for idx, evt in enumerate(evenements_collectes, start=1):
        region = str(evt.donnees.get("region", "-"))
        tableau.add_row(
            str(idx),
            evt.source,
            evt.format_origine,
            evt.categorie,
            region,
            evt.event_id[:8],
        )

    console.print(tableau)
    console.print(
        f"\n[bold green]Terminé[/bold green] — "
        f"Collectés: [bold]{len(evenements_collectes)}[/bold] | "
        f"Erreurs: [bold]{erreurs_collecte}[/bold] | "
        f"Fichiers générés: [bold]{len(fichiers_export)}[/bold]\n"
    )


if __name__ == "__main__":
    executer_pipeline()