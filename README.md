# AI Chatbot with Ollama

A full-stack AI chatbot application using Flask backend + Nginx frontend, powered by Ollama for running open-source LLMs locally or in containers.

## Architecture

- **Backend**: Flask REST API (`/api/chat` endpoint)
- **Frontend**: Vanilla JavaScript + HTML/CSS with Nginx serving
- **LLM**: Ollama (gemma3 model, customizable)
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Docker & Docker Compose (v2+)
- 4GB+ RAM (for Ollama)
- 5GB+ disk space (for model storage)

## Local Development

### 1. Setup

```bash
# Clone repository
git clone <repo-url>
cd AI-chatbot-using-ollama

# Copy environment template
cp .env.example .env


### Deploying with Ollama Cloud
1. Create an Ollama Cloud API key at https://ollama.com/cloud and copy the key.
2. In Render (or your hosting), set the environment variables:
- `OLLAMA_HOST`: `https://ollama.com` (default)
- `OLLAMA_API_KEY`: *your key* (secret)
- `OLLAMA_MODEL`: the model name (default `gemma3`)
3. Deploy the backend (render: Web Service). Build command: `pip install -r requirements.txt`. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`.
4. (Optional) Deploy frontend as Render Static Site and point API calls to your backend's URL.


Notes: If you prefer OpenAI or another provider later, swap the `llm_client.py` implementation to call that provider and keep the same route contract.