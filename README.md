# 校园社团管理系统（基础 V1.0）

大学软件工程课程 8 人小组项目。现有 Vue 前端与 `backend/` 内的 FastAPI 核心后端；前端默认使用本地 mock，也可切换真实接口。后端目前覆盖认证、个人中心、社团、活动、通知及连通性测试；其他业务后端仍待实现。

后端安装、MySQL 迁移、演示数据及联调步骤见 [backend/README.md](./backend/README.md)。
本机开发可用 Docker Desktop 启动项目专用 MySQL；业务数据保存在本机命名卷中。当前电脑若有 `.env.development.local`，其设置会覆盖下文所述的默认 mock 模式。
第 7 组使用学校服务器共享开发数据的连接与维护步骤见 [共享数据库说明](./backend/SHARED_DATABASE.md)。

## 技术栈

Vue 3（`<script setup>`）+ Vite + TypeScript + Vue Router + Pinia + Element Plus + Axios + ESLint + Prettier

## 快速开始

环境要求：Node.js >= 18（本项目在 Node 22 / 24 验证通过），npm >= 9。

```bash
npm install      # 安装依赖（国内网络可加 --registry=https://registry.npmmirror.com）
npm run dev      # 启动开发服务器，默认 http://localhost:5173
```

其他命令：

| 命令                 | 说明                                      |
| -------------------- | ----------------------------------------- |
| `npm run dev`        | 启动开发服务器                            |
| `npm run build`      | 类型检查 + 生产构建，产物在 `dist/`       |
| `npm run preview`    | 预览构建产物                              |
| `npm run type-check` | 仅做 TypeScript / 模板类型检查（vue-tsc） |
| `npm run lint`       | ESLint 检查（提交前必须无报错）           |
| `npm run lint:fix`   | ESLint 自动修复                           |
| `npm run format`     | Prettier 格式化                           |

## mock 与真实接口一键切换

环境变量 `VITE_USE_MOCK` 控制数据来源，**页面代码零改动**：

| 文件               | VITE_USE_MOCK | 效果                                                                                |
| ------------------ | ------------- | ----------------------------------------------------------------------------------- |
| `.env.development` | `true`        | 走 `src/mock/`，模拟 200~500ms 延迟，返回与真实后端一致的 `{ code, message, data }` |
| `.env.production`  | `false`       | 走 axios 请求 `VITE_API_BASE_URL`                                                   |

切换方式：

1. 直接把 `.env.development` 里的 `VITE_USE_MOCK` 改成 `false`（改完需重启 dev server）。
2. 或新建 `.env.development.local` 覆盖，不影响仓库文件：
   ```bash
   echo "VITE_USE_MOCK=false" > .env.development.local
   echo "VITE_API_BASE_URL=http://localhost:8080" >> .env.development.local
   ```

真实模式下 `VITE_API_BASE_URL` 为后端服务地址，接口路径统一带 `/api` 前缀（例：`http://localhost:8080/api/test/hello`）。
若前后端不同源，请后端开启 CORS，或在 `vite.config.ts` 的 `server.proxy` 增加代理。

### mock 演示账号

`.env.development` 开启 mock 时，登录页底部提供一键填充按钮：

| 角色           | 账号（学号） | 密码     |
| -------------- | ------------ | -------- |
| 学生 student   | `2024001`    | `123456` |
| 社长 clubAdmin | `2021002`    | `123456` |
| 管理员 admin   | `admin`      | `123456` |

## 目录说明

```
├── index.html
├── vite.config.ts          # 别名 @ -> src，dev 端口
├── tsconfig.json
├── eslint.config.js        # ESLint 9 flat config
├── .prettierrc.json / .editorconfig
├── .env.development / .env.production
├── docs/
│   ├── api.md              # 前后端接口契约（权威文档）
│   ├── ai-workflow-frontend.md  # AI 辅助开发流程
│   └── ui/                 # UI 稿与 Xmind 页面结构图
└── src/
    ├── main.ts / App.vue
    ├── api/                # 按模块分文件的接口层，页面只允许调用这里
    │   └── request.ts      # axios 封装：baseURL / token 注入 / 统一错误 / mock 分流
    ├── types/              # 业务类型定义，与 docs/api.md 字段一一对应
    ├── mock/               # 本地 mock：registry(路由匹配) + db(假数据) + handlers
    ├── router/             # 懒加载路由 + 登录/角色守卫
    ├── stores/             # Pinia store（user 登录态）
    ├── layouts/            # FrontLayout(顶部导航) / AdminLayout(后台侧边栏)
    ├── components/         # 通用组件：ClubCard / ActivityCard / SearchBar / CategoryFilter / StateBlock / PagePlaceholder
    ├── views/              # 按页面分文件夹，一页面一目录
    ├── styles/             # CSS 变量主题 + Element Plus 覆盖 + 全局样式
    └── utils/              # storage / format / constants
```

