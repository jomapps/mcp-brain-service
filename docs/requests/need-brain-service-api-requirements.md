# Brain Service API Requirements for Automated Gather Creation

**Service**: Brain Service API (brain.ft.tc)
**Version**: 1.0.0
**Date**: January 2025
**Status**: Requirements Specification

---

## 📋 Overview

The Brain service API needs **4 new endpoints** to support automated gather creation. This document specifies **only** the API contract - the implementation details are separate.

---

## 🆕 Required API Endpoints

### 1. Batch Node Creation

**Endpoint**: `POST /api/v1/nodes/batch`

**Purpose**: Create multiple nodes in a single request to reduce API calls

**Authentication**: `Authorization: Bearer {BRAIN_API_KEY}`

**Request Headers**:
```
Content-Type: application/json
Authorization: Bearer brain-api-key-xxxxx
```

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
        "qualityScore": 75.5,
        "model": "anthropic/claude-sonnet-4.5",
        "taskId": "celery-task-123",
        "summary": "Brief summary text",
        "context": "Why this matters"
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

**Response (200 OK)**:
```json
{
  "success": true,
  "created": 2,
  "nodeIds": [
    "neo4j-internal-id-abc123",
    "neo4j-internal-id-def456"
  ],
  "nodes": [
    {
      "id": "neo4j-internal-id-abc123",
      "type": "GatherItem",
      "properties": {
        "department": "story",
        "departmentName": "Story Department",
        "isAutomated": true,
        "iteration": 5,
        "qualityScore": 75.5
      },
      "embedding": {
        "dimensions": 1536,
        "model": "jina-embeddings-v2"
      }
    },
    {
      "id": "neo4j-internal-id-def456",
      "type": "GatherItem",
      "properties": {
        "department": "character",
        "isAutomated": true
      },
      "embedding": {
        "dimensions": 1536
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

**Error Response (400 Bad Request)**:
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

**Error Response (401 Unauthorized)**:
```json
{
  "error": "unauthorized",
  "message": "Invalid or missing API key"
}
```

**Constraints**:
- Maximum batch size: 50 nodes
- Minimum batch size: 1 node
- All nodes must have: `type`, `content`, `projectId`
- ProjectId must be valid MongoDB ObjectId format

**Performance SLA**:
- 10 nodes: <1000ms (95th percentile)
- 50 nodes: <4000ms (95th percentile)

---

### 2. Duplicate Search

**Endpoint**: `POST /api/v1/search/duplicates`

**Purpose**: Find semantically similar nodes to detect duplicates

**Authentication**: `Authorization: Bearer {BRAIN_API_KEY}`

**Request Body**:
```json
{
  "content": "Text content to check for duplicates",
  "projectId": "507f1f77bcf86cd799439011",
  "threshold": 0.90,
  "limit": 10,
  "type": "GatherItem",
  "department": "story",
  "excludeNodeIds": ["neo4j-id-to-exclude"]
}
```

**Request Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | Yes | Text to find duplicates for |
| projectId | string | Yes | Project ID for isolation |
| threshold | number | No | Similarity threshold 0.0-1.0 (default: 0.90) |
| limit | number | No | Max results to return (default: 10, max: 50) |
| type | string | No | Filter by node type (default: "GatherItem") |
| department | string | No | Filter by department slug |
| excludeNodeIds | array | No | Node IDs to exclude from search |

**Response (200 OK)**:
```json
{
  "duplicates": [
    {
      "nodeId": "neo4j-internal-id-456",
      "similarity": 0.95,
      "content": "Very similar content text here",
      "properties": {
        "department": "story",
        "summary": "Brief summary",
        "createdAt": "2025-01-15T10:30:00Z",
        "isAutomated": false
      }
    },
    {
      "nodeId": "neo4j-internal-id-789",
      "similarity": 0.92,
      "content": "Another similar text",
      "properties": {
        "department": "story",
        "summary": "Different summary",
        "createdAt": "2025-01-14T15:20:00Z",
        "isAutomated": true
      }
    }
  ],
  "query_embedding_time_ms": 200,
  "search_time_ms": 150,
  "total_time_ms": 350
}
```

**Response (200 OK - No Duplicates)**:
```json
{
  "duplicates": [],
  "query_embedding_time_ms": 180,
  "search_time_ms": 120,
  "total_time_ms": 300
}
```

**Behavior**:
- Results sorted by similarity (highest first)
- Only returns nodes with similarity >= threshold
- Filters by projectId (isolation enforced)
- Excludes nodes in `excludeNodeIds` list

**Performance SLA**:
- <500ms (95th percentile)
- Search against 10,000 nodes

---

### 3. Department Context Retrieval

**Endpoint**: `GET /api/v1/context/department`

**Purpose**: Aggregate context from previous departments

**Authentication**: `Authorization: Bearer {BRAIN_API_KEY}`

**Query Parameters**:
```
?projectId=507f1f77bcf86cd799439011
&department=character
&previousDepartments[]=story
&previousDepartments[]=visual
&limit=20
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| projectId | string | Yes | Project ID |
| department | string | Yes | Target department slug |
| previousDepartments | array | No | Previous department slugs |
| limit | number | No | Nodes per department (default: 20) |

