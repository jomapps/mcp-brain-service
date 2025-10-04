"""
REST API routes for Brain Service
Provides HTTP endpoints for nodes, search, and graph operations
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel, Field, ValidationError

from src.services.knowledge_service import KnowledgeService
from src.services.gather_service import GatherService
from src.lib.embeddings import get_embedding_service, JinaEmbeddingService
from src.lib.neo4j_client import get_neo4j_client
from src.lib.llm_client import get_llm_client
from src.models.batch import (
    BatchNodeCreateRequest, BatchNodeCreateResponse,
    DuplicateSearchRequest, DuplicateSearchResponse,
    DepartmentContextRequest, DepartmentContextResponse,
    CoverageAnalysisRequest, CoverageAnalysisResponse,
    BatchErrorResponse, BatchValidationError
)

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

# Dependency to get gather service
async def get_gather_service() -> GatherService:
    """Get or create gather service instance"""
    jina_service = JinaEmbeddingService()
    neo4j_client = await get_neo4j_client()
    llm_client = get_llm_client()
    return GatherService(
        jina_service=jina_service,
        neo4j_client=neo4j_client,
        llm_client=llm_client
    )

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


# ============================================================================
# NEW BATCH ENDPOINTS FOR AUTOMATED GATHER CREATION
# ============================================================================

@router.post("/nodes/batch", response_model=BatchNodeCreateResponse)
async def batch_create_nodes(
    request: BatchNodeCreateRequest,
    gather_service: GatherService = Depends(get_gather_service),
    _: bool = Depends(verify_api_key)
):
    """
    Create multiple nodes in a single batch request

    - **Max batch size**: 50 nodes
    - **Min batch size**: 1 node
    - **Required fields**: type, content, projectId
    - **Performance SLA**: <1000ms for 10 nodes, <4000ms for 50 nodes (95th percentile)
    """
    try:
        # Validate batch size
        if len(request.nodes) < 1 or len(request.nodes) > 50:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "batch_validation_failed",
                    "message": "Batch size must be between 1 and 50 nodes",
                    "details": {"batch_size": len(request.nodes)}
                }
            )

        # Validate each node
        invalid_nodes = []
        for i, node in enumerate(request.nodes):
            if not node.content or not node.content.strip():
                invalid_nodes.append({
                    "index": i,
                    "reason": "Missing or empty content field"
                })
            if not node.type or not node.type.strip():
                invalid_nodes.append({
                    "index": i,
                    "reason": "Missing or empty type field"
                })

        if invalid_nodes:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "batch_validation_failed",
                    "message": "Invalid nodes in batch",
                    "details": {"invalid_nodes": invalid_nodes}
                }
            )

        # Create nodes
        result = await gather_service.batch_create_nodes(request.nodes)

        return BatchNodeCreateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch node creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"Failed to create batch nodes: {str(e)}"
            }
        )


@router.post("/search/duplicates", response_model=DuplicateSearchResponse)
async def search_duplicates(
    request: DuplicateSearchRequest,
    gather_service: GatherService = Depends(get_gather_service),
    _: bool = Depends(verify_api_key)
):
    """
    Find semantically similar nodes to detect duplicates

    - **Threshold**: 0.0-1.0 (default: 0.90)
    - **Limit**: 1-50 results (default: 10)
    - **Performance SLA**: <500ms (95th percentile)
    """
    try:
        result = await gather_service.search_duplicates(
            content=request.content,
            project_id=request.projectId,
            threshold=request.threshold,
            limit=request.limit,
            node_type=request.type,
            department=request.department,
            exclude_node_ids=request.excludeNodeIds
        )

        return DuplicateSearchResponse(**result)

    except Exception as e:
        logger.error(f"Duplicate search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"Failed to search duplicates: {str(e)}"
            }
        )


@router.get("/context/department", response_model=DepartmentContextResponse)
async def get_department_context(
    projectId: str = Query(..., description="Project ID"),
    department: str = Query(..., description="Target department slug"),
    previousDepartments: List[str] = Query(default=[], description="Previous department slugs"),
    limit: int = Query(default=20, ge=1, le=100, description="Nodes per department"),
    gather_service: GatherService = Depends(get_gather_service),
    _: bool = Depends(verify_api_key)
):
    """
    Aggregate context from previous departments

    - **Limit**: 1-100 nodes per department (default: 20)
    - **Performance SLA**: <800ms (95th percentile)
    """
    try:
        # Validate projectId format
        if not projectId or len(projectId) != 24:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_failed",
                    "message": "projectId must be 24 characters"
                }
            )

        result = await gather_service.get_department_context(
            project_id=projectId,
            target_department=department,
            previous_departments=previousDepartments,
            limit=limit
        )

        return DepartmentContextResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Department context retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"Failed to retrieve department context: {str(e)}"
            }
        )


@router.post("/analyze/coverage", response_model=CoverageAnalysisResponse)
async def analyze_coverage(
    request: CoverageAnalysisRequest,
    gather_service: GatherService = Depends(get_gather_service),
    _: bool = Depends(verify_api_key)
):
    """
    Analyze content coverage and identify gaps

    - **Max items**: 100 gather items
    - **Performance SLA**: <1500ms (95th percentile)
    """
    try:
        # Validate gather items count
        if len(request.gatherItems) > 100:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_failed",
                    "message": "Maximum 100 gather items allowed",
                    "details": {"item_count": len(request.gatherItems)}
                }
            )

        result = await gather_service.analyze_coverage(
            project_id=request.projectId,
            department=request.department,
            gather_items=request.gatherItems,
            department_description=request.departmentDescription
        )

        return CoverageAnalysisResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Coverage analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"Failed to analyze coverage: {str(e)}"
            }
        )
