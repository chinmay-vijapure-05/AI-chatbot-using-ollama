import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS with more restrictive settings
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', '*').split(','),
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuration from environment
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma:2b')
MAX_PROMPT_LENGTH = int(os.getenv('MAX_PROMPT_LENGTH', 10000))

def call_ollama_model(prompt):
    """Call Ollama API for chat completions. Tries /api/chat first, falls back to /api/generate."""
    # Try the chat endpoint first (newer API)
    try:
        response = requests.post(
            f'{OLLAMA_HOST}/api/chat',
            json={
                'model': OLLAMA_MODEL,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'stream': False
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        if 'message' in data:
            content = data['message'].get('content', '')
            if content:
                return content
        elif 'response' in data:
            return data['response']
        # If we get here, response format was unexpected
        logger.warning("Chat endpoint response format unexpected, trying generate endpoint")
    except requests.exceptions.HTTPError as e:
        # If chat endpoint returns 404, try generate endpoint
        if e.response.status_code == 404:
            logger.info("Chat endpoint not available, trying generate endpoint")
        else:
            # For other HTTP errors, re-raise to be handled by outer exception handler
            raise
    except (KeyError, ValueError):
        # If response format is unexpected, try generate endpoint
        logger.info("Chat endpoint response format unexpected, trying generate endpoint")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        # For network errors, re-raise to be handled by outer exception handler
        raise
    
    # Fallback to generate endpoint (older API, more widely supported)
    try:
        response = requests.post(
            f'{OLLAMA_HOST}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        if 'response' in data:
            return data['response']
        else:
            logger.error(f"Unexpected response format from generate endpoint: {data}")
            return "Error: Unexpected response format from Ollama"
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out")
        return "Error: Ollama request timed out. Model may still be loading."
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Ollama at {OLLAMA_HOST}")
        return f"Error: Cannot connect to Ollama at {OLLAMA_HOST}. Is Ollama running?"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Ollama: {str(e)}")
        return f"Error calling Ollama: {str(e)}"
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing Ollama response: {str(e)}")
        return "Error: Unexpected response format from Ollama"

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests."""
    try:
        # Validate request size
        if request.content_length and request.content_length > 1024 * 1024:  # 1MB limit
            return jsonify({'error': 'Request too large'}), 413
        
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt'}), 400
        
        prompt = data['prompt'].strip()
        if not prompt:
            return jsonify({'reply': '(Empty prompt received)'}), 200
        
        # Validate prompt length
        if len(prompt) > MAX_PROMPT_LENGTH:
            return jsonify({'error': f'Prompt too long. Maximum length is {MAX_PROMPT_LENGTH} characters'}), 400
        
        logger.info(f"Processing chat request (length: {len(prompt)})")
        reply = call_ollama_model(prompt)
        return jsonify({'reply': reply})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        response = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'ok', 'service': 'chatbot-api', 'ollama': 'connected'}), 200
        else:
            logger.warning(f"Ollama health check returned status {response.status_code}")
            return jsonify({'status': 'warning', 'service': 'chatbot-api', 'ollama': 'unreachable'}), 503
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ollama health check failed: {str(e)}")
        return jsonify({'status': 'warning', 'service': 'chatbot-api', 'ollama': 'unreachable'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        return jsonify({'status': 'error', 'service': 'chatbot-api', 'ollama': 'unknown'}), 500

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)