"""Embedding service for generating text embeddings."""

import logging
import hashlib
import random
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model_name: str = "jina-embeddings-v4", dimension: int = 768):
        """Initialize embedding service.
        
        Args:
            model_name: Name of the embedding model
            dimension: Embedding vector dimension
        """
        self.model_name = model_name
        self.dimension = dimension
        logger.info(f"Initialized embedding service with model: {model_name}")
    
    async def encode(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = []
            
            for text in texts:
                # For now, create a deterministic embedding based on text hash
                # In production, this would call Jina v4 API
                embedding = self._generate_deterministic_embedding(text)
                embeddings.append(embedding)
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """Generate a deterministic embedding for testing purposes.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        # Create a hash-based seed for reproducible "embeddings"
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)
        
        # Generate deterministic random numbers based on the seed
        rng = random.Random(seed)
        
        # Generate embedding vector
        embedding = []
        for _ in range(self.dimension):
            # Generate values between -1 and 1
            value = rng.random() * 2 - 1
            embedding.append(value)
        
        # Normalize the vector (simple L2 normalization)
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
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
        
        # Ensure result is between 0 and 1
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
        _embedding_service = EmbeddingService()
    
    return _embedding_service