"""db.py 模块测试"""

import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from scripts.db import (
    init_db, upsert_work_item, upsert_work_items,
    start_sync, finish_sync, get_last_sync_time,
    add_project, get_projects, update_project_status,
    save_report, confirm_report, get_report,
)


class TestInitDB:
    """行为 #1: init_db 创建所有表（4 张）和索引，幂等"""

    def test_creates_all_tables(self, db_path):
        """init_db 应创建 work_items, projects, sync_log, reports 四张表"""
        init_db(db_path)

        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        conn.close()

        assert "work_items" in table_names
        assert "projects" in table_names
        assert "sync_log" in table_names
        assert "reports" in table_names

    def test_is_idempotent(self, db_path):
        """多次调用 init_db 不应报错"""
        init_db(db_path)
        init_db(db_path)  # 第二次调用
        init_db(db_path)  # 第三次调用

        # 验证表仍然存在
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        conn.close()

        assert len(tables) == 4

    def test_creates_indexes(self, db_path):
        """init_db 应创建所需索引"""
        init_db(db_path)

        conn = sqlite3.connect(db_path)
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        index_names = [i[0] for i in indexes]
        conn.close()

        assert "idx_work_items_date" in index_names
        assert "idx_work_items_type" in index_names
        assert "idx_work_items_status" in index_names
        assert "idx_work_items_project" in index_names
        assert "idx_work_items_source" in index_names


class TestUpsertWorkItem:
    """行为 #2-3: upsert_work_item 插入和更新"""

    def test_insert_new_item(self, db_path):
        """插入新记录，返回 id，数据可查询"""
        init_db(db_path)

        item = {
            "id": uuid.uuid4().hex[:12],
            "type": "task",
            "source": "lark_task",
            "source_id": "task_123",
            "title": "完成 XX 模块开发",
            "date": "2026-07-20",
            "status": "pending",
            "project_name": "XX平台",
        }
        result_id = upsert_work_item(db_path, item)

        assert result_id == item["id"]

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT * FROM work_items WHERE id = ?", (item["id"],)
        ).fetchone()
        conn.close()

        assert row is not None
        assert row[1] == "task"  # type
        assert row[2] == "lark_task"  # source
        assert row[4] == "完成 XX 模块开发"  # title

    def test_update_existing_item(self, db_path):
        """按 source+source_id 更新已存在的记录"""
        init_db(db_path)

        item = {
            "id": uuid.uuid4().hex[:12],
            "type": "task",
            "source": "lark_task",
            "source_id": "task_456",
            "title": "原始标题",
            "date": "2026-07-20",
            "status": "pending",
        }
        upsert_work_item(db_path, item)

        # 更新同一 source+source_id 的记录
        item["title"] = "更新后的标题"
        item["status"] = "completed"
        result_id = upsert_work_item(db_path, item)

        assert result_id == item["id"]

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT title, status FROM work_items WHERE id = ?", (item["id"],)
        ).fetchone()
        conn.close()

        assert row[0] == "更新后的标题"
        assert row[1] == "completed"

        # 确认只有一条记录
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM work_items").fetchone()[0]
        conn.close()
        assert count == 1


class TestBatchUpsert:
    """行为 #4: upsert_work_items 批量 upsert"""

    def test_batch_insert(self, db_path):
        """批量插入多条记录，返回变更数"""
        init_db(db_path)

        items = [
            {
                "id": uuid.uuid4().hex[:12],
                "type": "task",
                "source": "manual",
                "source_id": f"manual_{i}",
                "title": f"任务 {i}",
                "date": "2026-07-20",
            }
            for i in range(3)
        ]
        count = upsert_work_items(db_path, items)
        assert count == 3

        conn = sqlite3.connect(db_path)
        total = conn.execute("SELECT COUNT(*) FROM work_items").fetchone()[0]
        conn.close()
        assert total == 3

    def test_batch_mixed_insert_update(self, db_path):
        """批量写入：新记录插入，已有记录更新"""
        init_db(db_path)

        # 先插入一条
        existing = {
            "id": uuid.uuid4().hex[:12],
            "type": "task",
            "source": "test",
            "source_id": "exist_1",
            "title": "旧标题",
            "date": "2026-07-20",
        }
        upsert_work_item(db_path, existing)

        # 批量：一条新 + 一条更新
        existing["title"] = "新标题"
        new_item = {
            "id": uuid.uuid4().hex[:12],
            "type": "task",
            "source": "test",
            "source_id": "new_1",
            "title": "新任务",
            "date": "2026-07-20",
        }
        count = upsert_work_items(db_path, [existing, new_item])
        assert count == 2


class TestSyncLog:
    """行为 #5-6: sync_log 生命周期"""

    def test_sync_log_lifecycle(self, db_path):
        """完整的同步日志记录流程"""
        init_db(db_path)

        log_id = start_sync(db_path, "lark_vc")
        assert log_id > 0

        finish_sync(db_path, log_id, new=5, updated=2, errors=1, status="ok")

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT source, new_count, updated_count, error_count, status FROM sync_log WHERE id = ?",
            (log_id,)
        ).fetchone()
        conn.close()

        assert row[0] == "lark_vc"
        assert row[1] == 5
        assert row[2] == 2
        assert row[3] == 1
        assert row[4] == "ok"

    def test_get_last_sync_time(self, db_path):
        """查询上次同步时间"""
        init_db(db_path)

        # 无记录时返回 None
        assert get_last_sync_time(db_path, "unknown") is None

        log_id = start_sync(db_path, "lark_task")
        finish_sync(db_path, log_id, new=1, updated=0, errors=0)

        result = get_last_sync_time(db_path, "lark_task")
        assert result is not None


class TestProjects:
    """行为 #7: 项目 CRUD"""

    def test_project_crud(self, db_path):
        init_db(db_path)

        pid = add_project(db_path, "XX平台重构")
        assert pid

        projects = get_projects(db_path)
        assert len(projects) == 1
        assert projects[0]["name"] == "XX平台重构"

        update_project_status(db_path, pid, "已完结")
        projects = get_projects(db_path)
        assert projects[0]["status"] == "已完结"


class TestReports:
    """行为 #8: 报告生命周期"""

    def test_report_lifecycle(self, db_path):
        init_db(db_path)

        report_id = save_report(db_path, {
            "id": uuid.uuid4().hex[:12],
            "report_type": "daily",
            "period_start": "2026-07-20",
            "period_end": "2026-07-20",
            "content": "# 日报\n内容",
        })
        assert report_id

        report = get_report(db_path, report_id)
        assert report["status"] == "draft"
        assert report["report_type"] == "daily"

        confirm_report(db_path, report_id)
        report = get_report(db_path, report_id)
        assert report["status"] == "confirmed"
        assert report["confirmed_at"] is not None