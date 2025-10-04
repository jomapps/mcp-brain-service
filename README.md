# MCP Brain Service

A Python-based service that provides embedding generation, semantic search, and AI-powered content analysis for the Auto-Movie application. Built with FastAPI, Neo4j, Jina AI, and OpenRouter LLM integration.

## 🎉 Latest Release: v1.1.0 - Batch Endpoints

**New in this release**: 4 powerful batch endpoints for automated gather creation workflows!

- ✅ **Batch Node Creation** - Create up to 50 nodes in a single request
- ✅ **Duplicate Detection** - Find semantically similar content
- ✅ **Department Context** - Aggregate insights with AI theme extraction
- ✅ **Coverage Analysis** - Identify gaps with LLM-powered recommendations

[📚 View Full Changelog](CHANGELOG.md) | [📖 API Documentation](docs/BATCH_ENDPOINTS_GUIDE.md)

## Features

### Core Capabilities
- **Character Management**: Create and store characters with personality and appearance descriptions
- **Embedding Generation**: Automatic text embedding using Jina AI (v4)
- **Semantic Search**: Find similar content using natural language queries
- **Batch Operations**: Efficient bulk node creation and processing
- **Duplicate Detection**: Semantic similarity-based duplicate identification
- **AI-Powered Analysis**: LLM-based theme extraction and coverage analysis
- **Content Validation**: Automatic rejection of invalid/error data (NEW!)
- **Node Deletion**: API endpoint and bulk cleanup tools (NEW!)
- **WebSocket API**: Real-time MCP (Model Context Protocol) communication
- **REST API**: Comprehensive HTTP endpoints for all operations
- **Project Isolation**: Complete data isolation by project ID
- **Performance Optimized**: Fast response times with parallel processing

## Architecture

### Technology Stack
- **FastAPI**: Web framework with WebSocket and REST API support
- **Neo4j**: Graph database for knowledge graph storage
- **Jina AI**: State-of-the-art embedding generation (v4)
- **OpenRouter**: LLM integration (Claude Sonnet 4.5, Qwen backup)
- **PayloadCMS**: Department configuration management
- **Pydantic**: Data validation and serialization
- **Pytest**: Comprehensive test suite (contract, integration, unit, performance)

### Services
- **Gather Service**: Batch operations, duplicate detection, context aggregation, coverage analysis
- **Knowledge Service**: Document storage and retrieval
- **Character Service**: Character management and search
- **LLM Client**: AI-powered theme extraction and analysis
- **PayloadCMS Client**: Department configuration fetching

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

Create a `.env` file with required environment variables:

```bash
# Neo4j Database
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Jina AI Embeddings
JINA_API_KEY=your-jina-api-key
JINA_MODEL=jina-embeddings-v4

# OpenRouter LLM
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_DEFAULT_MODEL=anthropic/claude-sonnet-4.5

# PayloadCMS
MAIN_APP_PAYLOAD_API_URL=https://your-app.com/api
MAIN_APP_PAYLOAD_API_KEY=your-payload-key

# Brain Service
BRAIN_SERVICE_API_KEY=your-brain-api-key
```

See [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for complete configuration details.

## API Endpoints

### 🆕 Batch Endpoints (v1.1.0)

#### 1. Batch Node Creation
```bash
POST /api/v1/nodes/batch
Authorization: Bearer {API_KEY}

# Create multiple nodes in one request (1-50 nodes)
{
  "nodes": [
    {
      "type": "GatherItem",
      "content": "Full text content",
      "projectId": "507f1f77bcf86cd799439011",
      "properties": {"department": "story"}
    }
  ]
}
```

#### 2. Duplicate Search
```bash
POST /api/v1/search/duplicates
Authorization: Bearer {API_KEY}

# Find semantically similar content
{
  "content": "Text to check for duplicates",
  "projectId": "507f1f77bcf86cd799439011",
  "threshold": 0.90,
  "limit": 10
}
```

#### 3. Department Context
```bash
GET /api/v1/context/department?projectId={id}&department=character&previousDepartments=story
Authorization: Bearer {API_KEY}

# Aggregate context from previous departments with AI theme extraction
```

#### 4. Coverage Analysis
```bash
POST /api/v1/analyze/coverage
Authorization: Bearer {API_KEY}

# Analyze content coverage and identify gaps
{
  "projectId": "507f1f77bcf86cd799439011",
  "department": "story",
  "gatherItems": [
    {"content": "Plot overview...", "summary": "Main plot"}
  ]
}
```

**📖 Full API Documentation**: [Batch Endpoints Guide](docs/BATCH_ENDPOINTS_GUIDE.md)

### 🆕 Data Quality & Deletion Features

#### Content Validation (Automatic)
All node creation requests are automatically validated:
- ✅ Rejects empty content
- ✅ Rejects error messages ("Error:", "no user message", etc.)
- ✅ Rejects invalid data ("undefined", "null", "[object Object]", "NaN")
- ✅ Enforces minimum content length (10 characters)

```bash
# This will be rejected with 400 error
POST /api/v1/nodes
{
  "content": "Error: No user message found",  # ❌ Invalid
  "projectId": "my-project",
  "type": "gather"
}
```

#### Delete Node
```bash
DELETE /api/v1/nodes/{node_id}?project_id={project_id}
Authorization: Bearer {API_KEY}

# Deletes a specific node and all its relationships
```

#### Bulk Cleanup Script
```bash
# Preview what would be deleted (always start here)
python scripts/cleanup_invalid_nodes.py --dry-run

# Clean specific project
python scripts/cleanup_invalid_nodes.py --project-id my-project

# List all projects
python scripts/cleanup_invalid_nodes.py --list-projects
```

**📖 Full Documentation**: [Deletion & Validation Guide](docs/DELETION_AND_VALIDATION.md)

### Legacy Endpoints

## WebSocket API Usage

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