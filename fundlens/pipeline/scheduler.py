"""APScheduler config for the daily pipeline job."""

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from config.settings import settings
from fundlens.pipeline.daily_update import run_daily_update


def start_scheduler() -> None:
    scheduler = BlockingScheduler(timezone="America/New_York")
    scheduler.add_job(
        run_daily_update,
        trigger="cron",
        day_of_week="mon-fri",
        hour=settings.daily_update_hour,
        minute=settings.daily_update_minute,
        id="daily_nav_update",
    )
    logger.info(f"Scheduler started — daily job at {settings.daily_update_hour:02d}:{settings.daily_update_minute:02d} ET (Mon-Fri)")
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
