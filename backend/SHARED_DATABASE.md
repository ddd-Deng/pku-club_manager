# 第 7 组共享开发数据库

组员各自运行前后端，通过 SSH 隧道访问学校 DSW 中的同一套 MySQL。它是课程开发环境，DSW 停机时数据库也会停止。正式生产部署需要另行准备。

## 服务器与数据位置

- SSH：`group7@8.130.213.80`，端口 `1021`。
- MySQL：8.4.11，服务器内监听 `127.0.0.1:13307`；不直接开放公网端口。
- 安装、实时数据、日志与配置：`/home/group7/campus-club-mysql/`，目录权限为 700。
- 维护脚本：`/home/group7/campus-club-shared-mysql.py`，源文件为 `scripts/shared_mysql.py`。
- 业务库：`campus_club`。应用账号仅有该库的查询、增加、修改、删除权限；迁移账号有该库的结构修改权限。
- 缓存设置为 128 MiB，最大连接数 128。此配置不是进程内存或 CPU 的硬上限。

不使用 sudo、Docker 或系统服务，不修改其他组的数据库或资源。缺少的 libaio 在组内目录解压使用。所有组员共用 Linux 账号，因此组内账号文件不能作为成员之间的权限隔离。

## 每位组员连接

先取得第 7 组 SSH 登录权限。密码不要发进 Git 或聊天。按课程要求修改初始密码；公钥登录由组内管理。

在一个 PowerShell 窗口建立隧道，保持该窗口运行：

```powershell
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:13307:127.0.0.1:13307 -p 1021 group7@8.130.213.80
```

服务器停止后，需要先启动数据库：

```powershell
ssh -p 1021 group7@8.130.213.80 'python3 ~/campus-club-shared-mysql.py start'
```

下载应用连接配置到 `backend/` 的本地文件；它已被 Git 忽略：

```powershell
scp -P 1021 group7@8.130.213.80:campus-club-mysql/etc/app.env backend/.env.shared
```

在 `backend/.env` 中将 `DATABASE_URL` 替换为 `.env.shared` 中的值，保留自己生成的 `TOKEN_SECRET` 和本机 CORS 设置。不要在终端输出文件内容。前端根目录 `.env.development.local` 使用：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8080
```

分别启动本机后端与前端：

```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8080
```

```powershell
npm ci
npm run dev
```

`app.env` 只有应用数据库连接信息；请勿分发 `root.cnf`、`migration.env` 或备份密钥。各组员的登录 Token 与自己的后端密钥对应，切换后端或密钥后需要重新登录。

## 协作与迁移

共享库会即时反映所有组员的业务修改。由一名维护者运行 Alembic 迁移，使用 `migration.env` 的连接信息作为临时环境变量；应用账号没有建表或删表权限。不并发执行结构迁移，不对共享库运行数据重置。

`pytest` 继续使用每个人的本地 `campus_club_test`。测试夹具会删除该库的业务记录，不能改为共享开发库。未运行本地 MySQL 时，显式配置了测试库的测试会失败。

本机迁移资料存放在 `.shared-db.local/`，包含原业务库 SQL、记录数量、连接配置回退副本和备份恢复密钥，已整体忽略。原 Docker 数据卷继续保留。迁移后清除服务器中的旧登录会话，所有人重新登录；不重置账号密码。

新服务器的首次安装由维护者上传脚本并执行 `install`。安装器拒绝以 root 运行，并拒绝重新初始化已存在的数据目录。若 `13307` 已被占用，安装器选择 `14307`；此时组员的隧道目标和本地数据库 URL 均须统一使用配置中的端口。

## 加密备份与恢复

备份写入 `/mnt/data/group7/campus-club-backups/`，该路径属于 OSS 挂载。**OSS 只存加密 SQL 备份，不作为 MySQL 数据目录。**先压缩，再使用随机密钥与 OpenSSL AES-256-CBC/PBKDF2 加密，同时保存 SHA-256 校验和 HMAC-SHA256 认证文件。恢复前先校验和认证密文，拒绝损坏或未经认证的内容。保留最近 48 份成功备份，数据很少时可覆盖约两天的每小时快照。

恢复密钥在服务器 `campus-club-mysql/etc/backup.key`。维护者必须在实例之外保留副本；本机副本位于 `.shared-db.local/backup.key`。密钥丢失后无法解密备份。共享 OSS 目录的普通文件权限不保证各组隔离，因此备份不保存明文 SQL。

维护操作可从 SSH 执行：

```bash
python3 ~/campus-club-shared-mysql.py status
python3 ~/campus-club-shared-mysql.py counts
python3 ~/campus-club-shared-mysql.py backup
python3 ~/campus-club-shared-mysql.py start-backups
python3 ~/campus-club-shared-mysql.py stop
```

`start-backups` 启动普通用户的每小时备份进程；DSW 停机时该进程也会停止，`start` 会重新启动它。手动 `backup` 会立即产生一份备份。失败信息写入 `logs/backup.log`，MySQL 错误写入 `logs/mysql.log`。

恢复演练使用 `restore-test`，导入独立的 `campus_club_restore_group7` 临时库并打印记录数量，成功后删除该临时库。若临时库已经存在，拒绝覆盖：

```bash
python3 ~/campus-club-shared-mysql.py restore-test /mnt/data/group7/campus-club-backups/某份备份.sql.gz.enc
```

`restore` 只接受空业务库，拒绝覆盖已有表；`import` 同样拒绝覆盖。若 DSW 本地数据丢失，需要重新安装、从维护者电脑上传原来的 `backup.key`，再 `restore` 相应备份；重新生成的应用连接密码须重新分发。恢复后要重新登录。

DSW 的重启、自动停止及本地数据保存策略由学校配置。本次仅验证 MySQL 进程重启与备份恢复，不通过停止整个 DSW 实例进行实验，以免影响其他组。

## 2026-10-14 交付验证

- 本机业务库已导入共享库：5 个账号、4 条学籍、8 个社团、8 个活动，成员、公告、招新帖记录均保留；逐表数量一致，只有旧登录会话按要求清除。
- Alembic 版本为 `0001 (head)`；5 个迁移账号均通过真实 HTTP 登录验证。两个独立 HTTP 客户端完成草稿创建、读取、删除，临时记录与测试登录会话已清理。
- MySQL 进程重启后数据仍在；带 HMAC 认证的加密备份恢复到独立临时库成功。每小时备份进程已启动，首个自动周期尚未作为验收项观察；手动备份已验证。
- 后端 Ruff 检查、格式检查通过，19 项 pytest 测试通过，包含独立本机 MySQL 测试及共享数据保护测试。只有现有 TestClient 依赖弃用提示；共享开发库未被测试清理。
- 前端 lint、类型检查、构建通过；构建保留现有大包提示。本机前后端均返回 HTTP 200，后端已指向共享库。
- 一次服务器采样：MySQL RSS 约 449 MiB，CPU 进程统计约 0.8%；数据目录约 169 MiB，程序目录约 405 MiB。备份进程另约 22 MiB。它们是观察值，不是硬限额或负载测试结果。
- 尚需组员验收：第二台电脑从不同网络连接并联调。未验证整个 DSW 实例停止后的存储保留；发生本地数据丢失时按备份流程恢复。
