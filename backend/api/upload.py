import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename

from models import db, Document, ChatMessage
from rag.chunking import chunk_text_pages, chunk_tables, chunk_images
from rag.vector_store import index_chunks, search
from document_processing.pdf_parser import extract_text_by_page, get_document_stats
from document_processing.table_extractor import extract_tables
from document_processing.image_processor import extract_and_describe_images, describe_page_visually
from agent.reasoning import answer_question, build_context_from_chunks
from code_generation.generator import generate_chart_code
from code_generation.executor import run_chart_code
from rag.vector_store import index_chunks, search, build_document_filter
from  rag.vector_store import delete_document_chunks  # adapte le chemin d'import
from agent.reasoning import answer_question, build_context_from_chunks, build_sources_from_results
from rag.vector_store import index_chunks, search, build_document_filter, search_with_table_priority
from services.cloud_storage import upload_pdf_to_cloud, local_copy_of
from datetime import datetime
from models import db, Document, Conversation, ChatMessage
upload_bp = Blueprint("upload", __name__)

_ANALYTICAL_KEYWORDS = [
    "compare", "comparaison", "évolution", "évolué", "tendance", "classement",
    "qui a le plus", "qui a le moins", "la plus", "la moins", "part de", "pourcentage",
    "proportion", "total", "somme", "ratio", "écart", "différence", "variation",
    "pourquoi", "explique", "analyse", "contribué", "expliquer",
]


def is_analytical_question(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in _ANALYTICAL_KEYWORDS)
def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


import os
from services.cloud_storage import upload_pdf_to_cloud, local_copy_of

@upload_bp.route("", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni (champ 'file' attendu)"}), 400

    files = request.files.getlist("file")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "Nom de fichier vide"}), 400

    uploaded_docs = []
    errors = []

    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            errors.append(f"{file.filename} : seuls les fichiers PDF sont acceptés")
            continue

        document_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)

        # Sauvegarde temporaire locale, uniquement le temps de l'envoi vers Cloudinary
        tmp_dir = Path(current_app.config["UPLOAD_FOLDER"])
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"{document_id}.pdf"
        file.save(tmp_path)

        cloud_url = upload_pdf_to_cloud(str(tmp_path), public_id=document_id)
        os.remove(tmp_path)  # rien ne reste en local, seule l'URL est conservée

        doc = Document(
            id=document_id,
            filename=filename,
            status="uploaded",
            path=cloud_url,  # URL Cloudinary, plus un chemin disque
        )
        db.session.add(doc)
        uploaded_docs.append(doc)

    db.session.commit()

    return jsonify({
        "uploaded": [doc.to_dict() for doc in uploaded_docs],
        "errors": errors,
    }), 201

    
@upload_bp.route("/status/<document_id>", methods=["GET"])
def get_status(document_id):
    doc = Document.query.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404
    return jsonify({"document_id": doc.id, "status": doc.status})


@upload_bp.route("/extract/<document_id>", methods=["GET"])
def extract_text(document_id):
    doc = Document.query.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    with local_copy_of(doc) as local_path:
        stats = get_document_stats(local_path)
        pages = extract_text_by_page(local_path)

    return jsonify({
        "document_id": document_id,
        "stats": stats,
        "preview": pages[:1],
    })

@upload_bp.route("/extract-tables/<document_id>", methods=["GET"])
def extract_tables_route(document_id):
    doc = Document.query.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    with local_copy_of(doc) as local_path:
        tables = extract_tables(local_path)

    return jsonify({
        "document_id": document_id,
        "num_tables": len(tables),
        "tables": tables,
    })

@upload_bp.route("/extract-images/<document_id>", methods=["GET"])
def extract_images_route(document_id):
    doc = Document.query.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    with local_copy_of(doc) as local_path:
        results = extract_and_describe_images(local_path)

    return jsonify({
        "document_id": document_id,
        "num_images": len(results),
        "images": results,
    })
