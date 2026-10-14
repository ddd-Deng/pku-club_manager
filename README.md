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

## 启动前须知

以下两套步骤均连接第 7 组服务器上的共享开发数据库：前后端运行在自己的电脑上，通过 SSH 隧道访问 MySQL。本机不需要安装 MySQL 或 Docker。共享库已由维护者建表并初始化，组员首次使用也无需重复执行建库、迁移或演示数据初始化。

先下载或克隆本仓库的 `main` 分支，并进入包含 `frontend/`、`backend/` 和 `scripts/` 的项目根目录。**下面每个独立命令块、每个新终端均以项目根目录为起点**；命令块内部的 `cd` 会继续改变当前目录。前后端依赖应在各自电脑重新安装，不复制其他电脑的 `.venv` 或 `node_modules`。

按操作系统选择：[Windows 启动](#windows-启动共享开发数据库) / [macOS 启动](#macos-启动共享开发数据库)。两者均按“首次准备 → 每次启动 → 停止”说明。配置文件只保存在本机，不提交 Git；共享库权限、迁移、备份和服务器恢复见 [共享数据库说明](./backend/SHARED_DATABASE.md)。

## Windows 启动（共享开发数据库）

### 首次准备

**1. 安装并检查运行环境。** 安装 Python 3.11+、Node.js（本项目已在 22 / 24 验证）、npm 9+ 和 Windows OpenSSH 客户端，并取得第 7 组 SSH 登录权限。安装后重新打开 PowerShell，在项目根目录检查：

```powershell
python --version
node --version
npm.cmd --version
ssh -V
```

如果命令不存在，先完成对应软件安装及 PATH 配置；确认 `python` 指向 3.11 或更新版本。下面使用 `npm.cmd` 调用 Windows 的 npm 入口，无需激活 Python 虚拟环境。

**2. 安装前后端依赖，并创建本地配置。** 在 PowerShell 中从项目根目录执行：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
cd ..
npm.cmd --prefix frontend ci
scp -P 1021 group7@8.130.213.80:campus-club-mysql/etc/app.env backend/.env.shared
if (-not (Test-Path frontend/.env.development.local)) {
  Copy-Item frontend/.env.development frontend/.env.development.local
}
```

复制模板时会保留已有配置。首次连接服务器时确认服务器指纹；未配置公钥登录时输入服务器密码。下载的 `backend/.env.shared` 包含应用数据库连接信息，不包含 SSH 密码。

**3. 填写后端配置。** 用编辑器打开 `backend/.env`，将 `DATABASE_URL` 完整替换为 `backend/.env.shared` 中的值。确认地址为本机 `127.0.0.1:13307`、数据库名为 `campus_club`；模板中的 `3306` 和 `CHANGE_ME` 不能直接用于连接共享库。生成自己的 Token 密钥：

```powershell
.\backend\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

将输出填入 `backend/.env` 的 `TOKEN_SECRET`，替换占位值，保存文件。保留模板中的本机 CORS 配置即可。`backend/.env` 不会随 Git 下载，所以每台新电脑都要完成此步骤。

**4. 切换前端到真实接口。** 编辑 `frontend/.env.development.local`，设置并保存：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8080
```

首次准备到此完成。日常使用直接按下一节启动；依赖文件变化时再安装相应依赖。

### 每次启动

**一键启动：** 进入项目的 `scripts/` 文件夹，双击 **`start.cmd`**；也可以从项目根目录的 PowerShell 执行：

```powershell
.\scripts\start.cmd
```

脚本自动建立 SSH 隧道、检查数据库、启动本机后端和前端，并打开浏览器。使用时需要联网；没有可用公钥时会打开 SSH 窗口，让你输入服务器密码，并保持窗口运行。已有项目服务会被复用；前端入口和页面模块都能加载才算启动成功，模块加载异常时会自动重启本项目的前端。启动时显式指定前端目录与 Vite 配置。新启动的前端使用真实接口；复用手动启动的前端时沿用其原配置，切换模式后应重启。

**手动启动：** 若需要分别开发或排查问题，可以使用以下方式替代一键启动。打开三个本机 PowerShell 窗口，每个都从项目根目录开始。

终端 1：建立 SSH 隧道并保持运行。直接在本机执行，不必先登录到服务器终端；连接后没有输出、持续等待是正常现象。

```powershell
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:13307:127.0.0.1:13307 -p 1021 group7@8.130.213.80
```

终端 2：启动后端。

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

终端 3：启动前端。

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

### 停止

一键启动后，双击 **`scripts/stop.cmd`**，或从项目根目录执行：

```powershell
.\scripts\stop.cmd
```

停止入口核对进程身份和创建时间，结束本项目的前端、后端及 SSH 隧道，包括之前手动启动的对应服务；服务器共享数据库继续运行。无关进程占用端口时，启动入口会报错，不会结束它。启动失败只清理本次新启动的进程。日志和进程记录位于被 Git 忽略的 `.dev.local/`。

如果采用三个终端手动启动，也可以先在前端、后端终端按 `Ctrl+C`，再在 SSH 隧道终端按 `Ctrl+C`。

## macOS 启动（共享开发数据库）

### 首次准备

**1. 安装并检查运行环境。** 安装 Python 3.11+、Node.js（本项目已在 22 / 24 验证）和 npm 9+，并取得第 7 组 SSH 登录权限。在 macOS 的“终端”中，从项目根目录检查：

```bash
python3 --version
node --version
npm --version
ssh -V
```

**2. 安装前后端依赖，并创建本地配置。** 从项目根目录执行：

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

`cp -n` 保留已有配置。首次连接服务器时确认服务器指纹；未配置公钥登录时输入服务器密码。下载的 `backend/.env.shared` 包含应用数据库连接信息，不包含 SSH 密码。

**3. 填写后端配置。** 编辑 `backend/.env`，将 `DATABASE_URL` 完整替换为 `backend/.env.shared` 中的值。确认地址为本机 `127.0.0.1:13307`、数据库名为 `campus_club`；模板中的 `3306` 和 `CHANGE_ME` 不能直接用于连接共享库。生成自己的 Token 密钥：

```bash
backend/.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

将输出填入 `backend/.env` 的 `TOKEN_SECRET`，替换占位值，保存文件。保留模板中的本机 CORS 配置即可。`backend/.env` 不会随 Git 下载，所以每台新电脑都要完成此步骤。

**4. 切换前端到真实接口。** 编辑 `frontend/.env.development.local`，设置并保存：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8080
```

首次准备到此完成。日常使用直接按下一节启动；依赖文件变化时再安装相应依赖。

### 每次启动

`scripts/start.cmd`、`scripts/stop.cmd` 和当前的 `scripts/dev.py` 仅支持 Windows。Mac 使用下面的三个本机终端窗口或标签页，每个都从项目根目录开始。

终端 1：建立 SSH 隧道并保持运行。直接在 Mac 本机执行，不必先登录到服务器终端；连接后没有输出、持续等待是正常现象。

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:13307:127.0.0.1:13307 -p 1021 group7@8.130.213.80
```

终端 2：启动后端。使用虚拟环境中的 Python，不需要另行激活环境。

```bash
cd backend
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

终端 3：启动前端。

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

### 停止

先在前端、后端终端按 `Control+C`，再在 SSH 隧道终端按 `Control+C`；服务器共享数据库继续运行。macOS 命令已核对语法和配置路径，尚未在真实 Mac 上实机验证。

## 访问与连通性检查

两个系统启动后使用相同地址：

- 前端页面：`http://127.0.0.1:5173/`。
- 后端接口文档：`http://127.0.0.1:8080/docs`。
- 连通性接口：`http://127.0.0.1:8080/api/test/hello`，响应的 `data.source` 应为 `server`。也可在前端 `/test/hello` 页面检查真实接口连接。

SSH 隧道提示端口已占用时，先检查是否已有隧道运行。若数据库不可用，确认隧道、本地配置以及服务器状态；服务器停机后由维护者按共享数据库说明恢复。若维护者改用 `14307`，隧道和 `DATABASE_URL` 的端口需同时调整。

切换到目录结构不同的 Git 分支前，先停止本机服务，切换完成后重新启动。若页面出现 `Failed to resolve import` 或 Vue 插件错误，在 Windows 上重新运行 `scripts/start.cmd` 会检查模块并恢复异常前端；macOS 手动停止并重启前端，再刷新浏览器。

## 仅开发前端 mock 页面

前端默认使用 mock。如果只开发前端模拟页面，在 `frontend/.env.development.local` 设置 `VITE_USE_MOCK=true`，然后只执行相应系统的前端手动启动命令，无需后端或 SSH 隧道。Windows 一键入口会为新启动的前端设置真实接口，因此 mock 开发使用手动方式。

前端本地配置改动后需重启前端。完整页面状态和开发命令见 [frontend/README.md](./frontend/README.md)。独立本地数据库、迁移和自动化测试步骤见 [backend/README.md](./backend/README.md)；测试使用每位组员独立的 `campus_club_test`，不清理共享开发库。

## 实现状态与协作

- 后端已实现 37 个核心接口：认证、个人中心、社团、活动、通知、连通性测试。
- 前端已实现登录注册、首页、社团广场、连通性页面；搜索仅有 mock 后端。详情页、个人中心、管理后台业务、通知和 AI 页面仍是占位。
- 邮件找回、真实搜索、场地物资预约、知识库与 AI 后端尚未实现。

共同接口契约见 [docs/api.md](./docs/api.md)，开发规则见 [CLAUDE.md](./CLAUDE.md)。小组成员从共同基线创建功能分支，检查并审查后合并；结构迁移由维护者统一执行。

所有 npm 命令在 `frontend/` 下执行，也可在项目根目录使用 `npm --prefix frontend run lint`、`npm --prefix frontend run type-check`、`npm --prefix frontend run build`。Git 操作仍在项目根目录执行。依赖、构建产物、本地密码配置及数据库备份都不提交。
