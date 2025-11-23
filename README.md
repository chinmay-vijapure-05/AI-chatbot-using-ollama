# AI Chatbot with Ollama

A full-stack AI chatbot application using Flask backend + Nginx frontend, powered by Ollama for running open-source LLMs locally or in containers.

## Architecture

- **Backend**: Flask REST API (`/api/chat` endpoint)
- **Frontend**: Vanilla JavaScript + HTML/CSS with Nginx serving
- **LLM**: Ollama (gemma:2b model, customizable)
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