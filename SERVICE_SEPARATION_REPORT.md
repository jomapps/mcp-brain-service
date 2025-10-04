# Service Separation Report

## Overview
This document clarifies the separation between two distinct services running on this server.

---

## Service 1: MCP Brain Service

### Repository Information
- **Location**: `/var/www/mcp-brain-service`
- **Git Remote**: `git@github.com:jomapps/mcp-brain-service.git`
- **Branch**: `master`
- **Status**: ✅ Properly synced with remote

### Service Configuration
- **Port**: 8002
- **Domain**: brain.ft.tc
- **Purpose**: Character embedding and semantic search service for Auto-Movie
- **Technology**: FastAPI + Neo4j + WebSocket support

### PM2 Configuration
- **Config File**: `/var/www/mcp-brain-service/ecosystem.config.js`
- **Process Name**: `mcp-brain-service`
- **Status**: ✅ Running (PID: 24028)
- **Script**: `venv/bin/python -m src.main`
- **Logs**:
  - Error: `/var/log/mcp-brain-service-error.log`
  - Output: `/var/log/mcp-brain-service-out.log`
  - Combined: `/var/log/mcp-brain-service-combined.log`

### Nginx Configuration
- **Config File**: `/etc/nginx/sites-available/brain.ft.tc.conf`
- **Enabled**: ✅ Yes (symlinked in sites-enabled)
- **Proxy**: `http://127.0.0.1:8002`
- **SSL**: ✅ Configured with Let's Encrypt

---

## Service 2: Celery-Redis (AI Movie Task Service)

### Repository Information
- **Location**: `/var/www/celery-redis`
- **Git Remote**: `git@github.com:jomapps/celery-redis.git`
- **Branch**: `master`
- **Status**: ⚠️ **NO COMMITS YET** - All files untracked

### Service Configuration
- **Port**: 8001
- **Domain**: tasks.ft.tc
- **Purpose**: AI Movie Task Service with Celery workers and Redis queue
- **Technology**: FastAPI + Celery + Redis

### PM2 Configuration
- **Config File**: ❌ **MISSING** - No ecosystem.config.js found
- **Process Name**: N/A
- **Status**: ❌ **NOT RUNNING** under PM2
- **Expected Script**: `venv/bin/python -m app.main`

### Nginx Configuration
- **Config File**: `/etc/nginx/sites-available/tasks.ft.tc.conf`
- **Enabled**: ✅ Yes (symlinked in sites-enabled)
- **Proxy**: `http://127.0.0.1:8001`
- **SSL**: ✅ Configured with Let's Encrypt
- **Status**: ⚠️ Configured but backend service not running

---

## Issues Identified

### Critical Issues

1. **celery-redis repository has no commits**
   - All files are untracked
   - Need to perform initial commit and push

2. **celery-redis has no PM2 configuration**
   - Service is not managed by PM2
   - No automatic restart or process monitoring
   - Need to create ecosystem.config.js

3. **celery-redis service not running**
   - Port 8001 is not listening
   - Nginx proxy will fail (502 Bad Gateway)

### Minor Issues

1. **mcp-brain-service has untracked files**
   - `ecosystem.config.js` (should be committed)
   - `RELOCATION_COMPLETE.md` (documentation)
   - `venv/` (correctly ignored)

---

## Recommended Actions

### For celery-redis (Priority: HIGH)

1. **Initialize Git Repository**
   ```bash
   cd /var/www/celery-redis
   git add .
   git commit -m "Initial commit: AI Movie Task Service"
   git push -u origin master
   ```

2. **Create PM2 Configuration**
   - Create `ecosystem.config.js` for the FastAPI app
   - Create separate PM2 config for Celery workers
   - Start services with PM2

3. **Verify Service**
   - Ensure port 8001 is listening
   - Test nginx proxy
   - Check SSL certificate

### For mcp-brain-service (Priority: LOW)

1. **Commit PM2 Configuration**
   ```bash
   cd /var/www/mcp-brain-service
   git add ecosystem.config.js
   git commit -m "Add PM2 ecosystem configuration"
   git push
   ```

2. **Review Documentation**
   - Decide if RELOCATION_COMPLETE.md should be committed
   - Update .gitignore if needed

---

## Port Allocation Summary

| Service | Port | Domain | Status |
|---------|------|--------|--------|
| mcp-brain-service | 8002 | brain.ft.tc | ✅ Running |
| celery-redis (API) | 8001 | tasks.ft.tc | ❌ Not Running |

---

## Next Steps

1. Create PM2 configuration for celery-redis
2. Initialize git repository for celery-redis
3. Start celery-redis services
4. Verify both services are running independently
5. Test nginx proxies for both domains
6. Commit mcp-brain-service PM2 config

---

**Generated**: 2025-10-03
**Status**: Action Required

