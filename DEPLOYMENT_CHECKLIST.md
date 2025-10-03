# MCP Brain Service - Deployment Checklist

## 🚨 CRITICAL: No Mock Mode - Production Ready

This service now **requires** all dependencies to be properly configured. Mock modes have been removed to ensure production reliability.

---

## ✅ Pre-Deployment Checklist

### 1. Environment Variables (REQUIRED)

All of these environment variables **MUST** be set on brain.ft.tc:

```bash
# Neo4j Configuration (CRITICAL - Service will NOT start without these)
NEO4J_URI=bolt://your-neo4j-host:7687  # or neo4j://host:7687
NEO4J_USER=your_neo4j_username
NEO4J_PASSWORD=your_neo4j_password

# Jina AI Configuration (CRITICAL - Required for embeddings)
JINA_API_KEY=jina_xxxxxxxxxxxxxxxxxxxxx  # Get from https://jina.ai
JINA_MODEL=jina-embeddings-v2-base-en  # Optional, defaults to this

# Brain Service API (for client authentication)
BRAIN_SERVICE_API_KEY=ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa

# CORS Origins (Optional)
CORS_ORIGINS=http://localhost:3000,http://localhost:3010,https://brain.ft.tc
```

### 2. Neo4j Database

- ✅ Neo4j instance running and accessible
- ✅ Network connectivity from brain.ft.tc to Neo4j
- ✅ Credentials tested and working
- ✅ Database has sufficient storage
- ✅ Port 7687 (bolt) or 7474 (http) accessible

**Test Connection:**
```bash
# From brain.ft.tc server, test Neo4j connection
cypher-shell -a $NEO4J_URI -u $NEO4J_USER -p $NEO4J_PASSWORD "RETURN 1;"
```

### 3. Jina AI API

- ✅ Valid Jina API key obtained from https://jina.ai
- ✅ API key has sufficient quota/credits
- ✅ Network connectivity to api.jina.ai

**Test API Key:**
```bash
curl -X POST https://api.jina.ai/v1/embeddings \
  -H "Authorization: Bearer $JINA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"jina-embeddings-v2-base-en","input":["test"]}'
```

---

## 📦 Deployment Steps

### Step 1: Upload Code to brain.ft.tc

Files modified/created:
```
mcp-brain-service/
├── src/
│   ├── main.py                    # ✅ Updated with strict validation
│   ├── api_routes.py              # ✅ NEW - REST API endpoints
│   ├── lib/
│   │   ├── neo4j_client.py        # ✅ No mock mode, strict validation
│   │   └── embeddings.py          # ✅ No mock mode, strict validation
│   └── services/
│       └── knowledge_service.py   # ✅ Uses JinaEmbeddingService correctly
```

### Step 2: Install Dependencies

```bash
# SSH into brain.ft.tc
cd /path/to/mcp-brain-service
pip install -r requirements.txt

# Verify Neo4j driver installed
python -c "from neo4j import AsyncGraphDatabase; print('✅ Neo4j driver OK')"

# Verify aiohttp installed
python -c "import aiohttp; print('✅ aiohttp OK')"
```

### Step 3: Set Environment Variables

```bash
# Add to .env file or system environment
cat > .env << EOF
NEO4J_URI=bolt://your-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
JINA_API_KEY=jina_your_api_key
BRAIN_SERVICE_API_KEY=ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa
CORS_ORIGINS=http://localhost:3000,http://localhost:3010,https://brain.ft.tc
EOF

# Load environment
source .env
```

### Step 4: Test Configuration

```bash
# Test startup (will fail fast if config is wrong)
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002

# You should see:
# ============================================================
# 🚀 Starting MCP Brain Service
# ============================================================
# 📊 Initializing Neo4j connection...
# ✅ Neo4j connection verified
# 🧠 Initializing Jina embedding service...
# ✅ Jina embeddings ready (model: jina-embeddings-v2-base-en)
# ============================================================
# ✅ MCP Brain Service started successfully
#    - Neo4j: Connected
#    - Jina: jina-embeddings-v2-base-en
#    - API: REST endpoints active at /api/v1
# ============================================================
```

### Step 5: Verify Endpoints

