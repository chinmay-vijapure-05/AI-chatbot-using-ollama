import os
import logging
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from groq import Groq

# ================= Logging =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= Flask App =================
app = Flask(__name__)

# IMPORTANT: required for sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-this")

app.config.update(
    SESSION_COOKIE_SAMESITE="None",  # REQUIRED for cross-origin
    SESSION_COOKIE_SECURE=True       # REQUIRED on HTTPS (Render)
)

# Allow cookies for sessions (important for frontend-hosted apps)
CORS(app, supports_credentials=True)

# ================= Groq Configuration =================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set. AI requests will fail.")

client = Groq(api_key=GROQ_API_KEY)

# ================= Constants =================
MAX_HISTORY_MESSAGES = 10  # keep last N messages only


def call_groq(messages: list) -> str:
    """
    messages: list of dicts like
    [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
        )

        if not response.choices:
            return "No response from AI"

        return response.choices[0].message.content

    except Exception:
        logger.exception("Groq API call failed")
        return "Error: AI service not responding"


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    user_prompt = data["prompt"].strip()

    # ===== Initialize session memory if missing =====
    if "history" not in session:
        session["history"] = []

    # ===== Append user message =====
    session["history"].append({
        "role": "user",
        "content": user_prompt
    })

    # ===== Trim history to avoid token overflow =====
    session["history"] = session["history"][-MAX_HISTORY_MESSAGES:]

    # ===== Call Groq with full conversation =====
    reply = call_groq(session["history"])

    # ===== Append assistant reply =====
    session["history"].append({
        "role": "assistant",
        "content": reply
    })

    session.modified = True

    return jsonify({"reply": reply})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Local dev only — ignored in Docker
    app.run(host="0.0.0.0", port=5000)
