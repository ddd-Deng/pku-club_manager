"""Prepare local-only credentials and provision the project databases in Docker MySQL."""

import argparse
import secrets
import time
from pathlib import Path

import pymysql
from dotenv import dotenv_values

from app.config import BACKEND_DIR

SECRETS_FILE = BACKEND_DIR / ".env.mysql"
APP_FILE = BACKEND_DIR / ".env"
TEST_FILE = BACKEND_DIR / ".env.test"


def _exclusive_write(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8") as file:
        file.write(content)


def prepare() -> None:
    if any(path.exists() for path in (SECRETS_FILE, APP_FILE, TEST_FILE)):
        raise SystemExit("本地配置文件已存在；为避免覆盖凭据，未做任何修改")
    root_password = secrets.token_urlsafe(36)
    app_password = secrets.token_urlsafe(36)
    test_password = secrets.token_urlsafe(36)
    token_secret = secrets.token_urlsafe(48)
    _exclusive_write(
        SECRETS_FILE,
        f"MYSQL_ROOT_PASSWORD={root_password}\n"
        f"MYSQL_APP_PASSWORD={app_password}\n"
        f"MYSQL_TEST_PASSWORD={test_password}\nMYSQL_PORT=3307\n",
    )
    _exclusive_write(
        APP_FILE,
        f"DATABASE_URL=mysql+pymysql://campus_app:{app_password}"
        "@127.0.0.1:3307/campus_club?charset=utf8mb4\n"
        f"TOKEN_SECRET={token_secret}\n"
        'CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]\n',
    )
    _exclusive_write(
        TEST_FILE,
        f"TEST_DATABASE_URL=mysql+pymysql://campus_test:{test_password}"
        "@127.0.0.1:3307/campus_club_test?charset=utf8mb4\n",
    )
    print("本地数据库凭据已生成；文件受 .gitignore 保护，内容未输出。")


def provision() -> None:
    values = dotenv_values(SECRETS_FILE)
    root_password = values.get("MYSQL_ROOT_PASSWORD")
    app_password = values.get("MYSQL_APP_PASSWORD")
    test_password = values.get("MYSQL_TEST_PASSWORD")
    port = int(values.get("MYSQL_PORT") or "3307")
    if not all((root_password, app_password, test_password)):
        raise SystemExit("缺少 .env.mysql 的数据库凭据")
    connection = None
    for _ in range(40):
        try:
            connection = pymysql.connect(
                host="127.0.0.1",
                port=port,
                user="root",
                password=root_password,
                autocommit=True,
                connect_timeout=2,
                charset="utf8mb4",
            )
            break
        except pymysql.MySQLError:
            time.sleep(2)
    if connection is None:
        raise SystemExit("MySQL 尚未就绪；请检查 Docker 容器状态")
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS campus_club "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(
                "CREATE DATABASE IF NOT EXISTS campus_club_test "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(
                "CREATE USER IF NOT EXISTS 'campus_app'@'%%' IDENTIFIED BY %s", (app_password,)
            )
            cursor.execute("ALTER USER 'campus_app'@'%%' IDENTIFIED BY %s", (app_password,))
            cursor.execute(
                "CREATE USER IF NOT EXISTS 'campus_test'@'%%' IDENTIFIED BY %s", (test_password,)
            )
            cursor.execute("ALTER USER 'campus_test'@'%%' IDENTIFIED BY %s", (test_password,))
            cursor.execute("GRANT ALL PRIVILEGES ON campus_club.* TO 'campus_app'@'%'")
            cursor.execute("GRANT ALL PRIVILEGES ON campus_club_test.* TO 'campus_test'@'%'")
    print("业务库和独立测试库已创建，应用账号权限已配置。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "provision"])
    args = parser.parse_args()
    prepare() if args.action == "prepare" else provision()
