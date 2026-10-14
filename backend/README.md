# 校园社团管理核心后端

Python 3.11+、FastAPI、MySQL 8。实现 `docs/api.md` 标记的 37 个核心接口；`/docs` 提供可交互接口说明。`backend/` 与前端在同一 Git 仓库中。

第 7 组多人联调采用共享开发数据库时，见 [共享数据库说明](./SHARED_DATABASE.md)。它与每位组员本机的独立测试库分开。

macOS 组员连接现有共享数据库的完整安装与启动步骤见 [项目 README 的 macOS 章节](../README.md#macos-启动共享开发数据库)。Mac 虚拟环境的 Python 路径为 `.venv/bin/python`；下方 PowerShell 命令中的 `.venv\Scripts\` 路径仅用于 Windows。共享库日常启动无需执行下方本地建库、迁移或初始化命令。

本机开发优先使用 `compose.yaml` 启动专用 MySQL。容器仅监听本机 `127.0.0.1:3307`，数据保存在 Docker 命名卷 `campus-club-mysql-data` 中；停止或重启容器不会清除业务数据。Git 只保存编排、迁移和初始化脚本，不保存数据卷与密码。

## 本地准备（PowerShell）

在 `backend/` 中安装依赖并自动生成本机凭据，然后启动 Docker MySQL、创建业务库和独立测试库：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m app.local_db prepare
docker compose --env-file .env.mysql -f compose.yaml up -d
.\.venv\Scripts\python.exe -m app.local_db provision
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8080
```

`prepare` 只在第一次运行，生成 `.env.mysql`、`.env`、`.env.test`；文件已存在时会拒绝覆盖。`provision` 可重复执行，只管理两个项目数据库和专用用户。之后重启数据库只需运行 `docker compose --env-file .env.mysql -f compose.yaml up -d`。数据库容器启动后，再启动后端服务即可。停止数据库可运行 `docker compose --env-file .env.mysql -f compose.yaml stop`，数据仍保留。

如果不用 Docker，先在已有 MySQL 实例中创建两个**独立**的空数据库。数据库创建只需执行一次。测试库会在测试前清理本项目的业务表，绝不能与业务库共用。

```sql
CREATE DATABASE campus_club CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE campus_club_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

在 `backend/` 下创建 `.env`，以 `.env.example` 为模板，填入能访问 `campus_club` 的 `DATABASE_URL` 和随机生成的 `TOKEN_SECRET`。账号密码写入此文件，不提交 Git。测试时按 `.env.test.example` 创建 `.env.test`，填入只访问 `campus_club_test` 的 `TEST_DATABASE_URL`。若密码包含 `@`、`:` 等字符，需要对 URL 中的密码部分进行 URL 编码。创建随机密钥示例：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

已有 MySQL 的迁移与启动命令：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\alembic.exe -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8080
```

迁移记录在 `migrations/versions/`；启动服务不会自动建表或重置数据。`app.seed` 需要**显式**执行，可重复运行且不会覆盖已有记录。演示账号：学生 `2024001`、社长 `2021002`、管理员 `admin`，密码均为 `123456`。演示学籍另含可注册账号 `2024099` / `zhangsan@campus.edu.cn` / `张三` 和 `2024100` / `lisi@campus.edu.cn` / `李四`。这些凭据仅用于课程演示。

## 与前端联调

前端默认继续使用 mock。在 `frontend/` 目录新建 `.env.development.local`：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8080
```

在 `frontend/` 中重启 `npm run dev`，访问 `/test/hello`，其 `source` 应为 `server`；再检查登录注册、首页和社团广场。真实后端尚未提供搜索、场地、AI 和邮件找回接口，对应页面或请求会显示失败状态。前端占位页面尚不能通过用户界面完成申请、报名等操作，可先在 `http://127.0.0.1:8080/docs` 演示对应接口。

## 检查与测试

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q
```

仅在测试库配置就绪时执行的用例包含数据持久化、权限隔离、完整业务流程和并发报名。未设置 `TEST_DATABASE_URL` 时，它们会标为 `skipped`，并不意味着已通过。若配置了测试库但数据库不可访问，测试会失败而不会跳过。测试代码只允许数据库名为 `campus_club_test`，并且不自动创建或删除整个数据库。

数据库错误会被统一转换成响应，服务日志不会输出连接 URL 或密码。活动完成状态由服务内定时任务维护，单次更新可重复运行；多进程部署时应改为独立定时工作进程。
