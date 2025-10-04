# Brain Service Batch Endpoints - Developer Guide

Complete guide for using the 4 new batch endpoints for automated gather creation.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Error Handling](#error-handling)
5. [Best Practices](#best-practices)
6. [Examples](#examples)

---

## Quick Start

### Base URL
```
Production: https://brain.ft.tc/api/v1
Development: http://localhost:8002/api/v1
```

### Authentication
All endpoints require Bearer token authentication:
```bash
Authorization: Bearer {BRAIN_API_KEY}
```

### Test the API
```bash
# Run the test script
./test_new_endpoints.sh

# Or check health
curl http://localhost:8002/health
```

---

## Authentication

### API Key Setup
1. Get your API key from environment variable `BRAIN_SERVICE_API_KEY`
2. Include in all requests:
```bash
curl -H "Authorization: Bearer your-api-key-here" ...
```

### Error Responses
- **401 Unauthorized**: Invalid or missing API key
- **403 Forbidden**: Access denied

---

## Endpoints

### 1. Batch Node Creation

**POST** `/api/v1/nodes/batch`

Create multiple nodes in a single request for efficient bulk operations.

#### Request Body
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
        "qualityScore": 75.5,
        "model": "anthropic/claude-sonnet-4.5",
        "taskId": "celery-task-123",
        "summary": "Brief summary text",
        "context": "Why this matters"
      }
    }
  ]
}
```

#### Constraints
- **Min nodes**: 1
- **Max nodes**: 50
- **Required fields**: `type`, `content`, `projectId`
- **projectId format**: 24-character hex string (MongoDB ObjectId)

#### Response
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
    "embedding_time_ms": 450,
    "neo4j_write_time_ms": 120,
    "total_time_ms": 570
  }
}
```

#### Example
```bash
curl -X POST "http://localhost:8002/api/v1/nodes/batch" \
  -H "Authorization: Bearer $API_KEY" \
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

---

### 2. Duplicate Search

**POST** `/api/v1/search/duplicates`

Find semantically similar nodes to detect potential duplicates.

#### Request Body
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

#### Parameters
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| content | string | Yes | - | Text to find duplicates for |
| projectId | string | Yes | - | Project ID (24 hex chars) |
| threshold | number | No | 0.90 | Similarity threshold (0.0-1.0) |
| limit | number | No | 10 | Max results (1-50) |
| type | string | No | "GatherItem" | Filter by node type |
| department | string | No | - | Filter by department |
| excludeNodeIds | array | No | [] | Node IDs to exclude |

#### Response
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

#### Example
```bash
curl -X POST "http://localhost:8002/api/v1/search/duplicates" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Story about a hero journey",
    "projectId": "507f1f77bcf86cd799439011",
    "threshold": 0.85,
    "limit": 5,
    "department": "story"
  }'
```

---

### 3. Department Context Retrieval

**GET** `/api/v1/context/department`

Aggregate context from previous departments with LLM-based theme extraction.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| projectId | string | Yes | - | Project ID (24 hex chars) |
| department | string | Yes | - | Target department slug |
| previousDepartments | array | No | [] | Previous department slugs |
| limit | number | No | 20 | Nodes per department (1-100) |

#### Response
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

#### Example
```bash
curl -X GET "http://localhost:8002/api/v1/context/department?projectId=507f1f77bcf86cd799439011&department=character&previousDepartments=story&previousDepartments=visual&limit=20" \
  -H "Authorization: Bearer $API_KEY"
```

---

### 4. Coverage Analysis

**POST** `/api/v1/analyze/coverage`

Analyze content coverage and identify gaps using LLM analysis.

#### Request Body
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

#### Constraints
- **Max items**: 100 gather items
- **Required fields**: `projectId`, `department`, `gatherItems`

#### Response
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
        "quality": "excellent",
        "items": ["item-id-1", "item-id-2"]
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
    "theme": 3,
    "pacing": 1
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

#### Example
```bash
curl -X POST "http://localhost:8002/api/v1/analyze/coverage" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "507f1f77bcf86cd799439011",
    "department": "story",
    "gatherItems": [
      {
        "content": "Plot overview: Hero journey through challenges",
        "summary": "Main plot"
      },
      {
        "content": "Character arc: Protagonist transformation",
        "summary": "Character development"
      }
    ]
  }'
```

---

## Error Handling

### Standard Error Format
All errors follow this structure:
```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {
    "field": "additional context"
  }
}
```

### Common Error Codes
| Code | Status | Description |
|------|--------|-------------|
| `unauthorized` | 401 | Invalid/missing API key |
| `validation_failed` | 400 | Request validation failed |
| `batch_validation_failed` | 400 | Batch nodes invalid |
| `internal_error` | 500 | Server error |

### Example Error Response
```json
{
  "error": "batch_validation_failed",
  "message": "Invalid nodes in batch",
  "details": {
    "invalid_nodes": [
      {
        "index": 0,
        "reason": "Missing required field: content"
      }
    ]
  }
}
```

---

## Best Practices

### 1. Batch Operations
- **Optimal batch size**: 10-20 nodes for best performance
- **Max batch size**: 50 nodes (hard limit)
- Always validate projectId format before sending

### 2. Duplicate Detection
- Use threshold 0.90+ for strict duplicate detection
- Use threshold 0.75-0.89 for similar content detection
- Always exclude the source node when checking for duplicates

### 3. Department Context
- Request only necessary previous departments
- Use limit parameter to control response size
- Cache results when possible (context doesn't change frequently)

### 4. Coverage Analysis
- Provide department description for better analysis
- Include summaries in gather items for faster processing
- Limit to 20-30 items for optimal LLM analysis quality

### 5. Performance
- Batch operations are faster than individual requests
- LLM operations (context, coverage) take longer (expected)
- Monitor timing metrics in responses

---

## Examples

### Python Client Example
```python
import requests

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8002/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Batch create nodes
response = requests.post(
    f"{BASE_URL}/nodes/batch",
    headers=headers,
    json={
        "nodes": [
            {
                "type": "GatherItem",
                "content": "Story content here",
                "projectId": "507f1f77bcf86cd799439011",
                "properties": {"department": "story"}
            }
        ]
    }
)

print(response.json())
```

### JavaScript/TypeScript Example
```typescript
const API_KEY = "your-api-key";
const BASE_URL = "http://localhost:8002/api/v1";

async function batchCreateNodes(nodes) {
  const response = await fetch(`${BASE_URL}/nodes/batch`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ nodes })
  });
  
  return await response.json();
}

// Usage
const result = await batchCreateNodes([
  {
    type: "GatherItem",
    content: "Story content here",
    projectId: "507f1f77bcf86cd799439011",
    properties: { department: "story" }
  }
]);
```

---

## Support

- **API Documentation**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health
- **Test Script**: `./test_new_endpoints.sh`

---

**Last Updated**: January 2025  
**Version**: 1.0.0

