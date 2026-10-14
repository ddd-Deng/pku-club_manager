from datetime import date, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.common import new_id, utcnow


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Club(Record, Base):
    __tablename__ = "clubs"
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(30), index=True)
    logo: Mapped[str] = mapped_column(String(2048), default="🎓")
    description: Mapped[str] = mapped_column(String(500), default="")
    introduction: Mapped[str] = mapped_column(Text, default="")
    founded_at: Mapped[date]
    tags: Mapped[list] = mapped_column(JSON, default=list)


class User(Record, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('student','clubAdmin','admin')"),)
    name: Mapped[str] = mapped_column(String(100))
    student_no: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")
    avatar: Mapped[str] = mapped_column(String(2048), default="🧑‍🎓")
    club_id: Mapped[str | None] = mapped_column(ForeignKey("clubs.id"))


class StudentIdentity(Base):
    __tablename__ = "student_identities"
    student_no: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)


class LoginSession(Record, Base):
    __tablename__ = "login_sessions"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class Member(Record, Base):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_member_club_user"),
        CheckConstraint("role IN ('member','officer','owner')"),
    )
    club_id: Mapped[str] = mapped_column(ForeignKey("clubs.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="member")


class Notice(Record, Base):
    __tablename__ = "notices"
    club_id: Mapped[str] = mapped_column(ForeignKey("clubs.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)


class Recruitment(Record, Base):
    __tablename__ = "recruitments"
    club_id: Mapped[str] = mapped_column(ForeignKey("clubs.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    deadline: Mapped[date]


class Application(Record, Base):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_application_club_user_status", "club_id", "user_id", "status"),
        CheckConstraint("status IN ('pending','approved','rejected')"),
    )
    club_id: Mapped[str] = mapped_column(ForeignKey("clubs.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    comment: Mapped[str | None] = mapped_column(String(500))


class Activity(Record, Base):
    __tablename__ = "activities"
    __table_args__ = (
        CheckConstraint("capacity > 0"),
        CheckConstraint("end_time > start_time"),
        CheckConstraint("status IN ('draft','published','unpublished','finished')"),
    )
    club_id: Mapped[str] = mapped_column(ForeignKey("clubs.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    cover: Mapped[str] = mapped_column(String(2048), default="🎯")
    location: Mapped[str] = mapped_column(String(200))
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    capacity: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    type: Mapped[str] = mapped_column(String(30))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class Registration(Record, Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_registration_activity_user"),
        CheckConstraint("status IN ('registered','cancelled')"),
    )
    activity_id: Mapped[str] = mapped_column(ForeignKey("activities.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="registered")


class Notification(Record, Base):
    __tablename__ = "notifications"
    __table_args__ = (CheckConstraint("type IN ('application','activity','venue')"),)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(default=False)
    link: Mapped[str] = mapped_column(String(300))


# Explicit MySQL options for all tables, including migration-created tables.
for table in Base.metadata.tables.values():
    table.dialect_options["mysql"]["engine"] = "InnoDB"
    table.dialect_options["mysql"]["charset"] = "utf8mb4"
