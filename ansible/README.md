# Ansible deployment

This directory deploys the OpsPilot backend container from Amazon ECR to an Ubuntu EC2 instance. Ansible installs Docker and AWS CLI on the host, authenticates to ECR through the EC2 instance profile, writes runtime configuration, recreates the container, and checks its health. SQLite data is kept in the `opspilot-data` Docker volume.

For a beginner-friendly walkthrough of AWS IAM, GitHub Actions, required settings, deployment, and rollback, see the [AWS deployment guide](../docs/AWS_DEPLOYMENT.md).

## Prerequisites

- An Ubuntu EC2 instance with SSH access and an instance profile that can pull the OpsPilot image from ECR.
- An ECR image tag that already exists and is accessible to that instance.
- Ansible and the `community.docker` collection on the control machine.
- Python Docker SDK on the control machine and on EC2 (the playbook installs the EC2-side SDK in a virtual environment).

Install the control-machine dependencies:

```bash
python -m pip install ansible docker
ansible-galaxy collection install community.docker
```

## Configure the inventory

Edit `inventory.ini` and set the current EC2 address and SSH private-key path. Keep private keys outside the repository.

```ini
[opspilot]
opspilot-ec2 ansible_host=YOUR_EC2_PUBLIC_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/YOUR_KEY.pem

[opspilot:vars]
ansible_python_interpreter=/usr/bin/python3
```

Test that Ansible can connect:

```bash
ansible opspilot -i inventory.ini -m ping
```

## Set deployment configuration

The playbook reads these environment variables on the control machine:

| Variable | Required | Default/notes |
| --- | --- | --- |
| `AWS_REGION` | No | Playbook default is `ap-south-1`; use the region containing ECR. |
| `ECR_REGISTRY` | No | Defaults to the registry configured in the playbook. |
| `ECR_REPOSITORY` | No | Defaults to `opspilot`. |
| `IMAGE_TAG` | No | Defaults to `latest`; prefer a commit SHA for reproducible deploys. |
| `JWT_SECRET` | Yes | Set a strong random value. |
| `ALLOWED_ORIGINS` | Yes | Exact frontend origin(s), comma-separated if multiple. |
| `FRONTEND_URL` | Yes | Public frontend URL. |
| `GEMINI_API_KEY` | For AI analysis | Without it, AI analysis cannot be used. |
| `APP_NAME`, `ENVIRONMENT`, `DATABASE_URL`, `LOG_LEVEL`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `GEMINI_MODEL` | No | Playbook provides defaults; set to override. |

Do not commit secrets or paste them into logs. In PowerShell, set variables with `$env:NAME = "value"`; in Bash, use `export NAME="value"`.

The requested `IMAGE_TAG` must already be pushed to ECR. The EC2 instance—not the Ansible controller—authenticates to ECR for the image pull, using its instance profile.

## Deploy

From this directory, run:

```bash
ansible-galaxy collection install community.docker
ansible-playbook -i inventory.ini deploy.yml
```

The playbook creates the `opspilot-data` volume if needed, writes application configuration to `/opt/opspilot/.env` with root-only permissions, deploys container `opspilot` on port 8000, and waits for Docker and HTTP health checks.

Verify the application from a machine that can reach the EC2 host:

```bash
curl http://YOUR_EC2_PUBLIC_IP:8000/health
```

Expected response:

```json
{"status":"healthy"}
```

## Troubleshooting

On EC2, inspect the deployed container with:

```bash
sudo docker ps -a
sudo docker logs opspilot
```

If SSH fails, confirm that the host address and key are current and that the EC2 security group allows TCP 22 from the control machine. If image pulling fails, check the EC2 instance profile, ECR region/repository, and requested tag. Restrict public access to port 8000 to the required clients, or place the API behind an HTTPS reverse proxy/load balancer.

Re-deploying replaces the container but keeps the named data volume. Back up the SQLite database before risky changes; restoring an earlier image does not revert database changes.