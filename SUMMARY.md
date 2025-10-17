# Gryt CI Agent - Implementation Summary

## What We Built

A **simple, cloud-agnostic job execution agent** for the Gryt CI API that runs CI/CD jobs in isolated Docker containers.

## Architecture

```
Main API (your server)
    ↓ HTTP + API Key
Agent VM (remote)
    ↓ Docker
Isolated Container (ephemeral)
    ↓ Execute
Gryt Pipeline
```

## Key Features

### 1. Simple & Stateless
- Just a FastAPI service + Docker
- No database, no state
- Receives job → executes → returns result
- ~300 lines of core code

### 2. Cloud-Agnostic
- Runs anywhere with Docker
- Not locked to AWS, GCP, Azure, etc.
- Works on:
  - DigitalOcean Droplets
  - AWS EC2
  - Hetzner Cloud
  - Bare metal servers
  - Your laptop (for testing)

### 3. Secure
- API key authentication
- Private network communication
- No public internet exposure
- Encrypted GitHub tokens
- Non-root container execution

### 4. Scalable
- Horizontal scaling: add more agent VMs
- Round-robin job distribution
- No single point of failure
- Agents are disposable/replaceable

### 5. Resilient
- Main API automatically falls back to local execution if agent unavailable
- No hard dependency on agents
- Can start without agents and add later

## Project Structure

```
gryt-ci-agent/
├── agent/
│   ├── __init__.py           # Package init
│   ├── main.py              # FastAPI service (API endpoints)
│   ├── executor.py          # Docker job execution engine
│   └── crypto.py            # Encryption utilities
├── pyproject.toml           # Dependencies
├── .envrc.example           # Environment template
├── gryt-agent.service       # Systemd service file
├── README.md                # User documentation
├── DEPLOYMENT.md            # Deployment guide
└── SUMMARY.md               # This file
```

## Core Components

### 1. FastAPI Service (`agent/main.py`)
- `GET /` - Root endpoint
- `GET /health` - Health check (no auth)
- `POST /jobs/execute` - Execute job (requires API key)

**Authentication:** X-API-Key header

### 2. Docker Executor (`agent/executor.py`)
Handles job execution:
1. Creates temp workspace
2. Clones GitHub repo (if specified)
3. Writes pipeline file
4. Runs Docker container with gryt
5. Captures output
6. Cleans up workspace

**Docker configuration:**
- Ephemeral containers (auto-removed)
- Volume mount workspace
- Resource limits (CPU, memory)
- No privileged mode

### 3. Agent Client in Main API (`gryt-ci-api/internal/services/agent_client.py`)
- `AgentClient` - Communicates with single agent
- `AgentPool` - Manages multiple agents with load balancing
- Automatic initialization from environment variables

### 4. Webhook Integration
Updated webhook handler to:
- Try agent pool first (if configured)
- Fall back to local execution on failure
- Log execution location (agent vs local)

## Configuration

### Agent Configuration
```bash
AGENT_API_KEY         # Pre-shared key for auth
GRYT_ENCRYPTION_KEY   # Same as main API (decrypt GitHub tokens)
AGENT_HOST            # Bind address (0.0.0.0)
AGENT_PORT            # Port (8080)
GRYT_DOCKER_IMAGE     # Default Docker image
```

### Main API Configuration
```bash
AGENT_URLS            # Comma-separated agent URLs
AGENT_API_KEY         # Same as agent(s)
```

## Deployment Options

### Quick (30 minutes)
See [AGENT_QUICKSTART.md](../gryt-ci-api/docs/AGENT_QUICKSTART.md)

### Production
See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- DigitalOcean Droplets
- AWS EC2
- Hetzner Cloud
- Bare metal

### Network Options
1. **Cloud VPC** - Private networking (10.x.x.x)
2. **Tailscale** - Mesh VPN (easiest)
3. **WireGuard** - Custom VPN (advanced)

## Usage Flow

### Without Agents (Default)
```
Webhook → Main API → Local Executor → Result
```

### With Agents
```
Webhook → Main API → Agent → Docker → Result
```

### With Agent Failure
```
Webhook → Main API → Agent (failed) → Local Executor → Result
```

## Scaling

