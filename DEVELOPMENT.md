# Development Guide — Commands & Conventions

Detailed reference for development commands, commit strategy, code style, and dependency management.

---

## Essential Commands

### Local Development

```bash
# Start all services (backend + frontend + database)
docker-compose up

# Start specific service only
docker-compose up backend
docker-compose up postgres

# Stop all services (keeps data)
docker-compose down

# Stop and reset everything (deletes data - dev only!)
docker-compose down -v

# View logs
docker-compose logs -f backend       # Follow backend logs
docker-compose logs postgres         # Postgres logs

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend bash
docker-compose exec postgres psql -U postgres

# Rebuild images (if dependencies changed)
docker-compose build
```

### Backend (Python)

```bash
# Install dependencies (one-time, in container)
docker-compose exec backend pip install -r requirements.txt

# Run tests (from backend directory or container)
pytest tests/ -v                              # Run all tests
pytest tests/test_signals.py -v              # Run specific file
pytest tests/test_signals.py::test_create -v # Run specific test
pytest tests/ -v -s                          # Show print statements
pytest tests/ --cov=app --cov-report=html    # Coverage report

# Format Python code (PEP 8)
black backend/app/

# Lint Python code
pylint backend/app/
flake8 backend/app/

# Database migrations
docker-compose exec backend alembic upgrade head          # Run migrations
docker-compose exec backend alembic revision --autogenerate -m "desc"  # Create migration
docker-compose exec backend alembic current              # Check version
docker-compose exec backend alembic downgrade -1         # Rollback

# Run app directly (if debugging)
docker-compose exec backend python -m uvicorn app.main:app --reload

# Check database directly
docker-compose exec postgres psql -U postgres -d intelligence_db
```

### Frontend (React)

```bash
# Install dependencies (one-time)
cd frontend && npm install

# Run frontend dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test
npm test -- --watch          # Watch mode
npm test -- --coverage       # Coverage report

# Code quality
npm run lint                  # Check code style
npm run format               # Auto-format code
npm run type-check           # TypeScript check

# Clean build artifacts
npm run clean
rm -rf dist node_modules     # Hard clean
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get API documentation (Swagger UI)
curl http://localhost:8000/docs

# Signal ingestion (replace TOKEN with actual curator token)
CURATOR_TOKEN="test-token-123"
curl -X POST http://localhost:8000/signals \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "Springer Nature",
    "event_type": "announcement",
    "topic": "OA Mandate",
    "source_url": "https://example.com",
    "evidence_snippet": "New OA policy announced",
    "confidence": "High",
    "impact_areas": ["Ops", "Tech"]
  }'

# Get signals
curl "http://localhost:8000/signals?topic=OA&limit=10"

# Get current brief
curl http://localhost:8000/briefs/current

# Test CORS
curl -H "Origin: http://localhost:3000" http://localhost:8000/health -v
```

---

## Commit Strategy

### Branch Names

```
feature/phase-num-description    # New feature (phase 1, 2, 3, etc.)
fix/bug-description              # Bug fix
refactor/area-description        # Code refactoring
docs/what-updated                # Documentation only
```

**Examples:**
```
feature/phase2-signal-ingestion-api
fix/cors-headers-missing
refactor/theme-clustering-algorithm
docs/update-readme-phase3-complete
```

### Commit Message Format

```
type(scope): description

- Bullet point 1
- Bullet point 2
- Bullet point 3
```

**Type:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

**Scope:** Phase number or area (phase1, signals, themes, frontend, etc.)

**Description:** One line, imperative mood ("add" not "adds", "fix" not "fixed")

### Examples

```
feat(phase2): add signal ingestion API with validation

- POST /signals endpoint with Pydantic validation
- Authorization header required (bearer token)
- Returns 201 Created with signal ID on success
- Returns 400 Bad Request with specific error on validation failure
- Tests pass: all CRUD operations verified

fix(phase3): prevent race condition in theme synthesis

- Add database transaction to theme generation
- Ensure signals aren't modified during clustering
- Add lock on weekly_briefs table

docs(phase4): update README with current status

- Phase 3 complete: signals API and list view working
- Phase 4 in progress: theme synthesis engine
- Added manual testing procedures to TESTING.md

refactor(signals): simplify confidence aggregation logic

- Remove unnecessary nested loops
- Use numpy for confidence calculations
- Performance improvement: 50% faster for 1000 signals
```

