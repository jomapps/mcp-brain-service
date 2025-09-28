# MCP Brain Service - Quick Start

## 🚀 Local Development Setup

### 1. Install Dependencies
```bash
cd services/mcp-brain-service
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Run Setup Script
```bash
python setup_local.py
```

### 3. Start the Service
```bash
# Option 1: Direct run
python src/main.py

# Option 2: With auto-reload
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

### 4. Test the Service
```bash
# In another terminal
python test_local.py
```

## 🔧 Environment Configuration

The service will work with minimal configuration. For full functionality:

1. **Neo4j** (optional): Set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in `.env`
2. **Jina AI** (optional): Set `JINA_API_KEY` in `.env` for real embeddings

## 🧪 Testing Endpoints

### Health Check
```bash
curl http://localhost:8002/health
```

### WebSocket Test
```bash
# Install wscat: npm install -g wscat
wscat -c ws://localhost:8002/

# Send test message:
{"tool": "create_character", "project_id": "test", "name": "Test", "personality_description": "Friendly", "appearance_description": "Tall"}
```

## 🚨 Common Issues

1. **Import Error**: Run `python setup_local.py` to check all imports
2. **Port in Use**: Change `PORT=8003` in `.env` if 8002 is occupied
3. **WebSocket Connection**: Ensure no firewall blocking port 8002