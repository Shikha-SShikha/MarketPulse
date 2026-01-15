"""Background jobs for the STM Intelligence Brief System."""

import asyncio
import logging
from datetime import date

from app.database import SessionLocal
from app.models import DataSource, Signal
from app.services import generate_weekly_brief, get_week_boundaries, create_signal_from_dict, create_notification
from app.collectors.rss_collector import RSSCollector
from app.collectors.web_collector import WebCollector
from app.config import get_settings

logger = logging.getLogger(__name__)

# LinkedIn collector is optional (requires Playwright installation)
try:
    from app.collectors.linkedin_collector import LinkedInCollector
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False
    logger.warning("LinkedIn collector not available - playwright not installed")


def generate_weekly_brief_job(reference_date: date = None) -> dict:
    """
    Job function to generate the weekly brief.

    This is called by the scheduler on Sunday 5 PM UTC.
    Can also be triggered manually via the admin endpoint.

    Args:
        reference_date: Date to generate brief for (defaults to today)

    Returns:
        Dictionary with job results
    """
    logger.info("Starting weekly brief generation job")

    week_start, week_end = get_week_boundaries(reference_date)
    logger.info(f"Generating brief for week: {week_start} to {week_end}")

    db = SessionLocal()
    try:
        brief = generate_weekly_brief(db, reference_date)

        if brief is None:
            logger.warning("No signals found for the week, no brief generated")
            return {
                "success": True,
                "message": "No signals found for the week",
                "brief_id": None,
                "week_start": week_start,
                "week_end": week_end,
                "themes_created": 0,
                "signals_processed": 0,
            }

        logger.info(
            f"Weekly brief generated: {brief.id}, "
            f"themes: {len(brief.theme_ids)}, "
            f"signals: {brief.total_signals}"
        )

        # Auto-evaluate all themes in the brief
        evaluated_count = 0
        passed_count = 0
        failed_count = 0
        eval_errors = []

        logger.info("Starting auto-evaluation of brief themes")
        try:
            from app import evaluations
            from app.services import get_themes_by_ids

            themes = get_themes_by_ids(db, brief.theme_ids)

            for theme in themes:
                try:
                    content_data = {
                        'title': theme.title,
                        'so_what': theme.so_what,
                        'now_what': theme.now_what,
                        'key_players': theme.key_players,
                        'signal_ids': [str(sid) for sid in theme.signal_ids],
                    }

                    eval_run = evaluations.evaluate_content(
                        db=db,
                        content_type='theme',
                        content_id=theme.id,
                        content_data=content_data,
                    )

                    evaluated_count += 1
                    if eval_run.passed:
                        passed_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error evaluating theme {theme.id}: {e}")
                    eval_errors.append(f"Theme {theme.id}: {str(e)}")

            logger.info(
                f"Auto-evaluation complete: {evaluated_count} themes evaluated, "
                f"{passed_count} passed, {failed_count} failed"
            )

        except Exception as e:
            logger.error(f"Error during auto-evaluation: {e}", exc_info=True)
            eval_errors.append(f"Auto-evaluation error: {str(e)}")

        return {
            "success": True,
            "message": "Brief generated successfully",
            "brief_id": brief.id,
            "week_start": brief.week_start,
            "week_end": brief.week_end,
            "themes_created": len(brief.theme_ids),
            "signals_processed": brief.total_signals,
            "evaluations_run": evaluated_count,
            "evaluations_passed": passed_count,
            "evaluations_failed": failed_count,
            "evaluation_errors": eval_errors,
        }

    except Exception as e:
        logger.error(f"Error generating weekly brief: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Error generating brief: {str(e)}",
            "brief_id": None,
            "week_start": week_start,
            "week_end": week_end,
            "themes_created": 0,
            "signals_processed": 0,
        }

    finally:
        db.close()
        logger.info("Weekly brief generation job completed")


