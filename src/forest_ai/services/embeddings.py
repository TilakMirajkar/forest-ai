import logging

from forest_ai.services.ai import AIServiceError, embed_text

logger = logging.getLogger(__name__)


def try_embed(content: str) -> list[float] | None:
    """Embed text, or return None if the model is down. Saving must not fail."""
    try:
        return embed_text(content)
    except AIServiceError:
        logger.warning("Embedding skipped: model unavailable")
        return None