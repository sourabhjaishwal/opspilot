# OpsPilot

OpsPilot is a small incident and service-health API. It provides persistent service management and incident tracking with SQLite.

## Current scope

The backend currently supports service CRUD, service status updates, incident CRUD, incident filtering, deterministic pagination, validation, and centralized domain error responses.

Authentication, deployment automation, Ansible, AWS, AI-assisted analysis, RAG, and frontend functionality are planned or out of scope for this stage. A production-style Docker image is available for local container testing.

## Technology stack

- Python 3.11+
- FastAPI and Uvicorn
- SQLAlchemy with SQLite
- Pydantic and pydantic-settings
- pytest and httpx

## Repository structure

```text
backend/
  app/                    FastAPI application, models, routes, schemas, services
  tests/                  API and service-layer tests using isolated SQLite
frontend/                 Vite + React operations dashboard
docs/                     Deployment and operations documentation
docs/ansible/             Paused Ansible playbooks and Molecule scenarios
```

## Local setup

Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` to customize local settings. The default database is `sqlite:///./opspilot.db`.

## Start the application

```bash
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Run with Docker

Build the image using the canonical `Dockerfile`:

```bash
docker build -t opspilot:0.2 .
```

Run the API with SQLite data persisted in a named volume. The volume is mounted at `/app/data`; application files remain part of the image:

```powershell
docker run -d `
  --name opspilot-api `
  -p 8000:8000 `
  -v opspilot-data:/app/data `
  opspilot:0.2
```

The container exposes port `8000`, runs as a non-root user, and includes a Docker health check for `/health`.

## API endpoints

### Health and root

- `GET /` - application name and version
- `GET /health` - returns `{"status": "healthy"}`

### Services

Services are persisted in SQLite. Service status must be `healthy`, `degraded`, or `down`.

- `POST /services` - create a service; returns `201`
- `GET /services` - list services, ordered by name
- `GET /services/{service_name}` - retrieve a service
- `PATCH /services/{service_name}` - update service name, description, or status
- `PATCH /services/{service_name}/status` - update status and record `last_checked_at`

Service names are unique. A duplicate name returns `409` with `{"detail": "Service name already exists"}`. A missing service returns `404` with `{"detail": "Service not found"}`.

Example service creation request:

```json
{
  "name": "payment-service",
  "description": "Handles payment processing",
  "status": "healthy"
}
```

### Incidents

Incidents must reference a registered service. Severity must be `low`, `medium`, `high`, or `critical`. Incident status must be `open`, `investigating`, or `resolved`.

- `POST /incidents` - create an incident; returns `201`
- `GET /incidents` - list incidents with filtering and pagination
- `GET /incidents/{incident_id}` - retrieve an incident
- `PATCH /incidents/{incident_id}` - update incident status

Creating an incident for an unknown service returns `404` with `{"detail": "Service not found"}`.

Example incident creation request:

```json
{
  "service": "payment-service",
  "severity": "high",
  "title": "Health endpoint returning 503",
  "description": "The payment service health endpoint is returning HTTP 503."
}
```

### Incident listing

`GET /incidents` supports these optional query parameters:

- `service` - exact service name filter
- `severity` - exact severity filter
- `status` - exact incident status filter
- `page` - page number, minimum `1`, default `1`
- `page_size` - items per page, minimum `1`, maximum `100`, default `20`

Multiple filters are combined using `AND`. Results are ordered by `created_at DESC`, then `id DESC` for deterministic pagination.

The response has this shape:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

`total` is the number of matching incidents before pagination.

## Error responses

Domain exceptions are translated centrally into consistent HTTP responses:

- `404` - `{"detail": "Incident not found"}`
- `404` - `{"detail": "Service not found"}`
- `409` - `{"detail": "Service name already exists"}`
- `422` - request validation error, such as an unsupported status or invalid pagination value

## Architecture

- Routes handle HTTP input, response schemas, dependency injection, and domain-exception propagation.
- Service modules contain database queries, persistence, validation, filtering, pagination, and other business logic.
- Domain exceptions are defined in `backend/app/exceptions.py`.
- Exception-to-HTTP translation is centralized in `backend/app/error_handlers.py` and registered by `backend/app/main.py`.

## Run tests

```bash
pytest
```

Tests use an isolated in-memory SQLite database and do not modify the normal local database.
