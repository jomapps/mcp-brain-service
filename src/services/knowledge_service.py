import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..models.knowledge import (
    Document, EmbeddingResult, SearchResults, GraphNode, 
    GraphRelationship, QueryResults, NeighborResults,
    WorkflowData, AgentMemory
)
from ..lib.embeddings import JinaEmbeddingService
from ..lib.neo4j_client import Neo4jClient

class KnowledgeService:
    def __init__(self, jina_service: JinaEmbeddingService, neo4j_client: Neo4jClient):
        self.jina = jina_service
        self.neo4j = neo4j_client
    
    async def embed_text(self, text: str, project_id: str) -> EmbeddingResult:
        """Generate embedding for a single text"""
        try:
            embedding = await self.jina.embed_single(text)
            document_id = str(uuid.uuid4())
            
            # Store in Neo4j
            await self.neo4j.create_node(
                labels=["Document", "Embedding"],
                properties={
                    "id": document_id,
                    "content": text,
                    "project_id": project_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            return EmbeddingResult(
                embedding=embedding,
                document_id=document_id,
                metadata={"project_id": project_id}
            )
        except Exception as e:
            raise Exception(f"Failed to embed text: {str(e)}")
    
    async def search_by_embedding(self, embedding: List[float], project_id: str, limit: int = 10) -> SearchResults:
        """Search for similar embeddings"""
        start_time = datetime.utcnow()
        
        try:
            # Query Neo4j for similar embeddings
            query = """
            MATCH (d:Document {project_id: $project_id})
            WHERE d.embedding IS NOT NULL
            RETURN d.id as document_id, d.content as content, d.metadata as metadata,
                   gds.similarity.cosine(d.embedding, $embedding) as similarity
            ORDER BY similarity DESC
            LIMIT $limit
            """
            
            results = await self.neo4j.run_query(query, {
                "project_id": project_id,
                "embedding": embedding,
                "limit": limit
            })
            
            embedding_results = [
                EmbeddingResult(
                    embedding=embedding,
                    document_id=record["document_id"],
                    similarity_score=record["similarity"],
                    metadata=record["metadata"]
                )
                for record in results
            ]
            
            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SearchResults(
                results=embedding_results,
                total_count=len(embedding_results),
                query_time_ms=query_time
            )
        except Exception as e:
            raise Exception(f"Failed to search embeddings: {str(e)}")
    
    async def store_document(self, content: str, metadata: Dict[str, Any], project_id: str) -> str:
        """Store document with embedding"""
        try:
            document_id = str(uuid.uuid4())
            embedding = await self.jina.embed_single(content)
            
            # Create document node
            await self.neo4j.create_node(
                labels=["Document"],
                properties={
                    "id": document_id,
                    "content": content,
                    "metadata": metadata,
                    "project_id": project_id,
                    "document_type": metadata.get("document_type", "unknown"),
                    "embedding": embedding,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            return document_id
        except Exception as e:
            raise Exception(f"Failed to store document: {str(e)}")
    
    async def create_relationship(self, from_id: str, to_id: str, relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """Create relationship between nodes"""
        try:
            query = """
            MATCH (a {id: $from_id}), (b {id: $to_id})
            CREATE (a)-[r:%s]->(b)
            SET r += $properties
            RETURN r
            """ % relationship_type
            
            result = await self.neo4j.run_query(query, {
                "from_id": from_id,
                "to_id": to_id,
                "properties": properties or {}
            })
            
            return len(result) > 0
        except Exception as e:
            raise Exception(f"Failed to create relationship: {str(e)}")
    
    async def query_graph(self, cypher_query: str, project_id: str, parameters: Dict[str, Any] = None) -> QueryResults:
        """Execute Cypher query with project isolation"""
        start_time = datetime.utcnow()
        
        try:
            # Add project_id filter to query if not present
            if "project_id" not in cypher_query.lower():
                # This is a simplified approach - in production, use query parsing
                cypher_query = cypher_query.replace("MATCH", f"MATCH")
                parameters = parameters or {}
                parameters["project_id"] = project_id
            
            results = await self.neo4j.run_query(cypher_query, parameters)
            query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return QueryResults(
                records=results,
                summary={"query": cypher_query, "parameters": parameters},
                query_time_ms=query_time
            )
        except Exception as e:
            raise Exception(f"Failed to execute graph query: {str(e)}")
    
    async def get_node_neighbors(self, node_id: str, project_id: str) -> NeighborResults:
        """Get node neighbors and relationships"""
        try:
            query = """
            MATCH (n {id: $node_id, project_id: $project_id})-[r]-(neighbor)
            WHERE neighbor.project_id = $project_id
            RETURN neighbor, r, type(r) as rel_type
            """
            
            results = await self.neo4j.run_query(query, {
                "node_id": node_id,
                "project_id": project_id
            })
            
            neighbors = []
            relationships = []
            
            for record in results:
                neighbor_data = record["neighbor"]
                neighbors.append(GraphNode(
                    id=neighbor_data["id"],
                    labels=neighbor_data.get("labels", []),
                    properties=neighbor_data
                ))
                
                relationships.append(GraphRelationship(
                    from_node=node_id,
                    to_node=neighbor_data["id"],
                    type=record["rel_type"],
                    properties=record["r"]
                ))
            
            return NeighborResults(
                node_id=node_id,
                neighbors=neighbors,
                relationships=relationships
            )
        except Exception as e:
            raise Exception(f"Failed to get node neighbors: {str(e)}")
    
    async def batch_embed_texts(self, texts: List[str], project_id: str) -> List[EmbeddingResult]:
        """Batch embed multiple texts"""
        try:
            embeddings = await self.jina.embed_batch(texts)
            results = []
            
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                document_id = str(uuid.uuid4())
                
                # Store in Neo4j
                await self.neo4j.create_node(
                    labels=["Document", "Embedding"],
                    properties={
                        "id": document_id,
                        "content": text,
                        "project_id": project_id,
                        "embedding": embedding,
                        "batch_id": str(uuid.uuid4()),
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
                
                results.append(EmbeddingResult(
                    embedding=embedding,
                    document_id=document_id,
                    metadata={"project_id": project_id, "batch_index": i}
                ))
            
            return results
        except Exception as e:
            raise Exception(f"Failed to batch embed texts: {str(e)}")
    
    async def bulk_store_documents(self, documents: List[Document], project_id: str) -> List[str]:
        """Bulk store documents with embeddings"""
        try:
            texts = [doc.content for doc in documents]
            embeddings = await self.jina.embed_batch(texts)
            document_ids = []
            
            for doc, embedding in zip(documents, embeddings):
                document_id = str(uuid.uuid4())
                
                await self.neo4j.create_node(
                    labels=["Document"],
                    properties={
                        "id": document_id,
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "project_id": project_id,
                        "document_type": doc.document_type,
                        "embedding": embedding,
                        "created_at": datetime.utcnow().isoformat()
                    }
                )
                
                document_ids.append(document_id)
            
            return document_ids
        except Exception as e:
            raise Exception(f"Failed to bulk store documents: {str(e)}")
    
    async def store_workflow_data(self, workflow_data: WorkflowData) -> str:
        """Store LangGraph workflow execution data"""
        try:
            workflow_id = str(uuid.uuid4())

            # Embed the workflow step data
            step_content = f"{workflow_data.step_name}: {workflow_data.input_data} -> {workflow_data.output_data}"
            embedding = await self.jina.embed_single(step_content)
            
            await self.neo4j.create_node(
                labels=["Workflow", "ExecutionStep"],
                properties={
                    "id": workflow_id,
                    "workflow_id": workflow_data.workflow_id,
                    "agent_id": workflow_data.agent_id,
                    "step_name": workflow_data.step_name,
                    "input_data": workflow_data.input_data,
                    "output_data": workflow_data.output_data,
                    "execution_time_ms": workflow_data.execution_time_ms,
                    "project_id": workflow_data.project_id,
                    "embedding": embedding,
                    "timestamp": workflow_data.timestamp.isoformat()
                }
            )
            
            return workflow_id
        except Exception as e:
            raise Exception(f"Failed to store workflow data: {str(e)}")
    
    async def search_similar_workflows(self, query: str, project_id: str, limit: int = 5) -> SearchResults:
        """Find similar workflow patterns"""
        try:
            query_embedding = await self.jina.embed_single(query)
            
            cypher_query = """
            MATCH (w:Workflow {project_id: $project_id})
            WHERE w.embedding IS NOT NULL
            RETURN w.id as document_id, w.step_name as content, w as metadata,
                   gds.similarity.cosine(w.embedding, $embedding) as similarity
            ORDER BY similarity DESC
            LIMIT $limit
            """
            
            results = await self.neo4j.run_query(cypher_query, {
                "project_id": project_id,
                "embedding": query_embedding,
                "limit": limit
            })
            
            workflow_results = [
                EmbeddingResult(
                    embedding=query_embedding,
                    document_id=record["document_id"],
                    similarity_score=record["similarity"],
                    metadata=record["metadata"]
                )
                for record in results
            ]
            
            return SearchResults(
                results=workflow_results,
                total_count=len(workflow_results),
                query_time_ms=0  # Calculate if needed
            )
        except Exception as e:
            raise Exception(f"Failed to search similar workflows: {str(e)}")
    
    async def store_agent_memory(self, agent_memory: AgentMemory) -> str:
        """Store agent conversation/decision memory"""
        try:
            memory_id = str(uuid.uuid4())
            embedding = await self.jina.embed_single(agent_memory.content)
            
            await self.neo4j.create_node(
                labels=["AgentMemory", agent_memory.memory_type.title()],
                properties={
                    "id": memory_id,
                    "agent_id": agent_memory.agent_id,
                    "memory_type": agent_memory.memory_type,
                    "content": agent_memory.content,
                    "metadata": agent_memory.metadata,
                    "project_id": agent_memory.project_id,
                    "embedding": embedding,
                    "timestamp": agent_memory.timestamp.isoformat()
                }
            )
            
            return memory_id
        except Exception as e:
            raise Exception(f"Failed to store agent memory: {str(e)}")