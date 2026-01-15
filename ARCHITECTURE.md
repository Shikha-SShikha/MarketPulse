# Architecture - STM Intelligence Brief System

System architecture, data flow, and technical design decisions.

## Table of Contents
- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Security Architecture](#security-architecture)
- [Scalability Considerations](#scalability-considerations)

---

## System Overview

The STM Intelligence Brief System is a **3-tier web application** for collecting market intelligence signals and synthesizing them into actionable weekly briefs for STM publishing sales teams.

### Key Components

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   Backend   │─────▶│  Database   │
│  React/TS   │◀─────│ FastAPI/Py  │◀─────│ PostgreSQL  │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  Scheduler  │
                     │ APScheduler │
                     └─────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + TypeScript | User interface (dashboard, admin) |
| **Styling** | Tailwind CSS | Responsive, utility-first styling |
| **API Client** | Axios | HTTP client with interceptors |
| **Backend** | FastAPI (Python 3.11) | REST API, business logic |
| **Database** | PostgreSQL 15 | Persistent data storage |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Migrations** | Alembic | Schema versioning |
| **Scheduler** | APScheduler | Weekly brief generation job |
| **Validation** | Pydantic v2 | Request/response validation |
| **Containerization** | Docker + Docker Compose | Development & deployment |

---

## Architecture Diagram

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USERS                                       │
│  ┌────────────────┐              ┌────────────────┐                │
│  │  Sales Teams   │              │   Curators     │                │
│  │  (Dashboard)   │              │   (Admin UI)   │                │
│  └────────┬───────┘              └────────┬───────┘                │
└───────────┼──────────────────────────────┼──────────────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────────────────────────────────────────────────┐
│                       FRONTEND (React)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Dashboard   │  │ Signal List  │  │ Signal Form  │           │
│  │   (Public)   │  │   (Admin)    │  │   (Admin)    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│         │                   │                  │                   │
│         └───────────────────┴──────────────────┘                   │
│                             │                                       │
│                  ┌──────────▼──────────┐                          │
│                  │   API Client        │                          │
│                  │   (Axios)           │                          │
│                  └──────────┬──────────┘                          │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                     HTTPS / REST API
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                     BACKEND (FastAPI)                              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Middleware Layer                                           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │  │
│  │  │  Error   │ │ Logging  │ │   Rate   │ │   CORS   │     │  │
│  │  │ Handling │ │          │ │ Limiting │ │          │     │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  API Routes                                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │   Signals    │  │    Briefs    │  │    Admin     │    │  │
│  │  │   (CRUD)     │  │  (Read-only) │  │ (Protected)  │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Business Logic (Services)                                  │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │   Signal   │  │    Theme     │  │    Brief     │      │  │
│  │  │  Service   │  │  Synthesis   │  │  Generator   │      │  │
│  │  └────────────┘  └──────────────┘  └──────────────┘      │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Background Jobs (APScheduler)                              │  │
│  │  ┌──────────────────────────────────────────┐              │  │
│  │  │  Weekly Brief Generation Job             │              │  │
│  │  │  (Sundays 5 PM UTC)                      │              │  │
│  │  └──────────────────────────────────────────┘              │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Data Access Layer (SQLAlchemy ORM)                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                │  │
│  │  │  Signal  │  │  Theme   │  │  Brief   │                │  │
│  │  │  Model   │  │  Model   │  │  Model   │                │  │
│  │  └──────────┘  └──────────┘  └──────────┘                │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                   Connection Pool (5-20)
                             │
┌────────────────────────────▼──────────────────────────────────────┐
│                    DATABASE (PostgreSQL 15)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │
│  │  signals   │  │   themes   │  │   briefs   │                  │
│  │   table    │  │    table   │  │    table   │                  │
│  └────────────┘  └────────────┘  └────────────┘                  │
│                                                                    │
│  Indexes: entity, topic, created_at, week_start                   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (React + TypeScript)

**Location:** `frontend/src/`

**Key Pages:**
- `pages/Dashboard.tsx` - Public dashboard showing weekly brief
- `pages/AdminSignalList.tsx` - Admin page for managing signals
- `pages/AdminSignalForm.tsx` - Form for creating new signals

**Components:**
- `components/ThemeCard.tsx` - Display theme with So What/Now What
- `components/SignalEvidence.tsx` - Expandable signal details
- `components/FormFields.tsx` - Reusable form inputs with validation
- `components/Toast.tsx` - Notification system

**API Client:**
- `api/client.ts` - Axios instance with interceptors
- `api/signals.ts` - Signal CRUD operations
- `api/briefs.ts` - Brief retrieval operations

**State Management:**
- `context/AuthContext.tsx` - Authentication state
- `context/ToastContext.tsx` - Toast notifications
- Local component state (no Redux needed for MVP)

**Build Output:** Static files (HTML, JS, CSS) → Deploy to CDN/S3

### 2. Backend (FastAPI + Python)

**Location:** `backend/app/`

**Module Structure:**
```
app/
├── main.py           # Application entry point, middleware setup
├── config.py         # Environment configuration
├── database.py       # Database connection, session factory
├── models.py         # SQLAlchemy ORM models
├── schemas.py        # Pydantic request/response schemas
├── routes.py         # API endpoint definitions
├── services.py       # Business logic (signals, themes, briefs)
├── jobs.py           # Background job definitions
├── scheduler.py      # APScheduler setup
├── middleware.py     # Custom middleware (logging, errors, rate limit)
└── exceptions.py     # Custom exception classes
```

**API Endpoints:**
```
GET  /health                    # Health check
GET  /signals                   # List signals (with filters)
GET  /signals/{id}              # Get single signal
POST /signals                   # Create signal (requires auth)
DELETE /signals/{id}            # Delete signal (requires auth)
GET  /briefs/current            # Get current week's brief
GET  /briefs/{id}               # Get specific brief
POST /admin/generate-brief      # Manual brief generation (requires auth)
GET  /docs                      # Swagger API documentation
```

**Middleware Stack (Order Matters):**
1. `ErrorHandlingMiddleware` - Catch all exceptions, return JSON
2. `RequestLoggingMiddleware` - Log requests with request IDs
3. `RateLimitMiddleware` - Rate limit admin endpoints (100/min)
4. `CORSMiddleware` - Handle cross-origin requests

**Authentication:** Bearer token (simple, sufficient for MVP)

### 3. Database (PostgreSQL)

**Location:** PostgreSQL container or managed service

**Tables:**
- `signals` - Raw market intelligence signals
- `themes` - Clustered signals with synthesis
- `weekly_briefs` - Generated weekly reports
- `alembic_version` - Migration version tracking

**Connection Pool:**
- Min connections: 5
- Max connections: 20 (5 base + 15 overflow)
- Pre-ping enabled (verify connections before use)

### 4. Background Scheduler (APScheduler)

**Location:** `backend/app/scheduler.py`

**Jobs:**
- `generate_weekly_brief_job` - Runs every Sunday at 5 PM UTC
- Triggers theme synthesis from past 7 days of signals
- Idempotent: won't create duplicate briefs for same week

**Lifecycle:**
- Starts with FastAPI app (`lifespan` event)
- Shuts down gracefully with app

---

## Data Flow

### Signal Creation Flow

```
1. Curator fills form → frontend/AdminSignalForm.tsx
   ↓
2. Form validates client-side (URL, length, required fields)
   ↓
3. POST /signals with Authorization header
   ↓
4. Middleware: Check auth token, rate limit, log request
   ↓
5. Pydantic validates request schema
   ↓
6. services.create_signal() saves to database
   ↓
7. Response: 201 Created with signal data
   ↓
8. Frontend shows success toast, updates suggestions
```

### Weekly Brief Generation Flow

```
1. Scheduler triggers job (Sunday 5 PM UTC)
   ↓
2. jobs.generate_weekly_brief_job() executes
   ↓
3. Query signals from past 7 days
   ↓
4. services.synthesize_weekly_themes() processes signals:
   a. Cluster by topic (exact match)
   b. Merge overlapping clusters (by impact_areas/tags)
   c. Calculate aggregate confidence
   d. Generate "So What" (template-based)
   e. Generate "Now What" action items (template-based)
   f. Rank themes by impact area coverage, recency, confidence
   ↓
5. Create WeeklyBrief record with theme_ids
   ↓
6. Log success/failure
   ↓
7. Sales team views on Dashboard next time they visit
```

### Dashboard View Flow

```
1. User visits frontend (localhost:3000 or dashboard.example.com)
   ↓
2. Dashboard.tsx loads, calls getCurrentBrief()
   ↓
3. GET /briefs/current (no auth required)
   ↓
4. Backend queries most recent WeeklyBrief
   ↓
5. If exists: Load themes + signals, return 200 with full data
   If not: Return 204 No Content
   ↓
6. Frontend displays brief with ranked themes
   ↓
7. User expands theme → shows contributing signals with evidence
```

---

## Database Schema

### Entity Relationship Diagram

```
┌───────────────────────────────┐
│        signals                │
├───────────────────────────────┤
│ id              UUID (PK)     │
│ entity          VARCHAR(255)  │◀────┐
│ event_type      VARCHAR(50)   │     │
│ topic           VARCHAR(255)  │     │
│ source_url      TEXT          │     │
│ evidence_snippet TEXT         │     │
│ confidence      VARCHAR(10)   │     │
│ impact_areas    ARRAY[TEXT]   │     │
│ entity_tags     ARRAY[TEXT]   │     │
│ created_at      TIMESTAMP     │     │
│ curator_name    VARCHAR(100)  │     │
│ notes           TEXT          │     │
│ deleted_at      TIMESTAMP     │     │
└───────────────────────────────┘     │
         ▲                            │
         │                            │
         │                            │
┌────────┴──────────────────────┐    │
│        themes                 │    │
├───────────────────────────────┤    │
│ id              UUID (PK)     │    │
│ title           VARCHAR(500)  │    │
│ signal_ids      ARRAY[UUID]   │────┘
│ key_players     ARRAY[TEXT]   │
│ aggregate_confidence VARCHAR  │
│ impact_areas    ARRAY[TEXT]   │
│ so_what         TEXT          │
│ now_what        ARRAY[TEXT]   │
│ created_at      TIMESTAMP     │
└───────────────────────────────┘
         ▲
         │
         │
┌────────┴──────────────────────┐
│     weekly_briefs             │
├───────────────────────────────┤
│ id              UUID (PK)     │
│ week_start      DATE          │
│ week_end        DATE          │
│ theme_ids       ARRAY[UUID]   │────┘
│ generated_at    TIMESTAMP     │
│ total_signals   INTEGER       │
│ coverage_areas  ARRAY[TEXT]   │
└───────────────────────────────┘
```

### Indexes

```sql
-- signals table
CREATE INDEX ix_signals_entity ON signals(entity);
CREATE INDEX ix_signals_topic ON signals(topic);
CREATE INDEX ix_signals_created_at ON signals(created_at DESC);

-- themes table
CREATE INDEX ix_themes_created_at ON themes(created_at DESC);

-- weekly_briefs table
CREATE INDEX ix_weekly_briefs_week_start ON weekly_briefs(week_start DESC);
CREATE INDEX ix_weekly_briefs_week_end ON weekly_briefs(week_end DESC);
```

---

## API Design

### RESTful Principles

- **GET** - Read operations (idempotent, cacheable)
- **POST** - Create operations
- **DELETE** - Delete operations (soft delete for signals)
- **No PUT/PATCH for MVP** (except internal use)

### Response Format

**Success (200/201):**
```json
{
  "id": "uuid",
  "entity": "Publisher Name",
  "created_at": "2025-12-18T10:00:00",
  ...
}
```

**Error (4xx/5xx):**
```json
{
  "error": "Human-readable error message",
  "status": 400,
  "details": {
    "field": "source_url"
  }
}
```

**List Response:**
```json
{
  "signals": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### Authentication

**Method:** Bearer token in `Authorization` header

```
Authorization: Bearer <CURATOR_TOKEN>
```

**Protected Endpoints:**
- `POST /signals`
- `DELETE /signals/{id}`
- `POST /admin/generate-brief`

**Public Endpoints:**
- `GET /health`
- `GET /signals` (list only)
- `GET /briefs/current`
- `GET /briefs/{id}`

---

## Security Architecture

### Defense Layers

1. **Network Layer**
   - Firewall: Only ports 80, 443, 22 open
   - Database not exposed publicly
   - TLS/SSL for all external traffic

2. **Application Layer**
   - CORS: Whitelist specific origins only
   - Rate limiting: 100 req/min on admin endpoints
   - Input validation: Pydantic schemas
   - SQL injection prevention: Parameterized queries (SQLAlchemy)
   - XSS prevention: React auto-escapes content

3. **Authentication Layer**
   - Bearer token required for write operations
   - Token stored securely (environment variable)
   - Frontend stores token in localStorage (MVP simplicity)

4. **Data Layer**
   - Database credentials in environment variables
   - Connection pool limits (prevent exhaustion)
   - Regular backups (daily automated)

### Security Best Practices

- ✅ Use HTTPS in production (Let's Encrypt)
- ✅ Environment-specific secrets (no hardcoded passwords)
- ✅ Structured logging (no sensitive data in logs)
- ✅ Regular dependency updates (security patches)
- ✅ Soft deletes (preserve audit trail)
- ✅ Request ID tracking (X-Request-ID header)

---

## Scalability Considerations

### Current Capacity (MVP)

- **Signals:** 10,000+ signals/year
- **Briefs:** 52 briefs/year
- **Users:** 50-100 concurrent users
- **Response time:** <500ms for API calls

### Bottlenecks & Solutions

| Bottleneck | Current | When to Scale | Solution |
|------------|---------|---------------|----------|
| Database connections | 20 max | >15 avg concurrent | Increase pool size, use PgBouncer |
| Brief generation | Single-threaded | >5 min generation time | Async processing, separate worker |
| Frontend hosting | Single server | >1000 users | CDN (CloudFront, Cloudflare) |
| API throughput | Single container | >100 req/sec | Horizontal scaling (multiple containers) |

### Scaling Strategies

**Vertical Scaling (Short-term):**
- Increase CPU/RAM for backend container
- Upgrade PostgreSQL instance size
- Optimize database queries (indexes, vacuum)

**Horizontal Scaling (Long-term):**
- Multiple backend containers behind load balancer
- Read replicas for database (if read-heavy)
- Separate worker service for brief generation
- Redis cache for frequently accessed briefs

---

## Deployment Architecture

### Production (Recommended)

```
                    ┌──────────────┐
                    │   Internet   │
                    └──────┬───────┘
                           │
                    ┌──────▼────────┐
                    │  Load Balancer│
                    │  (ALB/nginx)  │
                    │   + SSL/TLS   │
                    └──────┬────────┘
                           │
         ┌─────────────────┴──────────────────┐
         │                                     │
    ┌────▼────┐                         ┌─────▼─────┐
    │Frontend │                         │  Backend  │
    │ Static  │                         │ Container │
    │  Files  │                         │ (FastAPI) │
    │ (S3/CDN)│                         └─────┬─────┘
    └─────────┘                               │
                                              │
                                       ┌──────▼─────┐
                                       │ PostgreSQL │
                                       │  Database  │
                                       │  (RDS/DO)  │
                                       └────────────┘
```

### Development (Current)

```
    ┌─────────────────────────────────┐
    │    Docker Compose (Local)       │
    ├──────────┬──────────┬───────────┤
    │ Frontend │ Backend  │ Postgres  │
    │  :3000   │  :8000   │  :5432    │
    └──────────┴──────────┴───────────┘
```

---

## Technical Debt & Future Improvements

### Known Limitations (MVP)

- ❌ No user authentication (single curator token)
- ❌ No email notifications
- ❌ Theme synthesis is template-based (not ML-powered)
- ❌ No search functionality on dashboard
- ❌ No export to PDF/email
- ❌ No analytics/trends over time

### Future Enhancements

**Phase 11+ (Post-MVP):**
1. **User Management:** Multi-user support, role-based access
2. **Advanced Synthesis:** ML-based clustering, NLP for "So What"
3. **Notifications:** Email alerts when brief generated
4. **Search & Filters:** Full-text search across signals/briefs
5. **Analytics Dashboard:** Trends, signal volume, theme evolution
6. **Export:** PDF generation, email distribution
7. **API v2:** GraphQL for more flexible queries
8. **Mobile App:** React Native for on-the-go access

---

## Decision Log

### Why FastAPI?
- Fast development with automatic docs (Swagger)
- Type safety with Pydantic
- Async support (future-proof)
- Active community

### Why PostgreSQL?
- Mature, reliable, open-source
- Array types for impact_areas/tags (avoid joins)
- JSON support (future flexibility)
- Strong ACID guarantees

### Why React?
- Component reusability
- Large ecosystem (Tailwind, Axios, React Router)
- TypeScript support (type safety)
- Client-side rendering (fast, simple hosting)

### Why Simple Authentication?
- MVP needs: one curator or small team
- Bearer token is sufficient
- Can upgrade to OAuth2/JWT later

### Why APScheduler (not Celery)?
- Simpler setup (no Redis/RabbitMQ needed)
- Sufficient for one weekly job
- Built-in persistence (if needed later)
- Can migrate to Celery when scaling

---

## Monitoring & Observability

### Metrics to Track

- **Availability:** Uptime, health check response
- **Performance:** API response time (p50, p95, p99)
- **Errors:** 4xx/5xx rate, exception count
- **Database:** Connection pool usage, query latency
- **Business:** Signals/day, briefs generated, user activity

### Logging Strategy

- **Structured logs:** JSON format for parsing
- **Request IDs:** Track request lifecycle
- **Log levels:** DEBUG (dev), INFO (prod), ERROR (always)
- **Retention:** 30 days default, 90 days for errors

---

**Last Updated:** December 2025
