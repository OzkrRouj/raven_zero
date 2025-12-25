import asyncio
import shutil
from datetime import datetime, timezone

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.core.logger import logger
from app.core.redis import get_redis

jobstores = {"default": MemoryJobStore()}
executors = {"default": AsyncIOExecutor()}
job_defaults = {"coalesce": False, "max_instances": 1, "misfire_grace_time": 300}

scheduler = AsyncIOScheduler(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone="UTC"
)


async def cleanup_orphaned_files():
    logger.info("cleanup_orphaned_files_started")

    try:
        redis = await get_redis()
        if not redis:
            logger.error("redis_connection_failed", context="cleanup_orphaned_files")
            return

        storage_path = settings.storage_path
        if not storage_path.exists():
            logger.warning("storage_path_not_found")
            return

        now = datetime.now(timezone.utc)
        orphan_limit_minutes = settings.orphan_age_minutes
        cleaned_count = 0

        for folder in storage_path.iterdir():
            if not folder.is_dir():
                continue

            key = f"upload:{folder.name}"

            try:
                exists = await redis.exists(key)

                if not exists:
                    stat = folder.stat()
                    created_time = datetime.fromtimestamp(
                        stat.st_ctime, tz=timezone.utc
                    )

                    age_minutes = (now - created_time).total_seconds() / 60

                    if age_minutes > orphan_limit_minutes:
                        logger.info(
                            "removing_orphaned_folder",
                            age_minutes=round(age_minutes, 1),
                            created_at=created_time.isoformat(),
                        )
                        await asyncio.to_thread(shutil.rmtree, folder)
                        cleaned_count += 1

            except Exception as e:
                logger.error(
                    "error_processing_folder",
                    error=str(e),
                    exc_info=True,
                )

        logger.info(
            "cleanup_completed",
            removed_count=cleaned_count,
            total_duration_seconds=round(
                (datetime.now(timezone.utc) - now).total_seconds(), 2
            ),
        )

        await redis.set("health:last_cleanup", now.isoformat())

    except Exception as e:
        logger.critical("cleanup_job_failed", error=str(e), exc_info=True)
        raise


async def health_check_marker():
    try:
        redis = await get_redis()
        if redis:
            await redis.set(
                "health:scheduler_heartbeat", datetime.now(timezone.utc).isoformat()
            )
    except Exception as e:
        logger.error(f"❌ Error on heartbeat: {e}")


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        cleanup_orphaned_files,
        trigger=IntervalTrigger(minutes=settings.cleanup_interval_minutes),
        id="cleanup_orphans",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )

    scheduler.add_job(
        health_check_marker,
        trigger=IntervalTrigger(minutes=1),
        id="scheduler_heartbeat",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("🕒 Cleaner scheduler started.")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("👋 Cleaner scheduler stopped.")
