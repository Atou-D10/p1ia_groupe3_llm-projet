"""Partie 2c : traçage de chaque requête dans logs/traces.jsonl.

Une ligne JSON par question : date, question, durée de chaque étape (ms),
tokens d'entrée et de sortie, coût estimé.

Utilisation (partie 3) :
    from src.observability import Tracer

    t = Tracer(question)
    with t.etape("recherche"):
        passages = retrieve(question)
    with t.etape("llm"):
        rep = client.chat.completions.create(...)
    t.tokens(entree=rep.usage.prompt_tokens, sortie=rep.usage.completion_tokens)
    t.enregistrer(reponse=rep.choices[0].message.content, passages=passages)

Test : python -m src.observability
"""
import json
import time
from contextlib import contextmanager
from datetime import datetime

from src.config import EMBED_MODEL, LLM_MODEL, LOGS_DIR

TRACES_PATH = LOGS_DIR / "traces.jsonl"

# Coût réellement payé : 0 $, car nous utilisons le niveau gratuit de Groq.
PRIX_ENTREE_USD_PAR_MILLION = 0.0
PRIX_SORTIE_USD_PAR_MILLION = 0.0
NOTE_COUT = "niveau gratuit Groq : 0 $ ; les embeddings tournent en local (gratuit)"


class Tracer:
    """Chronomètre les étapes d'une requête et écrit le bilan dans traces.jsonl."""

    def __init__(self, question):
        self.question = question
        self.date = datetime.now().astimezone().isoformat(timespec="seconds")
        self.debut = time.perf_counter()
        self.etapes_ms = {}
        self.tokens_entree = 0
        self.tokens_sortie = 0

    @contextmanager
    def etape(self, nom):
        """Mesure la durée du bloc `with` ; elle est notée même si le bloc plante."""
        debut = time.perf_counter()
        try:
            yield
        finally:
            self.etapes_ms[nom] = round(1000 * (time.perf_counter() - debut), 1)

    def tokens(self, entree=0, sortie=0):
        """Ajoute les tokens consommés par un appel au LLM (cumulés s'il y en a plusieurs)."""
        self.tokens_entree += entree or 0
        self.tokens_sortie += sortie or 0

    def enregistrer(self, reponse=None, passages=None, **autres):
        """Écrit une ligne dans logs/traces.jsonl et la renvoie sous forme de dict."""
        cout = (
            self.tokens_entree * PRIX_ENTREE_USD_PAR_MILLION
            + self.tokens_sortie * PRIX_SORTIE_USD_PAR_MILLION
        ) / 1_000_000
        trace = {
            "date": self.date,
            "question": self.question,
            "etapes_ms": self.etapes_ms,
            "total_ms": round(1000 * (time.perf_counter() - self.debut), 1),
            "tokens_entree": self.tokens_entree,
            "tokens_sortie": self.tokens_sortie,
            "cout_usd": round(cout, 6),
            "note_cout": NOTE_COUT,
            "modele_embeddings": EMBED_MODEL,
            "modele_llm": LLM_MODEL,
            # On garde seulement l'id et le score des passages, pas leur texte complet
            "passages": [{"id": p["id"], "score": p["score"]} for p in passages or []],
            "reponse": reponse,
            **autres,
        }
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(TRACES_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")
        return trace


def main():
    """Petit test sans LLM : trace une recherche réelle dans logs/traces.jsonl."""
    from src.index import charger_modele
    from src.retrieve import retrieve

    question = "Combien de semaines dure le congé de maternité ?"
    t = Tracer(question)
    # Le premier appel charge le modèle depuis le disque (plusieurs secondes, une
    # seule fois par lancement) : on le chronomètre à part de la recherche elle-même.
    with t.etape("chargement_modele"):
        charger_modele()
    with t.etape("recherche"):
        passages = retrieve(question)
    trace = t.enregistrer(passages=passages)
    print(json.dumps(trace, ensure_ascii=False, indent=2))
    print(f"\nLigne ajoutée à {TRACES_PATH}")


if __name__ == "__main__":
    main()
