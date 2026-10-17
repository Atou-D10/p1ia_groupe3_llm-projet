# p1ia_groupe3_llm-projet : Assistant RAG sur <À COMPLÉTER : thème du corpus>

Activité pratique « LLM & Écosystème » : Groupe 3, filière P1 IA.

Assistant capable de répondre en français à des questions sur un corpus de documents publics, en **citant les passages utilisés**, puis d'**évaluer** la qualité de ses réponses (fidélité au corpus, pertinence des passages retrouvés).

**Membres du groupe** : Adama Sarr, Maimouna Diallo, Fallou Mbaye, Fatou Fall, Atou Diagne

## Sommaire
1. [Fonctionnalités](#fonctionnalités)
2. [Corpus](#corpus)
3. [Prérequis](#prérequis)
4. [Installation](#installation)
5. [Lancer le projet](#lancer-le-projet)
6. [Structure du projet](#structure-du-projet)
7. [Choix techniques](#choix-techniques)
8. [Évaluation](#évaluation)
9. [Fonctionnalités avancées](#fonctionnalités-avancées)
10. [Limites connues](#limites-connues)
11. [Sources et références](#sources-et-références)

## Fonctionnalités

**Socle obligatoire**
- **Pipeline RAG** : découpage des documents, embeddings, base vectorielle, génération de la réponse avec indication des passages utilisés.
- **Évaluation** : jeu d'une vingtaine de questions avec réponses de référence, mesure de la fidélité au corpus et de la pertinence des passages retrouvés.

**Pour aller plus loin**
- **Function calling** : <À COMPLÉTER : fonction(s) disponibles, ex. calcul, recherche structurée>.
- **Observabilité** : trace de chaque requête (latence, tokens, coût) dans `logs/traces.jsonl` <ou outil choisi>.
- **Garde-fous** : <À COMPLÉTER : cas gérés, ex. question hors sujet, injection de prompt, données personnelles>.

## Corpus

- **Choix** : <À COMPLÉTER : type de documents et pourquoi ce corpus>
- **Langue** : français
- **Volume** : <nombre de documents> documents, <nombre de chunks> chunks
- **Licences** : voir [`SOURCES.md`](SOURCES.md) et `data/sources.csv`
- Le corpus est **public uniquement** : aucune donnée personnelle, confidentielle ou interne à une entreprise.

## Prérequis

- **Python 3.12** (3.11 fonctionne aussi ; évitez 3.13 et plus, certaines dépendances n'y sont pas encore disponibles)
- Une **clé API gratuite Groq** : https://console.groq.com
- Environ 2 Go d'espace disque (PyTorch et le modèle d'embeddings sont volumineux)
- Aucun budget nécessaire

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/Atou-D10/p1ia_groupe3_llm-projet.git
cd p1ia_groupe3_llm-projet

# 2. Créer et activer l'environnement virtuel
python -m venv .venv
# Windows (PowerShell) :
.venv\Scripts\Activate.ps1
# Linux / macOS :
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer la clé API
# Windows : Copy-Item .env.example .env
# Linux / macOS : cp .env.example .env
# puis ouvrir .env et renseigner GROQ_API_KEY
```

> Sous PowerShell, si l'activation du venv est bloquée :
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### Variables d'environnement (`.env`)

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `GROQ_API_KEY` | Clé API du LLM (obligatoire) | *(vide)* |
| `LLM_MODEL` | Modèle utilisé pour générer les réponses | `llama-3.3-70b-versatile` |
| `TOP_K` | Nombre de passages récupérés par question | `4` |
| `MIN_SCORE` | Seuil de similarité : en dessous, la question est jugée hors corpus | `0.25` |

Si l'appel au LLM échoue avec « model not found », vérifiez la liste actuelle des modèles sur la console Groq et mettez à jour `LLM_MODEL`.

## Lancer le projet

À exécuter **depuis la racine du projet**, venv activé, dans cet ordre :

```bash
# 1. Collecte des documents -> data/raw/ et data/sources.csv
python -m src.collect

# 2. Nettoyage et découpage -> data/processed/chunks.jsonl
python -m src.chunking

# 3. Embeddings et base vectorielle -> chroma_db/
python -m src.index

# 4. Poser une question (sans argument : mode interactif)
python -m src.cli "Votre question ici"

# 5. Lancer l'évaluation -> reports/eval_results.csv
python -m src.evaluate
```

Les étapes 1 à 3 ne se lancent qu'une fois (ou quand le corpus change). Les traces de chaque requête sont écrites dans `logs/traces.jsonl`.

## Structure du projet

```
p1ia_groupe3_llm-projet/
├── README.md
├── SOURCES.md                 # sources, licences, outils et modèles utilisés
├── requirements.txt
├── .env.example               # modèle de configuration (sans clé)
├── .gitignore
├── data/
│   ├── raw/                   # documents bruts collectés
│   ├── processed/             # chunks.jsonl
│   ├── eval/                  # questions.jsonl (questions + réponses de référence)
│   └── sources.csv            # titre, url, licence, date d'accès
├── src/
│   ├── config.py              # chemins et constantes partagées
│   ├── collect.py             # collecte du corpus
│   ├── chunking.py            # nettoyage et découpage
│   ├── index.py               # embeddings + base vectorielle
│   ├── retrieve.py            # recherche des passages
│   ├── pipeline.py            # pipeline RAG complet avec sources
│   ├── cli.py                 # interface en ligne de commande (démo)
│   ├── evaluate.py            # évaluation
│   ├── tools.py               # function calling
│   ├── observability.py       # traces : latence, tokens, coût
│   └── guardrails.py          # garde-fous
├── reports/
│   ├── rapport.md             # rapport final
│   └── eval_results.csv       # résultats détaillés (généré)
├── logs/                      # traces.jsonl (généré)
└── notebooks/                 # exploration (optionnel)
```

### Formats de données partagés

- **Chunk** (une ligne JSON dans `data/processed/chunks.jsonl`) :
  `{"id": "...", "texte": "...", "titre": "...", "source": "<url ou fichier>"}`
- **Question d'évaluation** (une ligne JSON dans `data/eval/questions.jsonl`) :
  `{"question": "...", "reference": "...", "source_attendue": "...", "type": "factuelle|comparaison|hors_corpus|piege"}`
- **Collection vectorielle** : `ml_fr` <À ADAPTER si renommée dans `config.py`>

## Choix techniques

| Composant | Choix | Justification |
|---|---|---|
| Embeddings | <À COMPLÉTER : ex. `paraphrase-multilingual-MiniLM-L12-v2`> | <ex. multilingue, léger, gratuit, tourne sur CPU> |
| Base vectorielle | <À COMPLÉTER : ex. ChromaDB> | <ex. locale, aucune installation serveur> |
| LLM | <À COMPLÉTER : ex. Llama 3.3 70B via Groq> | <ex. open source, bon en français, API gratuite, function calling> |
| Découpage | <taille> caractères, chevauchement <valeur> | <À COMPLÉTER> |
| Observabilité | <À COMPLÉTER> | <À COMPLÉTER> |

## Évaluation

- **Jeu de test** : <20> questions dans `data/eval/questions.jsonl`, avec réponse de référence rédigée à partir du corpus avant de lancer le système. Types : factuelles, comparaisons, hors corpus, pièges.
- **Pertinence des passages retrouvés** : <À COMPLÉTER : hit@k, MRR>
- **Qualité des réponses** : <À COMPLÉTER : exactitude et fidélité au corpus, méthode de notation>
- **Résultats** : <À COMPLÉTER : tableau récapitulatif ou renvoi vers `reports/rapport.md`>

Le détail question par question est dans `reports/eval_results.csv`. L'analyse des erreurs est dans `reports/rapport.md`.

## Fonctionnalités avancées

### Function calling
<À COMPLÉTER : fonction(s) exposée(s) au modèle, exemple de question qui la déclenche>

### Observabilité
<À COMPLÉTER : outil utilisé, informations tracées, exemple de ligne de `logs/traces.jsonl`, latences et coûts moyens observés>

### Garde-fous
<À COMPLÉTER : cas gérés (hors sujet, injection de prompt, données personnelles), comportement du système, exemples testés>

## Limites connues

<À COMPLÉTER à partir de l'analyse des erreurs. Pistes :>
- <limites du corpus : taille, style, couverture>
- <cas où la récupération échoue ou ramène des passages hors sujet>
- <cas où le modèle répond au-delà des passages fournis>
- <sensibilité du seuil `MIN_SCORE` et des paramètres de découpage>
- <ce que nous changerions avec plus de temps>

## Sources et références

Liste complète des documents du corpus, avec URL, licence et date d'accès : [`SOURCES.md`](SOURCES.md) et `data/sources.csv`.

Outils et bibliothèques : <À COMPLÉTER : sentence-transformers, ChromaDB, Groq, etc., avec liens>.
