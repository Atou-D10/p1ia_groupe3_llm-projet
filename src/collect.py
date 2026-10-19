"""Partie 1a : extraction du texte brut du PDF.

Usage : python -m src.collect
"""
import pymupdf

from src.config import PDF_PATH, RAW_TEXT_PATH


def extract_text(pdf_path):
    """Concatène le texte de toutes les pages, dans l'ordre de lecture."""
    with pymupdf.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)