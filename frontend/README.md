# Frontend

OpsPilot's frontend is a React 19 single-page application built with Vite and SCSS. It provides account registration and login, a service-health dashboard, incident creation and management, incident filtering/pagination, and AI incident analysis.

## Run locally

Install a Vite 8-compatible Node.js version (20.19+ or 22.12+), then from this directory run:

```bash
npm ci
npm run dev
```

Vite serves the frontend at `http://localhost:5173`. Run the FastAPI backend separately on port 8000 and configure its CORS allowlist for the frontend origin. The API client defaults to `http://localhost:8000`.

## Configure the API URL

Set `VITE_API_BASE_URL` to the backend origin the browser should call. Vite embeds `VITE_*` values in the generated static files at build time, so change the value and rebuild when the backend URL changes.

For a production build, create or update `.env.production` in this directory:

```env
VITE_API_BASE_URL=https://your-api.example.com
```

Use the actual deployed API origin, not `localhost`. This value is public configuration; do not put credentials, API keys, or other secrets in frontend environment variables or source code. The backend must allow the deployed frontend origin through `ALLOWED_ORIGINS`.

## Checks and preview

```bash
npm run lint
npm run build
npm run preview
```

The production build is written to `dist/`. The Docker image at the repository root packages the backend only; host the frontend build separately and configure its API URL before building. See the [AWS deployment guide](../docs/AWS_DEPLOYMENT.md) for the current backend deployment path.