### Before Committing

1. **Run tests:**
   ```bash
   pytest backend/tests/ -v
   npm test
   ```

2. **Check code style:**
   ```bash
   black backend/
   npm run format
   ```

3. **Run linter:**
   ```bash
   pylint backend/app/
   npm run lint
   ```

4. **Verify changes:**
   ```bash
   git status       # Show what's changed
   git diff         # Show exact changes
   ```

### What to Include / Exclude

**Include in commit:**
- Source code (app/ directory)
- Tests (tests/ directory)
- Models and schemas
- Updated documentation (README.md, TESTING.md, AGENTS.md)
- Updated .env.example (not .env itself)
- Dependency files (requirements.txt, package.json)

**Never commit:**
- `.env` files (use .env.example)
- `node_modules/` directory
- `__pycache__/` or `.pyc` files
- `.DS_Store` or IDE settings
- Secrets or API keys
- Build artifacts (`dist/`, `build/`)

### Commit Workflow

```bash
# Create feature branch
git checkout -b feature/phase2-signals

# Make changes, test, format, lint

# Stage specific files
git add backend/app/routes.py backend/app/schemas.py

# Show what's staged
git diff --cached

# Commit with message
git commit -m "feat(phase2): add signal ingestion endpoint

- POST /signals with full validation
- Bearer token auth required
- Tests pass: 12/12 signal CRUD tests pass"

# Repeat for next logical change

# When phase complete, push (don't force push!)
git push origin feature/phase2-signals

# Create pull request or wait for code review
```

---

## Code Style & Conventions

### Python Code Style

**Standard:** PEP 8

**Tools:**
- **Format:** `black` (automatic formatting)
- **Lint:** `pylint` or `flake8`

**Key Rules:**
```python
# Line length: 88 characters (black default)
# Indentation: 4 spaces (never tabs)

# Naming conventions
def calculate_confidence():        # Functions: snake_case
class SignalResponse:              # Classes: PascalCase
BATCH_SIZE = 100                   # Constants: UPPER_CASE
is_valid = True                    # Booleans: is_*, has_*, should_*

# Comments explain "why" not "what"
# ❌ Bad: Get signal from database
signal = db.query(Signal).first()

# ✅ Good: Fetch latest signal to check if curator already submitted this topic
signal = db.query(Signal)\
    .filter(Signal.topic == topic)\
    .order_by(Signal.created_at.desc())\
    .first()

# Docstrings on functions and classes
def synthesize_themes(signals: list[Signal]) -> list[Theme]:
    """
    Cluster signals into themes by topic and entity proximity.

    Args:
        signals: List of Signal objects from past 7 days

    Returns:
        List of Theme objects, ranked by impact

    Raises:
        ValueError: If signals list is empty
    """
    pass

# Error handling
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Validation failed: {e}")
    raise ValidationError(f"Invalid input: {e}")
```

### TypeScript / React Code Style

**Standard:** Airbnb JavaScript Style Guide

**Tools:**
- **Format:** Prettier
- **Lint:** ESLint

**Key Rules:**
```typescript
// Import order: React → libraries → local
import React, { useState } from 'react'
import axios from 'axios'
import { Signal } from '../api/types'
import SignalCard from './SignalCard'

// Naming conventions
const signal: Signal = {}              // Variables: camelCase
function handleFormSubmit() {}         // Functions: camelCase
interface Signal {}                    // Types: PascalCase
const BATCH_SIZE = 100                 // Constants: UPPER_CASE

// Component naming
function Dashboard() {}                // Components: PascalCase
export default Dashboard

// Props typing
interface DashboardProps {
  currentBrief: Brief
  onRefresh: () => void
}

function Dashboard({ currentBrief, onRefresh }: DashboardProps) {
  return <div>...</div>
}

// Comments explain "why"
// ✅ Good: Fetch brief on mount and when phase changes
useEffect(() => {
  refreshBrief()
}, [currentPhase])

// Error handling
try {
  const response = await axios.get<Brief>('/briefs/current')
  setBrief(response.data)
} catch (error) {
  const message = error instanceof Error ? error.message : 'Unknown error'
  setError(message)
}
```

### General Principles

