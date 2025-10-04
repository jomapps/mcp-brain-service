# Quick Start: Deletion & Validation Features

**Version**: 1.2.0  
**Status**: Ready to Use ✅

## What's New?

Three powerful features to maintain data quality:

1. **Automatic Validation** - Rejects invalid data automatically
2. **DELETE API** - Remove specific nodes via REST API
3. **Cleanup Script** - Bulk delete invalid data

## Quick Examples

### 1. Validation (Automatic)

Invalid data is automatically rejected:

```bash
# ❌ This will be rejected
curl -X POST http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gather",
    "content": "Error: No user message found",
    "projectId": "my-project"
  }'

# Response: 400 Bad Request
{
  "error": "validation_failed",
  "message": "Invalid content: Cannot store error messages or invalid data"
}
```

```bash
# ✅ This will be accepted
curl -X POST http://localhost:8000/api/v1/nodes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "gather",
    "content": "User wants to book a flight to Paris next week",
    "projectId": "my-project"
  }'

# Response: 200 OK
{
  "node": {
    "id": "abc-123-def-456",
    "type": "gather",
    "content": "User wants to book a flight to Paris next week"
  }
}
```

### 2. Delete Single Node

```bash
# Delete a specific node
curl -X DELETE "http://localhost:8000/api/v1/nodes/abc-123?project_id=my-project" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Response: 200 OK
{
  "status": "success",
  "message": "Node deleted successfully",
  "deleted_count": 1,
  "node_id": "abc-123"
}
```

### 3. Bulk Cleanup

```bash
# Step 1: Preview (ALWAYS DO THIS FIRST!)
python scripts/cleanup_invalid_nodes.py --dry-run

# Output shows what would be deleted:
# Processing pattern: 'Error:'
#   Would delete 5 nodes
#   Sample IDs: ['abc-123', 'def-456', ...]

# Step 2: List projects to see data distribution
python scripts/cleanup_invalid_nodes.py --list-projects

# Output:
# PROJECT STATISTICS
#   my-project-123: 150 nodes
#   test-project: 25 nodes

# Step 3: Clean specific project
python scripts/cleanup_invalid_nodes.py --project-id my-project-123

# Step 4: Or clean all projects
python scripts/cleanup_invalid_nodes.py
```

## What Gets Blocked/Deleted?

### Invalid Patterns (Automatically Rejected)

- ❌ `Error:` or `error:`
- ❌ `no user message` or `No user message`
- ❌ `undefined`
- ❌ `null` or `NULL`
- ❌ `[object Object]`
- ❌ `NaN`
- ❌ Empty content
- ❌ Content shorter than 10 characters

### Valid Content (Accepted)

- ✅ Meaningful text with 10+ characters
- ✅ User messages and requests
- ✅ Descriptions and summaries
- ✅ Any legitimate content

## Common Use Cases

### Use Case 1: Prevent Bad Data (Automatic)

**Scenario**: Your app sends error messages to the API

**Solution**: Validation automatically rejects them

**Action**: None needed - it just works!

### Use Case 2: Remove One Bad Node

**Scenario**: You found a specific node with bad data

**Solution**: Use DELETE endpoint

```bash
curl -X DELETE "http://localhost:8000/api/v1/nodes/{node_id}?project_id={project_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Use Case 3: Clean Up Existing Bad Data

**Scenario**: You have many nodes with error messages

**Solution**: Use cleanup script

```bash
# Preview first
python scripts/cleanup_invalid_nodes.py --dry-run

# Then execute
python scripts/cleanup_invalid_nodes.py
```

### Use Case 4: Clean Specific Project Only

**Scenario**: Only one project has bad data

**Solution**: Use project filter

```bash
python scripts/cleanup_invalid_nodes.py --project-id my-project --dry-run
python scripts/cleanup_invalid_nodes.py --project-id my-project
```

### Use Case 5: Custom Cleanup

**Scenario**: You want to remove specific patterns

**Solution**: Use custom patterns

```bash
python scripts/cleanup_invalid_nodes.py \
  --patterns "test data" "debug" "temporary" \
  --dry-run
```

## Safety Features

### 1. Validation
- ✅ Rejects at API level (before storage)
- ✅ Returns clear error messages
- ✅ No data corruption

### 2. DELETE Endpoint
- ✅ Requires authentication
- ✅ Requires project ID (prevents accidents)
- ✅ Returns 404 if not found
- ✅ All operations logged

### 3. Cleanup Script
- ✅ Dry-run mode (preview first)
- ✅ 5-second countdown before deletion
- ✅ Detailed statistics
- ✅ Project filtering
- ✅ Error handling (continues on failure)

## Testing

Run the comprehensive test suite:

```bash
./test_deletion_features.sh
```

**Tests include**:
- ✅ Empty content validation
- ✅ Error message validation
- ✅ Short content validation
- ✅ Valid content acceptance
- ✅ Node deletion
- ✅ 404 handling
- ✅ Cleanup script dry-run
- ✅ List projects
- ✅ Full workflow integration

## Troubleshooting

### Problem: Validation rejecting valid content

**Check**: Is your content at least 10 characters?

```bash
# Too short (rejected)
"short"

# Long enough (accepted)
"This is valid content"
```

### Problem: Can't delete node

**Check**: Are you providing the correct project_id?

```bash
# Wrong - missing project_id
curl -X DELETE "http://localhost:8000/api/v1/nodes/abc-123"

# Correct - includes project_id
curl -X DELETE "http://localhost:8000/api/v1/nodes/abc-123?project_id=my-project"
```

### Problem: Cleanup script not finding nodes

**Check**: Are you using the right patterns?

```bash
# List what's in the database first
python scripts/cleanup_invalid_nodes.py --list-projects

# Try verbose mode to see what's happening
python scripts/cleanup_invalid_nodes.py --verbose --dry-run
```

### Problem: Connection error

**Check**: Are environment variables set?

```bash
echo $NEO4J_URI
echo $NEO4J_USER
# Should output your Neo4j connection details
```

## Documentation

- **Full Guide**: [docs/DELETION_AND_VALIDATION.md](docs/DELETION_AND_VALIDATION.md)
- **Script Docs**: [scripts/README.md](scripts/README.md)
- **API Docs**: [docs/how-to-use.md](docs/how-to-use.md)
- **Implementation**: [DELETION_FEATURES_IMPLEMENTATION.md](DELETION_FEATURES_IMPLEMENTATION.md)

## Need Help?

1. **Check logs**:
   ```bash
   grep "validation_failed" /var/log/brain-service.log
   grep "delete node" /var/log/brain-service.log
   ```

2. **Run tests**:
   ```bash
   ./test_deletion_features.sh
   ```

3. **Try dry-run**:
   ```bash
   python scripts/cleanup_invalid_nodes.py --dry-run --verbose
   ```

4. **Review documentation**:
   - Start with this file (QUICK_START_DELETION.md)
   - Then read [docs/DELETION_AND_VALIDATION.md](docs/DELETION_AND_VALIDATION.md)

## Summary

✅ **Validation**: Automatic - no action needed  
✅ **DELETE API**: For single nodes  
✅ **Cleanup Script**: For bulk operations  
✅ **Safe**: Dry-run, validation, logging  
✅ **Tested**: Comprehensive test suite  
✅ **Documented**: Multiple guides available  

**You're all set!** The features are ready to use.

