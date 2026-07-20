# 输入数据结构

`work-report-generator` 接受的 JSON 输入格式。与 `lark-meeting-fetcher` 的输出格式一致。

## 顶层结构

```json
{
  "period": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  },
  "fetched_at": "ISO 8601 datetime (optional)",
  "summary": {
    "total": 0,
    "with_note": 0,
    "with_minutes": 0,
    "without_any": 0,
    "fetch_errors": 0
  },
  "meetings": [
    { /* Meeting 对象 */ }
  ]
}
```

## Meeting 对象（必填字段）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | string | ✅ | 日期，格式 `YYYY-MM-DD` |
| `topic` | string | ✅ | 会议主题 |
| `start_time` | string | ✅ | 开始时间，格式 `HH:MM` |
| `end_time` | string | — | 结束时间 |
| `has_note` | bool | ✅ | 是否有纪要 |
| `has_minutes` | bool | ✅ | 是否有妙记 |
| `fetch_status` | string | ✅ | 获取状态：`ok` / `no_note` / `missing_scope` / `fetch_error` / `empty_content` |

## Meeting 对象（可选字段，用于报告内容）

| 字段 | 类型 | 说明 |
|------|------|------|
| `meeting_id` | string | 会议 ID |
| `organizer` | string | 组织者 |
| `participants` | string[] | 参会人列表 |
| `ai_summary` | string | AI 纪要内容 |
| `todos` | object[] | 待办列表 |
| `todos[].content` | string | 待办内容 |
| `todos[].assignee` | string | 负责人 |
| `note_doc_token` | string | 纪要文档 token |
| `error_message` | string | 错误信息 |

## 最小可用输入示例

```json
{
  "period": {"start": "2026-06-17", "end": "2026-06-17"},
  "meetings": [
    {
      "date": "2026-06-17",
      "topic": "项目早会",
      "start_time": "09:00",
      "end_time": "09:30",
      "has_note": true,
      "has_minutes": false,
      "fetch_status": "ok",
      "ai_summary": "讨论了日报上线计划和接口开发进度。"
    }
  ]
}
```

## 扩展其他数据源

非飞书会议的数据源，只需将数据映射为上述 Meeting 结构即可。
例如 TAPD 任务可映射为：

```json
{
  "date": "2026-06-17",
  "topic": "TAPD: 修复登录页样式问题",
  "start_time": "全天",
  "has_note": false,
  "has_minutes": false,
  "fetch_status": "ok",
  "ai_summary": "完成登录页 CSS 修复，已提交 code review。"
}
```