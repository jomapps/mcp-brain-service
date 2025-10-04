# How to Use MCP Brain Service

## Overview

The MCP Brain Service is a **Knowledge Graph API** that provides semantic search capabilities using **Neo4j Graph Database** and **Jina AI Embeddings (v4)**. It combines graph-based knowledge storage with vector embeddings for powerful semantic search and relationship tracking.

**Service URL**: https://brain.ft.tc
**Port**: 8002
**Protocol**: HTTP/HTTPS
**API Version**: v1
**Base Path**: `/api/v1`

### Key Features
- ✅ **Neo4j Graph Database** - Store nodes and relationships
- ✅ **Jina Embeddings v4** - State-of-the-art semantic embeddings
- ✅ **Neo4j GDS 2.13.2** - Graph Data Science with cosine similarity
- ✅ **Semantic Search** - Find similar content using vector embeddings
- ✅ **Content Validation** - Automatic rejection of invalid/error data (v1.2.0)
- ✅ **Node Deletion** - API endpoint and bulk cleanup tools (v1.2.0)
- ✅ **Batch Operations** - Efficient bulk node creation and processing (v1.1.0)
- ✅ **Project Isolation** - Keep your data separate by project
- ✅ **Systemd Service** - Auto-start on boot, auto-restart on failure

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Integration Examples](#integration-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Service Management](#service-management)

---

## Quick Start

### Health Check (No Authentication Required)

```bash
# Check if service is running
curl https://brain.ft.tc/health

# Response
{
  "status": "healthy",
  "service": "MCP Brain Service",
  "version": "1.0.0",
  "timestamp": "2025-10-04T00:22:10.104554Z",
  "components": {
    "neo4j": {
      "status": "healthy",
      "uri": "neo4j://127.0.0.1:7687",
      "timestamp": "2025-10-04T00:22:09.387352"
    },
    "jina": {
      "status": "healthy",
      "model": "jina-embeddings-v4",
      "timestamp": "2025-10-04T00:22:10.104512"
    }
  }
}
```

### Basic Node Creation

```bash
curl -X POST https://brain.ft.tc/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "character",
    "content": "Aladdin is a street-smart young man who wears a brown vest and purple pants",
    "projectId": "aladdin_movie",
    "properties": {
      "name": "Aladdin",
      "outfit": "brown vest, purple pants"
    }
  }'
```

### Basic Search Request

```bash
curl -X POST https://brain.ft.tc/api/v1/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "character wearing brown vest",
    "project_id": "aladdin_movie",
    "top_k": 5
  }'
```

---

## Authentication

All `/api/v1/*` endpoints require Bearer token authentication.

**Header Format**:
```
Authorization: Bearer YOUR_API_KEY
```

**Getting Your API Key**:
- Contact your system administrator
- Or check the `.env` file on the server: `API_KEY` variable

**Example**:
```bash
curl -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  https://brain.ft.tc/api/v1/health
```

---

## API Endpoints

### 1. Health Check (Public - No Auth)

**Endpoint**: `GET /health`

**Description**: Check if the service is running and healthy.

**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "service": "MCP Brain Service",
  "version": "1.0.0",
  "timestamp": "2025-10-04T00:22:10.104554Z",
  "components": {
    "neo4j": {
      "status": "healthy",
      "uri": "neo4j://127.0.0.1:7687",
      "timestamp": "2025-10-04T00:22:09.387352"
    },
    "jina": {
      "status": "healthy",
      "model": "jina-embeddings-v4",
      "timestamp": "2025-10-04T00:22:10.104512"
    }
  }
}
```

### 2. Authenticated Health Check

**Endpoint**: `GET /api/v1/health`

**Description**: Health check with authentication verification.

**Authentication**: Required

**Response**:
```json
{
  "status": "healthy",
  "service": "MCP Brain Service",
  "version": "1.0.0",
  "timestamp": "2025-10-04T00:22:30.386560Z"
}
```

### 3. Create Node

**Endpoint**: `POST /api/v1/nodes`

**Description**: Create a new node in the knowledge graph with automatic embedding generation.

**Authentication**: Required

**Request Body**:
```json
{
  "type": "character",
  "content": "Aladdin is a street-smart young man who wears a brown vest and purple pants",
  "projectId": "aladdin_movie",
  "properties": {
    "name": "Aladdin",
    "outfit": "brown vest, purple pants",
    "role": "protagonist"
  }
}
```

**Response**:
```json
{
  "node": {
    "id": "7b7d3e95-1512-4791-b5ef-648d2fa02aa9",
    "type": "character",
    "content": "Aladdin is a street-smart young man who wears a brown vest and purple pants",
    "projectId": "aladdin_movie",
    "properties": {
      "name": "Aladdin",
      "outfit": "brown vest, purple pants",
      "role": "protagonist"
    }
  }
}
```

**Notes**:
- `content` is used to generate the embedding automatically
- `properties` can contain nested objects (they will be serialized to JSON)
- Each node gets a unique UUID

### 4. Semantic Search

**Endpoint**: `POST /api/v1/search`

**Description**: Search for similar nodes using semantic embeddings with Neo4j GDS cosine similarity.

**Authentication**: Required

**Request Body**:
```json
{
  "query": "character wearing brown vest",
  "project_id": "aladdin_movie",
  "top_k": 5
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "7b7d3e95-1512-4791-b5ef-648d2fa02aa9",
      "type": "character",
      "text": "",
      "content": "",
      "score": 0.8786,
      "similarity": 0.8786,
      "metadata": {
        "type": "character",
        "project_id": "aladdin_movie",
        "name": "Aladdin",
        "outfit": "brown vest, purple pants"
      },
      "relationships": null
    }
  ],
  "total_count": 1,
  "query_time_ms": 946.03
}
```

**Notes**:
- Uses Jina embeddings v4 for query encoding
- Uses Neo4j GDS cosine similarity for matching
- Results are sorted by similarity score (higher is better)
- `project_id` filters results to specific project

### 5. Get Node by ID

**Endpoint**: `GET /api/v1/nodes/{node_id}`

**Description**: Retrieve a specific node by its ID.

**Authentication**: Required

**Response**:
```json
{
  "id": "7b7d3e95-1512-4791-b5ef-648d2fa02aa9",
  "type": "character",
  "content": "Aladdin is a street-smart young man...",
  "properties": {
    "name": "Aladdin",
    "project_id": "aladdin_movie"
  }
}
```

### 6. Get Statistics

**Endpoint**: `GET /api/v1/stats`

**Description**: Get database statistics.

**Authentication**: Required

**Response**:
```json
{
  "totalNodes": 3,
  "totalRelationships": 0,
  "nodesByType": {
    "Document": 0,
    "character": 2,
    "deployment_test": 1
  }
}
```

---

## 🆕 Data Quality & Deletion Features (v1.2.0)

### Content Validation (Automatic)

All node creation requests (`POST /api/v1/nodes` and `POST /api/v1/nodes/batch`) are automatically validated to prevent invalid data from being stored.

**Validation Rules**:
- ✅ Content cannot be empty or whitespace-only
- ✅ Content must be at least 10 characters long
- ✅ Content cannot contain error patterns:
  - "error:" (case-insensitive)
  - "no user message"
  - "undefined"
  - "null"

**Example - Invalid Request**:
```bash
curl -X POST https://brain.ft.tc/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gather",
    "content": "Error: No user message found",
    "projectId": "my-project"
  }'
