"""
Test script for evaluation system.

Creates test signals and a theme, then runs evaluations.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models import Signal, Theme
from app.evaluations import evaluate_content
import uuid
from datetime import datetime


def create_test_data(db):
    """Create test signals and theme for evaluation."""

    # Create test signals
    signals = []
    signal_ids = []

    # Signal 1: Springer Nature AI launch
    signal1 = Signal(
        id=uuid.uuid4(),
        entity="Springer Nature",
        event_type="launch",
        topic="AI/ML",
        source_url="https://example.com/springer-ai-tool",
        evidence_snippet="Springer Nature launches new AI-powered peer review tool to detect research integrity issues and accelerate publication workflow.",
        confidence="High",
        impact_areas=["Tech", "Integrity"],
        status="approved",
        created_at=datetime.utcnow(),
    )
    db.add(signal1)
    signals.append(signal1)
    signal_ids.append(signal1.id)

    # Signal 2: Elsevier partnership
    signal2 = Signal(
        id=uuid.uuid4(),
        entity="Elsevier",
        event_type="partnership",
        topic="AI/ML",
        source_url="https://example.com/elsevier-partnership",
        evidence_snippet="Elsevier partners with leading AI research lab to develop automated metadata extraction tools for scholarly articles.",
        confidence="High",
        impact_areas=["Tech", "Ops"],
        status="approved",
        created_at=datetime.utcnow(),
    )
    db.add(signal2)
    signals.append(signal2)
    signal_ids.append(signal2.id)

    # Signal 3: Wiley integrity announcement
    signal3 = Signal(
        id=uuid.uuid4(),
        entity="Wiley",
        event_type="announcement",
        topic="Integrity",
        source_url="https://example.com/wiley-integrity",
        evidence_snippet="Wiley announces enhanced image integrity checks across all journals, mandating original image files for all submissions.",
        confidence="Medium",
        impact_areas=["Integrity", "Ops"],
        status="approved",
        created_at=datetime.utcnow(),
    )
    db.add(signal3)
    signals.append(signal3)
    signal_ids.append(signal3.id)

    db.commit()

    # Create a test theme using these signals
    theme = Theme(
        id=uuid.uuid4(),
        title="AI-Powered Publishing Tools Gaining Traction",
        signal_ids=signal_ids,
        key_players=["Springer Nature", "Elsevier", "Wiley"],
        aggregate_confidence="High",
        impact_areas=["Tech", "Integrity", "Ops"],
        so_what="STM publishers are investing heavily in AI tools for peer review, metadata extraction, and integrity checks. This trend threatens traditional production service providers who don't offer AI capabilities.",
        now_what=[
            "Assess Kriyadocs' AI capabilities vs. competitors",
            "Develop messaging around AI-enhanced services",
            "Partner with AI vendors to enhance service offerings"
        ],
        created_at=datetime.utcnow(),
    )
    db.add(theme)
    db.commit()

    print(f"\nCreated {len(signals)} test signals:")
    for i, signal in enumerate(signals, 1):
        print(f"  {i}. {signal.entity}: {signal.topic} - ID: {signal.id}")

    print(f"\nCreated test theme:")
    print(f"  Title: {theme.title}")
    print(f"  ID: {theme.id}")
    print(f"  Signal IDs: {len(theme.signal_ids)}")

    return theme, signals


def test_evaluation(db, theme):
    """Run evaluation on the test theme."""

    print("\n" + "="*70)
    print("RUNNING EVALUATION")
    print("="*70)

    # Prepare content data
    content_data = {
        'title': theme.title,
        'so_what': theme.so_what,
        'now_what': theme.now_what,
        'key_players': theme.key_players,
        'signal_ids': theme.signal_ids,
    }

    # Run evaluation
    eval_run = evaluate_content(
        db=db,
        content_type="theme",
        content_id=theme.id,
        content_data=content_data,
    )

    print(f"\nEvaluation Results:")
    print(f"  Overall Score: {eval_run.overall_score:.2f} / 10.0")
    print(f"  Pass/Fail: {'✅ PASSED' if eval_run.passed else '❌ FAILED'}")
    print(f"  Threshold: {eval_run.threshold}")
    print(f"\nDimensional Scores:")
    print(f"  Hallucination: {eval_run.hallucination_score:.2f}/10")
    print(f"  Grounding: {eval_run.grounding_score:.2f}/10")
    print(f"  Relevance: {eval_run.relevance_score:.2f}/10")
    print(f"  Actionability: {eval_run.actionability_score:.2f}/10")
    print(f"  Coherence: {eval_run.coherence_score:.2f}/10")

    print(f"\nIssues Found: {len(eval_run.issues)}")
    for i, issue in enumerate(eval_run.issues, 1):
        print(f"  {i}. [{issue.severity.upper()}] {issue.issue_type}: {issue.description}")

    return eval_run


def main():
    """Run the test."""
    db = SessionLocal()

    try:
        # Create test data
        theme, signals = create_test_data(db)

        # Test evaluation
        eval_run = test_evaluation(db, theme)

        # Test evaluation listing endpoint
        print("\n" + "="*70)
        print("TESTING EVALUATION LISTING")
        print("="*70)

        from app.models import EvaluationRun
        all_evals = db.query(EvaluationRun).all()
        print(f"\nTotal evaluations in database: {len(all_evals)}")
        for eval in all_evals:
            print(f"  - {eval.content_type} ({eval.content_id}): {eval.overall_score:.2f} ({'PASSED' if eval.passed else 'FAILED'})")

        print("\n✅ Evaluation system test completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
