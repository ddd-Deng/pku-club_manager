from datetime import date

import bleach
from fastapi import APIRouter, Query
from sqlalchemy import String, cast, or_, select

from app.common import fail, iso, ok, page_result, utcnow
from app.models import Activity, Application, Club, Member, Notice, Notification, Recruitment, User
from app.schemas import (
    ApplicationStatus,
    ApplyPayload,
    ClubPayload,
    MemberPayload,
    RecruitmentPayload,
    ReviewPayload,
)
from app.security import CurrentUser, Db, StudentUser, managed_club
from app.serializers import activity_data, application_data, club_data, member_data

router = APIRouter(prefix="/api/clubs", tags=["社团"])
CATEGORIES = ["学术科技", "文化艺术", "体育竞技", "志愿服务"]


def find_club(db: Db, club_id: str, lock: bool = False) -> Club:
    query = select(Club).where(Club.id == club_id)
    club = db.scalar(query.with_for_update() if lock else query)
    if club is None:
        fail(1404, "社团不存在")
    return club


def detail(db: Db, club: Club) -> dict:
    data = club_data(db, club)
    data["notices"] = [
        {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "publishedAt": iso(item.created_at),
        }
        for item in db.scalars(
            select(Notice)
            .where(Notice.club_id == club.id)
            .order_by(Notice.created_at.desc(), Notice.id)
        )
    ]
    data["recentActivities"] = [
        activity_data(db, item)
        for item in db.scalars(
            select(Activity)
            .where(
                Activity.club_id == club.id,
                Activity.status == "published",
                Activity.deleted_at.is_(None),
            )
            .order_by(Activity.start_time.desc(), Activity.id)
            .limit(3)
        )
    ]
    return data


def recruitment_data(item: Recruitment) -> dict:
    return {
        "id": item.id,
        "clubId": item.club_id,
        "title": item.title,
        "content": item.content,
        "deadline": item.deadline.isoformat(),
        "createdAt": iso(item.created_at),
    }


