# Codebase Reference — File-by-File

Detailed reference for every directory and key file. Use this when you need to understand what each file does.

---

## Backend Structure

### `backend/app/main.py`
**Purpose:** FastAPI app initialization, middleware setup, scheduler initialization.

**Key Responsibilities:**
- Create FastAPI app instance
- Configure middleware (CORS, error handling)
- Initialize APScheduler
- Register all route handlers
- Database setup/teardown

**When to Modify:** Adding new routes, configuring middleware, changing scheduler settings.

### `backend/app/models.py`
**Purpose:** SQLAlchemy ORM models for database tables.

**Models:**
- `Signal` → raw market data (entity, event_type, topic, source_url, evidence_snippet, confidence, impact_areas, entity_tags, created_at, curator_name, notes)
- `Theme` → clustered signals (id, title, signal_ids[], key_players[], aggregate_confidence, impact_areas[], so_what, now_what[], created_at)
- `WeeklyBrief` → ranked themes per week (id, week_start, week_end, theme_ids[], generated_at, total_signals, coverage_areas[])

**When to Modify:** When data structure changes (new fields, new table, relationship changes).

**Important:** All models inherit from `Base` (SQLAlchemy declarative), foreign keys use ForeignKey().

### `backend/app/schemas.py`
**Purpose:** Pydantic models for request/response validation.

**Schemas:**
- `SignalCreate` → Input validation (POST /signals)
- `SignalResponse` → Output format (GET /signals)
- `BriefResponse` → Output format (GET /briefs/current)
- `ErrorResponse` → Error format

**When to Modify:** When API contracts change (new fields, new validation rules).

**Important:** Pydantic validates all inputs automatically (prevents injection, type errors).

### `backend/app/routes.py`
**Purpose:** API endpoint definitions.

**Endpoints:**
- `POST /signals` → Curator signal ingestion
- `GET /signals` → List signals (filters: date, topic, entity)
- `GET /signals/{id}` → View single signal
- `PATCH /signals/{id}` → Update signal notes (curator only)
- `DELETE /signals/{id}` → Soft delete signal
- `GET /briefs/current` → Get latest brief
- `GET /briefs/{id}` → Get specific brief (optional)
- `GET /health` → Health check

**When to Modify:** When adding new endpoints or changing existing ones.

**Important:** All endpoints require Authorization header (bearer token for admin endpoints). Use `@router.post()`, `@router.get()` decorators.

### `backend/app/services.py`
**Purpose:** Business logic (separated from routes for testability).

**Functions:**
- `create_signal()` → Validate and store signal
- `get_signals()` → Query signals with filters
- `validate_url()` → URL format validation
- `synthesize_weekly_themes()` → Main theme synthesis algorithm
- `cluster_signals_by_topic()` → Group signals into clusters
- `aggregate_confidence()` → Combine confidence scores
- `generate_so_what()` → Create "why matters" explanation
- `generate_now_what()` → Create action bullets
- `rank_themes_by_impact()` → Sort themes by impact

**When to Modify:** When business logic changes (synthesis algorithm, validation rules, etc.).

### `backend/app/jobs.py`
**Purpose:** Scheduled jobs (long-running background tasks).

**Jobs:**
- `generate_weekly_brief_job()` → Main job (Sunday 5 PM UTC)
  - Query signals from past 7 days
  - Call synthesize_weekly_themes()
  - Create WeeklyBrief record
  - Log generation details

**When to Modify:** When changing brief generation logic or schedule.

**Important:** Must be idempotent (safe to run multiple times).

### `backend/app/scheduler.py`
**Purpose:** APScheduler configuration and job registration.

**Responsibilities:**
- Initialize APScheduler
- Register jobs
- Handle scheduling errors

**When to Modify:** When adding new jobs or changing schedule.

### `backend/app/database.py`
**Purpose:** SQLAlchemy engine, session factory, database configuration.

