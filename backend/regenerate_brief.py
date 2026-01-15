"""
Delete old brief and regenerate with improved prompts.
"""

import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models import WeeklyBrief, Theme, EvaluationRun, EvaluationIssue
from app.services import generate_weekly_brief
from datetime import date


def main():
    db = SessionLocal()

    try:
        print("="*70)
        print("DELETING OLD BRIEF AND EVALUATIONS")
        print("="*70)

        # Get the latest brief
        old_brief = db.query(WeeklyBrief).order_by(WeeklyBrief.generated_at.desc()).first()

        if old_brief:
            print(f"\nFound brief: {old_brief.id}")
            print(f"Week: {old_brief.week_start} to {old_brief.week_end}")
            print(f"Themes: {len(old_brief.theme_ids)}")

            # Delete evaluations for themes in this brief
            theme_ids = old_brief.theme_ids
            eval_count = db.query(EvaluationRun).filter(
                EvaluationRun.content_id.in_(theme_ids)
            ).count()

            if eval_count > 0:
                print(f"\nDeleting {eval_count} evaluations...")
                # Delete evaluation issues first (foreign key)
                eval_ids = [e.id for e in db.query(EvaluationRun.id).filter(
                    EvaluationRun.content_id.in_(theme_ids)
                ).all()]

                db.query(EvaluationIssue).filter(
                    EvaluationIssue.evaluation_run_id.in_(eval_ids)
                ).delete(synchronize_session=False)

                # Delete evaluation runs
                db.query(EvaluationRun).filter(
                    EvaluationRun.content_id.in_(theme_ids)
                ).delete(synchronize_session=False)

            # Delete themes
            print(f"Deleting {len(theme_ids)} themes...")
            db.query(Theme).filter(Theme.id.in_(theme_ids)).delete(synchronize_session=False)

            # Delete brief
            print("Deleting brief...")
            db.delete(old_brief)

            db.commit()
            print("✅ Old brief and evaluations deleted")

        print("\n" + "="*70)
        print("REGENERATING BRIEF WITH IMPROVED PROMPTS")
        print("="*70)

        # Regenerate brief for the same week
        reference_date = date(2025, 12, 25)  # Wednesday of that week
        new_brief = generate_weekly_brief(db, reference_date=reference_date)

        if new_brief:
            print(f"\n✅ New brief generated!")
            print(f"Brief ID: {new_brief.id}")
            print(f"Week: {new_brief.week_start} to {new_brief.week_end}")
            print(f"Total Signals: {new_brief.total_signals}")
            print(f"Themes: {len(new_brief.theme_ids)}")

            # Show first theme as sample
            first_theme = db.query(Theme).filter(Theme.id == new_brief.theme_ids[0]).first()
            if first_theme:
                print(f"\nSample Theme:")
                print(f"  Title: {first_theme.title}")
                print(f"  Why It Matters: {first_theme.so_what[:200]}...")
                print(f"  Next Steps (first): {first_theme.now_what[0][:150]}...")
        else:
            print("❌ Failed to regenerate brief")

    finally:
        db.close()


if __name__ == "__main__":
    main()
