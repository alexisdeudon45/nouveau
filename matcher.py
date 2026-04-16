"""Calcule un score de pertinence CV ↔ offre basé sur les compétences."""
import re


def _normalize(text: str) -> set[str]:
    text = text.lower()
    tokens = re.findall(r"[a-zàâéèêëîïôùûüç+#.]{2,}", text)
    return set(tokens)


def compute_score(cv_skills: list[str], job_description: str) -> float:
    if not cv_skills or not job_description:
        return 0.0

    cv_tokens = set()
    for skill in cv_skills:
        cv_tokens |= _normalize(skill)

    job_tokens = _normalize(job_description)

    if not cv_tokens:
        return 0.0

    matches = cv_tokens & job_tokens
    score = len(matches) / len(cv_tokens)
    return round(min(score, 1.0), 4)
