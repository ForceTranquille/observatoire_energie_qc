from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt
import pandas as pd


class AnalyseurEnergie:
    """Charge les CSV propres, calcule des indicateurs et génère des graphiques."""

    def __init__(self, dossier_entree: Path, dossier_figures: Path):
        self._dossier_entree = Path(dossier_entree)
        self._dossier_figures = Path(dossier_figures)
        self._dossier_figures.mkdir(parents=True, exist_ok=True)

    def charger_datasets(self) -> Dict[str, pd.DataFrame]:
        datasets: Dict[str, pd.DataFrame] = {}
        for nom in ("meteo", "consommation", "demande_quebec", "pannes", "pannes_en_cours", "alerte"):
            fichier = self._dossier_entree / f"{nom}_propre.csv"
            if fichier.exists():
                datasets[nom] = pd.read_csv(fichier)
        return datasets

    def resume_numerique(self, df: pd.DataFrame) -> pd.DataFrame:
        cols_num = df.select_dtypes(include="number").columns.tolist()
        if not cols_num:
            return pd.DataFrame()
        return df[cols_num].agg(["count", "mean", "median", "min", "max", "std"]).round(2)

    def croiser_conso_meteo(
        self, datasets: Dict[str, pd.DataFrame], sauvegarder_csv: bool = True
    ) -> pd.DataFrame:
        df_conso = datasets.get("consommation")
        df_meteo = datasets.get("meteo")
        if df_conso is None or df_meteo is None:
            return pd.DataFrame()

        df_conso_reg = (
            df_conso.groupby("region", as_index=False)["demande_mw"]
            .mean()
            .rename(columns={"demande_mw": "demande_mw_moy"})
        )

        cols_meteo = [c for c in ("temperature_c", "vent_kmh", "precipitations_mm") if c in df_meteo.columns]
        df_meteo_reg = (
            df_meteo.groupby("region", as_index=False)[cols_meteo]
            .mean()
            .rename(columns={c: f"{c}_moy" for c in cols_meteo})
        )

        df_croise = pd.merge(df_conso_reg, df_meteo_reg, on="region", how="outer").round(2)
        if sauvegarder_csv and not df_croise.empty:
            df_croise.to_csv(
                self._dossier_entree / "croisement_conso_meteo.csv",
                index=False,
                encoding="utf-8",
            )
        return df_croise

    def generer_graphiques(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Path]:
        figures: Dict[str, Path] = {}

        # 1. Demande moyenne (MW) par région
        df_conso = datasets.get("consommation")
        if df_conso is not None and {"region", "demande_mw"}.issubset(df_conso.columns):
            fig, ax = plt.subplots(figsize=(7, 4))
            conso_reg = df_conso.groupby("region")["demande_mw"].mean().sort_values(ascending=False)
            conso_reg.plot(kind="bar", ax=ax, color="#1f77b4")
            ax.set_title("Demande électrique moyenne par région (MW)")
            ax.set_xlabel("Région")
            ax.set_ylabel("Demande moyenne (MW)")
            ax.tick_params(axis="x", rotation=0)
            fig.tight_layout()
            chemin = self._dossier_figures / "demande_par_region.png"
            fig.savefig(chemin, dpi=150)
            plt.close(fig)
            figures["demande_region"] = chemin

        # 2. Clients touchés par panne
        df_pannes = datasets.get("pannes")
        if df_pannes is not None and {"id_panne", "clients_touches"}.issubset(df_pannes.columns):
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.bar(df_pannes["id_panne"].astype(str), df_pannes["clients_touches"], color="#d62728")
            ax.set_title("Clients touchés par identifiant de panne")
            ax.set_xlabel("ID Panne")
            ax.set_ylabel("Clients touchés")
            fig.tight_layout()
            chemin = self._dossier_figures / "clients_par_panne.png"
            fig.savefig(chemin, dpi=150)
            plt.close(fig)
            figures["clients_panne"] = chemin

        # 3. Demande du Québec au pas de 15 min (données ouvertes Hydro-Québec)
        df_qc = datasets.get("demande_quebec")
        if df_qc is not None and {"date", "demande_mw"}.issubset(df_qc.columns) and not df_qc.empty:
            serie = df_qc.assign(date=pd.to_datetime(df_qc["date"], errors="coerce"))
            serie = serie.dropna(subset=["date"]).drop_duplicates(subset=["date"]).sort_values("date")
            fig, ax = plt.subplots(figsize=(9, 4))
            ax.plot(serie["date"], serie["demande_mw"], color="#1f77b4", linewidth=1.5)
            ax.set_title("Demande électrique du Québec (pas de 15 min)")
            ax.set_xlabel("Date et heure")
            ax.set_ylabel("Demande (MW)")
            fig.autofmt_xdate()
            fig.tight_layout()
            chemin = self._dossier_figures / "demande_quebec_15min.png"
            fig.savefig(chemin, dpi=150)
            plt.close(fig)
            figures["demande_quebec"] = chemin

        # 4. Pannes en cours (données réelles d'Hydro-Québec) : 10 pannes les plus importantes
        df_reel = datasets.get("pannes_en_cours")
        if df_reel is not None and {"id_panne", "clients_touches"}.issubset(df_reel.columns) and not df_reel.empty:
            top = df_reel.dropna(subset=["clients_touches"]).drop_duplicates(subset=["id_panne"])
            top = top.nlargest(10, "clients_touches")
            fig, ax = plt.subplots(figsize=(9, 4))
            ax.barh(top["id_panne"].astype(str), top["clients_touches"], color="#d62728")
            ax.invert_yaxis()
            ax.set_title("Pannes en cours au Québec : 10 plus importantes (données réelles)")
            ax.set_xlabel("Clients touchés")
            fig.tight_layout()
            chemin = self._dossier_figures / "pannes_en_cours_top10.png"
            fig.savefig(chemin, dpi=150)
            plt.close(fig)
            figures["pannes_en_cours"] = chemin

        return figures