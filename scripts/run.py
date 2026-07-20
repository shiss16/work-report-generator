"""Agent 调用入口 — 简化版，供 SKILL.md 引用

用法:
    python scripts/run.py daily   # 日报模式
    python scripts/run.py weekly  # 周报模式（预览）
    python scripts/run.py weekly --confirm  # 周报模式（确认发布）
"""

import os
import sys
from datetime import date, timedelta
from scripts.config import load_config, get_db_path, get_output_dir
from scripts.assemble import assemble_daily, assemble_weekly
from scripts.render.daily import DailyRenderer
from scripts.render.weekly import WeeklyRenderer
from scripts.render.markdown_output import save_to_local


def run(workspace: str, mode: str, confirm: bool = False):
    config = load_config(workspace)
    db_path = get_db_path(workspace)
    output_dir = get_output_dir(workspace)

    if mode == "daily":
        target_date = date.today().isoformat()
        report = assemble_daily(db_path, target_date, config)
        renderer = DailyRenderer()
        md = renderer.render(report, config)

        output_path = os.path.join(output_dir, f"{target_date}.md")
        save_to_local(md, output_path)
        return {"report": report, "markdown": md, "output_path": output_path}

    elif mode == "weekly":
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        start_date = monday.isoformat()
        end_date = today.isoformat()

        report = assemble_weekly(db_path, start_date, end_date, config)
        renderer = WeeklyRenderer()
        md = renderer.render(report, config)

        output_path = os.path.join(output_dir, f"weekly_{start_date}_{end_date}.md")
        save_to_local(md, output_path)
        return {
            "report": report, "markdown": md, "output_path": output_path,
            "confirmed": confirm,
        }


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    confirm = "--confirm" in sys.argv
    workspace = os.getcwd()

    result = run(workspace, mode, confirm)
    print(result["markdown"])
    print(f"\n---\n报告已保存: {result['output_path']}")