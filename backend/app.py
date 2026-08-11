from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from api.upload import upload_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation de la base de données PostgreSQL
    db.init_app(app)
    with app.app_context():
        db.create_all()  # crée les tables 'documents' et 'chat_history' si elles n'existent pas encore

    app.register_blueprint(upload_bp, url_prefix="/api/upload")
    # Autorise le frontend React (port 5173, celui de Vite) à appeler l'API
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)