## 页面与路由

页面结构以 `docs/ui/xmind-structure.jpeg` 为准（8 个网页 + 活动详情页）。

| 路由              | 页面                         | 布局     | 权限                 | 第一阶段状态                                       |
| ----------------- | ---------------------------- | -------- | -------------------- | -------------------------------------------------- |
| `/`               | 系统首页                     | 顶部导航 | 公开                 | ✅ 完整实现（社团推荐 + 近期活动 + 搜索）          |
| `/clubs`          | 社团广场                     | 顶部导航 | 公开                 | ✅ 完整实现（搜索 + 分类筛选 + 分页 + 社团卡片）   |
| `/login`          | 登录 & 注册                  | 顶部导航 | 公开（已登录跳首页） | ✅ mock 与真实后端均支持登录 / 学籍白名单注册       |
| `/test/hello`     | 接口连通性测试               | 顶部导航 | 公开                 | ✅ 完整实现（hello world + `GET /api/test/hello`） |
| `/clubs/:id`      | 社团详情                     | 顶部导航 | 公开                 | ⏳ 占位                                            |
| `/activities/:id` | 活动详情                     | 顶部导航 | 公开                 | ⏳ 占位                                            |
| `/admin`          | 社团管理后台（6 个标签分区） | 侧边栏   | clubAdmin / admin    | ⏳ 占位                                            |
| `/profile`        | 个人中心                     | 顶部导航 | 登录                 | ⏳ 占位                                            |
| `/notifications`  | 消息与通知                   | 顶部导航 | 登录                 | ⏳ 占位                                            |
| `/ai`             | AI 知识库问答                | 顶部导航 | 登录                 | ⏳ 占位                                            |
| `/search`         | 搜索结果                     | 顶部导航 | 公开                 | ✅ mock 模式可搜索、筛选、分页与管理搜索历史；真实搜索后端待实现 |

守卫规则：未登录访问受保护页 → 跳 `/login?redirect=原路径`；角色不符 → 提示并回首页；请求层收到 401 → 清 token 并跳登录。

## 验证 Demo

```bash
npm install && npm run dev
```

1. 打开 `http://localhost:5173/` → 首页展示社团推荐卡片与近期活动（数据来自 mock）。
2. 打开 `http://localhost:5173/clubs` → 搜索"摄影"、切换分类"文化艺术"，可见筛选与分页生效。
3. 打开 `http://localhost:5173/test/hello` → 页面显示 `hello world`，并展示 `GET /api/test/hello` 返回的 JSON。
4. 未登录访问 `http://localhost:5173/admin` → 跳转登录页；用 `2024001` 登录后再访问 → 提示无权限并回首页；用 `2021002` 或 `admin` 登录 → 进入侧边栏后台。
5. 启动真实后端，把 `VITE_USE_MOCK` 改为 `false` 并重启前端 → 连通性页面显示 `source: "server"`，首页与社团广场读取数据库记录；后端停机时显示失败态。
6. `npm run lint` 与 `npm run type-check` 均无报错。

## 开发约定

- 组件文件与组件名 **PascalCase**（`ClubCard.vue`）；目录与路由 **kebab-case**（`views/club/`、`/clubs/:id`）；函数与变量 **camelCase**。
- 页面**不得**直接 import axios 或 mock，只能调用 `src/api/*` 模块；新接口先在 `docs/api.md` 定义契约，再在 `src/types` 补类型、`src/api` 补方法、`src/mock/handlers` 补 mock。
- 列表页统一使用 `StateBlock` 处理加载中 / 空数据 / 失败三态，失败态需提供"重新加载"。
- 列表接口统一分页结构 `{ list, total, page, pageSize }`；响应统一 `{ code, message, data }`，`code === 0` 为成功。
- 颜色、圆角、阴影只使用 `src/styles/variables.css` 中的 CSS 变量，不散落硬编码色值。
- commit 前缀：`feat` / `fix` / `docs` / `refactor` / `style`，例：`feat: 实现社团广场分类筛选`。

详细规则见 [CLAUDE.md](./CLAUDE.md)，接口契约见 [docs/api.md](./docs/api.md)，AI 协作流程见 [docs/ai-workflow-frontend.md](./docs/ai-workflow-frontend.md)。

## 后续迭代建议

1. 按 `docs/api.md` 契约补齐占位页面（社团详情 → 活动详情 → 个人中心 → 管理后台 → 消息 → AI 问答 → 搜索）。
2. 后端联调：把对应模块的 mock handler 替换为真实接口验证，保留 mock 以便离线演示。
3. 补充上传（知识库文档）与富文本（社团简介）能力，以及图片资源改为对象存储 URL。
