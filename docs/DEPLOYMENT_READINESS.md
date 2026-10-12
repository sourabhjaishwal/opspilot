# Deployment readiness

**Reviewed:** October 12, 2026

This document combines the deployment status and final verification checklist. It replaces the older deployment-ready and final-checklist reports, which recorded point-in-time results and repeated one another.

## Verified in the repository

- Backend: 60 tests passed locally; see [backend test results](./BACKEND_TEST_RESULTS.md).
- Frontend: production build and ESLint passed locally; see [frontend build results](./FRONTEND_BUILD_RESULTS.md).
- CI workflow: configured to run backend tests, frontend build, and Docker image build on pushes to `test` and `main`, and pull requests targeting `main`.
- AWS workflow: manually triggered with `workflow_dispatch`, authenticates to AWS through GitHub OIDC, pushes SHA and `latest` image tags to ECR, and deploys the SHA tag to EC2 with Ansible.
- Database seed behavior: six example services and 12 incidents are defined; the tests cover fresh seeding and idempotent reruns. See [database results](./DATABASE_RESULTS.md).
- Docker: repository-root Dockerfile packages the backend API only, uses a non-root user, exposes port 8000, and mounts persistent data at `/app/data`.

## Deployment checklist

Before deploying:

- [ ] Confirm EC2 is running and reachable at the host configured in GitHub.
- [ ] Confirm GitHub's `aws-demo` environment has the required variables and secrets.
- [ ] Confirm the OIDC role trust policy matches the GitHub repository/environment and has scoped ECR push permissions.
- [ ] Confirm the EC2 instance profile has ECR pull permissions.
- [ ] Confirm ECR repository and region values are correct and a successful workflow can push the image.
- [ ] Confirm the EC2 security group permits SSH only from trusted sources and allows API traffic only as intended.
- [ ] Confirm the frontend production build uses the intended backend URL and the backend CORS allowlist includes the frontend origin.
- [ ] After deployment, verify the workflow, deployed SHA, container status, and `GET /health`.
- [ ] Back up the persistent SQLite volume before risky changes; verify data persistence after container recreation if that behavior is a release requirement.

## External status not verified here

This review did not inspect live AWS resources, GitHub environment settings, DNS/hosting state, or the deployed application. Therefore it does not confirm that OIDC role assumption, ECR push/pull permissions, SSH access, EC2 deployment, public frontend-to-API calls, HTTPS, or database persistence in a live environment currently work.

Follow the [AWS deployment guide](./AWS_DEPLOYMENT.md) for the deployment procedure and configuration details. Do not describe the live AWS deployment as production-ready or end-to-end verified until the checklist has been completed against the target environment.
