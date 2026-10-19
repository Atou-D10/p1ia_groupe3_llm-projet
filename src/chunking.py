"""Partie 1b : nettoyage, détection des articles et découpage en chunks.

Usage : python -m src.chunking
"""
import json
import re

from src.config import (CHUNK_MAX_CHARS, CHUNK_OVERLAP, CHUNKS_PATH,
                        RAW_TEXT_PATH, SOURCE_LABEL)

# ----------------------------------------------------------------------
# 1. Nettoyage
# ----------------------------------------------------------------------


def clean(text):
    # numéros de page (ligne de 4 chiffres), en-tête du JO répété, date répétée
    text = re.sub(r"(?m)^\d{4}\s*$", "", text)
    text = re.sub(r"(?m)^JOURNAL OFFICIEL DE LA REPUBLIQUE DU SENEGAL\s*$", "", text)
    text = re.sub(r"(?m)^17\s+septembre\s+2026\s*$", "", text)
    # lignes de la couverture qui se retrouvent au milieu du texte (page 1 du PDF)
    text = re.sub(r"(?m)^\s*JEUDI\s+17\s+SEPTEMBRE\s+2026\s*$", "", text)
    text = re.sub(r"(?m)^\s*NUMERO\s+SPECIAL\s*$", "", text)
    # espaces et lignes vides
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()