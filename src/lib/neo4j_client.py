import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        """Initialize Neo4j client - REQUIRES valid Neo4j connection"""
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")

        # Validate required environment variables
        if not self.uri:
            raise ValueError(
                "NEO4J_URI environment variable is required. "
                "Neo4j is critical for Brain service operation. "
                "Please set NEO4J_URI (e.g., bolt://localhost:7687 or neo4j://host:7687)"
            )

        if not self.user:
            raise ValueError(
                "NEO4J_USER environment variable is required. "
                "Neo4j is critical for Brain service operation."
            )

        if not self.password:
            raise ValueError(
                "NEO4J_PASSWORD environment variable is required. "
                "Neo4j is critical for Brain service operation."
            )

        # Check if Neo4j driver is available
        if not NEO4J_AVAILABLE:
            raise ImportError(
                "Neo4j driver is not installed. "
                "Neo4j is critical for Brain service operation. "
                "Install with: pip install neo4j"
            )

        # Initialize driver
        try:
            logger.info(f"Connecting to Neo4j at {self.uri}")
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            logger.info("Neo4j driver initialized successfully")
        except Exception as e:
            error_msg = (
                f"Failed to initialize Neo4j driver: {str(e)}. "
                f"Neo4j is critical for Brain service operation. "
                f"Please verify NEO4J_URI={self.uri}, NEO4J_USER={self.user}, "
                f"and NEO4J_PASSWORD are correct and Neo4j is running."
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    async def verify_connection(self):
        """Verify Neo4j connection on startup"""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record and record["test"] == 1:
                    logger.info("✅ Neo4j connection verified successfully")
                    return True
                else:
                    raise Exception("Invalid response from Neo4j")
        except Exception as e:
            error_msg = (
                f"Neo4j connection verification failed: {str(e)}. "
                f"Neo4j is critical for Brain service operation. "
                f"Please verify Neo4j is running at {self.uri} and credentials are correct."
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    async def create_node(self, labels: List[str], properties: Dict[str, Any]) -> str:
        """Create a node with given labels and properties"""
        try:
            labels_str = ":".join(labels)
            query = f"CREATE (n:{labels_str}) SET n = $properties RETURN n.id as id"

            async with self.driver.session() as session:
                result = await session.run(query, properties=properties)
                record = await result.single()
                node_id = record["id"] if record else properties.get("id", "unknown")
                logger.debug(f"Created node {node_id} with labels {labels}")
                return node_id
        except Exception as e:
            logger.error(f"Failed to create node: {str(e)}")
            raise Exception(f"Neo4j create_node failed: {str(e)}") from e

    async def run_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query and return results"""
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters or {})
                records = []
                async for record in result:
                    records.append(dict(record))
                logger.debug(f"Query returned {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Failed to run query: {str(e)}")
            raise Exception(f"Neo4j query failed: {str(e)}") from e

    async def health_check(self) -> Dict[str, Any]:
        """Check Neo4j connection health"""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record and record["test"] == 1:
                    return {
                        "status": "healthy",
                        "uri": self.uri,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "Invalid response from Neo4j",
                        "uri": self.uri,
                        "timestamp": datetime.utcnow().isoformat()
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "uri": self.uri,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

# Global instance
_neo4j_client = None

async def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client instance"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
        # Verify connection on first initialization
        await _neo4j_client.verify_connection()
    return _neo4j_client
