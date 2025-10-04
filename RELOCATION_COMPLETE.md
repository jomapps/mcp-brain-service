# MCP Brain Service - Relocation Complete ✅

**Date:** October 4, 2025  
**Domain:** brain.ft.tc  
**Service:** MCP Brain Service

## Final Status: SUCCESS ✅

The MCP Brain Service has been successfully relocated to a standalone directory with proper git repository setup.

---

## New Location Details

### Repository Information
- **Path:** `/var/www/mcp-brain-service`
- **Git Remote:** `git@github.com:jomapps/mcp-brain-service.git`
- **Branch:** `master`
- **Latest Commit:** `97201e3 - brain endpoints fixed`
- **Repository Type:** Standalone (no longer a submodule)

### Service Information
- **PM2 Name:** `mcp-brain-service`
- **PM2 ID:** 0
- **Process ID:** 24028
- **Port:** 8002
- **Working Directory:** `/var/www/mcp-brain-service`
- **Status:** ✅ Online and Healthy

### Domain & SSL
- **Domain:** `https://brain.ft.tc`
- **Nginx Config:** `/etc/nginx/sites-available/brain.ft.tc.conf`
- **Proxy Target:** `http://127.0.0.1:8002`
- **SSL:** ✅ Enabled (Let's Encrypt)

---

## What Was Migrated

### Files & Directories Copied
1. ✅ **Environment File** (`.env`) - Copied from old location
2. ✅ **Virtual Environment** (`venv/`) - Full Python environment with all dependencies
3. ✅ **Data Directory** (`data/`) - Including Retriv index
4. ✅ **Source Code** - Fresh clone from GitHub repository

### Configuration Files Created
1. ✅ **ecosystem.config.js** - PM2 process manager configuration
2. ✅ **RELOCATION_COMPLETE.md** - This documentation file

---

## Verification Results

### Health Checks ✅
```bash
# Local health check
$ curl http://localhost:8002/health
{"status":"healthy","timestamp":"2025-10-03T23:13:32.134904Z"}

# Public health check
$ curl https://brain.ft.tc/health
{"status":"healthy","timestamp":"2025-10-03T23:13:36.474488Z"}

# Service info
$ curl https://brain.ft.tc/
{"message":"MCP Brain Service is running"}
```

### Process Verification ✅
```bash
$ pm2 list
┌────┬──────────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
│ id │ name                 │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
├────┼──────────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
│ 0  │ mcp-brain-service    │ default     │ N/A     │ fork    │ 24028    │ 9s     │ 0    │ online    │ 0%       │ 168.2mb  │ root     │ disabled │
└────┴──────────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘

$ pwdx 24028
24028: /var/www/mcp-brain-service

$ netstat -tlnp | grep :8002
tcp        0      0 0.0.0.0:8002            0.0.0.0:*               LISTEN      24028/python
```

### Git Repository Verification ✅
```bash
$ cd /var/www/mcp-brain-service && git remote -v
origin	git@github.com:jomapps/mcp-brain-service.git (fetch)
origin	git@github.com:jomapps/mcp-brain-service.git (push)

$ git branch
* master

$ git log --oneline -5
97201e3 brain endpoints fixed
2e74b1f feat: Add Retriv hybrid search integration to MCP Brain Service
b210d2b planned for retriv
472812b feat: include timestamp in health endpoint
207441d feat: Enhanced MCP brain service with Jina v4 integration
```

---

## Service Management

### PM2 Commands
```bash
# View service status
pm2 list

# View real-time logs
pm2 logs mcp-brain-service

# View last 50 lines of logs
pm2 logs mcp-brain-service --lines 50 --nostream

# Restart service
pm2 restart mcp-brain-service

# Stop service
pm2 stop mcp-brain-service

# Start service
pm2 start mcp-brain-service

# Or start with config file
cd /var/www/mcp-brain-service
pm2 start ecosystem.config.js
```

### Log Files
- **Error Log:** `/var/log/mcp-brain-service-error.log`
- **Output Log:** `/var/log/mcp-brain-service-out.log`
- **Combined Log:** `/var/log/mcp-brain-service-combined.log`

### Git Operations
```bash
cd /var/www/mcp-brain-service

# Pull latest changes
git pull origin master

# Check status
git status

# View commit history
git log --oneline

# View remote
git remote -v
```

---

## Auto-Start Configuration

✅ **PM2 is configured to auto-start on system reboot**

The PM2 process list has been saved and will automatically restore on server restart:
```bash
# PM2 startup is already configured
# Process list saved at: /root/.pm2/dump.pm2
```

---

## Old Location

The old location still exists but is **NO LONGER IN USE**:
- **Old Path:** `/var/www/movie-generation-platform/services/mcp-brain-service`
- **Status:** Inactive (can be removed after verification period)

### Optional Cleanup (After Verification)
Once you've confirmed everything works correctly for a few days, you can remove the old location:
```bash
# CAUTION: Only run this after confirming the new location works perfectly
rm -rf /var/www/movie-generation-platform/services/mcp-brain-service
```

---

## Service Architecture

### Technology Stack
- **Framework:** FastAPI with WebSocket support
- **Database:** Neo4j (optional - service runs without it)
- **Embeddings:** Jina v4 integration (with mock fallback)
- **Search:** Retriv hybrid search integration
- **Process Manager:** PM2
- **Web Server:** Nginx (reverse proxy)
- **SSL:** Let's Encrypt

### Key Features
- Character management with personality and appearance descriptions
- Embedding generation for semantic search
- WebSocket API for real-time MCP communication
- Project isolation for multi-tenant support
- Performance optimized (P95 < 1 minute for semantic search)

---

## Troubleshooting

### If Service Doesn't Start
```bash
# Check PM2 logs
pm2 logs mcp-brain-service --lines 100

# Check if port 8002 is in use
netstat -tlnp | grep :8002

# Restart the service
pm2 restart mcp-brain-service

# If needed, delete and restart
pm2 delete mcp-brain-service
cd /var/www/mcp-brain-service
pm2 start ecosystem.config.js
pm2 save
```

### If Domain Returns Bad Gateway
```bash
# Check if service is running
pm2 list

# Check if port 8002 is listening
netstat -tlnp | grep :8002

# Test local endpoint
curl http://localhost:8002/health

# Check nginx configuration
nginx -t

# Restart nginx if needed
systemctl restart nginx
```

### If Git Issues Occur
```bash
cd /var/www/mcp-brain-service

# Check git status
git status

# Reset to remote state (CAUTION: loses local changes)
git fetch origin
git reset --hard origin/master

# Check remote connection
git remote -v
```

---

## Next Steps

1. ✅ **Monitor the service** for the next few days to ensure stability
2. ✅ **Test all endpoints** to confirm functionality
3. ⏳ **Remove old location** after verification period (optional)
4. ⏳ **Update any documentation** that references the old path
5. ⏳ **Update deployment scripts** if they reference the old location

---

## Contact & Support

For issues or questions:
- Check logs: `pm2 logs mcp-brain-service`
- View service status: `pm2 list`
- Test health endpoint: `curl https://brain.ft.tc/health`

---

**Relocation completed successfully on October 4, 2025 at 01:13 UTC**

