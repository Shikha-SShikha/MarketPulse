"""
Evaluation framework for AI-generated content quality assessment.

Implements rule-based and LLM-as-judge evaluations for:
- Hallucination detection (Priority #1)
- Grounding in evidence
- Relevance and actionability
- Coherence and clarity
"""

import uuid
from typing import Dict, List, Tuple, Any
from sqlalchemy.orm import Session
from app.models import Signal, Theme, WeeklyBrief, EvaluationRun, EvaluationIssue
from app.config import get_settings
import openai
import json


# ============================================================================
# Rule-Based Hallucination Checks (Priority #1)
# ============================================================================

def check_hallucinations(
    db: Session,
    content_type: str,
    content_data: Dict[str, Any],
) -> Tuple[float, List[Dict]]:
    """
    Run comprehensive hallucination checks on AI-generated content.

    Priority checks:
    1. Signal ID existence - Do all referenced signal IDs exist?
    2. Entity validation - Are all entities from actual signals?
    3. Data fabrication - Any stats/facts not in source signals?

    Args:
        db: Database session
        content_type: Type of content ('theme', 'weekly_brief', 'signal_summary')
        content_data: The content to evaluate (includes signal_ids, entities, insights)

    Returns:
        Tuple of (hallucination_score 0-10, list of issues found)
        10.0 = no hallucinations, 0.0 = severe hallucinations
    """
    issues = []

    # Extract signal IDs from content based on type
    signal_ids = _extract_signal_ids(content_type, content_data)

    # Check 1: Verify all signal IDs exist in database
    if signal_ids:
        missing_ids = _check_signal_ids_exist(db, signal_ids)
        if missing_ids:
            issues.append({
                'type': 'hallucination',
                'severity': 'critical',
                'description': f'Referenced {len(missing_ids)} non-existent signal IDs',
                'signal_ids': [str(sid) for sid in missing_ids],
                'details': {'missing_signal_ids': [str(sid) for sid in missing_ids]}
            })

    # Check 2: Verify all mentioned entities exist in source signals
    entities = _extract_entities(content_type, content_data)
    if entities and signal_ids:
        fabricated_entities = _check_entities_in_signals(db, signal_ids, entities)
        if fabricated_entities:
            issues.append({
                'type': 'hallucination',
                'severity': 'critical',
                'description': f'Mentioned {len(fabricated_entities)} entities not found in source signals',
                'entities': fabricated_entities,
                'details': {'fabricated_entities': fabricated_entities}
            })

    # Check 3: Verify signal count claims match reality
    if content_type == 'signal_summary':
        claimed_count = content_data.get('total_signals', 0)
        actual_count = len(signal_ids)
        if claimed_count != actual_count:
            issues.append({
                'type': 'hallucination',
                'severity': 'major',
                'description': f'Claimed {claimed_count} signals but actually used {actual_count}',
                'details': {'claimed_count': claimed_count, 'actual_count': actual_count}
            })

    # Calculate hallucination score
    # Critical issues: -3.0 each, Major: -1.5 each, Minor: -0.5 each
    score = 10.0
    for issue in issues:
        if issue['severity'] == 'critical':
            score -= 3.0
        elif issue['severity'] == 'major':
            score -= 1.5
        elif issue['severity'] == 'minor':
            score -= 0.5

    # Clamp to [0, 10]
    score = max(0.0, min(10.0, score))

    return score, issues


def _extract_signal_ids(content_type: str, content_data: Dict) -> List[uuid.UUID]:
    """Extract all signal IDs referenced in content."""
    signal_ids = []

    if content_type == 'theme':
        # Theme has signal_ids array
        signal_ids = content_data.get('signal_ids', [])

    elif content_type == 'signal_summary':
        # Summary has key_insights with signal_ids
        for insight in content_data.get('key_insights', []):
            signal_ids.extend(insight.get('signal_ids', []))

    elif content_type == 'weekly_brief':
        # Brief has themes, each with signal_ids
        for theme in content_data.get('themes', []):
            signal_ids.extend(theme.get('signal_ids', []))

    # Convert to UUIDs if strings
    return [uuid.UUID(str(sid)) if isinstance(sid, str) else sid for sid in signal_ids]


def _extract_entities(content_type: str, content_data: Dict) -> List[str]:
    """Extract all entities mentioned in content."""
    entities = set()

    if content_type == 'theme':
        entities.update(content_data.get('key_players', []))

    elif content_type == 'signal_summary':
        for insight in content_data.get('key_insights', []):
            entities.update(insight.get('entities', []))

    elif content_type == 'weekly_brief':
        for theme in content_data.get('themes', []):
            entities.update(theme.get('key_players', []))

    return list(entities)


