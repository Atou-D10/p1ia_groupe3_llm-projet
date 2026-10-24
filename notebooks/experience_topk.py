"""Étape 5 : expérience pour le rapport de la partie 2.

Compare deux modèles d'embeddings (MiniLM, e5-small) et plusieurs valeurs de TOP_K
sur 13 questions dont on connaît l'article attendu, plus 3 questions hors corpus.

Mesures :
- hit@k : proportion de questions dont l'article attendu est dans les k premiers passages ;
- MRR : moyenne de 1/rang du bon article (1 si 1er, 0,5 si 2e, ... 0 si absent du top 10) ;
- latence moyenne d'une recherche ;
- meilleurs scores des questions dans le corpus et hors corpus (pour MIN_SCORE).

Usage (depuis la racine du projet, venv activé) :
    python notebooks/experience_topk.py

Crée deux collections de test (exp_minilm, exp_e5small) sans toucher à la collection
principale « code_travail ». Écrit le détail dans reports/experience_partie2.csv.
"""
import csv
import sys
import time
from pathlib import Path

# Permet d'importer src.* quand on lance le script depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import REPORTS_DIR  # noqa: E402
from src.index import charger_modele, construire_index  # noqa: E402
from src.retrieve import retrieve  # noqa: E402

MODELES = {
    "exp_minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "exp_e5small": "intfloat/multilingual-e5-small",
}
VALEURS_K = [1, 3, 4, 5, 10]

# (question, article attendu, type) : « proche » reprend les mots de l'article,
# « reformulée » utilise des mots de tous les jours (plus difficile).
QUESTIONS = [
    ("Quelle est la durée légale du travail par semaine ?", 241, "proche"),
    ("À partir de quel âge un enfant peut-il être employé ?", 281, "proche"),
    ("Combien de jours de congé payé gagne-t-on par mois de travail ?", 249, "proche"),
    ("Combien de semaines dure le congé de maternité ?", 277, "proche"),
    ("Le repos hebdomadaire est-il obligatoire ?", 246, "proche"),
    ("Quelle est la durée maximale d'un contrat à durée déterminée ?", 100, "proche"),
    ("Mon patron peut-il me renvoyer pendant mon congé de maternité ?", 277, "reformulée"),
    ("Si je travaille plus de 40 heures, est-ce que je dois être payé plus ?", 244, "reformulée"),
    ("Une femme qui attend un bébé peut-elle quitter son travail du jour au lendemain ?", 278, "reformulée"),
    ("Mon employeur peut-il me payer seulement tous les deux mois ?", 199, "reformulée"),
    ("Comment mon patron doit-il m'annoncer mon licenciement ?", 149, "reformulée"),
    ("Puis-je être puni pour avoir dénoncé le harcèlement de mon chef ?", 20, "reformulée"),
    ("Combien de temps une entreprise peut-elle mettre ses employés au chômage technique ?", 123, "reformulée"),
]
HORS_CORPUS = [
    "Comment préparer un thiéboudienne ?",
    "Quel est le prix d'un billet d'avion Dakar-Paris ?",
    "Qui a gagné la Coupe d'Afrique des nations 2022 ?",
]


def rang_article(passages, attendu):
    """Position (1, 2, ...) du premier passage de l'article attendu, ou None s'il est absent."""
    for position, p in enumerate(passages, start=1):
        if p["article"] == attendu:
            return position
    return None


def main():
    lignes_csv = []
    resume = []
    k_max = max(VALEURS_K)

    for collection, modele in MODELES.items():
        print(f"\n=== {modele} ===")
        nombre, duree = construire_index(modele, collection)
        print(f"Indexation : {nombre} chunks en {duree:.1f} s ({1000 * duree / nombre:.0f} ms par chunk)")
        charger_modele(modele)  # déjà chargé par l'indexation : les temps ne mesurent que la recherche

        rangs, latences, scores_dedans = [], [], []
        for question, attendu, type_q in QUESTIONS:
            debut = time.perf_counter()
            passages = retrieve(question, k=k_max, model_name=modele, collection_name=collection)
            latences.append(1000 * (time.perf_counter() - debut))
            rang = rang_article(passages, attendu)
            rangs.append(rang)
            scores_dedans.append(passages[0]["score"])
            lignes_csv.append({
                "modele": modele, "question": question, "type": type_q,
                "article_attendu": attendu, "rang": rang if rang else "absent du top 10",
                "top1_article": passages[0]["article"], "top1_score": passages[0]["score"],
            })
            print(f"  rang {rang if rang else '-':>2}  [{passages[0]['score']:.3f}]  ({type_q}) {question}")

        scores_hors = []
        for question in HORS_CORPUS:
            passages = retrieve(question, k=1, model_name=modele, collection_name=collection)
            scores_hors.append(passages[0]["score"])
            lignes_csv.append({
                "modele": modele, "question": question, "type": "hors corpus",
                "article_attendu": "", "rang": "",
                "top1_article": passages[0]["article"], "top1_score": passages[0]["score"],
            })
            print(f"  hors corpus [{passages[0]['score']:.3f}]  {question}")

        n = len(QUESTIONS)
        ligne = {"modele": modele, "indexation_s": round(duree, 1)}
        for k in VALEURS_K:
            ligne[f"hit@{k}"] = sum(1 for r in rangs if r and r <= k) / n
        ligne["MRR"] = sum(1 / r for r in rangs if r) / n
        ligne["latence_ms"] = sum(latences) / n
        ligne["min_score_dedans"] = min(scores_dedans)
        ligne["max_score_hors"] = max(scores_hors)
        for type_q in ("proche", "reformulée"):
            rangs_type = [r for r, (_, _, t) in zip(rangs, QUESTIONS) if t == type_q]
            ligne[f"hit@4 {type_q}"] = sum(1 for r in rangs_type if r and r <= 4) / len(rangs_type)
        resume.append(ligne)

    # Tableau récapitulatif, prêt à recopier dans le rapport
    print("\n=== Résumé (13 questions) ===")
    colonnes = list(resume[0].keys())
    print(" | ".join(colonnes))
    for ligne in resume:
        print(" | ".join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in ligne.values()))

    REPORTS_DIR.mkdir(exist_ok=True)
    chemin = REPORTS_DIR / "experience_partie2.csv"
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(lignes_csv[0].keys()))
        writer.writeheader()
        writer.writerows(lignes_csv)
    print(f"\nDétail question par question : {chemin}")


if __name__ == "__main__":
    main()
