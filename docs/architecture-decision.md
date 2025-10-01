# Architecture Decision: Data Preparation in App vs Brain Service

## Decision Summary

**Data preparation belongs in the application (Next.js), not in the brain service.**

The brain service should remain pure infrastructure - a generic storage and retrieval system with no business logic or app-specific knowledge.

## The Question

When integrating PayloadCMS with the brain service, where should data preparation and enrichment happen?

### Option A: Brain Service Prepares Data ❌
```
Next.js → Raw PayloadCMS data → Brain Service
                                      ↓
                              Brain Service enriches
                              Brain Service transforms
                              Brain Service stores
```

### Option B: App Prepares Data ✅ (CHOSEN)
```
Next.js → Prepares & enriches data → Brain Service
                                          ↓
                                  Brain Service stores
                                  Brain Service queries
```

## Why Option B (App Prepares Data)

### 1. Domain Knowledge Lives in the App

**The App Knows:**
- PayloadCMS schema and relationships
- Business logic (what makes a "complete" character)
- Which fields are important for story bible
- How scenes relate to each other
- Project-specific rules and validation

**Brain Service Should Only Know:**
- How to store embeddings
- How to search semantically
- How to manage graph relationships
- Generic storage/retrieval patterns

### 2. Brain Service as Pure Infrastructure

Think of brain service like a database:

```
❌ Bad: PostgreSQL understanding your e-commerce checkout flow
✅ Good: PostgreSQL storing data, app handles business logic

❌ Bad: Brain service understanding PayloadCMS character structure
✅ Good: Brain service storing/searching, app handles preparation
```

### 3. Flexibility & Reusability

**If Brain Service Does Prep:**
- Tightly coupled to PayloadCMS structure
- Hard to reuse for other projects
- Changes to PayloadCMS require brain service updates
- Brain service becomes app-specific

**If App Does Prep:**
- Brain service is generic and reusable
- Different apps can use same brain service
- PayloadCMS changes only affect Next.js app
- Brain service is infrastructure, not application logic

### 4. Separation of Concerns

**Clear Boundaries:**
```
Next.js App:
- Business logic
- Data validation
- Enrichment (pulling related data)
- Transformation (formatting for brain)
- PayloadCMS integration

Brain Service:
- Storage (Neo4j, Jina, Retriv)
- Retrieval (hybrid search, graph queries)
- Embedding generation
- Infrastructure concerns
```

### 5. Easier Testing & Debugging

**App-side prep:**
```typescript
// In Next.js - easy to test
const preparedData = prepareCharacterForBrain(character)
// You can see exactly what's being sent
await brainService.store(preparedData)
```

**Brain-side prep:**
```python
# In brain service - harder to debug from app
# App sends raw data, brain does magic
# If something's wrong, need to check brain service logs
```

### 6. Performance & Scaling

**App-side prep:**
- Preparation happens in Next.js (scales with your app)
- Brain service only does storage/retrieval (simpler, faster)
- Can cache prepared data in Next.js
- Parallel preparation for batch operations

**Brain-side prep:**
- Brain service does more work per request
- Harder to scale (more CPU/memory needed)
- Brain service becomes bottleneck

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js App (PayloadCMS)                  │
│                                                              │
│  User updates Character → PayloadCMS saves                   │
│                              ↓                               │
│  PayloadCMS Hook (afterChange)                               │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Preparation Layer (in Next.js)               │    │
│  │  - Enrichment: Pull related PayloadCMS data        │    │
│  │  - Transformation: Convert to brain format         │    │
│  │  - Validation: Ensure data quality                 │    │
│  └────────────────────────────────────────────────────┘    │
│                              ↓                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Brain Service Client (in Next.js)                 │    │
│  │  - brainService.store(preparedData)                │    │
│  │  - brainService.query(searchParams)                │    │
│  └────────────────────────────────────────────────────┘    │
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
│  │ POST /store        │      │ POST /query        │        │
│  │ POST /store/batch  │      │ POST /search       │        │
│  └────────────────────┘      └────────────────────┘        │
│           ↓                           ↑                      │
│  ┌──────────────────────────────────────────────┐          │
│  │         Storage & Retrieval Services          │          │
│  │  - RetrivService (hybrid search)             │          │
│  │  - Neo4jService (graph storage)              │          │
│  │  - JinaService (embeddings)                  │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## What Each Layer Does

