# Brain Service API Contracts

## Overview

The brain service provides simple storage and enhanced query APIs. It expects the calling application (Next.js) to prepare and enrich data before sending.

**Base URL**: `https://brain.ft.tc`

## Core Principles

1. **Brain service is infrastructure** - no business logic
2. **App prepares data** - brain service just stores/retrieves
3. **Generic and reusable** - works for any project/app
4. **Simple contracts** - clear input/output formats

## Document Format

All documents stored in the brain service follow this structure:

```typescript
interface BrainDocument {
  id: string                    // Unique identifier (e.g., "char_aladdin_proj123")
  type: string                  // Document type (e.g., "character", "scene", "image")
  project_id: string            // Project isolation
  text: string                  // Searchable text content (prepared by app)
  metadata: Record<string, any> // Structured metadata (prepared by app)
  relationships?: Relationship[] // Graph relationships (prepared by app)
}

interface Relationship {
  type: string      // Relationship type (e.g., "loves", "appears_in")
  target_id: string // Target document ID
  strength?: number // Optional relationship strength (0-1)
}
```

## Storage API

### Store Single Document

**Endpoint**: `POST /store`

**Request Body**:
```json
{
  "id": "char_aladdin_proj123",
  "type": "character",
  "project_id": "proj123",
  "text": "Aladdin: A street-smart young man from Agrabah. Personality: resourceful, kind-hearted, brave. Appearance: brown vest, white pants, red sash, messy black hair. Appears in scenes: 1, 2, 3, 4, 5, 6, 7.",
  "metadata": {
    "character_name": "Aladdin",
    "scenes_present": [1, 2, 3, 4, 5, 6, 7],
    "personality_traits": ["resourceful", "kind", "brave"],
    "visual_descriptors": ["brown_vest", "white_pants", "red_sash", "messy_hair"]
  },
  "relationships": [
    {
      "type": "loves",
      "target_id": "char_jasmine_proj123",
      "strength": 1.0
    },
    {
      "type": "allies",
      "target_id": "char_genie_proj123",
      "strength": 0.9
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "id": "char_aladdin_proj123",
  "stored_in": ["neo4j", "jina", "retriv"]
}
```

**What Brain Service Does**:
1. Stores document in Neo4j (with relationships)
2. Generates embedding via Jina and stores
3. Indexes in Retriv for hybrid search

### Store Multiple Documents (Batch)

**Endpoint**: `POST /store/batch`

**Request Body**:
```json
{
  "documents": [
    {
      "id": "char_aladdin_proj123",
      "type": "character",
      "project_id": "proj123",
      "text": "...",
      "metadata": {...},
      "relationships": [...]
    },
    {
      "id": "scene_3_proj123",
      "type": "scene",
      "project_id": "proj123",
      "text": "...",
      "metadata": {...},
      "relationships": [...]
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "stored_count": 2,
  "failed_count": 0,
  "results": [
    {"id": "char_aladdin_proj123", "status": "success"},
    {"id": "scene_3_proj123", "status": "success"}
  ]
}
```

## Query API

### Hybrid Search (Retriv)

**Endpoint**: `POST /query`

**Request Body**:
```json
{
  "project_id": "proj123",
  "query": "What does Aladdin wear in scene 3?",
  "search_type": "hybrid",
  "top_k": 5,
  "filters": {
    "type": "character",
    "metadata.scenes_present": [3]
  }
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "char_aladdin_proj123",
      "type": "character",
      "score": 0.92,
      "text": "Aladdin: A street-smart young man...",
      "metadata": {
        "character_name": "Aladdin",
        "visual_descriptors": ["brown_vest", "white_pants", "red_sash"]
      },
      "relationships": [...]
    }
  ],
  "search_type": "hybrid",
  "query_time_ms": 45
}
```

**Search Types**:
- `"hybrid"`: Retriv hybrid search (BM25 + embeddings) - **RECOMMENDED**
- `"semantic"`: Pure Jina semantic search
- `"graph"`: Neo4j graph traversal

### Character Context Query

**Endpoint**: `POST /query/character-context`

**Request Body**:
```json
{
  "project_id": "proj123",
  "character_name": "Aladdin",
  "scene_number": 3,
  "include_relationships": true,
  "include_visual_history": true
}
```

