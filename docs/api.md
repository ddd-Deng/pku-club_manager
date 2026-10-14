# 前后端接口契约（API Contract）

> 校园社团管理系统（基础 V1.0）· 前端 ↔ 后端 / AI 服务接口约定
> 本文档是**唯一权威契约**：前端 `src/types`、`src/api`、`src/mock` 与后端实现都必须与此一致。
> 覆盖 Xmind 页面结构图中的全部功能点。变更接口请同步修改本文档与前端类型定义。

## 1. 通用约定

### 1.1 基础信息

| 项       | 约定                                                                                               |
| -------- | -------------------------------------------------------------------------------------------------- |
| 协议     | HTTP/HTTPS + JSON（`Content-Type: application/json; charset=utf-8`）                               |
| baseURL  | 由前端环境变量 `VITE_API_BASE_URL` 配置（默认 `http://localhost:8080`）                            |
| 路径前缀 | 所有接口以 `/api` 开头                                                                             |
| 时间格式 | ISO 8601 字符串，如 `2026-10-20T14:00:00.000Z`                                                     |
| ID 类型  | `string`（后端可用数字自增或 UUID，序列化为字符串）                                                |
| 命名风格 | JSON 字段统一 `camelCase`                                                                          |
| 鉴权方式 | 请求头 `Authorization: Bearer <token>`，token 由登录接口下发                                       |
| 跨域     | 前端与后端不同源时，后端需允许 `GET/POST/PUT/DELETE/OPTIONS` 与 `Authorization`、`Content-Type` 头 |

### 1.2 统一响应结构

所有接口（含成功与失败）都返回同一层信封：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

| 字段    | 类型   | 说明                                          |
| ------- | ------ | --------------------------------------------- |
| code    | number | `0` 表示成功；非 `0` 为业务错误码（见 1.4）   |
| message | string | 成功为 `ok`，失败为可直接展示给用户的中文提示 |
| data    | any    | 业务数据；无返回值时为 `null`                 |

> HTTP 状态码建议：业务错误也返回 200，由 `code` 表达；鉴权失败返回 401；权限不足返回 403。前端对 `code !== 0`、HTTP 401/403 均做统一处理。

### 1.3 统一分页结构

所有列表接口的 `data` 必须为：

```json
{
  "list": [],
  "total": 0,
  "page": 1,
  "pageSize": 10
}
```

| 查询参数 | 类型   | 默认 | 说明               |
| -------- | ------ | ---- | ------------------ |
| page     | number | 1    | 页码，从 1 开始    |
| pageSize | number | 10   | 每页条数，最大 100 |

> 少量明确不分页的接口（如分类枚举、首页推荐、未读数、足迹）在文档中单独标注「不分页」，直接返回数组或对象。

### 1.4 错误码

| code | 含义                                      | 前端行为                               |
| ---- | ----------------------------------------- | -------------------------------------- |
| 0    | 成功                                      | 取 `data`                              |
| 401  | 未登录 / token 失效                       | 清 token 并跳 `/login?redirect=原路径` |
| 403  | 角色或数据权限不足                        | 提示 message                           |
| 1001 | 账号或密码错误                            | 提示 message                           |
| 1002 | 学籍信息不匹配（找回密码 / 身份校验失败） | 提示 message                           |
| 1003 | 请求参数不完整或非法                      | 提示 message                           |
| 1004 | 资源已存在（如学号已注册）                | 提示 message                           |
| 1005 | 原密码不正确                              | 提示 message                           |
| 1404 | 资源不存在                                | 提示 message                           |
| 1409 | 状态冲突（重复申请 / 重复报名）           | 提示 message                           |
| 1410 | 已处理，不能重复操作                      | 提示 message                           |
| 1411 | 名额已满                                  | 提示 message                           |
| 1412 | 活动未发布，不可操作                      | 提示 message                           |
| 1413 | 时段不存在                                | 提示 message                           |
| 1414 | 时段已被占用                              | 提示 message                           |
| 5000 | 服务端内部错误                            | 提示「服务异常，请稍后重试」           |

### 1.5 角色

| 角色值    | 中文              | 权限范围                                                            |
| --------- | ----------------- | ------------------------------------------------------------------- |
| student   | 学生              | 浏览、报名活动、提交入社申请、个人中心                              |
| clubAdmin | 社长 / 社团管理员 | 学生权限 + 管理**本社团**的资料、活动、招新、成员、场地预约、知识库 |
| admin     | 系统管理员        | 全部社团管理权限 + 场地预约审批 + 全局数据                          |

### 1.6 公共枚举

