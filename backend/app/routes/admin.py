from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.common import fail, iso, ok, page_result, utcnow
from app.models import Application, Club, Member, Notification, User
from app.schemas import AccountStatusPayload, AdminProfilePayload, PresidentPayload
from app.security import AdminUser, Db, revoke_user_sessions
from app.serializers import user_data

router = APIRouter(prefix="/api/admin", tags=["系统管理员"])


def account_data(db, user):
    return {**user_data(db, user), "isActive": user.is_active, "createdAt": iso(user.created_at)}


def club_data(db, club):
    president = db.scalar(select(User).where(User.role == "clubAdmin", User.club_id == club.id))
    return {
        "id": club.id,
        "name": club.name,
        "category": club.category,
        "president": {"id": president.id, "name": president.name, "studentNo": president.student_no}
        if president
        else None,
    }


def locked_student(db, user_id):
    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None:
        fail(1404, "账号不存在", 404)
    if user.role == "admin":
        fail(403, "此功能不能修改管理员账号", 403)
    return user


@router.get("/users")
def accounts(
    db: Db,
    admin: AdminUser,
    keyword: str = Query("", max_length=200),
    role: Literal["student", "clubAdmin"] | None = None,
    isActive: bool | None = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    query = select(User).where(User.role.in_(["student", "clubAdmin"]))
    if keyword:
        query = query.where(
            or_(
                User.name.contains(keyword),
                User.student_no.contains(keyword),
                User.email.contains(keyword),
            )
        )
    if role:
        query = query.where(User.role == role)
    if isActive is not None:
        query = query.where(User.is_active == isActive)
    return ok(
        page_result(
            db,
            query.order_by(User.created_at.desc(), User.id),
            page,
            pageSize,
            lambda user: account_data(db, user),
        )
    )


@router.put("/users/{user_id}")
def edit_account(user_id: str, payload: AdminProfilePayload, db: Db, admin: AdminUser):
    user = locked_student(db, user_id)
    if payload.email and db.scalar(
        select(User.id).where(User.email == payload.email, User.id != user.id)
    ):
        fail(1004, "邮箱已被其他账号使用")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.flush()
    return ok(account_data(db, user))


@router.put("/users/{user_id}/status")
def account_status(user_id: str, payload: AccountStatusPayload, db: Db, admin: AdminUser):
    user = locked_student(db, user_id)
    if not payload.is_active and user.role == "clubAdmin":
        fail(1409, "请先更换该社团社长，再禁用此账号", 409)
    user.is_active = payload.is_active
    if not user.is_active:
        revoke_user_sessions(db, user.id)
    db.flush()
    return ok(account_data(db, user))


@router.get("/clubs")
def clubs(
    db: Db,
    admin: AdminUser,
    keyword: str = Query("", max_length=200),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    query = select(Club)
    if keyword:
        query = query.where(Club.name.contains(keyword))
    return ok(
        page_result(
            db,
            query.order_by(Club.created_at.desc(), Club.id),
            page,
            pageSize,
            lambda club: club_data(db, club),
        )
    )


@router.put("/clubs/{club_id}/president")
def appoint(club_id: str, payload: PresidentPayload, db: Db, admin: AdminUser):
    club = db.scalar(select(Club).where(Club.id == club_id).with_for_update())
    if club is None:
        fail(1404, "社团不存在", 404)
    previous = db.scalar(select(User.id).where(User.role == "clubAdmin", User.club_id == club_id))
    ids = sorted({payload.user_id, *([previous] if previous else [])})
    locked = {
        user.id: user
        for user in db.scalars(
            select(User)
            .where(User.id.in_(ids))
            .order_by(User.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    }
    candidate = locked.get(payload.user_id)
    if candidate is None:
        fail(1404, "候选账号不存在", 404)
    if candidate.role == "admin":
        fail(403, "此功能不能修改管理员账号", 403)
    if not candidate.is_active:
        fail(1409, "候选人必须是启用的学生账号", 409)
    if candidate.role == "clubAdmin" and candidate.club_id != club_id:
        fail(1409, "候选人已管理其他社团，请先完成原社团交接", 409)
    if previous == candidate.id:
        return ok(club_data(db, club))
    if payload.expected_president_id != previous:
        fail(1410, "社长已被其他管理员更改，请刷新后重试", 409)
    if previous:
        former = locked[previous]
        former.role, former.club_id = "student", None
        member = db.scalar(
            select(Member)
            .where(Member.user_id == previous, Member.club_id == club_id)
            .with_for_update()
        )
        if member is None or member.role != "owner":
            fail(1409, "原社长成员数据不一致，请联系维护者", 409)
        member.role = "member"
        revoke_user_sessions(db, previous)
        db.flush()  # Release the unique club assignment before assigning its successor.
    candidate.role, candidate.club_id = "clubAdmin", club_id
    member = db.scalar(
        select(Member)
        .where(Member.user_id == candidate.id, Member.club_id == club_id)
        .with_for_update()
    )
    if member:
        member.role = "owner"
    else:
        db.add(Member(user_id=candidate.id, club_id=club_id, role="owner"))
    for application in db.scalars(
        select(Application)
        .where(
            Application.user_id == candidate.id,
            Application.club_id == club_id,
            Application.status == "pending",
        )
        .with_for_update()
    ):
        application.status, application.reviewed_at = "approved", utcnow()
        application.comment = "管理员任命为社长，自动完成入社"
        db.add(
            Notification(
                user_id=candidate.id,
                type="application",
                title="入社申请审核结果",
                content=f"你已被任命为{club.name}社长，入社申请已通过",
                link="/profile",
            )
        )
    revoke_user_sessions(db, candidate.id)
    db.flush()
    return ok(club_data(db, club))
