"""数据库工具模块 — SQLite 连接管理、初始化、upsert API"""

import sqlite3
from datetime import datetime, timezone


def get_connection(db_path: str) -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """初始化数据库（建表），幂等"""
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS work_items (
            id          TEXT PRIMARY KEY,
            type        TEXT NOT NULL,
            source      TEXT NOT NULL,
            source_id   TEXT,
            title       TEXT NOT NULL,
            status      TEXT,
            project_name TEXT,
            date        TEXT NOT NULL,
            start_time  TEXT,
            end_time    TEXT,
            participants TEXT,
            ai_summary  TEXT,
            todos       TEXT,
            fetch_status TEXT,
            error_message TEXT,
            extra       TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_work_items_date ON work_items(date);
        CREATE INDEX IF NOT EXISTS idx_work_items_type ON work_items(type);
        CREATE INDEX IF NOT EXISTS idx_work_items_status ON work_items(status);
        CREATE INDEX IF NOT EXISTS idx_work_items_project ON work_items(project_name);
        CREATE INDEX IF NOT EXISTS idx_work_items_source ON work_items(source);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_work_items_source_id
            ON work_items(source, source_id) WHERE source_id IS NOT NULL;

        CREATE TABLE IF NOT EXISTS projects (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE,
            status      TEXT DEFAULT '进行中',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sync_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL,
            started_at  TEXT NOT NULL,
            finished_at TEXT,
            new_count   INTEGER DEFAULT 0,
            updated_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'running'
        );

        CREATE TABLE IF NOT EXISTS reports (
            id          TEXT PRIMARY KEY,
            report_type TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end   TEXT NOT NULL,
            status      TEXT DEFAULT 'draft',
            content     TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            confirmed_at TEXT
        );
    """)
    conn.close()


def upsert_work_item(db_path: str, item: dict) -> str:
    """写入或更新一条 WorkItem（按 source+source_id 去重），返回 id"""
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()

    source = item["source"]
    source_id = item.get("source_id")

    if source_id:
        existing = conn.execute(
            "SELECT id FROM work_items WHERE source = ? AND source_id = ?",
            (source, source_id)
        ).fetchone()

        if existing:
            # 更新已存在的记录
            conn.execute("""
                UPDATE work_items
                SET title = ?, status = ?, project_name = ?, date = ?,
                    ai_summary = ?, todos = ?, fetch_status = ?,
                    error_message = ?, extra = ?, updated_at = ?
                WHERE id = ?
            """, (
                item.get("title"),
                item.get("status"),
                item.get("project_name"),
                item.get("date"),
                item.get("ai_summary"),
                item.get("todos"),
                item.get("fetch_status"),
                item.get("error_message"),
                item.get("extra"),
                now,
                existing[0],
            ))
            conn.commit()
            conn.close()
            return existing[0]

    # 插入新记录
    conn.execute("""
        INSERT INTO work_items (id, type, source, source_id, title, status,
            project_name, date, start_time, end_time, participants,
            ai_summary, todos, fetch_status, error_message, extra)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["id"],
        item["type"],
        item["source"],
        item.get("source_id"),
        item["title"],
        item.get("status"),
        item.get("project_name"),
        item["date"],
        item.get("start_time"),
        item.get("end_time"),
        item.get("participants"),
        item.get("ai_summary"),
        item.get("todos"),
        item.get("fetch_status"),
        item.get("error_message"),
        item.get("extra"),
    ))
    conn.commit()
    conn.close()
    return item["id"]


# ---- 批量操作 ----

def upsert_work_items(db_path: str, items: list[dict]) -> int:
    """批量写入/更新，返回变更数"""
    count = 0
    for item in items:
        upsert_work_item(db_path, item)
        count += 1
    return count


# ---- 同步日志 ----

def start_sync(db_path: str, source: str) -> int:
    """开始一次同步，写入 sync_log，返回 log_id"""
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO sync_log (source, started_at) VALUES (?, ?)",
        (source, now)
    )
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


def finish_sync(db_path: str, log_id: int, new: int, updated: int,
                errors: int, status: str = "ok") -> None:
    """完成同步，更新 sync_log"""
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE sync_log SET finished_at = ?, new_count = ?, updated_count = ?, "
        "error_count = ?, status = ? WHERE id = ?",
        (now, new, updated, errors, status, log_id)
    )
    conn.commit()
    conn.close()


def get_last_sync_time(db_path: str, source: str) -> str | None:
    """获取上次同步完成时间"""
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT finished_at FROM sync_log WHERE source = ? AND status = 'ok' "
        "ORDER BY finished_at DESC LIMIT 1",
        (source,)
    ).fetchone()
    conn.close()
    return row[0] if row else None


# ---- 项目维护 ----

def add_project(db_path: str, name: str, status: str = "进行中") -> str:
    """添加项目，返回 id"""
    import uuid
    conn = sqlite3.connect(db_path)
    project_id = uuid.uuid4().hex[:8]
    conn.execute(
        "INSERT INTO projects (id, name, status) VALUES (?, ?, ?)",
        (project_id, name, status)
    )
    conn.commit()
    conn.close()
    return project_id


def get_projects(db_path: str) -> list[dict]:
    """获取所有项目"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM projects ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_project_status(db_path: str, project_id: str, status: str) -> None:
    """更新项目状态"""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE projects SET status = ? WHERE id = ?",
        (status, project_id)
    )
    conn.commit()
    conn.close()


# ---- 报告管理 ----

def save_report(db_path: str, report: dict) -> str:
    """保存报告草稿，返回 id"""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO reports (id, report_type, period_start, period_end, content) "
        "VALUES (?, ?, ?, ?, ?)",
        (report["id"], report["report_type"], report["period_start"],
         report["period_end"], report.get("content"))
    )
    conn.commit()
    conn.close()
    return report["id"]


def confirm_report(db_path: str, report_id: str) -> None:
    """确认报告"""
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE reports SET status = 'confirmed', confirmed_at = ? WHERE id = ?",
        (now, report_id)
    )
    conn.commit()
    conn.close()


def get_report(db_path: str, report_id: str) -> dict | None:
    """获取报告详情"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    return dict(row) if row else None