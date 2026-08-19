import chromadb
from chromadb.utils import embedding_functions

from config import Config

_client = None
_collection = None

_embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(Config.CHROMA_PERSIST_DIR))
        _collection = _client.get_or_create_collection(
            name="financial_reports_fr",
            embedding_function=_embedding_function,
        )
    return _collection


def index_chunks(chunks: list[dict]):
    if not chunks:
        return 0

    collection = get_collection()
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
    return len(chunks)


def build_document_filter(document_ids) -> dict | None:
    """
    Construit le filtre ChromaDB à partir d'un ou plusieurs document_id.
    Accepte une string (un seul doc) ou une liste (plusieurs docs).
    """
    if not document_ids:
        return None

    if isinstance(document_ids, str):
        return {"document_id": document_ids}

    if isinstance(document_ids, list):
        if len(document_ids) == 1:
            return {"document_id": document_ids[0]}
        return {"document_id": {"$in": document_ids}}

    return None


def search(query: str, filters: dict = None, n_results: int = 5):
    collection = get_collection()
    return collection.query(
        query_texts=[query],
        n_results=n_results,
        where=filters,
    )
def delete_document_chunks(document_id: str) -> int:
    """
    Supprime tous les chunks (texte, tableaux, images) associés à un
    document_id donné. Retourne le nombre de chunks supprimés.
    """
    collection = get_collection()

    # On récupère d'abord les ids concernés pour pouvoir logger/retourner un compte
    existing = collection.get(where={"document_id": document_id})
    ids_to_delete = existing.get("ids", [])

    if not ids_to_delete:
        return 0

    collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)