@upload_bp.route("/describe-page/<document_id>/<int:page_number>", methods=["GET"])
def describe_page_route(document_id, page_number):
    doc = Document.query.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    with local_copy_of(doc) as local_path:
        description = describe_page_visually(local_path, page_number)

    return jsonify({
        "document_id": document_id,
        "page": page_number,
        "description": description,
    })

@upload_bp.route("/index/<document_id>", methods=["POST"])
def index_document(document_id):
    doc = Document.query.get(document_id)
    if not doc:
        return jsonify({"error": "document_id inconnu"}), 404

    if doc.status == "indexed":
        return jsonify({
            "document_id": document_id,
            "status": "already_indexed",
            "message": "Ce document est déjà indexé. Réindexation ignorée.",
        }), 200

    with local_copy_of(doc) as local_path:
        pages = extract_text_by_page(local_path)
        tables = extract_tables(local_path)
        images = extract_and_describe_images(local_path)

    chunks = []
    chunks += chunk_text_pages(pages, document_id, filename=doc.filename)
    chunks += chunk_tables(tables, document_id, filename=doc.filename)
    chunks += chunk_images(images, document_id, filename=doc.filename)

    num_indexed = index_chunks(chunks)

    doc.status = "indexed"
    db.session.commit()

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



from rag.vector_store import index_chunks, search, build_document_filter, search_with_table_priority

@upload_bp.route("/chat", methods=["POST"])
def chat_route():
    body = request.get_json()
    question = body.get("question")
    document_ids = body.get("document_ids") or body.get("document_id")
    conversation_id = body.get("conversation_id")

    if isinstance(document_ids, str):
        document_ids = [document_ids]

    conv = None
    if conversation_id:
        conv = Conversation.query.get(conversation_id)
        if not conv:
            return jsonify({"error": "conversation_id inconnu"}), 404
        document_ids = conv.document_ids  # source de vérité une fois la discussion démarrée

    if not question or not document_ids:
        return jsonify({"error": "champs 'question' et 'document_id(s)' requis"}), 400

    if conv is None:
        conv = Conversation(
            title=question[:60] + ("…" if len(question) > 60 else ""),
            document_ids=document_ids,
        )
        db.session.add(conv)
        db.session.flush()

    n_results = 12 if is_analytical_question(question) else 8
    search_results = search_with_table_priority(question, document_ids, n_results=n_results, n_tables=5)

    answer = answer_question(question, search_results)
    sources = build_sources_from_results(search_results)

    message = ChatMessage(
        conversation_id=conv.id,
        document_id=document_ids[0],
        question=question,
        answer=answer,
        sources=sources,
    )
    db.session.add(message)
    conv.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "conversation_id": conv.id,
        "conversation_title": conv.title,
        "document_ids": document_ids,
        "question": question,
        "answer": answer,
        "sources": sources,
    })



from code_generation.generator import generate_chart_code, classify_chart_intent

