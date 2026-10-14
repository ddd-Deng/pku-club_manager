# 管理员账号管理与社长交接交付说明

## 本次交付

后端核心接口从 37 个增加到 42 个，新增五个管理员接口，契约见 [api.md 第 12 章](./api.md#12-管理员账号与社长管理)。前端和 mock 已同步实现三个页面：

| 页面 | 入口 | 权限与用途 |
| --- | --- | --- |
| `/admin/accounts` | 管理后台 → 学生账号管理 | 管理员查询、筛选、分页、修改姓名邮箱、启禁用学生或社长账号 |
| `/admin/presidents` | 管理后台 → 任命／更换社长 | 管理员选择有效学生，确认交接双方并任命；无社长时首次任命 |
| `/account/password` | 前台用户菜单或后台顶部 → 修改密码 | 所有登录用户验证原密码后修改本人密码，成功后重新登录 |

一人最多管理一个社团。新社长尚未入社时自动添加成员，有待审核申请时同步通过并通知；旧社长成为普通学生并保留普通成员身份。交接撤销双方会话。禁用在任社长前必须交接，禁用保留业务历史，重新启用不恢复旧 Token。管理员账号受保护，学生与社长不能进入管理员页面或调用管理员接口。

管理员不负责重置密码、创建删除账号或维护学籍白名单。原有六个社团管理分区、社团详情、活动详情、个人中心、消息与 AI 页面仍为占位；相关后端接口已实现的状态与页面实现状态分开记录。

## 数据库升级记录

2026-10-14，在独立 `campus_club_test` 验证迁移及业务后，已备份并使用现有迁移账号将共享 `campus_club` 升级到 `0002`，随后重启本机后端。

服务器上的加密备份路径为：

```text
/mnt/data/group7/campus-club-backups/campus_club_20261014T115504020961Z.sql.gz.enc
```

迁移前后核对全部项目表的记录数，以及用户身份、角色归属与成员记录，均未改变；五个现有账号默认启用。没有对共享账号执行任命、禁用或改密。页面登录验证会产生正常登录会话。

其他组员更新代码后重启后端即可使用现有共享库，不需要再初始化数据。独立数据库维护者应先备份，再以迁移账号执行 `alembic upgrade head`。迁移检查社长归属与所有者成员关系；发现不一致会中止，应先核实修复，不能自动清理。后端启动不会自动建表或重置业务数据。

## 验收结果（2026-10-14）

| 检查 | 结果与范围 |
| --- | --- |
| 后端 Ruff 检查及格式检查 | 通过 |
| 后端 pytest | 41 项通过、无跳过；使用独立 MySQL `campus_club_test`，没有以 SQLite 替代 |
| 接口契约 | 验证核心接口数量为 42，统一响应、权限及参数校验通过 |
| 管理员 mock 测试 | 4 项通过；账号保护、空 Token、启禁用、交接、申请通知、改密及会话撤销 |
| 前端 ESLint、类型检查、生产构建 | 通过 |
| Edge 自动化浏览器：共享库 | 管理员列表、资料弹窗、候选人弹窗、本人改密必填校验；学生与社长直接访问管理员地址被拒绝；空数据、网络失败与重新加载通过 |
| Edge 自动化浏览器：独立 MySQL | 真实前后端完成分页、禁用→启用、姓名编辑、交接→新社长重新登录、管理员入口隐藏、本人改密→新密码登录 |
| Edge 自动化浏览器：mock | 完成启禁用、姓名编辑、交接、新社长菜单检查、本人改密和重新登录 |
| 页面视觉检查 | 检查账号及社长列表截图，布局与内容正常；上述浏览器流程无未捕获页面异常 |

浏览器验证使用独立的无头 Edge 会话，没有操作已有浏览器窗口。真实写操作通过临时后端连接独立测试库，未修改共享业务账号。临时测试前后端完成后自动停止。

MySQL 测试覆盖首次任命、非成员自动入社、已有成员晋升、旧社长降级、待审核申请及通知、历史记录保留、跨社团权限更新、管理员账号保护、重复邮箱与参数格式、禁用和启用后的旧 Token 失效、本人改密。并发覆盖同一候选人被两个社团任命、同一社团交接冲突、任命与禁用竞争、登录与禁用竞争；验证失败事务无部分修改，以及迁移保留记录、约束生效和不一致数据中止。

现有依赖产生一条 Starlette/HTTPX 弃用警告，前端构建仍提示部分资源包超过 500 kB；两者不影响本次检查通过。macOS 启动步骤已有文档，本次没有进行 Mac 实机验收。

## 复现自动化检查

后端测试必须显式配置 `backend/.env.test` 中的 `TEST_DATABASE_URL`，驱动为 `mysql+pymysql`，数据库名必须是 `campus_club_test`。测试会清理该测试库的项目表；请使用自己的测试实例，不能与他人同时运行，也不能指向共享 `campus_club`。连接信息和密码不提交 Git。

Windows 从项目根目录运行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q
cd ..
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run type-check
npm.cmd --prefix frontend run test:admin-mock
npm.cmd --prefix frontend run build
```

macOS 从项目根目录运行相同检查：

```bash
cd backend
./.venv/bin/python -m ruff check .
./.venv/bin/python -m ruff format --check .
./.venv/bin/python -m pytest -q
cd ..
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test:admin-mock
npm --prefix frontend run build
```

浏览器人工复核可按上表顺序进行。共享库仅查询和打开后取消弹窗；启禁用、任命和改密请在 mock 或独立测试库的演示账号上验证。mock 设置 `VITE_USE_MOCK=true` 后重启前端；刷新页面会重新加载演示数据。真实测试模式设置 `VITE_USE_MOCK=false` 并将前端地址指向使用测试库的后端，仍通过统一请求层调用接口。

## Git 交付

从最新 `main` 创建 `codex/admin-management`，按接口与迁移、前端页面与 mock 测试、后端测试与文档分阶段提交。完成验收后，按用户要求快进合并至本地 `main`，保留原有三个功能提交；未推送 GitHub。后续本机开发默认直接在 `main` 上进行，除非用户另有分支要求。使用说明分别更新了根目录 README、前后端 README、接口契约与项目规则。
