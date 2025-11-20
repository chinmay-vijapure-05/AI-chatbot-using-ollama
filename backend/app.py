from flask import Flask, request, jsonify
from flask_cors import CORS 
import requests

app = Flask(__name__) 
CORS(app) # Enable CORS for frontend-backend requests during development 

def local_ai_model(prompt):
    try:
        response = requests.post(
            'http://localhost:11435/api/generate',
            json={
                'model': 'gemma3:1b',
                'prompt': prompt,
                'stream': False
            }
        )
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.RequestException as e:
        return f"Error calling local AI model: {str(e)}"

@app.route('/api/chat', methods=['POST'])
def chat(): 
    data = request.get_json() 
    if not data or 'prompt' not in data: 
        return jsonify({'error': 'Missing prompt'}), 400 
    prompt = data['prompt'].strip() 
    if not prompt: 
        return jsonify({'reply': '(Empty prompt received)'}), 200 
    reply = local_ai_model(prompt) 
    return jsonify({'reply': reply}) 

if __name__ == "__main__": 
    app.run(port=5000,debug=True)