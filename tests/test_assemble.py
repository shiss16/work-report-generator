"""assemble.py + render 模块测试"""

import sqlite3
import uuid
import os
import pytest
from scripts.db import init_db
from scripts.assemble import assemble_daily, assemble_weekly
from scripts.render.daily import DailyRenderer
from scripts.render.weekly import WeeklyRenderer
from scripts.render.markdown_output import save_to_local
from scripts.render.feishu_output import (
    build_feishu_message_prompt,
    build_feishu_doc_prompt,
)


@pytest.fixture
def populated_db(db_path):
    """预填充测试数据"""
    init_db(db_path)

    items = [
        # 会议
        ("m1", "meeting", "lark_vc", "vc_1", "项目早会", None, None,
         "2026-07-20", "09:00", "09:30", "ok", "讨论了进度",
         '[{"content": "完成接口开发", "assignee": "张三"}]', "2026-07-20T00:00:00+00:00"),
        ("m2", "meeting", "lark_vc", "vc_2", "需求评审", None, None,
         "2026-07-20", "14:00", "15:00", "no_note", None, None,
         "2026-07-20T00:00:00+00:00"),
        # 任务
        ("t1", "task", "lark_task", "task_1", "完成 XX 模块开发", "completed", "XX平台",
         "2026-07-20", None, None, None, None, None, "2026-07-20T00:00:00+00:00"),
        ("t2", "task", "lark_task", "task_2", "方案评审", "pending", "XX平台",
         "2026-07-20", None, None, None, None, None, "2026-07-20T00:00:00+00:00"),
    ]

    for item in items:
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO work_items (id, type, source, source_id, title, status,
                project_name, date, start_time, end_time, fetch_status,
                ai_summary, todos, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, item)
        conn.commit()
        conn.close()

    return db_path


@pytest.fixture
def default_config():
    return {
        "report": {
            "daily": {
                "include_stale_tasks": True,
                "stale_threshold_days": 7,
                "max_items_per_section": 20,
            },
            "weekly": {
                "include_threads": True,
                "confirm_before_publish": True,
            },
        },
        "outputs": {
            "daily": [{"type": "local_md"}],
            "weekly": [{"type": "local_md"}],
        },
    }


class TestAssembleDaily:
    """行为 #16: assemble_daily 产出日报 DSL"""

    def test_daily_structure(self, populated_db, default_config):
        report = assemble_daily(populated_db, "2026-07-20", default_config)
        assert report["meta"]["report_type"] == "daily"
        # 7/20 是周一，回溯到上周五 7/17
        assert report["meta"]["period"]["start"] == "2026-07-17"
        assert report["meta"]["period"]["end"] == "2026-07-20"
        assert len(report["daily_items"]) == 1
        day = report["daily_items"][0]
        assert len(day["meetings"]) == 2
        assert len(day["tasks_completed"]) == 1
        assert len(day["tasks_pending"]) == 1


class TestAssembleWeekly:
    """行为 #17: assemble_weekly 产出周报 DSL"""

    def test_weekly_structure(self, populated_db, default_config):
        report = assemble_weekly(populated_db, "2026-07-20", "2026-07-20", default_config)
        assert report["meta"]["report_type"] == "weekly"
        assert "stats" in report
        assert "threads" in report


class TestDailyRenderer:
    """行为 #18: DailyRenderer 渲染日报 Markdown"""

    def test_renders_daily_markdown(self, populated_db, default_config):
        report = assemble_daily(populated_db, "2026-07-20", default_config)
        renderer = DailyRenderer()
        md = renderer.render(report, default_config)

        assert "2026-07-20" in md
        assert "项目早会" in md
        assert "完成 XX 模块开发" in md
        assert "方案评审" in md


class TestWeeklyRenderer:
    """行为 #19: WeeklyRenderer 渲染周报 Markdown"""

    def test_renders_weekly_markdown(self, populated_db, default_config):
        report = assemble_weekly(populated_db, "2026-07-20", "2026-07-20", default_config)
        renderer = WeeklyRenderer()
        md = renderer.render(report, default_config)

        assert "工作内容报告" in md
        assert "项目早会" in md


