# Retriv Integration Plan

## Overview

Enhance the MCP Brain Service with Retriv hybrid search to provide better query results by combining keyword matching (BM25) with semantic search (embeddings).

**Key Principle**: Retriv is not a separate system - it's an enhancement to existing query capabilities.

## Architecture Decision

### What We're NOT Doing
- ❌ Creating separate agent services
- ❌ Adding data preparation logic to brain service
- ❌ Making brain service understand PayloadCMS structure
- ❌ Creating new APIs or routes

### What We ARE Doing
- ✅ Adding Retriv as a better query engine
- ✅ Enhancing existing search methods
- ✅ Keeping brain service as pure infrastructure
- ✅ Making existing MCP tools return better results

## Current vs Enhanced Architecture

### Current Query Flow
```
Query → Jina Embeddings → Semantic Search → Results
Query → Neo4j → Graph Relationships → Results
```

### Enhanced Query Flow (With Retriv)
```
Query → Retriv (BM25 + Embeddings) → Hybrid Search → Better Results
Query → Neo4j → Graph Relationships → Results
```

**Retriv replaces/enhances Jina-only search with hybrid search (keyword + semantic)**

## Why Retriv?

### Problem with Current Approach
- **Jina alone**: Good for semantic similarity, but misses exact keyword matches
- **Example**: Query "Aladdin's vest in scene 3"
  - Jina might miss "vest" if it focuses on semantic meaning
  - Jina might miss "scene 3" exact number

### Solution with Retriv
- **Hybrid Search**: Combines BM25 (keyword) + Dense embeddings (semantic)
- **Example**: Query "Aladdin's vest in scene 3"
  - BM25 catches: "Aladdin", "vest", "scene", "3" (exact matches)
  - Embeddings catch: semantic meaning of "clothing", "appearance"
  - Combined: More accurate results!

## Implementation Plan

### Phase 1: Add Retriv Package
**File**: `requirements.txt`

```txt
# Add to existing requirements
retriv==0.2.4
```

### Phase 2: Create Retriv Service
**File**: `src/services/retriv_service.py`

```python
"""Retriv hybrid search service for enhanced querying."""

from typing import List, Dict, Any, Optional
from retriv import HybridRetriever
import logging

logger = logging.getLogger(__name__)


class RetrivService:
    """Wrapper around Retriv for hybrid search (BM25 + embeddings)."""
    
    def __init__(self, index_path: str = "./data/retriv_index"):
        self.index_path = index_path
        self.retriever = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Retriv retriever."""
        if self._initialized:
            return
        
        try:
            self.retriever = HybridRetriever(
                index_name="brain_service",
                model="sentence-transformers/all-MiniLM-L6-v2",  # Fast, good quality
                min_df=1,
                tokenizer="whitespace",
                stemmer="english",
                stopwords="english",
                do_lowercasing=True,
                do_ampersand_normalization=True,
                do_special_chars_normalization=True,
                do_acronyms_normalization=True,
                do_punctuation_removal=True,
            )
            self._initialized = True
            logger.info("Retriv service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Retriv: {e}")
            raise
    
    async def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents for hybrid search.
        
        Args:
            documents: List of documents with structure:
                {
                    "id": "unique_id",
                    "text": "searchable text content",
                    "metadata": {...}
                }
        """
        if not self._initialized:
            await self.initialize()
        
        # Prepare documents for Retriv
        collection = [
            {
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc.get("metadata", {})
            }
            for doc in documents
        ]
        
        # Index documents
        self.retriever.index(collection)
        logger.info(f"Indexed {len(collection)} documents in Retriv")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search using BM25 + embeddings.
        
        Args:
            query: Search query
            top_k: Number of results to return
            project_id: Filter by project ID
            filters: Additional metadata filters
        
        Returns:
            List of search results with scores
        """
        if not self._initialized:
            await self.initialize()
        
        # Perform hybrid search
        results = self.retriever.search(
            query=query,
            return_docs=True,
            cutoff=top_k
        )
        
        # Apply filters
        filtered_results = []
        for result in results:
            metadata = result.get("metadata", {})
            
            # Filter by project_id
            if project_id and metadata.get("project_id") != project_id:
                continue
            
            # Apply custom filters
            if filters:
                if not self._matches_filters(metadata, filters):
                    continue
            
            filtered_results.append(result)
        
        return filtered_results[:top_k]
    
    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                # Check if any filter value matches
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        return True
    
    async def delete_document(self, doc_id: str):
        """Delete a document from the index."""
        if not self._initialized:
            await self.initialize()
        
        # Retriv doesn't have direct delete, need to rebuild index
        # For now, log warning
        logger.warning(f"Document deletion not implemented for Retriv: {doc_id}")
    
    async def clear_project(self, project_id: str):
        """Clear all documents for a project."""
        if not self._initialized:
            await self.initialize()
        
        # Retriv doesn't have direct delete, need to rebuild index
        logger.warning(f"Project clearing not implemented for Retriv: {project_id}")


# Global instance
_retriv_service: Optional[RetrivService] = None


def get_retriv_service() -> RetrivService:
    """Get or create global Retriv service instance."""
    global _retriv_service
    
    if _retriv_service is None:
        _retriv_service = RetrivService()
    
    return _retriv_service
```

