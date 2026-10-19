"""Partie 1a : extraction du texte brut du PDF.

Usage : python -m src.collect
"""
import pymupdf

from src.config import PDF_PATH, RAW_TEXT_PATH


def extract_text(pdf_path):
    """Concatène le texte de toutes les pages, dans l'ordre de lecture."""
    with pymupdf.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)

# La page 1 du PDF mêle la couverture du Journal officiel (abonnements, sommaire)
# et le début de la loi : on coupe donc sur des repères de texte, pas sur les pages.
START_MARKER = "TITRE PREMIER"
END_MARKER = "Fait Dakar, le 03 septembre 2026"


def keep_law_only(text):
    """Supprime la couverture du JO (avant le titre I) et la signature (après l'article 462)."""
    start = text.index(START_MARKER)
    end = text.index(END_MARKER)
    return text[start:end]