class TestMarkdownOutput:
    """行为 #20: save_to_local 保存到文件"""

    def test_saves_to_file(self, tmp_path):
        content = "# 测试\n内容"
        path = save_to_local(content, str(tmp_path / "test.md"))
        assert path == str(tmp_path / "test.md")
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == content


class TestAssembleWeeklyThreadsOverride:
    """行为 #21: assemble_weekly 接受 threads 参数并返回"""

    def test_threads_override(self, populated_db, default_config):
        custom_threads = [
            {"theme": "AI 平台建设", "summary": "完成了模型部署和接口联调。"},
            {"theme": "数据治理", "summary": "制定了数据质量标准和监控方案。"},
        ]
        report = assemble_weekly(
            populated_db, "2026-07-20", "2026-07-20",
            default_config, threads=custom_threads
        )
        assert report["threads"] == custom_threads
        assert len(report["threads"]) == 2
        assert report["threads"][0]["theme"] == "AI 平台建设"


class TestFeishuOutput:
    """行为 #22-23: feishu_output 生成正确结构"""

    def test_message_prompt(self):
        config = {"channels": {"feishu": {"msg_target": "self"}}}
        result = build_feishu_message_prompt("# 日报\n内容", config)
        assert result["action"] == "send_message"
        assert result["skill"] == "lark-im"
        assert result["target"] == "self"
        assert "# 日报" in result["content"]

    def test_doc_prompt(self):
        config = {"channels": {"feishu": {"doc_folder": "folder_123"}}}
        result = build_feishu_doc_prompt("# 周报\n内容", "2026-07-20 周报", config)
        assert result["action"] == "create_doc"
        assert result["skill"] == "lark-doc"
        assert result["title"] == "2026-07-20 周报"
        assert result["folder"] == "folder_123"


class TestCLI:
    """行为 #24-25: CLI 端到端"""

    def test_cli_daily(self, populated_db, default_config, tmp_path):
        """CLI daily 模式端到端"""
        import subprocess

        # 创建临时 config
        config_dir = tmp_path / ".workbuddy" / "data"
        config_dir.mkdir(parents=True)
        import yaml
        with open(config_dir / "config.yaml", "w") as f:
            yaml.dump(default_config, f)

        # 复制数据库到临时 workspace
        db_dest = str(config_dir / "workbuddy.db")
        import shutil
        shutil.copy(populated_db, db_dest)

        result = subprocess.run([
            "D:/Users/148618/AppData/Local/Programs/Python/Python314/python.exe",
            "scripts/cli.py", "daily",
            "--workspace", str(tmp_path),
            "--date", "2026-07-20",
        ], capture_output=True, text=True, cwd="D:/Users/148618/.workbuddy/skills/work-report-generator")

        assert result.returncode == 0
        assert "项目早会" in result.stdout
        assert "完成 XX 模块开发" in result.stdout

    def test_cli_weekly(self, populated_db, default_config, tmp_path):
        """CLI weekly 模式端到端"""
        import subprocess

        config_dir = tmp_path / ".workbuddy" / "data"
        config_dir.mkdir(parents=True)
        import yaml
        with open(config_dir / "config.yaml", "w") as f:
            yaml.dump(default_config, f)

        db_dest = str(config_dir / "workbuddy.db")
        import shutil
        shutil.copy(populated_db, db_dest)

        result = subprocess.run([
            "D:/Users/148618/AppData/Local/Programs/Python/Python314/python.exe",
            "scripts/cli.py", "weekly",
            "--workspace", str(tmp_path),
            "--start", "2026-07-20",
            "--end", "2026-07-20",
        ], capture_output=True, text=True, cwd="D:/Users/148618/.workbuddy/skills/work-report-generator")

        assert result.returncode == 0
        assert "工作内容报告" in result.stdout
        assert "项目早会" in result.stdout