### Next.js App Responsibilities

**1. Data Enrichment**
```typescript
// Pull related data from PayloadCMS
const enrichedCharacter = {
  ...character,
  scenes: await getCharacterScenes(character.id),
  relationships: await getCharacterRelationships(character.id),
  project: await getProject(character.projectId)
}
```

**2. Data Transformation**
```typescript
// Convert to brain-ready format
const brainDocument = {
  id: `char_${character.id}_${projectId}`,
  type: 'character',
  project_id: projectId,
  text: buildSearchableText(enrichedCharacter),
  metadata: extractMetadata(enrichedCharacter),
  relationships: buildRelationships(enrichedCharacter)
}
```

**3. Validation**
```typescript
// Ensure data quality before sending
if (!brainDocument.text || brainDocument.text.length < 10) {
  throw new Error('Invalid document: text too short')
}
```

**4. Storage**
```typescript
// Send to brain service
await brainService.store(brainDocument)
```

### Brain Service Responsibilities

**1. Storage**
```python
# Store in Neo4j
await neo4j_client.create_node(document)

# Generate and store embedding
embedding = await jina_service.embed_single(document["text"])

# Index in Retriv
await retriv_service.index_documents([document])
```

**2. Retrieval**
```python
# Hybrid search with Retriv
results = await retriv_service.search(
    query=query,
    project_id=project_id
)

# Enrich with Neo4j relationships
enriched = await neo4j_client.get_relationships(results)

return enriched
```

**3. Infrastructure Concerns**
- Connection pooling
- Error handling
- Retry logic
- Performance optimization
- Monitoring and logging

## Benefits of This Approach

### For Development
1. **Clear Boundaries**: Easy to understand what goes where
2. **Easy Testing**: Test preparation logic separately from storage
3. **Fast Iteration**: Change PayloadCMS structure without touching brain service
4. **Better Debugging**: See exactly what data is being sent

### For Deployment
1. **Independent Scaling**: Scale app and brain service separately
2. **Simpler Brain Service**: Less code, fewer dependencies
3. **Reusable Infrastructure**: Brain service can serve multiple apps
4. **Easier Maintenance**: Changes to business logic don't affect infrastructure

### For Performance
1. **Parallel Preparation**: Prepare multiple documents in Next.js
2. **Caching**: Cache prepared data in Next.js
3. **Lighter Brain Service**: Only does storage/retrieval
4. **Better Resource Usage**: CPU-intensive prep in app, I/O in brain service

## Implementation Guide

See the following documents for implementation details:

1. **Next.js Data Preparation**: `docs/architecture-data-prep-in-app.md`
2. **Brain Service Enhancement**: `docs/retriv-integration-plan.md`
3. **API Contracts**: `docs/api-contracts.md` (to be created)

## Decision Rationale

This decision follows industry best practices:

1. **Database Pattern**: Databases don't understand business logic
2. **Microservices Pattern**: Services should have single responsibility
3. **Clean Architecture**: Separate business logic from infrastructure
4. **Domain-Driven Design**: Domain knowledge lives in the domain layer (app)

## Conclusion

**Brain service = Infrastructure (like a database)**
**Next.js app = Business logic (like application code)**

This separation makes the system:
- Easier to understand
- Easier to test
- Easier to maintain
- Easier to scale
- More reusable

The brain service becomes a generic, reusable infrastructure component that can serve multiple applications, while each application handles its own business logic and data preparation.

