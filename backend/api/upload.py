import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
from rag.chunking import chunk_text_pages, chunk_tables, chunk_images
from rag.vector_store import index_chunks, search
from document_processing.pdf_parser import extract_text_by_page, get_document_stats
from document_processing.table_extractor import extract_tables
from document_processing.image_processor import extract_and_describe_images, describe_page_visually
from agent.reasoning import answer_question
from code_generation.generator import generate_chart_code
from code_generation.executor import run_chart_code
from agent.reasoning import build_context_from_chunks
import base64
from flask import Flask, request, jsonify, send_file
from flask import Blueprint, current_app, jsonify, request, send_file
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
@upload_bp.route("/chat", methods=["POST"])
def chat_route():
    body = request.get_json()
    question = body.get("question")
    document_id = body.get("document_id")

    if not question or not document_id:
        return jsonify({"error": "champs 'question' et 'document_id' requis"}), 400

    filters = {"document_id": document_id}
    search_results = search(question, filters=filters)

    answer = answer_question(question, search_results)

    return jsonify({
        "document_id": document_id,
        "question": question,
        "answer": answer,
    })

@upload_bp.route("/chart", methods=["POST"])
def chart_route():
    body = request.get_json()
    question = body.get("question")
    document_id = body.get("document_id")

    if not question or not document_id:
        return jsonify({"error": "champs 'question' et 'document_id' requis"}), 400

    filters = {"document_id": document_id}
    search_results = search(question, filters=filters, n_results=5)
    context = build_context_from_chunks(search_results)
    
    print("=== CONTEXTE ===")
    print(context)
    print("================")

    code = generate_chart_code(question, context)

    print("=== CODE GÉNÉRÉ ===")
    print(code)
    print("===================")

    code = generate_chart_code(question, context)
    result = run_chart_code(code)

    if not result["success"]:
        return jsonify({"error": result["error"], "generated_code": code}), 500

    # Sauvegarde du PNG sur disque au lieu de l'encoder en base64
    results_folder = Path(current_app.config["RESULTS_FOLDER"])
    results_folder.mkdir(parents=True, exist_ok=True)

    chart_path = results_folder / f"{document_id}_chart.png"
    with open(chart_path, "wb") as f:
        f.write(result["chart_bytes"])

    return jsonify({
        "document_id": document_id,
        "question": question,
        "chart_url": f"/api/upload/chart-image/{document_id}",
        "attempts": result["attempts"],
    })


@upload_bp.route("/chart-image/<document_id>", methods=["GET"])
def get_chart_image(document_id):
    """
    Sert directement le fichier PNG généré, consultable dans un navigateur
    ou dans Postman (onglet 'Send and Download' ou aperçu image automatique).
    """
    results_folder = Path(current_app.config["RESULTS_FOLDER"])
    chart_path = results_folder / f"{document_id}_chart.png"

    if not chart_path.exists():
        return jsonify({"error": "Aucun graphique généré pour ce document_id"}), 404

    return send_file(chart_path, mimetype="image/png")