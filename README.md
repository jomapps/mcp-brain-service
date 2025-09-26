# MCP Brain Service

A Python-based WebSocket service that provides character embedding and semantic search functionality for the Auto-Movie application. Built with FastAPI, Neo4j, and custom embedding generation.

## Features

- **Character Management**: Create and store characters with personality and appearance descriptions
- **Embedding Generation**: Automatic text embedding generation for semantic search
- **Semantic Search**: Find similar characters using natural language queries
- **WebSocket API**: Real-time MCP (Model Context Protocol) communication
- **Project Isolation**: Characters are isolated by project ID
- **Performance Optimized**: P95 response time < 1 minute for semantic search

## Architecture

- **FastAPI**: Web framework with WebSocket support
- **Neo4j**: Graph database for character storage (optional)
- **Custom Embedding Service**: Deterministic embedding generation (Jina v4 ready)
- **Pydantic**: Data validation and serialization
- **Pytest**: Comprehensive test suite with contract, integration, unit, and performance tests

## Quick Start

### Prerequisites

- Python 3.11+
- Neo4j (optional - service runs without database)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp-brain-service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running the Service

1. Start the WebSocket server:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

2. The service will be available at:
   - WebSocket endpoint: `ws://localhost:8002/`
   - Health check: `http://localhost:8002/health`

### Configuration

Environment variables:
- `NEO4J_URI`: Neo4j connection URI (default: `neo4j://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (default: `password`)

## API Usage

### Create Character

Send a WebSocket message to create a new character:

```json
{
  "tool": "create_character",
  "project_id": "your_project_id",
  "name": "Gandalf",
  "personality_description": "A wise and powerful wizard, mentor to Frodo Baggins.",
  "appearance_description": "An old man with a long white beard, a pointy hat, and a staff."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Character created successfully.",
  "character_id": "unique_character_id"
}
```

### Find Similar Characters

Send a WebSocket message to find similar characters:

```json
{
  "tool": "find_similar_characters",
  "project_id": "your_project_id",
  "query": "A powerful magic user"
}
```

**Response:**
```json
{
  "status": "success",
  "results": [
    {
      "id": "character_id",
      "name": "Gandalf",
      "similarity_score": 0.95
    }
  ]
}
```

### Error Handling

All errors return a consistent format:

```json
{
  "status": "error",
  "message": "Error description"
}
```

## Testing

Run the complete test suite:

```bash
# All tests
pytest

# Contract tests
pytest tests/contract/

# Integration tests  
pytest tests/integration/

# Unit tests
pytest tests/unit/

# Performance tests
pytest tests/performance/
```

### Test Categories

- **Contract Tests**: WebSocket API contract validation
- **Integration Tests**: End-to-end user story validation
- **Unit Tests**: Input validation and model testing
- **Performance Tests**: Response time and concurrency testing

## Development

### Project Structure

```
src/
├── models/          # Pydantic data models
├── services/        # Business logic services
├── lib/            # Database and utility components
└── main.py         # FastAPI application entry point

tests/
├── contract/       # API contract tests
├── integration/    # End-to-end tests
├── unit/          # Unit tests
└── performance/   # Performance tests
```

### Code Quality

- **Linting**: Configured with Ruff
- **Type Hints**: Full type annotation coverage
- **Validation**: Pydantic models with comprehensive validation
- **Error Handling**: Structured error responses and logging

### Running Tests in Development

```bash
# Start the service
python src/main.py

# In another terminal, run tests
pytest tests/contract/test_websocket.py -v
```

## Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Environment Variables

Required for production:
```bash
NEO4J_URI=neo4j://your-neo4j-host:7687
NEO4J_USER=your-username
NEO4J_PASSWORD=your-password
```

### Health Monitoring

The service provides a health endpoint at `/health` for monitoring:

```bash
curl http://localhost:8002/health
# Response: {"status": "healthy"}
```

## Performance Characteristics

- **P95 Response Time**: < 1 minute for semantic search (typically < 10ms)
- **Concurrency**: Supports multiple concurrent WebSocket connections
- **Memory Usage**: Optimized for embedding storage and similarity calculations
- **Database**: Optional Neo4j integration with graceful degradation

## Contributing

1. Follow TDD principles - write tests first
2. Ensure all tests pass: `pytest`
3. Run linting: `ruff check src/ tests/`
4. Update documentation for API changes

## License

[Your License Here]

## Support

For issues and questions, please refer to the project's issue tracker.