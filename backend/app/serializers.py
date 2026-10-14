from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common import iso
from app.models import Activity, Application, Club, Member, Notification, Registration, User


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
        "description": club.description,
        "introduction": club.introduction,
        "foundedAt": club.founded_at.isoformat(),
        "tags": club.tags,
        "memberCount": count,
    }


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
