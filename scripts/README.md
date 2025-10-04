# Cleanup Scripts

This directory contains utility scripts for maintaining the MCP Brain Service knowledge graph.

## cleanup_invalid_nodes.py

A utility script to remove invalid or irrelevant nodes from the Neo4j knowledge graph.

### Purpose

This script helps clean up nodes that contain:
- Error messages (e.g., "Error: No user message found")
- Invalid data (e.g., "undefined", "null", "NaN")
- Empty or malformed content
- Other irrelevant information

### Prerequisites

1. **Environment Variables**: Ensure these are set:
   ```bash
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="your-password"
   ```

2. **Python Environment**: Activate your virtual environment:
   ```bash
   source venv/bin/activate
   ```

### Usage

#### 1. Preview What Would Be Deleted (Dry Run)

**Always run a dry run first** to see what would be deleted:

```bash
python scripts/cleanup_invalid_nodes.py --dry-run
```

#### 2. Clean Specific Project

```bash
python scripts/cleanup_invalid_nodes.py --project-id my-project-123
```

#### 3. Clean All Projects

```bash
python scripts/cleanup_invalid_nodes.py
```

#### 4. List All Projects

See which projects have nodes:

```bash
python scripts/cleanup_invalid_nodes.py --list-projects
```

#### 5. Custom Patterns

Search for and delete custom patterns:

```bash
python scripts/cleanup_invalid_nodes.py --patterns "Error:" "test data" "invalid"
```

#### 6. Verbose Output

Get detailed logging:

```bash
python scripts/cleanup_invalid_nodes.py --verbose --dry-run
```

### Default Invalid Patterns

The script searches for these patterns by default:

- `Error:`
- `error:`
- `no user message`
- `No user message`
- `undefined`
- `null`
- `NULL`
- `[object Object]`
- `NaN`

### Examples

#### Example 1: Safe Preview

```bash
# Preview what would be deleted across all projects
python scripts/cleanup_invalid_nodes.py --dry-run

# Output:
# ============================================================
# CLEANUP INVALID NODES
# ============================================================
# Mode: DRY RUN (preview only)
# Project filter: All projects
# Patterns: Error:, error:, no user message, undefined, null
# ============================================================
#
# Processing pattern: 'Error:'
#   Would delete 5 nodes
#   Sample IDs: ['abc-123', 'def-456', ...]
# ...
```

#### Example 2: Clean Specific Project

```bash
# First, list projects to find the one you want
python scripts/cleanup_invalid_nodes.py --list-projects

# Output:
# ============================================================
# PROJECT STATISTICS
# ============================================================
#   my-project-123: 150 nodes
#   test-project: 25 nodes
# ============================================================

# Then clean the specific project
python scripts/cleanup_invalid_nodes.py --project-id test-project --dry-run

# If satisfied with preview, run without --dry-run
python scripts/cleanup_invalid_nodes.py --project-id test-project
```

#### Example 3: Custom Cleanup

```bash
# Clean only nodes with specific error messages
python scripts/cleanup_invalid_nodes.py \
  --patterns "Error: No user message" "Connection failed" \
  --dry-run
```

### Safety Features

1. **Dry Run Mode**: Always preview before deleting
2. **5-Second Countdown**: When running live deletion, you have 5 seconds to cancel
3. **Project Isolation**: Can target specific projects
4. **Detailed Logging**: See exactly what's being deleted
5. **Error Handling**: Continues even if some operations fail

### Output

The script provides detailed output:

```
============================================================
CLEANUP SUMMARY
============================================================
Total nodes found: 15
Total deleted: 15

By pattern:
  'Error:': 5
  'no user message': 3
  'undefined': 7

Duration: 2.34 seconds
============================================================

✅ Cleanup completed successfully!
```

### Integration with API

This script complements the new API endpoints:

1. **Prevention**: The `/api/v1/nodes` POST endpoint now validates content
2. **Manual Deletion**: The `/api/v1/nodes/{node_id}` DELETE endpoint removes single nodes
3. **Bulk Cleanup**: This script handles bulk deletion of existing invalid data

### Troubleshooting

#### Connection Error

```
❌ Failed to connect to Neo4j: ...
```

**Solution**: Check your environment variables:
```bash
echo $NEO4J_URI
echo $NEO4J_USER
# Don't echo password for security
```

#### No Nodes Found

```
No nodes found matching 'Error:'
```

**Solution**: This is good! It means your database is clean. You can:
- Try different patterns with `--patterns`
- Check if nodes exist with `--list-projects`

#### Permission Denied

```
Permission denied: scripts/cleanup_invalid_nodes.py
```

**Solution**: Make the script executable:
```bash
chmod +x scripts/cleanup_invalid_nodes.py
```

### Best Practices

1. **Always Dry Run First**: Never skip the dry run step
2. **Backup Before Bulk Operations**: Consider backing up your Neo4j database
3. **Start with Specific Projects**: Test on a small project first
4. **Monitor Logs**: Use `--verbose` to understand what's happening
5. **Schedule Regular Cleanups**: Consider running this weekly/monthly

### Automation

You can schedule this script with cron:

```bash
# Add to crontab (crontab -e)
# Run cleanup every Sunday at 2 AM
0 2 * * 0 cd /var/www/mcp-brain-service && source venv/bin/activate && python scripts/cleanup_invalid_nodes.py >> /var/log/brain-cleanup.log 2>&1
```

### Related Documentation

- [API Routes Documentation](../docs/how-to-use.md)
- [Batch Endpoints Guide](../docs/BATCH_ENDPOINTS_GUIDE.md)
- [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md)

