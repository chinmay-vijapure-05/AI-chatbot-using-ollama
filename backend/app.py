import os
import logging
import requests
from flask import Flask, request, jsonify, session, Response, stream_with_context
from flask_cors import CORS
from groq import Groq

# ================= Logging =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= Flask App =================
app = Flask(__name__)

# REQUIRED for sessions
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-this")

app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True
)

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
def is_small_talk(prompt: str) -> bool:
    return prompt.lower().strip() in {
        "hi", "hello", "hey", "hii",
        "thanks", "thank you",
        "ok", "okay"
    }


def should_use_search(prompt: str) -> bool:
    keywords = [
        "latest", "today", "current", "news", "price",
        "who is", "what is", "recent", "update", "now"
    ]
    p = prompt.lower()
    return any(k in p for k in keywords)


def serper_search(query: str) -> str:
    if not SERPER_API_KEY:
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
        res = requests.post(SERPER_URL, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()

        snippets = []
        for item in data.get("organic", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            if title and snippet:
                snippets.append(f"- {title}: {snippet}")

        return "\n".join(snippets)

    except Exception:
        logger.exception("Serper API failed")
        return ""


def call_groq(messages: list, temperature: float = 0.7) -> str:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    except Exception:
        logger.exception("Groq call failed")
        return "Error: AI service not responding"


# ================= Routes =================
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    user_prompt = data["prompt"].strip()

    if "history" not in session:
        session["history"] = []

    # ---- SMALL TALK GUARD ----
    if is_small_talk(user_prompt):
        reply = "Hi! How can I help you today?"
        session["history"].append({"role": "assistant", "content": reply})
        session.modified = True
        return jsonify({"reply": reply})

    # store CLEAN user intent
    session["history"].append({
        "role": "user",
        "content": user_prompt
    })
    session["history"] = session["history"][-MAX_HISTORY_MESSAGES:]

    messages_for_llm = list(session["history"])

    if should_use_search(user_prompt):
        search_context = serper_search(user_prompt)
        if search_context:
            messages_for_llm[-1] = {
                "role": "user",
                "content": (
                    "Use the following web search results to answer accurately.\n\n"
                    f"Search results:\n{search_context}\n\n"
                    f"User question:\n{user_prompt}"
                )
            }

    reply = call_groq(messages_for_llm, temperature=0.3)

    session["history"].append({
        "role": "assistant",
        "content": reply
    })
    session.modified = True

    return jsonify({"reply": reply})


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({"error": "Missing prompt"}), 400

    user_prompt = data["prompt"].strip()

    if "history" not in session:
        session["history"] = []

    # ---- SMALL TALK GUARD (STREAMING) ----
    if is_small_talk(user_prompt):
        def generate():
            yield "data: Hi! How can I help you today?\n\n"
            yield "data: [DONE]\n\n"

        session["history"].append({
            "role": "assistant",
            "content": "Hi! How can I help you today?"
        })
        session.modified = True

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream"
        )

    # store CLEAN user intent
    session["history"].append({
        "role": "user",
        "content": user_prompt
    })
    session["history"] = session["history"][-MAX_HISTORY_MESSAGES:]

    messages_for_llm = list(session["history"])

    if should_use_search(user_prompt):
        search_context = serper_search(user_prompt)
        if search_context:
            messages_for_llm[-1] = {
                "role": "user",
                "content": (
                    "Use the following web search results to answer accurately.\n\n"
                    f"Search results:\n{search_context}\n\n"
                    f"User question:\n{user_prompt}"
                )
            }

    def generate():
        full_reply = ""

        try:
            stream = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages_for_llm,
                temperature=0.3,
                stream=True
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_reply += delta
                    yield f"data: {delta}\n\n"

            session["history"].append({
                "role": "assistant",
                "content": full_reply
            })
            session.modified = True
            yield "data: [DONE]\n\n"

        except Exception:
            logger.exception("Streaming failed")
            yield "data: [ERROR]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream"
    )


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