```json
{
  "role": ["student", "clubAdmin", "admin"],
  "clubCategory": ["学术科技", "文化艺术", "体育竞技", "志愿服务"],
  "activityStatus": ["draft", "published", "unpublished", "finished"],
  "activityType": ["讲座", "比赛", "演出", "实践", "志愿活动"],
  "applicationStatus": ["pending", "approved", "rejected"],
  "reservationStatus": ["pending", "approved", "rejected"],
  "notificationType": ["application", "activity", "venue"],
  "memberRole": ["member", "officer", "owner"]
}
```

---

## 2. 登录注册与身份（Xmind 网页 2）

### 2.1 POST /api/auth/login — 统一账号登录

- 所需角色：公开
- 请求参数

  | 字段     | 类型    | 必填 | 说明                                  |
  | -------- | ------- | ---- | ------------------------------------- |
  | account  | string  | 是   | 学号或邮箱                            |
  | password | string  | 是   | 密码                                  |
  | remember | boolean | 否   | 是否记住登录状态（影响 token 有效期） |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "token": "eyJhbGciOiJIUzI1NiJ9.mock",
      "user": {
        "id": "u-student",
        "name": "林晓",
        "studentNo": "2024001",
        "email": "linxiao@campus.edu.cn",
        "role": "student",
        "avatar": "🧑‍🎓",
        "clubId": null,
        "clubName": null
      }
    }
  }
  ```

- 错误码：1001 账号或密码错误；1003 参数不完整

### 2.2 POST /api/auth/register — 注册学生账号

- 所需角色：公开（注册成功即返回 token，前端自动登录）
- 请求参数

  | 字段      | 类型   | 必填 | 说明                     |
  | --------- | ------ | ---- | ------------------------ |
  | name      | string | 是   | 姓名                     |
  | studentNo | string | 是   | 学号，需通过学生身份校验 |
  | email     | string | 是   | 邮箱                     |
  | password  | string | 是   | 密码，至少 6 位          |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "token": "eyJhbGciOiJIUzI1NiJ9.mock",
      "user": {
        "id": "u-2024099",
        "name": "张三",
        "studentNo": "2024099",
        "email": "zhangsan@campus.edu.cn",
        "role": "student",
        "avatar": "🧑‍🎓",
        "clubId": null,
        "clubName": null
      }
    }
  }
  ```

- 错误码：1003 信息不完整；1004 该学号已注册

### 2.3 POST /api/auth/logout — 登出

- 所需角色：登录（任意角色）
- 请求参数：无（依赖 `Authorization` 头）
- 响应示例

  ```json
  { "code": 0, "message": "ok", "data": null }
  ```

### 2.4 POST /api/auth/password/forgot — 密码找回

- 所需角色：公开
- 请求参数

  | 字段      | 类型   | 必填 | 说明                   |
  | --------- | ------ | ---- | ---------------------- |
  | studentNo | string | 是   | 学号                   |
  | email     | string | 是   | 注册邮箱，需与学号匹配 |

- 响应示例（后端向邮箱发送重置链接）

  ```json
  { "code": 0, "message": "重置链接已发送至邮箱", "data": null }
  ```

- 错误码：1002 学籍信息不匹配

### 2.5 POST /api/auth/student-verify — 学生身份校验

- 所需角色：公开
- 请求参数：`studentNo`(string, 必填)、`email`(string, 必填)
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": { "verified": true, "name": "林晓" }
  }
  ```

---

## 3. 用户与个人中心（Xmind 网页 5）

### 3.1 GET /api/user/profile — 获取当前登录用户资料

- 所需角色：登录（任意角色）
- 请求参数：无
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "u-club",
      "name": "陈光影",
      "studentNo": "2021002",
      "email": "chensy@campus.edu.cn",
      "role": "clubAdmin",
      "avatar": "📷",
      "clubId": "c-1",
      "clubName": "摄影社"
    }
  }
  ```

### 3.2 PUT /api/user/profile — 修改个人资料

- 所需角色：登录（本人）
- 请求参数

  | 字段   | 类型   | 必填 | 说明              |
  | ------ | ------ | ---- | ----------------- |
  | name   | string | 否   | 姓名              |
  | email  | string | 否   | 邮箱              |
  | avatar | string | 否   | 头像 URL 或 emoji |

- 响应示例：同 3.1（返回更新后的用户对象）

### 3.3 PUT /api/user/password — 修改密码（账号安全设置）

- 所需角色：登录（本人）
- 请求参数：`oldPassword`(string, 必填)、`newPassword`(string, 必填, ≥6 位)
- 响应示例

  ```json
  { "code": 0, "message": "ok", "data": null }
  ```

- 错误码：1005 原密码不正确；1003 新密码不合法

