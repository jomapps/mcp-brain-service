"""Embedding service for generating text embeddings using Jina AI API."""

import asyncio
import aiohttp
import os
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class JinaEmbeddingService:
    def __init__(self):
        """Initialize Jina embedding service - REQUIRES valid API key"""
        self.api_key = os.getenv("JINA_API_KEY")
        self.api_url = os.getenv("JINA_API_URL", "https://api.jina.ai/v1/embeddings")
        self.model = os.getenv("JINA_MODEL", "jina-embeddings-v2-base-en")
        self.max_retries = 3
        self.timeout = 30

        # Validate required API key
        if not self.api_key:
            raise ValueError(
                "JINA_API_KEY environment variable is required. "
                "Jina AI is critical for embedding generation in Brain service. "
                "Get your API key from https://jina.ai and set JINA_API_KEY environment variable."
            )

        logger.info(f"Jina embedding service initialized with model: {self.model}")

    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text"""
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding with retry logic"""
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }

                    if str(self.model).startswith("jina-embeddings-v4"):
                        payload = {
                            "model": self.model,
                            "input": [{"text": t} for t in texts]
                        }
                    else:
                        payload = {
                            "model": self.model,
                            "input": texts,
                            "encoding_format": "float"
                        }

                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            embeddings = [item["embedding"] for item in data["data"]]
                            logger.debug(f"Generated {len(embeddings)} embeddings")
                            return embeddings
                        elif response.status == 429:  # Rate limit
                            wait_time = 2 ** attempt
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                        elif response.status == 401:
                            error_text = await response.text()
                            raise Exception(
                                f"Jina API authentication failed: {error_text}. "
                                f"Please verify JINA_API_KEY is correct."
                            )
                        else:
                            error_text = await response.text()
                            raise Exception(f"Jina API error {response.status}: {error_text}")

            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                if attempt == self.max_retries - 1:
                    raise Exception(
                        f"Jina API timeout after {self.max_retries} retries. "
                        f"Check network connectivity to {self.api_url}"
                    )
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to get embeddings after {self.max_retries} attempts: {str(e)}")
                    raise Exception(f"Jina embedding failed: {str(e)}") from e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
                await asyncio.sleep(2 ** attempt)

        raise Exception(f"Failed to get embeddings after {self.max_retries} retries")

    async def embed_image(self, image_data: bytes) -> List[float]:
        """Image embedding support (future feature)"""
        raise NotImplementedError(
            "Image embedding not yet implemented. "
            "Jina AI image embeddings will be supported in future version."
        )

    async def health_check(self) -> dict:
        """Check Jina API health"""
        try:
            # Test with a simple embedding
            await self.embed_single("health check")
            return {
                "status": "healthy",
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class EmbeddingService:
    """Thin adapter interface around JinaEmbeddingService used by the app."""
    def __init__(self, backend: Optional[JinaEmbeddingService] = None):
        self.backend = backend or JinaEmbeddingService()

    async def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode a list of texts into embeddings."""
        return await self.backend.embed_batch(texts)

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        import math
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

# Global embedding service instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance.

    Returns:
        Embedding service instance
    """
    global _embedding_service

    if _embedding_service is None:
        # Initialize adapter backed by JinaEmbeddingService
        _embedding_service = EmbeddingService()

    return _embedding_service
