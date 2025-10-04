# MCP Brain Service - Quick Reference

## Service Management

```bash
# Start the service
sudo systemctl start mcp-brain-service

# Stop the service
sudo systemctl stop mcp-brain-service

# Restart the service
sudo systemctl restart mcp-brain-service

# Check service status
sudo systemctl status mcp-brain-service

# View live logs
sudo journalctl -u mcp-brain-service -f

# View last 100 log lines
sudo journalctl -u mcp-brain-service -n 100

# Enable auto-start on boot (already enabled)
sudo systemctl enable mcp-brain-service

# Disable auto-start on boot
sudo systemctl disable mcp-brain-service
```

## API Endpoints

### Base URL
```
http://localhost:8002
http://brain.ft.tc:8002
```

### Authentication
All `/api/v1/*` endpoints require Bearer token authentication:
```bash
Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa
```

### Health Check (No Auth)
```bash
curl http://localhost:8002/health
```

### Authenticated Health Check
```bash
curl -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  http://localhost:8002/api/v1/health
```

### Get Statistics
```bash
curl -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  http://localhost:8002/api/v1/stats
```

### Create Node
```bash
curl -X POST http://localhost:8002/api/v1/nodes \
  -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "document",
    "content": "Your content here",
    "projectId": "your-project-id",
    "properties": {
      "key": "value"
    }
  }'
```

### Semantic Search
```bash
curl -X POST http://localhost:8002/api/v1/search \
  -H "Authorization: Bearer ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search query",
    "project_id": "your-project-id",
    "top_k": 10
  }'
```

## Configuration Files

### Service Configuration
- **Location:** `/etc/systemd/system/mcp-brain-service.service`
- **Working Directory:** `/var/www/mcp-brain-service`
- **Environment File:** `/var/www/mcp-brain-service/.env`

### Environment Variables (.env)
```bash
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa

JINA_API_KEY=jina_bafa0ee92bea44198004e4ca0c9d517coCaPnnZjX0bUmXU8WnfR3NE3YcpK
JINA_MODEL=jina-embeddings-v4

API_KEY=ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa
```

## Neo4j Management

### Check Neo4j Status
```bash
sudo systemctl status neo4j
```

### Restart Neo4j
```bash
sudo systemctl restart neo4j
```

### Connect to Neo4j Shell
```bash
cypher-shell -a neo4j://127.0.0.1:7687 -u neo4j -p "ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa"
```

### Verify GDS Installation
```bash
cypher-shell -a neo4j://127.0.0.1:7687 -u neo4j -p "ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  "RETURN gds.version() as version;"
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u mcp-brain-service -n 50

# Check if port 8002 is already in use
sudo lsof -i :8002

# Verify Neo4j is running
sudo systemctl status neo4j

# Test Neo4j connection
cypher-shell -a neo4j://127.0.0.1:7687 -u neo4j -p "ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" "RETURN 1;"
```

### Check Environment Variables
```bash
# View loaded environment
sudo systemctl show mcp-brain-service --property=Environment
```

### Manual Start (for debugging)
```bash
cd /var/www/mcp-brain-service
source .env
./venv/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8002
```

## Performance Monitoring

### Check Service Resource Usage
```bash
sudo systemctl status mcp-brain-service
```

### Monitor Logs in Real-time
```bash
sudo journalctl -u mcp-brain-service -f
```

### Check Neo4j Memory Usage
```bash
cypher-shell -a neo4j://127.0.0.1:7687 -u neo4j -p "ae6e18cb408bc7128f23585casdlaelwlekoqdsldsa" \
  "CALL dbms.queryJmx('org.neo4j:*') YIELD attributes RETURN attributes;"
```

## Backup & Maintenance

### Backup Neo4j Database
```bash
sudo systemctl stop neo4j
sudo neo4j-admin database dump neo4j --to-path=/backup/neo4j/
sudo systemctl start neo4j
```

### Update Code from Git
```bash
cd /var/www/mcp-brain-service
git pull origin master
sudo systemctl restart mcp-brain-service
```

### Update Python Dependencies
```bash
cd /var/www/mcp-brain-service
./venv/bin/pip install -r requirements.txt --upgrade
sudo systemctl restart mcp-brain-service
```

## Key Files & Directories

```
/var/www/mcp-brain-service/          # Application root
├── .env                              # Environment variables
├── src/                              # Source code
├── venv/                             # Python virtual environment
├── start.sh                          # Startup script
├── mcp-brain-service.service         # Systemd service file (copy)
├── DEPLOYMENT_SUMMARY.md             # Deployment documentation
├── DEPLOYMENT_CHECKLIST.md           # Deployment checklist
└── QUICK_REFERENCE.md                # This file

/etc/systemd/system/
└── mcp-brain-service.service         # Active systemd service file

/var/lib/neo4j/
├── data/                             # Neo4j database files
└── plugins/
    └── neo4j-graph-data-science-2.13.2.jar  # GDS plugin
```

## Important Notes

- ✅ Service auto-starts on boot
- ✅ Service auto-restarts on failure (10 second delay)
- ✅ All logs go to systemd journal
- ✅ Neo4j GDS 2.13.2 installed for semantic search
- ✅ Jina embeddings v4 model configured
- ⚠️ API key required for all `/api/v1/*` endpoints
- ⚠️ Public health check at `/health` (no auth)

## Support

For issues or questions, check:
1. Service logs: `sudo journalctl -u mcp-brain-service -f`
2. Neo4j logs: `sudo journalctl -u neo4j -f`
3. DEPLOYMENT_SUMMARY.md for detailed deployment info

