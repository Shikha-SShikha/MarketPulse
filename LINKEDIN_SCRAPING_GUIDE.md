# LinkedIn Scraping Setup & Guidelines

## ⚠️ IMPORTANT WARNINGS

### Legal & Terms of Service

**LinkedIn scraping violates LinkedIn's Terms of Service.**

- LinkedIn explicitly prohibits automated scraping in their User Agreement
- Your account **will be at risk** of suspension or permanent ban
- This tool is provided for **educational/research purposes only**
- Use at your own risk

### Recommended Approach

**✅ DO:**
- Use a dedicated LinkedIn account (create new free account)
- Do NOT use your personal or company LinkedIn account
- Limit scraping to public profiles only
- Use conservative rate limits (10-15 second delays)
- Monitor for CAPTCHA challenges
- Accept that the account may get banned

**❌ DON'T:**
- Scrape private profiles or connections
- Use your personal LinkedIn credentials
- Scrape at high frequency (stick to daily collection)
- Ignore rate limits or warnings
- Expect 100% reliability

---

## Setup Instructions

### 1. Install Playwright

The LinkedIn collector requires Playwright for browser automation.

```bash
# In backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (one-time setup)
playwright install chromium
```

### 2. Create Dedicated LinkedIn Account

1. Create a new LinkedIn account (free tier is fine)
2. Use a separate email (e.g., `intelligence-bot@yourdomain.com`)
3. Complete basic profile setup (minimal connections needed)
4. **Accept that this account may get banned**

### 3. Configure Credentials

Add LinkedIn credentials to your environment configuration:

**Option A: Environment Variables**
```bash
export LINKEDIN_EMAIL="your-dedicated-account@example.com"
export LINKEDIN_PASSWORD="your-password"
```

**Option B: .env File** (recommended)
```bash
# backend/.env
LINKEDIN_EMAIL=your-dedicated-account@example.com
LINKEDIN_PASSWORD=your-password
```

**Option C: Docker Compose**
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      LINKEDIN_EMAIL: your-dedicated-account@example.com
      LINKEDIN_PASSWORD: your-password
```

---

## Creating LinkedIn Data Sources

### Monitor a Specific Profile

Track posts from an industry influencer:

```bash
curl -X POST http://localhost:8000/admin/data-sources \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ann Michael (Scholarly Kitchen)",
    "source_type": "linkedin",
    "url": "https://www.linkedin.com/in/annmichael/",
    "enabled": true,
    "default_confidence": "Medium",
    "config": {
      "target_type": "profile",
      "target_value": "annmichael",
      "max_posts": 20,
      "min_delay_seconds": 10,
      "max_delay_seconds": 15
    }
  }'
```

### Monitor a Hashtag

Track posts tagged with a specific hashtag:

```bash
curl -X POST http://localhost:8000/admin/data-sources \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LinkedIn #STMPublishing",
    "source_type": "linkedin",
    "url": "https://www.linkedin.com/feed/hashtag/stmpublishing/",
    "enabled": true,
    "default_confidence": "Medium",
    "config": {
      "target_type": "hashtag",
      "target_value": "stmpublishing",
      "max_posts": 30,
      "min_delay_seconds": 10,
      "max_delay_seconds": 15
    }
  }'
```

---

## Configuration Options

### Data Source Config

```json
{
  "target_type": "profile | hashtag",
  "target_value": "username or #hashtag",
  "max_posts": 20,               // Limit per collection (10-30 recommended)
  "min_delay_seconds": 10,       // Minimum delay between actions
  "max_delay_seconds": 15        // Maximum delay between actions
}
```

### Target Types

**1. Profile (`target_type: "profile"`)**
- Monitor specific LinkedIn profiles
- Good for: Industry influencers, thought leaders
- `target_value`: LinkedIn username (from profile URL)
- Example: `"annmichael"` from `linkedin.com/in/annmichael/`

**2. Hashtag (`target_type: "hashtag"`)**
- Monitor posts with specific hashtags
- Good for: Topic monitoring, trend tracking
- `target_value`: Hashtag without # symbol
- Example: `"stmpublishing"` for posts tagged `#stmpublishing`

---

## Recommended Influencers to Monitor

### STM Publishing Influencers

```json
[
  {
    "name": "Ann Michael",
    "username": "annmichael",
    "role": "COO, Delta Think; Contributor, Scholarly Kitchen",
    "focus": "STM strategy, Open Access, business models"
  },
  {
    "name": "Rick Anderson",
    "username": "rickanderson",
    "role": "Associate Dean, University of Utah",
    "focus": "Library perspective, acquisitions, open access"
  },
  {
    "name": "Angela Cochran",
    "username": "angelacochran",
    "role": "Publisher, American Society of Civil Engineers",
    "focus": "STM publishing, peer review, integrity"
  },
  {
    "name": "Phil Davis",
    "username": "phildavis",
    "role": "Publishing Consultant, Scholarly Kitchen Contributor",
    "focus": "Publishing metrics, open access, research trends"
  }
]
```