### 3.4 GET /api/user/footprints — 燕园活动足迹档案（不分页）

- 所需角色：登录
- 请求参数：无
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      {
        "id": "fp-a-7",
        "activityId": "a-7",
        "title": "秋季读书分享会",
        "clubName": "文学社",
        "finishedAt": "2026-10-03T13:00:00.000Z"
      }
    ]
  }
  ```

### 3.5 GET /api/user/applications — 我的入社申请记录（不分页）

- 所需角色：student
- 请求参数：无（后端按 token 识别用户）
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      {
        "id": "ap-3",
        "clubId": "c-3",
        "clubName": "辩论社",
        "applicantName": "林晓",
        "message": "想锻炼表达能力，希望加入辩论社。",
        "status": "pending",
        "createdAt": "2026-10-11T02:00:00.000Z",
        "reviewedAt": null
      }
    ]
  }
  ```

### 3.6 GET /api/user/activity-registrations — 我的活动报名记录（不分页）

- 所需角色：student
- 请求参数：无
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      {
        "id": "rg-1",
        "activityId": "a-1",
        "title": "秋日校园摄影大赛",
        "clubName": "摄影社",
        "startTime": "2026-10-20T06:00:00.000Z",
        "status": "registered",
        "createdAt": "2026-10-12T02:00:00.000Z"
      }
    ]
  }
  ```

---

## 4. 社团（Xmind 网页 1 / 3 / 4）

### 4.1 GET /api/clubs — 社团列表（分页）

- 所需角色：公开
- 请求参数（query）

  | 字段     | 类型   | 必填 | 说明                                            |
  | -------- | ------ | ---- | ----------------------------------------------- |
  | keyword  | string | 否   | 模糊匹配社团名称 / 简介 / 标签                  |
  | category | string | 否   | 社团分类，取值见 1.6；`全部类型` 或不传表示不限 |
  | page     | number | 否   | 页码，默认 1                                    |
  | pageSize | number | 否   | 每页条数，默认 10（前端广场页传 8）             |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "list": [
        {
          "id": "c-1",
          "name": "摄影社",
          "category": "文化艺术",
          "logo": "📷",
          "description": "用镜头记录校园瞬间，定期组织摄影培训与作品展览。",
          "memberCount": 128,
          "foundedAt": "2015-09-01",
          "tags": ["摄影", "校园纪实", "户外活动"]
        }
      ],
      "total": 8,
      "page": 1,
      "pageSize": 8
    }
  }
  ```

### 4.2 GET /api/clubs/categories — 社团分类枚举（不分页）

- 所需角色：公开
- 请求参数：无
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": ["学术科技", "文化艺术", "体育竞技", "志愿服务"]
  }
  ```

### 4.3 GET /api/clubs/recommended — 首页社团推荐（不分页）

- 所需角色：公开
- 请求参数：`limit`(number, 否, 默认 4)
- 响应示例：同 4.1 的 `list` 元素数组

### 4.4 GET /api/clubs/{id} — 社团详情

- 所需角色：公开
- 路径参数：`id`(string, 必填) 社团 ID
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "c-1",
      "name": "摄影社",
      "category": "文化艺术",
      "logo": "📷",
      "description": "用镜头记录校园瞬间，定期组织摄影培训与作品展览。",
      "introduction": "摄影社成立于 2015 年，下设外拍组、后期组、器材组……",
      "memberCount": 128,
      "foundedAt": "2015-09-01",
      "tags": ["摄影", "校园纪实", "户外活动"],
      "notices": [
        {
          "id": "n-1",
          "title": "秋季招新截止提醒",
          "content": "本学期招新将于两周后截止，请有意向的同学尽快提交入社申请。",
          "publishedAt": "2026-10-11T02:00:00.000Z"
        }
      ],
      "recentActivities": [
        {
          "id": "a-1",
          "clubId": "c-1",
          "clubName": "摄影社",
          "title": "秋日校园摄影大赛",
          "cover": "🍂",
          "description": "以\"秋日校园\"为主题征集摄影作品。",
          "location": "大学生活动中心展厅",
          "startTime": "2026-10-20T06:00:00.000Z",
          "endTime": "2026-10-20T09:00:00.000Z",
          "status": "published",
          "capacity": 80,
          "registeredCount": 46,
          "type": "比赛"
        }
      ]
    }
  }
  ```

- 错误码：1404 社团不存在

### 4.5 PUT /api/clubs/{id} — 编辑社团资料（管理后台「社团资料编辑分区」）

