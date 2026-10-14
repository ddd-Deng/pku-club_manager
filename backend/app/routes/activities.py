from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.common import fail, ok, page_result, utcnow
from app.models import Activity, Club, Member, Notification, Registration
from app.schemas import ActivityPatch, ActivityPayload, ActivityStatus
from app.security import CurrentUser, Db, OptionalUser, StudentUser, managed_club
from app.serializers import activity_data, registration_count, registration_data

router = APIRouter(prefix="/api/activities", tags=["活动"])


def find_activity(db: Db, activity_id: str, lock: bool = False) -> Activity:
    query = select(Activity).where(Activity.id == activity_id, Activity.deleted_at.is_(None))
    row = db.scalar(query.with_for_update() if lock else query)
    if not row:
        fail(1404, "活动不存在")
    return row


def valid_times(start: datetime, end: datetime) -> None:
    if end <= start:
        fail(1003, "结束时间必须晚于开始时间")


@router.get("")
def activities(
    db: Db,
    user: OptionalUser,
    keyword: str = Query("", max_length=200),
    clubId: str | None = None,
    category: str | None = None,
    startDate: date | None = None,
    endDate: date | None = None,
    status: ActivityStatus | None = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    query = select(Activity).where(Activity.deleted_at.is_(None))
    if status in ("draft", "unpublished"):
        if not user:
            fail(401, "请先登录", 401)
        if user.role not in ("clubAdmin", "admin"):
            fail(403, "无权查看未公开活动", 403)
        if user.role == "clubAdmin":
            if clubId and clubId != user.club_id:
                fail(403, "只能管理自己所属的社团", 403)
            query = query.where(Activity.club_id == user.club_id)
    query = (
        query.where(Activity.status == status)
        if status
        else query.where(Activity.status.in_(["published", "finished"]))
    )
    if clubId:
        query = query.where(Activity.club_id == clubId)
    if category and category != "全部类型":
        query = query.join(Club).where(Club.category == category)
    if keyword.strip():
        query = query.where(
            or_(
                Activity.title.contains(keyword.strip(), autoescape=True),
                Activity.description.contains(keyword.strip(), autoescape=True),
            )
        )
    if startDate and endDate and startDate > endDate:
        fail(1003, "开始日期不能晚于结束日期")
    if startDate:
        query = query.where(Activity.start_time >= datetime.combine(startDate, time.min))
    if endDate:
        query = query.where(
            Activity.start_time < datetime.combine(endDate + timedelta(days=1), time.min)
        )
    return ok(
        page_result(
            db,
            query.order_by(Activity.start_time, Activity.id),
            page,
            pageSize,
            lambda item: activity_data(db, item, user),
        )
    )


@router.get("/upcoming")
def upcoming(db: Db, limit: int = Query(5, ge=1, le=100)):
    rows = db.scalars(
        select(Activity)
        .where(
            Activity.status == "published",
            Activity.start_time >= utcnow(),
            Activity.deleted_at.is_(None),
        )
        .order_by(Activity.start_time, Activity.id)
        .limit(limit)
    )
    return ok([activity_data(db, row) for row in rows])


@router.get("/{activity_id}")
def activity_detail(activity_id: str, db: Db, user: OptionalUser):
    item = find_activity(db, activity_id)
    if item.status in ("draft", "unpublished"):
        if not user:
            fail(401, "请先登录", 401)
        managed_club(db, user, item.club_id)
    return ok(activity_data(db, item, user))


@router.post("")
def create_activity(payload: ActivityPayload, db: Db, user: CurrentUser):
    club_id = payload.club_id if user.role == "admin" else user.club_id
    if not club_id:
        fail(
            1003 if user.role == "admin" else 403,
            "请指定可管理的社团",
            200 if user.role == "admin" else 403,
        )
    if user.role == "clubAdmin" and payload.club_id and payload.club_id != user.club_id:
        fail(403, "不能在其他社团创建活动", 403)
    managed_club(db, user, club_id)
    valid_times(payload.start_time, payload.end_time)
    if payload.start_time <= utcnow():
        fail(1003, "新活动开始时间必须晚于当前时间")
    item = Activity(**payload.model_dump(exclude={"club_id"}), club_id=club_id, status="draft")
    db.add(item)
    db.flush()
    return ok(activity_data(db, item, user))


@router.put("/{activity_id}")
def edit_activity(activity_id: str, payload: ActivityPatch, db: Db, user: CurrentUser):
    item = find_activity(db, activity_id, lock=True)
    managed_club(db, user, item.club_id)
    if item.status == "finished" or item.start_time <= utcnow():
        fail(1410, "活动已开始或已结束，不能编辑")
    values = payload.model_dump(exclude_unset=True)
    if "club_id" in values and values["club_id"] != item.club_id:
        fail(1003, "不能变更活动所属社团")
    values.pop("club_id", None)
    start, end = values.get("start_time", item.start_time), values.get("end_time", item.end_time)
    valid_times(start, end)
    if start <= utcnow():
        fail(1003, "活动开始时间必须晚于当前时间")
    if values.get("capacity", item.capacity) < registration_count(db, item.id):
        fail(1003, "名额不能少于当前报名人数")
    for key, value in values.items():
        setattr(item, key, value)
    db.flush()
    return ok(activity_data(db, item, user))


@router.post("/{activity_id}/publish")
def publish(activity_id: str, db: Db, user: CurrentUser):
    item = find_activity(db, activity_id, lock=True)
    managed_club(db, user, item.club_id)
    if item.status not in ("draft", "unpublished") or item.start_time <= utcnow():
        fail(1410, "当前状态或时间不允许发布活动")
    item.status = "published"
    for member in db.scalars(select(Member).where(Member.club_id == item.club_id)):
        db.add(
            Notification(
                user_id=member.user_id,
                type="activity",
                title="活动上新提醒",
                content=f"{item.title} 已发布",
                link=f"/activities/{item.id}",
            )
        )
    db.flush()
    return ok(activity_data(db, item, user))


@router.post("/{activity_id}/unpublish")
def unpublish(activity_id: str, db: Db, user: CurrentUser):
    item = find_activity(db, activity_id, lock=True)
    managed_club(db, user, item.club_id)
    if item.status != "published" or item.end_time <= utcnow():
        fail(1410, "当前状态不可下架")
    item.status = "unpublished"
    return ok(activity_data(db, item, user))


@router.delete("/{activity_id}")
def delete_activity(activity_id: str, db: Db, user: CurrentUser):
    item = find_activity(db, activity_id, lock=True)
    managed_club(db, user, item.club_id)
    allowed = ("draft", "unpublished") if user.role == "admin" else ("draft",)
    if item.status not in allowed or registration_count(db, item.id):
        fail(1410, "只能删除允许状态且无有效报名的活动")
    # Soft deletion preserves cancelled personal registration history and foreign keys.
    item.deleted_at = utcnow()
    return ok()


@router.post("/{activity_id}/registrations")
def register_activity(activity_id: str, db: Db, user: StudentUser):
    item = find_activity(db, activity_id, lock=True)
    if item.status != "published":
        fail(1412, "活动未发布，暂不能报名")
    if item.start_time <= utcnow():
        fail(1410, "活动已开始，不能报名")
    record = db.scalar(
        select(Registration).where(
            Registration.activity_id == item.id, Registration.user_id == user.id
        )
    )
    if record and record.status == "registered":
        fail(1409, "你已报名该活动")
    if registration_count(db, item.id) >= item.capacity:
        fail(1411, "报名人数已满")
    if record:
        record.status, record.created_at = "registered", utcnow()
    else:
        record = Registration(activity_id=item.id, user_id=user.id)
        db.add(record)
    db.flush()
    return ok(registration_data(db, record))


@router.delete("/{activity_id}/registrations")
def cancel_registration(activity_id: str, db: Db, user: StudentUser):
    item = find_activity(db, activity_id, lock=True)
    if item.start_time <= utcnow():
        fail(1410, "活动已开始，不可取消")
    record = db.scalar(
        select(Registration).where(
            Registration.activity_id == item.id,
            Registration.user_id == user.id,
            Registration.status == "registered",
        )
    )
    if not record:
        fail(1404, "未找到你的报名记录")
    record.status = "cancelled"
    return ok()
