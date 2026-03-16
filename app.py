from flask import Flask, send_from_directory
from flask_cors import CORS
from api.auth import auth_bp
from api.dashboard import dashboard_bp
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")

# 🔐 SESSION CONFIG (CRITICAL)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # True only for HTTPS

# 🔓 CORS CONFIG (CRITICAL)
CORS(
    app,
    supports_credentials=True)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return {"error": "Not Found"}, 404

    if path and (FRONTEND_DIST / path).exists():
        return send_from_directory(FRONTEND_DIST, path)

    if (FRONTEND_DIST / "index.html").exists():
        return send_from_directory(FRONTEND_DIST, "index.html")

    return {"error": "Frontend build not found. Build frontend before running."}, 500

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