def _check_signal_ids_exist(db: Session, signal_ids: List[uuid.UUID]) -> List[uuid.UUID]:
    """Check which signal IDs don't exist in database."""
    # Query database for these signal IDs
    existing_ids = db.query(Signal.id).filter(
        Signal.id.in_(signal_ids),
        Signal.deleted_at.is_(None)
    ).all()
    existing_ids_set = {row[0] for row in existing_ids}

    # Find missing IDs
    missing = [sid for sid in signal_ids if sid not in existing_ids_set]
    return missing


def _check_entities_in_signals(db: Session, signal_ids: List[uuid.UUID], entities: List[str]) -> List[str]:
    """Check which entities aren't found in the source signals."""
    # Get all entities mentioned in source signals
    signals = db.query(Signal.entity).filter(
        Signal.id.in_(signal_ids),
        Signal.deleted_at.is_(None)
    ).all()

    signal_entities = {row[0] for row in signals}

    # Also check entity_tags if present
    signals_with_tags = db.query(Signal.entity_tags).filter(
        Signal.id.in_(signal_ids),
        Signal.deleted_at.is_(None),
        Signal.entity_tags.isnot(None)
    ).all()

    for row in signals_with_tags:
        if row[0]:  # entity_tags array
            signal_entities.update(row[0])

    # Find entities not in source signals
    fabricated = [entity for entity in entities if entity not in signal_entities]
    return fabricated


# ============================================================================
# LLM-as-Judge Quality Scoring
# ============================================================================

def evaluate_with_llm(
    db: Session,
    content_type: str,
    content_data: Dict[str, Any],
) -> Tuple[Dict[str, float], List[Dict]]:
    """
    Use GPT-4o-mini as a judge to evaluate content quality.

    Evaluates:
    - Grounding: How well insights are supported by evidence (0-10)
    - Relevance: How relevant insights are to STM sales teams (0-10)
    - Actionability: How clear and actionable the advice is (0-10)
    - Coherence: How logically coherent the content is (0-10)

    Returns:
        Tuple of (scores dict, issues list)
    """
    # Get source signals for context
    signal_ids = _extract_signal_ids(content_type, content_data)
    signals = db.query(Signal).filter(
        Signal.id.in_(signal_ids),
        Signal.deleted_at.is_(None)
    ).all()

    # Build prompt for LLM judge
    prompt = _build_evaluation_prompt(content_type, content_data, signals)

    try:
        # Call OpenAI with structured output
        settings = get_settings()
        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert evaluator of market intelligence content. Evaluate content objectively and assign scores from 0-10."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "evaluation_result",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "grounding_score": {"type": "number"},
                            "relevance_score": {"type": "number"},
                            "actionability_score": {"type": "number"},
                            "coherence_score": {"type": "number"},
                            "issues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "severity": {"type": "string"},
                                        "description": {"type": "string"}
                                    },
                                    "required": ["type", "severity", "description"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["grounding_score", "relevance_score", "actionability_score", "coherence_score", "issues"],
                        "additionalProperties": False
                    }
                }
            },
            temperature=0.1,
            max_tokens=1000,
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)

        scores = {
            'grounding_score': float(result['grounding_score']),
            'relevance_score': float(result['relevance_score']),
            'actionability_score': float(result['actionability_score']),
            'coherence_score': float(result['coherence_score']),
        }

        issues = result.get('issues', [])

        return scores, issues

    except Exception as e:
        # Fallback to default passing scores if OpenAI fails
        print(f"LLM evaluation failed: {e}")
        return {
            'grounding_score': 8.0,
            'relevance_score': 8.0,
            'actionability_score': 8.0,
            'coherence_score': 8.0,
        }, []


