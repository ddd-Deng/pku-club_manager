import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException

from app.common import BusinessError, iso, ok, utcnow
from app.config import Settings
from app.db import session_factory
from app.jobs import finish_loop
from app.routes import activities, auth, clubs, notifications, users

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, sessions=None, run_jobs: bool = True) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        settings.require_secret()
        app.state.sessions = sessions if sessions is not None else session_factory(settings)
        stop = asyncio.Event()
        task = (
            asyncio.create_task(
                finish_loop(app.state.sessions, settings.finish_interval_seconds, stop)
            )
            if run_jobs
            else None
        )
        try:
            yield
        finally:
            stop.set()
            if task:
                await task
            if sessions is None:
                app.state.sessions.kw["bind"].dispose()

    app = FastAPI(title="校园社团管理核心 API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def error(code: int, message: str, status: int = 200):
        return JSONResponse({"code": code, "message": message, "data": None}, status_code=status)

    @app.exception_handler(BusinessError)
    async def business_error(request: Request, exc: BusinessError):
        return error(exc.code, exc.message, exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Avoid echoing submitted passwords or other input values in error responses.
        return error(1003, "请求参数不完整、格式错误或超出允许范围")

    @app.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError):
        return error(1004, "资源已存在或关联数据不符合约束")

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logger.error("数据库操作失败，请检查连接和迁移状态")
        return error(5000, "数据库暂不可用，请稍后重试", 503)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error(
            1404 if exc.status_code == 404 else exc.status_code,
            "接口不存在或尚未实现" if exc.status_code == 404 else "请求方法不允许",
            exc.status_code,
        )

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        logger.error("请求处理异常：%s", type(exc).__name__)
        return error(5000, "服务异常，请稍后重试", 500)

    @app.get("/api/test/hello", tags=["连通性"])
    def hello():
        return ok({"message": "hello world", "source": "server", "serverTime": iso(utcnow())})

    for router in (
        auth.router,
        users.router,
        clubs.router,
        activities.router,
        notifications.router,
    ):
        app.include_router(router)
    return app


app = create_app()
