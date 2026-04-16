"""Valide le domaine d'une offre via zero-shot classification HuggingFace."""
from huggingface_hub import InferenceClient

CANDIDATE_LABELS = [
    "data engineering",
    "software development",
    "data science",
    "devops / infrastructure",
    "project management",
    "marketing",
    "finance",
    "human resources",
    "sales",
    "design",
]


def classify_job(description: str, client: InferenceClient, top_n: int = 1) -> list[dict]:
    if not description or len(description.strip()) < 20:
        return [{"label": "unknown", "score": 0.0}]

    # tronquer à 500 chars pour rester dans les limites de l'API gratuite
    text = description[:500]

    result = client.zero_shot_classification(
        text=text,
        candidate_labels=CANDIDATE_LABELS,
        model="typeform/distilbert-base-uncased-mnli",
    )

    return [{"label": item.label, "score": round(item.score, 4)} for item in result[:top_n]]
