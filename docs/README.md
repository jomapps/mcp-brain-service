# MCP Brain Service Documentation

## Overview

The MCP Brain Service is a pure infrastructure service for storing and retrieving documents with semantic search, graph relationships, and hybrid search capabilities.

**Key Principle**: Brain service is infrastructure, not application logic. Apps prepare data, brain service stores and retrieves.

## Quick Links

### Architecture & Design
- [Architecture Decision](./architecture-decision.md) - Why data preparation belongs in the app
- [Retriv Integration Plan](./retriv-integration-plan.md) - How to enhance queries with hybrid search
- [API Contracts](./api-contracts.md) - Storage and query API specifications

### Implementation
- [Implementation Checklist](./implementation-checklist.md) - Step-by-step guide to add Retriv

### Operations
- [QUICKSTART](../QUICKSTART.md) - Get started quickly
- [PRODUCTION](../PRODUCTION.md) - Production deployment guide
- [WARP](../WARP.md) - Development commands and tips

## What is MCP Brain Service?

A Python-based service that provides:

1. **Storage**: Store documents with embeddings and relationships
2. **Semantic Search**: Find similar documents using Jina embeddings
3. **Hybrid Search**: Combine keyword (BM25) + semantic search with Retriv
4. **Graph Queries**: Navigate relationships using Neo4j
5. **MCP Protocol**: WebSocket-based tool interface for agents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application (Next.js)                     │
│                                                              │
│  - Prepares data (enrichment, transformation)                │
│  - Calls brain service for storage/retrieval                 │
└─────────────────────────────────────────────────────────────┘
                    ↓                           ↑
              (store API)                  (query API)
                    ↓                           ↑
┌─────────────────────────────────────────────────────────────┐
│              Brain Service (brain.ft.tc)                     │
│              Pure Storage & Retrieval Infrastructure         │
│                                                              │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │ Store API          │      │ Query API          │        │
│  │ - Store documents  │      │ - Hybrid search    │        │
│  │ - Batch storage    │      │ - Semantic search  │        │
│  └────────────────────┘      │ - Graph queries    │        │
│                               └────────────────────┘        │
│           ↓                           ↑                      │
│  ┌──────────────────────────────────────────────┐          │
│  │         Storage & Retrieval Services          │          │
│  │  - RetrivService (hybrid search)             │          │
│  │  - Neo4jService (graph storage)              │          │
│  │  - JinaService (embeddings)                  │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. Pure Infrastructure

Brain service is like a database - it doesn't understand your business logic:

```
✅ Good: App prepares character data → Brain service stores
❌ Bad: Brain service understands PayloadCMS structure
```

### 2. Document Format

All documents follow a standard format:

```typescript
{
  id: string              // Unique identifier
  type: string            // Document type (character, scene, etc.)
  project_id: string      // Project isolation
  text: string            // Searchable text (prepared by app)
  metadata: object        // Structured data (prepared by app)
  relationships: array    // Graph relationships (prepared by app)
}
```

### 3. Hybrid Search

Retriv combines two search methods:

- **BM25 (Keyword)**: Matches exact terms like "vest", "scene 3"
- **Embeddings (Semantic)**: Understands meaning like "clothing", "appearance"
- **Combined**: Better results than either alone

### 4. Project Isolation

All data is isolated by `project_id` - different projects don't see each other's data.

## Getting Started

### For Brain Service Development

1. Read [Retriv Integration Plan](./retriv-integration-plan.md)
2. Follow [Implementation Checklist](./implementation-checklist.md)
3. Run tests: `pytest`
4. Deploy: See [PRODUCTION.md](../PRODUCTION.md)

### For App Integration

1. Read [Architecture Decision](./architecture-decision.md)
2. Review [API Contracts](./api-contracts.md)
3. Implement data preparation in your app
4. Call brain service storage/query APIs

## API Overview

### Storage

```bash
# Store single document
POST /store
{
  "id": "char_aladdin_proj123",
  "type": "character",
  "project_id": "proj123",
  "text": "Aladdin: A street-smart young man...",
  "metadata": {...},
  "relationships": [...]
}

# Store multiple documents
POST /store/batch
{
  "documents": [...]
}
```

### Query

```bash
# Hybrid search (recommended)
POST /query
{
  "project_id": "proj123",
  "query": "What does Aladdin wear in scene 3?",
  "search_type": "hybrid",
  "top_k": 5
}

# Character context
POST /query/character-context
{
  "project_id": "proj123",
  "character_name": "Aladdin",
  "scene_number": 3
}
```

See [API Contracts](./api-contracts.md) for full details.

## MCP Tools

Brain service also exposes WebSocket-based MCP tools:

- `store_document` - Store a document
- `store_batch` - Store multiple documents
- `search` - Hybrid search
- `find_similar` - Find similar documents
- `get_relationships` - Get document relationships

## Technology Stack

- **FastAPI**: Web framework with WebSocket support
- **Neo4j**: Graph database for relationships
- **Jina AI**: Embedding generation
- **Retriv**: Hybrid search (BM25 + embeddings)
- **Pydantic**: Data validation
- **Pytest**: Testing framework

## Development Workflow

1. **Make changes** to brain service code
2. **Run tests**: `pytest`
3. **Test locally**: `python src/main.py`
4. **Deploy**: Follow deployment guide

## Testing

```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=src
```

## Deployment

See [PRODUCTION.md](../PRODUCTION.md) for deployment instructions.

Quick deploy to Coolify:
1. Push to main branch
2. Coolify auto-deploys
3. Verify health: `curl https://brain.ft.tc/health`

## Monitoring

### Health Check

```bash
curl https://brain.ft.tc/health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "connected",
    "jina": "connected",
    "retriv": "initialized"
  }
}
```

### Logs

```bash
# View logs in Coolify dashboard
# Or SSH to server and check Docker logs
docker logs mcp-brain-service
```

## Troubleshooting

### Retriv Not Initializing

```bash
# Check if Retriv package installed
pip list | grep retriv

# Check data directory permissions
ls -la data/retriv_index/

# Check logs for errors
docker logs mcp-brain-service | grep -i retriv
```

### Slow Queries

```bash
# Check Retriv index size
du -sh data/retriv_index/

# Monitor query performance
# Add logging in retriv_service.py
```

### Neo4j Connection Issues

```bash
# Check Neo4j connection
curl http://neo4j.ft.tc:7474

# Verify credentials in .env
echo $NEO4J_URI
echo $NEO4J_USER
```

## Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Update documentation
5. Submit PR

## Support

- **Issues**: Create GitHub issue
- **Questions**: Check documentation first
- **Urgent**: Contact team lead

## Roadmap

### Current (v1.0)
- ✅ Neo4j storage
- ✅ Jina embeddings
- ✅ MCP protocol
- 🚧 Retriv hybrid search (in progress)

### Future (v1.1)
- [ ] REST API routes
- [ ] Authentication
- [ ] Rate limiting
- [ ] Caching layer

### Future (v2.0)
- [ ] Multi-modal search (images + text)
- [ ] Real-time updates
- [ ] Advanced analytics
- [ ] Multi-tenancy

## License

[Your License Here]

## Contact

[Your Contact Info Here]

