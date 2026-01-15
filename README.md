# STM Intelligence Brief System

Market/competitive intelligence platform for STM publishing sales teams.

## Current Status

**Phase 10 Complete + Phase 2A Complete** — Production Ready with Automation!

**What works now:**
- Sales Dashboard: Weekly brief display with ranked themes and evidence
- Theme Cards: Expandable cards showing "So What" and "Now What" action items
- Signal Evidence: Source links, confidence badges, impact areas
- Admin UI: Signal entry form with validation, autocomplete, and list view
- Backend: FastAPI with Signal CRUD + Weekly Brief generation
- Scheduler: APScheduler runs weekly brief job every Sunday 5 PM UTC
- Database: PostgreSQL with Signal, Theme, WeeklyBrief tables
- Error Handling: Consistent JSON error responses, user-friendly messages
- Logging: Structured request/response logging with request IDs
- Rate Limiting: Admin endpoints limited to 100 requests/min
- Tests: 39 passing tests (signals, briefs, middleware)
- **Production Deployment:** Complete deployment guides, runbook, architecture docs
- **Docker Entrypoint:** Production-ready startup script with health checks
- **Automated Collection (Phase 2A):**
  - RSS/Atom feed collector (4 sources configured)
  - Web scraper with CSS selectors (1 source configured)
  - LinkedIn profile/hashtag collector (optional, with warnings)
  - Daily automated collection job (9 AM UTC)
  - Signal review UI (approve/reject pending signals)
  - Data source manager (CRUD for sources)
  - Dashboard notifications with unread count
  - Automatic classification (event type, topic, impact areas)
  - Entity extraction (30+ known STM entities)

**Try it:**
```bash
# Start backend
docker compose up

# Start frontend (in separate terminal)
cd frontend && npm install && npm run dev

# View sales dashboard
open http://localhost:3000

# Admin UI (requires token: dev-token-change-in-production)
open http://localhost:3000/admin/signals/new
```

**Pages:**
- `/` — Sales Dashboard (weekly brief with themes)
- `/admin/signals` — Signal list management
- `/admin/signals/new` — Add new signal form
- `/admin/signals/review` — Signal review (approve/reject pending signals)
- `/admin/data-sources` — Data source manager (add/edit RSS/web sources)

**API Endpoints:**
```bash
curl http://localhost:8000/health                    # Health check
curl http://localhost:8000/signals                   # List signals
curl http://localhost:8000/briefs/current            # Get current brief
curl http://localhost:8000/admin/signals/pending     # Get pending signals for review
curl http://localhost:8000/admin/data-sources        # List data sources
curl -X POST http://localhost:8000/admin/collect-signals  # Manual collection trigger
curl http://localhost:8000/notifications             # Get notifications
open http://localhost:8000/docs                      # API docs
```

**Next:** Ready for pilot deployment! See `DEPLOYMENT.md` for production setup.

---

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)

### Quick Start

1. **Start all services:**
   ```bash
   docker compose up
   ```

2. **Verify backend:**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status": "ok"}
   ```

3. **Verify frontend (run separately):**
   ```bash
   cd frontend
   npm install
   npm run dev
   # Open http://localhost:3000
   ```

### Environment Setup

Copy environment templates:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

---

## Project Structure

```
backend/           Python FastAPI (API, business logic, jobs)
frontend/          React TypeScript (dashboard, admin UI)
docker-compose.yml Local development environment
AGENTS.md          AI agent instructions (persistent memory)
CODEBASE.md        Detailed file-by-file reference
DEVELOPMENT.md     Commands and conventions
TROUBLESHOOTING.md Common issues and solutions
```

---

## Reference Documentation

### Development & Planning
- **Full Specification:** `from-thinking-to-coding/1-create-a-spec/complete-specification.md`
- **Implementation Plan:** `from-thinking-to-coding/2-create-a-plan/implementation-plan.md`
- **Agent Instructions:** `AGENTS.md`
- **Codebase Reference:** `CODEBASE.md`

### Production & Operations
- **Deployment Guide:** `DEPLOYMENT.md` - Production deployment instructions (Docker, cloud platforms)
- **Operations Runbook:** `RUNBOOK.md` - Troubleshooting, incident response, maintenance
- **Architecture:** `ARCHITECTURE.md` - System design, data flow, technical decisions
- **Development Guide:** `DEVELOPMENT.md` - Commands and conventions
- **Troubleshooting:** `TROUBLESHOOTING.md` - Common issues and solutions

---

## Development

See `DEVELOPMENT.md` for detailed commands and conventions.

### Quick Commands

```bash
# Start services
docker compose up

# Run backend tests
docker compose exec backend pytest tests/ -v

# Run database migrations
docker compose exec backend alembic upgrade head

# Run frontend dev server
cd frontend && npm run dev

# Check API docs
open http://localhost:8000/docs
```

---
