## Production Deployment on Ubuntu with Coolify

This guide describes how to deploy MCP Brain Service (FastAPI + WebSocket) to a production Ubuntu server using Coolify.

### Overview
- App: Python/FastAPI (entrypoint `src.main:app`), serves HTTP and WebSocket
- Default internal port: 8002 (configurable via `PORT`)
- Optional dependency: Neo4j (via env `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)
- Recommended deployment: Coolify Application built from this repository with a Dockerfile

---

## 1) Prerequisites
1. Ubuntu 22.04+ server (2 vCPU / 2–4 GB RAM recommended)
2. Root or sudo SSH access
3. A domain/subdomain for Coolify (e.g., `coolify.example.com`) and one for the app (e.g., `brain.example.com`)
4. DNS A records pointing to your server’s public IP:
   - `coolify.example.com` → server IP
   - `brain.example.com` → server IP
5. Open ports in your firewall: 22 (SSH), 80 (HTTP), 443 (HTTPS)

---

## 2) Install Coolify
Coolify provides a one‑command installer that sets up Docker and Coolify.

1. SSH into your server
2. Run the installer (refer to the official docs if this changes):

```bash
curl -fsSL https://get.coollabs.io/coolify/install.sh | bash
```

3. When the installer completes, visit `https://coolify.example.com` in your browser to finish setup:
   - Create admin user
   - Confirm Coolify is healthy (Docker running, Traefik/SSL healthy)

Docs: https://coolify.io/docs

---

## 3) Prepare this repository for deployment
Coolify can auto-build Python apps, but the most reliable approach is to include a Dockerfile.

1) Create a Dockerfile in the project root:

```Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8002

WORKDIR /app

# System deps (optional, add as needed)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app source
COPY src ./src
COPY pyproject.toml ./

EXPOSE 8002

# Run with uvicorn; respect PORT env (Coolify can map any external port)
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8002}"]
```

2) (Recommended) Create a `.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
*.sqlite3
.env
.venv
/.git
/.github
/tests
/docs
```

Commit and push these files to your main branch.

---

## 4) (Optional) Provision Neo4j
This app will run without Neo4j, but to enable persistence and similarity search you can provide a Neo4j instance.

Options:
- Managed or existing Neo4j: get connection URI and credentials
- Self-hosted alongside the app:
  - You can deploy Neo4j as a separate application in Coolify using the official `neo4j:5` image.
  - Configure persistent volumes and set `NEO4J_AUTH=neo4j/<password>`.

Record your connection details:
- `NEO4J_URI` (e.g., `neo4j://neo4j.your-domain:7687`)
- `NEO4J_USER` (e.g., `neo4j`)
- `NEO4J_PASSWORD` (e.g., `supersecret`)

---

## 5) Create and configure the Application in Coolify
1. In Coolify, click “New” → “Application”.
2. Select “Git Repository” and connect your provider (GitHub/GitLab/Bitbucket), then choose this repo and branch.
3. Build settings:
   - Build type: Dockerfile
   - Dockerfile path: `./Dockerfile`
   - Context: `./`
4. Ports & networking:
   - Internal port: `8002` (matches Dockerfile `EXPOSE` and default `PORT`)
   - Attach a domain: `brain.example.com` (Coolify will provision Let’s Encrypt automatically)
5. Environment variables (Environment tab):
   - `PORT=8002`
   - (Optional) `NEO4J_URI=neo4j://host:7687`
   - (Optional) `NEO4J_USER=neo4j`
   - (Optional) `NEO4J_PASSWORD=your_password`

Save these settings.

---

## 6) First deploy
1. Click “Deploy” in the application page.
2. Wait for image build → container start → health checks.
3. Verify health endpoint: `https://brain.example.com/health` should return `{"status":"healthy"}`.
4. WebSocket: ensure your client uses `wss://brain.example.com/` in production.

---

## 7) CI/CD and auto‑deploys
- Enable auto‑deploy on push to your chosen branch to let Coolify build and redeploy automatically.
- Use deployment hooks or approvals as desired.

---

## 8) Observability & operations
- Logs: view build logs and runtime logs in the Coolify UI.
- Rollbacks: redeploy a previous successful build from history.
- Scaling: increase CPU/RAM in the app’s resource settings; add replicas if your plan supports it.
- Backups: if running Neo4j yourself, schedule backups of the data volume.

---

## 9) Security and hardening
- Restrict SSH access (key-based auth, fail2ban, ufw rules).
- Keep Ubuntu and Docker engine up to date.
- Set strong `NEO4J_PASSWORD` and disable default creds.
- Limit CORS in `src/main.py` to trusted origins for production.

---

## 10) Troubleshooting
- Build fails: check Dockerfile path and build logs; confirm `requirements.txt` installs.
- App starts but 502/Bad Gateway:
  - Confirm internal port is 8002 and matches Coolify’s service port.
  - Check logs for uvicorn startup; ensure no binding to localhost only.
- WebSocket issues:
  - Use `wss://` over HTTPS; Coolify/Traefik supports WebSockets by default.
  - Verify no proxies in front strip upgrade headers.
- Neo4j connection errors:
  - Confirm network reachability and credentials; set `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.

---

## 11) Local verification (optional)
Before pushing, you can build and run locally:

```bash
# Build
docker build -t mcp-brain-service:local .

# Run
docker run --rm -p 8002:8002 \
  -e PORT=8002 \
  -e NEO4J_URI=neo4j://host.docker.internal:7687 \
  -e NEO4J_USER=neo4j -e NEO4J_PASSWORD=password \
  mcp-brain-service:local

# Test
curl http://localhost:8002/health
```

If you need adjustments or want this automated via Coolify’s Nixpacks (no Dockerfile), let us know and we can add the exact start command and config.
