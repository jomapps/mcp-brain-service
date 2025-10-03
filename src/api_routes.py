"""
REST API routes for Brain Service
Provides HTTP endpoints for nodes, search, and graph operations
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from src.services.knowledge_service import KnowledgeService
from src.lib.embeddings import get_embedding_service
from src.lib.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1")

# Dependency to get knowledge service
async def get_knowledge_service() -> KnowledgeService:
    """Get or create knowledge service instance"""
    from src.lib.embeddings import JinaEmbeddingService
    jina_service = JinaEmbeddingService()
    neo4j_client = await get_neo4j_client()
    return KnowledgeService(jina_service=jina_service, neo4j_client=neo4j_client)

# Request/Response models
class AddNodeRequest(BaseModel):
    type: str = Field(..., description="Node type (e.g., 'gather', 'character', 'document')")
    content: str = Field(..., description="Text content to embed")
    projectId: str = Field(..., description="Project ID for isolation")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional node properties")

class AddNodeResponse(BaseModel):
    node: Dict[str, Any]

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    project_id: str = Field(..., description="Project ID for isolation")
    type: Optional[str] = Field(None, description="Node type filter")
    top_k: int = Field(default=10, description="Number of results to return")
    threshold: Optional[float] = Field(None, description="Similarity threshold (0-1)")

class SearchResult(BaseModel):
    id: str
    type: str
    text: str
    content: str
    score: float
    similarity: float
    metadata: Dict[str, Any]
    relationships: Optional[List[Dict[str, Any]]] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    query_time_ms: float

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str

# API key validation
async def verify_api_key(authorization: str = Header(...)) -> bool:
    """Verify API key from Authorization header"""
    import os
    expected_key = os.getenv("BRAIN_SERVICE_API_KEY", "ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa")

    # Support both "Bearer <token>" and direct token
    token = authorization.replace("Bearer ", "").strip()

    if token != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True

# Routes
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "MCP Brain Service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.post("/nodes", response_model=AddNodeResponse)
async def add_node(
    request: AddNodeRequest,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: bool = Depends(verify_api_key)
):
    """Add a new node to the knowledge graph"""
    try:
        # Store document with embedding
        document_id = await knowledge_service.store_document(
            content=request.content,
            metadata={
                **request.properties,
                "type": request.type,
                "project_id": request.projectId
            },
            project_id=request.projectId
        )

        return {
            "node": {
                "id": document_id,
                "type": request.type,
                "content": request.content,
                "projectId": request.projectId,
                "properties": request.properties
            }
        }
    except Exception as e:
        logger.error(f"Failed to add node: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse)
async def search_nodes(
    request: SearchRequest,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: bool = Depends(verify_api_key)
):
    """Search for similar nodes using semantic search"""
    try:
        import time
        start_time = time.time()

        # Generate embedding for query
        from src.lib.embeddings import JinaEmbeddingService
        jina_service = JinaEmbeddingService()
        query_embedding = await jina_service.embed_single(request.query)

        # Search by embedding
        search_results = await knowledge_service.search_by_embedding(
            embedding=query_embedding,
            project_id=request.project_id,
            limit=request.top_k
        )

        # Filter by type if specified
        filtered_results = search_results.results
        if request.type:
            filtered_results = [
                r for r in filtered_results
                if r.metadata and r.metadata.get("type") == request.type
            ]

        # Filter by threshold if specified
        if request.threshold:
            filtered_results = [
                r for r in filtered_results
                if r.similarity_score and r.similarity_score >= request.threshold
            ]

        # Convert to response format
        results = [
            SearchResult(
                id=result.document_id,
                type=result.metadata.get("type", "unknown") if result.metadata else "unknown",
                text=result.metadata.get("content", "") if result.metadata else "",
                content=result.metadata.get("content", "") if result.metadata else "",
                score=result.similarity_score or 0,
                similarity=result.similarity_score or 0,
                metadata=result.metadata or {},
                relationships=None
            )
            for result in filtered_results
        ]

        query_time = (time.time() - start_time) * 1000

        return SearchResponse(
            results=results,
            total_count=len(results),
            query_time_ms=query_time
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: bool = Depends(verify_api_key)
):
    """Semantic search endpoint (alias for /search)"""
    return await search_nodes(request, knowledge_service, _)

@router.get("/nodes/{node_id}")
async def get_node(
    node_id: str,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: bool = Depends(verify_api_key)
):
    """Get a node by ID"""
    try:
        # Query Neo4j for node
        query = "MATCH (n {id: $node_id}) RETURN n"
        results = await knowledge_service.neo4j.run_query(query, {"node_id": node_id})

        if not results:
            raise HTTPException(status_code=404, detail="Node not found")

        node_data = results[0]["n"]

        return {
            "node": {
                "id": node_data.get("id"),
                "type": node_data.get("type", "unknown"),
                "content": node_data.get("content"),
                "properties": node_data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: bool = Depends(verify_api_key)
):
    """Get service statistics"""
    try:
        # Query Neo4j for stats
        stats_query = """
        MATCH (n)
        RETURN
            count(n) as totalNodes,
            count{(n)-[]-()} as totalRelationships,
            collect(distinct labels(n)[0]) as nodeTypes
        """

        results = await knowledge_service.neo4j.run_query(stats_query, {})

        if results:
            result = results[0]
            return {
                "totalNodes": result.get("totalNodes", 0),
                "totalRelationships": result.get("totalRelationships", 0),
                "nodesByType": {node_type: 0 for node_type in result.get("nodeTypes", [])}
            }

        return {
            "totalNodes": 0,
            "totalRelationships": 0,
            "nodesByType": {}
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        # Return empty stats instead of failing
        return {
            "totalNodes": 0,
            "totalRelationships": 0,
            "nodesByType": {}
        }
