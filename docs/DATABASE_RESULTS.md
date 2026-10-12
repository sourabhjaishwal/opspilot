# Database and seed-data results

**Reviewed:** October 12, 2026

OpsPilot uses SQLAlchemy with SQLite for this project. The database URL is read from `DATABASE_URL`; the local example uses `sqlite:///./data/example.db`. The Docker image defaults to `sqlite:///./data/opspilot.db` and mounts `/app/data` from the `opspilot-data` Docker volume for deployment persistence.

## Seed data

The seed script at `backend/app/scripts/seed.py` defines six fictional services and two example incidents for each service (12 incidents total) for local development and demonstrations. It checks for existing services and incidents before inserting, and generates incident numbers based on existing records. It does not clear or reset the database.

Run it from the backend directory after configuring the required settings:

```bash
cd backend
mkdir -p data
python -m app.scripts.seed
```

On Windows PowerShell, create the folder with `New-Item -ItemType Directory -Force data`. This is needed when `DATABASE_URL` points inside `data/` and that directory does not already exist; SQLAlchemy creates database tables but does not create missing parent directories.

The current test suite verifies that a fresh test database receives the expected seed records and that a second run creates no duplicates. The seed tests use an isolated test database; they do not report the contents or health of any developer's local database.

## Results and notes

- The seed tests pass as part of the 60-test backend suite.
- A clean seed run defines six services and 12 incidents; an existing database may contain additional user-created records.
- The knowledge base is a JSON file at `backend/app/knowledge/knowledge_base.json`, not a database table.
- No live database inventory is included here because local and deployed SQLite files are environment-specific and ignored by Git.
- Back up the SQLite file or Docker volume before maintenance. Re-running the seed script does not delete data, and changing a container image does not back up or restore the database.

See [backend test results](./BACKEND_TEST_RESULTS.md) for the command and test summary, and the [AWS deployment guide](./AWS_DEPLOYMENT.md) for the Docker volume path.
