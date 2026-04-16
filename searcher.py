"""Recherche des offres d'emploi via JobSpy."""
import pandas as pd
from jobspy import scrape_jobs


REMOTE_KEYWORDS = {"remote", "télétravail", "teletravail", "distanciel", "anywhere"}


def search_jobs(job_title: str, city: str | None, results: int = 15) -> pd.DataFrame:
    location = city if city else "France"

    df = scrape_jobs(
        site_name=["indeed", "linkedin"],
        search_term=job_title,
        location=location,
        results_wanted=results,
        country_indeed="France",
        hours_old=168,  # 7 jours
    )

    if df.empty:
        return df

    # Filtre géographique : exclure si ville absente ou remote uniquement
    def is_valid_location(row) -> bool:
        loc = str(row.get("location", "") or "").lower()
        if not loc or loc in ("nan", "none", ""):
            return False
        if any(k in loc for k in REMOTE_KEYWORDS) and city:
            return False
        return True

    df = df[df.apply(is_valid_location, axis=1)].reset_index(drop=True)
    return df
