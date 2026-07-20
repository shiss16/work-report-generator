"""查询引擎 — 按时间/类型/项目/状态查询"""

import sqlite3
from datetime import datetime, timezone, timedelta


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def query_work_items(
    db_path: str,
    start_date: str,
    end_date: str,
    types: list[str] = None,
    status: str = None,
    project_name: str = None,
) -> list[dict]:
    """按时间范围+条件查询 WorkItem 列表"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    sql = "SELECT * FROM work_items WHERE date >= ? AND date <= ?"
    params = [start_date, end_date]

    if types:
        placeholders = ",".join("?" * len(types))
        sql += f" AND type IN ({placeholders})"
        params.extend(types)

    if status:
        sql += " AND status = ?"
        params.append(status)

    if project_name:
        sql += " AND project_name = ?"
        params.append(project_name)

    sql += " ORDER BY date, start_time, title"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def query_meetings_with_status(
    db_path: str, start_date: str, end_date: str
) -> list[dict]:
    """查询会议列表，含 fetch_status 统计"""
    return query_work_items(db_path, start_date, end_date, types=["meeting"])


def query_completed_tasks(
    db_path: str, start_date: str, end_date: str
) -> list[dict]:
    """查询已完成任务（按 updated_at 在范围内）"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT * FROM work_items WHERE type = 'task' AND status = 'completed' "
        "AND updated_at >= ? AND updated_at < ? ORDER BY updated_at DESC",
        (f"{start_date}T00:00:00", f"{end_date}T23:59:59")
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def query_pending_tasks(db_path: str) -> list[dict]:
    """查询所有未完成的任务"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT * FROM work_items WHERE type = 'task' "
        "AND status IN ('pending', 'in_progress') ORDER BY date, title"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def query_stale_tasks(db_path: str, threshold_days: int = 7) -> list[dict]:
    """查询超期未更新的僵尸任务"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    stale_date = (datetime.now(timezone.utc) - timedelta(days=threshold_days)).isoformat()

    rows = conn.execute(
        "SELECT * FROM work_items WHERE type = 'task' "
        "AND status IN ('pending', 'in_progress') "
        "AND updated_at < ? ORDER BY updated_at",
        (stale_date,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def query_summary(db_path: str, start_date: str, end_date: str) -> dict:
    """查询概览统计"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 会议统计
    meetings = conn.execute(
        "SELECT fetch_status, date FROM work_items "
        "WHERE type = 'meeting' AND date >= ? AND date <= ?",
        (start_date, end_date)
    ).fetchall()

    total_meetings = len(meetings)
    with_note = sum(1 for m in meetings if m["fetch_status"] == "ok")
    with_minutes = sum(1 for m in meetings if m["fetch_status"] == "ok")
    without_any = sum(1 for m in meetings if m["fetch_status"] == "no_note")
    fetch_errors = sum(1 for m in meetings if m["fetch_status"] == "fetch_error")

    # 任务统计
    total_tasks = conn.execute(
        "SELECT COUNT(*) FROM work_items WHERE type = 'task' "
        "AND date >= ? AND date <= ?",
        (start_date, end_date)
    ).fetchone()[0]

    completed_tasks = conn.execute(
        "SELECT COUNT(*) FROM work_items WHERE type = 'task' "
        "AND status = 'completed' AND date >= ? AND date <= ?",
        (start_date, end_date)
    ).fetchone()[0]

    pending_tasks = conn.execute(
        "SELECT COUNT(*) FROM work_items WHERE type = 'task' "
        "AND status IN ('pending', 'in_progress')"
    ).fetchone()[0]

    stale_tasks = len(query_stale_tasks(db_path))

    # 最忙日
    date_counts = {}
    for m in meetings:
        date_counts[m["date"]] = date_counts.get(m["date"], 0) + 1

    busiest_day = max(date_counts, key=date_counts.get) if date_counts else None
    busiest_count = date_counts.get(busiest_day, 0) if busiest_day else 0

    conn.close()

    return {
        "total_meetings": total_meetings,
        "with_note": with_note,
        "with_minutes": with_minutes,
        "without_any": without_any,
        "fetch_errors": fetch_errors,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "stale_tasks": stale_tasks,
        "busiest_day": busiest_day,
        "busiest_count": busiest_count,
    }