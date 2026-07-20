"""飞书输出 — 生成飞书消息/文档的提示信息

本模块不直接调用飞书 API，而是生成结构化的提示信息，
供 Agent 通过 lark-im / lark-doc skill 执行。
"""


def build_feishu_message_prompt(markdown: str, config: dict) -> dict:
    """生成飞书消息推送的提示信息"""
    target = config.get("channels", {}).get("feishu", {}).get("msg_target", "self")

    return {
        "action": "send_message",
        "skill": "lark-im",
        "target": target,
        "content": markdown,
        "instruction": f"使用 lark-im skill 发送以下消息给 {target}"
    }


def build_feishu_doc_prompt(markdown: str, title: str, config: dict) -> dict:
    """生成飞书文档发布的提示信息"""
    folder = config.get("channels", {}).get("feishu", {}).get("doc_folder", "")

    return {
        "action": "create_doc",
        "skill": "lark-doc",
        "title": title,
        "folder": folder,
        "content": markdown,
        "instruction": f"使用 lark-doc skill 创建飞书文档，标题: {title}"
    }