### Phase 3: Enhance Knowledge Service
**File**: `src/services/knowledge_service.py`

Enhance the existing `KnowledgeService` to use Retriv for better search:

```python
# Add to existing imports
from .retriv_service import get_retriv_service

class KnowledgeService:
    def __init__(self, jina_service, neo4j_client):
        self.jina = jina_service
        self.neo4j = neo4j_client
        self.retriv = get_retriv_service()  # NEW
    
    async def initialize(self):
        """Initialize all services."""
        await self.retriv.initialize()
    
    async def store_document(self, document: Dict[str, Any]):
        """
        Store document in all systems.
        
        Args:
            document: {
                "id": "unique_id",
                "type": "character|scene|image",
                "project_id": "proj_123",
                "text": "searchable text",
                "metadata": {...},
                "relationships": [...]
            }
        """
        # 1. Store in Neo4j (existing)
        await self._store_in_neo4j(document)
        
        # 2. Generate and store embeddings (existing)
        embedding = await self.jina.embed_single(document["text"])
        await self._store_embedding(document["id"], embedding)
        
        # 3. Index in Retriv (NEW)
        await self.retriv.index_documents([document])
    
    async def search(
        self,
        query: str,
        project_id: str,
        search_type: str = "hybrid",  # "hybrid", "semantic", "graph"
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search using Retriv hybrid search.
        
        Args:
            query: Search query
            project_id: Project to search within
            search_type: Type of search to perform
            top_k: Number of results
        
        Returns:
            List of search results
        """
        if search_type == "hybrid":
            # Use Retriv for hybrid search (BETTER!)
            results = await self.retriv.search(
                query=query,
                project_id=project_id,
                top_k=top_k
            )
        elif search_type == "semantic":
            # Use Jina for pure semantic search (existing)
            results = await self._semantic_search(query, project_id, top_k)
        elif search_type == "graph":
            # Use Neo4j for graph queries (existing)
            results = await self._graph_search(query, project_id, top_k)
        else:
            raise ValueError(f"Unknown search_type: {search_type}")
        
        return results
```

### Phase 4: Update MCP Tools
**File**: `src/mcp_server.py`

Existing MCP tools automatically get better results:

```python
@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:
    """Handle MCP tool calls."""
    
    if name == "find_similar_characters":
        # This now uses Retriv hybrid search automatically!
        results = await knowledge_service.search(
            query=arguments["query"],
            project_id=arguments["project_id"],
            search_type="hybrid",  # Better than pure semantic
            top_k=arguments.get("limit", 5)
        )
        return [types.TextContent(type="text", text=json.dumps(results))]
    
    # ... other tools
```

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_retriv_service.py

async def test_retriv_indexing():
    """Test document indexing."""
    retriv = RetrivService()
    await retriv.initialize()
    
    docs = [
        {
            "id": "char_1",
            "text": "Aladdin wears a brown vest",
            "metadata": {"project_id": "proj_1", "type": "character"}
        }
    ]
    
    await retriv.index_documents(docs)
    results = await retriv.search("brown vest", project_id="proj_1")
    
    assert len(results) > 0
    assert results[0]["id"] == "char_1"
```

### Integration Tests
```python
# tests/integration/test_enhanced_search.py

async def test_hybrid_search_better_than_semantic():
    """Test that hybrid search gives better results."""
    # Index test data
    await knowledge_service.store_document({
        "id": "char_aladdin",
        "text": "Aladdin wears brown vest in scene 3",
        "project_id": "test_proj"
    })
    
    # Query with exact keywords
    hybrid_results = await knowledge_service.search(
        query="brown vest scene 3",
        project_id="test_proj",
        search_type="hybrid"
    )
    
    semantic_results = await knowledge_service.search(
        query="brown vest scene 3",
        project_id="test_proj",
        search_type="semantic"
    )
    
    # Hybrid should rank exact matches higher
    assert hybrid_results[0]["score"] >= semantic_results[0]["score"]
```

## Deployment

### Update Requirements
```bash
cd mcp-brain-service
pip install -r requirements.txt
```

### Initialize Retriv on Startup
The service will automatically initialize Retriv when first used.

### Data Migration (Optional)
If you have existing data, re-index it:

```python
# One-time migration script
async def migrate_existing_data():
    """Re-index existing Neo4j data into Retriv."""
    # Fetch all documents from Neo4j
    documents = await neo4j_client.get_all_documents()
    
    # Index in Retriv
    await retriv_service.index_documents(documents)
```

## Benefits

1. **Better Search Results**: Hybrid search combines keyword + semantic
2. **Backward Compatible**: Existing code still works
3. **No API Changes**: Same MCP tools, just better results
4. **Drop-in Enhancement**: Minimal code changes
5. **Story Bible Ready**: Perfect for "Aladdin's vest in scene 3" type queries

## Next Steps

1. Add `retriv` to requirements.txt
2. Create `retriv_service.py`
3. Enhance `knowledge_service.py`
4. Test with existing MCP tools
5. Deploy to brain.ft.tc

