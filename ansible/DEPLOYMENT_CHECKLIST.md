# Deployment Checklist

Use this checklist to ensure a smooth deployment.

## Pre-Deployment

### Environment Setup
- [ ] Ansible 2.15+ installed on control machine
- [ ] SSH access to target VM(s)
- [ ] SSH key added to target VM(s)
- [ ] VM meets requirements (2+ vCPU, 4GB+ RAM, 40GB+ disk)
- [ ] VM running Ubuntu 24.04 LTS (or 22.04)
- [ ] Network connectivity verified

### Configuration
- [ ] Clone/download Gryt CI Agent repository
- [ ] Navigate to `ansible/` directory
- [ ] Run `make install` to install Galaxy dependencies
- [ ] Edit `inventories/production/hosts.yml` with VM IP(s)
- [ ] Update `agent_git_repo` in `group_vars/gryt_agents.yml`
- [ ] Update `allowed_api_ips` in `group_vars/gryt_agents.yml`

### Secrets Management
- [ ] Generate API key: `make generate-key`
- [ ] Generate encryption key: `make generate-encryption-key`
- [ ] Create vault file: `make setup`
- [ ] Edit vault file with generated keys
- [ ] Encrypt vault: `make encrypt-vault`
- [ ] Store vault password securely

### Pre-Flight Checks
- [ ] Test connectivity: `make test`
- [ ] Check playbook syntax: `make check`
- [ ] Run dry-run: `make dry-run`
- [ ] Review output for errors

## Deployment

### Initial Deployment
- [ ] Run deployment: `make deploy`
- [ ] Monitor output for errors
- [ ] Note any warnings or failures
- [ ] Verify no failed tasks

### Verification
- [ ] Check agent health: `make health`
- [ ] Verify service status: `make status`
- [ ] Check logs for errors: `make logs`
- [ ] Test Docker access: `ssh gryt@agent-ip docker ps`
- [ ] Verify firewall rules: `ssh root@agent-ip ufw status`
- [ ] Test health endpoint manually: `curl http://agent-ip:8080/health`

## Post-Deployment

### Main API Configuration
- [ ] Update main API `.envrc` with agent URL
- [ ] Update main API `.envrc` with API key
- [ ] Restart main API service
- [ ] Verify main API can reach agent

### Testing
- [ ] Trigger test webhook
- [ ] Monitor agent logs during job execution
- [ ] Verify job completes successfully
- [ ] Check job artifacts/output
- [ ] Test failure scenarios

### Monitoring Setup
- [ ] Set up health check monitoring
- [ ] Configure log aggregation (optional)
- [ ] Set up alerting (optional)
- [ ] Configure resource monitoring
- [ ] Test alert mechanisms

### Security Verification
- [ ] Verify root login disabled: `ssh root@agent-ip` (should fail if configured)
- [ ] Verify firewall enabled: `ssh ubuntu@agent-ip ufw status`
- [ ] Verify API key file permissions: `ls -la /opt/gryt-ci-agent/.envrc` (should be 600)
- [ ] Verify service user: `ps aux | grep gryt-agent` (should run as gryt)
- [ ] Test unauthorized access (should be blocked)

### Documentation
- [ ] Document agent URLs
- [ ] Document API keys (in secure location)
- [ ] Note any custom configurations
- [ ] Update runbook with specific details
- [ ] Share access info with team (securely)

## Maintenance Setup

### Automation
- [ ] Verify automatic updates enabled
- [ ] Verify Docker cleanup cron scheduled: `crontab -l -u gryt`
- [ ] Test log rotation: `ls /etc/logrotate.d/gryt-agent`
- [ ] Schedule regular health checks

### Backups
- [ ] Run initial backup: `ansible-playbook playbooks/backup-config.yml`
- [ ] Verify backup created
- [ ] Store backup securely
- [ ] Schedule regular backups

### Disaster Recovery
- [ ] Document recovery procedure
- [ ] Test restore from backup
- [ ] Document rollback procedure
- [ ] Create emergency contacts list

## Multi-Agent Deployments

If deploying multiple agents:

- [ ] Add all agents to inventory
- [ ] Verify each agent accessible
- [ ] Deploy to all: `make deploy`
- [ ] Verify all agents healthy
- [ ] Update main API with all agent URLs (comma-separated)
- [ ] Test load distribution

## Troubleshooting Checks

If issues occur:

- [ ] Review Ansible output for errors
- [ ] Check SSH connectivity: `ssh root@agent-ip`
- [ ] Verify Python installed: `ssh root@agent-ip python3 --version`
- [ ] Check Docker status: `ssh root@agent-ip systemctl status docker`
- [ ] Review agent logs: `make logs`
- [ ] Check disk space: `ssh root@agent-ip df -h`
- [ ] Verify network connectivity
- [ ] Check firewall rules

## Final Verification

- [ ] Agent responding to health checks
- [ ] Jobs executing successfully
- [ ] Logs appearing correctly
- [ ] No error messages in logs
- [ ] Main API successfully communicating
- [ ] Monitoring alerts working
- [ ] Documentation complete
- [ ] Team notified of deployment

## Sign-Off

Deployment completed by: ________________
Date: ________________
Agent URL(s): ________________
Notes: ________________

---

## Quick Reference Commands

```bash
# Test connectivity
make test

# Deploy
make deploy

# Check health
make health

# View logs
make logs

# Check status
make status

# Update code
make update

# Backup config
ansible-playbook playbooks/backup-config.yml

# Rotate keys
ansible-playbook playbooks/rotate-keys.yml
```

## Emergency Contacts

Main API: ________________
Agent VMs: ________________
SSH Keys: ________________
Vault Password: ________________ (store securely!)

## Rollback Plan

If deployment fails:

1. Check error messages
2. Review logs: `make logs`
3. If needed, restore from backup
4. SSH to VM and manually fix issues
5. Re-run playbook: `make deploy`

## Next Steps

After successful deployment:

1. Monitor for 24 hours
2. Test with production workload
3. Adjust resources if needed
4. Scale horizontally if needed
5. Set up regular maintenance schedule

---

**Deployment Status**: [ ] Not Started | [ ] In Progress | [ ] Complete | [ ] Failed

**Notes:**

_____________________________________________
_____________________________________________
_____________________________________________
