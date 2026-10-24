# Partie 2 : embeddings, base vectorielle et observabilité

*Maimouna Diallo. Fichiers : `src/index.py`, `src/retrieve.py`, `src/observability.py`,
`notebooks/mesure_tokens.py`, `notebooks/experience_topk.py`.*

Toutes les mesures ont été faites le 24 octobre 2026 sur un PC Windows sans carte graphique
(processeur seul, Python 3.12).

## 1. Rôle de la partie

Transformer les 524 chunks du Code du Travail en vecteurs (embeddings), les ranger dans une
base vectorielle, et fournir aux autres parties :

- `retrieve(question, k=TOP_K)` : la liste des k passages les plus proches de la question,
  au format `{id, texte, titre, source, article, score}`, triés du plus au moins pertinent.
  Le score est la similarité cosinus (1 = identique) ;
- `Tracer` : un outil qui écrit une ligne JSON par question dans `logs/traces.jsonl`
  (date, durée de chaque étape, tokens, coût).

La recherche ne rédige pas de réponse : elle choisit les articles, et le LLM (partie 3)
rédige la réponse à partir d'eux.

## 2. Choix du modèle d'embeddings

**Problème signalé par la partie 1** : le modèle prévu au départ,
`paraphrase-multilingual-MiniLM-L12-v2`, ne lit que 128 tokens. Ce qui dépasse est ignoré
sans avertissement.

**Mesure** (`notebooks/mesure_tokens.py`, avec le tokenizer de chaque modèle sur les 524 chunks) :

| Modèle | Longueur max | Tokens par chunk (moy. / max) | Chunks tronqués |
|---|---|---|---|
| paraphrase-multilingual-MiniLM-L12-v2 | 128 | 190 / 358 | **393 / 524 (75 %)** |
| multilingual-e5-small | 512 | 192 / 360 | **0** |
| multilingual-e5-base | 512 | 192 / 360 | 0 |

Avec MiniLM, trois chunks sur quatre auraient été lus à moitié. Or la fin d'un article
contient souvent l'essentiel (délai, sanction, exception).

**Choix : `intfloat/multilingual-e5-small`**
- il lit nos chunks en entier ;
- il est aussi léger que MiniLM (environ 118 M de paramètres, 470 Mo) et tourne sur un PC ordinaire ;
- il a été entraîné pour la recherche de passages à partir d'une question
  (Wang et al., *Multilingual E5 Text Embeddings*, 2024, arXiv:2402.05672) ;
- il est gratuit et sous licence MIT.

e5-base n'a pas été retenu : il est plus lourd (environ 1,1 Go) et plus lent, pour un gain
non nécessaire ici (voir §5).
L'autre option, raccourcir les chunks à environ 500 caractères pour MiniLM, aurait coupé
davantage d'articles et demandé de refaire le découpage de la partie 1.

**Contrainte du modèle** : e5 exige le préfixe `"passage: "` devant les textes indexés et
`"query: "` devant les questions. C'est géré automatiquement dans `src/index.py` (`prefixes()`).

## 3. Choix de la base vectorielle : ChromaDB

| Option | Avantages | Inconvénients pour nous |
|---|---|---|
| **ChromaDB** (retenue) | installation par `pip`, aucun serveur, enregistrée sur disque (`chroma_db/`), garde les métadonnées (titre, source, article) | moins performante sur des millions de vecteurs, ce qui ne nous concerne pas (524) |
| FAISS | très rapide | simple bibliothèque de calcul : sauvegarde et métadonnées à gérer soi-même |
| Qdrant, Milvus | conçues pour la production | demandent un serveur (souvent Docker), trop lourd pour un projet que chacun doit relancer facilement |

La collection utilise la distance cosinus (`hnsw:space = cosine`), et les vecteurs sont
normalisés. L'indexation est **relançable sans doublons** : la collection est supprimée puis
recréée à chaque `python -m src.index`. Le nom du modèle est enregistré dans la collection,
et `retrieve` refuse de chercher si le modèle a changé entre-temps.

