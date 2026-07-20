# Report DSL 结构定义

Assembler 产出的中间数据结构，所有 Renderer 消费同一份 DSL。

## 顶层结构

```python
{
    "meta": {...},       # 元信息
    "stats": {...},      # 概览统计
    "daily_items": [...], # 每日详情
    "threads": [...],    # 工作脉络（周报用）
    "stale_tasks": [...] # 僵尸任务
}
```

## meta 元信息

```python
{
    "report_type": "daily",           # 'daily' | 'weekly'
    "period": {
        "start": "2026-07-20",        # 开始日期
        "end": "2026-07-20"           # 结束日期
    },
    "generated_at": "2026-07-20T08:45:00+08:00",
    "workspace": "日常工作整理"        # 可选
}
```

## stats 概览统计

```python
{
    "total_meetings": 3,     # 会议总数
    "with_note": 2,          # 有纪要
    "with_minutes": 0,       # 有妙记
    "without_any": 1,        # 无记录
    "fetch_errors": 0,       # 获取失败
    "total_tasks": 12,       # 任务总数
    "completed_tasks": 5,    # 已完成
    "pending_tasks": 7,      # 待办中
    "stale_tasks": 2,        # 僵尸任务数
    "busiest_day": "2026-07-18",  # 最忙日
    "busiest_count": 5       # 最忙日会议数
}
```

## daily_items 每日详情

```python
[
    {
        "date": "2026-07-20",
        "day_of_week": "周一",
        "meetings": [
            {
                "title": "项目早会",
                "start_time": "09:00",
                "end_time": "09:30",
                "fetch_status": "ok",
                "ai_summary": "讨论了进度...",
                "todos": [{"content": "...", "assignee": "张三"}],
                "participants": ["张三", "李四"]
            }
        ],
        "tasks_completed": [
            {"title": "完成 XX 模块开发", "project_name": "XX平台"}
        ],
        "tasks_pending": [
            {"title": "方案评审", "project_name": "XX平台"}
        ]
    }
]
```

## threads 工作脉络

```python
[
    {
        "theme": "XX平台重构",
        "summary": "本周完成了接口开发和联调，进入测试阶段。",
        "related_items": ["item_id_1", "item_id_2"]
    }
]
```

## stale_tasks 僵尸任务

```python
[
    {
        "title": "旧需求调研",
        "project_name": "YY项目",
        "days_stale": 12
    }
]
```

## Renderer 接口

所有 Renderer 实现相同的接口：

```python
class BaseRenderer:
    def render(self, report: dict, config: dict) -> str:
        """渲染报告为字符串（Markdown 等）"""
        ...
```

新增呈现方式（如 PDF、HTML）只需实现此接口，不改动其他模块。