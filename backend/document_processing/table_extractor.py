from docling.document_converter import DocumentConverter


def extract_tables(pdf_path: str) -> list[dict]:
    """
    Extrait tous les tableaux d'un PDF avec Docling.
    Retourne une liste de dicts : { "page": int, "table_index": int, "data": list[list[str]] }
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document

    tables = []
    for i, table in enumerate(doc.tables):
        # Docling expose le tableau sous forme de grille de cellules
        grid = table.export_to_dataframe().values.tolist()
        headers = table.export_to_dataframe().columns.tolist()

        page_no = table.prov[0].page_no if table.prov else None

        tables.append({
            "table_index": i,
            "page": page_no,
            "headers": headers,
            "data": grid,
        })

    return tables