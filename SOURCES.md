# Sources et références

La liste automatique des documents du corpus est dans `data/sources.csv`
(titre, URL, licence, date d'accès).

## Corpus

| Source | Détail |
|---|---|
| Document | Loi n° 2026-18 du 03 septembre 2026 portant Code du Travail |
| Publication | Journal officiel de la République du Sénégal, n° 7931 (numéro spécial), 17 septembre 2026 |
| Fichier local | `data/raw/code_travail_loi_2026-18.pdf` (72 pages, texte extractible) |
| Contenu | 462 articles répartis en 15 titres |
| Langue | Français |
| Licence | Texte officiel publié au Journal officiel ; conditions de réutilisation non vérifiées |
| Lien d'origine | https://dgtss.gouv.sn/lois/ |

## Fichiers dérivés (générés par le code)

- `data/raw/code_travail.txt` : texte brut extrait du PDF (`python -m src.collect`), non versionné
- `data/processed/chunks.jsonl` : 524 chunks, un par article, les articles longs étant scindés (`python -m src.chunking`)

## Outils (partie 1)

- PyMuPDF : extraction du texte du PDF (version : 1.28.2)
- Python 3.12, bibliothèques standard `re` et `json`

## Modèles et outils des autres parties

<À COMPLÉTER par les parties 2 à 5 : modèle d'embeddings, base vectorielle, LLM, outil d'observabilité>