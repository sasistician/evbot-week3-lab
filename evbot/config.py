"""Environment configuration shared by every component."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OLLAMA_MODEL_SIMPLE = os.getenv("OLLAMA_MODEL_SIMPLE", "llama3.2")
OLLAMA_MODEL_COMPLEX = os.getenv("OLLAMA_MODEL_COMPLEX", "llama3.1")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", str(BASE_DIR / "memory.db"))

EV_DOCS_DIR = BASE_DIR / "data" / "ev_docs"
CHROMA_COLLECTION_NAME = "ev_knowledge_base"

# Router thresholds
COMPLEXITY_WORD_COUNT_THRESHOLD = 25
COMPARISON_KEYWORDS = (
    "compare",
    "vs",
    "versus",
    "difference between",
    "which is better",
    "recommend",
    "pros and cons",
    "trade-off",
    "tradeoff",
)

# Input guardrail vocabulary
EV_TOPIC_KEYWORDS = (
    "ev",
    "evs",
    "electric vehicle",
    "electric car",
    "charging",
    "charger",
    "battery",
    "range",
    "kwh",
    "tesla",
    "rivian",
    "mach-e",
    "mustang mach-e",
    "bolt",
    "ioniq",
    "hyundai",
    "ford",
    "chevy",
    "chevrolet",
    "incentive",
    "rebate",
    "tax credit",
    "warranty",
    "degradation",
    "regenerative braking",
    "supercharger",
    "dcfc",
    "level 1",
    "level 2",
)

RAG_RETRIEVAL_K = 4
# Complex queries often compare multiple EVs, so they need more retrieved
# context to cover every entity mentioned rather than just the first one.
RAG_RETRIEVAL_K_COMPLEX = 8
MEMORY_RECENT_TURNS = 6
