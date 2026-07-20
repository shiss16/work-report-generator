# WorkItem 数据模型定义

`work-report-generator` 消费的数据模型。所有数据源写入 SQLite 时需遵循此 Schema。

## 必填字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | TEXT | UUID，唯一标识 | `a1b2c3d4e5f6` |
| `type` | TEXT | 工作项类型 | `task` / `meeting` |
| `source` | TEXT | 来源系统标识 | `lark_task` / `lark_vc` / `tapd` / `manual` |
| `title` | TEXT | 标题 | `修复登录页样式问题` |
| `date` | TEXT | 关联日期 YYYY-MM-DD | `2026-07-20` |

## 可选字段

| 字段 | 类型 | 适用 type | 说明 |
|------|------|:--:|------|
| `source_id` | TEXT | 所有 | 源系统原始 ID，**强烈建议填写**，用于去重和增量更新 |
| `status` | TEXT | task | `pending` / `in_progress` / `completed` |
| `project_name` | TEXT | 所有 | 所属项目名称 |
| `start_time` | TEXT | meeting | 开始时间 `HH:MM` |
| `end_time` | TEXT | meeting | 结束时间 |
| `participants` | TEXT | meeting | JSON 数组 `["张三", "李四"]` |
| `ai_summary` | TEXT | meeting/task | AI 纪要或任务描述原文 |
| `todos` | TEXT | meeting/task | JSON 数组 `[{"content": "...", "assignee": "..."}]` |
| `fetch_status` | TEXT | meeting | `ok` / `no_note` / `missing_scope` / `fetch_error` / `empty_content` |
| `error_message` | TEXT | 所有 | 错误信息 |
| `extra` | TEXT | 所有 | JSON 扩展字段，放类型特有属性，自由扩展 |

## fetch_status 取值

| 值 | 含义 |
|----|------|
| `ok` | 成功获取全部数据 |
| `no_note` | 无纪要/无妙记 |
| `missing_scope` | 缺少权限 |
| `fetch_error` | 获取过程中出错 |
| `empty_content` | 有纪要但内容为空 |

## 去重规则

`source + source_id` 组合唯一（数据库有 UNIQUE INDEX 保证）：

- **不存在** → INSERT 新行
- **已存在** → UPDATE 更新以下可变字段：`title`, `status`, `project_name`, `date`, `ai_summary`, `todos`, `fetch_status`, `error_message`, `extra`, `updated_at`

## 示例

### task 类型

```json
{
  "id": "a1b2c3d4",
  "type": "task",
  "source": "lark_task",
  "source_id": "task_12345",
  "title": "完成 XX 模块开发",
  "date": "2026-07-20",
  "status": "completed",
  "project_name": "XX平台"
}
```

### meeting 类型

```json
{
  "id": "b2c3d4e5",
  "type": "meeting",
  "source": "lark_vc",
  "source_id": "vc_67890",
  "title": "项目早会",
  "date": "2026-07-20",
  "start_time": "09:00",
  "end_time": "09:30",
  "participants": "[\"张三\", \"李四\"]",
  "ai_summary": "讨论了进度安排和接口开发计划。",
  "todos": "[{\"content\": \"完成接口开发\", \"assignee\": \"张三\"}]",
  "fetch_status": "ok"
}
```

### 扩展类型示例

```json
{
  "id": "c3d4e5f6",
  "type": "code_commit",
  "source": "github",
  "source_id": "commit_abc123",
  "title": "fix: 修复登录页样式问题",
  "date": "2026-07-20",
  "project_name": "XX平台",
  "extra": "{\"repo\": \"frontend\", \"branch\": \"main\", \"files_changed\": 3}"
}
```