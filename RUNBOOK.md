# Operations Runbook - STM Intelligence Brief System

Operational procedures, troubleshooting guides, and emergency response for production deployments.

## Table of Contents
- [Quick Reference](#quick-reference)
- [Common Operations](#common-operations)
- [Incident Response](#incident-response)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Scheduled Maintenance](#scheduled-maintenance)
- [Emergency Contacts](#emergency-contacts)

---

## Quick Reference

### Service Status

```bash
# Check all services
docker compose ps

# Check backend health
curl https://api.example.com/health

# Check database
docker compose exec postgres pg_isready -U postgres

# View logs (last 100 lines)
docker compose logs backend --tail 100
docker compose logs postgres --tail 100
```

### Critical Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Health check | `{"status":"ok","version":"1.0.0"}` |
| `GET /briefs/current` | Current brief | `200` with brief data or `204` if none |
| `GET /signals` | Signal list | `200` with signals array |
| `GET /docs` | API docs | Swagger UI page |

---

## Common Operations

### 1. Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart postgres

# Restart with rebuild (if code changed)
docker compose up -d --build backend
```

### 2. View Logs

```bash
# Follow backend logs (real-time)
docker compose logs -f backend

# View last 500 lines
docker compose logs backend --tail 500

# Filter for errors
docker compose logs backend | grep ERROR

# Export logs to file
docker compose logs backend > backend_$(date +%Y%m%d).log
```

### 3. Database Operations

#### Connect to Database
```bash
# Interactive psql session
docker compose exec postgres psql -U postgres -d intelligence_db

# Run query
docker compose exec postgres psql -U postgres -d intelligence_db -c "SELECT COUNT(*) FROM signals;"
```

#### Check Database Size
```bash
docker compose exec postgres psql -U postgres -d intelligence_db -c "
SELECT
    pg_size_pretty(pg_database_size('intelligence_db')) as database_size,
    (SELECT COUNT(*) FROM signals) as signal_count,
    (SELECT COUNT(*) FROM themes) as theme_count,
    (SELECT COUNT(*) FROM weekly_briefs) as brief_count;
"
```

#### Run Migrations
```bash
# Check current version
docker compose exec backend alembic current

# Upgrade to latest
docker compose exec backend alembic upgrade head

# Rollback one version
docker compose exec backend alembic downgrade -1

# View migration history
docker compose exec backend alembic history
```

### 4. Weekly Brief Generation

#### Manual Trigger
```bash
# Generate brief now (requires curator token)
curl -X POST https://api.example.com/admin/generate-brief \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

#### Check Scheduler Status
```bash
# View scheduler logs
docker compose logs backend | grep "Scheduler"

# Expected output:
# [INFO] Scheduler started with 1 jobs:
# [INFO]   - Generate Weekly Brief: next run at 2025-12-21 17:00:00+00:00
```

#### Verify Scheduler Job
```bash
# Check if job is registered
docker compose exec backend python -c "
from app.scheduler import scheduler
for job in scheduler.get_jobs():
    print(f'{job.name}: next run {job.next_run_time}')
"
```

### 5. Add Test Data

```bash
# Add sample signal for testing
curl -X POST https://api.example.com/signals \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "Test Publisher",
    "event_type": "announcement",
    "topic": "Test Topic",
    "source_url": "https://example.com/test",
    "evidence_snippet": "This is a test signal to verify the system is working correctly. It contains more than 50 characters as required.",
    "confidence": "High",
    "impact_areas": ["Ops"]
  }'
```

---

## Incident Response

### Service Down

**Symptoms:** Health check fails, 502/503 errors

**Response:**
```bash
# 1. Check service status
docker compose ps

# 2. Check logs for errors
docker compose logs backend --tail 100

# 3. Restart affected service
docker compose restart backend

# 4. If database connection issues
docker compose restart postgres
sleep 10
docker compose restart backend

# 5. Verify recovery
curl https://api.example.com/health
```

### Database Connection Issues

**Symptoms:** "connection refused", "too many connections", timeout errors

**Response:**
```bash
# 1. Check database status
docker compose exec postgres pg_isready -U postgres

# 2. Check active connections
docker compose exec postgres psql -U postgres -c "
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE datname = 'intelligence_db';
"

# 3. If too many connections, restart services
docker compose restart backend
sleep 5
docker compose exec postgres psql -U postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'intelligence_db' AND pid <> pg_backend_pid();
"

# 4. Restart database if needed
docker compose restart postgres
sleep 10
docker compose restart backend
```

### Brief Generation Failed

**Symptoms:** No brief generated on Sunday, scheduler errors in logs

**Response:**
```bash
# 1. Check scheduler logs
docker compose logs backend | grep "Generate Weekly Brief"

# 2. Check for signals this week
docker compose exec postgres psql -U postgres -d intelligence_db -c "
SELECT COUNT(*) FROM signals
WHERE created_at >= NOW() - INTERVAL '7 days';
"

# 3. Manually trigger brief generation
curl -X POST https://api.example.com/admin/generate-brief \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Check for errors in response
# If successful, scheduler may be stuck - restart backend
docker compose restart backend
```

### High Memory Usage

**Symptoms:** Slow response times, OOM errors

**Response:**
```bash
# 1. Check memory usage
docker stats --no-stream

# 2. Check database connections
docker compose exec postgres psql -U postgres -c "
SELECT count(*) FROM pg_stat_activity;
"

# 3. Reduce connection pool if needed
# Edit backend/.env:
# DATABASE_URL=postgresql://...?pool_size=3&max_overflow=7

# 4. Restart services
docker compose restart backend
```

### Disk Space Full

**Symptoms:** "No space left on device", write errors

**Response:**
```bash
# 1. Check disk usage
df -h
docker system df

# 2. Clean Docker resources
docker system prune -a --volumes

# 3. Clean old logs
find /var/log -name "*.log" -mtime +30 -delete

# 4. Archive old database backups
find /backups -name "*.dump" -mtime +90 -delete
```

---

## Troubleshooting Guide

### Problem: CORS errors in frontend

**Symptoms:** Browser console shows CORS policy errors

**Solution:**
```bash
# 1. Check ALLOWED_ORIGINS in backend/.env
grep ALLOWED_ORIGINS backend/.env

# 2. Update to include frontend domain
# backend/.env:
ALLOWED_ORIGINS=https://dashboard.example.com,https://admin.example.com

# 3. Restart backend
docker compose restart backend
```

### Problem: 403 Forbidden when creating signals

**Symptoms:** API returns 403 when curator tries to add signals

**Solution:**
```bash
# 1. Verify token in request header
# Header should be: Authorization: Bearer <token>

# 2. Check token matches backend configuration
grep CURATOR_TOKEN backend/.env

# 3. Update token if needed
# Generate new token:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Update backend/.env and restart
docker compose restart backend
```

### Problem: Migrations failed

**Symptoms:** "relation does not exist", migration errors

**Solution:**
```bash
# 1. Check current migration version
docker compose exec backend alembic current

# 2. Check what migrations exist
docker compose exec backend alembic history

# 3. If out of sync, reset (CAUTION: loses data)
docker compose exec postgres psql -U postgres -d intelligence_db -c "
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
"

# 4. Rerun migrations
docker compose exec backend alembic upgrade head
```

### Problem: Scheduler not running

**Symptoms:** Brief not generated on Sundays, no scheduler logs

**Solution:**
```bash
# 1. Check if scheduler is enabled in logs
docker compose logs backend | grep "Scheduler started"

# 2. Verify timezone is correct (should be UTC)
docker compose exec backend date -u

# 3. Manually trigger to test
curl -X POST https://api.example.com/admin/generate-brief \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. If scheduler stuck, restart backend
docker compose restart backend
```

### Problem: Frontend shows old data

**Symptoms:** Dashboard not updating after brief generation

**Solution:**
```bash
# 1. Hard refresh browser (Ctrl+Shift+R)

# 2. Check if backend has new data
curl https://api.example.com/briefs/current

# 3. Check browser console for API errors

# 4. Clear browser cache
# Chrome: Settings > Privacy > Clear browsing data
```

---

## Scheduled Maintenance

### Weekly Tasks (Every Monday)

```bash
# 1. Check logs for errors
docker compose logs backend | grep ERROR | tail -50

# 2. Verify last brief was generated
curl https://api.example.com/briefs/current | jq '.generated_at'

# 3. Check database size
docker compose exec postgres psql -U postgres -d intelligence_db -c "
SELECT pg_size_pretty(pg_database_size('intelligence_db'));
"

# 4. Verify backups exist
ls -lh /backups/backup_*.dump | tail -7
```

### Monthly Tasks

```bash
# 1. Update dependencies (test in staging first)
docker compose exec backend pip list --outdated
cd frontend && npm outdated

# 2. Review and archive old signals (optional)
docker compose exec postgres psql -U postgres -d intelligence_db -c "
SELECT COUNT(*) FROM signals WHERE created_at < NOW() - INTERVAL '90 days';
"

# 3. Check disk space trends
df -h
du -sh /var/lib/docker/volumes

# 4. Test backup restoration
# Restore to test database and verify
```

### Quarterly Tasks

```bash
# 1. Security audit
docker compose exec backend pip-audit

# 2. Update Docker base images
# backend/Dockerfile: Update python:3.11-slim to latest
# postgres: Update to postgres:15-alpine latest

# 3. Review and update SSL certificates
sudo certbot renew --dry-run

# 4. Load testing
# Use tool like k6 or Apache Bench
ab -n 1000 -c 10 https://api.example.com/health
```

---

## Database Backup & Restore

### Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U postgres -F c \
  -f /tmp/backup_$(date +%Y%m%d).dump intelligence_db

# Copy backup out of container
docker compose cp postgres:/tmp/backup_$(date +%Y%m%d).dump ./backups/
```

### Restore

```bash
# Stop backend first
docker compose stop backend

# Restore database
docker compose exec postgres pg_restore -U postgres -d intelligence_db \
  -c /path/to/backup.dump

# Restart services
docker compose start backend
```

### Test Restore

```bash
# 1. Create test database
docker compose exec postgres psql -U postgres -c "CREATE DATABASE test_restore;"

# 2. Restore to test database
docker compose exec postgres pg_restore -U postgres -d test_restore \
  /path/to/backup.dump

# 3. Verify data
docker compose exec postgres psql -U postgres -d test_restore -c "
SELECT COUNT(*) FROM signals;
"

# 4. Drop test database
docker compose exec postgres psql -U postgres -c "DROP DATABASE test_restore;"
```

---

## Performance Optimization

### Slow Queries

```bash
# Enable query logging
docker compose exec postgres psql -U postgres -c "
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();
"

# View slow queries
docker compose exec postgres psql -U postgres -d intelligence_db -c "
SELECT query, calls, mean_exec_time, max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"
```

### Database Vacuum

```bash
# Analyze tables
docker compose exec postgres psql -U postgres -d intelligence_db -c "
VACUUM ANALYZE signals;
VACUUM ANALYZE themes;
VACUUM ANALYZE weekly_briefs;
"

# Check table bloat
docker compose exec postgres psql -U postgres -d intelligence_db -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## Security Incidents

### Suspected Unauthorized Access

```bash
# 1. Check recent signal creations
docker compose exec postgres psql -U postgres -d intelligence_db -c "
SELECT entity, created_at, curator_name
FROM signals
ORDER BY created_at DESC
LIMIT 20;
"

# 2. Check API logs for suspicious activity
docker compose logs backend | grep "POST /signals"

# 3. Rotate curator token immediately
# Generate new token
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Update backend/.env and restart
docker compose restart backend

# 5. Notify team and audit recent signals
```

### Data Breach Response

```bash
# 1. Immediately stop backend
docker compose stop backend

# 2. Take database snapshot
docker compose exec postgres pg_dump -U postgres -F c \
  -f /tmp/incident_backup_$(date +%Y%m%d_%H%M%S).dump intelligence_db

# 3. Review logs for access patterns
docker compose logs backend > incident_logs_$(date +%Y%m%d).txt

# 4. Contact security team
# 5. Follow incident response plan
```

---

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| DevOps Lead | devops@example.com | 24/7 |
| Database Admin | dba@example.com | Business hours |
| Security Team | security@example.com | 24/7 |
| Product Owner | product@example.com | Business hours |

### Escalation Path

1. **Level 1:** On-call engineer (15 min response)
2. **Level 2:** DevOps lead (30 min response)
3. **Level 3:** CTO (1 hour response)

---

## Monitoring Alerts

### Critical Alerts (Page immediately)

- Health check failed (2+ consecutive failures)
- Database connection errors
- Disk space > 90% full
- Memory usage > 90%

### Warning Alerts (Ticket/email)

- API error rate > 5%
- Slow query detected (> 5s)
- Backup failed
- SSL certificate expiring (< 30 days)

### Info Alerts (Log only)

- Brief generated successfully
- Scheduled job completed
- Service restarted

---

## Change Management

### Deploying Updates

```bash
# 1. Announce maintenance window
# 2. Backup database
# 3. Deploy to staging first
# 4. Run tests in staging
# 5. Deploy to production
# 6. Run smoke tests
# 7. Monitor for 1 hour
# 8. Announce completion
```

### Rollback Procedure

```bash
# 1. Stop services
docker compose down

# 2. Checkout previous version
git checkout <previous-tag>

# 3. Restore database if needed
docker compose exec postgres pg_restore -U postgres -d intelligence_db \
  /path/to/pre-deploy-backup.dump

# 4. Restart services
docker compose up -d

# 5. Verify health
curl https://api.example.com/health
```

---

## Notes

- Always test procedures in staging first
- Document all incidents for post-mortems
- Keep this runbook updated with new procedures
- Review and update quarterly

**Last Updated:** December 2025
