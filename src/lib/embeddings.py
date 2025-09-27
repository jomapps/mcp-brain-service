"""Embedding service for generating text embeddings using Jina AI API."""

import logging
import os
from typing import List
import requests

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Jina AI API."""
    
    def __init__(self, model_name: str = "jina-embeddings-v3", api_key: str = None):
        """Initialize embedding service.
        
        Args:
            model_name: Name of the Jina embedding model
            api_key: Jina AI API key (if None, reads from environment)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.api_url = "https://api.jina.ai/v1/embeddings"
        
        if not self.api_key:
            raise ValueError("Jina API key not provided. Set JINA_API_KEY environment variable.")
        
        logger.info(f"Initialized Jina embedding service with model: {model_name}")
    
    async def encode(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Jina AI API.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model_name,
                "input": texts
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]
            
            logger.debug(f"Generated {len(embeddings)} embeddings using Jina API")
            logger.debug(f"Usage: {result.get('usage', 'N/A')}")
            
            return embeddings
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Jina API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = sum(a**2 for a in vec1) ** 0.5
        magnitude2 = sum(b**2 for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Ensure result is between 0 and 1 (convert from [-1,1] to [0,1])
        return max(0.0, min(1.0, (similarity + 1) / 2))


# Global embedding service instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance.
    
    Returns:
        Embedding service instance
    """
    global _embedding_service
    
    if _embedding_service is None:
        # Initialize with production Jina settings
        _embedding_service = EmbeddingService(
            model_name=os.getenv("JINA_MODEL_NAME", "jina-embeddings-v3")
        )
    
    return _embedding_service
