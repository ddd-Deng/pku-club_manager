import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.config import BACKEND_DIR, Settings
from app.db import session_factory
from app.main import create_app
from app.models import Base
from app.seed import seed


def validate_test_database(url: str) -> str:
    parsed = make_url(url)
    if parsed.drivername != "mysql+pymysql" or parsed.database != "campus_club_test":
        raise ValueError("测试只允许 mysql+pymysql 的 campus_club_test 数据库")
    return url


@pytest.fixture(scope="session")
def mysql_sessions():
    url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(BACKEND_DIR / ".env.test").get(
        "TEST_DATABASE_URL"
    )
    if not url:
        pytest.skip("未配置 TEST_DATABASE_URL，MySQL 集成与并发测试未执行")
    validate_test_database(url)
    settings = Settings(_env_file=None, database_url=url, token_secret="test-secret-" * 4)
    sessions = session_factory(settings)
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.attributes["database_url"] = url
    # A configured but unavailable database must fail, never silently skip.
    command.upgrade(cfg, "head")
    yield sessions
    sessions.kw["bind"].dispose()


@pytest.fixture
def sessions(mysql_sessions):
    with mysql_sessions.begin() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
    seed(mysql_sessions)
    yield mysql_sessions


@pytest.fixture
def client(sessions):
    settings = Settings(_env_file=None, token_secret="test-secret-" * 4)
    with TestClient(create_app(settings, sessions=sessions, run_jobs=False)) as client:
        yield client


@pytest.fixture
def tokens(client):
    return {
        role: client.post(
            "/api/auth/login", json={"account": account, "password": "123456"}
        ).json()["data"]["token"]
        for role, account in (("student", "2024001"), ("owner", "2021002"), ("admin", "admin"))
    }


def headers(token):
    return {"Authorization": f"Bearer {token}"}
