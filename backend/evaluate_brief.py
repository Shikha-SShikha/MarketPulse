"""
Evaluate all themes in the latest weekly brief.
"""

import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models import WeeklyBrief, Theme
from app.evaluations import evaluate_content


def main():
    db = SessionLocal()

    try:
        # Get the latest brief
        brief = db.query(WeeklyBrief).order_by(WeeklyBrief.generated_at.desc()).first()

        if not brief:
            print("No weekly briefs found!")
            return

        print(f"\n{'='*70}")
        print(f"EVALUATING WEEKLY BRIEF")
        print(f"{'='*70}")
        print(f"Brief ID: {brief.id}")
        print(f"Week: {brief.week_start} to {brief.week_end}")
        print(f"Total Signals: {brief.total_signals}")
        print(f"Themes: {len(brief.theme_ids)}")
        print()

        # Get all themes
        themes = db.query(Theme).filter(Theme.id.in_(brief.theme_ids)).all()

        results = []
        for i, theme in enumerate(themes, 1):
            print(f"{'='*70}")
            print(f"EVALUATING THEME {i}/{len(themes)}")
            print(f"{'='*70}")
            print(f"Title: {theme.title}")
            print(f"Signals: {len(theme.signal_ids)}")
            print()

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

            results.append({
                'theme': theme.title,
                'overall_score': eval_run.overall_score,
                'passed': eval_run.passed,
                'hallucination': eval_run.hallucination_score,
                'grounding': eval_run.grounding_score,
                'relevance': eval_run.relevance_score,
                'actionability': eval_run.actionability_score,
                'coherence': eval_run.coherence_score,
                'issues': len(eval_run.issues),
            })

            print(f"Overall Score: {eval_run.overall_score:.2f}/10")
            print(f"Status: {'✅ PASSED' if eval_run.passed else '❌ FAILED'}")
            print(f"Issues: {len(eval_run.issues)}")
            if eval_run.issues:
                for issue in eval_run.issues:
                    print(f"  - [{issue.severity.upper()}] {issue.issue_type}: {issue.description}")
            print()

        # Summary
        print(f"\n{'='*70}")
        print(f"EVALUATION SUMMARY")
        print(f"{'='*70}")

        passed = sum(1 for r in results if r['passed'])
        failed = len(results) - passed
        avg_score = sum(r['overall_score'] for r in results) / len(results)

        print(f"Total Themes Evaluated: {len(results)}")
        print(f"Passed: {passed} ({passed/len(results)*100:.1f}%)")
        print(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
        print(f"Average Score: {avg_score:.2f}/10")
        print()

        print("Individual Results:")
        for i, r in enumerate(results, 1):
            status = "✅ PASS" if r['passed'] else "❌ FAIL"
            print(f"  {i}. [{status}] {r['overall_score']:.2f}/10 - {r['theme'][:60]}...")
            print(f"     H:{r['hallucination']:.1f} G:{r['grounding']:.1f} R:{r['relevance']:.1f} A:{r['actionability']:.1f} C:{r['coherence']:.1f} Issues:{r['issues']}")

        print(f"\n✅ Evaluation complete! Check dashboard at /admin/evaluations")

    finally:
        db.close()


if __name__ == "__main__":
    main()
