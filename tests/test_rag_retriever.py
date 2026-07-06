import chromadb

from evbot.config import CHROMA_COLLECTION_NAME
from evbot.rag import retriever


def _seed(persist_dir: str) -> None:
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.create_collection(CHROMA_COLLECTION_NAME)
    collection.add(
        documents=[
            "Tesla Model 3\n\nThe Model 3 has an EPA-estimated range of about 272 miles.",
            "Chevy Bolt\n\nThe Bolt EUV starts at around $27,000 before incentives.",
            "Home Charging Setup\n\nLevel 2 charging typically requires a 240V circuit.",
        ],
        metadatas=[
            {"source_file": "tesla_model_3.md", "category": "model_specs"},
            {"source_file": "chevy_bolt.md", "category": "model_specs"},
            {"source_file": "home_charging_setup.md", "category": "charging"},
        ],
        ids=["tesla-0", "bolt-0", "charging-0"],
    )


def test_retrieve_returns_relevant_chunk(tmp_path):
    persist_dir = str(tmp_path / "chroma_db")
    _seed(persist_dir)

    results = retriever.retrieve("What is the range of the Model 3?", k=2, persist_dir=persist_dir)

    assert results
    assert any("272 miles" in r for r in results)


def test_retrieve_empty_collection_returns_empty_list(tmp_path):
    persist_dir = str(tmp_path / "chroma_db")
    client = chromadb.PersistentClient(path=persist_dir)
    client.create_collection(CHROMA_COLLECTION_NAME)

    results = retriever.retrieve("anything", persist_dir=persist_dir)

    assert results == []


def test_retrieve_missing_collection_returns_empty_list(tmp_path):
    persist_dir = str(tmp_path / "chroma_db")

    results = retriever.retrieve("anything", persist_dir=persist_dir)

    assert results == []
