# OpsPilot

OpsPilot is a microservices incident response and service health management platform with local Retrieval-Augmented Generation (RAG) AI incident root-cause analysis.

## Technology Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite, Pydantic v2, google-genai SDK
- **Frontend:** React 18, Vite, SCSS
- **AI/RAG:** Google Gemini (`gemini-2.5-flash`), local token-matching retrieval engine

---

## AI Incident Analysis

OpsPilot integrates Google Gemini to provide automated, structured root-cause insights and diagnostic investigation checklists directly in the operational incident response workflow.

### Architecture Flow

```text
Incident (Client)
      ↓
POST /incidents/{incident_id}/analyze
      ↓
FastAPI Router (auth check via JWT Bearer)
      ↓
AI Service (`ai_service.py`)
      ↓
RAG Retrieval (`rag_service.py` -> local knowledge base)
      ↓
Gemini Prompt (Incident context + Retrieved knowledge)
      ↓
Gemini API (`client.models.generate_content`)
      ↓
Structured JSON Analysis (`AIIncidentAnalysis`)
      ↓
Frontend Advisory Dashboard
```

### What Gemini Generates

Gemini returns a strictly typed JSON object adhering to the `AIIncidentAnalysis` schema:

1. **`summary`**: A concise, 1-sentence incident overview with an explicit disclaimer that findings are AI-generated recommendations.
2. **`possible_root_cause`**: 1–2 sentence hypotheses of underlying failure mechanisms based on symptoms, service context, and retrieved troubleshooting steps.
3. **`recommended_checks`**: An actionable diagnostic checklist of specific metrics, logs, queries, or configs to inspect.
4. **`suggested_resolution`**: Pragmatic, concrete remediation steps.
5. **`knowledge_used`**: A boolean flag indicating whether internal runbook entries matched and augmented the analysis.

### Security and API Key Isolation

The Gemini API key (`GEMINI_API_KEY`) is stored exclusively in backend environment variables (`.env`) and is **never** transmitted to or accessible from frontend clients. All AI calls are mediated by authenticated FastAPI endpoints (`POST /incidents/{incident_id}/analyze`).

---

## RAG / Knowledge Retrieval

OpsPilot implements a **lightweight, explainable local RAG system** designed for fast incident triage without complex vector infrastructure.

### How it Works

```text
1. Incident is received (title, description, service, severity)
         ↓
2. Local Knowledge Base is searched (backend/app/knowledge/knowledge_base.json)
         ↓
3. Relevant entries are retrieved (token/keyword subset matching)
         ↓
4. Retrieved context is injected into the Gemini prompt
         ↓
5. Gemini generates the final context-aware analysis
```

1. **Query Tokenization:** The incident's `title`, `description`, `service_name`, and `severity` are lowercased and split into a normalized token set.
2. **Subset Matching:** Each knowledge base entry contains a curated list of keywords/phrases (e.g., `"connection pool"`, `"500"`, `"timeout"`). An entry matches if all tokens of a keyword are present in the incident tokens.
3. **Relevance Ranking:** Entries are scored by the count of matching keyword phrases and sorted in descending order.
4. **Context Injection:** The top matches (up to 3) are formatted into structured text sections (causes, troubleshooting steps, resolutions) and appended to the Gemini prompt under a clear advisory header.
5. **Graceful Fallback:** If no entries match, Gemini proceeds with zero-shot analysis using only the raw incident details.

> **Note:** This is a lightweight, zero-dependency local RAG implementation for demonstration and MVP operational use, avoiding heavy external vector databases (Pinecone, Chroma, Milvus) while delivering explainable, deterministic retrieval.

---

## Incident Number Format

Every incident is automatically assigned a unique, ServiceNow-style incident number:

* **Format:** `INC` + 5-digit zero-padded number (e.g., `INC00001`, `INC00042`, `INC00100`).
* **Generation:** Derived using `SELECT MAX(id) + 1` from the SQLite database at creation time.
* **Guarantees:** Unique, monotonically increasing, collision-free, and persistent in the database (`incidents.incident_number` column with unique index).
* **Backfill:** Existing records without incident numbers are automatically assigned numbers during database seeding.

---

## Database Seed & Demo Data

The database includes an idempotent seed script covering realistic microservice architectures:

```bash
cd backend
python -m app.scripts.seed
```

### Seeded Services (6):
- **Payment API** (`down`) — Payment settlement and gateway webhook backlogs
- **User Management API** (`degraded`) — OAuth2 token clock skew and LDAP timeouts
- **Order Management API** (`degraded`) — DB connection pool timeouts and checkout locks
- **Notification Service** (`healthy`) — Email/SMS rate limiting and template render warnings
- **Inventory Service** (`healthy`) — Cache invalidation delays
- **Reporting Service** (`healthy`) — Daily ledger aggregations

### Seeded Incidents (12):
Twelve realistic incidents with varying severities (`critical`, `high`, `medium`, `low`), statuses (`open`, `investigating`, `resolved`), and populated `INC00001`–`INC00012` identifiers.

---

## Local Development Setup

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Configure `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
DATABASE_URL=sqlite:///./opspilot.db
SECRET_KEY=opspilot-dev-secret-key-change-in-production-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Run migrations & seed:
```bash
python -m app.scripts.seed
```

Start the API:
```bash
uvicorn app.main:app --reload --port 8000
```

API Documentation: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## Running Tests

Run the full automated test suite (60 unit and integration tests):

```bash
cd backend
pytest -v
```

All tests run against isolated in-memory SQLite instances with fully mocked external AI APIs.
