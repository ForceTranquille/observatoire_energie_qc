"""TP collecte de données – Hydro-Québec (420-C71-BB) — Approche 1 : programmation Python.

Le script suit les numéros de l'énoncé, comme l'exemple de Hafed Benteftifa :

  1. Description du processus (workflow)      6. API : production/consommation + demande.json
  2. Configuration                            7. API : pannes en cours (sous réserve de robots.txt)
  3. Politique du site : robots.txt           8. Exploration des DataFrames
  4. Web scraping (requests + BeautifulSoup)  9. Export CSV
  5. API : catalogue des jeux de données     10. Approche 2 : outil / agent IA (voir docs/)

Usage :  python tp_collecte_hydroquebec.py            (pauses aléatoires de 13/15/18 s)
         python tp_collecte_hydroquebec.py --sans-pause   (développement seulement)
"""
import argparse
import json
import logging
import random
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # graphiques enregistrés en fichier (pas de fenêtre)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import requests  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

from collecte.demande_hq_collecteur import DemandeHQCollecteur  # noqa: E402
from collecte.robots import charger_robots  # noqa: E402
from collecte.web_scraping_collecteur import WebScrapingCollecteur  # noqa: E402

logger = logging.getLogger("tp_collecte")

# ========== 1. Description du processus (workflow) ==========
WORKFLOW = """\
Besoin (domaine : énergie et pannes au Québec)
  -> Politique du site (robots.txt)  --refus-->  documenter et NE PAS collecter
  -> Collecte : scraping (pause 13/15/18 s) | API Explore | JSON ouvert | pannes
  -> Représentation : DataFrame pandas
  -> Exploration : info / describe / graphiques
  -> Export CSV
(diagramme complet : docs/workflow.md)
"""

# ========== 2. Configuration ==========
HEADERS = {"User-Agent": "TP-collecte-donnees-BdB/1.0 (usage pédagogique)"}
SITE = "https://www.hydroquebec.com"
PAGE = SITE + "/documents-donnees/donnees-ouvertes/"
SITE_DONNEES = "https://donnees.hydroquebec.com"
API = SITE_DONNEES + "/api/explore/v2.1"
DATASET = "historique-production-consommation-ec-horaire"
PANNES = "https://pannes.hydroquebec.com/pannes/donnees/v3_0"
DELAIS_ALEATOIRES = WebScrapingCollecteur.DELAIS_AUTORISES  # (13, 15, 18) secondes

DOSSIER_SORTIE = Path(__file__).resolve().parent / "donnees" / "tp"


def pause_aleatoire(
    sleeper: Callable[[float], None] = time.sleep,
    choisir: Callable = random.choice,
) -> int:
    """Pause de politesse : 13 s, 15 s ou 18 s tirées au hasard."""
    delai = choisir(DELAIS_ALEATOIRES)
    logger.info("Pause aléatoire de %s s", delai)
    sleeper(delai)
    return delai


# ========== 3. Politique du site : robots.txt ==========
def verifier_robots(urls: List[str]) -> Dict[str, bool]:
    """Pour chaque URL : lit robots.txt de son hôte et indique si la collecte est permise."""
    verdicts: Dict[str, bool] = {}
    vus: Dict[str, object] = {}
    for url in urls:
        base = "/".join(url.split("/")[:3])
        if base not in vus:
            vus[base] = charger_robots(base, HEADERS["User-Agent"])
        rp, code = vus[base]
        verdicts[url] = rp.can_fetch(HEADERS["User-Agent"], url)
        print(f"  robots.txt {base} -> HTTP {code} | {url} : "
              f"{'autorisé' if verdicts[url] else 'REFUSÉ'}")
    return verdicts


# ========== 4. Web scraping – page « Données ouvertes » ==========
def extraire_liens(html: str, base_url: str) -> pd.DataFrame:
    """Liens situés sous chaque titre h2/h3 de la page (section, texte, url)."""
    soup = BeautifulSoup(html, "html.parser")
    lignes = []
    for h in soup.find_all(["h2", "h3"]):
        titre = h.get_text(" ", strip=True)
        if not titre:
            continue
        for sib in h.find_all_next():
            if sib.name in ("h2", "h3"):
                break
            if sib.name == "a" and sib.get("href"):
                lignes.append({
                    "section": titre,
                    "lien_texte": sib.get_text(" ", strip=True),
                    "url": requests.compat.urljoin(base_url, sib["href"]),
                })
    colonnes = ["section", "lien_texte", "url"]
    return pd.DataFrame(lignes, columns=colonnes).drop_duplicates()


