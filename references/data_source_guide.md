# 数据源接入指南

如何将新的数据源接入 work-report-generator。

## 核心原则

**work-report-generator 只读不写。** 数据源各自实现写入逻辑，唯一契约是写入的数据必须符合 WorkItem Schema。

## 接入三步法

### Step 1: 理解 Schema

阅读 `references/work_item_schema.md`，了解每个字段的含义、类型和约束。

### Step 2: 实现数据映射

将源系统的数据转换为 WorkItem 字典：

```python
import uuid

def map_source_to_workitem(raw_data: dict) -> dict:
    """将源数据映射为 WorkItem 字典"""
    return {
        "id": uuid.uuid4().hex[:12],
        "type": "task",              # 或 "meeting"，根据实际类型
        "source": "my_source",       # 来源标识，建议小写+下划线
        "source_id": raw_data["id"], # 源系统原始 ID，用于去重
        "title": raw_data["name"],
        "date": raw_data["modified"][:10],
        "status": "pending",
        "project_name": extract_project(raw_data),
        # 以下为可选字段，按需填写
        "ai_summary": raw_data.get("description"),
        "todos": None,
        "extra": json.dumps({"custom_field": "value"}),
    }
```

### Step 3: 写入 SQLite

使用 `db.py` 提供的工具函数写入：

```python
from scripts.db import upsert_work_items, start_sync, finish_sync

def sync_my_source(db_path: str):
    """同步一个数据源"""

    # 1. 开始同步，记录日志
    log_id = start_sync(db_path, "my_source")

    # 2. 拉取源数据
    raw_data_list = fetch_from_my_source()

    # 3. 映射为 WorkItem
    items = [map_source_to_workitem(d) for d in raw_data_list]

    # 4. 批量写入（自动去重）
    count = upsert_work_items(db_path, items)

    # 5. 完成同步
    finish_sync(db_path, log_id, new=count, updated=0, errors=0)
```

## 三种接入模式

### 模式 A: Python 脚本

适用于有 SDK/API 的数据源（TAPD、GitHub、Jira 等）。

```python
# tapd_sync.py
from scripts.db import init_db, upsert_work_items, start_sync, finish_sync

def sync():
    db_path = "path/to/workbuddy.db"
    init_db(db_path)

    log_id = start_sync(db_path, "tapd")
    stories = tapd_client.get_stories()
    items = [map_tapd_to_workitem(s) for s in stories]
    count = upsert_work_items(db_path, items)
    finish_sync(db_path, log_id, new=count, updated=0, errors=0)
```

### 模式 B: Agent 驱动

适用于通过 lark-cli 等命令行工具拉取的数据源（飞书会议、飞书任务）。

```python
# lark_meeting_sync.py
# 在 Agent 工作流中：
# 1. 调用 lark-cli 命令拉取数据
# 2. 调用 map_lark_meeting_to_workitem() 映射
# 3. 调用 upsert_work_items() 写入
```

### 模式 C: 手动输入

适用于用户口头记录的工作项。

Agent 解析用户输入后，直接构造 WorkItem 并写入：

```python
from scripts.db import upsert_work_item

item = {
    "id": uuid.uuid4().hex[:12],
    "type": "task",
    "source": "manual",
    "title": "完成 XX 模块开发",
    "date": "2026-07-20",
    "status": "completed",
    "project_name": "XX 平台",
}
upsert_work_item(db_path, item)
```

## db.py 工具函数参考

| 函数 | 用途 |
|------|------|
| `init_db(db_path)` | 初始化数据库（建表），幂等 |
| `upsert_work_item(db_path, item)` | 写入/更新一条记录 |
| `upsert_work_items(db_path, items)` | 批量写入/更新 |
| `start_sync(db_path, source)` | 开始同步，返回 log_id |
| `finish_sync(db_path, log_id, ...)` | 完成同步，更新日志 |
| `get_last_sync_time(db_path, source)` | 获取上次同步时间 |

## 注意事项

1. **`source` 字段**：每个数据源使用唯一的 source 标识，如 `tapd`、`github`、`lark_vc`
2. **`source_id` 字段**：强烈建议填写，用于增量去重。不填则每次全量覆盖
3. **`todos` 字段**：必须是 JSON 字符串格式的数组
4. **`participants` 字段**：必须是 JSON 字符串格式的数组
5. **同步日志**：务必使用 `start_sync`/`finish_sync` 记录，方便排查问题
6. **时间格式**：日期用 `YYYY-MM-DD`，时间用 `HH:MM`