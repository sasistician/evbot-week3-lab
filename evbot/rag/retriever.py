"""Query the Chroma collection seeded by ingest.py."""

import chromadb

from evbot.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, RAG_RETRIEVAL_K


def retrieve(query: str, k: int = RAG_RETRIEVAL_K, persist_dir: str = CHROMA_PERSIST_DIR) -> list[str]:
    client = chromadb.PersistentClient(path=persist_dir)
    try:
        collection = client.get_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        return []

    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(k, collection.count()))
    return results["documents"][0] if results["documents"] else []
