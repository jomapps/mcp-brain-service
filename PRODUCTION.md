# MCP Brain Service - Production Deployment Guide

## 🚀 Production Readiness Checklist

### ✅ Completed Production Fixes

1. **Real Jina AI Integration** - Replaced mock embeddings with actual Jina v3 API
2. **Production CORS Configuration** - Restricted origins to specific domains  
3. **Environment Variable Configuration** - Comprehensive .env setup
4. **Database Seeding System** - Real sample character data for demos
5. **Docker Production Configuration** - Ready for Ubuntu server deployment

---

## 🔧 Environment Configuration

### Required Environment Variables

Create a `.env` file in your production environment:

```bash
# Application Settings
PORT=8002
ENVIRONMENT=production

# CORS Configuration - Your actual domains
CORS_ORIGINS=https://auto-movie.ft.tc,https://brain.ft.tc,https://auto-movie.ngrok.pro

# Neo4j Database (Your production credentials)
NEO4J_URI=neo4j://neo4j.ft.tc:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_actual_neo4j_password

# Jina AI API (Your actual API key)
JINA_API_KEY=jina_your_actual_api_key_here
JINA_MODEL_NAME=jina-embeddings-v3

# Logging
LOG_LEVEL=INFO
```

---

## 🗄️ Database Setup

### 1. Seed Sample Data (First Time)

After deploying, run the seeding script to populate your Neo4j database:

```bash
# SSH into your Ubuntu server
python src/seed_data.py
```

This will create:
- **6 demo characters** across 2 projects
- **Real Jina embeddings** for all character descriptions
- **Similarity search testing** to verify functionality

### Sample Characters Created:
- **Project demo-project-001**: Elena Rodriguez (cybersecurity), Marcus Chen (food vendor), Dr. Amelia Hartwell (marine biologist)
- **Project demo-project-002**: Captain Jake Morrison (pilot), Luna Blackwood (bookshop owner), Tommy Nguyen (tech prodigy)

---

## 🐳 Docker Deployment (Coolify)

### Dockerfile
Your existing Dockerfile is production-ready:
- Python 3.12 slim base
- Optimized for production
- Environment variable support
- Port 8002 exposed

### Coolify Configuration

1. **Repository**: Point to your Git repository
2. **Build Command**: `docker build .`
3. **Port Mapping**: `8002:8002`
4. **Environment Variables**: Set all variables from `.env` section above
5. **Domain**: Configure `brain.ft.tc` to point to this service

---

## 🌐 Service Integration

### API Endpoints
- **Health Check**: `GET /health` 
- **Root**: `GET /`
- **WebSocket**: `WS /` (Main MCP communication)

### Integration with Auto-Movie Platform
```typescript
// Frontend configuration
const BRAIN_SERVICE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://brain.ft.tc'
  : 'http://localhost:8002'
```

---

## 🔍 Production Testing

### 1. Health Check
```bash
curl https://brain.ft.tc/health
# Should return: {"status":"healthy"}
```

### 2. Test WebSocket Connection
```javascript
const ws = new WebSocket('wss://brain.ft.tc/');
ws.onmessage = (event) => console.log(JSON.parse(event.data));

// Test character creation
ws.send(JSON.stringify({
  tool: "create_character",
  project_id: "test-project",
  name: "Test Character",
  personality_description: "A brave and curious explorer",
  appearance_description: "Tall with brown hair and keen eyes"
}));
```

### 3. Test Character Similarity Search
```javascript
ws.send(JSON.stringify({
  tool: "find_similar_characters", 
  project_id: "demo-project-001",
  query: "tech expert programmer"
}));
```

---

## 📊 Monitoring & Logs

### View Application Logs
```bash
# Coolify dashboard or direct docker logs
docker logs your_container_name
```

### Key Metrics to Monitor
- **Jina API Usage**: Track API call usage and costs
- **Neo4j Connection Status**: Database connectivity
- **Memory Usage**: Embedding vectors can be memory intensive
- **Response Times**: WebSocket message processing

---

## 🔐 Security Considerations

### ✅ Production Security Features
1. **API Key Protection**: Jina API key in environment variables
2. **Database Credentials**: Neo4j credentials secured
3. **CORS Restrictions**: Only allowed domains can access
4. **No Hardcoded Secrets**: All sensitive data in environment

### Additional Recommendations
1. **HTTPS Only**: Ensure all domains use HTTPS
2. **Firewall Rules**: Restrict database access to application server only
3. **API Rate Limiting**: Consider adding rate limiting for WebSocket endpoints
4. **Log Sanitization**: Ensure no API keys appear in logs

---

## 🚨 Troubleshooting

### Common Issues

**1. Jina API Errors**
- Check API key is valid
- Verify internet connectivity
- Monitor API usage limits

**2. Neo4j Connection Failures**  
- Verify Neo4j server is running
- Check firewall rules (port 7687)
- Test credentials manually

**3. CORS Errors**
- Update CORS_ORIGINS environment variable
- Check domain spelling and protocol (https://)

**4. Import Errors**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python path configuration

---

## 📈 Scaling Considerations

### Current Architecture
- Single-instance FastAPI service
- Direct Jina API calls (no caching)
- Direct Neo4j connections

### Future Scaling Options
1. **Embedding Caching**: Redis cache for frequently used embeddings
2. **Load Balancing**: Multiple service instances behind load balancer  
3. **Connection Pooling**: Neo4j connection pool optimization
4. **Async Optimization**: Batch embedding requests to Jina

---

## 🔄 Maintenance

### Regular Tasks
1. **Monitor Jina API Usage**: Track costs and usage patterns
2. **Database Backups**: Regular Neo4j backup schedule
3. **Log Rotation**: Prevent log files from growing too large
4. **Dependency Updates**: Keep Python packages updated for security

### Updating Sample Data
```bash
# To refresh sample characters
python src/seed_data.py
```

---

Your MCP Brain Service is now production-ready! 🎉

All mock implementations have been replaced with real services:
- ✅ **Real Jina AI embeddings** (1024-dimensional vectors)
- ✅ **Production CORS configuration** 
- ✅ **Environment-based configuration**
- ✅ **Rich sample data for demonstrations**
- ✅ **Docker deployment ready**