- 所需角色：clubAdmin（仅本社团）/ admin
- 请求参数

  | 字段         | 类型     | 必填 | 说明                            |
  | ------------ | -------- | ---- | ------------------------------- |
  | name         | string   | 否   | 社团名称                        |
  | description  | string   | 否   | 一句话简介（卡片展示）          |
  | introduction | string   | 否   | 详细介绍（富文本，HTML 字符串） |
  | logo         | string   | 否   | 头像 URL 或 emoji               |
  | tags         | string[] | 否   | 标签，最多 5 个                 |

- 响应示例：同 4.4（返回更新后的详情）
- 错误码：403 只能管理自己所属的社团；1404 社团不存在

### 4.6 POST /api/clubs/{id}/applications — 提交入社申请

- 所需角色：student
- 请求参数：`message`(string, 否, ≤200 字) 申请理由
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "ap-1729900000000",
      "clubId": "c-1",
      "clubName": "摄影社",
      "applicantName": "林晓",
      "message": "热爱摄影，希望加入学习后期。",
      "status": "pending",
      "createdAt": "2026-10-13T02:00:00.000Z",
      "reviewedAt": null
    }
  }
  ```

- 错误码：1409 已提交过该社团的申请；1404 社团不存在
- 副作用：向该社团 clubAdmin 推送一条 `type=application` 的通知

### 4.7 GET /api/clubs/{id}/applications — 入社申请列表（分页，招新审核分区）

- 所需角色：clubAdmin（仅本社团）/ admin
- 请求参数（query）：`status`(string, 否, pending/approved/rejected)、`page`、`pageSize`
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "list": [
        {
          "id": "ap-1",
          "clubId": "c-1",
          "clubName": "摄影社",
          "applicantName": "王小明",
          "message": "热爱风光摄影，有自己的相机。",
          "status": "pending",
          "createdAt": "2026-10-12T02:00:00.000Z",
          "reviewedAt": null
        }
      ],
      "total": 2,
      "page": 1,
      "pageSize": 10
    }
  }
  ```

### 4.8 PUT /api/clubs/{id}/applications/{appId} — 审核入社申请

- 所需角色：clubAdmin（仅本社团）/ admin
- 请求参数：`action`(string, 必填, `approve` | `reject`)、`comment`(string, 否) 审核意见
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "ap-1",
      "clubId": "c-1",
      "clubName": "摄影社",
      "applicantName": "王小明",
      "message": "热爱风光摄影，有自己的相机。",
      "status": "approved",
      "createdAt": "2026-10-12T02:00:00.000Z",
      "reviewedAt": "2026-10-13T03:00:00.000Z"
    }
  }
  ```

- 错误码：1410 该申请已处理；1003 action 非法
- 副作用：`approve` 时社团 `memberCount +1` 并新增成员记录；向申请人推送 `type=application` 通知

### 4.9 GET /api/clubs/{id}/members — 成员列表（不分页）

- 所需角色：clubAdmin（仅本社团）/ admin
- 请求参数：无
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      { "id": "m-1", "name": "陈光影", "role": "owner", "joinedAt": "2025-09-08T02:00:00.000Z" },
      { "id": "m-2", "name": "赵一帆", "role": "officer", "joinedAt": "2025-12-08T02:00:00.000Z" }
    ]
  }
  ```

### 4.10 PUT /api/clubs/{id}/members/{memberId} — 成员权限管理

- 所需角色：clubAdmin（仅本社团，且不能变更 owner）/ admin
- 请求参数

  | 字段   | 类型   | 必填 | 说明                                     |
  | ------ | ------ | ---- | ---------------------------------------- |
  | role   | string | 否   | `member` \| `officer`，调整成员角色      |
  | action | string | 否   | 传 `remove` 表示移除成员（与 role 互斥） |

- 响应示例：返回变更后的成员对象；`action=remove` 时返回被移除成员
- 错误码：1404 成员不存在；403 无权操作 owner

### 4.11 POST /api/clubs/{id}/recruitments — 发布招新帖

