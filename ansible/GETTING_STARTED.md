# Getting Started with Ansible Deployment

## Overview

This Ansible playbook automates the complete deployment of Gryt CI Agent on Ubuntu 24.04 LTS VMs.

## What You'll Get

After deployment, you'll have:
- ✅ Fully configured Ubuntu 24.04 LTS VM
- ✅ Python 3.12 installed
- ✅ Docker Engine installed and configured
- ✅ Gryt CI Agent installed and running
- ✅ Systemd service with auto-restart
- ✅ UFW firewall configured
- ✅ SSH hardened
- ✅ Automatic security updates
- ✅ Docker cleanup automation
- ✅ Log rotation

## 5-Minute Quick Start

### 1. Install Ansible
```bash
# Ubuntu/Debian
sudo apt install ansible

# macOS
brew install ansible
```

### 2. Setup
```bash
cd ansible
make install    # Install dependencies
make setup      # Create vault file
```

### 3. Configure
```bash
# Edit inventory with your VM IP
nano inventories/production/hosts.yml

# Generate and set secrets
make generate-key  # Copy this
nano inventories/production/group_vars/gryt_agents/vault.yml
make encrypt-vault

# Update agent settings
nano group_vars/gryt_agents.yml
```

### 4. Deploy
```bash
make test     # Test connection
make deploy   # Deploy!
```

### 5. Verify
```bash
make health   # Check health
make logs     # View logs
```

## Next Steps

- See [QUICKSTART.md](QUICKSTART.md) for detailed setup
- See [README.md](README.md) for complete documentation
- See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for deployment checklist
- See [ANSIBLE_DEPLOYMENT.md](ANSIBLE_DEPLOYMENT.md) for technical details

## Common Commands

```bash
make help           # Show all commands
make deploy         # Deploy to all agents
make update         # Update agent code
make restart        # Restart agent service
make logs           # View logs
make health         # Check health
make docker-cleanup # Clean up Docker
```

## Need Help?

1. Check [README.md](README.md) for full documentation
2. Review error messages in Ansible output
3. Check agent logs: `make logs`
4. Verify connectivity: `make test`

## File Overview

| File | Purpose |
|------|---------|
| `site.yml` | Main playbook |
| `ansible.cfg` | Ansible configuration |
| `Makefile` | Helper commands |
| `README.md` | Complete documentation |
| `QUICKSTART.md` | Quick setup guide |
| `DEPLOYMENT_CHECKLIST.md` | Deployment checklist |
| `inventories/production/hosts.yml` | Server inventory |
| `group_vars/gryt_agents.yml` | Configuration variables |
| `group_vars/gryt_agents/vault.yml` | Encrypted secrets |

---

**Ready to deploy?** Start with [QUICKSTART.md](QUICKSTART.md)!
