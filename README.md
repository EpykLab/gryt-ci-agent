# Gryt CI Agent

Lightweight job execution agent for [Gryt CI](../gryt-ci-api). Receives job requests from the main API and executes them in isolated Docker containers.

## Features

- **Simple**: Just a FastAPI service that runs Docker containers
- **Cloud-Agnostic**: Runs anywhere with Docker (VMs, bare metal, your laptop)
- **Stateless**: No database, no state - just execute and report back
- **Secure**: API key authentication, encrypted GitHub tokens
- **Resource-Limited**: CPU and memory limits per job

## Architecture

```
Main API → (HTTP + API Key) → Agent → Docker Container → gryt run
```

## Requirements

- Python 3.12+
- Docker Engine installed and running
- Network access to main Gryt CI API

## Quick Start

### 1. Install Dependencies

```bash
cd gryt-ci-agent
pip install -e .
```

### 2. Configure Environment

```bash
cp .envrc.example .envrc
nano .envrc
```

Set these required variables:
- `AGENT_API_KEY`: Pre-shared key for authentication (generate with `openssl rand -hex 32`)
- `GRYT_ENCRYPTION_KEY`: Same key used by main API (for decrypting GitHub tokens)

### 3. Start Agent

```bash
# Source environment
source .envrc

# Run agent
python -m agent.main
```

Agent will start on `http://0.0.0.0:8080`

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENT_API_KEY` | ✅ | - | API key for authentication |
| `GRYT_ENCRYPTION_KEY` | ✅ | - | Encryption key (same as main API) |
| `AGENT_HOST` | ❌ | `0.0.0.0` | Host to bind to |
| `AGENT_PORT` | ❌ | `8080` | Port to listen on |
| `GRYT_DOCKER_IMAGE` | ❌ | `ghcr.io/epyklab/gryt/pipeline:latest` | Default Docker image |

## API Endpoints

### Health Check

```bash
GET /health

Response:
{
  "status": "healthy",
  "version": "0.1.0",
  "docker_available": true
}
```

No authentication required. Use this for monitoring/health checks.

### Execute Job

```bash
POST /jobs/execute
Headers:
  X-API-Key: <your-api-key>
  Content-Type: application/json

Body:
{
  "job_id": 123,
  "pipeline_b64": "<base64-encoded-pipeline>",
  "git_url": "https://github.com/user/repo.git",
  "git_branch": "main",
  "github_token_encrypted": "<encrypted-token>",
  "docker_image": "ghcr.io/epyklab/gryt/pipeline:latest",
  "env_vars": {"FOO": "bar"},
  "cpu_limit": "1.0",
  "memory_limit": "512m"
}

Response:
{
  "job_id": 123,
  "success": true,
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "duration_seconds": 42.5,
  "started_at": "2025-10-17T10:00:00Z",
  "completed_at": "2025-10-17T10:00:42Z"
}
```

## Deployment

### Option 1: Systemd Service (Recommended)

Create `/etc/systemd/system/gryt-agent.service`:

```ini
[Unit]
Description=Gryt CI Agent
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=gryt
WorkingDirectory=/opt/gryt-ci-agent
EnvironmentFile=/opt/gryt-ci-agent/.envrc
ExecStart=/usr/bin/python3 -m agent.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable gryt-agent
sudo systemctl start gryt-agent
sudo systemctl status gryt-agent
```

### Option 2: Docker Compose

```yaml
version: '3.8'
services:
  gryt-agent:
    image: python:3.12-slim
    volumes:
      - ./:/app
      - /var/run/docker.sock:/var/run/docker.sock
    working_dir: /app
    command: python -m agent.main
    environment:
      - AGENT_API_KEY=${AGENT_API_KEY}
      - GRYT_ENCRYPTION_KEY=${GRYT_ENCRYPTION_KEY}
      - AGENT_PORT=8080
    ports:
      - "8080:8080"
    restart: unless-stopped
```

Run with: `docker-compose up -d`

### Option 3: Manual VM Setup

#### DigitalOcean Droplet
```bash
# 1. Create droplet (Ubuntu 22.04, 2 vCPU, 4GB RAM)

