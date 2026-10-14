"""Run against an explicit, isolated campus_club_test MySQL database."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.common import utcnow
from app.jobs import finish_activities
from app.models import Activity, LoginSession, Member, Notification, Registration
from app.security import token_digest
from tests.conftest import headers, validate_test_database

pytestmark = pytest.mark.mysql


def success(response):
    body = response.json()
    assert response.status_code == 200, body
    assert body["code"] == 0, body
    return body["data"]


def future(days=5, hours=0):
    return (datetime.now(UTC) + timedelta(days=days, hours=hours)).isoformat()


def activity_payload(capacity=1):
    return {
        "title": "联调演示活动",
        "description": "报名并取消的流程测试",
        "location": "活动中心",
        "startTime": future(5),
        "endTime": future(5, 2),
        "capacity": capacity,
        "type": "实践",
        "cover": "🎯",
    }


def test_database_guard_rejects_business_database():
    with pytest.raises(ValueError):
        validate_test_database("mysql+pymysql://u:p@localhost/campus_club")
    with pytest.raises(ValueError):
        validate_test_database("sqlite:///campus_club_test")


def test_auth_whitelist_session_and_profile(client, sessions, tokens):
    verify = success(
        client.post(
            "/api/auth/student-verify",
            json={"studentNo": "2024099", "email": "zhangsan@campus.edu.cn"},
        )
    )
    assert verify == {"verified": True, "name": "张三"}
    bad = client.post(
        "/api/auth/register",
        json={
            "name": "冒用",
            "studentNo": "2024099",
            "email": "zhangsan@campus.edu.cn",
            "password": "123456",
        },
    ).json()
    assert bad["code"] == 1002
    created = success(
        client.post(
            "/api/auth/register",
            json={
                "name": "张三",
                "studentNo": "2024099",
                "email": "zhangsan@campus.edu.cn",
                "password": "123456",
            },
        )
    )
    assert created["user"]["role"] == "student"
    assert created["user"]["clubId"] is None
    assert (
        client.post(
            "/api/auth/register",
            json={
                "name": "张三",
                "studentNo": "2024099",
                "email": "zhangsan@campus.edu.cn",
                "password": "123456",
            },
        ).json()["code"]
        == 1004
    )
    token = created["token"]
    with sessions.begin() as db:
        session = db.scalar(
            select(LoginSession).where(LoginSession.user_id == created["user"]["id"])
        )
        assert session.token_hash != token
        assert session.token_hash == token_digest(token, "test-secret-" * 4)
        session.expires_at = utcnow() - timedelta(seconds=1)
    assert client.get("/api/user/profile", headers=headers(token)).status_code == 401
    fresh = success(
        client.post(
            "/api/auth/login",
            json={
                "account": "2024099",
                "password": "123456",
                "remember": True,
            },
        )
    )["token"]
    assert success(client.get("/api/user/profile", headers=headers(fresh)))["name"] == "张三"
    assert (
        client.put(
            "/api/user/password",
            headers=headers(fresh),
            json={
                "oldPassword": "wrong",
                "newPassword": "abcdef",
            },
        ).json()["code"]
        == 1005
    )
    success(
        client.put(
            "/api/user/password",
            headers=headers(fresh),
            json={
                "oldPassword": "123456",
                "newPassword": "abcdef",
            },
        )
    )
    assert client.get("/api/user/profile", headers=headers(fresh)).status_code == 401
    assert (
        client.post("/api/auth/login", json={"account": "2024099", "password": "123456"}).json()[
            "code"
        ]
        == 1001
    )
    changed = success(
        client.post("/api/auth/login", json={"account": "2024099", "password": "abcdef"})
    )["token"]
    success(client.post("/api/auth/logout", headers=headers(changed)))
    assert client.get("/api/user/profile", headers=headers(changed)).status_code == 401
    assert client.get("/api/notifications", headers=headers(tokens["student"])).status_code == 200


def test_club_application_review_and_permissions(client, sessions, tokens):
    student, owner, admin = (headers(tokens[key]) for key in ("student", "owner", "admin"))
    clubs = success(client.get("/api/clubs", params={"keyword": "摄影", "pageSize": 8}))
    assert clubs["total"] == 1 and clubs["list"][0]["id"] == "c-1"
    assert len(success(client.get("/api/clubs/categories"))) == 4
    assert len(success(client.get("/api/clubs/recommended"))) == 4
    assert success(client.get("/api/clubs/c-1"))["notices"]
    assert success(client.get("/api/clubs/c-1/recruitments"))
    assert client.put("/api/clubs/c-2", headers=owner, json={"name": "不允许"}).status_code == 403
    unsafe_html = "<p>欢迎</p><script>alert(1)</script>"
    unsafe_html += '<a href="javascript:alert(1)">链接</a>'
    updated = success(
        client.put(
            "/api/clubs/c-1",
            headers=owner,
            json={"introduction": unsafe_html},
        )
    )
    assert "<script" not in updated["introduction"]
    assert "javascript:" not in updated["introduction"]
    published = success(
        client.post(
            "/api/clubs/c-1/recruitments",
            headers=owner,
            json={
                "title": "新学期招新",
                "content": "欢迎报名",
                "deadline": (datetime.now(UTC) + timedelta(days=10)).date().isoformat(),
            },
        )
    )
    assert published["clubId"] == "c-1"
    app = success(
        client.post("/api/clubs/c-1/applications", headers=student, json={"message": "喜欢摄影"})
    )
    assert (
        client.post(
            "/api/clubs/c-1/applications", headers=student, json={"message": "重复"}
        ).json()["code"]
        == 1409
    )
    assert success(client.get("/api/notifications/unread-count", headers=owner)) >= 1
    assert client.get("/api/clubs/c-1/applications", headers=student).status_code == 403
    assert (
        client.put(
            f"/api/clubs/c-2/applications/{app['id']}", headers=admin, json={"action": "approve"}
        ).json()["code"]
        == 1404
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: client.put(
                    f"/api/clubs/c-1/applications/{app['id']}",
                    headers=owner,
                    json={"action": "approve"},
                ).json()["code"],
                range(2),
            )
        )
    assert sorted(results) == [0, 1410]
    members = success(client.get("/api/clubs/c-1/members", headers=owner))
    member = next(row for row in members if row["name"] == "林晓")
    with sessions.begin() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Member)
                .where(Member.club_id == "c-1", Member.user_id == "u-student")
            )
            == 1
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == "u-student", Notification.type == "application")
            )
            == 1
        )
    assert (
        client.put(
            f"/api/clubs/c-1/members/{member['id']}", headers=student, json={"role": "officer"}
        ).status_code
        == 403
    )
    assert (
        client.put(
            "/api/clubs/c-1/members/m-owner", headers=admin, json={"action": "remove"}
        ).status_code
        == 403
    )
    assert (
        success(
            client.put(
                f"/api/clubs/c-1/members/{member['id']}", headers=owner, json={"role": "officer"}
            )
        )["role"]
        == "officer"
    )
    success(client.put("/api/user/profile", headers=student, json={"name": "林晓改名"}))
    own = success(client.get("/api/user/applications", headers=student))
    assert own[0]["applicantName"] == "林晓改名"
    notification = success(client.get("/api/notifications", headers=student))["list"][0]
    assert (
        client.put(f"/api/notifications/{notification['id']}/read", headers=owner).json()["code"]
        == 1404
    )
    assert (
        success(client.put(f"/api/notifications/{notification['id']}/read", headers=student))[
            "read"
        ]
        is True
    )
    assert success(client.put("/api/notifications/read-all", headers=student))["updated"] == 0
    assert success(client.get("/api/clubs/c-1", headers=student))["memberCount"] == 2
    assert (
        client.post(
            "/api/clubs/c-1/applications", headers=student, json={"message": "再次申请"}
        ).json()["code"]
        == 1409
    )


def test_activity_lifecycle_registration_and_history(client, sessions, tokens):
    student, owner, admin = (headers(tokens[key]) for key in ("student", "owner", "admin"))
    item = success(client.post("/api/activities", headers=owner, json=activity_payload(capacity=1)))
    activity_id = item["id"]
    assert item["status"] == "draft"
    assert client.get(f"/api/activities/{activity_id}").status_code == 401
    assert client.get(f"/api/activities/{activity_id}", headers=student).status_code == 403
    assert (
        client.post("/api/activities", headers=student, json=activity_payload()).status_code == 403
    )
    assert (
        client.post(
            "/api/activities", headers=owner, json={**activity_payload(), "clubId": "c-2"}
        ).status_code
        == 403
    )
    assert (
        success(client.post(f"/api/activities/{activity_id}/publish", headers=owner))["status"]
        == "published"
    )
    assert (
        client.post(f"/api/activities/{activity_id}/publish", headers=owner).json()["code"] == 1410
    )
    assert success(client.get(f"/api/activities/{activity_id}"))["registered"] is False
    reg = success(client.post(f"/api/activities/{activity_id}/registrations", headers=student))
    assert reg["userId"] == "u-student"
    assert (
        client.post(f"/api/activities/{activity_id}/registrations", headers=student).json()["code"]
        == 1409
    )
    assert (
        success(client.get(f"/api/activities/{activity_id}", headers=student))["registeredCount"]
        == 1
    )
    assert (
        client.put(f"/api/activities/{activity_id}", headers=owner, json={"capacity": 0}).json()[
            "code"
        ]
        == 1003
    )
    assert client.delete(f"/api/activities/{activity_id}", headers=admin).json()["code"] == 1410
    success(client.delete(f"/api/activities/{activity_id}/registrations", headers=student))
    assert (
        success(client.get("/api/user/activity-registrations", headers=student))[0]["status"]
        == "cancelled"
    )
    success(client.post(f"/api/activities/{activity_id}/registrations", headers=student))
    assert (
        success(client.get(f"/api/activities/{activity_id}", headers=student))["registered"] is True
    )
    assert (
        client.post(f"/api/activities/{activity_id}/registrations", headers=admin).status_code
        == 403
    )
    with sessions.begin() as db:
        activity = db.get(Activity, activity_id)
        activity.start_time = utcnow() - timedelta(days=2)
        activity.end_time = utcnow() - timedelta(days=1)
    assert (
        client.delete(f"/api/activities/{activity_id}/registrations", headers=student).json()[
            "code"
        ]
        == 1410
    )
    assert finish_activities(sessions) == 1
    assert finish_activities(sessions) == 0
    assert success(client.get(f"/api/activities/{activity_id}"))["status"] == "finished"
    assert (
        success(client.get("/api/user/footprints", headers=student))[0]["activityId"] == activity_id
    )


def test_last_slot_concurrent_enrollment_and_pagination(client, sessions, tokens):
    owner = headers(tokens["owner"])
    first = headers(tokens["student"])
    second_token = success(
        client.post(
            "/api/auth/register",
            json={
                "name": "张三",
                "studentNo": "2024099",
                "email": "zhangsan@campus.edu.cn",
                "password": "123456",
            },
        )
    )["token"]
    activity_id = success(client.post("/api/activities", headers=owner, json=activity_payload()))[
        "id"
    ]
    success(client.post(f"/api/activities/{activity_id}/publish", headers=owner))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda token: client.post(
                    f"/api/activities/{activity_id}/registrations", headers=token
                ).json()["code"],
                (first, headers(second_token)),
            )
        )
    assert sorted(results) == [0, 1411]
    assert success(client.get(f"/api/activities/{activity_id}"))["registeredCount"] == 1
    with sessions.begin() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(Registration)
                .where(Registration.activity_id == activity_id, Registration.status == "registered")
            )
            == 1
        )
    page = success(client.get("/api/activities", params={"page": 2, "pageSize": 2}))
    assert page["page"] == 2 and page["pageSize"] == 2 and page["total"] >= 8
    assert client.get("/api/activities", params={"pageSize": 101}).json()["code"] == 1003


def test_rejection_retry_and_isolation(client, sessions, tokens):
    student, owner, admin = (headers(tokens[key]) for key in ("student", "owner", "admin"))
    first = success(client.post("/api/clubs/c-2/applications", headers=student, json={}))
    assert (
        client.put(
            f"/api/clubs/c-2/applications/{first['id']}", headers=owner, json={"action": "reject"}
        ).status_code
        == 403
    )
    rejected = success(
        client.put(
            f"/api/clubs/c-2/applications/{first['id']}", headers=admin, json={"action": "reject"}
        )
    )
    assert rejected["status"] == "rejected"
    second = success(client.post("/api/clubs/c-2/applications", headers=student, json={}))
    assert second["id"] != first["id"]
    member = success(
        client.put(
            f"/api/clubs/c-2/applications/{second['id']}", headers=admin, json={"action": "approve"}
        )
    )
    assert member["status"] == "approved"
    assert (
        client.put(
            "/api/clubs/c-1/members/"
            + success(client.get("/api/clubs/c-2/members", headers=admin))[0]["id"],
            headers=owner,
            json={"action": "remove"},
        ).json()["code"]
        == 1404
    )
