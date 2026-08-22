import chromadb
from chromadb.utils import embedding_functions

from config import Config

_client = None
_collection = None

_embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)


def get_collection():
    """
    Singleton simple : on garde une seule connexion ChromaDB
    et une seule collection ouverte pendant la vie du serveur.
    Distance cosinus imposée explicitement (hnsw:space=cosine),
    pour que la valeur renvoyée dans 'distances' reste comprise entre 0 et 2
    (0 = identique, 2 = opposé), et surtout que (1 - distance) reste
    interprétable comme une similarité cosinus classique.
    """
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(Config.CHROMA_PERSIST_DIR))
        _collection = _client.get_or_create_collection(
            name="financial_reports_fr",
            embedding_function=_embedding_function,
            metadata={"hnsw:space": "cosine"},
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
    if not document_ids:
        return None

    if isinstance(document_ids, str):
        return {"document_id": document_ids}

    if isinstance(document_ids, list):
        if len(document_ids) == 1:
            return {"document_id": document_ids[0]}
        return {"document_id": {"$in": document_ids}}

    return None


def search(query: str, filters: dict = None, n_results: int = 10):
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
def build_filter(document_ids, type_filter: str = None) -> dict | None:
    """
    Construit un filtre ChromaDB combinant document_id(s) et, optionnellement,
    un type de chunk précis (ex: "tableau").
    """
    conditions = []

    if document_ids:
        if isinstance(document_ids, str):
            conditions.append({"document_id": document_ids})
        elif isinstance(document_ids, list):
            if len(document_ids) == 1:
                conditions.append({"document_id": document_ids[0]})
            else:
                conditions.append({"document_id": {"$in": document_ids}})

    if type_filter:
        conditions.append({"type": type_filter})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def _merge_results(*result_sets):
    """
    Fusionne plusieurs résultats ChromaDB (dédoublonnés par id),
    triés par distance croissante (plus similaire en premier).
    """
    seen_ids = set()
    merged_ids, merged_docs, merged_metas, merged_dists = [], [], [], []

    for results in result_sets:
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for i, doc, meta, dist in zip(ids, docs, metas, dists):
            if i in seen_ids:
                continue
            seen_ids.add(i)
            merged_ids.append(i)
            merged_docs.append(doc)
            merged_metas.append(meta)
            merged_dists.append(dist)

    order = sorted(range(len(merged_dists)), key=lambda idx: merged_dists[idx])
    return {
        "ids": [[merged_ids[i] for i in order]],
        "documents": [[merged_docs[i] for i in order]],
        "metadatas": [[merged_metas[i] for i in order]],
        "distances": [[merged_dists[i] for i in order]],
    }


def search_with_table_priority(query: str, document_ids, n_results: int = 8, n_tables: int = 5):
    """
    Recherche hybride : combine une recherche sémantique générale avec une
    recherche dédiée, filtrée uniquement sur les chunks de type 'tableau'.

    Objectif : garantir que les tableaux financiers (souvent moins bien
    classés par pure similarité sémantique face à du texte narratif sur le
    même sujet) soient toujours transmis au LLM, plutôt que de dépendre du
    hasard du classement vectoriel.
    """
    collection = get_collection()

    general_filter = build_filter(document_ids)
    general_results = collection.query(
        query_texts=[query], n_results=n_results, where=general_filter
    )

    table_filter = build_filter(document_ids, type_filter="tableau")
    table_results = collection.query(
        query_texts=[query], n_results=n_tables, where=table_filter
    )

    return _merge_results(table_results, general_results)