"""Configuration partagée par toutes les parties du projet."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Chemins -----------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EVAL_DIR = DATA_DIR / "eval"
REPORTS_DIR = ROOT / "reports"
LOGS_DIR = ROOT / "logs"
CHROMA_DIR = ROOT / "chroma_db"

PDF_PATH = RAW_DIR / "code_travail_loi_2026-18.pdf"
RAW_TEXT_PATH = RAW_DIR / "code_travail.txt"
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"
SOURCES_CSV = DATA_DIR / "sources.csv"

# --- Corpus ------------------------------------------------------------
SOURCE_LABEL = (
    "Loi n° 2026-18 du 03 septembre 2026 portant Code du Travail "
    "(JO du Sénégal n° 7931 du 17 septembre 2026)"
)

# --- Partie 1 : découpage ----------------------------------------------
CHUNK_MAX_CHARS = 1200   # au-delà, un article est scindé en plusieurs chunks
CHUNK_OVERLAP = 150      # chevauchement entre deux chunks d'un même article

# --- Parties 2 à 5 (à ajuster par les personnes concernées) ------------
COLLECTION_NAME = "code_travail"
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = int(os.getenv("TOP_K", "4"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.25"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")