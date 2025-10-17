# Tailscale Role

This role installs and configures Tailscale on Ubuntu 24.04 LTS for secure private networking between the Gryt CI agents and API.

## Requirements

- Ubuntu 24.04 LTS
- A Tailscale account and auth key

## Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `tailscale_enabled` | No | `false` | Enable Tailscale installation and configuration |
| `tailscale_authkey` | Yes* | - | Tailscale authentication key (required when enabling) |
| `tailscale_hostname` | No | `inventory_hostname` | Custom hostname for the Tailscale node |
| `tailscale_advertise_tags` | No | - | List of tags to advertise (e.g., `["tag:agent"]`) |
| `tailscale_accept_routes` | No | `false` | Accept subnet routes from other nodes |
| `tailscale_ssh` | No | `false` | Enable Tailscale SSH |

\* Required when `tailscale_enabled` is `true`

## Getting a Tailscale Auth Key

1. Go to https://login.tailscale.com/admin/settings/keys
2. Generate an auth key
3. Choose options:
   - **Reusable**: Yes (if deploying multiple agents)
   - **Ephemeral**: No (nodes should persist)
   - **Tags**: Optional, e.g., `tag:agent`

## Usage

### Basic Configuration

Tailscale is enabled by default in `group_vars/gryt_agents.yml` and reads the auth key from the encrypted vault.

1. **Add your Tailscale auth key to the vault:**
   ```bash
   cd ansible
   ansible-vault edit inventories/production/group_vars/gryt_agents/vault.yml
   ```
   
   Add the key:
   ```yaml
   vault_tailscale_authkey: "tskey-auth-xxxxx-your-key-here"
   ```

2. **Deploy normally:**
   ```bash
   make deploy
   ```

The `tailscale_authkey` variable in `group_vars/gryt_agents.yml` automatically references `vault_tailscale_authkey` from the vault.

### Advanced Configuration

In `host_vars/agent-01.yml`:

```yaml
tailscale_enabled: true
tailscale_hostname: gryt-agent-01
tailscale_advertise_tags:
  - tag:agent
  - tag:ci
tailscale_ssh: true
```

### Deploying with Tailscale

```bash
# Deploy with Tailscale enabled
cd ansible
make deploy EXTRA_ARGS="-e tailscale_enabled=true -e tailscale_authkey=tskey-auth-xxxxx"

# Or update only Tailscale
ansible-playbook site.yml --tags tailscale -e tailscale_enabled=true -e tailscale_authkey=tskey-auth-xxxxx
```

## Firewall Configuration

When Tailscale is enabled (`tailscale_enabled: true`), the security role automatically:
- Allows all traffic on the `tailscale0` interface
- Allows agent port traffic specifically from Tailscale network

This ensures your agent API is only accessible via Tailscale, not the public internet.

## After Deployment

1. Verify Tailscale is running:
   ```bash
   ssh user@agent-vm
   sudo tailscale status
   ```

2. Get the Tailscale IP:
   ```bash
   sudo tailscale ip -4
   ```

3. Test connectivity from your API server (after installing Tailscale there):
   ```bash
   # From API server (after Tailscale is installed)
   curl http://<agent-tailscale-ip>:8080/health
   ```

## Security Notes

- Store `tailscale_authkey` in Ansible Vault or pass via environment variables
- Never commit auth keys to version control
- Use ACL policies in Tailscale admin console to restrict access
- Consider using tags and ACL rules for fine-grained access control

## Tags

- `tailscale` - All Tailscale tasks
- `install` - Installation tasks only
- `config` - Configuration tasks only
- `service` - Service management tasks only
