# 校园社团管理系统（基础 V1.0）

软件工程课程小组项目，前后端按目录分工，由同一个 Git 仓库管理。

## 项目结构

```text
frontend/          # Vue 前端工程
  src/             # 页面、组件、路由、接口调用、类型、mock
  package.json     # 前端依赖与运行命令
  vite.config.ts   # 前端构建和开发服务配置
backend/           # FastAPI + MySQL 后端工程
  app/             # 接口、业务、权限和数据库模型
  migrations/      # Alembic 数据库迁移
  tests/           # 后端测试
  scripts/         # 共享数据库部署与维护脚本
docs/              # 前后端共同接口契约、设计资料
scripts/           # 项目级辅助脚本
  dev.py           # Windows 本机服务启动与停止逻辑
  start.cmd        # 双击启动
  stop.cmd         # 双击停止
CLAUDE.md          # 项目开发规则
.editorconfig      # 前后端共同的编辑器规则
.gitignore         # 全仓库忽略规则
```

前端源码使用标准的 `frontend/src/` 结构；入口、依赖、锁文件、环境配置和构建产物均位于 `frontend/`。源码迁移不改变接口地址或用户权限。

## Windows 一键启动

这台电脑已安装依赖并配置共享数据库。日常使用进入项目的 `scripts/` 文件夹，双击 **`start.cmd`**：自动连接 SSH、检查数据库、启动本机后端和前端，并打开浏览器。双击同目录的 **`stop.cmd`** 停止本机项目服务，服务器共享数据库继续运行。

脚本根据自身位置定位目录，也可以从任意目录通过完整路径运行。已经运行的项目服务会被复用，不重复启动；无关进程占用端口时会报错，不结束无关进程。启动失败时只清理本次新启动的进程。停止入口会核对进程身份及创建时间，并停止本项目服务，包括之前手动启动的对应服务。

新电脑首次使用仍需安装前后端依赖、配置 `backend/.env` 并取得第 7 组 SSH 权限；没有可用公钥时，会弹出 SSH 窗口让你确认服务器指纹并输入服务器密码。新启动的前端使用真实接口模式；复用手动启动的前端时沿用原配置，需要切换模式时先停止再启动。脚本不保存 SSH 密码，也不运行迁移、初始化或重置数据库。凭据不完整时请按后端说明配置。日志与进程记录保存在被 Git 忽略的 `.dev.local/`。

`scripts/start.cmd`、`scripts/stop.cmd` 和当前的 `scripts/dev.py` 仅支持 Windows。macOS 使用下面的终端步骤；Windows 手动启动步骤见后续章节。

## macOS 启动（共享开发数据库）

### 首次准备

安装 Python 3.11+、Node.js（本项目已在 22 / 24 验证）和 npm 9+，并取得第 7 组服务器的 SSH 登录权限。在 macOS 的“终端”中确认 `python3 --version`、`node --version`、`npm --version` 和 `ssh -V` 能运行。连接共享库不需要在 Mac 上安装 MySQL 或 Docker。

下载项目后，先进入包含 `frontend/` 和 `backend/` 的项目根目录。以下命令都以项目根目录为起点；不要复制 Windows 的 `.venv` 或 `node_modules`，应在 Mac 上重新安装：

```bash
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -e '.[dev]'
cp -n .env.example .env
cd ..
npm --prefix frontend ci
scp -P 1021 group7@8.130.213.80:campus-club-mysql/etc/app.env backend/.env.shared
cp -n frontend/.env.development frontend/.env.development.local
```

`cp -n` 保留已有配置。首次 SSH 连接需要确认服务器指纹；未配置公钥登录时输入服务器密码。编辑 `backend/.env`：将 `DATABASE_URL` 替换为下载的 `backend/.env.shared` 中的值，确认连接地址为本机 `127.0.0.1:13307`、数据库为 `campus_club`。为自己的后端生成 `TOKEN_SECRET`，并将结果填入配置文件：

