import fitz  # PyMuPDF


def extract_text_by_page(pdf_path: str) -> list[dict]:
    """
    Extrait le texte de chaque page d'un PDF.
    Retourne une liste de dicts : { "page": int, "text": str }
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        text = page.get_text().strip()

        pages.append({
            "page": page_number + 1,  # numérotation humaine, commence à 1
            "text": text,
        })

    doc.close()
    return pages


def get_document_stats(pdf_path: str) -> dict:
    """
    Statistiques rapides sur le document : nombre de pages,
    et une estimation simple pour détecter un PDF scanné
    (peu de texte extrait alors que le document a des pages).
    """
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    total_chars = sum(len(doc[i].get_text()) for i in range(num_pages))
    doc.close()

    avg_chars_per_page = total_chars / num_pages if num_pages else 0

    return {
        "num_pages": num_pages,
        "total_chars": total_chars,
        "avg_chars_per_page": round(avg_chars_per_page, 1),
        # Seuil arbitraire mais efficace en pratique : sous ~50 caractères/page
        # en moyenne, c'est probablement un PDF scanné (pas de texte natif) → OCR nécessaire plus tard
        "likely_scanned": avg_chars_per_page < 50,
    }