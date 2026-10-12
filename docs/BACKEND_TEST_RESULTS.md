# Backend test results

**Validation date:** October 12, 2026  
**Result:** Passed

## Summary

| Check | Result |
| --- | --- |
| Backend tests | 60 passed |
| Runtime | 4.98 seconds |
| Warnings | 3 dependency deprecation warnings |

The suite covers authentication and authorization, services, incident CRUD and pagination/filtering, health routing, AI analysis behavior and error handling, local knowledge retrieval, and database seeding/idempotence.

## Run locally

From the repository root, PowerShell users can set the same non-secret test settings as CI and run pytest:

```powershell
$env:APP_NAME = "OpsPilot"
$env:ENVIRONMENT = "test"
$env:DATABASE_URL = "sqlite://"
$env:LOG_LEVEL = "INFO"
$env:JWT_SECRET = "ci-only-test-secret"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "60"
$env:ALLOWED_ORIGINS = "http://localhost"
$env:FRONTEND_URL = "http://localhost"
$env:GEMINI_MODEL = "gemini-2.0-flash-exp"
python -m pytest backend\tests -q
```

The test configuration uses a non-production JWT secret and does not require a real Gemini API key; external AI behavior is mocked in tests. Do not use these CI values for a deployed application.

The CI workflow installs Python 3.11 dependencies, sets these test environment values, and runs `pytest tests/ -v --tb=short` from `backend/`. Current test count can change as tests are added or removed.
