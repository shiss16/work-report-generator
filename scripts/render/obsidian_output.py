"""Obsidian Vault 输出

将日报/周报写入 Obsidian vault，包含 frontmatter 元数据和 wikilink。
vault 位于 workspace 子目录 obsidian-vault/。
"""

import os
from datetime import date, datetime

# === 常量 ===

DAILY_FRONTMATTER = """---
date: {date}
type: daily
week: {week}
tags: [日报{project_tags}]
projects: [{project_names}]
---"""

WEEKLY_FRONTMATTER = """---
date: {start}
type: weekly
week: {week}
period_start: {start}
period_end: {end}
tags: [周报]
---"""


# === 工具函数 ===

def _extract_projects(report: dict) -> list[str]:
    """从 report DSL 中提取项目名列表（去重）"""
    projects = set()
    for day in report.get("daily_items", []):
        for t in day.get("tasks_completed", []):
            if t.get("project_name"):
                projects.add(t["project_name"])
        for t in day.get("tasks_pending", []):
            if t.get("project_name"):
                projects.add(t["project_name"])
    return sorted(projects)


def _iso_week(date_str: str) -> str:
    """返回 ISO 周次，如 '2026-W30'"""
    d = date.fromisoformat(date_str)
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _project_tags(projects: list[str]) -> str:
    """项目名列表转为 tags 字符串"""
    return ", " + ", ".join(projects) if projects else ""


def _project_names(projects: list[str]) -> str:
    """项目名列表转为 YAML 列表字符串，如 '"AI平台", "数据管道"'"""
    return ", ".join(f'"{p}"' for p in projects)


def _project_wikilinks(projects: list[str]) -> str:
    """项目名列表转为 wikilink 行，用于嵌入正文"""
    if not projects:
        return ""
    return "\n".join(f"- [[{p}]]" for p in projects)


# === 公开 API ===

def ensure_vault_structure(vault_path: str) -> None:
    """创建 vault 目录结构（幂等）"""
    for subdir in ["日报", "周报", "项目", "索引", "模板"]:
        os.makedirs(os.path.join(vault_path, subdir), exist_ok=True)


def save_daily_to_obsidian(vault_path: str, report: dict, markdown: str) -> str:
    """将日报写入 Obsidian vault

    Args:
        vault_path: vault 根目录
        report: Report DSL
        markdown: 渲染后的 Markdown

    Returns:
        写入的文件路径
    """
    ensure_vault_structure(vault_path)

    period = report["meta"]["period"]
    date_str = period["end"]
    week = _iso_week(date_str)
    projects = _extract_projects(report)

    frontmatter = DAILY_FRONTMATTER.format(
        date=date_str,
        week=week,
        project_tags=_project_tags(projects),
        project_names=_project_names(projects),
    )

    # 正文前添加项目 wikilink
    wikilinks = _project_wikilinks(projects)
    if wikilinks:
        content = frontmatter + "\n\n## 相关项目\n\n" + wikilinks + "\n\n" + markdown
    else:
        content = frontmatter + "\n\n" + markdown

    filepath = os.path.join(vault_path, "日报", f"{date_str}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def save_weekly_to_obsidian(vault_path: str, report: dict, markdown: str) -> str:
    """将周报写入 Obsidian vault

    Args:
        vault_path: vault 根目录
        report: Report DSL
        markdown: 渲染后的 Markdown

    Returns:
        写入的文件路径
    """
    ensure_vault_structure(vault_path)

    period = report["meta"]["period"]
    start = period["start"]
    end = period["end"]
    week = _iso_week(start)

    frontmatter = WEEKLY_FRONTMATTER.format(
        start=start,
        end=end,
        week=week,
    )

    content = frontmatter + "\n\n" + markdown

    filepath = os.path.join(vault_path, "周报", f"{week}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def create_moc_templates(vault_path: str) -> None:
    """创建 MOC（Map of Content）模板文件

    写入：索引/日报汇总.md, 索引/周报汇总.md, 索引/项目总览.md
    """
    ensure_vault_structure(vault_path)

    templates = {
        "日报汇总.md": """---
type: moc
tags: [索引]
---

# 日报汇总

```dataview
TABLE projects, week
FROM "日报"
SORT date DESC
```
""",
        "周报汇总.md": """---
type: moc
tags: [索引]
---

# 周报汇总

```dataview
TABLE period_start as "开始", period_end as "结束"
FROM "周报"
SORT date DESC
```
""",
        "项目总览.md": """---
type: moc
tags: [索引]
---

# 项目总览

```dataview
LIST
FROM "项目"
SORT file.name ASC
```

## 所有项目标签

```dataview
LIST
FROM [[]]
WHERE contains(tags, "日报")
```
""",
    }

    for filename, content in templates.items():
        filepath = os.path.join(vault_path, "索引", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)