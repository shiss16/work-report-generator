"""命令行入口 — 日报/周报生成"""

import argparse
import os
import sys

# 确保能找到 scripts 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.config import load_config, get_db_path, get_output_dir
from scripts.assemble import assemble_daily, assemble_weekly
from scripts.render.daily import DailyRenderer
from scripts.render.weekly import WeeklyRenderer
from scripts.render.markdown_output import save_to_local


def main():
    parser = argparse.ArgumentParser(description="工作内容报告生成器")
    parser.add_argument("mode", choices=["daily", "weekly"], help="报告模式")
    parser.add_argument("--workspace", required=True, help="workspace 路径")
    parser.add_argument("--date", help="日报日期 (YYYY-MM-DD)")
    parser.add_argument("--start", help="周报开始日期")
    parser.add_argument("--end", help="周报结束日期")
    parser.add_argument("--confirm", action="store_true", help="确认并发布周报")
    args = parser.parse_args()

    config = load_config(args.workspace)
    db_path = get_db_path(args.workspace)
    output_dir = get_output_dir(args.workspace)

    if args.mode == "daily":
        from datetime import date
        target_date = args.date or date.today().isoformat()
        report = assemble_daily(db_path, target_date, config)
        renderer = DailyRenderer()
        md = renderer.render(report, config)

        output_path = f"{output_dir}/{target_date}.md"
        save_to_local(md, output_path)
        print(f"日报已生成: {output_path}")
        print(md)

    elif args.mode == "weekly":
        from datetime import date, timedelta
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        start_date = args.start or monday.isoformat()
        end_date = args.end or today.isoformat()

        report = assemble_weekly(db_path, start_date, end_date, config)
        renderer = WeeklyRenderer()
        md = renderer.render(report, config)

        output_path = f"{output_dir}/weekly_{start_date}_{end_date}.md"
        save_to_local(md, output_path)

        if args.confirm:
            print(f"周报已确认发布: {output_path}")
        else:
            print(f"周报预览已生成: {output_path}")
        print(md)


if __name__ == "__main__":
    main()