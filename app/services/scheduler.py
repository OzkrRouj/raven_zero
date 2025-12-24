import asyncio
import logging
import shutil
from datetime import datetime, timezone

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

jobstores = {"default": MemoryJobStore()}
executors = {"default": AsyncIOExecutor()}
job_defaults = {"coalesce": False, "max_instances": 1, "misfire_grace_time": 300}

scheduler = AsyncIOScheduler(
    jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone="UTC"
)


async def cleanup_orphaned_files():
    logger.info("🧹 [Scheduler] Starting orphaned files scan...")

    try:
        redis = await get_redis()
        if not redis:
            logger.error("❌ [Scheduler] No Redis connection. Aborting cleanup.")
            return

        storage_path = settings.storage_path
        if not storage_path.exists():
            logger.warning(f"⚠️ [Scheduler] Path not found: {storage_path}")
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
                            f"🗑️ Removing orphan: {folder.name} (Age: {age_minutes:.1f} min)"
                        )

                        await asyncio.to_thread(shutil.rmtree, folder)
                        cleaned_count += 1

            except Exception as e:
                logger.error(f"❌ Error processing folder {folder.name}: {e}")

        if cleaned_count > 0:
            logger.info(f"✅ [Scheduler] Cleanup completed. Removed: {cleaned_count}")
        else:
            logger.debug("✅ [Scheduler] No orphaned files to remove.")

        await redis.set("health:last_cleanup", now.isoformat())

    except Exception as e:
        logger.error(f"❌ [Scheduler] Critical error in cleanup job: {e}")


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
