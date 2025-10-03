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
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j driver not available, using mock client")
            self.driver = None
            self.use_mock = True
        else:
            try:
                self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
                self.use_mock = False
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {str(e)}")
                self.driver = None
                self.use_mock = True
    
    async def create_node(self, labels: List[str], properties: Dict[str, Any]) -> str:
        """Create a node with given labels and properties"""
        if self.use_mock:
            return self._mock_create_node(labels, properties)
        
        try:
            labels_str = ":".join(labels)
            query = f"CREATE (n:{labels_str}) SET n = $properties RETURN n.id as id"
            
            async with self.driver.session() as session:
                result = await session.run(query, properties=properties)
                record = await result.single()
                return record["id"] if record else properties.get("id", "unknown")
        except Exception as e:
            logger.error(f"Failed to create node: {str(e)}")
            raise
    
    async def run_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query and return results"""
        if self.use_mock:
            return self._mock_query_result(query, parameters)
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters or {})
                records = []
                async for record in result:
                    records.append(dict(record))
                return records
        except Exception as e:
            logger.error(f"Failed to run query: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Neo4j connection health"""
        if self.use_mock:
            return {"status": "mock", "timestamp": datetime.utcnow().isoformat()}
        
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record and record["test"] == 1:
                    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
                else:
                    return {"status": "unhealthy", "error": "Invalid response", "timestamp": datetime.utcnow().isoformat()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _mock_create_node(self, labels: List[str], properties: Dict[str, Any]) -> str:
        """Mock node creation for development"""
        node_id = properties.get("id", f"mock_{hash(str(properties)) % 10000}")
        logger.info(f"Mock created node {node_id} with labels {labels}")
        return node_id
    
    def _mock_query_result(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Mock query results for development"""
        logger.info(f"Mock query: {query}")
        
        # Return mock results based on query type
        if "similarity" in query.lower():
            return [
                {"document_id": "mock_1", "content": "Mock content 1", "similarity": 0.95, "metadata": {}},
                {"document_id": "mock_2", "content": "Mock content 2", "similarity": 0.87, "metadata": {}},
            ]
        elif "neighbor" in query.lower():
            return [
                {"neighbor": {"id": "mock_neighbor", "labels": ["MockNode"], "name": "Mock Neighbor"}, 
                 "r": {"type": "RELATED_TO"}, "rel_type": "RELATED_TO"}
            ]
        else:
            return [{"result": "mock_result", "count": 1}]
    
    async def close(self):
        """Close the Neo4j connection"""
        if self.driver and not self.use_mock:
            await self.driver.close()

# Global instance
_neo4j_client = None

async def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client instance"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client