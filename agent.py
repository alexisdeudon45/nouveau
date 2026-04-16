"""Agent de recrutement prédictif — orchestration principale."""
import os
import sys
import anthropic
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from extractor import extract_cv
from searcher import search_jobs
from classifier import classify_job
from matcher import compute_score

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def run(pdf_path: str, max_jobs: int = 10) -> None:
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not hf_token:
        sys.exit("Erreur : HUGGINGFACE_TOKEN manquant dans .env")
    if not anthropic_key:
        sys.exit("Erreur : ANTHROPIC_API_KEY manquant dans .env")

    claude = anthropic.Anthropic(api_key=anthropic_key)
    hf = InferenceClient(token=hf_token)

    # ── 1. Extraction CV ──────────────────────────────────────────────────────
    print("[ 1/4 ] Extraction du CV...")
    cv = extract_cv(pdf_path, claude)
    print(f"        Candidat : {cv.get('name')} | Poste : {cv.get('job_title')} | Ville : {cv.get('city')}")
    print(f"        Skills   : {', '.join(cv.get('skills', [])[:8])}")

    # ── 2. Recherche d'offres ─────────────────────────────────────────────────
    print("\n[ 2/4 ] Recherche d'offres (Indeed + LinkedIn)...")
    df = search_jobs(cv.get("job_title", ""), cv.get("city"), results=max_jobs)

    if df.empty:
        print("        Aucune offre trouvée après filtrage géographique.")
        return

    print(f"        {len(df)} offre(s) retenue(s) après filtre géographique.")

    # ── 3. Classification + Matching ──────────────────────────────────────────
    print("\n[ 3/4 ] Classification NLP + calcul des scores...")

    rows = []
    for _, job in df.iterrows():
        desc = str(job.get("description") or "")
        domain_result = classify_job(desc, hf)
        domain = domain_result[0]["label"] if domain_result else "unknown"
        domain_score = domain_result[0]["score"] if domain_result else 0.0
        match_score = compute_score(cv.get("skills", []), desc)

        rows.append({
            "score":    f"{match_score*100:.0f}%",
            "poste":    str(job.get("title", "N/A")),
            "entreprise": str(job.get("company", "N/A")),
            "ville":    str(job.get("location", "N/A")),
            "domaine":  f"{domain} ({domain_score*100:.0f}%)",
            "lien":     str(job.get("job_url", "")),
        })

    # ── 4. Tri et affichage ───────────────────────────────────────────────────
    print("\n[ 4/4 ] Résultats\n")
    rows.sort(key=lambda r: r["score"], reverse=True)

    header = "| Score | Poste | Entreprise | Ville | Domaine (HF) | Lien |"
    sep    = "|-------|-------|------------|-------|--------------|------|"
    print(header)
    print(sep)
    for r in rows:
        link = f"[voir]({r['lien']})" if r["lien"] else "N/A"
        print(f"| {r['score']} | {r['poste']} | {r['entreprise']} | {r['ville']} | {r['domaine']} | {link} |")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage : python agent.py chemin/vers/cv.pdf")
    run(sys.argv[1])
