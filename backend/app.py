from flask import Flask
from flask_cors import CORS
from config import Config
from models import db, Document, Conversation, ChatMessage
from api.upload import upload_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        print("DATABASE :", db.engine.url)
        print("TABLES :", db.metadata.tables.keys())

        db.create_all()

    app.register_blueprint(upload_bp, url_prefix="/api/upload")

    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:5173"}}
    )

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)