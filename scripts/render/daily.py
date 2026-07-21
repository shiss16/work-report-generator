"""日报渲染器"""

import json


def _parse_todos(todos_raw) -> list[dict]:
    """解析 todos，兼容字符串数组和对象数组两种格式

    字符串格式: ["张三：完成xxx", "李四：确认yyy"]
    对象格式:   [{"content": "xxx", "assignee": "张三"}]

    返回: [{"content": "...", "assignee": "..."}]
    """
    if not todos_raw:
        return []

    if isinstance(todos_raw, str):
        try:
            todos_raw = json.loads(todos_raw)
        except (json.JSONDecodeError, TypeError):
            return []

    if not isinstance(todos_raw, list):
        return []

    result = []
    for item in todos_raw:
        if isinstance(item, dict):
            result.append({
                "content": item.get("content", ""),
                "assignee": item.get("assignee", ""),
            })
        elif isinstance(item, str):
            # 尝试解析 "张三：xxx" 格式
            if "：" in item:
                assignee, content = item.split("：", 1)
                result.append({"content": content.strip(), "assignee": assignee.strip()})
            elif ":" in item:
                assignee, content = item.split(":", 1)
                result.append({"content": content.strip(), "assignee": assignee.strip()})
            else:
                result.append({"content": item.strip(), "assignee": ""})
    return result


def _parse_participants(participants_raw) -> list[str]:
    """解析参会人列表"""
    if not participants_raw:
        return []
    if isinstance(participants_raw, str):
        try:
            return json.loads(participants_raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if isinstance(participants_raw, list):
        return participants_raw
    return []


def _calc_duration(start: str, end: str) -> str:
    """计算会议时长，如 '20min'"""
    try:
        from datetime import datetime
        s = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end)
        minutes = int((e - s).total_seconds() / 60)
        if minutes >= 60:
            h = minutes // 60
            m = minutes % 60
            return f"{h}h{m}min" if m else f"{h}h"
        return f"{minutes}min"
    except Exception:
        return ""


def _status_icon(status: str) -> str:
    icons = {
        "ok": "✅",
        "no_note": "—",
        "missing_scope": "🔒",
        "fetch_error": "⚠️",
        "empty_content": "⚠️",
    }
    return icons.get(status, "—")


_PRIORITY_LABELS = {
    "urgent": "🔴 紧急",
    "high": "🟡 本周",
    "normal": "🟢 常规",
}


class DailyRenderer:
    """日报 Markdown 渲染"""

    def render(self, report: dict, config: dict) -> str:
        meta = report["meta"]
        period = meta["period"]
        stats = report.get("stats", {})
        lines = []

        # === 标题 ===
        lines.append(f"## {period['end']} 工作日报")
        lines.append("")

        # 收集所有待办和参会人
        all_todos = []
        all_participants = set()
        total_meetings = 0
        meetings_with_note = 0

        for day in report.get("daily_items", []):
            for m in day.get("meetings", []):
                total_meetings += 1
                if m.get("fetch_status") == "ok":
                    meetings_with_note += 1
                todos = _parse_todos(m.get("todos"))
                all_todos.extend(todos)
                for p in _parse_participants(m.get("participants")):
                    all_participants.add(p)

        # === 概览 ===
        parts = [f"{total_meetings} 场会议"]
        if meetings_with_note > 0:
            parts.append(f"{meetings_with_note} 场有纪要")
        if all_participants:
            parts.append(f"{len(all_participants)} 人参会")
        if all_todos:
            parts.append(f"{len(all_todos)} 条待办")
        lines.append(f"> {' | '.join(parts)}")
        lines.append("")

        # === LLM 简报 ===
        brief = report.get("brief", "")
        actions = report.get("actions", [])

        if brief:
            lines.append("### 🎯 今日简报")
            lines.append("")
            lines.append(brief)
            lines.append("")

        # === LLM 行动清单 ===
        if actions:
            lines.append("### 📋 今日行动清单")
            lines.append("")
            for action in actions:
                priority = action.get("priority", "normal")
                label = _PRIORITY_LABELS.get(priority, "🟢 常规")
                content = action.get("content", "")
                assignee = action.get("assignee", "")
                reason = action.get("reason", "")
                source = action.get("source", "")

                line = f"- {label} "
                if assignee:
                    line += f"**{assignee}**：{content}"
                else:
                    line += content
                if reason:
                    line += f"  — _{reason}_"
                lines.append(line)
            lines.append("")

        # === 会议详情 ===
        lines.append("### 📅 昨日会议")
        lines.append("")

        for day in report.get("daily_items", []):
            if not day.get("meetings"):
                continue

            for m in day["meetings"]:
                status_icon = _status_icon(m.get("fetch_status", ""))

                # 时间范围 + 时长
                start = m.get("start_time", "")
                end = m.get("end_time", "")
                time_str = f"{start.split(' ')[-1][:5]}-{end.split(' ')[-1][:5]}"
                duration = _calc_duration(start, end)
                time_info = f"{time_str} · {duration}" if duration else time_str

                # 参会人
                participants = _parse_participants(m.get("participants"))
                ppl = "、".join(participants[:6])
                if len(participants) > 6:
                    ppl += f"等{len(participants)}人"

                # 标题行
                lines.append(f"- {status_icon} **{m['title']}** ({time_info})")
                if ppl:
                    lines.append(f"  👤 {ppl}")

                # AI 摘要
                if m.get("ai_summary"):
                    lines.append(f"  {m['ai_summary'][:250]}")

                # 会议待办
                meeting_todos = _parse_todos(m.get("todos"))
                for todo in meeting_todos:
                    if todo["assignee"]:
                        lines.append(f"  - [ ] {todo['assignee']}：{todo['content']}")
                    else:
                        lines.append(f"  - [ ] {todo['content']}")

                lines.append("")

        # === 完成任务 ===
        has_completed = False
        for day in report.get("daily_items", []):
            if day.get("tasks_completed"):
                if not has_completed:
                    lines.append("### ✅ 完成任务")
                    lines.append("")
                    has_completed = True
                for t in day["tasks_completed"]:
                    proj = f" [{t.get('project_name', '')}]" if t.get("project_name") else ""
                    lines.append(f"- {t['title']}{proj}")
        if has_completed:
            lines.append("")

        # === 待办任务 ===
        has_pending = False
        for day in report.get("daily_items", []):
            if day.get("tasks_pending"):
                if not has_pending:
                    lines.append("### 📌 待办任务")
                    lines.append("")
                    has_pending = True
                for t in day["tasks_pending"]:
                    proj = f" [{t.get('project_name', '')}]" if t.get("project_name") else ""
                    lines.append(f"- {t['title']}{proj}")
        if has_pending:
            lines.append("")

        # === 僵尸任务 ===
        stale = report.get("stale_tasks", [])
        if stale:
            lines.append("### ⚠️ 僵尸任务")
            lines.append("")
            for t in stale:
                lines.append(f"- {t['title']} — 已搁置 {t['days_stale']} 天")
            lines.append("")

        return "\n".join(lines)