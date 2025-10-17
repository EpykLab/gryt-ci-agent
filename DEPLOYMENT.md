# Gryt CI Agent Deployment Guide

Complete guide for deploying the Gryt CI Agent on a VM (cloud-agnostic).

## Architecture Overview

```
┌─────────────────────┐
│   Main Gryt API     │
│  (your server)      │
└──────────┬──────────┘
           │ HTTPS/HTTP + API Key
           │ (Private Network)
           ▼
┌─────────────────────┐
│  Gryt CI Agent VM   │
│  - FastAPI service  │
│  - Docker Engine    │
│  - Isolated jobs    │
└─────────────────────┘
```

## Prerequisites

- Linux VM (Ubuntu 22.04 LTS recommended)
- 2+ vCPU, 4GB+ RAM (scale based on concurrent jobs)
- 40GB+ disk space
- Root/sudo access
- Private network connectivity to main API

## Deployment Options

### Option 1: DigitalOcean Droplet

**Step 1: Create Droplet**

1. Go to DigitalOcean Console
2. Create Droplet:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic ($24/month - 2 vCPU, 4GB RAM, 80GB SSD)
   - **Region:** Same as main API for lower latency
   - **VPC:** Enable private networking
   - **SSH Keys:** Add your SSH key

**Step 2: Initial Setup**

```bash
# SSH into droplet
ssh root@<droplet-public-ip>

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Verify Docker works
docker run hello-world

# Install Python 3.12
apt install -y python3.12 python3-pip git

# Create service user
useradd -m -s /bin/bash gryt
usermod -aG docker gryt

# Test Docker as gryt user
sudo -u gryt docker ps
```

**Step 3: Install Agent**

```bash
# Clone agent repository
cd /opt
git clone https://github.com/your-org/gryt-ci-agent.git
chown -R gryt:gryt gryt-ci-agent

# Install dependencies
cd gryt-ci-agent
sudo -u gryt pip3 install -e .
```

**Step 4: Configure Agent**

```bash
# Copy environment template
cd /opt/gryt-ci-agent
cp .envrc.example .envrc

# Edit configuration
nano .envrc
```

Set these values:
```bash
# Generate API key: openssl rand -hex 32
export AGENT_API_KEY="your-generated-api-key"

# Copy from main API (must match!)
export GRYT_ENCRYPTION_KEY="same-key-as-main-api"

# Agent settings
export AGENT_HOST="0.0.0.0"
export AGENT_PORT="8080"
export GRYT_DOCKER_IMAGE="ghcr.io/epyklab/gryt/pipeline:latest"
```

```bash
# Secure the file
chmod 600 .envrc
chown gryt:gryt .envrc
```

**Step 5: Install as Systemd Service**

```bash
# Copy service file
cp gryt-agent.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable gryt-agent
systemctl start gryt-agent

# Check status
systemctl status gryt-agent

# View logs
journalctl -u gryt-agent -f
```

**Step 6: Configure Firewall**

```bash
# Allow SSH
ufw allow OpenSSH

# Allow agent port ONLY from main API (use private IP)
ufw allow from <main-api-private-ip> to any port 8080

# Enable firewall
ufw enable
```

**Step 7: Verify Agent**

```bash
# Health check (from agent itself)
curl http://localhost:8080/health

# Should return:
# {"status":"healthy","version":"0.1.0","docker_available":true}
```

**Step 8: Configure Main API**

On your main Gryt CI API server:

```bash
# Edit .envrc
nano /path/to/gryt-ci-api/.envrc

# Add agent configuration (use private IP!)
export AGENT_URLS="http://<agent-private-ip>:8080"
export AGENT_API_KEY="same-key-you-set-on-agent"

# Restart main API
systemctl restart gryt-api  # or however you run it
```

**Step 9: Test End-to-End**

```bash
# From main API, trigger a webhook
curl -X POST http://your-api.com/api/v1/webhooks/run/<webhook-key>

# Check logs on agent
ssh gryt@<agent-ip>
sudo journalctl -u gryt-agent -f

# Should see job execution
```

---

### Option 2: AWS EC2

**Step 1: Launch Instance**

1. Go to EC2 Console
2. Launch Instance:
   - **AMI:** Ubuntu 22.04 LTS
   - **Instance Type:** t3.medium (2 vCPU, 4GB RAM) or larger
   - **Network:** Use VPC with private subnet
   - **Security Group:** 
     - Allow SSH (22) from your IP
     - Allow 8080 from main API security group
   - **Storage:** 40GB+ gp3

**Step 2: Follow Same Setup**

SSH in and follow Steps 2-9 from DigitalOcean guide above.

---

### Option 3: Hetzner Cloud

**Step 1: Create Server**

1. Go to Hetzner Cloud Console
2. Create Server:
   - **Image:** Ubuntu 22.04
   - **Type:** CPX21 (3 vCPU, 4GB RAM) - €8.46/month
   - **Network:** Create private network
   - **SSH Key:** Add your key

**Step 2: Follow Same Setup**

SSH in and follow Steps 2-9 from DigitalOcean guide above.

---

### Option 4: Bare Metal / On-Premises

