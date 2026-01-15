# Deployment Guide - Render.com

This guide covers deploying the STM Intelligence Brief System to Render.com using the Blueprint specification.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code must be pushed to a GitHub repository
3. **OpenAI API Key**: Required for AI-powered brief generation
4. **Environment Variables**: Review `.env.example` for required configuration

## Architecture

The application consists of three services:

1. **PostgreSQL Database** (Render managed PostgreSQL with pgvector)
2. **Backend API** (FastAPI with Docker)
3. **Frontend** (React/Vite static site)

## Deployment Steps

### 1. Push Code to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create New Blueprint on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and configure services

### 3. Configure Required Environment Variables

Before deploying, you MUST set these environment variables in the Render dashboard:

#### Backend Service (`stm-intelligence-api`)

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key (get from https://platform.openai.com/api-keys)
- `ALLOWED_ORIGINS`: Your frontend URL (format: `https://your-frontend.onrender.com`)

**Auto-Generated (by Render):**
- `DATABASE_URL`: PostgreSQL connection string
- `CURATOR_TOKEN`: Secure authentication token

**Optional (for advanced features):**
- `LINKEDIN_EMAIL`: LinkedIn scraping (see LINKEDIN_SCRAPING_GUIDE.md)
- `LINKEDIN_PASSWORD`: LinkedIn password
- `EMAIL_IMAP_SERVER`: Email ingestion (e.g., `imap.gmail.com`)
- `EMAIL_USERNAME`: Email account
- `EMAIL_PASSWORD`: Email password or app-specific password

### 4. Deploy Services

1. Click **"Apply"** to create all services
2. Render will automatically:
   - Create PostgreSQL database with pgvector extension
   - Build and deploy backend API (10-15 minutes)
   - Build and deploy frontend static site (5 minutes)
3. Wait for all services to show "Live" status

### 5. Update ALLOWED_ORIGINS

After frontend deploys:

1. Copy frontend URL from Render dashboard
2. Go to Backend service → Environment
3. Update `ALLOWED_ORIGINS` to: `https://your-frontend-url.onrender.com`
4. Save changes (backend will restart)

### 6. Verify Deployment

#### Check Backend Health

```bash
curl https://stm-intelligence-api.onrender.com/health
# Expected: {"status":"ok","version":"1.0.0"}
```

#### Check Frontend

Visit your frontend URL and verify:
- Dashboard loads without errors
- "Weekly Intelligence Brief" appears
- No console errors about CORS

### 7. Initial Setup

1. **Get Curator Token**:
   - Go to Backend service in Render dashboard
   - Click "Environment" tab
   - Copy `CURATOR_TOKEN` value

2. **Login as Curator**:
   - Click "Admin Panel" in the header
   - Paste the curator token
   - You should see admin features

3. **Trigger First Collection**:
   - Navigate to Admin → Signals List
   - Click "Collect Signals Now"
   - Wait 1-2 minutes for collection

4. **Generate First Brief**:
   - Click refresh icon in header (or Admin → Generate Brief)
   - Wait 2-3 minutes for AI generation
   - Brief should appear on dashboard

## Monitoring & Management

### View Logs

Access logs in Render dashboard:
- **Backend**: Shows API requests, scheduled jobs, errors
- **Frontend**: Shows build process
- **Database**: Shows connections and queries

### Scheduled Collection

Signals are automatically collected daily at 9 AM UTC. Check backend logs for:
```
[INFO] Starting scheduler...
[INFO] Next collection at 2024-XX-XX 09:00:00 UTC
```

### Manual Operations

#### Trigger Collection
Admin → Signals → "Collect Signals Now"

#### Generate Brief
Click refresh icon in header or Admin → Generate Brief

#### Download PDF
View brief → "Download PDF" button

## Troubleshooting

### Backend Won't Start

**Check:**
1. Environment variables are set (especially `OPENAI_API_KEY`)
2. Database service is "Live" and healthy
3. Backend logs for specific errors

**Common Issues:**
- Missing `OPENAI_API_KEY` → Set in Environment tab
- Database connection timeout → Restart backend service
- Migration failures → Check database is accessible

### Frontend Shows API Errors

**Check:**
1. Backend service is "Live"
2. `VITE_API_URL` points to correct backend URL
3. `ALLOWED_ORIGINS` includes frontend URL
4. CORS errors in browser console

**Fix:**
- Update `ALLOWED_ORIGINS` in backend environment
- Verify backend URL in frontend environment
- Check backend health endpoint works

### PDF Download Fails

**Check:**
1. WeasyPrint dependencies installed (they are in Dockerfile)
2. Backend logs show WeasyPrint errors
3. Brief exists (try accessing /briefs/current first)

**Fix:**
- Usually fixed by redeploying backend
- Check system dependencies are in Dockerfile

### No Signals Collected

**Check:**
1. Data sources configured (Admin → Data Sources)
2. Default RSS feeds exist in database
3. Collection job scheduled (backend logs)

**Fix:**
- Manually trigger collection: Admin → "Collect Signals Now"
- Check backend logs for collection errors
- Verify RSS feed URLs are accessible

## Cost & Scaling

### Current Cost (Starter Plans)

| Service | Monthly Cost |
|---------|-------------|
| PostgreSQL Database | $7 |
| Backend Web Service | $7 |
| Frontend Static Site | Free |
| **Total** | **$14/month** |

### Scaling Options

**Standard Plans** ($25/month per service):
- 2GB RAM, 1 CPU
- Better for production workloads
- Faster response times

**Professional Plans** ($85+/month):
- Read replicas for database
- Multiple backend instances
- Load balancing

## Security

1. **Rotate Curator Token** every 90 days:
   - Generate new token: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Update in Render environment

2. **API Key Security**:
   - Never commit to git
   - Use Render's environment variables only
   - Rotate if compromised

3. **Database Access**:
   - Render automatically uses SSL
   - Passwords auto-generated and secure
   - Limit connections to Render services only

## Backup & Recovery

### Database Backups

Render automatically backs up databases daily:
- 7 days of daily backups
- Point-in-time recovery available

**Manual Backup:**
```bash
# Get DATABASE_URL from Render dashboard
pg_dump $DATABASE_URL > backup.sql
```

**Restore:**
1. Render Dashboard → Database → Backups
2. Select backup → Restore

### Rollback Deployment

1. Render Dashboard → Service → Events
2. Find previous successful deploy
3. Click "Rollback to this version"

## Support Resources

- **Render Docs**: https://render.com/docs
- **Render Support**: Dashboard → Chat support
- **OpenAI Help**: https://help.openai.com
- **Project Issues**: Check backend logs first

## Next Steps

After successful deployment:

1. ✅ Configure additional data sources (if needed)
2. ✅ Set up email/Slack alerts
3. ✅ Share curator credentials with team
4. ✅ Schedule weekly brief reviews
5. ✅ Monitor resource usage and costs

Congratulations! Your STM Intelligence Brief System is now live on Render! 🎉
