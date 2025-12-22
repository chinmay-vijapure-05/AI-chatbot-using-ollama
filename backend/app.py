import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ===== Groq Configuration =====
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY is not set. AI requests will fail.")

client = Groq(api_key=GROQ_API_KEY)


def call_groq(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
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

    reply = call_groq(data["prompt"])
    return jsonify({"reply": reply})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Local dev only — ignored in Docker
    app.run(host="0.0.0.0", port=5000)