@router.get("")
def list_clubs(
    db: Db,
    keyword: str = Query("", max_length=200),
    category: str = "",
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    query = select(Club)
    keyword = keyword.strip()
    if keyword:
        query = query.where(
            or_(
                Club.name.contains(keyword, autoescape=True),
                Club.description.contains(keyword, autoescape=True),
                cast(Club.tags, String).contains(keyword, autoescape=True),
            )
        )
    if category and category != "全部类型":
        if category not in CATEGORIES:
            fail(1003, "社团分类不合法")
        query = query.where(Club.category == category)
    return ok(
        page_result(
            db,
            query.order_by(Club.created_at, Club.id),
            page,
            pageSize,
            lambda item: club_data(db, item),
        )
    )


@router.get("/categories")
def categories():
    return ok(CATEGORIES)


@router.get("/recommended")
def recommended(db: Db, limit: int = Query(4, ge=1, le=100)):
    rows = db.scalars(select(Club).order_by(Club.created_at, Club.id).limit(limit))
    return ok([club_data(db, row) for row in rows])


@router.get("/{club_id}")
def get_club(club_id: str, db: Db):
    return ok(detail(db, find_club(db, club_id)))


@router.put("/{club_id}")
def edit_club(club_id: str, payload: ClubPayload, db: Db, user: CurrentUser):
    club = managed_club(db, user, club_id, lock=True)
    values = payload.model_dump(exclude_unset=True)
    if "introduction" in values:
        values["introduction"] = bleach.clean(
            values["introduction"],
            tags=["p", "br", "strong", "em", "ul", "ol", "li", "h2", "h3", "a"],
            attributes={"a": ["href", "title"]},
            protocols=["http", "https", "mailto"],
            strip=True,
        )
    for key, value in values.items():
        setattr(club, key, value)
    db.flush()
    return ok(detail(db, club))


@router.post("/{club_id}/applications")
def apply(club_id: str, payload: ApplyPayload, db: Db, user: StudentUser):
    # Serialize all applications/membership changes within a club, including first submissions.
    club = find_club(db, club_id, lock=True)
    if user.club_id == club_id:
        fail(1409, "不能申请加入自己管理的社团")
    if db.scalar(select(Member.id).where(Member.club_id == club_id, Member.user_id == user.id)):
        fail(1409, "你已经是该社团成员")
    if db.scalar(
        select(Application.id).where(
            Application.club_id == club_id,
            Application.user_id == user.id,
            Application.status == "pending",
        )
    ):
        fail(1409, "你已提交入社申请，请等待审核")
    item = Application(club_id=club_id, user_id=user.id, message=payload.message)
    db.add(item)
    for owner in db.scalars(select(User).where(User.role == "clubAdmin", User.club_id == club_id)):
        db.add(
            Notification(
                user_id=owner.id,
                type="application",
                title="入社申请待审核",
                content=f"{user.name} 提交了{club.name}入社申请",
                link="/admin",
            )
        )
    db.flush()
    return ok(application_data(db, item))


@router.get("/{club_id}/applications")
def applications(
    club_id: str,
    db: Db,
    user: CurrentUser,
    status: ApplicationStatus | None = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    managed_club(db, user, club_id)
    query = select(Application).where(Application.club_id == club_id)
    if status:
        query = query.where(Application.status == status)
    return ok(
        page_result(
            db,
            query.order_by(Application.created_at.desc(), Application.id),
            page,
            pageSize,
            lambda item: application_data(db, item),
        )
    )


@router.put("/{club_id}/applications/{app_id}")
def review(club_id: str, app_id: str, payload: ReviewPayload, db: Db, user: CurrentUser):
    managed_club(db, user, club_id, lock=True)
    item = db.scalar(
        select(Application)
        .where(Application.id == app_id, Application.club_id == club_id)
        .with_for_update()
    )
    if not item:
        fail(1404, "申请不存在或不属于该社团")
    if item.status != "pending":
        fail(1410, "该申请已处理，不能重复审核")
    item.status = "approved" if payload.action == "approve" else "rejected"
    item.reviewed_at, item.comment = utcnow(), payload.comment
    if payload.action == "approve":
        if db.scalar(
            select(Member.id).where(Member.club_id == club_id, Member.user_id == item.user_id)
        ):
            fail(1409, "申请人已经是成员")
        db.add(Member(club_id=club_id, user_id=item.user_id))
    db.add(
        Notification(
            user_id=item.user_id,
            type="application",
            title="入社申请审核结果",
            content=f"你的申请已{'通过' if item.status == 'approved' else '拒绝'}",
            link="/profile",
        )
    )
    db.flush()
    return ok(application_data(db, item))


@router.get("/{club_id}/members")
def members(club_id: str, db: Db, user: CurrentUser):
    managed_club(db, user, club_id)
    return ok(
        [
            member_data(db, item)
            for item in db.scalars(
                select(Member)
                .where(Member.club_id == club_id)
                .order_by(Member.created_at, Member.id)
            )
        ]
    )


@router.put("/{club_id}/members/{member_id}")
def edit_member(club_id: str, member_id: str, payload: MemberPayload, db: Db, user: CurrentUser):
    managed_club(db, user, club_id, lock=True)
    member = db.scalar(
        select(Member).where(Member.id == member_id, Member.club_id == club_id).with_for_update()
    )
    if not member:
        fail(1404, "成员不存在或不属于该社团")
    if member.role == "owner":
        fail(403, "此接口不能变更或移除社团所有者", 403)
    if payload.action == "remove":
        result = member_data(db, member)
        db.delete(member)
    else:
        member.role = payload.role
        result = member_data(db, member)
    return ok(result)


@router.post("/{club_id}/recruitments")
def publish_recruitment(club_id: str, payload: RecruitmentPayload, db: Db, user: CurrentUser):
    managed_club(db, user, club_id)
    if payload.deadline < date.today():
        fail(1003, "招新截止日期不能早于今天")
    item = Recruitment(club_id=club_id, **payload.model_dump())
    db.add(item)
    db.flush()
    return ok(recruitment_data(item))


@router.get("/{club_id}/recruitments")
def recruitments(club_id: str, db: Db):
    find_club(db, club_id)
    return ok(
        [
            recruitment_data(item)
            for item in db.scalars(
                select(Recruitment)
                .where(Recruitment.club_id == club_id)
                .order_by(Recruitment.created_at.desc(), Recruitment.id)
            )
        ]
    )
