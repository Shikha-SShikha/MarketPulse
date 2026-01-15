# Troubleshooting Guide

Common issues and solutions when developing on STM Intelligence Brief System.

---

## Backend (FastAPI) Issues

### Backend won't start / "Connection refused"

**Symptoms:** `docker-compose up` fails or backend crashes

**Solutions:**

1. Check logs for specific error:
   ```bash
   docker-compose logs backend
   ```

2. Verify database is running:
   ```bash
   docker-compose logs postgres
   # Should show "database system is ready to accept connections"
   ```

3. Verify DATABASE_URL is correct in .env:
   ```bash
   echo $DATABASE_URL
   # Should be: postgresql://postgres:postgres@postgres:5432/intelligence_db
   ```

4. Check if port is in use:
   ```bash
   lsof -i :8000
   # Kill process if needed: kill -9 <PID>
   ```

5. Reset everything (dev only):
   ```bash
   docker-compose down -v
   docker-compose up
   ```

### Migrations fail / "Table already exists"

**Symptoms:** Alembic migration fails during startup

**Solutions:**

1. Check migration status:
   ```bash
   docker-compose exec backend alembic current
   ```

2. If stuck, reset database:
   ```bash
   docker-compose down -v
   docker-compose up
   ```

3. Manually run migrations:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

### "AttributeError: 'NoneType' object has no attribute..."

**Symptoms:** Runtime error in services.py

**Solutions:**

1. Check database query returns None (missing record)
2. Add null checks in services.py
3. Return 404 instead of crashing

Example fix:
```python
signal = db.query(Signal).filter(...).first()
if not signal:
    raise NotFoundError("Signal not found")
```

### CORS error: "Access to XMLHttpRequest blocked by CORS policy"

**Symptoms:** Frontend API calls fail with CORS error

**Solutions:**

1. Verify CORS middleware configured in middleware.py:
   ```python
   allow_origins = ["http://localhost:3000", "http://localhost:5173"]
   ```

2. Verify backend returns CORS headers:
   ```bash
   curl -H "Origin: http://localhost:3000" http://localhost:8000/health -v
   # Should show: Access-Control-Allow-Origin: http://localhost:3000
   ```

3. Check ALLOWED_ORIGINS env var if using env-based config:
   ```bash
   echo $ALLOWED_ORIGINS
   ```

4. Restart backend if changed middleware:
   ```bash
   docker-compose restart backend
   ```

### Tests fail: "ImportError: No module named 'app'"

**Symptoms:** `pytest` can't find app module

**Solutions:**

1. Verify PYTHONPATH is set:
   ```bash
   export PYTHONPATH=/path/to/backend:$PYTHONPATH
   ```

2. Run tests from backend directory:
   ```bash
   cd backend
   pytest tests/ -v
   ```

3. Or run via docker:
   ```bash
   docker-compose exec backend pytest tests/ -v
   ```

### "Broken pipe" or connection timeout errors

**Symptoms:** Random errors, usually in job or long-running task

**Solutions:**

1. Check connection pool settings in database.py
2. Verify database isn't crashing (check postgres logs)
3. Restart docker if persistent:
   ```bash
   docker-compose restart
   ```

### Job not running on schedule

**Symptoms:** `generate_weekly_brief_job` doesn't run at Sunday 5 PM

**Solutions:**

1. Verify scheduler initialized (check logs for "Scheduler started"):
   ```bash
   docker-compose logs backend | grep -i scheduler
   ```

2. Verify job registered:
   ```bash
   docker-compose logs backend | grep -i "job"
   ```

3. Check if backend process is still running (jobs only run if app running)

4. Manually trigger job for testing:
   - Add test endpoint that calls job function
   - Call endpoint to verify job logic works

5. Check scheduler timezone (should be UTC):
   ```python
   # In scheduler.py
   scheduler.configure(timezone='UTC')
   ```

---

## Frontend (React) Issues

### Frontend shows "Failed to fetch" or blank page

**Symptoms:** React app shows error, can't call backend API

