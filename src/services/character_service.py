"""Character service for managing character operations."""

import logging
from datetime import datetime
from typing import List, Optional

from src.models.character import Character, CharacterCreate, CharacterSearchResult
from src.lib.database import Neo4jConnection
from src.lib.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class CharacterService:
    """Service for managing character operations."""
    
    def __init__(self, neo4j_connection: Optional[Neo4jConnection] = None, embedding_service: Optional[EmbeddingService] = None):
        """Initialize the character service.
        
        Args:
            neo4j_connection: Neo4j database connection
            embedding_service: Embedding service for generating embeddings
        """
        self.neo4j_connection = neo4j_connection
        self.embedding_service = embedding_service
    
    async def create_character(self, character_data: CharacterCreate) -> Character:
        """Create a new character with embeddings.
        
        Args:
            character_data: Character creation data
            
        Returns:
            Created character with generated embeddings
            
        Raises:
            Exception: If character creation fails
        """
        try:
            # Create character instance
            character = Character(**character_data.dict())
            
            # Generate embeddings for personality and appearance
            if self.embedding_service:
                embeddings = await self.embedding_service.encode([
                    character.personality_description,
                    character.appearance_description
                ])
                character.embedding_personality = embeddings[0]
                character.embedding_appearance = embeddings[1]
            
            # Store character in Neo4j database
            if self.neo4j_connection:
                await self._store_character_in_db(character)
            
            logger.info(f"Created character: {character.name} (ID: {character.id})")
            return character
            
        except Exception as e:
            logger.error(f"Failed to create character: {str(e)}")
            raise
    
    async def find_similar_characters(
        self, 
        project_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[CharacterSearchResult]:
        """Find characters similar to the given query.
        
        Args:
            project_id: Project ID to search within
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of similar characters with similarity scores
            
        Raises:
            Exception: If search fails
        """
        try:
            if not query.strip():
                logger.warning("Empty query provided for character search")
                return []
            
            # Generate embedding for the query
            query_embedding = None
            if self.embedding_service:
                embeddings = await self.embedding_service.encode([query])
                query_embedding = embeddings[0]
            
            # Search for similar characters in the database
            results = []
            if self.neo4j_connection and query_embedding:
                results = await self._search_similar_characters(
                    project_id, query_embedding, limit
                )
            
            logger.info(f"Found {len(results)} similar characters for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar characters: {str(e)}")
            raise
    
    
    async def _store_character_in_db(self, character: Character) -> None:
        """Store character in Neo4j database.
        
        Args:
            character: Character to store
        """
        if not self.neo4j_connection:
            logger.warning("No Neo4j connection configured, skipping database storage")
            return
        
        try:
            async with self.neo4j_connection.session() as session:
                # Create character node in Neo4j
                query = """
                CREATE (c:Character {
                    id: $id,
                    project_id: $project_id,
                    name: $name,
                    personality_description: $personality_description,
                    appearance_description: $appearance_description,
                    embedding_personality: $embedding_personality,
                    embedding_appearance: $embedding_appearance,
                    created_at: $created_at,
                    updated_at: $updated_at
                })
                RETURN c
                """
                
                await session.run(query, {
                    "id": character.id,
                    "project_id": character.project_id,
                    "name": character.name,
                    "personality_description": character.personality_description,
                    "appearance_description": character.appearance_description,
                    "embedding_personality": character.embedding_personality,
                    "embedding_appearance": character.embedding_appearance,
                    "created_at": character.created_at.isoformat(),
                    "updated_at": character.updated_at.isoformat()
                })
                
            logger.debug(f"Stored character in database: {character.id}")
            
        except Exception as e:
            logger.error(f"Failed to store character in database: {str(e)}")
            raise
    
    async def _search_similar_characters(
        self, 
        project_id: str, 
        query_embedding: List[float], 
        limit: int
    ) -> List[CharacterSearchResult]:
        """Search for similar characters using vector similarity.
        
        Args:
            project_id: Project ID to search within
            query_embedding: Query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of similar characters with similarity scores
        """
        if not self.neo4j_connection:
            logger.warning("No Neo4j connection configured, returning empty results")
            return []
        
        try:
            async with self.neo4j_connection.session() as session:
                # Get all characters in the project with their embeddings
                query = """
                MATCH (c:Character {project_id: $project_id})
                RETURN c.id as id, c.name as name, 
                       c.embedding_personality as embedding_personality,
                       c.embedding_appearance as embedding_appearance
                """
                
                result = await session.run(query, {"project_id": project_id})
                
                characters = []
                records = [record async for record in result]
                
                for record in records:
                    # Calculate similarity with both personality and appearance embeddings
                    personality_sim = 0.0
                    appearance_sim = 0.0
                    
                    if (record["embedding_personality"] and 
                        self.embedding_service and 
                        len(query_embedding) > 0):
                        
                        personality_sim = self.embedding_service.cosine_similarity(
                            query_embedding, 
                            record["embedding_personality"]
                        )
                    
                    if (record["embedding_appearance"] and 
                        self.embedding_service and 
                        len(query_embedding) > 0):
                        
                        appearance_sim = self.embedding_service.cosine_similarity(
                            query_embedding,
                            record["embedding_appearance"]
                        )
                    
                    # Combined similarity score (weighted average)
                    combined_similarity = (personality_sim * 0.7 + appearance_sim * 0.3)
                    
                    characters.append(CharacterSearchResult(
                        id=record["id"],
                        name=record["name"],
                        similarity_score=combined_similarity
                    ))
                
                # Sort by similarity score (highest first) and limit results
                characters.sort(key=lambda x: x.similarity_score, reverse=True)
                
                return characters[:limit]
                
        except Exception as e:
            logger.error(f"Failed to search similar characters: {str(e)}")
            raise