**Response (200 OK)**:
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
          "content": "Story premise: A hero's journey through redemption...",
          "summary": "Main story arc",
          "relevance": 0.95
        },
        {
          "nodeId": "neo4j-id-2",
          "content": "Plot structure: Three act structure with rising tension...",
          "summary": "Narrative structure",
          "relevance": 0.88
        }
      ],
      "keyThemes": ["redemption", "family", "sacrifice"]
    },
    "visual": {
      "nodeCount": 12,
      "qualityScore": 78,
      "topNodes": [
        {
          "nodeId": "neo4j-id-10",
          "content": "Visual style: Dark noir aesthetic with high contrast...",
          "summary": "Visual aesthetic",
          "relevance": 0.90
        }
      ],
      "keyThemes": ["dark aesthetic", "noir lighting", "urban decay"]
    }
  },
  "aggregatedSummary": "The story follows a redemption arc with dark visual themes, featuring complex family dynamics against an urban noir backdrop.",
  "relevantNodes": [
    {
      "nodeId": "neo4j-id-1",
      "department": "story",
      "content": "Story premise...",
      "relevanceToTarget": 0.92
    }
  ],
  "totalNodesAggregated": 27,
  "timing": {
    "query_time_ms": 180,
    "aggregation_time_ms": 220,
    "total_time_ms": 400
  }
}
```

**Behavior**:
- Query nodes from specified `previousDepartments` only
- Calculate relevance to `targetDepartment` using embeddings
- Extract key themes per department (LLM-based)
- Return top N most relevant nodes per department
- Generate aggregated summary (optional)

**Performance SLA**:
- <800ms (95th percentile)
- Up to 5 previous departments

---

### 4. Coverage Analysis

**Endpoint**: `POST /api/v1/analyze/coverage`

**Purpose**: Analyze content coverage and identify gaps

**Authentication**: `Authorization: Bearer {BRAIN_API_KEY}`

**Request Body**:
```json
{
  "projectId": "507f1f77bcf86cd799439011",
  "department": "story",
  "gatherItems": [
    {
      "content": "Plot overview: The story follows...",
      "summary": "Plot structure"
    },
    {
      "content": "Character relationships: The protagonist has...",
      "summary": "Character dynamics"
    }
  ],
  "departmentDescription": "Story Department handles narrative, plot structure, pacing, character arcs, and thematic development"
}
```

**Request Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| projectId | string | Yes | Project ID |
| department | string | Yes | Department slug |
| gatherItems | array | Yes | Current gather items |
| departmentDescription | string | No | Department purpose/scope |

**Response (200 OK)**:
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
      },
      {
        "aspect": "Character Arcs",
        "coverage": 70,
        "itemCount": 3,
        "quality": "good",
        "items": ["item-id-3"]
      }
    ],
    "gaps": [
      {
        "aspect": "Pacing",
        "coverage": 20,
        "itemCount": 1,
        "severity": "high",
        "suggestion": "Add detailed pacing breakdown for each act with specific timing notes"
      },
      {
        "aspect": "Dialogue Samples",
        "coverage": 0,
        "itemCount": 0,
        "severity": "medium",
        "suggestion": "Include representative dialogue examples to demonstrate character voices"
      },
      {
        "aspect": "Thematic Development",
        "coverage": 30,
        "itemCount": 1,
        "severity": "medium",
        "suggestion": "Expand on how themes are woven through the narrative"
      }
    ],
    "recommendations": [
      "Focus next iteration on pacing details - this is the biggest gap",
      "Add dialogue samples to demonstrate character voices",
      "Expand thematic development section"
    ]
  },
  "itemDistribution": {
    "plot": 8,
    "character": 5,
    "theme": 3,
    "pacing": 1,
    "dialogue": 0
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

**Behavior**:
- Analyze content against department description
- Cluster items by topic/aspect
- Calculate coverage per aspect (0-100)
- Identify missing or weak areas
- Generate actionable recommendations
- Return quality metrics

**Performance SLA**:
- <1500ms (95th percentile)
- Up to 100 gather items

---

## 🔐 Authentication & Authorization

### API Key Authentication

**Header**: `Authorization: Bearer {BRAIN_API_KEY}`

**Validation**:
- API key must be valid and active
- Return 401 if missing or invalid
- Log authentication failures

**Rate Limiting**:
- Per API key, per endpoint
- Limits defined per endpoint (see below)

---

## 📊 Rate Limiting

### Per-Endpoint Limits (per project, per minute)

| Endpoint | Limit | Burst |
|----------|-------|-------|
| POST /api/v1/nodes/batch | 10 req/min | 20 |
| POST /api/v1/search/duplicates | 30 req/min | 50 |
| GET /api/v1/context/department | 20 req/min | 30 |
| POST /api/v1/analyze/coverage | 5 req/min | 10 |

**Rate Limit Headers** (included in all responses):
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1705320000
```