def scraper_page_donnees_ouvertes() -> pd.DataFrame:
    reponse = requests.get(PAGE, headers=HEADERS, timeout=30)
    reponse.raise_for_status()
    return extraire_liens(reponse.text, PAGE)


# ========== 5-6. API Explore v2.1 ==========
def get_json(url: str, params: Optional[dict] = None, retries: int = 3,
             sleeper: Callable[[float], None] = time.sleep) -> dict:
    """GET JSON avec nouvel essai espacé (2^i s) si le serveur répond 429."""
    for i in range(retries):
        r = requests.get(url, params=params, headers=HEADERS, timeout=60)
        if r.status_code == 429:
            sleeper(2 ** i)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Échec après plusieurs essais : " + url)


def collecter_catalogue() -> pd.DataFrame:
    cat = get_json(f"{API}/catalog/datasets", {"limit": 100, "select": "dataset_id,metas"})
    print("Nombre de jeux de données :", cat["total_count"])
    return pd.DataFrame([
        {"dataset_id": d["dataset_id"],
         "titre": d["metas"]["default"].get("title"),
         "modifie": d["metas"]["default"].get("modified"),
         "nb_records": d["metas"]["default"].get("records_count")}
        for d in cat["results"]])


def fetch_records(dataset: str, max_rows: int = 2000, page: int = 100,
                  sleeper: Callable[[float], None] = time.sleep, **params) -> pd.DataFrame:
    """Pagination : 100 lignes par requête au plus (offset + limit <= 10 000)."""
    out: list = []
    offset = 0
    while offset < max_rows:
        data = get_json(f"{API}/catalog/datasets/{dataset}/records",
                        {"limit": min(page, max_rows - offset), "offset": offset, **params})
        lot = data["results"]
        if not lot:
            break
        out += lot
        offset += len(lot)
        if offset >= data["total_count"]:
            break
        sleeper(0.3)  # politesse envers le serveur
    return pd.DataFrame(out)


def collecter_production_consommation(max_rows: int = 2000):
    """Colonnes découvertes via les métadonnées (on ne les devine pas)."""
    meta = get_json(f"{API}/catalog/datasets/{DATASET}")
    champs = pd.DataFrame(meta["fields"])[["name", "type", "label"]]
    col_date = next(f["name"] for f in meta["fields"] if f["type"] in ("datetime", "date"))
    df = fetch_records(DATASET, max_rows=max_rows, order_by=f"{col_date} desc")
    df[col_date] = pd.to_datetime(df[col_date], utc=True)
    return df.sort_values(col_date).reset_index(drop=True), col_date, champs


def collecter_demande_json() -> pd.DataFrame:
    """JSON ouvert de la demande du Québec (pas de 15 min) via le collecteur du pipeline."""
    evenements = DemandeHQCollecteur("TP_Demande_JSON").extraire()
    df = pd.DataFrame([e.donnees for e in evenements])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


# ========== 7. Pannes en cours (JSON) – seulement si robots.txt le permet ==========
def to_lonlat(v):
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            return (None, None)
    return tuple(v[:2]) if isinstance(v, (list, tuple)) and len(v) >= 2 else (None, None)


def collecter_pannes() -> pd.DataFrame:
    version = requests.get(f"{PANNES}/bisversion.json", headers=HEADERS, timeout=30).text.strip().strip('"')
    raw = requests.get(f"{PANNES}/bismarkers{version}.json", headers=HEADERS, timeout=30).json()
    cols = ["clients_touches", "debut", "fin_estimee", "type", "localisation",
            "statut_equipe", "inutilise", "code_cause", "id_municipalite", "id_message"]
    df = pd.DataFrame(raw["pannes"]).iloc[:, :len(cols)]
    df.columns = cols[:df.shape[1]]
    df[["lon", "lat"]] = df["localisation"].apply(to_lonlat).tolist()
    df["clients_touches"] = pd.to_numeric(df["clients_touches"], errors="coerce")
    df["debut"] = pd.to_datetime(df["debut"], errors="coerce")
    return df.drop(columns=["inutilise", "localisation"])


