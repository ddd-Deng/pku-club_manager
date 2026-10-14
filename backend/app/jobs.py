import asyncio
import logging

from sqlalchemy import update

from app.common import utcnow
from app.models import Activity

logger = logging.getLogger(__name__)


def finish_activities(sessions) -> int:
    with sessions.begin() as db:
        result = db.execute(
            update(Activity)
            .where(
                Activity.status == "published",
                Activity.end_time <= utcnow(),
                Activity.deleted_at.is_(None),
            )
            .values(status="finished")
        )
        return result.rowcount


async def finish_loop(sessions, interval: int, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await asyncio.to_thread(finish_activities, sessions)
        except Exception:
            # Do not log connection URLs or database credentials.
            logger.error("活动结束状态更新失败，请检查数据库和迁移状态")
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except TimeoutError:
            pass
