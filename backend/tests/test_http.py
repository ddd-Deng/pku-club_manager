from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.security import passwords, token_digest, verify_password


class NoDatabaseSessions:
    @contextmanager
    def __call__(self):
        class Session:
            def begin(self):
                return self

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def __getattr__(self, name):
                raise AssertionError(f"此测试不应访问数据库：{name}")

        yield Session()


def test_openapi_has_exactly_37_core_operations():
    schema = create_app().openapi()
    assert (
        sum(
            len(set(value) & {"get", "post", "put", "delete"}) for value in schema["paths"].values()
        )
        == 37
    )
    assert "/api/clubs/{club_id}/recruitments" in schema["paths"]
    assert "/api/ai/chat" not in schema["paths"]
    assert "/api/auth/password/forgot" not in schema["paths"]
    body = schema["components"]["schemas"]["ActivityPayload"]
    assert "startTime" in body["properties"]
    assert "clubId" in body["properties"]


def test_http_envelopes_validation_and_cors_without_database():
    settings = Settings(_env_file=None, token_secret="test-secret-" * 4)
    with TestClient(create_app(settings, sessions=NoDatabaseSessions(), run_jobs=False)) as client:
        hello = client.get("/api/test/hello").json()
        assert hello["code"] == 0 and hello["data"]["source"] == "server"
        assert hello["data"]["serverTime"].endswith("Z")
        assert len(client.get("/api/clubs/categories").json()["data"]) == 4
        assert client.get("/api/user/profile").status_code == 401
        invalid = client.post("/api/auth/login", json={"account": "", "password": "SECRET"})
        assert invalid.json()["code"] == 1003 and "SECRET" not in invalid.text
        missing = client.get("/api/search").json()
        assert missing == {"code": 1404, "message": "接口不存在或尚未实现", "data": None}
        assert client.delete("/api/test/hello").status_code == 405
        cors = client.options(
            "/api/user/profile",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )
        assert cors.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_password_and_token_storage():
    encoded = passwords.hash("example-password")
    assert encoded.startswith("$argon2")
    assert verify_password(encoded, "example-password")
    assert not verify_password(encoded, "wrong-password")
    assert not verify_password("invalid-hash", "password")
    assert token_digest("token", "first") != token_digest("token", "second")
    assert len(token_digest("token", "first")) == 64
