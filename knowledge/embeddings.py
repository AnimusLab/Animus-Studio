"""
Embedding generation — wraps LiteLLM's embedding endpoint.

Uses text-embedding-3-small by default (1536 dims, matches pgvector schema).
Provider-agnostic: swap model string to use any OpenAI-compatible endpoint.
"""
from __future__ import annotations
import litellm
import structlog

logger = structlog.get_logger()

DEFAULT_EMBED_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


async def embed_text(text: str, model: str = DEFAULT_EMBED_MODEL) -> list[float]:
    """
    Generate a single embedding vector for the given text.
    Returns a list of floats of length EMBEDDING_DIMS.
    """
    # Truncate to ~8k tokens to stay within model limits
    text = text[:32_000]

    response = await litellm.aembedding(model=model, input=[text])
    vector = response.data[0]["embedding"]

    logger.debug("embedding.generated", model=model, dims=len(vector), chars=len(text))
    return vector


async def embed_batch(
    texts: list[str],
    model: str = DEFAULT_EMBED_MODEL,
    batch_size: int = 100,
) -> list[list[float]]:
    """
    Batch-embed a list of texts efficiently.
    Splits into batches to avoid API rate limits.
    """
    all_vectors: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = [t[:32_000] for t in texts[i : i + batch_size]]
        response = await litellm.aembedding(model=model, input=batch)
        vectors = [item["embedding"] for item in response.data]
        all_vectors.extend(vectors)
        logger.debug("embedding.batch", model=model, batch=i // batch_size, count=len(batch))

    return all_vectors
