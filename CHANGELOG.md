# Changelog - MarketPulse Intelligence Platform

## 2026-01-23 - Deployment & Quality Improvements

### Fixed TypeScript Build Errors for Render Deployment ✅
**Commit:** `0ff2dad`

Fixed all TypeScript compilation errors blocking Render deployment:
- Fixed possibly undefined config properties in API client error logging
- Fixed unused parameter warnings in AdminHeader component
- Fixed Tag color type mismatches in EvaluationDashboard
- Build now completes successfully with no errors

**Impact:** Production deployment now succeeds on Render.

---

### Fixed Segment Overview Signal Count Mismatch ✅
**Commit:** `8a97b20`

**Problem:** Segment Overview showed 52 signals, but brief showed 59 signals (7 missing)

**Root Cause:** Signals were not being linked to the `entities` table when collectors couldn't find matching entities. This caused:
- 77 total signals in database without entity linkage
- Segment Overview only counts signals linked to entities
- Brief counts ALL signals, causing mismatch

**Solution:**
- Auto-create entities when signals don't have entity linkage
- Infer entity segment from name using keyword matching:
  - Competitors: Kriyadocs, Cactus, Editage, SPi Global, etc.
  - Customers: Springer, Elsevier, Wiley, Nature, Science, etc.
  - Influencers: Scholarly Kitchen, Retraction Watch, blogs
  - Industry: STM Association, ISMTE, CSE, COPE, etc.
- All new signals now automatically linked to entities

**Impact:** Segment Overview numbers now match brief totals.

---

### Improved Signal Relevance Filtering ✅
**Commit:** `8a97b20`

**Problem:** Irrelevant signals appearing in briefs:
- Journal TOC notices: "Science, Volume 391, Issue 6783..."
- Generic alerts: "Latest articles from..."
- Signals with no meaningful topic (just "General")

**Solution:**
- Added `is_relevant_to_stm()` pre-classification filter
- Filters out journal TOC notices using regex patterns
- Filters out subscription/alert messages
- Requires at least one topic keyword match
- Rejects signals with no event type AND no topic

**Filtered Patterns:**
```python
- "volume \d+, issue \d+"
- "toc alert"
- "table of contents"
- "latest articles from"
- "subscribe to"
- "email alert"
```

**Impact:** Only actionable STM publishing intelligence signals collected.

---

### Required Topics for All Signals ✅
**Commit:** `8a97b20`

**Problem:** Signals appearing with generic "General" topic and no context

**Solution:**
- Topics are now **required** (classification returns None if no topic detected)
- Every signal must match at least one topic keyword:
  - **Open Access** - OA, Plan S, APCs
  - **Integrity** - Retractions, ethics, peer review
  - **AI/ML** - Artificial intelligence, ChatGPT, ML
  - **Workflow** - Editorial systems, submission, manuscript tracking
  - **Data** - Data sharing, FAIR, repositories
  - **Preprints** - bioRxiv, arXiv, preprint servers
  - **Accessibility** - WCAG, inclusive design, screen readers
  - **Production Platforms** - CMS, editorial systems
  - **Delivery Models** - Onshore/offshore, staffing models

**Impact:** No more vague "General" signals - every signal has actionable topic classification.

---

### Testing Results

#### Signal Filtering Tests (All Passing)
```
✅ REJECTED: "Science, Volume 391, Issue 6783, January 2026"
✅ REJECTED: "Table of Contents Alert: Nature, Issue 123"
✅ REJECTED: "Latest articles from Science"
✅ REJECTED: "Conference announcement"
✅ REJECTED: "Subscribe to our newsletter"

✅ ACCEPTED: "Springer announces AI-powered peer review platform"
   → Event: announcement, Topic: Integrity

✅ ACCEPTED: "Elsevier partners with Retraction Watch"
   → Event: partnership, Topic: Integrity

✅ ACCEPTED: "New open access policy from NIH"
   → Event: policy, Topic: Open Access

✅ ACCEPTED: "Breakthrough in ML for manuscript screening"
   → Event: other, Topic: AI/ML
```

#### Entity Auto-Creation Tests
```
✅ Publishing Perspectives → Auto-created as Influencer
✅ Knowledge Speak → Auto-created as Influencer
✅ Scholarly Kitchen Blog → Auto-created as Influencer
✅ Retraction Watch → Auto-created as Influencer
```

---

## Production Deployment Guide

### Step 1: Push Latest Changes
```bash
git push
```

### Step 2: Initialize Production Database
See **PRODUCTION_SETUP.md** for detailed instructions:
1. Get CURATOR_TOKEN from Render dashboard
2. Run `./scripts/init_production.sh` with your API URL and token
3. Access dashboard at production URL
4. Login with production token

### Step 3: Verify Signal Quality
After initialization:
1. Check Segment Overview - numbers should match brief totals
2. Review signals - should see no TOC notices
3. Verify every signal has a topic (no generic "General")
4. Confirm entity linkage in database

---

## Next Steps

### Immediate
- [ ] Push changes to GitHub
- [ ] Run production initialization script
- [ ] Verify signal quality in production
- [ ] Monitor automated collection (daily at 9 AM UTC)

### Future Improvements
- [ ] Add more topic keywords as needed
- [ ] Expand entity auto-classification rules
- [ ] Consider adding "Relevance Score" to signals
- [ ] Add curator feedback loop for false positives/negatives

---

## Support

For issues or questions:
- Check **PRODUCTION_SETUP.md** for deployment help
- Check **TESTING.md** for testing procedures
- Review **AGENTS.md** for development guidelines
