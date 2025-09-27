# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

The MCP Brain Service is a Python-based WebSocket service that provides character embedding and semantic search functionality for the Auto-Movie application. It implements the Model Context Protocol (MCP) for real-time communication and uses Neo4j for data persistence and custom embedding generation for semantic search.

## Key Commands

### Development Server
```bash
# Start development server with auto-reload
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload

# Alternative: Run directly
python src/main.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/contract/          # WebSocket API contracts
pytest tests/integration/       # End-to-end workflows
pytest tests/unit/             # Input validation and models
pytest tests/performance/      # Response time and concurrency

# Run single test with verbose output
pytest tests/contract/test_websocket.py -v

# Run performance tests with output
pytest tests/performance/test_performance.py -v -s
```

### Code Quality
```bash
# Lint code
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

### Dependencies
```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Using Poetry (alternative)
poetry install
```

## Architecture

### Core Components

- **FastAPI Application** (`src/main.py`): WebSocket server with MCP message routing
- **Character Service** (`src/services/character_service.py`): Business logic for character operations
- **Neo4j Database** (`src/lib/database.py`): Graph database integration with graceful degradation
- **Embedding Service** (`src/lib/embeddings.py`): Text-to-vector conversion for semantic search
- **Pydantic Models** (`src/models/`): Data validation and serialization

### WebSocket MCP Protocol

The service communicates via WebSocket using JSON messages with this structure:

**Request Format:**
```json
{
  "tool": "create_character|find_similar_characters",
  "project_id": "string",
  ...additional_fields
}
```

**Response Format:**
```json
{
  "status": "success|error",
  "message": "string",
  ...additional_data
}
```

### Character Creation Flow
1. Validate WebSocket message fields
2. Create Character instance with Pydantic validation
3. Generate embeddings for personality and appearance descriptions
4. Store character in Neo4j (if available)
5. Return character ID in response

### Semantic Search Flow
1. Parse search query from WebSocket message
2. Generate query embedding vector
3. Retrieve all characters from project in Neo4j
4. Calculate cosine similarity between query and character embeddings
5. Return ranked results by similarity score (70% personality, 30% appearance weighting)

### Database Strategy
- **Neo4j Integration**: Optional - service runs without database for development
- **Graceful Degradation**: Database connection failures don't break the service
- **Character Storage**: Graph nodes with embedding vectors as properties
- **Project Isolation**: Characters are scoped by project_id

### Embedding Strategy
- **Deterministic Generation**: Currently uses hash-based pseudo-embeddings for development
- **Jina v4 Ready**: Architecture prepared for production embedding service integration
- **Vector Operations**: Custom cosine similarity implementation
- **Dual Embeddings**: Separate vectors for personality and appearance

## Test Architecture

### Test Categories
- **Contract Tests**: Validate WebSocket API message formats and responses
- **Integration Tests**: Test complete user workflows end-to-end  
- **Unit Tests**: Test individual components and validation logic
- **Performance Tests**: Verify P95 response time requirements (<60s, typically <10ms)

### Running Tests During Development
```bash
# Start the service in one terminal
python src/main.py

# Run contract tests in another terminal
pytest tests/contract/test_websocket.py -v

# Run performance tests with live metrics
pytest tests/performance/test_performance.py -v -s
```

### Performance Requirements
- P95 semantic search response time: < 1 minute (target: < 10ms)
- Concurrent WebSocket connections supported
- Character creation time: < 5 seconds

## Environment Configuration

### Required Environment Variables
```bash
# Neo4j Configuration (optional)
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j  
NEO4J_PASSWORD=password
```

### Health Monitoring
- Health endpoint: `GET http://localhost:8002/health`
- WebSocket endpoint: `ws://localhost:8002/`

## Byterover MCP Integration

This project includes Byterover MCP tools for enhanced development workflow. When working with plans and implementations:

### Byterover Workflows
- **Onboarding**: Use `byterover-check-handbook-existence` and `byterover-create-handbook` for project setup
- **Planning**: Use `byterover-retrieve-knowledge` and `byterover-store-knowledge` for context management
- **Implementation**: Use `byterover-update-plan-progress` to track completion
- **Module Updates**: Use `byterover-update-module` after significant architectural changes

### Required Byterover Usage Patterns
- Always use `byterover-retrieve-knowledge` before starting tasks
- Store implementation knowledge with `byterover-store-knowledge`
- Reference Byterover sources explicitly: "According to Byterover memory layer"
- Update plan progress as tasks complete

## Key Development Patterns

### Error Handling
- All WebSocket responses use consistent `{status, message}` format
- Database connection failures are logged but don't crash the service
- Embedding generation errors are propagated to the WebSocket client
- Malformed JSON messages return structured error responses

### Adding New MCP Tools
1. Add message handler in `process_message()` function
2. Implement handler function following `handle_create_character` pattern
3. Add request/response models in `src/models/`
4. Add contract tests in `tests/contract/test_websocket.py`
5. Add integration test in appropriate `tests/integration/` file

### Database Operations
- Always use async context managers: `async with session.session() as session:`
- Check for Neo4j connection availability before operations
- Use parameterized queries to prevent injection
- Handle connection failures gracefully

### Performance Considerations
- Embedding generation is the main performance bottleneck
- Neo4j vector similarity searches scale with character count
- WebSocket connections are lightweight but consider concurrent limits
- Memory usage grows with stored embedding vectors
