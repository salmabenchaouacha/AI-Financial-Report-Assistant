import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
from rag.chunking import chunk_text_pages, chunk_tables, chunk_images
from rag.vector_store import index_chunks, search
from document_processing.pdf_parser import extract_text_by_page, get_document_stats
from document_processing.table_extractor import extract_tables
from document_processing.image_processor import extract_and_describe_images, describe_page_visually

upload_bp = Blueprint("upload", __name__)

# Stockage temporaire en mémoire du statut de chaque document.
# Sera remplacé plus tard par une vraie base de données.
DOCUMENTS_STATUS = {}


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


@upload_bp.route("", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni (champ 'file' attendu)"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Nom de fichier vide"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Seuls les fichiers PDF sont acceptés"}), 400

    document_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    save_path = upload_folder / f"{document_id}_{filename}"
    file.save(save_path)

    DOCUMENTS_STATUS[document_id] = {
        "document_id": document_id,
        "filename": filename,
        "status": "uploaded",
        "path": str(save_path),
    }

    return jsonify(DOCUMENTS_STATUS[document_id]), 201


@upload_bp.route("/status/<document_id>", methods=["GET"])
def get_status(document_id):
    doc = DOCUMENTS_STATUS.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404
    return jsonify({"document_id": doc["document_id"], "status": doc["status"]})


@upload_bp.route("/extract/<document_id>", methods=["GET"])
def extract_text(document_id):
    doc = DOCUMENTS_STATUS.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    stats = get_document_stats(doc["path"])
    pages = extract_text_by_page(doc["path"])

    return jsonify({
        "document_id": document_id,
        "stats": stats,
        "preview": pages[:1],
    })


@upload_bp.route("/extract-tables/<document_id>", methods=["GET"])
def extract_tables_route(document_id):
    doc = DOCUMENTS_STATUS.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    tables = extract_tables(doc["path"])

    return jsonify({
        "document_id": document_id,
        "num_tables": len(tables),
        "tables": tables,
    })


@upload_bp.route("/extract-images/<document_id>", methods=["GET"])
def extract_images_route(document_id):
    doc = DOCUMENTS_STATUS.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    results = extract_and_describe_images(doc["path"])

    return jsonify({
        "document_id": document_id,
        "num_images": len(results),
        "images": results,
    })


@upload_bp.route("/describe-page/<document_id>/<int:page_number>", methods=["GET"])
def describe_page_route(document_id, page_number):
    doc = DOCUMENTS_STATUS.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    description = describe_page_visually(doc["path"], page_number)

    return jsonify({
        "document_id": document_id,
        "page": page_number,
        "description": description,
    })
@upload_bp.route("/index/<document_id>", methods=["POST"])
def index_document(document_id):
    """
    Pipeline complet : extrait texte + tableaux + images, chunk tout,
    et indexe dans ChromaDB. À lancer une fois par document.
    """
    doc = DOCUMENTS_STATUS.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    pages = extract_text_by_page(doc["path"])
    tables = extract_tables(doc["path"])
    images = extract_and_describe_images(doc["path"])

    chunks = []
    chunks += chunk_text_pages(pages, document_id)
    chunks += chunk_tables(tables, document_id)
    chunks += chunk_images(images, document_id)

    num_indexed = index_chunks(chunks)

    DOCUMENTS_STATUS[document_id]["status"] = "indexed"

    return jsonify({
        "document_id": document_id,
        "status": "indexed",
        "num_chunks_indexed": num_indexed,
        "breakdown": {
            "texte": len(pages),
            "tableaux": len(tables),
            "images": len(images),
        },
    })


@upload_bp.route("/search", methods=["POST"])
def search_route():
    """
    Endpoint de test pour vérifier que la recherche sémantique fonctionne.
    Body attendu : { "query": "...", "document_id": "..." (optionnel) }
    """
    body = request.get_json()
    query = body.get("query")
    document_id = body.get("document_id")

    if not query:
        return jsonify({"error": "champ 'query' requis"}), 400

    filters = {"document_id": document_id} if document_id else None
    results = search(query, filters=filters)

    return jsonify(results)   