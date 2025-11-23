import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration from environment
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma:2b')

def call_ollama_model(prompt):
    """Call Ollama API for chat completions."""
    try:
        response = requests.post(
            f'{OLLAMA_HOST}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.Timeout:
        return "Error: Ollama request timed out. Model may still be loading."
    except requests.exceptions.ConnectionError:
        return f"Error: Cannot connect to Ollama at {OLLAMA_HOST}. Is Ollama running?"
    except requests.exceptions.RequestException as e:
        return f"Error calling Ollama: {str(e)}"
    except (KeyError, ValueError):
        return "Error: Unexpected response format from Ollama"

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests."""
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Missing prompt'}), 400
    
    prompt = data['prompt'].strip()
    if not prompt:
        return jsonify({'reply': '(Empty prompt received)'}), 200
    
    reply = call_ollama_model(prompt)
    return jsonify({'reply': reply})

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        response = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'ok', 'service': 'chatbot-api', 'ollama': 'connected'}), 200
        else:
            return jsonify({'status': 'warning', 'service': 'chatbot-api', 'ollama': 'unreachable'}), 503
    except:
        return jsonify({'status': 'warning', 'service': 'chatbot-api', 'ollama': 'unreachable'}), 503

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)