```

**Response (400 Bad Request)**:
```json
{
  "error": "validation_failed",
  "message": "Invalid content: Cannot store error messages or invalid data",
  "details": {
    "field": "content",
    "pattern_matched": "error:",
    "reason": "Error messages and invalid data are not allowed"
  }
}
```

**Example - Valid Request**:
```bash
curl -X POST https://brain.ft.tc/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gather",
    "content": "User wants to book a flight to Paris for next week",
    "projectId": "my-project"
  }'
```

**Response (200 OK)**:
```json
{
  "node": {
    "id": "abc-123-def-456",
    "type": "gather",
    "content": "User wants to book a flight to Paris for next week",
    "projectId": "my-project",
    "properties": {}
  }
}
```

### 7. Delete Node

**Endpoint**: `DELETE /api/v1/nodes/{node_id}`

**Description**: Delete a specific node and all its relationships from the knowledge graph.

**Authentication**: Required

**Query Parameters**:
- `project_id` (required): Project ID for isolation and security

**Example Request**:
```bash
curl -X DELETE "https://brain.ft.tc/api/v1/nodes/abc-123-def-456?project_id=my-project" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Success Response (200 OK)**:
```json
{
  "status": "success",
  "message": "Node deleted successfully",
  "deleted_count": 1,
  "node_id": "abc-123-def-456"
}
```

**Error Response (404 Not Found)**:
```json
{
  "error": "node_not_found",
  "message": "Node with ID 'abc-123-def-456' not found in project 'my-project'",
  "details": {
    "node_id": "abc-123-def-456",
    "project_id": "my-project"
  }
}
```

**Notes**:
- Uses `DETACH DELETE` to remove the node and all its relationships
- Requires both node ID and project ID for security
- Returns 404 if node doesn't exist or belongs to different project
- All deletions are logged for audit purposes

### Bulk Cleanup Script

For bulk deletion of invalid nodes, use the cleanup script:

```bash
# Preview what would be deleted (always start here)
python scripts/cleanup_invalid_nodes.py --dry-run

# List all projects and their node counts
python scripts/cleanup_invalid_nodes.py --list-projects

# Clean specific project
python scripts/cleanup_invalid_nodes.py --project-id my-project-123

# Clean all projects
python scripts/cleanup_invalid_nodes.py

# Custom patterns
python scripts/cleanup_invalid_nodes.py --patterns "Error:" "test data" "invalid"

# Verbose output
python scripts/cleanup_invalid_nodes.py --verbose --dry-run
```

**Default Invalid Patterns**:
- `Error:`, `error:`
- `no user message`, `No user message`
- `undefined`, `null`, `NULL`
- `[object Object]`, `NaN`

