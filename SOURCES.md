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

### Partie 2 : embeddings, base vectorielle, observabilité

| Outil | Rôle | Licence | Lien |
|---|---|---|---|
| intfloat/multilingual-e5-small | modèle d'embeddings (384 dimensions, 512 tokens max) | MIT | https://huggingface.co/intfloat/multilingual-e5-small |
| sentence-transformers | calcul des embeddings en local | Apache 2.0 | https://www.sbert.net |
| ChromaDB | base vectorielle locale | Apache 2.0 | https://www.trychroma.com |
| sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | modèle comparé (non retenu, tronque à 128 tokens) | Apache 2.0 | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| Traces maison (`src/observability.py`) | observabilité : une ligne JSON par requête dans `logs/traces.jsonl` | — | — |

Référence : Wang et al., *Multilingual E5 Text Embeddings: A Technical Report*, 2024, arXiv:2402.05672.


## Modèles et outils des autres parties
<À COMPLÉTER par les parties 3 à 5 : LLM, function calling, garde-fous>



