# Quick Start Guide

Get your Gryt CI Agent deployed in 5 minutes.

## Prerequisites

- Ubuntu 24.04 LTS VM with SSH access
- Ansible installed on your machine
- VM IP address and SSH key

## Steps

### 1. Install Dependencies

```bash
cd ansible
make install
```

### 2. Configure Inventory

```bash
# Edit inventory file
nano inventories/production/hosts.yml
```

Replace with your VM IP:
```yaml
all:
  children:
    gryt_agents:
      hosts:
        agent-01:
          ansible_host: YOUR_VM_IP  # Change this!
```

### 3. Set Up Secrets

```bash
# Generate keys
make generate-key          # Copy this for AGENT_API_KEY
make generate-encryption-key  # Copy this for GRYT_ENCRYPTION_KEY

# Create vault file
make setup

# Edit vault file
nano inventories/production/group_vars/gryt_agents/vault.yml

# Add your keys:
vault_agent_api_key: "paste-api-key-here"
vault_gryt_encryption_key: "paste-encryption-key-here"

# Encrypt vault
make encrypt-vault
# Enter a password (remember it!)
```

### 4. Update Variables

```bash
nano group_vars/gryt_agents.yml
```

Update these values:
```yaml
agent_git_repo: "https://github.com/YOUR-ORG/gryt-ci-agent.git"
allowed_api_ips:
  - "YOUR_MAIN_API_IP"  # Your main API server IP
```

### 5. Test Connection

```bash
make test
```

Should return:
```
agent-01 | SUCCESS => {
    "ping": "pong"
}
```

### 6. Deploy

```bash
make deploy
```

Enter your vault password when prompted.

### 7. Verify

```bash
# Check agent health
curl http://YOUR_VM_IP:8080/health

# Or use make command
make health

# View logs
make logs
```

## Done!

Your Gryt CI Agent is now running!

### Next Steps

1. **Configure Main API**: Add agent URL to main API's `AGENT_URLS`
2. **Test a Job**: Trigger a webhook to test job execution
3. **Monitor**: Set up log monitoring and alerts
4. **Scale**: Deploy more agents by adding hosts to inventory

## Common Commands

```bash
make help           # Show all commands
make deploy         # Deploy/update agents
make restart        # Restart agent service
make logs           # View logs
make health         # Check health
make update         # Update agent code only
make docker-cleanup # Clean up Docker
```

## Troubleshooting

### Can't connect to VM

```bash
# Test SSH manually
ssh root@YOUR_VM_IP

# If using different user
ansible-playbook site.yml -u ubuntu

# If using password auth
ansible-playbook site.yml --ask-pass
```

### Vault password issues

```bash
# Create password file
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass

# Now deploy without being prompted
make deploy
```

### Agent won't start

```bash
# Check status
make status

# View detailed logs
make logs

# SSH into VM
ssh root@YOUR_VM_IP
journalctl -u gryt-agent -f
```

## Need Help?

- Full documentation: See [README.md](README.md)
- Check logs: `make logs`
- GitHub Issues: https://github.com/your-org/gryt-ci-agent/issues
