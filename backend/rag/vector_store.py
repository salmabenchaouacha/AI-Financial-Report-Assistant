import chromadb

from config import Config

_client = None
_collection = None


def get_collection():
    """
    Singleton simple : on garde une seule connexion ChromaDB
    et une seule collection ouverte pendant la vie du serveur.
    """
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(Config.CHROMA_PERSIST_DIR))
        _collection = _client.get_or_create_collection(name="financial_reports")
    return _collection


def index_chunks(chunks: list[dict]):
    """
    Indexe une liste de chunks dans ChromaDB.
    Chaque chunk doit avoir : id, text, metadata
    """
    if not chunks:
        return 0

    collection = get_collection()
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
    return len(chunks)


def search(query: str, filters: dict = None, n_results: int = 5):
    collection = get_collection()
    return collection.query(
        query_texts=[query],
        n_results=n_results,
        where=filters,
    )