**Solutions:**

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   # Should return {"status": "ok"}
   ```

2. Check browser console for specific error (F12 → Console tab)

3. Verify VITE_API_URL is correct in .env:
   ```bash
   echo $VITE_API_URL
   # Should be http://localhost:8000
   ```

4. Check if frontend is calling correct endpoint:
   ```bash
   # In browser dev tools → Network tab
   # Look at request URL - should be http://localhost:8000/...
   ```

5. Restart frontend dev server:
   ```bash
   cd frontend
   npm run dev
   ```

### "Cannot find module" or "Module not found"

**Symptoms:** TypeScript compiler error

**Solutions:**

1. Verify dependencies installed:
   ```bash
   cd frontend
   npm install
   ```

2. Check import path is correct:
   ```typescript
   import { Component } from './components/Component'  // ✅ correct
   import { Component } from './Component'            // ❌ wrong
   ```

3. Rebuild TypeScript:
   ```bash
   npm run build
   ```

### Type errors: "Property 'X' does not exist on type 'Y'"

**Symptoms:** TypeScript compilation fails

**Solutions:**

1. Check API response matches expected type:
   ```typescript
   // If backend returns different shape, update type
   interface Signal {
     id: string
     entity: string
     // ...
   }
   ```

2. Add explicit types to API responses:
   ```typescript
   const response = await axios.get<Brief>('/briefs/current')
   ```

3. Use `unknown` as escape hatch (not recommended):
   ```typescript
   const data = response.data as any  // Avoid this!
   ```

### Hot reload not working

**Symptoms:** Change code but page doesn't update

**Solutions:**

1. Full page refresh (Cmd+Shift+R or Ctrl+Shift+R)

2. Stop and restart dev server:
   ```bash
   npm run dev
   ```

3. Check if Vite config is correct (vite.config.ts)

### npm install fails / dependency conflicts

**Symptoms:** `npm install` shows errors

**Solutions:**

1. Clear npm cache:
   ```bash
   npm cache clean --force
   ```

2. Delete node_modules and lock file:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Check Node version is compatible (should be 16+):
   ```bash
   node --version
   ```

---

## Database (PostgreSQL) Issues

### "Connection refused" to PostgreSQL

**Symptoms:** Can't connect to database

**Solutions:**

1. Verify PostgreSQL container is running:
   ```bash
   docker-compose ps
   # Should show postgres container as "Up"
   ```

2. Check PostgreSQL logs:
   ```bash
   docker-compose logs postgres
   ```

3. Verify port is correct (default 5432):
   ```bash
   docker-compose exec postgres psql -U postgres -c "SELECT 1"
   # If returns "1", connection works
   ```

4. Restart PostgreSQL:
   ```bash
   docker-compose restart postgres
   ```

### "FATAL: database 'intelligence_db' does not exist"

**Symptoms:** Can't connect to database

**Solutions:**

1. Create database:
   ```bash
   docker-compose exec postgres psql -U postgres -c "CREATE DATABASE intelligence_db"
   ```

2. Or reset everything:
   ```bash
   docker-compose down -v
   docker-compose up
   ```

### Data disappeared after restart

**Symptoms:** All signals/briefs gone

**Cause:** Probably used `docker-compose down -v` which deletes volumes

**Solutions:**

1. Use `docker-compose down` without `-v` to keep data:
   ```bash
   docker-compose down      # Keeps data
   docker-compose down -v   # Deletes data (dev only!)
   ```

2. If data lost, re-enter signals

3. In production, use managed database service with backups

### Slow queries / performance issues

**Symptoms:** Dashboard takes long time to load

**Solutions:**

1. Check indexes exist:
   ```bash
   docker-compose exec postgres psql -U postgres -d intelligence_db -c "\di"
   ```

2. Verify indexes are on key columns:
   - signals(entity, created_at)
   - signals(topic, created_at)
   - signals(created_at)

3. Check query execution plan:
   ```bash
   docker-compose exec postgres psql -U postgres -d intelligence_db
   EXPLAIN SELECT * FROM signals WHERE topic = 'OA' AND created_at > NOW() - INTERVAL '7 days';
   ```

4. If slow, add missing indexes in models.py

---

## Docker Issues

### "Docker daemon is not running" or "Cannot connect to Docker"

**Solutions:**

1. Start Docker (macOS/Windows):
   - Open Docker Desktop app

2. Start Docker (Linux):
   ```bash
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   # Logout and login to apply group changes
   ```

### "Port already in use"

**Symptoms:** Can't start services because port in use

**Solutions:**

1. Find what's using the port:
   ```bash
   lsof -i :8000      # Port 8000 (backend)
   lsof -i :3000      # Port 3000 (frontend)
   lsof -i :5432      # Port 5432 (database)
   ```

2. Kill the process:
   ```bash
   kill -9 <PID>
   ```

3. Or change port in docker-compose.yml:
   ```yaml
   ports:
     - "8001:8000"  # Use 8001 instead of 8000
   ```

### "Volume already exists"

**Symptoms:** `docker-compose up` fails due to volume conflict

**Solutions:**

1. Remove old volumes:
   ```bash
   docker volume ls | grep intelligence
   docker volume rm <volume-name>
   ```

2. Or reset completely:
   ```bash
   docker-compose down -v
   docker-compose up
   ```

---

## Testing Issues

### Tests pass locally but fail in CI/CD

**Causes:** Environment differences

**Solutions:**

1. Run tests in Docker to match CI environment:
   ```bash
   docker-compose exec backend pytest tests/ -v
   ```

2. Verify all env vars set in CI config

3. Use conftest.py fixtures for test database setup

### "Test database locked" or concurrent test issues

**Solutions:**

1. Run tests sequentially (not parallel):
   ```bash
   pytest tests/ -v  # Default is sequential
   ```

2. Ensure each test cleans up after itself:
   ```python
   @pytest.fixture
   def db():
       # Setup
       yield db_session
       # Cleanup
       db_session.rollback()
   ```

### Flaky tests / intermittent failures

**Causes:** Tests depend on timing, database state, or order

**Solutions:**

1. Don't depend on test order (each test should be independent)

2. Add explicit waits in integration tests:
   ```python
   time.sleep(0.1)  # Await async operations
   ```

3. Clean database before each test:
   ```python
   db.query(Signal).delete()
   db.commit()
   ```

---

## Common Gotchas

### "Session in wrong state"

**Problem:** SQLAlchemy session error

**Fix:** Always commit/rollback after changes:
```python
db.add(signal)
db.commit()
db.refresh(signal)  # Refresh from DB
```

### "Function needs to be awaited"

**Problem:** Async function not awaited

**Fix:** Use `await` in async context:
```python
async def endpoint():
    result = await async_function()  # ✅ correct
```

### "useState should be in component body"

**Problem:** React hook called conditionally

**Fix:** Move hook to top level of component:
```typescript
export function MyComponent() {
  const [state, setState] = useState('')  // ✅ top level
  return <div>...</div>
}
```

---

## Getting Help

1. **Check logs first:** `docker-compose logs <service>`
2. **Search AGENTS.md:** Patterns and gotchas documented there
3. **Check browser console:** F12 → Console tab for frontend errors
4. **Run tests:** `pytest -v` shows specific failures
5. **Restart everything:** `docker-compose down -v && docker-compose up`

---