- 所需角色：clubAdmin（仅本社团）/ admin
- 请求参数：`title`(string, 必填)、`content`(string, 必填)、`deadline`(string, 必填, `YYYY-MM-DD`)
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "rc-1729900000000",
      "clubId": "c-1",
      "title": "摄影社秋季招新帖",
      "content": "招收热爱摄影的新成员，不限器材基础，提供培训。",
      "deadline": "2026-10-27",
      "createdAt": "2026-10-13T02:00:00.000Z"
    }
  }
  ```

### 4.12 GET /api/clubs/{id}/recruitments — 招新帖列表（不分页）

- 所需角色：公开
- 请求参数：无
- 响应示例：同 4.11 的 `data` 数组

---

## 5. 活动（Xmind 网页 1 / 3 / 4 + 活动详情页）

### 5.1 GET /api/activities — 活动列表（分页）

- 所需角色：公开（未传 `status` 时只返回 `published` 与 `finished`）
- 请求参数（query）

  | 字段            | 类型   | 必填 | 说明                                                                         |
  | --------------- | ------ | ---- | ---------------------------------------------------------------------------- |
  | keyword         | string | 否   | 匹配活动标题 / 描述                                                          |
  | clubId          | string | 否   | 限定社团（社团详情页历史活动用）                                             |
  | category        | string | 否   | 按社团分类过滤                                                               |
  | startDate       | string | 否   | `YYYY-MM-DD`，活动开始日期下限                                               |
  | endDate         | string | 否   | `YYYY-MM-DD`，活动开始日期上限                                               |
  | status          | string | 否   | `draft` / `published` / `unpublished` / `finished`（管理后台活动管理分区用） |
  | page / pageSize | number | 否   | 分页                                                                         |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "list": [
        {
          "id": "a-1",
          "clubId": "c-1",
          "clubName": "摄影社",
          "title": "秋日校园摄影大赛",
          "cover": "🍂",
          "description": "以\"秋日校园\"为主题征集摄影作品。",
          "location": "大学生活动中心展厅",
          "startTime": "2026-10-20T06:00:00.000Z",
          "endTime": "2026-10-20T09:00:00.000Z",
          "status": "published",
          "capacity": 80,
          "registeredCount": 46,
          "type": "比赛"
        }
      ],
      "total": 7,
      "page": 1,
      "pageSize": 10
    }
  }
  ```

### 5.2 GET /api/activities/upcoming — 近期活动 / 首页活动预告（不分页）

- 所需角色：公开
- 请求参数：`limit`(number, 否, 默认 5)
- 说明：只返回 `status=published` 且 `startTime >= now` 的活动，按开始时间升序
- 响应示例：同 5.1 的 `list` 元素数组

### 5.3 GET /api/activities/{id} — 活动详情

- 所需角色：公开（`draft` / `unpublished` 状态仅 clubAdmin / admin 可见）
- 路径参数：`id`(string, 必填)
- 响应示例：同 5.1 的 `list` 元素对象，另附 `registered`(boolean, 当前登录用户是否已报名，未登录为 false)

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "a-1",
      "title": "秋日校园摄影大赛",
      "status": "published",
      "registered": true,
      "registeredCount": 46,
      "capacity": 80
    }
  }
  ```

- 错误码：1404 活动不存在

### 5.4 POST /api/activities — 新建活动（管理后台「活动管理分区」）

- 所需角色：clubAdmin（本社团）/ admin
- 请求参数

  | 字段        | 类型   | 必填 | 说明                          |
  | ----------- | ------ | ---- | ----------------------------- |
  | title       | string | 是   | 活动标题                      |
  | description | string | 是   | 活动描述                      |
  | location    | string | 是   | 活动地点                      |
  | startTime   | string | 是   | ISO 时间                      |
  | endTime     | string | 是   | ISO 时间，需晚于 startTime    |
  | capacity    | number | 是   | 名额上限                      |
  | type        | string | 是   | 活动类型，取值见 1.6          |
  | cover       | string | 否   | 封面 URL 或 emoji             |
  | clubId      | string | 否   | 仅 admin 需要传，指定归属社团 |

- 响应示例：新建活动默认 `status=draft`（草稿），返回完整活动对象（结构同 5.1 列表项）
- 错误码：1003 标题等必填项缺失；403 无权在该社团下建活动

### 5.5 PUT /api/activities/{id} — 编辑活动

- 所需角色：clubAdmin（本社团）/ admin
- 请求参数：同 5.4，全部可选（只传需要修改的字段）
- 响应示例：返回更新后的活动对象
- 说明：已发布活动编辑后仍保持 `published`；草稿编辑后仍为 `draft`

### 5.6 POST /api/activities/{id}/publish — 发布活动（草稿 → 已发布）

- 所需角色：clubAdmin（本社团）/ admin
- 请求参数：无
- 响应示例：返回 `status=published` 的活动对象
- 副作用：向关注该社团的用户推送 `type=activity` 的「活动上新提醒」
- 错误码：1410 活动已发布

### 5.7 POST /api/activities/{id}/unpublish — 下架活动

- 所需角色：clubAdmin（本社团）/ admin
- 请求参数：无
- 响应示例：返回 `status=unpublished` 的活动对象
- 错误码：1410 活动当前状态不可下架

### 5.8 DELETE /api/activities/{id} — 删除活动

- 所需角色：clubAdmin（本社团，仅可删 `draft`）/ admin
- 请求参数：无
- 响应示例

  ```json
  { "code": 0, "message": "ok", "data": null }
  ```

- 错误码：1410 已发布活动不可删除，请先下架

### 5.9 POST /api/activities/{id}/registrations — 活动报名

- 所需角色：student
- 请求参数：无（用户由 token 识别）
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "rg-1729900000000",
      "activityId": "a-1",
      "userId": "u-student",
      "userName": "林晓",
      "status": "registered",
      "createdAt": "2026-10-13T02:00:00.000Z"
    }
  }
  ```

