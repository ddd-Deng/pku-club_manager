# CLAUDE.md — AI 协作开发规则（前端）

本文件是本项目给 AI（Claude / 其他代码助手）的开发约束，**每次开发都必须遵守**。
项目：校园社团管理系统（基础 V1.0）前端 · 阶段一 Demo · 只写前端，不写后端 / 数据库 / AI 模型代码。

## 0. 硬约束

1. 技术栈固定：Vue 3 `<script setup>` + Vite + TypeScript + Vue Router + Pinia + Element Plus + Axios + ESLint + Prettier。不得擅自更换、不得引入 UI 框架替代品或状态管理替代品。
2. 用户已授权在 `backend/` 使用 Python + FastAPI + MySQL 实现核心后端、数据库迁移与测试；前端继续遵守现有技术栈。AI、场地预约、搜索后端、邮件找回不在本阶段范围。接口变更同步 `docs/api.md`、类型和 mock。
3. 页面结构、页面名称、组件划分、跳转关系以 `docs/ui/xmind-structure.jpeg` 为准；UI 稿文字存在乱码，只参考布局 / 配色 / 风格（蓝白、卡片、圆角）。
4. 新增依赖前必须说明理由并征得确认，优先使用已有依赖。
5. 交付前必须通过：`npm run lint`（零报错）、`npm run type-check`（零报错）、`npm run dev` 可启动、涉及页面手工点检。

## 1. 目录与命名

- 组件文件与组件名 PascalCase：`ClubCard.vue`、`StateBlock.vue`。
- 目录与路由 kebab-case：`src/views/club/`、`/clubs/:id`、`/test/hello`。
- 函数、变量 camelCase：`loadClubs()`、`errorMessage`。
- 类型定义放 `src/types/<domain>.ts`，与 `docs/api.md` 字段名严格一致；`src/types/index.ts` 统一导出。
- 视图按页面分文件夹，一页一目录：`src/views/<page>/XxxView.vue`。
- 样式类名 BEM 风格前缀化：`.club-card__title`；公共类以 `app-` 开头：`.app-container`、`.app-section-title`。

## 2. 数据层（最重要）

- 页面 / 组件**只能**调用 `src/api/<module>.ts` 导出的函数，禁止直接 import axios、禁止 import mock 数据、禁止在页面里写 URL 字符串。
- 所有请求走 `src/api/request.ts` 的 `request<T>()`：自动注入 `Authorization: Bearer <token>`、自动校验 `{ code, message, data }`、统一弹出错误提示、401 自动清登录态并跳登录页。
- mock 与真实接口必须返回**完全一致**的信封结构；`VITE_USE_MOCK` 是唯一开关，切换时页面代码零改动。
- 列表接口统一返回分页结构 `{ list, total, page, pageSize }`；查询参数统一 `page`、`pageSize`、`keyword`。
- 新增接口的固定四步：① 在 `docs/api.md` 写契约（method / path / 参数 / 响应示例 / 所需角色）② 在 `src/types` 加类型 ③ 在 `src/api` 加方法 ④ 在 `src/mock/handlers` 加 mock handler。缺任何一步都算未完成。
- mock handler 用 `mockRoute('GET', '/api/xxx/:id', handler)` 注册，需带 `/api` 前缀；业务失败 `throw new MockError(code, message)`；权限用 `requireAuth` / `requireRole` / `requireClubOwner`；分页用 `paginate()`。

## 3. 页面实现规范

- 每个数据页面必须处理三态，统一使用 `StateBlock`：`loading`（骨架屏）、`error`（失败 + 重新加载按钮）、`empty`（空数据）。
- 页面状态获取模式固定：`loading` / `errorMessage` / 数据 ref + `async function loadData()` + `onMounted(loadData)`，`catch` 里只记录 `error.message`，提示交给请求层。
- 路由跳转用 `router.push`，参数走 `query` 或 `params`，禁止拼接手写 `<a href>`。
- 布局：前台页面用 `FrontLayout`（蓝色顶部导航），后台用 `AdminLayout`（左侧边栏 + 标签分区）。新页面挂到对应布局的 children 下。
- 权限：路由 meta 用 `requiresAuth`（需登录）、`roles: ['student' | 'clubAdmin' | 'admin']`（角色限制）、`publicOnly`（登录页）。

## 4. 样式与主题

- 颜色 / 圆角 / 阴影 / 尺寸只用 `src/styles/variables.css` 的 CSS 变量（`--app-color-primary` 等），主色 `#2E7CF0`。
- 覆盖 Element Plus 主题通过变量映射（`--el-color-primary: var(--app-color-primary)`），写在 `variables.css` / `styles/index.css`，不要用 `!important` 硬盖。
- 组件样式一律 `<style scoped>`，禁止全局污染第三方类名（确需覆盖写在 `styles/index.css` 并注释原因）。
- 栅格：首页社团卡片 4 列、活动 2 列、广场 4 列，`max-width: 1200px` 居中，需带 `@media (max-width: 992px)` 降级。

## 5. TypeScript 与 ESLint

- `strict: true`，禁止 `any`（ESLint `@typescript-eslint/no-explicit-any`）；不确定类型用 `unknown` + 收窄。
- 开启 `verbatimModuleSyntax`：类型导入必须 `import type { X } from '...'`。
- 开启 `noUnusedLocals` / `noUnusedParameters`：未使用的导入、变量、参数必须删除（mock handler 用不到的 `ctx` 直接省略参数）。
- ESLint 9 flat config（`eslint.config.js`）：`js.recommended` + `typescript-eslint.recommended` + `eslint-plugin-vue` flat/recommended + `eslint-config-prettier`。格式化交给 Prettier，不要把 Prettier 塞进 lint 报错。
- Vue SFC 顺序：`<script setup>` → `<template>` → `<style scoped>`；`defineProps` 用类型声明 + `withDefaults`；`defineEmits` 用类型声明；双向绑定优先 `defineModel`。

## 6. 提交与协作

- commit 前缀：`feat` / `fix` / `docs` / `refactor` / `style`，中文描述，例：`feat: 社团广场增加分类筛选与分页`。
- 一次提交只做一件事；接口契约变更（`docs/api.md`）必须与前端代码同一次提交。
- 不提交 `node_modules/`、`dist/`、`.env.*.local`（见 `.gitignore`）。
- 改动前先读 `README.md` 的"页面与路由"表和 `docs/api.md`，避免重复造轮子或偏离契约。

## 7. 禁止事项

- 禁止在页面里写死假数据（假数据只存在于 `src/mock/db.ts`）。
- 禁止绕过 `request.ts` 直接发请求或自行处理 token。
- 禁止修改统一响应结构、分页结构、角色枚举值。
- 禁止把占位页面伪装成已实现（占位统一用 `PagePlaceholder` 并注明）。
- 禁止为了通过 lint 而关闭规则或加 `eslint-disable`（确有必要需在 PR 说明原因）。
