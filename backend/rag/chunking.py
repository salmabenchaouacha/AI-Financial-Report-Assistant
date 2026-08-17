import uuid

def split_text_into_chunks(text: str, max_chunk_size: int = 700, overlap: int = 100) -> list[str]:
    """
    Découpe un texte en chunks de taille raisonnable.
    Fonctionne ligne par ligne (le texte extrait de PDF n'a souvent que des
    simples \n entre lignes, pas de vrais doubles \n entre paragraphes),
    avec un léger chevauchement entre chunks consécutifs.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    chunks = []
    current_chunk = ""

    for line in lines:
        if current_chunk and len(current_chunk) + len(line) > max_chunk_size:
            chunks.append(current_chunk.strip())
            # Overlap : on garde la fin du chunk précédent au début du suivant
            current_chunk = current_chunk[-overlap:] + "\n" + line
        else:
            current_chunk = f"{current_chunk}\n{line}" if current_chunk else line

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def chunk_text_pages(pages: list[dict], document_id: str, annee_fiscale: int = None) -> list[dict]:
    """
    Transforme les pages de texte extraites en chunks indexables.
    Chaque page est découpée en plusieurs chunks (par paragraphes, avec overlap)
    plutôt qu'un seul chunk par page entière, pour une recherche plus précise.
    """
    chunks = []
    for page in pages:
        if not page["text"].strip():
            continue  # on ignore les pages vides

        text_chunks = split_text_into_chunks(page["text"])

        for text_chunk in text_chunks:
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": text_chunk,
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