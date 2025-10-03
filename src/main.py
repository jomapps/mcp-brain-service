"""Main FastAPI application with WebSocket support."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.services.character_service import CharacterService
from src.models.character import CharacterCreate
from src.lib.database import get_neo4j_connection, close_neo4j_connection
from src.lib.embeddings import get_embedding_service
from src.api_routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Brain Service",
    description="Character embedding and semantic search service for Auto-Movie",
    version="1.0.0"
)

# Configure CORS origins based on environment
# Get allowed origins from environment or use defaults
allowed_origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:3010,https://auto-movie.ngrok.pro,https://auto-movie.ft.tc"
).split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include REST API routes
app.include_router(api_router)

# Initialize services - will be configured on startup
character_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup - with strict validation."""
    global character_service

    try:
        logger.info("=" * 60)
        logger.info("🚀 Starting MCP Brain Service")
        logger.info("=" * 60)

        # Validate and initialize Neo4j (REQUIRED)
        logger.info("📊 Initializing Neo4j connection...")
        from src.lib.neo4j_client import get_neo4j_client
        neo4j_client = await get_neo4j_client()
        logger.info("✅ Neo4j connection verified")

        # Validate and initialize Jina embeddings (REQUIRED)
        logger.info("🧠 Initializing Jina embedding service...")
        from src.lib.embeddings import JinaEmbeddingService
        jina_service = JinaEmbeddingService()
        jina_health = await jina_service.health_check()
        if jina_health["status"] != "healthy":
            raise Exception(f"Jina service unhealthy: {jina_health.get('error', 'Unknown error')}")
        logger.info(f"✅ Jina embeddings ready (model: {jina_service.model})")

        # Initialize embedding service wrapper
        embedding_service = get_embedding_service()

        # Initialize database connection for character service (legacy support)
        try:
            neo4j_connection = await get_neo4j_connection()
        except:
            neo4j_connection = None

        # Initialize character service with integrations
        character_service = CharacterService(
            neo4j_connection=neo4j_connection,
            embedding_service=embedding_service
        )

        logger.info("=" * 60)
        logger.info("✅ MCP Brain Service started successfully")
        logger.info("   - Neo4j: Connected")
        logger.info(f"   - Jina: {jina_service.model}")
        logger.info(f"   - API: REST endpoints active at /api/v1")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ FAILED TO START MCP BRAIN SERVICE")
        logger.error(f"   Error: {str(e)}")
        logger.error("=" * 60)
        logger.error("\nRequired Environment Variables:")
        logger.error("  - NEO4J_URI (e.g., bolt://localhost:7687)")
        logger.error("  - NEO4J_USER")
        logger.error("  - NEO4J_PASSWORD")
        logger.error("  - JINA_API_KEY (from https://jina.ai)")
        logger.error("=" * 60)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        await close_neo4j_connection()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "MCP Brain Service is running"}


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Comprehensive health check endpoint."""
    from src.lib.neo4j_client import get_neo4j_client
    from src.lib.embeddings import JinaEmbeddingService

    # Check Neo4j
    neo4j_health = {"status": "unknown"}
    try:
        neo4j = await get_neo4j_client()
        neo4j_health = await neo4j.health_check()
    except Exception as e:
        neo4j_health = {"status": "error", "error": str(e)}

    # Check Jina
    jina_health = {"status": "unknown"}
    try:
        jina = JinaEmbeddingService()
        jina_health = await jina.health_check()
    except Exception as e:
        jina_health = {"status": "error", "error": str(e)}

    # Overall status
    overall_healthy = (
        neo4j_health.get("status") == "healthy" and
        jina_health.get("status") == "healthy"
    )

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "service": "MCP Brain Service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "neo4j": neo4j_health,
            "jina": jina_health
        }
    }


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for MCP communication."""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.debug(f"Received message: {data}")
            
            try:
                # Parse JSON message
                message = json.loads(data)
                
                # Process message and get response
                response = await process_message(message)
                
                # Send response back to client
                await websocket.send_text(json.dumps(response))
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_response = {
                    "status": "error",
                    "message": f"Invalid JSON format: {str(e)}"
                }
                await websocket.send_text(json.dumps(error_response))
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_response = {
                    "status": "error",
                    "message": f"Internal error: {str(e)}"
                }
                await websocket.send_text(json.dumps(error_response))
                
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


async def process_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming WebSocket message.
    
    Args:
        message: Parsed JSON message
        
    Returns:
        Response dictionary
    """
    tool = message.get("tool")
    
    if not tool:
        return {
            "status": "error",
            "message": "Missing 'tool' field in message"
        }
    
    if tool == "create_character":
        return await handle_create_character(message)
    elif tool == "find_similar_characters":
        return await handle_find_similar_characters(message)
    else:
        return {
            "status": "error",
            "message": f"Unknown tool: {tool}"
        }


async def handle_create_character(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create_character tool request.
    
    Args:
        message: WebSocket message
        
    Returns:
        Response dictionary
    """
    try:
        # Validate required fields
        required_fields = ["project_id", "name", "personality_description", "appearance_description"]
        missing_fields = [field for field in required_fields if field not in message]
        
        if missing_fields:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Create character data
        character_data = CharacterCreate(
            project_id=message["project_id"],
            name=message["name"],
            personality_description=message["personality_description"],
            appearance_description=message["appearance_description"]
        )
        
        # Create character using service
        character = await character_service.create_character(character_data)
        
        return {
            "status": "success",
            "message": "Character created successfully.",
            "character_id": character.id
        }
        
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return {
            "status": "error",
            "message": f"Failed to create character: {str(e)}"
        }


async def handle_find_similar_characters(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle find_similar_characters tool request.
    
    Args:
        message: WebSocket message
        
    Returns:
        Response dictionary
    """
    try:
        # Validate required fields
        required_fields = ["project_id", "query"]
        missing_fields = [field for field in required_fields if field not in message]
        
        if missing_fields:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        project_id = message["project_id"]
        query = message["query"]
        
        # Find similar characters using service
        results = await character_service.find_similar_characters(project_id, query)
        
        # Convert results to dictionaries
        results_data = [
            {
                "id": result.id,
                "name": result.name,
                "similarity_score": result.similarity_score
            }
            for result in results
        ]
        
        return {
            "status": "success",
            "results": results_data
        }
        
    except Exception as e:
        logger.error(f"Error finding similar characters: {e}")
        return {
            "status": "error",
            "message": f"Failed to find similar characters: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=True
    )