### Hashtags to Monitor

```
#STMPublishing
#OpenAccess
#ScholarlyCommunication
#PeerReview
#ResearchIntegrity
#AcademicPublishing
```

---

## Rate Limiting & Best Practices

### Conservative Settings (Recommended)

```json
{
  "max_posts": 20,           // Fewer posts = faster, lower risk
  "min_delay_seconds": 10,   // Never less than 10 seconds
  "max_delay_seconds": 15    // Random delays look more human
}
```

### Collection Frequency

**✅ Recommended:** Daily collection (9 AM UTC default)
**❌ Avoid:** Hourly or more frequent collection

### What to Expect

- **Scraping Time:** 3-5 minutes per profile/hashtag (20 posts)
- **Success Rate:** 80-90% (may fail on CAPTCHA, login issues)
- **Signals Extracted:** 10-15 per profile (after filtering)
- **Account Ban Risk:** Medium-High (use dedicated account)

---

## Troubleshooting

### CAPTCHA Challenges

**Symptom:** Login fails with "CAPTCHA required" message

**Solutions:**
1. Login manually to the account in a regular browser
2. Complete CAPTCHA challenge
3. Wait 24 hours before retrying automated scraping
4. Reduce scraping frequency

### Account Suspension

**Symptom:** "Account restricted" or "Unusual activity detected"

**Solutions:**
1. Account is likely banned (temporary or permanent)
2. Create new dedicated account
3. Use even more conservative rate limits
4. Consider alternative sources (RSS, web scraping)

### Login Failures

**Symptom:** "Invalid credentials" or timeout during login

**Solutions:**
1. Verify credentials in `.env` file
2. Check if account has 2FA enabled (not supported)
3. Try logging in manually first
4. Ensure Playwright browsers are installed

### No Posts Found

**Symptom:** Collection succeeds but extracts 0 signals

**Solutions:**
1. Verify target profile/hashtag is public
2. Check LinkedIn hasn't changed HTML structure (selectors may need update)
3. Profile may have no recent posts
4. Try different profile/hashtag

---

## Monitoring & Maintenance

### Check Collection Status

```bash
# View data source status
curl http://localhost:8000/admin/data-sources \
  -H "Authorization: Bearer $CURATOR_TOKEN"

# Check for errors
docker logs intelligence_backend | grep "LinkedIn"
```

### Key Metrics to Monitor

- **Success rate:** Should be >70%
- **Error count:** Increases suggest ban risk
- **Signals per collection:** Should be >5 per source
- **Collection time:** Should be <5 minutes

### When to Disable

Disable LinkedIn scraping if:
- Account gets banned (repeated)
- Success rate drops below 50%
- CAPTCHA challenges become frequent
- Better alternatives emerge (newsletters, RSS)

---

## Alternatives to Consider

If LinkedIn scraping proves too unreliable:

1. **Newsletter Subscriptions**
   - Subscribe to "This Week in STM" newsletters
   - Use email ingestion (Phase 2A.7)
   - More reliable, less maintenance

2. **Manual Monitoring**
   - 10 minutes/day curator reviews LinkedIn
   - Copy/paste relevant posts into signal form
   - Human judgment, zero ban risk

3. **Third-Party Tools**
   - ZoomInfo, PitchBook (paid services)
   - Official LinkedIn API (business account required)
   - More expensive but legitimate

---

## Security Considerations

### Credential Storage

- Store credentials in environment variables or `.env` (never in code)
- Use dedicated account (not personal credentials)
- Rotate passwords periodically
- Never commit `.env` files to version control

### Access Control

- Only curators should have access to LinkedIn credentials
- Use separate credentials for each environment (dev/prod)
- Monitor authentication logs for suspicious activity

### Data Retention

- LinkedIn posts are public but respect user privacy
- Store only essential information (text, author, date)
- Don't store profile photos or personal details
- Follow GDPR/privacy regulations for your jurisdiction

---

## Legal Disclaimer

**This tool is provided for educational and research purposes only.**

- LinkedIn's Terms of Service prohibit automated scraping
- Use of this tool may result in account suspension
- The developers assume no liability for account bans or legal issues
- Use at your own risk and ensure compliance with applicable laws
- Consider consulting legal counsel before production use

**We strongly recommend:**
1. Using RSS feeds and web scraping first (legitimate, reliable)
2. Manual LinkedIn monitoring (10 min/day, zero risk)
3. Only using LinkedIn scraping if other methods are insufficient
4. Using a dedicated account you can afford to lose