# 2. SSH in and setup
ssh root@<droplet-ip>

# 3. Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# 4. Install Python 3.12
apt update
apt install -y python3.12 python3-pip

# 5. Clone agent repo
cd /opt
git clone <agent-repo-url> gryt-ci-agent
cd gryt-ci-agent

# 6. Install dependencies
pip3 install -e .

# 7. Configure
cp .envrc.example .envrc
nano .envrc  # Set AGENT_API_KEY and GRYT_ENCRYPTION_KEY

# 8. Setup systemd service (see above)

# 9. Configure firewall (only allow main API)
ufw allow from <main-api-ip> to any port 8080
ufw enable
```

## Security

### Network Security

**Production setup:**
- Agent should NOT be exposed to public internet
- Use private networking (VPN, VPC, Tailscale, etc.)
- Only main API can reach agent
- Use firewall rules to restrict access

**Example: Tailscale VPN**
```bash
# On both main API and agent machines
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# Agent only accessible via Tailscale IPs (100.x.x.x)
```

### API Key Management

Generate a strong API key:
```bash
openssl rand -hex 32
```

Set same key on both main API and agent:
- Main API: `AGENT_API_KEY=<key>`
- Agent: `AGENT_API_KEY=<key>`

Rotate keys periodically.

### Docker Security

The agent runs containers with these security measures:
- Non-privileged containers
- Resource limits (CPU, memory)
- No host network access
- Automatic cleanup after execution

For enhanced security, consider:
- Running agent as non-root user
- Using Docker's user namespaces
- Restricting Docker socket access

## Monitoring

### Health Checks

Use the `/health` endpoint for monitoring:

```bash
curl http://agent-ip:8080/health
```

For Uptime Kuma, Prometheus, etc., set up HTTP checks against this endpoint.

### Logs

View agent logs:
```bash
# Systemd
sudo journalctl -u gryt-agent -f

# Docker Compose
docker-compose logs -f
```

### Metrics (Future)

Planned metrics to expose:
- Jobs executed (total, success, failure)
- Average job duration
- Docker resource usage
- Queue depth (if pull-based)

## Troubleshooting

### Docker Connection Error

```
Error: Failed to connect to Docker
```

**Solution:**
- Ensure Docker is running: `systemctl status docker`
- Check user has Docker permissions: `usermod -aG docker $USER`
- Verify Docker socket: `ls -l /var/run/docker.sock`

### Image Pull Failures

```
Error: Failed to pull image
```

**Solution:**
- Check internet connectivity
- For private images, authenticate: `docker login ghcr.io`
- Verify image name and tag

### Job Execution Timeout

Jobs that run too long will hang. Future versions will add configurable timeouts.

### Out of Disk Space

Docker images and containers consume disk. Clean up periodically:

```bash
docker system prune -af --volumes
```

## Development

### Running Tests

```bash
pytest
```

### Testing Locally

```bash
# Terminal 1: Start agent
source .envrc
python -m agent.main

# Terminal 2: Test with curl
curl -X POST http://localhost:8080/jobs/execute \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "pipeline_b64": "<base64-encoded-pipeline>"
  }'
```

## Scaling

### Horizontal Scaling

Run multiple agents on different machines. Main API will distribute jobs across all agents (load balancing).

**Simple setup:**
1. Deploy agent on 3 VMs
2. Configure main API with all agent URLs: `AGENT_URLS=http://agent1:8080,http://agent2:8080,http://agent3:8080`
3. Main API round-robins jobs to agents

### Vertical Scaling

Increase VM resources (CPU, RAM) to handle more concurrent jobs.

## Future Enhancements

- [ ] Pull-based job execution (agent polls main API)
- [ ] Job log streaming (WebSockets)
- [ ] Job queue with priorities
- [ ] Graceful shutdown (wait for jobs to complete)
- [ ] Metrics and monitoring endpoints
- [ ] Support for custom Docker images per job
- [ ] Job artifacts upload (S3, Minio)
- [ ] Kubernetes deployment manifests

## License

[Your License]
