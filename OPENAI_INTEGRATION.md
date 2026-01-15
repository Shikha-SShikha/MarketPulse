# OpenAI Integration for AI-Powered Brief Generation

## Overview

The STM Intelligence Brief System now uses **OpenAI's GPT-4o-mini** to generate contextual, personalized "Why This Matters" (So What) and "Action Items" (Now What) content for weekly briefs.

## Why OpenAI?

**Before (Template-Based):**
- ❌ All "So What" sections used the same 2 templates
- ❌ Generic, repetitive explanations
- ❌ Action items were boilerplate ("Monitor developments...")
- ❌ No context from actual signal content

**After (AI-Powered):**
- ✅ Unique explanations tailored to each theme
- ✅ Context-aware based on actual signals
- ✅ Specific, actionable recommendations
- ✅ Professional, varied writing style
- ✅ Sales team gets better intelligence

## Setup Instructions

### 1. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key (starts with `sk-...`)

### 2. Add API Key to Backend

Edit `backend/.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4o-mini  # Cost-effective, fast model
OPENAI_TEMPERATURE=0.7    # Balance creativity & consistency
```

### 3. Restart Backend

```bash
docker compose restart backend
```

## How It Works

### "So What" (Why This Matters) Generation

**Input:**
- Topic (e.g., "AI/ML", "Open Access")
- Entities involved (e.g., "Springer Nature", "Elsevier")
- Impact areas (e.g., "Tech", "Ops")
- Evidence snippets from signals

**OpenAI Prompt:**
```
You are writing a "Why This Matters" section for a weekly intelligence
brief for STM publishing sales teams.

Topic: {topic}
Entities: {entities}
Impact areas: {impact_areas}

Signals:
- Springer Nature: Announces new AI-powered peer review system...
- Elsevier: Launches machine learning platform for...

Write 1-2 sentences explaining WHY this matters for STM publishing
suppliers. Focus on market shifts, business implications, and strategic
importance for sales teams.
```

**Output Example:**
> "The convergence of major publishers (Springer Nature, Elsevier) adopting AI-powered review systems signals a fundamental shift in editorial workflows. This creates immediate opportunities for service providers offering AI integration expertise and poses competitive risks for those relying on traditional manual processes."

### "Now What" (Action Items) Generation

**Input:** Same as above

**OpenAI Prompt:**
```
Generate 2-3 SPECIFIC, ACTIONABLE bullet points for sales teams at
STM publishing service providers.

Focus on:
- Concrete actions (not generic "monitor")
- Client conversations
- Competitive positioning
- Business opportunities
```

**Output Example:**
- Prepare a competitive analysis comparing Springer Nature's AI review system with client workflows to identify automation gaps
- Reach out to accounts using traditional peer review to discuss AI-assisted quality control solutions
- Develop case studies highlighting successful AI integration projects for upcoming Q1 pitches

## Fallback Behavior

The system includes automatic fallbacks:

1. **No API Key:** Uses template-based generation (original system)
2. **API Error:** Falls back to templates and logs error
3. **Invalid Response:** Falls back to templates

This ensures briefs are **always generated**, even if OpenAI fails.

## Cost Estimation

**Model:** GPT-4o-mini
**Cost:** ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

**Per Brief:**
- Average: ~500 input tokens, ~150 output tokens per theme
- 5 themes per week = ~2,500 input, ~750 output tokens
- **Cost per brief: ~$0.001** (less than 1 cent)
- **Monthly cost (4 briefs): ~$0.004** (less than half a penny)

**Extremely cost-effective for the value provided!**

## Testing

### Test Without OpenAI (Template Mode)

Leave `.env` with default:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

Generate brief:
```bash
curl -X POST http://localhost:8000/admin/generate-brief \
  -H "Authorization: Bearer dev-token-change-in-production"
```

Check logs for: `"Using template-based generation (OpenAI not configured)"`

### Test With OpenAI (AI Mode)

Set real API key in `.env`, restart backend, generate brief.

Check logs for: `"Generated So What with OpenAI for theme: {title}"`

### Compare Outputs

1. Generate brief in template mode → Save output
2. Delete brief from database
3. Add OpenAI API key, restart
4. Generate brief again → Compare quality

You should see more specific, varied, actionable content!

## Configuration Options

### Model Selection

**gpt-4o-mini** (Default - Recommended):
- Fast, cost-effective
- Great quality for this use case
- ~$0.001 per brief

**gpt-4o**:
- Higher quality
- ~10x more expensive
- Overkill for this task

**gpt-3.5-turbo**:
- Cheaper than gpt-4o-mini
- Lower quality
- Not recommended

### Temperature

**0.7** (Default - Recommended):
- Good balance of creativity and consistency
- Varied but professional writing

**0.3-0.5**:
- More conservative, consistent
- Less variation in style

**0.8-1.0**:
- More creative, varied
- Risk of less professional tone

## Troubleshooting

### Brief Still Uses Templates

**Check:**
1. Is `OPENAI_API_KEY` set in `.env`?
2. Did you restart backend after setting it?
3. Check backend logs for OpenAI errors

### OpenAI API Errors

**Common Issues:**
- **401 Unauthorized:** Invalid API key
- **429 Rate Limit:** Too many requests (unlikely at <$0.001/brief)
- **500 Server Error:** OpenAI service issue (falls back to templates)

**Solution:** System automatically falls back to templates on error.

### Quality Issues

**If outputs are too generic:**
- Increase temperature to 0.8-0.9
- Check that signals have good evidence snippets

**If outputs are too creative:**
- Decrease temperature to 0.5-0.6
- Switch to gpt-4o for more consistent quality

## Future Enhancements

Potential improvements:
1. **Theme title generation with AI** - More descriptive titles
2. **Executive summary generation** - Brief-level summary
3. **Entity sentiment analysis** - Track positive/negative signals
4. **Trend detection** - Identify emerging patterns across weeks

## Questions?

See:
- OpenAI API Docs: https://platform.openai.com/docs
- Pricing: https://openai.com/api/pricing/
- Rate limits: https://platform.openai.com/docs/guides/rate-limits
