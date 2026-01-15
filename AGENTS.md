# AGENTS.md — STM Intelligence Brief System

**Persistent memory for AI agents. Update it whenever you discover gotchas, patterns, or important decisions.**

---

## What This Project Does

**STM Intelligence Brief System:** Market/competitive intelligence platform for sales teams in scholarly publishing.

**Problem:** Sales waste 30+ min/week researching competitors. Intelligence comes from personal networks, not systematic sources.

**Solution:** Curator collects signals from public sources → system clusters into themes + synthesizes actions → weekly dashboard brief for sales.

**MVP Scope:** Weekly dashboard delivery. Defer alerts, battlecards, exec views to Phase 2+.

**Reference:** See `from-thinking-to-coding/` for full specification and implementation plan.

---
All news (site-wide):

https://www.knowledgespeak.com/feed/ – full news stream.

## Project Structure

```
backend/          Python FastAPI (signals, themes, synthesis, brief job)
frontend/         React TypeScript (sales dashboard, curator admin)
docker-compose.yml   Local dev environment
README.md         Current status, how to run
TESTING.md        Manual QA procedures
CODEBASE.md       Detailed codebase reference (file-by-file)
TROUBLESHOOTING.md    Solutions to common issues
```

**Key Directories:**
- `backend/app/` → Main business logic (models, routes, services, jobs)
- `frontend/src/pages/` → Page components (Dashboard, AdminSignalForm, etc.)
- `backend/migrations/` → Database schema versions (Alembic)

---

## Core Concepts (WHY)

### Architecture

**Backend (FastAPI):**
- Signal ingestion API (curator submits data)
- Theme synthesis engine (cluster signals → themes)
- Weekly scheduled job (auto-generates briefs)

**Frontend (React):**
- Public dashboard (sales view briefs)
- Admin interface (curator manages signals)

**Database (PostgreSQL):**
- signals → raw market data with provenance
- themes → clustered signals + "So What / Now What"
- weekly_briefs → ranked themes per week

### Key Decisions

| Decision | Why |
|---|---|
| Python FastAPI | Fast, async-ready, great for scheduled jobs |
| React + TypeScript | Type-safe, prevents runtime errors |
| PostgreSQL | Relational model fits signal→theme→brief flow |
| APScheduler | Lightweight in-process job runner |
| Manual curation first | Validates quality before automation |
| Dashboard only (no email) | Simpler MVP, always up-to-date |

---

## How to Work Here (HOW)

### Before Starting

1. Read README.md "Current Status" (know which phase you're on)
2. Read next phase from `from-thinking-to-coding/2-create-a-plan/implementation-plan.md`
3. Verify app runs: `docker-compose up` (wait for "Application startup complete")

### During Work

- Small, focused commits (one feature = one commit)
- Update AGENTS.md when you discover gotchas or patterns
- Update README.md when status/capabilities change
- Run tests before committing: `pytest backend/tests/ -v`

### After Each Phase

1. **Verify:** Run tests and manual testing (steps in TESTING.md)
2. **Document:** Update README.md with current status
3. **Commit:** Propose commit message and wait for approval
4. **Memory:** Capture learnings in AGENTS.md (gotchas, patterns)

---

## Critical Framework Patterns

**See CODEBASE.md for detailed reference.** Quick highlights:

### Python FastAPI
- Database schema changes → full Docker restart required
- APScheduler jobs only run if app process running
- Always use ORM (never raw SQL) to prevent injection
- CORS must allow frontend domain

### React Frontend
- Environment variables: `.env` file, accessed via `import.meta.env.VITE_*`
- TypeScript: All API responses should be typed

### PostgreSQL
- Local dev connection: `postgresql://postgres:postgres@localhost:5432/intelligence_db`
- Reset database (dev only): `docker-compose down -v && docker-compose up`

---

## Essential Commands

**Backend:**
```bash
docker-compose up                    # Start all services
pytest backend/tests/ -v             # Run tests (show output!)
docker-compose logs backend          # Check backend logs
docker-compose down -v && docker-compose up   # Reset database
```

**Frontend:**
```bash
npm install                          # Install dependencies
npm test                             # Run tests
npm run lint                         # Check code style
```

**See TROUBLESHOOTING.md for solutions to common issues.**

---

## Getting Started (For New Agents)

**You know nothing at session start. Follow this path:**

1. **Understand:** Read "What This Project Does" above
2. **Reference:** Read `from-thinking-to-coding/1-create-a-spec/complete-specification.md`
3. **Plan:** Read `from-thinking-to-coding/2-create-a-plan/implementation-plan.md`
4. **Status:** Check README.md to see what phase is current
5. **Verify:** Run tests and features per TESTING.md
6. **Continue:** Start next phase from implementation plan
7. **Update:** Follow phase wrap-up protocol (see section below)

---

## Phase Wrap-Up Protocol

**Before marking any phase complete:**

### 1. Verify (With Evidence)

```bash
pytest backend/tests/ -v              # Show output
npm test                              # If applicable
docker-compose build                  # Show exit status
```

### 2. Update Docs

- [ ] README.md "Current Status" (phase complete, what works, what's next)
- [ ] TESTING.md (add manual QA steps for new features)
- [ ] AGENTS.md (any gotchas discovered)
- [ ] Spec/Plan (if implementation differs from original plan)

### 3. User Confirmation

Walk user through manual testing steps (specific, not vague):
- "Click X button, you should see Y message"
- NOT: "test the feature"

Wait for explicit confirmation that tests passed.

### 4. Memory Sweep

Ask: "What did I learn this session that future sessions need to know?"

Update AGENTS.md if:
- Discovered framework gotcha
- Found pattern that works well
- Made architectural decision
- Learned important command or workflow

### 5. Commit

Suggest commit message referencing phase:
```
feat(phase3): add signal list API with filtering

- List API with pagination (20 per page)
- Filter by date range, search by topic
- Tests pass: all signal CRUD operations verified
```

Wait for approval before committing.

---

## Red Flags (Never Do These)

- ❌ "Tests should pass" (show output first)
- ❌ "Phase complete, moving to Phase X" (wait for user confirmation)
- ❌ Code updated but docs not (update docs before committing)
- ❌ "Everything looks good" (run verification first)
- ❌ Jump to next phase without wrap-up (always follow protocol)

---

## Code Review

Request code review for major phases or complex features. Include specific sections to review from spec.

---

## Continuous Documentation

**Update immediately. Don't wait for wrap-up.**

When you discover:
- Framework gotcha → Add to AGENTS.md
- Pattern that works → Add to AGENTS.md
- Architectural decision → Update spec/plan
- New capability → Update README.md
- Testing procedure → Update TESTING.md

---

## Detailed References

For more information, see these files:

- **CODEBASE.md** — Detailed file-by-file reference, all directories, key files
- **TROUBLESHOOTING.md** — Solutions to common issues (backend won't start, tests failing, etc.)
- **DEVELOPMENT.md** — Commands, commit strategy, code style, dependencies

---

## Notes for Agents

This is a straightforward MVP with intentional simplicity:
- **No overcomplexity:** FastAPI, React, PostgreSQL — boring, well-understood stack
- **Theme synthesis is simple:** Naive clustering works for MVP (ML comes in Phase 2)
- **Manual curation:** Quality over volume (automate after proving business model)

**Every phase should end with working software you can see and test.**

---

**Last Updated:** 2025-12-17
**Maintain By:** Updating whenever you discover gotchas, patterns, decisions
**Reference:** Complete spec in `from-thinking-to-coding/1-create-a-spec/`

