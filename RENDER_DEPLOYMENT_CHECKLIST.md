# Render Deployment Checklist

Use this checklist to deploy the STM Intelligence Brief System to Render.

## Pre-Deployment

- [ ] Code is committed and pushed to GitHub
- [ ] You have a Render account (https://render.com)
- [ ] You have an OpenAI API key (https://platform.openai.com/api-keys)
- [ ] Review `.env.example` for required variables

## Deployment

- [ ] Go to Render Dashboard → New → Blueprint
- [ ] Connect GitHub repository
- [ ] Verify `render.yaml` is detected
- [ ] Click "Apply" to create services
- [ ] Wait for services to deploy (10-15 minutes)

## Configuration

### Backend Environment Variables

- [ ] Set `OPENAI_API_KEY` (required)
- [ ] Copy auto-generated `CURATOR_TOKEN` (save securely)
- [ ] Update `ALLOWED_ORIGINS` with frontend URL
- [ ] (Optional) Set LinkedIn credentials
- [ ] (Optional) Set email ingestion credentials

### Frontend Environment Variables

- [ ] Verify `VITE_API_URL` is auto-configured to backend

## Verification

- [ ] Backend health check: `curl https://your-backend.onrender.com/health`
- [ ] Frontend loads without errors
- [ ] Login with curator token works
- [ ] Trigger signal collection (Admin → Collect Signals Now)
- [ ] Generate brief (Refresh icon in header)
- [ ] Download PDF works

## Post-Deployment

- [ ] Save curator token securely (password manager)
- [ ] Configure data sources (if needed)
- [ ] Set up Render alerts (email/Slack)
- [ ] Share access with team
- [ ] Schedule weekly brief reviews
- [ ] Monitor costs and resource usage

## Troubleshooting

If issues occur:

1. Check service status (all should be "Live")
2. Review logs in Render dashboard
3. Verify environment variables are set correctly
4. Restart services if needed
5. Check DEPLOYMENT.md for detailed troubleshooting

## Quick Reference

**Cost**: $14/month (Starter plans)

**URLs**:
- Backend: `https://stm-intelligence-api.onrender.com`
- Frontend: `https://stm-intelligence-frontend.onrender.com`
- Database: Internal connection only

**Support**:
- Render Docs: https://render.com/docs
- Render Support: Dashboard → Chat
- Full Guide: See DEPLOYMENT.md
