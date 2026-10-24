"""Partie 2a : calcul des embeddings des chunks et indexation dans ChromaDB.

Usage : python -m src.index

Relançable sans doublons : la collection est supprimée puis recréée à chaque
lancement. À relancer si chunks.jsonl ou EMBED_MODEL changent.
"""
import json
import time

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import CHROMA_DIR, CHUNKS_PATH, COLLECTION_NAME, EMBED_MODEL


def prefixes(model_name):
    """Retourne (préfixe des questions, préfixe des passages) attendus par le modèle.

    Les modèles e5 ont été entraînés avec "query: " devant les questions et
    "passage: " devant les textes : sans ces préfixes, leurs résultats se dégradent.
    Les autres modèles (ex. MiniLM) n'en utilisent pas.
    """
    if "e5" in model_name.lower():
        return "query: ", "passage: "
    return "", ""


# Modèles déjà chargés, rangés par nom : on ne charge chaque modèle qu'une fois
_MODELES = {}


def charger_modele(model_name=EMBED_MODEL):
    """Charge le modèle d'embeddings une seule fois (téléchargé au premier appel)."""
    if model_name not in _MODELES:
        try:
            # D'abord depuis le disque, sans contacter Hugging Face : plus rapide,
            # et ça marche même quand la connexion est coupée ou instable.
            _MODELES[model_name] = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            # Premier lancement : le modèle n'est pas encore sur le disque, on le télécharge.
            _MODELES[model_name] = SentenceTransformer(model_name)
    return _MODELES[model_name]


def lire_chunks(path=CHUNKS_PATH):
    """Lit chunks.jsonl : une ligne JSON = un chunk (id, texte, titre, source, article)."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(ligne) for ligne in f if ligne.strip()]


def construire_index(model_name=EMBED_MODEL, collection_name=COLLECTION_NAME):
    """Calcule les embeddings de tous les chunks et les range dans ChromaDB.

    Retourne (nombre de chunks indexés, durée du calcul des embeddings en secondes).
    """
    chunks = lire_chunks()
    modele = charger_modele(model_name)
    _, prefixe_passage = prefixes(model_name)

    # 1) Embeddings : une liste de nombres par chunk, calculés par paquets de 32.
    #    normalize_embeddings=True ramène chaque vecteur à une longueur de 1,
    #    ce qui rend la similarité cosinus juste et stable.
    debut = time.perf_counter()
    embeddings = modele.encode(
        [prefixe_passage + c["texte"] for c in chunks],
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    duree = time.perf_counter() - debut

    # 2) Base vectorielle enregistrée sur le disque, dans le dossier chroma_db/
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 3) On repart de zéro à chaque lancement : c'est ce qui évite les doublons.
    #    (la première fois, la collection n'existe pas encore : on ignore l'erreur)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    # 4) "hnsw:space": "cosine" -> ChromaDB compare les vecteurs avec la distance
    #    cosinus. On note aussi le modèle utilisé, pour que retrieve.py vérifie
    #    qu'il interroge la base avec le même modèle.
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine", "embed_model": model_name},
    )

    # 5) On range, pour chaque chunk : son id, son texte (sans préfixe),
    #    son embedding et ses étiquettes (pour citer la source plus tard).
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["texte"] for c in chunks],
        embeddings=embeddings.tolist(),
        metadatas=[
            {"titre": c["titre"], "source": c["source"], "article": c["article"]}
            for c in chunks
        ],
    )
    return collection.count(), duree


def main():
    print(f"Modèle d'embeddings : {EMBED_MODEL}")
    nombre, duree = construire_index()
    print(f"{nombre} chunks indexés dans {CHROMA_DIR} (collection « {COLLECTION_NAME} »)")
    print(f"Calcul des embeddings : {duree:.1f} s, soit {1000 * duree / nombre:.0f} ms par chunk")


if __name__ == "__main__":
    main()
