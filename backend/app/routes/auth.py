from fastapi import APIRouter, Request
from sqlalchemy import delete, or_, select

from app.common import fail, ok
from app.models import LoginSession, StudentIdentity, User
from app.schemas import LoginPayload, RegisterPayload, VerifyPayload
from app.security import (
    DUMMY_HASH,
    CurrentUser,
    Db,
    issue_session,
    passwords,
    read_token,
    token_digest,
    verify_password,
)
from app.serializers import user_data

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(payload: LoginPayload, request: Request, db: Db):
    user = db.scalar(
        select(User).where(
            or_(User.student_no == payload.account, User.email == payload.account.lower())
        )
    )
    valid = verify_password(user.password_hash if user else DUMMY_HASH, payload.password)
    if user is None or not valid:
        fail(1001, "账号或密码错误")
    if passwords.check_needs_rehash(user.password_hash):
        user.password_hash = passwords.hash(payload.password)
    token = issue_session(db, user, request.app.state.settings.token_secret, payload.remember)
    return ok({"token": token, "user": user_data(db, user)})


@router.post("/register")
def register(payload: RegisterPayload, request: Request, db: Db):
    identity = db.scalar(
        select(StudentIdentity)
        .where(StudentIdentity.student_no == payload.student_no)
        .with_for_update()
    )
    if not identity or identity.name != payload.name or identity.email != payload.email:
        fail(1002, "学籍信息不匹配")
    if db.scalar(
        select(User.id).where(
            or_(User.student_no == payload.student_no, User.email == payload.email)
        )
    ):
        fail(1004, "该学号或邮箱已注册")
    user = User(
        name=payload.name,
        student_no=payload.student_no,
        email=payload.email,
        password_hash=passwords.hash(payload.password),
        role="student",
    )
    db.add(user)
    db.flush()
    token = issue_session(db, user, request.app.state.settings.token_secret)
    return ok({"token": token, "user": user_data(db, user)})


@router.post("/logout")
def logout(request: Request, db: Db, user: CurrentUser):
    db.execute(
        delete(LoginSession).where(
            LoginSession.user_id == user.id,
            LoginSession.token_hash
            == token_digest(read_token(request), request.app.state.settings.token_secret),
        )
    )
    return ok()


@router.post("/student-verify")
def verify_student(payload: VerifyPayload, db: Db):
    identity = db.get(StudentIdentity, payload.student_no)
    verified = bool(identity and identity.email == payload.email)
    return ok({"verified": verified, "name": identity.name if verified else ""})
