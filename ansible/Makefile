# Makefile for Gryt CI Agent Ansible deployment

.PHONY: help install setup deploy check test update clean lint

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install Ansible dependencies
	ansible-galaxy install -r requirements.yml

setup: ## Initial setup (create vault file)
	@echo "Creating vault file from example..."
	@mkdir -p inventories/production/group_vars/gryt_agents
	@cp inventories/production/group_vars/gryt_agents/vault.yml.example \
	    inventories/production/group_vars/gryt_agents/vault.yml 2>/dev/null || true
	@echo "Edit vault.yml and then run: make encrypt-vault"

encrypt-vault: ## Encrypt vault file
	ansible-vault encrypt inventories/production/group_vars/gryt_agents/vault.yml

edit-vault: ## Edit encrypted vault file
	ansible-vault edit inventories/production/group_vars/gryt_agents/vault.yml

view-vault: ## View encrypted vault file
	ansible-vault view inventories/production/group_vars/gryt_agents/vault.yml

check: ## Check playbook syntax
	ansible-playbook site.yml --syntax-check

lint: ## Run ansible-lint
	ansible-lint site.yml

test: ## Test connection to hosts
	ansible gryt_agents -m ping

list-hosts: ## List all hosts
	ansible-playbook site.yml --list-hosts

list-tasks: ## List all tasks
	ansible-playbook site.yml --list-tasks

dry-run: ## Dry run (check mode)
	ansible-playbook site.yml --check

deploy: ## Deploy to all agents
	ansible-playbook site.yml

deploy-staging: ## Deploy to staging
	ansible-playbook site.yml -i inventories/staging/hosts.yml

deploy-one: ## Deploy to single host (usage: make deploy-one HOST=agent-01)
	ansible-playbook site.yml --limit $(HOST)

update: ## Update agent code only
	ansible-playbook site.yml --tags agent,install

restart: ## Restart agent service
	ansible gryt_agents -b -m systemd -a "name=gryt-agent state=restarted"

status: ## Check agent service status
	ansible gryt_agents -b -m command -a "systemctl status gryt-agent"

logs: ## View agent logs
	ansible gryt_agents -b -m command -a "journalctl -u gryt-agent -n 50 --no-pager"

health: ## Check agent health
	ansible gryt_agents -m uri -a "url=http://localhost:8080/health"

docker-cleanup: ## Run Docker cleanup on all agents
	ansible gryt_agents -b -u gryt -m command -a "docker system prune -af --volumes"

clean: ## Clean temporary files
	rm -rf retry/ ansible.log *.retry
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

generate-key: ## Generate API key
	@echo "Generated API key:"
	@openssl rand -hex 32

generate-encryption-key: ## Generate encryption key
	@echo "Generated encryption key:"
	@openssl rand -base64 32
