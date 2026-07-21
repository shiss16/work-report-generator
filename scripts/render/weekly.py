"""周报渲染器"""


class WeeklyRenderer:
    """周报 Markdown 渲染"""

    def render(self, report: dict, config: dict) -> str:
        meta = report["meta"]
        period = meta["period"]
        stats = report.get("stats", {})
        lines = []

        # 标题
        lines.append(f"## {period['start']} - {period['end']} 工作内容报告")
        lines.append("")
        lines.append(f"> 会议 {stats.get('total_meetings', 0)} 场 | "
                     f"有纪要 {stats.get('with_note', 0)} 场 | "
                     f"任务 {stats.get('total_tasks', 0)} 个")
        lines.append("")

        # 概览表格
        lines.append("### 📊 概览")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 会议总数 | {stats.get('total_meetings', 0)} 场 |")
        lines.append(f"| 有纪要 | {stats.get('with_note', 0)} 场 |")
        lines.append(f"| 无记录 | {stats.get('without_any', 0)} 场 |")
        if stats.get("busiest_day"):
            lines.append(f"| 最忙日 | {stats['busiest_day']}（{stats.get('busiest_count', 0)} 场）|")
        lines.append(f"| 完成任务 | {stats.get('completed_tasks', 0)} 个 |")
        lines.append(f"| 待办任务 | {stats.get('pending_tasks', 0)} 个 |")
        lines.append("")

        # 每日详情
        for day in report.get("daily_items", []):
            dw = day.get("day_of_week", "")
            lines.append(f"---")
            lines.append("")
            lines.append(f"### 📅 {day['date']}（{dw}）")
            lines.append("")

            if day.get("meetings"):
                for m in day["meetings"]:
                    status_icon = _status_icon(m.get("fetch_status", ""))
                    start = m.get('start_time', '')
                    end = m.get('end_time', '')
                    time_range = f"{start.split(' ')[-1][:5]}-{end.split(' ')[-1][:5]}"
                    lines.append(f"**{m['title']}** {status_icon}")
                    lines.append(f"  > {time_range}")
                    if m.get("ai_summary"):
                        lines.append(f"  > {m['ai_summary'][:150]}")
                    lines.append("")

            if day.get("tasks_completed"):
                lines.append("**完成：**")
                for t in day["tasks_completed"]:
                    proj = f" [{t.get('project_name', '')}]" if t.get("project_name") else ""
                    lines.append(f"  - {t['title']}{proj}")
                lines.append("")

        # 工作脉络
        threads = report.get("threads", [])
        if threads:
            lines.append("---")
            lines.append("")
            lines.append("### 📊 工作脉络总结")
            lines.append("")
            for i, t in enumerate(threads, 1):
                lines.append(f"{i}. **{t['theme']}** — {t['summary']}")
            lines.append("")

        # 僵尸任务
        stale = report.get("stale_tasks", [])
        if stale:
            lines.append("### ⚠️ 僵尸任务")
            for t in stale:
                lines.append(f"  - {t['title']} — 已搁置 {t['days_stale']} 天")

        return "\n".join(lines)


def _status_icon(status: str) -> str:
    icons = {
        "ok": "✅",
        "no_note": "—",
        "missing_scope": "🔒",
        "fetch_error": "⚠️",
        "empty_content": "⚠️",
    }
    return icons.get(status, "—")