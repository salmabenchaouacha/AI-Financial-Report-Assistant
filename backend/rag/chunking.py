import uuid


def chunk_text_pages(pages: list[dict], document_id: str, annee_fiscale: int = None) -> list[dict]:
    """
    Transforme les pages de texte extraites en chunks indexables.
    Pour l'instant : un chunk par page (simple, on affinera par section plus tard si besoin).
    """
    chunks = []
    for page in pages:
        if not page["text"].strip():
            continue  # on ignore les pages vides

        chunks.append({
            "id": str(uuid.uuid4()),
            "text": page["text"],
            "metadata": {
                "document_id": document_id,
                "page": page["page"],
                "type": "texte",
                "annee_fiscale": annee_fiscale or 0,
            },
        })
    return chunks


def chunk_tables(tables: list[dict], document_id: str, annee_fiscale: int = None) -> list[dict]:
    """
    Transforme chaque tableau extrait en UN SEUL chunk complet (jamais coupé),
    avec ses en-têtes injectés dans le texte pour garder le contexte.
    """
    chunks = []
    for table in tables:
        headers = " | ".join(str(h) for h in table["headers"])
        rows_text = "\n".join(
            " | ".join(str(cell) for cell in row) for row in table["data"]
        )
        table_text = f"[TABLEAU - page {table['page']}]\n{headers}\n{rows_text}"

        chunks.append({
            "id": str(uuid.uuid4()),
            "text": table_text,
            "metadata": {
                "document_id": document_id,
                "page": table["page"] or 0,
                "type": "tableau",
                "annee_fiscale": annee_fiscale or 0,
            },
        })
    return chunks


def chunk_images(image_descriptions: list[dict], document_id: str, annee_fiscale: int = None) -> list[dict]:
    """
    Transforme chaque description d'image/graphique en un chunk indexable.
    """
    chunks = []
    for img in image_descriptions:
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": f"[IMAGE/GRAPHIQUE - page {img['page']}]\n{img['description']}",
            "metadata": {
                "document_id": document_id,
                "page": img["page"],
                "type": "image",
                "annee_fiscale": annee_fiscale or 0,
            },
        })
    return chunks
