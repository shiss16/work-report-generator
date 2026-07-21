"""LLM 增强 — 为日报生成简报和行动清单"""

import json


def _safe_str(val, default=""):
    """安全转字符串"""
    if val is None:
        return default
    return str(val)


def _parse_todos_for_prompt(todos_raw) -> list[str]:
    """解析 todos 为字符串列表，用于 prompt 构建"""
    if not todos_raw:
        return []
    if isinstance(todos_raw, str):
        try:
            parsed = json.loads(todos_raw)
        except (json.JSONDecodeError, TypeError):
            return []
    elif isinstance(todos_raw, list):
        parsed = todos_raw
    else:
        return []

    result = []
    for item in parsed:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            content = item.get("content", "")
            assignee = item.get("assignee", "")
            if assignee:
                result.append(f"{assignee}：{content}")
            else:
                result.append(content)
    return result


def build_daily_prompt(meetings: list[dict], user_name: str) -> str:
    """构建日报增强 LLM prompt

    Args:
        meetings: 7 天内的会议列表，每项含 title, date, ai_summary, todos, participants
        user_name: 当前用户姓名，用于过滤个人相关待办

    Returns:
        LLM prompt 字符串
    """
    # 构建会议数据摘要
    meeting_lines = []
    for i, m in enumerate(meetings, 1):
        title = _safe_str(m.get("title"), "无标题")
        date = _safe_str(m.get("date"), "")
        summary = _safe_str(m.get("ai_summary"), "无纪要")
        todos = _parse_todos_for_prompt(m.get("todos"))

        lines = [f"会议{i}：{title}（{date}）"]
        lines.append(f"  摘要：{summary}")
        if todos:
            for t in todos:
                lines.append(f"  待办：{t}")
        meeting_lines.append("\n".join(lines))

    meetings_text = "\n\n".join(meeting_lines) if meeting_lines else "（无会议记录）"

    prompt = f"""你是 {user_name} 的工作助手。请根据以下昨天的会议记录，生成一份今日工作指南。

## 会议记录

{meetings_text}

## 输出要求

请以 JSON 格式输出，包含两个字段：

1. **brief**：一段 2-4 句话的自然语言简报，总结昨天关键进展和今天需要关注的重点。语气简洁直接。
2. **actions**：今日行动清单，每个行动包含：
   - priority: "urgent"（今天截止/阻塞项）| "high"（本周内）| "normal"（常规跟进）
   - content: 具体行动内容
   - assignee: 负责人
   - reason: 为什么这项行动需要优先处理（1句话）
   - source: 来源会议名称

输出格式：
```json
{{
  "brief": "...",
  "actions": [
    {{
      "priority": "urgent",
      "content": "...",
      "assignee": "...",
      "reason": "...",
      "source": "..."
    }}
  ]
}}
```

注意：
- 优先关注 {user_name} 的待办，其他人的待办仅在需要 {user_name} 配合时列出
- 从会议摘要中识别隐含的截止日期和阻塞关系
- 如果某件事在多个会议中被提及，说明它是当前焦点
- 仅输出 JSON，不要任何额外文字
"""
    return prompt


def parse_llm_response(response: str) -> dict:
    """解析 LLM 返回的 JSON 响应

    Args:
        response: LLM 返回的原始文本

    Returns:
        {"brief": str, "actions": list}，解析失败返回空 dict
    """
    if not response:
        return {"brief": "", "actions": []}

    # 尝试提取 JSON 块
    text = response.strip()
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        text = text[start:end].strip()

    try:
        data = json.loads(text)
        return {
            "brief": data.get("brief", ""),
            "actions": data.get("actions", []),
        }
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass

    # Fallback: 尝试从文本中提取 JSON 对象
    for i, ch in enumerate(text):
        if ch == "{":
            # 尝试从当前位置解析 JSON
            depth = 0
            for j in range(i, len(text)):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            data = json.loads(text[i:j + 1])
                            return {
                                "brief": data.get("brief", ""),
                                "actions": data.get("actions", []),
                            }
                        except (json.JSONDecodeError, ValueError):
                            break
            break

    return {"brief": "", "actions": []}


def call_llm(prompt: str) -> str:
    """调用 LLM（生产环境实现，测试时 monkeypatch）

    Args:
        prompt: prompt 文本

    Returns:
        LLM 响应文本
    """
    # 生产环境由 Agent 工作流调用，此处为占位
    raise NotImplementedError(
        "call_llm() 由 Agent 工作流实现，测试时请 monkeypatch"
    )