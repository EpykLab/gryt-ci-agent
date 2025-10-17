# Gryt CI Agent - Ansible Deployment

Automated deployment of Gryt CI Agent on Ubuntu 24.04 LTS using Ansible.

## Features

- **Automated VM Setup**: Complete system configuration and hardening
- **Docker Installation**: Latest Docker Engine with optimized settings
- **Security Hardening**: SSH hardening, UFW firewall, kernel parameters
- **Service Management**: Systemd service with auto-restart
- **Best Practices**: Follows Ansible and security best practices
- **Idempotent**: Safe to run multiple times
- **Scalable**: Deploy to multiple agents simultaneously

## Prerequisites

### Control Machine (Your Laptop/Workstation)

1. **Ansible 2.15+**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install ansible
   
   # macOS
   brew install ansible
   
   # Python pip
   pip3 install ansible
   ```

2. **SSH Access**
   - SSH key configured for root/ubuntu user on target VMs
   - Test: `ssh root@your-vm-ip`

### Target VMs

- **OS**: Ubuntu 24.04 LTS (or 22.04)
- **Resources**: 2+ vCPU, 4GB+ RAM, 40GB+ disk
- **Network**: Private network access to main API
- **Access**: Root or sudo access

## Quick Start

### 1. Install Ansible Dependencies

```bash
cd ansible
ansible-galaxy install -r requirements.yml
```

### 2. Configure Inventory

Edit your inventory file with your VM details:

```bash
cp inventories/production/hosts.example inventories/production/hosts.yml
nano inventories/production/hosts.yml
```

Example:
```yaml
all:
  children:
    gryt_agents:
      hosts:
        agent-01:
          ansible_host: 10.0.1.5
        agent-02:
          ansible_host: 10.0.1.6
```

### 3. Configure Variables

Edit the group variables:

```bash
nano group_vars/gryt_agents.yml
```

Update:
- `agent_git_repo`: Your Gryt CI Agent repository URL
- `allowed_api_ips`: Your main API server IP addresses

### 4. Set Up Secrets

Create and encrypt your vault file:

```bash
# Create vault file from example
mkdir -p inventories/production/group_vars/gryt_agents
cp inventories/production/group_vars/gryt_agents/vault.yml.example \
   inventories/production/group_vars/gryt_agents/vault.yml

# Edit with your secrets
nano inventories/production/group_vars/gryt_agents/vault.yml
```

Generate secure keys:
```bash
# Generate API key
openssl rand -hex 32

# Generate encryption key (if needed)
openssl rand -base64 32
```

Encrypt the vault:
```bash
ansible-vault encrypt inventories/production/group_vars/gryt_agents/vault.yml
```

### 5. Test Connection

```bash
ansible gryt_agents -m ping
```

### 6. Deploy

Run the playbook:

```bash
# Deploy to all agents
ansible-playbook site.yml --ask-vault-pass

# Or with vault password file
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass
ansible-playbook site.yml

# Deploy to specific host
ansible-playbook site.yml --limit agent-01

# Dry run (check mode)
ansible-playbook site.yml --check
```

### 7. Verify Deployment

```bash
# Check agent health
curl http://agent-ip:8080/health

# View logs
ssh gryt@agent-ip
sudo journalctl -u gryt-agent -f
```

## Playbook Structure

```
ansible/
├── site.yml                    # Main playbook
├── ansible.cfg                 # Ansible configuration
├── requirements.yml            # Galaxy dependencies
├── inventories/
│   └── production/
│       ├── hosts.yml           # Inventory file
│       └── group_vars/
│           └── gryt_agents/
│               └── vault.yml   # Encrypted secrets
├── group_vars/
│   ├── all.yml                 # Global variables
│   └── gryt_agents.yml         # Agent-specific variables
└── roles/
    ├── common/                 # System setup
    ├── security/               # Security hardening
    ├── docker/                 # Docker installation
    └── gryt_agent/             # Agent deployment
```

## Roles

### Common Role
- Updates system packages
- Installs Python 3.12
- Creates gryt user
- Configures automatic updates
- Sets up fail2ban

### Security Role
- Hardens SSH configuration
- Configures UFW firewall
- Sets kernel security parameters
- Disables unused services
- Optional: auditd setup

### Docker Role
- Installs Docker Engine
- Configures Docker daemon
- Adds gryt user to docker group
- Sets up Docker cleanup cron job

### Gryt Agent Role
- Clones agent repository
- Installs Python dependencies
- Creates configuration files
- Sets up systemd service
- Configures logging

## Advanced Usage

### Deploy to Multiple Environments

Create separate inventories:

```bash
# Staging
ansible-playbook site.yml -i inventories/staging/hosts.yml

# Production
ansible-playbook site.yml -i inventories/production/hosts.yml
```

### Run Specific Roles or Tags

```bash
# Only security hardening
ansible-playbook site.yml --tags security

# Skip security
ansible-playbook site.yml --skip-tags security

# Only update agent code
ansible-playbook site.yml --tags agent,install

# Only configure firewall
ansible-playbook site.yml --tags firewall
```

### Override Variables

```bash
# Change agent port
ansible-playbook site.yml -e "agent_port=9090"

# Use different Docker image
ansible-playbook site.yml -e "gryt_docker_image=custom/image:latest"

# Disable firewall
ansible-playbook site.yml -e "ufw_enabled=false"
```

### Update Existing Agents

```bash
# Pull latest code and restart
ansible-playbook site.yml --tags agent

