# How to Use MCP Brain Service with Retriv Hybrid Search

## Overview

The MCP Brain Service provides hybrid search capabilities combining **BM25 (keyword matching)** and **Dense Embeddings (semantic search)** for better, more accurate search results.

**Service URL**: https://brain.ft.tc  
**Port**: 8002 (internal)  
**Protocol**: HTTP/HTTPS

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Using Retriv Service](#using-retriv-service)
4. [Integration Examples](#integration-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Health Check

```bash
# Check if service is running
curl https://brain.ft.tc/health

# Response
{
  "status": "healthy",
  "timestamp": "2025-10-01T04:24:53.487345Z"
}
```

### Basic Search Request

```bash
curl -X POST https://brain.ft.tc/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Aladdin wearing brown vest",
    "project_id": "my_project_123",
    "top_k": 5
  }'
```

---

## API Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T04:24:53.487345Z"
}
```

### 2. Index Documents (Future)

**Endpoint**: `POST /index`

**Request**:
```json
{
  "documents": [
    {
      "id": "char_aladdin",
      "text": "Aladdin is a street-smart young man who wears a brown vest and purple pants",
      "metadata": {
        "project_id": "aladdin_movie",
        "type": "character",
        "name": "Aladdin"
      }
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "indexed": 1,
  "message": "Documents indexed successfully"
}
```

### 3. Hybrid Search (Future)

**Endpoint**: `POST /search`

**Request**:
```json
{
  "query": "brown vest scene 3",
  "project_id": "aladdin_movie",
  "top_k": 5,
  "filters": {
    "type": "character"
  }
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "char_aladdin",
      "text": "Aladdin wears a brown vest...",
      "score": 0.95,
      "metadata": {
        "project_id": "aladdin_movie",
        "type": "character",
        "name": "Aladdin"
      }
    }
  ],
  "total": 1,
  "query_time_ms": 45
}
```

---

## Using Retriv Service

### Python Integration

#### 1. Direct Service Usage

```python
import httpx
import asyncio

async def search_brain_service(query: str, project_id: str):
    """Search using the brain service."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://brain.ft.tc/search",
            json={
                "query": query,
                "project_id": project_id,
                "top_k": 5
            },
            timeout=30.0
        )
        return response.json()

# Usage
results = asyncio.run(search_brain_service(
    query="Aladdin's vest in scene 3",
    project_id="my_project"
))
```

#### 2. Internal Service Usage (Same Server)

If your app is on the same server, you can import the service directly:

```python
from src.services.retriv_service import get_retriv_service

async def use_retriv():
    # Get service instance
    retriv = get_retriv_service()
    
    # Initialize (lazy loading)
    await retriv.initialize()
    
    # Index documents
    documents = [
        {
            "id": "char_1",
            "text": "Aladdin wears a brown vest and purple pants",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "character",
                "name": "Aladdin"
            }
        },
        {
            "id": "scene_3",
            "text": "Scene 3: Aladdin meets Jasmine in the marketplace",
            "metadata": {
                "project_id": "aladdin_movie",
                "type": "scene",
                "scene_number": 3
            }
        }
    ]
    
    await retriv.index_documents(documents)
    
    # Search with hybrid approach
    results = await retriv.search(
        query="brown vest scene 3",
        project_id="aladdin_movie",
        top_k=5
    )
    
    print(f"Found {len(results)} results")
    for result in results:
        print(f"- {result['id']}: {result['text'][:50]}...")
    
    # Get statistics
    stats = retriv.get_stats()
    print(f"Index stats: {stats}")
```

### Node.js Integration

```javascript
const axios = require('axios');

async function searchBrainService(query, projectId) {
  try {
    const response = await axios.post('https://brain.ft.tc/search', {
      query: query,
      project_id: projectId,
      top_k: 5
    }, {
      timeout: 30000
    });
    
    return response.data;
  } catch (error) {
    console.error('Search failed:', error.message);
    throw error;
  }
}

// Usage
searchBrainService("Aladdin's vest in scene 3", "my_project")
  .then(results => {
    console.log('Search results:', results);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

---

## Integration Examples

### Example 1: Story Bible Service Integration

```python
# In your story bible service
import httpx

class StoryBibleService:
    def __init__(self):
        self.brain_url = "https://brain.ft.tc"
    
    async def find_character_details(self, character_name: str, project_id: str):
        """Find character details using hybrid search."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/search",
                json={
                    "query": f"{character_name} appearance clothing description",
                    "project_id": project_id,
                    "top_k": 3,
                    "filters": {"type": "character"}
                }
            )
            
            results = response.json()
            return results.get("results", [])
    
    async def find_scene_context(self, scene_number: int, project_id: str):
        """Find scene context using hybrid search."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/search",
                json={
                    "query": f"scene {scene_number}",
                    "project_id": project_id,
                    "top_k": 5,
                    "filters": {"type": "scene"}
                }
            )
            
            results = response.json()
            return results.get("results", [])
```

### Example 2: Visual Design Service Integration

```python
# In your visual design service
import httpx

class VisualDesignService:
    def __init__(self):
        self.brain_url = "https://brain.ft.tc"
    
    async def get_character_visual_references(
        self, 
        character_name: str, 
        project_id: str
    ):
        """Get visual references for character design."""
        async with httpx.AsyncClient() as client:
            # Search for character descriptions
            response = await client.post(
                f"{self.brain_url}/search",
                json={
                    "query": f"{character_name} appearance outfit clothing colors",
                    "project_id": project_id,
                    "top_k": 5,
                    "filters": {"type": "character"}
                }
            )
            
            results = response.json()
            
            # Extract visual details
            visual_refs = []
            for result in results.get("results", []):
                visual_refs.append({
                    "source": result["id"],
                    "description": result["text"],
                    "score": result["score"]
                })
            
            return visual_refs
```

### Example 3: Episode Breakdown Service Integration

```python
# In your episode breakdown service
import httpx

class EpisodeBreakdownService:
    def __init__(self):
        self.brain_url = "https://brain.ft.tc"
    
    async def find_related_scenes(
        self, 
        scene_description: str, 
        project_id: str
    ):
        """Find related scenes for continuity."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/search",
                json={
                    "query": scene_description,
                    "project_id": project_id,
                    "top_k": 10,
                    "filters": {"type": "scene"}
                }
            )
            
            results = response.json()
            return results.get("results", [])
    
    async def check_character_consistency(
        self, 
        character_name: str, 
        scene_number: int,
        project_id: str
    ):
        """Check character consistency across scenes."""
        async with httpx.AsyncClient() as client:
            # Find character in specific scene
            response = await client.post(
                f"{self.brain_url}/search",
                json={
                    "query": f"{character_name} scene {scene_number}",
                    "project_id": project_id,
                    "top_k": 5
                }
            )
            
            results = response.json()
            return results.get("results", [])
