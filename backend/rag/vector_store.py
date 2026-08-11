import chromadb
from chromadb.utils import embedding_functions

from config import Config

_client = None
_collection = None

# Modèle d'embedding multilingue, adapté au français (contrairement au modèle
# par défaut de ChromaDB qui est optimisé anglais). Tourne localement, aucun
# appel API, donc pas de dépendance au quota Gemini pour la recherche.
_embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)


def get_collection():
    """
    Singleton simple : on garde une seule connexion ChromaDB
    et une seule collection ouverte pendant la vie du serveur.
    """
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(Config.CHROMA_PERSIST_DIR))
        _collection = _client.get_or_create_collection(
            name="financial_reports_fr",  # nouveau nom, voir explication ci-dessous
            embedding_function=_embedding_function,
        )
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