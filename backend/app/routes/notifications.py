from fastapi import APIRouter, Query
from sqlalchemy import func, select, update

from app.common import fail, ok, page_result
from app.models import Notification
from app.schemas import NotificationType
from app.security import CurrentUser, Db
from app.serializers import notification_data

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("")
def notifications(
    db: Db,
    user: CurrentUser,
    type: NotificationType | None = None,
    read: bool | None = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    query = select(Notification).where(Notification.user_id == user.id)
    if type:
        query = query.where(Notification.type == type)
    if read is not None:
        query = query.where(Notification.read == read)
    return ok(
        page_result(
            db,
            query.order_by(Notification.created_at.desc(), Notification.id),
            page,
            pageSize,
            notification_data,
        )
    )


@router.get("/unread-count")
def unread_count(db: Db, user: CurrentUser):
    return ok(
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read.is_(False))
        )
    )


@router.put("/read-all")
def read_all(db: Db, user: CurrentUser):
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read.is_(False))
        .values(read=True)
    )
    return ok({"updated": result.rowcount})


@router.put("/{notification_id}/read")
def mark_read(notification_id: str, db: Db, user: CurrentUser):
    item = db.scalar(
        select(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user.id)
        .with_for_update()
    )
    if not item:
        fail(1404, "通知不存在")
    item.read = True
    return ok(notification_data(item))
