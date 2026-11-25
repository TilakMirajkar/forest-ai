import httpx2
from forest_ai.core.config import get_settings

SYSTEM_PROMPT = (
    "You are a gentle journaling companion. Based on the user's recent entries "
    "and mood summary, ask exactly one thoughtful reflective question. "
    "Be supportive. Do not diagnose or give medical or clinical advice. "
    "Reply with the question only."
)


class AIServiceError(Exception):
    """Raised when the local model cannot produce a response."""


def generate_reflection(context: str) -> str:
    settings = get_settings()
    payload = {
        "model": settings.ollama_model,
        "system": SYSTEM_PROMPT,
        "prompt": context,
        "stream": False,
        "options": {"num_predict": 120, "temperature": 0.7},
    }
    try:
        response = httpx2.post(
            f"{settings.ollama_base_url}/api/generate",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx2.HTTPError as exc:
        raise AIServiceError("Local model is unavailable") from exc

    text = response.json().get("response", "").strip()
    if not text:
        raise AIServiceError("Local model returned an empty response")
    return text

def embed_text(text: str) -> list[float]:
    settings = get_settings()
    try:
        response = httpx2.post(
            f"{settings.ollama_base_url}/api/embed",
            json={"model": settings.embedding_model, "input": text},
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx2.HTTPError as exc:
        raise AIServiceError("Embedding model is unavailable") from exc

    embeddings = response.json().get("embeddings", [])
    if not embeddings:
        raise AIServiceError("Embedding model returned no vector")
    return embeddings[0]