**Contains:**
- `SQLALCHEMY_DATABASE_URL` parsing from env
- `engine` creation with connection pooling
- `SessionLocal` factory
- `Base` declarative class

**When to Modify:** When changing database config (connection pooling, echo SQL, etc.).

### `backend/app/config.py`
**Purpose:** Environment variable configuration.

**Loads from .env:**
- `DATABASE_URL`
- `CURATOR_TOKEN`
- `ALLOWED_ORIGINS` (CORS)
- `LOG_LEVEL`

**When to Modify:** When adding new config options.

### `backend/app/exceptions.py`
**Purpose:** Custom exceptions for the application.

**Exceptions:**
- `ValidationError` → Input validation failed
- `NotFoundError` → Resource not found
- `UnauthorizedError` → Missing/invalid auth
- `DatabaseError` → Database operation failed

**When to Modify:** When adding new error types.

### `backend/app/logging.py`
**Purpose:** Structured logging setup.

**Format:** `[HH:MM:SS] [PREFIX] message`

**When to Modify:** When changing log format or adding log handlers.

### `backend/app/middleware.py`
**Purpose:** Request/response middleware (CORS, error handling, logging).

**Middleware:**
- CORS configuration (allow frontend domain)
- Error response formatting (consistent JSON error format)
- Request/response logging

**When to Modify:** When changing CORS rules or error handling.

### `backend/migrations/`
**Purpose:** Alembic database migrations (version control for schema).

**Usage:**
- `alembic upgrade head` → Run all pending migrations
- `alembic revision --autogenerate -m "description"` → Create new migration
- `alembic downgrade -1` → Rollback one version

**When to Modify:** After changing models.py, auto-generate new migration.

### `backend/tests/`
**Purpose:** Unit and integration tests.

**Structure:**
- `test_signals.py` → Signal ingestion, validation, CRUD
- `test_themes.py` → Theme synthesis, clustering, ranking
- `test_briefs.py` → Brief generation, retrieval
- `conftest.py` → Shared fixtures (test database, etc.)

**When to Modify:** When adding new features, write tests first.

---

## Frontend Structure

### `frontend/src/App.tsx`
**Purpose:** React app root, routing configuration, global providers.

**Responsibilities:**
- Define routes (/, /admin/signals, /admin/signals/new, etc.)
- Provide Auth context
- Global error boundary

**When to Modify:** When adding new pages or routes.

### `frontend/src/pages/Dashboard.tsx`
**Purpose:** Sales dashboard (main public-facing page).

**Responsibilities:**
- Fetch current brief (GET /briefs/current)
- Display ranked themes
- Handle loading/error states

**When to Modify:** When changing brief display format, adding filtering, etc.

### `frontend/src/pages/AdminSignalForm.tsx`
**Purpose:** Curator signal entry form.

**Responsibilities:**
- Form for submitting new signals
- Field validation (URL, character count)
- Success/error messaging

**When to Modify:** When changing form fields or validation rules.

### `frontend/src/pages/AdminSignalList.tsx`
**Purpose:** Curator dashboard (view/manage signals).

**Responsibilities:**
- List all curator's signals
- Filters (date range, search)
- Actions (edit, delete)

**When to Modify:** When adding filtering options or bulk actions.

### `frontend/src/components/ThemeCard.tsx`
**Purpose:** Individual theme display component.

**Props:** theme (Theme object)

**When to Modify:** When changing theme card layout/styling.

### `frontend/src/components/SignalEvidence.tsx`
**Purpose:** Expanded signal details display.

**Props:** signal (Signal object), showEvidence (boolean)

**When to Modify:** When changing evidence display format.

### `frontend/src/context/AuthContext.tsx`
**Purpose:** Curator authentication token management.

**Stores in localStorage:** `curatorToken`

**When to Modify:** When changing auth approach (adding OAuth2, etc.).

