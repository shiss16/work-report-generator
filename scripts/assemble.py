"""组装引擎 — 产出 Report DSL"""

from datetime import datetime, timezone, timedelta
from scripts.query import (
    query_meetings_with_status,
    query_completed_tasks,
    query_pending_tasks,
    query_stale_tasks,
    query_summary,
)


def assemble_daily(db_path: str, target_date: str, config: dict) -> dict:
    """组装日报 DSL"""
    report_cfg = config.get("report", {}).get("daily", {})

    # 如果是周一，回溯到上周五
    target_dt = datetime.fromisoformat(target_date)
    if target_dt.weekday() == 0:
        start_date = (target_dt - timedelta(days=3)).strftime("%Y-%m-%d")
    else:
        start_date = target_date

    now = datetime.now(timezone.utc).isoformat()
    meetings = query_meetings_with_status(db_path, start_date, target_date)
    completed = query_completed_tasks(db_path, start_date, target_date)
    pending = query_pending_tasks(db_path)
    stale = query_stale_tasks(db_path, report_cfg.get("stale_threshold_days", 7))
    stats = query_summary(db_path, start_date, target_date)

    # 按日期分组
    days = {}
    for m in meetings:
        d = m["date"]
        if d not in days:
            days[d] = {"date": d, "meetings": [], "tasks_completed": [], "tasks_pending": []}
        days[d]["meetings"].append(m)

    for t in completed:
        d = t["date"]
        if d not in days:
            days[d] = {"date": d, "meetings": [], "tasks_completed": [], "tasks_pending": []}
        days[d]["tasks_completed"].append(t)

    for t in pending:
        d = t["date"]
        if d not in days:
            days[d] = {"date": d, "meetings": [], "tasks_completed": [], "tasks_pending": []}
        days[d]["tasks_pending"].append(t)

    # 添加星期
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    daily_items = []
    for d in sorted(days.keys()):
        dt = datetime.fromisoformat(d)
        days[d]["day_of_week"] = day_names[dt.weekday()]
        daily_items.append(days[d])

    return {
        "meta": {
            "report_type": "daily",
            "period": {"start": start_date, "end": target_date},
            "generated_at": now,
        },
        "stats": stats,
        "daily_items": daily_items,
        "stale_tasks": [
            {"title": t["title"], "project_name": t.get("project_name", ""),
             "days_stale": (datetime.now(timezone.utc) - datetime.fromisoformat(t["updated_at"])).days}
            for t in stale
        ],
    }


def assemble_weekly(db_path: str, start_date: str, end_date: str,
                    config: dict, threads: list = None) -> dict:
    """组装周报 DSL

    Args:
        threads: 可选，由外部（如 LLM Agent）传入的工作脉络列表。
                 格式: [{"theme": "...", "summary": "..."}]
                 不传则自动基于项目聚合。
    """
    now = datetime.now(timezone.utc).isoformat()
    meetings = query_meetings_with_status(db_path, start_date, end_date)
    completed = query_completed_tasks(db_path, start_date, end_date)
    pending = query_pending_tasks(db_path)
    stale = query_stale_tasks(db_path)
    stats = query_summary(db_path, start_date, end_date)

    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    days = {}
    for m in meetings:
        d = m["date"]
        if d not in days:
            days[d] = {"date": d, "meetings": [], "tasks_completed": [], "tasks_pending": []}
        days[d]["meetings"].append(m)

    for t in completed:
        d = t["date"]
        if d not in days:
            days[d] = {"date": d, "meetings": [], "tasks_completed": [], "tasks_pending": []}
        days[d]["tasks_completed"].append(t)

    for t in pending:
        d = t["date"]
        if d not in days:
            days[d] = {"date": d, "meetings": [], "tasks_completed": [], "tasks_pending": []}
        days[d]["tasks_pending"].append(t)

    daily_items = []
    for d in sorted(days.keys()):
        dt = datetime.fromisoformat(d)
        days[d]["day_of_week"] = day_names[dt.weekday()]
        daily_items.append(days[d])

    # 工作脉络：优先使用外部传入的 threads，否则按项目聚合
    if threads is not None:
        result_threads = threads
    else:
        project_topics = {}
        for m in meetings:
            if m.get("project_name"):
                proj = m["project_name"]
                if proj not in project_topics:
                    project_topics[proj] = []
                project_topics[proj].append(m["title"])

        result_threads = []
        for proj, topics in project_topics.items():
            result_threads.append({
                "theme": proj,
                "summary": f"本周涉及 {len(topics)} 场会议",
                "related_items": [],
            })

    return {
        "meta": {
            "report_type": "weekly",
            "period": {"start": start_date, "end": end_date},
            "generated_at": now,
        },
        "stats": stats,
        "daily_items": daily_items,
        "threads": result_threads,
        "stale_tasks": [
            {"title": t["title"], "project_name": t.get("project_name", ""),
             "days_stale": (datetime.now(timezone.utc) - datetime.fromisoformat(t["updated_at"])).days}
            for t in stale
        ],
    }