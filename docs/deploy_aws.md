# AWS Deployment

This guide deploys the existing OpsPilot Docker image to an AWS EC2 host with Ansible.

## Prerequisites

- An AWS EC2 instance running a supported Linux distribution, such as Ubuntu 22.04.
- Docker installed and enabled on the EC2 instance.
- An EC2 security group allowing:
  - TCP port 22 from the administrator's IP range.
  - TCP port 8000 from the intended API client IP range.
- SSH access to the instance using a private key.
- Ansible installed on the deployment machine.
- Python 3 available on the EC2 instance.
- The `opspilot:latest` image available on the EC2 host, or the OpsPilot repository available there so the deployment role can build it.

Do not commit private SSH keys or real host addresses to the repository.

## Configure the inventory

Copy the placeholders in `docs/ansible/inventory/aws_hosts.yml` to the real deployment values:

```yaml
all:
  children:
    aws_ec2:
      hosts:
        opspilot_production:
          ansible_host: 203.0.113.10
          ansible_user: ubuntu
          ansible_ssh_private_key_file: "~/.ssh/opspilot-aws.pem"
```

Use `ec2-user` instead of `ubuntu` for distributions that use that account.

Review `docs/ansible/vars/production.yml` before deployment. It defines the production environment, log level, port, AWS region, image name, and persistent volume name.

## Prepare the image

The deployment role uses the existing `opspilot:latest` image when it is present. If the image is missing, it builds from the configured project path on the target host. For a remote EC2 deployment, either build the image on the host:

```bash
docker build -t opspilot:latest .
```

or load/pull `opspilot:latest` from the image registry used by your deployment process.

## Run the deployment

From the repository root:

```bash
cd docs/ansible
ansible-playbook -i inventory/aws_hosts.yml deploy_aws.yml
```

The playbook:

1. Checks Python, Docker, and outbound network access.
2. Ensures the Docker service is running.
3. Creates the `opspilot-data` volume if needed.
4. Builds the image if it is missing.
5. Starts `opspilot-api` with port `8000:8000` and the persistent `/app/data` volume.
6. Verifies the public health endpoint returns HTTP 200.

Use verbose output when troubleshooting:

```bash
ansible-playbook -i inventory/aws_hosts.yml deploy_aws.yml -vv
```

## Verify the deployment

From the deployment machine:

```bash
curl http://203.0.113.10:8000/health
```

Expected response:

```json
{ "status": "healthy" }
```

On the EC2 host:

```bash
ssh -i ~/.ssh/opspilot-aws.pem ubuntu@203.0.113.10
sudo docker ps --filter name=opspilot-api
sudo docker inspect opspilot-api --format '{{.State.Health.Status}}'
sudo docker volume inspect opspilot-data
sudo docker logs --tail 100 opspilot-api
```

The container should be running, its health status should become `healthy`, and the `opspilot-data` volume should exist.

## Rollback

Stop and remove the current container while preserving the database volume:

```bash
sudo docker stop opspilot-api
sudo docker rm opspilot-api
```

Start a previously validated image tag with the same volume:

```bash
sudo docker run -d \
  --name opspilot-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v opspilot-data:/app/data \
  -e LOG_LEVEL=INFO \
  -e ENVIRONMENT=production \
  opspilot:<previous-tag>
```

Verify the rollback:

```bash
curl http://203.0.113.10:8000/health
sudo docker ps --filter name=opspilot-api
```

Do not remove `opspilot-data` during rollback unless the database data is intentionally being deleted.