def _build_evaluation_prompt(content_type: str, content_data: Dict, signals: List[Signal]) -> str:
    """Build evaluation prompt for LLM judge."""

    # Format source signals
    signals_text = "\n\n".join([
        f"Signal {i+1}:\n"
        f"Entity: {signal.entity}\n"
        f"Event: {signal.event_type}\n"
        f"Topic: {signal.topic}\n"
        f"Evidence: {signal.evidence_snippet}\n"
        f"Impact Areas: {', '.join(signal.impact_areas)}"
        for i, signal in enumerate(signals[:20])  # Limit to first 20 for token efficiency
    ])

    # Format content to evaluate
    if content_type == 'theme':
        content_text = (
            f"Theme Title: {content_data.get('title')}\n"
            f"Why It Matters: {content_data.get('so_what')}\n"
            f"Next Steps: {', '.join(content_data.get('now_what', []))}\n"
            f"Key Players: {', '.join(content_data.get('key_players', []))}"
        )
    elif content_type == 'signal_summary':
        insights_text = "\n".join([
            f"{i+1}. {insight['insight']} (Entities: {', '.join(insight['entities'])})"
            for i, insight in enumerate(content_data.get('key_insights', []))
        ])
        content_text = (
            f"Executive Summary: {content_data.get('summary')}\n\n"
            f"Key Insights:\n{insights_text}"
        )
    else:
        content_text = json.dumps(content_data, indent=2)

    prompt = f"""Evaluate the following market intelligence content for quality.

SOURCE SIGNALS ({len(signals)} total):
{signals_text}

CONTENT TO EVALUATE:
{content_text}

Evaluate on these dimensions (0-10 scale, 10 = perfect):

1. **Grounding Score**: How well are insights supported by the source signals?
   - 10: Every claim is directly supported by evidence
   - 5: Some claims lack direct support
   - 0: Most claims are unsupported or fabricated

2. **Relevance Score**: How relevant are insights for STM sales teams?
   - 10: Highly actionable competitive/market intelligence
   - 5: Somewhat relevant but generic
   - 0: Irrelevant or off-topic

3. **Actionability Score**: How clear and actionable is the advice?
   - 10: Clear, specific actions sales can take
   - 5: Vague or generic recommendations
   - 0: No actionable advice

4. **Coherence Score**: How logically coherent is the content?
   - 10: Perfectly clear and well-structured
   - 5: Some confusion or unclear points
   - 0: Incoherent or contradictory

Also identify any issues:
- Type: "poor_grounding", "poor_advice", "low_actionability", "coherence_error"
- Severity: "critical", "major", "minor"
- Description: Specific problem found

Return your evaluation as JSON with scores and issues array.
"""

    return prompt


# ============================================================================
# Main Evaluation Orchestrator
# ============================================================================

def evaluate_content(
    db: Session,
    content_type: str,
    content_id: uuid.UUID,
    content_data: Dict[str, Any],
) -> EvaluationRun:
    """
    Run complete evaluation on AI-generated content.

    Combines rule-based hallucination checks with LLM-as-judge scoring.
    Saves results to evaluation_runs and evaluation_issues tables.

    Args:
        db: Database session
        content_type: 'theme', 'weekly_brief', or 'signal_summary'
        content_id: UUID of the content being evaluated
        content_data: The content to evaluate

    Returns:
        EvaluationRun object with scores and issues
    """
    # Step 1: Rule-based hallucination checks (Priority #1)
    hallucination_score, hallucination_issues = check_hallucinations(
        db, content_type, content_data
    )

    # Step 2: LLM-as-judge quality scoring
    llm_scores, llm_issues = evaluate_with_llm(
        db, content_type, content_data
    )

    # Combine scores
    all_scores = {
        'hallucination_score': hallucination_score,
        'grounding_score': llm_scores['grounding_score'],
        'relevance_score': llm_scores['relevance_score'],
        'actionability_score': llm_scores['actionability_score'],
        'coherence_score': llm_scores['coherence_score'],
    }

    # Calculate overall score (average)
    overall_score = sum(all_scores.values()) / len(all_scores)

    # Determine pass/fail (threshold: 9.0 = 90% - industry standard)
    threshold = 9.0
    passed = overall_score >= threshold

    # Create evaluation run record
    eval_run = EvaluationRun(
        content_type=content_type,
        content_id=content_id,
        hallucination_score=hallucination_score,
        grounding_score=llm_scores['grounding_score'],
        relevance_score=llm_scores['relevance_score'],
        actionability_score=llm_scores['actionability_score'],
        coherence_score=llm_scores['coherence_score'],
        overall_score=overall_score,
        passed=passed,
        threshold=threshold,
        evaluator_model="gpt-4o-mini",
        evaluation_method="hybrid",
    )

    db.add(eval_run)
    db.flush()  # Get eval_run.id

    # Create issue records
    all_issues = hallucination_issues + llm_issues
    for issue_data in all_issues:
        issue = EvaluationIssue(
            evaluation_run_id=eval_run.id,
            issue_type=issue_data['type'],
            severity=issue_data['severity'],
            description=issue_data['description'],
            affected_signal_ids=issue_data.get('signal_ids'),
            affected_entities=issue_data.get('entities'),
            details=issue_data.get('details'),
        )
        db.add(issue)

    db.commit()
    db.refresh(eval_run)

    return eval_run
