"""Admin workflows and locking tested on the isolated MySQL test database."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import BACKEND_DIR
from app.models import Application, LoginSession, Member, Notification, Registration, User
from tests.conftest import headers
from tests.test_mysql_integration import success

pytestmark = pytest.mark.mysql


def appoint(client, token, club="c-1", user="u-student", previous="u-club"):
    return client.put(
        f"/api/admin/clubs/{club}/president",
        headers=headers(token),
        json={"userId": user, "expectedPresidentId": previous},
    )


def register_other(client):
    return success(
        client.post(
            "/api/auth/register",
            json={
                "studentNo": "2024099",
                "name": "张三",
                "email": "zhangsan@campus.edu.cn",
                "password": "123456",
            },
        )
    )


def test_admin_permissions_filters_and_profile(client, tokens):
    for role in ("student", "owner"):
        assert client.get("/api/admin/users", headers=headers(tokens[role])).status_code == 403
        assert client.get("/api/admin/clubs", headers=headers(tokens[role])).status_code == 403
        assert (
            client.put(
                "/api/admin/users/u-student", headers=headers(tokens[role]), json={"name": "越权"}
            ).status_code
            == 403
        )
        assert (
            client.put(
                "/api/admin/users/u-student/status",
                headers=headers(tokens[role]),
                json={"isActive": False},
            ).status_code
            == 403
        )
        assert appoint(client, tokens[role]).status_code == 403
    assert client.get("/api/admin/users").status_code == 401
    admin = headers(tokens["admin"])
    result = success(client.get("/api/admin/users", headers=admin))
    assert result["total"] == 2
    assert all(row["role"] != "admin" and row["isActive"] for row in result["list"])
    assert all("passwordHash" not in row and "token" not in row for row in result["list"])
    assert (
        success(client.get("/api/admin/users?role=clubAdmin&pageSize=1", headers=admin))["total"]
        == 1
    )
    assert success(client.get("/api/admin/users?keyword=2024001", headers=admin))["total"] == 1
    for payload in ({}, {"role": "admin"}, {"studentNo": "new"}, {"email": "bad"}, {"name": None}):
        assert (
            client.put("/api/admin/users/u-student", headers=admin, json=payload).json()["code"]
            == 1003
        )
    duplicate = client.put(
        "/api/admin/users/u-student", headers=admin, json={"email": "admin@campus.edu.cn"}
    )
    assert duplicate.json()["code"] == 1004
    changed = success(
        client.put(
            "/api/admin/users/u-student",
            headers=admin,
            json={"name": "更新姓名", "email": "UPDATED@CAMPUS.EDU.CN"},
        )
    )
    assert changed["email"] == "updated@campus.edu.cn" and changed["studentNo"] == "2024001"
    for suffix, payload in (("", {"name": "改管理员"}), ("/status", {"isActive": False})):
        assert (
            client.put(f"/api/admin/users/u-admin{suffix}", headers=admin, json=payload).status_code
            == 403
        )


def test_disable_enable_retains_records_and_revokes_tokens(client, sessions, tokens):
    admin = headers(tokens["admin"])
    second = success(
        client.post("/api/auth/login", json={"account": "2024001", "password": "123456"})
    )["token"]
    success(
        client.post(
            "/api/clubs/c-2/applications",
            headers=headers(tokens["student"]),
            json={"message": "保留记录"},
        )
    )
    success(client.post("/api/activities/a-1/registrations", headers=headers(tokens["student"])))
    disabled = success(
        client.put("/api/admin/users/u-student/status", headers=admin, json={"isActive": False})
    )
    assert disabled["isActive"] is False
    for token in (tokens["student"], second):
        assert client.get("/api/user/profile", headers=headers(token)).status_code == 401
    assert (
        client.post("/api/auth/login", json={"account": "2024001", "password": "123456"}).json()[
            "code"
        ]
        == 1006
    )
    assert success(client.get("/api/admin/users?isActive=false", headers=admin))["total"] == 1
    success(client.put("/api/admin/users/u-student/status", headers=admin, json={"isActive": True}))
    assert client.get("/api/user/profile", headers=headers(second)).status_code == 401
    assert (
        client.post("/api/auth/login", json={"account": "2024001", "password": "123456"}).json()[
            "code"
        ]
        == 0
    )
    with sessions() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Application)
                .where(Application.user_id == "u-student")
            )
            == 1
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(Registration.user_id == "u-student")
            )
            == 1
        )
    assert (
        client.put(
            "/api/admin/users/u-club/status", headers=admin, json={"isActive": False}
        ).status_code
        == 409
    )


def test_handover_member_application_notification_and_permissions(client, sessions, tokens):
    application = success(
        client.post(
            "/api/clubs/c-1/applications",
            headers=headers(tokens["student"]),
            json={"message": "申请"},
        )
    )
    result = success(appoint(client, tokens["admin"]))
    assert result["president"]["id"] == "u-student"
    for role in ("owner", "student"):
        assert client.get("/api/user/profile", headers=headers(tokens[role])).status_code == 401
    with sessions() as db:
        assert db.get(User, "u-club").role == "student" and db.get(User, "u-club").club_id is None
        assert db.get(User, "u-student").club_id == "c-1"
        assert db.get(Member, "m-owner").role == "member"
        assert db.get(Application, application["id"]).status == "approved"
        assert (
            db.scalar(select(func.count()).select_from(Member).where(Member.club_id == "c-1")) == 2
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == "u-student")
            )
            == 1
        )
    new = success(
        client.post("/api/auth/login", json={"account": "2024001", "password": "123456"})
    )["token"]
    old = success(
        client.post("/api/auth/login", json={"account": "2021002", "password": "123456"})
    )["token"]
    assert (
        client.put(
            "/api/clubs/c-1", headers=headers(new), json={"description": "新社长维护"}
        ).json()["code"]
        == 0
    )
    assert (
        client.put("/api/clubs/c-1", headers=headers(old), json={"description": "越权"}).status_code
        == 403
    )
    assert (
        client.put(
            "/api/clubs/c-2", headers=headers(new), json={"description": "跨社团"}
        ).status_code
        == 403
    )
    success(
        appoint(client, tokens["admin"])
    )  # Idempotent retry must not add members or revoke new sessions.
    assert client.get("/api/user/profile", headers=headers(new)).status_code == 200
    with sessions() as db:
        assert (
            db.scalar(select(func.count()).select_from(Member).where(Member.club_id == "c-1")) == 2
        )
    success(
        client.put(
            "/api/admin/users/u-club/status",
            headers=headers(tokens["admin"]),
            json={"isActive": False},
        )
    )


def test_first_appointment_existing_member_and_rejections(client, sessions, tokens):
    admin = headers(tokens["admin"])
    with sessions.begin() as db:
        db.add(Member(id="existing", user_id="u-student", club_id="c-2", role="officer"))
    assert appoint(client, tokens["admin"], club="c-2", previous="u-club").status_code == 409
    success(appoint(client, tokens["admin"], club="c-2", previous=None))
    with sessions() as db:
        assert db.get(Member, "existing").role == "owner"
        assert (
            db.scalar(select(func.count()).select_from(Member).where(Member.club_id == "c-2")) == 1
        )
    assert appoint(client, tokens["admin"], club="c-3", previous=None).status_code == 409
    assert appoint(client, tokens["admin"], club="missing", previous=None).status_code == 404
    assert appoint(client, tokens["admin"], user="missing").status_code == 404
    other = register_other(client)
    success(
        client.put(
            f"/api/admin/users/{other['user']['id']}/status",
            headers=admin,
            json={"isActive": False},
        )
    )
    assert appoint(client, tokens["admin"], user=other["user"]["id"]).status_code == 409
    assert (
        client.put(
            "/api/admin/clubs/c-1/president", headers=admin, json={"userId": "u-club"}
        ).json()["code"]
        == 1003
    )


def race(actions):
    barrier = Barrier(len(actions))

    def call(action):
        barrier.wait(timeout=10)
        return action()

    with ThreadPoolExecutor(max_workers=len(actions)) as pool:
        return list(pool.map(call, actions))


def test_concurrent_two_clubs_cannot_share_one_president(client, sessions, tokens):
    responses = race(
        [
            lambda: appoint(client, tokens["admin"], club="c-2", previous=None),
            lambda: appoint(client, tokens["admin"], club="c-3", previous=None),
        ]
    )
    assert sorted(response.status_code for response in responses) == [200, 409]
    with sessions() as db:
        user = db.get(User, "u-student")
        members = db.scalars(select(Member).where(Member.user_id == user.id)).all()
        assert (
            len(members) == 1 and members[0].club_id == user.club_id and members[0].role == "owner"
        )


def test_concurrent_handover_detects_stale_expected_owner(client, sessions, tokens):
    other = register_other(client)
    responses = race(
        [
            lambda: appoint(client, tokens["admin"]),
            lambda: appoint(client, tokens["admin"], user=other["user"]["id"]),
        ]
    )
    assert sorted(response.status_code for response in responses) == [200, 409]
    with sessions() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Member)
                .where(Member.club_id == "c-1", Member.role == "owner")
            )
            == 1
        )
        assert (
            db.scalar(select(func.count()).select_from(Member).where(Member.club_id == "c-1")) == 2
        )
        assert db.get(Member, "m-owner").role == "member"


def test_concurrent_disable_and_appointment_are_consistent(client, sessions, tokens):
    responses = race(
        [
            lambda: appoint(client, tokens["admin"], club="c-2", previous=None),
            lambda: client.put(
                "/api/admin/users/u-student/status",
                headers=headers(tokens["admin"]),
                json={"isActive": False},
            ),
        ]
    )
    assert sorted(response.status_code for response in responses) == [200, 409]
    with sessions() as db:
        user = db.get(User, "u-student")
        assert (user.is_active and user.role == "clubAdmin") or (
            not user.is_active and user.role == "student"
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(LoginSession)
                .where(LoginSession.user_id == user.id)
            )
            == 0
        )


def test_concurrent_login_and_disable_never_revives_old_sessions(client, sessions, tokens):
    responses = race(
        [
            lambda: client.post(
                "/api/auth/login", json={"account": "2024001", "password": "123456"}
            ),
            lambda: client.put(
                "/api/admin/users/u-student/status",
                headers=headers(tokens["admin"]),
                json={"isActive": False},
            ),
        ]
    )
    assert responses[1].json()["code"] == 0
    if responses[0].json()["code"] == 0:
        assert (
            client.get(
                "/api/user/profile", headers=headers(responses[0].json()["data"]["token"])
            ).status_code
            == 401
        )
    else:
        assert responses[0].json()["code"] == 1006
    with sessions() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(LoginSession)
                .where(LoginSession.user_id == "u-student")
            )
            == 0
        )


def test_owner_inconsistency_rolls_back_handover(client, sessions, tokens):
    with sessions.begin() as db:
        db.get(Member, "m-owner").role = "member"
    assert appoint(client, tokens["admin"]).status_code == 409
    with sessions() as db:
        assert db.get(User, "u-club").role == "clubAdmin"
        assert db.get(User, "u-student").role == "student"
    assert client.get("/api/user/profile", headers=headers(tokens["owner"])).status_code == 200


def test_database_enforces_unique_president_and_role_club(client, sessions, tokens):
    with pytest.raises(SQLAlchemyError), sessions.begin() as db:
        user = db.get(User, "u-student")
        user.role, user.club_id = "clubAdmin", "c-1"
        db.flush()
    with pytest.raises(SQLAlchemyError), sessions.begin() as db:
        db.get(User, "u-student").club_id = "c-2"
        db.flush()


def test_migration_preserves_accounts_and_members(sessions):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = sessions.kw["bind"].url.render_as_string(
        hide_password=False
    )
    with sessions() as db:
        before = db.execute(text("SELECT id,name,role,club_id FROM users ORDER BY id")).all()
        members = db.execute(text("SELECT id,user_id,club_id,role FROM members ORDER BY id")).all()
    try:
        command.downgrade(config, "0001")
        command.upgrade(config, "head")
        with sessions() as db:
            assert (
                db.execute(text("SELECT id,name,role,club_id FROM users ORDER BY id")).all()
                == before
            )
            assert (
                db.execute(text("SELECT id,user_id,club_id,role FROM members ORDER BY id")).all()
                == members
            )
            assert all(db.scalars(select(User.is_active)))
    finally:
        command.upgrade(config, "head")


def test_migration_refuses_inconsistent_owner_without_reset(sessions):
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = sessions.kw["bind"].url.render_as_string(
        hide_password=False
    )
    command.downgrade(config, "0001")
    try:
        with sessions.begin() as db:
            db.execute(text("UPDATE members SET role='member' WHERE id='m-owner'"))
        with pytest.raises(RuntimeError, match="数据不一致"):
            command.upgrade(config, "head")
        with sessions() as db:
            assert db.scalar(text("SELECT role FROM members WHERE id='m-owner'")) == "member"
            assert db.scalar(text("SELECT role FROM users WHERE id='u-club'")) == "clubAdmin"
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0001"
    finally:
        with sessions.begin() as db:
            db.execute(text("UPDATE members SET role='owner' WHERE id='m-owner'"))
        command.upgrade(config, "head")
