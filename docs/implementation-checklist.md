# Implementation Checklist

## Overview

This checklist guides the implementation of Retriv integration into the MCP Brain Service.

**Goal**: Enhance brain service with hybrid search while keeping it as pure infrastructure.

## Phase 1: Setup & Dependencies

### 1.1 Add Retriv Package
- [ ] Add `retriv==0.2.4` to `requirements.txt`
- [ ] Run `pip install -r requirements.txt`
- [ ] Verify Retriv installation: `python -c "import retriv; print(retriv.__version__)"`

### 1.2 Create Data Directory
- [ ] Create `data/retriv_index/` directory for Retriv indices
- [ ] Add to `.gitignore`: `data/retriv_index/`
- [ ] Ensure directory has write permissions

### 1.3 Update Environment Variables
- [ ] Add to `.env.example`:
  ```
  # Retriv Configuration
  RETRIV_INDEX_PATH=./data/retriv_index
  RETRIV_MODEL=sentence-transformers/all-MiniLM-L6-v2
  ```

## Phase 2: Create Retriv Service

### 2.1 Create Service File
- [ ] Create `src/services/retriv_service.py`
- [ ] Implement `RetrivService` class
- [ ] Add initialization method
- [ ] Add document indexing method
- [ ] Add search method
- [ ] Add filter support

### 2.2 Service Methods
- [ ] `initialize()` - Initialize Retriv retriever
- [ ] `index_documents(documents)` - Index documents for search
- [ ] `search(query, project_id, filters, top_k)` - Hybrid search
- [ ] `delete_document(doc_id)` - Remove document (if supported)
- [ ] `clear_project(project_id)` - Clear project data

### 2.3 Global Instance
- [ ] Create `get_retriv_service()` function
- [ ] Implement singleton pattern
- [ ] Add proper error handling

## Phase 3: Enhance Knowledge Service

### 3.1 Update Knowledge Service
- [ ] Import `get_retriv_service` in `src/services/knowledge_service.py`
- [ ] Add `self.retriv` to `__init__`
- [ ] Add `initialize()` method to init Retriv
- [ ] Update `store_document()` to index in Retriv

### 3.2 Enhanced Search Method
- [ ] Add `search()` method with `search_type` parameter
- [ ] Implement `search_type="hybrid"` using Retriv
- [ ] Keep `search_type="semantic"` using Jina (existing)
- [ ] Keep `search_type="graph"` using Neo4j (existing)
- [ ] Add result enrichment logic

### 3.3 Backward Compatibility
- [ ] Ensure existing methods still work
- [ ] Default to hybrid search for better results
- [ ] Add deprecation warnings if needed

## Phase 4: Update MCP Tools

### 4.1 Update MCP Server
- [ ] Open `src/mcp_server.py`
- [ ] Update `find_similar_characters` to use hybrid search
- [ ] Update `search_documents` to use hybrid search
- [ ] Add `search_type` parameter to tools (optional)

### 4.2 Add New Tools (Optional)
- [ ] Add `store_document` MCP tool
- [ ] Add `store_batch` MCP tool
- [ ] Add `hybrid_search` MCP tool

## Phase 5: Create REST API Routes (Optional)

### 5.1 Create Routes Directory
- [ ] Create `src/routes/` directory
- [ ] Create `src/routes/__init__.py`

### 5.2 Storage Routes
- [ ] Create `src/routes/storage.py`
- [ ] Implement `POST /store` endpoint
- [ ] Implement `POST /store/batch` endpoint
- [ ] Add request validation with Pydantic

### 5.3 Query Routes
- [ ] Create `src/routes/query.py`
- [ ] Implement `POST /query` endpoint
- [ ] Implement `POST /query/character-context` endpoint
- [ ] Implement `POST /query/story-bible` endpoint
- [ ] Add response formatting

### 5.4 Register Routes
- [ ] Update `src/main.py` to include routes
- [ ] Add CORS configuration
- [ ] Add error handling middleware

## Phase 6: Testing

### 6.1 Unit Tests
- [ ] Create `tests/unit/test_retriv_service.py`
- [ ] Test Retriv initialization
- [ ] Test document indexing
- [ ] Test search functionality
- [ ] Test filtering
- [ ] Test error handling

### 6.2 Integration Tests
- [ ] Create `tests/integration/test_enhanced_search.py`
- [ ] Test hybrid search vs semantic search
- [ ] Test end-to-end document storage and retrieval
- [ ] Test project isolation
- [ ] Test batch operations

### 6.3 Performance Tests
- [ ] Create `tests/performance/test_retriv_performance.py`
- [ ] Test search latency (should be < 100ms)
- [ ] Test indexing throughput
- [ ] Test concurrent queries
- [ ] Compare hybrid vs semantic performance

### 6.4 Contract Tests
- [ ] Test API request/response formats
- [ ] Test error responses
- [ ] Test backward compatibility