- 错误码：1411 报名人数已满；1412 活动未发布；1409 已报名
- 副作用：`registeredCount +1`

### 5.10 DELETE /api/activities/{id}/registrations — 取消报名

- 所需角色：student（本人报名记录）
- 请求参数：无
- 响应示例：`{ "code": 0, "message": "ok", "data": null }`
- 错误码：1404 未找到报名记录；1410 活动已开始，不可取消
- 副作用：`registeredCount -1`（不小于 0）

---

## 6. 场地与物资预约（Xmind 网页 4「场地物资预约分区」）

### 6.1 GET /api/venues — 场地与可预约时段（不分页）

- 所需角色：登录（任意角色）
- 请求参数（query）：`date`(string, 否, `YYYY-MM-DD`) 只返回指定日期的时段
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [
      {
        "id": "v-1",
        "name": "大学生活动中心 305",
        "location": "大学生活动中心三楼",
        "slots": [
          { "date": "2026-10-14", "timeSlot": "14:00-16:00", "available": true },
          { "date": "2026-10-14", "timeSlot": "19:00-21:00", "available": false }
        ]
      }
    ]
  }
  ```

### 6.2 POST /api/venue-reservations — 提交场地 / 物资预约

- 所需角色：clubAdmin（本社团）/ admin
- 请求参数

  | 字段     | 类型     | 必填 | 说明                                      |
  | -------- | -------- | ---- | ----------------------------------------- |
  | venueId  | string   | 是   | 场地 ID                                   |
  | date     | string   | 是   | `YYYY-MM-DD`                              |
  | timeSlot | string   | 是   | 时段，如 `19:00-21:00`                    |
  | purpose  | string   | 是   | 用途说明                                  |
  | items    | string[] | 否   | 随场地预约的物资，如 `["投影仪", "白板"]` |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "vr-1729900000000",
      "venueId": "v-1",
      "venueName": "大学生活动中心 305",
      "clubId": "c-1",
      "clubName": "摄影社",
      "date": "2026-10-17",
      "timeSlot": "19:00-21:00",
      "purpose": "摄影社例会与评片会",
      "items": ["投影仪", "白板"],
      "status": "pending",
      "createdAt": "2026-10-13T02:00:00.000Z"
    }
  }
  ```

- 错误码：1413 时段不存在；1414 时段已被占用；1404 场地不存在

### 6.3 GET /api/venue-reservations — 预约单列表（分页）

- 所需角色：clubAdmin（只返回本社团）/ admin（可看全部）
- 请求参数（query）：`status`(string, 否, pending/approved/rejected)、`clubId`(string, 否, 仅 admin 有效)、`page`、`pageSize`
- 响应示例：分页结构，`list` 元素同 6.2 的 `data`

### 6.4 PUT /api/venue-reservations/{id} — 审批预约单

- 所需角色：admin
- 请求参数：`action`(string, 必填, `approve` | `reject`)、`comment`(string, 否)
- 响应示例：返回更新后的预约单（`status` 为 `approved` / `rejected`）
- 副作用：向提交方 clubAdmin 推送 `type=venue` 的「场地预约审批反馈」通知
- 错误码：1410 该预约单已审批；1003 action 非法

---

## 7. 社团知识库与 AI 问答（Xmind 网页 4「知识库上传分区」+ 网页 7）

### 7.1 POST /api/kb/documents — 上传知识库文档

