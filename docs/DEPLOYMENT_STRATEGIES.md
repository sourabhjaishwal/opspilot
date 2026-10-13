# OpsPilot Deployment Strategies

OpsPilot has a **frontend** (the website people use) and a **backend** (the API that handles data and requests). They can be hosted together or separately. These options explain what each setup does, why it exists, and when it makes sense.

**Current project setup:** Option B is implemented for the AWS backend. The frontend is deployed separately. Option A describes a simple managed-hosting choice; Option C hosts the frontend on AWS; Option D is an ECS alternative that is not configured in this repository.

## Option A — Vercel frontend + Render backend

**What it is:** Vercel hosts the website and Render hosts the API. Both are managed hosting services.

**Why it was chosen:** It provides a straightforward public demo without requiring the developer to manage a server.

**How it works:**
1. Connect the frontend project to Vercel and the backend to Render.
2. Set the frontend's `VITE_API_BASE_URL` to the Render API address.
3. Set the backend's `ALLOWED_ORIGINS` to the Vercel website address.
4. Build the frontend with `npm ci` and `npm run build` when deploying manually; Vercel can run the build when connected to the repository.

**Advantages and limitations:** Quick to set up and little server maintenance. Hosting limits, pricing, and configuration are managed separately by each provider, and this route teaches fewer AWS operations.

**When to use it:** Choose this for an easy-to-share demo or portfolio site when low maintenance matters more than AWS practice. Verify that any existing hosted services are still active before sharing them.

## Option B — Vercel frontend + Docker backend on AWS EC2

**What it is:** Vercel hosts the website; an AWS EC2 virtual machine runs the backend in Docker. Amazon ECR stores the Docker image, and Ansible deploys it to EC2.

**Why it was chosen:** It is the project's current AWS learning path. It demonstrates Docker, ECR, IAM/OIDC, GitHub Actions, and Ansible while avoiding the extra work of moving the frontend to AWS.

**How it works:**
1. Build and test the backend image locally:
   ```bash
   docker build -t opspilot:local .
   ```
2. Configure the AWS region, ECR repository, GitHub OIDC role, EC2 instance role, EC2 host, SSH key, and application secrets.
3. In GitHub Actions, run **OpsPilot AWS Deployment** manually. The workflow runs backend tests, pushes a commit-tagged image to ECR, connects to EC2, and runs Ansible.
4. Set Vercel's `VITE_API_BASE_URL` to the EC2 API address and the backend's `ALLOWED_ORIGINS` to the Vercel website address.
5. Check the deployment at `http://YOUR_EC2_HOST:8000/health`.

**Advantages and limitations:** Gives practical AWS and deployment experience with a relatively small architecture. The developer must secure and maintain EC2; the API needs appropriate network access and HTTPS for production use. EC2 storage, ECR, and public IP resources may still cost money when the instance is stopped. The SQLite volume persists across container replacements but is not a backup.

**When to use it:** Choose this to learn AWS deployment while keeping the frontend simple. This is the best match for the deployment currently implemented in the repository.

## Option C — S3 + CloudFront frontend + EC2 backend

**What it is:** Amazon S3 stores the built website, CloudFront delivers it to visitors, and EC2 runs the backend API.

**Why it was chosen:** It extends Option B to include AWS static website hosting and content delivery.

**How it works:**
1. Set `VITE_API_BASE_URL` in `frontend/.env.production` to the backend API address.
2. Build the website and copy its static files to the S3 website bucket:
   ```bash
   cd frontend
   npm ci
   npm run build
   aws s3 sync dist/ s3://YOUR_BUCKET
   ```
3. Configure CloudFront to serve the bucket and invalidate its cache after an update:
   ```bash
   aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
   ```
4. Set the backend's `ALLOWED_ORIGINS` to the CloudFront website address and configure HTTPS and DNS as needed.

**Advantages and limitations:** Keeps the frontend and CDN on AWS and provides control over delivery. It requires extra AWS permissions, HTTPS/DNS, frontend build configuration, and CORS setup. The backend still needs its own hosting and security configuration.

**When to use it:** Choose this when learning AWS frontend hosting is an explicit goal. Otherwise, keep the frontend on Vercel and use Option B.

## Option D — AWS ECS backend

**What it is:** Amazon ECS manages backend containers as a service. It can run containers on EC2 instances or on AWS Fargate, where AWS manages the compute hosts. The frontend still needs a separate host, such as Vercel or S3/CloudFront.

**Why it was chosen:** ECS is a way to learn managed container orchestration and have AWS maintain the desired number of running tasks.

**How it works:**
1. Build and test the backend Docker image, then push a version-tagged image to ECR. The local build command is:
   ```bash
   docker build -t opspilot:local .
   ```
2. Configure IAM roles for GitHub image publishing and ECS task execution. ECS on EC2 also needs an instance role.
3. Create an ECS cluster, task definition, and service. Configure networking, application secrets, health checks, and logs.
4. Update the ECS task definition to use the new ECR image, then deploy the service through the AWS Console, AWS CLI, or a configured workflow.
5. Set the frontend API URL and backend CORS allowlist, then verify the API health endpoint.

**Advantages and limitations:** ECS manages container scheduling and recovery; Fargate also removes the need to maintain EC2 hosts. It requires more AWS configuration than Option B. ECS is not configured in this repository, and the current SQLite-on-one-host setup is not suitable for scaling across multiple tasks without changing the data storage design.

**When to use it:** Choose this for a deliberate container-orchestration learning project or when the application needs ECS-managed tasks. Do not use ECS and Ansible to independently manage the same backend container.

## Current deployment at a glance

The checked-in AWS workflow is manually started with **workflow_dispatch**; pushes do not automatically deploy the AWS backend. It tests the backend, builds a Linux AMD64 image, pushes it to ECR, and uses SSH plus Ansible to deploy it to EC2. The frontend is not built or hosted by this AWS workflow. A successful workflow does not by itself confirm that the public application or AWS resources are currently available.

For detailed prerequisites, configuration, rollback, and troubleshooting, see [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md).
