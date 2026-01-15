"""APScheduler configuration for scheduled jobs."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs import generate_weekly_brief_job, collect_signals_job_sync
from app.config import get_settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: BackgroundScheduler = None


def init_scheduler() -> BackgroundScheduler:
    """
    Initialize and start the background scheduler.

    Configures the weekly brief generation job to run every Sunday at 5 PM UTC.

    Returns:
        Configured and started BackgroundScheduler
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler

    scheduler = BackgroundScheduler(
        timezone="UTC",
        job_defaults={
            "coalesce": True,  # Combine missed runs into one
            "max_instances": 1,  # Only one instance at a time
            "misfire_grace_time": 21600,  # 6 hour grace period for missed jobs
        }
    )

    # Schedule weekly brief generation for Sunday 5 PM UTC
    scheduler.add_job(
        generate_weekly_brief_job,
        trigger=CronTrigger(
            day_of_week="sun",
            hour=17,
            minute=0,
            timezone="UTC",
        ),
        id="weekly_brief_generation",
        name="Generate Weekly Brief",
        replace_existing=True,
    )

    # Schedule signal collection (daily at configured hour, default 9 AM UTC)
    settings = get_settings()
    if settings.enable_automated_collection:
        scheduler.add_job(
            collect_signals_job_sync,
            trigger=CronTrigger(
                hour=settings.collection_schedule_hour,
                minute=0,
                timezone="UTC",
            ),
            id="signal_collection",
            name="Collect Automated Signals",
            replace_existing=True,
        )
        logger.info(f"Signal collection scheduled for {settings.collection_schedule_hour}:00 UTC daily")
    else:
        logger.info("Automated signal collection is disabled")

    scheduler.start()

    # Log scheduled jobs
    jobs = scheduler.get_jobs()
    logger.info(f"Scheduler started with {len(jobs)} jobs:")
    for job in jobs:
        logger.info(f"  - {job.name}: next run at {job.next_run_time}")

    return scheduler


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("Scheduler shut down")


def get_scheduler() -> BackgroundScheduler:
    """Get the current scheduler instance."""
    return scheduler
