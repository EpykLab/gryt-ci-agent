# Ansible Deployment - Summary

Complete Ansible automation for deploying Gryt CI Agent on Ubuntu 24.04 LTS.

## What's Included

### Core Playbook
- **site.yml**: Main playbook that orchestrates the entire deployment
- **ansible.cfg**: Optimized Ansible configuration
- **requirements.yml**: Galaxy dependencies

### Roles (4 Total)

1. **common**: System configuration
   - Package updates
   - Python 3.12 installation
   - User/group creation
   - Automatic updates
   - Fail2ban

2. **security**: Security hardening
   - SSH hardening
   - UFW firewall
   - Kernel security parameters
   - Auditd (optional)

3. **docker**: Docker Engine
   - Docker CE installation
   - Daemon configuration
   - User permissions
   - Cleanup automation

4. **gryt_agent**: Agent deployment
   - Git clone
   - Python dependencies
   - Systemd service
   - Health checks
   - Log rotation

### Additional Playbooks

- **update-agent.yml**: Update agent code only
- **rotate-keys.yml**: Rotate API keys
- **backup-config.yml**: Backup configurations

### Configuration Files

- **inventories/production/hosts.yml**: Server inventory
- **group_vars/all.yml**: Global variables
- **group_vars/gryt_agents.yml**: Agent-specific variables
- **group_vars/gryt_agents/vault.yml**: Encrypted secrets

### Utilities

- **Makefile**: Convenient commands
- **QUICKSTART.md**: 5-minute setup guide
- **README.md**: Complete documentation

## Directory Structure

```
ansible/
├── site.yml                          # Main playbook
├── ansible.cfg                       # Configuration
├── requirements.yml                  # Dependencies
├── Makefile                         # Helper commands
├── README.md                        # Full documentation
├── QUICKSTART.md                    # Quick start guide
├── .gitignore                       # Git ignore rules
│
├── inventories/
│   └── production/
│       ├── hosts.yml                # Inventory
│       └── group_vars/
│           └── gryt_agents/
│               └── vault.yml.example # Secrets template
│
├── group_vars/
│   ├── all.yml                      # Global vars
│   └── gryt_agents.yml              # Agent vars
│
├── playbooks/
│   ├── update-agent.yml             # Update playbook
│   ├── rotate-keys.yml              # Key rotation
│   └── backup-config.yml            # Backup playbook
│
└── roles/
    ├── common/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── defaults/main.yml
    │   └── templates/
    │       ├── 50unattended-upgrades.j2
    │       ├── 20auto-upgrades.j2
    │       └── jail.local.j2
    │
    ├── security/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   └── defaults/main.yml
    │
    ├── docker/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── defaults/main.yml
    │   └── templates/
    │       ├── daemon.json.j2
    │       └── docker-cleanup.sh.j2
    │
    └── gryt_agent/
        ├── tasks/main.yml
        ├── handlers/main.yml
        ├── defaults/main.yml
        └── templates/
            ├── envrc.j2
            ├── gryt-agent.service.j2
            └── logrotate.j2
```

## Features

### Best Practices Implemented

✅ **Idempotent**: Safe to run multiple times
✅ **Role-based**: Modular and reusable
✅ **Handlers**: Efficient service restarts
✅ **Templates**: Dynamic configuration
✅ **Tags**: Selective execution
✅ **Vault**: Encrypted secrets
✅ **Health Checks**: Automated verification
✅ **Error Handling**: Robust error management
✅ **Logging**: Comprehensive logging
✅ **Documentation**: Complete docs

### Security Features

- SSH hardening (no root, no passwords)
- UFW firewall with IP whitelisting
- Kernel security parameters
- Automatic security updates
- Fail2ban for SSH protection
- Service user with minimal permissions
- Secure file permissions (600 for secrets)
- Optional auditd logging

### Automation Features

- Automated Docker cleanup (daily)
- Automatic security updates
- Log rotation
- Service auto-restart on failure
- Health monitoring
- Fact caching for performance

## Quick Commands

```bash
# Setup
make install              # Install dependencies
make setup               # Create vault file
make encrypt-vault       # Encrypt secrets

# Testing
make test                # Test connectivity
make check               # Check syntax
make dry-run             # Dry run

# Deployment
make deploy              # Deploy all
make deploy-one HOST=x   # Deploy to one

# Management
make update              # Update code
make restart             # Restart service
make logs                # View logs
make health              # Check health

# Maintenance
make docker-cleanup      # Clean Docker
make generate-key        # Generate API key
```

## Quick Start (3 Steps)

1. **Configure**
   ```bash
   cd ansible
   make install
   nano inventories/production/hosts.yml  # Set VM IP
   ```

2. **Set Secrets**
   ```bash
   make setup
   make generate-key  # Copy output
   nano inventories/production/group_vars/gryt_agents/vault.yml
   make encrypt-vault
   ```

3. **Deploy**
   ```bash
   make deploy
   ```

## Customization

### Change Agent Port
```yaml
# group_vars/gryt_agents.yml
agent_port: 9090
```

