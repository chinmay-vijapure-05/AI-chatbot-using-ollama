# AI Chatbot (Flask + Groq)

A full-stack AI chatbot application with a Flask backend and a static HTML/CSS/JavaScript frontend.  
The chatbot consumes a cloud-hosted LLM via the Groq API.

## Architecture

- **Frontend**: Static HTML/CSS/JavaScript (hosted on Render Static Site)
- **Backend**: Flask REST API (`/api/chat`) running in Docker (Render Web Service)
- **LLM**: Groq (cloud-hosted open-source models)
- **Containerization**: Docker (backend only)

## API Endpoints

- `POST /api/chat`  
  Request:
  ```json
  { "prompt": "Hello" }
