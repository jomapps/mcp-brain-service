import asyncio
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from .services.knowledge_service import KnowledgeService
from .services.batch_service import BatchService
from .lib.embeddings import JinaEmbeddingService
from .lib.neo4j_client import Neo4jClient
from .models.knowledge import Document, WorkflowData, AgentMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-brain-service")

# Initialize services
jina_service = JinaEmbeddingService()
neo4j_client = Neo4jClient()
knowledge_service = KnowledgeService(jina_service, neo4j_client)
batch_service = BatchService(knowledge_service)

# Create MCP server
server = Server("mcp-brain-service")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MCP tools"""
    return [
        # Original tools
        types.Tool(
            name="create_character",
            description="Create a new character with embedding",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "traits": {"type": "array", "items": {"type": "string"}},
                    "project_id": {"type": "string"}
                },
                "required": ["name", "description", "project_id"]
            }
        ),
        types.Tool(
            name="find_similar_characters",
            description="Find characters similar to a description",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "project_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["description", "project_id"]
            }
        ),
        
        # New embedding tools
        types.Tool(
            name="embed_text",
            description="Generate embedding for a single text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "project_id": {"type": "string"}
                },
                "required": ["text", "project_id"]
            }
        ),
        types.Tool(
            name="search_by_embedding",
            description="Search for similar content by embedding",
            inputSchema={
                "type": "object",
                "properties": {
                    "embedding": {"type": "array", "items": {"type": "number"}},
                    "project_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["embedding", "project_id"]
            }
        ),
        types.Tool(
            name="store_document",
            description="Store document with automatic embedding",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "metadata": {"type": "object"},
                    "project_id": {"type": "string"}
                },
                "required": ["content", "metadata", "project_id"]
            }
        ),
        
        # Knowledge graph tools
        types.Tool(
            name="create_relationship",
            description="Create relationship between nodes",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_id": {"type": "string"},
                    "to_id": {"type": "string"},
                    "relationship_type": {"type": "string"},
                    "properties": {"type": "object", "default": {}}
                },
                "required": ["from_id", "to_id", "relationship_type"]
            }
        ),
        types.Tool(
            name="query_graph",
            description="Execute Cypher query on knowledge graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "cypher_query": {"type": "string"},
                    "project_id": {"type": "string"},
                    "parameters": {"type": "object", "default": {}}
                },
                "required": ["cypher_query", "project_id"]
            }
        ),
        types.Tool(
            name="get_node_neighbors",
            description="Get neighbors and relationships of a node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                    "project_id": {"type": "string"}
                },
                "required": ["node_id", "project_id"]
            }
        ),
        
        # Batch processing tools
        types.Tool(
            name="batch_embed_texts",
            description="Batch embed multiple texts efficiently",
            inputSchema={
                "type": "object",
                "properties": {
                    "texts": {"type": "array", "items": {"type": "string"}},
                    "project_id": {"type": "string"}
                },
                "required": ["texts", "project_id"]
            }
        ),
        types.Tool(
            name="bulk_store_documents",
            description="Bulk store multiple documents with embeddings",
            inputSchema={
                "type": "object",
                "properties": {
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "metadata": {"type": "object"},
                                "document_type": {"type": "string"}
                            },
                            "required": ["content", "metadata", "document_type"]
                        }
                    },
                    "project_id": {"type": "string"}
                },
                "required": ["documents", "project_id"]
            }
        ),
        
        # Workflow and agent memory tools
        types.Tool(
            name="store_workflow_data",
            description="Store LangGraph workflow execution data",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "step_name": {"type": "string"},
                    "input_data": {"type": "object"},
                    "output_data": {"type": "object"},
                    "execution_time_ms": {"type": "number"},
                    "project_id": {"type": "string"}
                },
                "required": ["workflow_id", "agent_id", "step_name", "input_data", "output_data", "execution_time_ms", "project_id"]
            }
        ),
        types.Tool(
            name="search_similar_workflows",
            description="Find similar workflow patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "project_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query", "project_id"]
            }
        ),
        types.Tool(
            name="store_agent_memory",
            description="Store agent conversation/decision memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "memory_type": {"type": "string", "enum": ["conversation", "decision", "context"]},
                    "content": {"type": "string"},
                    "metadata": {"type": "object"},
                    "project_id": {"type": "string"}
                },
                "required": ["agent_id", "memory_type", "content", "metadata", "project_id"]
            }
        ),
        
        # Batch processing tools
        types.Tool(
            name="process_document_batch",
            description="Process large batches of documents efficiently",
            inputSchema={
                "type": "object",
                "properties": {
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "metadata": {"type": "object"},
                                "document_type": {"type": "string"}
                            },
                            "required": ["content", "metadata", "document_type"]
                        }
                    },
                    "project_id": {"type": "string"}
                },
                "required": ["documents", "project_id"]
            }
        ),
        types.Tool(
            name="batch_similarity_search",
            description="Perform batch similarity searches",
            inputSchema={
                "type": "object",
                "properties": {
                    "queries": {"type": "array", "items": {"type": "string"}},
                    "project_id": {"type": "string"},
                    "limit_per_query": {"type": "integer", "default": 10}
                },
                "required": ["queries", "project_id"]
            }
        ),
        
        # Health check tool
        types.Tool(
            name="health_check",
            description="Check service health and connectivity",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    try:
        if name == "create_character":
            # Original character creation logic
            character_data = {
                "name": arguments["name"],
                "description": arguments["description"],
                "traits": arguments.get("traits", []),
                "project_id": arguments["project_id"]
            }
            
            # Store as document
            document_id = await knowledge_service.store_document(
                content=f"Character: {character_data['name']} - {character_data['description']}",
                metadata={
                    "document_type": "character",
                    "name": character_data["name"],
                    "traits": character_data["traits"]
                },
                project_id=arguments["project_id"]
            )
            
            return [types.TextContent(
                type="text",
                text=f"Character created with ID: {document_id}"
            )]
        
        elif name == "find_similar_characters":
            # Find similar characters using embedding search
            query_embedding = await knowledge_service.embed_text(
                arguments["description"], 
                arguments["project_id"]
            )
            
            results = await knowledge_service.search_by_embedding(
                query_embedding.embedding,
                arguments["project_id"],
                arguments.get("limit", 5)
            )
            
            return [types.TextContent(
                type="text",
                text=f"Found {len(results.results)} similar characters in {results.query_time_ms}ms"
            )]
        
        elif name == "embed_text":
            result = await knowledge_service.embed_text(
                arguments["text"],
                arguments["project_id"]
            )
            return [types.TextContent(
                type="text",
                text=f"Text embedded with document ID: {result.document_id}"
            )]
        
        elif name == "search_by_embedding":
            results = await knowledge_service.search_by_embedding(
                arguments["embedding"],
                arguments["project_id"],
                arguments.get("limit", 10)
            )
            return [types.TextContent(
                type="text",
                text=f"Found {results.total_count} results in {results.query_time_ms}ms"
            )]
        
        elif name == "store_document":
            document_id = await knowledge_service.store_document(
                arguments["content"],
                arguments["metadata"],
                arguments["project_id"]
            )
            return [types.TextContent(
                type="text",
                text=f"Document stored with ID: {document_id}"
            )]
        
        elif name == "create_relationship":
            success = await knowledge_service.create_relationship(
                arguments["from_id"],
                arguments["to_id"],
                arguments["relationship_type"],
                arguments.get("properties", {})
            )
            return [types.TextContent(
                type="text",
                text=f"Relationship created: {success}"
            )]
        
        elif name == "query_graph":
            results = await knowledge_service.query_graph(
                arguments["cypher_query"],
                arguments["project_id"],
                arguments.get("parameters", {})
            )
            return [types.TextContent(
                type="text",
                text=f"Query executed: {len(results.records)} records in {results.query_time_ms}ms"
            )]
        
        elif name == "get_node_neighbors":
            results = await knowledge_service.get_node_neighbors(
                arguments["node_id"],
                arguments["project_id"]
            )
            return [types.TextContent(
                type="text",
                text=f"Found {len(results.neighbors)} neighbors and {len(results.relationships)} relationships"
            )]
        
        elif name == "batch_embed_texts":
            results = await knowledge_service.batch_embed_texts(
                arguments["texts"],
                arguments["project_id"]
            )
            return [types.TextContent(
                type="text",
                text=f"Batch embedded {len(results)} texts"
            )]
        
        elif name == "bulk_store_documents":
            documents = [
                Document(
                    content=doc["content"],
                    metadata=doc["metadata"],
                    document_type=doc["document_type"],
                    project_id=arguments["project_id"]
                )
                for doc in arguments["documents"]
            ]
            document_ids = await knowledge_service.bulk_store_documents(documents, arguments["project_id"])
            return [types.TextContent(
                type="text",
                text=f"Bulk stored {len(document_ids)} documents"
            )]
        
        elif name == "store_workflow_data":
            from datetime import datetime
            workflow_data = WorkflowData(
                workflow_id=arguments["workflow_id"],
                agent_id=arguments["agent_id"],
                step_name=arguments["step_name"],
                input_data=arguments["input_data"],
                output_data=arguments["output_data"],
                execution_time_ms=arguments["execution_time_ms"],
                project_id=arguments["project_id"],
                timestamp=datetime.utcnow()
            )
            workflow_id = await knowledge_service.store_workflow_data(workflow_data)
            return [types.TextContent(
                type="text",
                text=f"Workflow data stored with ID: {workflow_id}"
            )]
        
        elif name == "search_similar_workflows":
            results = await knowledge_service.search_similar_workflows(
                arguments["query"],
                arguments["project_id"],
                arguments.get("limit", 5)
            )
            return [types.TextContent(
                type="text",
                text=f"Found {len(results.results)} similar workflows"
            )]
        
        elif name == "store_agent_memory":
            from datetime import datetime
            agent_memory = AgentMemory(
                agent_id=arguments["agent_id"],
                memory_type=arguments["memory_type"],
                content=arguments["content"],
                metadata=arguments["metadata"],
                project_id=arguments["project_id"],
                timestamp=datetime.utcnow()
            )
            memory_id = await knowledge_service.store_agent_memory(agent_memory)
            return [types.TextContent(
                type="text",
                text=f"Agent memory stored with ID: {memory_id}"
            )]
        
        elif name == "process_document_batch":
            documents = [
                Document(
                    content=doc["content"],
                    metadata=doc["metadata"],
                    document_type=doc["document_type"],
                    project_id=arguments["project_id"]
                )
                for doc in arguments["documents"]
            ]
            result = await batch_service.process_document_batch(documents, arguments["project_id"])
            return [types.TextContent(
                type="text",
                text=f"Batch processed: {result['processed_count']}/{result['total_documents']} documents in {result['processing_time_seconds']:.2f}s"
            )]
        
        elif name == "batch_similarity_search":
            result = await batch_service.batch_similarity_search(
                arguments["queries"],
                arguments["project_id"],
                arguments.get("limit_per_query", 10)
            )
            return [types.TextContent(
                type="text",
                text=f"Batch search: {result['successful_searches']}/{result['total_queries']} queries in {result['processing_time_seconds']:.2f}s"
            )]
        
        elif name == "health_check":
            jina_health = await jina_service.health_check()
            neo4j_health = await neo4j_client.health_check()
            
            return [types.TextContent(
                type="text",
                text=f"Health Check - Jina: {jina_health['status']}, Neo4j: {neo4j_health['status']}"
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        logger.error(f"Tool call failed: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-brain-service",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())