**Example Output**:
```
============================================================
CLEANUP INVALID NODES
============================================================
Mode: DRY RUN (preview only)
Project filter: All projects
Patterns: Error:, error:, no user message, undefined, null
============================================================

Processing pattern: 'Error:'
  Would delete 5 nodes
  Sample IDs: ['abc-123', 'def-456', 'ghi-789']

Processing pattern: 'no user message'
  Would delete 3 nodes
  Sample IDs: ['jkl-012', 'mno-345']

============================================================
CLEANUP SUMMARY
============================================================
Total nodes found: 8
Would delete: 8 nodes

By pattern:
  'Error:': 5
  'no user message': 3

Duration: 1.23 seconds
============================================================

✅ Dry run completed. Run without --dry-run to actually delete nodes.
```

**Safety Features**:
- ✅ Dry-run mode (preview before deleting)
- ✅ 5-second countdown before live deletion
- ✅ Project filtering
- ✅ Detailed statistics and logging
- ✅ Error handling (continues on failure)

**Full Documentation**: See [Deletion & Validation Guide](./DELETION_AND_VALIDATION.md)

---

## 🆕 Batch Endpoints (v1.1.0)

### 7. Batch Node Creation

**Endpoint**: `POST /api/v1/nodes/batch`

**Description**: Create multiple nodes in a single request for efficient bulk operations.

**Authentication**: Required

**Request Body**:
```json
{
  "nodes": [
    {
      "type": "GatherItem",
      "content": "Full text content for embedding generation",
      "projectId": "507f1f77bcf86cd799439011",
      "properties": {
        "department": "story",
        "departmentName": "Story Department",
        "isAutomated": true,
        "iteration": 5,
        "qualityScore": 75.5
      }
    },
    {
      "type": "GatherItem",
      "content": "Another gather item content",
      "projectId": "507f1f77bcf86cd799439011",
      "properties": {
        "department": "character",
        "isAutomated": true
      }
    }
  ]
}
```

**Constraints**:
- Min nodes: 1
- Max nodes: 50
- Required fields: `type`, `content`, `projectId`
- projectId format: 24-character hex string (MongoDB ObjectId)

**Response**:
```json
{
  "success": true,
  "created": 2,
  "nodeIds": ["uuid-1", "uuid-2"],
  "nodes": [
    {
      "id": "uuid-1",
      "type": "GatherItem",
      "properties": {...},
      "embedding": {
        "dimensions": 1536,
        "model": "jina-embeddings-v4"
      }
    }
  ],
  "timing": {
    "embedding_time_ms": 626.8,
    "neo4j_write_time_ms": 60.3,
    "total_time_ms": 687.2
  }
}
```

**Example**:
```bash
curl -X POST https://brain.ft.tc/api/v1/nodes/batch \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [
      {
        "type": "GatherItem",
        "content": "Story premise: A hero embarks on a journey...",
        "projectId": "507f1f77bcf86cd799439011",
        "properties": {
          "department": "story",
          "isAutomated": true
        }
      }
    ]
  }'
```

### 8. Duplicate Search

**Endpoint**: `POST /api/v1/search/duplicates`

**Description**: Find semantically similar nodes to detect potential duplicates.

**Authentication**: Required

**Request Body**:
```json
{
  "content": "Text content to check for duplicates",
  "projectId": "507f1f77bcf86cd799439011",
  "threshold": 0.90,
  "limit": 10,
  "type": "GatherItem",
  "department": "story",
  "excludeNodeIds": ["node-id-to-exclude"]
}
```

**Parameters**:
- `content` (required): Text to find duplicates for
- `projectId` (required): Project ID (24 hex chars)
- `threshold` (optional, default: 0.90): Similarity threshold (0.0-1.0)
- `limit` (optional, default: 10): Max results (1-50)
- `type` (optional, default: "GatherItem"): Filter by node type
- `department` (optional): Filter by department
- `excludeNodeIds` (optional): Node IDs to exclude

**Response**:
```json
{
  "duplicates": [
    {
      "nodeId": "neo4j-id-456",
      "similarity": 0.95,
      "content": "Very similar content text",
      "properties": {
        "department": "story",
        "summary": "Brief summary",
        "createdAt": "2025-01-15T10:30:00Z"
      }
    }
  ],
  "query_embedding_time_ms": 200,
  "search_time_ms": 150,
  "total_time_ms": 350
}
```

**Example**:
```bash
curl -X POST https://brain.ft.tc/api/v1/search/duplicates \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Story about a hero journey",
    "projectId": "507f1f77bcf86cd799439011",
    "threshold": 0.85,
    "limit": 5,
    "department": "story"
  }'
```

### 9. Department Context Retrieval

**Endpoint**: `GET /api/v1/context/department`

**Description**: Aggregate context from previous departments with AI-powered theme extraction.

**Authentication**: Required

**Query Parameters**:
- `projectId` (required): Project ID (24 hex chars)
- `department` (required): Target department slug
- `previousDepartments` (optional): Previous department slugs (array)
- `limit` (optional, default: 20): Nodes per department (1-100)

**Response**:
```json
{
  "projectId": "507f1f77bcf86cd799439011",
  "targetDepartment": "character",
  "context": {
    "story": {
      "nodeCount": 15,
      "qualityScore": 85,
      "topNodes": [
        {
          "nodeId": "neo4j-id-1",
          "content": "Story premise...",
          "summary": "Main story arc",
          "relevance": 0.95
        }
      ],
      "keyThemes": ["redemption", "family", "sacrifice"]
    }
  },
  "aggregatedSummary": "The story follows a redemption arc...",
  "relevantNodes": [...],
  "totalNodesAggregated": 27,
  "timing": {
    "query_time_ms": 180,
    "aggregation_time_ms": 220,
    "total_time_ms": 400
  }
}
```

