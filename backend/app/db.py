from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings


def session_factory(settings: Settings) -> sessionmaker[Session]:
    settings.require_database()
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        isolation_level="READ COMMITTED",
        connect_args={"connect_timeout": 5},
    )
    return sessionmaker(engine, expire_on_commit=False)


def get_db(request: Request) -> Generator[Session]:
    # One transaction includes all business writes and notifications.
    with request.app.state.sessions() as db, db.begin():
        yield db
