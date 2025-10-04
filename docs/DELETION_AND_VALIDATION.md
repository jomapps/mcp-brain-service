# Deletion and Validation Features

This document describes the deletion and validation features implemented in the MCP Brain Service to prevent and remove invalid/irrelevant data.

## Overview

Three complementary features work together to maintain data quality:

1. **Content Validation** - Prevents invalid data from being stored
2. **DELETE Endpoint** - Removes specific nodes via API
3. **Cleanup Script** - Bulk deletion of existing invalid data

## Problem Statement

The service was storing irrelevant or erroneous data such as:
- Error messages: "Error: No user message found"
- Invalid values: "undefined", "null", "NaN"
- Empty or malformed content
- System messages that shouldn't be persisted

This polluted the knowledge graph and degraded search quality.

## Solution

### 1. Content Validation (Prevention)

**Location**: `src/api_routes.py` - `POST /api/v1/nodes` endpoint

**What it does**: Validates content before storing in the database

**Validation Rules**:
- ✅ Content cannot be empty or whitespace-only
- ✅ Content must be at least 10 characters long
- ✅ Content cannot contain error patterns:
  - "error:" (case-insensitive)
  - "no user message"
  - "undefined"
  - "null"
  - "[object Object]"

**Example Request** (Invalid):
```bash
curl -X POST http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gather",
    "content": "Error: No user message found",
    "projectId": "my-project",
    "properties": {}
  }'
```

**Response** (400 Bad Request):
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

**Example Request** (Valid):
```bash
curl -X POST http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gather",
    "content": "User wants to book a flight to Paris for next week",
    "projectId": "my-project",
    "properties": {"source": "chat"}
  }'
```

**Response** (200 OK):
```json
{
  "node": {
    "id": "abc-123-def-456",
    "type": "gather",
    "content": "User wants to book a flight to Paris for next week",
    "projectId": "my-project",
    "properties": {"source": "chat"}
  }
}
```

### 2. DELETE Endpoint (Manual Removal)

**Location**: `src/api_routes.py` - `DELETE /api/v1/nodes/{node_id}`

**What it does**: Deletes a specific node and all its relationships

**Features**:
- ✅ Requires both node ID and project ID (security)
- ✅ Uses `DETACH DELETE` to remove relationships
- ✅ Returns 404 if node not found
- ✅ Requires API key authentication

**Example Request**:
```bash
curl -X DELETE "http://localhost:8000/api/v1/nodes/abc-123-def-456?project_id=my-project" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Node deleted successfully",
  "deleted_count": 1,
  "node_id": "abc-123-def-456"
}
```

**Response** (404 Not Found):
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

### 3. Cleanup Script (Bulk Deletion)

**Location**: `scripts/cleanup_invalid_nodes.py`

**What it does**: Bulk deletion of nodes matching invalid patterns

**Features**:
- ✅ Dry run mode (preview before deleting)
- ✅ Project filtering
- ✅ Custom pattern matching
- ✅ Detailed statistics and logging
- ✅ 5-second safety countdown

**Usage Examples**:

#### Preview what would be deleted (always start here):
```bash
python scripts/cleanup_invalid_nodes.py --dry-run
```

#### List all projects:
```bash
python scripts/cleanup_invalid_nodes.py --list-projects
```

#### Clean specific project:
```bash
python scripts/cleanup_invalid_nodes.py --project-id my-project-123
```

#### Custom patterns:
```bash
python scripts/cleanup_invalid_nodes.py --patterns "Error:" "test data" "invalid"
```

#### Verbose output:
```bash
python scripts/cleanup_invalid_nodes.py --verbose --dry-run
```

**Default Invalid Patterns**:
- `Error:`
- `error:`
- `no user message`
- `No user message`
- `undefined`
- `null`
- `NULL`
- `[object Object]`
- `NaN`

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

## Workflow Recommendations

### For New Data (Prevention)

The validation happens automatically on the `POST /api/v1/nodes` endpoint. No action needed - invalid data is rejected automatically.

### For Existing Invalid Data (Cleanup)

**Step 1**: Identify the scope
```bash
# See which projects have data
python scripts/cleanup_invalid_nodes.py --list-projects
```

**Step 2**: Preview deletions
```bash
# Dry run for all projects
python scripts/cleanup_invalid_nodes.py --dry-run

# Or for specific project
python scripts/cleanup_invalid_nodes.py --project-id my-project --dry-run
```

**Step 3**: Execute cleanup
```bash
# Clean specific project
python scripts/cleanup_invalid_nodes.py --project-id my-project

# Or clean all projects
python scripts/cleanup_invalid_nodes.py
```

### For Single Node Deletion

Use the DELETE API endpoint:
```bash
curl -X DELETE "http://localhost:8000/api/v1/nodes/{node_id}?project_id={project_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Testing

A comprehensive test suite is provided in `test_deletion_features.sh`:

```bash
# Run all tests
./test_deletion_features.sh

# Tests include:
# ✅ Empty content validation
# ✅ Error message validation
# ✅ Short content validation
# ✅ Valid content acceptance
# ✅ Node deletion
# ✅ Non-existent node handling
# ✅ Cleanup script dry run
# ✅ Full workflow integration
```

## API Changes Summary

### Modified Endpoints

#### `POST /api/v1/nodes`
- **Added**: Content validation before storage
- **Breaking Change**: No - only rejects invalid data that shouldn't have been stored
- **Error Codes**: 400 for validation failures

### New Endpoints

#### `DELETE /api/v1/nodes/{node_id}`
- **Method**: DELETE
- **Parameters**: 
  - `node_id` (path): Node ID to delete
  - `project_id` (query): Project ID for isolation
- **Authentication**: Required (API key)
- **Response Codes**:
  - 200: Success
  - 404: Node not found
  - 401: Invalid API key
  - 500: Server error

## Security Considerations

1. **Project Isolation**: DELETE endpoint requires project_id to prevent cross-project deletion
2. **Authentication**: All endpoints require valid API key
3. **Audit Trail**: All deletions are logged
4. **Safety Features**: Cleanup script has dry-run mode and countdown

## Performance Impact

- **Validation**: Minimal (<1ms per request)
- **DELETE Endpoint**: Fast (<50ms for single node)
- **Cleanup Script**: Depends on data volume (typically <5s for 1000 nodes)

## Monitoring

### Logs to Watch

```bash
# Validation rejections
grep "validation_failed" /var/log/brain-service.log

# Deletions
grep "delete node" /var/log/brain-service.log

# Cleanup operations
grep "CLEANUP" /var/log/brain-cleanup.log
```

### Metrics to Track

- Number of validation failures (should decrease over time)
- Number of deletions (should decrease as data quality improves)
- Invalid data patterns (to identify new patterns to block)

## Future Enhancements

Potential improvements:

1. **Batch DELETE endpoint** - Delete multiple nodes in one request
2. **Soft delete** - Mark as deleted instead of permanent removal
3. **Deletion history** - Track what was deleted and when
4. **Auto-cleanup** - Scheduled automatic cleanup
5. **Custom validation rules** - Per-project validation rules
6. **Webhook notifications** - Alert on validation failures

## Related Documentation

- [API Routes Documentation](./how-to-use.md)
- [Batch Endpoints Guide](./BATCH_ENDPOINTS_GUIDE.md)
- [Cleanup Script README](../scripts/README.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)

## Support

For issues or questions:
1. Check logs for error details
2. Run tests: `./test_deletion_features.sh`
3. Try dry-run mode first
4. Review this documentation

