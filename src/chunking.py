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


# ----------------------------------------------------------------------
# 3. Découpage en chunks
# ----------------------------------------------------------------------
def split_text(text, max_chars, overlap):
    """Coupe un long texte vers la fin d'une phrase, avec chevauchement."""
    if len(text) <= max_chars:
        return [text]
    pieces, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            cut = max(text.rfind(". ", start, end), text.rfind("\n", start, end),
                      text.rfind("; ", start, end))
            if cut > start + max_chars // 2:
                end = cut + 1
        pieces.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        space = text.find(" ", start, end)   # repartir au début d'un mot
        if space != -1:
            start = space + 1
    return pieces


def build_chunks(articles):
    """Transforme les articles en chunks au format partagé par le groupe.

    Chaque chunk contient : id, texte (contexte + intitulé + extrait de l'article),
    titre, source et numéro d'article. Les articles longs sont scindés en plusieurs
    chunks ; le contexte (Titre > Chapitre > Section) est répété dans chacun.
    """
    chunks = []
    for a in articles:
        contexte = " > ".join(x for x in (a["titre"], a["chapitre"], a["section"]) if x)
        en_tete = f"Article {a['num']}. - {a['intitule']}"
        morceaux = split_text(a["corps"], CHUNK_MAX_CHARS, CHUNK_OVERLAP)
        for k, morceau in enumerate(morceaux, start=1):
            suffixe = f" (partie {k}/{len(morceaux)})" if len(morceaux) > 1 else ""
            chunks.append({
                "id": f"art-{a['num']:03d}" + (f"-{k}" if len(morceaux) > 1 else ""),
                "texte": f"{contexte}\n{en_tete}{suffixe}\n{morceau}",
                "titre": f"Article {a['num']} - {a['intitule']}",
                "source": f"{SOURCE_LABEL}, article {a['num']}",
                "article": a["num"],
            })
    return chunks


# ----------------------------------------------------------------------
# 4. Programme principal
# ----------------------------------------------------------------------
def main():
    """Enchaîne tout le traitement : nettoyage, détection des articles, découpage,
    puis écrit les chunks dans data/processed/chunks.jsonl (une ligne JSON par chunk).
    Affiche un contrôle : nombre d'articles, articles manquants, longueur des chunks.
    """
    text = clean(RAW_TEXT_PATH.read_text(encoding="utf-8"))
    articles = parse_articles(text)
    chunks = build_chunks(articles)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    numeros = [a["num"] for a in articles]
    manquants = sorted(set(range(1, max(numeros) + 1)) - set(numeros))
    longueurs = [len(c["texte"]) for c in chunks]
    print(f"{len(articles)} articles détectés (attendu : 462), manquants : {manquants or 'aucun'}")
    print(f"{len(chunks)} chunks écrits dans {CHUNKS_PATH}")
    print(f"longueur des chunks : min {min(longueurs)}, "
          f"moyenne {sum(longueurs) // len(longueurs)}, max {max(longueurs)}")


if __name__ == "__main__":
    main()