```

---

## Best Practices

### 1. Query Construction

**Good Queries** (Hybrid search works best):
```python
# Combine keywords + context
"Aladdin brown vest scene 3"
"Jasmine blue outfit marketplace"
"Genie magical powers lamp"
```

**Less Effective Queries**:
```python
# Too vague
"character"
"scene"

# Too long (truncated at 128 tokens)
"very long description that goes on and on..."
```

### 2. Project Isolation

Always use `project_id` to isolate your data:

```python
# Good - isolated by project
results = await retriv.search(
    query="Aladdin",
    project_id="aladdin_movie",  # ✓ Isolated
    top_k=5
)

# Bad - searches across all projects
results = await retriv.search(
    query="Aladdin",
    project_id=None,  # ✗ Not isolated
    top_k=5
)
```

### 3. Metadata Filtering

Use filters to narrow down results:

```python
# Filter by type
results = await retriv.search(
    query="brown vest",
    project_id="aladdin_movie",
    filters={"type": "character"},  # Only characters
    top_k=5
)

# Multiple filters
results = await retriv.search(
    query="marketplace",
    project_id="aladdin_movie",
    filters={
        "type": "scene",
        "location": "marketplace"
    },
    top_k=5
)
```

### 4. Error Handling

Always handle errors gracefully:

```python
import httpx

async def safe_search(query: str, project_id: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://brain.ft.tc/search",
                json={
                    "query": query,
                    "project_id": project_id,
                    "top_k": 5
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        print("Search timed out")
        return {"results": [], "error": "timeout"}
    except httpx.HTTPError as e:
        print(f"HTTP error: {e}")
        return {"results": [], "error": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"results": [], "error": str(e)}
```

### 5. Performance Optimization

```python
# Batch indexing (better performance)
documents = [doc1, doc2, doc3, ...]  # Many documents
await retriv.index_documents(documents)  # ✓ Single call

# vs

# Individual indexing (slower)
for doc in documents:
    await retriv.index_documents([doc])  # ✗ Multiple calls
```

---

## Troubleshooting

### Service Not Responding

```bash
# Check if service is running
pm2 list | grep brain-api

# Check logs
pm2 logs brain-api

# Restart if needed
pm2 restart brain-api
```

### Search Returns No Results

1. **Check if documents are indexed**:
   ```python
   stats = retriv.get_stats()
   print(f"Total documents: {stats['total_documents']}")
   ```

2. **Verify project_id matches**:
   ```python
   # Make sure project_id is consistent
   await retriv.index_documents([{
       "id": "doc1",
       "text": "...",
       "metadata": {"project_id": "my_project"}  # ✓ Same ID
   }])
   
   results = await retriv.search(
       query="...",
       project_id="my_project"  # ✓ Same ID
   )
   ```

3. **Try broader query**:
   ```python
   # Too specific
   results = await retriv.search(query="exact phrase match")
   
   # Better
   results = await retriv.search(query="key words from phrase")
   ```

### Slow Performance

1. **Reduce top_k**:
   ```python
   # Faster
   results = await retriv.search(query="...", top_k=5)
   
   # Slower
   results = await retriv.search(query="...", top_k=100)
   ```

2. **Use filters**:
   ```python
   # Faster - filtered search
   results = await retriv.search(
       query="...",
       filters={"type": "character"}
   )
   ```

---

## Support

### Documentation
- **Deployment Guide**: `/services/mcp-brain-service/RETRIV_DEPLOYMENT.md`
- **Integration Plan**: `/services/mcp-brain-service/docs/retriv-integration-plan.md`
- **API Contracts**: `/services/mcp-brain-service/docs/api-contracts.md`

### Service Information
- **URL**: https://brain.ft.tc
- **Health**: https://brain.ft.tc/health
- **PM2 Process**: brain-api (ID: 2)

### Logs
```bash
# View logs
pm2 logs brain-api

# Error logs only
pm2 logs brain-api --err

# Last 100 lines
pm2 logs brain-api --lines 100
```

---

## Summary

The MCP Brain Service with Retriv provides:
- ✅ **Hybrid Search**: BM25 (keyword) + Embeddings (semantic)
- ✅ **Better Accuracy**: Combines exact matching with semantic understanding
- ✅ **Project Isolation**: Keep your data separate
- ✅ **Flexible Filtering**: Filter by metadata
- ✅ **Easy Integration**: Simple HTTP API or direct Python import

**Start using it today to improve your search results!**

