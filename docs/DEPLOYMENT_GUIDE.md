# Brain Service Deployment Guide

**Version**: 1.0.0  
**Date**: January 2025  
**Status**: Production Ready

---

## 📋 Overview

This guide covers deploying the Brain Service with the new batch endpoints for automated gather creation.

---

## 🔧 Prerequisites

### System Requirements
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.12+
- Neo4j 5.13+
- PM2 (for process management)
- Nginx (for reverse proxy)

### External Services
- **Jina AI**: Embedding generation (https://jina.ai)
- **OpenRouter**: LLM operations (https://openrouter.ai)
- **PayloadCMS**: Department configurations (main application)
- **Neo4j**: Graph database

---

## 📦 Installation

### 1. Clone Repository
```bash
cd /var/www
git clone git@github.com:jomapps/mcp-brain-service.git
cd mcp-brain-service
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 1. Environment Variables

Create or update `.env` file:

```bash
# Application Settings
PORT=8002
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS Configuration
CORS_ORIGINS=http://localhost:3010,https://auto-movie.ft.tc,https://brain.ft.tc

# Neo4j Database
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Jina AI Embeddings
JINA_API_KEY=your-jina-api-key
JINA_MODEL=jina-embeddings-v4
JINA_API_URL=https://api.jina.ai/v1/embeddings

# OpenRouter LLM
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DEFAULT_MODEL=anthropic/claude-sonnet-4.5
OPENROUTER_BACKUP_MODEL=qwen/qwen3-vl-235b-a22b-thinking

# Main PayloadCMS Application
MAIN_APP_PAYLOAD_API_URL=https://aladdin.ngrok.pro/api
MAIN_APP_PAYLOAD_API_KEY=your-payload-api-key

# Brain Service API Key
BRAIN_SERVICE_API_KEY=your-brain-service-api-key

# Development Settings
USE_MOCK_EMBEDDINGS=false
USE_MOCK_NEO4J=false
```

### 2. Verify Configuration
```bash
# Load environment variables
source .env

# Test connections
python3 -c "
from src.lib.embeddings import JinaEmbeddingService
from src.lib.llm_client import get_llm_client
import asyncio

async def test():
    jina = JinaEmbeddingService()
    print('✓ Jina service initialized')
    
    llm = get_llm_client()
    print('✓ LLM client initialized')

asyncio.run(test())
"
```

---

## 🚀 Deployment Methods

### Method 1: PM2 (Recommended)

#### 1. Install PM2
```bash
npm install -g pm2
```

#### 2. Start Service
```bash
pm2 start ecosystem.config.js
```

#### 3. Verify Status
```bash
pm2 status
pm2 logs mcp-brain-service
```

#### 4. Setup Auto-Start
```bash
pm2 startup
pm2 save
```

#### 5. Monitor
```bash
pm2 monit
```

### Method 2: Systemd Service

#### 1. Copy Service File
```bash
sudo cp mcp-brain-service.service /etc/systemd/system/
```

#### 2. Update Service File
Edit `/etc/systemd/system/mcp-brain-service.service`:
```ini
[Unit]
Description=MCP Brain Service
After=network.target neo4j.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/mcp-brain-service
Environment="PATH=/var/www/mcp-brain-service/venv/bin"
EnvironmentFile=/var/www/mcp-brain-service/.env
ExecStart=/var/www/mcp-brain-service/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3. Enable and Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-brain-service
sudo systemctl start mcp-brain-service
```

#### 4. Check Status
```bash
sudo systemctl status mcp-brain-service
sudo journalctl -u mcp-brain-service -f
```

### Method 3: Docker (Optional)

#### 1. Build Image
```bash
docker build -t mcp-brain-service:latest .
```

#### 2. Run Container
```bash
docker run -d \
  --name mcp-brain-service \
  --env-file .env \
  -p 8002:8002 \
  --restart unless-stopped \
  mcp-brain-service:latest
```

---

## 🌐 Nginx Configuration

### 1. Create Nginx Config
```bash
sudo nano /etc/nginx/sites-available/brain.ft.tc
```

### 2. Add Configuration
```nginx
upstream brain_service {
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name brain.ft.tc;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name brain.ft.tc;

    # SSL Configuration (use certbot for Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/brain.ft.tc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/brain.ft.tc/privkey.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy Settings
    location / {
        proxy_pass http://brain_service;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for LLM operations
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://brain_service;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API Documentation
    location /docs {
        proxy_pass http://brain_service/docs;
        proxy_set_header Host $host;
    }

    # Health Check
    location /health {
        proxy_pass http://brain_service/health;
        access_log off;
    }
}
```

### 3. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/brain.ft.tc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL Certificate (Let's Encrypt)
```bash
sudo certbot --nginx -d brain.ft.tc
```

---

## ✅ Verification

### 1. Health Check
```bash
curl https://brain.ft.tc/health | jq .
```

Expected response:
```json
{
  "status": "healthy",
  "service": "MCP Brain Service",
  "version": "1.0.0",
  "components": {
    "neo4j": {"status": "healthy"},
    "jina": {"status": "healthy"}
  }
}
```

### 2. Test Batch Endpoints
```bash
# Run test script
./test_new_endpoints.sh
```

### 3. Check API Documentation
```bash
# Open in browser
https://brain.ft.tc/docs
```

### 4. Monitor Logs
```bash
# PM2
pm2 logs mcp-brain-service

# Systemd
sudo journalctl -u mcp-brain-service -f

# Docker
docker logs -f mcp-brain-service
```

---

## 🔍 Monitoring

### Application Logs
```bash
# PM2
pm2 logs mcp-brain-service --lines 100

# Systemd
sudo journalctl -u mcp-brain-service -n 100 --no-pager
```

### Performance Monitoring
```bash
# PM2 monitoring
pm2 monit

# System resources
htop
```

### Health Checks
```bash
# Automated health check script
watch -n 30 'curl -s https://brain.ft.tc/health | jq .'
```

---

## 🔄 Updates & Maintenance

### Update Service
```bash
cd /var/www/mcp-brain-service
git pull origin master
source venv/bin/activate
pip install -r requirements.txt

# Restart service
pm2 restart mcp-brain-service
# OR
sudo systemctl restart mcp-brain-service
```

### Database Maintenance
```bash
# Neo4j backup
neo4j-admin backup --backup-dir=/backup/neo4j

# Neo4j cleanup (if needed)
# Run Cypher queries to clean old data
```

### Log Rotation
```bash
# PM2 handles log rotation automatically

# For systemd, configure logrotate
sudo nano /etc/logrotate.d/mcp-brain-service
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
pm2 logs mcp-brain-service --err

# Verify environment variables
env | grep -E 'JINA|NEO4J|OPENROUTER'

# Test Python imports
python3 -c "from src.main import app; print('OK')"
```

### Connection Errors
```bash
# Test Neo4j
cypher-shell -u neo4j -p password "RETURN 1"

# Test Jina API
curl -H "Authorization: Bearer $JINA_API_KEY" \
  https://api.jina.ai/v1/embeddings

# Test OpenRouter
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models
```

### Performance Issues
```bash
# Check system resources
htop
df -h
free -m

# Check Neo4j performance
neo4j-admin memrec

# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s https://brain.ft.tc/health
```

---

## 🔒 Security Checklist

- [ ] Environment variables secured (not in git)
- [ ] API keys rotated and stored securely
- [ ] SSL/TLS enabled (HTTPS)
- [ ] Firewall configured (only necessary ports open)
- [ ] Neo4j authentication enabled
- [ ] Regular security updates applied
- [ ] Logs monitored for suspicious activity
- [ ] Backup strategy in place

---

## 📊 Performance Tuning

### Neo4j Optimization
```bash
# Edit neo4j.conf
sudo nano /etc/neo4j/neo4j.conf

# Increase memory
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=2g
```

### Python/Uvicorn Optimization
```bash
# Use multiple workers
uvicorn src.main:app --host 0.0.0.0 --port 8002 --workers 4
```

---

## 📞 Support

### Documentation
- API Docs: https://brain.ft.tc/docs
- Developer Guide: `/docs/BATCH_ENDPOINTS_GUIDE.md`
- Implementation Summary: `/docs/IMPLEMENTATION_SUMMARY.md`

### Logs Location
- PM2: `~/.pm2/logs/`
- Systemd: `journalctl -u mcp-brain-service`
- Application: Check `LOG_LEVEL` in `.env`

---

**Deployment Status**: ✅ Ready for Production  
**Last Updated**: January 2025

