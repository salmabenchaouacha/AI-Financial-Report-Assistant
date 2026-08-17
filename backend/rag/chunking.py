import uuid


def split_text_into_chunks(text: str, max_chunk_size: int = 700, overlap: int = 100) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    chunks = []
    current_chunk = ""

    for line in lines:
        if current_chunk and len(current_chunk) + len(line) > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] + "\n" + line
        else:
            current_chunk = f"{current_chunk}\n{line}" if current_chunk else line

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def chunk_text_pages(pages: list[dict], document_id: str, filename: str = "", annee_fiscale: int = None) -> list[dict]:
    chunks = []
    for page in pages:
        if not page["text"].strip():
            continue

        text_chunks = split_text_into_chunks(page["text"])

        for text_chunk in text_chunks:
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": text_chunk,
                "metadata": {
                    "document_id": document_id,
                    "filename": filename,
                    "page": page["page"],
                    "type": "texte",
                    "annee_fiscale": annee_fiscale or 0,
                },
            })
    return chunks


def chunk_tables(tables: list[dict], document_id: str, filename: str = "", annee_fiscale: int = None) -> list[dict]:
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
                "filename": filename,
                "page": table["page"] or 0,
                "type": "tableau",
                "annee_fiscale": annee_fiscale or 0,
            },
        })
    return chunks


def chunk_images(image_descriptions: list[dict], document_id: str, filename: str = "", annee_fiscale: int = None) -> list[dict]:
    chunks = []
    for img in image_descriptions:
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": f"[IMAGE/GRAPHIQUE - page {img['page']}]\n{img['description']}",
            "metadata": {
                "document_id": document_id,
                "filename": filename,
                "page": img["page"],
                "type": "image",
                "annee_fiscale": annee_fiscale or 0,
            },
        })
    return chunks