```bash
backend/.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

编辑 `frontend/.env.development.local`，设置：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8080
```

这些本地配置不提交 Git。共享数据库已由维护者初始化，组员启动时无需运行建库、迁移或演示数据初始化；表结构变更统一由维护者执行。详细权限和连接配置见 [共享数据库说明](./backend/SHARED_DATABASE.md)。

### 每次启动

打开三个终端窗口或标签页，每个都先进入项目根目录。

**终端 1：建立 SSH 隧道，并保持运行。** 这是在 Mac 本机执行的命令，不需要先进入服务器终端。命令连接后没有输出、持续等待是正常现象。

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:13307:127.0.0.1:13307 -p 1021 group7@8.130.213.80
```

**终端 2：启动本机后端。** 使用虚拟环境中的 Python，不需要另行激活环境。

```bash
cd backend
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

**终端 3：启动本机前端。** 依赖安装仅在首次使用或锁文件变更后执行，日常无需重复安装。

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

浏览器打开 `http://127.0.0.1:5173/`。接口文档地址为 `http://127.0.0.1:8080/docs`，连通性检查地址为 `http://127.0.0.1:8080/api/test/hello`，其响应的 `data.source` 应为 `server`。

结束使用时，先在前端和后端终端按 `Control+C`，再在隧道终端按 `Control+C`；服务器共享数据库继续运行。如果隧道提示端口已占用，先检查是否已有隧道运行。若服务器停机导致数据库不可用，由维护者按共享数据库说明恢复服务。若维护者改用 `14307`，隧道和 `DATABASE_URL` 的端口需同时调整。

只开发前端 mock 页面时，可保持 `VITE_USE_MOCK=true` 并只启动前端，无需后端或 SSH 隧道。本说明在 Windows 环境核对了命令与配置路径，尚未在真实 Mac 上实机验证。

## 启动前端

需要 Node.js 和 npm。首次安装依赖，在项目根目录执行：

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

之后启动只需进入 `frontend/` 并运行最后一条命令。页面地址是 `http://127.0.0.1:5173/`。

前端默认使用 mock。本机真实联调配置在 **`frontend/.env.development.local`**：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8080
```

该文件不提交 Git；改动后重启前端。完整页面状态、前端命令和开发说明见 [frontend/README.md](./frontend/README.md)。

## 启动后端和共享数据库连接

后端需要 Python 3.11+ 和 MySQL。安装、迁移、演示数据及本地测试步骤见 [backend/README.md](./backend/README.md)。

第 7 组开发时，服务器 MySQL 已启动，组员各自在本机建立 SSH 隧道并保持该终端运行：

```powershell
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:13307:127.0.0.1:13307 -p 1021 group7@8.130.213.80
```

在另一个终端，从项目根目录启动本机后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

再打开一个终端，按前面的命令进入 `frontend/` 启动前端。共享库凭据、服务器启动、备份和恢复步骤见 [共享数据库说明](./backend/SHARED_DATABASE.md)。开发测试继续使用每位组员独立的本地 MySQL 测试库，不清理共享开发库。

## 实现状态与协作

- 后端已实现 37 个核心接口：认证、个人中心、社团、活动、通知、连通性测试。
- 前端已实现登录注册、首页、社团广场、连通性页面；搜索仅有 mock 后端。详情页、个人中心、管理后台业务、通知和 AI 页面仍是占位。
- 邮件找回、真实搜索、场地物资预约、知识库与 AI 后端尚未实现。

共同接口契约见 [docs/api.md](./docs/api.md)，开发规则见 [CLAUDE.md](./CLAUDE.md)。小组成员从共同基线创建功能分支，检查并审查后合并；结构迁移由维护者统一执行。

所有 npm 命令在 `frontend/` 下执行，也可在项目根目录使用 `npm --prefix frontend run lint`、`npm --prefix frontend run type-check`、`npm --prefix frontend run build`。Git 操作仍在项目根目录执行。依赖、构建产物、本地密码配置及数据库备份都不提交。
