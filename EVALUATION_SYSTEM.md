# AI Output Evaluation System

## Overview

Comprehensive quality assurance system for AI-generated content in the STM Intelligence Brief application. Ensures all briefs, themes, and summaries meet 95%+ quality standards.

## Architecture

### Backend Components

**1. Database Schema** (`backend/app/models.py`)
- **EvaluationRun** - Stores quality scores and metadata
  - Tracks: hallucination, grounding, relevance, actionability, coherence scores
  - Pass/fail status with configurable threshold (default: 9.5/10 = 95%)
  - Evaluator model and method tracking
- **EvaluationIssue** - Detailed issue tracking
  - Issue type, severity, description
  - Links to affected signals and entities
  - Structured details for analysis

**2. Evaluation Logic** (`backend/app/evaluations.py`)

**Rule-Based Hallucination Checks (Priority #1):**
- Signal ID existence validation
- Entity validation against source signals
- Data fabrication detection
- Scoring: 10.0 (perfect) with penalties per issue (-3.0 critical, -1.5 major, -0.5 minor)

**LLM-as-Judge Quality Scoring:**
- Uses GPT-4o-mini for quality assessment
- Evaluates 4 dimensions (0-10 scale):
  - **Grounding:** Evidence support quality
  - **Relevance:** Relevance to STM sales teams
  - **Actionability:** Clarity of recommended actions
  - **Coherence:** Logical consistency

**3. API Endpoints** (`backend/app/routes.py`)
- `POST /evaluations/run` - Run evaluation on content
- `GET /evaluations` - List evaluations with filters
- `GET /evaluations/stats` - Monitoring statistics

### Frontend Components

**1. Evaluation Dashboard** (`frontend/src/pages/EvaluationDashboard.tsx`)

**Summary Stats Section:**
- Total evaluations count
- Pass/fail counts with visual indicators
- Pass rate with progress bar (95% target)
- Average overall score

**Score Breakdown Section:**
- Individual dimension scores with progress bars
- Visual indicators for each metric
- Easy identification of weak areas

**Issue Tracking:**
- Issue count by type
- Breakdown of problem categories

**Recent Evaluations Table:**
- Content type filtering
- Status filtering (all/passed/failed)
- Complete score breakdown
- Issue count per evaluation

**Recent Failures Section:**
- Detailed failure information
- Issue lists with severity tags
- Score breakdowns for debugging

**2. Navigation**
- Added to AdminHeader component
- Accessible via main navigation menu
- Route: `/admin/evaluations`

## Features

### Quality Metrics

**Hybrid Evaluation Approach:**
1. **Rule-Based Checks** - Fast, deterministic hallucination detection
2. **LLM-as-Judge** - Nuanced quality assessment
3. **Combined Scoring** - Average of all dimensions

**Traceability:**
- All issues linked to source signals
- Entity tracking in problems
- Structured details for investigation

**Continuous Improvement:**
- Track metrics over time
- Identify patterns in failures
- Monitor specific issue types

### Monitoring Dashboard

**Time Range Filtering:**
- Last 7 days
- Last 30 days
- Last 90 days

**Status Filtering:**
- All evaluations
- Passed only
- Failed only

**Visual Indicators:**
- Color-coded scores (green/yellow/red)
- Progress bars for pass rates
- Tags for statuses and severities
- Icons for pass/fail states

## Usage

### Running Evaluations

**Manual Evaluation:**
```bash
curl -X POST "http://localhost:8000/evaluations/run?content_type=theme&content_id=<theme-id>"
```

**Programmatic Evaluation:**
```python
from app.evaluations import evaluate_content

eval_run = evaluate_content(
    db=db,
    content_type="theme",
    content_id=theme.id,
    content_data={
        'title': theme.title,
        'so_what': theme.so_what,
        'now_what': theme.now_what,
        'key_players': theme.key_players,
        'signal_ids': theme.signal_ids,
    }
)
```

### Viewing Results

**Dashboard Access:**
1. Navigate to `/admin/evaluations`
2. Select time range filter
3. Filter by status if needed
4. Review overall statistics
5. Investigate individual evaluations
6. Examine failures for patterns

**API Access:**
```bash
# Get statistics
curl http://localhost:8000/evaluations/stats

# List evaluations
curl http://localhost:8000/evaluations?passed=false&limit=10

# Filter by content type
curl http://localhost:8000/evaluations?content_type=theme
```

## Test Results

**Sample Evaluation (from test_evaluations.py):**
```
Test Theme: "AI-Powered Publishing Tools Gaining Traction"

Overall Score: 9.80/10 ✅ PASSED
Threshold: 9.5/10

Dimensional Scores:
- Hallucination: 10.00/10 (no fabricated data)
- Grounding: 10.00/10 (perfectly supported by evidence)
- Relevance: 10.00/10 (highly relevant to STM sales)
- Actionability: 9.00/10 (clear actions, could be more specific)
- Coherence: 10.00/10 (logically sound)

Issues Found: 1 minor
- [MINOR] poor_advice: While the next steps are actionable,
  they could benefit from more specificity regarding
  how to assess AI capabilities.

Pass Rate: 100% (exceeds 95% target)
```

## Configuration

**Evaluation Settings** (in evaluations.py):
- Default threshold: 9.5/10 (95%)
- Hallucination penalty (critical): -3.0
- Hallucination penalty (major): -1.5
- Hallucination penalty (minor): -0.5
- LLM model: gpt-4o-mini
- Evaluation method: hybrid

## Future Enhancements

**Planned Features:**
1. Automatic evaluation on content generation
2. Email alerts for failures
3. Trend analysis and charts
4. Issue categorization improvements
5. A/B testing of prompts
6. Benchmark tracking over time

## Troubleshooting

**Common Issues:**

1. **Low Hallucination Scores:**
   - Check signal ID references
   - Verify entity names match source signals
   - Ensure no fabricated statistics

2. **Low Grounding Scores:**
   - Review evidence support in source signals
   - Check if insights go beyond available data
   - Verify claims are directly supported

3. **Low Actionability Scores:**
   - Make recommendations more specific
   - Include clear steps and owners
   - Add measurable outcomes

4. **API Errors:**
   - Ensure OpenAI API key is configured
   - Check database connectivity
   - Verify content IDs exist

## Files

**Backend:**
- `backend/app/models.py` - Database models
- `backend/app/evaluations.py` - Evaluation logic
- `backend/app/routes.py` - API endpoints
- `backend/app/schemas.py` - Response schemas
- `backend/test_evaluations.py` - Test script
- `backend/migrations/versions/a56385b6e2fb_add_evaluation_tables.py` - Migration

**Frontend:**
- `frontend/src/pages/EvaluationDashboard.tsx` - Dashboard UI
- `frontend/src/components/AdminHeader.tsx` - Navigation
- `frontend/src/App.tsx` - Route configuration

## Development

**Running Tests:**
```bash
docker exec intelligence_backend python test_evaluations.py
```

**Checking Statistics:**
```bash
curl -s http://localhost:8000/evaluations/stats | python3 -m json.tool
```

**Accessing Dashboard:**
```
http://localhost:3000/admin/evaluations
```

---

**Status:** ✅ Complete and Production-Ready
**Target:** 95% pass rate - Currently: 100% ✅
**Priority:** Hallucinations > Poor Advice > Low Actionability
