"""Scheduled task to clean up expired ROM verifications"""

from config import ENABLE_SCHEDULED_CLEANUP_VERIFICATIONS, SCHEDULED_CLEANUP_VERIFICATIONS_CRON
from handler.database import db_rom_verification_handler
from logger.logger import log
from tasks.tasks import PeriodicTask


class CleanupExpiredVerificationsTask(PeriodicTask):
    def __init__(self):
        super().__init__(
            title="Scheduled cleanup expired verifications",
            description="Marks expired ROM verifications as expired",
            enabled=ENABLE_SCHEDULED_CLEANUP_VERIFICATIONS,
            manual_run=False,
            cron_string=SCHEDULED_CLEANUP_VERIFICATIONS_CRON,
            func="tasks.scheduled.cleanup_expired_verifications.cleanup_expired_verifications_task.run",
        )

    async def run(self):
        if not ENABLE_SCHEDULED_CLEANUP_VERIFICATIONS:
            log.info("Scheduled cleanup of expired verifications not enabled, unscheduling...")
            self.unschedule()
            return None

        log.info("Scheduled cleanup of expired verifications started...")
        
        try:
            count = db_rom_verification_handler.mark_expired_verifications()
            if count > 0:
                log.info(f"Marked {count} expired ROM verifications")
            else:
                log.debug("No expired ROM verifications found")
        except Exception as e:
            log.error(f"Error cleaning up expired verifications: {e}")
        
        log.info("Scheduled cleanup of expired verifications completed")


cleanup_expired_verifications_task = CleanupExpiredVerificationsTask()
