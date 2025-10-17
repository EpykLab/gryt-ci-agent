# Docker Role

This Ansible role installs and configures Docker for the Gryt CI Agent.

## Features

- Installs Docker CE and related packages
- Configures Docker daemon with best practices
- Sets up user namespace remapping to fix permission issues
- Adds users to the docker group
- Configures automated cleanup
- Pulls the Gryt pipeline Docker image

## User Namespace Remapping

By default, this role enables **user namespace remapping** which solves the permission issues that occur when Docker creates files as root in mounted volumes.

### How It Works

When `docker_userns_remap_enabled` is `true` (default):
1. Creates a system user `dockremap` (configurable via `docker_userns_remap_user`)
2. Configures `/etc/subuid` and `/etc/subgid` to map container UIDs to host UIDs
3. Docker daemon runs with `userns-remap` enabled
4. Files created by containers are owned by the mapped user, not root
5. The gryt user can delete workspace files without permission errors

### Benefits

- **No permission issues**: Files created in Docker volumes are owned by mapped users
- **Better security**: Containers don't run as true root
- **Production-ready**: Industry best practice for Docker deployments
- **No sudo required**: The agent can clean up workspaces without special permissions

### Important Notes

**First-time Setup:**
- When enabling user namespace remapping, Docker will need to download images again
- Existing images are stored in a different location (`/var/lib/docker/<uid>.<gid>/`)
- This is a one-time overhead during initial setup

**Disabling:**
To disable user namespace remapping (not recommended for production):
```yaml
docker_userns_remap_enabled: false
```

## Variables

### Required Variables
None - all have sensible defaults

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `docker_cleanup_enabled` | `true` | Enable automated Docker cleanup |
| `docker_cleanup_schedule` | `"0 3 * * *"` | Cron schedule for cleanup (3 AM daily) |
| `docker_log_driver` | `"json-file"` | Docker logging driver |
| `docker_log_max_size` | `"10m"` | Maximum size of log files |
| `docker_log_max_file` | `"3"` | Number of log files to keep |
| `docker_storage_driver` | `"overlay2"` | Docker storage driver |
| `docker_userns_remap_enabled` | `true` | Enable user namespace remapping |
| `docker_userns_remap_user` | `"dockremap"` | User for namespace remapping |
| `docker_users` | `[]` | List of users to add to docker group |
| `gryt_docker_image` | `""` | Docker image to pre-pull |

## Dependencies

None

## Example Playbook

```yaml
- hosts: gryt_agents
  roles:
    - role: docker
      vars:
        docker_users:
          - gryt
        gryt_docker_image: "ghcr.io/epyklab/gryt/pipeline:latest"
```

## Tags

- `docker` - All Docker tasks
- `docker,config` - Docker daemon configuration
- `docker,user` - User management tasks
- `docker,test` - Docker installation test
- `docker,image` - Image pulling
- `docker,cleanup` - Cleanup configuration

## Testing

After applying this role, verify the setup:

```bash
# Check Docker service
sudo systemctl status docker

# Verify user namespace remapping
docker info | grep "userns"

# Test as gryt user
sudo -u gryt docker run --rm hello-world

# Check subuid/subgid configuration
cat /etc/subuid
cat /etc/subgid
```

## Troubleshooting

### Images need to be re-downloaded
This is expected when enabling user namespace remapping for the first time. Docker stores images in a different location when using user namespaces.

### Permission denied errors
Ensure the user is in the `docker` group and has logged out/in (or run `newgrp docker`).

### Container fails to start with user namespace errors
Check that `/etc/subuid` and `/etc/subgid` are properly configured with the range `100000:65536`.

## References

- [Docker User Namespace Documentation](https://docs.docker.com/engine/security/userns-remap/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