**Example**:
```bash
curl -X GET "https://brain.ft.tc/api/v1/context/department?projectId=507f1f77bcf86cd799439011&department=character&previousDepartments=story&previousDepartments=visual&limit=20" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 10. Coverage Analysis

**Endpoint**: `POST /api/v1/analyze/coverage`

**Description**: Analyze content coverage and identify gaps using AI-powered analysis.

**Authentication**: Required

**Request Body**:
```json
{
  "projectId": "507f1f77bcf86cd799439011",
  "department": "story",
  "gatherItems": [
    {
      "content": "Plot overview: The story follows...",
      "summary": "Main plot structure"
    },
    {
      "content": "Character development: Protagonist grows...",
      "summary": "Character arc"
    }
  ],
  "departmentDescription": "Story department handles narrative, plot structure, pacing, and themes"
}
```

**Constraints**:
- Max items: 100 gather items
- Required fields: `projectId`, `department`, `gatherItems`

**Response**:
```json
{
  "department": "story",
  "coverageScore": 75,
  "analysis": {
    "coveredAspects": [
      {
        "aspect": "Plot Structure",
        "coverage": 90,
        "itemCount": 5,
        "quality": "excellent"
      }
    ],
    "gaps": [
      {
        "aspect": "Pacing",
        "coverage": 20,
        "itemCount": 1,
        "severity": "high",
        "suggestion": "Add detailed pacing breakdown for each act"
      }
    ],
    "recommendations": [
      "Focus next iteration on pacing details",
      "Add dialogue samples to demonstrate character voices"
    ]
  },
  "itemDistribution": {
    "plot": 8,
    "character": 5,
    "theme": 3
  },
  "qualityMetrics": {
    "depth": 72,
    "breadth": 68,
    "coherence": 85,
    "actionability": 70
  },
  "timing": {
    "embedding_time_ms": 300,
    "analysis_time_ms": 450,
    "total_time_ms": 750
  }
}
```

**Example**:
```bash
curl -X POST https://brain.ft.tc/api/v1/analyze/coverage \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "507f1f77bcf86cd799439011",
    "department": "story",
    "gatherItems": [
      {
        "content": "Plot overview: Hero journey through challenges",
        "summary": "Main plot"
      }
    ]
  }'
```

---

## Integration Examples

### Python Integration

#### 1. Using httpx (Recommended for External Services)

```python
import httpx
import asyncio

