# Ansible Deployment for OpsPilot

This directory contains Ansible playbooks and configuration for deploying OpsPilot to AWS EC2.

## Files

- **`inventory.ini`** - Ansible inventory file (configure with your EC2 IP and SSH key)
- **`deploy.yml`** - Main deployment playbook
- **`ansible.cfg`** - Ansible configuration

## Prerequisites

1. Ansible installed locally: `pip install ansible docker`
2. AWS EC2 instance running Ubuntu 22.04 LTS
3. SSH key with access to EC2 instance
4. Docker image built: `docker build -t opspilot:latest .`

## Configuration

### 1. Update Inventory

Edit `inventory.ini` and replace placeholders:

```ini
[opspilot]
opspilot-ec2 ansible_host=YOUR_EC2_PUBLIC_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/YOUR_KEY.pem

[opspilot:vars]
ansible_python_interpreter=/usr/bin/python3
```

### 2. Set Environment Variables

Required environment variables (used by `deploy.yml`):

```bash
export JWT_SECRET="your-jwt-secret-min-32-chars"
export GEMINI_API_KEY="your-gemini-api-key"
export ALLOWED_ORIGINS="https://your-frontend.com"
export FRONTEND_URL="https://your-frontend.com"
```

Optional variables (have defaults):

```bash
export APP_NAME="OpsPilot"
export ENVIRONMENT="production"
export LOG_LEVEL="INFO"
export ACCESS_TOKEN_EXPIRE_MINUTES="60"
export GEMINI_MODEL="gemini-2.0-flash-exp"
```

## Usage

### Test Connection

```bash
ansible opspilot -i inventory.ini -m ping
```

Expected output:
```
opspilot-ec2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

### Transfer Docker Image to EC2

```bash
# Save Docker image
docker save opspilot:latest | gzip > /tmp/opspilot-latest.tar.gz

# Transfer to EC2
scp -i ~/.ssh/YOUR_KEY.pem /tmp/opspilot-latest.tar.gz ubuntu@YOUR_EC2_IP:/tmp/

# Load on EC2
ssh -i ~/.ssh/YOUR_KEY.pem ubuntu@YOUR_EC2_IP "gunzip -c /tmp/opspilot-latest.tar.gz | docker load"
```

### Deploy

```bash
ansible-playbook -i inventory.ini deploy.yml
```

### Verify Deployment

```bash
curl http://YOUR_EC2_IP:8000/health
```

Expected response:
```json
{"status":"healthy"}
```

## What the Playbook Does

1. Installs Docker on EC2 (if not present)
2. Creates persistent Docker volume `opspilot-data`
3. Stops old container (if running)
4. Starts new container with:
   - Port mapping: 8000:8000
   - Volume mount: `opspilot-data:/app/data`
   - Environment variables from your exports
   - Restart policy: `unless-stopped`
5. Waits for health check to pass
6. Reports success

## Troubleshooting

### Connection Issues

```bash
# Test SSH access
ssh -i ~/.ssh/YOUR_KEY.pem ubuntu@YOUR_EC2_IP

# Verify EC2 security group allows:
# - Port 22 (SSH) from your IP
# - Port 8000 (HTTP) from 0.0.0.0/0
```

### Playbook Errors

Run with verbose output:
```bash
ansible-playbook -i inventory.ini deploy.yml -vvv
```

### Docker Issues on EC2

```bash
# SSH into EC2
ssh -i ~/.ssh/YOUR_KEY.pem ubuntu@YOUR_EC2_IP

# Check Docker status
docker ps
docker logs opspilot-api

# Verify image loaded
docker images opspilot
```

## Notes

- The playbook is idempotent—safe to run multiple times
- SQLite data persists in the Docker volume across deployments
- Old containers are removed, but the volume remains intact
- Environment variables are passed from your shell to Ansible to Docker

## GitHub Actions Integration

In CI/CD, GitHub Actions:
1. Builds the Docker image
2. Transfers it to EC2 via SCP
3. Runs this Ansible playbook with secrets from GitHub Secrets
4. Verifies the health endpoint

See `.github/workflows/deploy.yml` for the complete pipeline.
