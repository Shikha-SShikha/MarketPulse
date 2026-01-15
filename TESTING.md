# Manual Testing Procedures

Step-by-step testing instructions for each feature. Update this file as features are added.

---

## Phase 0: Project Scaffolding

### Test 1: Backend Health Check

**Steps:**
1. Start services: `docker-compose up`
2. Wait for "Application startup complete" in logs
3. Run: `curl http://localhost:8000/health`

**Expected:** `{"status":"ok"}`

### Test 2: Frontend Loads

**Steps:**
1. Navigate to frontend: `cd frontend`
2. Install dependencies: `npm install`
3. Start dev server: `npm run dev`
4. Open browser: http://localhost:3000

**Expected:** Welcome page with "STM Intelligence Brief" header and "Phase 0 Complete" message

### Test 3: PostgreSQL Running

**Steps:**
1. Start services: `docker-compose up`
2. Check PostgreSQL: `docker-compose exec postgres psql -U postgres -c "SELECT 1"`

**Expected:** Returns `1` (database is responding)

### Test 4: CORS Configured

**Steps:**
1. Start services: `docker-compose up`
2. Test CORS: `curl -H "Origin: http://localhost:3000" http://localhost:8000/health -v`

**Expected:** Response includes `Access-Control-Allow-Origin: http://localhost:3000`

---

## Phase 1: Database Schema

*(To be added after Phase 1 implementation)*

---

## Phase 2: Signal Ingestion API

*(To be added after Phase 2 implementation)*

---

## Phase 3: Signal List & Query API

*(To be added after Phase 3 implementation)*

---

## Phase 4: Admin Signal Entry Form

*(To be added after Phase 4 implementation)*

---

## Phase 5: Signal List Management UI

*(To be added after Phase 5 implementation)*

---

## Phase 6: Theme Synthesis Engine

*(To be added after Phase 6 implementation)*

---

## Phase 7: Weekly Brief Job & API

*(To be added after Phase 7 implementation)*

---

## Phase 8: Sales Dashboard

*(To be added after Phase 8 implementation)*

---
