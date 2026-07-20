---
name: work-report-generator
description: >-
  从 SQLite 数据库读取结构化工作数据（会议纪要、任务记录等），按日期组织、
  提取关键工作项，生成日报/周报 Markdown 报告。数据源无关，配置驱动。
  触发词：生成工作周报、整理工作内容、汇总会议、工作报告、weekly report、
  日报、daily、周报、weekly。
agent_created: true
---

# 工作内容报告生成器

从 SQLite 数据库读取 WorkItem 数据，生成按日期组织的日报/周报 Markdown 报告。
**数据源无关**——只要数据源将工作项写入 SQLite 并符合 WorkItem Schema，就能生成报告。

## 架构

```
config.yaml (project-level: .workbuddy/data/config.yaml)
     │
     ▼
┌──────────────────────────────────────────────────────┐
│  work-report-generator (user-level skill)             │
│                                                       │
│  SQLite DB ──→ Query ──→ Assemble ──→ Render ──→ 输出 │
│                                                       │
│  数据源（外部）写 WorkItem 行 ──→ SQLite work_items 表 │
└──────────────────────────────────────────────────────┘
```

## 快速开始

### 日报

```
用户: "日报" / "daily" / "整理工作"
```

### 周报

```
用户: "周报" / "weekly" / "本周总结"
```

### 命令行

```bash
# 日报
python scripts/run.py daily

# 周报（预览）
python scripts/run.py weekly

# 周报（确认发布）
python scripts/run.py weekly --confirm
```

## 工作流

### 日报模式

```
用户说"日报"等触发词
  │
  ├── Step 1: 确定 workspace（默认当前工作目录）
  ├── Step 2: 加载 config.yaml（scripts/config.py）
  │           └── 缺失时使用默认配置
  ├── Step 3: 运行 scripts/run.py daily
  │           ├── assemble_daily() → 产出日报 DSL
  │           ├── DailyRenderer → 渲染 Markdown
  │           └── save_to_local() → 写入 reports/YYYY-MM-DD.md
  ├── Step 4: 按 config.outputs.daily 输出
  │           ├── local_md → 已保存
  │           └── feishu_msg → 调用 lark-im skill 发送飞书消息
  └── 完成
```

### 周报模式

```
用户说"周报"等触发词
  │
  ├── Step 1-3: 同日报，模式为 weekly
  ├── Step 4: 按 config.outputs.weekly 输出
  │           ├── local_md → 已保存
  │           └── feishu_msg → 调用 lark-im skill 发送飞书消息（预览）
  ├── Step 5: 等待用户确认
  │           ├── 用户说"确认" → 发布飞书文档（调用 lark-doc skill）
  │           └── 未确认 → 仅本地存档
  └── 完成
```

### 周报模式（带 LLM 增强）

```
用户说"周报"等触发词
  │
  ├── Step 1-3: 同日报，模式为 weekly
  ├── Step 3.5: 如果 config.report.weekly.include_threads 为 true
  │           ├── 收集所有会议的 title 和 ai_summary
  │           ├── 用 LLM 分析工作主线（3-5 条，每条 1-2 句话）
  │           └── 将 LLM 产出的 threads 传入 assemble_weekly(threads=...)
  ├── Step 4: 按 config.outputs.weekly 输出
  │           ├── local_md → 已保存
  │           └── feishu_msg → 调用 lark-im skill 发送飞书消息（预览）
  ├── Step 5: 等待用户确认
  │           ├── 用户说"确认" → 发布飞书文档（调用 lark-doc skill）
  │           └── 未确认 → 仅本地存档
  └── 完成
```

## 配置

配置文件位于 `{workspace}/.workbuddy/data/config.yaml`，缺失时使用默认配置。

```yaml
# 数据源声明
data_sources:
  tasks: lark_task
  calendar: lark_calendar
  meetings: lark_vc

# 输出渠道
outputs:
  daily:
    - type: feishu_msg
    - type: local_md
  weekly:
    - type: feishu_msg
    - type: local_md
    - type: feishu_doc   # 确认后发布

# 渠道配置
channels:
  feishu:
    msg_target: self
    doc_folder: ""

# 报告偏好
report:
  daily:
    include_stale_tasks: true
    stale_threshold_days: 7
    sync_if_stale_minutes: 60
  weekly:
    include_threads: true
    confirm_before_publish: true
    sync_if_stale_minutes: 60
```

## 数据集成

work-report-generator 只读不写。数据源独立写入 SQLite，唯一契约是符合 WorkItem Schema。

### 接入新数据源

1. 读 `references/work_item_schema.md` 了解字段定义
2. 将源数据映射为 WorkItem 字典
3. 调用 `scripts/db.py` 的 `upsert_work_item()` 写入

```python
from scripts.db import upsert_work_item

item = {
    "id": "...",
    "type": "task",
    "source": "my_source",
    "source_id": "original_id",
    "title": "任务标题",
    "date": "2026-07-20",
    "status": "pending",
}
upsert_work_item(db_path, item)
```

详见 `references/data_source_guide.md`。

## 自动化

三条 WorkBuddy Automation（需另行设置）：

| 名称 | 调度 | 任务 |
|------|------|------|
| 数据同步 | 每天 17:20 | 触发数据同步 |
| 每日日报 | 工作日 8:45 | 日报模式 |
| 每周周报 | 周五 17:25 | 周报模式 |

## 参考

- WorkItem Schema: `references/work_item_schema.md`
- 数据源接入指南: `references/data_source_guide.md`
- Report DSL 定义: `references/report_dsl.md`
- 配置参考: `references/config_reference.md`
- 日报模板: `references/daily_template.md`
- 周报模板: `references/weekly_template.md`