- 所需角色：clubAdmin（本社团）/ admin
- 请求方式：`multipart/form-data`
- 请求参数

  | 字段   | 类型   | 必填 | 说明                                        |
  | ------ | ------ | ---- | ------------------------------------------- |
  | file   | File   | 是   | 文档文件，支持 pdf / docx / md / txt，≤10MB |
  | clubId | string | 否   | 仅 admin 需要传，指定归属社团               |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "id": "kb-1729900000000",
      "clubId": "c-1",
      "clubName": "摄影社",
      "title": "摄影社章程.pdf",
      "size": 245760,
      "uploadedBy": "陈光影",
      "uploadedAt": "2026-10-13T02:00:00.000Z"
    }
  }
  ```

- 错误码：1003 文件格式或大小不合规
- 说明：后端上传成功后需触发文档解析与向量化，供 7.4 的 RAG 检索使用（AI 侧实现，不在前端范围）

### 7.2 GET /api/kb/documents — 知识库文档列表（分页）

- 所需角色：登录
- 请求参数（query）：`clubId`(string, 否)、`page`、`pageSize`
- 响应示例：分页结构，`list` 元素同 7.1 的 `data`

### 7.3 DELETE /api/kb/documents/{id} — 删除知识库文档

- 所需角色：clubAdmin（本社团）/ admin
- 请求参数：无
- 响应示例：`{ "code": 0, "message": "ok", "data": null }`
- 错误码：1404 文档不存在

### 7.4 POST /api/ai/chat — RAG 问答（网页 7「RAG 问答对话窗口」）

- 所需角色：登录
- 请求参数

  | 字段     | 类型   | 必填 | 说明                                                                            |
  | -------- | ------ | ---- | ------------------------------------------------------------------------------- |
  | question | string | 是   | 用户问题，≤500 字                                                               |
  | clubId   | string | 否   | 限定检索某个社团的知识库                                                        |
  | history  | array  | 否   | 多轮上下文，元素 `{ role: 'user' \| 'assistant', content: string }`，最多 10 条 |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "answer": "根据《摄影社章程》第 3 条，社团例会每周三 19:00 在大学生活动中心 305 举行……",
      "references": [{ "docId": "kb-1", "title": "摄影社章程.pdf" }]
    }
  }
  ```

- 错误码：1003 问题为空；5000 AI 服务异常
- 说明：AI 模型与向量检索由后端 / AI 同学实现，前端只负责提问、渲染答案与引用来源

### 7.5 GET /api/ai/documents/search — 社团文档检索（网页 7「社团文档检索框」，不分页）

- 所需角色：登录
- 请求参数（query）：`keyword`(string, 必填)、`clubId`(string, 否)
- 响应示例：同 7.1 的 `data` 数组（按相关度排序，最多 20 条）
- 错误码：1003 keyword 为空

---

## 8. 消息与通知（Xmind 网页 6）

### 8.1 GET /api/notifications — 通知列表（分页）

- 所需角色：登录（只返回本人相关通知）
- 请求参数（query）

  | 字段            | 类型    | 必填 | 说明                                                                       |
  | --------------- | ------- | ---- | -------------------------------------------------------------------------- |
  | type            | string  | 否   | `application`(入社申请审核) / `activity`(活动上新) / `venue`(场地预约审批) |
  | read            | boolean | 否   | 只查已读 / 未读                                                            |
  | page / pageSize | number  | 否   | 分页                                                                       |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "list": [
        {
          "id": "nt-1",
          "type": "application",
          "title": "入社申请待审核",
          "content": "王小明 提交了摄影社入社申请，请及时处理。",
          "read": false,
          "createdAt": "2026-10-12T02:00:00.000Z",
          "link": "/admin"
        }
      ],
      "total": 4,
      "page": 1,
      "pageSize": 10
    }
  }
  ```

### 8.2 GET /api/notifications/unread-count — 未读通知数（不分页）

- 所需角色：登录
- 请求参数：无
- 响应示例

  ```json
  { "code": 0, "message": "ok", "data": 2 }
  ```

- 用途：顶部导航铃铛角标

### 8.3 PUT /api/notifications/{id}/read — 标记单条已读

- 所需角色：登录（本人）
- 请求参数：无
- 响应示例：返回更新后的通知对象（`read: true`）
- 错误码：1404 通知不存在

### 8.4 PUT /api/notifications/read-all — 全部标记已读

- 所需角色：登录（本人）
- 请求参数：无
- 响应示例

  ```json
  { "code": 0, "message": "ok", "data": { "updated": 2 } }
  ```

---

## 9. 搜索（Xmind 网页 8）

### 9.1 GET /api/search — 综合搜索（分页）

- 所需角色：公开
- 请求参数（query）

  | 字段                | 类型   | 必填 | 说明                                           |
  | ------------------- | ------ | ---- | ---------------------------------------------- |
  | keyword             | string | 是   | 检索关键词，匹配社团与活动                     |
  | type                | string | 否   | `club` \| `activity`，限定结果类型（高级筛选） |
  | category            | string | 否   | 社团分类（高级筛选）                           |
  | activityType        | string | 否   | 活动类型（高级筛选）                           |
  | startDate / endDate | string | 否   | 活动时间范围，`YYYY-MM-DD`                     |
  | page / pageSize     | number | 否   | 分页                                           |

- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "list": [
        { "type": "club", "id": "c-1", "title": "摄影社", "subtitle": "用镜头记录校园瞬间……" },
        {
          "type": "activity",
          "id": "a-1",
          "title": "秋日校园摄影大赛",
          "subtitle": "摄影社 · 比赛"
        }
      ],
      "total": 2,
      "page": 1,
      "pageSize": 10
    }
  }
  ```

