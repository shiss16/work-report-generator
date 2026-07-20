"""配置管理 — config.yaml 读取与校验"""

import os
import yaml


DEFAULT_CONFIG = {
    "data_sources": {
        "tasks": "lark_task",
        "calendar": "lark_calendar",
        "meetings": "lark_vc",
    },
    "outputs": {
        "daily": [
            {"type": "feishu_msg"},
            {"type": "local_md"},
        ],
        "weekly": [
            {"type": "feishu_msg"},
            {"type": "local_md"},
            {"type": "feishu_doc"},
        ],
    },
    "channels": {
        "feishu": {
            "msg_target": "self",
            "doc_folder": "",
        }
    },
    "report": {
        "daily": {
            "include_stale_tasks": True,
            "stale_threshold_days": 7,
            "max_items_per_section": 20,
            "sync_if_stale_minutes": 60,
        },
        "weekly": {
            "include_threads": True,
            "include_charts": False,
            "confirm_before_publish": True,
            "sync_if_stale_minutes": 60,
        },
    },
    "automation": {
        "sync": {"schedule": "每天 17:20", "scope_days": 3},
        "daily_report": {"schedule": "工作日 8:45"},
        "weekly_report": {"schedule": "周五 17:25", "scope_days": 7},
    },
}


def load_config(workspace_path: str) -> dict:
    """加载并校验 config.yaml，缺失文件返回默认配置"""
    config_path = os.path.join(workspace_path, ".workbuddy", "data", "config.yaml")

    if not os.path.exists(config_path):
        return dict(DEFAULT_CONFIG)

    with open(config_path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    return _deep_merge(dict(DEFAULT_CONFIG), user_config)


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典"""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def validate_config(config: dict) -> list[str]:
    """校验配置完整性，返回错误列表"""
    errors = []

    if "outputs" not in config:
        errors.append("缺少 outputs 配置")
        return errors

    if "daily" not in config["outputs"]:
        errors.append("outputs 缺少 daily 配置")

    if "weekly" not in config["outputs"]:
        errors.append("outputs 缺少 weekly 配置")

    if "report" not in config:
        errors.append("缺少 report 配置")

    return errors


def get_db_path(workspace_path: str) -> str:
    """获取数据库路径"""
    return os.path.join(workspace_path, ".workbuddy", "data", "workbuddy.db")


def get_output_dir(workspace_path: str) -> str:
    """获取输出目录"""
    return os.path.join(workspace_path, ".workbuddy", "data", "reports")