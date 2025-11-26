import os
import requests


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "60"))


# Helper to call Ollama Cloud via the /api/generate endpoint.
# If you prefer the Python client from ollama, you can swap to that later.


def generate_text(model: str, prompt: str, stream: bool = False, **kwargs):
    """Return the JSON response from Ollama Cloud generate endpoint.

    model: name of the model (e.g. "gemma3")
    prompt: prompt string
    stream: if True, this returns a generator yielding lines (streamed response)
    kwargs: other optional params passed to the API body (suffix, system, format, etc.)
    """
    url = f"{OLLAMA_HOST.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt}
    payload.update(kwargs)


    headers = {}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
    headers["Content-Type"] = "application/json"


    # streaming behaviour: keep it simple and stream raw lines
    if stream:
        resp = requests.post(url, json=payload, headers=headers, stream=True, timeout=TIMEOUT)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                yield line.decode("utf-8")
        return

    resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()