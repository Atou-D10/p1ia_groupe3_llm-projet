"""Étape 1 : combien de chunks dépassent la longueur maximale de chaque modèle ?

Usage (depuis la racine du projet, venv activé) :
    python notebooks/mesure_tokens.py
"""
import json

from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

# Les modèles comparés, avec le préfixe que chacun attend devant un passage
MODELES = [
    ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", ""),
    ("intfloat/multilingual-e5-small", "passage: "),
    ("intfloat/multilingual-e5-base", "passage: "),
]

# On lit les 524 chunks (une ligne JSON = un chunk)
with open("data/processed/chunks.jsonl", encoding="utf-8") as f:
    chunks = [json.loads(ligne) for ligne in f]

for nom, prefixe in MODELES:
    # Le tokenizer est le "découpeur en tokens" du modèle (petit fichier, pas le modèle entier)
    tokenizer = AutoTokenizer.from_pretrained(nom)
    # La longueur maximale utilisée par sentence-transformers est écrite dans ce fichier de config
    config = hf_hub_download(nom, "sentence_bert_config.json")
    with open(config, encoding="utf-8") as f:
        limite = json.load(f)["max_seq_length"]

    # Nombre de tokens de chaque chunk (avec le préfixe et les tokens spéciaux de début/fin)
    longueurs = [len(tokenizer(prefixe + c["texte"])["input_ids"]) for c in chunks]
    trop_longs = [n for n in longueurs if n > limite]

    print(f"\n{nom}")
    print(f"  longueur max du modèle : {limite} tokens")
    print(f"  tokens par chunk : moyenne {sum(longueurs) / len(longueurs):.0f}, max {max(longueurs)}")
    print(f"  chunks tronqués : {len(trop_longs)} sur {len(chunks)} "
          f"({100 * len(trop_longs) / len(chunks):.0f} %)")
