# GitHub Projects 看板搭建与卡片清单（backlog #12）

> 日期：2026-11-18｜负责人：待指派（需具备仓库 Projects 权限的组员）
> 目标：在 GitHub 上建好四列看板，摆放与 `docs/backlog.md` 一一对应的 15 张卡片，组员可访问并移动卡片。

## 1. 现状说明

本机没有安装 `gh` CLI，也没有仓库的 GitHub 凭据，因此看板**尚未实际创建**。
本文档给出可直接执行的搭建步骤与卡片清单；仓库地址为
`https://github.com/ddd-Deng/pku-club_manager`，由具备权限的组员在 15 分钟内即可完成。

## 2. 看板结构（四列）

| 列名        | 含义                                   | 进入条件                       |
| ----------- | -------------------------------------- | ------------------------------ |
| `Backlog`   | 已识别但尚未开始的需求                 | 写入 `docs/backlog.md` 即入列  |
| `In Progress` | 本迭代正在开发                       | 已建功能分支并开始编码         |
| `Review`    | 自测通过、等待组内评审 / 课堂演示      | lint、type-check、pytest 全绿  |
| `Done`      | 已合并进 `main` 且可演示               | PR 合并 + How to demo 走通     |

建议同时配置两个自定义字段（Project 设置 → New field）：

- `Imp`（Number）：重要度，与 `docs/backlog.md` 的 Imp 列一致。
- `Est`（Number）：故事点，与 backlog 的 Est 列一致。
- 可选：`Iteration`（Iteration，长度 7 天）用于把卡片分配到阶段二 / 阶段三，配合甘特图讲解。

## 3. 卡片清单（15 张，与 backlog ID 一一对应）

标题统一使用 `#ID 名称` 格式，正文粘贴 backlog 的 How to demo 与 Notes，便于课堂演示时按卡讲。

| 卡片标题                             | Imp | Est | 建议初始列 | 标签（可选）        |
| ------------------------------------ | --- | --- | ---------- | ------------------- |
| `#1 社团详情页`                      | 40  | 8   | Done       | F1-查阅社团信息     |
| `#2 活动详情页（报名/取消）`         | 40  | 8   | Done       | F1-查阅社团信息     |
| `#3 申请入社页`                      | 30  | 5   | Done       | F1-查阅社团信息     |
| `#4 后台·社团资料编辑`               | 30  | 5   | Done       | F2-管理社团         |
| `#5 后台·活动管理`                   | 35  | 8   | Done       | F2-管理社团         |
| `#6 后台·招新审核`                   | 35  | 8   | Done       | F2-管理社团         |
| `#7 后台·发布招新帖`                 | 20  | 3   | Done       | F2-管理社团         |
| `#8 后台·成员权限管理`               | 25  | 5   | Done       | F2-管理社团         |
| `#9 OOA/OOD 设计文档`                | 50  | 5   | Done       | 设计文档            |
| `#10 设计引导 Agent 对照记录`        | 30  | 2   | Done       | AI 协作             |
| `#11 阶段文档与 README 状态更新`     | 20  | 1   | Done       | 文档                |
| `#12 GitHub Kanban 看板搭建`         | 20  | 1   | In Progress| 流程                |
| `#13 个人中心页`                     | 30  | 8   | Done       | F1-查阅社团信息     |
| `#14 场地物资预约后台分区`           | 20  | 5   | Done       | F2-管理社团         |
| `#15 知识库上传后台分区`             | 15  | 5   | Backlog    | 后续迭代            |

第三阶段新增的缺陷修复卡（建议补 2 张，便于在看板上体现「第一次迭代」的返工闭环）：

| 卡片标题                                     | Imp | Est | 建议初始列 | 说明                                                       |
| -------------------------------------------- | --- | --- | ---------- | ---------------------------------------------------------- |
| `#16 修复：学生看不到入社申请进度`           | 35  | 3   | Done       | 个人中心 + 社团详情 `myStatus`；覆盖「社长通过后学生无感」 |
| `#17 修复：社团简介出现裸露 HTML 标签`     | 25  | 2   | Done       | 统一为纯文本契约：seed、写入净化、读取归一三处同时修正     |

## 4. 手工搭建步骤（Projects V2）

1. 打开仓库 → 右上 `Projects` 标签 → `Link a project` → `New project`。
2. 模板选 `Kanban`（或 `Board`），命名 `校园社团管理系统 · 迭代看板`。
3. 把默认列改成上表四列：`Backlog` / `In Progress` / `Review` / `Done`。
4. 新建自定义字段 `Imp`、`Est`（Number），可选 `Iteration`。
5. 逐张新增卡片：标题按第 3 节，正文粘贴 backlog 的 How to demo / Notes，拖到建议列。
6. `Settings`（Project 设置）→ `Manage access` → 邀请全体组员为 `Writer`（可移动卡片）。
7. 仓库 `Settings` → `General` → `Features` 勾选 `Issues`，后续把卡片转为 Issue 以便与 commit 关联（提交信息写 `#卡片号` 即可在卡片时间线里看到 commit）。

## 5. 可选：用 gh CLI 批量建卡

安装并登录 `gh` 后（`gh auth login`），可用仓库 Issue 承载卡片，Projects 会自动同步：

```bash
gh issue create --title "#13 个人中心页" --body "见 docs/backlog.md ID 13" --label "F1-查阅社团信息"
gh issue list --limit 20
gh project item-add <PROJECT_NUMBER> --owner ddd-Deng --issue <ISSUE_NUMBER>
```

## 6. 验收标准（对应 backlog 的 How to demo）

- [ ] 四列齐备，列名与本文档一致。
- [ ] 15 张卡（含新增 2 张修复卡共 17 张）全部就位，Imp / Est 已填。
- [ ] 任一组员登录后可以拖动卡片从 `In Progress` 到 `Review`（现场演示一次）。
- [ ] 至少一张卡片的时间线能看到关联 commit（证明看板与代码库联动）。
