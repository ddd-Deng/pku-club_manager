# 第二阶段设计文档：社团信息查阅 与 社团管理（前端部分）

> 作者：前端组（2 人）｜日期：2026-11-10｜分支：`feature/phase2-core-frontend`
>
> 本文档是第二阶段"先分析设计、再用设计引导 Agent 实现"流程的产物。
> §1–§4 为面向对象分析（OOA），§5 为面向对象设计（OOD），§6 为设计模式应用，
> §7 为"设计引导 Agent"的约束清单，§8 为与"无设计直出"版本的对照分析。

---

## 1. 需求概述（需求变更分析）

第二阶段在阶段一（框架 + 首页/广场/登录 + 连通性页面）基础上，新增两个核心功能：

| 编号 | 核心功能 | 使用者 | 范围 |
| ---- | -------- | ------ | ---- |
| F1 | 查阅社团信息 | 学生（个人） | 社团详情、活动详情、活动报名、入社申请 |
| F2 | 管理社团 | 社长（clubAdmin） | 社团资料编辑、活动管理、招新帖与入社申请审核、成员权限管理 |

明确**不做**的（避免范围蔓延，写进 backlog 的 Notes）：场地物资预约、知识库上传、AI 问答、消息通知页——属其他阶段或其他组接口，本阶段保留占位。

## 2. 用况图（Use Case）

### 2.1 F1 查阅社团信息

```plantuml
@startuml
left to right direction
actor "游客" as Guest
actor "学生" as Student

rectangle "查阅社团信息" {
  usecase "浏览社团列表" as UC1
  usecase "查看社团详情" as UC2
  usecase "查看社团公告" as UC3
  usecase "查看近期活动" as UC4
  usecase "查看活动详情" as UC5
  usecase "报名 / 取消报名活动" as UC6
  usecase "提交入社申请" as UC7
}
Guest --> UC1
Guest --> UC2
Student --> UC1
Student --> UC2
Student --> UC5
Student --> UC6
Student --> UC7
UC2 ..> UC3 : <<include>>
UC2 ..> UC4 : <<include>>
UC6 ..> UC5 : <<extend>>
UC7 ..> UC2 : <<extend>>
@enduml
```

说明：游客可浏览；报名与入社申请必须登录（学生角色），未登录时系统引导跳转登录页（`publicOnly` 守卫之外的 `requiresAuth` 守卫）。

### 2.2 F2 管理社团

```plantuml
@startuml
left to right direction
actor "社长 clubAdmin" as Admin

rectangle "管理社团" {
  usecase "编辑社团资料" as UC1
  usecase "新建 / 编辑活动" as UC2
  usecase "发布 / 下架 / 删除活动" as UC3
  usecase "发布招新帖" as UC4
  usecase "审核入社申请" as UC5
  usecase "管理成员权限" as UC6
}
Admin --> UC1
Admin --> UC2
Admin --> UC3
Admin --> UC4
Admin --> UC5
Admin --> UC6
note right of Admin : 仅能管理本社团\n(requireClubOwner)
note bottom of Admin : 系统管理员 admin 的全局管理\n本阶段不做（组内范围决定）
@enduml
```

## 3. 类图（前端静态结构）

```plantuml
@startuml
package "视图层 (views/components)" {
  class ClubDetailView
  class ClubApplyView
  class ActivityDetailView
  class AdminConsoleView
  class ClubProfileForm <<子组件>>
  class ActivityManager <<子组件>>
  class ApplicationReviewPanel <<子组件>>
  class MemberManager <<子组件>>
  class StateBlock
  class ClubCard
  class ActivityCard
}

package "服务层 (api)" {
  class clubApi <<module>> {
    +getClubDetail(id)
    +applyJoinClub(clubId, message)
    +getClubApplications(clubId, q)
    +reviewApplication(clubId, appId, payload)
    +getClubMembers(clubId)
    +updateClubMember(clubId, memberId, payload)
    +publishRecruitment(clubId, payload)
    +updateClub(id, payload)
  }
  class activityApi <<module>> {
    +getActivityDetail(id)
    +getActivities(q)
    +createActivity(payload)
    +updateActivity(id, payload)
    +publishActivity(id)
    +unpublishActivity(id)
    +deleteActivity(id)
    +registerActivity(id)
    +cancelRegistration(id)
  }
  class request <<adapter>> {
    +request<T>(options): Promise<T>
  }
}

package "数据层 (types / mock)" {
  class Club
  class ClubDetail
  class ClubApplication
  class ClubMember
  class RecruitmentPost
  class Activity
  class ActivityPayload
  class MockRegistry <<handlers>>

  ClubDetail --|> Club
  ClubDetail o-- ClubNotice
  ClubDetail o-- Activity : recentActivities
}

ClubDetailView --> clubApi
ClubApplyView --> clubApi
ActivityDetailView --> activityApi
AdminConsoleView --> ClubProfileForm
AdminConsoleView --> ActivityManager
AdminConsoleView --> ApplicationReviewPanel
AdminConsoleView --> MemberManager
ClubProfileForm --> clubApi
ActivityManager --> activityApi
ApplicationReviewPanel --> clubApi
MemberManager --> clubApi

clubApi --> request
activityApi --> request
request ..> MockRegistry : mock 模式
request ..> AxiosInstance : 真实模式
ClubDetailView ..> StateBlock
ClubDetailView ..> ActivityCard
ActivityDetailView ..> ClubCard
ActivityDetailView ..> ClubApplyView : 路由跳转
@enduml
```

