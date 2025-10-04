# MCP Brain Service - Configuration Status

**Repository**: mcp-brain-service  
**Date**: 2025-10-03  
**Status**: ✅ Operational

---

## Repository Information

### Git Configuration
- **Location**: `/var/www/mcp-brain-service`
- **Remote**: `git@github.com:jomapps/mcp-brain-service.git`
- **Branch**: `master`
- **Status**: Up to date with origin/master

### Pending Changes
- ✅ `.gitignore` - Updated to include `venv/`
- 📄 `ecosystem.config.js` - PM2 configuration (needs to be committed)
- 📄 `RELOCATION_COMPLETE.md` - Documentation (needs review)
- 📄 `SERVICE_SEPARATION_REPORT.md` - Documentation (needs review)

---

## Service Configuration

### Application Details
- **Name**: MCP Brain Service
- **Description**: Character embedding and semantic search service for Auto-Movie
- **Technology Stack**: FastAPI + Neo4j + WebSocket
- **Port**: 8002
- **Domain**: brain.ft.tc

### Health Check
```bash
curl http://localhost:8002/health
# Response: {"status":"healthy","timestamp":"2025-10-03T23:34:15.321105Z"}
```

✅ **Status**: Service is healthy and responding

---

## PM2 Configuration

### Configuration File
**Location**: `/var/www/mcp-brain-service/ecosystem.config.js`

```javascript
module.exports = {
  apps: [{
    name: 'mcp-brain-service',
    cwd: '/var/www/mcp-brain-service',
    script: 'venv/bin/python',
    args: '-m src.main',
    interpreter: 'none',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/var/log/mcp-brain-service-error.log',
    out_file: '/var/log/mcp-brain-service-out.log',
    log_file: '/var/log/mcp-brain-service-combined.log',
    time: true
  }]
};
```

### PM2 Process Status
- **Process Name**: mcp-brain-service
- **PID**: 24028
- **Status**: ✅ Online
- **Uptime**: 20+ minutes
- **Memory**: 168.2 MB
- **Restarts**: 0

### Log Files
- **Error Log**: `/var/log/mcp-brain-service-error.log`
- **Output Log**: `/var/log/mcp-brain-service-out.log`
- **Combined Log**: `/var/log/mcp-brain-service-combined.log`

### PM2 Commands
```bash
# View process status
pm2 list

# View logs
pm2 logs mcp-brain-service

# Restart service
pm2 restart mcp-brain-service

# Monitor resources
pm2 monit

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

---

## Nginx Configuration

### Configuration File
**Location**: `/etc/nginx/sites-available/brain.ft.tc.conf`

### Key Settings
- **Server Name**: brain.ft.tc
- **Proxy Pass**: http://127.0.0.1:8002
- **SSL**: ✅ Enabled (Let's Encrypt)
- **Certificate**: `/etc/letsencrypt/live/brain.ft.tc/fullchain.pem`
- **HTTP → HTTPS**: ✅ Redirect enabled

### Nginx Status
- **Configuration Test**: ✅ Passed (`nginx -t`)
- **Sites Enabled**: ✅ Symlinked
- **SSL Certificate**: ✅ Valid

### Nginx Commands
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo nginx -s reload

# Restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

---

## Network Configuration

### Port Status
```
Port 8002: ✅ LISTENING (PID: 24028/python)
```

### Firewall
Ensure port 8002 is accessible locally (nginx proxy handles external access)

---

## Environment Variables

### Required Variables
Check `.env` file for:
- Database connection strings (Neo4j)
- API keys
- CORS origins
- Other service-specific configurations

### CORS Configuration
Currently configured origins (from `src/main.py`):
- `http://localhost:3010`
- `https://auto-movie.ngrok.pro`
- `https://auto-movie.ft.tc`

---

## Deployment Checklist

### ✅ Completed
- [x] Git repository initialized and synced
- [x] PM2 configuration created
- [x] Service running under PM2
- [x] Port 8002 listening
- [x] Health endpoint responding
- [x] Nginx configuration created
- [x] SSL certificate installed
- [x] Domain configured (brain.ft.tc)
- [x] .gitignore updated to exclude venv/

### 📋 Pending
- [ ] Commit ecosystem.config.js to repository
- [ ] Review and commit/remove RELOCATION_COMPLETE.md
- [ ] Review and commit/remove SERVICE_SEPARATION_REPORT.md
- [ ] Commit updated .gitignore
- [ ] Push changes to remote repository
- [ ] Verify PM2 startup script is configured
- [ ] Document environment variables in .env.example

---

## Recommended Next Steps

### 1. Commit PM2 Configuration
```bash
cd /var/www/mcp-brain-service
git add ecosystem.config.js
git add .gitignore
git commit -m "Add PM2 ecosystem configuration and update .gitignore"
git push origin master
```

### 2. Setup PM2 Startup
```bash
# Generate startup script
pm2 startup

# Save current process list
pm2 save
```

### 3. Monitor Service
```bash
# Check logs for any errors
pm2 logs mcp-brain-service --lines 100

# Monitor resource usage
pm2 monit
```

### 4. Test External Access
```bash
# Test HTTPS endpoint
curl https://brain.ft.tc/health

# Should return: {"status":"healthy","timestamp":"..."}
```

---

## Troubleshooting

### Service Not Starting
```bash
# Check PM2 logs
pm2 logs mcp-brain-service

# Check if port is already in use
netstat -tlnp | grep 8002

# Restart service
pm2 restart mcp-brain-service
```

### Nginx 502 Bad Gateway
```bash
# Verify service is running
pm2 list

# Check if port 8002 is listening
netstat -tlnp | grep 8002

# Test local endpoint
curl http://localhost:8002/health
```

### SSL Certificate Issues
```bash
# Check certificate expiry
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Reload nginx after renewal
sudo nginx -s reload
```

---

## Service URLs

- **Local**: http://localhost:8002
- **Production**: https://brain.ft.tc
- **Health Check**: https://brain.ft.tc/health

---

## Contact & Support

For issues or questions about this service:
1. Check PM2 logs: `pm2 logs mcp-brain-service`
2. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. Review application logs in `/var/log/mcp-brain-service-*.log`

---

**Last Updated**: 2025-10-03  
**Maintained By**: jomapps

