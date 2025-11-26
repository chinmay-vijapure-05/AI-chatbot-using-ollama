from flask import Flask, request, jsonify
from llm_client import generate_text
import os


app = Flask(__name__)
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3")


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True)
    message = body.get("message") or body.get("prompt") or ""
    model = body.get("model", DEFAULT_MODEL)
    try:
        # simple synchronous call
        result = generate_text(model=model, prompt=message)
        # The cloud returns structured JSON; adapt to your existing frontend expectations
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)