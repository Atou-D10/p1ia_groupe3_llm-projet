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

# Fragments après un trait d'union de fin de ligne qui doivent GARDER le trait d'union
# (ex. « ceux-ci », « main-d'œuvre », « peut-il »).
HYPHEN_KEEP = (r"(?:d'|l'|qu'|ci\b|là\b|il\b|ils\b|elle\b|elles\b|on\b|t-|"
               r"même|nous\b|vous\b|je\b|tu\b|delà\b)")


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
    # mots coupés en fin de ligne : « syn-\ndicale » -> « syndicale »
    text = re.sub(r"(?<=[A-Za-zÀ-ÿ])-\n(?=" + HYPHEN_KEEP + ")", "-", text)
    text = re.sub(r"(?<=[A-Za-zÀ-ÿ])-\n(?=[a-zàâäéèêëîïôöûùüç])", "", text)
    return text.strip()


# ----------------------------------------------------------------------
# 2. Détection des articles
# ----------------------------------------------------------------------
# Accepte « Article 12. - », « Article 109 - » (sans point) et « Art. 49. - ».
RE_ARTICLE = re.compile(r"^Art(?:icle|\.)\s+(premier|\d+)\.?\s+-\s+(.*)$")


# ----------------------------------------------------------------------
# 2. Détection des articles et de la hiérarchie (Titre > Chapitre > Section)
# ----------------------------------------------------------------------
# Accepte « Article 12. - », « Article 109 - » (sans point) et « Art. 49. - ».
RE_ARTICLE = re.compile(r"^Art(?:icle|\.)\s+(premier|\d+)\.?\s+-\s+(.*)$")
RE_TITRE = re.compile(r"^TITRE\s+\S+\.\s+-\s+")
RE_CHAPITRE = re.compile(r"^Chapitre\s+[^.]{1,25}\.\s+-\s+")
RE_SECTION = re.compile(r"^(?:Section|Sous-section)\s+[^.]{1,25}\.\s+-\s+")


def join_lines(lines):
    """Recolle les lignes visuelles du PDF en paragraphes ; garde les listes à tirets."""
    out, new_par = [], False
    for line in lines:
        if line == "-":
            new_par = True
            continue
        if new_par or line.startswith("- "):
            line = "- " + line.lstrip("- ")
            out.append("\n" + line)
        elif out:
            out.append(" " + line)
        else:
            out.append(line)
        new_par = False
    return "".join(out).strip()


def parse_articles(text):
    """Retourne la liste des articles : numéro, intitulé, lignes, titre/chapitre/section."""
    lines = text.split("\n")
    articles, cur = [], None
    titre = chapitre = section = ""
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue

        if RE_TITRE.match(line):
            # l'intitulé du titre est en majuscules et peut tenir sur plusieurs lignes
            while i < len(lines) and lines[i].strip() and lines[i].strip().isupper():
                line += " " + lines[i].strip()
                i += 1
            titre, chapitre, section, cur = line, "", "", None
        elif RE_CHAPITRE.match(line) or RE_SECTION.match(line):
            # une ligne qui commence par une minuscule prolonge l'intitulé
            while i < len(lines) and lines[i].strip() and lines[i].strip()[0].islower():
                line += " " + lines[i].strip()
                i += 1
            if RE_CHAPITRE.match(line):
                chapitre, section = line, ""
            else:
                section = line
            cur = None
        else:
            m = RE_ARTICLE.match(line)
            if m:
                num = 1 if m.group(1) == "premier" else int(m.group(1))
                cur = {"num": num, "intitule": m.group(2).strip(), "lines": [],
                       "titre": titre, "chapitre": chapitre, "section": section}
                articles.append(cur)
            elif cur is not None:
                cur["lines"].append(line)
    for a in articles:
        a["corps"] = join_lines(a.pop("lines"))
    return articles