## 4. Démarche : les ajustements successifs

Le système n'a pas fonctionné du premier coup. Voici les problèmes rencontrés, comment ils ont
été détectés, et ce qui a été corrigé.

1. **Troncature** : mesurée (75 % des chunks), corrigée par le changement de modèle (§2).
2. **Base construite avec le mauvais modèle.** La première indexation a tourné alors que
   `config.py` contenait encore MiniLM. Le contrôle de cohérence de `retrieve.py` l'a détecté
   (« La base a été construite avec … »). Sans ce contrôle, les résultats auraient été faux
   sans aucun message d'erreur. Corrigé en réindexant.
3. **Seuil MIN_SCORE inadapté** : avec e5, tous les scores sont entre 0,75 et 0,91, y compris
   pour des questions hors sujet. La valeur prévue (0,25) ne filtrait donc rien (§6).
4. **Première trace à 11,7 s pour une seule recherche.** Le traçage a montré que le modèle
   était rechargé à chaque lancement, avec des tentatives de connexion répétées à Hugging Face
   sur une connexion instable. Corrigé en chargeant le modèle depuis le disque d'abord
   (`local_files_only=True`). Le projet fonctionne maintenant hors connexion après le premier
   téléchargement. Résultat : 2,9 s.
5. **Modèle chargé deux fois (bug de cache).** La trace en deux étapes montrait deux
   chargements. `@lru_cache` traitait `charger_modele()` et `charger_modele("…e5-small")` comme
   deux appels différents. Corrigé par un dictionnaire rangé par nom de modèle.
   Résultat : chargement 2,1 s, puis recherche 0,16 s.

Les points 2, 4 et 5 ont été trouvés grâce aux outils de la partie : le contrôle de cohérence
et la trace.

## 5. Expérience : modèle d'embeddings et TOP_K

**Protocole** (`notebooks/experience_topk.py`, détail dans `reports/experience_partie2.csv`) :
13 questions dont l'article attendu est connu. 6 questions sont « proches » (elles reprennent
les mots de la loi) et 7 « reformulées » (langage courant, par exemple
« Mon patron peut-il me renvoyer pendant mon congé de maternité ? »). S'y ajoutent
3 questions hors corpus. Les deux modèles sont indexés et interrogés de la même façon.
On mesure le **hit@k** (part des questions dont le bon article est dans les k premiers
passages) et le **MRR** (moyenne de 1/rang du bon article).

| Modèle | hit@1 | hit@3 | hit@4 | hit@5 | hit@10 | MRR | hit@4 proches | hit@4 reformulées |
|---|---|---|---|---|---|---|---|---|
| MiniLM | 0,54 | 0,77 | 0,77 | 0,85 | 1,00 | 0,68 | 0,83 | 0,71 |
| **e5-small** | **0,69** | **0,92** | **1,00** | **1,00** | 1,00 | **0,81** | **1,00** | **1,00** |

**Effet du modèle** : e5-small est meilleur à toutes les valeurs de k. L'écart est surtout
visible sur les questions reformulées (hit@4 : 1,00 contre 0,71). Par exemple, pour
« Mon patron peut-il me renvoyer pendant mon congé de maternité ? », l'article 277 arrive
2e avec e5, mais seulement 7e avec MiniLM.

**Effet de TOP_K** (avec e5-small) : un seul passage (k = 1) ne suffit pas, car le bon article
n'est 1er que dans 69 % des cas. Il faut **k = 4** pour retrouver le bon article dans 100 % de
nos 13 questions : avec k = 3, la question sur le harcèlement (bon article au 4e rang)
échoue. Au-delà de 4, on n'améliore plus rien sur ce jeu de questions, et on envoie plus de
texte au LLM, donc plus de tokens et de bruit. **TOP_K = 4 est donc conservé.**

