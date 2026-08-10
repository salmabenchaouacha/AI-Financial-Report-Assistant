import io
import os

import fitz  # PyMuPDF
import google.generativeai as genai
from PIL import Image



genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


def extract_images(pdf_path: str) -> list[dict]:
    """
    Extrait toutes les images bitmap intégrées dans le PDF.
    Ne détecte PAS les graphiques vectoriels (charts Excel/matplotlib exportés en PDF).
    """
    doc = fitz.open(pdf_path)
    images = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            images.append({
                "page": page_number + 1,
                "image_index": img_index,
                "image_bytes": base_image["image"],
                "ext": base_image["ext"],
            })

    doc.close()
    return images


def describe_image(image_bytes: bytes) -> str:
    """
    Envoie une image au modèle vision Gemini et retourne une description textuelle.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    image = Image.open(io.BytesIO(image_bytes))

    prompt = (
        "Décris ce graphique ou cette image issue d'un rapport financier. "
        "Si c'est un graphique, précise les valeurs, tendances et unités visibles. "
        "Sois factuel et concis."
    )

    response = model.generate_content([prompt, image])
    return response.text


def extract_and_describe_images(pdf_path: str) -> list[dict]:
    """
    Combine extraction + description des images bitmap classiques.
    """
    images = extract_images(pdf_path)
    results = []

    for img in images:
        description = describe_image(img["image_bytes"])
        results.append({
            "page": img["page"],
            "image_index": img["image_index"],
            "description": description,
        })

    return results


def render_page_as_image(pdf_path: str, page_number: int, zoom: float = 2.0) -> bytes:
    """
    Convertit une page entière du PDF en image PNG (rasterisation).
    Capture aussi bien les images bitmap que les graphiques vectoriels,
    que page.get_images() ne peut pas détecter seul.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]  # page_number commence à 1

    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    image_bytes = pix.tobytes("png")

    doc.close()
    return image_bytes


def describe_page_visually(pdf_path: str, page_number: int) -> str:
    """
    Rasterise une page et la décrit avec le modèle vision.
    Utile pour capturer des graphiques vectoriels qu'aucune extraction
    d'image classique ne peut détecter.
    """
    image_bytes = render_page_as_image(pdf_path, page_number)
    return describe_image(image_bytes)