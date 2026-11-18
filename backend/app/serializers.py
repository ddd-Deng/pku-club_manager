from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common import iso, plain_text
from app.models import (
    Activity,
    Application,
    Club,
    Member,
    Notification,
    Registration,
    User,
    Venue,
    VenueReservation,
)


def user_data(db: Session, user: User) -> dict:
    club = db.get(Club, user.club_id) if user.club_id else None
    return {
        "id": user.id,
        "name": user.name,
        "studentNo": user.student_no,
        "email": user.email,
        "role": user.role,
        "avatar": user.avatar,
        "clubId": user.club_id,
        "clubName": club.name if club else None,
    }


def club_data(db: Session, club: Club) -> dict:
    count = db.scalar(select(func.count()).select_from(Member).where(Member.club_id == club.id))
    return {
        "id": club.id,
        "name": club.name,
        "category": club.category,
        "logo": club.logo,
        # 历史数据可能残留 <p> 等标签，读取时统一归一为纯文本
        "description": plain_text(club.description),
        "introduction": plain_text(club.introduction),
        "foundedAt": club.founded_at.isoformat(),
        "tags": club.tags,
        "memberCount": count,
    }


def club_relation(db: Session, club_id: str, user: User) -> str:
    """当前用户与社团的关系：member / pending / approved / rejected / none。

    详情页据此提示「你已提交申请」「你已是成员」，避免学生提交后看不到进度。
    """
    if db.scalar(select(Member.id).where(Member.club_id == club_id, Member.user_id == user.id)):
        return "member"
    latest = db.scalar(
        select(Application.status)
        .where(Application.club_id == club_id, Application.user_id == user.id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .limit(1)
    )
    return latest or "none"


def application_data(db: Session, item: Application) -> dict:
    return {
        "id": item.id,
        "clubId": item.club_id,
        "clubName": db.get(Club, item.club_id).name,
        "applicantName": db.get(User, item.user_id).name,
        "message": item.message,
        "status": item.status,
        "createdAt": iso(item.created_at),
        "reviewedAt": iso(item.reviewed_at),
    }


def member_data(db: Session, member: Member) -> dict:
    return {
        "id": member.id,
        "name": db.get(User, member.user_id).name,
        "role": member.role,
        "joinedAt": iso(member.created_at),
    }


def registration_count(db: Session, activity_id: str) -> int:
    return db.scalar(
        select(func.count())
        .select_from(Registration)
        .where(Registration.activity_id == activity_id, Registration.status == "registered")
    )


def activity_data(db: Session, activity: Activity, user: User | None = None) -> dict:
    registered = bool(
        user
        and db.scalar(
            select(Registration.id).where(
                Registration.activity_id == activity.id,
                Registration.user_id == user.id,
                Registration.status == "registered",
            )
        )
    )
    return {
        "id": activity.id,
        "clubId": activity.club_id,
        "clubName": db.get(Club, activity.club_id).name,
        "title": activity.title,
        "cover": activity.cover,
        "description": activity.description,
        "location": activity.location,
        "startTime": iso(activity.start_time),
        "endTime": iso(activity.end_time),
        "status": activity.status,
        "capacity": activity.capacity,
        "registeredCount": registration_count(db, activity.id),
        "type": activity.type,
        "registered": registered,
    }


def registration_data(db: Session, item: Registration) -> dict:
    return {
        "id": item.id,
        "activityId": item.activity_id,
        "userId": item.user_id,
        "userName": db.get(User, item.user_id).name,
        "status": item.status,
        "createdAt": iso(item.created_at),
    }


def notification_data(item: Notification) -> dict:
    return {
        "id": item.id,
        "type": item.type,
        "title": item.title,
        "content": item.content,
        "read": item.read,
        "createdAt": iso(item.created_at),
        "link": item.link,
    }


def venue_data(venue: Venue, days: list[date], taken: set[tuple[str, str]]) -> dict:
    """场地与可预约时段；taken 为已被待审/已通过预约占用的 (日期, 时段) 集合。"""
    return {
        "id": venue.id,
        "name": venue.name,
        "location": venue.location,
        "slots": [
            {
                "date": day.isoformat(),
                "timeSlot": slot,
                "available": (day.isoformat(), slot) not in taken,
            }
            for day in days
            for slot in venue.time_slots
        ],
    }


def venue_reservation_data(db: Session, item: VenueReservation) -> dict:
    venue = db.get(Venue, item.venue_id)
    club = db.get(Club, item.club_id)
    return {
        "id": item.id,
        "venueId": item.venue_id,
        "venueName": venue.name if venue else "",
        "clubId": item.club_id,
        "clubName": club.name if club else "",
        "date": item.reserve_date.isoformat(),
        "timeSlot": item.time_slot,
        "purpose": item.purpose,
        "items": item.items,
        "status": item.status,
        "comment": item.comment,
        "reviewedAt": iso(item.reviewed_at),
        "createdAt": iso(item.created_at),
    }