设计要点：**单一职责**——`AdminConsoleView` 只做"标签容器 + 数据分发"，四个业务分区拆为四个子组件，各自只依赖自己用到的 api 方法。这是与"无设计直出"版本最大的结构差异（见 §8）。

## 4. 顺序图（关键流程）

### 4.1 学生报名活动

```plantuml
@startuml
actor 学生
participant ActivityDetailView
participant activityApi
participant request as request<<adapter>>
participant MockHandler as mock<<mock handler>>
participant MockDb as db

学生 -> ActivityDetailView : 点击"立即报名"
ActivityDetailView -> activityApi : registerActivity(id)
activityApi -> request : request({POST /api/activities/:id/registrations})
request -> mock : dispatchMock(options)
mock -> mock : requireRole(['student'])
mock -> db : 校验状态/名额/重复报名
alt 校验通过
  mock --> request : { code:0, data: registration }
  request --> activityApi : registration
  activityApi --> ActivityDetailView
  ActivityDetailView -> ActivityDetailView : loadActivity() 刷新进度
  ActivityDetailView --> 学生 : ElMessage.success("报名成功")
else 业务失败
  mock --> request : MockError(1409/1411/1412)
  request --> ActivityDetailView : ApiError
  ActivityDetailView --> 学生 : 统一错误提示
end
@enduml
```

### 4.2 社长审核入社申请

```plantuml
@startuml
actor 社长
participant ApplicationReviewPanel
participant clubApi
participant request as request<<adapter>>
participant MockHandler as mock
participant MockDb as db

社长 -> ApplicationReviewPanel : 点击"通过"
ApplicationReviewPanel -> clubApi : reviewApplication(clubId, appId, {action:'approve'})
clubApi -> request : request({PUT /api/clubs/:id/applications/:appId})
request -> mock : dispatchMock
mock -> mock : requireClubOwner(ctx, clubId)
mock -> db : application.status='approved', reviewedAt=now
mock --> request : { code:0, data: application }
request --> ApplicationReviewPanel
ApplicationReviewPanel -> ApplicationReviewPanel : 重新加载申请列表 + 社团详情(成员数)
ApplicationReviewPanel --> 社长 : ElMessage.success("已通过申请")
@enduml
```

## 5. 状态图（活动生命周期）

```plantuml
@startuml
[*] --> draft : 新建活动(POST /api/activities)
draft --> published : 发布(POST /:id/publish)
published --> unpublished : 下架(POST /:id/unpublish)
published --> finished : 开始时间到(系统定时任务)
unpublished --> [*] : (不可恢复展示)
draft --> [*] : 删除(DELETE /:id，仅草稿)
finished --> [*]
@enduml
```

报名状态：`registered → cancelled`（活动开始前可取消），与活动状态联动校验（未发布不可报名、名额满不可报名）。

包图：视图层 `src/views` / 组件层 `src/components` / 服务层 `src/api` / 数据层 `src/types` + `src/mock`，依赖方向只允许自上而下（视图→服务→数据），禁止反向依赖（与 CLAUDE.md 一致）。

## 6. 设计模式应用（OOD）

| 模式 | 应用位置 | 解决的问题 |
| ---- | -------- | ---------- |
| **适配器模式 (Adapter)** | `src/api/request.ts` | 把 mock 数据源与 axios 真实请求统一为同一个 `request<T>()` 接口，`VITE_USE_MOCK` 是唯一开关，页面代码零改动 |
| **状态管理（统一三态）** | `src/components/StateBlock.vue` | loading / error / empty 三态统一渲染，数据页只关心数据加载函数 |
| **观察者模式** | `src/stores/user.ts` + 路由守卫 + 401 拦截 | 登录态变化自动驱动路由跳转与请求头注入 |
| **单一职责（组件拆分）** | `AdminConsoleView` → 4 个子组件 | 每个子组件只负责一个业务分区，独立加载、独立依赖 api 方法 |
| **策略模式（隐含）** | 活动状态决定操作按钮策略 | draft→[发布,删除]，published→[下架]，finished→[只读] |

## 7. 用设计引导 Agent：约束清单

以下条目来自上面的类图与顺序图，作为给 Agent 的实现约束（也是"设计引导 Agent"的核心证据，见 `docs/agent-guidance-log.md`）：

