from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session


def new_id() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    # MySQL DATETIME stores naive UTC, serialized explicitly as UTC at API boundary.
    return datetime.now(UTC).replace(tzinfo=None)


def iso(value: datetime | None) -> str | None:
    return value.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z") if value else None


class BusinessError(Exception):
    def __init__(self, code: int, message: str, status: int = 200):
        self.code, self.message, self.status = code, message, status


def fail(code: int, message: str, status: int = 200) -> None:
    raise BusinessError(code, message, status)


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def page_result(db: Session, query, page: int, page_size: int, serializer) -> dict:
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    rows = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "list": [serializer(row) for row in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }
