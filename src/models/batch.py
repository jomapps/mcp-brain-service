"""
Pydantic models for batch API endpoints
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional


# ============================================================================
# Batch Node Creation Models
# ============================================================================

class BatchNodeInput(BaseModel):
    """Single node input for batch creation"""
    type: str = Field(..., description="Node type (e.g., 'GatherItem')")
    content: str = Field(..., description="Full text content for embedding generation")
    projectId: str = Field(..., description="Project ID (MongoDB ObjectId format)")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional node properties")
    
    @field_validator('projectId')
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate MongoDB ObjectId format (24 hex characters)"""
        if not v or len(v) != 24:
            raise ValueError("projectId must be 24 characters")
        try:
            int(v, 16)  # Check if valid hex
        except ValueError:
            raise ValueError("projectId must be valid hex string")
        return v


class BatchNodeCreateRequest(BaseModel):
    """Request model for batch node creation"""
    nodes: List[BatchNodeInput] = Field(..., min_length=1, max_length=50, description="List of nodes to create (1-50)")


class BatchNodeOutput(BaseModel):
    """Single node output from batch creation"""
    id: str = Field(..., description="Neo4j internal node ID")
    type: str
    properties: Dict[str, Any]
    embedding: Dict[str, Any] = Field(..., description="Embedding metadata")


class BatchNodeCreateResponse(BaseModel):
    """Response model for batch node creation"""
    success: bool
    created: int
    nodeIds: List[str]
    nodes: List[BatchNodeOutput]
    timing: Dict[str, float]


class BatchValidationError(BaseModel):
    """Validation error for a single node in batch"""
    index: int
    reason: str


class BatchErrorResponse(BaseModel):
    """Error response for batch operations"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Duplicate Search Models
# ============================================================================

class DuplicateSearchRequest(BaseModel):
    """Request model for duplicate search"""
    content: str = Field(..., description="Text content to check for duplicates")
    projectId: str = Field(..., description="Project ID for isolation")
    threshold: float = Field(default=0.90, ge=0.0, le=1.0, description="Similarity threshold")
    limit: int = Field(default=10, ge=1, le=50, description="Max results to return")
    type: Optional[str] = Field(default="GatherItem", description="Filter by node type")
    department: Optional[str] = Field(None, description="Filter by department slug")
    excludeNodeIds: Optional[List[str]] = Field(default_factory=list, description="Node IDs to exclude")
    
    @field_validator('projectId')
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate MongoDB ObjectId format"""
        if not v or len(v) != 24:
            raise ValueError("projectId must be 24 characters")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("projectId must be valid hex string")
        return v


class DuplicateResult(BaseModel):
    """Single duplicate search result"""
    nodeId: str
    similarity: float
    content: str
    properties: Dict[str, Any]


class DuplicateSearchResponse(BaseModel):
    """Response model for duplicate search"""
    duplicates: List[DuplicateResult]
    query_embedding_time_ms: float
    search_time_ms: float
    total_time_ms: float


# ============================================================================
# Department Context Models
# ============================================================================

class DepartmentContextRequest(BaseModel):
    """Request model for department context retrieval"""
    projectId: str = Field(..., description="Project ID")
    department: str = Field(..., description="Target department slug")
    previousDepartments: Optional[List[str]] = Field(default_factory=list, description="Previous department slugs")
    limit: int = Field(default=20, ge=1, le=100, description="Nodes per department")
    
    @field_validator('projectId')
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate MongoDB ObjectId format"""
        if not v or len(v) != 24:
            raise ValueError("projectId must be 24 characters")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("projectId must be valid hex string")
        return v


class DepartmentNode(BaseModel):
    """Node from a department"""
    nodeId: str
    content: str
    summary: Optional[str] = None
    relevance: float


class DepartmentContextData(BaseModel):
    """Context data for a single department"""
    nodeCount: int
    qualityScore: float
    topNodes: List[DepartmentNode]
    keyThemes: List[str]


class RelevantNode(BaseModel):
    """Relevant node across departments"""
    nodeId: str
    department: str
    content: str
    relevanceToTarget: float


class DepartmentContextResponse(BaseModel):
    """Response model for department context"""
    projectId: str
    targetDepartment: str
    context: Dict[str, DepartmentContextData]
    aggregatedSummary: str
    relevantNodes: List[RelevantNode]
    totalNodesAggregated: int
    timing: Dict[str, float]


# ============================================================================
# Coverage Analysis Models
# ============================================================================

class CoverageGatherItem(BaseModel):
    """Gather item for coverage analysis"""
    content: str
    summary: Optional[str] = None


class CoverageAnalysisRequest(BaseModel):
    """Request model for coverage analysis"""
    projectId: str = Field(..., description="Project ID")
    department: str = Field(..., description="Department slug")
    gatherItems: List[CoverageGatherItem] = Field(..., min_length=1, description="Current gather items")
    departmentDescription: Optional[str] = Field(None, description="Department purpose/scope")
    
    @field_validator('projectId')
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate MongoDB ObjectId format"""
        if not v or len(v) != 24:
            raise ValueError("projectId must be 24 characters")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("projectId must be valid hex string")
        return v


class CoveredAspect(BaseModel):
    """Aspect that is covered"""
    aspect: str
    coverage: int = Field(..., ge=0, le=100)
    itemCount: int
    quality: str = Field(..., pattern="^(excellent|good|fair|poor)$")
    items: Optional[List[str]] = Field(default_factory=list)


class CoverageGap(BaseModel):
    """Gap in coverage"""
    aspect: str
    coverage: int = Field(..., ge=0, le=100)
    itemCount: int
    severity: str = Field(..., pattern="^(high|medium|low)$")
    suggestion: str


class CoverageAnalysis(BaseModel):
    """Coverage analysis details"""
    coveredAspects: List[CoveredAspect]
    gaps: List[CoverageGap]
    recommendations: List[str]


class QualityMetrics(BaseModel):
    """Quality metrics for coverage"""
    depth: int = Field(..., ge=0, le=100)
    breadth: int = Field(..., ge=0, le=100)
    coherence: int = Field(..., ge=0, le=100)
    actionability: int = Field(..., ge=0, le=100)


class CoverageAnalysisResponse(BaseModel):
    """Response model for coverage analysis"""
    department: str
    coverageScore: int = Field(..., ge=0, le=100)
    analysis: CoverageAnalysis
    itemDistribution: Dict[str, int]
    qualityMetrics: QualityMetrics
    timing: Dict[str, float]

