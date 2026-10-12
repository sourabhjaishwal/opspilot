# AWS Deployment

**Reviewed:** October 12, 2026

OpsPilot runs as a Docker container on one Ubuntu EC2 instance. GitHub Actions builds the image, pushes it to Amazon ECR, and runs the Ansible playbook over SSH. The EC2 instance pulls the exact commit image using its instance role. SQLite data is stored in a named Docker volume.

```text
GitHub Actions --OIDC--> Amazon ECR --EC2 instance role--> EC2
       |                                             |
       +---------------- SSH / Ansible --------------+
                                                     |
                                      Docker + opspilot-data volume
```

## Prerequisites

- An Ubuntu 22.04 EC2 instance with a public DNS name or IP.
- An EC2 key pair and inbound SSH access (TCP 22 restricted to trusted addresses).
- An EC2 instance profile with permission to pull from the OpsPilot ECR repository.
- An ECR repository for the OpsPilot image.
- A GitHub Actions OIDC provider and role with permission to push to that ECR repository.
- A GitHub environment named `aws-demo`, matching the workflow's dispatch option.

Allow inbound TCP 8000 only from intended clients, or put the app behind a reverse proxy/load balancer that provides HTTPS. Do not expose SSH broadly.

## AWS identity and permissions

Configure the GitHub Actions OIDC role trust policy to allow only this repository's `aws-demo` GitHub environment. Its subject condition should be:

```text
repo:sourabhjaishwal/opspilot:environment:aws-demo
```

Grant that role ECR push permissions scoped to the OpsPilot repository (`ecr:BatchCheckLayerAvailability`, `ecr:CompleteLayerUpload`, `ecr:InitiateLayerUpload`, `ecr:PutImage`, `ecr:UploadLayerPart`, `ecr:BatchGetImage`) and `ecr:GetAuthorizationToken` on `*`.

Attach a separate pull-only policy to the EC2 instance profile: `ecr:BatchCheckLayerAvailability`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` scoped to the repository, and `ecr:GetAuthorizationToken` on `*`. Do not put AWS access keys on the instance or in GitHub.

## GitHub configuration

Add these repository or `aws-demo` environment variables under **Settings → Secrets and variables → Actions → Variables**:

| Variable | Purpose |
| --- | --- |
| `AWS_ROLE_ARN` | ARN of the GitHub Actions OIDC role |
| `AWS_REGION` | Region containing ECR and EC2 |
| `ECR_REGISTRY` | ECR registry hostname, without a scheme |
| `ECR_REPOSITORY` | ECR repository name |

Add these secrets under **Settings → Secrets and variables → Actions → Secrets** (prefer environment secrets scoped to `aws-demo`):

| Secret | Purpose |
| --- | --- |
| `EC2_HOST` | EC2 public DNS name or IP |
| `EC2_SSH_PRIVATE_KEY` | Private key matching the EC2 key pair |
| `JWT_SECRET` | Random, high-entropy JWT signing secret |
| `ALLOWED_ORIGINS` | Comma-separated frontend origins allowed by CORS |
| `FRONTEND_URL` | Public frontend URL |
| `GEMINI_API_KEY` | Google Gemini API key |

`APP_NAME` and `GEMINI_MODEL` can also be supplied as secrets; the playbook has defaults for them. Never commit real credentials or environment files.

Generate a JWT secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deploy with GitHub Actions

1. Confirm the `aws-demo` environment has access to the required secrets and variables.
2. In **Actions**, select **OpsPilot AWS Deployment**, choose **Run workflow**, and run it for the intended branch/commit.
3. The workflow runs backend tests, builds a `linux/amd64` image, pushes both the commit SHA and `latest` tags to ECR, checks SSH connectivity, and deploys the SHA-tagged image with Ansible.
4. Confirm the workflow succeeds, then verify the endpoint:

```bash
curl http://EC2_HOST:8000/health
```

The expected response is `{"status":"healthy"}`. The AWS deployment workflow is manually triggered; it runs backend tests and builds/pushes the backend image, but does not build or host the frontend. The separate CI workflow runs backend tests, the frontend build, and a Docker build on pushes to `test` and `main` and on pull requests to `main`.

## Manual Ansible deployment

Install Ansible and its Docker collection on the control machine:

```bash
python -m pip install ansible docker
ansible-galaxy collection install community.docker
```

Set `ansible_host`, `ansible_user` (normally `ubuntu`), and the private-key path in `ansible/inventory.ini`. Ensure the image already exists in ECR and that the EC2 instance profile can pull it. Configure the values consumed by the playbook:

```bash
export AWS_REGION="your-region"
export ECR_REGISTRY="your-account.dkr.ecr.your-region.amazonaws.com"
export ECR_REPOSITORY="opspilot"
export IMAGE_TAG="commit-sha"
export JWT_SECRET="your-random-secret"
export ALLOWED_ORIGINS="https://your-frontend.example"
export FRONTEND_URL="https://your-frontend.example"
export GEMINI_API_KEY="your-gemini-api-key"
```

The selected image tag must already exist in ECR. Deploy it with:

```bash
cd ansible
ansible-playbook -i inventory.ini deploy.yml
```

The playbook installs Docker and AWS CLI on EC2, creates `opspilot-data`, authenticates to ECR with the instance profile, writes application settings to `/opt/opspilot/.env`, replaces the container, and waits for container and HTTP health checks. Supply `APP_NAME`, `ENVIRONMENT`, `LOG_LEVEL`, `DATABASE_URL`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `GEMINI_MODEL` only when overriding the playbook defaults.

## Data, rollback, and diagnostics

- SQLite is stored at `/app/data/opspilot.db` inside the container and persisted in Docker volume `opspilot-data`. Replacing the container does not remove the volume.
- Back up the database volume before risky changes; a container rollback does not roll back database changes.
- To roll back, set `IMAGE_TAG` to a previously pushed commit SHA and rerun deployment. With Ansible, set `IMAGE_TAG` to that SHA. For GitHub Actions, run the workflow from a branch/ref that resolves to the desired commit.
- Check container status and logs on EC2 with `sudo docker ps -a` and `sudo docker logs opspilot`.
- The playbook writes the production environment file with root-only permissions at `/opt/opspilot/.env`.
