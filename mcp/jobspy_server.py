"""
Serveur MCP JobSpy — Méthode Cerise Modulaire
Expose search_jobs comme tool MCP et jobs://latest-summary comme resource.
Lancement : python -m mcp.jobspy_server (stdio transport)
"""
import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from mcp.server.fastmcp import FastMCP
from jobspy import scrape_jobs

# ── État partagé entre calls ──────────────────────────────────
_latest_df: pd.DataFrame = pd.DataFrame()

# ── Serveur FastMCP ───────────────────────────────────────────
mcp = FastMCP(
    name="jobspy",
    instructions=(
        "Serveur de recherche d'offres d'emploi. "
        "Utilise search_jobs pour lancer une recherche, "
        "puis jobs://latest-summary pour consulter les résultats."
    ),
)

REMOTE_KEYWORDS = {"remote", "télétravail", "teletravail", "distanciel", "anywhere"}


def _filter_location(df: pd.DataFrame, city: str | None) -> pd.DataFrame:
    if df.empty or not city:
        return df

    def valid(row) -> bool:
        loc = str(row.get("location", "") or "").lower()
        if not loc or loc in ("nan", "none", ""):
            return False
        return not any(k in loc for k in REMOTE_KEYWORDS)

    return df[df.apply(valid, axis=1)].reset_index(drop=True)


def _serialize(df: pd.DataFrame) -> list[dict]:
    records = []
    for _, row in df.iterrows():
        record = {}
        for k, v in row.items():
            if pd.isna(v) if not isinstance(v, (list, dict)) else False:
                record[k] = None
            elif hasattr(v, "isoformat"):
                record[k] = v.isoformat()
            else:
                record[k] = v
        records.append(record)
    return records


# ── TOOL : search_jobs ────────────────────────────────────────

@mcp.tool()
def search_jobs(
    search_term: str,
    location: str = "France",
    results_wanted: int = 10,
    hours_old: int = 168,
    job_type: Optional[str] = None,
    is_remote: bool = False,
    min_salary: Optional[int] = None,
) -> str:
    """
    Recherche des offres d'emploi sur Indeed et LinkedIn.
    Applique un filtre géographique strict (exclut les offres sans ville définie).
    Retourne un JSON avec la liste des offres triées par pertinence.
    """
    global _latest_df

    df = scrape_jobs(
        site_name=["indeed", "linkedin"],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        job_type=job_type,
        is_remote=is_remote,
        country_indeed="France",
    )

    df = _filter_location(df, location)

    if min_salary and not df.empty and "min_amount" in df.columns:
        df = df[df["min_amount"].fillna(0) >= min_salary]

    _latest_df = df

    if df.empty:
        return json.dumps({"count": 0, "jobs": [], "message": "Aucune offre trouvée après filtrage."})

    jobs = _serialize(df[["title", "company", "location", "date_posted", "job_url",
                            "min_amount", "max_amount", "description"]
                         ].head(results_wanted))

    return json.dumps({"count": len(jobs), "jobs": jobs}, ensure_ascii=False, indent=2)


# ── RESOURCE : jobs://latest-summary ─────────────────────────

@mcp.resource("jobs://latest-summary")
def get_job_summary() -> str:
    """Tableau Markdown des offres issues de la dernière recherche."""
    if _latest_df.empty:
        return "Aucune recherche effectuée. Appelez d'abord `search_jobs`."

    cols = ["title", "company", "location", "date_posted", "job_url"]
    existing = [c for c in cols if c in _latest_df.columns]
    subset = _latest_df[existing].head(20)

    lines = ["| Poste | Entreprise | Ville | Date | Lien |",
             "|-------|------------|-------|------|------|"]
    for _, row in subset.iterrows():
        url = row.get("job_url", "")
        link = f"[voir]({url})" if url else "N/A"
        lines.append(
            f"| {row.get('title','N/A')} "
            f"| {row.get('company','N/A')} "
            f"| {row.get('location','N/A')} "
            f"| {str(row.get('date_posted',''))[:10]} "
            f"| {link} |"
        )

    return "\n".join(lines)


# ── RESOURCE : jobs://results/{search_term} ───────────────────

@mcp.resource("jobs://results/{search_term}")
def get_jobs_by_term(search_term: str) -> str:
    """Retourne en JSON les offres mémorisées pour un terme donné."""
    if _latest_df.empty:
        return json.dumps({"error": "Aucune donnée disponible."})

    filtered = _latest_df[
        _latest_df["title"].str.contains(search_term, case=False, na=False)
    ] if "title" in _latest_df.columns else _latest_df

    return json.dumps({"count": len(filtered), "jobs": _serialize(filtered)},
                      ensure_ascii=False, indent=2)


# ── PROMPT : job_search_assistant ────────────────────────────

@mcp.prompt(title="Assistant Recherche Emploi")
def job_search_assistant(job_title: str, city: str, skills: str) -> str:
    """Génère une requête de recherche optimisée à partir du profil candidat."""
    return (
        f"Tu es un agent de recrutement expert. "
        f"Recherche des offres pour un profil '{job_title}' basé à '{city}' "
        f"avec les compétences : {skills}.\n"
        f"Utilise l'outil search_jobs avec les paramètres optimaux pour ce profil. "
        f"Ensuite affiche les résultats via jobs://latest-summary."
    )


# ── Entrée stdio ──────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