**Rate Limit Exceeded (429)**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 42,
  "limit": 30,
  "window": "1 minute"
}
```

---

## 🔒 ProjectId Isolation

### CRITICAL Security Requirement

**EVERY endpoint MUST**:
- Accept `projectId` in request
- Filter ALL database queries by `projectId`
- Prevent cross-project data access
- Validate `projectId` format (MongoDB ObjectId)

**Enforcement**:
```cypher
// Example Neo4j query (must include projectId filter)
MATCH (n:GatherItem {projectId: $projectId})
WHERE ...
```

**Validation**:
- `projectId` must be 24-character hex string
- Return 400 if invalid format
- Return 404 if project not found

---

## 📈 Performance SLAs

### Response Time Targets (95th percentile)

| Endpoint | Target | Max Acceptable |
|----------|--------|----------------|
| POST /api/v1/nodes/batch (10 nodes) | <1000ms | <2000ms |
| POST /api/v1/nodes/batch (50 nodes) | <4000ms | <8000ms |
| POST /api/v1/search/duplicates | <500ms | <1000ms |
| GET /api/v1/context/department | <800ms | <1500ms |
| POST /api/v1/analyze/coverage | <1500ms | <3000ms |

### Throughput Requirements

- **Batch Creation**: 500 nodes/minute
- **Duplicate Search**: 1000 searches/minute
- **Context Retrieval**: 100 requests/minute
- **Coverage Analysis**: 50 analyses/minute

---

## 🧪 API Testing Requirements

### Contract Testing

**Required Tests**:
- [ ] Request validation (required fields)
- [ ] Response format compliance
- [ ] Error response format
- [ ] Authentication enforcement
- [ ] Rate limiting behavior
- [ ] ProjectId isolation
- [ ] Performance SLAs

### Integration Testing

**Test Scenarios**:
- [ ] Batch create → duplicate search (should find created nodes)
- [ ] Context retrieval with multiple departments
- [ ] Coverage analysis with empty vs full gather items
- [ ] Concurrent requests handling
- [ ] Rate limit recovery

---

## 📝 API Documentation

### OpenAPI Specification

**Required**:
- OpenAPI 3.0 spec file (`/api/v1/openapi.json`)
- Interactive docs at `/api/v1/docs`
- Schema validation enabled

### Client Libraries

**Recommended** (not required):
- Python client library
- TypeScript/JavaScript client library

### Example Code

**Provide examples for each endpoint**:
```python
# Python example
import requests

