"""query.py 模块测试"""

import sqlite3
import uuid
import pytest
from scripts.db import init_db, upsert_work_item
from scripts.query import (
    query_work_items,
    query_meetings_with_status,
    query_completed_tasks,
    query_pending_tasks,
    query_stale_tasks,
    query_summary,
)


@pytest.fixture
def populated_db(db_path):
    """预填充测试数据"""
    init_db(db_path)

    # 3 场会议：2 天
    meetings = [
        {
            "id": "m1", "type": "meeting", "source": "lark_vc",
            "source_id": "vc_1", "title": "项目早会",
            "date": "2026-07-20", "start_time": "09:00", "end_time": "09:30",
            "fetch_status": "ok", "ai_summary": "讨论了进度",
            "todos": '[{"content": "完成接口开发", "assignee": "张三"}]',
        },
        {
            "id": "m2", "type": "meeting", "source": "lark_vc",
            "source_id": "vc_2", "title": "需求评审",
            "date": "2026-07-20", "start_time": "14:00", "end_time": "15:00",
            "fetch_status": "no_note",
        },
        {
            "id": "m3", "type": "meeting", "source": "lark_vc",
            "source_id": "vc_3", "title": "周会",
            "date": "2026-07-21", "start_time": "10:00", "end_time": "11:00",
            "fetch_status": "ok", "ai_summary": "周会总结",
        },
    ]

    # 5 个任务
    tasks = [
        {
            "id": "t1", "type": "task", "source": "lark_task",
            "source_id": "task_1", "title": "完成 XX 模块开发",
            "date": "2026-07-20", "status": "completed", "project_name": "XX平台",
        },
        {
            "id": "t2", "type": "task", "source": "lark_task",
            "source_id": "task_2", "title": "方案评审",
            "date": "2026-07-20", "status": "pending", "project_name": "XX平台",
        },
        {
            "id": "t3", "type": "task", "source": "lark_task",
            "source_id": "task_3", "title": "代码 review",
            "date": "2026-07-20", "status": "pending", "project_name": "YY项目",
        },
        {
            "id": "t4", "type": "task", "source": "lark_task",
            "source_id": "task_4", "title": "发布上线",
            "date": "2026-07-21", "status": "completed",
        },
        {
            "id": "t5", "type": "task", "source": "lark_task",
            "source_id": "task_5", "title": "旧需求调研",
            "date": "2026-07-01", "status": "pending",
            "updated_at": "2026-07-01T00:00:00+00:00",  # 超期
        },
    ]

    for item in meetings + tasks:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO work_items (id, type, source, source_id, title, status,
                project_name, date, start_time, end_time, fetch_status,
                ai_summary, todos, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["id"], item["type"], item["source"], item.get("source_id"),
            item["title"], item.get("status"), item.get("project_name"),
            item["date"], item.get("start_time"), item.get("end_time"),
            item.get("fetch_status"), item.get("ai_summary"), item.get("todos"),
            item.get("updated_at", "2026-07-20T00:00:00+00:00"),
        ))
        conn.commit()
        conn.close()

    return db_path


class TestQueryWorkItems:
    """行为 #12: query_work_items 按日期范围和条件查询"""

    def test_query_by_date_range(self, populated_db):
        """按日期范围查询"""
        items = query_work_items(populated_db, "2026-07-20", "2026-07-20")
        assert len(items) == 5  # 3 meetings + 2 tasks on 7/20

    def test_filter_by_type(self, populated_db):
        """按类型过滤"""
        items = query_work_items(populated_db, "2026-07-20", "2026-07-21", types=["meeting"])
        assert len(items) == 3
        assert all(i["type"] == "meeting" for i in items)

    def test_filter_by_status(self, populated_db):
        """按状态过滤"""
        items = query_work_items(populated_db, "2026-07-20", "2026-07-21", status="completed")
        assert len(items) == 2  # t1, t4

    def test_filter_by_project(self, populated_db):
        """按项目名过滤"""
        items = query_work_items(populated_db, "2026-07-20", "2026-07-20", project_name="XX平台")
        assert len(items) == 2  # t1, t2


class TestMeetingQueries:
    """行为 #13: query_meetings_with_status"""

    def test_meetings_with_status(self, populated_db):
        meetings = query_meetings_with_status(populated_db, "2026-07-20", "2026-07-21")
        assert len(meetings) == 3
        assert meetings[0]["title"] == "项目早会"
        assert meetings[0]["fetch_status"] == "ok"


class TestTaskQueries:
    """行为 #14: 任务查询函数"""

    def test_completed_tasks(self, populated_db):
        tasks = query_completed_tasks(populated_db, "2026-07-20", "2026-07-21")
        assert len(tasks) == 2

    def test_pending_tasks(self, populated_db):
        tasks = query_pending_tasks(populated_db)
        assert len(tasks) == 3  # t2, t3, t5

    def test_stale_tasks(self, populated_db):
        # t5 的 updated_at 是 7/1，超过 7 天
        tasks = query_stale_tasks(populated_db, threshold_days=7)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "旧需求调研"


class TestQuerySummary:
    """行为 #15: query_summary 概览统计"""

    def test_summary(self, populated_db):
        stats = query_summary(populated_db, "2026-07-20", "2026-07-21")
        assert stats["total_meetings"] == 3
        assert stats["with_note"] == 2
        assert stats["without_any"] == 1  # m2 has no_note
        assert stats["total_tasks"] == 4  # t1-t4 within range, t5 on 7/1
        assert stats["completed_tasks"] == 2
        assert stats["pending_tasks"] == 3  # all pending tasks (including t5)
        assert stats["busiest_day"] == "2026-07-20"