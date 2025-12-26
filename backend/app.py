import os
import logging
import requests
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

# Allow cookies for sessions
CORS(app, supports_credentials=True)

# ================= Groq Configuration =================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

client = Groq(api_key=GROQ_API_KEY)

# ================= Serper Configuration =================
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

# ================= Constants =================
MAX_HISTORY_MESSAGES = 10
MAX_SEARCH_RESULTS = 5


# ================= Utilities =================
def should_use_search(prompt: str) -> bool:
    """
    Heuristic to decide when web search is needed
    """
    keywords = [
        "latest", "today", "current", "news", "price",
        "who is", "what is", "recent", "update", "now"
    ]
    prompt_lower = prompt.lower()
    return any(k in prompt_lower for k in keywords)


def serper_search(query: str) -> str:
    """
    Calls Serper API and returns formatted snippets
    """
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not set. Skipping search.")
        return ""

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "q": query,
        "num": MAX_SEARCH_RESULTS
    }

    try:
        response = requests.post(
            SERPER_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        snippets = []
        for item in data.get("organic", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            if title and snippet:
                snippets.append(f"- {title}: {snippet}")

        return "\n".join(snippets)

    except Exception:
        logger.exception("Serper API call failed")
        return ""


def call_groq(messages: list) -> str:
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


# ================= Routes =================
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    user_prompt = data["prompt"].strip()

    # ===== Init session history =====
    if "history" not in session:
        session["history"] = []

    # ===== Decide if search is needed =====
    search_context = ""
    if should_use_search(user_prompt):
        search_context = serper_search(user_prompt)

    # ===== Build message to LLM =====
    if search_context:
        augmented_prompt = (
            "Use the following web search results to answer accurately.\n\n"
            f"Search results:\n{search_context}\n\n"
            f"User question:\n{user_prompt}"
        )
    else:
        augmented_prompt = user_prompt

    session["history"].append({
        "role": "user",
        "content": augmented_prompt
    })

    session["history"] = session["history"][-MAX_HISTORY_MESSAGES:]

    # ===== Call Groq =====
    reply = call_groq(session["history"])

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
    app.run(host="0.0.0.0", port=5000)