class BrainServiceClient:
    def __init__(self, api_key: str, base_url: str = "https://brain.ft.tc"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def create_node(self, node_type: str, content: str, project_id: str, properties: dict = None):
        """Create a new node in the knowledge graph."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/nodes",
                headers=self.headers,
                json={
                    "type": node_type,
                    "content": content,
                    "projectId": project_id,
                    "properties": properties or {}
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def search(self, query: str, project_id: str, top_k: int = 5):
        """Search for similar nodes using semantic search."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/search",
                headers=self.headers,
                json={
                    "query": query,
                    "project_id": project_id,
                    "top_k": top_k
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_node(self, node_id: str):
        """Get a specific node by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/nodes/{node_id}",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_stats(self):
        """Get database statistics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/stats",
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def batch_create_nodes(self, nodes: list):
        """Create multiple nodes in a single batch request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/nodes/batch",
                headers=self.headers,
                json={"nodes": nodes},
                timeout=60.0  # Longer timeout for batch operations
            )
            response.raise_for_status()
            return response.json()

    async def search_duplicates(self, content: str, project_id: str, threshold: float = 0.90):
        """Search for duplicate content."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/search/duplicates",
                headers=self.headers,
                json={
                    "content": content,
                    "projectId": project_id,
                    "threshold": threshold,
                    "limit": 10
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def get_department_context(
        self,
        project_id: str,
        department: str,
        previous_departments: list = None
    ):
        """Get context from previous departments."""
        params = {
            "projectId": project_id,
            "department": department,
            "limit": 20
        }
        if previous_departments:
            params["previousDepartments"] = previous_departments

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/context/department",
                headers=self.headers,
                params=params,
                timeout=60.0  # LLM operations take longer
            )
            response.raise_for_status()
            return response.json()

    async def analyze_coverage(
        self,
        project_id: str,
        department: str,
        gather_items: list
    ):
        """Analyze content coverage."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/analyze/coverage",
                headers=self.headers,
                json={
                    "projectId": project_id,
                    "department": department,
                    "gatherItems": gather_items
                },
                timeout=60.0  # LLM operations take longer
            )
            response.raise_for_status()
            return response.json()

# Usage Example
async def main():
    client = BrainServiceClient(api_key="YOUR_API_KEY")

    # Create a character node
    node = await client.create_node(
        node_type="character",
        content="Aladdin is a street-smart young man who wears a brown vest",
        project_id="aladdin_movie",
        properties={
            "name": "Aladdin",
            "outfit": "brown vest, purple pants"
        }
    )
    print(f"Created node: {node['node']['id']}")

    # Search for similar content
    results = await client.search(
        query="character wearing brown vest",
        project_id="aladdin_movie",
        top_k=5
    )
    print(f"Found {results['total_count']} results")
    for result in results['results']:
        print(f"  - {result['id']}: similarity={result['similarity']:.4f}")

    # Get statistics
    stats = await client.get_stats()
    print(f"Total nodes: {stats['totalNodes']}")

    # Batch create nodes
    batch_result = await client.batch_create_nodes([
        {
            "type": "GatherItem",
            "content": "Story premise: Hero's journey",
            "projectId": "507f1f77bcf86cd799439011",
            "properties": {"department": "story"}
        },
        {
            "type": "GatherItem",
            "content": "Character description: Brave protagonist",
            "projectId": "507f1f77bcf86cd799439011",
            "properties": {"department": "character"}
        }
    ])
    print(f"Created {batch_result['created']} nodes in {batch_result['timing']['total_time_ms']:.2f}ms")

    # Check for duplicates
    duplicates = await client.search_duplicates(
        content="Story premise: Hero's journey",
        project_id="507f1f77bcf86cd799439011",
        threshold=0.85
    )
    print(f"Found {len(duplicates['duplicates'])} potential duplicates")

    # Get department context
    context = await client.get_department_context(
        project_id="507f1f77bcf86cd799439011",
        department="character",
        previous_departments=["story"]
    )
    print(f"Aggregated {context['totalNodesAggregated']} nodes from previous departments")

    # Analyze coverage
    coverage = await client.analyze_coverage(
        project_id="507f1f77bcf86cd799439011",
        department="story",
        gather_items=[
            {"content": "Plot overview", "summary": "Main plot"},
            {"content": "Character arcs", "summary": "Character development"}
        ]
    )
    print(f"Coverage score: {coverage['coverageScore']}%")

# Run
asyncio.run(main())
```

#### 2. Using requests (Synchronous)

```python
import requests

class BrainServiceClient:
    def __init__(self, api_key: str, base_url: str = "https://brain.ft.tc"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def create_node(self, node_type: str, content: str, project_id: str, properties: dict = None):
        """Create a new node."""
        response = requests.post(
            f"{self.base_url}/api/v1/nodes",
            headers=self.headers,
            json={
                "type": node_type,
                "content": content,
                "projectId": project_id,
                "properties": properties or {}
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def search(self, query: str, project_id: str, top_k: int = 5):
        """Search for similar nodes."""
        response = requests.post(
            f"{self.base_url}/api/v1/search",
            headers=self.headers,
            json={
                "query": query,
                "project_id": project_id,
                "top_k": top_k
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()

# Usage
client = BrainServiceClient(api_key="YOUR_API_KEY")
results = client.search("brown vest", "aladdin_movie")
print(results)
```

### Node.js Integration

```javascript
const axios = require('axios');

class BrainServiceClient {
  constructor(apiKey, baseUrl = 'https://brain.ft.tc') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  async createNode(type, content, projectId, properties = {}) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/v1/nodes`,
        {
          type,
          content,
          projectId,
          properties
        },
        {
          headers: this.headers,
          timeout: 30000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to create node:', error.message);
      throw error;
    }
  }

  async search(query, projectId, topK = 5) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/v1/search`,
        {
          query,
          project_id: projectId,
          top_k: topK
        },
        {
          headers: this.headers,
          timeout: 30000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Search failed:', error.message);
      throw error;
    }
  }

  async getNode(nodeId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/v1/nodes/${nodeId}`,
        {
          headers: this.headers,
          timeout: 30000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get node:', error.message);
      throw error;
    }
  }

  async getStats() {
    try {
      const response = await axios.get(
        `${this.baseUrl}/api/v1/stats`,
        {
          headers: this.headers,
          timeout: 30000
        }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get stats:', error.message);
      throw error;
    }
  }
}

// Usage Example
async function main() {
  const client = new BrainServiceClient('YOUR_API_KEY');

  // Create a node
  const node = await client.createNode(
    'character',
    'Aladdin is a street-smart young man who wears a brown vest',
    'aladdin_movie',
    { name: 'Aladdin', outfit: 'brown vest, purple pants' }
  );
  console.log('Created node:', node.node.id);

  // Search
  const results = await client.search(
    'character wearing brown vest',
    'aladdin_movie',
    5
  );
  console.log(`Found ${results.total_count} results`);
  results.results.forEach(result => {
    console.log(`  - ${result.id}: similarity=${result.similarity.toFixed(4)}`);
  });

  // Get stats
  const stats = await client.getStats();
  console.log(`Total nodes: ${stats.totalNodes}`);
}

main().catch(console.error);
```

---

## Use Case Examples

### Example 1: Story Bible Service Integration

```python
# In your story bible service
import httpx

class StoryBibleService:
    def __init__(self, api_key: str):
        self.brain_url = "https://brain.ft.tc"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def index_character(self, character_data: dict, project_id: str):
        """Index a character in the knowledge graph."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/api/v1/nodes",
                headers=self.headers,
                json={
                    "type": "character",
                    "content": character_data["description"],
                    "projectId": project_id,
                    "properties": {
                        "name": character_data["name"],
                        "outfit": character_data.get("outfit", ""),
                        "personality": character_data.get("personality", ""),
                        "role": character_data.get("role", "")
                    }
                }
            )
            return response.json()

    async def find_character_details(self, character_name: str, project_id: str):
        """Find character details using semantic search."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/api/v1/search",
                headers=self.headers,
                json={
                    "query": f"{character_name} appearance clothing description",
                    "project_id": project_id,
                    "top_k": 3
                }
            )

            results = response.json()
            return results.get("results", [])

    async def find_scene_context(self, scene_description: str, project_id: str):
        """Find scene context using semantic search."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/api/v1/search",
                headers=self.headers,
                json={
                    "query": scene_description,
                    "project_id": project_id,
                    "top_k": 5
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
    def __init__(self, api_key: str):
        self.brain_url = "https://brain.ft.tc"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def index_visual_reference(self, reference_data: dict, project_id: str):
        """Index a visual reference."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/api/v1/nodes",
                headers=self.headers,
                json={
                    "type": "visual_reference",
                    "content": reference_data["description"],
                    "projectId": project_id,
                    "properties": {
                        "character": reference_data.get("character", ""),
                        "colors": reference_data.get("colors", []),
                        "style": reference_data.get("style", ""),
                        "image_url": reference_data.get("image_url", "")
                    }
                }
            )
            return response.json()

    async def get_character_visual_references(
        self,
        character_name: str,
        project_id: str
    ):
        """Get visual references for character design."""
        async with httpx.AsyncClient() as client:
            # Search for character descriptions
            response = await client.post(
                f"{self.brain_url}/api/v1/search",
                headers=self.headers,
                json={
                    "query": f"{character_name} appearance outfit clothing colors style",
                    "project_id": project_id,
                    "top_k": 5
                }
            )

            results = response.json()

            # Extract visual details
            visual_refs = []
            for result in results.get("results", []):
                visual_refs.append({
                    "id": result["id"],
                    "type": result["type"],
                    "similarity": result["similarity"],
                    "metadata": result["metadata"]
                })

            return visual_refs
```

### Example 3: Episode Breakdown Service Integration

```python
# In your episode breakdown service
import httpx

class EpisodeBreakdownService:
    def __init__(self, api_key: str):
        self.brain_url = "https://brain.ft.tc"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def index_scene(self, scene_data: dict, project_id: str):
        """Index a scene in the knowledge graph."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/api/v1/nodes",
                headers=self.headers,
                json={
                    "type": "scene",
                    "content": scene_data["description"],
                    "projectId": project_id,
                    "properties": {
                        "scene_number": scene_data["scene_number"],
                        "location": scene_data.get("location", ""),
                        "characters": scene_data.get("characters", []),
                        "time_of_day": scene_data.get("time_of_day", "")
                    }
                }
            )
            return response.json()

    async def find_related_scenes(
        self,
        scene_description: str,
        project_id: str
    ):
        """Find related scenes for continuity."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.brain_url}/api/v1/search",
                headers=self.headers,
                json={
                    "query": scene_description,
                    "project_id": project_id,
                    "top_k": 10
                }
            )

            results = response.json()
            return results.get("results", [])

    async def check_character_consistency(
        self,
        character_name: str,
        scene_context: str,
        project_id: str
    ):
        """Check character consistency across scenes."""
        async with httpx.AsyncClient() as client:
            # Find character in specific context
            response = await client.post(
                f"{self.brain_url}/api/v1/search",
                headers=self.headers,
                json={
                    "query": f"{character_name} {scene_context}",
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

**Good Queries** (Semantic search works best with descriptive text):
```python
# Descriptive and specific
"Aladdin wearing brown vest and purple pants"
"Jasmine in blue outfit at the marketplace"
"Genie with magical powers emerging from lamp"
"Scene where characters meet in the bazaar"
```

**Less Effective Queries**:
```python
# Too vague
"character"
"scene"

# Single keywords (better to add context)
"vest"  # Better: "character wearing vest"
```

### 2. Project Isolation

**Always use `project_id`** to isolate your data:

```python
# ✅ Good - isolated by project
results = await client.search(
    query="Aladdin",
    project_id="aladdin_movie",  # Isolated to this project
    top_k=5
)

# ✅ Also good - different projects don't interfere
results = await client.search(
    query="Aladdin",
    project_id="another_movie",  # Different project
    top_k=5
)
```

**Why it matters**:
- Prevents cross-project contamination
- Improves search accuracy
- Enables multi-tenant usage

### 3. Content Quality

**Good content for embeddings**:
```python
# Descriptive and detailed
await client.create_node(
    type="character",
    content="Aladdin is a street-smart young man from Agrabah who wears a distinctive brown vest over a white shirt, purple pants, and a red fez. He is kind-hearted, brave, and resourceful.",
    project_id="aladdin_movie",
    properties={"name": "Aladdin"}
)
```

**Less effective content**:
```python
# Too short, lacks context
await client.create_node(
    type="character",
    content="Aladdin",  # Not enough information for good embeddings
    project_id="aladdin_movie",
    properties={"name": "Aladdin"}
)
```

### 4. Metadata Usage

**Use properties for structured data**:
```python
await client.create_node(
    type="character",
    content="Detailed character description...",
    project_id="aladdin_movie",
    properties={
        "name": "Aladdin",
        "outfit": "brown vest, purple pants",
        "personality": ["brave", "kind", "resourceful"],
        "relationships": {
            "love_interest": "Jasmine",
            "friend": "Genie"
        }
    }
)
```

**Note**: Properties can contain nested objects - they will be automatically serialized to JSON.

### 5. Error Handling

Always handle errors gracefully:

```python
import httpx

async def safe_search(query: str, project_id: str, api_key: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://brain.ft.tc/api/v1/search",
                headers={"Authorization": f"Bearer {api_key}"},
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
        return {"results": [], "total_count": 0, "error": "timeout"}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid API key")
        else:
            print(f"HTTP error: {e}")
        return {"results": [], "total_count": 0, "error": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"results": [], "total_count": 0, "error": str(e)}
```

### 6. Performance Optimization

**Adjust `top_k` based on your needs**:
```python
# Faster - fewer results
results = await client.search(query="...", project_id="...", top_k=5)

# Slower - more results
results = await client.search(query="...", project_id="...", top_k=50)
```

**Reuse client connections**:
```python
# ✅ Good - reuse client
client = BrainServiceClient(api_key="...")
for query in queries:
    results = await client.search(query, project_id)

# ❌ Less efficient - create new client each time
for query in queries:
    client = BrainServiceClient(api_key="...")
    results = await client.search(query, project_id)
```

### 7. Similarity Score Interpretation

**Understanding similarity scores**:
- **0.9 - 1.0**: Very high similarity (near-duplicate content)
- **0.7 - 0.9**: High similarity (related content)
- **0.5 - 0.7**: Moderate similarity (somewhat related)
- **< 0.5**: Low similarity (may not be relevant)

**Example**:
```python
results = await client.search("brown vest", "aladdin_movie")
for result in results['results']:
    if result['similarity'] > 0.7:
        print(f"Highly relevant: {result['id']}")
    elif result['similarity'] > 0.5:
        print(f"Moderately relevant: {result['id']}")
    else:
        print(f"Low relevance: {result['id']}")

---

## Troubleshooting

### Service Not Responding

```bash
# Check if service is running
sudo systemctl status mcp-brain-service

# Check logs
sudo journalctl -u mcp-brain-service -n 50

# Restart if needed
sudo systemctl restart mcp-brain-service

# Check if port 8002 is accessible
curl http://localhost:8002/health
```

### Authentication Errors (401 Unauthorized)

**Problem**: Getting 401 errors when calling API endpoints.

**Solution**:
```python
# Make sure you're including the Authorization header
headers = {
    "Authorization": "Bearer YOUR_API_KEY",  # Don't forget "Bearer " prefix
    "Content-Type": "application/json"
}

# Verify your API key is correct
# Check the .env file on the server for the correct API_KEY value
```

### Search Returns No Results

1. **Check if nodes are indexed**:
   ```python
   stats = await client.get_stats()
   print(f"Total nodes: {stats['totalNodes']}")
   print(f"Nodes by type: {stats['nodesByType']}")
   ```

2. **Verify project_id matches**:
   ```python
   # Make sure project_id is consistent
   await client.create_node(
       type="character",
       content="...",
       project_id="my_project",  # ✓ Same ID
       properties={}
   )

   results = await client.search(
       query="...",
       project_id="my_project"  # ✓ Same ID
   )
   ```

3. **Try broader query**:
   ```python
   # Too specific
   results = await client.search(
       query="exact very specific phrase that might not match",
       project_id="my_project"
   )

   # Better - use key concepts
   results = await client.search(
       query="key concepts from content",
       project_id="my_project"
   )
   ```

4. **Check similarity scores**:
   ```python
   # Even if results are returned, check if they're relevant
   for result in results['results']:
       print(f"ID: {result['id']}, Similarity: {result['similarity']:.4f}")
       if result['similarity'] < 0.5:
           print("  ⚠️ Low similarity - may not be relevant")
   ```

### Slow Performance

1. **Reduce top_k**:
   ```python
   # Faster - return fewer results
   results = await client.search(query="...", project_id="...", top_k=5)

   # Slower - return more results
   results = await client.search(query="...", project_id="...", top_k=100)
   ```

2. **Check query time**:
   ```python
   results = await client.search(query="...", project_id="...")
   print(f"Query took {results['query_time_ms']:.2f}ms")
   # Normal: 500-1500ms
   # Slow: > 2000ms
   ```

3. **Monitor Neo4j performance**:
   ```bash
   # Check Neo4j status
   sudo systemctl status neo4j

   # Check Neo4j logs
   sudo journalctl -u neo4j -n 50
   ```

### Connection Timeouts

**Problem**: Requests timing out.

**Solution**:
```python
# Increase timeout for slow queries
async with httpx.AsyncClient(timeout=60.0) as client:  # 60 second timeout
    response = await client.post(...)
```

### Neo4j Connection Issues

**Problem**: Service can't connect to Neo4j.

**Check**:
```bash
# Verify Neo4j is running
sudo systemctl status neo4j

# Test Neo4j connection
cypher-shell -a neo4j://127.0.0.1:7687 -u neo4j -p "PASSWORD" "RETURN 1;"

# Check Neo4j GDS is loaded
cypher-shell -a neo4j://127.0.0.1:7687 -u neo4j -p "PASSWORD" "RETURN gds.version();"
```

---

## Service Management

### Systemd Service Commands

The MCP Brain Service runs as a systemd service with auto-start and auto-restart capabilities.

```bash
# Start the service
sudo systemctl start mcp-brain-service

# Stop the service
sudo systemctl stop mcp-brain-service

# Restart the service
sudo systemctl restart mcp-brain-service

# Check service status
sudo systemctl status mcp-brain-service

# Enable auto-start on boot (already enabled)
sudo systemctl enable mcp-brain-service

# Disable auto-start on boot
sudo systemctl disable mcp-brain-service
```

### Viewing Logs

```bash
# View live logs (follow mode)
sudo journalctl -u mcp-brain-service -f

# View last 100 lines
sudo journalctl -u mcp-brain-service -n 100

# View logs from today
sudo journalctl -u mcp-brain-service --since today

# View logs with timestamps
sudo journalctl -u mcp-brain-service -n 50 --no-pager
```

### Service Configuration

**Service File**: `/etc/systemd/system/mcp-brain-service.service`

**Working Directory**: `/var/www/mcp-brain-service`

**Environment File**: `/var/www/mcp-brain-service/.env`

**Port**: 8002

**Auto-restart**: Yes (10 second delay on failure)

**Auto-start on boot**: Yes

### Updating the Service

```bash
# Pull latest code
cd /var/www/mcp-brain-service
git pull origin master

# Install/update dependencies (if needed)
./venv/bin/pip install -r requirements.txt

# Restart service to apply changes
sudo systemctl restart mcp-brain-service

# Verify service is running
sudo systemctl status mcp-brain-service
curl http://localhost:8002/health
```

---

## Support & Documentation

### Documentation Files
- **How to Use**: `/docs/how-to-use.md` (this file)
- **Deployment Summary**: `/DEPLOYMENT_SUMMARY.md`
- **Quick Reference**: `/QUICK_REFERENCE.md`
- **Deployment Checklist**: `/DEPLOYMENT_CHECKLIST.md`
- **API Contracts**: `/docs/api-contracts.md`

### Service Information
- **URL**: https://brain.ft.tc
- **Public Health Check**: https://brain.ft.tc/health
- **API Base**: https://brain.ft.tc/api/v1
- **Port**: 8002
- **Service**: mcp-brain-service (systemd)

### Technology Stack
- **Database**: Neo4j 5.26.12 with GDS 2.13.2
- **Embeddings**: Jina AI v4 (jina-embeddings-v4)
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Process Manager**: systemd

### Getting Help

1. **Check service status**: `sudo systemctl status mcp-brain-service`
2. **Check logs**: `sudo journalctl -u mcp-brain-service -n 100`
3. **Test health endpoint**: `curl https://brain.ft.tc/health`
4. **Verify Neo4j**: `sudo systemctl status neo4j`

---

## Summary

The MCP Brain Service provides:
- ✅ **Neo4j Graph Database** - Powerful graph-based knowledge storage
- ✅ **Jina Embeddings v4** - State-of-the-art semantic embeddings
- ✅ **Semantic Search** - Find similar content using vector similarity
- ✅ **Neo4j GDS** - Graph Data Science with cosine similarity
- ✅ **Project Isolation** - Keep your data separate by project
- ✅ **REST API** - Simple HTTP API with authentication
- ✅ **Auto-restart** - Systemd service with automatic recovery
- ✅ **Production Ready** - Deployed and tested on brain.ft.tc

**Start using it today to power your knowledge graph and semantic search needs!**

---

## Quick Reference

### Create a Node
```bash
curl -X POST https://brain.ft.tc/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"character","content":"Description","projectId":"project_id","properties":{}}'
```

### Batch Create Nodes (v1.1.0)
```bash
curl -X POST https://brain.ft.tc/api/v1/nodes/batch \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"nodes":[{"type":"GatherItem","content":"Content","projectId":"507f1f77bcf86cd799439011","properties":{}}]}'
```

### Search
```bash
curl -X POST https://brain.ft.tc/api/v1/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"search query","project_id":"project_id","top_k":5}'
```

### Search Duplicates (v1.1.0)
```bash
curl -X POST https://brain.ft.tc/api/v1/search/duplicates \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content":"Text to check","projectId":"507f1f77bcf86cd799439011","threshold":0.90}'
```

### Get Department Context (v1.1.0)
```bash
curl -X GET "https://brain.ft.tc/api/v1/context/department?projectId=507f1f77bcf86cd799439011&department=character&previousDepartments=story" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Analyze Coverage (v1.1.0)
```bash
curl -X POST https://brain.ft.tc/api/v1/analyze/coverage \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"projectId":"507f1f77bcf86cd799439011","department":"story","gatherItems":[{"content":"Plot","summary":"Main"}]}'
```

### Get Stats
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://brain.ft.tc/api/v1/stats
```

### Health Check
```bash
curl https://brain.ft.tc/health
```

---

## Additional Documentation

For more detailed information about the new batch endpoints:
- **Batch Endpoints Guide**: `/docs/BATCH_ENDPOINTS_GUIDE.md`
- **Implementation Summary**: `/docs/IMPLEMENTATION_SUMMARY.md`
- **Deployment Guide**: `/docs/DEPLOYMENT_GUIDE.md`
- **Changelog**: `/CHANGELOG.md`

