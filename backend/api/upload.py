import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

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