```bash
# Test health endpoint
curl https://brain.ft.tc/health

# Expected response:
{
  "status": "healthy",
  "service": "MCP Brain Service",
  "version": "1.0.0",
  "timestamp": "2025-10-03T...",
  "components": {
    "neo4j": {
      "status": "healthy",
      "uri": "bolt://...",
      "timestamp": "..."
    },
    "jina": {
      "status": "healthy",
      "model": "jina-embeddings-v2-base-en",
      "timestamp": "..."
    }
  }
}

# Test API v1 health
curl https://brain.ft.tc/api/v1/health \
  -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa"

# Test adding a node
curl -X POST https://brain.ft.tc/api/v1/nodes \
  -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "test",
    "content": "Test node",
    "projectId": "test-project-123",
    "properties": {}
  }'

# Test semantic search
curl -X POST https://brain.ft.tc/api/v1/search \
  -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "project_id": "test-project-123",
    "top_k": 5
  }'
```

---

## 🔍 Troubleshooting

### Service Won't Start

**Error:** `NEO4J_URI environment variable is required`
- **Solution:** Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables

**Error:** `JINA_API_KEY environment variable is required`
- **Solution:** Get API key from https://jina.ai and set JINA_API_KEY

**Error:** `Neo4j connection verification failed`
- **Solution:**
  - Verify Neo4j is running
  - Check NEO4J_URI is correct (bolt:// or neo4j://)
  - Verify credentials are correct
  - Check network connectivity

**Error:** `Jina API authentication failed`
- **Solution:**
  - Verify JINA_API_KEY is correct
  - Check API key has quota/credits
  - Test connectivity to api.jina.ai

### API Returns 500 Errors

**Check service logs:**
```bash
# If running with uvicorn
journalctl -u brain-service -f

# Or check application logs
tail -f /path/to/logs/brain-service.log
```

**Common issues:**
- Neo4j connection lost → Check Neo4j is running
- Jina API quota exceeded → Check Jina dashboard
- Invalid request format → Check API documentation in `api_routes.py`

---

## 📊 Monitoring

### Health Check Endpoint

Monitor: `GET https://brain.ft.tc/health`

**Healthy Response:**
```json
{
  "status": "healthy",
  "components": {
    "neo4j": {"status": "healthy"},
    "jina": {"status": "healthy"}
  }
}
```

**Degraded Response:**
```json
{
  "status": "degraded",
  "components": {
    "neo4j": {"status": "error", "error": "connection failed"},
    "jina": {"status": "healthy"}
  }
}
```

### Set Up Monitoring Alerts

- Alert if `/health` returns status != "healthy"
- Alert if response time > 5 seconds
- Alert on HTTP 5xx errors
- Monitor Neo4j connection count
- Monitor Jina API usage/quota

---

## 🎯 Post-Deployment Validation

Run integration tests:

```bash
cd /path/to/aladdin
node tests/test-brain-integration.js
```

Expected output:
```
✅ health: PASSED
✅ addNode: PASSED
✅ search: PASSED
✅ stats: PASSED

Results: 4/4 tests passed
```

---

## 📝 Service Configuration

### systemd Service (Recommended)

Create `/etc/systemd/system/brain-service.service`:

```ini
[Unit]
Description=MCP Brain Service
After=network.target neo4j.service

[Service]
Type=simple
User=brain
WorkingDirectory=/opt/mcp-brain-service
Environment="NEO4J_URI=bolt://localhost:7687"
Environment="NEO4J_USER=neo4j"
Environment="NEO4J_PASSWORD=your_password"
Environment="JINA_API_KEY=jina_your_key"
Environment="BRAIN_SERVICE_API_KEY=ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa"
ExecStart=/usr/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable brain-service
sudo systemctl start brain-service
sudo systemctl status brain-service
```

---

## ✅ Deployment Complete

Once all checks pass:

1. ✅ Service starts without errors
2. ✅ `/health` returns "healthy"
3. ✅ Integration tests pass
4. ✅ Can add nodes via API
5. ✅ Semantic search works
6. ✅ Monitoring alerts configured

**The Aladdin Gather feature should now work correctly!** 🎉

---

## 📞 Support

If you encounter issues:

1. Check service logs
2. Verify environment variables
3. Test Neo4j and Jina connectivity separately
4. Review this checklist
5. Check GitHub issues at the project repository