@upload_bp.route("/chart", methods=["POST"])
def chart_route():
    body = request.get_json()
    question = body.get("question")
    document_ids = body.get("document_ids") or body.get("document_id")
    conversation_id = body.get("conversation_id")

    if isinstance(document_ids, str):
        document_ids = [document_ids]

    conv = None
    if conversation_id:
        conv = Conversation.query.get(conversation_id)
        if not conv:
            return jsonify({"error": "conversation_id inconnu"}), 404
        document_ids = conv.document_ids

    if not question or not document_ids:
        return jsonify({"error": "champs 'question' et 'document_id(s)' requis"}), 400

    if conv is None:
        conv = Conversation(
            title=question[:60] + ("…" if len(question) > 60 else ""),
            document_ids=document_ids,
        )
        db.session.add(conv)
        db.session.flush()

    filters = build_document_filter(document_ids)
    search_results = search(question, filters=filters, n_results=8)
    context = build_context_from_chunks(search_results)

    chart_intent = classify_chart_intent(question)
    code = generate_chart_code(question, context, chart_intent=chart_intent)
    result = run_chart_code(code)

    if not result["success"]:
        return jsonify({"error": result["error"], "generated_code": code}), 500

    results_folder = Path(current_app.config["RESULTS_FOLDER"])
    results_folder.mkdir(parents=True, exist_ok=True)

    primary_document_id = document_ids[0]

    # UUID unique pour chaque graphique généré
    chart_id = str(uuid.uuid4())

    chart_path = results_folder / f"{chart_id}.png"

    with open(chart_path, "wb") as f:
        f.write(result["chart_bytes"])

    chart_url = f"/api/upload/chart-image/{chart_id}"
    message = ChatMessage(
        conversation_id=conv.id,
        document_id=primary_document_id,
        question=question,
        answer="Graphique généré.",
        chart_url=chart_url,
    )
    db.session.add(message)
    conv.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "conversation_id": conv.id,
        "conversation_title": conv.title,
        "document_ids": document_ids,
        "question": question,
        "chart_type_detected": chart_intent,
        "chart_url": chart_url,
        "attempts": result["attempts"],
    })


@upload_bp.route("/chart-image/<chart_id>", methods=["GET"])
def get_chart_image(chart_id):
    results_folder = Path(current_app.config["RESULTS_FOLDER"])
    chart_path = results_folder / f"{chart_id}.png"

    if not chart_path.exists():
        return jsonify({"error": "Graphique introuvable"}), 404

    response = send_file(chart_path, mimetype="image/png")

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
@upload_bp.route("/documents", methods=["GET"])
def list_documents():
    docs = Document.query.order_by(Document.created_at.desc()).all()
    return jsonify({"documents": [d.to_dict() for d in docs]})

@upload_bp.route("/documents/<document_id>", methods=["DELETE"])
def delete_document(document_id):
    doc = Document.query.get(document_id)

    if not doc:
        return jsonify({"error": "Document introuvable"}), 404

    # Supprimer le fichier PDF
    if doc.path:
        pdf_path = Path(doc.path)
        if pdf_path.exists():
            pdf_path.unlink()

    # Supprimer les vecteurs associés dans ChromaDB
    deleted_chunks = delete_document_chunks(document_id)

    # Supprimer le document de PostgreSQL
    db.session.delete(doc)
    db.session.commit()

    return jsonify({
        "message": "Document supprimé avec succès",
        "document_id": document_id,
        "chunks_supprimes": deleted_chunks
    }), 200
    
@upload_bp.route("/conversations", methods=["GET"])
def list_conversations():
    convs = Conversation.query.order_by(Conversation.updated_at.desc()).all()
    return jsonify({"conversations": [c.to_dict() for c in convs]})


@upload_bp.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    conv = Conversation.query.get(conversation_id)
    if not conv:
        return jsonify({"error": "conversation_id inconnu"}), 404
    return jsonify(conv.to_dict(include_messages=True))


@upload_bp.route("/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    conv = Conversation.query.get(conversation_id)
    if not conv:
        return jsonify({"error": "conversation_id inconnu"}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({"status": "deleted"})

@upload_bp.route("/stats", methods=["GET"])
def get_stats():
    return jsonify({
        "documents": Document.query.count(),
        "indexed_documents": Document.query.filter_by(status="indexed").count(),
        "analyses": Conversation.query.count(),
        "charts": ChatMessage.query.filter(ChatMessage.chart_url.isnot(None)).count(),
    })
    
@upload_bp.route("/reports", methods=["GET"])
def list_reports():
    messages = ChatMessage.query.filter(ChatMessage.chart_url.isnot(None)).order_by(ChatMessage.created_at.desc()).all()
    results = []
    for m in messages:
        doc = Document.query.get(m.document_id)
        results.append({
            "id": m.id,
            "question": m.question,
            "chart_url": m.chart_url,
            "filename": doc.filename if doc else None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    return jsonify({"reports": results})