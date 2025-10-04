# DELETE Endpoint 405 Error - Root Cause Analysis & Fix

**Date**: October 4, 2025  
**Issue**: DELETE /api/v1/nodes/{node_id} returning 405 Method Not Allowed  
**Status**: ✅ **RESOLVED**

---

## 🐛 Problem Summary

The Brain API at `https://brain.ft.tc` was returning `405 Method Not Allowed` when attempting to delete nodes via the DELETE endpoint, despite the endpoint being properly implemented in the code.

### Symptoms
- DELETE requests returned: `405 Method Not Allowed`
- Response header showed: `allow: GET` (only GET method allowed)
- GET requests to the same endpoint worked fine
- Code inspection showed DELETE route was properly defined

### Test Case
```bash
curl -X DELETE "https://brain.ft.tc/api/v1/nodes/68e0e835a74df94e04112dd0?project_id=68df4dab400c86a6a8cf40c6" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -v
```

**Expected**: 200 OK or 404 Not Found  
**Actual**: 405 Method Not Allowed

---

## 🔍 Root Cause Analysis

### Investigation Steps

1. **Code Verification** ✅
   - Confirmed DELETE endpoint exists in `src/api_routes.py` (line 200)
   - Route properly decorated with `@router.delete("/nodes/{node_id}")`
   - Response model and authentication properly configured

2. **Route Registration** ✅
   - Verified routes are registered in FastAPI app
   - Both DELETE and GET routes present for `/api/v1/nodes/{node_id}`
   - Route matching test confirmed DELETE method matches correctly

3. **Service Status** ❌ **ISSUE FOUND**
   - Discovered TWO Python processes running:
     - PID 37546: Old uvicorn process from 06:33 (running OLD code)
     - PID 52893: PM2 managed process from 12:27 (failing to start)
   
4. **Port Conflict** ❌ **ISSUE FOUND**
   - Old process was bound to port 8002
   - New process couldn't start due to "Address already in use"
   - PM2 auto-reload was broken

5. **Environment Variables** ❌ **ISSUE FOUND**
   - PM2 configuration didn't load `.env` file
   - Service failed to start due to missing NEO4J_URI, JINA_API_KEY
   - Old process continued serving requests with outdated code

### Root Cause

**The production service was running an OLD version of the code that didn't include the DELETE endpoint implementation.**

The issue was caused by:
1. PM2 configuration not loading environment variables from `.env` file
2. Service failing to start properly, leaving old process running
3. Auto-reload mechanism broken due to port conflict
4. Old uvicorn process (started manually) still serving requests

---

## ✅ Solution

### Fix Applied

1. **Updated PM2 Configuration** (`ecosystem.config.js`)
   - Changed from direct Python execution to using `start.sh` script
   - `start.sh` properly loads `.env` file before starting service
   
   **Before**:
   ```javascript
   script: 'venv/bin/python',
   args: '-m src.main',
   interpreter: 'none',
   ```
   
   **After**:
   ```javascript
   script: 'start.sh',
   interpreter: 'bash',
   ```

2. **Killed Old Process**
   - Terminated stale uvicorn process (PID 37546)
   - Cleared port 8002 for proper service startup

3. **Restarted Service**
   ```bash
   pm2 delete mcp-brain-service
   pm2 start ecosystem.config.js
   pm2 save
   ```

### Verification

✅ **Local Test**:
```bash
curl -X DELETE "http://127.0.0.1:8002/api/v1/nodes/test-node?project_id=test-project" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
Response: `404 Not Found` (correct - node doesn't exist)

✅ **Production Test**:
```bash
curl -X DELETE "https://brain.ft.tc/api/v1/nodes/test-node?project_id=test-project" \
  -H "Authorization: Bearer YOUR_API_KEY"
```
Response: `404 Not Found` (correct - node doesn't exist)

✅ **Health Check**:
```bash
curl https://brain.ft.tc/health
```
Response: `200 OK` - All components healthy

---

## 📝 Answers to Original Questions

### 1. Is the DELETE endpoint implemented?
**YES** ✅ - The endpoint is fully implemented in `src/api_routes.py` (lines 200-274)

### 2. Is there an alternative bulk delete endpoint?
**NO** ❌ - Currently only single node deletion is supported. For bulk operations, you need to:
- Loop through nodes and delete individually
- OR implement a new bulk delete endpoint (feature request)

### 3. Should we use a different endpoint?
**NO** ❌ - The current endpoint is correct: `DELETE /api/v1/nodes/{node_id}?project_id={project_id}`

### 4. Authentication issue?
**NO** ❌ - The 405 error was not related to authentication. It was caused by the service running old code without the DELETE endpoint.

---

## 🚀 Current Status

### Service Information
- **Status**: ✅ Online and Healthy
- **Port**: 8002
- **Domain**: https://brain.ft.tc
- **PM2 Process**: mcp-brain-service (ID: 7)
- **Environment**: Production with proper .env loading

### DELETE Endpoint
- **Status**: ✅ **WORKING**
- **Endpoint**: `DELETE /api/v1/nodes/{node_id}`
- **Query Params**: `project_id` (required)
- **Authentication**: Bearer token required
- **Response Codes**:
  - `200 OK`: Node deleted successfully
  - `404 Not Found`: Node doesn't exist
  - `401 Unauthorized`: Invalid/missing API key
  - `500 Internal Server Error`: Server error

### Example Usage
```bash
# Delete a node
curl -X DELETE "https://brain.ft.tc/api/v1/nodes/NODE_ID?project_id=PROJECT_ID" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Success response (200 OK)
{
  "status": "success",
  "message": "Node deleted successfully",
  "deleted_count": 1,
  "node_id": "NODE_ID"
}

# Not found response (404)
{
  "detail": {
    "error": "node_not_found",
    "message": "Node with ID 'NODE_ID' not found in project 'PROJECT_ID'",
    "details": {
      "node_id": "NODE_ID",
      "project_id": "PROJECT_ID"
    }
  }
}
```

---

## 🔧 Prevention Measures

### Recommendations

1. **Always use PM2 for process management**
   - Don't start services manually with uvicorn
   - Use `pm2 start ecosystem.config.js`
   - Use `pm2 restart mcp-brain-service` for updates

2. **Verify service status after deployment**
   ```bash
   pm2 list
   pm2 logs mcp-brain-service --lines 50
   curl http://localhost:8002/health
   ```

3. **Check for duplicate processes**
   ```bash
   ps aux | grep "python.*src.main"
   netstat -tlnp | grep 8002
   ```

4. **Monitor PM2 logs for startup errors**
   ```bash
   pm2 logs mcp-brain-service --err --lines 100
   ```

5. **Test endpoints after deployment**
   - Run test suite: `./test_deletion_features.sh`
   - Verify all HTTP methods work
   - Check OpenAPI docs: https://brain.ft.tc/docs

---

## 📚 Related Documentation

- **API Documentation**: `docs/mcp-brain-service/how-to-use.md`
- **Deletion Features**: `docs/DELETION_AND_VALIDATION.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Test Script**: `test_deletion_features.sh`

---

## ✅ Resolution Checklist

- [x] Identified root cause (old process running)
- [x] Fixed PM2 configuration to load .env
- [x] Killed stale processes
- [x] Restarted service with proper configuration
- [x] Verified DELETE endpoint works locally
- [x] Verified DELETE endpoint works in production
- [x] Saved PM2 configuration
- [x] Documented issue and resolution
- [x] Tested with actual node IDs from issue report

---

**Issue Status**: ✅ **RESOLVED**  
**Service Status**: ✅ **HEALTHY**  
**DELETE Endpoint**: ✅ **WORKING**

