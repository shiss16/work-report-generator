"""config.py 模块测试"""

import os
import tempfile
import pytest
import yaml
from scripts.config import load_config, validate_config, get_db_path, get_output_dir, get_obsidian_vault_path


@pytest.fixture
def workspace_dir():
    """创建临时 workspace 目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestLoadConfig:
    """行为 #9: load_config 读取并解析 YAML"""

    def test_loads_valid_config(self, workspace_dir):
        """读取有效的 config.yaml"""
        config_path = os.path.join(workspace_dir, ".workbuddy", "data", "config.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump({
                "data_sources": {"tasks": "lark_task"},
                "outputs": {"daily": [{"type": "local_md"}]},
                "report": {"daily": {"include_stale_tasks": True}},
            }, f)

        config = load_config(workspace_dir)
        assert config["data_sources"]["tasks"] == "lark_task"
        assert config["outputs"]["daily"][0]["type"] == "local_md"

    def test_returns_defaults_when_no_config(self, workspace_dir):
        """配置文件不存在时返回默认配置"""
        config = load_config(workspace_dir)
        assert "outputs" in config
        assert "report" in config

    def test_get_db_path(self, workspace_dir):
        """返回正确的数据库路径"""
        path = get_db_path(workspace_dir)
        expected = os.path.join(workspace_dir, ".workbuddy", "data", "workbuddy.db")
        assert path == expected

    def test_get_output_dir(self, workspace_dir):
        """返回正确的输出目录"""
        path = get_output_dir(workspace_dir)
        expected = os.path.join(workspace_dir, ".workbuddy", "data", "reports")
        assert path == expected

    def test_get_obsidian_vault_path_default(self, workspace_dir):
        """返回默认 vault 路径"""
        path = get_obsidian_vault_path(workspace_dir)
        expected = os.path.join(workspace_dir, "obsidian-vault")
        assert path == expected

    def test_get_obsidian_vault_path_from_config(self, workspace_dir):
        """从 config 读取自定义 vault 路径"""
        config_path = os.path.join(workspace_dir, ".workbuddy", "data", "config.yaml")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump({
                "outputs": {"daily": [{"type": "local_md"}]},
                "report": {"daily": {}},
                "channels": {
                    "obsidian": {
                        "vault_path": "my-vault"
                    }
                },
            }, f)

        path = get_obsidian_vault_path(workspace_dir)
        expected = os.path.join(workspace_dir, "my-vault")
        assert path == expected


class TestValidateConfig:
    """行为 #10: validate_config 检查必填字段"""

    def test_valid_config_passes(self):
        config = {
            "outputs": {
                "daily": [{"type": "local_md"}],
                "weekly": [{"type": "local_md"}],
            },
            "report": {"daily": {}, "weekly": {}},
        }
        errors = validate_config(config)
        assert errors == []

    def test_missing_outputs(self):
        config = {"report": {"daily": {}}}
        errors = validate_config(config)
        assert len(errors) > 0