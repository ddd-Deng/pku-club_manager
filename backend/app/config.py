from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = ""
    token_secret: str = ""
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    finish_interval_seconds: int = Field(default=60, ge=1)

    @field_validator("database_url")
    @classmethod
    def mysql_only(cls, value: str) -> str:
        if value and make_url(value).drivername != "mysql+pymysql":
            raise ValueError("DATABASE_URL 必须使用 mysql+pymysql")
        return value

    def require_database(self) -> None:
        if not self.database_url:
            raise RuntimeError("请在 backend/.env 中配置 DATABASE_URL")

    def require_secret(self) -> None:
        if len(self.token_secret) < 32 or self.token_secret.startswith("CHANGE_ME"):
            raise RuntimeError("TOKEN_SECRET 必须是至少 32 字符的随机密钥")