response = requests.post(
    'https://brain.ft.tc/api/v1/nodes/batch',
    headers={'Authorization': 'Bearer brain-api-key'},
    json={'nodes': [...]}
)
```

---

## 🚨 Error Handling

### Standard Error Format

**All errors must use this format**:
```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {
    "field": "additional context"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `unauthorized` | 401 | Invalid/missing API key |
| `forbidden` | 403 | Access denied |
| `not_found` | 404 | Resource not found |
| `validation_failed` | 400 | Request validation failed |
| `batch_validation_failed` | 400 | Batch nodes invalid |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Server error |
| `service_unavailable` | 503 | Service temporarily unavailable |

---

## 📊 Monitoring & Alerting

### Required Metrics (Prometheus)

```
# Request metrics
http_requests_total{endpoint="/api/v1/nodes/batch",status="200"}
http_request_duration_seconds{endpoint="/api/v1/nodes/batch",quantile="0.95"}

# Rate limit metrics
rate_limit_exceeded_total{endpoint="/api/v1/search/duplicates"}

# Performance metrics
embedding_generation_duration_seconds{model="jina-v2"}
neo4j_query_duration_seconds{query_type="batch_insert"}
```

### Alert Conditions

**Critical**:
- Error rate > 5% (5xx errors)
- P95 latency > 2x SLA
- Service unavailable

**Warning**:
- Error rate > 2%
- P95 latency > 1.5x SLA
- Rate limit hit rate > 20%

---

## ✅ Acceptance Criteria

### Functional Requirements
- [ ] All 4 endpoints implemented and accessible
- [ ] Request/response formats match specification
- [ ] Authentication required and enforced
- [ ] Rate limiting active per endpoint
- [ ] ProjectId isolation verified (no cross-project access)
- [ ] Error responses follow standard format

### Performance Requirements
- [ ] Batch creation (10 nodes): <1000ms (P95)
- [ ] Duplicate search: <500ms (P95)
- [ ] Context retrieval: <800ms (P95)
- [ ] Coverage analysis: <1500ms (P95)
- [ ] Throughput targets met

### Security Requirements
- [ ] API key validation on all endpoints
- [ ] Rate limiting per project per endpoint
- [ ] ProjectId validation and isolation
- [ ] No sensitive data in error messages

### Documentation Requirements
- [ ] OpenAPI spec available
- [ ] Interactive docs at `/api/v1/docs`
- [ ] Example code for each endpoint
- [ ] Error code documentation

---

## 🔄 Versioning & Compatibility

### API Version

**Current**: `v1`

**URL Format**: `https://brain.ft.tc/api/v1/...`

### Breaking Changes

**None expected** - These are new endpoints

### Deprecation Policy

- 6 months notice for deprecation
- Maintain backward compatibility for 1 year

---

**Status**: Ready for Implementation
**Estimated Effort**: 1 week (backend development)
**Risk Level**: Low (additive API changes only)
**Priority**: High (blocks automated gather creation)