# ========== 8. Exploration ==========
def explorer(nom: str, df: pd.DataFrame) -> None:
    print(f"\n--- {nom} : {df.shape[0]} lignes x {df.shape[1]} colonnes")
    df.info()
    print(df.describe(include="all").T.head(15))


def graphique_serie(df: pd.DataFrame, col_x: str, col_y: str, titre: str, fichier: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df[col_x], df[col_y], linewidth=1.5)
    ax.set_title(titre)
    ax.set_xlabel(col_x)
    ax.set_ylabel(col_y)
    fig.autofmt_xdate()
    fig.tight_layout()
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fichier, dpi=150)
    plt.close(fig)
    return fichier


# ========== 9. Export ==========
def exporter(dossier: Path, **frames: pd.DataFrame) -> List[Path]:
    dossier.mkdir(parents=True, exist_ok=True)
    fichiers = []
    for nom, df in frames.items():
        if df is not None and not df.empty:
            chemin = dossier / f"hq_{nom}.csv"
            df.to_csv(chemin, index=False, encoding="utf-8")
            fichiers.append(chemin)
    return fichiers


# ========== Orchestration ==========
def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sans-pause", action="store_true",
                        help="ignore les pauses de 13/15/18 s (développement seulement)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    sleeper = (lambda s: None) if args.sans_pause else time.sleep

    print("1. Workflow\n" + WORKFLOW)

    print("3. Politique du site (robots.txt)")
    verdicts = verifier_robots([PAGE, API + "/catalog/datasets", PANNES + "/bisversion.json"])

    frames: Dict[str, pd.DataFrame] = {}
    erreurs: Dict[str, str] = {}

    def essayer(nom: str, autorise: bool, fonction):
        if not autorise:
            print(f"  [SAUTÉ] {nom} : refusé par robots.txt (documenté, non collecté)")
            return None
        try:
            return fonction()
        except Exception as exc:  # une source en panne ne bloque pas les autres
            erreurs[nom] = str(exc)
            print(f"  [ERREUR] {nom} : {exc}")
            return None

    print("\n4. Web scraping")
    df_page = essayer("page_donnees_ouvertes", verdicts[PAGE], scraper_page_donnees_ouvertes)
    if df_page is not None:
        frames["page_donnees_ouvertes"] = df_page
        pause_aleatoire(sleeper)

    print("\n5. API – catalogue")
    df_cat = essayer("catalogue", verdicts[API + "/catalog/datasets"], collecter_catalogue)
    if df_cat is not None:
        frames["catalogue"] = df_cat

    print("\n6. API – production/consommation et demande.json")
    horaire = essayer("production_consommation_horaire", verdicts[API + "/catalog/datasets"],
                      collecter_production_consommation)
    col_date = None
    if horaire is not None:
        frames["production_consommation_horaire"], col_date, _ = horaire
    df_demande = essayer("demande_quebec", True, collecter_demande_json)
    if df_demande is not None:
        frames["demande_quebec"] = df_demande

    print("\n7. Pannes en cours")
    df_pannes = essayer("pannes_en_cours", verdicts[PANNES + "/bisversion.json"], collecter_pannes)
    if df_pannes is not None:
        frames["pannes_en_cours"] = df_pannes

    print("\n8. Exploration")
    for nom, df in frames.items():
        explorer(nom, df)
    figures = []
    if "demande_quebec" in frames and not frames["demande_quebec"].empty:
        figures.append(graphique_serie(frames["demande_quebec"], "date", "demande_mw",
                                       "Demande du Québec (pas de 15 min)",
                                       DOSSIER_SORTIE / "figures" / "demande_quebec.png"))

    print("\n9. Export")
    for chemin in exporter(DOSSIER_SORTIE, **frames):
        print("  ", chemin)
    for chemin in figures:
        print("  ", chemin)

    print("\n10. Approche 2 (outil / agent IA) : voir docs/approche2_agent_ia.md")
    if erreurs:
        print("\nSources en erreur :", erreurs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