- 错误码：1003 keyword 为空
- 副作用：登录状态下写入搜索历史（同关键词去重，更新为最近一次时间）

### 9.2 GET /api/search/history — 搜索历史（不分页）

- 所需角色：登录
- 请求参数：`limit`(number, 否, 默认 10)
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": [{ "id": "sh-1", "keyword": "摄影", "searchedAt": "2026-10-12T02:00:00.000Z" }]
  }
  ```

### 9.3 DELETE /api/search/history/{id} — 删除单条搜索历史

- 所需角色：登录（本人）
- 请求参数：无
- 响应示例：`{ "code": 0, "message": "ok", "data": null }`
- 错误码：1404 历史记录不存在

### 9.4 DELETE /api/search/history — 清空搜索历史

- 所需角色：登录（本人）
- 请求参数：无
- 响应示例：`{ "code": 0, "message": "ok", "data": null }`

---

## 10. 连通性测试

### 10.1 GET /api/test/hello — 前后端连通性测试

- 所需角色：公开
- 请求参数：无
- 响应示例

  ```json
  {
    "code": 0,
    "message": "ok",
    "data": {
      "message": "hello world",
      "source": "server",
      "serverTime": "2026-10-13T02:00:00.000Z"
    }
  }
  ```

- 说明：前端页面 `/test/hello` 展示 `hello world` 与该接口返回值。mock 模式下 `source` 为 `mock`，真实模式下后端返回 `server`。这是联调时的第一个验证接口。

---

## 11. 前端调用映射与实现状态

### 11.1 接口 → 前端 API 模块映射

| 模块            | 前端文件                  | mock handler                    | 覆盖接口 |
| --------------- | ------------------------- | ------------------------------- | -------- |
| 认证            | `src/api/auth.ts`         | `src/mock/handlers/auth.ts`     | 2.1–2.5  |
| 用户 / 个人中心 | `src/api/user.ts`         | `src/mock/handlers/user.ts`     | 3.1–3.6  |
| 社团            | `src/api/club.ts`         | `src/mock/handlers/club.ts`     | 4.1–4.11 |
| 活动            | `src/api/activity.ts`     | `src/mock/handlers/activity.ts` | 5.1–5.10 |
| 场地物资        | `src/api/venue.ts`        | `src/mock/handlers/misc.ts`     | 6.1–6.4  |
| 知识库          | `src/api/kb.ts`           | `src/mock/handlers/misc.ts`     | 7.1–7.3  |
| AI 问答         | `src/api/ai.ts`           | `src/mock/handlers/misc.ts`     | 7.4–7.5  |
| 消息通知        | `src/api/notification.ts` | `src/mock/handlers/misc.ts`     | 8.1–8.4  |
| 搜索            | `src/api/search.ts`       | `src/mock/handlers/misc.ts`     | 9.1–9.4  |
| 连通性测试      | `src/api/test.ts`         | `src/mock/handlers/misc.ts`     | 10.1     |

### 11.2 第一阶段 mock 覆盖情况

- **已实现 mock**（页面可直接演示）：10.1 hello、2.1–2.3 登录注册登出、3.1 用户资料、4.1–4.4 社团列表 / 分类 / 推荐 / 详情、5.1–5.2 活动列表与近期活动、8.1–8.2 通知列表与未读数、9.1 综合搜索、7.4 AI 问答。
- **契约已定义、mock 待补**：其余接口在 mock 模式下会返回 `[mock] 接口未实现：<METHOD> <PATH>（契约见 docs/api.md）`，属预期行为；实现对应页面前先在 `src/mock/handlers/` 补 handler。
- 上传类接口（7.1）真实模式为 `multipart/form-data`，mock 模式接受 `{ title, size }` 字段模拟。

### 11.3 后端联调清单

1. 后端按本契约实现 `10.1`，前端把 `VITE_USE_MOCK` 改为 `false`，打开 `/test/hello` 应显示 `source: "server"`。
2. 依次联调：登录（2.1）→ 社团列表（4.1）→ 社团详情（4.4）→ 活动（5.x）→ 其余模块。
3. 后端需保证：信封结构、分页结构、字段名 camelCase、角色枚举值、错误码语义与本文档一致；前端不做字段兼容适配。
4. 若后端字段确需调整，先改本文档与 `src/types`，再改 mock 与页面，避免三处不一致。