## 6. Seuil MIN_SCORE (question hors corpus)

| Modèle | Plus bas meilleur score (vraies questions) | Plus haut score (hors corpus) | Marge |
|---|---|---|---|
| MiniLM | 0,56 | 0,42 | 0,14 |
| e5-small | 0,864 | 0,814 | **0,05** |

Avec e5-small, les questions hors sujet obtiennent des scores élevés : « Comment préparer un
thiéboudienne ? » obtient 0,814. Sur nos 16 questions, un seuil autour de **0,84** sépare
encore les deux groupes, mais la marge est étroite (0,05). MiniLM sépare plus nettement
(marge de 0,14), mais il retrouve moins bien les bons articles. **C'est un compromis
assumé** : on privilégie la qualité de la recherche, et le seuil doit être calibré avec soin
par la partie 4 sur ses 20 questions, dont des questions pièges. La valeur 0,25 de
`config.py` est à remplacer.

## 7. Latences et coûts mesurés

| Étape | Durée | Fréquence |
|---|---|---|
| Indexation des 524 chunks, e5-small | 38 à 40 s (environ 75 ms par chunk) | une fois, ou quand le corpus change |
| Indexation, MiniLM (pour comparer) | 19 à 23 s | — |
| Chargement du modèle | environ 2,1 s | une fois par lancement de l'application |
| Recherche d'une question | environ 30 ms (e5 et MiniLM) | à chaque question |

e5-small indexe deux fois plus lentement que MiniLM, parce qu'il lit les chunks en entier.
C'est un coût payé une seule fois. À la recherche, les deux modèles sont aussi rapides.

**Coût** : 0 $ pour les embeddings (calculés en local) et 0 $ pour le LLM (niveau gratuit de
Groq). La trace l'indique explicitement (`note_cout`). Les **tokens et la latence du LLM** sont
enregistrés par `Tracer` dès que `pipeline.py` (partie 3) l'utilise. Ils n'étaient pas
disponibles au moment de cette mesure.

## 8. Limites

- **Petit jeu de test** : 13 questions, rédigées par nous, avec un seul article attendu
  chacune. Les chiffres donnent une tendance, pas une mesure précise : une question de plus
  ou de moins change le hit@k de 8 points.
- **Seuil hors corpus fragile** avec e5 (marge de 0,05) : une question hors sujet proche du
  vocabulaire du travail (« Quel est le salaire moyen en France ? ») pourrait passer.
- **Un seul article attendu par question**, alors que certaines réponses sont réparties sur
  plusieurs articles (par exemple 277 et 280 pour la maternité).
- **Mesures sur une seule machine**, sans carte graphique : les durées varient d'un PC à l'autre.
- **Tokens et coût du LLM** non encore mesurés (ils dépendent de la partie 3).

## 9. Ce que nous changerions avec plus de temps

- Tester `multilingual-e5-base` ou `bge-m3`, plus gros, pour voir si le gain de qualité
  compense la lenteur.
- Ajouter une **recherche par mots-clés** (BM25) combinée aux embeddings (« recherche
  hybride »), utile pour les numéros d'article (« que dit l'article 150 ? »).
- Calibrer MIN_SCORE sur un plus grand jeu de questions hors corpus, ou utiliser l'écart
  entre le 1er et le 2e score plutôt qu'un seuil fixe.

## 10. Relancer cette partie

```
python -m src.index                   # crée chroma_db/ (environ 40 s ; télécharge le modèle la 1re fois)
python -m src.retrieve                # test sur 5 questions
python -m src.retrieve "ma question"  # recherche libre
python -m src.observability           # écrit une trace dans logs/traces.jsonl
python notebooks/mesure_tokens.py     # mesure de troncature (§2)
python notebooks/experience_topk.py   # expérience modèles et TOP_K (§5 et §6)
```