### Use Custom Docker Image
```yaml
# group_vars/gryt_agents.yml
gryt_docker_image: "custom/pipeline:v2"
```

### Disable Firewall
```yaml
# group_vars/gryt_agents.yml
ufw_enabled: false
```

### Add More Agents
```yaml
# inventories/production/hosts.yml
all:
  children:
    gryt_agents:
      hosts:
        agent-01:
          ansible_host: 10.0.1.5
        agent-02:
          ansible_host: 10.0.1.6
        agent-03:
          ansible_host: 10.0.1.7
```

## Advanced Usage

### Run Specific Roles
```bash
ansible-playbook site.yml --tags security
ansible-playbook site.yml --tags docker,agent
ansible-playbook site.yml --skip-tags firewall
```

### Override Variables
```bash
ansible-playbook site.yml -e "agent_port=9090"
ansible-playbook site.yml -e "ufw_enabled=false"
```

### Deploy to Subset
```bash
ansible-playbook site.yml --limit agent-01
ansible-playbook site.yml --limit "agent-01,agent-02"
```

## Maintenance Tasks

### Update Agent Code
```bash
ansible-playbook playbooks/update-agent.yml
```

### Rotate API Keys
```bash
ansible-playbook playbooks/rotate-keys.yml
```

### Backup Configuration
```bash
ansible-playbook playbooks/backup-config.yml
```

### Manual Commands
```bash
# Restart service
ansible gryt_agents -b -m systemd -a "name=gryt-agent state=restarted"

# View logs
ansible gryt_agents -b -m command -a "journalctl -u gryt-agent -n 50"

# Check health
ansible gryt_agents -m uri -a "url=http://localhost:8080/health"

# Run arbitrary command
ansible gryt_agents -b -a "docker ps"
```

## Troubleshooting

### Connection Issues
```bash
# Test SSH
ssh root@YOUR_VM_IP

# Use different user
ansible-playbook site.yml -u ubuntu

# Use password auth
ansible-playbook site.yml --ask-pass
```

### Vault Issues
```bash
# View vault
ansible-vault view inventories/production/group_vars/gryt_agents/vault.yml

# Edit vault
ansible-vault edit inventories/production/group_vars/gryt_agents/vault.yml

# Use password file
echo "password" > .vault_pass
chmod 600 .vault_pass
```

### Debugging
```bash
# Verbose output
ansible-playbook site.yml -vvv

# Check syntax
ansible-playbook site.yml --syntax-check

# List tasks
ansible-playbook site.yml --list-tasks

# List hosts
ansible-playbook site.yml --list-hosts
```

## Cloud Provider Examples

### DigitalOcean
```yaml
hosts:
  do-agent:
    ansible_host: 10.108.0.5
    ansible_user: root
```

### AWS EC2
```yaml
hosts:
  aws-agent:
    ansible_host: 172.31.10.5
    ansible_user: ubuntu
```

### Hetzner Cloud
```yaml
hosts:
  hetzner-agent:
    ansible_host: 10.0.0.5
    ansible_user: root
```

## Variables Reference

### Required (in vault.yml)
- `vault_agent_api_key`: Agent API key
- `vault_gryt_encryption_key`: Encryption key

### Important
- `agent_git_repo`: Git repository URL
- `allowed_api_ips`: Main API IPs (array)

### Optional
- `agent_host`: Bind address (default: 0.0.0.0)
- `agent_port`: Port (default: 8080)
- `gryt_user`: Service user (default: gryt)
- `agent_install_dir`: Install path (default: /opt/gryt-ci-agent)
- `ufw_enabled`: Enable firewall (default: true)
- `docker_cleanup_enabled`: Enable cleanup (default: true)

See `group_vars/*.yml` for complete list.

## CI/CD Integration

### GitHub Actions
```yaml
- name: Deploy Agent
  run: |
    cd ansible
    echo "${{ secrets.VAULT_PASS }}" > .vault_pass
    ansible-playbook site.yml
```

### GitLab CI
```yaml
deploy:
  script:
    - cd ansible
    - echo "$VAULT_PASS" > .vault_pass
    - ansible-playbook site.yml
```

## What Gets Installed

- Ubuntu system updates
- Python 3.12
- Docker Engine (latest)
- Gryt CI Agent
- Systemd service
- UFW firewall
- Fail2ban
- Automatic updates
- Log rotation
- Docker cleanup cron

## Post-Deployment

1. Verify agent health: `curl http://agent-ip:8080/health`
2. Update main API with agent URL and API key
3. Test job execution with webhook
4. Set up monitoring/alerts
5. Schedule regular backups

## Support

- **Full docs**: [README.md](README.md)
- **Quick start**: [QUICKSTART.md](QUICKSTART.md)
- **Main guide**: [../DEPLOYMENT.md](../DEPLOYMENT.md)
- **Issues**: GitHub Issues

## Summary

This Ansible playbook provides:
- ✅ Production-ready deployment
- ✅ Security hardening
- ✅ Best practices
- ✅ Easy maintenance
- ✅ Scalable architecture
- ✅ Complete documentation

Deploy with confidence! 🚀
