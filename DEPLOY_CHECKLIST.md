# 🚀 Coolify Deployment Checklist - MCP Brain Service

## ✅ Pre-Deployment Checklist

### 1. **Git Repository Status**
- [x] Code committed and pushed to `master` branch
- [x] Production-ready changes deployed
- [x] Commit hash: `8e1117c` - "feat: production-ready MCP Brain Service with real Jina AI integration"

### 2. **Coolify Environment Variables Setup**

Copy and paste these environment variables into your Coolify application settings:

```bash
# Application Settings
PORT=8002
ENVIRONMENT=production

# CORS Configuration - UPDATE WITH YOUR ACTUAL DOMAINS
CORS_ORIGINS=https://auto-movie.ft.tc,https://brain.ft.tc,https://auto-movie.ngrok.pro

# Neo4j Database - YOUR PRODUCTION CREDENTIALS
NEO4J_URI=neo4j://neo4j.ft.tc:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa

# Jina AI API - YOUR ACTUAL KEY
JINA_API_KEY=jina_bafa0ee92bea44198004e4ca0c9d517coCaPnnZjX0bUmXU8WnfR3NE3YcpK
JINA_MODEL_NAME=jina-embeddings-v3

# Logging
LOG_LEVEL=INFO
```

### 3. **Coolify Configuration**
- **Domain**: `brain.ft.tc`
- **Port**: `8002`
- **Build Method**: Docker
- **Repository**: `https://github.com/jomapps/mcp-brain-service.git`
- **Branch**: `master`

---

## 🔄 Deployment Process

### Step 1: Update Environment Variables
1. Go to your Coolify dashboard
2. Navigate to MCP Brain Service application
3. Go to **Environment Variables** section
4. **Clear existing variables** and **add all variables** from the list above
5. **Save changes**

### Step 2: Trigger Rebuild
The push to master should have automatically triggered a rebuild. If not:
1. Go to **Deployments** tab
2. Click **Deploy** button
3. Monitor build logs for any errors

### Step 3: Post-Deployment Verification

#### A. Health Check
```bash
curl https://brain.ft.tc/health
# Expected: {"status":"healthy"}
```

#### B. Root Endpoint
```bash
curl https://brain.ft.tc/
# Expected: {"message":"MCP Brain Service is running"}
```

#### C. WebSocket Test (Browser Console)
```javascript
const ws = new WebSocket('wss://brain.ft.tc/');
ws.onopen = () => console.log('✅ WebSocket connected');
ws.onmessage = (e) => console.log('📨 Received:', JSON.parse(e.data));
ws.onerror = (e) => console.log('❌ WebSocket error:', e);
```

---

## 📊 Post-Deployment Tasks

### 1. Database Seeding (IMPORTANT)
After successful deployment, seed the database with sample data:

```bash
# SSH into your server or use Coolify terminal
python src/seed_data.py
```

This will create:
- 6 demo characters with real Jina embeddings
- 2 demo projects (demo-project-001, demo-project-002)
- Test similarity search functionality

### 2. Integration Testing
Test the full workflow:

```javascript
// 1. Create a test character
const ws = new WebSocket('wss://brain.ft.tc/');

ws.onopen = () => {
  // Create character
  ws.send(JSON.stringify({
    tool: "create_character",
    project_id: "test-integration",
    name: "Test Character",
    personality_description: "A brave and intelligent detective with keen observation skills",
    appearance_description: "Tall woman with sharp green eyes and dark coat"
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log('Response:', response);
  
  // If character created successfully, test similarity search
  if (response.status === 'success') {
    setTimeout(() => {
      ws.send(JSON.stringify({
        tool: "find_similar_characters",
        project_id: "demo-project-001", 
        query: "intelligent problem solver"
      }));
    }, 1000);
  }
};
```

---

## 🚨 Troubleshooting

### Common Deployment Issues

#### 1. Build Fails
- Check Coolify build logs
- Verify Dockerfile is present
- Ensure requirements.txt has all dependencies

#### 2. Application Starts but Health Check Fails
- Check if port 8002 is exposed correctly
- Verify environment variables are set
- Look at application logs for startup errors

#### 3. Jina API Errors
- Verify `JINA_API_KEY` is correct
- Check internet connectivity from server
- Monitor Jina API usage limits

#### 4. Neo4j Connection Issues
- Test Neo4j connectivity: `telnet neo4j.ft.tc 7687`
- Verify credentials in environment variables
- Check if Neo4j service is running

#### 5. CORS Errors (Frontend Integration)
- Update `CORS_ORIGINS` with correct domains
- Ensure protocols match (https://)
- Check browser developer console for specific errors

---

## 📈 Performance Monitoring

### Key Metrics to Watch
1. **Response Times**: WebSocket message processing
2. **Memory Usage**: Embedding vectors can be memory intensive
3. **API Calls**: Jina API usage and costs
4. **Database Connections**: Neo4j connection pool status

### Coolify Monitoring
- **CPU Usage**: Should be low unless processing many embeddings
- **Memory**: Watch for memory leaks in long-running processes
- **Network**: Monitor inbound/outbound traffic patterns

---

## 🔄 Rollback Plan

If deployment fails:

```bash
# Revert to previous working commit
git revert 8e1117c
git push origin master

# Or rollback to specific working commit
git reset --hard 9eebf1a  # Previous working commit
git push --force origin master
```

---

## ✅ Success Criteria

Your deployment is successful when:

- [x] Health check returns `{"status":"healthy"}`
- [x] Root endpoint returns service message  
- [x] WebSocket connection establishes successfully
- [x] Character creation works with real Jina embeddings
- [x] Similarity search returns relevant results
- [x] No errors in application logs
- [x] CORS allows requests from auto-movie.ft.tc

---

**🎉 Ready to Deploy!**

The rebuild should have been triggered automatically. Monitor your Coolify dashboard for the deployment status, and run the post-deployment verification steps once it's live.