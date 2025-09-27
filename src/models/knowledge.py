from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class Document(BaseModel):
    content: str
    metadata: Dict[str, Any]
    document_type: str  # "character", "scene", "dialogue", "workflow", "agent_memory"
    project_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmbeddingResult(BaseModel):
    embedding: List[float]
    document_id: str
    similarity_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchResults(BaseModel):
    results: List[EmbeddingResult]
    total_count: int
    query_time_ms: float

class GraphNode(BaseModel):
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    
class GraphRelationship(BaseModel):
    from_node: str
    to_node: str
    type: str
    properties: Dict[str, Any]

class QueryResults(BaseModel):
    records: List[Dict[str, Any]]
    summary: Dict[str, Any]
    query_time_ms: float

class NeighborResults(BaseModel):
    node_id: str
    neighbors: List[GraphNode]
    relationships: List[GraphRelationship]

class WorkflowData(BaseModel):
    workflow_id: str
    agent_id: str
    step_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time_ms: float
    project_id: str
    timestamp: datetime

class AgentMemory(BaseModel):
    agent_id: str
    memory_type: str  # "conversation", "decision", "context"
    content: str
    metadata: Dict[str, Any]
    project_id: str
    timestamp: datetime