from fastapi import APIRouter
from sqlalchemy import select

from app.common import fail, iso, ok, utcnow
from app.models import Activity, Application, Club, Registration
from app.schemas import PasswordPayload, ProfilePayload
from app.security import CurrentUser, Db, passwords, revoke_user_sessions, verify_password
from app.serializers import application_data, user_data

router = APIRouter(prefix="/api/user", tags=["个人中心"])


@router.get("/profile")
def profile(db: Db, user: CurrentUser):
    return ok(user_data(db, user))


@router.put("/profile")
def edit_profile(payload: ProfilePayload, db: Db, user: CurrentUser):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.flush()
    return ok(user_data(db, user))


@router.put("/password")
def change_password(payload: PasswordPayload, db: Db, user: CurrentUser):
    if not verify_password(user.password_hash, payload.old_password):
        fail(1005, "原密码不正确")
    user.password_hash = passwords.hash(payload.new_password)
    revoke_user_sessions(db, user.id)
    return ok()


@router.get("/applications")
def applications(db: Db, user: CurrentUser):
    rows = db.scalars(
        select(Application)
        .where(Application.user_id == user.id)
        .order_by(Application.created_at.desc(), Application.id)
    )
    return ok([application_data(db, row) for row in rows])


@router.get("/activity-registrations")
def registrations(db: Db, user: CurrentUser):
    rows = db.scalars(
        select(Registration)
        .where(Registration.user_id == user.id)
        .order_by(Registration.created_at.desc(), Registration.id)
    )
    result = []
    for row in rows:
        activity = db.get(Activity, row.activity_id)
        result.append(
            {
                "id": row.id,
                "activityId": activity.id,
                "title": activity.title,
                "clubName": db.get(Club, activity.club_id).name,
                "startTime": iso(activity.start_time),
                "status": row.status,
                "createdAt": iso(row.created_at),
            }
        )
    return ok(result)


@router.get("/footprints")
def footprints(db: Db, user: CurrentUser):
    rows = db.scalars(
        select(Activity)
        .join(Registration)
        .where(
            Registration.user_id == user.id,
            Registration.status == "registered",
            Activity.end_time <= utcnow(),
            Activity.status.in_(["published", "finished"]),
        )
        .order_by(Activity.end_time.desc(), Activity.id)
    )
    return ok(
        [
            {
                "id": f"fp-{row.id}",
                "activityId": row.id,
                "title": row.title,
                "clubName": db.get(Club, row.club_id).name,
                "finishedAt": iso(row.end_time),
            }
            for row in rows
        ]
    )