**Response**:
```json
{
  "character": {
    "id": "char_aladdin_proj123",
    "name": "Aladdin",
    "appearance": {
      "scene_3": {
        "clothing": ["brown_vest", "white_pants", "red_sash"],
        "state": "disheveled from running"
      }
    },
    "personality": ["resourceful", "kind", "brave"]
  },
  "relationships": [
    {
      "type": "loves",
      "target": "Jasmine",
      "strength": 1.0
    }
  ],
  "visual_history": [
    {
      "scene": 2,
      "image_id": "img_456",
      "description": "Aladdin running from guards"
    }
  ],
  "context_summary": "Aladdin should appear disheveled with torn vest from previous chase scene."
}
```

### Story Bible Search

**Endpoint**: `POST /query/story-bible`

**Request Body**:
```json
{
  "project_id": "proj123",
  "query": "continuity notes for Aladdin's costume",
  "filters": {
    "type": "continuity_note",
    "tags": ["costume", "aladdin"]
  },
  "top_k": 5
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "continuity_scene3_proj123",
      "type": "continuity_note",
      "score": 0.95,
      "text": "Scene 3: Aladdin's vest is torn on left shoulder from Scene 2 chase",
      "metadata": {
        "scene_number": 3,
        "items": ["brown_vest", "tear_left_shoulder"]
      }
    }
  ]
}
```

## MCP Tools (WebSocket)

The brain service also exposes MCP tools via WebSocket for agent integration.

### Available Tools

1. **store_document** - Store a single document
2. **store_batch** - Store multiple documents
3. **search** - Hybrid search
4. **find_similar** - Find similar documents
5. **get_relationships** - Get document relationships

### Example MCP Call

```json
{
  "tool": "search",
  "project_id": "proj123",
  "query": "Aladdin appearance",
  "search_type": "hybrid",
  "top_k": 5
}
```

## Error Responses

### Standard Error Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_DOCUMENT",
    "message": "Document text is required",
    "details": {
      "field": "text",
      "received": null
    }
  }
}
```

### Error Codes

- `INVALID_DOCUMENT`: Document validation failed
- `STORAGE_FAILED`: Failed to store in one or more backends
- `QUERY_FAILED`: Query execution failed
- `PROJECT_NOT_FOUND`: Project ID not found
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Data Preparation Guidelines

### What the App Should Send

**Good Document** (Prepared by App):
```json
{
  "id": "char_aladdin_proj123",
  "type": "character",
  "project_id": "proj123",
  "text": "Aladdin: A street-smart young man from Agrabah. Personality: resourceful, kind-hearted, brave, clever. Appearance: brown vest, white pants, red sash, messy black hair. Appears in scenes: 1, 2, 3, 4, 5, 6, 7. Relationships: loves Jasmine, allies with Genie and Abu, enemies with Jafar.",
  "metadata": {
    "character_name": "Aladdin",
    "scenes_present": [1, 2, 3, 4, 5, 6, 7],
    "personality_traits": ["resourceful", "kind", "brave", "clever"],
    "visual_descriptors": ["brown_vest", "white_pants", "red_sash", "messy_hair"]
  }
}
```

**Bad Document** (Raw PayloadCMS):
```json
{
  "id": "123",
  "name": "Aladdin",
  "description": "A young man",
  "createdAt": "2024-01-01"
}
```

### Text Field Guidelines

The `text` field should be:
1. **Comprehensive**: Include all searchable information
2. **Natural Language**: Written for semantic search
3. **Keyword Rich**: Include important terms for BM25
4. **Context Aware**: Include scene numbers, relationships, etc.

**Example**:
```
Aladdin: A street-smart young man from Agrabah.
Personality: resourceful, kind-hearted, brave, clever.
Appearance: brown vest, white pants, red sash, messy black hair.
Appears in scenes: 1, 2, 3, 4, 5, 6, 7.
Relationships: loves Jasmine, allies with Genie and Abu, enemies with Jafar.
```

### Metadata Guidelines

Metadata should be:
1. **Structured**: Use consistent field names
2. **Filterable**: Include fields you'll filter by
3. **Typed**: Use appropriate types (arrays, numbers, strings)
4. **Minimal**: Only include what's needed for filtering/display

## Authentication

**Current**: No authentication (internal service)
**Future**: API key or JWT token

```http
Authorization: Bearer <token>
```

## Rate Limits

- **Storage**: 100 requests/minute
- **Query**: 1000 requests/minute
- **Batch**: 10 requests/minute (max 100 documents per batch)

## Monitoring

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": "connected",
    "jina": "connected",
    "retriv": "initialized"
  },
  "version": "1.0.0"
}
```

## Next Steps

1. Implement storage endpoints in brain service
2. Implement query endpoints with Retriv
3. Create data preparation layer in Next.js
4. Test end-to-end integration
5. Deploy to production