# Update Docker image
ansible gryt_agents -b -m docker_image \
  -a "name=ghcr.io/epyklab/gryt/pipeline:latest source=pull"
```

### Parallel Execution

```bash
# Deploy to 10 hosts at once
ansible-playbook site.yml -f 10
```

## Maintenance

### Update Agent Code

```bash
ansible-playbook site.yml --tags agent,install
```

### Restart Agent Service

```bash
ansible gryt_agents -b -m systemd \
  -a "name=gryt-agent state=restarted"
```

### View Agent Logs

```bash
ansible gryt_agents -b -m command \
  -a "journalctl -u gryt-agent -n 50 --no-pager"
```

### Check Agent Health

```bash
ansible gryt_agents -m uri \
  -a "url=http://localhost:8080/health"
```

### Rotate API Keys

1. Generate new key: `openssl rand -hex 32`
2. Update vault: `ansible-vault edit inventories/production/group_vars/gryt_agents/vault.yml`
3. Redeploy: `ansible-playbook site.yml --tags agent,config`
4. Update main API with new key

### Docker Cleanup

```bash
# Manual cleanup
ansible gryt_agents -b -u gryt -m command \
  -a "docker system prune -af --volumes"
```

## Troubleshooting

### SSH Connection Issues

```bash
# Test SSH manually
ssh -vvv root@agent-ip

# Use different user
ansible-playbook site.yml -u ubuntu

# Use password authentication
ansible-playbook site.yml --ask-pass
```

### Vault Issues

```bash
# View vault contents
ansible-vault view inventories/production/group_vars/gryt_agents/vault.yml

# Edit vault
ansible-vault edit inventories/production/group_vars/gryt_agents/vault.yml

# Change vault password
ansible-vault rekey inventories/production/group_vars/gryt_agents/vault.yml
```

### Playbook Fails

```bash
# Verbose output
ansible-playbook site.yml -vvv

# Start at specific task
ansible-playbook site.yml --start-at-task="Task name"

# Check syntax
ansible-playbook site.yml --syntax-check

# List tasks
ansible-playbook site.yml --list-tasks

# List hosts
ansible-playbook site.yml --list-hosts
```

### Agent Won't Start

```bash
# Check service status
ansible gryt_agents -b -m command \
  -a "systemctl status gryt-agent"

# View full logs
ansible gryt_agents -b -m command \
  -a "journalctl -u gryt-agent -n 100 --no-pager"

# Test Docker access
ansible gryt_agents -b -u gryt -m command \
  -a "docker ps"
```

## Security Best Practices

1. **Use Ansible Vault** for all secrets
2. **Never commit** `.vault_pass` or unencrypted secrets
3. **Rotate keys regularly** (API keys, encryption keys)
4. **Use private networks** for agent communication
5. **Enable UFW firewall** and restrict access
6. **Keep SSH keys secure** with passphrases
7. **Enable automatic security updates**
8. **Monitor logs** for suspicious activity
9. **Use SSH key authentication** only
10. **Regular backups** of configuration

## Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `vault_agent_api_key` | Agent API key | `abc123...` |
| `vault_gryt_encryption_key` | Encryption key | `xyz789...` |
| `agent_git_repo` | Git repository URL | `https://github.com/...` |
| `allowed_api_ips` | Main API IPs | `["10.0.1.10"]` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `agent_host` | `0.0.0.0` | Agent bind address |
| `agent_port` | `8080` | Agent port |
| `gryt_user` | `gryt` | Service user |
| `agent_install_dir` | `/opt/gryt-ci-agent` | Install directory |
| `ufw_enabled` | `true` | Enable firewall |
| `docker_cleanup_enabled` | `true` | Docker cleanup cron |
| `timezone` | `UTC` | System timezone |

See `group_vars/` files for complete list.

## Examples

### Deploy Single Agent

```bash
ansible-playbook site.yml --limit agent-01
```

### Deploy to Multiple Clouds

```yaml
# inventories/production/hosts.yml
all:
  children:
    gryt_agents:
      hosts:
        do-agent-01:
          ansible_host: 10.108.0.5
          ansible_user: root
        aws-agent-01:
          ansible_host: 172.31.10.5
          ansible_user: ubuntu
        hetzner-agent-01:
          ansible_host: 10.0.0.5
          ansible_user: root
```

### Custom Agent Configuration

```yaml
# group_vars/gryt_agents.yml
agent_port: 9090
gryt_docker_image: "custom/pipeline:v2"
docker_cleanup_schedule: "0 2 * * *"  # 2 AM
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy Agent
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Ansible
        run: pip install ansible
      - name: Deploy
        run: |
          cd ansible
          echo "${{ secrets.VAULT_PASS }}" > .vault_pass
          ansible-playbook site.yml
```

### GitLab CI

```yaml
deploy:
  stage: deploy
  image: python:3.12
  script:
    - pip install ansible
    - cd ansible
    - echo "$VAULT_PASS" > .vault_pass
    - ansible-playbook site.yml
  only:
    - main
```

## Support

For issues or questions:
- Check logs: `journalctl -u gryt-agent -f`
- Review playbook output
- GitHub Issues: https://github.com/your-org/gryt-ci-agent/issues

## Contributing

1. Test changes in staging environment
2. Use `ansible-lint` for validation
3. Document new variables
4. Update this README

## License

Same as Gryt CI Agent project.
