"""Idempotent seeding script: chunk data/ev_docs/*.md into the Chroma collection.

Run with: uv run python -m evbot.rag.ingest

Chunking is hand-rolled and deliberately simple (split on blank lines, keep
the doc's H1 title as context on every chunk) rather than pulling in a
text-splitter library — the point is for students to read and modify this,
not to be state-of-the-art.
"""

import chromadb

from evbot.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, EV_DOCS_DIR


def _chunk_document(text: str) -> list[str]:
    lines = text.strip().splitlines()
    title = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else ""
    body = "\n".join(lines[1:]) if title else text

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if title:
        return [f"{title}\n\n{p}" for p in paragraphs]
    return paragraphs


def _load_documents() -> tuple[list[str], list[dict], list[str]]:
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for path in sorted(EV_DOCS_DIR.glob("**/*.md")):
        category = path.parent.name
        text = path.read_text()
        for i, chunk in enumerate(_chunk_document(text)):
            documents.append(chunk)
            metadatas.append({"source_file": path.name, "category": category})
            ids.append(f"{path.stem}-{i}")

    return documents, metadatas, ids


def ingest() -> int:
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    existing = {c.name for c in client.list_collections()}
    if CHROMA_COLLECTION_NAME in existing:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    collection = client.create_collection(CHROMA_COLLECTION_NAME)

    documents, metadatas, ids = _load_documents()
    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)

    return len(documents)


def main() -> None:
    chunk_count = ingest()
    doc_count = len(list(EV_DOCS_DIR.glob("**/*.md")))
    print(f"Ingested {doc_count} documents into {chunk_count} chunks.")


if __name__ == "__main__":
    main()