**Requirements:**
- Linux server with Docker
- Network connectivity to main API
- Firewall rules configured

**Setup:**

Follow Steps 2-9 from DigitalOcean guide. Adjust network/firewall configuration based on your infrastructure.

---

## Private Networking Options

### Option A: VPC / Private Network (Cloud Provider)

Most cloud providers offer VPC with private networking:
- **DigitalOcean:** VPC
- **AWS:** VPC
- **Hetzner:** Private Networks

Main API and agents communicate via private IPs (10.x.x.x or similar).

### Option B: Tailscale (Easiest)

Tailscale creates a secure mesh VPN - works across any cloud/on-prem:

**On Main API:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

**On Agent:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

Both machines get 100.x.x.x IPs. Use these IPs in `AGENT_URLS`.

### Option C: WireGuard

For advanced users. Set up WireGuard VPN between main API and agents.

---

## Scaling: Multiple Agents

**Add More Agents:**

1. Deploy additional agent VMs (follow guide above)
2. Update main API environment:

```bash
export AGENT_URLS="http://10.0.1.5:8080,http://10.0.1.6:8080,http://10.0.1.7:8080"
```

Main API will round-robin jobs across all agents.

**Recommended Setup:**
- Small workload: 1 agent
- Medium workload: 2-3 agents
- Large workload: 5+ agents

---

## Monitoring

### Health Checks

Use Uptime Kuma, Prometheus, or similar:

```bash
curl http://agent-ip:8080/health
```

Set up alerts if agent becomes unhealthy.

### Log Monitoring

**View logs:**
```bash
sudo journalctl -u gryt-agent -f
```

**Ship to centralized logging:**
- Grafana Loki
- ELK Stack
- CloudWatch Logs (AWS)

### Resource Monitoring

Monitor CPU, memory, disk usage:
- DigitalOcean Monitoring (built-in)
- Prometheus + Node Exporter
- Netdata

---

## Maintenance

### Updating Agent

```bash
ssh gryt@agent-ip

# Pull latest code
cd /opt/gryt-ci-agent
sudo -u gryt git pull

# Install dependencies
sudo -u gryt pip3 install -e .

# Restart service
sudo systemctl restart gryt-agent
```

### Rotating API Keys

**Generate new key:**
```bash
openssl rand -hex 32
```

**Update on agent:**
```bash
sudo nano /opt/gryt-ci-agent/.envrc
# Update AGENT_API_KEY
sudo systemctl restart gryt-agent
```

**Update on main API:**
```bash
nano /path/to/gryt-ci-api/.envrc
# Update AGENT_API_KEY
systemctl restart gryt-api
```

### Docker Cleanup

Periodically clean up Docker resources:

```bash
# View disk usage
docker system df

# Clean up (removes unused containers, images, volumes)
docker system prune -af --volumes

# Automate with cron
sudo crontab -e -u gryt
# Add: 0 3 * * * docker system prune -af --volumes
```

---

## Troubleshooting

### Agent Won't Start

```bash
# Check logs
sudo journalctl -u gryt-agent -n 50

# Common issues:
# - Docker not running
# - Missing environment variables
# - Port 8080 already in use
```

### Docker Permission Denied

```bash
# Ensure user is in docker group
sudo usermod -aG docker gryt

# Logout and login
```

### Main API Can't Reach Agent

```bash
# Test connectivity from main API server
curl http://<agent-private-ip>:8080/health

# Check firewall rules
# Check network configuration (VPC, security groups)
```

### Jobs Failing

```bash
# Check agent logs for errors
sudo journalctl -u gryt-agent -f

# Test Docker manually
sudo -u gryt docker run --rm ghcr.io/epyklab/gryt/pipeline:latest gryt --version
```

---

## Security Checklist

- [ ] Agent uses private IP / VPN
- [ ] Firewall rules restrict access to main API only
- [ ] API key is strong (32+ characters)
- [ ] Agent runs as non-root user
- [ ] HTTPS for main API (Let's Encrypt)
- [ ] SSH key authentication (no passwords)
- [ ] Regular system updates (`unattended-upgrades`)
- [ ] Encryption key secured (file permissions 600)
- [ ] Log monitoring enabled
- [ ] Health check alerts configured

---

## Cost Estimates

### DigitalOcean
- **Single Agent:** $24/month (2 vCPU, 4GB RAM)
- **3 Agents:** $72/month

### AWS EC2
- **Single Agent:** ~$30/month (t3.medium)
- **3 Agents:** ~$90/month

### Hetzner (Cheapest)
- **Single Agent:** €8.46/month (~$9/month)
- **3 Agents:** €25.38/month (~$27/month)

### On-Premises
- **Hardware cost** (one-time)
- **Power + cooling** (ongoing)

---

## Next Steps

1. Deploy first agent
2. Test with webhook
3. Monitor for 24 hours
4. Add more agents if needed
5. Set up monitoring/alerts
6. Document your specific setup

---

## Support

For issues:
- Check logs: `journalctl -u gryt-agent -f`
- GitHub Issues: https://github.com/your-org/gryt-ci-agent/issues
- Main API logs: Check if main API is reaching agent

---

**You're all set!** The agent is now running and ready to execute jobs. 🚀
