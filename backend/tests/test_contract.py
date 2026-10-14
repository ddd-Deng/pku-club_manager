from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable

from app.common import iso
from app.config import Settings
from app.models import Base
from app.schemas import ActivityPayload, MemberPayload, RegisterPayload


def test_schema_alias_and_email():
    data = RegisterPayload(
        name="张三", studentNo="2024099", email="TEST@CAMPUS.EDU.CN", password="123456"
    )
    assert data.student_no == "2024099"
    assert data.email == "test@campus.edu.cn"
    with pytest.raises(ValidationError):
        RegisterPayload(**data.model_dump(), role="admin")


def test_patch_requires_one_member_action():
    for data in ({}, {"role": "member", "action": "remove"}, {"role": None}):
        with pytest.raises(ValidationError):
            MemberPayload(**data)


def test_dates_are_explicit_utc():
    data = dict(
        title="测试",
        description="测试",
        location="教室",
        capacity=1,
        type="讲座",
        startTime="2030-01-01T09:00:00+08:00",
        endTime="2030-01-01T10:00:00+08:00",
    )
    activity = ActivityPayload(**data)
    assert iso(activity.start_time) == "2030-01-01T01:00:00Z"
    data["startTime"] = "2030-01-01T09:00:00"
    with pytest.raises(ValidationError):
        ActivityPayload(**data)
    assert iso(datetime.now(UTC).replace(tzinfo=None)).endswith("Z")


def test_mysql_schema_compiles_with_constraints():
    for table in Base.metadata.sorted_tables:
        sql = str(CreateTable(table).compile(dialect=mysql.dialect()))
        assert "ENGINE=InnoDB" in sql
        assert "CHARSET=utf8mb4" in sql
    assert len(Base.metadata.tables) == 11


def test_config_rejects_sqlite_and_example_secret():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="sqlite://")
    with pytest.raises(RuntimeError):
        Settings(_env_file=None, token_secret="CHANGE_ME" * 8).require_secret()
