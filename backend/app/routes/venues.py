from datetime import date, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.common import fail, ok, page_result, utcnow
from app.models import Club, Notification, User, Venue, VenueReservation
from app.schemas import ReservationPayload, ReservationReviewPayload, ReservationStatus
from app.security import CurrentUser, Db, managed_club
from app.serializers import venue_data, venue_reservation_data

router = APIRouter(prefix="/api", tags=["场地与物资预约"])

# 可预约窗口：今日起 14 天。窗口外的日期一律视为「时段不存在」。
RESERVATION_WINDOW_DAYS = 14
# 占用时段的预约状态：被拒绝的预约会释放时段
ACTIVE_STATUSES = ("pending", "approved")


def today() -> date:
    return utcnow().date()


def in_window(day: date) -> bool:
    return today() <= day <= today() + timedelta(days=RESERVATION_WINDOW_DAYS - 1)


def window_days(day: date | None = None) -> list[date]:
    if day is not None:
        return [day]
    return [today() + timedelta(days=offset) for offset in range(RESERVATION_WINDOW_DAYS)]


def find_venue(db: Db, venue_id: str, lock: bool = False) -> Venue:
    query = select(Venue).where(Venue.id == venue_id)
    venue = db.scalar(query.with_for_update() if lock else query)
    if venue is None:
        fail(1404, "场地不存在")
    return venue


def taken_slots(db: Db, venue_id: str, days: list[date]) -> set[tuple[str, str]]:
    """已被待审或已通过预约占用的 (日期, 时段) 集合。"""
    rows = db.execute(
        select(VenueReservation.reserve_date, VenueReservation.time_slot).where(
            VenueReservation.venue_id == venue_id,
            VenueReservation.reserve_date.in_(days),
            VenueReservation.status.in_(ACTIVE_STATUSES),
        )
    )
    return {(row[0].isoformat(), row[1]) for row in rows}


def reserve_club(db: Db, user: User) -> Club:
    """预约以社团名义提交：本阶段仅社长可为自己所属社团提交。"""
    if user.role != "clubAdmin":
        fail(403, "只有社长可以为本社团提交场地预约", 403)
    if not user.club_id:
        fail(403, "当前社长账号未绑定社团，无法提交预约", 403)
    return managed_club(db, user, user.club_id)


@router.get("/venues")
def list_venues(db: Db, user: CurrentUser, day: str = Query("", alias="date")):
    target: date | None = None
    if day:
        try:
            target = date.fromisoformat(day)
        except ValueError:
            fail(1003, "日期格式应为 YYYY-MM-DD")
        if not in_window(target):
            fail(1413, "该日期不在可预约范围内")
    days = window_days(target)
    venues = db.scalars(select(Venue).order_by(Venue.created_at, Venue.id))
    return ok([venue_data(venue, days, taken_slots(db, venue.id, days)) for venue in venues])


@router.post("/venue-reservations")
def create_reservation(payload: ReservationPayload, db: Db, user: CurrentUser):
    club = reserve_club(db, user)
    # 锁定场地行，串行化同一场地的时段占用判断
    venue = find_venue(db, payload.venue_id, lock=True)
    if not in_window(payload.date):
        fail(1413, "该日期不在可预约范围内")
    if payload.time_slot not in venue.time_slots:
        fail(1413, "该时段不存在")
    occupied = db.scalar(
        select(VenueReservation.id)
        .where(
            VenueReservation.venue_id == venue.id,
            VenueReservation.reserve_date == payload.date,
            VenueReservation.time_slot == payload.time_slot,
            VenueReservation.status.in_(ACTIVE_STATUSES),
        )
        .with_for_update()
    )
    if occupied:
        fail(1414, "该时段已被预约")
    item = VenueReservation(
        venue_id=venue.id,
        club_id=club.id,
        user_id=user.id,
        reserve_date=payload.date,
        time_slot=payload.time_slot,
        purpose=payload.purpose,
        items=payload.items,
    )
    db.add(item)
    db.flush()
    return ok(venue_reservation_data(db, item))


@router.get("/venue-reservations")
def list_reservations(
    db: Db,
    user: CurrentUser,
    status: ReservationStatus | None = None,
    clubId: str = Query("", max_length=36),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    query = select(VenueReservation)
    if user.role == "clubAdmin":
        query = query.where(VenueReservation.club_id == user.club_id)
    elif user.role == "admin":
        if clubId:
            query = query.where(VenueReservation.club_id == clubId)
    else:
        fail(403, "只有社长或系统管理员可以查看预约单", 403)
    if status:
        query = query.where(VenueReservation.status == status)
    return ok(
        page_result(
            db,
            query.order_by(VenueReservation.created_at.desc(), VenueReservation.id),
            page,
            pageSize,
            lambda item: venue_reservation_data(db, item),
        )
    )


@router.put("/venue-reservations/{reservation_id}")
def review_reservation(
    reservation_id: str, payload: ReservationReviewPayload, db: Db, user: CurrentUser
):
    if user.role != "admin":
        fail(403, "只有系统管理员可以审批预约单", 403)
    item = db.scalar(
        select(VenueReservation).where(VenueReservation.id == reservation_id).with_for_update()
    )
    if item is None:
        fail(1404, "预约单不存在")
    if item.status != "pending":
        fail(1410, "该预约单已审批")
    item.status = "approved" if payload.action == "approve" else "rejected"
    item.reviewed_at, item.comment = utcnow(), payload.comment
    venue = db.get(Venue, item.venue_id)
    db.add(
        Notification(
            user_id=item.user_id,
            type="venue",
            title="场地预约审批反馈",
            content=(
                f"「{venue.name if venue else '场地'} {item.reserve_date.isoformat()} "
                f"{item.time_slot}」预约已{'通过' if item.status == 'approved' else '被拒绝'}"
            ),
            link="/admin",
        )
    )
    db.flush()
    return ok(venue_reservation_data(db, item))
