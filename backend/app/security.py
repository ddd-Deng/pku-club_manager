import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Request
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.common import fail, utcnow
from app.db import get_db
from app.models import Club, LoginSession, User

passwords = PasswordHasher()
# Verify missing accounts too, to avoid the obvious timing difference.
DUMMY_HASH = passwords.hash(secrets.token_urlsafe(32))


def verify_password(encoded: str, password: str) -> bool:
    try:
        return passwords.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def token_digest(token: str, secret: str) -> str:
    return hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def issue_session(db: Session, user: User, secret: str, remember: bool = False) -> str:
    token = secrets.token_urlsafe(48)
    db.add(
        LoginSession(
            user_id=user.id,
            token_hash=token_digest(token, secret),
            expires_at=utcnow() + timedelta(days=7 if remember else 1),
        )
    )
    db.flush()
    return token


def read_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth:
        return None
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token or len(token) > 256:
        fail(401, "登录已失效，请重新登录", 401)
    return token


def optional_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User | None:
    token = read_token(request)
    if token is None:
        return None
    session = db.scalar(
        select(LoginSession).where(
            LoginSession.token_hash == token_digest(token, request.app.state.settings.token_secret),
            LoginSession.expires_at > utcnow(),
        )
    )
    if session is None:
        fail(401, "登录已失效，请重新登录", 401)
    return db.get(User, session.user_id)


def current_user(user: Annotated[User | None, Depends(optional_user)]) -> User:
    if user is None:
        fail(401, "请先登录", 401)
    return user


def student_user(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role not in ("student", "clubAdmin"):
        fail(403, "当前角色不能申请入社或报名活动", 403)
    return user


def managed_club(db: Session, user: User, club_id: str, lock: bool = False) -> Club:
    if user.role not in ("clubAdmin", "admin") or (
        user.role == "clubAdmin" and user.club_id != club_id
    ):
        fail(403, "只能管理自己所属的社团", 403)
    query = select(Club).where(Club.id == club_id)
    if lock:
        query = query.with_for_update()
    club = db.scalar(query)
    if club is None:
        fail(1404, "社团不存在")
    return club


def revoke_user_sessions(db: Session, user_id: str) -> None:
    db.execute(delete(LoginSession).where(LoginSession.user_id == user_id))


Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(current_user)]
StudentUser = Annotated[User, Depends(student_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]