### `frontend/src/api/signals.ts`
**Purpose:** API client for signal endpoints.

**Functions:**
- `createSignal(data)` → POST /signals
- `getSignals(filters)` → GET /signals
- `updateSignalNotes(id, notes)` → PATCH /signals/{id}
- `deleteSignal(id)` → DELETE /signals/{id}

**When to Modify:** When adding new signal endpoints.

### `frontend/src/api/briefs.ts`
**Purpose:** API client for brief endpoints.

**Functions:**
- `getCurrentBrief()` → GET /briefs/current
- `getBriefById(id)` → GET /briefs/{id}

**When to Modify:** When adding new brief endpoints.

### `frontend/src/index.css`
**Purpose:** Global styles (mobile-first, high contrast).

**When to Modify:** When changing global theme, colors, typography.

---

## Configuration Files

### `docker-compose.yml`
**Purpose:** Local dev environment (PostgreSQL + backend + frontend).

**Services:**
- `postgres` → PostgreSQL database
- `backend` → FastAPI app
- `frontend` → React dev server (optional)

**When to Modify:** When adding services, changing ports, changing image versions.

### `backend/requirements.txt`
**Purpose:** Python dependencies.

**Key Packages:**
- `fastapi` → Web framework
- `sqlalchemy` → ORM
- `apscheduler` → Job scheduling
- `pydantic` → Validation
- `psycopg2` → PostgreSQL driver

**When to Modify:** When adding new dependencies (avoid unless necessary).

### `frontend/package.json`
**Purpose:** JavaScript dependencies and npm scripts.

**Key Packages:**
- `react` → UI framework
- `typescript` → Type safety
- `tailwindcss` → CSS framework
- `axios` → HTTP client

**When to Modify:** When adding new dependencies (avoid unless necessary).

### `.env.example`
**Purpose:** Template for environment variables (copy to `.env` locally, use in CI/CD).

**Contains:**
- `DATABASE_URL`
- `CURATOR_TOKEN`
- `ALLOWED_ORIGINS`
- `VITE_API_URL` (frontend)

**When to Modify:** When adding new required env vars.

---

## Documentation Files

### `README.md`
**Purpose:** Project status, how to run, quick test command.

**Sections:**
- Current Status (which phase complete, what works)
- Getting Started (how to run locally)
- Testing (how to test features)

**When to Modify:** After each phase completion.

### `TESTING.md`
**Purpose:** Manual QA procedures for each feature.

**Format:** Step-by-step instructions ("Click X, you should see Y")

**When to Modify:** After adding new features.

### `AGENTS.md`
**Purpose:** Persistent memory for AI agents (gotchas, patterns, decisions).

**When to Modify:** Whenever you discover important learnings.

### This File (`CODEBASE.md`)
**Purpose:** Detailed file-by-file reference.

**When to Modify:** When adding new files or changing existing ones.

---

## How Files Connect

```
User submits signal (admin form)
  ↓ (POST /signals)
routes.py → services.py::create_signal()
  ↓
models.py::Signal (ORM)
  ↓
database.py → PostgreSQL

Weekly job runs (Sunday 5 PM)
  ↓ (APScheduler)
jobs.py::generate_weekly_brief_job()
  ↓
services.py::synthesize_weekly_themes()
  ↓
models.py::Theme + WeeklyBrief
  ↓
database.py → PostgreSQL

Sales views brief
  ↓ (GET /briefs/current)
routes.py
  ↓
frontend Dashboard.tsx
  ↓
components ThemeCard + SignalEvidence
```

---

## Key Patterns

**Database Access:** Always use SQLAlchemy ORM (models.py) → services.py → routes.py

**Validation:** Pydantic schemas (schemas.py) validates all input automatically

**Errors:** Catch at service layer, return appropriate HTTP status from routes

**Logging:** Use structured logging with timestamps for session tracking

**Tests:** Unit tests isolate services, integration tests use test database

---

