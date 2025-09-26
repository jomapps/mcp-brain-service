"""Database connection and configuration."""

import logging
import os
from typing import AsyncContextManager, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j database connection manager."""
    
    def __init__(
        self,
        uri: str = "neo4j://localhost:7687",
        user: str = "neo4j", 
        password: str = "password"
    ):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            user: Database username
            password: Database password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[AsyncDriver] = None
    
    async def connect(self) -> AsyncDriver:
        """Connect to Neo4j database.
        
        Returns:
            Async Neo4j driver instance
        """
        if self._driver is None:
            try:
                self._driver = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password)
                )
                
                # Test connection
                async with self._driver.session() as session:
                    await session.run("RETURN 1")
                
                logger.info(f"Connected to Neo4j at {self.uri}")
                
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise
        
        return self._driver
    
    async def close(self) -> None:
        """Close database connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    def session(self) -> AsyncContextManager:
        """Get database session context manager."""
        if self._driver is None:
            raise RuntimeError("Not connected to database. Call connect() first.")
        
        return self._driver.session()


def get_neo4j_config() -> dict:
    """Get Neo4j configuration from environment variables.
    
    Returns:
        Neo4j configuration dictionary
    """
    return {
        "uri": os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password")
    }


# Global connection instance
_neo4j_connection: Optional[Neo4jConnection] = None


async def get_neo4j_connection() -> Neo4jConnection:
    """Get or create Neo4j connection instance.
    
    Returns:
        Neo4j connection instance
    """
    global _neo4j_connection
    
    if _neo4j_connection is None:
        config = get_neo4j_config()
        _neo4j_connection = Neo4jConnection(**config)
        await _neo4j_connection.connect()
    
    return _neo4j_connection


async def close_neo4j_connection() -> None:
    """Close global Neo4j connection."""
    global _neo4j_connection
    
    if _neo4j_connection:
        await _neo4j_connection.close()
        _neo4j_connection = None