async def collect_signals_job() -> dict:
    """
    Job function to collect signals from all enabled data sources.

    This is called by the scheduler daily at 9 AM UTC.
    Can also be triggered manually via the admin endpoint.

    Returns:
        Dictionary with job results
    """
    logger.info("Starting automated signal collection job")

    db = SessionLocal()
    total_signals = 0
    total_pending = 0
    errors = []
    sources_processed = 0

    try:
        # Get all enabled data sources
        sources = db.query(DataSource).filter(DataSource.enabled == True).all()

        if not sources:
            logger.warning("No enabled data sources found")
            return {
                "success": True,
                "message": "No enabled data sources to collect from",
                "signals_collected": 0,
                "signals_pending_review": 0,
                "sources_processed": 0,
                "errors": [],
            }

        logger.info(f"Found {len(sources)} enabled data sources")

        # Process each data source
        for source in sources:
            try:
                logger.info(f"Collecting from: {source.name} ({source.source_type})")

                # Create appropriate collector based on source type
                collector = None
                if source.source_type == 'rss':
                    collector = RSSCollector(source, db)
                elif source.source_type == 'web':
                    collector = WebCollector(source, db)
                elif source.source_type == 'linkedin':
                    # Check if LinkedIn collector is available
                    if not LINKEDIN_AVAILABLE:
                        logger.warning(f"LinkedIn collector not available (playwright not installed), skipping {source.name}")
                        continue
                    # Get LinkedIn credentials
                    settings = get_settings()
                    if not settings.linkedin_email or not settings.linkedin_password:
                        logger.warning(f"LinkedIn credentials not configured, skipping {source.name}")
                        continue
                    collector = LinkedInCollector(source, db, settings.linkedin_email, settings.linkedin_password)
                elif source.source_type == 'email':
                    logger.warning(f"Email collector not yet implemented for {source.name}")
                    continue
                else:
                    logger.error(f"Unknown source type: {source.source_type} for {source.name}")
                    continue

                # Collect signals
                signals = await collector.collect()

                # Save signals to database (with deduplication)
                source_signals = 0
                source_pending = 0
                source_duplicates = 0
                for signal_data in signals:
                    try:
                        # Check if signal already exists (by source_url)
                        existing = db.query(Signal).filter(
                            Signal.source_url == signal_data['source_url'],
                            Signal.deleted_at.is_(None)
                        ).first()

                        if existing:
                            logger.debug(f"Skipping duplicate signal: {signal_data['source_url']}")
                            source_duplicates += 1
                            continue

                        signal = create_signal_from_dict(db, signal_data)
                        source_signals += 1

                        if signal.status == 'pending_review':
                            source_pending += 1

                    except Exception as e:
                        error_msg = f"Error saving signal from {source.name}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)

                total_signals += source_signals
                total_pending += source_pending
                sources_processed += 1

                logger.info(
                    f"Collected {source_signals} new signals from {source.name} "
                    f"({source_duplicates} duplicates skipped, {source_pending} pending review)"
                )

            except Exception as e:
                error_msg = f"Error collecting from {source.name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

        # Create notification for curator if there are pending signals
        if total_pending > 0:
            try:
                create_notification(
                    db,
                    notification_type="pending_signals",
                    title=f"{total_pending} signals need review",
                    message=f"{total_pending} automated signals are pending curator review.",
                    link="/admin/signals?status=pending_review"
                )
                logger.info(f"Created notification for {total_pending} pending signals")
            except Exception as e:
                logger.error(f"Error creating notification: {e}")

        logger.info(
            f"Signal collection complete: {total_signals} signals collected from {sources_processed} sources, "
            f"{total_pending} pending review, {len(errors)} errors"
        )

        return {
            "success": len(errors) == 0,
            "message": "Signal collection completed",
            "signals_collected": total_signals,
            "signals_pending_review": total_pending,
            "sources_processed": sources_processed,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"Signal collection job failed: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Signal collection failed: {str(e)}",
            "signals_collected": total_signals,
            "signals_pending_review": total_pending,
            "sources_processed": sources_processed,
            "errors": errors + [str(e)],
        }

    finally:
        db.close()
        logger.info("Signal collection job completed")


def collect_signals_job_sync() -> dict:
    """
    Synchronous wrapper for collect_signals_job.

    APScheduler requires non-async functions, so this wrapper
    creates an event loop and runs the async job.
    """
    return asyncio.run(collect_signals_job())
