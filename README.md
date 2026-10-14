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
scripts/dev.py     # Windows 本机服务启动与停止逻辑
start.cmd          # 双击启动
stop.cmd           # 双击停止
CLAUDE.md          # 项目开发规则
.editorconfig      # 前后端共同的编辑器规则
.gitignore         # 全仓库忽略规则
```

前端源码使用标准的 `frontend/src/` 结构；入口、依赖、锁文件、环境配置和构建产物均位于 `frontend/`。源码迁移不改变接口地址或用户权限。

## Windows 一键启动

这台电脑已安装依赖并配置共享数据库。日常使用直接双击项目根目录的 **`start.cmd`**：自动连接 SSH、检查数据库、启动本机后端和前端，并打开浏览器。双击 **`stop.cmd`** 停止本机项目服务，服务器共享数据库继续运行。

脚本根据自身位置定位目录，也可以从任意目录通过完整路径运行。已经运行的项目服务会被复用，不重复启动；无关进程占用端口时会报错，不结束无关进程。启动失败时只清理本次新启动的进程。停止入口会核对进程身份及创建时间，并停止本项目服务，包括之前手动启动的对应服务。

新电脑首次使用仍需安装前后端依赖、配置 `backend/.env` 并取得第 7 组 SSH 权限；没有可用公钥时，会弹出 SSH 窗口让你确认服务器指纹并输入服务器密码。新启动的前端使用真实接口模式；复用手动启动的前端时沿用原配置，需要切换模式时先停止再启动。脚本不保存 SSH 密码，也不运行迁移、初始化或重置数据库。凭据不完整时请按后端说明配置。日志与进程记录保存在被 Git 忽略的 `.dev.local/`。

以下分步命令适合单独开发、排查问题或非 Windows 系统。

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
