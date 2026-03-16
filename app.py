from flask import Flask
from flask_cors import CORS
from api.auth import auth_bp
from api.dashboard import dashboard_bp
import os

app = Flask(__name__)

# 🔐 SESSION CONFIG (CRITICAL)
app.secret_key = "dev-secret-key"
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

if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