1. 页面只能调用 `src/api/*` 导出的方法，禁止直接 axios / fetch / mock。
2. 所有请求走 `request<T>()`；mock 与真实返回信封 `{code,message,data}` 必须一致。
3. `AdminConsoleView` 不得把四个分区的逻辑写在一个文件里；必须拆出 `ClubProfileForm`、`ActivityManager`、`ApplicationReviewPanel`、`MemberManager` 四个子组件（放 `src/views/admin/components/`）。
4. 每个数据页必须有 loading / error / empty 三态，用 `StateBlock`。
5. 活动操作按钮按状态图渲染（draft/published/finished 策略不同）。
6. 样式只用 `variables.css` 变量；组件 `<style scoped>`。
7. 提交前 `npm run lint`、`npm run type-check` 零报错。

## 8. 对照分析：设计引导 Agent vs 无设计直出

> 背景：阶段二开始前，我们曾让 Agent 在无设计文档的情况下直接生成全部页面（版本 A，已删除）。
> 版本 B 为本分支按本文档约束生成的实现。差异记录如下：

| 维度 | 无设计直出（版本 A） | 设计引导（版本 B） |
| ---- | -------------------- | ------------------ |
| AdminConsoleView 结构 | 单文件约 890 行，4 个业务分区混杂，重复的状态/加载逻辑散落各处 | 容器 + 4 个单一职责子组件，每个子组件独立加载与刷新 |
| 可测试性 | 难以单测，需整页挂载 | 子组件可独立评审/测试 |
| 可讲解性 | 讲不清"为什么这样组织" | 类图即代码结构，可对照讲解 |
| 与契约一致性 | 凭 Agent 记忆对齐 api.md，存在字段使用随意 | 类型定义先行（types/），视图严格按类型取字段 |
| 设计模式体现 | 无意识地使用了 request 适配器 | 显式命名并在文档中说明模式意图 |
| 返工成本 | 需求变动需在大文件中定位多处 | 修改集中在单一子组件 |

结论：即便是"让 Agent 写代码"，**先有设计再约束 Agent**，产出在结构清晰度、可维护性、可讲解性上显著优于直出；同时设计文档成为课堂展示"人工评审过程"的直接证据。

---

## 9. 联调协调案例：活动时间时区漂移（8 小时）

> 本节记录一次真实的**组内前后端协调问题**，作为"不同部分协作遇到典型问题如何解决"的示例。
> 对应课程关注的：接口契约设计、单元测试的局限、持续集成/联调、无指责复盘。

### 9.1 现象

联调时发现：在管理后台**编辑一个已存在的活动**并保存，活动开始/结束时间会**往回跳 8 小时**；且每编辑保存一次就再偏 8 小时。新建活动则完全正常。

### 9.2 根因（契约 + 时区 + mock 掩盖，三重叠加）

| 层 | 事实 | 问题 |
| --- | --- | --- |
| 后端契约 | `docs/api.md` 约定时间字段为 ISO8601 UTC 带 `Z`（如 `2026-11-15T19:00:00Z`）；后端 `common.py` 的 `iso()` 正确输出 UTC 带 `Z` | 后端**符合契约** |
| 前端实现 | 编辑弹窗用 `activity.startTime.slice(0,16)` 填 `el-date-picker`；保存用 `new Date(...).toISOString()` 转回 UTC | `slice` 砍掉 `Z`，无时区串被当**本地时间**显示（本应是北京时间 11-16 凌晨 3 点，却显示 11-15 19 点，少 8 小时）；保存再 `toISOString()` 又减 8 小时 → 双重偏移 |
| mock 掩盖 | mock 模式时间是前端本地生成再本地读，时区天然抵消，**编辑保存不漂移** | 各端**自测都过**，联调用真实后端才暴露 |

**关键结论**：两端**各自都符合契约**，拼起来却是错的——契约只规定了"序列化格式为 UTC 带 Z"，**没明确"前端展示前需转本地时区"这一消费端责任**。

### 9.3 解决

- **后端无需改动**（契约与实现均正确）。
- **前端修复**：新增 `toLocalInput()`，编辑时把 UTC 串先转为本地 `YYYY-MM-DDTHH:mm` 再填入选择器；与保存时 `toISOString()` 转回 UTC 形成**往返一致**，消除漂移。
- 修复 commit：`4a1b708`（`frontend/src/views/admin/components/ActivityManager.vue`）。

### 9.4 流程改进（无指责复盘）

1. **契约增补**：在 `docs/api.md` 时间字段处明确补充"消费端（前端）展示前必须转本地时区"，把责任写进契约而非靠口头约定。
2. **联调前置**：时区、编码、金额、浮点精度这类"格式敏感"字段，**不能只用 mock 验证**，必须在真实数据流上跑一次"编辑→保存→回显"闭环。
3. **责任边界**：先对齐"期望值"再分头排查，避免误报"后端错了"；本例通过对照契约定位到是前端消费端缺失转换。

> 教学价值：这是"接口契约未覆盖消费约定 + 单元测试局限 + 联调才暴露"的典型组合，
> 也是软件工程课强调的**契约先行、持续集成、blameless 复盘**的真实落地。
