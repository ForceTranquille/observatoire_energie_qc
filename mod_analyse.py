from pathlib import Path
from typing import NamedTuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from analyse.analyse_energie import AnalyseurEnergie

console = Console()


class SyntheseRegionale(NamedTuple):
    region: str
    demande_mw: float
    temperature_c: float
    vent_kmh: float
    precipitations_mm: float


class ApercuScraping(NamedTuple):
    region: str
    titre_page: str
    nb_paragraphes: str
    url_source: str


def _df_vers_table(titre: str, df) -> Table:
    table = Table(
        title=titre,
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold cyan",
        expand=False,
    )
    for col in df.columns:
        table.add_column(str(col), no_wrap=True)
    for _, row in df.iterrows():
        table.add_row(*[str(val) for val in row])
    return table


def _extraire_apercus_scraping(df) -> list[ApercuScraping]:
    apercus: list[ApercuScraping] = []
    for _, row in df.iterrows():
        region = str(row["region"]) if "region" in df.columns else "N/A"
        titre = str(row["titre_page"])[:45] if "titre_page" in df.columns else "N/A"
        nb_para = str(row["nb_paragraphes"]) if "nb_paragraphes" in df.columns else "-"
        url = str(row["url_source"])[:55] if "url_source" in df.columns else "N/A"
        apercus.append(
            ApercuScraping(
                region=region,
                titre_page=titre,
                nb_paragraphes=nb_para,
                url_source=url,
            )
        )
    return apercus


def _afficher_apercu_scraping(df) -> None:
    apercus = _extraire_apercus_scraping(df)
    table = Table(
        title="Aperçu — web_scraping",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold cyan",
        expand=False,
    )
    for col in ["region", "titre_page", "nb_paragraphes", "url_source"]:
        table.add_column(col, no_wrap=True)

    for item in apercus:
        table.add_row(item.region, item.titre_page, item.nb_paragraphes, item.url_source)

    console.print(table)


def _extraire_syntheses_regionales(df_croise) -> list[SyntheseRegionale]:
    syntheses: list[SyntheseRegionale] = []
    for _, row in df_croise.iterrows():
        syntheses.append(
            SyntheseRegionale(
                region=str(row["region"]),
                demande_mw=round(float(row["demande_mw_moy"]), 2),
                temperature_c=round(float(row["temperature_c_moy"]), 2),
                vent_kmh=round(float(row["vent_kmh_moy"]), 2),
                precipitations_mm=round(float(row["precipitations_mm_moy"]), 2),
            )
        )
    return syntheses


def _afficher_synthese_regionale(df_croise) -> None:
    syntheses = _extraire_syntheses_regionales(df_croise)
    table = Table(
        title="Synthèse régionale",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold cyan",
        expand=False,
    )
    for col in ["region", "Demande (MW)", "Temp (°C)", "Vent (km/h)", "Pluie (mm)"]:
        table.add_column(col, no_wrap=True)

    for item in syntheses:
        table.add_row(
            item.region,
            f"{item.demande_mw:.2f}",
            f"{item.temperature_c:.2f}",
            f"{item.vent_kmh:.2f}",
            f"{item.precipitations_mm:.1f}",
        )

    console.print("\n[bold cyan]Croisement régional Consommation & Météo[/bold cyan]")
    console.print(table)


def executer_analyse() -> None:
    console.print(
        Panel.fit(
            "[bold white]OBSERVATOIRE ÉNERGÉTIQUE QC — ANALYSE[/bold white]\n"
            "[cyan]Statistiques, croisement régional & graphiques (420-C71-BB)[/cyan]",
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )

    racine_projet = Path(__file__).resolve().parent
    dossier_sortie = racine_projet / "donnees" / "sortie"
    dossier_figures = dossier_sortie / "figures"

    analyseur = AnalyseurEnergie(dossier_entree=dossier_sortie, dossier_figures=dossier_figures)
    datasets = analyseur.charger_datasets()

    if not datasets:
        console.print("[yellow]Aucun fichier *_propre.csv trouvé dans donnees/sortie.[/yellow]")
        return

    for nom, df in datasets.items():
        console.print(f"\n[bold cyan]Catégorie : {nom}[/bold cyan] ([bold]{len(df)}[/bold] ligne(s))")
        if nom == "web_scraping":
            _afficher_apercu_scraping(df)
            continue

        resume = analyseur.resume_numerique(df)
        if not resume.empty:
            resume_aff = resume.reset_index().rename(columns={"index": "stat"})
            console.print(_df_vers_table(f"Stats — {nom}", resume_aff))

    df_croise = analyseur.croiser_conso_meteo(datasets, sauvegarder_csv=True)
    if not df_croise.empty:
        _afficher_synthese_regionale(df_croise)

    figures = analyseur.generer_graphiques(datasets)
    console.print("\n[bold cyan]Graphiques générés[/bold cyan]")
    for cle, chemin in figures.items():
        console.print(
            f"  [bold green]OK[/bold green]  {cle:<16} "
            f"[dim]|[/dim] {chemin.parent.name}/{chemin.name}"
        )


if __name__ == "__main__":
    executer_analyse()