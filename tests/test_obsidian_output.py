"""obsidian_output.py 模块测试 — TDD"""

import os
import tempfile
import pytest
from unittest import mock
from scripts.render.obsidian_output import (
    save_daily_to_obsidian,
    save_weekly_to_obsidian,
    ensure_vault_structure,
    DAILY_FRONTMATTER,
    WEEKLY_FRONTMATTER,
)


@pytest.fixture
def vault_path():
    """创建临时 Obsidian vault 目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_daily_report():
    """日报数据结构"""
    return {
        "meta": {
            "report_type": "daily",
            "period": {"start": "2026-07-21", "end": "2026-07-21"},
            "generated_at": "2026-07-21T08:45:00+08:00",
        },
        "stats": {
            "total_meetings": 2,
            "with_note": 1,
            "total_tasks": 3,
            "completed_tasks": 1,
            "pending_tasks": 2,
        },
        "daily_items": [
            {
                "date": "2026-07-21",
                "day_of_week": "周二",
                "meetings": [
                    {
                        "title": "AI平台周会",
                        "start_time": "2026-07-21T09:00:00",
                        "end_time": "2026-07-21T09:30:00",
                        "fetch_status": "ok",
                        "ai_summary": "讨论了本周迭代计划",
                        "todos": '[{"content": "完成接口开发", "assignee": "张三"}]',
                        "participants": '["张三", "李四"]',
                    }
                ],
                "tasks_completed": [
                    {"title": "数据同步模块重构", "project_name": "AI平台"},
                ],
                "tasks_pending": [
                    {"title": "TAPD接入", "project_name": "数据管道"},
                ],
            }
        ],
    }


@pytest.fixture
def sample_weekly_report():
    """周报数据结构"""
    return {
        "meta": {
            "report_type": "weekly",
            "period": {"start": "2026-07-20", "end": "2026-07-26"},
            "generated_at": "2026-07-26T17:25:00+08:00",
        },
        "stats": {
            "total_meetings": 5,
            "with_note": 3,
            "total_tasks": 8,
            "completed_tasks": 4,
            "pending_tasks": 4,
        },
        "daily_items": [],
        "threads": [
            {"theme": "AI平台迭代", "summary": "完成数据同步模块重构"},
        ],
    }


# ===== 行为 1: 写入日报到 Obsidian vault =====

class TestSaveDailyToObsidian:
    """行为 1: 写入日报到 obsidian-vault/日报/YYYY-MM-DD.md"""

    def test_creates_file_at_correct_path(self, vault_path, sample_daily_report):
        """日报文件写入正确路径"""
        markdown = "# 日报内容"
        result = save_daily_to_obsidian(vault_path, sample_daily_report, markdown)
        expected_path = os.path.join(vault_path, "日报", "2026-07-21.md")
        assert result == expected_path
        assert os.path.exists(expected_path)

    def test_includes_frontmatter(self, vault_path, sample_daily_report):
        """日报文件包含 frontmatter 元数据"""
        markdown = "# 日报内容"
        filepath = save_daily_to_obsidian(vault_path, sample_daily_report, markdown)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "---" in content
        assert "date: 2026-07-21" in content
        assert "type: daily" in content
        assert "tags:" in content

    def test_includes_wikilinks_to_projects(self, vault_path, sample_daily_report):
        """日报包含项目 wikilink"""
        markdown = "# 日报内容"
        filepath = save_daily_to_obsidian(vault_path, sample_daily_report, markdown)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "[[AI平台]]" in content
        assert "[[数据管道]]" in content

    def test_appends_markdown_after_frontmatter(self, vault_path, sample_daily_report):
        """frontmatter 之后是 markdown 正文"""
        markdown = "# 我的日报标题"
        filepath = save_daily_to_obsidian(vault_path, sample_daily_report, markdown)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        parts = content.split("---\n", 2)
        assert len(parts) >= 3
        assert markdown in parts[2]

    def test_auto_creates_daily_subdirectory(self, vault_path, sample_daily_report):
        """自动创建日报子目录"""
        markdown = "# 日报"
        # 确保目录不存在
        daily_dir = os.path.join(vault_path, "日报")
        assert not os.path.exists(daily_dir)

        save_daily_to_obsidian(vault_path, sample_daily_report, markdown)
        assert os.path.isdir(daily_dir)


# ===== 行为 2: 写入周报到 Obsidian vault =====

class TestSaveWeeklyToObsidian:
    """行为 2: 写入周报到 obsidian-vault/周报/YYYY-Www.md"""

    def test_creates_file_at_correct_path(self, vault_path, sample_weekly_report):
        """周报文件写入正确路径，使用 ISO 周次"""
        markdown = "# 周报内容"
        result = save_weekly_to_obsidian(vault_path, sample_weekly_report, markdown)
        expected_path = os.path.join(vault_path, "周报", "2026-W30.md")
        assert result == expected_path
        assert os.path.exists(expected_path)

    def test_includes_weekly_frontmatter(self, vault_path, sample_weekly_report):
        """周报文件包含 frontmatter"""
        markdown = "# 周报内容"
        filepath = save_weekly_to_obsidian(vault_path, sample_weekly_report, markdown)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "---" in content
        assert "type: weekly" in content
        assert "week: 2026-W30" in content
        assert "period_start: 2026-07-20" in content
        assert "period_end: 2026-07-26" in content


# ===== 行为 3: 自动创建 vault 目录结构 =====

class TestEnsureVaultStructure:
    """行为 3: 自动创建 vault 目录结构"""

    def test_creates_all_directories(self, vault_path):
        """创建日报/周报/项目/索引/模板 五个子目录"""
        ensure_vault_structure(vault_path)

        for subdir in ["日报", "周报", "项目", "索引", "模板"]:
            assert os.path.isdir(os.path.join(vault_path, subdir))

    def test_is_idempotent(self, vault_path):
        """幂等——重复调用不报错"""
        ensure_vault_structure(vault_path)
        ensure_vault_structure(vault_path)  # 不应抛异常


# ===== 行为 5: MOC 模板 =====

class TestMocTemplates:
    """行为 5: 创建 MOC 模板文件"""

    def test_daily_summary_template(self, vault_path):
        """日报汇总模板包含 Dataview 查询"""
        from scripts.render.obsidian_output import create_moc_templates
        create_moc_templates(vault_path)

        template_path = os.path.join(vault_path, "索引", "日报汇总.md")
        assert os.path.exists(template_path)

        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "dataview" in content
        assert "日报" in content

    def test_weekly_summary_template(self, vault_path):
        """周报汇总模板"""
        from scripts.render.obsidian_output import create_moc_templates
        create_moc_templates(vault_path)

        template_path = os.path.join(vault_path, "索引", "周报汇总.md")
        assert os.path.exists(template_path)

    def test_project_overview_template(self, vault_path):
        """项目总览模板"""
        from scripts.render.obsidian_output import create_moc_templates
        create_moc_templates(vault_path)

        template_path = os.path.join(vault_path, "索引", "项目总览.md")
        assert os.path.exists(template_path)


# ===== 行为 6: run.py 集成 obsidian 输出 =====

class TestRunIntegration:
    """行为 6: run.py 日报/周报模式自动调用 obsidian 输出"""

    def test_daily_calls_obsidian_output(self, vault_path, sample_daily_report):
        """日报模式下，配置含 obsidian_vault 时自动写入"""
        from scripts.run import run

        with mock.patch("scripts.run.load_config") as mock_load:
            with mock.patch("scripts.run.assemble_daily") as mock_assemble:
                with mock.patch("scripts.run.DailyRenderer") as mock_renderer:
                    with mock.patch("scripts.run.save_to_local") as mock_save:
                        with mock.patch("scripts.run.get_obsidian_vault_path") as mock_vault_path:
                            with mock.patch("scripts.run.save_daily_to_obsidian") as mock_obsidian:
                                with mock.patch("scripts.run.get_db_path") as mock_db:
                                    with mock.patch("scripts.run.get_output_dir") as mock_out:
                                        # 设置 mock
                                        config = {
                                            "outputs": {
                                                "daily": [
                                                    {"type": "local_md"},
                                                    {"type": "obsidian_vault"},
                                                ],
                                            },
                                            "report": {"daily": {}, "weekly": {}},
                                        }
                                        mock_load.return_value = config
                                        mock_vault_path.return_value = vault_path
                                        mock_db.return_value = ":memory:"
                                        mock_out.return_value = os.path.join(vault_path, "reports")
                                        mock_assemble.return_value = sample_daily_report
                                        mock_renderer_instance = mock.MagicMock()
                                        mock_renderer_instance.render.return_value = "# 日报"
                                        mock_renderer.return_value = mock_renderer_instance

                                        run("fake_workspace", "daily")

                                        # 验证 obsidian 输出被调用
                                        mock_obsidian.assert_called_once()
                                        call_args = mock_obsidian.call_args[0]
                                        assert call_args[0] == vault_path  # vault_path
                                        assert call_args[1] == sample_daily_report  # report
                                        assert call_args[2] == "# 日报"  # markdown

    def test_daily_skips_obsidian_when_not_configured(self, vault_path, sample_daily_report):
        """日报模式下，配置不含 obsidian_vault 时不调用"""
        from scripts.run import run

        with mock.patch("scripts.run.load_config") as mock_load:
            with mock.patch("scripts.run.assemble_daily") as mock_assemble:
                with mock.patch("scripts.run.DailyRenderer") as mock_renderer:
                    with mock.patch("scripts.run.save_to_local") as mock_save:
                        with mock.patch("scripts.run.get_obsidian_vault_path") as mock_vault_path:
                            with mock.patch("scripts.run.save_daily_to_obsidian") as mock_obsidian:
                                with mock.patch("scripts.run.get_db_path") as mock_db:
                                    with mock.patch("scripts.run.get_output_dir") as mock_out:
                                        config = {
                                            "outputs": {
                                                "daily": [{"type": "local_md"}],
                                            },
                                            "report": {"daily": {}, "weekly": {}},
                                        }
                                        mock_load.return_value = config
                                        mock_vault_path.return_value = vault_path
                                        mock_db.return_value = ":memory:"
                                        mock_out.return_value = os.path.join(vault_path, "reports")
                                        mock_assemble.return_value = sample_daily_report
                                        mock_renderer_instance = mock.MagicMock()
                                        mock_renderer_instance.render.return_value = "# 日报"
                                        mock_renderer.return_value = mock_renderer_instance

                                        run("fake_workspace", "daily")

                                        mock_obsidian.assert_not_called()

    def test_weekly_calls_obsidian_output(self, vault_path, sample_weekly_report):
        """周报模式下，配置含 obsidian_vault 时自动写入"""
        from scripts.run import run

        with mock.patch("scripts.run.load_config") as mock_load:
            with mock.patch("scripts.run.assemble_weekly") as mock_assemble:
                with mock.patch("scripts.run.WeeklyRenderer") as mock_renderer:
                    with mock.patch("scripts.run.save_to_local") as mock_save:
                        with mock.patch("scripts.run.get_obsidian_vault_path") as mock_vault_path:
                            with mock.patch("scripts.run.save_weekly_to_obsidian") as mock_obsidian:
                                with mock.patch("scripts.run.get_db_path") as mock_db:
                                    with mock.patch("scripts.run.get_output_dir") as mock_out:
                                        config = {
                                            "outputs": {
                                                "weekly": [
                                                    {"type": "local_md"},
                                                    {"type": "obsidian_vault"},
                                                ],
                                            },
                                            "report": {"daily": {}, "weekly": {}},
                                        }
                                        mock_load.return_value = config
                                        mock_vault_path.return_value = vault_path
                                        mock_db.return_value = ":memory:"
                                        mock_out.return_value = os.path.join(vault_path, "reports")
                                        mock_assemble.return_value = sample_weekly_report
                                        mock_renderer_instance = mock.MagicMock()
                                        mock_renderer_instance.render.return_value = "# 周报"
                                        mock_renderer.return_value = mock_renderer_instance

                                        run("fake_workspace", "weekly")

                                        mock_obsidian.assert_called_once()
                                        call_args = mock_obsidian.call_args[0]
                                        assert call_args[0] == vault_path
                                        assert call_args[1] == sample_weekly_report
                                        assert call_args[2] == "# 周报"