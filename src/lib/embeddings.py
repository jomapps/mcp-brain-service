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
        self.api_key = os.getenv("JINA_API_KEY")
        self.api_url = os.getenv("JINA_API_URL", "https://api.jina.ai/v1/embeddings")
        self.model = os.getenv("JINA_MODEL", "jina-embeddings-v2-base-en")
        self.max_retries = 3
        self.timeout = 30
        
        if not self.api_key:
            logger.warning("JINA_API_KEY not set, using mock embeddings")
            self.use_mock = True
        else:
            self.use_mock = False
    
    async def embed_single(self, text: str) -> List[float]:
        """Embed a single text"""
        if self.use_mock:
            return self._mock_embedding(text)
        
        return (await self.embed_batch([text]))[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding with retry logic"""
        if self.use_mock:
            return [self._mock_embedding(text) for text in texts]
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {
                        "model": self.model,
                        "input": texts,
                        "encoding_format": "float"
                    }
                    
                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return [item["embedding"] for item in data["data"]]
                        elif response.status == 429:  # Rate limit
                            wait_time = 2 ** attempt
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            raise Exception(f"Jina API error {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                if attempt == self.max_retries - 1:
                    raise Exception("Jina API timeout after all retries")
                await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to get embeddings after {self.max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Failed to get embeddings after all retries")
    
    async def embed_image(self, image_data: bytes) -> List[float]:
        """Image embedding support (future feature)"""
        if self.use_mock:
            return self._mock_embedding("image_data")
        
        # TODO: Implement image embedding when Jina supports it
        raise NotImplementedError("Image embedding not yet implemented")
    
    def _mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for development"""
        import hashlib
        import struct
        
        # Create deterministic mock embedding based on text hash
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 768-dimensional vector (typical embedding size)
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            if i + 1 < len(hash_bytes):
                val = struct.unpack('h', hash_bytes[i:i+2])[0] / 32768.0
                embedding.append(val)
        
        # Pad to 768 dimensions
        while len(embedding) < 768:
            embedding.append(0.0)
        
        return embedding[:768]
    
    async def health_check(self) -> dict:
        """Check Jina API health"""
        if self.use_mock:
            return {"status": "mock", "timestamp": datetime.utcnow().isoformat()}
        
        try:
            # Test with a simple embedding
            await self.embed_single("health check")
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}


# Global embedding service instance
_embedding_service: JinaEmbeddingService = None


def get_embedding_service() -> JinaEmbeddingService:
    """Get global embedding service instance.
    
    Returns:
        Embedding service instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        # Initialize with production Jina settings
        _embedding_service = JinaEmbeddingService()
    
    return _embedding_service
