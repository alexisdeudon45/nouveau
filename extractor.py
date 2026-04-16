"""Extrait les informations clés d'un CV PDF vers un dict structuré."""
import json
import re
import fitz  # pymupdf
import anthropic


def pdf_to_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)


def extract_cv(pdf_path: str, client: anthropic.Anthropic) -> dict:
    raw_text = pdf_to_text(pdf_path)

    prompt = f"""Extrais les informations suivantes de ce CV et retourne UNIQUEMENT un JSON valide, sans texte autour.

Champs attendus :
- name (string)
- job_title (string) : le métier principal / poste recherché
- skills (list[string]) : toutes les compétences techniques
- city (string | null) : ville actuelle du candidat
- experience_years (int | null) : années d'expérience estimées

CV :
{raw_text}

Réponds uniquement avec le JSON."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)
