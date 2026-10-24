"""Partie 2b : recherche des passages les plus proches d'une question.

Usage :
    python -m src.retrieve "Quelle est la durée du congé de maternité ?"
    python -m src.retrieve          (sans argument : 5 questions de test + 1 hors corpus)

Format renvoyé (utilisé par les parties 3 et 4, ne pas changer sans prévenir) :
    [{"id", "texte", "titre", "source", "article", "score"}, ...]
trié du plus pertinent au moins pertinent ; score = similarité cosinus (1 = identique).
"""
import sys
import time
from functools import lru_cache

import chromadb

from src.config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, MIN_SCORE, TOP_K
from src.index import charger_modele, prefixes


@lru_cache(maxsize=None)
def ouvrir_collection(collection_name=COLLECTION_NAME):
    """Ouvre la collection ChromaDB créée par index.py (une seule fois par exécution)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        return client.get_collection(collection_name)
    except Exception as erreur:
        raise RuntimeError(
            f"Collection « {collection_name} » introuvable dans {CHROMA_DIR}. "
            "Lancez d'abord : python -m src.index"
        ) from erreur


def retrieve(question, k=TOP_K, model_name=EMBED_MODEL, collection_name=COLLECTION_NAME):
    """Renvoie les k passages les plus proches de la question, du meilleur au moins bon."""
    collection = ouvrir_collection(collection_name)

    # Sécurité : la question doit être transformée avec le MÊME modèle que les chunks,
    # sinon les nombres ne sont pas comparables (deux "GPS" différents).
    modele_index = (collection.metadata or {}).get("embed_model")
    if modele_index and modele_index != model_name:
        raise RuntimeError(
            f"La base a été construite avec {modele_index} mais la recherche utilise "
            f"{model_name}. Relancez : python -m src.index"
        )

    # 1) Embedding de la question, avec le préfixe "query: " pour e5
    prefixe_question, _ = prefixes(model_name)
    vecteur = charger_modele(model_name).encode(
        [prefixe_question + question], normalize_embeddings=True
    )

    # 2) ChromaDB renvoie les k chunks dont l'embedding est le plus proche
    resultats = collection.query(
        query_embeddings=vecteur.tolist(),
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # 3) Mise au format partagé. ChromaDB donne une distance cosinus
    #    (0 = identique) : on la convertit en score de similarité (1 = identique).
    passages = []
    for id_, texte, meta, distance in zip(
        resultats["ids"][0],
        resultats["documents"][0],
        resultats["metadatas"][0],
        resultats["distances"][0],
    ):
        passages.append({
            "id": id_,
            "texte": texte,
            "titre": meta["titre"],
            "source": meta["source"],
            "article": meta["article"],
            "score": round(1 - distance, 4),
        })
    return passages


# Questions réelles sur le Code du Travail, avec l'article qui contient la réponse
QUESTIONS_TEST = [
    ("Quelle est la durée légale du travail par semaine ?", 241),
    ("À partir de quel âge un enfant peut-il être employé ?", 281),
    ("Combien de jours de congé payé gagne-t-on par mois de travail ?", 249),
    ("Combien de semaines dure le congé de maternité ?", 277),
    ("Le repos hebdomadaire est-il obligatoire ?", 246),
    ("Comment préparer un thiéboudienne ?", None),  # hors corpus
]


def afficher(question, passages, duree_ms, attendu=None):
    print(f"\nQuestion : {question}  ({duree_ms:.0f} ms)")
    for rang, p in enumerate(passages, start=1):
        repere = "  <-- attendu" if p["article"] == attendu else ""
        print(f"  {rang}. [{p['score']:.3f}] {p['id']:<10} {p['titre']}{repere}")
    if passages and passages[0]["score"] < MIN_SCORE:
        print(f"  (meilleur score sous MIN_SCORE = {MIN_SCORE} : jugée hors corpus)")


def main():
    print(f"Modèle : {EMBED_MODEL} | TOP_K = {TOP_K} | MIN_SCORE = {MIN_SCORE}")
    if len(sys.argv) > 1:
        questions = [(" ".join(sys.argv[1:]), None)]
    else:
        questions = QUESTIONS_TEST

    # Le premier appel charge le modèle (plusieurs secondes) : on le fait à part
    # pour que les durées affichées ne mesurent que la recherche.
    retrieve("échauffement", k=1)

    trouves = 0
    for question, attendu in questions:
        debut = time.perf_counter()
        passages = retrieve(question)
        duree_ms = 1000 * (time.perf_counter() - debut)
        afficher(question, passages, duree_ms, attendu)
        if attendu is not None and any(p["article"] == attendu for p in passages):
            trouves += 1

    nb_attendus = sum(1 for _, attendu in questions if attendu is not None)
    if nb_attendus:
        print(f"\nArticle attendu dans le top {TOP_K} : {trouves}/{nb_attendus}")


if __name__ == "__main__":
    main()
