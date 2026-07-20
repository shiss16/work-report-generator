"""日报渲染器"""


class DailyRenderer:
    """日报 Markdown 渲染"""

    def render(self, report: dict, config: dict) -> str:
        meta = report["meta"]
        period = meta["period"]
        stats = report.get("stats", {})
        lines = []

        # 标题
        lines.append(f"## {period['start']} 工作日报")
        lines.append("")

        # 概览
        lines.append(f"> 会议 {stats.get('total_meetings', 0)} 场 | "
                     f"有纪要 {stats.get('with_note', 0)} 场 | "
                     f"待办 {stats.get('pending_tasks', 0)} 个")
        lines.append("")

        # 每日详情
        for day in report.get("daily_items", []):
            dw = day.get("day_of_week", "")
            lines.append(f"### {day['date']}（{dw}）")
            lines.append("")

            # 会议
            if day.get("meetings"):
                for m in day["meetings"]:
                    status_icon = _status_icon(m.get("fetch_status", ""))
                    time_range = f"{m.get('start_time', '')}-{m.get('end_time', '')}"
                    lines.append(f"- {status_icon} **{m['title']}** ({time_range})")
                    if m.get("ai_summary"):
                        lines.append(f"  {m['ai_summary'][:100]}")
                    if m.get("todos"):
                        try:
                            import json
                            todos = json.loads(m["todos"]) if isinstance(m["todos"], str) else m["todos"]
                            for todo in todos:
                                lines.append(f"  - [ ] {todo['content']}（{todo.get('assignee', '')}）")
                        except (json.JSONDecodeError, TypeError):
                            pass
                lines.append("")

            # 完成任务
            if day.get("tasks_completed"):
                lines.append("✅ 完成")
                for t in day["tasks_completed"]:
                    proj = f" [{t.get('project_name', '')}]" if t.get("project_name") else ""
                    lines.append(f"  - {t['title']}{proj}")
                lines.append("")

            # 待办任务
            if day.get("tasks_pending"):
                lines.append("📌 待办")
                for t in day["tasks_pending"]:
                    proj = f" [{t.get('project_name', '')}]" if t.get("project_name") else ""
                    lines.append(f"  - {t['title']}{proj}")
                lines.append("")

        # 僵尸任务
        stale = report.get("stale_tasks", [])
        if stale:
            lines.append("⚠️ 僵尸任务")
            for t in stale:
                lines.append(f"  - {t['title']} — 已搁置 {t['days_stale']} 天")
            lines.append("")

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