## Phase 7: Documentation

### 7.1 Code Documentation
- [ ] Add docstrings to all new methods
- [ ] Add type hints
- [ ] Add usage examples in docstrings

### 7.2 API Documentation
- [ ] Update `docs/api-contracts.md` with actual endpoints
- [ ] Add request/response examples
- [ ] Document error codes
- [ ] Add authentication details (if applicable)

### 7.3 Update README
- [ ] Update `README.md` with Retriv features
- [ ] Add setup instructions
- [ ] Add usage examples
- [ ] Update architecture diagram

### 7.4 Update WARP.md
- [ ] Add Retriv commands
- [ ] Add testing commands
- [ ] Add troubleshooting section

## Phase 8: Deployment Preparation

### 8.1 Environment Configuration
- [ ] Update `.env.example` with all Retriv variables
- [ ] Document environment variables in README
- [ ] Create production `.env` template

### 8.2 Docker Configuration
- [ ] Update `Dockerfile` if needed
- [ ] Update `docker-compose.yml` with Retriv volumes
- [ ] Test Docker build
- [ ] Test Docker run

### 8.3 Deployment Scripts
- [ ] Update deployment scripts
- [ ] Add data migration script (if needed)
- [ ] Add rollback procedure

### 8.4 Monitoring
- [ ] Add Retriv health check
- [ ] Add performance metrics
- [ ] Add error logging
- [ ] Add usage analytics

## Phase 9: Migration (If Existing Data)

### 9.1 Data Assessment
- [ ] Count existing documents in Neo4j
- [ ] Assess data quality
- [ ] Identify missing fields

### 9.2 Migration Script
- [ ] Create `scripts/migrate_to_retriv.py`
- [ ] Fetch all documents from Neo4j
- [ ] Transform to Retriv format
- [ ] Index in Retriv
- [ ] Verify migration

### 9.3 Validation
- [ ] Compare search results before/after
- [ ] Verify all documents indexed
- [ ] Check for data loss

## Phase 10: Deployment

### 10.1 Staging Deployment
- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Test with real data
- [ ] Monitor performance

### 10.2 Production Deployment
- [ ] Create deployment plan
- [ ] Schedule maintenance window (if needed)
- [ ] Deploy to production
- [ ] Run health checks
- [ ] Monitor for errors

### 10.3 Post-Deployment
- [ ] Verify all services running
- [ ] Check search quality
- [ ] Monitor performance metrics
- [ ] Gather user feedback

## Phase 11: Optimization (Post-Launch)

### 11.1 Performance Tuning
- [ ] Analyze slow queries
- [ ] Optimize Retriv configuration
- [ ] Add caching if needed
- [ ] Tune batch sizes

### 11.2 Search Quality
- [ ] Collect search queries
- [ ] Analyze result relevance
- [ ] Adjust Retriv parameters
- [ ] A/B test configurations

### 11.3 Monitoring & Alerts
- [ ] Set up performance alerts
- [ ] Set up error alerts
- [ ] Create dashboard
- [ ] Document metrics

## Success Criteria

### Functional Requirements
- [ ] Hybrid search returns relevant results
- [ ] Search includes both keyword and semantic matches
- [ ] Project isolation works correctly
- [ ] Batch operations work efficiently

### Performance Requirements
- [ ] Search latency < 100ms (p95)
- [ ] Indexing throughput > 100 docs/sec
- [ ] No degradation of existing features
- [ ] Memory usage within acceptable limits

### Quality Requirements
- [ ] All tests passing
- [ ] Code coverage > 80%
- [ ] No critical bugs
- [ ] Documentation complete

## Rollback Plan

If issues arise:

1. [ ] Revert to previous version
2. [ ] Disable Retriv integration
3. [ ] Fall back to Jina-only search
4. [ ] Investigate and fix issues
5. [ ] Redeploy when ready

## Notes

- Keep brain service as pure infrastructure
- No business logic in brain service
- App prepares data, brain service stores/retrieves
- Retriv enhances queries, doesn't replace existing functionality

## Timeline Estimate

- **Phase 1-2**: 2-3 hours (Setup & Retriv Service)
- **Phase 3-4**: 2-3 hours (Integration)
- **Phase 5**: 3-4 hours (REST API - Optional)
- **Phase 6**: 4-5 hours (Testing)
- **Phase 7**: 2-3 hours (Documentation)
- **Phase 8-10**: 3-4 hours (Deployment)

**Total**: ~20-25 hours for complete implementation

## Questions/Blockers

Track any questions or blockers here:

- [ ] Question 1: ...
- [ ] Blocker 1: ...

## Completion

- [ ] All phases complete
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Deployed to production
- [ ] Monitoring in place
- [ ] Team trained

**Completed by**: ___________
**Date**: ___________