- **DRY (Don't Repeat Yourself):** Extract common logic to functions/components
- **YAGNI (You Aren't Gonna Need It):** Don't add features you don't need yet
- **Naming:** Clear intent (`validate_url` not `check_url`, `is_valid` not `flag`)
- **Comments:** Explain decisions, not obvious code
- **Logging:** Use for debugging, not print statements
- **Error Handling:** Always catch and handle gracefully

---

## Dependency Management

### Principle: Minimize Dependencies

Each dependency is a liability:
- More to update
- More security patches
- Larger bundle size (frontend)
- Slower install time
- More potential bugs

**Before adding a package:**
1. Check if stdlib/built-in available
2. Verify it's well-maintained and widely-used
3. Explain why it's needed
4. Check for alternatives

### Python Dependencies

**Current Stack (Minimal):**
```
fastapi              # Web framework (fast, async-ready)
sqlalchemy           # ORM (database abstraction)
psycopg2             # PostgreSQL driver
pydantic             # Validation (request/response)
apscheduler          # Job scheduling (weekly brief)
```

**Development Only:**
```
pytest               # Testing
black                # Code formatting
pylint               # Linting
```

**Adding a Package:**
```bash
# Add to requirements.txt with comment explaining why
pip install package-name
pip freeze > requirements.txt

# Add comment in requirements.txt
package-name==1.2.3  # Used for [specific purpose]
```

**Updating Packages:**
```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all (use caution)
pip install --upgrade -r requirements.txt
```

### JavaScript Dependencies

**Current Stack (Minimal):**
```
react                # UI framework
typescript           # Type safety
tailwindcss          # CSS framework
axios                # HTTP client
react-router-dom     # Routing
```

**Development Only:**
```
vite                 # Build tool
vitest               # Testing
eslint               # Linting
prettier             # Formatting
```

**Adding a Package:**
```bash
# Add to package.json
npm install package-name

# Add comment in package.json if non-obvious
"package-name": "^1.2.3"  // Used for [specific purpose]
```

**Updating Packages:**
```bash
# Check for updates
npm outdated

# Update specific package
npm install package-name@latest

# Update all
npm update
```

### Lock Files

**Keep in git:**
- `requirements.txt` (Python) — pins exact versions
- `package-lock.json` (JavaScript) — pins exact versions

**Ensures reproducible builds** across environments.

---

## Development Environment Setup

### First-Time Setup

```bash
# 1. Clone repo (already done if you're here)
git clone <repo-url>
cd Prototype\ 3/

# 2. Copy environment template
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Set env vars
# Edit .env files with actual values (CURATOR_TOKEN, API_URL, etc.)

# 4. Start services
docker-compose up

# 5. Verify everything works
curl http://localhost:8000/health
curl http://localhost:3000
pytest backend/tests/ -v

# 6. You're ready to develop!
```

### Daily Development

```bash
# 1. Start fresh
docker-compose up

# 2. Read current status
cat README.md | grep -A 5 "Current Status"

# 3. Read next phase
grep -A 20 "Phase X:" ../from-thinking-to-coding/2-create-a-plan/implementation-plan.md

# 4. Make changes, test frequently
# ... make code changes ...
pytest backend/tests/ -v
npm test

# 5. Commit when feature complete
git add <files>
git commit -m "feat(phaseX): description"

# 6. Update documentation
# ... update README, TESTING, AGENTS files ...
```

### When Adding New Dependencies

```bash
# 1. Before installing, ask:
# - Is there a stdlib alternative?
# - Is this well-maintained?
# - Are there lighter alternatives?

# 2. Install and verify it works
pip install package-name
python -c "import package_name"

# 3. Add to requirements.txt with comment
# 4. Update .env.example if new config needed
# 5. Commit requirements.txt

# 6. Document in AGENTS.md why it was added
```

---

## Performance Considerations

### Backend

**Avoid:**
- N+1 queries (query signals, then query entities for each signal)
- Large in-memory sorting (use database ordering)
- Blocking I/O (use async)

**Do:**
- Use database indexes (created in models.py)
- Batch operations when possible
- Cache frequently accessed data

### Frontend

**Avoid:**
- Rendering 1000s of items (use virtualization)
- Inline functions in render (create outside component)
- Large bundle size (code split)

**Do:**
- Lazy load components
- Memoize expensive calculations
- Use React DevTools Profiler to identify slowness

---