### Vertical Scaling
Increase agent VM resources:
- More CPU → more concurrent jobs
- More RAM → larger jobs
- More disk → more Docker images

### Horizontal Scaling
Add more agent VMs:
```bash
# Main API environment
export AGENT_URLS="http://10.0.1.5:8080,http://10.0.1.6:8080,http://10.0.1.7:8080"
```

Jobs distributed round-robin.

### Recommended Setup
- **1-10 jobs/hour:** 1 agent (2 vCPU, 4GB RAM)
- **10-50 jobs/hour:** 2-3 agents
- **50+ jobs/hour:** 5+ agents

## Cost Estimates

| Provider | Specs | Cost/month |
|----------|-------|------------|
| Hetzner | 3 vCPU, 4GB | €8.46 (~$9) |
| DigitalOcean | 2 vCPU, 4GB | $24 |
| AWS EC2 | 2 vCPU, 4GB | ~$30 |

**Total for 3-agent setup:**
- Hetzner: ~$27/month
- DigitalOcean: $72/month
- AWS: ~$90/month

## Security Model

### Network Security
- Agent on private network only
- Firewall rules restrict access to main API
- No public internet exposure

### Authentication
- Pre-shared API key (32+ characters)
- Key rotation support
- Invalid key = 401 Unauthorized

### Container Isolation
- Non-privileged containers
- Resource limits enforced
- Automatic cleanup
- Workspace isolation

### Data Security
- GitHub tokens encrypted at rest
- Decrypted only during execution
- Never logged in plaintext
- Workspace deleted after job

## Monitoring

### Health Checks
```bash
curl http://agent-ip:8080/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "docker_available": true
}
```

### Logs
```bash
# Systemd
journalctl -u gryt-agent -f

# Look for:
# - "Received job execution request"
# - "Job X Completed in Y seconds"
# - Docker errors
```

### Metrics (Manual)
- Jobs executed
- Success rate
- Average duration
- Docker disk usage

## Future Enhancements

### Short Term
- [ ] Job execution timeouts
- [ ] Configurable resource limits per job
- [ ] Better error messages

### Medium Term
- [ ] Pull-based execution (agent polls main API)
- [ ] Job log streaming (WebSockets)
- [ ] Metrics endpoint (Prometheus)
- [ ] Job queue with priorities

### Long Term
- [ ] Kubernetes deployment
- [ ] Auto-scaling agents
- [ ] Job artifacts storage (S3)
- [ ] Web UI for logs
- [ ] Custom Docker images per pipeline

## Testing

### Manual Test
```bash
# 1. Start agent
python -m agent.main

# 2. Send test job
curl -X POST http://localhost:8080/jobs/execute \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "pipeline_b64": "'"$(echo 'version: 1\nsteps:\n  - run: echo Hello' | base64)"'"
  }'

# 3. Check response
# Should show success, stdout="Hello"
```

### End-to-End Test
1. Deploy agent
2. Configure main API with agent URL
3. Trigger webhook
4. Verify job ran on agent (check logs)
5. Verify results returned to API

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent won't start | Check Docker is running, verify .envrc |
| Can't reach agent | Check firewall, network config |
| Jobs fail | Check Docker permissions, image availability |
| Out of disk | Run `docker system prune -af` |

## Documentation

- [README.md](./README.md) - User guide
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Full deployment guide
- [AGENT_QUICKSTART.md](../gryt-ci-api/docs/AGENT_QUICKSTART.md) - 30-min setup
- [AGENT_ARCHITECTURE.md](../gryt-ci-api/docs/AGENT_ARCHITECTURE.md) - Architecture details

## Success Criteria

✅ Agent runs anywhere with Docker  
✅ No cloud vendor lock-in  
✅ Simple to deploy (<30 min)  
✅ Secure by default (private network, API key)  
✅ Automatic fallback if agent fails  
✅ Horizontal scaling with multiple agents  
✅ Comprehensive documentation  

## Summary

The Gryt CI Agent is a **minimal, production-ready job execution system** that:
- Isolates job execution from the main API
- Runs anywhere (cloud-agnostic)
- Scales horizontally
- Fails gracefully
- Requires minimal setup

Perfect for teams that want reliable CI/CD without vendor lock-in.

**Total complexity:** ~400 lines of Python + Docker. That's it! 🎉
