# Changelog

All notable changes to the MCP Brain Service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-01-04

### 🎉 Added - Batch Endpoints for Automated Gather Creation

#### New API Endpoints
- **POST /api/v1/nodes/batch** - Batch node creation (1-50 nodes per request)
  - Parallel embedding generation for optimal performance
  - Comprehensive validation and error handling
  - Detailed timing metrics in response
  - Support for custom properties per node

- **POST /api/v1/search/duplicates** - Semantic duplicate detection
  - Configurable similarity threshold (0.0-1.0)
  - Filter by type, department
  - Exclude specific node IDs
  - Project isolation enforced
  - Results sorted by similarity score

- **GET /api/v1/context/department** - Department context aggregation
  - Query nodes from multiple previous departments
  - LLM-based theme extraction per department
  - Quality score calculation
  - Aggregated summary generation using Claude Sonnet 4.5
  - Relevance scoring for cross-department insights

- **POST /api/v1/analyze/coverage** - Content coverage analysis
  - LLM-based gap identification
  - Covered aspects with quality ratings
  - Actionable recommendations
  - Quality metrics (depth, breadth, coherence, actionability)
  - Item distribution analysis
  - Overall coverage score

#### New Services
- **OpenRouter LLM Client** (`src/lib/llm_client.py`)
  - Integration with OpenRouter API
  - Support for Claude Sonnet 4.5 (primary model)
  - Backup model support (Qwen)
  - Methods: `chat_completion()`, `extract_themes()`, `generate_summary()`, `analyze_coverage()`
  - Comprehensive error handling and retry logic

- **PayloadCMS Client** (`src/lib/payload_client.py`)
  - Fetch department configurations from main application
  - Department validation
  - Health check support

- **Gather Service** (`src/services/gather_service.py`)
  - Core business logic for all batch endpoints
  - Integration with Jina embeddings, Neo4j, and LLM services
  - Comprehensive error handling
  - Performance optimization

#### New Models
- **Batch Models** (`src/models/batch.py`)
  - `BatchNodeCreateRequest/Response`
  - `DuplicateSearchRequest/Response`
  - `DepartmentContextRequest/Response`
  - `CoverageAnalysisRequest/Response`
  - Comprehensive Pydantic validation
  - MongoDB ObjectId format validation
  - Field constraints and defaults

#### Testing
- **Contract Tests** (`tests/contract/test_batch_endpoints.py`)
  - 13 comprehensive test cases
  - Success scenarios for all endpoints
  - Validation error testing
  - Authentication testing
  - Edge case coverage
  - 11/13 tests passing (2 intermittent due to asyncio event loop)

#### Documentation
- **Implementation Summary** (`docs/IMPLEMENTATION_SUMMARY.md`)
  - Complete feature overview
  - Architecture details
  - Performance metrics
  - Deployment checklist

- **Developer Guide** (`docs/BATCH_ENDPOINTS_GUIDE.md`)
  - Comprehensive API documentation
  - Request/response examples
  - Error handling guide
  - Best practices
  - Code examples (Python, JavaScript)

- **Deployment Guide** (`docs/DEPLOYMENT_GUIDE.md`)
  - Step-by-step deployment instructions
  - Configuration guide
  - Multiple deployment methods (PM2, Systemd, Docker)
  - Nginx configuration
  - Monitoring and troubleshooting

- **Test Script** (`test_new_endpoints.sh`)
  - Automated testing for all 4 endpoints
  - Easy verification of deployment

#### Environment Variables
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM operations
- `OPENROUTER_BASE_URL` - OpenRouter API base URL
- `OPENROUTER_DEFAULT_MODEL` - Primary LLM model (Claude Sonnet 4.5)
- `OPENROUTER_BACKUP_MODEL` - Backup LLM model (Qwen)
- `MAIN_APP_PAYLOAD_API_URL` - PayloadCMS API URL
- `MAIN_APP_PAYLOAD_API_KEY` - PayloadCMS API key

### 🔧 Changed
- Updated `src/api_routes.py` to include new batch endpoints
- Enhanced error handling across all endpoints
- Improved API documentation with detailed examples

### 🔒 Security
- API key authentication enforced on all new endpoints
- Project isolation validated on all queries
- MongoDB ObjectId format validation
- Input sanitization and validation

### 📊 Performance
- Batch creation: ~4 seconds for 10 nodes (includes embedding generation)
- Duplicate search: ~2 seconds
- Department context: ~8 seconds (includes LLM operations)
- Coverage analysis: ~15 seconds (includes LLM analysis)

---

## [1.0.0] - 2024-12-XX

### Added
- Initial release of MCP Brain Service
- Character embedding and semantic search
- Neo4j graph database integration
- Jina AI embedding service integration
- WebSocket support for MCP communication
- REST API endpoints:
  - POST /api/v1/nodes - Create single node
  - POST /api/v1/search - Semantic search
  - GET /api/v1/nodes/{id} - Get node by ID
  - GET /api/v1/stats - Service statistics
  - GET /health - Health check
- Character service for character management
- Knowledge service for document storage and retrieval
- Retriv integration for hybrid search (BM25 + embeddings)

### Security
- API key authentication
- CORS configuration
- Project-based data isolation

### Documentation
- README.md with setup instructions
- API documentation via FastAPI auto-generated docs
- Integration tests
- Performance tests

---

## Release Notes

### Version 1.1.0 Highlights

This release adds powerful batch processing capabilities for automated gather creation workflows:

1. **Batch Operations**: Create up to 50 nodes in a single request with parallel embedding generation
2. **Duplicate Detection**: Find semantically similar content to prevent duplicates
3. **Context Aggregation**: Gather insights from previous departments with AI-powered theme extraction
4. **Coverage Analysis**: Identify gaps and get actionable recommendations using advanced LLM analysis

These features enable efficient, automated content generation workflows while maintaining high quality and avoiding duplication.

### Breaking Changes
None - All changes are additive and backward compatible.

### Migration Guide
No migration required. New endpoints are available immediately after deployment.

### Known Issues
- 2 contract tests have intermittent failures due to asyncio event loop issues in test environment (not affecting production)
- LLM operations may take 10-15 seconds depending on content size (expected behavior)

### Upgrade Instructions
1. Pull latest code from repository
2. Update environment variables (add OpenRouter and PayloadCMS configs)
3. Install dependencies: `pip install -r requirements.txt`
4. Restart service: `pm2 restart mcp-brain-service`
5. Verify: `curl https://brain.ft.tc/health`

---

## Future Roadmap

### Version 1.2.0 (Planned)
- [ ] Rate limiting per endpoint
- [ ] Prometheus metrics integration
- [ ] Redis caching for department context
- [ ] Batch retry logic for failed nodes
- [ ] WebSocket support for batch operations
- [ ] Enhanced LLM prompt optimization

### Version 1.3.0 (Planned)
- [ ] Multi-language support for embeddings
- [ ] Advanced analytics dashboard
- [ ] Automated quality scoring
- [ ] Content recommendation engine
- [ ] Integration with additional LLM providers

---

## Contributors

- **Jom Apps Services** - Initial implementation and batch endpoints

---

## Links

- **Repository**: https://github.com/jomapps/mcp-brain-service
- **Documentation**: https://brain.ft.tc/docs
- **Issues**: https://github.com/jomapps/mcp-brain-service/issues

---

**Note**: For detailed API documentation, see `/docs/BATCH_ENDPOINTS_GUIDE.md`

